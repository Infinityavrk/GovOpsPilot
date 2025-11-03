#!/usr/bin/env python3
"""
Natural Language Ticket API
Backend API to process natural language descriptions and create tickets
"""

import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from chatbot_production_integration import ChatbotProductionIntegration

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize the production integration
production_integration = ChatbotProductionIntegration()

@app.route('/')
def home():
    """Serve the natural language interface"""
    try:
        with open('natural_language_helpdesk.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>Natural Language Helpdesk API</h1>
        <p>API is running! Use POST /api/create-ticket to create tickets from natural language.</p>
        <p>Example: POST {"description": "Aadhaar authentication failing in Indore - critical!"}</p>
        """

@app.route('/api/create-ticket', methods=['POST'])
def create_ticket_api():
    """Create ticket from natural language description"""
    
    try:
        data = request.get_json()
        
        if not data or 'description' not in data:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        description = data['description'].strip()
        
        if not description:
            return jsonify({
                'success': False,
                'error': 'Description cannot be empty'
            }), 400
        
        # Process through production integration
        result = production_integration.process_chatbot_message(
            description, 
            user_info=data.get('user_info', {'type': 'web_user'})
        )
        
        if result['success']:
            ticket_data = result['ticket_data']
            
            # Format response for frontend
            response = {
                'success': True,
                'ticket': {
                    'ticket_id': ticket_data['ticket_id'],
                    'department': ticket_data['department'],
                    'priority': ticket_data['priority'],
                    'service_type': ticket_data['service_type'],
                    'location': ticket_data['location'],
                    'sla_deadline': ticket_data['sla_due_time'],
                    'sla_hours': ticket_data.get('sla_hours', 24),
                    'breach_probability': ticket_data['breach_probability'],
                    'revenue_impact': ticket_data['revenue_impact'],
                    'confidence_score': ticket_data['confidence_score'],
                    'sentiment': ticket_data.get('sentiment', 'neutral'),
                    'urgency_level': ticket_data.get('urgency_level', 'normal'),
                    'created_at': ticket_data['created_at'],
                    'status': ticket_data['status']
                },
                'analysis': {
                    'department': ticket_data['department'],
                    'department_confidence': ticket_data['confidence_score'],
                    'priority': ticket_data['priority'],
                    'priority_reason': get_priority_reason(ticket_data['priority'], description),
                    'location': ticket_data['location'],
                    'service_type': ticket_data['service_type'],
                    'sentiment': ticket_data.get('sentiment', 'neutral'),
                    'urgency_level': ticket_data.get('urgency_level', 'normal')
                },
                'production_flow': {
                    'initiated': True,
                    'steps_completed': count_completed_steps(ticket_data.get('production_flow', {})),
                    'total_steps': 9,
                    'status': 'processing'
                }
            }
            
            return jsonify(response)
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to process ticket')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    """Get all created tickets"""
    
    try:
        # In a real implementation, this would query DynamoDB
        # For now, return mock data or stored tickets
        
        tickets = []  # Would fetch from database
        
        return jsonify({
            'success': True,
            'tickets': tickets,
            'count': len(tickets)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_description():
    """Analyze description without creating ticket"""
    
    try:
        data = request.get_json()
        
        if not data or 'description' not in data:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        description = data['description'].strip()
        analysis = analyze_with_ai(description)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

def analyze_with_ai(description):
    """Analyze description with AI (same logic as frontend)"""
    
    text = description.lower()
    
    # Department analysis
    department = 'MPOnline'
    department_confidence = 0.6
    
    if any(word in text for word in ['aadhaar', 'authentication', 'biometric', 'uid']):
        department = 'UIDAI'
        department_confidence = 0.95
    elif any(word in text for word in ['payment', 'gateway', 'transaction', 'money']):
        department = 'MeiTY'
        department_confidence = 0.90
    elif any(word in text for word in ['portal', 'website', 'digital', 'online']):
        department = 'DigitalMP'
        department_confidence = 0.88
    elif any(word in text for word in ['certificate', 'document', 'app']):
        department = 'eDistrict'
        department_confidence = 0.85
    
    # Priority analysis
    priority = 'P3'
    priority_reason = 'Standard issue'
    
    if any(word in text for word in ['critical', 'urgent', 'failing', 'down', 'emergency']):
        priority = 'P1'
        priority_reason = 'Critical/Urgent keywords detected'
    elif any(word in text for word in ['important', 'high', 'serious', 'asap']):
        priority = 'P2'
        priority_reason = 'High importance indicators'
    elif any(word in text for word in ['minor', 'small', 'question']):
        priority = 'P4'
        priority_reason = 'Low priority indicators'
    
    # Location detection
    locations = ['mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'kolkata',
                'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur',
                'indore', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'gwalior']
    
    location = 'Not specified'
    for loc in locations:
        if loc in text:
            location = loc.title()
            break
    
    # Service type
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
    
    # Sentiment analysis
    negative_words = ['angry', 'frustrated', 'terrible', 'awful', 'horrible']
    positive_words = ['please', 'help', 'thank', 'appreciate', 'grateful']
    
    sentiment = 'neutral'
    if any(word in text for word in negative_words):
        sentiment = 'negative'
    elif any(word in text for word in positive_words):
        sentiment = 'positive'
    
    # Urgency detection
    urgency_words = ['urgent', 'asap', 'immediately', 'now', 'quickly']
    urgency_level = 'high' if any(word in text for word in urgency_words) else 'normal'
    
    return {
        'department': department,
        'department_confidence': department_confidence,
        'priority': priority,
        'priority_reason': priority_reason,
        'location': location,
        'service_type': service_type,
        'sentiment': sentiment,
        'urgency_level': urgency_level,
        'confidence': department_confidence,
        'analysis_timestamp': datetime.now().isoformat()
    }

def get_priority_reason(priority, description):
    """Get reason for priority classification"""
    
    text = description.lower()
    
    if priority == 'P1':
        if 'critical' in text:
            return 'Critical keyword detected'
        elif 'urgent' in text:
            return 'Urgent keyword detected'
        elif 'failing' in text or 'down' in text:
            return 'Service failure indicators'
        else:
            return 'High severity indicators'
    elif priority == 'P2':
        return 'High importance indicators'
    elif priority == 'P4':
        return 'Low priority indicators'
    else:
        return 'Standard issue classification'

def count_completed_steps(production_flow):
    """Count completed production flow steps"""
    
    if not production_flow:
        return 0
    
    completed = 0
    steps = [
        'dynamodb_stored', 'eventbridge_triggered', 'sagemaker_analyzed',
        'stepfunctions_started', 'alerts_sent', 'quicksight_updated',
        's3_archived', 'retraining_triggered'
    ]
    
    for step in steps:
        if production_flow.get(step, False):
            completed += 1
    
    return completed

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Natural Language Ticket API',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Natural Language Ticket API")
    print("=" * 50)
    print("🌐 Frontend: http://localhost:5000")
    print("🔗 API: http://localhost:5000/api/create-ticket")
    print("📊 Health: http://localhost:5000/health")
    print()
    print("📝 Example API Usage:")
    print('curl -X POST http://localhost:5000/api/create-ticket \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"description": "Aadhaar authentication failing in Indore - critical!"}\'')
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)