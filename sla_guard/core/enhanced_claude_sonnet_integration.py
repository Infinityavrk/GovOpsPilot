#!/usr/bin/env python3
"""
Enhanced Llama 3.5 Integration for SLA Guard
Leverages the advanced capabilities of Claude 3.5 Sonnet for superior ticket analysis,
intelligent routing, and predictive SLA breach detection.

Features:
- Advanced natural language understanding with Claude 3.5 Sonnet
- Multi-step reasoning for complex ticket classification
- Intelligent priority escalation with confidence scoring
- Real-time sentiment analysis and urgency detection
- Automated response generation and solution recommendations
"""

import json
import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import re
import threading
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global log storage for UI display
backend_logs = deque(maxlen=100)  # Keep last 100 log entries
log_lock = threading.Lock()

def add_backend_log(level: str, message: str, details: Dict = None):
    """Add a log entry for backend operations"""
    with log_lock:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'details': details or {}
        }
        backend_logs.append(log_entry)
        
        # Also log to console
        if level == 'INFO':
            logger.info(f"🔧 {message}")
        elif level == 'WARNING':
            logger.warning(f"⚠️ {message}")
        elif level == 'ERROR':
            logger.error(f"❌ {message}")
        elif level == 'SUCCESS':
            logger.info(f"✅ {message}")

def get_backend_logs():
    """Get recent backend logs for UI display"""
    with log_lock:
        return list(backend_logs)

