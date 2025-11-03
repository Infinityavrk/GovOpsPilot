#!/usr/bin/env python3
"""
License Optimization Integration for SLA Guard
Simplified integration with AWS GenAI for license optimization
"""

import json
import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LicenseOptimizationAgent:
    def __init__(self, region='us-east-2'):
        """Initialize License Optimization AI Agent"""
        self.region = region
        
        # Initialize AWS clients
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name=region)
            self.bedrock_available = True
            logger.info("✅ Bedrock client initialized for license optimization")
        except Exception as e:
            logger.warning(f"⚠️ Bedrock client initialization failed: {e}")
            self.bedrock = None
            self.bedrock_available = False
        
        # Model configuration
        self.model_id = 'us.meta.llama3-2-3b-instruct-v1:0'  # Same as SLA Guard
        
        logger.info("🤖 License Optimization AI Agent initialized")

    def analyze_license_portfolio(self, license_data: List[Dict]) -> Dict[str, Any]:
        """Analyze complete license portfolio using AI"""
        logger.info(f"🔍 Analyzing license portfolio with {len(license_data)} assets...")
        
        # Calculate basic metrics
        analysis_result = {
            'total_assets': len(license_data),
            'total_cost': sum(asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0) for asset in license_data),
            'underutilized_assets': [],
            'duplicate_assets': [],
            'renewal_alerts': [],
            'cost_optimization_opportunities': [],
            'ai_insights': {},
            'recommendations': []
        }
        
        # Detect underutilized licenses
        underutilized = self._detect_underutilized_licenses(license_data)
        analysis_result['underutilized_assets'] = underutilized
        
        # Detect duplicate subscriptions
        duplicates = self._detect_duplicate_subscriptions(license_data)
        analysis_result['duplicate_assets'] = duplicates
        
        # Check renewal alerts
        renewals = self._check_renewal_alerts(license_data)
        analysis_result['renewal_alerts'] = renewals
        
        # Generate AI insights
        ai_insights = self._generate_ai_insights(license_data)
        analysis_result['ai_insights'] = ai_insights
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(license_data, analysis_result)
        analysis_result['recommendations'] = recommendations
        
        logger.info(f"✅ Analysis completed: {len(recommendations)} recommendations generated")
        return analysis_result

    def _detect_underutilized_licenses(self, assets: List[Dict]) -> List[Dict]:
        """Detect underutilized licenses"""
        underutilized = []
        
        for asset in assets:
            total_licenses = asset.get('totalLicenses', 0)
            used_licenses = asset.get('usedLicenses', 0)
            cost_per_license = asset.get('costPerLicense', 0)
            
            if total_licenses > 0:
                utilization_rate = used_licenses / total_licenses
                
                if utilization_rate < 0.7:  # Less than 70% utilization
                    waste_cost = (total_licenses - used_licenses) * cost_per_license
                    
                    underutilized.append({
                        'asset_id': asset.get('id', 'UNKNOWN'),
                        'name': asset.get('name', 'Unknown'),
                        'vendor': asset.get('vendor', 'Unknown'),
                        'utilization_rate': utilization_rate,
                        'unused_licenses': total_licenses - used_licenses,
                        'waste_cost_annual': waste_cost * 12,  # Assuming monthly cost
                        'department': asset.get('department', 'Unknown'),
                        'recommendation': f"Reduce licenses to {max(int(used_licenses * 1.2), 1)} (20% buffer)"
                    })
        
        return sorted(underutilized, key=lambda x: x['waste_cost_annual'], reverse=True)

    def _detect_duplicate_subscriptions(self, assets: List[Dict]) -> List[Dict]:
        """Detect duplicate or overlapping subscriptions"""
        duplicates = []
        
        # Group by vendor
        vendor_groups = {}
        for asset in assets:
            vendor = asset.get('vendor', 'Unknown').lower()
            if vendor not in vendor_groups:
                vendor_groups[vendor] = []
            vendor_groups[vendor].append(asset)
        
        # Check for communication/collaboration tool overlaps
        communication_tools = []
        for asset in assets:
            name = asset.get('name', '').lower()
            if any(tool in name for tool in ['zoom', 'teams', 'slack', 'meet', 'webex']):
                communication_tools.append(asset)
        
        if len(communication_tools) > 1:
            total_cost = sum(asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0) for asset in communication_tools)
            duplicates.append({
                'category': 'Communication Tools',
                'assets': [
                    {
                        'asset_id': asset.get('id'),
                        'name': asset.get('name'),
                        'cost': asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0),
                        'department': asset.get('department')
                    } for asset in communication_tools
                ],
                'total_cost': total_cost,
                'consolidation_opportunity': total_cost * 0.4  # 40% potential savings
            })
        
        return duplicates

    def _check_renewal_alerts(self, assets: List[Dict]) -> List[Dict]:
        """Check for upcoming renewals"""
        renewals = []
        current_date = datetime.now()
        
        for asset in assets:
            renewal_date_str = asset.get('renewalDate')
            if renewal_date_str:
                try:
                    renewal_date = datetime.strptime(renewal_date_str, '%Y-%m-%d')
                    days_to_renewal = (renewal_date - current_date).days
                    
                    if 0 <= days_to_renewal <= 90:  # Next 90 days
                        current_cost = asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0)
                        
                        renewals.append({
                            'asset_id': asset.get('id'),
                            'name': asset.get('name'),
                            'vendor': asset.get('vendor'),
                            'renewal_date': renewal_date_str,
                            'days_to_renewal': days_to_renewal,
                            'current_cost': current_cost,
                            'department': asset.get('department'),
                            'optimization_opportunity': current_cost * 0.15  # 15% potential savings
                        })
                except ValueError:
                    logger.warning(f"Invalid renewal date format for asset {asset.get('id')}")
        
        return sorted(renewals, key=lambda x: x['days_to_renewal'])

    def _generate_ai_insights(self, assets: List[Dict]) -> Dict[str, Any]:
        """Generate AI-powered insights"""
        
        total_cost = sum(asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0) for asset in assets)
        total_licenses = sum(asset.get('totalLicenses', 0) for asset in assets)
        total_used = sum(asset.get('usedLicenses', 0) for asset in assets)
        overall_utilization = total_used / total_licenses if total_licenses > 0 else 0
        
        # Vendor analysis
        vendor_spending = {}
        for asset in assets:
            vendor = asset.get('vendor', 'Unknown')
            cost = asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0)
            if vendor not in vendor_spending:
                vendor_spending[vendor] = 0
            vendor_spending[vendor] += cost
        
        # Department analysis
        dept_spending = {}
        for asset in assets:
            dept = asset.get('department', 'Unknown')
            cost = asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0)
            if dept not in dept_spending:
                dept_spending[dept] = 0
            dept_spending[dept] += cost
        
        # Calculate optimization potential
        optimization_potential = 0
        for asset in assets:
            total_licenses = asset.get('totalLicenses', 0)
            used_licenses = asset.get('usedLicenses', 0)
            cost_per_license = asset.get('costPerLicense', 0)
            
            if total_licenses > 0:
                utilization = used_licenses / total_licenses
                if utilization < 0.7:
                    waste = (total_licenses - max(int(used_licenses * 1.2), 1)) * cost_per_license * 12
                    optimization_potential += waste
        
        return {
            'portfolio_health_score': self._calculate_portfolio_health_score(assets),
            'total_annual_cost': total_cost * 12,
            'overall_utilization_rate': overall_utilization,
            'top_spending_vendors': sorted(vendor_spending.items(), key=lambda x: x[1], reverse=True)[:5],
            'department_breakdown': dept_spending,
            'optimization_potential': optimization_potential,
            'risk_assessment': 'Medium' if overall_utilization < 0.6 else 'Low'
        }

    def _generate_optimization_recommendations(self, assets: List[Dict], analysis: Dict) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Try AI-powered recommendations first
        if self.bedrock_available:
            try:
                ai_recommendations = self._get_bedrock_recommendations(assets, analysis)
                if ai_recommendations:
                    return ai_recommendations
            except Exception as e:
                logger.warning(f"AI recommendation generation failed: {e}")
        
        # Fallback to rule-based recommendations
        return self._get_fallback_recommendations(assets, analysis)

    def _get_bedrock_recommendations(self, assets: List[Dict], analysis: Dict) -> List[Dict]:
        """Generate recommendations using Amazon Bedrock with enhanced prompting"""
        try:
            # Prepare detailed context for AI
            context = {
                'total_assets': len(assets),
                'underutilized_count': len(analysis['underutilized_assets']),
                'duplicate_count': len(analysis['duplicate_assets']),
                'total_annual_cost': analysis['ai_insights']['total_annual_cost'],
                'optimization_potential': analysis['ai_insights']['optimization_potential'],
                'top_vendors': analysis['ai_insights']['top_spending_vendors'][:3],
                'portfolio_health': analysis['ai_insights']['portfolio_health_score']
            }
            
            # Create detailed asset summary for AI context
            asset_summary = []
            for asset in assets[:5]:  # Top 5 assets by cost
                annual_cost = asset.get('costPerLicense', 0) * asset.get('totalLicenses', 0) * 12
                utilization = asset.get('usedLicenses', 0) / max(asset.get('totalLicenses', 1), 1)
                asset_summary.append(f"- {asset.get('name', 'Unknown')}: ₹{annual_cost:,.0f}/year, {utilization:.1%} utilized")
            
            prompt = f"""You are an expert AI consultant for Indian government enterprise software license optimization with deep knowledge of GeM procurement processes.

PORTFOLIO ANALYSIS:
- Total Software Assets: {context['total_assets']}
- Annual License Cost: ₹{context['total_annual_cost']:,.0f}
- Portfolio Health Score: {context['portfolio_health']:.1f}/100
- Underutilized Assets: {context['underutilized_count']}
- Duplicate/Overlapping Assets: {context['duplicate_count']}
- Optimization Potential: ₹{context['optimization_potential']:,.0f}

TOP SPENDING VENDORS:
{chr(10).join([f"- {vendor}: ₹{cost:,.0f}" for vendor, cost in context['top_vendors']])}

KEY ASSETS:
{chr(10).join(asset_summary)}

GOVERNMENT CONTEXT:
- All procurement must follow GeM (Government e-Marketplace) guidelines
- Budget approvals required for changes >₹50,000
- Vendor negotiations should leverage government buying power
- Focus on Indian vendors where possible (Make in India)
- Consider security and compliance requirements

Generate 4-6 specific, actionable optimization recommendations in JSON format:
{{
    "recommendations": [
        {{
            "type": "LICENSE_REDUCTION|CONSOLIDATION|RENEWAL_OPTIMIZATION|VENDOR_NEGOTIATION|COMPLIANCE_OPTIMIZATION",
            "title": "Brief recommendation title",
            "description": "Detailed actionable description with specific steps",
            "potential_savings": 50000,
            "implementation_effort": "LOW|MEDIUM|HIGH",
            "priority": "HIGH|MEDIUM|LOW",
            "confidence": 0.85,
            "gem_integration_required": true,
            "compliance_impact": "Positive impact on security/compliance",
            "timeline_months": 3,
            "risk_level": "LOW|MEDIUM|HIGH"
        }}
    ]
}}

Focus on:
1. Highest financial impact recommendations
2. GeM procurement compliance
3. Government-specific considerations
4. Realistic implementation timelines
5. Risk mitigation strategies

Respond with ONLY valid JSON."""

            body = {
                "prompt": prompt,
                "max_gen_len": 1500,
                "temperature": 0.1,
                "top_p": 0.9
            }
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            result = json.loads(response['body'].read())
            ai_response = result.get('generation', '')
            
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                try:
                    ai_data = json.loads(json_match.group())
                    recommendations = []
                    
                    for rec_data in ai_data.get('recommendations', []):
                        rec = {
                            'recommendation_id': str(uuid.uuid4()),
                            'asset_id': 'PORTFOLIO',
                            'recommendation_type': rec_data.get('type', 'LICENSE_REDUCTION'),
                            'title': rec_data.get('title', rec_data.get('description', '')[:50] + '...'),
                            'description': rec_data.get('description', ''),
                            'potential_savings': float(rec_data.get('potential_savings', 0)),
                            'confidence_score': float(rec_data.get('confidence', 0.8)),
                            'priority': rec_data.get('priority', 'MEDIUM'),
                            'implementation_effort': rec_data.get('implementation_effort', 'MEDIUM'),
                            'timeline_months': int(rec_data.get('timeline_months', 3)),
                            'risk_level': rec_data.get('risk_level', 'LOW'),
                            'compliance_impact': rec_data.get('compliance_impact', 'Positive'),
                            'action_required': 'Review and approve recommendation',
                            'approval_needed': True,
                            'gem_integration_required': rec_data.get('gem_integration_required', True)
                        }
                        recommendations.append(rec)
                    
                    logger.info(f"✅ Generated {len(recommendations)} AI-powered recommendations")
                    return recommendations
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse AI recommendation JSON")
                    
        except Exception as e:
            logger.warning(f"Bedrock recommendation generation failed: {e}")
        
        return None

    def _get_fallback_recommendations(self, assets: List[Dict], analysis: Dict) -> List[Dict]:
        """Generate fallback recommendations using rule-based logic"""
        recommendations = []
        
        # Recommendations for underutilized assets
        for underutilized in analysis['underutilized_assets'][:3]:  # Top 3
            rec = {
                'recommendation_id': str(uuid.uuid4()),
                'asset_id': underutilized['asset_id'],
                'recommendation_type': 'LICENSE_REDUCTION',
                'description': f"Reduce {underutilized['name']} licenses by {underutilized['unused_licenses']} unused licenses",
                'potential_savings': underutilized['waste_cost_annual'],
                'confidence_score': 0.85,
                'priority': 'HIGH' if underutilized['waste_cost_annual'] > 100000 else 'MEDIUM',
                'action_required': 'Reduce license count and renegotiate contract',
                'approval_needed': True,
                'gem_integration_required': True
            }
            recommendations.append(rec)
        
        # Recommendations for duplicates
        for duplicate in analysis['duplicate_assets']:
            rec = {
                'recommendation_id': str(uuid.uuid4()),
                'asset_id': duplicate['assets'][0]['asset_id'] if duplicate['assets'] else 'UNKNOWN',
                'recommendation_type': 'CONSOLIDATION',
                'description': f"Consolidate {duplicate['category']} to eliminate overlap and reduce costs",
                'potential_savings': duplicate['consolidation_opportunity'],
                'confidence_score': 0.75,
                'priority': 'HIGH',
                'action_required': 'Consolidate subscriptions and cancel duplicates',
                'approval_needed': True,
                'gem_integration_required': True
            }
            recommendations.append(rec)
        
        # Recommendations for renewals
        for renewal in analysis['renewal_alerts'][:2]:  # Top 2
            if renewal['optimization_opportunity'] > 0:
                rec = {
                    'recommendation_id': str(uuid.uuid4()),
                    'asset_id': renewal['asset_id'],
                    'recommendation_type': 'RENEWAL_OPTIMIZATION',
                    'description': f"Optimize {renewal['name']} renewal terms and negotiate better pricing",
                    'potential_savings': renewal['optimization_opportunity'],
                    'confidence_score': 0.70,
                    'priority': 'MEDIUM',
                    'action_required': 'Negotiate better terms during renewal',
                    'approval_needed': True,
                    'gem_integration_required': True
                }
                recommendations.append(rec)
        
        return sorted(recommendations, key=lambda x: x['potential_savings'], reverse=True)

    def _calculate_portfolio_health_score(self, assets: List[Dict]) -> float:
        """Calculate overall portfolio health score"""
        if not assets:
            return 0.0
        
        # Calculate average utilization
        total_utilization = 0
        valid_assets = 0
        
        for asset in assets:
            total_licenses = asset.get('totalLicenses', 0)
            used_licenses = asset.get('usedLicenses', 0)
            
            if total_licenses > 0:
                utilization = used_licenses / total_licenses
                total_utilization += utilization
                valid_assets += 1
        
        avg_utilization = total_utilization / valid_assets if valid_assets > 0 else 0
        
        # Vendor diversity (more vendors = higher risk, but also more options)
        unique_vendors = len(set(asset.get('vendor', 'Unknown') for asset in assets))
        vendor_diversity_score = min(unique_vendors / len(assets), 1.0)
        
        # Renewal management (upcoming renewals within 90 days)
        upcoming_renewals = 0
        current_date = datetime.now()
        
        for asset in assets:
            renewal_date_str = asset.get('renewalDate')
            if renewal_date_str:
                try:
                    renewal_date = datetime.strptime(renewal_date_str, '%Y-%m-%d')
                    days_to_renewal = (renewal_date - current_date).days
                    if 0 <= days_to_renewal <= 90:
                        upcoming_renewals += 1
                except ValueError:
                    pass
        
        renewal_score = 1.0 - (upcoming_renewals / len(assets))
        
        # Weighted health score
        health_score = (avg_utilization * 0.5 + vendor_diversity_score * 0.2 + renewal_score * 0.3) * 100
        
        return round(health_score, 2)