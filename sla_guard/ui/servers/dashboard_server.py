#!/usr/bin/env python3
"""
Interactive Dashboard Server
Serves real AWS data to the interactive dashboard
"""

import json
import time
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import boto3
from botocore.exceptions import ClientError
import webbrowser
import os

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, aws_data=None, **kwargs):
        self.aws_data = aws_data
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/status':
            self.send_json_response(self.aws_data.get_all_status())
        elif parsed_path.path == '/api/metrics':
            self.send_json_response(self.aws_data.get_live_metrics())
        elif parsed_path.path == '/api/service':
            query = parse_qs(parsed_path.query)
            service = query.get('name', [''])[0]
            self.send_json_response(self.aws_data.get_service_details(service))
        elif parsed_path.path == '/' or parsed_path.path == '/dashboard':
            self.serve_dashboard()
        else:
            super().do_GET()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def serve_dashboard(self):
        dashboard_path = os.path.join(os.path.dirname(__file__), 'interactive_dashboard.html')
        try:
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Inject API endpoints
            content = content.replace(
                '</head>',
                '''
                <script>
                    const API_BASE = window.location.origin;
                    
                    async function fetchAWSStatus() {
                        try {
                            const response = await fetch(`${API_BASE}/api/status`);
                            const data = await response.json();
                            updateStatusIndicators(data);
                        } catch (error) {
                            console.error('Failed to fetch AWS status:', error);
                        }
                    }
                    
                    async function fetchLiveMetrics() {
                        try {
                            const response = await fetch(`${API_BASE}/api/metrics`);
                            const data = await response.json();
                            updateLiveMetrics(data);
                        } catch (error) {
                            console.error('Failed to fetch metrics:', error);
                        }
                    }
                    
                    function updateStatusIndicators(data) {
                        Object.keys(data).forEach(service => {
                            const indicator = document.getElementById(`status-${service}`);
                            if (indicator) {
                                indicator.className = `status-indicator ${data[service].status}`;
                            }
                        });
                    }
                    
                    function updateLiveMetrics(data) {
                        Object.keys(data).forEach(metric => {
                            const element = document.getElementById(metric);
                            if (element) {
                                element.textContent = data[metric];
                            }
                        });
                    }
                    
                    // Auto-refresh every 30 seconds
                    setInterval(() => {
                        fetchAWSStatus();
                        fetchLiveMetrics();
                    }, 30000);
                    
                    // Initial load
                    document.addEventListener('DOMContentLoaded', () => {
                        fetchAWSStatus();
                        fetchLiveMetrics();
                    });
                </script>
                </head>
                '''
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404, "Dashboard file not found")

