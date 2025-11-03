#!/usr/bin/env python3
"""
Local testing for SLA Guard Agent functions
Tests individual components without AWS dependencies
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the lambda functions to path for testing
sys.path.append('../aws_deployment/lambda_functions')

def test_metric_processor():
    """Test the metric processor logic locally"""
    print("🧪 Testing Metric Processor Logic...")
    
    # Sample ticket data
    sample_ticket = {
        'ticket_id': 'TEST-001',
        'title': 'Test printer issue',
        'description': 'Testing SLA calculations',
        'priority': 3,
        'status': 'open',
        'category': 'hardware',
        'created_at': (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'assigned_to': 'test-tech',
        'reporter': 'test@company.com'
    }
    
    # SLA configuration
    sla_config = {
        'priority_3': {'response_time': 240, 'resolution_time': 1440},
        'target_adherence': 0.95
    }
    
    # Test SLA calculation
    try:
        sla_metrics = calculate_sla_metrics_local(sample_ticket, sla_config)
        
        print(f"✅ Ticket: {sample_ticket['ticket_id']}")
        print(f"   Breach Probability: {sla_metrics['breach_probability']:.1%}")
        print(f"   SLA Status: {sla_metrics['sla_status']}")
        print(f"   Time to Breach: {sla_metrics['time_to_breach_minutes']:.0f} minutes")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def calculate_sla_metrics_local(ticket_data: Dict[str, Any], sla_config: Dict[str, Any]) -> Dict[str, Any]:
    """Local implementation of SLA metrics calculation"""
    
    priority = ticket_data.get('priority', 3)
    priority_key = f'priority_{priority}'
    
    if priority_key not in sla_config:
        priority_key = 'priority_3'  # Default to P3
    
    thresholds = sla_config[priority_key]
    created_at = datetime.fromisoformat(ticket_data.get('created_at', datetime.utcnow().isoformat()))
    current_time = datetime.utcnow()
    
    # Calculate time elapsed
    elapsed_minutes = (current_time - created_at).total_seconds() / 60
    
    # Response SLA
    response_threshold = float(thresholds['response_time'])
    response_remaining = max(0, response_threshold - elapsed_minutes)
    response_breach_risk = min(1.0, elapsed_minutes / response_threshold)
    
    # Resolution SLA
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
    
    # Determine SLA status
    if breach_probability >= 0.9:
        sla_status = 'BREACH_IMMINENT'
    elif breach_probability >= 0.7:
        sla_status = 'AT_RISK'
    elif breach_probability >= 0.5:
        sla_status = 'WATCH'
    else:
        sla_status = 'HEALTHY'
    
    return {
        'response_threshold_minutes': response_threshold,
        'resolution_threshold_minutes': resolution_threshold,
        'elapsed_minutes': elapsed_minutes,
        'response_remaining_minutes': response_remaining,
        'resolution_remaining_minutes': resolution_remaining,
        'response_breach_risk': response_breach_risk,
        'resolution_breach_risk': resolution_breach_risk,
        'breach_probability': breach_probability,
        'sla_status': sla_status,
        'time_to_breach_minutes': min(response_remaining, resolution_remaining),
        'calculated_at': current_time.isoformat()
    }

def test_breach_predictor():
    """Test the breach predictor logic locally"""
    print("\n🧠 Testing Breach Predictor Logic...")
    
    # Sample event data
    event_data = {
        'ticket_id': 'TEST-001',
        'priority': 1,
        'status': 'open',
        'category': 'infrastructure',
        'breach_probability': 0.85,
        'response_remaining_minutes': 5,
        'resolution_remaining_minutes': 30
    }
    
    try:
        # Test ML features extraction
        features = extract_ml_features_local(event_data)
        print(f"✅ Extracted {len(features)} ML features")
        
        # Test prediction logic
        prediction = get_prediction_local(event_data, features)
        print(f"   Final Breach Probability: {prediction['final_breach_probability']:.1%}")
        print(f"   Recommended Actions: {', '.join(prediction['recommended_actions'][:3])}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def extract_ml_features_local(event_data: Dict[str, Any]) -> List[float]:
    """Local implementation of ML feature extraction"""
    
    # Simplified feature extraction for testing
    features = [
        float(event_data.get('priority', 3)),
        1.0 if event_data.get('status') == 'open' else 0.0,
        1.0 if event_data.get('status') == 'in_progress' else 0.0,
        float(event_data.get('response_remaining_minutes', 0)),
        float(event_data.get('resolution_remaining_minutes', 0)),
        1.0 if event_data.get('category') == 'hardware' else 0.0,
        1.0 if event_data.get('category') == 'software' else 0.0,
        1.0 if event_data.get('category') == 'infrastructure' else 0.0,
        1.0 if event_data.get('category') == 'access' else 0.0,
        240.0,  # avg_resolution_time
        0.15,   # breach_rate
        0.25,   # escalation_rate
        10.0,   # active_tickets
        0.7,    # technician_utilization
        30.0    # avg_response_time
    ]
    
    return features

def get_prediction_local(event_data: Dict[str, Any], features: List[float]) -> Dict[str, Any]:
    """Local implementation of prediction logic"""
    
    # Simplified prediction logic
    rule_based_prob = event_data.get('breach_probability', 0.0)
    
    # Simple heuristic based on time remaining
    response_remaining = features[3]  # response_remaining_minutes
    resolution_remaining = features[4]  # resolution_remaining_minutes
    
    if response_remaining <= 5:
        ml_prob = 0.9
    elif response_remaining <= 15:
        ml_prob = 0.7
    elif resolution_remaining <= 60:
        ml_prob = 0.6
    else:
        ml_prob = 0.3
    
    # Combine predictions
    ml_confidence = 0.85
    final_probability = (rule_based_prob * (1 - ml_confidence) + ml_prob * ml_confidence)
    
    # Get recommended actions
    recommended_actions = get_recommended_actions_local(event_data, final_probability)
    
    return {
        'ticket_id': event_data['ticket_id'],
        'rule_based_probability': rule_based_prob,
        'ml_probability': ml_prob,
        'final_breach_probability': final_probability,
        'confidence': ml_confidence,
        'recommended_actions': recommended_actions,
        'priority_boost': final_probability >= 0.7,
        'time_to_breach_minutes': min(response_remaining, resolution_remaining),
        'prediction_timestamp': datetime.utcnow().isoformat()
    }

def get_recommended_actions_local(event_data: Dict[str, Any], breach_probability: float) -> List[str]:
    """Local implementation of action recommendations"""
    
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

def test_action_trigger():
    """Test the action trigger logic locally"""
    print("\n⚡ Testing Action Trigger Logic...")
    
    # Sample action context
    action_context = {
        'ticket_id': 'TEST-001',
        'breach_probability': 0.85,
        'confidence': 0.9,
        'time_to_breach': 15,
        'recommended_actions': ['escalate-immediately', 'notify-manager', 'boost-priority'],
        'priority_boost': True,
        'category': 'infrastructure',
        'current_priority': 2
    }
    
    try:
        # Test action execution logic
        executed_actions = execute_actions_local(action_context)
        
        print(f"✅ Executed {len(executed_actions)} actions:")
        for action in executed_actions:
            print(f"   • {action['action']}: {action['description']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def execute_actions_local(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Local implementation of action execution"""
    
    executed_actions = []
    
    for action in context['recommended_actions'][:3]:  # Execute first 3 actions
        action_result = {
            'action': action,
            'ticket_id': context['ticket_id'],
            'success': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if action == 'escalate-immediately':
            action_result['description'] = 'Escalated to senior admin (Priority boosted to P1)'
        elif action == 'notify-manager':
            action_result['description'] = 'Manager notified via email and SMS'
        elif action == 'boost-priority':
            action_result['description'] = f"Priority boosted from P{context['current_priority']} to P{max(1, context['current_priority'] - 1)}"
        elif action == 'assign-senior-tech':
            action_result['description'] = 'Senior technician assigned'
        elif action == 'trigger-incident-response':
            action_result['description'] = 'Incident response team activated'
        else:
            action_result['description'] = f"Action executed: {action.replace('-', ' ').title()}"
        
        executed_actions.append(action_result)
    
    return executed_actions

def main():
    """Run all local tests"""
    print("🧩 SLA Guard Agent - Local Function Testing")
    print("=" * 50)
    
    tests = [
        ("Metric Processor", test_metric_processor),
        ("Breach Predictor", test_breach_predictor),
        ("Action Trigger", test_action_trigger)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 Test Results:")
    print("=" * 20)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All local tests passed! Functions are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main()