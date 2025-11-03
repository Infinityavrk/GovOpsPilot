import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
# import numpy as np  # Not needed for basic predictions

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')
sagemaker_runtime = boto3.client('sagemaker-runtime')

# Environment variables
SLA_STATE_TABLE = os.environ['SLA_STATE_TABLE']
SHARED_CONFIG_TABLE = os.environ['SHARED_CONFIG_TABLE']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT', 'sla-predictor-endpoint')

def handler(event, context):
    """
    ML-powered SLA breach prediction using Amazon SageMaker
    Processes metric updates and predicts breach probability
    """
    try:
        logger.info(f"Processing breach prediction: {json.dumps(event)}")
        
        # Process different event sources
        if 'Records' in event:
            # DynamoDB stream or EventBridge events
            for record in event['Records']:
                process_prediction_record(record)
        else:
            # Direct invocation
            prediction_result = process_direct_prediction(event)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Breach prediction completed successfully',
                    'prediction': prediction_result,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Breach prediction completed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in breach prediction: {str(e)}")
        raise

def process_prediction_record(record: Dict[str, Any]):
    """Process individual record for breach prediction"""
    
    try:
        # Extract event data
        if record.get('eventSource') == 'aws:dynamodb':
            event_data = extract_dynamodb_event(record)
        else:
            event_data = extract_eventbridge_event(record)
        
        if not event_data:
            return
        
        # Get enhanced features for ML prediction
        features = extract_ml_features(event_data)
        
        # Get ML prediction from SageMaker
        ml_prediction = get_sagemaker_prediction(features)
        
        # Combine rule-based and ML predictions
        final_prediction = combine_predictions(event_data, ml_prediction)
        
        # Check if action is needed
        if should_trigger_action(final_prediction):
            trigger_preventive_action(event_data, final_prediction)
        
        # Update SLA state with prediction
        update_sla_prediction(event_data, final_prediction)
        
    except Exception as e:
        logger.error(f"Error processing prediction record: {e}")

