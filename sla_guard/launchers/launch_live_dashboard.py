#!/usr/bin/env python3
"""
Launch Live Interactive SLA Guard Dashboard
Ultimate interactive experience with real ticket creation and tracking
"""

import sys
import os
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    
    try:
        import boto3
        print("✅ boto3 available")
    except ImportError:
        missing.append("boto3")
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def launch_live_dashboard(port=8080):
    """Launch the live dashboard with real ticket creation"""
    if not check_dependencies():
        return False
    
    server_script = Path(__file__).parent / "live_ticket_server.py"
    
    if not server_script.exists():
        print(f"❌ Live server script not found: {server_script}")
        return False
    
    print(f"🚀 Starting Live Ticket Dashboard...")
    print(f"📡 Port: {port}")
    print(f"🎫 Real ticket creation enabled")
    print(f"🔄 Live pipeline tracking")
    print(f"📊 Real-time AWS integration")
    print(f"⚡ Background ticket processing")
    
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

def launch_static_live_dashboard():
    """Launch the static live dashboard (no server required)"""
    dashboard_file = Path(__file__).parent / "live_ticket_dashboard.html"
    
    if dashboard_file.exists():
        file_url = f"file://{dashboard_file.absolute()}"
        print(f"🚀 Opening Static Live Dashboard...")
        print(f"📁 File: {dashboard_file}")
        
        try:
            webbrowser.open(file_url)
            print("✅ Dashboard opened in your browser!")
            print("🎫 Features: Live ticket creation, pipeline visualization, interactive controls")
            print("📊 Note: Uses simulated data (no AWS integration)")
            return True
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            return False
    else:
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False

def launch_detailed_step_dashboard():
    """Launch the detailed step-by-step dashboard"""
    dashboard_file = Path(__file__).parent / "detailed_step_dashboard.html"
    
    if dashboard_file.exists():
        file_url = f"file://{dashboard_file.absolute()}"
        print(f"🚀 Opening Detailed Step Dashboard...")
        print(f"📁 File: {dashboard_file}")
        
        try:
            webbrowser.open(file_url)
            print("✅ Dashboard opened in your browser!")
            print("🔍 Features: Step-by-step processing, real-time logs, detailed metrics")
            print("📊 Shows exactly what happens in each pipeline step!")
            return True
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            return False
    else:
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False

def launch_sla_mitigation_dashboard():
    """Launch the AI-powered SLA mitigation dashboard"""
    dashboard_file = Path(__file__).parent / "sla_mitigation_dashboard.html"
    
    if dashboard_file.exists():
        file_url = f"file://{dashboard_file.absolute()}"
        print(f"🚀 Opening AI-Powered SLA Mitigation Dashboard...")
        print(f"📁 File: {dashboard_file}")
        
        try:
            webbrowser.open(file_url)
            print("✅ Dashboard opened in your browser!")
            print("🤖 Features: AI breach prediction, real-time mitigation, AWS-native components")
            print("🛡️ Shows complete SLA breach prevention process!")
            return True
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            return False
    else:
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False

def show_dashboard_features():
    """Show the amazing features of the live dashboard"""
    print("🛡️ SLA Guard Live Interactive Dashboard")
    print("=" * 50)
    print("🎫 LIVE TICKET CREATION:")
    print("   • Create random tickets with realistic data")
    print("   • Generate critical tickets with high breach probability")
    print("   • Custom ticket creation with form inputs")
    print("   • Traffic burst simulation (5-12 tickets)")
    print("   • Auto-creation every 10-30 seconds")
    print()
    print("🏭 LIVE PIPELINE VISUALIZATION:")
    print("   • Real-time ticket flow through 8 pipeline steps")
    print("   • Animated step counters and progress bars")
    print("   • Color-coded risk levels (green/yellow/red)")
    print("   • Processing status with pulsing animations")
    print()
    print("📊 INTERACTIVE CONTROLS:")
    print("   • Pause/Resume processing")
    print("   • Filter tickets by risk level or status")
    print("   • Real-time statistics updates")
    print("   • Clear all tickets")
    print()
    print("🚨 REAL-TIME ALERTS:")
    print("   • High-risk ticket notifications")
    print("   • Revenue impact warnings ($100K+)")
    print("   • SLA breach probability alerts")
    print("   • System status notifications")
    print()
    print("💾 AWS INTEGRATION (Live Server):")
    print("   • Real DynamoDB ticket storage")
    print("   • Actual AWS service status checking")
    print("   • Live CloudWatch metrics")
    print("   • Background ticket processing")
    print()

def show_launch_options():
    """Show available launch options"""
    print("🎯 Launch Options:")
    print("=" * 20)
    print("1. 🌟 Live Dashboard with AWS Integration (Recommended)")
    print("   • Real DynamoDB ticket creation")
    print("   • Live AWS service monitoring")
    print("   • Background processing simulation")
    print("   • REST API endpoints")
    print()
    print("2. 🤖 AI-Powered SLA Mitigation Dashboard (NEW!)")
    print("   • Complete breach prediction & prevention demo")
    print("   • AWS-native components visualization")
    print("   • Real-time AI mitigation actions")
    print("   • Shows Lambda, SageMaker, Step Functions, QuickSight")
    print()
    print("3. 🔍 Detailed Step Dashboard")
    print("   • Step-by-step processing visualization")
    print("   • Real-time activity logs for each step")
    print("   • Detailed metrics and status")
    print("   • Shows exactly what happens in each step")
    print()
    print("4. 🎨 Static Live Dashboard")
    print("   • Beautiful interactive UI")
    print("   • Simulated ticket processing")
    print("   • No server or AWS required")
    print("   • Perfect for demos")
    print()
    print("5. 📋 Show Features")
    print("   • Detailed feature overview")
    print("   • What makes it interactive")
    print()

def main():
    """Main function"""
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == 'live':
            port = 8080
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                except ValueError:
                    print("Invalid port. Using default 8080.")
            launch_live_dashboard(port)
        elif action == 'mitigation' or action == 'ai':
            launch_sla_mitigation_dashboard()
        elif action == 'detailed':
            launch_detailed_step_dashboard()
        elif action == 'static':
            launch_static_live_dashboard()
        elif action == 'features':
            show_dashboard_features()
        elif action == 'help':
            show_launch_options()
        else:
            print("Usage: python launch_live_dashboard.py [live|mitigation|detailed|static|features|help]")
            print("Run without arguments for interactive menu.")
    else:
        # Interactive menu
        show_dashboard_features()
        print()
        show_launch_options()
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                port_input = input("Enter port (default 8080): ").strip()
                port = 8080
                if port_input:
                    try:
                        port = int(port_input)
                    except ValueError:
                        print("Invalid port. Using default 8080.")
                
                print(f"\n🚀 Launching Live Dashboard on port {port}...")
                print("💡 This will create REAL tickets in your DynamoDB table!")
                confirm = input("Continue? (y/N): ").strip().lower()
                
                if confirm == 'y':
                    launch_live_dashboard(port)
                else:
                    print("Launching AI mitigation dashboard instead...")
                    launch_sla_mitigation_dashboard()
            elif choice == '2':
                launch_sla_mitigation_dashboard()
            elif choice == '3':
                launch_detailed_step_dashboard()
            elif choice == '4':
                launch_static_live_dashboard()
            elif choice == '5':
                show_dashboard_features()
            else:
                print("Invalid choice. Launching AI mitigation dashboard...")
                launch_sla_mitigation_dashboard()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()