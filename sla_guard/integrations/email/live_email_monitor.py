#!/usr/bin/env python3
"""
Live Email Monitor for Real Email Testing
Monitors a real email account and creates tickets from incoming emails
"""

import imaplib
import email
import json
import time
import threading
from datetime import datetime
import os
import re

class LiveEmailMonitor:
    def __init__(self):
        self.email_config = {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'email': 'tjstatindicator@gmail.com',
            'password': 'Trutjadmin@1234',
            'support_email': 'tjstatindicator@gmail.com'
        }
        self.processed_emails = set()
        self.tickets_created = []
        self.monitoring = False
        
    def setup_email_monitor(self, email_address, password, support_email=None):
        """Setup email monitoring configuration"""
        
        self.email_config.update({
            'email': email_address,
            'password': password,
            'support_email': support_email or email_address
        })
        
        print(f"📧 Live Email Monitor Setup")
        print(f"   Email: {email_address}")
        print(f"   Support: {self.email_config['support_email']}")
        print(f"   Server: {self.email_config['imap_server']}")
        
        return True
    
    def test_email_connection(self):
        """Test email connection"""
        
        try:
            print("🔍 Testing email connection...")
            
            mail = imaplib.IMAP4_SSL(self.email_config['imap_server'], 
                                   self.email_config['imap_port'])
            mail.login(self.email_config['email'], self.email_config['password'])
            mail.select('inbox')
            
            # Get email count
            status, messages = mail.search(None, 'ALL')
            email_count = len(messages[0].split()) if messages[0] else 0
            
            mail.close()
            mail.logout()
            
            print(f"   ✅ Connection successful")
            print(f"   📬 Total emails in inbox: {email_count}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
    
    def start_monitoring(self):
        """Start live email monitoring"""
        
        if not self.test_email_connection():
            return False
        
        self.monitoring = True
        
        def monitor_loop():
            print(f"🔄 Starting live email monitoring...")
            print(f"📧 Send emails to: {self.email_config['support_email']}")
            print(f"⏰ Checking every 10 seconds...")
            print(f"🛑 Press Ctrl+C to stop")
            print("=" * 60)
            
            while self.monitoring:
                try:
                    self.check_for_new_emails()
                    time.sleep(10)  # Check every 10 seconds
                    
                except KeyboardInterrupt:
                    print(f"\n👋 Monitoring stopped by user")
                    self.monitoring = False
                    break
                    
                except Exception as e:
                    print(f"❌ Monitoring error: {e}")
                    time.sleep(30)  # Wait longer on error
        
        # Start monitoring in thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        return True
    
    def check_for_new_emails(self):
        """Check for new emails and process them"""
        
        try:
            # Connect to email
            mail = imaplib.IMAP4_SSL(self.email_config['imap_server'], 
                                   self.email_config['imap_port'])
            mail.login(self.email_config['email'], self.email_config['password'])
            mail.select('inbox')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
                
                for email_id in email_ids:
                    if email_id.decode() not in self.processed_emails:
                        self.process_email(mail, email_id)
                        self.processed_emails.add(email_id.decode())
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"❌ Error checking emails: {e}")
    
    def process_email(self, mail, email_id):
        """Process a single email"""
        
        try:
            # Fetch email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if status == 'OK':
                # Parse email
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email data
                email_data = self.extract_email_data(email_message)
                
                print(f"\n📧 NEW EMAIL RECEIVED:")
                print(f"   From: {email_data['from']}")
                print(f"   Subject: {email_data['subject']}")
                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                
                # Check if it's a support request
                if self.is_support_email(email_data):
                    ticket_data = self.create_ticket_from_email(email_data)
                    
                    if ticket_data:
                        self.tickets_created.append(ticket_data)
                        self.save_ticket_data(ticket_data)
                        
                        print(f"   ✅ TICKET CREATED:")
                        print(f"      Ticket ID: {ticket_data['ticket_id']}")
                        print(f"      Department: {ticket_data['department']}")
                        print(f"      Priority: {ticket_data['priority']}")
                        print(f"      Location: {ticket_data['location']}")
                        print(f"      SLA Deadline: {ticket_data['sla_deadline']}")
                        print(f"      Breach Risk: {ticket_data['breach_probability']:.1%}")
                        
                        # Update web interface
                        self.update_web_interface()
                        
                        # Mark as read
                        mail.store(email_id, '+FLAGS', '\\Seen')
                else:
                    print(f"   ℹ️  Not a support request - skipped")
                
        except Exception as e:
            print(f"❌ Error processing email {email_id}: {e}")
    
    def extract_email_data(self, email_message):
        """Extract data from email message"""
        
        # Get email body
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return {
            'from': email_message.get('From', ''),
            'to': email_message.get('To', ''),
            'subject': email_message.get('Subject', ''),
            'date': email_message.get('Date', ''),
            'body': body,
            'message_id': email_message.get('Message-ID', ''),
            'received_at': datetime.now().isoformat()
        }
    
    def is_support_email(self, email_data):
        """Check if email is a support request"""
        
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        
        # Support keywords
        support_keywords = [
            'problem', 'issue', 'error', 'fail', 'not working', 'down', 'outage',
            'authentication', 'aadhaar', 'service', 'unable', 'cannot', 'help',
            'support', 'urgent', 'critical', 'broken', 'bug', 'complaint',
            'payment', 'portal', 'mobile', 'app', 'certificate', 'digital',
            'timeout', 'slow', 'crash', 'login', 'access'
        ]
        
        return any(keyword in subject or keyword in body for keyword in support_keywords)
    
    def create_ticket_from_email(self, email_data):
        """Create ticket from email data"""
        
        # Analyze email content
        analysis = self.analyze_email_content(email_data)
        
        # Generate ticket ID
        now = datetime.now()
        date_str = now.strftime('%y%m%d')
        time_str = now.strftime('%H%M')
        ticket_id = f"{analysis['department']}-{analysis['priority']}-{date_str}-{time_str}"
        
        # Calculate SLA deadline
        sla_hours = {
            'P1': 2, 'P2': 8, 'P3': 24, 'P4': 72
        }.get(analysis['priority'], 24)
        
        sla_deadline = now.replace(hour=(now.hour + sla_hours) % 24)
        
        # Create ticket data
        ticket_data = {
            'ticket_id': ticket_id,
            'source': 'email',
            'email_from': email_data['from'],
            'email_subject': email_data['subject'],
            'email_body': email_data['body'],
            'department': analysis['department'],
            'priority': analysis['priority'],
            'service_type': analysis['service_type'],
            'location': analysis['location'],
            'reporter_name': self.extract_name_from_email(email_data['from']),
            'contact': self.extract_email_from_sender(email_data['from']),
            'description': email_data['body'][:500] + ('...' if len(email_data['body']) > 500 else ''),
            'status': 'Open',
            'created_at': now.isoformat(),
            'sla_deadline': sla_deadline.strftime('%I:%M %p'),
            'breach_probability': self.calculate_breach_probability(analysis),
            'revenue_impact': self.calculate_revenue_impact(analysis),
            'confidence_score': 0.85,
            'customer_tier': self.map_priority_to_tier(analysis['priority']),
            'sla_met': 'Pending',
            'resolution_time_hours': 0,
            'ai_analyzed': True
        }
        
        return ticket_data
    
    def analyze_email_content(self, email_data):
        """Analyze email content to extract ticket information"""
        
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        text = subject + ' ' + body
        
        # Determine priority
        priority = 'P3'  # Default medium
        if any(word in text for word in ['critical', 'urgent', 'emergency', 'outage', 'down', 'failing']):
            priority = 'P1'
        elif any(word in text for word in ['important', 'asap', 'priority', 'high', 'serious']):
            priority = 'P2'
        elif any(word in text for word in ['question', 'inquiry', 'request', 'minor']):
            priority = 'P4'
        
        # Determine department
        department = 'MPOnline'  # Default
        if any(word in text for word in ['aadhaar', 'aadhar', 'authentication', 'biometric', 'uid']):
            department = 'UIDAI'
        elif any(word in text for word in ['payment', 'transaction', 'money', 'bank', 'gateway']):
            department = 'MeiTY'
        elif any(word in text for word in ['portal', 'website', 'digital', 'online']):
            department = 'DigitalMP'
        elif any(word in text for word in ['certificate', 'document', 'service', 'district']):
            department = 'eDistrict'
        
        # Determine service type
        service_type = 'other'
        if any(word in text for word in ['aadhaar', 'authentication', 'biometric']):
            service_type = 'aadhaar-auth'
        elif any(word in text for word in ['payment', 'gateway', 'transaction']):
            service_type = 'payment-gateway'
        elif any(word in text for word in ['portal', 'website']):
            service_type = 'citizen-portal'
        elif any(word in text for word in ['mobile', 'app', 'smartphone']):
            service_type = 'mobile-app'
        elif any(word in text for word in ['certificate', 'document']):
            service_type = 'certificate-services'
        
        # Extract location
        location = self.extract_location(text)
        
        return {
            'priority': priority,
            'department': department,
            'service_type': service_type,
            'location': location
        }
    
    def extract_location(self, text):
        """Extract location from text"""
        
        locations = [
            'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'kolkata',
            'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur',
            'indore', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'gwalior',
            'jabalpur', 'ujjain', 'sagar', 'dewas', 'satna', 'ratlam',
            'maharashtra', 'karnataka', 'tamil nadu', 'uttar pradesh', 'gujarat',
            'rajasthan', 'west bengal', 'madhya pradesh', 'telangana', 'bihar'
        ]
        
        found_locations = []
        for location in locations:
            if location in text.lower():
                found_locations.append(location.title())
        
        return ', '.join(found_locations) if found_locations else 'Not specified'
    
    def extract_name_from_email(self, email_str):
        """Extract name from email address"""
        
        if '<' in email_str:
            name = email_str.split('<')[0].strip().strip('"')
            return name if name else 'Unknown'
        else:
            return email_str.split('@')[0].replace('.', ' ').title()
    
    def extract_email_from_sender(self, email_str):
        """Extract email address from sender string"""
        
        if '<' in email_str:
            return email_str.split('<')[1].split('>')[0]
        else:
            return email_str
    
    def calculate_breach_probability(self, analysis):
        """Calculate breach probability"""
        
        base_prob = {
            'P1': 0.85, 'P2': 0.65, 'P3': 0.45, 'P4': 0.25
        }.get(analysis['priority'], 0.45)
        
        # Adjust for service type
        service_multiplier = {
            'aadhaar-auth': 1.3,
            'payment-gateway': 1.2,
            'citizen-portal': 1.1,
            'mobile-app': 1.0,
            'certificate-services': 1.1,
            'other': 1.0
        }.get(analysis['service_type'], 1.0)
        
        return min(0.95, base_prob * service_multiplier)
    
    def calculate_revenue_impact(self, analysis):
        """Calculate revenue impact"""
        
        base_impact = {
            'P1': 200000, 'P2': 100000, 'P3': 50000, 'P4': 20000
        }.get(analysis['priority'], 50000)
        
        service_multiplier = {
            'aadhaar-auth': 2.0,
            'payment-gateway': 1.8,
            'citizen-portal': 1.2,
            'mobile-app': 1.1,
            'certificate-services': 1.3,
            'other': 1.0
        }.get(analysis['service_type'], 1.0)
        
        return int(base_impact * service_multiplier)
    
    def map_priority_to_tier(self, priority):
        """Map priority to customer tier"""
        
        return {
            'P1': 'Enterprise',
            'P2': 'Platinum',
            'P3': 'Gold',
            'P4': 'Silver'
        }.get(priority, 'Silver')
    
    def save_ticket_data(self, ticket_data):
        """Save ticket data to JSON file"""
        
        # Save individual ticket
        filename = f"sla_guard/aws_deployment/live_tickets.json"
        
        try:
            # Load existing tickets
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    tickets = json.load(f)
            else:
                tickets = []
            
            # Add new ticket
            tickets.append(ticket_data)
            
            # Keep only last 50 tickets
            tickets = tickets[-50:]
            
            # Save updated tickets
            with open(filename, 'w') as f:
                json.dump(tickets, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving ticket: {e}")
    
    def update_web_interface(self):
        """Update web interface with latest ticket data"""
        
        try:
            # Create JavaScript file for web interface
            js_content = f'''
// Live ticket data - Updated: {datetime.now().isoformat()}
const liveTickets = {json.dumps(self.tickets_created, indent=2)};

// Function to load live tickets into web interface
function loadLiveTickets() {{
    console.log('Loading live tickets:', liveTickets.length);
    
    // Update counters
    document.getElementById('emails-processed-count').textContent = {len(self.tickets_created)};
    document.getElementById('tickets-from-email-count').textContent = {len(self.tickets_created)};
    
    // Process each ticket
    liveTickets.forEach((ticket, index) => {{
        setTimeout(() => {{
            if (typeof processIncomingEmail === 'function') {{
                processIncomingEmail(ticket);
            }}
        }}, index * 1000); // 1 second delay between tickets
    }});
}}

// Auto-load on page load
if (typeof document !== 'undefined') {{
    document.addEventListener('DOMContentLoaded', loadLiveTickets);
}}
'''
            
            with open('sla_guard/aws_deployment/live_tickets.js', 'w') as f:
                f.write(js_content)
                
        except Exception as e:
            print(f"❌ Error updating web interface: {e}")
    
    def get_statistics(self):
        """Get monitoring statistics"""
        
        return {
            'total_emails_processed': len(self.processed_emails),
            'tickets_created': len(self.tickets_created),
            'success_rate': 100.0 if self.tickets_created else 0.0,
            'monitoring_active': self.monitoring,
            'last_check': datetime.now().isoformat()
        }
    
    def stop_monitoring(self):
        """Stop email monitoring"""
        
        self.monitoring = False
        print("🛑 Email monitoring stopped")

def main():
    """Main function to start live email monitoring"""
    
    try:
        monitor = LiveEmailMonitor()
        
        print("📧 LIVE EMAIL MONITOR FOR TICKET CREATION")
        print("=" * 50)
        print("This will monitor a real email account and create tickets from incoming emails.")
        print()
        
        # Get email configuration
        email_address = input("📧 Enter your email address: ").strip()
        
        if not email_address:
            print("❌ Email address is required")
            return
        
        # For Gmail, you need an app password
        print("\n🔐 For Gmail users:")
        print("   1. Enable 2-Factor Authentication")
        print("   2. Generate an App Password")
        print("   3. Use the App Password (not your regular password)")
        print()
        
        password = input("🔐 Enter your email password/app password: ").strip()
        
        if not password:
            print("❌ Password is required")
            return
        
        support_email = input("🎫 Enter support email (or press Enter to use same): ").strip()
        
        # Setup monitor
        monitor.setup_email_monitor(email_address, password, support_email)
        
        # Test connection
        if not monitor.test_email_connection():
            return
        
        print(f"\n🚀 LIVE EMAIL MONITORING READY!")
        print(f"📧 Monitoring: {email_address}")
        print(f"🎫 Support Email: {monitor.email_config['support_email']}")
        print(f"⏰ Check Interval: 10 seconds")
        print()
        
        print("📝 HOW TO TEST:")
        print(f"1. Send an email to: {monitor.email_config['support_email']}")
        print("2. Subject: 'Aadhaar authentication services failing in Indore'")
        print("3. Body: Include keywords like 'critical', 'urgent', 'authentication', 'Indore'")
        print("4. Watch the console for automatic ticket creation")
        print("5. Check live_tickets.json for created ticket data")
        print()
        
        # Start monitoring
        if monitor.start_monitoring():
            try:
                while monitor.monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop_monitoring()
        
        # Show final statistics
        stats = monitor.get_statistics()
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Emails Processed: {stats['total_emails_processed']}")
        print(f"   Tickets Created: {stats['tickets_created']}")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")
        
        if monitor.tickets_created:
            print(f"\n🎫 TICKETS CREATED:")
            for ticket in monitor.tickets_created:
                print(f"   • {ticket['ticket_id']} ({ticket['priority']}) - {ticket['location']}")
        
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    main()