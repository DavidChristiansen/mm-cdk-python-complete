#!/usr/bin/env python3

from aws_cdk import core

from cdk.developer_stack import DeveloperStack
from cdk.webapplication_stack import WebApplicationStack
from cdk.network_stack import NetworkStack
from cdk.ecr_stack import EcrStack


app = core.App()

developerToolStack = DeveloperStack(app, "MythicalMysfits-DeveloperTools")
WebApplicationStack(app, "MythicalMysfits-WebApplication")
NetworkStack(app, "MythicalMysfits-NetworkStack")
EcrStack(app, "MythicalMysfits-EcrStack")

app.synth()
