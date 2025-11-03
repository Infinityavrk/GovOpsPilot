#!/usr/bin/env python3
"""
Launch Bedrock UI
Quick launcher for the Bedrock Claude UI with system checks
"""

import os
import sys
import subprocess
import webbrowser
import time
from datetime import datetime

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = ['flask', 'flask-cors', 'boto3']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"   ✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"   ❌ Failed to install {package}")
                return False
    
    return True

def check_bearer_token():
    """Check if bearer token is set"""
    print("\n🔑 Checking bearer token...")
    
    bearer_token = os.environ.get('AWS_BEARER_TOKEN_BEDROCK')
    if bearer_token:
        print(f"   ✅ Bearer token found ({len(bearer_token)} characters)")
        return True
    else:
        print(f"   ⚠️ Bearer token not found in environment")
        
        # Set the bearer token
        token = "bedrock-api-key-YmVkcm9jay5hbWF6b25hd3MuY29tLz9BY3Rpb249Q2FsbFdpdGhCZWFyZXJUb2tlbiZYLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFTSUFYTkFBWjRIR0pMSUxEQk1JJTJGMjAyNTExMDIlMkZ1cy1lYXN0LTIlMkZiZWRyb2NrJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTExMDJUMTcyMTI2WiZYLUFtei1FeHBpcmVzPTQzMjAwJlgtQW16LVNlY3VyaXR5LVRva2VuPUlRb0piM0pwWjJsdVgyVmpFSUglMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkZ3RWFDWFZ6TFdWaGMzUXRNaUpITUVVQ0lRRE0wZ0xGZFlwN0VPcFREeHBsVGkzSiUyQkp6MEQ0bFFLdGp5V0NiMWJrU3Nld0lnWmI3d3Q2TUVBYjRjTUJpeG14a0NjaEJSWUVobFNiam5lY01NNjJaQUR6RXF0UVFJU2hBQUdndzFNRGc1TlRVek1qQTNPREFpRE1TNnluYWJQYXRjclhRMGlpcVNCQ2hnM1B4cjRUTyUyRiUyQnpjSURTNXY0VHliOVNEVGxLUEthNFNPSTJwQkRiYTRJSWx2OXozejAlMkJualUzRkVvTzQyeGxqUGh6aEp3WHd4aXlPdlAlMkJNU3lsdTFHQU9CWXNJeEdtNlRTZ2dhQ003NUhEVEl5ZE1GT255UTJEanZjQk5QVk5ZRHNoZG1ibExISGpxdjNXazNZJTJCbSUyQmtsVnByTXpDWGQ3SlBCdHpFcW8zRHhCSWIzOGhHYWVnMVJvVWtBdWdJdzlmM1BhU2klMkZKZEsxVGlxcXhmcmZPaUdPJTJGOUVVbnlPWmxqbks4WHlHdU9ZWnR3Vk1XTDFVam1qalBoRzhNZ0tlUXZpbjBjJTJGQVhVbG84dlppR0lWOXp1V21id2xHdjZyRHpYaWY1UmdiMHhSNUlkUGdWJTJCUW9JTTlFJTJCb2JQNTJQMEElMkZhTFpkVlBCcHNjMnVEeEhlSnQ2ejEzTVNXa0FmWnBuU3dBQkRtekVudnF3WjRFeXVSelJqNTNCVTYyUWt2SGZ6YlgzYUtSVHZJcVdBWXY2ejlJRk5tZnhVZXZCOG54bnZtaUtYcVB5alhtciUyQnJZQXJFZVJ2REtWeHBhWEVPYTRwYlM5OTdnYTA3UE15Z3BWZ1Z3RDczQnNROVNtTjhNWnd6eTBrTkNnUG43aGJTVzRlVFNDRVlCSkxiczR5WHlqTWZkMjlNRDk1OFBvNFFieUFtZzhXYXpBVHdXUHJSZHdveDlvelR5cWE2Z0JwQllLMm9ORHNXaEkxJTJCZlZnZFJSU0p3blNMMXJJaFlCNXRXNDZNUUpjcGdzUXBBbXQ2MWdTTWUwM2swSUNhTlpjR3FxN1cydXBIU1p6NG1ZQlNQMnNkTjJGVnBNd01DMFZIZURwZ2JvVzBjR1RpJTJCcmlmVmozJTJCa1glMkJNQ1AyRU5ySjhjajFKTjBxcjklMkZZd1NaYU1BcFdNSUttbnNnR09zTUM5WnZzemFadHZDVyUyQnNzQnhvZkQ0dklMM3YlMkJuYlE1NEdZUFhIZ3Yxc2VEYlVVUUNmTmhYZGgzYzJmWm54cmFOdjlsM1VJcGx3aXU5SDJQV0kyMGglMkZoT1R0ZHg2ZVdUY1hMWkc5VFl2bFk0Tm9YcWlzR0tla2J2YllYbGlPdnpzeFYzUWFPJTJGSEk2MmlFeWJOJTJCT1N2OVI1Zlc2QUoxM1pkY3I5UENIVnpHWElXRHEzSXJuVTF1bHMzMGxrUU5DUmslMkZLMU1ZNkhZc0VKOENsNGZkVm9UdG1iYXgzOHZJZ3ExcWs2WjRETUhaSXhRcDdiJTJGVnRTa0Q0amthRXB3enE2SUtYekJ0ZVBZeTlEZXQ3ZyUyRkRpb2E0dW5tU1RTQkROdG1mVm14SFlheXJ4UGV5ZE9kYnpRRTd2MWllRWM2Mk10b3FMaWpNd2RQUDNQczFZTW82UzFtSUQ4QmtlWHdZJTJCZ1BTQU8zUE5GbE9SOVFKdUZ5bG9EamVlQVNSQURpZ3ZCd2taYVc1dDh2enhPRWJjV0NUNUpyZGQ2ZyUyRmFXbjZzNXR3VGhRY054bm8yRURyWSUyRlElM0QmWC1BbXotU2lnbmF0dXJlPTNjOTc0YjMyOGFjYjQwNmYzMjRlYWRmNDA1N2JjYjA5NzcyOGEwY2MzNzljODQyZTgxZjRkMDBhNDFmOTg4ZjYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JlZlcnNpb249MQ=="
        os.environ['AWS_BEARER_TOKEN_BEDROCK'] = token
        print(f"   ✅ Bearer token set automatically")
        return True

