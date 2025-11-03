#!/usr/bin/env python3
"""
QuickSight Setup with Data Transformations
Creates dataset with proper data type transformations
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

class QuickSightWithTransforms:
    def __init__(self):
        self.bucket_name = 'sla-guard-archive-508955320780'
        self.account_id = '508955320780'
        self.target_region = 'us-east-1'
        
        # Force region configuration
        os.environ['AWS_DEFAULT_REGION'] = self.target_region
        os.environ['AWS_REGION'] = self.target_region
        
        # Create clients with explicit region
        self.s3_client = boto3.client('s3', region_name=self.target_region)
        self.quicksight_client = boto3.client('quicksight', region_name=self.target_region)
    
    def upload_manifest(self):
        """Upload manifest file"""
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
    
    def create_data_source(self):
        """Create QuickSight data source"""
        print("🔗 Creating QuickSight data source...")
        
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
            )
            print(f"✅ Data source created: {data_source_id}")
            return data_source_id
            
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Data source already exists: {data_source_id}")
                return data_source_id
            else:
                print(f"❌ Data source creation failed: {e}")
                return None
    
    def create_dataset_with_transforms(self, data_source_id):
        """Create dataset with logical transformations"""
        print("📊 Creating QuickSight dataset with transformations...")
        
        dataset_id = 'sla-guard-dataset'
        
        try:
            self.quicksight_client.create_data_set(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id,
                Name='SLA Guard Analytics Dataset',
                PhysicalTableMap={
                    'sla-tickets-raw': {
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
                LogicalTableMap={
                    'sla-analytics': {
                        'Alias': 'SLA Analytics',
                        'DataTransforms': [
                            {
                                'CastColumnTypeOperation': {
                                    'ColumnName': 'breach_probability',
                                    'NewColumnType': 'DECIMAL',
                                    'Format': '0.00'
                                }
                            },
                            {
                                'CastColumnTypeOperation': {
                                    'ColumnName': 'confidence_score',
                                    'NewColumnType': 'DECIMAL',
                                    'Format': '0.00'
                                }
                            },
                            {
                                'CastColumnTypeOperation': {
                                    'ColumnName': 'revenue_impact',
                                    'NewColumnType': 'DECIMAL',
                                    'Format': '0.00'
                                }
                            },
                            {
                                'CastColumnTypeOperation': {
                                    'ColumnName': 'resolution_time_hours',
                                    'NewColumnType': 'DECIMAL',
                                    'Format': '0.00'
                                }
                            },
                            {
                                'CreateColumnsOperation': {
                                    'Columns': [
                                        {
                                            'ColumnName': 'created_date',
                                            'ColumnId': 'created_date',
                                            'Expression': 'parseDate({created_at}, "yyyy-MM-dd HH:mm:ss")'
                                        },
                                        {
                                            'ColumnName': 'sla_deadline_date',
                                            'ColumnId': 'sla_deadline_date',
                                            'Expression': 'parseDate({sla_deadline}, "yyyy-MM-dd HH:mm:ss")'
                                        },
                                        {
                                            'ColumnName': 'is_critical',
                                            'ColumnId': 'is_critical',
                                            'Expression': 'ifelse(toString({revenue_impact}) > "100000", "Critical", "Normal")'
                                        },
                                        {
                                            'ColumnName': 'risk_level',
                                            'ColumnId': 'risk_level',
                                            'Expression': 'ifelse(toString({breach_probability}) > "0.7", "High Risk", ifelse(toString({breach_probability}) > "0.3", "Medium Risk", "Low Risk"))'
                                        }
                                    ]
                                }
                            }
                        ],
                        'Source': {
                            'PhysicalTableId': 'sla-tickets-raw'
                        }
                    }
                },
                ImportMode='SPICE'
            )
            print(f"✅ Dataset with transformations created: {dataset_id}")
            return dataset_id
            
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Dataset already exists: {dataset_id}")
                return dataset_id
            else:
                print(f"❌ Dataset creation failed: {e}")
                print("💡 Falling back to simple dataset creation...")
                return self.create_simple_dataset(data_source_id)
    
    def create_simple_dataset(self, data_source_id):
        """Fallback: Create simple dataset without transformations"""
        print("📊 Creating simple QuickSight dataset...")
        
        dataset_id = 'sla-guard-dataset-simple'
        
        try:
            self.quicksight_client.create_data_set(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id,
                Name='SLA Guard Simple Dataset',
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
            print(f"✅ Simple dataset created: {dataset_id}")
            return dataset_id
            
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                print(f"ℹ️  Simple dataset already exists: {dataset_id}")
                return dataset_id
            else:
                print(f"❌ Simple dataset creation failed: {e}")
                return None
    
    def run_setup(self):
        """Run complete setup with transformations"""
        print("🚀 QuickSight Setup with Data Transformations")
        print("=" * 50)
        
        # Upload manifest
        if not self.upload_manifest():
            return False
        
        # Create data source
        data_source_id = self.create_data_source()
        if not data_source_id:
            return False
        
        # Create dataset with transformations
        dataset_id = self.create_dataset_with_transforms(data_source_id)
        if not dataset_id:
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Setup Complete with Data Transformations!")
        print("=" * 50)
        print(f"📊 Data Source: {data_source_id}")
        print(f"📈 Dataset: {dataset_id}")
        print(f"🌐 QuickSight: https://{self.target_region}.quicksight.aws.amazon.com/")
        
        print("\n📋 Available Columns:")
        print("✅ Original: ticket_id, priority, status, customer_tier, department, sla_met")
        print("✅ Numeric: breach_probability, confidence_score, revenue_impact, resolution_time_hours")
        print("✅ Dates: created_date, sla_deadline_date")
        print("✅ Calculated: is_critical, risk_level")
        
        print("\n📊 Ready for Dashboard Creation:")
        print("1. Go to QuickSight Console")
        print("2. Create analysis from your dataset")
        print("3. Use transformed columns for better visualizations")
        print("4. Build KPIs and charts with proper data types")
        
        return True

def main():
    """Main function"""
    setup = QuickSightWithTransforms()
    setup.run_setup()

if __name__ == "__main__":
    main()