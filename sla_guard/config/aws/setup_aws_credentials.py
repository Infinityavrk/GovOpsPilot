#!/usr/bin/env python3
"""
AWS Credentials Setup and Verification Script
Helps configure AWS credentials for SLA Guard deployment
"""

import boto3
import os
import subprocess
from botocore.exceptions import ClientError, NoCredentialsError

class AWSCredentialsSetup:
    def __init__(self):
        self.account_id = '508955320780'
        self.region = 'us-east-1'
        self.bucket_name = 'sla-guard-archive-508955320780'
    
    def check_aws_cli_installed(self):
        """Check if AWS CLI is installed"""
        try:
            result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
            print(f"✅ AWS CLI installed: {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            print("❌ AWS CLI not installed")
            print("💡 Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
            return False
    
    def check_current_credentials(self):
        """Check current AWS credentials"""
        print("🔍 Checking current AWS credentials...")
        
        try:
            # Try to get caller identity
            sts_client = boto3.client('sts')
            response = sts_client.get_caller_identity()
            
            current_account = response.get('Account')
            current_arn = response.get('Arn')
            
            print(f"✅ AWS credentials configured")
            print(f"📋 Account ID: {current_account}")
            print(f"👤 User ARN: {current_arn}")
            
            if current_account == self.account_id:
                print("✅ Correct account (Innovation-Brigade)")
                return True
            else:
                print(f"⚠️  Different account. Expected: {self.account_id}")
                return False
                
        except NoCredentialsError:
            print("❌ No AWS credentials found")
            return False
        except ClientError as e:
            print(f"❌ AWS credentials error: {e}")
            return False
    
    def check_s3_permissions(self):
        """Check S3 bucket permissions"""
        print("🗂️  Checking S3 bucket permissions...")
        
        try:
            s3_client = boto3.client('s3')
            
            # Check if bucket exists and is accessible
            s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 bucket accessible: {self.bucket_name}")
            
            # Try to list objects
            response = s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            print(f"✅ S3 list permissions working")
            
            # Try to put a test object
            test_key = 'test-credentials.txt'
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body='Test credentials check',
                ContentType='text/plain'
            )
            print(f"✅ S3 write permissions working")
            
            # Clean up test object
            s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
            print(f"✅ S3 delete permissions working")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"❌ S3 bucket does not exist: {self.bucket_name}")
            elif error_code == 'AccessDenied':
                print(f"❌ Access denied to S3 bucket: {self.bucket_name}")
            else:
                print(f"❌ S3 error: {e}")
            return False
    
    def check_quicksight_permissions(self):
        """Check QuickSight permissions"""
        print("📊 Checking QuickSight permissions...")
        
        try:
            quicksight_client = boto3.client('quicksight')
            
            # Try to list users (basic permission check)
            response = quicksight_client.list_users(
                AwsAccountId=self.account_id,
                Namespace='default'
            )
            print(f"✅ QuickSight permissions working")
            
            # Check if user exists
            users = response.get('UserList', [])
            innovation_user = None
            for user in users:
                if 'Innovation-Brigade' in user.get('UserName', ''):
                    innovation_user = user
                    break
            
            if innovation_user:
                print(f"✅ QuickSight user found: {innovation_user['UserName']}")
            else:
                print("⚠️  Innovation-Brigade user not found in QuickSight")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                print("❌ QuickSight access denied")
                print("💡 Make sure QuickSight is enabled and you have permissions")
            else:
                print(f"❌ QuickSight error: {e}")
            return False
    
    def provide_setup_instructions(self):
        """Provide AWS credentials setup instructions"""
        print("\n" + "=" * 60)
        print("🔧 AWS Credentials Setup Instructions")
        print("=" * 60)
        
        print("\n1. Configure AWS CLI:")
        print("   aws configure")
        print("   - AWS Access Key ID: [Your access key]")
        print("   - AWS Secret Access Key: [Your secret key]")
        print(f"   - Default region name: {self.region}")
        print("   - Default output format: json")
        
        print("\n2. Alternative - Environment Variables:")
        print("   export AWS_ACCESS_KEY_ID=your_access_key")
        print("   export AWS_SECRET_ACCESS_KEY=your_secret_key")
        print(f"   export AWS_DEFAULT_REGION={self.region}")
        
        print("\n3. Alternative - AWS Profile:")
        print("   aws configure --profile innovation-brigade")
        print("   export AWS_PROFILE=innovation-brigade")
        
        print(f"\n4. Required Permissions:")
        print("   - S3: Full access to bucket: {self.bucket_name}")
        print("   - QuickSight: Admin or Author permissions")
        print("   - IAM: Basic read permissions")
        
        print(f"\n5. Account Information:")
        print(f"   - Account ID: {self.account_id}")
        print(f"   - Region: {self.region}")
        print("   - Account Name: Innovation-Brigade")
    
    def run_full_check(self):
        """Run complete AWS setup verification"""
        print("🚀 AWS Credentials Setup Verification")
        print("=" * 50)
        
        # Check AWS CLI
        cli_ok = self.check_aws_cli_installed()
        
        # Check credentials
        creds_ok = self.check_current_credentials()
        
        if not creds_ok:
            self.provide_setup_instructions()
            return False
        
        # Check S3 permissions
        s3_ok = self.check_s3_permissions()
        
        # Check QuickSight permissions
        qs_ok = self.check_quicksight_permissions()
        
        print("\n" + "=" * 50)
        print("📋 Setup Status Summary")
        print("=" * 50)
        print(f"AWS CLI: {'✅' if cli_ok else '❌'}")
        print(f"Credentials: {'✅' if creds_ok else '❌'}")
        print(f"S3 Access: {'✅' if s3_ok else '❌'}")
        print(f"QuickSight: {'✅' if qs_ok else '❌'}")
        
        if all([cli_ok, creds_ok, s3_ok, qs_ok]):
            print("\n🎉 All checks passed! You can now run:")
            print("   python automate_quicksight.py")
            return True
        else:
            print("\n⚠️  Some checks failed. Please fix the issues above.")
            if not creds_ok:
                self.provide_setup_instructions()
            return False

def main():
    """Main function"""
    setup = AWSCredentialsSetup()
    setup.run_full_check()

if __name__ == "__main__":
    main()