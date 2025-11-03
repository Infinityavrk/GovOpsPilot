#!/usr/bin/env python3
"""
Complete QuickSight Automation Script
Handles manifest upload, data source, dataset, and dashboard creation
"""

import boto3
import json
import time
import sys
from botocore.exceptions import ClientError

class QuickSightAutomation:
    def __init__(self):
        self.bucket_name = 'sla-guard-archive-508955320780'
        self.account_id = '508955320780'
        self.region = 'us-east-1'
        
        # Explicitly set region for all clients
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.quicksight_client = boto3.client('quicksight', region_name=self.region)
        self.user_arn = None  # Will be determined dynamically
        
    def get_quicksight_user(self):
        """Get the current QuickSight user ARN"""
        print("👤 Finding QuickSight user...")
        
        try:
            # List all users in the default namespace
            response = self.quicksight_client.list_users(
                AwsAccountId=self.account_id,
                Namespace='default'
            )
            
            users = response.get('UserList', [])
            if not users:
                print("❌ No QuickSight users found")
                return None
            
            # Get current AWS identity
            sts_client = boto3.client('sts', region_name=self.region)
            identity = sts_client.get_caller_identity()
            current_user_id = identity.get('UserId', '').split(':')[-1]  # Extract username part
            
            print(f"🔍 Current AWS user: {current_user_id}")
            print(f"📋 Available QuickSight users:")
            
            for user in users:
                username = user.get('UserName', '')
                arn = user.get('Arn', '')
                role = user.get('Role', '')
                print(f"   - {username} ({role}) - {arn}")
            
            # Try to find matching user or use the first admin/author
            selected_user = None
            
            # First, try to find exact match
            for user in users:
                if current_user_id.lower() in user.get('UserName', '').lower():
                    selected_user = user
                    break
            
            # If no exact match, use first admin or author
            if not selected_user:
                for user in users:
                    role = user.get('Role', '')
                    if role in ['ADMIN', 'AUTHOR']:
                        selected_user = user
                        break
            
            # If still no match, use first user
            if not selected_user and users:
                selected_user = users[0]
            
            if selected_user:
                self.user_arn = selected_user['Arn']
                print(f"✅ Using QuickSight user: {selected_user['UserName']}")
                print(f"🔗 User ARN: {self.user_arn}")
                return self.user_arn
            else:
                print("❌ No suitable QuickSight user found")
                return None
                
        except ClientError as e:
            print(f"❌ Error getting QuickSight users: {e}")
            return None
    
    def step_1_upload_manifest(self):
        """Step 1: Upload manifest file to S3"""
        print("📤 Step 1: Uploading manifest file to S3...")
        
        manifest_content = {
            "fileLocations": [
                {
                    "URIPrefixes": [f"s3://{self.bucket_name}/"]
                }
            ],
            "globalUploadSettings": {
                "format": "JSON",
                "delimiter": ",",
                "textqualifier": "\"",
                "containsHeader": "true"
            }
        }
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key='quicksight_manifest.json',
                Body=json.dumps(manifest_content, indent=2),
                ContentType='application/json'
            )
            print(f"✅ Manifest uploaded to s3://{self.bucket_name}/quicksight_manifest.json")
            return True
        except ClientError as e:
            print(f"❌ Failed to upload manifest: {e}")
            return False
    
    def step_2_create_data_source(self):
        """Step 2: Create QuickSight data source"""
        print("🔗 Step 2: Creating QuickSight data source...")
        
        data_source_id = 'sla-guard-data-source'
        
        try:
            self.quicksight_client.create_data_source(
                AwsAccountId=self.account_id,
                DataSourceId=data_source_id,
                Name='SLA Guard Production Data',
                Type='S3',
                DataSourceParameters={
                    'S3Parameters': {
                        'ManifestFileLocation': {
                            'Bucket': self.bucket_name,
                            'Key': 'quicksight_manifest.json'
                        }
                    }
                },
                Permissions=[{
                    'Principal': self.user_arn,
                    'Actions': [
                        'quicksight:DescribeDataSource',
                        'quicksight:DescribeDataSourcePermissions',
                        'quicksight:PassDataSource',
                        'quicksight:UpdateDataSource',
                        'quicksight:DeleteDataSource'
                    ]
                }]
            )
            print(f"✅ Data source created: {data_source_id}")
            return data_source_id
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Data source already exists: {data_source_id}")
                return data_source_id
            print(f"❌ Failed to create data source: {e}")
            return None
    
    def step_3_create_dataset(self, data_source_id):
        """Step 3: Create QuickSight dataset"""
        print("📊 Step 3: Creating QuickSight dataset...")
        
        dataset_id = 'sla-guard-dataset'
        
        try:
            self.quicksight_client.create_data_set(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id,
                Name='SLA Guard Analytics Dataset',
                PhysicalTableMap={
                    'sla-tickets': {
                        'S3Source': {
                            'DataSourceArn': f'arn:aws:quicksight:{self.region}:{self.account_id}:datasource/{data_source_id}',
                            'InputColumns': [
                                {'Name': 'ticket_id', 'Type': 'STRING'},
                                {'Name': 'priority', 'Type': 'STRING'},
                                {'Name': 'status', 'Type': 'STRING'},
                                {'Name': 'created_at', 'Type': 'STRING'},
                                {'Name': 'sla_deadline', 'Type': 'STRING'},
                                {'Name': 'breach_probability', 'Type': 'STRING'},
                                {'Name': 'confidence_score', 'Type': 'STRING'},
                                {'Name': 'revenue_impact', 'Type': 'STRING'},
                                {'Name': 'customer_tier', 'Type': 'STRING'},
                                {'Name': 'department', 'Type': 'STRING'},
                                {'Name': 'resolution_time_hours', 'Type': 'STRING'},
                                {'Name': 'sla_met', 'Type': 'STRING'}
                            ]
                        }
                    }
                },
                ImportMode='SPICE',
                Permissions=[{
                    'Principal': self.user_arn,
                    'Actions': [
                        'quicksight:DescribeDataSet',
                        'quicksight:PassDataSet',
                        'quicksight:DescribeIngestion',
                        'quicksight:CreateIngestion',
                        'quicksight:UpdateDataSet',
                        'quicksight:DeleteDataSet'
                    ]
                }]
            )
            print(f"✅ Dataset created: {dataset_id}")
            return dataset_id
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Dataset already exists: {dataset_id}")
                return dataset_id
            print(f"❌ Failed to create dataset: {e}")
            return None
    
    def step_4_create_analysis(self, dataset_id):
        """Step 4: Create QuickSight analysis"""
        print("📈 Step 4: Creating QuickSight analysis...")
        
        analysis_id = 'sla-guard-analysis'
        
        try:
            self.quicksight_client.create_analysis(
                AwsAccountId=self.account_id,
                AnalysisId=analysis_id,
                Name='SLA Guard Production Analysis',
                Definition={
                    'DataSetIdentifierDeclarations': [{
                        'DataSetIdentifier': dataset_id,
                        'DataSetArn': f'arn:aws:quicksight:{self.region}:{self.account_id}:dataset/{dataset_id}'
                    }]
                },
                Permissions=[{
                    'Principal': self.user_arn,
                    'Actions': [
                        'quicksight:RestoreAnalysis',
                        'quicksight:UpdateAnalysisPermissions',
                        'quicksight:DeleteAnalysis',
                        'quicksight:DescribeAnalysisPermissions',
                        'quicksight:QueryAnalysis',
                        'quicksight:DescribeAnalysis',
                        'quicksight:UpdateAnalysis'
                    ]
                }]
            )
            print(f"✅ Analysis created: {analysis_id}")
            return analysis_id
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Analysis already exists: {analysis_id}")
                return analysis_id
            print(f"❌ Failed to create analysis: {e}")
            return None
    
    def step_5_get_urls(self):
        """Step 5: Get access URLs"""
        print("🔗 Step 5: Getting access URLs...")
        
        quicksight_url = f"https://{self.region}.quicksight.aws.amazon.com/"
        s3_url = f"https://s3.console.aws.amazon.com/s3/buckets/{self.bucket_name}"
        
        print(f"📊 QuickSight Console: {quicksight_url}")
        print(f"🗂️  S3 Bucket: {s3_url}")
        
        return quicksight_url, s3_url
    
    def run_full_automation(self):
        """Run complete QuickSight automation"""
        print("🚀 Starting Complete QuickSight Automation")
        print("=" * 60)
        
        # Step 0: Get QuickSight user
        if not self.get_quicksight_user():
            print("❌ Cannot proceed without valid QuickSight user")
            return False
        
        # Step 1: Upload manifest
        if not self.step_1_upload_manifest():
            return False
        
        time.sleep(2)
        
        # Step 2: Create data source
        data_source_id = self.step_2_create_data_source()
        if not data_source_id:
            return False
        
        time.sleep(3)
        
        # Step 3: Create dataset
        dataset_id = self.step_3_create_dataset(data_source_id)
        if not dataset_id:
            return False
        
        time.sleep(3)
        
        # Step 4: Create analysis
        analysis_id = self.step_4_create_analysis(dataset_id)
        if not analysis_id:
            print("⚠️  Analysis creation failed, but you can create it manually")
        
        # Step 5: Get URLs
        quicksight_url, s3_url = self.step_5_get_urls()
        
        print("\n" + "=" * 60)
        print("🎉 QuickSight Automation Complete!")
        print("=" * 60)
        print(f"📊 Data Source: sla-guard-data-source")
        print(f"📈 Dataset: sla-guard-dataset")
        print(f"📋 Analysis: {analysis_id if analysis_id else 'Create manually'}")
        print(f"🌐 QuickSight: {quicksight_url}")
        
        print("\n📋 Next Steps:")
        print("1. Go to QuickSight Console")
        print("2. Open your analysis or create new one")
        print("3. Add visuals: KPIs, charts, tables")
        print("4. Publish as dashboard")
        print("5. Set up refresh schedule (every 5 minutes)")
        
        return True

