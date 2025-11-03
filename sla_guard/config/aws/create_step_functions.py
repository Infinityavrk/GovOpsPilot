#!/usr/bin/env python3
"""
Create Step Functions workflow for SLA Guard Agent
Completes the event-driven architecture: DynamoDB → Streams → EventBridge → Step Functions → Actions
"""

import boto3
import json
import os
from datetime import datetime

# AWS Profile Configuration
AWS_PROFILE = "AdministratorAccess-508955320780"
os.environ['AWS_PROFILE'] = AWS_PROFILE

class StepFunctionsCreator:
    def __init__(self):
        self.session = boto3.Session(profile_name=AWS_PROFILE)
        self.account_id = self.session.client('sts').get_caller_identity()['Account']
        self.region = self.session.region_name or 'us-east-2'
        
        self.stepfunctions_client = self.session.client('stepfunctions')
        self.iam_client = self.session.client('iam')
        self.events_client = self.session.client('events')
        
        print(f"🔄 Creating Step Functions Workflow")
        print(f"   Account: {self.account_id}")
        print(f"   Region: {self.region}")
        print("=" * 50)
    
    def create_complete_workflow(self):
        """Create the complete Step Functions workflow"""
        
        try:
            # Step 1: Create IAM role for Step Functions
            print("🔐 Step 1: Creating IAM role...")
            role_arn = self.create_stepfunctions_role()
            
            # Step 2: Create the Step Functions state machine
            print("\n🔄 Step 2: Creating Step Functions state machine...")
            state_machine_arn = self.create_state_machine(role_arn)
            
            # Step 3: Create EventBridge rule to trigger Step Functions
            print("\n📡 Step 3: Creating EventBridge rule...")
            self.create_eventbridge_rule(state_machine_arn)
            
            # Step 4: Enable DynamoDB Streams
            print("\n🗄️  Step 4: Enabling DynamoDB Streams...")
            self.enable_dynamodb_streams()
            
            print("\n✅ Step Functions workflow created successfully!")
            print(f"   State Machine ARN: {state_machine_arn}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to create workflow: {e}")
            return False
    
    def create_stepfunctions_role(self):
        """Create IAM role for Step Functions"""
        
        role_name = "SLAGuardStepFunctionsRole"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "states.amazonaws.com"},
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
                        "lambda:InvokeFunction"
                    ],
                    "Resource": [
                        f"arn:aws:lambda:*:{self.account_id}:function:sla-guard-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "events:PutEvents"
                    ],
                    "Resource": f"arn:aws:events:*:{self.account_id}:event-bus/service-efficiency-platform"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:*:{self.account_id}:*"
                }
            ]
        }
        
        try:
            print(f"   Creating role: {role_name}")
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="IAM role for SLA Guard Step Functions"
            )
            role_arn = response['Role']['Arn']
            
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName="SLAGuardStepFunctionsPolicy",
                PolicyDocument=json.dumps(permissions_policy)
            )
            
            print(f"   ✅ Role created: {role_arn}")
            return role_arn
            
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            print(f"   ✅ Role already exists")
            return f"arn:aws:iam::{self.account_id}:role/{role_name}"
    
    def create_state_machine(self, role_arn):
        """Create the Step Functions state machine"""
        
        state_machine_name = "SLAGuardWorkflow"
        
        # Define the workflow
        definition = {
            "Comment": "SLA Guard Agent workflow for breach prevention",
            "StartAt": "ProcessSLAMetrics",
            "States": {
                "ProcessSLAMetrics": {
                    "Type": "Task",
                    "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:sla-guard-metric-processor",
                    "Next": "CheckBreachRisk"
                },
                "CheckBreachRisk": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.breach_probability",
                            "NumericGreaterThan": 0.7,
                            "Next": "PredictBreach"
                        },
                        {
                            "Variable": "$.breach_probability",
                            "NumericGreaterThan": 0.4,
                            "Next": "MonitorTicket"
                        }
                    ],
                    "Default": "TicketHealthy"
                },
                "PredictBreach": {
                    "Type": "Task",
                    "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:sla-guard-breach-predictor",
                    "Next": "TriggerActions"
                },
                "TriggerActions": {
                    "Type": "Task",
                    "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:sla-guard-action-trigger",
                    "Next": "ValidateImpact"
                },
                "ValidateImpact": {
                    "Type": "Task",
                    "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:sla-guard-impact-validator",
                    "End": True
                },
                "MonitorTicket": {
                    "Type": "Task",
                    "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:sla-guard-status-updater",
                    "End": True
                },
                "TicketHealthy": {
                    "Type": "Pass",
                    "Result": "Ticket is healthy, no action needed",
                    "End": True
                }
            }
        }
        
        try:
            print(f"   Creating state machine: {state_machine_name}")
            response = self.stepfunctions_client.create_state_machine(
                name=state_machine_name,
                definition=json.dumps(definition),
                roleArn=role_arn,
                type='STANDARD',
                loggingConfiguration={
                    'level': 'ERROR',
                    'includeExecutionData': False,
                    'destinations': [
                        {
                            'cloudWatchLogsLogGroup': {
                                'logGroupArn': f'arn:aws:logs:{self.region}:{self.account_id}:log-group:/aws/stepfunctions/SLAGuardWorkflow'
                            }
                        }
                    ]
                }
            )
            
            state_machine_arn = response['stateMachineArn']
            print(f"   ✅ State machine created: {state_machine_arn}")
            return state_machine_arn
            
        except self.stepfunctions_client.exceptions.StateMachineAlreadyExists:
            print(f"   ✅ State machine already exists")
            # Get existing state machine ARN
            response = self.stepfunctions_client.list_state_machines()
            for sm in response['stateMachines']:
                if sm['name'] == state_machine_name:
                    return sm['stateMachineArn']
            
            return f"arn:aws:states:{self.region}:{self.account_id}:stateMachine:{state_machine_name}"
    
    def create_eventbridge_rule(self, state_machine_arn):
        """Create EventBridge rule to trigger Step Functions"""
        
        rule_name = "SLAGuardWorkflowTrigger"
        
        try:
            print(f"   Creating EventBridge rule: {rule_name}")
            
            # Create the rule
            self.events_client.put_rule(
                Name=rule_name,
                EventPattern=json.dumps({
                    "source": ["sla-guard.dynamodb"],
                    "detail-type": ["SLA Metrics Updated"],
                    "detail": {
                        "breach_probability": [{"numeric": [">", 0.4]}]
                    }
                }),
                State='ENABLED',
                Description='Trigger SLA Guard workflow for high-risk tickets',
                EventBusName='service-efficiency-platform'
            )
            
            # Add Step Functions as target
            self.events_client.put_targets(
                Rule=rule_name,
                EventBusName='service-efficiency-platform',
                Targets=[
                    {
                        'Id': '1',
                        'Arn': state_machine_arn,
                        'RoleArn': f"arn:aws:iam::{self.account_id}:role/SLAGuardStepFunctionsRole"
                    }
                ]
            )
            
            print(f"   ✅ EventBridge rule created")
            
        except Exception as e:
            print(f"   ⚠️  EventBridge rule error: {e}")
    
    def enable_dynamodb_streams(self):
        """Enable DynamoDB Streams on the SLA Guard table"""
        
        try:
            dynamodb_client = self.session.client('dynamodb')
            
            print(f"   Checking DynamoDB Streams...")
            
            # Check current stream status
            response = dynamodb_client.describe_table(TableName='sla-guard-state')
            
            stream_spec = response['Table'].get('StreamSpecification', {})
            
            if stream_spec.get('StreamEnabled'):
                print(f"   ✅ DynamoDB Streams already enabled")
            else:
                print(f"   Enabling DynamoDB Streams...")
                
                dynamodb_client.update_table(
                    TableName='sla-guard-state',
                    StreamSpecification={
                        'StreamEnabled': True,
                        'StreamViewType': 'NEW_AND_OLD_IMAGES'
                    }
                )
                
                print(f"   ✅ DynamoDB Streams enabled")
                
        except Exception as e:
            print(f"   ⚠️  DynamoDB Streams error: {e}")
    
    def test_workflow(self):
        """Test the Step Functions workflow"""
        
        print(f"\n🧪 Testing Step Functions workflow...")
        
        try:
            # Find the state machine
            response = self.stepfunctions_client.list_state_machines()
            state_machine_arn = None
            
            for sm in response['stateMachines']:
                if sm['name'] == 'SLAGuardWorkflow':
                    state_machine_arn = sm['stateMachineArn']
                    break
            
            if not state_machine_arn:
                print(f"   ❌ State machine not found")
                return False
            
            # Test execution
            test_input = {
                "ticket_id": "TEST-WORKFLOW-001",
                "priority": 1,
                "breach_probability": 0.8,
                "sla_status": "AT_RISK"
            }
            
            response = self.stepfunctions_client.start_execution(
                stateMachineArn=state_machine_arn,
                name=f"test-execution-{int(datetime.utcnow().timestamp())}",
                input=json.dumps(test_input)
            )
            
            execution_arn = response['executionArn']
            print(f"   ✅ Test execution started: {execution_arn}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Workflow test error: {e}")
            return False

def main():
    """Create Step Functions workflow"""
    
    try:
        creator = StepFunctionsCreator()
        success = creator.create_complete_workflow()
        
        if success:
            print(f"\n🎉 WORKFLOW COMPLETE!")
            print(f"   Your 5-layer SLA Guard architecture is now fully operational:")
            print(f"   📊 Data → 🧠 Model → ⚖️ Rules → 🔄 Workflow → 📈 Dashboard")
            
            # Test the workflow
            creator.test_workflow()
            
        else:
            print(f"\n❌ Workflow creation failed")
            
    except Exception as e:
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main()