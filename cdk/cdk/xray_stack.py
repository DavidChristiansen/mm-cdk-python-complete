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
    core,
)
from dotenv import load_dotenv
import os

load_dotenv()


class XRayStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        lambda_repository = aws_codecommit.Repository(
            self,
            "QuestionsLambdaRepository",
            repository_name="MythicalMysfits-QuestionsLambdaRepository",
        )

        core.CfnOutput(
            self,
            "questionsRepositoryCloneUrlHTTP",
            value=lambda_repository.repository_clone_url_http,
            description="Questions Lambda Repository Clone URL HTTP",
        )
        core.CfnOutput(
            self,
            "questionsRepositoryCloneUrlSSH",
            value=lambda_repository.repository_clone_url_ssh,
            description="Questions Lambda Repository Clone URL SSH",
        )

        table = aws_dynamodb.Table(
            self,
            "Table",
            table_name="MysfitsQuestionsTable",
            partition_key=aws_dynamodb.Attribute(
                name="QuestionId", type=aws_dynamodb.AttributeType.STRING
            ),
            stream=aws_dynamodb.StreamViewType.NEW_IMAGE,
        )

        lambda_function_policy_statement_ddb = aws_iam.PolicyStatement()
        lambda_function_policy_statement_ddb.add_actions("dynamodb:PutItem")
        lambda_function_policy_statement_ddb.add_resources(table.table_arn)

        lambda_function_policy_statement_xray = aws_iam.PolicyStatement()
        lambda_function_policy_statement_xray.add_actions(
            "xray:PutTraceSegments",
            "xray:PutTelemetryRecords",
            "xray:GetSamplingRules",
            "xray:GetSamplingTargets",
            "xray:GetSamplingStatisticSummaries",
        )
        lambda_function_policy_statement_xray.add_all_resources()

        mysfits_post_question = aws_lambda.Function(
            self,
            "PostQuestionFunction",
            handler="mysfitsPostQuestion.postQuestion",
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            description="A microservice Lambda function that receives a new question submitted to the MythicalMysfits website from a user and inserts it into a DynamoDB database table.",
            memory_size=128,
            code=aws_lambda.Code.asset(
                os.path.join("..", "..", "lambda-questions", "PostQuestionsService")
            ),
            timeout=core.Duration.seconds(30),
            initial_policy=[
                lambda_function_policy_statement_ddb,
                lambda_function_policy_statement_xray,
            ],
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        topic = aws_sns.Topic(
            self,
            "Topic",
            display_name="MythicalMysfitsQuestionsTopic",
            topic_name="MythicalMysfitsQuestionsTopic",
        )
        topic.add_subscription(subs.EmailSubscription(os.environ["SNS_EMAIL"]))

        post_question_lamdaa_function_policy_statement_sns = aws_iam.PolicyStatement()
        post_question_lamdaa_function_policy_statement_sns.add_actions("sns:Publish")
        post_question_lamdaa_function_policy_statement_sns.add_resources(
            topic.topic_arn
        )

        mysfits_process_question_stream = aws_lambda.Function(
            self,
            "ProcessQuestionStreamFunction",
            handler="mysfitsProcessStream.processStream",
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            description="An AWS Lambda function that will process all new questions posted to mythical mysfits and notify the site administrator of the question that was asked.",
            memory_size=128,
            code=aws_lambda.Code.asset(
                os.path.join("..", "..", "lambda-questions", "ProcessQuestionsStream")
            ),
            timeout=core.Duration.seconds(30),
            initial_policy=[
                post_question_lamdaa_function_policy_statement_sns,
                lambda_function_policy_statement_xray,
            ],
            tracing=aws_lambda.Tracing.ACTIVE,
            environment={"SNS_TOPIC_ARN": topic.topic_arn},
            events=[
                event.DynamoEventSource(
                    table,
                    starting_position=aws_lambda.StartingPosition.TRIM_HORIZON,
                    batch_size=1,
                )
            ],
        )

        questions_api_role = aws_iam.Role(
            self,
            "QuestionsApiRole",
            assumed_by=aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
        )

        api_policy = aws_iam.PolicyStatement()
        api_policy.add_actions("lambda:InvokeFunction")
        api_policy.add_resources(mysfits_post_question.function_arn)
        aws_iam.Policy(
            self,
            "QuestionsApiPolicy",
            policy_name="questions_api_policy",
            statements=[api_policy],
            roles=[questions_api_role],
        )

        questions_integration = aws_apigateway.LambdaIntegration(
            mysfits_post_question,
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
            handler=mysfits_post_question,
            options=aws_apigateway.RestApiProps(rest_api_name="Questions API Server"),
            proxy=False,
        )

        questions_method = api.root.add_resource("questions")
        questions_method.add_method(
            "POST",
            questions_integration,
            method_responses=[aws_apigateway.MethodResponse(status_code="200")],
            authorization_type=aws_apigateway.AuthorizationType.NONE,
        )

        questions_method.add_method(
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
