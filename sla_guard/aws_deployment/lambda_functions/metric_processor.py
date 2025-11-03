import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')
s3_client = boto3.client('s3')

# Environment variables
SLA_STATE_TABLE = os.environ['SLA_STATE_TABLE']
SHARED_CONFIG_TABLE = os.environ['SHARED_CONFIG_TABLE']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']
DATA_LAKE_BUCKET = os.environ['DATA_LAKE_BUCKET']

def handler(event, context):
    """
    Process incoming helpdesk tickets and metrics for SLA monitoring
    Simulates ticket ingestion from DynamoDB or JSON sources
    """
    try:
        logger.info(f"Processing SLA metrics: {json.dumps(event)}")
        
        # Get SLA configuration
        sla_config = get_sla_configuration()
        
        # Process different event sources
        if 'Records' in event:
            # DynamoDB stream or SQS messages
            for record in event['Records']:
                process_ticket_record(record, sla_config)
        else:
            # Direct invocation or scheduled processing
            process_scheduled_metrics(sla_config)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'SLA metrics processed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing SLA metrics: {str(e)}")
        raise

def get_sla_configuration() -> Dict[str, Any]:
    """Get SLA configuration from shared config table"""
    table = dynamodb.Table(SHARED_CONFIG_TABLE)
    
    try:
        response = table.get_item(Key={'config_key': 'sla_thresholds'})
        if 'Item' in response:
            return response['Item']['config_value']
    except Exception as e:
        logger.warning(f"Could not load SLA config: {e}")
    
    # Default SLA configuration
    return {
        'priority_1': {'response_time': 15, 'resolution_time': 240},  # 15min response, 4h resolution
        'priority_2': {'response_time': 60, 'resolution_time': 480},  # 1h response, 8h resolution
        'priority_3': {'response_time': 240, 'resolution_time': 1440}, # 4h response, 24h resolution
        'priority_4': {'response_time': 480, 'resolution_time': 2880}, # 8h response, 48h resolution
        'target_adherence': 0.95  # 95% SLA adherence target
    }

def process_ticket_record(record: Dict[str, Any], sla_config: Dict[str, Any]):
    """Process individual ticket record for SLA tracking"""
    
    # Extract ticket data based on source
    if record.get('eventSource') == 'aws:dynamodb':
        ticket_data = extract_dynamodb_ticket(record)
    else:
        ticket_data = extract_json_ticket(record)
    
    if not ticket_data:
        return
    
    # Calculate SLA metrics
    sla_metrics = calculate_sla_metrics(ticket_data, sla_config)
    
    # Store in SLA state table
    store_sla_state(ticket_data, sla_metrics)
    
    # Publish metric update event
    publish_metric_event(ticket_data, sla_metrics)
    
    # Store raw data in S3 data lake
    store_raw_data(ticket_data, sla_metrics)

