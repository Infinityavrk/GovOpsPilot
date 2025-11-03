from aws_cdk import (
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    aws_s3 as s3,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class SLAGuardConstruct(Construct):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        event_bus: events.EventBus,
        data_lake_bucket: s3.Bucket,
        shared_config_table: dynamodb.Table
    ) -> None:
        super().__init__(scope, construct_id)

        # DynamoDB table for SLA state tracking
        self.sla_state_table = dynamodb.Table(
            self, "SLAStateTable",
            table_name="sla-guard-state",
            partition_key=dynamodb.Attribute(
                name="service_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # Global Secondary Index for breach probability queries
        self.sla_state_table.add_global_secondary_index(
            index_name="breach-probability-index",
            partition_key=dynamodb.Attribute(
                name="breach_probability_bucket",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            )
        )

        # IAM role for SLA Guard Lambda functions
        self.sla_guard_role = iam.Role(
            self, "SLAGuardRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "SLAGuardPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                                "dynamodb:Query",
                                "dynamodb:UpdateItem"
                            ],
                            resources=[
                                self.sla_state_table.table_arn,
                                f"{self.sla_state_table.table_arn}/index/*",
                                shared_config_table.table_arn
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "events:PutEvents"
                            ],
                            resources=[event_bus.event_bus_arn]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sagemaker:InvokeEndpoint"
                            ],
                            resources=["*"]  # Will be restricted to specific endpoints
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:PutObject",
                                "s3:GetObject"
                            ],
                            resources=[f"{data_lake_bucket.bucket_arn}/*"]
                        )
                    ]
                )
            }
        )

        # Metric Processor Lambda - ingests and normalizes monitoring data
        self.metric_processor = lambda_.Function(
            self, "MetricProcessor",
            function_name="sla-guard-metric-processor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="metric_processor.handler",
            code=lambda_.Code.from_asset("../../src/sla_guard"),
            role=self.sla_guard_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "SLA_STATE_TABLE": self.sla_state_table.table_name,
                "SHARED_CONFIG_TABLE": shared_config_table.table_name,
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "DATA_LAKE_BUCKET": data_lake_bucket.bucket_name
            },
            tracing=lambda_.Tracing.ACTIVE
        )

        # Breach Predictor Lambda - ML-powered SLA breach prediction
        self.breach_predictor = lambda_.Function(
            self, "BreachPredictor",
            function_name="sla-guard-breach-predictor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="breach_predictor.handler",
            code=lambda_.Code.from_asset("../../src/sla_guard"),
            role=self.sla_guard_role,
            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "SLA_STATE_TABLE": self.sla_state_table.table_name,
                "SHARED_CONFIG_TABLE": shared_config_table.table_name,
                "EVENT_BUS_NAME": event_bus.event_bus_name,
                "SAGEMAKER_ENDPOINT": "sla-predictor-endpoint"  # Will be created separately
            },
            tracing=lambda_.Tracing.ACTIVE
        )

        # Action Trigger Lambda - triggers preventive actions
        self.action_trigger = lambda_.Function(
            self, "ActionTrigger",
            function_name="sla-guard-action-trigger",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="action_trigger.handler",
            code=lambda_.Code.from_asset("../../src/sla_guard"),
            role=self.sla_guard_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "SLA_STATE_TABLE": self.sla_state_table.table_name,
                "EVENT_BUS_NAME": event_bus.event_bus_name
            },
            tracing=lambda_.Tracing.ACTIVE
        )

        # Status Update Lambda - receives updates from other agents
        self.status_updater = lambda_.Function(
            self, "StatusUpdater",
            function_name="sla-guard-status-updater",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="status_updater.handler",
            code=lambda_.Code.from_asset("../../src/sla_guard"),
            role=self.sla_guard_role,
            timeout=Duration.seconds(15),
            memory_size=256,
            environment={
                "SLA_STATE_TABLE": self.sla_state_table.table_name
            },
            tracing=lambda_.Tracing.ACTIVE
        )

        # Impact Validator Lambda - validates optimization impact on SLA
        self.impact_validator = lambda_.Function(
            self, "ImpactValidator",
            function_name="sla-guard-impact-validator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="impact_validator.handler",
            code=lambda_.Code.from_asset("../../src/sla_guard"),
            role=self.sla_guard_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "SLA_STATE_TABLE": self.sla_state_table.table_name,
                "EVENT_BUS_NAME": event_bus.event_bus_name
            },
            tracing=lambda_.Tracing.ACTIVE
        )

        # EventBridge rule for scheduled metric processing
        events.Rule(
            self, "MetricProcessingSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(self.metric_processor)]
        )

        # EventBridge rule for breach prediction triggers
        events.Rule(
            self, "BreachPredictionTrigger",
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=["sla-guard"],
                detail_type=["Metric Update"]
            ),
            targets=[targets.LambdaFunction(self.breach_predictor)]
        )

        # DynamoDB stream trigger for real-time processing
        self.breach_predictor.add_event_source_mapping(
            "SLAStateStreamTrigger",
            event_source_arn=self.sla_state_table.table_stream_arn,
            starting_position=lambda_.StartingPosition.LATEST,
            batch_size=10,
            max_batching_window=Duration.seconds(5)
        )

        # Expose targets for cross-agent communication
        self.status_update_target = targets.LambdaFunction(self.status_updater)
        self.impact_validation_target = targets.LambdaFunction(self.impact_validator)