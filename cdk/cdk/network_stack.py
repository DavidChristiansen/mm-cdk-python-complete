from aws_cdk import aws_iam as iam, aws_ec2 as ec2, core


class NetworkStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, "VPC", nat_gateways=2, max_azs=2)
        dynamodb_endpoint = vpc.add_gateway_endpoint(
            "DynamoDbEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            subnets=[ec2.SubnetType.PRIVATE],
        )
        dynamodb_policy = iam.PolicyStatement()
        dynamodb_policy.add_any_principal()
        dynamodb_policy.add_actions("*")
        dynamodb_policy.add_all_resources()
        dynamodb_endpoint.add_to_policy(dynamodb_policy)
