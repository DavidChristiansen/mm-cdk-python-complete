#!/usr/bin/env python3

from aws_cdk import core

from cdk.developer_stack import DeveloperStack
from cdk.webapplication_stack import WebApplicationStack
from cdk.network_stack import NetworkStack
from cdk.ecr_stack import EcrStack
from cdk.ecs_stack import EcsStack, EcsStackProps
from cdk.cicd_stack import CiCdStack, CiCdStackProps
from cdk.dynamodb_stack import DynamoDbStack, DynamoDbStackProps
from cdk.apigateway_stack import APIGatewayStack, APIGatewayStackProps
from cdk.kinesis_firehose_stack import KinesisFirehoseStack, KinesisFirehoseStackProps
from cdk.xray_stack import XRayStack
from cdk.sagemaker_stack import SagemakerStack

app = core.App()

developerToolStack = DeveloperStack(app, "MythicalMysfits-DeveloperTools")
WebApplicationStack(app, "MythicalMysfits-WebApplication")

network_stack = NetworkStack(app, "MythicalMysfits-NetworkStack")

ecr_stack = EcrStack(app, "MythicalMysfits-EcrStack")
ecs_stack_props = EcsStackProps()
ecs_stack_props.vpc = network_stack.vpc
ecs_stack_props.ecr_repository = ecr_stack.ecr_repository

ecs_stack = EcsStack(app, "MythicalMysfits-EcsStack", ecs_stack_props)

cicd_stack_props = CiCdStackProps()
cicd_stack_props.ecr_repository = ecr_stack.ecr_repository
cicd_stack_props.ecs_service = ecs_stack.ecs_service.service

cicd_stack = CiCdStack(app, "MythicalMysfits-CiCdStack", cicd_stack_props)

dynamodb_stack_props = DynamoDbStackProps()
dynamodb_stack_props.fargate_service = ecs_stack.ecs_service.service
dynamodb_stack = DynamoDbStack(
    app, "MythicalMysfits-DynamoDbStack", dynamodb_stack_props
)

apigateway_stack_props = APIGatewayStackProps()
apigateway_stack_props.fargate_service = ecs_stack.ecs_service
apigateway_stack = APIGatewayStack(
    app, "MythicalMysfits-ApiGatewayStack", apigateway_stack_props
)

kinesis_firehose_stack_props = KinesisFirehoseStackProps()
kinesis_firehose_stack_props.table = dynamodb_stack.table
kinesis_firehose_stack_props.api_gateway = apigateway_stack.api_gateway
kinesis_firehose_stack = KinesisFirehoseStack(
    app, "MythicalMysfits-KinesisFirehoseStack", kinesis_firehose_stack_props
)

xray_stack = XRayStack(app, "MythicalMysfits-XRayStack")

sagemaker_stack = SagemakerStack(app, "MythicalMysfits-SageMaker")

app.synth()
