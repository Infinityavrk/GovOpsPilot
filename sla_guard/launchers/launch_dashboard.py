#!/usr/bin/env python3
"""
Launch SLA Guard Dashboard
Opens the production flow dashboard in browser
"""

import webbrowser
import os
import sys
from pathlib import Path

def launch_static_dashboard():
    """Launch the static HTML dashboard"""
    dashboard_file = Path(__file__).parent / "static_dashboard.html"
    
    if dashboard_file.exists():
        file_url = f"file://{dashboard_file.absolute()}"
        print(f"🚀 Opening SLA Guard Dashboard...")
        print(f"📁 File: {dashboard_file}")
        print(f"🌐 URL: {file_url}")
        
        try:
            webbrowser.open(file_url)
            print("✅ Dashboard opened in your default browser!")
            return True
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            print(f"💡 Manually open: {dashboard_file}")
            return False
    else:
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False

def create_and_launch_dynamic_dashboard():
    """Create and launch the dynamic dashboard"""
    try:
        from create_dashboard_ui import SLAGuardDashboardUI
        
        print("🔄 Creating dynamic dashboard...")
        dashboard = SLAGuardDashboardUI()
        filename = dashboard.create_dashboard_file()
        
        file_path = Path(filename).absolute()
        file_url = f"file://{file_path}"
        
        print(f"✅ Dynamic dashboard created: {filename}")
        print(f"🌐 Opening: {file_url}")
        
        webbrowser.open(file_url)
        return True
        
    except ImportError:
        print("❌ Dynamic dashboard dependencies not available")
        return False
    except Exception as e:
        print(f"❌ Failed to create dynamic dashboard: {e}")
        return False

def show_aws_urls():
    """Display all AWS console URLs"""
    print("\n" + "=" * 60)
    print("🔗 AWS Console URLs - Innovation-Brigade (508955320780)")
    print("=" * 60)
    
    urls = {
        "🏠 AWS Console": "https://us-east-1.console.aws.amazon.com/",
        "📊 QuickSight": "https://us-east-1.quicksight.aws.amazon.com/",
        "🗂️  S3 Archive": "https://s3.console.aws.amazon.com/s3/buckets/sla-guard-archive-508955320780",
        "📋 DynamoDB": "https://us-east-1.console.aws.amazon.com/dynamodbv2/home?region=us-east-1#table?name=sla-tickets",
        "⚡ Lambda": "https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/sla-guard-processor",
        "🤖 SageMaker": "https://us-east-1.console.aws.amazon.com/sagemaker/home?region=us-east-1#/endpoints/sla-guard-endpoint",
        "🔄 Step Functions": "https://us-east-1.console.aws.amazon.com/states/home?region=us-east-1",
        "📧 SNS": "https://us-east-1.console.aws.amazon.com/sns/v3/home?region=us-east-1",
        "⏰ EventBridge": "https://us-east-1.console.aws.amazon.com/events/home?region=us-east-1#/rules",
        "📈 CloudWatch": "https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1"
    }
    
    for name, url in urls.items():
        print(f"{name}: {url}")
    
    print("\n💡 Click any URL to open in your browser!")

def main():
    """Main function"""
    print("🛡️ SLA Guard Production Dashboard Launcher")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == 'static':
            launch_static_dashboard()
        elif action == 'dynamic':
            create_and_launch_dynamic_dashboard()
        elif action == 'urls':
            show_aws_urls()
        else:
            print("Usage: python launch_dashboard.py [static|dynamic|urls]")
    else:
        # Default: try static first, then dynamic
        print("🎯 Launching SLA Guard Dashboard...")
        
        if not launch_static_dashboard():
            print("\n🔄 Trying dynamic dashboard...")
            if not create_and_launch_dynamic_dashboard():
                print("\n❌ Could not launch dashboard")
                print("💡 Try: python launch_dashboard.py static")
        
        # Always show AWS URLs
        show_aws_urls()

if __name__ == "__main__":
    main()