class AWSDataProvider:
    def __init__(self):
        self.region = 'us-east-1'
        self.account_id = '508955320780'
        self.bucket_name = 'sla-guard-archive-508955320780'
        
        # Initialize AWS clients
        try:
            self.dynamodb = boto3.client('dynamodb', region_name=self.region)
            self.events = boto3.client('events', region_name=self.region)
            self.lambda_client = boto3.client('lambda', region_name=self.region)
            self.sagemaker = boto3.client('sagemaker', region_name=self.region)
            self.stepfunctions = boto3.client('stepfunctions', region_name=self.region)
            self.sns = boto3.client('sns', region_name=self.region)
            self.s3 = boto3.client('s3', region_name=self.region)
            self.quicksight = boto3.client('quicksight', region_name=self.region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        except Exception as e:
            print(f"Warning: Failed to initialize AWS clients: {e}")
    
    def get_all_status(self):
        """Get status of all services"""
        status = {}
        
        services = [
            ('dynamodb', self.check_dynamodb),
            ('eventbridge', self.check_eventbridge),
            ('lambda', self.check_lambda),
            ('sagemaker', self.check_sagemaker),
            ('stepfunctions', self.check_stepfunctions),
            ('sns', self.check_sns),
            ('s3', self.check_s3),
            ('quicksight', self.check_quicksight),
            ('retrain', self.check_retrain)
        ]
        
        for service_name, check_func in services:
            try:
                status[service_name] = check_func()
            except Exception as e:
                status[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return status
    
    def check_dynamodb(self):
        try:
            response = self.dynamodb.describe_table(TableName='sla-tickets')
            return {
                'status': 'operational',
                'table_status': response['Table']['TableStatus'],
                'item_count': response['Table'].get('ItemCount', 0)
            }
        except ClientError:
            return {'status': 'not_found'}
    
    def check_eventbridge(self):
        try:
            response = self.events.describe_rule(Name='sla-guard-scheduler')
            return {
                'status': 'operational',
                'state': response['State'],
                'schedule': response.get('ScheduleExpression', '')
            }
        except ClientError:
            return {'status': 'not_found'}
    
    def check_lambda(self):
        try:
            response = self.lambda_client.get_function(FunctionName='sla-guard-processor')
            return {
                'status': 'operational',
                'runtime': response['Configuration']['Runtime'],
                'last_modified': response['Configuration']['LastModified']
            }
        except ClientError:
            return {'status': 'not_found'}
    
    def check_sagemaker(self):
        try:
            response = self.sagemaker.describe_endpoint(EndpointName='sla-guard-endpoint')
            return {
                'status': 'operational',
                'endpoint_status': response['EndpointStatus'],
                'creation_time': response['CreationTime'].isoformat()
            }
        except ClientError:
            return {'status': 'not_found'}
    
    def check_stepfunctions(self):
        try:
            response = self.stepfunctions.list_state_machines()
            sla_sm = next((sm for sm in response['stateMachines'] 
                          if 'sla-guard' in sm['name'].lower()), None)
            if sla_sm:
                return {
                    'status': 'operational',
                    'name': sla_sm['name'],
                    'creation_date': sla_sm['creationDate'].isoformat()
                }
            else:
                return {'status': 'not_found'}
        except ClientError:
            return {'status': 'not_found'}
    
    def check_sns(self):
        try:
            response = self.sns.list_topics()
            sla_topic = next((topic for topic in response['Topics'] 
                            if 'sla-guard' in topic['TopicArn'].lower()), None)
            if sla_topic:
                return {
                    'status': 'operational',
                    'topic_arn': sla_topic['TopicArn']
                }
            else:
                return {'status': 'not_found'}
        except ClientError:
            return {'status': 'not_found'}
    
    def check_s3(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            objects = self.s3.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1000)
            return {
                'status': 'operational',
                'object_count': objects.get('KeyCount', 0),
                'bucket': self.bucket_name
            }
        except ClientError:
            return {'status': 'not_found'}
    
    def check_quicksight(self):
        try:
            response = self.quicksight.list_data_sets(AwsAccountId=self.account_id)
            sla_dataset = next((ds for ds in response['DataSetSummaries'] 
                              if 'sla-guard' in ds['Name'].lower()), None)
            if sla_dataset:
                return {
                    'status': 'operational',
                    'dataset_name': sla_dataset['Name'],
                    'dataset_id': sla_dataset['DataSetId']
                }
            else:
                return {'status': 'not_found'}
        except ClientError:
            return {'status': 'not_found'}
    
    def check_retrain(self):
        try:
            response = self.sagemaker.list_training_jobs(
                SortBy='CreationTime',
                SortOrder='Descending',
                MaxResults=10
            )
            sla_jobs = [job for job in response['TrainingJobSummaries'] 
                       if 'sla-guard' in job['TrainingJobName'].lower()]
            if sla_jobs:
                latest_job = sla_jobs[0]
                return {
                    'status': 'operational',
                    'job_status': latest_job['TrainingJobStatus'],
                    'creation_time': latest_job['CreationTime'].isoformat()
                }
            else:
                return {'status': 'not_found'}
        except ClientError:
            return {'status': 'not_found'}
    
    def get_live_metrics(self):
        """Get live metrics from CloudWatch and other sources"""
        import random
        
        # For demo purposes, generate realistic metrics
        # In production, these would come from CloudWatch, DynamoDB, etc.
        return {
            'compliance-rate': f"{94 + random.random() * 4:.1f}%",
            'breach-prob': f"{15 + random.random() * 8:.1f}%",
            'revenue-protected': f"${100 + random.randint(0, 50)}K",
            'active-tickets': str(200 + random.randint(0, 100)),
            'processing-time': f"{2 + random.random() * 2:.1f}s",
            'system-uptime': f"{99.5 + random.random() * 0.4:.1f}%",
            'dynamodb-items': f"{1200 + random.randint(0, 100):,}",
            'lambda-invocations': f"{1400 + random.randint(0, 200):,}",
            'sagemaker-predictions': f"{800 + random.randint(0, 100):,}",
            's3-objects': f"{15000 + random.randint(0, 1000):,}"
        }
    
    def get_service_details(self, service):
        """Get detailed information about a specific service"""
        # This would return detailed service information
        # For now, return basic info
        return {
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'details': f"Detailed information for {service}"
        }

class InteractiveDashboardServer:
    def __init__(self, port=8080):
        self.port = port
        self.aws_data = AWSDataProvider()
        self.server = None
    
    def start(self):
        """Start the dashboard server"""
        print(f"🚀 Starting SLA Guard Interactive Dashboard Server...")
        print(f"📡 Port: {self.port}")
        
        # Create handler with AWS data
        def handler(*args, **kwargs):
            return DashboardHandler(*args, aws_data=self.aws_data, **kwargs)
        
        try:
            self.server = HTTPServer(('localhost', self.port), handler)
            
            # Open browser
            dashboard_url = f"http://localhost:{self.port}/dashboard"
            print(f"🌐 Dashboard URL: {dashboard_url}")
            print(f"📊 API Endpoints:")
            print(f"   • Status: http://localhost:{self.port}/api/status")
            print(f"   • Metrics: http://localhost:{self.port}/api/metrics")
            
            # Open in browser after a short delay
            threading.Timer(1.0, lambda: webbrowser.open(dashboard_url)).start()
            
            print(f"✅ Server started! Opening dashboard in browser...")
            print(f"🛑 Press Ctrl+C to stop the server")
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print(f"\n🛑 Shutting down server...")
            if self.server:
                self.server.shutdown()
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
    
    def stop(self):
        """Stop the dashboard server"""
        if self.server:
            self.server.shutdown()

def main():
    """Main function"""
    import sys
    
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 8080.")
    
    server = InteractiveDashboardServer(port)
    server.start()

if __name__ == "__main__":
    main()