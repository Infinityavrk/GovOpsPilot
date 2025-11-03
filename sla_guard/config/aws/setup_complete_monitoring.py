#!/usr/bin/env python3
"""
Complete AWS Monitoring and Email Setup
One-stop script to set up monitoring, email alerts, and troubleshoot issues
"""

import boto3
import json
import time
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main setup function with interactive prompts"""
    print("🚀 AWS GenAI Complete Monitoring Setup")
    print("=" * 60)
    print("This script will set up:")
    print("• SNS topics for alerts")
    print("• Email subscriptions")
    print("• CloudWatch alarms")
    print("• SES email configuration")
    print("• Test email delivery")
    print("=" * 60)
    
    # Get user input
    email = input("📧 Enter your email address for alerts: ").strip()
    if not email:
        print("❌ Email address is required")
        sys.exit(1)
    
    region = input(f"🌍 Enter AWS region (default: us-east-1): ").strip() or 'us-east-1'
    
    print(f"\n📋 Configuration:")
    print(f"   Email: {email}")
    print(f"   Region: {region}")
    
    confirm = input("\n✅ Proceed with setup? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Setup cancelled")
        sys.exit(0)
    
    # Import and run monitoring setup
    try:
        from aws_monitoring_setup import AWSMonitoringSetup
        
        print(f"\n🔧 Setting up AWS monitoring...")
        setup = AWSMonitoringSetup(region=region, email_address=email)
        results = setup.setup_complete_monitoring()
        
        # Test email system
        print(f"\n🧪 Testing email alerts...")
        from test_email_alerts import EmailAlertTester
        
        tester = EmailAlertTester(region=region, email_address=email)
        test_results = tester.run_comprehensive_test()
        
        # Print final summary
        print_final_summary(email, region, results, test_results)
        
    except ImportError as e:
        print(f"❌ Required modules not found: {e}")
        print("Make sure aws_monitoring_setup.py and test_email_alerts.py are in the same directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

def print_final_summary(email, region, setup_results, test_results):
    """Print final setup summary"""
    print("\n" + "="*60)
    print("🎉 AWS GenAI Monitoring Setup Complete!")
    print("="*60)
    
    # Setup results
    setup_success = sum(1 for r in setup_results.values() if r['status'] == 'SUCCESS')
    setup_total = len(setup_results)
    
    # Test results
    test_success = sum(1 for r in test_results.values() if r['status'] == 'PASS')
    test_total = len(test_results)
    
    print(f"📊 Setup Results: {setup_success}/{setup_total} components configured")
    print(f"🧪 Test Results: {test_success}/{test_total} tests passed")
    
    print(f"\n📧 Email Configuration:")
    print(f"   Alert Email: {email}")
    print(f"   AWS Region: {region}")
    
    print(f"\n🔗 AWS Console URLs:")
    print(f"   CloudWatch Alarms: https://console.aws.amazon.com/cloudwatch/home?region={region}#alarmsV2:")
    print(f"   SNS Topics: https://console.aws.amazon.com/sns/v3/home?region={region}#/topics")
    print(f"   SES Identities: https://console.aws.amazon.com/ses/home?region={region}#/identities")
    print(f"   Lambda Functions: https://console.aws.amazon.com/lambda/home?region={region}#/functions")
    print(f"   DynamoDB Tables: https://console.aws.amazon.com/dynamodbv2/home?region={region}#tables")
    
    print(f"\n📱 Professional UI:")
    print(f"   Launch UI: python launch_professional_ui.py")
    print(f"   The UI now includes clickable AWS console links")
    
    print(f"\n⚠️ IMPORTANT - Check Your Email:")
    print(f"   1. 📧 SNS subscription confirmations")
    print(f"   2. ✅ SES email verification")
    print(f"   3. 🧪 Test alert messages")
    
    if setup_success == setup_total and test_success == test_total:
        print(f"\n🎉 Everything is working perfectly!")
        print(f"   • All AWS services configured")
        print(f"   • Email alerts are active")
        print(f"   • Monitoring is operational")
        print(f"   • Ready for production use")
    else:
        print(f"\n🔧 Action Required:")
        if setup_success < setup_total:
            print(f"   • Fix setup issues (see details above)")
        if test_success < test_total:
            print(f"   • Resolve email delivery problems")
            print(f"   • Run: python test_email_alerts.py --email {email}")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Launch the professional UI")
    print(f"   2. Test critical alert workflow")
    print(f"   3. Monitor CloudWatch alarms")
    print(f"   4. Verify email delivery")
    
    print(f"\n📞 Troubleshooting:")
    print(f"   • Test emails: python test_email_alerts.py --email {email}")
    print(f"   • Check AWS permissions and service quotas")
    print(f"   • Verify email address and domain")

if __name__ == "__main__":
    main()