#!/usr/bin/env python3
"""
Simple QuickSight Setup - No Permissions
Creates data source and dataset without setting permissions initially
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

class SimpleQuickSightSetup:
    def __init__(self):
        self.bucket_name = 'sla-guard-archive-508955320780'
        self.account_id = '508955320780'
        self.region = 'us-east-1'
        
        # Explicitly set region for all clients
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.quicksight_client = boto3.client('quicksight', region_name=self.region)
    
    def upload_manifest(self):
        """Upload manifest file to S3"""
        print("📤 Uploading manifest file to S3...")
        
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
    
    def create_data_source_simple(self):
        """Create data source without permissions"""
        print("🔗 Creating QuickSight data source (no permissions)...")
        
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
                }
                # No permissions specified - will inherit from user
            )
            print(f"✅ Data source created: {data_source_id}")
            return data_source_id
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Data source already exists: {data_source_id}")
                return data_source_id
            print(f"❌ Failed to create data source: {e}")
            return None
    
    def create_dataset_simple(self, data_source_id):
        """Create dataset without permissions"""
        print("📊 Creating QuickSight dataset (no permissions)...")
        
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
                ImportMode='SPICE'
                # No permissions specified - will inherit from user
            )
            print(f"✅ Dataset created: {dataset_id}")
            return dataset_id
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Dataset already exists: {dataset_id}")
                return dataset_id
            print(f"❌ Failed to create dataset: {e}")
            return None
    
    def list_quicksight_users(self):
        """List available QuickSight users"""
        print("👥 Available QuickSight users:")
        
        try:
            response = self.quicksight_client.list_users(
                AwsAccountId=self.account_id,
                Namespace='default'
            )
            
            users = response.get('UserList', [])
            for user in users:
                username = user.get('UserName', '')
                role = user.get('Role', '')
                email = user.get('Email', '')
                print(f"   - {username} ({role}) - {email}")
            
            return users
        except ClientError as e:
            print(f"❌ Error listing users: {e}")
            return []
    
    def run_simple_setup(self):
        """Run simple setup without permissions"""
        print("🚀 Simple QuickSight Setup (No Permissions)")
        print("=" * 50)
        
        # Show available users
        self.list_quicksight_users()
        
        # Upload manifest
        if not self.upload_manifest():
            return False
        
        time.sleep(2)
        
        # Create data source
        data_source_id = self.create_data_source_simple()
        if not data_source_id:
            return False
        
        time.sleep(3)
        
        # Create dataset
        dataset_id = self.create_dataset_simple(data_source_id)
        if not dataset_id:
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Simple Setup Complete!")
        print("=" * 50)
        print(f"📊 Data Source: {data_source_id}")
        print(f"📈 Dataset: {dataset_id}")
        print(f"🌐 QuickSight: https://{self.region}.quicksight.aws.amazon.com/")
        
        print("\n📋 Next Steps:")
        print("1. Go to QuickSight Console")
        print("2. Find your dataset in 'Datasets'")
        print("3. Click 'Create analysis'")
        print("4. Build your dashboard")
        print("5. Set permissions manually if needed")
        
        return True

def main():
    """Main function"""
    setup = SimpleQuickSightSetup()
    setup.run_simple_setup()

if __name__ == "__main__":
    main()