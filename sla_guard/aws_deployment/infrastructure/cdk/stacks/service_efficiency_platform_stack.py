from aws_cdk import (
    Stack,
    aws_events as events,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_sagemaker as sagemaker,
    aws_quicksight as quicksight,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from .constructs.sla_guard_construct import SLAGuardConstruct
from .constructs.unified_dashboard_construct import UnifiedDashboardConstruct

class ServiceEfficiencyPlatformStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Core EventBridge custom bus for inter-agent communication
        self.event_bus = events.EventBus(
            self, "ServiceEfficiencyEventBus",
            event_bus_name="service-efficiency-platform"
        )

        # S3 Data Lake for unified analytics
        self.data_lake_bucket = s3.Bucket(
            self, "ServiceEfficiencyDataLake",
            bucket_name=f"service-efficiency-data-lake-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ArchiveOldData",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ]
        )

        # Shared DynamoDB tables for cross-agent state
        self.shared_config_table = dynamodb.Table(
            self, "SharedConfigTable",
            table_name="service-efficiency-shared-config",
            partition_key=dynamodb.Attribute(
                name="config_key",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True
        )

        # SLA Guard Agent 🧩
        self.sla_guard = SLAGuardConstruct(
            self, "SLAGuard",
            event_bus=self.event_bus,
            data_lake_bucket=self.data_lake_bucket,
            shared_config_table=self.shared_config_table
        )

        # Unified QuickSight Dashboard
        self.dashboard = UnifiedDashboardConstruct(
            self, "UnifiedDashboard",
            data_lake_bucket=self.data_lake_bucket,
            sla_guard_table=self.sla_guard.sla_state_table,
            l1_task_table=None,  # Will be added when L1 agent is implemented
            asset_table=None     # Will be added when asset optimizer is implemented
        )

        # Cross-agent EventBridge rules for coordination
        self._setup_cross_agent_rules()

    def _setup_cross_agent_rules(self):
        """Set up EventBridge rules for cross-agent communication"""
        
        # SLA breach prediction triggers future L1 automation
        events.Rule(
            self, "SLAToL1TriggerRule",
            event_bus=self.event_bus,
            event_pattern=events.EventPattern(
                source=["sla-guard"],
                detail_type=["SLA Breach Prediction"],
                detail={
                    "breach_probability": events.Match.exists_at_path("$.breach_probability")
                }
            ),
            targets=[
                # Will be connected to L1 automation when implemented
            ]
        )

        # All events flow to dashboard for real-time updates
        events.Rule(
            self, "AllEventsToDashboardRule",
            event_bus=self.event_bus,
            event_pattern=events.EventPattern(
                source=["sla-guard", "l1-automation", "asset-optimizer"]
            ),
            targets=[
                self.dashboard.event_processor_target
            ]
        )