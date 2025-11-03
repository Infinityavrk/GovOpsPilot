#!/usr/bin/env python3
"""
Launch Enhanced UI
Quick launcher for the enhanced UI with backend status display
"""

import os
import sys
import webbrowser
import time
import threading
import traceback
from pathlib import Path
import builtins   # <-- we will inject project_root here


def setup_environment():
    """Setup environment variables"""
    os.environ['AWS_BEARER_TOKEN_BEDROCK'] = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
    
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


def detect_project_root():
    """
    Try to find the project root by walking up until we see ui/servers
    """
    # start from script dir if possible, else CWD
    if '__file__' in globals():
        start = Path(__file__).resolve().parent
    else:
        start = Path.cwd()

    for parent in [start] + list(start.parents):
        candidate = parent / "ui" / "servers"
        if candidate.exists():
            return parent

    # fallback: one level up from start
    return start.parent


def launch_server():
    """Launch the enhanced UI server"""
    print("🚀 Launching Enhanced SLA Guard UI")
    print("=" * 50)

    setup_environment()

    port = find_available_port()
    print(f"🌐 Using port: {port}")

    try:
        # 1️⃣ detect root
        project_root = detect_project_root().resolve()
        print(f"📁 Detected project root: {project_root}")

        # 2️⃣ make it available everywhere
        builtins.project_root = str(project_root)         # for modules that just do `project_root`
        os.environ["PROJECT_ROOT"] = str(project_root)    # for modules that read from env

        # 3️⃣ ensure our ui/servers is on path
        servers_path = project_root / "ui" / "servers"
        sys.path.insert(0, str(servers_path))

        # 4️⃣ import server now — this is where your old error came from
        from bedrock_ui_server import app

        def start_server():
            app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        time.sleep(2)

        url = f"http://localhost:{port}"
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)

        print(f"\n🎉 Enhanced UI Launched Successfully!")
        print("=" * 50)
        print(f"🌐 URL: {url}")
        print("🔧 Features:")
        print("   ✅ Real-time backend status display")
        print("   ✅ Single most appropriate category selection")
        print("   ✅ Bedrock Llama 3.2 integration")
        print("   ✅ Intelligent fallback system")
        print("   ✅ Government service expertise")
        print("   ✅ Multi-language support")
        print()
        print("🧪 Test with example tickets to see:")
        print("   • Which AI backend is actually running")
        print("   • Single category classification (no more Payment|Portal)")
        print("   • Real-time performance metrics")
        print()
        print("Press Ctrl+C to stop the server...")

        while True:
            time.sleep(1)

    except Exception as e:
        print("❌ Error launching server:", e)
        print("📄 Full traceback below (this will show which file actually raised it):")
        traceback.print_exc()


def main():
    print("🎯 SLA GUARD - ENHANCED UI LAUNCHER")
    print("=" * 60)
    print("✨ New Features:")
    print("   • Shows actual backend AI being used")
    print("   • Single most appropriate category selection")
    print("   • Real-time status indicators")
    print("   • Enhanced performance metrics")
    print("=" * 60)
    try:
        launch_server()
    except KeyboardInterrupt:
        print("\n✅ Launcher stopped by user")
    except Exception as e:
        print("\n❌ Launch failed:", e)


if __name__ == "__main__":
    main()
