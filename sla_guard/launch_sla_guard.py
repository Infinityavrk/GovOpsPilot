#!/usr/bin/env python3
"""
Main SLA Guard Launcher
Organized production launcher with proper imports
"""

import sys
import os
import subprocess
import webbrowser
import time

# Add core modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'integrations'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

def setup_environment():
    """Setup environment variables"""
    # Set the bearer token for AWS Bedrock
    os.environ['AWS_BEARER_TOKEN_BEDROCK'] = "bedrock-api-key-YmVkcm9jay5hbWF6b25hd3MuY29tLz9BY3Rpb249Q2FsbFdpdGhCZWFyZXJUb2tlbiZYLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFTSUFYTkFBWjRIR0pMSUxEQk1JJTJGMjAyNTExMDIlMkZ1cy1lYXN0LTIlMkZiZWRyb2NrJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTExMDJUMTcyMTI2WiZYLUFtei1FeHBpcmVzPTQzMjAwJlgtQW16LVNlY3VyaXR5LVRva2VuPUlRb0piM0pwWjJsdVgyVmpFSUglMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkZ3RWFDWFZ6TFdWaGMzUXRNaUpITUVVQ0lRRE0wZ0xGZFlwN0VPcFREeHBsVGkzSiUyQkp6MEQ0bFFLdGp5V0NiMWJrU3Nld0lnWmI3d3Q2TUVBYjRjTUJpeG14a0NjaEJSWUVobFNiam5lY01NNjJaQUR6RXF0UVFJU2hBQUdndzFNRGc1TlRVek1qQTNPREFpRE1TNnluYWJQYXRjclhRMGlpcVNCQ2hnM1B4cjRUTyUyRiUyQnpjSURTNXY0VHliOVNEVGxLUEthNFNPSTJwQkRiYTRJSWx2OXozejAlMkJualUzRkVvTzQyeGxqUGh6aEp3WHd4aXlPdlAlMkJNU3lsdTFHQU9CWXNJeEdtNlRTZ2dhQ003NUhEVEl5ZE1GT255UTJEanZjQk5QVk5ZRHNoZG1ibExISGpxdjNXazNZJTJCbSUyQmtsVnByTXpDWGQ3SlBCdHpFcW8zRHhCSWIzOGhHYWVnMVJvVWtBdWdJdzlmM1BhU2klMkZKZEsxVGlxcXhmcmZPaUdPJTJGOUVVbnlPWmxqbks4WHlHdU9ZWnR3Vk1XTDFVam1qalBoRzhNZ0tlUXZpbjBjJTJGQVhVbG84dlppR0lWOXp1V21id2xHdjZyRHpYaWY1UmdiMHhSNUlkUGdWJTJCUW9JTTlFJTJCb2JQNTJQMEElMkZhTFpkVlBCcHNjMnVEeEhlSnQ2ejEzTVNXa0FmWnBuU3dBQkRtekVudnF3WjRFeXVSelJqNTNCVTYyUWt2SGZ6YlgzYUtSVHZJcVdBWXY2ejlJRk5tZnhVZXZCOG54bnZtaUtYcVB5alhtciUyQnJZQXJFZVJ2REtWeHBhWEVPYTRwYlM5OTdnYTA3UE15Z3BWZ1Z3RDczQnNROVNtTjhNWnd6eTBrTkNnUG43aGJTVzRlVFNDRVlCSkxiczR5WHlqTWZkMjlNRDk1OFBvNFFieUFtZzhXYXpBVHdXUHJSZHdveDlvelR5cWE2Z0JwQllLMm9ORHNXaEkxJTJCZlZnZFJSU0p3blNMMXJJaFlCNXRXNDZNUUpjcGdzUXBBbXQ2MWdTTWUwM2swSUNhTlpjR3FxN1cydXBIU1p6NG1ZQlNQMnNkTjJGVnBNd01DMFZIZURwZ2JvVzBjR1RpJTJCcmlmVmozJTJCa1glMkJNQ1AyRU5ySjhjajFKTjBxcjklMkZZd1NaYU1BcFdNSUttbnNnR09zTUM5WnZzemFadHZDVyUyQnNzQnhvZkQ0dklMM3YlMkJuYlE1NEdZUFhIZ3Yxc2VEYlVVUUNmTmhYZGgzYzJmWm54cmFOdjlsM1VJcGx3aXU5SDJQV0kyMGglMkZoT1R0ZHg2ZVdUY1hMWkc5VFl2bFk0Tm9YcWlzR0tla2J2YllYbGlPdnpzeFYzUWFPJTJGSEk2MmlFeWJOJTJCT1N2OVI1Zlc2QUoxM1pkY3I5UENIVnpHWElXRHEzSXJuVTF1bHMzMGxrUU5DUmslMkZLMU1ZNkhZc0VKOENsNGZkVm9UdG1iYXgzOHZJZ3ExcWs2WjRETUhaSXhRcDdiJTJGVnRTa0Q0amthRXB3enE2SUtYekJ0ZVBZeTlEZXQ3ZyUyRkRpb2E0dW5tU1RTQkROdG1mVm14SFlheXJ4UGV5ZE9kYnpRRTd2MWllRWM2Mk10b3FMaWpNd2RQUDNQczFZTW82UzFtSUQ4QmtlWHdZJTJCZ1BTQU8zUE5GbE9SOVFKdUZ5bG9EamVlQVNSQURpZ3ZCd2taYVc1dDh2enhPRWJjV0NUNUpyZGQ2ZyUyRmFXbjZzNXR3VGhRY054bm8yRURyWSUyRlElM0QmWC1BbXotU2lnbmF0dXJlPTNjOTc0YjMyOGFjYjQwNmYzMjRlYWRmNDA1N2JjYjA5NzcyOGEwY2MzNzljODQyZTgxZjRkMDBhNDFmOTg4ZjYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JlZlcnNpb249MQ=="
    print("✅ Environment configured")

