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
    os.environ['AWS_BEARER_TOKEN_BEDROCK'] = (
        "bedrock-api-key-YmVkcm9jay5hbWF6b25hd3MuY29tLz9BY3Rpb249Q2FsbFdpdGhCZWFyZXJUb2tlbiZYLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFTSUFYTkFBWjRIR0pMSUxEQk1JJTJGMjAyNTExMDIlMkZ1cy1lYXN0LTIlMkZiZWRyb2NrJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTExMDJUMTcyMTI2WiZYLUFtei1FeHBpcmVzPTQzMjAwJlgtQW16LVNlY3VyaXR5LVRva2VuPUlRb0piM0pwWjJsdVgyVmpFSUglMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkYlMkZ3RWFDWFZ6TFdWaGMzUXRNaUpITUVVQ0lRRE0wZ0xGZFlwN0VPcFREeHBsVGkzSiUyQkp6MEQ0bFFLdGp5V0NiMWJrU3Nld0lnWmI3d3Q2TUVBYjRjTUJpeG14a0NjaEJSWUVobFNiam5lY01NNjJaQUR6RXF0UVFJU2hBQUdndzFNRGc1TlRVek1qQTNPREFpRE1TNnluYWJQYXRjclhRMGlpcVNCQ2hnM1B4cjRUTyUyRiUyQnpjSURTNXY0VHliOVNEVGxLUEthNFNPSTJwQkRiYTRJSWx2OXozejAlMkJualUzRkVvTzQyeGxqUGh6aEp3WHd4aXlPdlAlMkJNU3lsdTFHQU9CWXNJeEdtNlRTZ2dhQ003NUhEVEl5ZE1GT255UTJEanZjQk5QVk5ZRHNoZG1ibExISGpxdjNXazNZJTJCbSUyQmtsVnByTXpDWGQ3SlBCdHpFcW8zRHhCSWIzOGhHYWVnMVJvVWtBdWdJdzlmM1BhU2klMkZKZEsxVGlxcXhmcmZPaUdPJTJGOUVVbnlPWmxqbks4WHlHdU9ZWnR3Vk1XTDFVam1qalBoRzhNZ0tlUXZpbjBjJTJGQVhVbG84dlppR0lWOXp1V21id2xHdjZyRHpYaWY1UmdiMHhSNUlkUGdWJTJCUW9JTTlFJTJCb2JQNTJQMEElMkZhTFpkVlBCcHNjMnVEeEhlSnQ2ejEzTVNXa0FmWnBuU3dBQkRtekVudnF3WjRFeXVSelJqNTNCVTYyUWt2SGZ6YlgzYUtSVHZJcVdBWXY2ejlJRk5tZnhVZXZCOG54bnZtaUtYcVB5alhtciUyQnJZQXJFZVJ2REtWeHBhWEVPYTRwYlM5OTdnYTA3UE15Z3BWZ1Z3RDczQnNROVNtTjhNWnd6eTBrTkNnUG43aGJTVzRlVFNDRVlCSkxiczR5WHlqTWZkMjlNRDk1OFBvNFFieUFtZzhXYXpBVHdXUHJSZHdveDlvelR5cWE2Z0JwQllLMm9ORHNXaEkxJTJCZlZnZFJSU0p3blNMMXJJaFlCNXRXNDZNUUpjcGdzUXBBbXQ2MWdTTWUwM2swSUNhTlpjR3FxN1cydXBIU1p6NG1ZQlNQMnNkTjJGVnBNd01DMFZIZURwZ2JvVzBjR1RpJTJCcmlmVmozJTJCa1glMkJNQ1AyRU5ySjhjajFKTjBxcjklMkZZd1NaYU1BcFdNSUttbnNnR09zTUM5WnZzemFadHZDVyUyQnNzQnhvZkQ0dklMM3YlMkJuYlE1NEdZUFhIZ3Yxc2VEYlVVUUNmTmhYZGgzYzJmWm54cmFOdjlsM1VJcGx3aXU5SDJQV0kyMGglMkZoT1R0ZHg2ZVdUY1hMWkc5VFl2bFk0Tm9YcWlzR0tla2J2YllYbGlPdnpzeFYzUWFPJTJGSEk2MmlFeWJOJTJCT1N2OVI1Zlc2QUoxM1pkY3I5UENIVnpHWElXRHEzSXJuVTF1bHMzMGxrUU5DUmslMkZLMU1ZNkhZc0VKOENsNGZkVm9UdG1iYXgzOHZJZ3ExcWs2WjRETUhaSXhRcDdiJTJGVnRTa0Q0amthRXB3enE2SUtYekJ0ZVBZeTlEZXQ3ZyUyRkRpb2E0dW5tU1RTQkROdG1mVm14SFlheXJ4UGV5ZE9kYnpRRTd2MWllRWM2Mk10b3FMaWpNd2RQUDNQczFZTW82UzFtSUQ4QmtlWHdZJTJCZ1BTQU8zUE5GbE9SOVFKdUZ5bG9EamVlQVNSQURpZ3ZCd2taYVc1dDh2enhPRWJjV0NUNUpyZGQ2ZyUyRmFXbjZzNXR3VGhRY054bm8yRURyWSUyRlElM0QmWC1BbXotU2lnbmF0dXJlPTNjOTc0YjMyOGFjYjQwNmYzMjRlYWRmNDA1N2JjYjA5NzcyOGEwY2MzNzljODQyZTgxZjRkMDBhNDFmOTg4ZjYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JlZlcnNpb249MQ=="
    )
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
