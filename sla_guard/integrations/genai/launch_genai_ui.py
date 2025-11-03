#!/usr/bin/env python3
"""
Launch GenAI Workflow UI Server
Serves the interactive web interface for testing the complete GenAI workflow
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def launch_ui_server(port=8080):
    """Launch the GenAI workflow UI server"""
    
    # Change to the directory containing the HTML file
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if the HTML file exists
    html_file = "genai_workflow_ui.html"
    if not os.path.exists(html_file):
        print(f"❌ Error: {html_file} not found in {script_dir}")
        return
    
    print("🚀 AWS GenAI Workflow UI Server")
    print("=" * 50)
    print(f"📁 Serving from: {script_dir}")
    print(f"🌐 Port: {port}")
    print(f"📄 Main file: {html_file}")
    
    # Create HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            server_url = f"http://localhost:{port}/{html_file}"
            
            print(f"\n✅ Server started successfully!")
            print(f"🔗 Open in browser: {server_url}")
            print(f"\n🎯 Features:")
            print(f"   • Interactive GenAI workflow demonstration")
            print(f"   • Real-time pipeline visualization")
            print(f"   • Multiple test scenarios")
            print(f"   • Service status monitoring")
            print(f"   • ML prediction results")
            print(f"   • Alert decision simulation")
            
            print(f"\n📋 Test Scenarios Available:")
            print(f"   🔴 Critical Issue - Aadhaar system failure")
            print(f"   💳 Payment Problem - Gateway timeout issues")
            print(f"   🌐 Portal Issue - Access problems")
            print(f"   😊 Positive Feedback - User satisfaction")
            
            print(f"\n⚡ Workflow Steps Demonstrated:")
            print(f"   1. 📝 Natural Text Input")
            print(f"   2. 🧠 Bedrock + Comprehend Analysis")
            print(f"   3. 💾 DynamoDB Ticket Storage")
            print(f"   4. 📡 EventBridge Event Trigger")
            print(f"   5. ⚡ Lambda Function Processing")
            print(f"   6. 🤖 SageMaker ML Prediction")
            print(f"   7. 🚨 SNS Alert Decision")
            print(f"   8. 📊 QuickSight Data Preparation")
            
            print(f"\n🛑 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Try to open browser automatically
            try:
                webbrowser.open(server_url)
                print(f"🌐 Browser opened automatically")
            except Exception as e:
                print(f"⚠️ Could not open browser automatically: {e}")
                print(f"   Please manually open: {server_url}")
            
            # Start serving
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {port} is already in use")
            print(f"   Try a different port: python {sys.argv[0]} --port 8081")
        else:
            print(f"❌ Error starting server: {e}")
    except KeyboardInterrupt:
        print(f"\n\n🛑 Server stopped by user")
        print(f"✅ GenAI Workflow UI server shut down successfully")

def main():
    """Main function with command line argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Launch AWS GenAI Workflow UI')
    parser.add_argument('--port', type=int, default=8080, help='Port to serve on (default: 8080)')
    
    args = parser.parse_args()
    
    launch_ui_server(args.port)

if __name__ == "__main__":
    main()