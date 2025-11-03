#!/usr/bin/env python3
"""
GenAI Workflow UI Server with Backend Integration
Serves the UI and provides API endpoints to connect with the actual GenAI workflow
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Any

# Try to import Flask, fall back to simple HTTP server if not available
try:
    from flask import Flask, render_template_string, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask not available. Install with: pip install flask flask-cors")

# Import our GenAI workflow
try:
    from demo_genai_workflow import DemoGenAIWorkflow
    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False
    print("⚠️ GenAI workflow not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenAIUIServer:
    def __init__(self, port=8080):
        self.port = port
        self.workflow = None
        
        if WORKFLOW_AVAILABLE:
            try:
                self.workflow = DemoGenAIWorkflow()
                logger.info("✅ GenAI workflow initialized")
            except Exception as e:
                logger.warning(f"⚠️ GenAI workflow initialization failed: {e}")
        
        if FLASK_AVAILABLE:
            self.app = Flask(__name__)
            CORS(self.app)
            self.setup_routes()
        else:
            self.app = None

    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Serve the main UI"""
            html_file = Path(__file__).parent / "genai_workflow_ui.html"
            if html_file.exists():
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Inject API endpoint configuration
                api_config = """
                <script>
                    // API Configuration
                    const API_BASE_URL = window.location.origin;
                    
                    // Override the processWorkflow function to use real API
                    async function processWorkflow() {
                        const userInput = document.getElementById('user-input').value.trim();
                        const source = document.getElementById('source-select').value;
                        
                        if (!userInput) {
                            alert('Please enter a support ticket description.');
                            return;
                        }

                        // Show loading and hide results
                        document.getElementById('loading').style.display = 'block';
                        document.getElementById('results-section').style.display = 'none';
                        document.getElementById('process-btn').disabled = true;
                        document.getElementById('alert-banner').classList.remove('show');

                        // Reset workflow steps
                        resetWorkflowSteps();

                        try {
                            // Call real API
                            const response = await fetch(`${API_BASE_URL}/api/process`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    user_input: userInput,
                                    source: source
                                })
                            });
                            
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            
                            const result = await response.json();
                            
                            // Animate workflow steps
                            await animateWorkflowSteps();
                            
                            // Display real results
                            displayRealResults(result);
                            
                        } catch (error) {
                            console.error('API error:', error);
                            // Fall back to simulation
                            await simulateWorkflow(userInput, source);
                        } finally {
                            document.getElementById('loading').style.display = 'none';
                            document.getElementById('process-btn').disabled = false;
                        }
                    }
                    
                    async function animateWorkflowSteps() {
                        const steps = [
                            { id: 1, name: 'Natural Text Input', duration: 300 },
                            { id: 2, name: 'Bedrock + Comprehend Analysis', duration: 800 },
                            { id: 3, name: 'DynamoDB Ticket Storage', duration: 400 },
                            { id: 4, name: 'EventBridge Trigger', duration: 300 },
                            { id: 5, name: 'Lambda Processing', duration: 500 },
                            { id: 6, name: 'SageMaker ML Prediction', duration: 700 },
                            { id: 7, name: 'SNS Alert Decision', duration: 400 },
                            { id: 8, name: 'QuickSight Data Prep', duration: 500 }
                        ];

                        for (let i = 0; i < steps.length; i++) {
                            const step = steps[i];
                            
                            // Update current step
                            document.getElementById('current-step').textContent = `Step ${step.id}: ${step.name}...`;
                            
                            // Activate current step
                            const stepElement = document.getElementById(`step-${step.id}`);
                            stepElement.classList.add('active');
                            
                            // Update progress
                            const progress = ((i + 1) / steps.length) * 100;
                            document.getElementById('progress-fill').style.width = `${progress}%`;
                            
                            // Wait for step duration
                            await new Promise(resolve => setTimeout(resolve, step.duration));
                            
                            // Complete current step
                            stepElement.classList.remove('active');
                            stepElement.classList.add('completed');
                        }
                    }
                    
                    function displayRealResults(apiResult) {
                        if (apiResult.status !== 'SUCCESS') {
                            alert(`Workflow failed: ${apiResult.error || 'Unknown error'}`);
                            return;
                        }
                        
                        const result = apiResult.workflow_result;
                        const ticketData = result.ticket_data || {};
                        const mlPrediction = result.ml_prediction || {};
                        const alertDecision = result.alert_decision || {};
                        const servicesUsed = result.services_used || {};
                        
                        // Update service status
                        updateServiceStatus(servicesUsed);

                        // Update ticket information
                        document.getElementById('ticket-id').textContent = ticketData.ticket_id || 'N/A';
                        document.getElementById('ticket-status').textContent = result.status || 'N/A';
                        document.getElementById('processing-time').textContent = `${apiResult.duration_seconds || 0}s`;
                        document.getElementById('steps-completed').textContent = `${result.steps_completed?.length || 0}/8`;

                        // Update AI classification
                        document.getElementById('department').textContent = ticketData.department || 'N/A';
                        const priorityElement = document.getElementById('priority');
                        priorityElement.textContent = ticketData.priority || 'N/A';
                        priorityElement.className = `result-value priority-${(ticketData.priority || 'p3').toLowerCase()}`;
                        
                        document.getElementById('category').textContent = ticketData.category || 'N/A';
                        document.getElementById('urgency').textContent = `${ticketData.urgency || 0}/10`;
                        
                        const sentimentElement = document.getElementById('sentiment');
                        sentimentElement.textContent = ticketData.sentiment || 'N/A';
                        sentimentElement.className = `result-value sentiment-${ticketData.sentiment || 'neutral'}`;

                        // Update ML prediction
                        const breachProb = mlPrediction.breach_probability || 0;
                        document.getElementById('breach-probability').textContent = `${(breachProb * 100).toFixed(1)}%`;
                        document.getElementById('ml-confidence').textContent = `${((mlPrediction.confidence || 0) * 100).toFixed(1)}%`;
                        document.getElementById('model-used').textContent = mlPrediction.service || 'N/A';
                        
                        const riskElement = document.getElementById('risk-level');
                        const riskLevel = breachProb > 0.7 ? 'High' : breachProb > 0.4 ? 'Medium' : 'Low';
                        riskElement.textContent = riskLevel;
                        riskElement.className = `result-value risk-${riskLevel.toLowerCase()}`;

                        // Update alert decision
                        document.getElementById('alert-needed').textContent = alertDecision.alert_needed ? 'Yes' : 'No';
                        document.getElementById('alert-level').textContent = alertDecision.alert_level || 'none';
                        document.getElementById('alert-channels').textContent = (alertDecision.alert_channels || []).join(', ') || 'None';
                        document.getElementById('escalation-needed').textContent = alertDecision.escalation_needed ? 'Yes' : 'No';

                        // Update recommended actions
                        const actions = alertDecision.recommended_actions || ['Monitor ticket progress', 'Follow standard resolution process'];
                        document.getElementById('recommended-actions').innerHTML = actions.map(action => `<p>• ${action}</p>`).join('');

                        // Show alert banner if high risk
                        if (alertDecision.alert_needed) {
                            document.getElementById('alert-banner').classList.add('show');
                        }

                        // Show results section
                        document.getElementById('results-section').style.display = 'block';
                    }
                </script>
                """
                
                # Insert API configuration before closing body tag
                content = content.replace('</body>', f'{api_config}</body>')
                
                return content
            else:
                return "<h1>GenAI Workflow UI not found</h1><p>Please ensure genai_workflow_ui.html exists.</p>"

        @self.app.route('/api/process', methods=['POST'])
        def process_workflow():
            """API endpoint to process workflow"""
            try:
                data = request.get_json()
                user_input = data.get('user_input', '')
                source = data.get('source', 'web')
                
                if not user_input:
                    return jsonify({'error': 'user_input is required'}), 400
                
                if self.workflow:
                    # Use real GenAI workflow
                    start_time = datetime.now()
                    result = self.workflow.process_complete_workflow(user_input, source)
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    return jsonify({
                        'status': 'SUCCESS',
                        'workflow_result': result,
                        'duration_seconds': duration,
                        'timestamp': datetime.now().isoformat(),
                        'api_version': '1.0'
                    })
                else:
                    # Return mock data if workflow not available
                    return jsonify({
                        'status': 'SUCCESS',
                        'workflow_result': self.generate_mock_result(user_input, source),
                        'duration_seconds': 2.5,
                        'timestamp': datetime.now().isoformat(),
                        'api_version': '1.0',
                        'note': 'Using mock data - GenAI workflow not available'
                    })
                    
            except Exception as e:
                logger.error(f"API error: {e}")
                return jsonify({
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/status')
        def get_status():
            """API endpoint to get system status"""
            return jsonify({
                'status': 'online',
                'workflow_available': WORKFLOW_AVAILABLE,
                'flask_available': FLASK_AVAILABLE,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            })

    def generate_mock_result(self, user_input: str, source: str) -> Dict[str, Any]:
        """Generate mock result when real workflow is not available"""
        text = user_input.lower()
        
        # Simple classification
        department = 'Other'
        if 'aadhaar' in text or 'authentication' in text:
            department = 'UIDAI'
        elif 'payment' in text or 'gateway' in text:
            department = 'MeiTY'
        elif 'portal' in text or 'website' in text:
            department = 'DigitalMP'
        
        priority = 'P3'
        urgency = 5
        if 'critical' in text or 'urgent' in text or 'down' in text:
            priority = 'P1'
            urgency = 9
        elif 'issue' in text or 'problem' in text:
            priority = 'P2'
            urgency = 7
        
        sentiment = 'neutral'
        if 'thank' in text or 'excellent' in text:
            sentiment = 'positive'
        elif 'critical' in text or 'problem' in text:
            sentiment = 'negative'
        
        breach_prob = 0.3
        if priority == 'P1':
            breach_prob = 0.85
        elif priority == 'P2':
            breach_prob = 0.6
        
        return {
            'status': 'SUCCESS',
            'ticket_data': {
                'ticket_id': f'TKT-{datetime.now().strftime("%Y%m%d")}-mock123',
                'department': department,
                'priority': priority,
                'category': 'Other',
                'urgency': urgency,
                'sentiment': sentiment
            },
            'ml_prediction': {
                'breach_probability': breach_prob,
                'confidence': 0.75,
                'service': 'mock_fallback'
            },
            'alert_decision': {
                'alert_needed': breach_prob > 0.7,
                'alert_level': 'high' if breach_prob > 0.7 else 'medium' if breach_prob > 0.5 else 'low',
                'alert_channels': ['email', 'slack'] if breach_prob > 0.7 else ['email'] if breach_prob > 0.5 else [],
                'escalation_needed': breach_prob > 0.8,
                'recommended_actions': [
                    'Monitor ticket progress',
                    'Follow standard resolution process',
                    'Escalate if needed' if breach_prob > 0.7 else 'Continue monitoring'
                ]
            },
            'services_used': {
                'bedrock': False,
                'comprehend': False,
                'sagemaker': False,
                'fallback': True
            },
            'steps_completed': ['natural_language_processing', 'ticket_classification', 'ml_prediction', 'alert_decision']
        }

    def run(self):
        """Run the server"""
        if not FLASK_AVAILABLE:
            print("❌ Flask is required to run the UI server")
            print("   Install with: pip install flask flask-cors")
            return
        
        print("🚀 GenAI Workflow UI Server with Backend Integration")
        print("=" * 60)
        print(f"🌐 Server URL: http://localhost:{self.port}")
        print(f"📊 API Status: http://localhost:{self.port}/api/status")
        print(f"🔧 Workflow Available: {'✅ Yes' if WORKFLOW_AVAILABLE else '❌ No (using mock data)'}")
        print(f"🎯 Features:")
        print(f"   • Interactive GenAI workflow UI")
        print(f"   • Real-time backend integration")
        print(f"   • API endpoints for processing")
        print(f"   • Automatic fallback to mock data")
        print("=" * 60)
        
        try:
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Launch GenAI Workflow UI Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to serve on (default: 8080)')
    
    args = parser.parse_args()
    
    server = GenAIUIServer(port=args.port)
    server.run()

if __name__ == "__main__":
    main()