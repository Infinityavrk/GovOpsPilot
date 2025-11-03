#!/usr/bin/env python3
"""
QuickSight Manifest Setup Script
Automates the upload of manifest file and QuickSight configuration
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

class QuickSightManifestSetup:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.quicksight_client = boto3.client('quicksight')
        self.bucket_name = 'sla-guard-archive-508955320780'
        self.account_id = '508955320780'
        self.region = 'us-east-1'
        
    def upload_manifest_to_s3(self):
        """Upload the manifest file to S3"""
        print("📤 Uploading manifest file to S3...")
        
        manifest_content = {
            "fileLocations": [
                {
                    "URIPrefixes": [
                        f"s3://{self.bucket_name}/"
                    ]
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
            # Upload manifest file
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
    
    def create_data_source(self):
        """Create QuickSight data source"""
        print("🔗 Creating QuickSight data source...")
        
        data_source_id = 'sla-guard-data-source'
        
        try:
            response = self.quicksight_client.create_data_source(
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
                Permissions=[
                    {
                        'Principal': f'arn:aws:quicksight:{self.region}:{self.account_id}:user/default/Innovation-Brigade',
                        'Actions': [
                            'quicksight:DescribeDataSource',
                            'quicksight:DescribeDataSourcePermissions',
                            'quicksight:PassDataSource',
                            'quicksight:UpdateDataSource',
                            'quicksight:DeleteDataSource',
                            'quicksight:UpdateDataSourcePermissions'
                        ]
                    }
                ],
                SslProperties={
                    'DisableSsl': False
                }
            )
            print(f"✅ Data source created: {data_source_id}")
            return data_source_id
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Data source already exists: {data_source_id}")
                return data_source_id
            else:
                print(f"❌ Failed to create data source: {e}")
                return None
    
    def create_dataset(self, data_source_id):
        """Create QuickSight dataset"""
        print("📊 Creating QuickSight dataset...")
        
        dataset_id = 'sla-guard-dataset'
        
        try:
            response = self.quicksight_client.create_data_set(
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
                                {'Name': 'created_at', 'Type': 'DATETIME'},
                                {'Name': 'sla_deadline', 'Type': 'DATETIME'},
                                {'Name': 'breach_probability', 'Type': 'DECIMAL'},
                                {'Name': 'confidence_score', 'Type': 'DECIMAL'},
                                {'Name': 'revenue_impact', 'Type': 'DECIMAL'},
                                {'Name': 'customer_tier', 'Type': 'STRING'},
                                {'Name': 'department', 'Type': 'STRING'},
                                {'Name': 'resolution_time_hours', 'Type': 'DECIMAL'},
                                {'Name': 'sla_met', 'Type': 'STRING'}
                            ]
                        }
                    }
                },
                ImportMode='SPICE',
                Permissions=[
                    {
                        'Principal': f'arn:aws:quicksight:{self.region}:{self.account_id}:user/default/Innovation-Brigade',
                        'Actions': [
                            'quicksight:DescribeDataSet',
                            'quicksight:DescribeDataSetPermissions',
                            'quicksight:PassDataSet',
                            'quicksight:DescribeIngestion',
                            'quicksight:ListIngestions',
                            'quicksight:UpdateDataSet',
                            'quicksight:DeleteDataSet',
                            'quicksight:CreateIngestion',
                            'quicksight:CancelIngestion',
                            'quicksight:UpdateDataSetPermissions'
                        ]
                    }
                ]
            )
            print(f"✅ Dataset created: {dataset_id}")
            return dataset_id
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Dataset already exists: {dataset_id}")
                return dataset_id
            else:
                print(f"❌ Failed to create dataset: {e}")
                return None
    
    def trigger_dataset_ingestion(self, dataset_id):
        """Trigger SPICE ingestion for the dataset"""
        print("🔄 Triggering dataset ingestion...")
        
        ingestion_id = f"ingestion-{int(time.time())}"
        
        try:
            response = self.quicksight_client.create_ingestion(
                DataSetId=dataset_id,
                IngestionId=ingestion_id,
                AwsAccountId=self.account_id
            )
            print(f"✅ Ingestion started: {ingestion_id}")
            return ingestion_id
        except ClientError as e:
            print(f"❌ Failed to start ingestion: {e}")
            return None
    
    def check_ingestion_status(self, dataset_id, ingestion_id):
        """Check the status of dataset ingestion"""
        print("⏳ Checking ingestion status...")
        
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                response = self.quicksight_client.describe_ingestion(
                    DataSetId=dataset_id,
                    IngestionId=ingestion_id,
                    AwsAccountId=self.account_id
                )
                
                status = response['Ingestion']['IngestionStatus']
                print(f"📊 Ingestion status: {status}")
                
                if status == 'COMPLETED':
                    print("✅ Dataset ingestion completed successfully!")
                    return True
                elif status == 'FAILED':
                    print("❌ Dataset ingestion failed!")
                    return False
                
                time.sleep(10)
                attempt += 1
                
            except ClientError as e:
                print(f"❌ Error checking ingestion status: {e}")
                return False
        
        print("⏰ Ingestion taking longer than expected...")
        return False
    
    def get_quicksight_url(self):
        """Get the QuickSight console URL"""
        return f"https://{self.region}.quicksight.aws.amazon.com/"
    
    def run_setup(self):
        """Run the complete QuickSight manifest setup"""
        print("🚀 Starting QuickSight Manifest Setup...")
        print("=" * 50)
        
        # Step 1: Upload manifest to S3
        if not self.upload_manifest_to_s3():
            return False
        
        # Step 2: Create data source
        data_source_id = self.create_data_source()
        if not data_source_id:
            return False
        
        # Wait a moment for data source to be ready
        time.sleep(5)
        
        # Step 3: Create dataset
        dataset_id = self.create_dataset(data_source_id)
        if not dataset_id:
            return False
        
        # Step 4: Trigger ingestion
        ingestion_id = self.trigger_dataset_ingestion(dataset_id)
        if ingestion_id:
            self.check_ingestion_status(dataset_id, ingestion_id)
        
        print("\n" + "=" * 50)
        print("🎉 QuickSight Setup Complete!")
        print(f"📊 QuickSight Console: {self.get_quicksight_url()}")
        print(f"🗂️  Data Source: {data_source_id}")
        print(f"📈 Dataset: {dataset_id}")
        print("\n📋 Next Steps:")
        print("1. Go to QuickSight Console")
        print("2. Create Analysis from your dataset")
        print("3. Build dashboard with KPIs and charts")
        print("4. Publish dashboard for your team")
        
        return True

def main():
    """Main function"""
    setup = QuickSightManifestSetup()
    success = setup.run_setup()
    
    if success:
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Check the errors above.")

if __name__ == "__main__":
    main()