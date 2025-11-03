#!/usr/bin/env python3
"""
Simple Email Reader for Ticket Creation
Reads emails and populates the existing helpdesk form
"""

import imaplib
import email
import json
import re
from datetime import datetime
import time
import threading

class SimpleEmailReader:
    def __init__(self):
        self.email_config = {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'email': '',
            'password': ''
        }
        self.processed_emails = set()
        self.latest_tickets = []
        
    def setup_email_reader(self, email_address, password):
        """Setup email reader configuration"""
        
        self.email_config.update({
            'email': email_address,
            'password': password
        })
        
        print(f"📧 Email Reader Setup Complete")
        print(f"   Email: {email_address}")
        print(f"   Server: {self.email_config['imap_server']}")
        
        return True
    
    def read_emails(self):
        """Read and process emails"""
        
        try:
            # Connect to email server
            mail = imaplib.IMAP4_SSL(self.email_config['imap_server'], 
                                   self.email_config['imap_port'])
            mail.login(self.email_config['email'], self.email_config['password'])
            mail.select('inbox')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
                
                for email_id in email_ids:
                    try:
                        # Fetch email
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        if status == 'OK':
                            # Parse email
                            email_body = msg_data[0][1]
                            email_message = email.message_from_bytes(email_body)
                            
                            # Extract email data
                            email_data = self.extract_email_data(email_message)
                            
                            # Process for ticket creation
                            ticket_data = self.process_email_for_ticket(email_data)
                            
                            if ticket_data:
                                self.latest_tickets.append(ticket_data)
                                print(f"✅ Processed: {ticket_data['ticket_id']}")
                            
                            # Mark as read
                            mail.store(email_id, '+FLAGS', '\\Seen')
                            
                    except Exception as e:
                        print(f"❌ Error processing email {email_id}: {e}")
            
            mail.close()
            mail.logout()
            
            return self.latest_tickets
            
        except Exception as e:
            print(f"❌ Email reading error: {e}")
            return []
    
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
    
    def process_email_for_ticket(self, email_data):
        """Process email and create ticket data"""
        
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        
        # Check if it's a support request
        support_keywords = [
            'problem', 'issue', 'error', 'fail', 'not working', 'down', 'outage',
            'authentication', 'aadhaar', 'service', 'unable', 'cannot', 'help',
            'support', 'urgent', 'critical', 'broken', 'bug', 'complaint'
        ]
        
        is_support = any(keyword in subject or keyword in body for keyword in support_keywords)
        
        if not is_support:
            return None
        
        # Analyze email content
        analysis = self.analyze_email_content(subject, body, email_data['from'])
        
        # Generate ticket ID
        now = datetime.now()
        date_str = now.strftime('%y%m%d')
        ticket_id = f"{analysis['department']}-{analysis['priority']}-{date_str}-{now.strftime('%H%M')}"
        
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
            'sla_deadline': self.calculate_sla_deadline(analysis['priority']),
            'breach_probability': self.calculate_breach_probability(analysis),
            'revenue_impact': self.calculate_revenue_impact(analysis),
            'confidence_score': 0.85
        }
        
        return ticket_data
    
    def analyze_email_content(self, subject, body, sender):
        """Analyze email content to extract ticket information"""
        
        text = subject + ' ' + body
        
        # Determine priority
        priority = 'P3'  # Default medium
        if any(word in text for word in ['critical', 'urgent', 'emergency', 'outage', 'down']):
            priority = 'P1'
        elif any(word in text for word in ['important', 'asap', 'priority', 'high']):
            priority = 'P2'
        elif any(word in text for word in ['question', 'inquiry', 'request']):
            priority = 'P4'
        
        # Determine department
        department = 'MPOnline'  # Default
        if any(word in text for word in ['aadhaar', 'aadhar', 'authentication', 'biometric']):
            department = 'UIDAI'
        elif any(word in text for word in ['payment', 'transaction', 'money', 'bank']):
            department = 'MeiTY'
        elif any(word in text for word in ['portal', 'website', 'digital', 'online']):
            department = 'DigitalMP'
        elif any(word in text for word in ['certificate', 'document', 'service']):
            department = 'eDistrict'
        
        # Determine service type
        service_type = 'other'
        if any(word in text for word in ['aadhaar', 'authentication']):
            service_type = 'aadhaar-auth'
        elif any(word in text for word in ['payment', 'gateway']):
            service_type = 'payment-gateway'
        elif any(word in text for word in ['portal', 'website']):
            service_type = 'citizen-portal'
        elif any(word in text for word in ['mobile', 'app']):
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
            'indore', 'bhopal', 'visakhapatnam', 'patna', 'vadodara',
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
    
    def calculate_sla_deadline(self, priority):
        """Calculate SLA deadline based on priority"""
        
        from datetime import timedelta
        
        sla_hours = {
            'P1': 2,
            'P2': 8,
            'P3': 24,
            'P4': 72
        }.get(priority, 24)
        
        deadline = datetime.now() + timedelta(hours=sla_hours)
        return deadline.strftime('%I:%M %p')
    
    def calculate_breach_probability(self, analysis):
        """Calculate breach probability"""
        
        base_prob = {
            'P1': 0.85,
            'P2': 0.65,
            'P3': 0.45,
            'P4': 0.25
        }.get(analysis['priority'], 0.45)
        
        return base_prob
    
    def calculate_revenue_impact(self, analysis):
        """Calculate revenue impact"""
        
        base_impact = {
            'P1': 200000,
            'P2': 100000,
            'P3': 50000,
            'P4': 20000
        }.get(analysis['priority'], 50000)
        
        return base_impact
    
    def get_latest_tickets_json(self):
        """Get latest tickets as JSON for web interface"""
        
        return json.dumps(self.latest_tickets, indent=2)
    
    def start_monitoring(self):
        """Start continuous email monitoring"""
        
        def monitor():
            while True:
                try:
                    self.read_emails()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    print(f"❌ Monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        print("📧 Email monitoring started")

def main():
    """Main function to setup and test email reader"""
    
    try:
        reader = SimpleEmailReader()
        
        print("📧 SIMPLE EMAIL READER FOR TICKET CREATION")
        print("=" * 50)
        
        # Get email credentials
        email_address = input("📧 Enter your email address: ").strip()
        password = input("🔐 Enter your email password/app password: ").strip()
        
        if not email_address or not password:
            print("❌ Email and password are required")
            return
        
        # Setup reader
        reader.setup_email_reader(email_address, password)
        
        # Test reading emails
        print("\n🔍 Reading emails...")
        tickets = reader.read_emails()
        
        if tickets:
            print(f"\n✅ Found {len(tickets)} support emails:")
            for ticket in tickets:
                print(f"   🎫 {ticket['ticket_id']}")
                print(f"      From: {ticket['reporter_name']}")
                print(f"      Subject: {ticket['email_subject']}")
                print(f"      Priority: {ticket['priority']}")
                print(f"      Department: {ticket['department']}")
                print(f"      Location: {ticket['location']}")
                print()
        else:
            print("ℹ️  No support emails found")
        
        # Save tickets to JSON file for web interface
        with open('sla_guard/aws_deployment/latest_email_tickets.json', 'w') as f:
            f.write(reader.get_latest_tickets_json())
        
        print("💾 Tickets saved to latest_email_tickets.json")
        
        # Ask if user wants to start monitoring
        start_monitoring = input("\n🔄 Start continuous email monitoring? (y/n): ").strip().lower()
        
        if start_monitoring == 'y':
            reader.start_monitoring()
            print("📧 Email monitoring active. Press Ctrl+C to stop.")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped")
        
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    main()