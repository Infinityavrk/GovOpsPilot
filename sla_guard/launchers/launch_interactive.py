#!/usr/bin/env python3
"""
Launch Interactive SLA Guard Dashboard
Easy launcher for the interactive dashboard with real AWS data
"""

import sys
import os
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import boto3
        print("✅ boto3 available")
        return True
    except ImportError:
        print("❌ boto3 not found. Install with: pip install boto3")
        return False

def launch_static_dashboard():
    """Launch the static interactive dashboard"""
    dashboard_file = Path(__file__).parent / "interactive_dashboard.html"
    
    if dashboard_file.exists():
        file_url = f"file://{dashboard_file.absolute()}"
        print(f"🚀 Opening Static Interactive Dashboard...")
        print(f"📁 File: {dashboard_file}")
        
        try:
            webbrowser.open(file_url)
            print("✅ Dashboard opened in your browser!")
            print("📊 Features: Interactive UI, animations, mock real-time data")
            return True
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            return False
    else:
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False

def launch_server_dashboard(port=8080):
    """Launch the server-based dashboard with real AWS data"""
    if not check_dependencies():
        return False
    
    server_script = Path(__file__).parent / "dashboard_server.py"
    
    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        return False
    
    print(f"🚀 Starting Interactive Dashboard Server...")
    print(f"📡 Port: {port}")
    print(f"🔄 Real AWS data integration enabled")
    print(f"⏰ Auto-refresh every 30 seconds")
    
    try:
        # Start the server
        subprocess.run([sys.executable, str(server_script), str(port)])
        return True
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def show_dashboard_options():
    """Show available dashboard options"""
    print("🛡️ SLA Guard Interactive Dashboard Options")
    print("=" * 50)
    print("1. 🌟 Static Interactive Dashboard (Recommended)")
    print("   • Beautiful interactive UI")
    print("   • Animations and hover effects")
    print("   • Mock real-time data")
    print("   • No server required")
    print()
    print("2. 🔄 Server Dashboard with Real AWS Data")
    print("   • Live AWS service status")
    print("   • Real CloudWatch metrics")
    print("   • Auto-refresh every 30 seconds")
    print("   • Requires AWS credentials")
    print()
    print("3. 🔗 Show AWS Console URLs")
    print("   • Direct links to all services")
    print("   • Innovation-Brigade account")
    print()

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
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == 'static':
            launch_static_dashboard()
        elif action == 'server':
            port = 8080
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                except ValueError:
                    print("Invalid port. Using default 8080.")
            launch_server_dashboard(port)
        elif action == 'urls':
            show_aws_urls()
        elif action == 'help':
            show_dashboard_options()
        else:
            print("Usage: python launch_interactive.py [static|server|urls|help]")
            print("Run without arguments for interactive menu.")
    else:
        # Interactive menu
        show_dashboard_options()
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                launch_static_dashboard()
            elif choice == '2':
                port_input = input("Enter port (default 8080): ").strip()
                port = 8080
                if port_input:
                    try:
                        port = int(port_input)
                    except ValueError:
                        print("Invalid port. Using default 8080.")
                launch_server_dashboard(port)
            elif choice == '3':
                show_aws_urls()
            else:
                print("Invalid choice. Launching static dashboard...")
                launch_static_dashboard()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()