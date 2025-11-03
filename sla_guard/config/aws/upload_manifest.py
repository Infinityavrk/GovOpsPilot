#!/usr/bin/env python3
"""
Simple QuickSight Manifest Upload Script
Uploads manifest file to S3 and provides setup instructions
"""

import boto3
import json
from botocore.exceptions import ClientError

def upload_manifest():
    """Upload QuickSight manifest file to S3"""
    
    # Configuration
    bucket_name = 'sla-guard-archive-508955320780'
    
    # Create S3 client
    s3_client = boto3.client('s3')
    
    # Manifest content
    manifest_content = {
        "fileLocations": [
            {
                "URIPrefixes": [
                    f"s3://{bucket_name}/"
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
        print("📤 Uploading manifest file to S3...")
        
        # Upload manifest file
        s3_client.put_object(
            Bucket=bucket_name,
            Key='quicksight_manifest.json',
            Body=json.dumps(manifest_content, indent=2),
            ContentType='application/json'
        )
        
        print(f"✅ Manifest uploaded successfully!")
        print(f"📍 Location: s3://{bucket_name}/quicksight_manifest.json")
        
        # Provide next steps
        print("\n" + "=" * 50)
        print("🎯 Next Steps for QuickSight Setup:")
        print("=" * 50)
        print("1. Go to QuickSight Console:")
        print("   https://us-east-1.quicksight.aws.amazon.com/")
        print("\n2. Create New Dataset:")
        print("   - Click 'Datasets' → 'New dataset'")
        print("   - Choose 'S3' as data source")
        print("   - Name: 'SLA Guard Production Data'")
        print(f"   - Manifest file: s3://{bucket_name}/quicksight_manifest.json")
        print("\n3. Configure Dataset:")
        print("   - Import to SPICE for better performance")
        print("   - Set data types for columns")
        print("\n4. Create Dashboard:")
        print("   - Click 'Create analysis'")
        print("   - Add KPIs: Total Tickets, SLA Compliance Rate")
        print("   - Add Charts: Department performance, Breach trends")
        print("\n5. Set Refresh Schedule:")
        print("   - Schedule refresh every 5 minutes")
        print("   - Match your EventBridge schedule")
        
        return True
        
    except ClientError as e:
        print(f"❌ Failed to upload manifest: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_s3_access():
    """Check if S3 bucket is accessible"""
    bucket_name = 'sla-guard-archive-508955320780'
    s3_client = boto3.client('s3')
    
    try:
        print("🔍 Checking S3 bucket access...")
        response = s3_client.head_bucket(Bucket=bucket_name)
        print("✅ S3 bucket accessible")
        return True
    except ClientError as e:
        print(f"❌ S3 bucket not accessible: {e}")
        return False

def main():
    """Main function"""
    print("🚀 QuickSight Manifest Upload Tool")
    print("=" * 40)
    
    # Check S3 access first
    if not check_s3_access():
        print("\n💡 Make sure you have:")
        print("- AWS credentials configured")
        print("- S3 permissions for the bucket")
        return
    
    # Upload manifest
    if upload_manifest():
        print("\n🎉 Manifest upload completed!")
        print("You can now proceed with QuickSight dashboard creation.")
    else:
        print("\n❌ Manifest upload failed!")

if __name__ == "__main__":
    main()