def extract_dynamodb_ticket(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract ticket data from DynamoDB stream record"""
    try:
        if record['eventName'] in ['INSERT', 'MODIFY']:
            image = record['dynamodb'].get('NewImage', {})
            return {
                'ticket_id': image.get('ticket_id', {}).get('S', ''),
                'title': image.get('title', {}).get('S', ''),
                'description': image.get('description', {}).get('S', ''),
                'priority': int(image.get('priority', {}).get('N', '3')),
                'status': image.get('status', {}).get('S', 'open'),
                'created_at': image.get('created_at', {}).get('S', ''),
                'updated_at': image.get('updated_at', {}).get('S', ''),
                'assigned_to': image.get('assigned_to', {}).get('S', ''),
                'category': image.get('category', {}).get('S', 'general')
            }
    except Exception as e:
        logger.error(f"Error extracting DynamoDB ticket: {e}")
    return None

def extract_json_ticket(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract ticket data from JSON record"""
    try:
        # Handle SQS message body
        if 'body' in record:
            body = json.loads(record['body'])
            return body.get('ticket', body)
        
        # Direct JSON ticket data
        return record.get('ticket', record)
    except Exception as e:
        logger.error(f"Error extracting JSON ticket: {e}")
    return None

def calculate_sla_metrics(ticket_data: Dict[str, Any], sla_config: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate SLA metrics for a ticket"""
    
    priority = ticket_data.get('priority', 3)
    priority_key = f'priority_{priority}'
    
    if priority_key not in sla_config:
        priority_key = 'priority_3'  # Default to P3
    
    thresholds = sla_config[priority_key]
    created_at = datetime.fromisoformat(ticket_data.get('created_at', datetime.utcnow().isoformat()))
    current_time = datetime.utcnow()
    
    # Calculate time elapsed
    elapsed_minutes = (current_time - created_at).total_seconds() / 60
    
    # Response SLA (convert Decimal to float if needed)
    response_threshold = float(thresholds['response_time'])
    response_remaining = max(0, response_threshold - elapsed_minutes)
    response_breach_risk = min(1.0, elapsed_minutes / response_threshold)
    
    # Resolution SLA (convert Decimal to float if needed)
    resolution_threshold = float(thresholds['resolution_time'])
    resolution_remaining = max(0, resolution_threshold - elapsed_minutes)
    resolution_breach_risk = min(1.0, elapsed_minutes / resolution_threshold)
    
    # Overall breach probability (weighted average)
    if ticket_data.get('status') in ['resolved', 'closed']:
        breach_probability = 0.0  # Already resolved
    else:
        # Weight response more heavily for new tickets
        response_weight = 0.7 if ticket_data.get('status') == 'open' else 0.3
        resolution_weight = 1.0 - response_weight
        breach_probability = (response_breach_risk * response_weight + 
                            resolution_breach_risk * resolution_weight)
    
    return {
        'response_threshold_minutes': response_threshold,
        'resolution_threshold_minutes': resolution_threshold,
        'elapsed_minutes': elapsed_minutes,
        'response_remaining_minutes': response_remaining,
        'resolution_remaining_minutes': resolution_remaining,
        'response_breach_risk': response_breach_risk,
        'resolution_breach_risk': resolution_breach_risk,
        'breach_probability': breach_probability,
        'breach_probability_bucket': get_breach_bucket(breach_probability),
        'sla_status': get_sla_status(breach_probability),
        'calculated_at': current_time.isoformat()
    }

def get_breach_bucket(probability: float) -> str:
    """Categorize breach probability for indexing"""
    if probability >= 0.9:
        return 'critical'
    elif probability >= 0.7:
        return 'high'
    elif probability >= 0.5:
        return 'medium'
    elif probability >= 0.3:
        return 'low'
    else:
        return 'minimal'

def get_sla_status(probability: float) -> str:
    """Get human-readable SLA status"""
    if probability >= 0.9:
        return 'BREACH_IMMINENT'
    elif probability >= 0.7:
        return 'AT_RISK'
    elif probability >= 0.5:
        return 'WATCH'
    else:
        return 'HEALTHY'

def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    else:
        return obj

def store_sla_state(ticket_data: Dict[str, Any], sla_metrics: Dict[str, Any]):
    """Store SLA state in DynamoDB"""
    table = dynamodb.Table(SLA_STATE_TABLE)
    
    timestamp = int(datetime.utcnow().timestamp() * 1000)  # Milliseconds
    
    # Convert floats to Decimal for DynamoDB
    sla_metrics_decimal = convert_floats_to_decimal(sla_metrics)
    
    item = {
        'service_id': ticket_data['ticket_id'],
        'timestamp': timestamp,
        'ticket_data': ticket_data,
        'sla_metrics': sla_metrics_decimal,
        'breach_probability_bucket': sla_metrics['breach_probability_bucket'],
        'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())  # 90-day retention
    }
    
    try:
        table.put_item(Item=item)
        logger.info(f"Stored SLA state for ticket {ticket_data['ticket_id']}")
    except Exception as e:
        logger.error(f"Error storing SLA state: {e}")

def publish_metric_event(ticket_data: Dict[str, Any], sla_metrics: Dict[str, Any]):
    """Publish metric update event to EventBridge"""
    
    event_detail = {
        'ticket_id': ticket_data['ticket_id'],
        'priority': ticket_data.get('priority', 3),
        'status': ticket_data.get('status', 'open'),
        'breach_probability': sla_metrics['breach_probability'],
        'sla_status': sla_metrics['sla_status'],
        'response_remaining_minutes': sla_metrics['response_remaining_minutes'],
        'resolution_remaining_minutes': sla_metrics['resolution_remaining_minutes'],
        'category': ticket_data.get('category', 'general'),
        'timestamp': sla_metrics['calculated_at']
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Metric Update',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Published metric event for ticket {ticket_data['ticket_id']}")
    except Exception as e:
        logger.error(f"Error publishing metric event: {e}")

def store_raw_data(ticket_data: Dict[str, Any], sla_metrics: Dict[str, Any]):
    """Store raw data in S3 data lake for analytics"""
    
    now = datetime.utcnow()
    s3_key = f"raw/sla-metrics/year={now.year}/month={now.month:02d}/day={now.day:02d}/{ticket_data['ticket_id']}_{int(now.timestamp())}.json"
    
    data = {
        'ticket_data': ticket_data,
        'sla_metrics': sla_metrics,
        'ingestion_timestamp': now.isoformat()
    }
    
    try:
        s3_client.put_object(
            Bucket=DATA_LAKE_BUCKET,
            Key=s3_key,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        logger.info(f"Stored raw data to S3: {s3_key}")
    except Exception as e:
        logger.error(f"Error storing raw data to S3: {e}")

def process_scheduled_metrics(sla_config: Dict[str, Any]):
    """Process scheduled metric updates for all active tickets"""
    
    # This would typically query your ticket system
    # For demo purposes, we'll simulate some tickets
    sample_tickets = generate_sample_tickets()
    
    for ticket in sample_tickets:
        sla_metrics = calculate_sla_metrics(ticket, sla_config)
        store_sla_state(ticket, sla_metrics)
        publish_metric_event(ticket, sla_metrics)
        store_raw_data(ticket, sla_metrics)

def generate_sample_tickets() -> List[Dict[str, Any]]:
    """Generate sample tickets for demonstration"""
    
    base_time = datetime.utcnow()
    
    return [
        {
            'ticket_id': 'INC-001',
            'title': '3rd floor Marketing printer stuck — jobs queueing',
            'description': 'Print jobs are backing up in the queue, printer shows error',
            'priority': 3,
            'status': 'open',
            'created_at': (base_time - timedelta(minutes=45)).isoformat(),
            'updated_at': base_time.isoformat(),
            'assigned_to': 'tech-team',
            'category': 'hardware'
        },
        {
            'ticket_id': 'INC-002',
            'title': 'Email server performance degradation',
            'description': 'Users reporting slow email delivery and timeouts',
            'priority': 1,
            'status': 'in_progress',
            'created_at': (base_time - timedelta(minutes=10)).isoformat(),
            'updated_at': base_time.isoformat(),
            'assigned_to': 'senior-admin',
            'category': 'infrastructure'
        },
        {
            'ticket_id': 'INC-003',
            'title': 'Password reset request',
            'description': 'User unable to access account after password expiry',
            'priority': 4,
            'status': 'open',
            'created_at': (base_time - timedelta(hours=2)).isoformat(),
            'updated_at': base_time.isoformat(),
            'assigned_to': 'helpdesk',
            'category': 'access'
        }
    ]