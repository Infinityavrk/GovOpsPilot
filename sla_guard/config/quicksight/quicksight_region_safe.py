#!/usr/bin/env python3
"""
Region-Safe QuickSight Setup
Handles region configuration automatically
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

class RegionSafeQuickSight:
    def __init__(self):
        self.bucket_name = 'sla-guard-archive-508955320780'
        self.account_id = '508955320780'
        self.target_region = 'us-east-1'
        
        # Force region configuration
        self.setup_region()
        
        # Create clients with explicit region
        self.s3_client = boto3.client('s3', region_name=self.target_region)
        self.quicksight_client = boto3.client('quicksight', region_name=self.target_region)
        self.sts_client = boto3.client('sts', region_name=self.target_region)
    
    def setup_region(self):
        """Force correct region configuration"""
        print(f"🌍 Setting up region: {self.target_region}")
        
        # Set environment variables
        os.environ['AWS_DEFAULT_REGION'] = self.target_region
        os.environ['AWS_REGION'] = self.target_region
        
        print(f"✅ Region configured: {self.target_region}")
    
    def verify_setup(self):
        """Verify AWS setup and region"""
        print("🔍 Verifying AWS setup...")
        
        try:
            # Test STS
            identity = self.sts_client.get_caller_identity()
            account = identity.get('Account')
            user_arn = identity.get('Arn')
            
            print(f"✅ AWS Identity: {user_arn}")
            print(f"✅ Account: {account}")
            
            if account != self.account_id:
                print(f"⚠️  Account mismatch. Expected: {self.account_id}, Got: {account}")
            
            # Test S3
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 bucket accessible: {self.bucket_name}")
            
            return True
            
        except ClientError as e:
            print(f"❌ AWS setup verification failed: {e}")
            return False
    
    def upload_manifest(self):
        """Upload manifest with region safety"""
        print("📤 Uploading manifest file...")
        
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
            print(f"✅ Manifest uploaded successfully")
            return True
        except ClientError as e:
            print(f"❌ Manifest upload failed: {e}")
            return False
    
    def create_data_source_minimal(self):
        """Create data source with minimal configuration"""
        print("🔗 Creating QuickSight data source...")
        
        data_source_id = 'sla-guard-data-source'
        
        try:
            # Try to create without permissions first
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
            )
            print(f"✅ Data source created: {data_source_id}")
            return data_source_id
            
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Data source already exists: {data_source_id}")
                return data_source_id
            elif 'endpoint' in str(e).lower() or 'region' in str(e).lower():
                print(f"❌ Region error: {e}")
                print("💡 Try running: python check_aws_region.py")
                return None
            else:
                print(f"❌ Data source creation failed: {e}")
                return None
    
    def create_dataset_minimal(self, data_source_id):
        """Create dataset with minimal configuration"""
        print("📊 Creating QuickSight dataset...")
        
        dataset_id = 'sla-guard-dataset'
        
        try:
            self.quicksight_client.create_data_set(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id,
                Name='SLA Guard Analytics Dataset',
                PhysicalTableMap={
                    'sla-tickets': {
                        'S3Source': {
                            'DataSourceArn': f'arn:aws:quicksight:{self.target_region}:{self.account_id}:datasource/{data_source_id}',
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
            )
            print(f"✅ Dataset created: {dataset_id}")
            return dataset_id
            
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Dataset already exists: {dataset_id}")
                return dataset_id
            else:
                print(f"❌ Dataset creation failed: {e}")
                return None
    
    def run_setup(self):
        """Run complete region-safe setup"""
        print("🚀 Region-Safe QuickSight Setup")
        print("=" * 40)
        
        # Verify setup
        if not self.verify_setup():
            return False
        
        # Upload manifest
        if not self.upload_manifest():
            return False
        
        # Create data source
        data_source_id = self.create_data_source_minimal()
        if not data_source_id:
            return False
        
        # Create dataset
        dataset_id = self.create_dataset_minimal(data_source_id)
        if not dataset_id:
            return False
        
        print("\n" + "=" * 40)
        print("🎉 Setup Complete!")
        print("=" * 40)
        print(f"📊 Data Source: {data_source_id}")
        print(f"📈 Dataset: {dataset_id}")
        print(f"🌐 QuickSight: https://{self.target_region}.quicksight.aws.amazon.com/")
        
        print("\n📋 Next Steps:")
        print("1. Go to QuickSight Console")
        print("2. Create analysis from your dataset")
        print("3. Build dashboard with KPIs")
        print("4. Publish dashboard")
        
        return True

def main():
    """Main function"""
    setup = RegionSafeQuickSight()
    setup.run_setup()

if __name__ == "__main__":
    main()