def extract_dynamodb_event(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract event data from DynamoDB stream"""
    try:
        if record['eventName'] in ['INSERT', 'MODIFY']:
            image = record['dynamodb'].get('NewImage', {})
            
            # Extract ticket and SLA data
            ticket_data = image.get('ticket_data', {}).get('M', {})
            sla_metrics = image.get('sla_metrics', {}).get('M', {})
            
            return {
                'ticket_id': ticket_data.get('ticket_id', {}).get('S', ''),
                'priority': int(ticket_data.get('priority', {}).get('N', '3')),
                'status': ticket_data.get('status', {}).get('S', 'open'),
                'category': ticket_data.get('category', {}).get('S', 'general'),
                'created_at': ticket_data.get('created_at', {}).get('S', ''),
                'breach_probability': float(sla_metrics.get('breach_probability', {}).get('N', '0')),
                'elapsed_minutes': float(sla_metrics.get('elapsed_minutes', {}).get('N', '0')),
                'response_remaining_minutes': float(sla_metrics.get('response_remaining_minutes', {}).get('N', '0')),
                'resolution_remaining_minutes': float(sla_metrics.get('resolution_remaining_minutes', {}).get('N', '0'))
            }
    except Exception as e:
        logger.error(f"Error extracting DynamoDB event: {e}")
    return None

def extract_eventbridge_event(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract event data from EventBridge"""
    try:
        detail = record.get('detail', {})
        return {
            'ticket_id': detail.get('ticket_id', ''),
            'priority': detail.get('priority', 3),
            'status': detail.get('status', 'open'),
            'category': detail.get('category', 'general'),
            'breach_probability': detail.get('breach_probability', 0.0),
            'response_remaining_minutes': detail.get('response_remaining_minutes', 0),
            'resolution_remaining_minutes': detail.get('resolution_remaining_minutes', 0)
        }
    except Exception as e:
        logger.error(f"Error extracting EventBridge event: {e}")
    return None

def extract_ml_features(event_data: Dict[str, Any]) -> List[float]:
    """Extract features for ML model prediction"""
    
    # Get historical data for this ticket category
    historical_stats = get_historical_stats(event_data['category'])
    
    # Get current system load
    system_load = get_current_system_load()
    
    # Feature engineering
    features = [
        # Basic ticket features
        float(event_data.get('priority', 3)),
        1.0 if event_data.get('status') == 'open' else 0.0,
        1.0 if event_data.get('status') == 'in_progress' else 0.0,
        
        # Time-based features
        float(event_data.get('response_remaining_minutes', 0)),
        float(event_data.get('resolution_remaining_minutes', 0)),
        
        # Category encoding (one-hot for major categories)
        1.0 if event_data.get('category') == 'hardware' else 0.0,
        1.0 if event_data.get('category') == 'software' else 0.0,
        1.0 if event_data.get('category') == 'infrastructure' else 0.0,
        1.0 if event_data.get('category') == 'access' else 0.0,
        
        # Historical features
        historical_stats.get('avg_resolution_time', 480.0),
        historical_stats.get('breach_rate', 0.1),
        historical_stats.get('escalation_rate', 0.2),
        
        # System load features
        system_load.get('active_tickets', 10.0),
        system_load.get('technician_utilization', 0.7),
        system_load.get('avg_response_time', 30.0)
    ]
    
    return features

def get_historical_stats(category: str) -> Dict[str, float]:
    """Get historical statistics for ticket category"""
    
    # In production, this would query historical data
    # For demo, return category-based estimates
    category_stats = {
        'hardware': {
            'avg_resolution_time': 240.0,  # 4 hours
            'breach_rate': 0.15,
            'escalation_rate': 0.25
        },
        'software': {
            'avg_resolution_time': 180.0,  # 3 hours
            'breach_rate': 0.12,
            'escalation_rate': 0.20
        },
        'infrastructure': {
            'avg_resolution_time': 120.0,  # 2 hours
            'breach_rate': 0.08,
            'escalation_rate': 0.30
        },
        'access': {
            'avg_resolution_time': 60.0,   # 1 hour
            'breach_rate': 0.05,
            'escalation_rate': 0.10
        }
    }
    
    return category_stats.get(category, category_stats['hardware'])

def get_current_system_load() -> Dict[str, float]:
    """Get current system load metrics"""
    
    # Query current system state
    table = dynamodb.Table(SLA_STATE_TABLE)
    
    try:
        # Get active tickets count
        response = table.scan(
            FilterExpression='attribute_exists(ticket_data) AND ticket_data.#status IN (:open, :progress)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':open': 'open', ':progress': 'in_progress'},
            Select='COUNT'
        )
        
        active_tickets = response.get('Count', 10)
        
        # Estimate technician utilization based on active tickets
        technician_utilization = min(1.0, active_tickets / 20.0)  # Assume 20 tickets = 100% utilization
        
        # Estimate average response time based on load
        avg_response_time = 15.0 + (technician_utilization * 45.0)  # 15-60 minutes
        
        return {
            'active_tickets': float(active_tickets),
            'technician_utilization': technician_utilization,
            'avg_response_time': avg_response_time
        }
        
    except Exception as e:
        logger.warning(f"Could not get system load: {e}")
        return {
            'active_tickets': 10.0,
            'technician_utilization': 0.7,
            'avg_response_time': 30.0
        }

def get_sagemaker_prediction(features: List[float]) -> Dict[str, Any]:
    """Get prediction from SageMaker endpoint"""
    
    try:
        # Prepare input for SageMaker
        input_data = ','.join(map(str, features))
        
        # Invoke SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType='text/csv',
            Body=input_data
        )
        
        # Parse response
        result = json.loads(response['Body'].read().decode())
        
        # Extract prediction (assuming binary classification for breach/no-breach)
        if isinstance(result, list):
            breach_probability = float(result[0])
        else:
            breach_probability = float(result.get('predictions', [0.5])[0])
        
        return {
            'ml_breach_probability': breach_probability,
            'confidence': 0.85,  # Model confidence
            'model_version': 'v1.0'
        }
        
    except Exception as e:
        logger.warning(f"SageMaker prediction failed, using fallback: {e}")
        
        # Fallback: simple heuristic based on time remaining
        response_remaining = features[3]  # response_remaining_minutes
        resolution_remaining = features[4]  # resolution_remaining_minutes
        
        # Simple rule: higher probability as time runs out
        if response_remaining <= 5:
            breach_prob = 0.9
        elif response_remaining <= 15:
            breach_prob = 0.7
        elif resolution_remaining <= 60:
            breach_prob = 0.6
        else:
            breach_prob = 0.3
        
        return {
            'ml_breach_probability': breach_prob,
            'confidence': 0.6,
            'model_version': 'fallback'
        }

def combine_predictions(event_data: Dict[str, Any], ml_prediction: Dict[str, Any]) -> Dict[str, Any]:
    """Combine rule-based and ML predictions"""
    
    rule_based_prob = event_data.get('breach_probability', 0.0)
    ml_prob = ml_prediction.get('ml_breach_probability', 0.0)
    ml_confidence = ml_prediction.get('confidence', 0.5)
    
    # Weighted combination based on ML confidence
    final_probability = (rule_based_prob * (1 - ml_confidence) + 
                        ml_prob * ml_confidence)
    
    # Determine recommended actions
    recommended_actions = get_recommended_actions(event_data, final_probability)
    
    return {
        'ticket_id': event_data['ticket_id'],
        'rule_based_probability': rule_based_prob,
        'ml_probability': ml_prob,
        'final_breach_probability': final_probability,
        'confidence': ml_confidence,
        'model_version': ml_prediction.get('model_version', 'unknown'),
        'recommended_actions': recommended_actions,
        'priority_boost': should_boost_priority(final_probability),
        'time_to_breach_minutes': estimate_time_to_breach(event_data, final_probability),
        'prediction_timestamp': datetime.utcnow().isoformat()
    }