def find_available_port():
    """Find an available port"""
    import socket
    
    for port in range(5002, 5010):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return 5002

def launch_enhanced_ui():
    """Launch the enhanced SLA Guard UI"""
    print("🚀 Launching SLA Guard Enhanced UI")
    print("=" * 50)
    
    setup_environment()
    
    # Find available port
    port = find_available_port()
    print(f"🌐 Using port: {port}")
    
    try:
        # Add path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, os.path.join(current_dir, 'ui', 'servers'))
        
        # Import the server
        from bedrock_ui_server import app
        
        def start_server():
            app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
        
        # Start server in background thread
        import threading
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Open browser
        url = f'http://localhost:{port}'
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)
        
        print(f"\n🎉 SLA Guard Enhanced UI Launched Successfully!")
        print("=" * 50)
        print(f"🌐 URL: {url}")
        print("🔧 Features:")
        print("   ✅ Real-time AI ticket analysis")
        print("   ✅ License optimization with AWS AI")
        print("   ✅ Bedrock Llama 3.2 integration")
        print("   ✅ Government service expertise")
        print("   ✅ GeM procurement integration")
        print()
        print("Press Ctrl+C to stop the server...")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
            
    except Exception as e:
        print(f"❌ Error launching server: {e}")

def main():
    """Main launcher with options"""
    print("🎯 SLA GUARD - PRODUCTION LAUNCHER")
    print("=" * 60)
    print("🏛️ Government Service Efficiency Platform")
    print("🤖 Powered by AWS AI & Bedrock")
    print("=" * 60)
    
    print("\nAvailable Options:")
    print("1. 🚀 Launch Enhanced UI (Recommended)")
    print("2. 📊 Launch License Optimization")
    print("3. 🤖 Launch GenAI Workflow")
    print("4. ⚙️ Setup AWS Configuration")
    
    try:
        choice = input("\nSelect option (1-4) or press Enter for Enhanced UI: ").strip()
        
        if choice == "" or choice == "1":
            launch_enhanced_ui()
        elif choice == "2":
            print("📊 Launching License Optimization...")
            # License optimization is integrated in the Enhanced UI
            launch_enhanced_ui()
        elif choice == "3":
            print("🤖 Launching GenAI Workflow...")
            # GenAI workflow is integrated in the Enhanced UI
            launch_enhanced_ui()
        elif choice == "4":
            print("⚙️ Opening AWS Configuration...")
            subprocess.run([sys.executable, "config/aws/setup_aws_credentials.py"])
        else:
            print("Invalid option. Launching Enhanced UI...")
            launch_enhanced_ui()
            
    except KeyboardInterrupt:
        print("\n✅ Launcher stopped by user")
    except Exception as e:
        print(f"\n❌ Launch failed: {e}")

if __name__ == "__main__":
    main()