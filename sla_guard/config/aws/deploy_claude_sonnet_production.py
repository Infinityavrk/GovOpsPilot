#!/usr/bin/env python3
"""
Deploy Llama 3.5 Production Integration
Complete production deployment of enhanced Llama capabilities
with monitoring, scaling, and fallback systems.
"""

import json
import boto3
import time
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeSonnetProductionDeployment:
    def __init__(self, region='us-east-1', environment='production'):
        """Initialize production deployment"""
        self.region = region
        self.environment = environment
        self.account_id = '508955320780'
        
        # Initialize AWS clients
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.eventbridge = boto3.client('events', region_name=region)
        
        # Configuration
        self.config = {
            'claude_model_id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'fallback_model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'max_tokens': 4000,
            'temperature': 0.1,
            'timeout_seconds': 30,
            'retry_attempts': 3,
            'batch_size': 10,
            'monitoring_interval': 300  # 5 minutes
        }
        
        logger.info(f"🚀 Llama Production Deployment initialized")
        logger.info(f"   Region: {region}")
        logger.info(f"   Environment: {environment}")
        logger.info(f"   Account: {self.account_id}")

    def deploy_enhanced_lambda_functions(self) -> Dict[str, Any]:
        """Deploy enhanced Lambda functions with Llama integration"""
        logger.info("🔧 Deploying enhanced Lambda functions...")
        
        lambda_functions = [
            {
                'name': 'sla-guard-claude-analyzer',
                'description': 'Enhanced ticket analysis with Llama 3.5',
                'handler': 'claude_analyzer.lambda_handler',
                'runtime': 'python3.11',
                'timeout': 60,
                'memory': 1024,
                'environment_vars': {
                    'CLAUDE_MODEL_ID': self.config['claude_model_id'],
                    'FALLBACK_MODEL_ID': self.config['fallback_model_id'],
                    'MAX_TOKENS': str(self.config['max_tokens']),
                    'TEMPERATURE': str(self.config['temperature']),
                    'ENVIRONMENT': self.environment
                }
            },
            {
                'name': 'sla-guard-breach-predictor',
                'description': 'Advanced SLA breach prediction with Llama',
                'handler': 'breach_predictor.lambda_handler',
                'runtime': 'python3.11',
                'timeout': 45,
                'memory': 512,
                'environment_vars': {
                    'CLAUDE_MODEL_ID': self.config['claude_model_id'],
                    'PREDICTION_THRESHOLD': '0.7',
                    'ENVIRONMENT': self.environment
                }
            },
            {
                'name': 'sla-guard-response-generator',
                'description': 'Intelligent response generation with Llama',
                'handler': 'response_generator.lambda_handler',
                'runtime': 'python3.11',
                'timeout': 30,
                'memory': 512,
                'environment_vars': {
                    'CLAUDE_MODEL_ID': self.config['claude_model_id'],
                    'RESPONSE_TEMPLATES_TABLE': 'sla-guard-response-templates',
                    'ENVIRONMENT': self.environment
                }
            }
        ]
        
        deployment_results = []
        
        for func_config in lambda_functions:
            try:
                # Create Lambda function code
                lambda_code = self._generate_lambda_code(func_config['name'])
                
                # Deploy function
                result = self._deploy_lambda_function(func_config, lambda_code)
                deployment_results.append(result)
                
                logger.info(f"✅ Deployed: {func_config['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to deploy {func_config['name']}: {e}")
                deployment_results.append({
                    'function_name': func_config['name'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'deployed_functions': deployment_results,
            'total_functions': len(lambda_functions),
            'successful_deployments': len([r for r in deployment_results if r.get('status') == 'success'])
        }

    def _generate_lambda_code(self, function_name: str) -> str:
        """Generate Lambda function code for each service"""
        
        if function_name == 'sla-guard-claude-analyzer':
            return '''
import json
import boto3
import os
from datetime import datetime
from enhanced_claude_sonnet_integration import EnhancedClaudeSonnetIntegration

def lambda_handler(event, context):
    """Lambda handler for Llama ticket analysis"""
    
    try:
        # Initialize Claude integration
        claude_integration = EnhancedClaudeSonnetIntegration()
        
        # Extract ticket data from event
        ticket_text = event.get('ticket_text', '')
        ticket_context = event.get('context', {})
        
        if not ticket_text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing ticket_text'})
            }
        
        # Perform analysis
        analysis_result = claude_integration.analyze_ticket_with_claude_sonnet(
            ticket_text, 
            ticket_context
        )
        
        # Add metadata
        analysis_result.update({
            'lambda_function': 'sla-guard-claude-analyzer',
            'processed_at': datetime.now().isoformat(),
            'environment': os.environ.get('ENVIRONMENT', 'production')
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(analysis_result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'function': 'sla-guard-claude-analyzer'
            })
        }
'''
        
        elif function_name == 'sla-guard-breach-predictor':
            return '''
import json
import boto3
import os
from datetime import datetime
from enhanced_claude_sonnet_integration import EnhancedClaudeSonnetIntegration

def lambda_handler(event, context):
    """Lambda handler for SLA breach prediction"""
    
    try:
        # Initialize Claude integration
        claude_integration = EnhancedClaudeSonnetIntegration()
        
        # Extract analysis data from event
        ticket_analysis = event.get('ticket_analysis', {})
        historical_data = event.get('historical_data', [])
        
        if not ticket_analysis:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing ticket_analysis'})
            }
        
        # Perform breach prediction
        prediction_result = claude_integration.predict_sla_breach_risk(
            ticket_analysis,
            historical_data
        )
        
        # Check if alert needed
        threshold = float(os.environ.get('PREDICTION_THRESHOLD', '0.7'))
        alert_needed = prediction_result.get('breach_probability', 0) > threshold
        
        # Add metadata
        prediction_result.update({
            'lambda_function': 'sla-guard-breach-predictor',
            'processed_at': datetime.now().isoformat(),
            'alert_needed': alert_needed,
            'threshold_used': threshold
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(prediction_result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'function': 'sla-guard-breach-predictor'
            })
        }
'''
        
        elif function_name == 'sla-guard-response-generator':
            return '''
import json
import boto3
import os
from datetime import datetime
from enhanced_claude_sonnet_integration import EnhancedClaudeSonnetIntegration

def lambda_handler(event, context):
    """Lambda handler for intelligent response generation"""
    
    try:
        # Initialize Claude integration
        claude_integration = EnhancedClaudeSonnetIntegration()
        
        # Extract data from event
        ticket_analysis = event.get('ticket_analysis', {})
        user_context = event.get('user_context', {})
        
        if not ticket_analysis:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing ticket_analysis'})
            }
        
        # Generate intelligent response
        response_result = claude_integration.generate_intelligent_response(
            ticket_analysis,
            user_context
        )
        
        # Add metadata
        response_result.update({
            'lambda_function': 'sla-guard-response-generator',
            'generated_at': datetime.now().isoformat(),
            'user_type': user_context.get('user_type', 'unknown')
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'function': 'sla-guard-response-generator'
            })
        }
'''
        
        return "# Default Lambda function code"

    def _deploy_lambda_function(self, func_config: Dict[str, Any], code: str) -> Dict[str, Any]:
        """Deploy individual Lambda function"""
        
        try:
            # Create deployment package
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr('lambda_function.py', code)
                # Add enhanced_claude_sonnet_integration.py
                with open('enhanced_claude_sonnet_integration.py', 'r') as f:
                    zip_file.writestr('enhanced_claude_sonnet_integration.py', f.read())
            
            zip_buffer.seek(0)
            
            # Create or update Lambda function
            try:
                response = self.lambda_client.create_function(
                    FunctionName=func_config['name'],
                    Runtime=func_config['runtime'],
                    Role=f"arn:aws:iam::{self.account_id}:role/lambda-execution-role",
                    Handler=func_config['handler'],
                    Code={'ZipFile': zip_buffer.getvalue()},
                    Description=func_config['description'],
                    Timeout=func_config['timeout'],
                    MemorySize=func_config['memory'],
                    Environment={'Variables': func_config['environment_vars']},
                    Tags={
                        'Environment': self.environment,
                        'Service': 'sla-guard',
                        'Component': 'claude-sonnet'
                    }
                )
                
                return {
                    'function_name': func_config['name'],
                    'status': 'success',
                    'arn': response['FunctionArn'],
                    'action': 'created'
                }
                
            except self.lambda_client.exceptions.ResourceConflictException:
                # Function exists, update it
                response = self.lambda_client.update_function_code(
                    FunctionName=func_config['name'],
                    ZipFile=zip_buffer.getvalue()
                )
                
                # Update configuration
                self.lambda_client.update_function_configuration(
                    FunctionName=func_config['name'],
                    Runtime=func_config['runtime'],
                    Handler=func_config['handler'],
                    Description=func_config['description'],
                    Timeout=func_config['timeout'],
                    MemorySize=func_config['memory'],
                    Environment={'Variables': func_config['environment_vars']}
                )
                
                return {
                    'function_name': func_config['name'],
                    'status': 'success',
                    'arn': response['FunctionArn'],
                    'action': 'updated'
                }
                
        except Exception as e:
            return {
                'function_name': func_config['name'],
                'status': 'failed',
                'error': str(e)
            }

    def setup_eventbridge_integration(self) -> Dict[str, Any]:
        """Setup EventBridge rules for Llama integration"""
        logger.info("📡 Setting up EventBridge integration...")
        
        rules = [
            {
                'name': 'sla-guard-new-ticket-analysis',
                'description': 'Trigger Claude analysis for new tickets',
                'event_pattern': {
                    'source': ['sla-guard.tickets'],
                    'detail-type': ['New Ticket Created'],
                    'detail': {
                        'priority': ['P1', 'P2']  # Only analyze high priority tickets with Claude
                    }
                },
                'targets': [
                    {
                        'id': '1',
                        'arn': f"arn:aws:lambda:{self.region}:{self.account_id}:function:sla-guard-claude-analyzer"
                    }
                ]
            },
            {
                'name': 'sla-guard-breach-prediction',
                'description': 'Trigger breach prediction after analysis',
                'event_pattern': {
                    'source': ['sla-guard.analysis'],
                    'detail-type': ['Ticket Analysis Completed']
                },
                'targets': [
                    {
                        'id': '1',
                        'arn': f"arn:aws:lambda:{self.region}:{self.account_id}:function:sla-guard-breach-predictor"
                    }
                ]
            }
        ]
        
        setup_results = []
        
        for rule_config in rules:
            try:
                # Create EventBridge rule
                self.eventbridge.put_rule(
                    Name=rule_config['name'],
                    EventPattern=json.dumps(rule_config['event_pattern']),
                    Description=rule_config['description'],
                    State='ENABLED',
                    Tags=[
                        {'Key': 'Environment', 'Value': self.environment},
                        {'Key': 'Service', 'Value': 'sla-guard'}
                    ]
                )
                
                # Add targets
                self.eventbridge.put_targets(
                    Rule=rule_config['name'],
                    Targets=rule_config['targets']
                )
                
                setup_results.append({
                    'rule_name': rule_config['name'],
                    'status': 'success'
                })
                
                logger.info(f"✅ EventBridge rule created: {rule_config['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create rule {rule_config['name']}: {e}")
                setup_results.append({
                    'rule_name': rule_config['name'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'eventbridge_rules': setup_results,
            'total_rules': len(rules),
            'successful_rules': len([r for r in setup_results if r.get('status') == 'success'])
        }

    def setup_monitoring_and_alerting(self) -> Dict[str, Any]:
        """Setup CloudWatch monitoring and SNS alerting"""
        logger.info("📊 Setting up monitoring and alerting...")
        
        # Create CloudWatch alarms
        alarms = [
            {
                'name': 'sla-guard-claude-errors',
                'description': 'Llama error rate alarm',
                'metric_name': 'Errors',
                'namespace': 'AWS/Lambda',
                'dimensions': [
                    {'Name': 'FunctionName', 'Value': 'sla-guard-claude-analyzer'}
                ],
                'statistic': 'Sum',
                'period': 300,
                'evaluation_periods': 2,
                'threshold': 5,
                'comparison_operator': 'GreaterThanThreshold'
            },
            {
                'name': 'sla-guard-claude-duration',
                'description': 'Llama duration alarm',
                'metric_name': 'Duration',
                'namespace': 'AWS/Lambda',
                'dimensions': [
                    {'Name': 'FunctionName', 'Value': 'sla-guard-claude-analyzer'}
                ],
                'statistic': 'Average',
                'period': 300,
                'evaluation_periods': 2,
                'threshold': 45000,  # 45 seconds
                'comparison_operator': 'GreaterThanThreshold'
            },
            {
                'name': 'sla-guard-breach-prediction-accuracy',
                'description': 'Breach prediction accuracy monitoring',
                'metric_name': 'PredictionAccuracy',
                'namespace': 'SLAGuard/Claude',
                'statistic': 'Average',
                'period': 3600,  # 1 hour
                'evaluation_periods': 1,
                'threshold': 0.8,  # 80% accuracy
                'comparison_operator': 'LessThanThreshold'
            }
        ]
        
        # Create SNS topic for alerts
        try:
            sns_response = self.sns.create_topic(
                Name='sla-guard-claude-alerts',
                Tags=[
                    {'Key': 'Environment', 'Value': self.environment},
                    {'Key': 'Service', 'Value': 'sla-guard'}
                ]
            )
            topic_arn = sns_response['TopicArn']
            logger.info(f"✅ SNS topic created: {topic_arn}")
        except Exception as e:
            logger.error(f"❌ Failed to create SNS topic: {e}")
            topic_arn = None
        
        # Create CloudWatch alarms
        alarm_results = []
        
        for alarm_config in alarms:
            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_config['name'],
                    AlarmDescription=alarm_config['description'],
                    MetricName=alarm_config['metric_name'],
                    Namespace=alarm_config['namespace'],
                    Dimensions=alarm_config.get('dimensions', []),
                    Statistic=alarm_config['statistic'],
                    Period=alarm_config['period'],
                    EvaluationPeriods=alarm_config['evaluation_periods'],
                    Threshold=alarm_config['threshold'],
                    ComparisonOperator=alarm_config['comparison_operator'],
                    AlarmActions=[topic_arn] if topic_arn else [],
                    Tags=[
                        {'Key': 'Environment', 'Value': self.environment},
                        {'Key': 'Service', 'Value': 'sla-guard'}
                    ]
                )
                
                alarm_results.append({
                    'alarm_name': alarm_config['name'],
                    'status': 'success'
                })
                
                logger.info(f"✅ CloudWatch alarm created: {alarm_config['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create alarm {alarm_config['name']}: {e}")
                alarm_results.append({
                    'alarm_name': alarm_config['name'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'sns_topic_arn': topic_arn,
            'cloudwatch_alarms': alarm_results,
            'total_alarms': len(alarms),
            'successful_alarms': len([r for r in alarm_results if r.get('status') == 'success'])
        }

    def setup_dynamodb_tables(self) -> Dict[str, Any]:
        """Setup DynamoDB tables for Llama data"""
        logger.info("💾 Setting up DynamoDB tables...")
        
        tables = [
            {
                'name': 'sla-guard-claude-analytics',
                'description': 'Store Llama analysis results',
                'key_schema': [
                    {'AttributeName': 'ticket_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'analysis_timestamp', 'KeyType': 'RANGE'}
                ],
                'attribute_definitions': [
                    {'AttributeName': 'ticket_id', 'AttributeType': 'S'},
                    {'AttributeName': 'analysis_timestamp', 'AttributeType': 'S'}
                ],
                'billing_mode': 'PAY_PER_REQUEST'
            },
            {
                'name': 'sla-guard-response-templates',
                'description': 'Store intelligent response templates',
                'key_schema': [
                    {'AttributeName': 'template_id', 'KeyType': 'HASH'}
                ],
                'attribute_definitions': [
                    {'AttributeName': 'template_id', 'AttributeType': 'S'}
                ],
                'billing_mode': 'PAY_PER_REQUEST'
            },
            {
                'name': 'sla-guard-model-performance',
                'description': 'Track Llama performance metrics',
                'key_schema': [
                    {'AttributeName': 'date', 'KeyType': 'HASH'},
                    {'AttributeName': 'metric_type', 'KeyType': 'RANGE'}
                ],
                'attribute_definitions': [
                    {'AttributeName': 'date', 'AttributeType': 'S'},
                    {'AttributeName': 'metric_type', 'AttributeType': 'S'}
                ],
                'billing_mode': 'PAY_PER_REQUEST'
            }
        ]
        
        table_results = []
        
        for table_config in tables:
            try:
                # Check if table exists
                try:
                    table = self.dynamodb.Table(table_config['name'])
                    table.load()
                    
                    table_results.append({
                        'table_name': table_config['name'],
                        'status': 'exists',
                        'action': 'skipped'
                    })
                    
                    logger.info(f"✅ Table already exists: {table_config['name']}")
                    
                except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
                    # Create table
                    table = self.dynamodb.create_table(
                        TableName=table_config['name'],
                        KeySchema=table_config['key_schema'],
                        AttributeDefinitions=table_config['attribute_definitions'],
                        BillingMode=table_config['billing_mode'],
                        Tags=[
                            {'Key': 'Environment', 'Value': self.environment},
                            {'Key': 'Service', 'Value': 'sla-guard'},
                            {'Key': 'Component', 'Value': 'claude-sonnet'}
                        ]
                    )
                    
                    # Wait for table to be created
                    table.wait_until_exists()
                    
                    table_results.append({
                        'table_name': table_config['name'],
                        'status': 'success',
                        'action': 'created',
                        'arn': table.table_arn
                    })
                    
                    logger.info(f"✅ Table created: {table_config['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create table {table_config['name']}: {e}")
                table_results.append({
                    'table_name': table_config['name'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'dynamodb_tables': table_results,
            'total_tables': len(tables),
            'successful_tables': len([r for r in table_results if r.get('status') in ['success', 'exists']])
        }

    def validate_deployment(self) -> Dict[str, Any]:
        """Validate the complete deployment"""
        logger.info("🔍 Validating deployment...")
        
        validation_results = {
            'bedrock_access': False,
            'lambda_functions': [],
            'eventbridge_rules': [],
            'dynamodb_tables': [],
            'cloudwatch_alarms': [],
            'overall_status': 'unknown'
        }
        
        # Test Bedrock access
        try:
            response = self.bedrock.invoke_model(
                modelId=self.config['claude_model_id'],
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Say OK"}]
                })
            )
            validation_results['bedrock_access'] = True
            logger.info("✅ Bedrock access validated")
        except Exception as e:
            logger.error(f"❌ Bedrock access failed: {e}")
        
        # Test Lambda functions
        lambda_functions = [
            'sla-guard-claude-analyzer',
            'sla-guard-breach-predictor',
            'sla-guard-response-generator'
        ]
        
        for func_name in lambda_functions:
            try:
                response = self.lambda_client.get_function(FunctionName=func_name)
                validation_results['lambda_functions'].append({
                    'name': func_name,
                    'status': 'active',
                    'runtime': response['Configuration']['Runtime']
                })
                logger.info(f"✅ Lambda function validated: {func_name}")
            except Exception as e:
                validation_results['lambda_functions'].append({
                    'name': func_name,
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"❌ Lambda function validation failed: {func_name}")
        
        # Determine overall status
        bedrock_ok = validation_results['bedrock_access']
        lambda_ok = len([f for f in validation_results['lambda_functions'] if f.get('status') == 'active']) > 0
        
        if bedrock_ok and lambda_ok:
            validation_results['overall_status'] = 'success'
        elif lambda_ok:
            validation_results['overall_status'] = 'partial'
        else:
            validation_results['overall_status'] = 'failed'
        
        return validation_results

    def deploy_complete_system(self) -> Dict[str, Any]:
        """Deploy the complete Llama production system"""
        logger.info("🚀 Starting complete Llama production deployment...")
        
        deployment_start = time.time()
        
        results = {
            'deployment_id': f"claude-sonnet-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'start_time': datetime.now().isoformat(),
            'environment': self.environment,
            'region': self.region,
            'steps': []
        }
        
        try:
            # Step 1: Deploy Lambda functions
            logger.info("\n📦 Step 1: Deploying Lambda functions...")
            lambda_results = self.deploy_enhanced_lambda_functions()
            results['steps'].append({
                'step': 'lambda_deployment',
                'status': 'success' if lambda_results['successful_deployments'] > 0 else 'failed',
                'results': lambda_results
            })
            
            # Step 2: Setup DynamoDB tables
            logger.info("\n💾 Step 2: Setting up DynamoDB tables...")
            dynamodb_results = self.setup_dynamodb_tables()
            results['steps'].append({
                'step': 'dynamodb_setup',
                'status': 'success' if dynamodb_results['successful_tables'] > 0 else 'failed',
                'results': dynamodb_results
            })
            
            # Step 3: Setup EventBridge integration
            logger.info("\n📡 Step 3: Setting up EventBridge integration...")
            eventbridge_results = self.setup_eventbridge_integration()
            results['steps'].append({
                'step': 'eventbridge_setup',
                'status': 'success' if eventbridge_results['successful_rules'] > 0 else 'failed',
                'results': eventbridge_results
            })
            
            # Step 4: Setup monitoring and alerting
            logger.info("\n📊 Step 4: Setting up monitoring and alerting...")
            monitoring_results = self.setup_monitoring_and_alerting()
            results['steps'].append({
                'step': 'monitoring_setup',
                'status': 'success' if monitoring_results['successful_alarms'] > 0 else 'failed',
                'results': monitoring_results
            })
            
            # Step 5: Validate deployment
            logger.info("\n🔍 Step 5: Validating deployment...")
            validation_results = self.validate_deployment()
            results['steps'].append({
                'step': 'deployment_validation',
                'status': validation_results['overall_status'],
                'results': validation_results
            })
            
            # Calculate overall status
            successful_steps = len([s for s in results['steps'] if s['status'] == 'success'])
            total_steps = len(results['steps'])
            
            if successful_steps == total_steps:
                results['overall_status'] = 'success'
            elif successful_steps > 0:
                results['overall_status'] = 'partial'
            else:
                results['overall_status'] = 'failed'
            
            deployment_time = time.time() - deployment_start
            results['end_time'] = datetime.now().isoformat()
            results['deployment_duration'] = f"{deployment_time:.2f}s"
            
            logger.info(f"\n✅ Deployment completed in {deployment_time:.2f}s")
            logger.info(f"   Overall Status: {results['overall_status']}")
            logger.info(f"   Successful Steps: {successful_steps}/{total_steps}")
            
            return results
            
        except Exception as e:
            results['overall_status'] = 'failed'
            results['error'] = str(e)
            results['end_time'] = datetime.now().isoformat()
            
            logger.error(f"❌ Deployment failed: {e}")
            return results

    def generate_deployment_report(self, deployment_results: Dict[str, Any]):
        """Generate comprehensive deployment report"""
        print("\n" + "="*60)
        print("📋 Llama 3.5 PRODUCTION DEPLOYMENT REPORT")
        print("="*60)
        
        print(f"\n🎯 Deployment Overview:")
        print(f"   Deployment ID: {deployment_results['deployment_id']}")
        print(f"   Environment: {deployment_results['environment']}")
        print(f"   Region: {deployment_results['region']}")
        print(f"   Duration: {deployment_results.get('deployment_duration', 'N/A')}")
        print(f"   Overall Status: {deployment_results['overall_status'].upper()}")
        
        print(f"\n📊 Step-by-Step Results:")
        for i, step in enumerate(deployment_results['steps'], 1):
            status_icon = "✅" if step['status'] == 'success' else "⚠️" if step['status'] == 'partial' else "❌"
            print(f"   {i}. {step['step'].replace('_', ' ').title()}: {status_icon}")
            
            # Show key metrics for each step
            step_results = step.get('results', {})
            if 'successful_deployments' in step_results:
                print(f"      Functions: {step_results['successful_deployments']}/{step_results['total_functions']}")
            elif 'successful_tables' in step_results:
                print(f"      Tables: {step_results['successful_tables']}/{step_results['total_tables']}")
            elif 'successful_rules' in step_results:
                print(f"      Rules: {step_results['successful_rules']}/{step_results['total_rules']}")
            elif 'successful_alarms' in step_results:
                print(f"      Alarms: {step_results['successful_alarms']}/{step_results['total_alarms']}")
        
        # Validation results
        validation_step = next((s for s in deployment_results['steps'] if s['step'] == 'deployment_validation'), None)
        if validation_step:
            validation = validation_step['results']
            print(f"\n🔍 Validation Results:")
            print(f"   Bedrock Access: {'✅' if validation['bedrock_access'] else '❌'}")
            print(f"   Lambda Functions: {len([f for f in validation['lambda_functions'] if f.get('status') == 'active'])}/3")
            print(f"   Overall Validation: {validation['overall_status'].upper()}")
        
        # Next steps and recommendations
        print(f"\n🚀 Next Steps:")
        if deployment_results['overall_status'] == 'success':
            print(f"   ✅ Production system is ready!")
            print(f"   ✅ Llama 3.5 integration active")
            print(f"   ✅ Monitoring and alerting configured")
            print(f"   📊 Monitor performance in CloudWatch")
            print(f"   🧪 Run production tests to validate functionality")
        elif deployment_results['overall_status'] == 'partial':
            print(f"   ⚠️ Partial deployment completed")
            print(f"   🔧 Review failed components and retry")
            print(f"   ✅ Fallback systems should still work")
        else:
            print(f"   ❌ Deployment failed")
            print(f"   🔧 Check AWS permissions and configuration")
            print(f"   📞 Contact support if issues persist")
        
        print(f"\n📚 Documentation:")
        print(f"   • API Documentation: /docs/claude-sonnet-api.md")
        print(f"   • Monitoring Guide: /docs/monitoring-guide.md")
        print(f"   • Troubleshooting: /docs/troubleshooting.md")
        
        print(f"\n📞 Support:")
        print(f"   • CloudWatch Logs: /aws/lambda/sla-guard-claude-*")
        print(f"   • SNS Alerts: sla-guard-claude-alerts")
        print(f"   • Deployment ID: {deployment_results['deployment_id']}")


def main():
    """Main deployment function"""
    print("🚀 Llama 3.5 Production Deployment")
    print("=" * 60)
    
    # Initialize deployment
    deployer = ClaudeSonnetProductionDeployment()
    
    # Run complete deployment
    deployment_results = deployer.deploy_complete_system()
    
    # Generate report
    deployer.generate_deployment_report(deployment_results)
    
    print(f"\n🎉 Llama 3.5 production deployment completed!")

if __name__ == "__main__":
    main()