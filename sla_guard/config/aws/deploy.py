#!/usr/bin/env python3
"""
Complete AWS Deployment Script for SLA Guard Agent
Deploys all components with proper error handling and validation
"""

import boto3
import json
import os
import zipfile
import tempfile
import shutil
import time
from datetime import datetime
from decimal import Decimal

# AWS Profile Configuration
AWS_PROFILE = "AdministratorAccess-508955320780"
os.environ['AWS_PROFILE'] = AWS_PROFILE

class SLAGuardDeployer:
    def __init__(self):
        self.session = boto3.Session(profile_name=AWS_PROFILE)
        self.account_id = self.session.client('sts').get_caller_identity()['Account']
        #self.region = self.session.region_name or 'us-east-2'
        self.region = 'us-east-1'
        
        print(f"🚀 SLA Guard Agent Deployment")
        print(f"   Account: {self.account_id}")
        print(f"   Region: {self.region}")
        print(f"   Profile: {AWS_PROFILE}")
        print("=" * 50)
    
    def deploy_all(self):
        """Deploy all components in correct order"""
        
        try:
            # Step 1: Create basic AWS resources
            print("📦 Step 1: Creating basic AWS resources...")
            self.create_basic_resources()
            
            # Step 2: Deploy Lambda functions
            print("\n🔧 Step 2: Deploying Lambda functions...")
            self.deploy_lambda_functions()
            
            # Step 3: Create shared configuration
            print("\n⚙️  Step 3: Creating shared configuration...")
            self.create_shared_config()
            
            # Step 4: Verify deployment
            print("\n✅ Step 4: Verifying deployment...")
            self.verify_deployment()
            
            print("\n🎉 Deployment Complete!")
            print("=" * 30)
            print("✅ SLA Guard Agent is ready for production!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            return False
    
    def create_basic_resources(self):
        """Create S3, DynamoDB, and EventBridge resources"""
        
        # Create S3 bucket
        s3_client = self.session.client('s3', region_name=self.region)
        bucket_name = f"service-efficiency-data-lake-{self.account_id}"
        
        try:
            print(f"   Creating S3 bucket: {bucket_name}")
            if self.region == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            print(f"   ✅ S3 bucket created")
        except s3_client.exceptions.BucketAlreadyOwnedByYou:
            print(f"   ✅ S3 bucket already exists")
        
        # Create DynamoDB table
        dynamodb = self.session.resource('dynamodb', region_name=self.region)
        table_name = "sla-guard-state"
        
        try:
            print(f"   Creating DynamoDB table: {table_name}")
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'service_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'service_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'},
                    {'AttributeName': 'breach_probability_bucket', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'breach-probability-index',
                        'KeySchema': [
                            {'AttributeName': 'breach_probability_bucket', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            )
            table.wait_until_exists()
            print(f"   ✅ DynamoDB table created")
        except dynamodb.meta.client.exceptions.ResourceInUseException:
            print(f"   ✅ DynamoDB table already exists")
        
        # Create EventBridge bus
        events_client = self.session.client('events', region_name=self.region)
        bus_name = "service-efficiency-platform"
        
        try:
            print(f"   Creating EventBridge bus: {bus_name}")
            events_client.create_event_bus(Name=bus_name)
            print(f"   ✅ EventBridge bus created")
        except events_client.exceptions.ResourceAlreadyExistsException:
            print(f"   ✅ EventBridge bus already exists")
    
    def deploy_lambda_functions(self):
        """Deploy all Lambda functions"""
        
        lambda_client = self.session.client('lambda', region_name=self.region)
        iam_client = self.session.client('iam', region_name=self.region)
        
        # Create IAM role
        role_arn = self.create_lambda_role(iam_client)
        
        # Lambda functions to deploy
        functions = [
            {
                'name': 'sla-guard-metric-processor',
                'handler': 'metric_processor.handler',
                'description': 'SLA Guard metric processor - ingests and processes tickets'
            },
            {
                'name': 'sla-guard-breach-predictor',
                'handler': 'breach_predictor.handler',
                'description': 'SLA Guard breach predictor - ML-powered SLA breach prediction'
            },
            {
                'name': 'sla-guard-action-trigger',
                'handler': 'action_trigger.handler',
                'description': 'SLA Guard action trigger - executes preventive actions'
            },
            {
                'name': 'sla-guard-status-updater',
                'handler': 'status_updater.handler',
                'description': 'SLA Guard status updater - receives cross-agent updates'
            },
            {
                'name': 'sla-guard-impact-validator',
                'handler': 'impact_validator.handler',
                'description': 'SLA Guard impact validator - validates optimization impact'
            }
        ]
        
        # Create deployment package
        zip_content = self.create_deployment_package()
        
        # Deploy each function
        for func in functions:
            self.deploy_single_function(lambda_client, func, role_arn, zip_content)
    
    def create_lambda_role(self, iam_client):
        """Create IAM role for Lambda functions"""
        
        role_name = "SLAGuardLambdaRole"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:*:{self.account_id}:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:Query",
                        "dynamodb:UpdateItem",
                        "dynamodb:Scan"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:*:{self.account_id}:table/sla-guard-state",
                        f"arn:aws:dynamodb:*:{self.account_id}:table/sla-guard-state/index/*",
                        f"arn:aws:dynamodb:*:{self.account_id}:table/service-efficiency-shared-config"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": ["events:PutEvents"],
                    "Resource": f"arn:aws:events:*:{self.account_id}:event-bus/service-efficiency-platform"
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:PutObject"],
                    "Resource": f"arn:aws:s3:::service-efficiency-data-lake-{self.account_id}/*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["sagemaker:InvokeEndpoint"],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            print(f"   Creating IAM role: {role_name}")
            response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="IAM role for SLA Guard Lambda functions"
            )
            role_arn = response['Role']['Arn']
            
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="SLAGuardLambdaPolicy",
                PolicyDocument=json.dumps(permissions_policy)
            )
            
            print(f"   ✅ IAM role created")
            time.sleep(10)  # Wait for role propagation
            return role_arn
            
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"   ✅ IAM role already exists")
            return f"arn:aws:iam::{self.account_id}:role/{role_name}"
    
    def create_deployment_package(self):
        """Create deployment package for Lambda functions"""
        
        print(f"   Creating deployment package...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy Lambda function files
            src_dir = "lambda_functions"
            for file in os.listdir(src_dir):
                if file.endswith('.py'):
                    shutil.copy(os.path.join(src_dir, file), temp_dir)
            
            # Create zip file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zip_file:
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, temp_dir)
                            zf.write(file_path, arc_name)
                
                zip_content = open(zip_file.name, 'rb').read()
        
        print(f"   ✅ Deployment package created ({len(zip_content)} bytes)")
        return zip_content
    
    def deploy_single_function(self, lambda_client, func_config, role_arn, zip_content):
        """Deploy a single Lambda function"""
        
        environment = {
            'SLA_STATE_TABLE': 'sla-guard-state',
            'SHARED_CONFIG_TABLE': 'service-efficiency-shared-config',
            'EVENT_BUS_NAME': 'service-efficiency-platform',
            'DATA_LAKE_BUCKET': f'service-efficiency-data-lake-{self.account_id}',
            'SAGEMAKER_ENDPOINT': 'sla-predictor-endpoint'
        }
        
        try:
            print(f"   Deploying {func_config['name']}...")
            
            lambda_client.create_function(
                FunctionName=func_config['name'],
                Runtime='python3.11',
                Role=role_arn,
                Handler=func_config['handler'],
                Code={'ZipFile': zip_content},
                Description=func_config['description'],
                Timeout=60,
                MemorySize=512,
                Environment={'Variables': environment},
                TracingConfig={'Mode': 'Active'}
            )
            
            print(f"   ✅ {func_config['name']} deployed")
            
        except lambda_client.exceptions.ResourceConflictException:
            print(f"   ⚠️  {func_config['name']} exists, updating...")
            
            lambda_client.update_function_code(
                FunctionName=func_config['name'],
                ZipFile=zip_content
            )
            
            print(f"   ✅ {func_config['name']} updated")
    
    def create_shared_config(self):
        """Create shared configuration table and populate it"""
        
        dynamodb = self.session.resource('dynamodb')
        table_name = "service-efficiency-shared-config"
        
        try:
            print(f"   Creating shared config table: {table_name}")
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'config_key', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'config_key', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            print(f"   ✅ Shared config table created")
        except dynamodb.meta.client.exceptions.ResourceInUseException:
            print(f"   ✅ Shared config table already exists")
            table = dynamodb.Table(table_name)
        
        # Populate configuration
        self.populate_config(table)
    
    def populate_config(self, table):
        """Populate configuration table"""
        
        print(f"   Populating configuration...")
        
        # SLA thresholds
        sla_config = {
            'priority_1': {'response_time': 15, 'resolution_time': 240},
            'priority_2': {'response_time': 60, 'resolution_time': 480},
            'priority_3': {'response_time': 240, 'resolution_time': 1440},
            'priority_4': {'response_time': 480, 'resolution_time': 2880},
            'target_adherence': Decimal('0.95')
        }
        
        table.put_item(
            Item={
                'config_key': 'sla_thresholds',
                'config_value': sla_config,
                'description': 'SLA response and resolution time thresholds by priority',
                'updated_at': datetime.utcnow().isoformat()
            }
        )
        
        # ML model configuration
        ml_config = {
            'model_endpoint': 'sla-predictor-endpoint',
            'confidence_threshold': Decimal('0.6'),
            'feature_count': 15,
            'model_version': 'v1.0'
        }
        
        table.put_item(
            Item={
                'config_key': 'ml_model_config',
                'config_value': ml_config,
                'description': 'ML model configuration for breach prediction',
                'updated_at': datetime.utcnow().isoformat()
            }
        )
        
        print(f"   ✅ Configuration populated")
    
    def verify_deployment(self):
        """Verify all components are deployed correctly"""
        
        # Check Lambda functions
        lambda_client = self.session.client('lambda')
        functions = [
            'sla-guard-metric-processor',
            'sla-guard-breach-predictor',
            'sla-guard-action-trigger',
            'sla-guard-status-updater',
            'sla-guard-impact-validator'
        ]
        
        lambda_count = 0
        for func_name in functions:
            try:
                lambda_client.get_function(FunctionName=func_name)
                lambda_count += 1
            except:
                pass
        
        # Check DynamoDB tables
        dynamodb = self.session.resource('dynamodb')
        tables = ['sla-guard-state', 'service-efficiency-shared-config']
        
        table_count = 0
        for table_name in tables:
            try:
                table = dynamodb.Table(table_name)
                table.load()
                table_count += 1
            except:
                pass
        
        # Check EventBridge
        events_client = self.session.client('events')
        try:
            events_client.describe_event_bus(Name='service-efficiency-platform')
            eventbridge_ok = True
        except:
            eventbridge_ok = False
        
        # Check S3
        s3_client = self.session.client('s3')
        bucket_name = f"service-efficiency-data-lake-{self.account_id}"
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            s3_ok = True
        except:
            s3_ok = False
        
        # Summary
        total_resources = len(functions) + len(tables) + 1 + 1  # +1 for EventBridge, +1 for S3
        found_resources = lambda_count + table_count + (1 if eventbridge_ok else 0) + (1 if s3_ok else 0)
        
        print(f"   Resources deployed: {found_resources}/{total_resources}")
        
        if found_resources == total_resources:
            print(f"   🎉 ✅ FULLY DEPLOYED - Ready for testing!")
            return True
        else:
            print(f"   ⚠️  🟡 PARTIALLY DEPLOYED - Some resources missing")
            return False

def main():
    """Main deployment function"""
    
    try:
        deployer = SLAGuardDeployer()
        success = deployer.deploy_all()
        
        if success:
            print(f"\n🧪 Next Steps:")
            print(f"   1. Test the system: python3 test_aws_system.py")
            print(f"   2. Monitor logs: aws logs tail /aws/lambda/sla-guard-metric-processor --follow --profile {AWS_PROFILE}")
            print(f"   3. Check data: aws dynamodb scan --table-name sla-guard-state --max-items 5 --profile {AWS_PROFILE}")
        else:
            print(f"\n❌ Deployment failed. Check the errors above.")
            
    except Exception as e:
        print(f"\n💥 Deployment error: {e}")

if __name__ == "__main__":
    main()