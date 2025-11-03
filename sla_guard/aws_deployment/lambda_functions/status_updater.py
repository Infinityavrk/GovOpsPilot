import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
SLA_STATE_TABLE = os.environ['SLA_STATE_TABLE']

def handler(event, context):
    """
    Receive status updates from L1 automation and other agents
    Update SLA tracking based on task completion results
    """
    try:
        logger.info(f"Processing status update: {json.dumps(event)}")
        
        # Process EventBridge events from other agents
        if 'Records' in event:
            for record in event['Records']:
                process_status_record(record)
        else:
            # Direct invocation
            process_direct_status_update(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Status updated successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        raise

def process_status_record(record: Dict[str, Any]):
    """Process individual status update record"""
    
    try:
        detail = record.get('detail', {})
        source = record.get('source', '')
        detail_type = record.get('detail-type', '')
        
        if source == 'l1-automation':
            process_l1_update(detail, detail_type)
        elif source == 'asset-optimizer':
            process_optimizer_update(detail, detail_type)
        else:
            logger.warning(f"Unknown status update source: {source}")
            
    except Exception as e:
        logger.error(f"Error processing status record: {e}")

def process_l1_update(detail: Dict[str, Any], detail_type: str):
    """Process L1 automation status updates"""
    
    ticket_id = detail.get('ticket_id', '')
    if not ticket_id:
        logger.warning("No ticket_id in L1 update")
        return
    
    if detail_type == 'L1 Task Completion':
        handle_l1_task_completion(detail)
    elif detail_type == 'L1 Task Started':
        handle_l1_task_started(detail)
    elif detail_type == 'L1 Task Failed':
        handle_l1_task_failed(detail)
    else:
        logger.info(f"Unhandled L1 detail type: {detail_type}")

def handle_l1_task_completion(detail: Dict[str, Any]):
    """Handle L1 task completion"""
    
    ticket_id = detail['ticket_id']
    task_status = detail.get('status', 'completed')
    execution_time = detail.get('execution_time', 0)
    sla_impact = detail.get('sla_impact', 'positive')
    
    # Calculate SLA improvement based on task success
    sla_adjustment = calculate_sla_adjustment(task_status, execution_time, sla_impact)
    
    # Update SLA state
    update_sla_state(ticket_id, {
        'l1_task_completed': True,
        'l1_task_status': task_status,
        'l1_execution_time': execution_time,
        'sla_adjustment': sla_adjustment,
        'updated_by': 'l1-automation',
        'update_timestamp': datetime.utcnow().isoformat()
    })
    
    logger.info(f"Updated SLA state for ticket {ticket_id} after L1 completion")

def handle_l1_task_started(detail: Dict[str, Any]):
    """Handle L1 task start"""
    
    ticket_id = detail['ticket_id']
    task_type = detail.get('task_type', 'unknown')
    estimated_duration = detail.get('estimated_duration', 5)
    
    # Update SLA state to reflect automation in progress
    update_sla_state(ticket_id, {
        'l1_task_in_progress': True,
        'l1_task_type': task_type,
        'l1_estimated_duration': estimated_duration,
        'l1_started_at': datetime.utcnow().isoformat(),
        'updated_by': 'l1-automation'
    })
    
    logger.info(f"Updated SLA state for ticket {ticket_id} - L1 task started")

def handle_l1_task_failed(detail: Dict[str, Any]):
    """Handle L1 task failure"""
    
    ticket_id = detail['ticket_id']
    failure_reason = detail.get('failure_reason', 'unknown')
    retry_recommended = detail.get('retry_recommended', False)
    
    # Calculate negative SLA impact due to failure
    sla_adjustment = {
        'breach_probability_delta': 0.1,  # Increase breach probability
        'confidence_delta': -0.1,  # Decrease confidence in automation
        'escalation_recommended': True
    }
    
    # Update SLA state
    update_sla_state(ticket_id, {
        'l1_task_failed': True,
        'l1_failure_reason': failure_reason,
        'l1_retry_recommended': retry_recommended,
        'sla_adjustment': sla_adjustment,
        'updated_by': 'l1-automation',
        'update_timestamp': datetime.utcnow().isoformat()
    })
    
    logger.warning(f"Updated SLA state for ticket {ticket_id} after L1 failure: {failure_reason}")

def process_optimizer_update(detail: Dict[str, Any], detail_type: str):
    """Process asset optimizer status updates"""
    
    if detail_type == 'Optimization Impact Assessment':
        handle_optimization_impact(detail)
    elif detail_type == 'License Change Completed':
        handle_license_change(detail)
    else:
        logger.info(f"Unhandled optimizer detail type: {detail_type}")

def handle_optimization_impact(detail: Dict[str, Any]):
    """Handle optimization impact assessment"""
    
    affected_services = detail.get('affected_services', [])
    impact_level = detail.get('impact_level', 'low')
    optimization_id = detail.get('optimization_id', '')
    
    # Update SLA state for affected services
    for service_id in affected_services:
        sla_adjustment = calculate_optimization_impact(impact_level)
        
        update_sla_state(service_id, {
            'optimization_impact': True,
            'optimization_id': optimization_id,
            'impact_level': impact_level,
            'sla_adjustment': sla_adjustment,
            'updated_by': 'asset-optimizer',
            'update_timestamp': datetime.utcnow().isoformat()
        })
    
    logger.info(f"Updated SLA state for {len(affected_services)} services due to optimization impact")

def handle_license_change(detail: Dict[str, Any]):
    """Handle completed license changes"""
    
    affected_services = detail.get('affected_services', [])
    change_type = detail.get('change_type', 'unknown')
    success = detail.get('success', True)
    
    # Update SLA state based on license change outcome
    for service_id in affected_services:
        if success:
            sla_adjustment = {'breach_probability_delta': -0.05}  # Slight improvement
        else:
            sla_adjustment = {'breach_probability_delta': 0.15}   # Potential risk
        
        update_sla_state(service_id, {
            'license_change_completed': True,
            'license_change_type': change_type,
            'license_change_success': success,
            'sla_adjustment': sla_adjustment,
            'updated_by': 'asset-optimizer',
            'update_timestamp': datetime.utcnow().isoformat()
        })
    
    logger.info(f"Updated SLA state for {len(affected_services)} services after license change")

def calculate_sla_adjustment(task_status: str, execution_time: int, sla_impact: str) -> Dict[str, float]:
    """Calculate SLA adjustment based on L1 task results"""
    
    adjustment = {
        'breach_probability_delta': 0.0,
        'confidence_delta': 0.0,
        'time_saved_minutes': 0
    }
    
    if task_status == 'completed':
        # Successful automation improves SLA outlook
        if sla_impact == 'positive':
            adjustment['breach_probability_delta'] = -0.2  # Reduce breach probability
            adjustment['confidence_delta'] = 0.1           # Increase confidence
            adjustment['time_saved_minutes'] = max(15, execution_time * 3)  # Estimate time saved
        elif sla_impact == 'neutral':
            adjustment['breach_probability_delta'] = -0.1
            adjustment['time_saved_minutes'] = execution_time
    
    elif task_status == 'partial':
        # Partial success has limited impact
        adjustment['breach_probability_delta'] = -0.05
        adjustment['time_saved_minutes'] = execution_time // 2
    
    elif task_status == 'failed':
        # Failed automation may worsen SLA outlook
        adjustment['breach_probability_delta'] = 0.1
        adjustment['confidence_delta'] = -0.05
    
    return adjustment

def calculate_optimization_impact(impact_level: str) -> Dict[str, float]:
    """Calculate SLA impact from optimization changes"""
    
    impact_map = {
        'low': {'breach_probability_delta': 0.02},
        'medium': {'breach_probability_delta': 0.05},
        'high': {'breach_probability_delta': 0.1},
        'critical': {'breach_probability_delta': 0.2}
    }
    
    return impact_map.get(impact_level, {'breach_probability_delta': 0.02})

def update_sla_state(ticket_id: str, update_data: Dict[str, Any]):
    """Update SLA state in DynamoDB"""
    
    table = dynamodb.Table(SLA_STATE_TABLE)
    
    try:
        # Get the latest record for this ticket
        response = table.query(
            KeyConditionExpression='service_id = :ticket_id',
            ExpressionAttributeValues={':ticket_id': ticket_id},
            ScanIndexForward=False,  # Get latest first
            Limit=1
        )
        
        if response['Items']:
            latest_item = response['Items'][0]
            
            # Apply SLA adjustment if present
            if 'sla_adjustment' in update_data:
                apply_sla_adjustment(latest_item, update_data['sla_adjustment'])
            
            # Create new record with updates
            timestamp = int(datetime.utcnow().timestamp() * 1000)
            
            updated_item = latest_item.copy()
            updated_item.update({
                'timestamp': timestamp,
                'status_updates': latest_item.get('status_updates', []) + [update_data],
                'last_updated': datetime.utcnow().isoformat()
            })
            
            # Update specific fields
            for key, value in update_data.items():
                if key != 'sla_adjustment':
                    updated_item[key] = value
            
            table.put_item(Item=updated_item)
            logger.info(f"Updated SLA state for ticket {ticket_id}")
            
        else:
            logger.warning(f"No existing SLA state found for ticket {ticket_id}")
            
    except Exception as e:
        logger.error(f"Error updating SLA state: {e}")

def apply_sla_adjustment(item: Dict[str, Any], adjustment: Dict[str, float]):
    """Apply SLA adjustment to existing metrics"""
    
    try:
        sla_metrics = item.get('sla_metrics', {})
        
        # Adjust breach probability
        if 'breach_probability_delta' in adjustment:
            current_prob = sla_metrics.get('breach_probability', 0.0)
            new_prob = max(0.0, min(1.0, current_prob + adjustment['breach_probability_delta']))
            sla_metrics['breach_probability'] = new_prob
            sla_metrics['breach_probability_bucket'] = get_breach_bucket(new_prob)
            sla_metrics['sla_status'] = get_sla_status(new_prob)
        
        # Adjust confidence
        if 'confidence_delta' in adjustment:
            # This would apply to ML prediction confidence
            pass
        
        # Update time estimates
        if 'time_saved_minutes' in adjustment:
            time_saved = adjustment['time_saved_minutes']
            sla_metrics['response_remaining_minutes'] = sla_metrics.get('response_remaining_minutes', 0) + time_saved
            sla_metrics['resolution_remaining_minutes'] = sla_metrics.get('resolution_remaining_minutes', 0) + time_saved
        
        item['sla_metrics'] = sla_metrics
        
    except Exception as e:
        logger.error(f"Error applying SLA adjustment: {e}")

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

def process_direct_status_update(event: Dict[str, Any]):
    """Process direct status update"""
    
    ticket_id = event.get('ticket_id', '')
    update_type = event.get('update_type', 'general')
    update_data = event.get('update_data', {})
    
    if ticket_id:
        update_sla_state(ticket_id, {
            'direct_update': True,
            'update_type': update_type,
            **update_data,
            'updated_by': 'direct-api',
            'update_timestamp': datetime.utcnow().isoformat()
        })
        logger.info(f"Processed direct status update for ticket {ticket_id}")
    else:
        logger.warning("No ticket_id provided in direct status update")