def get_recommended_actions(event_data: Dict[str, Any], breach_probability: float) -> List[str]:
    """Get recommended actions based on breach probability"""
    
    actions = []
    category = event_data.get('category', 'general')
    priority = event_data.get('priority', 3)
    
    if breach_probability >= 0.9:
        actions.extend(['escalate-immediately', 'notify-manager'])
        if category == 'infrastructure':
            actions.append('trigger-incident-response')
    
    if breach_probability >= 0.7:
        actions.extend(['boost-priority', 'assign-senior-tech'])
        if category == 'hardware':
            actions.append('dispatch-onsite-tech')
        elif category == 'software':
            actions.append('engage-vendor-support')
    
    if breach_probability >= 0.5:
        actions.extend(['send-reminder', 'check-dependencies'])
        if priority <= 2:
            actions.append('prepare-workaround')
    
    # Category-specific actions
    if category == 'hardware' and breach_probability >= 0.6:
        actions.append('check-spare-parts')
    elif category == 'access' and breach_probability >= 0.4:
        actions.append('auto-reset-password')
    
    return list(set(actions))  # Remove duplicates

def should_boost_priority(breach_probability: float) -> bool:
    """Determine if ticket priority should be boosted"""
    return breach_probability >= 0.7

def estimate_time_to_breach(event_data: Dict[str, Any], breach_probability: float) -> int:
    """Estimate minutes until SLA breach"""
    
    response_remaining = event_data.get('response_remaining_minutes', 0)
    resolution_remaining = event_data.get('resolution_remaining_minutes', 0)
    
    # Use the shorter of the two timeframes
    min_remaining = min(response_remaining, resolution_remaining)
    
    # Adjust based on breach probability
    if breach_probability >= 0.9:
        return max(5, int(min_remaining * 0.1))  # Very soon
    elif breach_probability >= 0.7:
        return max(15, int(min_remaining * 0.3))
    elif breach_probability >= 0.5:
        return max(30, int(min_remaining * 0.5))
    else:
        return int(min_remaining)

def should_trigger_action(prediction: Dict[str, Any]) -> bool:
    """Determine if preventive action should be triggered"""
    return prediction['final_breach_probability'] >= 0.7

def trigger_preventive_action(event_data: Dict[str, Any], prediction: Dict[str, Any]):
    """Trigger preventive actions via EventBridge"""
    
    event_detail = {
        'ticket_id': prediction['ticket_id'],
        'breach_probability': prediction['final_breach_probability'],
        'confidence': prediction['confidence'],
        'time_to_breach': prediction['time_to_breach_minutes'],
        'recommended_actions': prediction['recommended_actions'],
        'priority_boost': prediction['priority_boost'],
        'category': event_data.get('category', 'general'),
        'current_priority': event_data.get('priority', 3),
        'prediction_timestamp': prediction['prediction_timestamp']
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'SLA Breach Prediction',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Triggered preventive action for ticket {prediction['ticket_id']}")
    except Exception as e:
        logger.error(f"Error triggering preventive action: {e}")

def update_sla_prediction(event_data: Dict[str, Any], prediction: Dict[str, Any]):
    """Update SLA state with ML prediction"""
    
    table = dynamodb.Table(SLA_STATE_TABLE)
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    
    try:
        table.update_item(
            Key={
                'service_id': prediction['ticket_id'],
                'timestamp': timestamp
            },
            UpdateExpression='SET ml_prediction = :pred, updated_at = :now',
            ExpressionAttributeValues={
                ':pred': prediction,
                ':now': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Updated SLA prediction for ticket {prediction['ticket_id']}")
    except Exception as e:
        logger.error(f"Error updating SLA prediction: {e}")

def process_direct_prediction(event: Dict[str, Any]):
    """Process direct prediction request"""
    
    # Extract ticket data from direct event
    event_data = {
        'ticket_id': event.get('ticket_id', 'DIRECT-001'),
        'priority': event.get('priority', 3),
        'status': event.get('status', 'open'),
        'category': event.get('category', 'general'),
        'breach_probability': event.get('breach_probability', 0.0),
        'response_remaining_minutes': event.get('response_remaining_minutes', 60),
        'resolution_remaining_minutes': event.get('resolution_remaining_minutes', 240)
    }
    
    # Process prediction
    features = extract_ml_features(event_data)
    ml_prediction = get_sagemaker_prediction(features)
    final_prediction = combine_predictions(event_data, ml_prediction)
    
    if should_trigger_action(final_prediction):
        trigger_preventive_action(event_data, final_prediction)
    
    update_sla_prediction(event_data, final_prediction)
    
    return final_prediction