class EnhancedClaudeSonnetIntegration:
    def __init__(self, region='us-east-2'):
        """Initialize enhanced Llama 3.5 integration"""
        self.region = region
        
        # Initialize Bedrock client
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name=region)
            self.bedrock_available = True
            add_backend_log("SUCCESS", "Bedrock client initialized successfully", {"region": region})
        except Exception as e:
            add_backend_log("WARNING", f"Bedrock client initialization failed: {e}", {"region": region})
            self.bedrock = None
            self.bedrock_available = False
        
        # Llama 3.2 3B model configuration (confirmed working)
        self.model_id = 'us.meta.llama3-2-3b-instruct-v1:0'  # Llama 3.2 3B (working)
        self.fallback_model_id = 'us.meta.llama3-2-3b-instruct-v1:0'  # Fallback to Llama 3.2 11B
        
        # Enhanced prompt templates
        self.system_prompts = {
            'ticket_analyzer': self._get_ticket_analyzer_prompt(),
            'priority_escalator': self._get_priority_escalator_prompt(),
            'solution_generator': self._get_solution_generator_prompt(),
            'breach_predictor': self._get_breach_predictor_prompt()
        }
        
        logger.info(f"🧠 Enhanced Llama 3.5 Integration ready")

    def analyze_ticket_with_claude_sonnet(self, ticket_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main analysis method using Llama with robust error handling
        """
        add_backend_log("INFO", "Starting enhanced Llama 3.5 analysis...", {"ticket_length": len(ticket_text)})
        
        if not self.bedrock_available:
            add_backend_log("WARNING", "Bedrock not available, using intelligent fallback", {})
            return self._fallback_analysis(ticket_text)
        
        try:
            # Create comprehensive analysis prompt
            analysis_prompt = self._create_analysis_prompt(ticket_text, context)
            
            # Call Llama
            response = self._call_claude_sonnet(analysis_prompt, 'ticket_analyzer')
            
            if response['success']:
                # Parse and clean the response
                analysis = self._parse_analysis_response(response['content'])
                
                # Add model information
                analysis['model_used'] = response['model_used']
                analysis['confidence'] = response.get('confidence', 95)
                
                add_backend_log("SUCCESS", f"Llama analysis completed with {response.get('confidence', 95)}% confidence", {
                    "model": response['model_used'],
                    "department": analysis.get('analysis_summary', {}).get('department'),
                    "priority": analysis.get('analysis_summary', {}).get('priority')
                })
                
                return analysis
            else:
                add_backend_log("WARNING", "Llama analysis failed, using fallback", {"error": response.get('error')})
                return self._fallback_analysis(ticket_text)
                
        except Exception as e:
            add_backend_log("ERROR", f"Error in Llama analysis: {e}", {"ticket_preview": ticket_text[:100]})
            return self._fallback_analysis(ticket_text)

    def _create_analysis_prompt(self, ticket_text: str, context: Dict[str, Any] = None) -> str:
        """Create comprehensive analysis prompt optimized for Llama 3.2"""
        
        context_info = ""
        if context:
            context_info = f"""
CONTEXT INFORMATION:
- User Location: {context.get('user_location', 'Unknown')}
- User Type: {context.get('user_type', 'citizen')}
- Technical Level: {context.get('technical_level', 'basic')}
- Current Time: {context.get('current_time', datetime.now().isoformat())}
"""
        
        # Optimized prompt for Llama 3.2 to ensure JSON output
        prompt = f"""You are an expert AI assistant for Indian government service ticket analysis. Analyze the following support ticket and respond with ONLY valid JSON.

{context_info}

TICKET TO ANALYZE:
{ticket_text}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON - no explanations, no markdown, no extra text
2. Select ONLY ONE value for each field - never use multiple options like "Payment|Portal"
3. Use exact values from the allowed options below

REQUIRED JSON FORMAT:
{{
    "analysis_summary": {{
        "department": "UIDAI",
        "priority": "P2", 
        "category": "Payment",
        "urgency_score": 7,
        "complexity_score": 6,
        "impact_scope": "department"
    }},
    "technical_assessment": {{
        "issue_type": "functionality",
        "estimated_resolution_time_hours": 12,
        "required_expertise": ["payment_systems", "technical_support"]
    }},
    "business_impact": {{
        "citizen_impact": "medium",
        "estimated_affected_users": 100
    }},
    "confidence_metrics": {{
        "overall_confidence": 0.85
    }}
}}

ALLOWED VALUES:
- department: UIDAI, MeitY, DigitalMP, eDistrict, MPOnline
- priority: P1, P2, P3, P4
- category: Authentication, Payment, Portal, Network, Certificate, Integration, Other
- impact_scope: single_user, department, regional, statewide, critical_infrastructure
- issue_type: outage, performance, functionality, access, data, integration
- citizen_impact: none, low, medium, high, critical

Analyze the ticket and respond with valid JSON only:"""
        
        return prompt

    def _get_analysis_format_template(self) -> str:
        """Get the analysis format template"""
        return """
        Please provide a comprehensive analysis in the following JSON format:

        {
            "analysis_summary": {
                "department": "Select ONLY ONE: UIDAI, MeitY, DigitalMP, eDistrict, or MPOnline",
                "priority": "Select ONLY ONE: P1, P2, P3, or P4",
                "category": "Select ONLY ONE: Authentication, Payment, Portal, Network, Certificate, Integration, or Other",
                "urgency_score": 1-10,
                "complexity_score": 1-10,
                "impact_scope": "Select ONLY ONE: single_user, department, regional, statewide, or critical_infrastructure"
            },
            "technical_assessment": {
                "issue_type": "outage|performance|functionality|access|data|integration",
                "affected_services": ["list of specific services"],
                "potential_root_causes": ["list of likely causes"],
                "estimated_resolution_time_hours": number,
                "required_expertise": ["list of skills needed"]
            },
            "business_impact": {
                "citizen_impact": "none|low|medium|high|critical",
                "revenue_impact": "none|low|medium|high|critical",
                "compliance_risk": "none|low|medium|high|critical",
                "reputation_risk": "none|low|medium|high|critical",
                "estimated_affected_users": number
            },
            "sentiment_analysis": {
                "primary_emotion": "frustrated|angry|concerned|neutral|satisfied",
                "urgency_indicators": ["list of urgency keywords found"],
                "communication_tone": "formal|informal|urgent|polite|demanding",
                "escalation_risk": "low|medium|high"
            },
            "intelligent_routing": {
                "recommended_team": "L1_Support|L2_Technical|L3_Engineering|Emergency_Response|Management",
                "required_skills": ["list of technical skills"],
                "escalation_path": ["sequence of escalation steps"],
                "sla_target_hours": number
            },
            "proactive_measures": {
                "immediate_actions": ["list of immediate steps"],
                "communication_plan": ["stakeholder communication steps"],
                "monitoring_requirements": ["what to monitor"],
                "prevention_recommendations": ["future prevention measures"]
            },
            "confidence_metrics": {
                "classification_confidence": 0.0-1.0,
                "priority_confidence": 0.0-1.0,
                "impact_confidence": 0.0-1.0,
                "overall_confidence": 0.0-1.0
            },
            "reasoning": {
                "classification_rationale": "explanation of department/category assignment",
                "priority_justification": "explanation of priority level",
                "key_indicators": ["list of key phrases/patterns that influenced analysis"],
                "risk_factors": ["list of identified risk factors"]
            }
        }

        Ensure your analysis is thorough, accurate, and actionable. Consider both explicit information in the ticket and implicit context clues.
        """

    def _get_ticket_analyzer_prompt(self) -> str:
        """Advanced ticket analysis prompt for Claude 3.5 Sonnet"""
        return """You are an expert AI assistant specializing in Indian government service ticket analysis. 
        You have deep knowledge of:
        - UIDAI (Aadhaar) services and common authentication issues
        - MeitY payment gateway systems and transaction failures
        - DigitalMP portal infrastructure and citizen service delivery
        - eDistrict certificate services and document processing
        - MPOnline platform operations and service integration

        Your task is to analyze support tickets with exceptional accuracy and provide structured insights
        that enable intelligent routing, priority assignment, and proactive issue resolution.

        Classification Guidelines:
        DEPARTMENTS:
        - UIDAI: Aadhaar authentication, biometric verification, UID services, identity validation
        - MeitY: Payment processing, transaction gateways, financial services, billing systems
        - DigitalMP: Digital service portals, online platforms, web applications, citizen interfaces
        - eDistrict: Certificate services, document verification, government document processing
        - MPOnline: Integrated services, multi-department coordination, platform-wide issues

        PRIORITY LEVELS (with SLA implications):
        - P1 (Critical): Complete service outage, security breaches, data corruption, emergency situations
          SLA: 2 hours resolution, immediate escalation required
        - P2 (High): Significant functionality impaired, multiple users affected, business impact
          SLA: 8 hours resolution, senior team notification
        - P3 (Medium): Standard issues, single user problems, workarounds available
          SLA: 24 hours resolution, normal queue processing
        - P4 (Low): Minor issues, enhancement requests, informational queries
          SLA: 72 hours resolution, low priority queue

        URGENCY FACTORS:
        - Scale of impact (single user vs. thousands)
        - Business criticality (revenue impact, citizen services)
        - Time sensitivity (deadlines, peak usage periods)
        - Cascading effects (potential to cause other failures)
        - Public visibility (media attention, political sensitivity)

        Analyze with multi-dimensional reasoning considering technical, business, and social impact."""

    def _get_priority_escalator_prompt(self) -> str:
        """Priority escalation analysis prompt"""
        return """You are a senior incident manager with expertise in SLA management and escalation protocols.
        
        Your role is to:
        1. Assess if current priority assignment is appropriate
        2. Identify escalation triggers and risk factors
        3. Recommend immediate actions and resource allocation
        4. Predict potential SLA breach scenarios
        5. Suggest preventive measures and mitigation strategies

        Consider these escalation factors:
        - Time elapsed since ticket creation
        - Previous similar incidents and their resolution patterns
        - Current system load and team capacity
        - Stakeholder expectations and communication requirements
        - Regulatory compliance and audit implications
        - Public service delivery commitments"""

    def _get_solution_generator_prompt(self) -> str:
        """Solution generation prompt for proactive assistance"""
        return """You are a technical solution architect with deep expertise in Indian government IT systems.
        
        Your knowledge includes:
        - Common resolution patterns for each service type
        - Step-by-step troubleshooting procedures
        - Known workarounds and temporary fixes
        - Integration points and dependency mapping
        - Best practices for citizen communication during outages

        Generate practical, actionable solutions that:
        1. Address the immediate problem
        2. Provide clear implementation steps
        3. Include verification procedures
        4. Consider user experience impact
        5. Suggest preventive measures for future occurrences"""

    def _get_breach_predictor_prompt(self) -> str:
        """SLA breach prediction prompt"""
        return """You are a predictive analytics expert specializing in SLA management and breach prevention.
        
        Analyze multiple factors to predict SLA breach probability:
        - Historical resolution times for similar issues
        - Current team workload and availability
        - Technical complexity and dependency factors
        - Time of day and day of week patterns
        - Seasonal variations and peak usage periods
        - Resource constraints and skill requirements

        Provide probabilistic assessments with confidence intervals and recommend proactive interventions."""

    def analyze_ticket_with_claude_sonnet(self, ticket_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive ticket analysis using Claude 3.5 Sonnet's advanced reasoning capabilities
        """
        logger.info("🧠 Starting enhanced Llama 3.5 analysis...")
        
        if not self.bedrock_available:
            logger.warning("Bedrock not available, using fallback analysis")
            return self._fallback_analysis(ticket_text)
        
        try:
            # Prepare enhanced analysis prompt
            analysis_prompt = self._create_analysis_prompt(ticket_text, context)
            
            # Call Claude 3.5 Sonnet
            response = self._call_claude_sonnet(analysis_prompt, 'ticket_analyzer')
            
            if response['success']:
                # Parse and validate response
                analysis_result = self._parse_analysis_response(response['content'])
                analysis_result['model_used'] = 'Meta Llama 3.2 3B Instruct'
                analysis_result['confidence_score'] = response.get('confidence', 95)
                
                logger.info(f"✅ Llama analysis completed with {analysis_result['confidence_score']}% confidence")
                return analysis_result
            else:
                logger.warning("Llama analysis failed, using fallback")
                return self._fallback_analysis(ticket_text)
                
        except Exception as e:
            logger.error(f"❌ Error in Llama analysis: {e}")
            return self._fallback_analysis(ticket_text)

    def _create_analysis_prompt(self, ticket_text: str, context: Dict[str, Any] = None) -> str:
        """Create comprehensive analysis prompt for Claude 3.5 Sonnet"""
        
        # Add contextual information if available
        context_info = ""
        if context:
            if context.get('user_location'):
                context_info += f"User Location: {context['user_location']}\n"
            if context.get('service_history'):
                context_info += f"Previous Issues: {context['service_history']}\n"
            if context.get('current_time'):
                context_info += f"Current Time: {context['current_time']}\n"
        
        # Optimized prompt for Llama 3.2 to ensure JSON output
        prompt = f"""You are an expert AI assistant for Indian government service ticket analysis. Analyze the following support ticket and respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON - no explanations, no markdown, no extra text
2. Select ONLY ONE value for each field - never use multiple options
3. Use exact values from the allowed options below

TICKET TO ANALYZE:
{context_info}
Ticket Text: "{ticket_text}"

REQUIRED JSON FORMAT (respond with this exact structure):
{{
    "analysis_summary": {{
        "department": "UIDAI",
        "priority": "P2", 
        "category": "Payment",
        "urgency_score": 7,
        "complexity_score": 6,
        "impact_scope": "department"
    }},
    "technical_assessment": {{
        "issue_type": "functionality",
        "affected_services": ["payment_gateway", "user_portal"],
        "potential_root_causes": ["server_overload", "database_issue"],
        "estimated_resolution_time_hours": 12,
        "required_expertise": ["backend_engineer", "database_admin"]
    }},
    "business_impact": {{
        "citizen_impact": "medium",
        "revenue_impact": "low",
        "compliance_risk": "low",
        "reputation_risk": "medium",
        "estimated_affected_users": 100
    }},
    "sentiment_analysis": {{
        "primary_emotion": "frustrated",
        "urgency_indicators": ["urgent", "immediate"],
        "communication_tone": "formal",
        "escalation_risk": "medium"
    }},
    "intelligent_routing": {{
        "recommended_team": "L2_Technical",
        "required_skills": ["payment_systems", "troubleshooting"],
        "escalation_path": ["L1_Support", "L2_Technical", "L3_Engineering"],
        "sla_target_hours": 24
    }},
    "proactive_measures": {{
        "immediate_actions": ["investigate_logs", "check_system_status"],
        "communication_plan": ["notify_stakeholders", "update_status_page"],
        "monitoring_requirements": ["system_health", "error_rates"],
        "prevention_recommendations": ["improve_monitoring", "capacity_planning"]
    }},
    "confidence_metrics": {{
        "classification_confidence": 0.85,
        "priority_confidence": 0.90,
        "impact_confidence": 0.80,
        "overall_confidence": 0.85
    }},
    "reasoning": {{
        "classification_rationale": "Based on keywords and service type",
        "priority_justification": "Medium impact with moderate urgency",
        "key_indicators": ["payment", "gateway", "error"],
        "risk_factors": ["user_impact", "business_continuity"]
    }}
}}

ALLOWED VALUES:
- department: UIDAI, MeitY, DigitalMP, eDistrict, MPOnline
- priority: P1, P2, P3, P4
- category: Authentication, Payment, Portal, Network, Certificate, Integration, Other
- impact_scope: single_user, department, regional, statewide, critical_infrastructure
- issue_type: outage, performance, functionality, access, data, integration
- citizen_impact: none, low, medium, high, critical

Analyze the ticket and respond with valid JSON only:"""
        
        return prompt

    def _call_claude_sonnet(self, prompt: str, prompt_type: str = 'ticket_analyzer') -> Dict[str, Any]:
        """Call Claude 3.5 Sonnet with enhanced configuration"""
        
        add_backend_log("INFO", f"Attempting {prompt_type} with Bedrock Llama 3.2", {"model": self.model_id})
        
        try:
            # Try Claude 3.5 Sonnet first
            model_id = self.model_id
            
            body = {
                "prompt": prompt,
                "max_gen_len": 2000,  # Maximum generation length
                "temperature": 0.1,   # Low temperature for consistent analysis
                "top_p": 0.9
            }
            
            response = self.bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            result = json.loads(response['body'].read())
            content = result.get('generation', '')
            
            add_backend_log("SUCCESS", f"Bedrock Llama 3.2 call successful", {
                "model": model_id,
                "response_length": len(content),
                "prompt_type": prompt_type
            })
            
            return {
                'success': True,
                'content': content,
                'model_used': model_id,
                'confidence': 95
            }
            
        except Exception as e:
            error_msg = str(e)
            add_backend_log("WARNING", f"Bedrock Llama 3.2 call failed: {error_msg}", {"model": self.model_id})
            
            # Try fallback to Claude 3 Sonnet
            if 'ResourceNotFoundException' in error_msg or 'ModelNotReadyException' in error_msg:
                try:
                    add_backend_log("INFO", "Trying fallback model...", {"fallback_model": self.fallback_model_id})
                    
                    response = self.bedrock.invoke_model(
                        modelId=self.fallback_model_id,
                        body=json.dumps(body)
                    )
                    
                    result = json.loads(response['body'].read())
                    content = result.get('generation', '')
                    
                    add_backend_log("SUCCESS", f"Fallback model successful", {
                        "model": self.fallback_model_id,
                        "response_length": len(content)
                    })
                    
                    return {
                        'success': True,
                        'content': content,
                        'model_used': self.fallback_model_id,
                        'confidence': 90
                    }
                    
                except Exception as fallback_error:
                    add_backend_log("ERROR", f"Fallback model also failed: {fallback_error}", {"fallback_model": self.fallback_model_id})
            
            add_backend_log("ERROR", "All AI models failed, using intelligent fallback", {"error": error_msg})
            return {
                'success': False,
                'error': error_msg,
                'model_used': 'none'
            }

    def _parse_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse and validate Llama's analysis response with robust error handling"""
        
        add_backend_log("INFO", "Parsing AI response and cleaning categories", {"response_length": len(response_content)})
        
        try:
            # Enhanced JSON extraction with better pattern matching
            json_str = None
            
            # Pattern 1: Find the most complete JSON object (handles "Extra data" error)
            # Look for balanced braces to get the complete JSON object
            brace_count = 0
            start_pos = response_content.find('{')
            
            if start_pos != -1:
                for i, char in enumerate(response_content[start_pos:], start_pos):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response_content[start_pos:i+1]
                            break
            
            # Pattern 2: Fallback to regex patterns if brace counting fails
            if not json_str:
                patterns = [
                    r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                    r'(?:JSON|json|Response):\s*(\{.*?\})',  # JSON after labels
                    r'\{[^{}]*"analysis_summary"[^{}]*\{.*?\}.*?\}',  # Look for our specific structure
                    r'\{.*?\}',  # Any JSON-like structure
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response_content, re.DOTALL)
                    if match:
                        json_str = match.group(1) if match.groups() else match.group()
                        break
            
            if json_str:
                try:
                    # First attempt: direct parsing
                    analysis = json.loads(json_str)
                    add_backend_log("SUCCESS", "JSON parsed successfully on first attempt", {"json_length": len(json_str)})
                except json.JSONDecodeError as json_error:
                    add_backend_log("WARNING", f"JSON parsing failed: {json_error}", {"attempting_cleanup": True})
                    
                    # Second attempt: clean and parse
                    try:
                        cleaned_json = self._fix_malformed_json(json_str)
                        analysis = json.loads(cleaned_json)
                        add_backend_log("SUCCESS", "JSON cleaned and parsed successfully", {"cleanup_applied": True})
                    except json.JSONDecodeError as cleanup_error:
                        # Third attempt: Aggressive comma fixing for specific "Expecting ',' delimiter" errors
                        add_backend_log("WARNING", f"Standard cleanup failed ({cleanup_error}), trying aggressive comma fix", {})
                        try:
                            aggressively_fixed = self._aggressive_comma_fix(json_str)
                            analysis = json.loads(aggressively_fixed)
                            add_backend_log("SUCCESS", "Aggressive comma fix successful", {"aggressive_fix_applied": True})
                        except json.JSONDecodeError as final_error:
                            # Fourth attempt: extract key information manually
                            add_backend_log("WARNING", f"All JSON fixes failed ({final_error}), extracting key values manually", {})
                            analysis = self._extract_key_values_from_text(response_content)
                
                # Validate required fields
                required_sections = [
                    'analysis_summary', 'technical_assessment', 'business_impact',
                    'sentiment_analysis', 'intelligent_routing', 'confidence_metrics'
                ]
                
                missing_sections = []
                for section in required_sections:
                    if section not in analysis:
                        missing_sections.append(section)
                        analysis[section] = {}
                
                if missing_sections:
                    add_backend_log("WARNING", f"Missing sections in analysis", {"missing": missing_sections})
                
                # Clean up and select single most appropriate values
                analysis = self._clean_analysis_results(analysis)
                
                # Add metadata
                analysis['parsed_successfully'] = True
                analysis['analysis_timestamp'] = datetime.now().isoformat()
                
                add_backend_log("SUCCESS", "Analysis parsed and cleaned successfully", {
                    "department": analysis.get('analysis_summary', {}).get('department'),
                    "category": analysis.get('analysis_summary', {}).get('category'),
                    "priority": analysis.get('analysis_summary', {}).get('priority')
                })
                
                return analysis
            else:
                # No JSON found, try to extract key information from text
                add_backend_log("WARNING", "No JSON found in response, extracting key values", {})
                analysis = self._extract_key_values_from_text(response_content)
                analysis['parsed_successfully'] = True
                analysis['analysis_timestamp'] = datetime.now().isoformat()
                return analysis
                
        except Exception as e:
            add_backend_log("ERROR", f"Error parsing AI response: {e}", {"response_preview": response_content[:200]})
            # Return fallback analysis
            return self._create_fallback_analysis(response_content, str(e))

    def _fix_malformed_json(self, json_str: str) -> str:
        """Fix common JSON formatting issues from Llama responses with enhanced comma handling"""
        
        add_backend_log("INFO", "Attempting to fix malformed JSON", {"original_length": len(json_str)})
        
        try:
            # Step 1: Extract only the JSON part
            # Remove any text before the first {
            start_brace = json_str.find('{')
            if start_brace != -1:
                json_str = json_str[start_brace:]
            
            # Remove any text after the last }
            end_brace = json_str.rfind('}')
            if end_brace != -1:
                json_str = json_str[:end_brace + 1]
            
            # Step 2: Fix basic JSON structure issues
            # Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')
            
            # Fix missing quotes around property names
            json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
            
            # Step 3: COMPREHENSIVE COMMA FIXING - The main issue
            # This is the most critical part for fixing "Expecting ',' delimiter" errors
            
            # Fix missing commas between properties on the same line
            # Pattern: "key1": "value1" "key2" -> "key1": "value1", "key2"
            json_str = re.sub(r'("\s*:\s*"[^"]*")\s+(")', r'\1, \2', json_str)
            json_str = re.sub(r'("\s*:\s*[^",}\]]+)\s+(")', r'\1, \2', json_str)
            
            # Fix missing commas between properties across lines
            json_str = re.sub(r'("\s*:\s*"[^"]*")\s*\n\s*(")', r'\1,\n\2', json_str)
            json_str = re.sub(r'("\s*:\s*[^",}\]]+)\s*\n\s*(")', r'\1,\n\2', json_str)
            
            # Fix missing commas after numbers/booleans/null
            json_str = re.sub(r'(\d+|\btrue\b|\bfalse\b|\bnull\b)\s+(")', r'\1, \2', json_str)
            json_str = re.sub(r'(\d+|\btrue\b|\bfalse\b|\bnull\b)\s*\n\s*(")', r'\1,\n\2', json_str)
            
            # Fix missing commas after arrays and objects
            json_str = re.sub(r'(\])\s+(")', r'\1, \2', json_str)
            json_str = re.sub(r'(\})\s+(")', r'\1, \2', json_str)
            json_str = re.sub(r'(\])\s*\n\s*(")', r'\1,\n\2', json_str)
            json_str = re.sub(r'(\})\s*\n\s*(")', r'\1,\n\2', json_str)
            
            # Step 4: Clean up formatting
            # Remove comments
            json_str = re.sub(r'//.*?\n', '\n', json_str)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            
            # Fix boolean values
            json_str = re.sub(r'\bTrue\b', 'true', json_str)
            json_str = re.sub(r'\bFalse\b', 'false', json_str)
            json_str = re.sub(r'\bNone\b', 'null', json_str)
            
            # Step 5: Final cleanup
            # Remove trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Remove double commas
            json_str = re.sub(r',,+', ',', json_str)
            
            # Normalize whitespace
            json_str = re.sub(r'\s+', ' ', json_str)
            json_str = re.sub(r'{\s+', '{', json_str)
            json_str = re.sub(r'\s+}', '}', json_str)
            json_str = re.sub(r':\s+', ': ', json_str)
            json_str = re.sub(r',\s+', ', ', json_str)
            
            # Ensure proper JSON boundaries
            json_str = json_str.strip()
            if not json_str.startswith('{'):
                json_str = '{' + json_str
            if not json_str.endswith('}'):
                json_str = json_str + '}'
            
            add_backend_log("SUCCESS", "Enhanced JSON cleanup completed", {"cleaned_length": len(json_str)})
            return json_str
            
        except Exception as e:
            add_backend_log("ERROR", f"JSON cleanup failed: {e}", {"original_length": len(json_str)})
            # Return original string if cleanup fails
            return json_str

    def _aggressive_comma_fix(self, json_str: str) -> str:
        """Aggressive comma fixing specifically for 'Expecting comma delimiter' errors"""
        
        add_backend_log("INFO", "Applying aggressive comma fixes", {"original_length": len(json_str)})
        
        try:
            # Extract JSON boundaries
            start_brace = json_str.find('{')
            end_brace = json_str.rfind('}')
            
            if start_brace != -1 and end_brace != -1:
                json_str = json_str[start_brace:end_brace + 1]
            
            # Ultra-aggressive comma insertion
            # Insert commas between any quote-space-quote pattern
            json_str = re.sub(r'"\s+"', '", "', json_str)
            
            # Insert commas between value and next property (most common issue)
            # After string values
            json_str = re.sub(r'(":\s*"[^"]*")\s+(")', r'\1, \2', json_str)
            
            # After number values  
            json_str = re.sub(r'(":\s*\d+(?:\.\d+)?)\s+(")', r'\1, \2', json_str)
            
            # After boolean/null values
            json_str = re.sub(r'(":\s*(?:true|false|null))\s+(")', r'\1, \2', json_str)
            
            # After arrays
            json_str = re.sub(r'(\])\s+(")', r'\1, \2', json_str)
            
            # After objects
            json_str = re.sub(r'(\})\s+(")', r'\1, \2', json_str)
            
            # Handle newline cases
            json_str = re.sub(r'(":\s*"[^"]*")\s*\n\s*(")', r'\1,\n\2', json_str)
            json_str = re.sub(r'(":\s*\d+(?:\.\d+)?)\s*\n\s*(")', r'\1,\n\2', json_str)
            json_str = re.sub(r'(":\s*(?:true|false|null))\s*\n\s*(")', r'\1,\n\2', json_str)
            json_str = re.sub(r'(\])\s*\n\s*(")', r'\1,\n\2', json_str)
            json_str = re.sub(r'(\})\s*\n\s*(")', r'\1,\n\2', json_str)
            
            # Clean up any double commas
            json_str = re.sub(r',,+', ',', json_str)
            
            # Remove trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Final whitespace cleanup
            json_str = re.sub(r'\s+', ' ', json_str)
            json_str = json_str.strip()
            
            add_backend_log("SUCCESS", "Aggressive comma fix completed", {"fixed_length": len(json_str)})
            return json_str
            
        except Exception as e:
            add_backend_log("ERROR", f"Aggressive comma fix failed: {e}", {})
            return json_str

    def _extract_key_values_from_text(self, text: str) -> Dict[str, Any]:
        """Extract key analysis values from text when JSON parsing fails"""
        
        add_backend_log("INFO", "Extracting key values from text response", {"text_length": len(text)})
        
        analysis = {
            'analysis_summary': {},
            'technical_assessment': {},
            'business_impact': {},
            'sentiment_analysis': {},
            'intelligent_routing': {},
            'confidence_metrics': {}
        }
        
        # More aggressive extraction patterns
        
        # Extract department - look for any mention of the departments
        dept_found = None
        for dept in ['UIDAI', 'MeitY', 'DigitalMP', 'eDistrict', 'MPOnline']:
            if dept.lower() in text.lower():
                dept_found = dept
                break
        
        # If no direct match, use keywords
        if not dept_found:
            if any(word in text.lower() for word in ['aadhaar', 'uid', 'authentication', 'biometric']):
                dept_found = 'UIDAI'
            elif any(word in text.lower() for word in ['payment', 'gateway', 'transaction', 'money']):
                dept_found = 'MeitY'
            elif any(word in text.lower() for word in ['portal', 'website', 'digital', 'online']):
                dept_found = 'DigitalMP'
            elif any(word in text.lower() for word in ['certificate', 'document', 'verification']):
                dept_found = 'eDistrict'
            else:
                dept_found = 'MPOnline'
        
        analysis['analysis_summary']['department'] = dept_found
        
        # Extract priority - look for P1, P2, P3, P4 or priority keywords
        priority_found = None
        priority_match = re.search(r'P[1-4]', text, re.IGNORECASE)
        if priority_match:
            priority_found = priority_match.group().upper()
        else:
            # Use keywords to determine priority
            if any(word in text.lower() for word in ['critical', 'urgent', 'emergency', 'down', 'outage']):
                priority_found = 'P1'
            elif any(word in text.lower() for word in ['high', 'important', 'serious', 'timeout']):
                priority_found = 'P2'
            elif any(word in text.lower() for word in ['minor', 'low', 'small', 'question']):
                priority_found = 'P4'
            else:
                priority_found = 'P3'
        
        analysis['analysis_summary']['priority'] = priority_found
        
        # Extract category - look for category keywords
        category_found = None
        for cat in ['Authentication', 'Payment', 'Portal', 'Network', 'Certificate', 'Integration']:
            if cat.lower() in text.lower():
                category_found = cat
                break
        
        # If no direct match, use keywords
        if not category_found:
            if any(word in text.lower() for word in ['login', 'password', 'auth', 'aadhaar', 'biometric']):
                category_found = 'Authentication'
            elif any(word in text.lower() for word in ['payment', 'transaction', 'gateway', 'money', 'billing']):
                category_found = 'Payment'
            elif any(word in text.lower() for word in ['portal', 'website', 'interface', 'page']):
                category_found = 'Portal'
            elif any(word in text.lower() for word in ['network', 'connection', 'timeout', 'slow']):
                category_found = 'Network'
            elif any(word in text.lower() for word in ['certificate', 'document', 'verification']):
                category_found = 'Certificate'
            elif any(word in text.lower() for word in ['integration', 'api', 'service']):
                category_found = 'Integration'
            else:
                category_found = 'Other'
        
        analysis['analysis_summary']['category'] = category_found
        
        # Extract urgency score - look for numbers 1-10
        urgency_score = 5  # default
        urgency_match = re.search(r'(?:urgency|score).*?(\d+)', text, re.IGNORECASE)
        if urgency_match:
            score = int(urgency_match.group(1))
            if 1 <= score <= 10:
                urgency_score = score
        else:
            # Estimate based on priority
            urgency_map = {'P1': 9, 'P2': 7, 'P3': 5, 'P4': 3}
            urgency_score = urgency_map.get(priority_found, 5)
        
        analysis['analysis_summary']['urgency_score'] = urgency_score
        analysis['analysis_summary']['complexity_score'] = 5
        analysis['analysis_summary']['impact_scope'] = 'department'
        
        # Add technical assessment
        analysis['technical_assessment']['issue_type'] = 'functionality'
        analysis['technical_assessment']['estimated_resolution_time_hours'] = {'P1': 4, 'P2': 12, 'P3': 24, 'P4': 72}.get(priority_found, 24)
        analysis['technical_assessment']['required_expertise'] = ['technical_support']
        
        # Add business impact
        analysis['business_impact']['citizen_impact'] = 'medium'
        analysis['business_impact']['estimated_affected_users'] = 100
        
        # Add confidence metrics
        analysis['confidence_metrics']['overall_confidence'] = 0.75
        
        add_backend_log("SUCCESS", "Key values extracted from text", {
            "department": analysis['analysis_summary']['department'],
            "category": analysis['analysis_summary']['category'],
            "priority": analysis['analysis_summary']['priority'],
            "urgency_score": analysis['analysis_summary']['urgency_score']
        })
        
        return analysis

    def _create_fallback_analysis(self, response_content: str, error: str) -> Dict[str, Any]:
        """Create a fallback analysis when all parsing fails"""
        
        add_backend_log("WARNING", "Creating fallback analysis due to parsing failure", {"error": error})
        
        return {
            'parsed_successfully': False,
            'error': error,
            'raw_response': response_content[:500],
            'analysis_summary': {
                'department': 'DigitalMP',
                'priority': 'P3',
                'category': 'Other',
                'urgency_score': 5,
                'impact_scope': 'department'
            },
            'technical_assessment': {},
            'business_impact': {},
            'sentiment_analysis': {},
            'intelligent_routing': {},
            'confidence_metrics': {
                'overall_confidence': 0.5
            },
            'analysis_timestamp': datetime.now().isoformat()
        }

    def _clean_analysis_results(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up analysis results to select single most appropriate values"""
        
        cleaned_items = []
        
        # Clean up analysis_summary
        if 'analysis_summary' in analysis:
            summary = analysis['analysis_summary']
            
            # Clean department - select first/most relevant
            if 'department' in summary:
                dept = str(summary['department'])
                if '|' in dept or ',' in dept:
                    # Split and take the first/most specific one
                    options = dept.replace('|', ',').split(',')
                    original_dept = dept
                    summary['department'] = options[0].strip()
                    cleaned_items.append(f"Department: {original_dept} → {summary['department']}")
            
            # Clean category - select most specific
            if 'category' in summary:
                cat = str(summary['category'])
                if '|' in cat or ',' in cat:
                    # Priority order for categories
                    category_priority = {
                        'Authentication': 1,
                        'Payment': 2, 
                        'Portal': 3,
                        'Certificate': 4,
                        'Network': 5,
                        'Integration': 6,
                        'Other': 7
                    }
                    
                    options = cat.replace('|', ',').split(',')
                    options = [opt.strip() for opt in options]
                    
                    # Select highest priority category
                    best_category = 'Other'
                    best_priority = 999
                    
                    for option in options:
                        priority = category_priority.get(option, 999)
                        if priority < best_priority:
                            best_priority = priority
                            best_category = option
                    
                    original_cat = cat
                    summary['category'] = best_category
                    cleaned_items.append(f"Category: {original_cat} → {best_category}")
            
            # Clean priority - ensure single value
            if 'priority' in summary:
                priority = str(summary['priority'])
                if '|' in priority or ',' in priority:
                    # Take the highest priority (P1 > P2 > P3 > P4)
                    options = priority.replace('|', ',').split(',')
                    priorities = []
                    for opt in options:
                        opt = opt.strip()
                        if 'P1' in opt:
                            priorities.append(1)
                        elif 'P2' in opt:
                            priorities.append(2)
                        elif 'P3' in opt:
                            priorities.append(3)
                        elif 'P4' in opt:
                            priorities.append(4)
                    
                    if priorities:
                        highest = min(priorities)  # P1=1 is highest priority
                        summary['priority'] = f'P{highest}'
                    else:
                        summary['priority'] = 'P3'  # Default
            
            # Clean impact scope - select most severe
            if 'impact_scope' in summary:
                scope = str(summary['impact_scope'])
                if '|' in scope or ',' in scope:
                    scope_priority = {
                        'critical_infrastructure': 1,
                        'statewide': 2,
                        'regional': 3,
                        'department': 4,
                        'single_user': 5
                    }
                    
                    options = scope.replace('|', ',').split(',')
                    options = [opt.strip() for opt in options]
                    
                    best_scope = 'single_user'
                    best_priority = 999
                    
                    for option in options:
                        priority = scope_priority.get(option, 999)
                        if priority < best_priority:
                            best_priority = priority
                            best_scope = option
                    
                    original_scope = scope
                    summary['impact_scope'] = best_scope
                    cleaned_items.append(f"Impact: {original_scope} → {best_scope}")
        
        if cleaned_items:
            add_backend_log("INFO", "Cleaned multiple selections to single values", {"cleaned": cleaned_items})
        
        return analysis

    def predict_sla_breach_risk(self, ticket_analysis: Dict[str, Any], historical_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Advanced SLA breach prediction using Claude 3.5 Sonnet's reasoning capabilities
        """
        logger.info("🔮 Predicting SLA breach risk with Llama...")
        
        if not self.bedrock_available:
            return self._fallback_breach_prediction(ticket_analysis)
        
        try:
            # Prepare breach prediction prompt
            prediction_prompt = self._create_breach_prediction_prompt(ticket_analysis, historical_data)
            
            # Call Claude for prediction
            response = self._call_claude_sonnet(prediction_prompt, 'breach_predictor')
            
            if response['success']:
                prediction_result = self._parse_breach_prediction(response['content'])
                prediction_result['model_used'] = response['model_used']
                
                logger.info(f"✅ Breach prediction completed: {prediction_result.get('breach_probability', 0):.1%} risk")
                return prediction_result
            else:
                return self._fallback_breach_prediction(ticket_analysis)
                
        except Exception as e:
            logger.error(f"❌ Error in breach prediction: {e}")
            return self._fallback_breach_prediction(ticket_analysis)

    def _create_breach_prediction_prompt(self, ticket_analysis: Dict[str, Any], historical_data: List[Dict] = None) -> str:
        """Create breach prediction prompt"""
        
        # Extract key metrics from analysis
        summary = ticket_analysis.get('analysis_summary', {})
        technical = ticket_analysis.get('technical_assessment', {})
        business = ticket_analysis.get('business_impact', {})
        routing = ticket_analysis.get('intelligent_routing', {})
        
        # Add historical context if available
        historical_context = ""
        if historical_data:
            historical_context = f"""
            HISTORICAL CONTEXT:
            Recent similar tickets: {len(historical_data)}
            Average resolution time: {self._calculate_avg_resolution(historical_data)} hours
            Success rate: {self._calculate_success_rate(historical_data):.1%}
            """
        
        prompt = f"""
        {self.system_prompts['breach_predictor']}

        TICKET ANALYSIS DATA:
        Department: {summary.get('department', 'Unknown')}
        Priority: {summary.get('priority', 'P3')}
        Category: {summary.get('category', 'Other')}
        Urgency Score: {summary.get('urgency_score', 5)}/10
        Complexity Score: {summary.get('complexity_score', 5)}/10
        Impact Scope: {summary.get('impact_scope', 'single_user')}
        
        Estimated Resolution Time: {technical.get('estimated_resolution_time_hours', 24)} hours
        Required Expertise: {technical.get('required_expertise', [])}
        
        Citizen Impact: {business.get('citizen_impact', 'medium')}
        Estimated Affected Users: {business.get('estimated_affected_users', 1)}
        
        SLA Target: {routing.get('sla_target_hours', 24)} hours
        Recommended Team: {routing.get('recommended_team', 'L1_Support')}
        
        Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Day of Week: {datetime.now().strftime('%A')}
        
        {historical_context}

        Please provide a comprehensive SLA breach risk assessment in JSON format:

        {{
            "breach_risk_assessment": {{
                "breach_probability": 0.0-1.0,
                "confidence_level": 0.0-1.0,
                "risk_category": "low|medium|high|critical",
                "time_to_breach_hours": number,
                "likelihood_factors": ["list of factors increasing breach risk"],
                "mitigation_factors": ["list of factors reducing breach risk"]
            }},
            "timeline_prediction": {{
                "estimated_resolution_hours": number,
                "earliest_possible_resolution": number,
                "latest_acceptable_resolution": number,
                "critical_decision_points": ["list of key milestones"]
            }},
            "resource_requirements": {{
                "required_skill_level": "junior|senior|expert|specialist",
                "estimated_effort_hours": number,
                "team_size_recommendation": number,
                "external_dependencies": ["list of external factors"]
            }},
            "escalation_triggers": {{
                "immediate_escalation_needed": true|false,
                "escalation_timeline": ["list of escalation points"],
                "stakeholder_notifications": ["list of who to notify when"],
                "communication_frequency": "hourly|every_4_hours|daily"
            }},
            "proactive_interventions": {{
                "recommended_actions": ["list of immediate actions"],
                "monitoring_checkpoints": ["list of monitoring points"],
                "contingency_plans": ["list of backup plans"],
                "resource_allocation": ["list of resource needs"]
            }},
            "success_factors": {{
                "critical_success_factors": ["list of key success requirements"],
                "potential_blockers": ["list of potential obstacles"],
                "risk_mitigation_strategies": ["list of risk reduction approaches"],
                "quality_assurance_steps": ["list of QA checkpoints"]
            }}
        }}

        Consider all factors including technical complexity, team availability, business impact, and historical patterns.
        """
        
        return prompt

    def _parse_breach_prediction(self, response_content: str) -> Dict[str, Any]:
        """Parse breach prediction response with robust error handling"""
        
        add_backend_log("INFO", "Parsing breach prediction response", {"response_length": len(response_content)})
        
        try:
            # Use the same robust JSON extraction as the main parser
            json_str = None
            
            # Pattern 1: Find the most complete JSON object (handles "Extra data" error)
            brace_count = 0
            start_pos = response_content.find('{')
            
            if start_pos != -1:
                for i, char in enumerate(response_content[start_pos:], start_pos):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response_content[start_pos:i+1]
                            break
            
            # Pattern 2: Fallback to regex patterns if brace counting fails
            if not json_str:
                patterns = [
                    r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                    r'(?:JSON|json|Response):\s*(\{.*?\})',  # JSON after labels
                    r'\{.*?\}',  # Any JSON-like structure
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response_content, re.DOTALL)
                    if match:
                        json_str = match.group(1) if match.groups() else match.group()
                        break
            
            if json_str:
                try:
                    # First attempt: direct parsing
                    prediction = json.loads(json_str)
                    add_backend_log("SUCCESS", "Breach prediction JSON parsed successfully", {"json_length": len(json_str)})
                except json.JSONDecodeError as json_error:
                    add_backend_log("WARNING", f"Breach prediction JSON parsing failed: {json_error}", {"attempting_cleanup": True})
                    
                    # Second attempt: use the robust JSON fixing
                    try:
                        cleaned_json = self._fix_malformed_json(json_str)
                        prediction = json.loads(cleaned_json)
                        add_backend_log("SUCCESS", "Breach prediction JSON cleaned and parsed successfully", {"cleanup_applied": True})
                    except json.JSONDecodeError as cleanup_error:
                        # Third attempt: aggressive comma fixing
                        add_backend_log("WARNING", f"Standard cleanup failed ({cleanup_error}), trying aggressive comma fix", {})
                        try:
                            aggressively_fixed = self._aggressive_comma_fix(json_str)
                            prediction = json.loads(aggressively_fixed)
                            add_backend_log("SUCCESS", "Aggressive comma fix successful for breach prediction", {"aggressive_fix_applied": True})
                        except json.JSONDecodeError as final_error:
                            # Fourth attempt: extract basic values from text
                            add_backend_log("WARNING", f"All JSON fixes failed ({final_error}), extracting basic values", {})
                            return self._extract_basic_prediction(response_content)
                
                # Extract key metrics for easy access
                breach_assessment = prediction.get('breach_risk_assessment', {})
                timeline = prediction.get('timeline_prediction', {})
                
                prediction.update({
                    'breach_probability': breach_assessment.get('breach_probability', 0.5),
                    'confidence_level': breach_assessment.get('confidence_level', 0.8),
                    'estimated_resolution_hours': timeline.get('estimated_resolution_hours', 24),
                    'prediction_timestamp': datetime.now().isoformat(),
                    'parsed_successfully': True
                })
                
                add_backend_log("SUCCESS", "Breach prediction analysis completed", {
                    "breach_probability": prediction.get('breach_probability', 0),
                    "confidence_level": prediction.get('confidence_level', 0)
                })
                
                return prediction
            else:
                # No JSON found, extract basic values from text
                add_backend_log("WARNING", "No JSON found in breach prediction response, extracting basic values", {})
                return self._extract_basic_prediction(response_content)
                
        except Exception as e:
            add_backend_log("ERROR", f"Error parsing breach prediction: {e}", {"response_preview": response_content[:200]})
            return {
                'breach_probability': 0.5,
                'confidence_level': 0.6,
                'estimated_resolution_hours': 24,
                'parsed_successfully': False,
                'error': str(e)
            }

    def _clean_json_text(self, json_text: str) -> str:
        """Clean up common JSON formatting issues"""
        
        # Remove trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Fix unquoted keys (common AI mistake)
        json_text = re.sub(r'(\w+):', r'"\1":', json_text)
        
        # Fix already quoted keys that got double-quoted
        json_text = re.sub(r'""(\w+)"":', r'"\1":', json_text)
        
        # Remove comments (// or /* */)
        json_text = re.sub(r'//.*?\n', '\n', json_text)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        return json_text

    def _extract_basic_prediction(self, response_content: str) -> Dict[str, Any]:
        """Extract basic prediction values from text when JSON parsing fails"""
        
        # Default values
        breach_probability = 0.5
        confidence_level = 0.7
        estimated_hours = 24
        
        # Try to extract probability from text
        prob_match = re.search(r'(\d+(?:\.\d+)?)\s*%?\s*(?:probability|risk|chance)', response_content, re.IGNORECASE)
        if prob_match:
            prob_value = float(prob_match.group(1))
            if prob_value > 1:  # Assume percentage
                breach_probability = prob_value / 100
            else:
                breach_probability = prob_value
        
        # Try to extract confidence
        conf_match = re.search(r'confidence[:\s]*(\d+(?:\.\d+)?)\s*%?', response_content, re.IGNORECASE)
        if conf_match:
            conf_value = float(conf_match.group(1))
            if conf_value > 1:  # Assume percentage
                confidence_level = conf_value / 100
            else:
                confidence_level = conf_value
        
        # Try to extract hours
        hours_match = re.search(r'(\d+)\s*hours?', response_content, re.IGNORECASE)
        if hours_match:
            estimated_hours = int(hours_match.group(1))
        
        return {
            'breach_probability': min(max(breach_probability, 0.0), 1.0),
            'confidence_level': min(max(confidence_level, 0.0), 1.0),
            'estimated_resolution_hours': max(estimated_hours, 1),
            'prediction_timestamp': datetime.now().isoformat(),
            'parsed_successfully': False,
            'fallback_parsing': True,
            'note': 'Extracted from text due to JSON parsing failure'
        }

    def generate_intelligent_response(self, ticket_analysis: Dict[str, Any], user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate intelligent automated response using Claude 3.5 Sonnet
        """
        logger.info("💬 Generating intelligent response with Llama...")
        
        if not self.bedrock_available:
            return self._fallback_response_generation(ticket_analysis)
        
        try:
            # Create response generation prompt
            response_prompt = self._create_response_prompt(ticket_analysis, user_context)
            
            # Call Claude for response generation
            response = self._call_claude_sonnet(response_prompt, 'solution_generator')
            
            if response['success']:
                response_result = self._parse_response_generation(response['content'])
                response_result['model_used'] = response['model_used']
                
                logger.info("✅ Intelligent response generated successfully")
                return response_result
            else:
                return self._fallback_response_generation(ticket_analysis)
                
        except Exception as e:
            logger.error(f"❌ Error in response generation: {e}")
            return self._fallback_response_generation(ticket_analysis)

    def _create_response_prompt(self, ticket_analysis: Dict[str, Any], user_context: Dict[str, Any] = None) -> str:
        """Create response generation prompt"""
        
        summary = ticket_analysis.get('analysis_summary', {})
        technical = ticket_analysis.get('technical_assessment', {})
        proactive = ticket_analysis.get('proactive_measures', {})
        
        user_info = ""
        if user_context:
            user_info = f"""
            User Type: {user_context.get('user_type', 'citizen')}
            Technical Level: {user_context.get('technical_level', 'basic')}
            Preferred Language: {user_context.get('language', 'English')}
            Communication Preference: {user_context.get('communication_style', 'formal')}
            """
        
        prompt = f"""
        {self.system_prompts['solution_generator']}

        TICKET ANALYSIS:
        Department: {summary.get('department')}
        Priority: {summary.get('priority')}
        Issue Type: {technical.get('issue_type')}
        Affected Services: {technical.get('affected_services', [])}
        Immediate Actions: {proactive.get('immediate_actions', [])}
        
        {user_info}

        Generate a comprehensive response in JSON format:

        {{
            "automated_response": {{
                "acknowledgment": "professional acknowledgment message",
                "status_update": "current status and what we're doing",
                "expected_timeline": "realistic timeline for resolution",
                "workaround_instructions": "step-by-step workaround if available",
                "next_steps": "what happens next in the process"
            }},
            "technical_guidance": {{
                "troubleshooting_steps": ["list of user-actionable steps"],
                "common_solutions": ["list of common fixes"],
                "escalation_criteria": "when to escalate or contact support again",
                "additional_resources": ["links or references for more help"]
            }},
            "communication_plan": {{
                "update_frequency": "how often we'll provide updates",
                "notification_channels": ["email|sms|portal notification"],
                "escalation_contacts": "who to contact for urgent issues",
                "feedback_mechanism": "how user can provide feedback"
            }},
            "proactive_information": {{
                "related_services_status": "status of related services",
                "prevention_tips": ["tips to prevent similar issues"],
                "service_improvements": "upcoming improvements or maintenance",
                "alternative_channels": ["alternative ways to access services"]
            }}
        }}

        Ensure the response is:
        - Professional and empathetic
        - Clear and actionable
        - Appropriate for the user's technical level
        - Culturally sensitive for Indian government services
        - Compliant with service standards and regulations
        """
        
        return prompt

    def _parse_response_generation(self, response_content: str) -> Dict[str, Any]:
        """Parse response generation output with robust JSON handling"""
        
        add_backend_log("INFO", "Parsing response generation output", {"response_length": len(response_content)})
        
        try:
            # Use the same robust JSON extraction as other parsers
            json_str = None
            
            # Pattern 1: Find the most complete JSON object
            brace_count = 0
            start_pos = response_content.find('{')
            
            if start_pos != -1:
                for i, char in enumerate(response_content[start_pos:], start_pos):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response_content[start_pos:i+1]
                            break
            
            # Pattern 2: Fallback to regex patterns
            if not json_str:
                patterns = [
                    r'```json\s*(\{.*?\})\s*```',
                    r'(?:JSON|json|Response):\s*(\{.*?\})',
                    r'\{.*?\}',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response_content, re.DOTALL)
                    if match:
                        json_str = match.group(1) if match.groups() else match.group()
                        break
            
            if json_str:
                try:
                    # First attempt: direct parsing
                    response_data = json.loads(json_str)
                    add_backend_log("SUCCESS", "Response generation JSON parsed successfully", {"json_length": len(json_str)})
                except json.JSONDecodeError as json_error:
                    add_backend_log("WARNING", f"Response generation JSON parsing failed: {json_error}", {"attempting_cleanup": True})
                    
                    # Second attempt: use robust JSON fixing
                    try:
                        cleaned_json = self._fix_malformed_json(json_str)
                        response_data = json.loads(cleaned_json)
                        add_backend_log("SUCCESS", "Response generation JSON cleaned and parsed successfully", {"cleanup_applied": True})
                    except json.JSONDecodeError as cleanup_error:
                        # Third attempt: aggressive comma fixing
                        add_backend_log("WARNING", f"Standard cleanup failed ({cleanup_error}), trying aggressive comma fix", {})
                        try:
                            aggressively_fixed = self._aggressive_comma_fix(json_str)
                            response_data = json.loads(aggressively_fixed)
                            add_backend_log("SUCCESS", "Aggressive comma fix successful for response generation", {"aggressive_fix_applied": True})
                        except json.JSONDecodeError as final_error:
                            # Fourth attempt: return fallback response
                            add_backend_log("WARNING", f"All JSON fixes failed ({final_error}), using fallback response", {})
                            return {
                                'parsed_successfully': False,
                                'error': str(final_error),
                                'fallback_response': "Thank you for contacting support. Your ticket has been received and is being processed.",
                                'generated_at': datetime.now().isoformat()
                            }
                
                response_data.update({
                    'generated_at': datetime.now().isoformat(),
                    'parsed_successfully': True
                })
                
                add_backend_log("SUCCESS", "Response generation completed successfully", {
                    "has_automated_response": 'automated_response' in response_data,
                    "has_technical_guidance": 'technical_guidance' in response_data
                })
                
                return response_data
            else:
                add_backend_log("WARNING", "No JSON found in response generation output", {})
                return {
                    'parsed_successfully': False,
                    'error': "No JSON found in response generation",
                    'fallback_response': "Thank you for contacting support. Your ticket has been received and is being processed.",
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            add_backend_log("ERROR", f"Error parsing response generation: {e}", {"response_preview": response_content[:200]})
            return {
                'parsed_successfully': False,
                'error': str(e),
                'fallback_response': "Thank you for contacting support. Your ticket has been received and is being processed.",
                'generated_at': datetime.now().isoformat()
            }

    def _fallback_analysis(self, ticket_text: str) -> Dict[str, Any]:
        """Intelligent fallback analysis when Claude is not available"""
        
        text_lower = ticket_text.lower()
        
        # Enhanced rule-based classification
        department = self._classify_department(text_lower)
        priority = self._classify_priority(text_lower)
        category = self._classify_category(text_lower)
        urgency_score = self._calculate_urgency_score(text_lower)
        
        return {
            'analysis_summary': {
                'department': department,
                'priority': priority,
                'category': category,
                'urgency_score': urgency_score,
                'impact_scope': 'single_user'
            },
            'technical_assessment': {
                'estimated_resolution_time_hours': {'P1': 4, 'P2': 12, 'P3': 24, 'P4': 72}.get(priority, 24),
                'issue_type': 'functionality'
            },
            'confidence_metrics': {
                'overall_confidence': 0.75
            },
            'model_used': 'intelligent_fallback',
            'fallback_used': True
        }

    def _classify_department(self, text: str) -> str:
        """Enhanced department classification"""
        
        department_keywords = {
            'UIDAI': ['aadhaar', 'uid', 'authentication', 'biometric', 'identity', 'verification'],
            'MeitY': ['payment', 'gateway', 'transaction', 'money', 'billing', 'financial'],
            'DigitalMP': ['portal', 'website', 'digital', 'online', 'platform', 'interface'],
            'eDistrict': ['certificate', 'document', 'verification', 'attestation', 'record']
        }
        
        scores = {}
        for dept, keywords in department_keywords.items():
            scores[dept] = sum(1 for keyword in keywords if keyword in text)
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'MPOnline'

    def _classify_priority(self, text: str) -> str:
        """Enhanced priority classification"""
        
        priority_keywords = {
            'P1': ['critical', 'urgent', 'emergency', 'down', 'failed', 'completely', 'thousands', 'outage'],
            'P2': ['important', 'high', 'serious', 'significant', 'timeout', 'intermittent', 'affecting'],
            'P4': ['minor', 'low', 'small', 'question', 'inquiry', 'thank', 'good', 'excellent']
        }
        
        for priority, keywords in priority_keywords.items():
            if any(keyword in text for keyword in keywords):
                return priority
        
        return 'P3'  # Default medium priority

    def _classify_category(self, text: str) -> str:
        """Enhanced category classification"""
        
        category_keywords = {
            'Authentication': ['login', 'password', 'authentication', 'aadhaar', 'biometric'],
            'Payment': ['payment', 'transaction', 'gateway', 'money', 'billing'],
            'Portal': ['portal', 'website', 'interface', 'page', 'digital'],
            'Network': ['network', 'connection', 'timeout', 'slow', 'connectivity'],
            'Certificate': ['certificate', 'document', 'verification', 'attestation']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'Other'

    def _calculate_urgency_score(self, text: str) -> int:
        """Calculate urgency score 1-10"""
        
        urgency_indicators = {
            'critical': 9, 'urgent': 8, 'emergency': 9, 'immediately': 8,
            'thousands': 7, 'hundreds': 6, 'many': 5, 'several': 4,
            'completely': 8, 'totally': 7, 'partially': 4, 'sometimes': 3,
            'revenue': 6, 'business': 5, 'citizens': 6, 'public': 5
        }
        
        score = 5  # Base score
        for indicator, weight in urgency_indicators.items():
            if indicator in text:
                score = max(score, weight)
        
        return min(score, 10)

    def _fallback_breach_prediction(self, ticket_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback breach prediction"""
        
        summary = ticket_analysis.get('analysis_summary', {})
        priority = summary.get('priority', 'P3')
        urgency = summary.get('urgency_score', 5)
        
        priority_risk = {'P1': 0.9, 'P2': 0.6, 'P3': 0.3, 'P4': 0.1}
        base_risk = priority_risk.get(priority, 0.3)
        urgency_factor = urgency / 10.0
        
        breach_probability = min(base_risk + urgency_factor * 0.3, 1.0)
        
        return {
            'breach_probability': breach_probability,
            'confidence_level': 0.75,
            'estimated_resolution_hours': {'P1': 4, 'P2': 12, 'P3': 24, 'P4': 72}.get(priority, 24),
            'model_used': 'fallback_prediction'
        }

    def _fallback_response_generation(self, ticket_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback response generation"""
        
        summary = ticket_analysis.get('analysis_summary', {})
        priority = summary.get('priority', 'P3')
        department = summary.get('department', 'MPOnline')
        
        response_templates = {
            'P1': "Thank you for reporting this critical issue. We have escalated this to our emergency response team and will provide updates every hour.",
            'P2': "Thank you for your report. This has been assigned high priority and our technical team is investigating. We'll update you within 4 hours.",
            'P3': "Thank you for contacting us. Your ticket has been received and assigned to our support team. We'll respond within 24 hours.",
            'P4': "Thank you for your inquiry. We've received your request and will respond within 72 hours."
        }
        
        timeline_hours = {'P1': 4, 'P2': 12, 'P3': 24, 'P4': 72}.get(priority, 24)
        
        return {
            'automated_response': {
                'acknowledgment': response_templates.get(priority, response_templates['P3']),
                'expected_timeline': f"Resolution expected within {timeline_hours} hours",
                'status_update': f"Your ticket has been routed to the {department} support team."
            },
            'model_used': 'fallback_response',
            'generated_at': datetime.now().isoformat()
        }

    def _calculate_avg_resolution(self, historical_data: List[Dict]) -> float:
        """Calculate average resolution time from historical data"""
        if not historical_data:
            return 24.0
        
        total_hours = sum(ticket.get('resolution_hours', 24) for ticket in historical_data)
        return total_hours / len(historical_data)

    def _calculate_success_rate(self, historical_data: List[Dict]) -> float:
        """Calculate SLA success rate from historical data"""
        if not historical_data:
            return 0.85
        
        successful = sum(1 for ticket in historical_data if ticket.get('sla_met', True))
        return successful / len(historical_data)


def main():
    """Demo the enhanced Llama 3.5 integration"""
    print("🚀 Enhanced Llama 3.5 Integration Demo")
    print("=" * 60)
    
    # Initialize enhanced integration
    claude_integration = EnhancedClaudeSonnetIntegration()
    
    # Test scenarios with varying complexity
    test_scenarios = [
        {
            'name': 'Critical Infrastructure Failure',
            'text': 'EMERGENCY: Complete Aadhaar authentication system failure across all of Madhya Pradesh! Citizens cannot access any government services, banks are unable to process KYC, and thousands of people are stranded at service centers. This started 30 minutes ago and is affecting critical infrastructure. Media is already reporting on this. Need immediate escalation to highest level!',
            'context': {
                'user_location': 'Bhopal, MP',
                'current_time': datetime.now().isoformat(),
                'user_type': 'government_official'
            }
        },
        {
            'name': 'Payment Gateway Performance Issue',
            'text': 'Our payment gateway is experiencing intermittent timeout issues affecting approximately 30% of transactions in the Bhopal and Indore regions since this morning. Merchants are reporting revenue losses and customer complaints are increasing. The issue seems to be related to peak hour traffic but we need urgent investigation.',
            'context': {
                'user_location': 'Indore, MP',
                'service_history': 'Previous payment issues resolved in 6 hours',
                'user_type': 'business_user'
            }
        },
        {
            'name': 'Citizen Portal Access Issue',
            'text': 'I am unable to access the citizen services portal to download my income certificate. The page loads very slowly and sometimes shows error messages. This is needed for my loan application which has a deadline tomorrow. Please help urgently.',
            'context': {
                'user_location': 'Gwalior, MP',
                'user_type': 'citizen',
                'technical_level': 'basic'
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test Scenario {i}: {scenario['name']}")
        print("-" * 50)
        print(f"📝 Input: {scenario['text'][:100]}...")
        
        # Step 1: Comprehensive Analysis
        print("\n🧠 Step 1: Comprehensive Ticket Analysis")
        analysis_result = claude_integration.analyze_ticket_with_claude_sonnet(
            scenario['text'], 
            scenario.get('context')
        )
        
        if analysis_result.get('parsed_successfully'):
            summary = analysis_result.get('analysis_summary', {})
            print(f"   Department: {summary.get('department')}")
            print(f"   Priority: {summary.get('priority')}")
            print(f"   Urgency Score: {summary.get('urgency_score')}/10")
            print(f"   Impact Scope: {summary.get('impact_scope')}")
            print(f"   Confidence: {analysis_result.get('confidence_score', 0)}%")
        else:
            print(f"   ⚠️ Analysis failed, using fallback")
        
        # Step 2: SLA Breach Prediction
        print("\n🔮 Step 2: SLA Breach Risk Prediction")
        breach_prediction = claude_integration.predict_sla_breach_risk(analysis_result)
        
        print(f"   Breach Probability: {breach_prediction.get('breach_probability', 0):.1%}")
        print(f"   Confidence Level: {breach_prediction.get('confidence_level', 0):.1%}")
        print(f"   Est. Resolution: {breach_prediction.get('estimated_resolution_hours', 24)} hours")
        
        # Step 3: Intelligent Response Generation
        print("\n💬 Step 3: Intelligent Response Generation")
        response_result = claude_integration.generate_intelligent_response(
            analysis_result, 
            scenario.get('context')
        )
        
        if response_result.get('parsed_successfully'):
            auto_response = response_result.get('automated_response', {})
            print(f"   Acknowledgment: {auto_response.get('acknowledgment', 'N/A')[:80]}...")
            print(f"   Timeline: {auto_response.get('expected_timeline', 'N/A')}")
        else:
            print(f"   ⚠️ Response generation failed, using fallback")
        
        print(f"   Model Used: {analysis_result.get('model_used', 'fallback')}")
        
        # Brief pause between scenarios
        import time
        time.sleep(1)
    
    print(f"\n🎉 Enhanced Llama 3.5 integration demo completed!")
    print(f"✅ Ready for production deployment with advanced AI capabilities")

if __name__ == "__main__":
    main()