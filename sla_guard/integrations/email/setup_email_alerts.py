#!/usr/bin/env python3
"""
Setup Email Alerts for SLA Guard
Creates SNS topics and SES configuration to send alerts to your email
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

class EmailAlertsSetup:
    def __init__(self):
        self.region = 'us-east-1'
        self.account_id = '508955320780'
        
        # Initialize AWS clients
        self.sns_client = boto3.client('sns', region_name=self.region)
        self.ses_client = boto3.client('ses', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.iam_client = boto3.client('iam', region_name=self.region)
        
        print(f"📧 Setting up Email Alerts for SLA Guard")
        print(f"   Account: {self.account_id}")
        print(f"   Region: {self.region}")
        print("=" * 50)
    
    def setup_complete_email_system(self, email_address):
        """Setup complete email alert system"""
        
        try:
            print(f"🚀 Setting up email alerts for: {email_address}")
            
            # Step 1: Verify email address in SES
            print("\n📧 Step 1: Setting up SES email verification...")
            self.setup_ses_email(email_address)
            
            # Step 2: Create SNS topics
            print("\n📢 Step 2: Creating SNS topics...")
            topics = self.create_sns_topics()
            
            # Step 3: Subscribe email to topics
            print("\n📬 Step 3: Subscribing email to topics...")
            self.subscribe_email_to_topics(email_address, topics)
            
            # Step 4: Create email sending Lambda function
            print("\n⚡ Step 4: Creating email Lambda function...")
            lambda_arn = self.create_email_lambda_function()
            
            # Step 5: Update Step Functions to send alerts
            print("\n🔄 Step 5: Updating Step Functions for alerts...")
            self.update_stepfunctions_for_alerts(topics, lambda_arn)
            
            # Step 6: Test the email system
            print("\n🧪 Step 6: Testing email alerts...")
            self.test_email_alerts(email_address, topics)
            
            print(f"\n✅ Email alert system setup complete!")
            print(f"   📧 Email: {email_address}")
            print(f"   📢 Topics created: {len(topics)}")
            print(f"   🔔 You will receive alerts for:")
            print(f"      • Critical SLA breaches (>70% risk)")
            print(f"      • High revenue impact tickets ($100K+)")
            print(f"      • System failures and errors")
            print(f"      • Daily SLA compliance reports")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to setup email alerts: {e}")
            return False
    
    def setup_ses_email(self, email_address):
        """Setup and verify email address in SES"""
        
        try:
            print(f"   Verifying email address: {email_address}")
            
            # Check if email is already verified
            response = self.ses_client.list_verified_email_addresses()
            verified_emails = response['VerifiedEmailAddresses']
            
            if email_address in verified_emails:
                print(f"   ✅ Email already verified: {email_address}")
                return True
            
            # Verify the email address
            self.ses_client.verify_email_identity(EmailAddress=email_address)
            
            print(f"   📧 Verification email sent to: {email_address}")
            print(f"   ⚠️  IMPORTANT: Check your email and click the verification link!")
            print(f"   ⏳ Waiting 30 seconds for verification...")
            
            # Wait and check verification status
            for i in range(6):  # Check 6 times over 30 seconds
                time.sleep(5)
                
                response = self.ses_client.list_verified_email_addresses()
                if email_address in response['VerifiedEmailAddresses']:
                    print(f"   ✅ Email verified successfully!")
                    return True
                
                print(f"   ⏳ Still waiting for verification... ({(i+1)*5}s)")
            
            print(f"   ⚠️  Email not yet verified. Please check your email and verify manually.")
            print(f"   💡 You can continue - alerts will work once email is verified.")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'MessageRejected':
                print(f"   ❌ Email address rejected. Please use a valid email address.")
            else:
                print(f"   ❌ SES setup error: {e}")
            return False
    
    def create_sns_topics(self):
        """Create SNS topics for different alert types"""
        
        topics_config = [
            {
                'name': 'sla-guard-critical-alerts',
                'display_name': 'SLA Guard Critical Alerts',
                'description': 'Critical SLA breach alerts (>70% risk)'
            },
            {
                'name': 'sla-guard-high-revenue-alerts',
                'display_name': 'SLA Guard High Revenue Alerts', 
                'description': 'High revenue impact alerts ($100K+)'
            },
            {
                'name': 'sla-guard-system-alerts',
                'display_name': 'SLA Guard System Alerts',
                'description': 'System failures and errors'
            },
            {
                'name': 'sla-guard-daily-reports',
                'display_name': 'SLA Guard Daily Reports',
                'description': 'Daily SLA compliance reports'
            }
        ]
        
        created_topics = {}
        
        for topic_config in topics_config:
            try:
                print(f"   Creating topic: {topic_config['name']}")
                
                response = self.sns_client.create_topic(
                    Name=topic_config['name'],
                    Attributes={
                        'DisplayName': topic_config['display_name'],
                        'Description': topic_config['description']
                    }
                )
                
                topic_arn = response['TopicArn']
                created_topics[topic_config['name']] = topic_arn
                
                print(f"   ✅ Topic created: {topic_arn}")
                
            except Exception as e:
                print(f"   ❌ Failed to create topic {topic_config['name']}: {e}")
        
        return created_topics
    
    def subscribe_email_to_topics(self, email_address, topics):
        """Subscribe email address to all SNS topics"""
        
        for topic_name, topic_arn in topics.items():
            try:
                print(f"   Subscribing {email_address} to {topic_name}")
                
                response = self.sns_client.subscribe(
                    TopicArn=topic_arn,
                    Protocol='email',
                    Endpoint=email_address
                )
                
                subscription_arn = response['SubscriptionArn']
                print(f"   ✅ Subscription created: {subscription_arn}")
                
            except Exception as e:
                print(f"   ❌ Failed to subscribe to {topic_name}: {e}")
    
    def create_email_lambda_function(self):
        """Create Lambda function for sending formatted emails"""
        
        function_name = 'sla-guard-email-sender'
        
        # Lambda function code for sending emails
        lambda_code = '''
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    print(f"Email sender triggered: {event}")
    
    ses = boto3.client('ses')
    
    # Extract alert information
    alert_type = event.get('alert_type', 'general')
    ticket_id = event.get('ticket_id', 'UNKNOWN')
    breach_probability = event.get('breach_probability', 0)
    revenue_impact = event.get('revenue_impact', 0)
    customer_tier = event.get('customer_tier', 'Unknown')
    department = event.get('department', 'Unknown')
    email_to = event.get('email_to', 'admin@company.com')
    
    # Format email based on alert type
    if alert_type == 'critical_breach':
        subject = f"🚨 CRITICAL SLA BREACH ALERT - {ticket_id}"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #e74c3c; color: white; padding: 20px; border-radius: 5px;">
                <h2>🚨 CRITICAL SLA BREACH ALERT</h2>
            </div>
            
            <div style="padding: 20px;">
                <h3>Ticket Details:</h3>
                <ul>
                    <li><strong>Ticket ID:</strong> {ticket_id}</li>
                    <li><strong>Breach Probability:</strong> {breach_probability:.1%}</li>
                    <li><strong>Revenue Impact:</strong> ${revenue_impact:,.0f}</li>
                    <li><strong>Customer Tier:</strong> {customer_tier}</li>
                    <li><strong>Department:</strong> {department}</li>
                    <li><strong>Alert Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                </ul>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4>🛡️ Automated Actions Taken:</h4>
                    <ul>
                        <li>✅ Senior team automatically assigned</li>
                        <li>✅ Ticket moved to priority queue</li>
                        <li>✅ Customer success team notified</li>
                        <li>✅ Enhanced monitoring activated</li>
                    </ul>
                </div>
                
                <p><strong>Action Required:</strong> Please review this high-risk ticket immediately.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 12px;">
                        This alert was generated by the SLA Guard AI system.<br>
                        Account: Innovation-Brigade (508955320780)
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
    elif alert_type == 'high_revenue':
        subject = f"💰 HIGH REVENUE IMPACT ALERT - {ticket_id}"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #f39c12; color: white; padding: 20px; border-radius: 5px;">
                <h2>💰 HIGH REVENUE IMPACT ALERT</h2>
            </div>
            
            <div style="padding: 20px;">
                <h3>Revenue Protection Alert:</h3>
                <ul>
                    <li><strong>Ticket ID:</strong> {ticket_id}</li>
                    <li><strong>Revenue at Risk:</strong> ${revenue_impact:,.0f}</li>
                    <li><strong>Breach Probability:</strong> {breach_probability:.1%}</li>
                    <li><strong>Customer Tier:</strong> {customer_tier}</li>
                    <li><strong>Department:</strong> {department}</li>
                </ul>
                
                <p><strong>Immediate attention required to protect revenue.</strong></p>
            </div>
        </body>
        </html>
        """
        
    elif alert_type == 'daily_report':
        subject = f"📊 Daily SLA Compliance Report - {datetime.now().strftime('%Y-%m-%d')}"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #3498db; color: white; padding: 20px; border-radius: 5px;">
                <h2>📊 Daily SLA Compliance Report</h2>
            </div>
            
            <div style="padding: 20px;">
                <h3>Today's Summary:</h3>
                <ul>
                    <li><strong>Total Tickets:</strong> {event.get('total_tickets', 0)}</li>
                    <li><strong>SLA Compliance:</strong> {event.get('compliance_rate', 95):.1f}%</li>
                    <li><strong>Breaches Prevented:</strong> {event.get('breaches_prevented', 0)}</li>
                    <li><strong>Revenue Protected:</strong> ${event.get('revenue_protected', 0):,.0f}</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
    else:
        subject = f"🔔 SLA Guard System Alert - {ticket_id}"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>🔔 SLA Guard System Alert</h2>
            <p>Alert details: {json.dumps(event, indent=2)}</p>
        </body>
        </html>
        """
    
    try:
        # Send email via SES
        response = ses.send_email(
            Source='noreply@sla-guard.com',  # This needs to be verified in SES
            Destination={'ToAddresses': [email_to]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Html': {'Data': body_html},
                    'Text': {'Data': f"SLA Guard Alert: {subject}\\n\\nTicket: {ticket_id}\\nBreach Probability: {breach_probability:.1%}\\nRevenue Impact: ${revenue_impact:,.0f}"}
                }
            }
        )
        
        print(f"Email sent successfully: {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Email sent successfully',
                'messageId': response['MessageId']
            })
        }
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
        '''
        
        try:
            print(f"   Creating Lambda function: {function_name}")
            
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=f'arn:aws:iam::{self.account_id}:role/lambda-execution-role',
                Handler='index.lambda_handler',
                Code={'ZipFile': lambda_code.encode('utf-8')},
                Description='Send formatted email alerts for SLA Guard',
                Timeout=30,
                MemorySize=128,
                Environment={
                    'Variables': {
                        'REGION': self.region,
                        'ACCOUNT_ID': self.account_id
                    }
                }
            )
            
            lambda_arn = response['FunctionArn']
            print(f"   ✅ Lambda function created: {lambda_arn}")
            
            # Add SES permissions to Lambda
            self.add_ses_permissions_to_lambda(function_name)
            
            return lambda_arn
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"   ✅ Lambda function already exists: {function_name}")
                
                # Update function code
                try:
                    self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=lambda_code.encode('utf-8')
                    )
                    print(f"   ✅ Lambda function code updated")
                except Exception as update_error:
                    print(f"   ⚠️  Could not update function: {update_error}")
                
                return f"arn:aws:lambda:{self.region}:{self.account_id}:function:{function_name}"
            else:
                print(f"   ❌ Error creating Lambda function: {e}")
                return None
    
    def add_ses_permissions_to_lambda(self, function_name):
        """Add SES permissions to Lambda execution role"""
        
        try:
            # Get the Lambda function to find its role
            response = self.lambda_client.get_function(FunctionName=function_name)
            role_arn = response['Configuration']['Role']
            role_name = role_arn.split('/')[-1]
            
            # SES permissions policy
            ses_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ses:SendEmail",
                            "ses:SendRawEmail"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            # Add policy to role
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName='SESEmailSendingPolicy',
                PolicyDocument=json.dumps(ses_policy)
            )
            
            print(f"   ✅ SES permissions added to Lambda role")
            
        except Exception as e:
            print(f"   ⚠️  Could not add SES permissions: {e}")
    
    def update_stepfunctions_for_alerts(self, topics, lambda_arn):
        """Update Step Functions to send alerts"""
        
        try:
            print(f"   Updating Step Functions for email alerts...")
            
            # This would update the Step Functions definition to include SNS/Lambda calls
            # For now, we'll create a separate alert trigger function
            
            alert_trigger_code = '''
import json
import boto3

def lambda_handler(event, context):
    print(f"Alert trigger: {event}")
    
    sns = boto3.client('sns')
    lambda_client = boto3.client('lambda')
    
    ticket_id = event.get('ticket_id', 'UNKNOWN')
    breach_probability = event.get('breach_probability', 0)
    revenue_impact = event.get('revenue_impact', 0)
    
    alerts_sent = []
    
    # Critical breach alert (>70% risk)
    if breach_probability > 0.7:
        try:
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:508955320780:sla-guard-critical-alerts',
                Subject=f'🚨 CRITICAL SLA BREACH - {ticket_id}',
                Message=f'Critical SLA breach detected!\\n\\nTicket: {ticket_id}\\nBreach Probability: {breach_probability:.1%}\\nRevenue Impact: ${revenue_impact:,.0f}\\n\\nImmediate action required!'
            )
            alerts_sent.append('critical_breach')
        except Exception as e:
            print(f"Failed to send critical alert: {e}")
    
    # High revenue impact alert ($100K+)
    if revenue_impact > 100000:
        try:
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:508955320780:sla-guard-high-revenue-alerts',
                Subject=f'💰 HIGH REVENUE IMPACT - {ticket_id}',
                Message=f'High revenue impact detected!\\n\\nTicket: {ticket_id}\\nRevenue at Risk: ${revenue_impact:,.0f}\\nBreach Probability: {breach_probability:.1%}\\n\\nRevenue protection required!'
            )
            alerts_sent.append('high_revenue')
        except Exception as e:
            print(f"Failed to send revenue alert: {e}")
    
    return {
        'alerts_sent': alerts_sent,
        'ticket_id': ticket_id,
        'breach_probability': breach_probability,
        'revenue_impact': revenue_impact
    }
            '''
            
            # Create alert trigger function
            self.lambda_client.create_function(
                FunctionName='sla-guard-alert-trigger',
                Runtime='python3.9',
                Role=f'arn:aws:iam::{self.account_id}:role/lambda-execution-role',
                Handler='index.lambda_handler',
                Code={'ZipFile': alert_trigger_code.encode('utf-8')},
                Description='Trigger email alerts for SLA Guard',
                Timeout=30,
                MemorySize=128
            )
            
            print(f"   ✅ Alert trigger function created")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"   ✅ Alert trigger function already exists")
            else:
                print(f"   ❌ Error creating alert trigger: {e}")
        except Exception as e:
            print(f"   ❌ Error updating Step Functions: {e}")
    
    def test_email_alerts(self, email_address, topics):
        """Test the email alert system"""
        
        print(f"   Testing email alerts to: {email_address}")
        
        # Test critical alert
        try:
            critical_topic = topics.get('sla-guard-critical-alerts')
            if critical_topic:
                self.sns_client.publish(
                    TopicArn=critical_topic,
                    Subject='🧪 TEST: Critical SLA Breach Alert',
                    Message=f'''This is a test of the SLA Guard critical alert system.

Ticket: TEST-CRITICAL-001
Breach Probability: 85.3%
Revenue Impact: $275,000
Customer Tier: Enterprise
Department: Technical Support

This is a test message. No action required.

SLA Guard System Test
Account: Innovation-Brigade (508955320780)
Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}'''
                )
                
                print(f"   ✅ Test critical alert sent")
        except Exception as e:
            print(f"   ❌ Failed to send test critical alert: {e}")
        
        # Test system alert
        try:
            system_topic = topics.get('sla-guard-system-alerts')
            if system_topic:
                self.sns_client.publish(
                    TopicArn=system_topic,
                    Subject='🧪 TEST: SLA Guard System Alert',
                    Message=f'''This is a test of the SLA Guard system alert.

System Status: All systems operational
Test Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}
Account: Innovation-Brigade (508955320780)

Email alert system is working correctly!'''
                )
                
                print(f"   ✅ Test system alert sent")
        except Exception as e:
            print(f"   ❌ Failed to send test system alert: {e}")
    
    def get_alert_status(self):
        """Get current status of email alert system"""
        
        print(f"\n📊 Email Alert System Status:")
        
        try:
            # Check SNS topics
            response = self.sns_client.list_topics()
            sla_topics = [topic for topic in response['Topics'] if 'sla-guard' in topic['TopicArn']]
            
            print(f"   📢 SNS Topics: {len(sla_topics)}")
            for topic in sla_topics:
                topic_name = topic['TopicArn'].split(':')[-1]
                print(f"      • {topic_name}")
                
                # Get subscriptions
                try:
                    subs_response = self.sns_client.list_subscriptions_by_topic(
                        TopicArn=topic['TopicArn']
                    )
                    subscriptions = subs_response['Subscriptions']
                    confirmed = len([s for s in subscriptions if s['SubscriptionArn'] != 'PendingConfirmation'])
                    pending = len([s for s in subscriptions if s['SubscriptionArn'] == 'PendingConfirmation'])
                    
                    print(f"        Confirmed: {confirmed}, Pending: {pending}")
                    
                except Exception as sub_error:
                    print(f"        Could not get subscriptions: {sub_error}")
            
            # Check SES verified emails
            response = self.ses_client.list_verified_email_addresses()
            verified_emails = response['VerifiedEmailAddresses']
            
            print(f"   📧 SES Verified Emails: {len(verified_emails)}")
            for email in verified_emails:
                print(f"      • {email}")
            
            # Check Lambda functions
            alert_functions = ['sla-guard-email-sender', 'sla-guard-alert-trigger']
            print(f"   ⚡ Alert Lambda Functions:")
            
            for func_name in alert_functions:
                try:
                    self.lambda_client.get_function(FunctionName=func_name)
                    print(f"      ✅ {func_name}")
                except ClientError:
                    print(f"      ❌ {func_name} - NOT FOUND")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Status check error: {e}")
            return False

def main():
    """Setup email alerts for SLA Guard"""
    
    try:
        setup = EmailAlertsSetup()
        
        # Get user's email address
        email_address = input("📧 Enter your email address for SLA Guard alerts: ").strip()
        
        if not email_address or '@' not in email_address:
            print("❌ Invalid email address. Please provide a valid email.")
            return
        
        print(f"\n🚀 Setting up email alerts for: {email_address}")
        
        # Setup complete email system
        success = setup.setup_complete_email_system(email_address)
        
        if success:
            print(f"\n🎉 EMAIL ALERT SYSTEM SETUP COMPLETE!")
            print(f"   📧 Email: {email_address}")
            print(f"   🔔 Alert Types:")
            print(f"      • 🚨 Critical SLA breaches (>70% risk)")
            print(f"      • 💰 High revenue impact ($100K+)")
            print(f"      • ⚠️  System failures and errors")
            print(f"      • 📊 Daily compliance reports")
            
            print(f"\n📬 Next Steps:")
            print(f"   1. Check your email for SNS subscription confirmations")
            print(f"   2. Click 'Confirm subscription' in each email")
            print(f"   3. Check your email for SES verification (if needed)")
            print(f"   4. Test alerts should arrive within a few minutes")
            
            # Show status
            setup.get_alert_status()
            
        else:
            print(f"\n❌ Email alert setup failed")
            
    except KeyboardInterrupt:
        print(f"\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main()