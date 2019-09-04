#!/usr/bin/env python3

from aws_cdk import core

from cdk.developer_stack import DeveloperStack
from cdk.webapplication_stack import WebApplicationStack


app = core.App()

developerToolStack = DeveloperStack(app, "MythicalMysfits-DeveloperTools")
WebApplicationStack(app, "MythicalMysfits-WebApplication")

app.synth()