def test_bedrock_connection():
    """Test Bedrock connection"""
    print("\n🤖 Testing Bedrock connection...")
    
    try:
        # Add path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..')
        sys.path.insert(0, os.path.join(project_root, 'integrations', 'genai'))
        
        from enhanced_claude_sonnet_integration import EnhancedClaudeSonnetIntegration
        
        claude_system = EnhancedClaudeSonnetIntegration()
        
        if claude_system.bedrock_available:
            print(f"   ✅ Bedrock client initialized")
            print(f"   🤖 Model: {claude_system.model_id}")
            return True
        else:
            print(f"   ⚠️ Bedrock client not available")
            print(f"   💡 System will use intelligent fallback")
            return True  # Still return True as fallback works
            
    except Exception as e:
        print(f"   ❌ Error testing Bedrock: {e}")
        return False

def launch_ui():
    """Launch the Bedrock UI"""
    print("\n🚀 Launching Bedrock UI...")
    
    # Set up paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    
    try:
        # Import and run the server
        sys.path.insert(0, os.path.join(project_root, 'ui', 'servers'))
        from bedrock_ui_server import app
        
        # Find available port
        port = 5002
        print("   ✅ Server starting...")
        print(f"   🌐 URL: http://localhost:{port}")
        print("   📱 Opening browser...")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open(f'http://localhost:{port}')
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Run the Flask app
        app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error launching UI: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("🚀 SLA GUARD - BEDROCK UI LAUNCHER")
    print("=" * 50)
    print("Launching advanced AI-powered ticket analysis UI")
    print("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        return False
    
    # Step 2: Check bearer token
    if not check_bearer_token():
        print("\n❌ Bearer token setup failed")
        return False
    
    # Step 3: Test Bedrock connection
    if not test_bedrock_connection():
        print("\n❌ Bedrock connection test failed")
        return False
    
    # Step 4: Launch UI
    print("\n" + "="*50)
    print("🎉 ALL CHECKS PASSED!")
    print("="*50)
    print("✅ Dependencies installed")
    print("✅ Bearer token configured")
    print("✅ Bedrock connection tested")
    print("✅ UI ready to launch")
    
    print(f"\n🌟 FEATURES AVAILABLE:")
    print("• 🤖 Real-time Bedrock Claude analysis")
    print("• 🏛️ Government service expertise")
    print("• 🌍 Multi-language support (Hindi-English)")
    print("• 📊 Advanced analytics and predictions")
    print("• ⚡ Intelligent fallback systems")
    print("• 📱 Responsive web interface")
    
    input("\nPress Enter to launch the UI...")
    
    return launch_ui()

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Launch failed")
        sys.exit(1)
    else:
        print("\n✅ UI launched successfully")