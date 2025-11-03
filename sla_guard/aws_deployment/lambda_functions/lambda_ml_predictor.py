#!/usr/bin/env python3
"""
AWS Lambda Function for ML Prediction Pipeline
Triggered by EventBridge → Invokes SageMaker → Updates DynamoDB → Sends SNS Alerts

This Lambda function is triggered by EventBridge events when new tickets are created
and handles the ML prediction workflow using SageMaker.
"""

import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sagemaker = boto3.client('sagemaker-runtime')
sns = boto3.client('sns')

# Configuration
TICKETS_TABLE = 'sla-guard-tickets'
SAGEMAKER_ENDPOINT = 'sla-breach-predictor'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:508955320780:sla-alerts'

def lambda_handler(event, context):
    """
    Main Lambda handler for EventBridge ticket events
    """
    logger.info(f"🚀 Lambda ML Predictor triggered: {json.dumps(event)}")
    
    try:
        # Parse EventBridge event
        if 'Records' in event:
            # Handle SNS/SQS records
            for record in event['Records']:
                process_ticket_event(json.loads(record['body']))
        elif 'detail' in event:
            # Handle direct EventBridge event
            process_ticket_event(event['detail'])
        else:
            # Handle direct invocation
            process_ticket_event(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'ML prediction completed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def process_ticket_event(event_detail: Dict[str, Any]):
    """Process individual ticket event"""
    ticket_id = event_detail.get('ticket_id')
    if not ticket_id:
        logger.error("No ticket_id in event detail")
        return
    
    logger.info(f"🎫 Processing ticket: {ticket_id}")
    
    # Get ticket from DynamoDB
    ticket = get_ticket_from_dynamodb(ticket_id)
    if not ticket:
        logger.error(f"Ticket not found: {ticket_id}")
        return
    
    # Prepare ML features
    features = prepare_ml_features(ticket)
    
    # Get ML prediction
    prediction = get_ml_prediction(features)
    
    # Update ticket with prediction
    update_ticket_with_prediction(ticket_id, prediction)
    
    # Send alert if high risk
    if prediction['breach_probability'] > 0.7:
        send_high_risk_alert(ticket, prediction)
    
    logger.info(f"✅ Ticket processing completed: {ticket_id}")

def get_ticket_from_dynamodb(ticket_id: str) -> Dict[str, Any]:
    """Retrieve ticket from DynamoDB"""
    try:
        table = dynamodb.Table(TICKETS_TABLE)
        response = table.get_item(Key={'ticket_id': ticket_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error retrieving ticket {ticket_id}: {str(e)}")
        return None

def prepare_ml_features(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare features for SageMaker ML model"""
    
    # Priority scoring
    priority_scores = {'P1': 4, 'P2': 3, 'P3': 2, 'P4': 1}
    priority_score = priority_scores.get(ticket.get('priority', 'P3'), 2)
    
    # Sentiment scoring
    sentiment_scores = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
    sentiment_score = sentiment_scores.get(ticket.get('sentiment', 'NEUTRAL'), 0)
    
    # Department risk factors
    dept_risk = {
        'UIDAI': 0.8,      # High risk - critical authentication services
        'MeiTY': 0.6,     # Medium-high risk - payment systems
        'DigitalMP': 0.4,  # Medium risk - portal services
        'Other': 0.3       # Lower risk
    }
    department_risk = dept_risk.get(ticket.get('department', 'Other'), 0.3)
    
    # Time-based features
    now = datetime.now()
    hour_of_day = now.hour
    day_of_week = now.weekday()  # 0=Monday, 6=Sunday
    
    # Business hours factor (higher risk outside business hours)
    is_business_hours = 9 <= hour_of_day <= 17 and day_of_week < 5
    business_hours_factor = 0.8 if is_business_hours else 1.2
    
    features = {
        'priority_score': priority_score,
        'urgency': ticket.get('urgency', 5),
        'sentiment_score': sentiment_score,
        'department_risk': department_risk,
        'hour_of_day': hour_of_day,
        'day_of_week': day_of_week,
        'is_business_hours': 1 if is_business_hours else 0,
        'business_hours_factor': business_hours_factor,
        'estimated_hours': ticket.get('estimated_resolution_hours', 24),
        'bedrock_confidence': ticket.get('bedrock_confidence', 0.5),
        'comprehend_confidence': ticket.get('comprehend_confidence', 0.5)
    }
    
    logger.info(f"📊 ML Features prepared: {features}")
    return features

def get_ml_prediction(features: Dict[str, Any]) -> Dict[str, Any]:
    """Get breach probability prediction from SageMaker or fallback model"""
    
    try:
        # Try SageMaker endpoint first
        payload = json.dumps(features)
        
        response = sagemaker.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType='application/json',
            Body=payload
        )
        
        result = json.loads(response['Body'].read().decode())
        
        prediction = {
            'breach_probability': result.get('breach_probability', 0.5),
            'confidence': result.get('confidence', 0.8),
            'model_version': result.get('model_version', '1.0'),
            'prediction_timestamp': datetime.utcnow().isoformat(),
            'model_used': 'sagemaker'
        }
        
        logger.info(f"🧠 SageMaker prediction: {prediction['breach_probability']:.3f}")
        return prediction
        
    except Exception as e:
        logger.warning(f"SageMaker prediction failed: {str(e)}, using fallback model")
        return get_fallback_prediction(features)

def get_fallback_prediction(features: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback ML prediction when SageMaker is unavailable"""
    
    # Base risk from priority
    priority_risk = features['priority_score'] / 4.0  # 0.25 to 1.0
    
    # Urgency factor
    urgency_factor = features['urgency'] / 10.0  # 0.0 to 1.0
    
    # Department risk
    dept_risk = features['department_risk']  # 0.3 to 0.8
    
    # Time factor (higher risk outside business hours)
    time_factor = features['business_hours_factor']  # 0.8 or 1.2
    
    # Sentiment factor (negative sentiment increases risk)
    sentiment_factor = 1.0
    if features['sentiment_score'] == -1:  # Negative
        sentiment_factor = 1.3
    elif features['sentiment_score'] == 1:  # Positive
        sentiment_factor = 0.9
    
    # Estimated resolution time factor
    est_hours = features['estimated_hours']
    if est_hours <= 4:
        time_pressure_factor = 1.4  # Very tight deadline
    elif est_hours <= 12:
        time_pressure_factor = 1.2  # Tight deadline
    elif est_hours <= 24:
        time_pressure_factor = 1.0  # Normal deadline
    else:
        time_pressure_factor = 0.8  # Relaxed deadline
    
    # Calculate combined breach probability
    base_probability = (priority_risk * 0.3 + 
                       urgency_factor * 0.2 + 
                       dept_risk * 0.3)
    
    adjusted_probability = (base_probability * 
                          time_factor * 
                          sentiment_factor * 
                          time_pressure_factor)
    
    # Ensure probability is between 0 and 1
    breach_probability = min(max(adjusted_probability, 0.0), 1.0)
    
    # Confidence based on available data quality
    confidence = (features['bedrock_confidence'] + features['comprehend_confidence']) / 200.0
    confidence = min(max(confidence, 0.6), 0.9)  # Between 60% and 90%
    
    prediction = {
        'breach_probability': breach_probability,
        'confidence': confidence,
        'model_version': 'fallback_v1.0',
        'prediction_timestamp': datetime.utcnow().isoformat(),
        'model_used': 'fallback',
        'factors': {
            'priority_risk': priority_risk,
            'urgency_factor': urgency_factor,
            'dept_risk': dept_risk,
            'time_factor': time_factor,
            'sentiment_factor': sentiment_factor,
            'time_pressure_factor': time_pressure_factor
        }
    }
    
    logger.info(f"🔄 Fallback prediction: {breach_probability:.3f} (confidence: {confidence:.3f})")
    return prediction

def update_ticket_with_prediction(ticket_id: str, prediction: Dict[str, Any]):
    """Update DynamoDB ticket with ML prediction results"""
    try:
        table = dynamodb.Table(TICKETS_TABLE)
        
        # Calculate new SLA deadline based on breach probability
        hours_adjustment = prediction['breach_probability'] * 12  # Up to 12 hours sooner
        new_deadline = datetime.utcnow() + timedelta(hours=max(4, 24-hours_adjustment))
        
        update_expression = """
        SET breach_risk = :risk, 
            ml_prediction_status = :status, 
            ml_confidence = :conf, 
            prediction_timestamp = :ts,
            model_used = :model,
            adjusted_sla_deadline = :deadline,
            last_updated = :updated
        """
        
        expression_values = {
            ':risk': prediction['breach_probability'],
            ':status': 'COMPLETED',
            ':conf': prediction['confidence'],
            ':ts': prediction['prediction_timestamp'],
            ':model': prediction['model_used'],
            ':deadline': new_deadline.isoformat(),
            ':updated': datetime.utcnow().isoformat()
        }
        
        table.update_item(
            Key={'ticket_id': ticket_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        logger.info(f"📊 Ticket {ticket_id} updated with prediction: {prediction['breach_probability']:.3f}")
        
    except Exception as e:
        logger.error(f"Error updating ticket {ticket_id}: {str(e)}")

def send_high_risk_alert(ticket: Dict[str, Any], prediction: Dict[str, Any]):
    """Send SNS alert for high-risk tickets"""
    try:
        risk_level = "🔴 CRITICAL" if prediction['breach_probability'] > 0.9 else "🟡 HIGH"
        
        alert_message = {
            'alert_type': 'SLA_BREACH_RISK',
            'risk_level': risk_level,
            'ticket_id': ticket['ticket_id'],
            'priority': ticket.get('priority', 'Unknown'),
            'department': ticket.get('department', 'Unknown'),
            'breach_probability': prediction['breach_probability'],
            'confidence': prediction['confidence'],
            'model_used': prediction['model_used'],
            'original_text': ticket.get('original_text', '')[:200] + '...',
            'sla_deadline': ticket.get('sla_deadline'),
            'adjusted_deadline': ticket.get('adjusted_sla_deadline'),
            'timestamp': datetime.utcnow().isoformat(),
            'action_required': True,
            'escalation_needed': prediction['breach_probability'] > 0.9
        }
        
        subject = f"{risk_level} SLA Breach Risk - {ticket['ticket_id']} ({ticket.get('priority', 'Unknown')})"
        
        # Format message for readability
        formatted_message = f"""
🚨 SLA BREACH RISK ALERT

Ticket: {ticket['ticket_id']}
Risk Level: {risk_level}
Breach Probability: {prediction['breach_probability']:.1%}
Confidence: {prediction['confidence']:.1%}

Details:
- Priority: {ticket.get('priority', 'Unknown')}
- Department: {ticket.get('department', 'Unknown')}
- Sentiment: {ticket.get('sentiment', 'Unknown')}
- Model: {prediction['model_used']}

Issue: {ticket.get('original_text', '')[:200]}...

SLA Deadline: {ticket.get('sla_deadline')}
Adjusted Deadline: {ticket.get('adjusted_sla_deadline')}

Action Required: {'YES - IMMEDIATE' if prediction['breach_probability'] > 0.9 else 'YES - URGENT'}
        """
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=formatted_message,
            Subject=subject,
            MessageAttributes={
                'alert_type': {'DataType': 'String', 'StringValue': 'SLA_BREACH_RISK'},
                'risk_level': {'DataType': 'String', 'StringValue': str(prediction['breach_probability'])},
                'ticket_id': {'DataType': 'String', 'StringValue': ticket['ticket_id']},
                'priority': {'DataType': 'String', 'StringValue': ticket.get('priority', 'Unknown')}
            }
        )
        
        logger.info(f"🚨 High-risk alert sent for ticket {ticket['ticket_id']}: {prediction['breach_probability']:.1%}")
        
    except Exception as e:
        logger.error(f"Failed to send SNS alert: {str(e)}")

# For local testing
def main():
    """Test the Lambda function locally"""
    print("🧪 Testing Lambda ML Predictor")
    print("=" * 40)
    
    # Mock EventBridge event
    test_event = {
        'detail': {
            'ticket_id': 'TKT-20250211-test123',
            'priority': 'P1',
            'department': 'UIDAI',
            'sentiment': 'NEGATIVE',
            'urgency': 9,
            'workflow_id': 'test-workflow-123'
        }
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = 'test-ml-predictor'
            self.memory_limit_in_mb = 512
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
    
    context = MockContext()
    
    # Test the handler
    result = lambda_handler(test_event, context)
    print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    main()