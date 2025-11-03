#!/usr/bin/env python3
import aws_cdk as cdk
from constructs import Construct
from stacks.service_efficiency_platform_stack import ServiceEfficiencyPlatformStack

app = cdk.App()

# Main platform stack
ServiceEfficiencyPlatformStack(
    app, 
    "ServiceEfficiencyPlatform",
    description="Unified AWS serverless platform for SLA Guard, L1 Automation, and Asset Optimization",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1"
    )
)

app.synth()