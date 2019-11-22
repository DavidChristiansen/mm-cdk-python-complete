from aws_cdk import core, aws_dynamodb, aws_iam, aws_ecs


class DynamoDbStackProps(core.StackProps):
    fargate_service: aws_ecs.FargateService = None


class DynamoDbStack(core.Stack):
    @property
    def table(self) -> aws_dynamodb.Table:
        return self._table

    def __init__(
        self, scope: core.Construct, id: str, props: DynamoDbStackProps, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        table = aws_dynamodb.Table(
            self,
            "Table",
            table_name="MysfitsTable",
            partition_key=aws_dynamodb.Attribute(
                name="MysfitId", type=aws_dynamodb.AttributeType.STRING
            ),
        )

        table.add_global_secondary_index(
            index_name="LawChaosIndex",
            partition_key=aws_dynamodb.Attribute(
                name="LawChaos", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="MysfitId", type=aws_dynamodb.AttributeType.STRING
            ),
            read_capacity=5,
            write_capacity=5,
            projection_type=aws_dynamodb.ProjectionType.ALL,
        )

        table.add_global_secondary_index(
            index_name="GoodEvilIndex",
            partition_key=aws_dynamodb.Attribute(
                name="GoodEvil", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="MysfitId", type=aws_dynamodb.AttributeType.STRING
            ),
            read_capacity=5,
            write_capacity=5,
            projection_type=aws_dynamodb.ProjectionType.ALL,
        )

        fargate_policy = aws_iam.PolicyStatement()
        for action in ["Scan", "Query", "UpdateItem", "GetItem", "DescribeTable"]:
            fargate_policy.add_actions("dynamodb:{}".format(action))
        fargate_policy.add_resources(table.table_arn)
        fargate_policy.add_resources("{}/index/LawChaosIndex".format(table.table_arn))
        fargate_policy.add_resources("{}/index/GoodEvilIndex".format(table.table_arn))
        props.fargate_service.task_definition.add_to_task_role_policy(fargate_policy)
        self._table = table
