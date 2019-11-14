from aws_cdk import (
    core,
    aws_ecs_patterns,
    aws_apigateway,
    aws_elasticloadbalancingv2 as elbv2,
)
import os.path
import json
from dotenv import load_dotenv


load_dotenv()


class APIGatewayStackProps(core.StackProps):
    fargate_service: aws_ecs_patterns.NetworkLoadBalancedFargateService = None


class APIGatewayStack(core.Stack):
    @property
    def api_gateway(self) -> aws_apigateway.CfnRestApi:
        return self._api_gateway

    def __init__(
        self, scope: core.Construct, id: str, props: APIGatewayStackProps, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        nlb = elbv2.NetworkLoadBalancer.from_network_load_balancer_attributes(
            self,
            "NLB",
            load_balancer_arn=props.fargate_service.load_balancer.load_balancer_arn,
        )

        vpc_link = aws_apigateway.VpcLink(
            self, "VPCLink", vpc_link_name="VPCLink for our REST API", targets=[nlb]
        )

        schema = APIGatewayStack._generate_swagger_spec(
            props.fargate_service.load_balancer.load_balancer_dns_name, vpc_link
        )
        json_schema = json.loads(schema)
        api = aws_apigateway.CfnRestApi(
            self,
            "Schema",
            name="MysfitsApi",
            body=json_schema,
            endpoint_configuration=aws_apigateway.CfnRestApi.EndpointConfigurationProperty(
                types=["REGIONAL"]
            ),
            fail_on_warnings=True,
        )

        aws_apigateway.CfnDeployment(
            self, "Prod", rest_api_id=api.ref, stage_name="prod"
        )

        core.CfnOutput(self, "APIID", value=api.ref, description="API Gateway ID")
        self._api_gateway = api

    @staticmethod
    def _generate_swagger_spec(dns_name: str, vpc_link: aws_apigateway.VpcLink) -> str:
        userpool_identity = os.environ["CDK_USERPOOL_IDENTITY"]
        schema_filepath = os.path.realpath(
            os.path.join("..", "api", "api-swagger.json")
        )
        with open(schema_filepath, "r") as file_handle:
            api_schema = file_handle.read()
        api_schema = api_schema.replace("REPLACE_ME_REGION", core.Aws.REGION)
        api_schema = api_schema.replace("REPLACE_ME_ACCOUNT_ID", core.Aws.ACCOUNT_ID)
        api_schema = api_schema.replace(
            "REPLACE_ME_COGNITO_USER_POOL_ID", userpool_identity
        )
        api_schema = api_schema.replace("REPLACE_ME_VPC_LINK_ID", vpc_link.vpc_link_id)
        api_schema = api_schema.replace("REPLACE_ME_NLB_DNS", dns_name)
        return api_schema
