#!/usr/bin/env python3
"""
Live Ticket Server
Serves the helpdesk form and provides real-time ticket updates
"""

import http.server
import socketserver
import json
import os
import threading
import time
from datetime import datetime

class LiveTicketHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        
        if self.path == '/':
            # Serve the main helpdesk form
            self.path = '/helpdesk_ticket_system.html'
        elif self.path == '/api/tickets':
            # Serve live ticket data
            self.serve_tickets_api()
            return
        elif self.path == '/api/status':
            # Serve monitoring status
            self.serve_status_api()
            return
        
        # Serve static files
        super().do_GET()
    
    def serve_tickets_api(self):
        """Serve live tickets as JSON API"""
        
        try:
            # Load live tickets
            tickets_file = 'live_tickets.json'
            if os.path.exists(tickets_file):
                with open(tickets_file, 'r') as f:
                    tickets = json.load(f)
            else:
                tickets = []
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'tickets': tickets,
                'count': len(tickets),
                'last_updated': datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, f"Error loading tickets: {e}")
    
    def serve_status_api(self):
        """Serve monitoring status"""
        
        try:
            # Check if monitoring is active
            status_file = 'monitor_status.json'
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    status = json.load(f)
            else:
                status = {
                    'monitoring_active': False,
                    'emails_processed': 0,
                    'tickets_created': 0,
                    'last_check': datetime.now().isoformat()
                }
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(status, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, f"Error loading status: {e}")

def start_server(port=8080):
    """Start the live ticket server"""
    
    # Change to the correct directory
    os.chdir('sla_guard/aws_deployment')
    
    try:
        with socketserver.TCPServer(("", port), LiveTicketHandler) as httpd:
            print(f"🌐 Live Ticket Server Started")
            print(f"   URL: http://localhost:{port}")
            print(f"   Helpdesk Form: http://localhost:{port}/")
            print(f"   Tickets API: http://localhost:{port}/api/tickets")
            print(f"   Status API: http://localhost:{port}/api/status")
            print(f"   Press Ctrl+C to stop")
            print("=" * 50)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_server(8081)