#!/usr/bin/env python3
"""
Launch License Optimization UI Server
Serves the AI License & Asset Optimization interface
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def launch_license_ui(port=8083):
    """Launch the License Optimization UI server"""
    
    # Change to the directory containing the HTML file
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if the HTML file exists
    html_file = "license_optimization_ui.html"
    if not os.path.exists(html_file):
        print(f"❌ Error: {html_file} not found in {script_dir}")
        return
    
    print("🤖 AI License & Asset Optimization Platform")
    print("=" * 60)
    print("🎯 Intelligent License Management with GeM Integration")
    print("=" * 60)
    print(f"📁 Serving from: {script_dir}")
    print(f"🌐 Port: {port}")
    print(f"📄 Main file: {html_file}")
    
    # Create HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            server_url = f"http://localhost:{port}/{html_file}"
            
            print(f"\n✅ License Optimization UI Started!")
            print(f"🔗 Open in browser: {server_url}")
            
            print(f"\n🤖 AI-Powered Features:")
            print(f"   • Intelligent license usage analysis")
            print(f"   • Automated underutilization detection")
            print(f"   • Duplicate subscription identification")
            print(f"   • Cost optimization recommendations")
            print(f"   • ML-powered savings predictions")
            
            print(f"\n🛒 GeM Procurement Integration:")
            print(f"   • Automated GeM catalog search")
            print(f"   • Procurement request generation")
            print(f"   • Vendor quote evaluation")
            print(f"   • Compliance verification")
            print(f"   • Finance approval workflow")
            
            print(f"\n📊 License Portfolio Management:")
            print(f"   • Real-time utilization monitoring")
            print(f"   • Renewal alerts and optimization")
            print(f"   • Vendor consolidation analysis")
            print(f"   • Department-wise cost breakdown")
            print(f"   • Portfolio health scoring")
            
            print(f"\n💰 Financial Benefits:")
            print(f"   • Cost reduction identification")
            print(f"   • ROI calculation and tracking")
            print(f"   • Budget optimization suggestions")
            print(f"   • Savings potential analysis")
            print(f"   • Payback period estimation")
            
            print(f"\n🔧 Key Capabilities:")
            print(f"   • Auto-detect underused licenses (Zoom, Adobe, etc.)")
            print(f"   • Suggest license rationalization")
            print(f"   • Recommend cost-saving bundles")
            print(f"   • Integrate with GeM procurement")
            print(f"   • Finance approval workflows")
            
            print(f"\n📈 Analytics & Reporting:")
            print(f"   • Portfolio health dashboard")
            print(f"   • Utilization trend analysis")
            print(f"   • Cost optimization reports")
            print(f"   • Vendor performance metrics")
            print(f"   • Compliance tracking")
            
            print(f"\n🎯 Use Cases:")
            print(f"   • Reduce unused Zoom licenses")
            print(f"   • Consolidate Adobe subscriptions")
            print(f"   • Optimize antivirus licensing")
            print(f"   • Negotiate better renewal terms")
            print(f"   • Eliminate duplicate software")
            
            print(f"\n🛑 Press Ctrl+C to stop the server")
            print("=" * 60)
            
            # Try to open browser automatically
            try:
                webbrowser.open(server_url)
                print(f"🌐 Browser opened automatically")
                print(f"💡 If browser didn't open, manually visit: {server_url}")
            except Exception as e:
                print(f"⚠️ Could not open browser automatically: {e}")
                print(f"   Please manually open: {server_url}")
            
            print(f"\n🎉 Start optimizing your license portfolio!")
            
            # Start serving
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {port} is already in use")
            print(f"   Try a different port: python {sys.argv[0]} --port {port + 1}")
        else:
            print(f"❌ Error starting server: {e}")
    except KeyboardInterrupt:
        print(f"\n\n🛑 Server stopped by user")
        print(f"✅ License Optimization UI server shut down successfully")
        print(f"🤖 Thank you for using the AI License Optimization Platform!")

def main():
    """Main function with command line argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Launch AI License & Asset Optimization UI')
    parser.add_argument('--port', type=int, default=8083, help='Port to serve on (default: 8083)')
    
    args = parser.parse_args()
    
    launch_license_ui(args.port)

if __name__ == "__main__":
    main()