def main():
    """Main function with command line options"""
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        automation = QuickSightAutomation()
        
        if action == 'manifest':
            automation.step_1_upload_manifest()
        elif action == 'datasource':
            if automation.get_quicksight_user():
                automation.step_1_upload_manifest()
                automation.step_2_create_data_source()
            else:
                print("❌ Cannot create data source without valid QuickSight user")
                print("💡 Try: python simple_quicksight_setup.py")
        elif action == 'dataset':
            if automation.get_quicksight_user():
                automation.step_1_upload_manifest()
                data_source_id = automation.step_2_create_data_source()
                if data_source_id:
                    automation.step_3_create_dataset(data_source_id)
            else:
                print("❌ Cannot create dataset without valid QuickSight user")
                print("💡 Try: python simple_quicksight_setup.py")
        elif action == 'full':
            automation.run_full_automation()
        elif action == 'simple':
            # Import and run simple setup
            from simple_quicksight_setup import SimpleQuickSightSetup
            simple_setup = SimpleQuickSightSetup()
            simple_setup.run_simple_setup()
        else:
            print("Usage: python automate_quicksight.py [manifest|datasource|dataset|full|simple]")
    else:
        # Run full automation by default
        automation = QuickSightAutomation()
        success = automation.run_full_automation()
        
        if not success:
            print("\n💡 If user permissions failed, try simple setup:")
            print("python automate_quicksight.py simple")
            print("or")
            print("python simple_quicksight_setup.py")

if __name__ == "__main__":
    main()