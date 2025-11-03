import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')
stepfunctions = boto3.client('stepfunctions')
sns = boto3.client('sns')
ses = boto3.client('ses')

# Environment variables
SLA_STATE_TABLE = os.environ['SLA_STATE_TABLE']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']

def handler(event, context):
    """
    Trigger preventive actions based on SLA breach predictions
    Schedules priority reminders via EventBridge + Step Functions
    Sends notifications via SNS/SES
    """
    try:
        logger.info(f"Processing action trigger: {json.dumps(event)}")
        
        # Process EventBridge events
        if 'Records' in event:
            for record in event['Records']:
                process_action_record(record)
        else:
            # Direct invocation
            process_direct_action(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Actions triggered successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error triggering actions: {str(e)}")
        raise

def process_action_record(record: Dict[str, Any]):
    """Process individual action trigger record"""
    
    try:
        # Extract event data
        detail = record.get('detail', {})
        
        action_context = {
            'ticket_id': detail.get('ticket_id', ''),
            'breach_probability': detail.get('breach_probability', 0.0),
            'confidence': detail.get('confidence', 0.0),
            'time_to_breach': detail.get('time_to_breach', 60),
            'recommended_actions': detail.get('recommended_actions', []),
            'priority_boost': detail.get('priority_boost', False),
            'category': detail.get('category', 'general'),
            'current_priority': detail.get('current_priority', 3)
        }
        
        # Execute recommended actions
        execute_actions(action_context)
        
    except Exception as e:
        logger.error(f"Error processing action record: {e}")

def execute_actions(context: Dict[str, Any]):
    """Execute the recommended actions"""
    
    ticket_id = context['ticket_id']
    actions = context['recommended_actions']
    
    logger.info(f"Executing actions for ticket {ticket_id}: {actions}")
    
    # Execute each recommended action
    for action in actions:
        try:
            if action == 'escalate-immediately':
                escalate_ticket(context)
            elif action == 'notify-manager':
                notify_manager(context)
            elif action == 'boost-priority':
                boost_priority(context)
            elif action == 'assign-senior-tech':
                assign_senior_tech(context)
            elif action == 'send-reminder':
                send_reminder(context)
            elif action == 'schedule-followup':
                schedule_followup(context)
            elif action == 'trigger-incident-response':
                trigger_incident_response(context)
            elif action == 'dispatch-onsite-tech':
                dispatch_onsite_tech(context)
            elif action == 'engage-vendor-support':
                engage_vendor_support(context)
            elif action == 'auto-reset-password':
                auto_reset_password(context)
            elif action == 'check-spare-parts':
                check_spare_parts(context)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")

def escalate_ticket(context: Dict[str, Any]):
    """Escalate ticket to higher priority queue"""
    
    # Start Step Functions workflow for escalation
    workflow_input = {
        'ticket_id': context['ticket_id'],
        'escalation_reason': 'SLA_BREACH_RISK',
        'breach_probability': context['breach_probability'],
        'time_to_breach': context['time_to_breach'],
        'original_priority': context['current_priority'],
        'new_priority': max(1, context['current_priority'] - 1)
    }
    
    try:
        stepfunctions.start_execution(
            stateMachineArn=get_escalation_workflow_arn(),
            name=f"escalation-{context['ticket_id']}-{int(datetime.utcnow().timestamp())}",
            input=json.dumps(workflow_input)
        )
        logger.info(f"Started escalation workflow for ticket {context['ticket_id']}")
    except Exception as e:
        logger.error(f"Error starting escalation workflow: {e}")

def notify_manager(context: Dict[str, Any]):
    """Send notification to manager about potential SLA breach"""
    
    subject = f"🚨 SLA Breach Risk Alert - Ticket {context['ticket_id']}"
    
    message = f"""
    URGENT: SLA Breach Risk Detected
    
    Ticket ID: {context['ticket_id']}
    Category: {context['category']}
    Current Priority: P{context['current_priority']}
    Breach Probability: {context['breach_probability']:.1%}
    Time to Breach: {context['time_to_breach']} minutes
    
    Recommended Actions:
    {chr(10).join(f"• {action.replace('-', ' ').title()}" for action in context['recommended_actions'])}
    
    Please review and take immediate action if necessary.
    
    Dashboard: https://quicksight.aws.amazon.com/sla-dashboard
    """
    
    # Send via SNS for immediate alerts
    send_sns_notification(subject, message, 'manager-alerts')
    
    # Send via SES for detailed email
    send_email_notification(
        to_addresses=['manager@company.com'],  # Configure actual addresses
        subject=subject,
        body=message
    )

def boost_priority(context: Dict[str, Any]):
    """Boost ticket priority"""
    
    new_priority = max(1, context['current_priority'] - 1)
    
    # Update ticket priority in ITSM system (simulated via EventBridge)
    priority_update_event = {
        'ticket_id': context['ticket_id'],
        'old_priority': context['current_priority'],
        'new_priority': new_priority,
        'reason': 'SLA_BREACH_RISK',
        'breach_probability': context['breach_probability'],
        'updated_by': 'sla-guard-agent',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Priority Boost',
                    'Detail': json.dumps(priority_update_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Boosted priority for ticket {context['ticket_id']} from P{context['current_priority']} to P{new_priority}")
    except Exception as e:
        logger.error(f"Error boosting priority: {e}")

def assign_senior_tech(context: Dict[str, Any]):
    """Assign ticket to senior technician"""
    
    assignment_event = {
        'ticket_id': context['ticket_id'],
        'assignment_type': 'SENIOR_TECH',
        'reason': 'SLA_BREACH_RISK',
        'breach_probability': context['breach_probability'],
        'category': context['category'],
        'urgency': 'HIGH' if context['breach_probability'] >= 0.8 else 'MEDIUM',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Senior Tech Assignment',
                    'Detail': json.dumps(assignment_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Assigned senior tech to ticket {context['ticket_id']}")
    except Exception as e:
        logger.error(f"Error assigning senior tech: {e}")

def send_reminder(context: Dict[str, Any]):
    """Send reminder to assigned technician"""
    
    subject = f"⏰ SLA Reminder - Ticket {context['ticket_id']}"
    
    message = f"""
    SLA Reminder for Ticket {context['ticket_id']}
    
    Category: {context['category']}
    Priority: P{context['current_priority']}
    Time to Breach: {context['time_to_breach']} minutes
    Breach Risk: {context['breach_probability']:.1%}
    
    Please prioritize this ticket to avoid SLA breach.
    
    View Ticket: https://itsm.company.com/ticket/{context['ticket_id']}
    """
    
    # Send to technician queue
    send_sns_notification(subject, message, 'technician-reminders')

def schedule_followup(context: Dict[str, Any]):
    """Schedule follow-up reminder using EventBridge Scheduler"""
    
    # Calculate follow-up time (half of remaining time)
    followup_minutes = max(5, context['time_to_breach'] // 2)
    followup_time = datetime.utcnow() + timedelta(minutes=followup_minutes)
    
    followup_event = {
        'ticket_id': context['ticket_id'],
        'followup_type': 'SLA_CHECK',
        'original_breach_probability': context['breach_probability'],
        'scheduled_at': datetime.utcnow().isoformat(),
        'followup_time': followup_time.isoformat()
    }
    
    # Schedule via EventBridge (in production, use EventBridge Scheduler)
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Followup Scheduled',
                    'Detail': json.dumps(followup_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Scheduled follow-up for ticket {context['ticket_id']} in {followup_minutes} minutes")
    except Exception as e:
        logger.error(f"Error scheduling follow-up: {e}")

def trigger_incident_response(context: Dict[str, Any]):
    """Trigger incident response for critical infrastructure issues"""
    
    incident_event = {
        'ticket_id': context['ticket_id'],
        'incident_type': 'SLA_BREACH_IMMINENT',
        'category': context['category'],
        'breach_probability': context['breach_probability'],
        'time_to_breach': context['time_to_breach'],
        'severity': 'CRITICAL' if context['breach_probability'] >= 0.9 else 'HIGH',
        'triggered_by': 'sla-guard-agent',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        # Start incident response workflow
        stepfunctions.start_execution(
            stateMachineArn=get_incident_response_workflow_arn(),
            name=f"incident-{context['ticket_id']}-{int(datetime.utcnow().timestamp())}",
            input=json.dumps(incident_event)
        )
        
        # Send critical alert
        send_sns_notification(
            f"🚨 CRITICAL: Incident Response Triggered - {context['ticket_id']}",
            f"Infrastructure incident response triggered for ticket {context['ticket_id']} due to imminent SLA breach ({context['breach_probability']:.1%} probability)",
            'incident-response'
        )
        
        logger.info(f"Triggered incident response for ticket {context['ticket_id']}")
    except Exception as e:
        logger.error(f"Error triggering incident response: {e}")

def dispatch_onsite_tech(context: Dict[str, Any]):
    """Dispatch onsite technician for hardware issues"""
    
    dispatch_event = {
        'ticket_id': context['ticket_id'],
        'dispatch_type': 'ONSITE_HARDWARE',
        'category': context['category'],
        'urgency': 'HIGH',
        'breach_probability': context['breach_probability'],
        'estimated_arrival': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Onsite Tech Dispatch',
                    'Detail': json.dumps(dispatch_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Dispatched onsite tech for ticket {context['ticket_id']}")
    except Exception as e:
        logger.error(f"Error dispatching onsite tech: {e}")

def engage_vendor_support(context: Dict[str, Any]):
    """Engage vendor support for software issues"""
    
    vendor_event = {
        'ticket_id': context['ticket_id'],
        'engagement_type': 'VENDOR_ESCALATION',
        'category': context['category'],
        'breach_probability': context['breach_probability'],
        'priority': 'HIGH',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Vendor Support Engagement',
                    'Detail': json.dumps(vendor_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Engaged vendor support for ticket {context['ticket_id']}")
    except Exception as e:
        logger.error(f"Error engaging vendor support: {e}")

def auto_reset_password(context: Dict[str, Any]):
    """Trigger automated password reset for access issues"""
    
    # This would integrate with L1 automation agent
    reset_event = {
        'ticket_id': context['ticket_id'],
        'automation_type': 'PASSWORD_RESET',
        'category': context['category'],
        'triggered_by': 'sla-guard',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'L1 Automation Trigger',
                    'Detail': json.dumps(reset_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Triggered auto password reset for ticket {context['ticket_id']}")
    except Exception as e:
        logger.error(f"Error triggering auto password reset: {e}")

def check_spare_parts(context: Dict[str, Any]):
    """Check spare parts availability for hardware issues"""
    
    parts_check_event = {
        'ticket_id': context['ticket_id'],
        'check_type': 'SPARE_PARTS_AVAILABILITY',
        'category': context['category'],
        'urgency': 'HIGH',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Spare Parts Check',
                    'Detail': json.dumps(parts_check_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Initiated spare parts check for ticket {context['ticket_id']}")
    except Exception as e:
        logger.error(f"Error checking spare parts: {e}")

def send_sns_notification(subject: str, message: str, topic_suffix: str):
    """Send SNS notification"""
    
    topic_arn = f"arn:aws:sns:{os.environ.get('AWS_REGION', 'us-east-1')}:{os.environ.get('AWS_ACCOUNT_ID', '123456789012')}:sla-guard-{topic_suffix}"
    
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        logger.info(f"Sent SNS notification to {topic_suffix}")
    except Exception as e:
        logger.warning(f"Could not send SNS notification: {e}")

def send_email_notification(to_addresses: List[str], subject: str, body: str):
    """Send email notification via SES"""
    
    try:
        ses.send_email(
            Source='noreply@company.com',  # Configure actual sender
            Destination={'ToAddresses': to_addresses},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        logger.info(f"Sent email notification to {to_addresses}")
    except Exception as e:
        logger.warning(f"Could not send email notification: {e}")

def get_escalation_workflow_arn() -> str:
    """Get escalation Step Functions workflow ARN"""
    return f"arn:aws:states:{os.environ.get('AWS_REGION', 'us-east-1')}:{os.environ.get('AWS_ACCOUNT_ID', '123456789012')}:stateMachine:sla-escalation-workflow"

def get_incident_response_workflow_arn() -> str:
    """Get incident response Step Functions workflow ARN"""
    return f"arn:aws:states:{os.environ.get('AWS_REGION', 'us-east-1')}:{os.environ.get('AWS_ACCOUNT_ID', '123456789012')}:stateMachine:incident-response-workflow"

def process_direct_action(event: Dict[str, Any]):
    """Process direct action trigger"""
    
    context = {
        'ticket_id': event.get('ticket_id', 'DIRECT-001'),
        'breach_probability': event.get('breach_probability', 0.8),
        'confidence': event.get('confidence', 0.9),
        'time_to_breach': event.get('time_to_breach', 30),
        'recommended_actions': event.get('recommended_actions', ['escalate-immediately']),
        'priority_boost': event.get('priority_boost', True),
        'category': event.get('category', 'general'),
        'current_priority': event.get('current_priority', 3)
    }
    
    execute_actions(context)