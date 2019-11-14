from aws_cdk import (
    aws_apigateway,
    aws_codecommit,
    aws_dynamodb,
    aws_iam,
    aws_kinesisfirehose,
    aws_lambda,
    aws_s3,
    core,
)


class KinesisFirehoseStackProps(core.StackProps):
    table: aws_dynamodb.Table = None
    api_gateway: aws_apigateway.CfnRestApi = None


class KinesisFirehoseStack(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, props: KinesisFirehoseStackProps, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        lambda_repository = aws_codecommit.Repository(
            self,
            "ClicksProcessingLambdaRepository",
            repository_name="MythicalMysfits-ClicksProcessingLambdaRepository",
        )

        core.CfnOutput(
            self,
            "kinesisRepositoryCloneUrlHttp",
            value=lambda_repository.repository_clone_url_http,
            description="Clicks Processing Lambda Repository Clone URL HTTP",
        )

        core.CfnOutput(
            self,
            "kinesisRepositoryCloneUrlSsh",
            value=lambda_repository.repository_clone_url_ssh,
            description="Clicks Processing Lambda Repository Clone URL SSH",
        )

        clicks_destination_bucket = aws_s3.Bucket(self, "Bucket", versioned=True)

        lambda_function_policy = aws_iam.PolicyStatement()
        lambda_function_policy.add_actions("dynamodb:GetItem")
        lambda_function_policy.add_resources(props.table.table_arn)

        mysfits_clicks_processor = aws_lambda.Function(
            self,
            "Function",
            handler="streamProcessor.processRecord",
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            description="An Amazon Kinesis Firehose stream processor that enriches click records to not just include a mysfitId, but also other attributes that can be analyzed later.",
            memory_size=128,
            code=aws_lambda.Code.asset("../../lambda-streaming-processor"),
            timeout=core.Duration.seconds(30),
            initial_policy=[lambda_function_policy],
            environment={
                # TODO: this seems better than having the user copy/paste it in, but is it the best way?
                "MYSFITS_API_URL": "https://{}.execute-api.{}.amazonaws.com/prod/".format(
                    props.api_gateway.ref, core.Aws.REGION
                )
            },
        )

        firehose_delivery_role = aws_iam.Role(
            self,
            "FirehoseDeliveryRole",
            role_name="FirehoseDeliveryRole",
            assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
            external_id=core.Aws.ACCOUNT_ID,
        )

        firehose_delivery_policy_s3_statement = aws_iam.PolicyStatement()
        firehose_delivery_policy_s3_statement.add_actions(
            "s3:AbortMultipartUpload",
            "s3:GetBucketLocation",
            "s3:GetObject",
            "s3:ListBucket",
            "s3:ListBucketMultipartUploads",
            "s3:PutObject",
        )
        firehose_delivery_policy_s3_statement.add_resources(
            clicks_destination_bucket.bucket_arn
        )
        firehose_delivery_policy_s3_statement.add_resources(
            clicks_destination_bucket.arn_for_objects("*")
        )

        firehose_delivery_policy_lambda_statement = aws_iam.PolicyStatement()
        firehose_delivery_policy_lambda_statement.add_actions("lambda:InvokeFunction")
        firehose_delivery_policy_lambda_statement.add_resources(
            mysfits_clicks_processor.function_arn
        )

        firehose_delivery_role.add_to_policy(firehose_delivery_policy_s3_statement)
        firehose_delivery_role.add_to_policy(firehose_delivery_policy_lambda_statement)

        mysfits_firehose_to_s3 = aws_kinesisfirehose.CfnDeliveryStream(
            self,
            "DeliveryStream",
            extended_s3_destination_configuration=aws_kinesisfirehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=clicks_destination_bucket.bucket_arn,
                buffering_hints=aws_kinesisfirehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60, size_in_m_bs=50
                ),
                compression_format="UNCOMPRESSED",
                prefix="firehose/",
                role_arn=firehose_delivery_role.role_arn,
                processing_configuration=aws_kinesisfirehose.CfnDeliveryStream.ProcessingConfigurationProperty(
                    enabled=True,
                    processors=[
                        aws_kinesisfirehose.CfnDeliveryStream.ProcessorProperty(
                            parameters=[
                                aws_kinesisfirehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="LambdaArn",
                                    parameter_value=mysfits_clicks_processor.function_arn,
                                )
                            ],
                            type="Lambda",
                        )
                    ],
                ),
            ),
        )

        aws_lambda.CfnPermission(
            self,
            "Permission",
            action="lambda:InvokeFunction",
            function_name=mysfits_clicks_processor.function_arn,
            principal="firehose.amazonaws.com",
            source_account=core.Aws.ACCOUNT_ID,
            source_arn=mysfits_firehose_to_s3.attr_arn,
        )

        click_processing_api_role = aws_iam.Role(
            self,
            "ClickProcessingApiRole",
            assumed_by=aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
        )

        api_policy = aws_iam.PolicyStatement()
        api_policy.add_actions("firehose:PutRecord")
        api_policy.add_resources(mysfits_firehose_to_s3.attr_arn)
        aws_iam.Policy(
            self,
            "ClickProcessingApiPolicy",
            policy_name="api_gateway_firehose_proxy_role",
            statements=[api_policy],
            roles=[click_processing_api_role],
        )

        api = aws_apigateway.RestApi(
            self,
            "APIEndpoint",
            rest_api_name="ClickProcessing API Service",
            endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
        )

        clicks = api.root.add_resource("clicks")

        clicks.add_method(
            "PUT",
            aws_apigateway.AwsIntegration(
                service="firehose",
                integration_http_method="POST",
                action="PutRecord",
                options=aws_apigateway.IntegrationOptions(
                    connection_type=aws_apigateway.ConnectionType.INTERNET,
                    credentials_role=click_processing_api_role,
                    integration_responses=[
                        aws_apigateway.IntegrationResponse(
                            status_code="200",
                            response_templates={"application/json": '{"status": "OK"}'},
                            response_parameters={
                                "method.response.header.Access-Control-Allow-Headers": "'Content-Type'",
                                "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,PUT'",
                                "method.response.header.Access-Control-Allow-Origin": "'*'",
                            },
                        )
                    ],
                    request_parameters={
                        "integration.request.header.Content-Type": "'application/x-amz-json-1.1'"
                    },
                    request_templates={
                        "application/json": """{ "DeliveryStreamName": "%s", "Record": { "Data": "$util.base64Encode($input.json('$'))" }}"""
                        % mysfits_firehose_to_s3.ref
                    },
                ),
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
        )

        clicks.add_method(
            "OPTIONS",
            aws_apigateway.MockIntegration(
                integration_responses=[
                    aws_apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Credentials": "'false'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,PUT,POST,DELETE'",
                        },
                    )
                ],
                passthrough_behavior=aws_apigateway.PassthroughBehavior.NEVER,
                request_templates={"application/json": '{"statusCode": 200}'},
            ),
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Credentials": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
        )
