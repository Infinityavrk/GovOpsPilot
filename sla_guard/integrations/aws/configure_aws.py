#!/usr/bin/env python3
"""
Simple AWS Configuration Script
Helps set up AWS credentials for SLA Guard
"""

import os
import subprocess
import sys

def configure_aws_cli():
    """Configure AWS CLI interactively"""
    print("🔧 AWS CLI Configuration")
    print("=" * 30)
    
    print("\nYou need AWS credentials for Innovation-Brigade account:")
    print("Account ID: 508955320780")
    print("Region: us-east-1")
    
    print("\n💡 If you don't have AWS credentials, contact your AWS administrator")
    
    try:
        # Run aws configure
        subprocess.run(['aws', 'configure'], check=True)
        print("\n✅ AWS CLI configured successfully!")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ AWS CLI configuration failed")
        return False
    except FileNotFoundError:
        print("\n❌ AWS CLI not found. Please install it first:")
        print("https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False

def set_environment_variables():
    """Guide user to set environment variables"""
    print("🌍 Environment Variables Setup")
    print("=" * 35)
    
    print("\nAdd these to your shell profile (~/.bashrc, ~/.zshrc, etc.):")
    print("export AWS_ACCESS_KEY_ID=your_access_key_here")
    print("export AWS_SECRET_ACCESS_KEY=your_secret_key_here")
    print("export AWS_DEFAULT_REGION=us-east-1")
    
    print("\nThen reload your shell:")
    print("source ~/.bashrc  # or ~/.zshrc")

def quick_test():
    """Quick test of AWS credentials"""
    print("\n🧪 Testing AWS credentials...")
    
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True, check=True)
        print("✅ AWS credentials working!")
        print(f"Response: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ AWS credentials test failed")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ AWS CLI not found")
        return False

def main():
    """Main configuration function"""
    print("🚀 SLA Guard AWS Setup")
    print("=" * 25)
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == 'cli':
            configure_aws_cli()
        elif action == 'env':
            set_environment_variables()
        elif action == 'test':
            quick_test()
        else:
            print("Usage: python configure_aws.py [cli|env|test]")
    else:
        print("\nChoose configuration method:")
        print("1. AWS CLI (Recommended)")
        print("2. Environment Variables")
        print("3. Test current setup")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            configure_aws_cli()
            quick_test()
        elif choice == '2':
            set_environment_variables()
        elif choice == '3':
            quick_test()
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()