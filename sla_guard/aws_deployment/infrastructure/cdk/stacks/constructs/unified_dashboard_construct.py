from aws_cdk import (
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_glue as glue,
    aws_athena as athena,
    aws_quicksight as quicksight,
    aws_iam as iam,
    aws_events_targets as targets,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class UnifiedDashboardConstruct(Construct):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        data_lake_bucket: s3.Bucket,
        sla_guard_table: dynamodb.Table,
        l1_task_table: dynamodb.Table,
        asset_table: dynamodb.Table
    ) -> None:
        super().__init__(scope, construct_id)

        # Glue Database for analytics
        self.glue_database = glue.CfnDatabase(
            self, "ServiceEfficiencyDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="service_efficiency_analytics",
                description="Unified analytics database for service efficiency platform"
            )
        )

        # Glue Tables for each data source
        self._create_glue_tables(data_lake_bucket)

        # ETL Lambda for data processing
        self.etl_processor = self._create_etl_processor(
            data_lake_bucket, sla_guard_table, l1_task_table, asset_table
        )

        # Dashboard event processor
        self.dashboard_processor = self._create_dashboard_processor(data_lake_bucket)

        # QuickSight resources
        self._create_quicksight_resources(data_lake_bucket)

        # Expose target for EventBridge
        self.event_processor_target = targets.LambdaFunction(self.dashboard_processor)

    def _create_glue_tables(self, data_lake_bucket: s3.Bucket):
        """Create Glue tables for analytics"""
        
        # SLA Metrics Table
        self.sla_metrics_table = glue.CfnTable(
            self, "SLAMetricsTable",
            catalog_id=self.account,
            database_name=self.glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="sla_metrics",
                description="SLA metrics and predictions",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "json",
                    "compressionType": "gzip"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=[
                        glue.CfnTable.ColumnProperty(name="ticket_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="priority", type="int"),
                        glue.CfnTable.ColumnProperty(name="category", type="string"),
                        glue.CfnTable.ColumnProperty(name="status", type="string"),
                        glue.CfnTable.ColumnProperty(name="breach_probability", type="double"),
                        glue.CfnTable.ColumnProperty(name="sla_status", type="string"),
                        glue.CfnTable.ColumnProperty(name="response_remaining_minutes", type="double"),
                        glue.CfnTable.ColumnProperty(name="resolution_remaining_minutes", type="double"),
                        glue.CfnTable.ColumnProperty(name="created_at", type="timestamp"),
                        glue.CfnTable.ColumnProperty(name="calculated_at", type="timestamp")
                    ],
                    location=f"s3://{data_lake_bucket.bucket_name}/processed/sla-metrics/",
                    input_format="org.apache.hadoop.mapred.TextInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.openx.data.jsonserde.JsonSerDe"
                    )
                ),
                partition_keys=[
                    glue.CfnTable.ColumnProperty(name="year", type="string"),
                    glue.CfnTable.ColumnProperty(name="month", type="string"),
                    glue.CfnTable.ColumnProperty(name="day", type="string")
                ]
            )
        )

        # L1 Automation Metrics Table
        self.l1_metrics_table = glue.CfnTable(
            self, "L1MetricsTable",
            catalog_id=self.account,
            database_name=self.glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="l1_automation_metrics",
                description="L1 automation performance metrics",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "json",
                    "compressionType": "gzip"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=[
                        glue.CfnTable.ColumnProperty(name="task_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="ticket_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="task_type", type="string"),
                        glue.CfnTable.ColumnProperty(name="status", type="string"),
                        glue.CfnTable.ColumnProperty(name="execution_time_seconds", type="double"),
                        glue.CfnTable.ColumnProperty(name="success", type="boolean"),
                        glue.CfnTable.ColumnProperty(name="time_saved_minutes", type="double"),
                        glue.CfnTable.ColumnProperty(name="started_at", type="timestamp"),
                        glue.CfnTable.ColumnProperty(name="completed_at", type="timestamp")
                    ],
                    location=f"s3://{data_lake_bucket.bucket_name}/processed/l1-automation/",
                    input_format="org.apache.hadoop.mapred.TextInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.openx.data.jsonserde.JsonSerDe"
                    )
                ),
                partition_keys=[
                    glue.CfnTable.ColumnProperty(name="year", type="string"),
                    glue.CfnTable.ColumnProperty(name="month", type="string"),
                    glue.CfnTable.ColumnProperty(name="day", type="string")
                ]
            )
        )

        # Asset Optimization Metrics Table
        self.asset_metrics_table = glue.CfnTable(
            self, "AssetMetricsTable",
            catalog_id=self.account,
            database_name=self.glue_database.ref,
            table_input=glue.CfnTable.TableInputProperty(
                name="asset_optimization_metrics",
                description="Asset and license optimization metrics",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "json",
                    "compressionType": "gzip"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=[
                        glue.CfnTable.ColumnProperty(name="optimization_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="asset_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="optimization_type", type="string"),
                        glue.CfnTable.ColumnProperty(name="potential_savings", type="double"),
                        glue.CfnTable.ColumnProperty(name="actual_savings", type="double"),
                        glue.CfnTable.ColumnProperty(name="status", type="string"),
                        glue.CfnTable.ColumnProperty(name="roi_percentage", type="double"),
                        glue.CfnTable.ColumnProperty(name="created_at", type="timestamp"),
                        glue.CfnTable.ColumnProperty(name="implemented_at", type="timestamp")
                    ],
                    location=f"s3://{data_lake_bucket.bucket_name}/processed/asset-optimization/",
                    input_format="org.apache.hadoop.mapred.TextInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.openx.data.jsonserde.JsonSerDe"
                    )
                ),
                partition_keys=[
                    glue.CfnTable.ColumnProperty(name="year", type="string"),
                    glue.CfnTable.ColumnProperty(name="month", type="string"),
                    glue.CfnTable.ColumnProperty(name="day", type="string")
                ]
            )
        )

    def _create_etl_processor(
        self, 
        data_lake_bucket: s3.Bucket,
        sla_guard_table: dynamodb.Table,
        l1_task_table: dynamodb.Table,
        asset_table: dynamodb.Table
    ) -> lambda_.Function:
        """Create ETL processor Lambda"""
        
        etl_role = iam.Role(
            self, "ETLProcessorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "ETLPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:Scan",
                                "dynamodb:Query",
                                "dynamodb:GetItem"
                            ],
                            resources=[
                                sla_guard_table.table_arn,
                                l1_task_table.table_arn,
                                asset_table.table_arn,
                                f"{sla_guard_table.table_arn}/index/*",
                                f"{l1_task_table.table_arn}/index/*",
                                f"{asset_table.table_arn}/index/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:PutObject",
                                "s3:GetObject",
                                "s3:DeleteObject"
                            ],
                            resources=[f"{data_lake_bucket.bucket_arn}/*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "glue:GetTable",
                                "glue:GetPartitions",
                                "glue:CreatePartition"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        return lambda_.Function(
            self, "ETLProcessor",
            function_name="service-efficiency-etl-processor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="etl_processor.handler",
            code=lambda_.Code.from_asset("src/dashboard"),
            role=etl_role,
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment={
                "SLA_GUARD_TABLE": sla_guard_table.table_name,
                "L1_TASK_TABLE": l1_task_table.table_name,
                "ASSET_TABLE": asset_table.table_name,
                "DATA_LAKE_BUCKET": data_lake_bucket.bucket_name,
                "GLUE_DATABASE": self.glue_database.ref
            },
            tracing=lambda_.Tracing.ACTIVE
        )

    def _create_dashboard_processor(self, data_lake_bucket: s3.Bucket) -> lambda_.Function:
        """Create dashboard event processor Lambda"""
        
        dashboard_role = iam.Role(
            self, "DashboardProcessorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "DashboardPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:PutObject",
                                "s3:GetObject"
                            ],
                            resources=[f"{data_lake_bucket.bucket_arn}/*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "quicksight:UpdateDashboard",
                                "quicksight:RefreshDataSet"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        return lambda_.Function(
            self, "DashboardProcessor",
            function_name="service-efficiency-dashboard-processor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="dashboard_processor.handler",
            code=lambda_.Code.from_asset("src/dashboard"),
            role=dashboard_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "DATA_LAKE_BUCKET": data_lake_bucket.bucket_name
            },
            tracing=lambda_.Tracing.ACTIVE
        )

    def _create_quicksight_resources(self, data_lake_bucket: s3.Bucket):
        """Create QuickSight resources"""
        
        # QuickSight Data Source
        self.quicksight_data_source = quicksight.CfnDataSource(
            self, "ServiceEfficiencyDataSource",
            aws_account_id=self.account,
            data_source_id="service-efficiency-athena-source",
            name="Service Efficiency Analytics",
            type="ATHENA",
            data_source_parameters=quicksight.CfnDataSource.DataSourceParametersProperty(
                athena_parameters=quicksight.CfnDataSource.AthenaParametersProperty(
                    work_group="primary"
                )
            ),
            permissions=[
                quicksight.CfnDataSource.ResourcePermissionProperty(
                    principal=f"arn:aws:quicksight:{self.region}:{self.account}:user/default/admin",
                    actions=[
                        "quicksight:DescribeDataSource",
                        "quicksight:DescribeDataSourcePermissions",
                        "quicksight:PassDataSource",
                        "quicksight:UpdateDataSource",
                        "quicksight:DeleteDataSource"
                    ]
                )
            ]
        )

        # QuickSight Data Sets
        self._create_quicksight_datasets()

        # QuickSight Dashboard
        self._create_quicksight_dashboard()

    def _create_quicksight_datasets(self):
        """Create QuickSight datasets"""
        
        # SLA Performance Dataset
        self.sla_dataset = quicksight.CfnDataSet(
            self, "SLAPerformanceDataSet",
            aws_account_id=self.account,
            data_set_id="sla-performance-dataset",
            name="SLA Performance Metrics",
            import_mode="DIRECT_QUERY",
            physical_table_map={
                "sla_metrics": quicksight.CfnDataSet.PhysicalTableProperty(
                    relational_table=quicksight.CfnDataSet.RelationalTableProperty(
                        data_source_arn=self.quicksight_data_source.attr_arn,
                        catalog="AwsDataCatalog",
                        schema=self.glue_database.ref,
                        name="sla_metrics"
                    )
                )
            },
            permissions=[
                quicksight.CfnDataSet.ResourcePermissionProperty(
                    principal=f"arn:aws:quicksight:{self.region}:{self.account}:user/default/admin",
                    actions=[
                        "quicksight:DescribeDataSet",
                        "quicksight:DescribeDataSetPermissions",
                        "quicksight:PassDataSet",
                        "quicksight:DescribeIngestion",
                        "quicksight:ListIngestions",
                        "quicksight:UpdateDataSet",
                        "quicksight:DeleteDataSet",
                        "quicksight:CreateIngestion",
                        "quicksight:CancelIngestion"
                    ]
                )
            ]
        )

        # L1 Automation Dataset
        self.l1_dataset = quicksight.CfnDataSet(
            self, "L1AutomationDataSet",
            aws_account_id=self.account,
            data_set_id="l1-automation-dataset",
            name="L1 Automation Metrics",
            import_mode="DIRECT_QUERY",
            physical_table_map={
                "l1_metrics": quicksight.CfnDataSet.PhysicalTableProperty(
                    relational_table=quicksight.CfnDataSet.RelationalTableProperty(
                        data_source_arn=self.quicksight_data_source.attr_arn,
                        catalog="AwsDataCatalog",
                        schema=self.glue_database.ref,
                        name="l1_automation_metrics"
                    )
                )
            },
            permissions=[
                quicksight.CfnDataSet.ResourcePermissionProperty(
                    principal=f"arn:aws:quicksight:{self.region}:{self.account}:user/default/admin",
                    actions=[
                        "quicksight:DescribeDataSet",
                        "quicksight:DescribeDataSetPermissions",
                        "quicksight:PassDataSet",
                        "quicksight:DescribeIngestion",
                        "quicksight:ListIngestions",
                        "quicksight:UpdateDataSet",
                        "quicksight:DeleteDataSet",
                        "quicksight:CreateIngestion",
                        "quicksight:CancelIngestion"
                    ]
                )
            ]
        )

        # Asset Optimization Dataset
        self.asset_dataset = quicksight.CfnDataSet(
            self, "AssetOptimizationDataSet",
            aws_account_id=self.account,
            data_set_id="asset-optimization-dataset",
            name="Asset Optimization Metrics",
            import_mode="DIRECT_QUERY",
            physical_table_map={
                "asset_metrics": quicksight.CfnDataSet.PhysicalTableProperty(
                    relational_table=quicksight.CfnDataSet.RelationalTableProperty(
                        data_source_arn=self.quicksight_data_source.attr_arn,
                        catalog="AwsDataCatalog",
                        schema=self.glue_database.ref,
                        name="asset_optimization_metrics"
                    )
                )
            },
            permissions=[
                quicksight.CfnDataSet.ResourcePermissionProperty(
                    principal=f"arn:aws:quicksight:{self.region}:{self.account}:user/default/admin",
                    actions=[
                        "quicksight:DescribeDataSet",
                        "quicksight:DescribeDataSetPermissions",
                        "quicksight:PassDataSet",
                        "quicksight:DescribeIngestion",
                        "quicksight:ListIngestions",
                        "quicksight:UpdateDataSet",
                        "quicksight:DeleteDataSet",
                        "quicksight:CreateIngestion",
                        "quicksight:CancelIngestion"
                    ]
                )
            ]
        )

    def _create_quicksight_dashboard(self):
        """Create QuickSight dashboard"""
        
        # Executive Dashboard
        self.executive_dashboard = quicksight.CfnDashboard(
            self, "ExecutiveDashboard",
            aws_account_id=self.account,
            dashboard_id="service-efficiency-executive",
            name="Service Efficiency - Executive View",
            definition=quicksight.CfnDashboard.DashboardVersionDefinitionProperty(
                data_set_identifiers_declarations=[
                    quicksight.CfnDashboard.DataSetIdentifierDeclarationProperty(
                        data_set_arn=self.sla_dataset.attr_arn,
                        identifier="sla_data"
                    ),
                    quicksight.CfnDashboard.DataSetIdentifierDeclarationProperty(
                        data_set_arn=self.l1_dataset.attr_arn,
                        identifier="l1_data"
                    ),
                    quicksight.CfnDashboard.DataSetIdentifierDeclarationProperty(
                        data_set_arn=self.asset_dataset.attr_arn,
                        identifier="asset_data"
                    )
                ],
                sheets=[
                    quicksight.CfnDashboard.SheetDefinitionProperty(
                        sheet_id="executive-summary",
                        name="Executive Summary",
                        visuals=[
                            # SLA Compliance KPI
                            quicksight.CfnDashboard.VisualProperty(
                                kpi_visual=quicksight.CfnDashboard.KPIVisualProperty(
                                    visual_id="sla-compliance-kpi",
                                    title=quicksight.CfnDashboard.VisualTitleLabelOptionsProperty(
                                        visibility="VISIBLE",
                                        format_text=quicksight.CfnDashboard.ShortFormatTextProperty(
                                            plain_text="SLA Compliance"
                                        )
                                    ),
                                    field_wells=quicksight.CfnDashboard.KPIFieldWellsProperty(
                                        values=[
                                            quicksight.CfnDashboard.MeasureFieldProperty(
                                                numerical_measure_field=quicksight.CfnDashboard.NumericalMeasureFieldProperty(
                                                    field_id="sla_compliance_rate",
                                                    column=quicksight.CfnDashboard.ColumnIdentifierProperty(
                                                        data_set_identifier="sla_data",
                                                        column_name="sla_status"
                                                    ),
                                                    aggregation_function=quicksight.CfnDashboard.NumericalAggregationFunctionProperty(
                                                        simple_numerical_aggregation="AVERAGE"
                                                    )
                                                )
                                            )
                                        ]
                                    )
                                )
                            ),
                            # Automation Success Rate KPI
                            quicksight.CfnDashboard.VisualProperty(
                                kpi_visual=quicksight.CfnDashboard.KPIVisualProperty(
                                    visual_id="automation-success-kpi",
                                    title=quicksight.CfnDashboard.VisualTitleLabelOptionsProperty(
                                        visibility="VISIBLE",
                                        format_text=quicksight.CfnDashboard.ShortFormatTextProperty(
                                            plain_text="Automation Success Rate"
                                        )
                                    ),
                                    field_wells=quicksight.CfnDashboard.KPIFieldWellsProperty(
                                        values=[
                                            quicksight.CfnDashboard.MeasureFieldProperty(
                                                numerical_measure_field=quicksight.CfnDashboard.NumericalMeasureFieldProperty(
                                                    field_id="automation_success_rate",
                                                    column=quicksight.CfnDashboard.ColumnIdentifierProperty(
                                                        data_set_identifier="l1_data",
                                                        column_name="success"
                                                    ),
                                                    aggregation_function=quicksight.CfnDashboard.NumericalAggregationFunctionProperty(
                                                        simple_numerical_aggregation="AVERAGE"
                                                    )
                                                )
                                            )
                                        ]
                                    )
                                )
                            ),
                            # Cost Savings KPI
                            quicksight.CfnDashboard.VisualProperty(
                                kpi_visual=quicksight.CfnDashboard.KPIVisualProperty(
                                    visual_id="cost-savings-kpi",
                                    title=quicksight.CfnDashboard.VisualTitleLabelOptionsProperty(
                                        visibility="VISIBLE",
                                        format_text=quicksight.CfnDashboard.ShortFormatTextProperty(
                                            plain_text="Monthly Cost Savings"
                                        )
                                    ),
                                    field_wells=quicksight.CfnDashboard.KPIFieldWellsProperty(
                                        values=[
                                            quicksight.CfnDashboard.MeasureFieldProperty(
                                                numerical_measure_field=quicksight.CfnDashboard.NumericalMeasureFieldProperty(
                                                    field_id="monthly_savings",
                                                    column=quicksight.CfnDashboard.ColumnIdentifierProperty(
                                                        data_set_identifier="asset_data",
                                                        column_name="actual_savings"
                                                    ),
                                                    aggregation_function=quicksight.CfnDashboard.NumericalAggregationFunctionProperty(
                                                        simple_numerical_aggregation="SUM"
                                                    )
                                                )
                                            )
                                        ]
                                    )
                                )
                            )
                        ]
                    )
                ]
            ),
            permissions=[
                quicksight.CfnDashboard.ResourcePermissionProperty(
                    principal=f"arn:aws:quicksight:{self.region}:{self.account}:user/default/admin",
                    actions=[
                        "quicksight:DescribeDashboard",
                        "quicksight:ListDashboardVersions",
                        "quicksight:UpdateDashboardPermissions",
                        "quicksight:QueryDashboard",
                        "quicksight:UpdateDashboard",
                        "quicksight:DeleteDashboard",
                        "quicksight:DescribeDashboardPermissions",
                        "quicksight:UpdateDashboardPublishedVersion"
                    ]
                )
            ]
        )