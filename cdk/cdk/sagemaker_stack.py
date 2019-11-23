from aws_cdk import (
    aws_apigateway,
    aws_codecommit,
    aws_dynamodb,
    aws_iam,
    aws_lambda,
    aws_s3,
    aws_lambda_event_sources as event,
    aws_sns,
    aws_sns_subscriptions as subs,
    aws_sagemaker,
    core,
)
from dotenv import load_dotenv
import os

load_dotenv()


class SagemakerStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Note: typo of role name is copied from original workshop
        mysfits_notebook_role = aws_iam.Role(
            self,
            "MysfitsNotbookRole",
            assumed_by=aws_iam.ServicePrincipal("sagemaker.amazonaws.com"),
        )

        mysfits_notebook_policy = aws_iam.PolicyStatement()
        mysfits_notebook_policy.add_actions(
            "sagemaker:*",
            "ecr:GetAuthorizationToken",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability",
            "cloudwatch:PutMetricData",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:DescribeLogStreams",
            "logs:PutLogEvents",
            "logs:GetLogEvents",
            "s3:CreateBucket",
            "s3:ListBucket",
            "s3:GetBucketLocation",
            "s3:GetObject",
            "s3:PutObject",
            "s3:DeleteObject",
        )
        mysfits_notebook_policy.add_all_resources()

        mysfits_notebook_pass_role_policy = aws_iam.PolicyStatement()
        mysfits_notebook_pass_role_policy.add_actions("iam:PassRole")
        mysfits_notebook_pass_role_policy.add_all_resources()
        mysfits_notebook_pass_role_policy.add_condition(
            "StringEquals", {"iam:PassedToService": "sagemaker.amazonaws.com"}
        )

        aws_iam.Policy(
            self,
            "MysfitsNotebookPolicy",
            statements=[mysfits_notebook_pass_role_policy, mysfits_notebook_policy],
            roles=[mysfits_notebook_role],
        )

        notebook_instance = aws_sagemaker.CfnNotebookInstance(
            self,
            "MythicalMysfits-SageMaker-Notebook",
            instance_type="ml.t2.medium",
            role_arn=mysfits_notebook_role.role_arn,
        )

        lambda_repository = aws_codecommit.Repository(
            self,
            "RecommendationsLambdaRepository",
            repository_name="MythicalMysfits-RecommendationsLambdaRepository",
        )

        core.CfnOutput(
            self,
            "recommandationsRepositoryCloneUrlHttp",
            value=lambda_repository.repository_clone_url_http,
            description="Recommendations Lambda Repository Clone Url HTTP",
        )

        core.CfnOutput(
            self,
            "recommandationsRepositoryCloneUrlSsh",
            value=lambda_repository.repository_clone_url_ssh,
            description="Recommendations Lambda Repository Clone Url SSH",
        )

        recommendations_lambda_function_policy_statement = aws_iam.PolicyStatement()
        recommendations_lambda_function_policy_statement.add_actions(
            "sagemaker:InvokeEndpoint"
        )
        recommendations_lambda_function_policy_statement.add_all_resources()

        mysfits_recommendations = aws_lambda.Function(
            self,
            "Function",
            handler="recommendations.recommend",
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            description="A microservice backend to a SageMaker endpoint",
            memory_size=128,
            code=aws_lambda.Code.asset(
                os.path.join("..", "..", "lambda-recommendations/service")
            ),
            timeout=core.Duration.seconds(30),
            initial_policy=[recommendations_lambda_function_policy_statement],
        )

        questions_api_role = aws_iam.Role(
            self,
            "QuestionsApiRole",
            assumed_by=aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
        )
        api_policy = aws_iam.PolicyStatement()
        api_policy.add_actions("lambda:InvokeFunction")
        api_policy.add_resources(mysfits_recommendations.function_arn)
        aws_iam.Policy(
            self,
            "QuestionsApiPolicy",
            policy_name="questions_api_policy",
            statements=[api_policy],
            roles=[questions_api_role],
        )

        questions_integration = aws_apigateway.LambdaIntegration(
            mysfits_recommendations,
            credentials_role=questions_api_role,
            integration_responses=[
                aws_apigateway.IntegrationResponse(
                    status_code="200",
                    response_templates={"application/json": '{"status": "OK"}'},
                )
            ],
        )

        api = aws_apigateway.LambdaRestApi(
            self,
            "APIEndpoint",
            handler=mysfits_recommendations,
            rest_api_name="Recommendation API Service",
            proxy=False,
        )

        recommendations_method = api.root.add_resource("recommendations")
        recommendations_method.add_method(
            "POST",
            questions_integration,
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
            authorization_type=aws_apigateway.AuthorizationType.NONE,
        )

        recommendations_method.add_method(
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
