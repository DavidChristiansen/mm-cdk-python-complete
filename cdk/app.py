#!/usr/bin/env python3

from aws_cdk import core

from cdk.developer_stack import DeveloperStack
from cdk.webapplication_stack import WebApplicationStack
from cdk.network_stack import NetworkStack
from cdk.ecr_stack import EcrStack
from cdk.ecs_stack import EcsStack, EcsStackProps
from cdk.cicd_stack import CiCdStack, CiCdStackProps


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

app.synth()
