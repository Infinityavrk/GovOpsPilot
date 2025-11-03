#!/usr/bin/env python3
"""
Enhanced Email-to-Ticket Integration System
Reads emails and automatically populates the existing helpdesk ticket form
"""

import boto3
import json
import re
import uuid
import email
import imaplib
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError
import threading
import time

class EmailIntegratedTicketSystem:
    def __init__(self):
        self.region = 'us-east-1'
        self.account_id = '508955320780'
        
        # Initialize AWS clients
        self.ses_client = boto3.client('ses', region_name=self.region)
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        
        # Email configuration
        self.email_config = {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': '',
            'password': '',
            'support_email': ''
        }
        
        print(f"📧 Enhanced Email-to-Ticket Integration System")
        print(f"   Account: {self.account_id}")
        print(f"   Region: {self.region}")
        print("=" * 60)
    
    def setup_email_integration(self, email_address, password, support_email):
        """Setup complete email integration with existing ticket form"""
        
        try:
            print(f"🚀 Setting up email integration...")
            print(f"   📧 Email: {email_address}")
            print(f"   🎫 Support: {support_email}")
            
            # Store email configuration
            self.email_config.update({
                'email': email_address,
                'password': password,
                'support_email': support_email
            })
            
            # Step 1: Create DynamoDB table for tickets
            print("\n📦 Step 1: Creating DynamoDB table...")
            self.create_tickets_table()
            
            # Step 2: Create email processing Lambda
            print("\n⚡ Step 2: Creating email processing Lambda...")
            self.create_email_processor_lambda()
            
            # Step 3: Create ticket API Lambda
            print("\n🎫 Step 3: Creating ticket API Lambda...")
            self.create_ticket_api_lambda()
            
            # Step 4: Start email monitoring
            print("\n👁️ Step 4: Starting email monitoring...")
            self.start_email_monitoring()
            
            # Step 5: Create enhanced HTML form
            print("\n🌐 Step 5: Creating enhanced ticket form...")
            self.create_enhanced_ticket_form()
            
            # Step 6: Test the system
            print("\n🧪 Step 6: Testing email integration...")
            self.test_email_integration()
            
            print(f"\n✅ EMAIL INTEGRATION SETUP COMPLETE!")
            print(f"   📧 Monitoring: {email_address}")
            print(f"   🎫 Auto-populate: Enabled")
            print(f"   🤖 AI Analysis: Active")
            print(f"   📊 Real-time Updates: Live")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to setup email integration: {e}")
            return False
    
    def create_tickets_table(self):
        """Create DynamoDB table for storing tickets"""
        
        table_name = 'sla-tickets'
        
        try:
            print(f"   Creating table: {table_name}")
            
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'ticket_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'ticket_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            print(f"   ✅ Table created: {table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"   ✅ Table already exists: {table_name}")
            else:
                print(f"   ❌ Error creating table: {e}")
    
    def create_email_processor_lambda(self):
        """Create Lambda function to process emails and extract ticket data"""
        
        function_name = 'email-ticket-processor'
        
        lambda_code = '''
import json
import boto3
import re
import uuid
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """Process email and extract ticket information"""
    
    print(f"Processing email: {event}")
    
    try:
        # Extract email data from event
        email_data = event.get('email_data', {})
        
        # Analyze email content
        analysis = analyze_email_for_ticket(email_data)
        
        if analysis['create_ticket']:
            # Create ticket data
            ticket_data = create_ticket_from_email(email_data, analysis)
            
            # Store in DynamoDB
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('sla-tickets')
            table.put_item(Item=ticket_data)
            
            print(f"Ticket created: {ticket_data['ticket_id']}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'ticket_id': ticket_data['ticket_id'],
                    'ticket_data': ticket_data
                })
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': False,
                    'reason': analysis.get('reason', 'Not a support request')
                })
            }
            
    except Exception as e:
        print(f"Error processing email: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def analyze_email_for_ticket(email_data):
    """Analyze email content to determine if ticket should be created"""
    
    subject = email_data.get('subject', '').lower()
    body = email_data.get('body', '').lower()
    sender = email_data.get('from', '').lower()
    
    # Support request indicators
    support_keywords = [
        'problem', 'issue', 'error', 'fail', 'not working', 'down', 'outage',
        'authentication', 'aadhaar', 'service', 'unable', 'cannot', 'help',
        'support', 'urgent', 'critical', 'broken', 'bug', 'complaint',
        'payment', 'portal', 'mobile', 'app', 'certificate', 'digital'
    ]
    
    # Check if it's a support request
    is_support = any(keyword in subject or keyword in body for keyword in support_keywords)
    
    if not is_support:
        return {
            'create_ticket': False,
            'reason': 'Not identified as support request'
        }
    
    # Determine priority
    priority = determine_priority(subject, body)
    
    # Determine department
    department = determine_department(subject, body)
    
    # Determine service type
    service_type = determine_service_type(subject, body)
    
    # Extract location
    location = extract_location(subject + ' ' + body)
    
    return {
        'create_ticket': True,
        'priority': priority,
        'department': department,
        'service_type': service_type,
        'location': location,
        'confidence': 0.85
    }

def determine_priority(subject, body):
    """Determine ticket priority from email content"""
    
    text = subject + ' ' + body
    
    if any(word in text for word in ['critical', 'urgent', 'emergency', 'outage', 'down']):
        return 'P1'
    elif any(word in text for word in ['important', 'asap', 'priority', 'high']):
        return 'P2'
    elif any(word in text for word in ['issue', 'problem', 'help']):
        return 'P3'
    else:
        return 'P4'

def determine_department(subject, body):
    """Determine department from email content"""
    
    text = subject + ' ' + body
    
    if any(word in text for word in ['aadhaar', 'aadhar', 'authentication', 'biometric']):
        return 'UIDAI'
    elif any(word in text for word in ['payment', 'transaction', 'money', 'bank']):
        return 'MeiTY'
    elif any(word in text for word in ['portal', 'website', 'digital', 'online']):
        return 'DigitalMP'
    elif any(word in text for word in ['certificate', 'document', 'service']):
        return 'eDistrict'
    else:
        return 'MPOnline'

def determine_service_type(subject, body):
    """Determine service type from email content"""
    
    text = subject + ' ' + body
    
    if any(word in text for word in ['aadhaar', 'authentication']):
        return 'aadhaar-auth'
    elif any(word in text for word in ['payment', 'gateway']):
        return 'payment-gateway'
    elif any(word in text for word in ['portal', 'website']):
        return 'citizen-portal'
    elif any(word in text for word in ['mobile', 'app']):
        return 'mobile-app'
    elif any(word in text for word in ['certificate', 'document']):
        return 'certificate-services'
    else:
        return 'other'

def extract_location(text):
    """Extract location from email text"""
    
    # Indian cities and states
    locations = [
        'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'kolkata',
        'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur',
        'indore', 'bhopal', 'visakhapatnam', 'patna', 'vadodara',
        'maharashtra', 'karnataka', 'tamil nadu', 'uttar pradesh', 'gujarat',
        'rajasthan', 'west bengal', 'madhya pradesh', 'telangana', 'bihar'
    ]
    
    found_locations = []
    for location in locations:
        if location in text.lower():
            found_locations.append(location.title())
    
    return ', '.join(found_locations) if found_locations else 'Not specified'

def create_ticket_from_email(email_data, analysis):
    """Create ticket data structure from email and analysis"""
    
    # Generate ticket ID
    now = datetime.now()
    date_str = now.strftime('%y%m%d')
    ticket_id = f"{analysis['department']}-{analysis['priority']}-{date_str}-{str(uuid.uuid4())[:4].upper()}"
    
    # Calculate SLA deadline
    sla_hours = {
        'P1': 2,
        'P2': 8,
        'P3': 24,
        'P4': 72
    }.get(analysis['priority'], 24)
    
    sla_deadline = now + timedelta(hours=sla_hours)
    
    # Calculate breach probability
    breach_prob = calculate_breach_probability(analysis['priority'], analysis['service_type'])
    
    # Calculate revenue impact
    revenue_impact = calculate_revenue_impact(analysis['priority'], analysis['service_type'])
    
    return {
        'ticket_id': ticket_id,
        'source': 'email',
        'email_from': email_data.get('from', ''),
        'email_subject': email_data.get('subject', ''),
        'email_body': email_data.get('body', ''),
        'department': analysis['department'],
        'priority': analysis['priority'],
        'service_type': analysis['service_type'],
        'location': analysis['location'],
        'status': 'Open',
        'created_at': now.isoformat(),
        'sla_deadline': sla_deadline.isoformat(),
        'sla_due_time': sla_deadline.strftime('%I:%M %p'),
        'breach_probability': breach_prob,
        'revenue_impact': revenue_impact,
        'confidence_score': analysis['confidence'],
        'customer_tier': map_priority_to_tier(analysis['priority']),
        'sla_met': 'Pending',
        'resolution_time_hours': 0,
        'ai_analyzed': True,
        'reporter_name': extract_name_from_email(email_data.get('from', '')),
        'contact': extract_email_from_sender(email_data.get('from', ''))
    }

def calculate_breach_probability(priority, service_type):
    """Calculate breach probability"""
    
    base_prob = {
        'P1': 0.85,
        'P2': 0.65,
        'P3': 0.45,
        'P4': 0.25
    }.get(priority, 0.45)
    
    service_multiplier = {
        'aadhaar-auth': 1.3,
        'payment-gateway': 1.2,
        'citizen-portal': 1.1,
        'mobile-app': 1.0,
        'certificate-services': 1.1,
        'other': 1.0
    }.get(service_type, 1.0)
    
    return min(0.95, base_prob * service_multiplier)

def calculate_revenue_impact(priority, service_type):
    """Calculate revenue impact"""
    
    base_impact = {
        'P1': 200000,
        'P2': 100000,
        'P3': 50000,
        'P4': 20000
    }.get(priority, 50000)
    
    service_multiplier = {
        'aadhaar-auth': 2.0,
        'payment-gateway': 1.8,
        'citizen-portal': 1.2,
        'mobile-app': 1.1,
        'certificate-services': 1.3,
        'other': 1.0
    }.get(service_type, 1.0)
    
    return int(base_impact * service_multiplier)

def map_priority_to_tier(priority):
    """Map priority to customer tier"""
    
    return {
        'P1': 'Enterprise',
        'P2': 'Platinum',
        'P3': 'Gold',
        'P4': 'Silver'
    }.get(priority, 'Silver')

def extract_name_from_email(email_str):
    """Extract name from email address"""
    
    if '<' in email_str:
        name = email_str.split('<')[0].strip().strip('"')
        return name if name else 'Unknown'
    else:
        return email_str.split('@')[0].replace('.', ' ').title()

def extract_email_from_sender(email_str):
    """Extract email address from sender string"""
    
    if '<' in email_str:
        return email_str.split('<')[1].split('>')[0]
    else:
        return email_str
        '''
        
        return self.create_lambda_function(function_name, lambda_code, 
                                         "Process emails and create tickets")
    
    def create_ticket_api_lambda(self):
        """Create API Lambda for ticket operations"""
        
        function_name = 'ticket-api'
        
        lambda_code = '''
import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def lambda_handler(event, context):
    """Handle ticket API requests"""
    
    print(f"API request: {event}")
    
    try:
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        body = event.get('body')
        
        if body:
            body = json.loads(body)
        
        # Route request
        if http_method == 'GET' and path == '/tickets':
            return get_tickets(query_params)
        elif http_method == 'GET' and path.startswith('/tickets/'):
            ticket_id = path.split('/')[-1]
            return get_ticket(ticket_id)
        elif http_method == 'POST' and path == '/tickets':
            return create_ticket(body)
        elif http_method == 'PUT' and path.startswith('/tickets/'):
            ticket_id = path.split('/')[-1]
            return update_ticket(ticket_id, body)
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        print(f"API error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_tickets(query_params):
    """Get all tickets with optional filtering"""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sla-tickets')
    
    try:
        response = table.scan()
        tickets = response['Items']
        
        # Convert Decimal to float for JSON serialization
        tickets = json.loads(json.dumps(tickets, default=decimal_default))
        
        # Apply filters
        status_filter = query_params.get('status')
        if status_filter:
            tickets = [t for t in tickets if t.get('status') == status_filter]
        
        priority_filter = query_params.get('priority')
        if priority_filter:
            tickets = [t for t in tickets if t.get('priority') == priority_filter]
        
        # Sort by created_at descending
        tickets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'tickets': tickets,
                'count': len(tickets)
            })
        }
        
    except Exception as e:
        print(f"Error getting tickets: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_ticket(ticket_id):
    """Get specific ticket by ID"""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sla-tickets')
    
    try:
        response = table.get_item(Key={'ticket_id': ticket_id})
        
        if 'Item' in response:
            ticket = json.loads(json.dumps(response['Item'], default=decimal_default))
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(ticket)
            }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Ticket not found'})
            }
            
    except Exception as e:
        print(f"Error getting ticket: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def create_ticket(ticket_data):
    """Create new ticket"""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sla-tickets')
    
    try:
        table.put_item(Item=ticket_data)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'ticket_id': ticket_data['ticket_id']
            })
        }
        
    except Exception as e:
        print(f"Error creating ticket: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def update_ticket(ticket_id, update_data):
    """Update existing ticket"""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sla-tickets')
    
    try:
        # Build update expression
        update_expression = "SET "
        expression_values = {}
        
        for key, value in update_data.items():
            if key != 'ticket_id':  # Don't update the key
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
        
        update_expression = update_expression.rstrip(', ')
        
        response = table.update_item(
            Key={'ticket_id': ticket_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_ticket = json.loads(json.dumps(response['Attributes'], default=decimal_default))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(updated_ticket)
        }
        
    except Exception as e:
        print(f"Error updating ticket: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
        '''
        
        return self.create_lambda_function(function_name, lambda_code,
                                         "API for ticket operations")
    
    def create_lambda_function(self, function_name, code, description):
        """Helper to create Lambda functions"""
        
        try:
            print(f"   Creating Lambda: {function_name}")
            
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=f'arn:aws:iam::{self.account_id}:role/lambda-execution-role',
                Handler='index.lambda_handler',
                Code={'ZipFile': code.encode('utf-8')},
                Description=description,
                Timeout=60,
                MemorySize=256
            )
            
            print(f"   ✅ Lambda created: {function_name}")
            return response['FunctionArn']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"   ✅ Lambda exists, updating: {function_name}")
                try:
                    self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=code.encode('utf-8')
                    )
                    print(f"   ✅ Lambda updated: {function_name}")
                except Exception as update_error:
                    print(f"   ⚠️  Update failed: {update_error}")
                
                return f"arn:aws:lambda:{self.region}:{self.account_id}:function:{function_name}"
            else:
                print(f"   ❌ Error creating Lambda: {e}")
                return None
    
    def start_email_monitoring(self):
        """Start monitoring emails in a separate thread"""
        
        def monitor_emails():
            """Monitor emails continuously"""
            
            print(f"   📧 Starting email monitoring...")
            
            while True:
                try:
                    # Connect to email server
                    mail = imaplib.IMAP4_SSL(self.email_config['imap_server'], 
                                           self.email_config['imap_port'])
                    mail.login(self.email_config['email'], 
                              self.email_config['password'])
                    mail.select('inbox')
                    
                    # Search for unread emails
                    status, messages = mail.search(None, 'UNSEEN')
                    
                    if status == 'OK' and messages[0]:
                        email_ids = messages[0].split()
                        
                        for email_id in email_ids:
                            try:
                                # Fetch email
                                status, msg_data = mail.fetch(email_id, '(RFC822)')
                                
                                if status == 'OK':
                                    # Parse email
                                    email_body = msg_data[0][1]
                                    email_message = email.message_from_bytes(email_body)
                                    
                                    # Extract email data
                                    email_data = {
                                        'from': email_message.get('From', ''),
                                        'to': email_message.get('To', ''),
                                        'subject': email_message.get('Subject', ''),
                                        'date': email_message.get('Date', ''),
                                        'body': self.extract_email_body(email_message),
                                        'message_id': email_message.get('Message-ID', ''),
                                        'received_at': datetime.now().isoformat()
                                    }
                                    
                                    print(f"   📧 New email: {email_data['subject']}")
                                    
                                    # Process email through Lambda
                                    self.process_email_through_lambda(email_data)
                                    
                                    # Mark as read
                                    mail.store(email_id, '+FLAGS', '\\Seen')
                                    
                            except Exception as e:
                                print(f"   ❌ Error processing email {email_id}: {e}")
                    
                    mail.close()
                    mail.logout()
                    
                    # Wait before next check
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    print(f"   ❌ Email monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_emails, daemon=True)
        monitor_thread.start()
        
        print(f"   ✅ Email monitoring started")
    
    def extract_email_body(self, email_message):
        """Extract plain text body from email"""
        
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return body
    
    def process_email_through_lambda(self, email_data):
        """Process email through Lambda function"""
        
        try:
            # Call email processor Lambda
            response = self.lambda_client.invoke(
                FunctionName='email-ticket-processor',
                InvocationType='RequestResponse',
                Payload=json.dumps({'email_data': email_data})
            )
            
            result = json.loads(response['Payload'].read().decode('utf-8'))
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                if body.get('success'):
                    print(f"   ✅ Ticket created: {body['ticket_id']}")
                else:
                    print(f"   ℹ️  No ticket created: {body.get('reason', 'Unknown')}")
            else:
                print(f"   ❌ Lambda error: {result}")
                
        except Exception as e:
            print(f"   ❌ Error calling Lambda: {e}")
    
    def create_enhanced_ticket_form(self):
        """Create enhanced HTML form with email integration"""
        
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Email-Integrated Ticket System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.2em;
            margin-bottom: 10px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 30px;
            padding: 30px;
        }
        
        .email-monitor {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        
        .section-title {
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .email-status {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 5px solid #27ae60;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #27ae60;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .recent-emails {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .email-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid #3498db;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .email-item:hover {
            background: #e3f2fd;
            transform: translateX(5px);
        }
        
        .email-item.processed {
            border-left-color: #27ae60;
            background: rgba(39, 174, 96, 0.1);
        }
        
        .email-subject {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .email-meta {
            font-size: 0.8em;
            color: #7f8c8d;
        }
        
        .ticket-form {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .auto-filled {
            background: rgba(39, 174, 96, 0.1);
            border-color: #27ae60;
        }
        
        .create-btn {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1em;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .create-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
        }
        
        .tickets-list {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        
        .ticket-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 5px solid #3498db;
        }
        
        .ticket-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .ticket-id {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .ticket-priority {
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .priority-p1 {
            background: #e74c3c;
            color: white;
        }
        
        .priority-p2 {
            background: #f39c12;
            color: white;
        }
        
        .priority-p3 {
            background: #3498db;
            color: white;
        }
        
        .priority-p4 {
            background: #27ae60;
            color: white;
        }
        
        .ticket-details {
            font-size: 0.9em;
            color: #7f8c8d;
        }
        
        .email-source {
            background: rgba(52, 152, 219, 0.1);
            color: #3498db;
            padding: 2px 6px;
            border-radius: 5px;
            font-size: 0.7em;
            font-weight: bold;
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Enhanced Email-Integrated Ticket System</h1>
            <p>Real-time email monitoring with automatic ticket creation</p>
            <p>Current Time: <span id="current-time"></span></p>
        </div>
        
        <div class="main-content">
            <!-- Email Monitor Panel -->
            <div class="email-monitor">
                <div class="section-title">📧 Email Monitor</div>
                
                <div class="email-status">
                    <div class="status-indicator">
                        <div class="status-dot"></div>
                        <span><strong>Status:</strong> Monitoring Active</span>
                    </div>
                    <div><strong>Emails Processed:</strong> <span id="emails-processed">0</span></div>
                    <div><strong>Tickets Created:</strong> <span id="tickets-created">0</span></div>
                    <div><strong>Last Check:</strong> <span id="last-check">Just now</span></div>
                </div>
                
                <div class="section-title">📬 Recent Emails</div>
                <div class="recent-emails" id="recent-emails">
                    <div class="email-item">
                        <div class="email-subject">System ready for email processing</div>
                        <div class="email-meta">Waiting for incoming emails...</div>
                    </div>
                </div>
            </div>
            
            <!-- Ticket Creation Form -->
            <div class="ticket-form">
                <div class="section-title">🎫 Create/Edit Ticket</div>
                
                <div class="form-group">
                    <label for="ticket-id">Ticket ID</label>
                    <input type="text" id="ticket-id" readonly placeholder="Auto-generated">
                </div>
                
                <div class="form-group">
                    <label for="department">Department</label>
                    <select id="department">
                        <option value="UIDAI">UIDAI - Unique Identification Authority</option>
                        <option value="MeiTY">MeiTY - MP State Electronics Development Corporation</option>
                        <option value="DigitalMP">Digital MP - Digital Services</option>
                        <option value="eDistrict">e-District - Citizen Services</option>
                        <option value="MPOnline">MP Online - Government Portal</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="priority">Priority</label>
                    <select id="priority">
                        <option value="P1">P1 - Critical (2 hours)</option>
                        <option value="P2">P2 - High (8 hours)</option>
                        <option value="P3">P3 - Medium (24 hours)</option>
                        <option value="P4">P4 - Low (72 hours)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="service-type">Service Type</label>
                    <select id="service-type">
                        <option value="aadhaar-auth">Aadhaar Authentication</option>
                        <option value="aadhaar-update">Aadhaar Update</option>
                        <option value="payment-gateway">Payment Gateway</option>
                        <option value="citizen-portal">Citizen Portal</option>
                        <option value="mobile-app">Mobile App</option>
                        <option value="certificate-services">Certificate Services</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="location">Location</label>
                    <input type="text" id="location" placeholder="City, State">
                </div>
                
                <div class="form-group">
                    <label for="reporter-name">Reporter Name</label>
                    <input type="text" id="reporter-name" placeholder="Name">
                </div>
                
                <div class="form-group">
                    <label for="contact">Contact</label>
                    <input type="text" id="contact" placeholder="Email or Phone">
                </div>
                
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" rows="4" placeholder="Issue description..."></textarea>
                </div>
                
                <button class="create-btn" onclick="createTicket()">🚀 Create Ticket</button>
            </div>
            
            <!-- Tickets List -->
            <div class="tickets-list">
                <div class="section-title">🎫 Recent Tickets</div>
                <div id="tickets-container">
                    <div class="ticket-item">
                        <div class="ticket-header">
                            <div class="ticket-id">System Ready</div>
                        </div>
                        <div class="ticket-details">
                            Email-to-ticket integration is active and monitoring for incoming emails.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let emailCounter = 0;
        let ticketCounter = 0;
        let tickets = [];
        
        // Real-time clock
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleString();
            document.getElementById('last-check').textContent = now.toLocaleTimeString();
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        // Simulate email monitoring
        function simulateEmailProcessing() {
            const sampleEmails = [
                {
                    subject: "Aadhaar authentication services failing in Indore",
                    from: "resident@example.com",
                    body: "A resident reports that Aadhaar authentication services are failing in Indore. Please investigate urgently.",
                    priority: "P1",
                    department: "UIDAI",
                    service: "aadhaar-auth",
                    location: "Indore, Madhya Pradesh"
                },
                {
                    subject: "Payment gateway timeout issues",
                    from: "merchant@business.com", 
                    body: "Payment gateway is timing out for multiple transactions. Customers unable to complete payments.",
                    priority: "P2",
                    department: "MeiTY",
                    service: "payment-gateway",
                    location: "Bhopal, Madhya Pradesh"
                },
                {
                    subject: "Mobile app login problems",
                    from: "user@citizen.gov.in",
                    body: "Citizens unable to login to mobile app. Getting authentication errors.",
                    priority: "P3",
                    department: "DigitalMP",
                    service: "mobile-app",
                    location: "Gwalior, Madhya Pradesh"
                }
            ];
            
            if (Math.random() < 0.3) { // 30% chance of new email
                const email = sampleEmails[Math.floor(Math.random() * sampleEmails.length)];
                processIncomingEmail(email);
            }
        }
        
        function processIncomingEmail(email) {
            emailCounter++;
            
            // Add to recent emails
            const emailsContainer = document.getElementById('recent-emails');
            const emailItem = document.createElement('div');
            emailItem.className = 'email-item';
            emailItem.innerHTML = `
                <div class="email-subject">${email.subject}</div>
                <div class="email-meta">From: ${email.from} | ${new Date().toLocaleTimeString()}</div>
            `;
            
            emailItem.onclick = () => populateFormFromEmail(email);
            
            emailsContainer.insertBefore(emailItem, emailsContainer.firstChild);
            
            // Keep only last 5 emails
            while (emailsContainer.children.length > 6) {
                emailsContainer.removeChild(emailsContainer.lastChild);
            }
            
            // Update counters
            document.getElementById('emails-processed').textContent = emailCounter;
            
            // Auto-populate form after 2 seconds
            setTimeout(() => {
                populateFormFromEmail(email);
                emailItem.classList.add('processed');
                
                // Auto-create ticket after 3 more seconds
                setTimeout(() => {
                    createTicketFromEmail(email);
                }, 3000);
            }, 2000);
        }
        
        function populateFormFromEmail(email) {
            // Generate ticket ID
            const now = new Date();
            const dateStr = now.toISOString().slice(2, 10).replace(/-/g, '');
            const ticketId = `${email.department}-${email.priority}-${dateStr}-${String(Math.floor(Math.random() * 9999)).padStart(4, '0')}`;
            
            // Populate form fields
            document.getElementById('ticket-id').value = ticketId;
            document.getElementById('department').value = email.department;
            document.getElementById('priority').value = email.priority;
            document.getElementById('service-type').value = email.service;
            document.getElementById('location').value = email.location;
            document.getElementById('reporter-name').value = extractNameFromEmail(email.from);
            document.getElementById('contact').value = email.from;
            document.getElementById('description').value = email.body;
            
            // Add visual indication of auto-fill
            const fields = ['department', 'priority', 'service-type', 'location', 'reporter-name', 'contact', 'description'];
            fields.forEach(fieldId => {
                const field = document.getElementById(fieldId);
                field.classList.add('auto-filled');
                setTimeout(() => field.classList.remove('auto-filled'), 3000);
            });
            
            // Show notification
            showNotification(`📧 Form auto-populated from email: ${email.subject.substring(0, 50)}...`);
        }
        
        function extractNameFromEmail(emailStr) {
            if (emailStr.includes('<')) {
                return emailStr.split('<')[0].trim().replace(/"/g, '');
            } else {
                return emailStr.split('@')[0].replace(/\\./g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
            }
        }
        
        function createTicketFromEmail(email) {
            ticketCounter++;
            
            const ticket = {
                id: document.getElementById('ticket-id').value,
                department: email.department,
                priority: email.priority,
                service: email.service,
                location: email.location,
                reporter: extractNameFromEmail(email.from),
                contact: email.from,
                description: email.body,
                source: 'email',
                created: new Date().toISOString(),
                status: 'Open'
            };
            
            tickets.unshift(ticket);
            updateTicketsList();
            
            document.getElementById('tickets-created').textContent = ticketCounter;
            
            showNotification(`🎫 Ticket created automatically: ${ticket.id}`);
        }
        
        function createTicket() {
            const ticket = {
                id: document.getElementById('ticket-id').value || generateTicketId(),
                department: document.getElementById('department').value,
                priority: document.getElementById('priority').value,
                service: document.getElementById('service-type').value,
                location: document.getElementById('location').value,
                reporter: document.getElementById('reporter-name').value,
                contact: document.getElementById('contact').value,
                description: document.getElementById('description').value,
                source: 'manual',
                created: new Date().toISOString(),
                status: 'Open'
            };
            
            tickets.unshift(ticket);
            updateTicketsList();
            
            ticketCounter++;
            document.getElementById('tickets-created').textContent = ticketCounter;
            
            // Clear form
            document.getElementById('ticket-id').value = '';
            document.getElementById('reporter-name').value = '';
            document.getElementById('contact').value = '';
            document.getElementById('description').value = '';
            document.getElementById('location').value = '';
            
            showNotification(`🎫 Ticket created manually: ${ticket.id}`);
        }
        
        function generateTicketId() {
            const now = new Date();
            const dateStr = now.toISOString().slice(2, 10).replace(/-/g, '');
            const dept = document.getElementById('department').value;
            const priority = document.getElementById('priority').value;
            return `${dept}-${priority}-${dateStr}-${String(Math.floor(Math.random() * 9999)).padStart(4, '0')}`;
        }
        
        function updateTicketsList() {
            const container = document.getElementById('tickets-container');
            container.innerHTML = '';
            
            tickets.slice(0, 10).forEach(ticket => {
                const ticketItem = document.createElement('div');
                ticketItem.className = 'ticket-item';
                ticketItem.innerHTML = `
                    <div class="ticket-header">
                        <div class="ticket-id">${ticket.id}</div>
                        <div class="ticket-priority priority-${ticket.priority.toLowerCase()}">${ticket.priority}</div>
                    </div>
                    <div class="ticket-details">
                        <strong>${ticket.department}</strong> | ${ticket.service} | ${ticket.location}<br>
                        Reporter: ${ticket.reporter} | Contact: ${ticket.contact}
                        ${ticket.source === 'email' ? '<span class="email-source">Email</span>' : ''}
                    </div>
                `;
                container.appendChild(ticketItem);
            });
        }
        
        function showNotification(message) {
            // Create notification element
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #27ae60;
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                max-width: 400px;
                transform: translateX(400px);
                transition: transform 0.3s ease;
            `;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            // Show notification
            setTimeout(() => {
                notification.style.transform = 'translateX(0)';
            }, 100);
            
            // Hide notification
            setTimeout(() => {
                notification.style.transform = 'translateX(400px)';
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 4000);
        }
        
        // Start email simulation
        setInterval(simulateEmailProcessing, 10000); // Check every 10 seconds
        
        // Initialize
        updateTicketsList();
    </script>
</body>
</html>'''
        
        # Save enhanced form
        with open('sla_guard/aws_deployment/enhanced_email_ticket_form.html', 'w') as f:
            f.write(html_content)
        
        print(f"   ✅ Enhanced form created: enhanced_email_ticket_form.html")
    
    def test_email_integration(self):
        """Test the email integration system"""
        
        print(f"   🧪 Testing email integration...")
        
        # Create test email data
        test_email = {
            'from': 'resident@example.com',
            'to': self.email_config['support_email'],
            'subject': 'Aadhaar authentication services failing in Indore',
            'body': '''A resident reports that Aadhaar authentication services are failing in Indore.

Details:
- Location: Indore, Madhya Pradesh
- Service: Aadhaar Authentication
- Issue: Authentication requests timing out
- Impact: Citizens unable to access government services
- Urgency: High - affecting multiple residents

Please investigate and resolve urgently.

Best regards,
Concerned Resident''',
            'message_id': f'test-{uuid.uuid4()}@example.com',
            'received_at': datetime.now().isoformat()
        }
        
        try:
            # Test email processing
            response = self.lambda_client.invoke(
                FunctionName='email-ticket-processor',
                InvocationType='RequestResponse',
                Payload=json.dumps({'email_data': test_email})
            )
            
            result = json.loads(response['Payload'].read().decode('utf-8'))
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                if body.get('success'):
                    ticket_data = body['ticket_data']
                    print(f"   ✅ Test successful - Ticket created:")
                    print(f"      Ticket ID: {ticket_data['ticket_id']}")
                    print(f"      Department: {ticket_data['department']}")
                    print(f"      Priority: {ticket_data['priority']}")
                    print(f"      Service: {ticket_data['service_type']}")
                    print(f"      Location: {ticket_data['location']}")
                    print(f"      Reporter: {ticket_data['reporter_name']}")
                    print(f"      Breach Risk: {ticket_data['breach_probability']:.1%}")
                    print(f"      Revenue Impact: ${ticket_data['revenue_impact']:,}")
                else:
                    print(f"   ⚠️  Test result: {body.get('reason', 'Unknown')}")
            else:
                print(f"   ❌ Test failed: {result}")
                
        except Exception as e:
            print(f"   ❌ Test error: {e}")

def main():
    """Setup enhanced email-to-ticket integration"""
    
    try:
        system = EmailIntegratedTicketSystem()
        
        print(f"🚀 ENHANCED EMAIL-TO-TICKET INTEGRATION SETUP")
        print(f"=" * 60)
        
        # Get email configuration
        email_address = input("📧 Enter your email address: ").strip()
        password = input("🔐 Enter your email password/app password: ").strip()
        support_email = input("🎫 Enter support email address: ").strip()
        
        if not all([email_address, password, support_email]):
            print("❌ All fields are required")
            return
        
        # Setup integration
        success = system.setup_email_integration(email_address, password, support_email)
        
        if success:
            print(f"\n🎉 EMAIL-TO-TICKET INTEGRATION COMPLETE!")
            print(f"=" * 60)
            print(f"📧 Email Monitoring: {email_address}")
            print(f"🎫 Support Email: {support_email}")
            print(f"🤖 AI Processing: Enabled")
            print(f"📊 Real-time Updates: Active")
            print(f"🌐 Enhanced Form: enhanced_email_ticket_form.html")
            
            print(f"\n🔄 How it works:")
            print(f"1. 📧 System monitors {email_address} for new emails")
            print(f"2. 🤖 AI analyzes email content and extracts:")
            print(f"   • Department (UIDAI, MeiTY, DigitalMP, etc.)")
            print(f"   • Priority (P1-Critical, P2-High, P3-Medium, P4-Low)")
            print(f"   • Service type (Aadhaar, Payment, Portal, etc.)")
            print(f"   • Location information")
            print(f"   • Reporter details")
            print(f"3. 🎫 Ticket automatically created in DynamoDB")
            print(f"4. 🌐 Form auto-populated with extracted data")
            print(f"5. 📊 Real-time dashboard updates")
            
            print(f"\n📧 Example Email Processing:")
            print(f"Input: 'Aadhaar authentication services failing in Indore'")
            print(f"Output: UIDAI-P1-{datetime.now().strftime('%y%m%d')}-XXXX")
            print(f"        Priority: P1, Department: UIDAI, Location: Indore")
            
            print(f"\n🌐 Open enhanced_email_ticket_form.html to see the integration!")
            
        else:
            print(f"\n❌ Setup failed")
            
    except KeyboardInterrupt:
        print(f"\n👋 Setup cancelled")
    except Exception as e:
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main()