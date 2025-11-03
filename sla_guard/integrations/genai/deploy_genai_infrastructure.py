#!/usr/bin/env python3
"""
Deploy Complete AWS GenAI Infrastructure
Sets up: DynamoDB → EventBridge → Lambda → SageMaker → SNS → QuickSight

This script deploys all the AWS infrastructure needed for the complete GenAI workflow:
1. DynamoDB table with EventBridge integration
2. EventBridge rules and targets
3. Lambda function for ML predictions
4. SNS topic for alerts
5. IAM roles and permissions
6. QuickSight dataset configuration
"""

import boto3
import json
import time
import zipfile
import io
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenAIInfrastructureDeployer:
    def __init__(self, region='us-east-1', account_id=None):
        """Initialize AWS clients for infrastructure deployment"""
        self.region = region
        self.account_id = account_id or boto3.client('sts').get_caller_identity()['Account']
        
        # Initialize AWS clients
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.events = boto3.client('events', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.quicksight = boto3.client('quicksight', region_name=region)
        
        # Resource names
        self.table_name = 'sla-guard-tickets'
        self.lambda_function_name = 'sla-guard-ml-predictor'
        self.sns_topic_name = 'sla-alerts'
        self.eventbridge_rule_name = 'sla-guard-ticket-events'
        self.iam_role_name = 'sla-guard-lambda-role'
        
        logger.info(f"🚀 GenAI Infrastructure Deployer initialized")
        logger.info(f"   Region: {region}")
        logger.info(f"   Account: {self.account_id}")

    def deploy_complete_infrastructure(self):
        """Deploy all infrastructure components"""
        logger.info("🏗️ Starting complete GenAI infrastructure deployment...")
        
        deployment_steps = [
            ("IAM Role", self.create_iam_role),
            ("DynamoDB Table", self.create_dynamodb_table),
            ("SNS Topic", self.create_sns_topic),
            ("Lambda Function", self.deploy_lambda_function),
            ("EventBridge Rule", self.create_eventbridge_rule),
            ("QuickSight Dataset", self.setup_quicksight_dataset)
        ]
        
        results = {}
        
        for step_name, step_function in deployment_steps:
            try:
                logger.info(f"📦 Deploying {step_name}...")
                result = step_function()
                results[step_name] = {'status': 'SUCCESS', 'result': result}
                logger.info(f"✅ {step_name} deployed successfully")
                time.sleep(2)  # Brief pause between deployments
            except Exception as e:
                logger.error(f"❌ {step_name} deployment failed: {str(e)}")
                results[step_name] = {'status': 'FAILED', 'error': str(e)}
        
        # Summary
        self.print_deployment_summary(results)
        return results

    def create_iam_role(self):
        """Create IAM role for Lambda function"""
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
        
        # Create role
        try:
            response = self.iam.create_role(
                RoleName=self.iam_role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='IAM role for SLA Guard Lambda ML predictor'
            )
            role_arn = response['Role']['Arn']
        except self.iam.exceptions.EntityAlreadyExistsException:
            response = self.iam.get_role(RoleName=self.iam_role_name)
            role_arn = response['Role']['Arn']
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
            'arn:aws:iam::aws:policy/AmazonSNSFullAccess',
            'arn:aws:iam::aws:policy/AmazonSageMakerReadOnly'
        ]
        
        for policy_arn in policies:
            try:
                self.iam.attach_role_policy(
                    RoleName=self.iam_role_name,
                    PolicyArn=policy_arn
                )
            except Exception as e:
                logger.warning(f"Policy attach warning: {str(e)}")
        
        # Custom policy for Bedrock and Comprehend
        custom_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "comprehend:DetectSentiment",
                        "comprehend:DetectEntities",
                        "comprehend:DetectKeyPhrases",
                        "sagemaker:InvokeEndpoint"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            self.iam.put_role_policy(
                RoleName=self.iam_role_name,
                PolicyName='SLAGuardGenAIPolicy',
                PolicyDocument=json.dumps(custom_policy)
            )
        except Exception as e:
            logger.warning(f"Custom policy warning: {str(e)}")
        
        return role_arn

    def create_dynamodb_table(self):
        """Create DynamoDB table with EventBridge integration"""
        table_schema = {
            'TableName': self.table_name,
            'KeySchema': [
                {'AttributeName': 'ticket_id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'ticket_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'},
                {'AttributeName': 'priority', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'priority-created-index',
                    'KeySchema': [
                        {'AttributeName': 'priority', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            'StreamSpecification': {
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            },
            'Tags': [
                {'Key': 'Project', 'Value': 'SLAGuard'},
                {'Key': 'Component', 'Value': 'GenAI-Workflow'}
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_schema)
            table_arn = response['TableDescription']['TableArn']
            
            # Wait for table to be active
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name)
            
        except self.dynamodb.exceptions.ResourceInUseException:
            response = self.dynamodb.describe_table(TableName=self.table_name)
            table_arn = response['Table']['TableArn']
        
        return table_arn

    def create_sns_topic(self):
        """Create SNS topic for alerts"""
        try:
            response = self.sns.create_topic(Name=self.sns_topic_name)
            topic_arn = response['TopicArn']
            
            # Set topic attributes
            self.sns.set_topic_attributes(
                TopicArn=topic_arn,
                AttributeName='DisplayName',
                AttributeValue='SLA Guard Alerts'
            )
            
            return topic_arn
            
        except Exception as e:
            # Topic might already exist
            topics = self.sns.list_topics()
            for topic in topics['Topics']:
                if self.sns_topic_name in topic['TopicArn']:
                    return topic['TopicArn']
            raise e

    def deploy_lambda_function(self):
        """Deploy Lambda function for ML predictions"""
        
        # Create deployment package
        lambda_code = self._create_lambda_deployment_package()
        
        # Get IAM role ARN
        role_response = self.iam.get_role(RoleName=self.iam_role_name)
        role_arn = role_response['Role']['Arn']
        
        function_config = {
            'FunctionName': self.lambda_function_name,
            'Runtime': 'python3.9',
            'Role': role_arn,
            'Handler': 'lambda_ml_predictor.lambda_handler',
            'Code': {'ZipFile': lambda_code},
            'Description': 'SLA Guard ML Predictor for GenAI workflow',
            'Timeout': 300,
            'MemorySize': 512,
            'Environment': {
                'Variables': {
                    'TICKETS_TABLE': self.table_name,
                    'SNS_TOPIC_ARN': f'arn:aws:sns:{self.region}:{self.account_id}:{self.sns_topic_name}',
                    'SAGEMAKER_ENDPOINT': 'sla-breach-predictor'
                }
            },
            'Tags': {
                'Project': 'SLAGuard',
                'Component': 'GenAI-ML-Predictor'
            }
        }
        
        try:
            response = self.lambda_client.create_function(**function_config)
            function_arn = response['FunctionArn']
        except self.lambda_client.exceptions.ResourceConflictException:
            # Update existing function
            self.lambda_client.update_function_code(
                FunctionName=self.lambda_function_name,
                ZipFile=lambda_code
            )
            response = self.lambda_client.get_function(FunctionName=self.lambda_function_name)
            function_arn = response['Configuration']['FunctionArn']
        
        return function_arn

    def _create_lambda_deployment_package(self):
        """Create Lambda deployment package"""
        # Read the Lambda function code
        with open('lambda_ml_predictor.py', 'r') as f:
            lambda_code = f.read()
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_ml_predictor.py', lambda_code)
        
        return zip_buffer.getvalue()

    def create_eventbridge_rule(self):
        """Create EventBridge rule to trigger Lambda"""
        
        # Create EventBridge rule
        rule_config = {
            'Name': self.eventbridge_rule_name,
            'EventPattern': json.dumps({
                'source': ['sla-guard.tickets'],
                'detail-type': ['New Ticket Created']
            }),
            'State': 'ENABLED',
            'Description': 'Trigger ML prediction for new SLA Guard tickets'
        }
        
        try:
            response = self.events.put_rule(**rule_config)
            rule_arn = response['RuleArn']
        except Exception as e:
            logger.warning(f"EventBridge rule creation warning: {str(e)}")
            # Get existing rule
            response = self.events.describe_rule(Name=self.eventbridge_rule_name)
            rule_arn = response['Arn']
        
        # Add Lambda target
        function_arn = f'arn:aws:lambda:{self.region}:{self.account_id}:function:{self.lambda_function_name}'
        
        try:
            self.events.put_targets(
                Rule=self.eventbridge_rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': function_arn
                    }
                ]
            )
            
            # Add permission for EventBridge to invoke Lambda
            try:
                self.lambda_client.add_permission(
                    FunctionName=self.lambda_function_name,
                    StatementId='AllowEventBridgeInvoke',
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=rule_arn
                )
            except Exception as e:
                logger.warning(f"Lambda permission warning: {str(e)}")
                
        except Exception as e:
            logger.warning(f"EventBridge target warning: {str(e)}")
        
        return rule_arn

    def setup_quicksight_dataset(self):
        """Setup QuickSight dataset for visualization"""
        try:
            # This is a placeholder - QuickSight setup requires manual configuration
            # or more complex API calls depending on your QuickSight setup
            logger.info("📊 QuickSight dataset setup - manual configuration required")
            
            dataset_config = {
                'name': 'sla-guard-tickets-dataset',
                'source': f'DynamoDB table: {self.table_name}',
                'region': self.region,
                'account': self.account_id
            }
            
            return dataset_config
            
        except Exception as e:
            logger.warning(f"QuickSight setup warning: {str(e)}")
            return {'status': 'manual_setup_required'}

    def print_deployment_summary(self, results):
        """Print deployment summary"""
        print("\n" + "="*60)
        print("🚀 AWS GenAI Infrastructure Deployment Summary")
        print("="*60)
        
        success_count = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
        total_count = len(results)
        
        print(f"📊 Overall Status: {success_count}/{total_count} components deployed successfully")
        print()
        
        for component, result in results.items():
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"{status_icon} {component}: {result['status']}")
            if result['status'] == 'FAILED':
                print(f"   Error: {result['error']}")
        
        print("\n🔗 Resource ARNs:")
        print(f"   DynamoDB Table: arn:aws:dynamodb:{self.region}:{self.account_id}:table/{self.table_name}")
        print(f"   Lambda Function: arn:aws:lambda:{self.region}:{self.account_id}:function/{self.lambda_function_name}")
        print(f"   SNS Topic: arn:aws:sns:{self.region}:{self.account_id}:{self.sns_topic_name}")
        print(f"   EventBridge Rule: arn:aws:events:{self.region}:{self.account_id}:rule/{self.eventbridge_rule_name}")
        
        print("\n🎯 Next Steps:")
        print("1. Configure AWS Bedrock access for Claude 3 Sonnet")
        print("2. Set up SageMaker endpoint for breach prediction")
        print("3. Subscribe to SNS topic for alerts")
        print("4. Configure QuickSight dashboard manually")
        print("5. Test the complete workflow")
        
        print("\n🧪 Test Command:")
        print("python complete_genai_workflow.py")

    def cleanup_infrastructure(self):
        """Clean up all deployed resources"""
        logger.info("🧹 Cleaning up GenAI infrastructure...")
        
        cleanup_steps = [
            ("EventBridge Rule", lambda: self.events.delete_rule(Name=self.eventbridge_rule_name, Force=True)),
            ("Lambda Function", lambda: self.lambda_client.delete_function(FunctionName=self.lambda_function_name)),
            ("SNS Topic", lambda: self.sns.delete_topic(TopicArn=f'arn:aws:sns:{self.region}:{self.account_id}:{self.sns_topic_name}')),
            ("DynamoDB Table", lambda: self.dynamodb.delete_table(TableName=self.table_name)),
            ("IAM Role", self._cleanup_iam_role)
        ]
        
        for step_name, cleanup_func in cleanup_steps:
            try:
                cleanup_func()
                logger.info(f"✅ {step_name} cleaned up")
            except Exception as e:
                logger.warning(f"⚠️ {step_name} cleanup warning: {str(e)}")

    def _cleanup_iam_role(self):
        """Clean up IAM role and policies"""
        # Detach policies
        try:
            policies = self.iam.list_attached_role_policies(RoleName=self.iam_role_name)
            for policy in policies['AttachedPolicies']:
                self.iam.detach_role_policy(
                    RoleName=self.iam_role_name,
                    PolicyArn=policy['PolicyArn']
                )
        except Exception as e:
            logger.warning(f"Policy detach warning: {str(e)}")
        
        # Delete inline policies
        try:
            inline_policies = self.iam.list_role_policies(RoleName=self.iam_role_name)
            for policy_name in inline_policies['PolicyNames']:
                self.iam.delete_role_policy(
                    RoleName=self.iam_role_name,
                    PolicyName=policy_name
                )
        except Exception as e:
            logger.warning(f"Inline policy cleanup warning: {str(e)}")
        
        # Delete role
        self.iam.delete_role(RoleName=self.iam_role_name)


def main():
    """Main deployment function"""
    print("🚀 AWS GenAI Infrastructure Deployment")
    print("=" * 50)
    
    import argparse
    parser = argparse.ArgumentParser(description='Deploy AWS GenAI Infrastructure')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--cleanup', action='store_true', help='Clean up resources instead of deploying')
    
    args = parser.parse_args()
    
    deployer = GenAIInfrastructureDeployer(region=args.region)
    
    if args.cleanup:
        deployer.cleanup_infrastructure()
        print("🧹 Cleanup completed!")
    else:
        results = deployer.deploy_complete_infrastructure()
        
        if all(r['status'] == 'SUCCESS' for r in results.values()):
            print("\n🎉 All infrastructure deployed successfully!")
        else:
            print("\n⚠️ Some components failed to deploy. Check logs above.")

if __name__ == "__main__":
    main()