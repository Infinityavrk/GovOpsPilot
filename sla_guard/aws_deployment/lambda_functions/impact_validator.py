import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')

# Environment variables
SLA_STATE_TABLE = os.environ['SLA_STATE_TABLE']
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']

def handler(event, context):
    """
    Validate optimization impact on SLA before allowing changes
    Ensures cost optimizations don't negatively affect service delivery
    """
    try:
        logger.info(f"Processing impact validation: {json.dumps(event)}")
        
        # Process EventBridge events from asset optimizer
        if 'Records' in event:
            for record in event['Records']:
                process_validation_record(record)
        else:
            # Direct invocation
            process_direct_validation(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Impact validation completed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in impact validation: {str(e)}")
        raise

def process_validation_record(record: Dict[str, Any]):
    """Process individual validation record"""
    
    try:
        detail = record.get('detail', {})
        detail_type = record.get('detail-type', '')
        
        if detail_type == 'Optimization Recommendation':
            validate_optimization_recommendation(detail)
        elif detail_type == 'License Change Request':
            validate_license_change_request(detail)
        else:
            logger.info(f"Unhandled validation detail type: {detail_type}")
            
    except Exception as e:
        logger.error(f"Error processing validation record: {e}")

def validate_optimization_recommendation(detail: Dict[str, Any]):
    """Validate optimization recommendation against SLA impact"""
    
    optimization_id = detail.get('optimization_id', '')
    optimization_type = detail.get('optimization_type', '')
    affected_assets = detail.get('affected_assets', [])
    potential_savings = detail.get('potential_savings', 0)
    proposed_changes = detail.get('proposed_changes', [])
    
    logger.info(f"Validating optimization {optimization_id}: {optimization_type}")
    
    # Analyze SLA impact for each affected asset
    impact_analysis = analyze_sla_impact(affected_assets, proposed_changes)
    
    # Make approval decision
    approval_decision = make_approval_decision(impact_analysis, potential_savings)
    
    # Send validation result back to optimizer
    send_validation_result(optimization_id, approval_decision, impact_analysis)

def validate_license_change_request(detail: Dict[str, Any]):
    """Validate license change request against SLA impact"""
    
    change_id = detail.get('change_id', '')
    change_type = detail.get('change_type', '')
    affected_services = detail.get('affected_services', [])
    license_details = detail.get('license_details', {})
    
    logger.info(f"Validating license change {change_id}: {change_type}")
    
    # Analyze impact on affected services
    service_impact = analyze_service_impact(affected_services, change_type, license_details)
    
    # Make approval decision
    approval_decision = make_license_approval_decision(service_impact, change_type)
    
    # Send validation result
    send_license_validation_result(change_id, approval_decision, service_impact)

def analyze_sla_impact(affected_assets: List[str], proposed_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze SLA impact of proposed optimization changes"""
    
    impact_analysis = {
        'overall_risk_level': 'low',
        'affected_services': [],
        'risk_factors': [],
        'mitigation_recommendations': [],
        'approval_recommended': True
    }
    
    high_risk_services = []
    medium_risk_services = []
    
    # Check each affected asset
    for asset_id in affected_assets:
        asset_impact = analyze_asset_impact(asset_id, proposed_changes)
        
        if asset_impact['risk_level'] == 'high':
            high_risk_services.append(asset_impact)
            impact_analysis['risk_factors'].extend(asset_impact['risk_factors'])
        elif asset_impact['risk_level'] == 'medium':
            medium_risk_services.append(asset_impact)
    
    # Determine overall risk level
    if high_risk_services:
        impact_analysis['overall_risk_level'] = 'high'
        impact_analysis['approval_recommended'] = False
        impact_analysis['mitigation_recommendations'].append('Defer optimization until SLA risk is reduced')
    elif len(medium_risk_services) > 3:
        impact_analysis['overall_risk_level'] = 'medium'
        impact_analysis['mitigation_recommendations'].append('Implement changes in phases')
    
    impact_analysis['affected_services'] = high_risk_services + medium_risk_services
    
    return impact_analysis

def analyze_asset_impact(asset_id: str, proposed_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze impact of changes on a specific asset"""
    
    asset_impact = {
        'asset_id': asset_id,
        'risk_level': 'low',
        'risk_factors': [],
        'current_sla_status': 'unknown',
        'predicted_impact': 'minimal'
    }
    
    # Get current SLA status for services using this asset
    current_sla_status = get_asset_sla_status(asset_id)
    asset_impact['current_sla_status'] = current_sla_status
    
    # Analyze each proposed change
    for change in proposed_changes:
        change_risk = assess_change_risk(asset_id, change, current_sla_status)
        
        if change_risk['risk_level'] == 'high':
            asset_impact['risk_level'] = 'high'
            asset_impact['risk_factors'].extend(change_risk['factors'])
        elif change_risk['risk_level'] == 'medium' and asset_impact['risk_level'] != 'high':
            asset_impact['risk_level'] = 'medium'
            asset_impact['risk_factors'].extend(change_risk['factors'])
    
    return asset_impact

def get_asset_sla_status(asset_id: str) -> Dict[str, Any]:
    """Get current SLA status for services using this asset"""
    
    table = dynamodb.Table(SLA_STATE_TABLE)
    
    try:
        # Query for recent SLA data related to this asset
        # In production, this would use a GSI or asset-service mapping
        response = table.scan(
            FilterExpression='contains(ticket_data.description, :asset_id) OR contains(ticket_data.title, :asset_id)',
            ExpressionAttributeValues={':asset_id': asset_id},
            Limit=10
        )
        
        if response['Items']:
            # Calculate aggregate SLA status
            total_breach_prob = 0
            at_risk_count = 0
            healthy_count = 0
            
            for item in response['Items']:
                sla_metrics = item.get('sla_metrics', {})
                breach_prob = sla_metrics.get('breach_probability', 0)
                total_breach_prob += breach_prob
                
                if breach_prob >= 0.7:
                    at_risk_count += 1
                else:
                    healthy_count += 1
            
            avg_breach_prob = total_breach_prob / len(response['Items'])
            
            return {
                'avg_breach_probability': avg_breach_prob,
                'at_risk_services': at_risk_count,
                'healthy_services': healthy_count,
                'total_services': len(response['Items']),
                'overall_status': 'at_risk' if avg_breach_prob >= 0.5 else 'healthy'
            }
    
    except Exception as e:
        logger.warning(f"Could not get SLA status for asset {asset_id}: {e}")
    
    return {
        'avg_breach_probability': 0.3,
        'at_risk_services': 0,
        'healthy_services': 1,
        'total_services': 1,
        'overall_status': 'healthy'
    }

def assess_change_risk(asset_id: str, change: Dict[str, Any], current_sla: Dict[str, Any]) -> Dict[str, Any]:
    """Assess risk of a specific change"""
    
    change_type = change.get('type', '')
    change_details = change.get('details', {})
    
    risk_assessment = {
        'risk_level': 'low',
        'factors': []
    }
    
    # Risk factors based on change type
    if change_type == 'license_reduction':
        reduction_percentage = change_details.get('reduction_percentage', 0)
        
        if reduction_percentage > 50:
            risk_assessment['risk_level'] = 'high'
            risk_assessment['factors'].append(f'Large license reduction ({reduction_percentage}%)')
        elif reduction_percentage > 25:
            risk_assessment['risk_level'] = 'medium'
            risk_assessment['factors'].append(f'Moderate license reduction ({reduction_percentage}%)')
    
    elif change_type == 'license_consolidation':
        affected_departments = change_details.get('affected_departments', [])
        
        if len(affected_departments) > 5:
            risk_assessment['risk_level'] = 'medium'
            risk_assessment['factors'].append(f'Multiple departments affected ({len(affected_departments)})')
    
    elif change_type == 'vendor_change':
        risk_assessment['risk_level'] = 'high'
        risk_assessment['factors'].append('Vendor change introduces operational risk')
    
    # Amplify risk if current SLA status is poor
    if current_sla.get('overall_status') == 'at_risk':
        if risk_assessment['risk_level'] == 'low':
            risk_assessment['risk_level'] = 'medium'
        elif risk_assessment['risk_level'] == 'medium':
            risk_assessment['risk_level'] = 'high'
        
        risk_assessment['factors'].append('Current SLA status is at risk')
    
    return risk_assessment

def analyze_service_impact(affected_services: List[str], change_type: str, license_details: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze impact on specific services"""
    
    service_impact = {
        'high_risk_services': [],
        'medium_risk_services': [],
        'low_risk_services': [],
        'overall_risk': 'low',
        'approval_recommended': True
    }
    
    for service_id in affected_services:
        service_sla = get_service_sla_status(service_id)
        service_risk = assess_service_change_risk(service_id, change_type, license_details, service_sla)
        
        if service_risk['risk_level'] == 'high':
            service_impact['high_risk_services'].append(service_risk)
        elif service_risk['risk_level'] == 'medium':
            service_impact['medium_risk_services'].append(service_risk)
        else:
            service_impact['low_risk_services'].append(service_risk)
    
    # Determine overall risk
    if service_impact['high_risk_services']:
        service_impact['overall_risk'] = 'high'
        service_impact['approval_recommended'] = False
    elif len(service_impact['medium_risk_services']) > 2:
        service_impact['overall_risk'] = 'medium'
    
    return service_impact

def get_service_sla_status(service_id: str) -> Dict[str, Any]:
    """Get current SLA status for a specific service"""
    
    table = dynamodb.Table(SLA_STATE_TABLE)
    
    try:
        response = table.query(
            KeyConditionExpression='service_id = :service_id',
            ExpressionAttributeValues={':service_id': service_id},
            ScanIndexForward=False,
            Limit=1
        )
        
        if response['Items']:
            item = response['Items'][0]
            sla_metrics = item.get('sla_metrics', {})
            
            return {
                'breach_probability': sla_metrics.get('breach_probability', 0),
                'sla_status': sla_metrics.get('sla_status', 'HEALTHY'),
                'response_remaining': sla_metrics.get('response_remaining_minutes', 60),
                'resolution_remaining': sla_metrics.get('resolution_remaining_minutes', 240)
            }
    
    except Exception as e:
        logger.warning(f"Could not get SLA status for service {service_id}: {e}")
    
    return {
        'breach_probability': 0.2,
        'sla_status': 'HEALTHY',
        'response_remaining': 60,
        'resolution_remaining': 240
    }

def assess_service_change_risk(service_id: str, change_type: str, license_details: Dict[str, Any], service_sla: Dict[str, Any]) -> Dict[str, Any]:
    """Assess risk of license change on specific service"""
    
    risk_assessment = {
        'service_id': service_id,
        'risk_level': 'low',
        'risk_factors': [],
        'current_sla_status': service_sla.get('sla_status', 'HEALTHY')
    }
    
    # Base risk from change type
    if change_type == 'license_downgrade':
        risk_assessment['risk_level'] = 'medium'
        risk_assessment['risk_factors'].append('License downgrade may affect functionality')
    elif change_type == 'license_removal':
        risk_assessment['risk_level'] = 'high'
        risk_assessment['risk_factors'].append('License removal will affect service availability')
    
    # Amplify risk based on current SLA status
    current_breach_prob = service_sla.get('breach_probability', 0)
    
    if current_breach_prob >= 0.7:
        if risk_assessment['risk_level'] == 'low':
            risk_assessment['risk_level'] = 'medium'
        elif risk_assessment['risk_level'] == 'medium':
            risk_assessment['risk_level'] = 'high'
        
        risk_assessment['risk_factors'].append(f'Service already at risk (breach probability: {current_breach_prob:.1%})')
    
    return risk_assessment

def make_approval_decision(impact_analysis: Dict[str, Any], potential_savings: float) -> Dict[str, Any]:
    """Make approval decision based on impact analysis and savings"""
    
    decision = {
        'approved': impact_analysis.get('approval_recommended', True),
        'approval_level': 'automatic',
        'conditions': [],
        'reasoning': []
    }
    
    risk_level = impact_analysis.get('overall_risk_level', 'low')
    
    if risk_level == 'high':
        decision['approved'] = False
        decision['reasoning'].append('High SLA risk identified')
    elif risk_level == 'medium':
        if potential_savings > 100000:  # $100k threshold
            decision['approved'] = True
            decision['approval_level'] = 'conditional'
            decision['conditions'].extend([
                'Implement in phases',
                'Monitor SLA impact closely',
                'Prepare rollback plan'
            ])
            decision['reasoning'].append('Medium risk acceptable due to high savings')
        else:
            decision['approved'] = False
            decision['reasoning'].append('Medium risk not justified by savings amount')
    else:
        decision['approved'] = True
        decision['reasoning'].append('Low SLA risk identified')
    
    return decision

def make_license_approval_decision(service_impact: Dict[str, Any], change_type: str) -> Dict[str, Any]:
    """Make approval decision for license changes"""
    
    decision = {
        'approved': service_impact.get('approval_recommended', True),
        'approval_level': 'automatic',
        'conditions': [],
        'reasoning': []
    }
    
    if service_impact['high_risk_services']:
        decision['approved'] = False
        decision['reasoning'].append(f"High risk services identified: {len(service_impact['high_risk_services'])}")
    elif service_impact['medium_risk_services']:
        decision['approval_level'] = 'conditional'
        decision['conditions'].extend([
            'Stagger implementation across services',
            'Monitor affected services for 24 hours',
            'Have rollback procedure ready'
        ])
        decision['reasoning'].append(f"Medium risk services require careful monitoring: {len(service_impact['medium_risk_services'])}")
    
    return decision

def send_validation_result(optimization_id: str, decision: Dict[str, Any], impact_analysis: Dict[str, Any]):
    """Send validation result back to asset optimizer"""
    
    result_event = {
        'optimization_id': optimization_id,
        'validation_result': 'approved' if decision['approved'] else 'rejected',
        'approval_level': decision['approval_level'],
        'conditions': decision['conditions'],
        'reasoning': decision['reasoning'],
        'impact_analysis': impact_analysis,
        'validated_by': 'sla-guard',
        'validation_timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'Optimization Validation Result',
                    'Detail': json.dumps(result_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Sent validation result for optimization {optimization_id}: {'approved' if decision['approved'] else 'rejected'}")
    except Exception as e:
        logger.error(f"Error sending validation result: {e}")

def send_license_validation_result(change_id: str, decision: Dict[str, Any], service_impact: Dict[str, Any]):
    """Send license validation result"""
    
    result_event = {
        'change_id': change_id,
        'validation_result': 'approved' if decision['approved'] else 'rejected',
        'approval_level': decision['approval_level'],
        'conditions': decision['conditions'],
        'reasoning': decision['reasoning'],
        'service_impact': service_impact,
        'validated_by': 'sla-guard',
        'validation_timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'sla-guard',
                    'DetailType': 'License Change Validation Result',
                    'Detail': json.dumps(result_event),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info(f"Sent license validation result for change {change_id}: {'approved' if decision['approved'] else 'rejected'}")
    except Exception as e:
        logger.error(f"Error sending license validation result: {e}")

def process_direct_validation(event: Dict[str, Any]):
    """Process direct validation request"""
    
    validation_type = event.get('validation_type', 'optimization')
    
    if validation_type == 'optimization':
        validate_optimization_recommendation(event)
    elif validation_type == 'license_change':
        validate_license_change_request(event)
    else:
        logger.warning(f"Unknown validation type: {validation_type}")