#!/usr/bin/env python3
"""
Send Test Critical Alert
Sends a test critical alert to verify email delivery
"""

import boto3
import json
from datetime import datetime

def send_test_critical_alert(email_address, region='us-east-1'):
    """Send a test critical alert"""
    
    sns = boto3.client('sns', region_name=region)
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    print(f"🚨 Sending Test Critical Alert")
    print(f"   Email: {email_address}")
    print(f"   Region: {region}")
    print(f"   Account: {account_id}")
    
    # Find critical alerts topic
    topics = sns.list_topics()['Topics']
    critical_topic = None
    for topic in topics:
        if 'sla-critical-alerts' in topic['TopicArn']:
            critical_topic = topic['TopicArn']
            break
    
    if not critical_topic:
        print("❌ Critical alerts topic not found")
        return
    
    # Create test critical alert
    alert_data = {
        'alert_type': 'CRITICAL_TEST',
        'ticket_id': f'TEST-CRITICAL-{int(datetime.now().timestamp())}',
        'priority': 'P1',
        'department': 'UIDAI',
        'breach_probability': 0.95,
        'sentiment': 'negative',
        'urgency': 10,
        'original_text': 'TEST ALERT: Aadhaar authentication services are completely down across all regions - this is a critical test of the email alert system',
        'timestamp': datetime.now().isoformat(),
        'alert_level': 'critical',
        'escalation_needed': True,
        'recommended_actions': [
            'Immediate escalation to senior support team',
            'Activate emergency response protocol',
            'Notify UIDAI technical operations team',
            'Set up incident command center'
        ]
    }
    
    # Format alert message
    alert_message = f"""
🚨 CRITICAL SLA ALERT - IMMEDIATE ACTION REQUIRED

This is a TEST of the SLA Guard critical alert system.

Ticket ID: {alert_data['ticket_id']}
Priority: {alert_data['priority']}
Department: {alert_data['department']}
Breach Probability: {alert_data['breach_probability']:.1%}
Urgency: {alert_data['urgency']}/10

Issue Description:
{alert_data['original_text']}

Alert Details:
- Timestamp: {alert_data['timestamp']}
- Alert Level: {alert_data['alert_level']}
- Escalation Required: {alert_data['escalation_needed']}
- Sentiment: {alert_data['sentiment']}

Immediate Actions Required:
• Assign senior engineer immediately
• Activate emergency response protocol  
• Notify UIDAI technical team
• Set up incident command center

AWS Console Links:
• SNS Topics: https://console.aws.amazon.com/sns/v3/home?region={region}#/topics
• CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region={region}#alarmsV2:
• SES Email: https://console.aws.amazon.com/ses/home?region={region}#/identities

This is a TEST alert. No actual emergency exists.
    """
    
    try:
        # Send the alert
        response = sns.publish(
            TopicArn=critical_topic,
            Message=alert_message,
            Subject=f'🚨 TEST CRITICAL SLA ALERT - {alert_data["ticket_id"]}'
        )
        
        print(f"✅ Test critical alert sent!")
        print(f"   Message ID: {response['MessageId']}")
        print(f"   Topic ARN: {critical_topic}")
        print(f"   Timestamp: {alert_data['timestamp']}")
        
        print(f"\n📧 Check your email ({email_address}) for the test alert!")
        print(f"   Subject: 🚨 TEST CRITICAL SLA ALERT - {alert_data['ticket_id']}")
        print(f"   If you don't receive it, check spam/junk folder")
        
        print(f"\n⚠️ Remember to confirm SNS subscriptions first:")
        print(f"   1. Check email for SNS confirmation messages")
        print(f"   2. Click 'Confirm subscription' in each email")
        print(f"   3. Then you'll receive this test alert")
        
        return response['MessageId']
        
    except Exception as e:
        print(f"❌ Failed to send test alert: {e}")
        return None

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("❌ Usage: python send_test_alert.py your-email@domain.com [region]")
        sys.exit(1)
    
    email = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-east-1'
    
    send_test_critical_alert(email, region)

if __name__ == "__main__":
    main()