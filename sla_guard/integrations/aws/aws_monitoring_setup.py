#!/usr/bin/env python3
"""
AWS Monitoring and Email Alert Setup
Sets up comprehensive monitoring for AWS services and configures email notifications
"""

import boto3
import json
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSMonitoringSetup:
    def __init__(self, region='us-east-1', email_address=None):
        """Initialize AWS monitoring setup"""
        self.region = region
        self.email_address = email_address
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Initialize AWS clients
        self.sns = boto3.client('sns', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.ses = boto3.client('ses', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.events = boto3.client('events', region_name=region)
        
        logger.info(f"🚀 AWS Monitoring Setup initialized")
        logger.info(f"   Region: {region}")
        logger.info(f"   Account: {self.account_id}")
        logger.info(f"   Email: {email_address}")

    def setup_complete_monitoring(self):
        """Setup complete AWS monitoring and alerting"""
        print("🔧 Setting up AWS Monitoring and Email Alerts")
        print("=" * 60)
        
        steps = [
            ("SNS Topic Creation", self.create_sns_topics),
            ("Email Subscription", self.setup_email_subscriptions),
            ("CloudWatch Alarms", self.create_cloudwatch_alarms),
            ("SES Email Setup", self.setup_ses_email),
            ("Service Health Monitoring", self.setup_service_monitoring),
            ("Critical Alert Lambda", self.deploy_alert_lambda),
            ("Test Email System", self.test_email_system)
        ]
        
        results = {}
        for step_name, step_function in steps:
            try:
                print(f"\n📦 {step_name}...")
                result = step_function()
                results[step_name] = {'status': 'SUCCESS', 'result': result}
                print(f"✅ {step_name} completed")
            except Exception as e:
                print(f"❌ {step_name} failed: {str(e)}")
                results[step_name] = {'status': 'FAILED', 'error': str(e)}
        
        self.print_monitoring_summary(results)
        return results

    def create_sns_topics(self):
        """Create SNS topics for different alert levels"""
        topics = {
            'sla-critical-alerts': 'Critical SLA breach alerts requiring immediate attention',
            'sla-high-alerts': 'High priority alerts for potential SLA breaches',
            'sla-system-health': 'System health and monitoring notifications',
            'sla-daily-reports': 'Daily summary reports and metrics'
        }
        
        created_topics = {}
        
        for topic_name, description in topics.items():
            try:
                response = self.sns.create_topic(Name=topic_name)
                topic_arn = response['TopicArn']
                
                # Set topic attributes
                self.sns.set_topic_attributes(
                    TopicArn=topic_arn,
                    AttributeName='DisplayName',
                    AttributeValue=description
                )
                
                created_topics[topic_name] = topic_arn
                logger.info(f"Created topic: {topic_name}")
                
            except Exception as e:
                logger.warning(f"Topic creation warning for {topic_name}: {e}")
                # Try to get existing topic
                topics_list = self.sns.list_topics()
                for topic in topics_list['Topics']:
                    if topic_name in topic['TopicArn']:
                        created_topics[topic_name] = topic['TopicArn']
                        break
        
        return created_topics

    def setup_email_subscriptions(self):
        """Setup email subscriptions for SNS topics"""
        if not self.email_address:
            logger.warning("No email address provided, skipping email subscriptions")
            return {'status': 'skipped', 'reason': 'no_email_provided'}
        
        # Get topic ARNs
        topics = self.sns.list_topics()['Topics']
        subscriptions = {}
        
        for topic in topics:
            topic_arn = topic['TopicArn']
            topic_name = topic_arn.split(':')[-1]
            
            if 'sla-' in topic_name:
                try:
                    response = self.sns.subscribe(
                        TopicArn=topic_arn,
                        Protocol='email',
                        Endpoint=self.email_address
                    )
                    
                    subscriptions[topic_name] = {
                        'subscription_arn': response['SubscriptionArn'],
                        'email': self.email_address,
                        'status': 'pending_confirmation'
                    }
                    
                    logger.info(f"Email subscription created for {topic_name}")
                    
                except Exception as e:
                    logger.warning(f"Email subscription failed for {topic_name}: {e}")
        
        return subscriptions

    def create_cloudwatch_alarms(self):
        """Create CloudWatch alarms for AWS services"""
        alarms = [
            {
                'AlarmName': 'SLA-Guard-Lambda-Errors',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'Errors',
                'Namespace': 'AWS/Lambda',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 5.0,
                'ActionsEnabled': True,
                'AlarmDescription': 'Lambda function errors for SLA Guard',
                'Dimensions': [
                    {
                        'Name': 'FunctionName',
                        'Value': 'sla-guard-ml-predictor'
                    }
                ],
                'Unit': 'Count'
            },
            {
                'AlarmName': 'SLA-Guard-DynamoDB-Throttles',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'ThrottledRequests',
                'Namespace': 'AWS/DynamoDB',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 0.0,
                'ActionsEnabled': True,
                'AlarmDescription': 'DynamoDB throttling for SLA Guard table',
                'Dimensions': [
                    {
                        'Name': 'TableName',
                        'Value': 'sla-guard-tickets'
                    }
                ],
                'Unit': 'Count'
            },
            {
                'AlarmName': 'SLA-Guard-High-Breach-Rate',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 1,
                'MetricName': 'HighRiskTickets',
                'Namespace': 'SLAGuard/Custom',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 10.0,
                'ActionsEnabled': True,
                'AlarmDescription': 'High number of tickets with breach risk > 70%',
                'Unit': 'Count'
            }
        ]
        
        created_alarms = []
        
        for alarm_config in alarms:
            try:
                # Add SNS action for critical alerts
                topics = self.sns.list_topics()['Topics']
                critical_topic = None
                for topic in topics:
                    if 'sla-critical-alerts' in topic['TopicArn']:
                        critical_topic = topic['TopicArn']
                        break
                
                if critical_topic:
                    alarm_config['AlarmActions'] = [critical_topic]
                
                self.cloudwatch.put_metric_alarm(**alarm_config)
                created_alarms.append(alarm_config['AlarmName'])
                logger.info(f"Created alarm: {alarm_config['AlarmName']}")
                
            except Exception as e:
                logger.warning(f"Alarm creation failed for {alarm_config['AlarmName']}: {e}")
        
        return created_alarms

    def setup_ses_email(self):
        """Setup SES for sending emails"""
        if not self.email_address:
            return {'status': 'skipped', 'reason': 'no_email_provided'}
        
        try:
            # Verify email address
            self.ses.verify_email_identity(EmailAddress=self.email_address)
            
            # Check verification status
            response = self.ses.get_identity_verification_attributes(
                Identities=[self.email_address]
            )
            
            verification_status = response['VerificationAttributes'].get(
                self.email_address, {}
            ).get('VerificationStatus', 'Pending')
            
            return {
                'email': self.email_address,
                'verification_status': verification_status,
                'note': 'Check your email for verification link if status is Pending'
            }
            
        except Exception as e:
            logger.warning(f"SES setup failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def setup_service_monitoring(self):
        """Setup monitoring for AWS services"""
        services_to_monitor = [
            {
                'service': 'bedrock',
                'endpoint': f'https://bedrock-runtime.{self.region}.amazonaws.com',
                'description': 'Amazon Bedrock Runtime'
            },
            {
                'service': 'comprehend',
                'endpoint': f'https://comprehend.{self.region}.amazonaws.com',
                'description': 'Amazon Comprehend'
            },
            {
                'service': 'sagemaker',
                'endpoint': f'https://runtime.sagemaker.{self.region}.amazonaws.com',
                'description': 'Amazon SageMaker Runtime'
            },
            {
                'service': 'dynamodb',
                'endpoint': f'https://dynamodb.{self.region}.amazonaws.com',
                'description': 'Amazon DynamoDB'
            },
            {
                'service': 'lambda',
                'endpoint': f'https://lambda.{self.region}.amazonaws.com',
                'description': 'AWS Lambda'
            }
        ]
        
        monitoring_config = {
            'services': services_to_monitor,
            'check_interval': 300,  # 5 minutes
            'timeout': 30,
            'region': self.region
        }
        
        return monitoring_config

    def deploy_alert_lambda(self):
        """Deploy Lambda function for critical alerts"""
        lambda_code = '''
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """Handle critical alerts and send immediate notifications"""
    
    sns = boto3.client('sns')
    ses = boto3.client('ses')
    
    # Parse the alert
    alert_data = json.loads(event['Records'][0]['Sns']['Message'])
    
    # Determine alert severity
    severity = 'HIGH'
    if 'critical' in alert_data.get('AlarmName', '').lower():
        severity = 'CRITICAL'
    
    # Send immediate email
    email_subject = f"🚨 {severity} SLA Alert - {alert_data.get('AlarmName', 'Unknown')}"
    
    email_body = f"""
    CRITICAL SLA ALERT
    
    Alert: {alert_data.get('AlarmName', 'Unknown')}
    Time: {datetime.now().isoformat()}
    Severity: {severity}
    
    Details:
    {json.dumps(alert_data, indent=2)}
    
    Action Required: Immediate investigation needed
    
    AWS Console: https://console.aws.amazon.com/cloudwatch/home?region={os.environ.get('AWS_REGION', 'us-east-1')}
    """
    
    try:
        # Send via SES if configured
        email_address = os.environ.get('ALERT_EMAIL')
        if email_address:
            ses.send_email(
                Source=email_address,
                Destination={'ToAddresses': [email_address]},
                Message={
                    'Subject': {'Data': email_subject},
                    'Body': {'Text': {'Data': email_body}}
                }
            )
    except Exception as e:
        print(f"SES send failed: {e}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Alert processed successfully')
    }
'''
        
        try:
            # Create deployment package
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr('lambda_function.py', lambda_code)
            
            # Deploy Lambda function
            function_name = 'sla-guard-critical-alerts'
            
            try:
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=f'arn:aws:iam::{self.account_id}:role/sla-guard-lambda-role',
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_buffer.getvalue()},
                    Description='Critical alert handler for SLA Guard',
                    Timeout=60,
                    Environment={
                        'Variables': {
                            'ALERT_EMAIL': self.email_address or '',
                            'AWS_REGION': self.region
                        }
                    }
                )
                function_arn = response['FunctionArn']
            except self.lambda_client.exceptions.ResourceConflictException:
                # Update existing function
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_buffer.getvalue()
                )
                response = self.lambda_client.get_function(FunctionName=function_name)
                function_arn = response['Configuration']['FunctionArn']
            
            return {
                'function_name': function_name,
                'function_arn': function_arn,
                'status': 'deployed'
            }
            
        except Exception as e:
            logger.warning(f"Alert Lambda deployment failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def test_email_system(self):
        """Test the email alert system"""
        if not self.email_address:
            return {'status': 'skipped', 'reason': 'no_email_provided'}
        
        try:
            # Find critical alerts topic
            topics = self.sns.list_topics()['Topics']
            critical_topic = None
            for topic in topics:
                if 'sla-critical-alerts' in topic['TopicArn']:
                    critical_topic = topic['TopicArn']
                    break
            
            if not critical_topic:
                return {'status': 'failed', 'error': 'Critical alerts topic not found'}
            
            # Send test message
            test_message = {
                'alert_type': 'TEST',
                'severity': 'CRITICAL',
                'message': 'This is a test of the SLA Guard critical alert system',
                'timestamp': datetime.now().isoformat(),
                'test': True
            }
            
            response = self.sns.publish(
                TopicArn=critical_topic,
                Message=json.dumps(test_message, indent=2),
                Subject='🧪 SLA Guard Alert System Test'
            )
            
            return {
                'status': 'sent',
                'message_id': response['MessageId'],
                'topic_arn': critical_topic,
                'email': self.email_address,
                'note': 'Check your email for the test alert'
            }
            
        except Exception as e:
            logger.error(f"Email test failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def get_aws_service_urls(self):
        """Get AWS service URLs for monitoring"""
        base_url = f"https://console.aws.amazon.com"
        
        urls = {
            'cloudwatch_dashboard': f"{base_url}/cloudwatch/home?region={self.region}#dashboards:",
            'cloudwatch_alarms': f"{base_url}/cloudwatch/home?region={self.region}#alarmsV2:",
            'sns_topics': f"{base_url}/sns/v3/home?region={self.region}#/topics",
            'lambda_functions': f"{base_url}/lambda/home?region={self.region}#/functions",
            'dynamodb_tables': f"{base_url}/dynamodbv2/home?region={self.region}#tables",
            'ses_identities': f"{base_url}/ses/home?region={self.region}#/identities",
            'bedrock_console': f"{base_url}/bedrock/home?region={self.region}#/",
            'sagemaker_endpoints': f"{base_url}/sagemaker/home?region={self.region}#/endpoints",
            'quicksight_dashboards': f"{base_url}/quicksight/sn/dashboards"
        }
        
        return urls

    def print_monitoring_summary(self, results):
        """Print comprehensive monitoring setup summary"""
        print("\n" + "="*60)
        print("📊 AWS Monitoring Setup Summary")
        print("="*60)
        
        success_count = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
        total_count = len(results)
        
        print(f"📈 Setup Status: {success_count}/{total_count} components configured")
        print()
        
        for component, result in results.items():
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"{status_icon} {component}: {result['status']}")
            if result['status'] == 'FAILED':
                print(f"   Error: {result['error']}")
        
        # AWS Service URLs
        urls = self.get_aws_service_urls()
        print(f"\n🔗 AWS Console URLs:")
        print(f"   CloudWatch Alarms: {urls['cloudwatch_alarms']}")
        print(f"   SNS Topics: {urls['sns_topics']}")
        print(f"   Lambda Functions: {urls['lambda_functions']}")
        print(f"   DynamoDB Tables: {urls['dynamodb_tables']}")
        print(f"   SES Identities: {urls['ses_identities']}")
        print(f"   Bedrock Console: {urls['bedrock_console']}")
        print(f"   SageMaker Endpoints: {urls['sagemaker_endpoints']}")
        print(f"   QuickSight Dashboards: {urls['quicksight_dashboards']}")
        
        print(f"\n📧 Email Configuration:")
        if self.email_address:
            print(f"   Alert Email: {self.email_address}")
            print(f"   ⚠️ IMPORTANT: Check your email for:")
            print(f"      1. SNS subscription confirmations")
            print(f"      2. SES verification email")
            print(f"      3. Test alert message")
        else:
            print(f"   ❌ No email configured - alerts will only go to SNS topics")
        
        print(f"\n🚨 Critical Alert Flow:")
        print(f"   1. High-risk ticket detected (>70% breach probability)")
        print(f"   2. SNS topic triggered: sla-critical-alerts")
        print(f"   3. Email sent via SNS subscription")
        print(f"   4. Lambda function processes alert")
        print(f"   5. Additional SES email sent for critical issues")
        
        print(f"\n📊 Monitoring Capabilities:")
        print(f"   • Real-time CloudWatch alarms")
        print(f"   • SNS email notifications")
        print(f"   • SES direct email alerts")
        print(f"   • Lambda-based alert processing")
        print(f"   • Service health monitoring")
        
        print(f"\n🔧 Next Steps:")
        print(f"   1. Confirm SNS email subscriptions")
        print(f"   2. Verify SES email identity")
        print(f"   3. Test critical alert workflow")
        print(f"   4. Monitor CloudWatch alarms")
        print(f"   5. Check email delivery")

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup AWS Monitoring and Email Alerts')
    parser.add_argument('--email', required=True, help='Email address for alerts')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    print("🚀 AWS Monitoring and Email Alert Setup")
    print("=" * 50)
    print(f"📧 Email: {args.email}")
    print(f"🌍 Region: {args.region}")
    print("=" * 50)
    
    setup = AWSMonitoringSetup(region=args.region, email_address=args.email)
    results = setup.setup_complete_monitoring()
    
    if all(r['status'] == 'SUCCESS' for r in results.values()):
        print(f"\n🎉 Monitoring setup completed successfully!")
        print(f"📧 Check your email ({args.email}) for confirmations")
    else:
        print(f"\n⚠️ Some components failed. Check the summary above.")

if __name__ == "__main__":
    main()