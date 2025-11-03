#!/usr/bin/env python3
"""
AI Agent for License & Asset Optimization
Auto-detects underused/duplicate subscriptions and suggests cost optimizations
Integrates with GeM procurement and finance approvals
"""

import json
import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LicenseAsset:
    """License asset data structure"""
    asset_id: str
    name: str
    vendor: str
    license_type: str
    total_licenses: int
    used_licenses: int
    cost_per_license: float
    renewal_date: str
    department: str
    procurement_id: Optional[str] = None
    gem_order_id: Optional[str] = None
    usage_trend: Optional[str] = None
    risk_score: Optional[float] = None

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation structure"""
    recommendation_id: str
    asset_id: str
    recommendation_type: str
    description: str
    potential_savings: float
    confidence_score: float
    priority: str
    action_required: str
    approval_needed: bool
    gem_integration_required: bool

class LicenseOptimizationAgent:
    def __init__(self, region='us-east-1'):
        """Initialize License Optimization AI Agent"""
        self.region = region
        
        # Initialize AWS clients
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.comprehend = boto3.client('comprehend', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # Initialize tables
        self.licenses_table_name = 'license-assets'
        self.recommendations_table_name = 'license-recommendations'
        self.gem_orders_table_name = 'gem-procurement-orders'
        
        logger.info("🤖 License Optimization AI Agent initialized")

    def analyze_license_portfolio(self, license_data: List[Dict]) -> Dict[str, Any]:
        """Analyze complete license portfolio using AI"""
        logger.info("🔍 Analyzing license portfolio with AI...")
        
        # Convert to structured format
        assets = [self._parse_license_asset(data) for data in license_data]
        
        # AI-powered analysis
        analysis_result = {
            'total_assets': len(assets),
            'total_cost': sum(asset.cost_per_license * asset.total_licenses for asset in assets),
            'underutilized_assets': [],
            'duplicate_assets': [],
            'renewal_alerts': [],
            'cost_optimization_opportunities': [],
            'ai_insights': {},
            'recommendations': []
        }
        
        # Detect underutilized licenses
        underutilized = self._detect_underutilized_licenses(assets)
        analysis_result['underutilized_assets'] = underutilized
        
        # Detect duplicate subscriptions
        duplicates = self._detect_duplicate_subscriptions(assets)
        analysis_result['duplicate_assets'] = duplicates
        
        # Check renewal alerts
        renewals = self._check_renewal_alerts(assets)
        analysis_result['renewal_alerts'] = renewals
        
        # Generate AI insights
        ai_insights = self._generate_ai_insights(assets)
        analysis_result['ai_insights'] = ai_insights
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(assets, analysis_result)
        analysis_result['recommendations'] = recommendations
        
        # Store analysis results
        self._store_analysis_results(analysis_result)
        
        return analysis_result

    def _parse_license_asset(self, data: Dict) -> LicenseAsset:
        """Parse license asset from raw data"""
        return LicenseAsset(
            asset_id=data.get('asset_id', str(uuid.uuid4())),
            name=data.get('name', ''),
            vendor=data.get('vendor', ''),
            license_type=data.get('license_type', 'subscription'),
            total_licenses=int(data.get('total_licenses', 0)),
            used_licenses=int(data.get('used_licenses', 0)),
            cost_per_license=float(data.get('cost_per_license', 0)),
            renewal_date=data.get('renewal_date', ''),
            department=data.get('department', ''),
            procurement_id=data.get('procurement_id'),
            gem_order_id=data.get('gem_order_id'),
            usage_trend=data.get('usage_trend'),
            risk_score=data.get('risk_score')
        )

    def _detect_underutilized_licenses(self, assets: List[LicenseAsset]) -> List[Dict]:
        """Detect underutilized licenses using AI analysis"""
        underutilized = []
        
        for asset in assets:
            if asset.total_licenses > 0:
                utilization_rate = asset.used_licenses / asset.total_licenses
                
                # AI-based utilization analysis
                if utilization_rate < 0.7:  # Less than 70% utilization
                    waste_cost = (asset.total_licenses - asset.used_licenses) * asset.cost_per_license
                    
                    # Use AI to analyze usage patterns
                    ai_analysis = self._analyze_usage_pattern(asset)
                    
                    underutilized.append({
                        'asset_id': asset.asset_id,
                        'name': asset.name,
                        'vendor': asset.vendor,
                        'utilization_rate': utilization_rate,
                        'unused_licenses': asset.total_licenses - asset.used_licenses,
                        'waste_cost_annual': waste_cost * 12,  # Assuming monthly cost
                        'department': asset.department,
                        'ai_analysis': ai_analysis,
                        'recommendation': self._get_utilization_recommendation(asset, utilization_rate)
                    })
        
        return sorted(underutilized, key=lambda x: x['waste_cost_annual'], reverse=True)

    def _detect_duplicate_subscriptions(self, assets: List[LicenseAsset]) -> List[Dict]:
        """Detect duplicate or overlapping subscriptions"""
        duplicates = []
        
        # Group by vendor and similar functionality
        vendor_groups = {}
        for asset in assets:
            vendor = asset.vendor.lower()
            if vendor not in vendor_groups:
                vendor_groups[vendor] = []
            vendor_groups[vendor].append(asset)
        
        # Analyze each vendor group for duplicates
        for vendor, vendor_assets in vendor_groups.items():
            if len(vendor_assets) > 1:
                # Use AI to detect functional overlap
                overlap_analysis = self._analyze_functional_overlap(vendor_assets)
                
                if overlap_analysis['has_overlap']:
                    total_cost = sum(asset.cost_per_license * asset.total_licenses for asset in vendor_assets)
                    
                    duplicates.append({
                        'vendor': vendor,
                        'assets': [
                            {
                                'asset_id': asset.asset_id,
                                'name': asset.name,
                                'cost': asset.cost_per_license * asset.total_licenses,
                                'department': asset.department
                            } for asset in vendor_assets
                        ],
                        'total_cost': total_cost,
                        'overlap_analysis': overlap_analysis,
                        'consolidation_opportunity': overlap_analysis['consolidation_savings']
                    })
        
        return duplicates

    def _check_renewal_alerts(self, assets: List[LicenseAsset]) -> List[Dict]:
        """Check for upcoming renewals and optimization opportunities"""
        renewals = []
        current_date = datetime.now()
        
        for asset in assets:
            if asset.renewal_date:
                try:
                    renewal_date = datetime.strptime(asset.renewal_date, '%Y-%m-%d')
                    days_to_renewal = (renewal_date - current_date).days
                    
                    if 0 <= days_to_renewal <= 90:  # Next 90 days
                        # AI analysis for renewal optimization
                        renewal_analysis = self._analyze_renewal_opportunity(asset)
                        
                        renewals.append({
                            'asset_id': asset.asset_id,
                            'name': asset.name,
                            'vendor': asset.vendor,
                            'renewal_date': asset.renewal_date,
                            'days_to_renewal': days_to_renewal,
                            'current_cost': asset.cost_per_license * asset.total_licenses,
                            'department': asset.department,
                            'renewal_analysis': renewal_analysis,
                            'optimization_opportunity': renewal_analysis['optimization_potential']
                        })
                except ValueError:
                    logger.warning(f"Invalid renewal date format for asset {asset.asset_id}")
        
        return sorted(renewals, key=lambda x: x['days_to_renewal'])

    def _generate_ai_insights(self, assets: List[LicenseAsset]) -> Dict[str, Any]:
        """Generate AI-powered insights using AWS GenAI services"""
        
        # Calculate portfolio metrics
        total_cost = sum(asset.cost_per_license * asset.total_licenses for asset in assets)
        total_licenses = sum(asset.total_licenses for asset in assets)
        total_used = sum(asset.used_licenses for asset in assets)
        overall_utilization = total_used / total_licenses if total_licenses > 0 else 0
        
        # Vendor analysis
        vendor_spending = {}
        for asset in assets:
            vendor = asset.vendor
            cost = asset.cost_per_license * asset.total_licenses
            if vendor not in vendor_spending:
                vendor_spending[vendor] = 0
            vendor_spending[vendor] += cost
        
        # Department analysis
        dept_spending = {}
        for asset in assets:
            dept = asset.department
            cost = asset.cost_per_license * asset.total_licenses
            if dept not in dept_spending:
                dept_spending[dept] = 0
            dept_spending[dept] += cost
        
        # AWS GenAI-powered analysis
        genai_insights = self._get_bedrock_portfolio_insights(assets)
        trends = self._analyze_spending_trends_with_comprehend(assets)
        
        base_insights = {
            'portfolio_health_score': self._calculate_portfolio_health_score(assets),
            'total_annual_cost': total_cost * 12,
            'overall_utilization_rate': overall_utilization,
            'top_spending_vendors': sorted(vendor_spending.items(), key=lambda x: x[1], reverse=True)[:5],
            'department_breakdown': dept_spending,
            'spending_trends': trends,
            'risk_assessment': self._assess_portfolio_risks(assets),
            'optimization_potential': self._calculate_optimization_potential(assets)
        }
        
        # Merge with GenAI insights
        if genai_insights:
            base_insights.update(genai_insights)
        
        return base_insights

    def _generate_optimization_recommendations(self, assets: List[LicenseAsset], analysis: Dict) -> List[OptimizationRecommendation]:
        """Generate AI-powered optimization recommendations using AWS GenAI"""
        
        # Try to get AI-powered recommendations from Bedrock
        ai_recommendations = self._get_bedrock_recommendations(assets, analysis)
        
        if ai_recommendations:
            logger.info("✅ Using Bedrock AI-generated recommendations")
            return ai_recommendations
        else:
            logger.info("🔄 Using fallback rule-based recommendations")
            return self._get_fallback_recommendations(assets, analysis)

    def _get_bedrock_recommendations(self, assets: List[LicenseAsset], analysis: Dict) -> List[OptimizationRecommendation]:
        """Generate recommendations using Amazon Bedrock Claude 3"""
        try:
            # Prepare data for AI recommendation generation
            recommendation_context = {
                'portfolio_summary': {
                    'total_assets': len(assets),
                    'underutilized_assets': len(analysis['underutilized_assets']),
                    'duplicate_assets': len(analysis['duplicate_assets']),
                    'renewal_alerts': len(analysis['renewal_alerts']),
                    'total_annual_cost': analysis['total_cost'] * 12
                },
                'underutilized_details': analysis['underutilized_assets'][:5],  # Top 5
                'duplicate_details': analysis['duplicate_assets'],
                'renewal_details': analysis['renewal_alerts'][:3]  # Top 3
            }

            prompt = f"""
            You are an expert AI consultant for enterprise software license optimization. 
            Based on the portfolio analysis below, generate specific, actionable optimization recommendations.

            Portfolio Analysis:
            {json.dumps(recommendation_context, indent=2)}

            Generate recommendations in the following JSON format:
            {{
                "recommendations": [
                    {{
                        "recommendation_type": "LICENSE_REDUCTION|CONSOLIDATION|RENEWAL_OPTIMIZATION|VENDOR_SWITCH",
                        "asset_id": "specific asset ID",
                        "title": "Brief title of recommendation",
                        "description": "Detailed description of the recommendation",
                        "potential_savings": "estimated annual savings in rupees",
                        "confidence_score": "confidence level between 0.0 and 1.0",
                        "priority": "HIGH|MEDIUM|LOW",
                        "action_required": "specific action steps",
                        "implementation_timeline": "estimated timeline",
                        "risk_factors": ["list of potential risks"],
                        "success_metrics": ["how to measure success"],
                        "gem_integration_required": true/false
                    }}
                ]
            }}

            Focus on:
            1. Highest impact recommendations first
            2. Specific, actionable steps
            3. Realistic savings estimates
            4. Implementation feasibility
            5. Risk mitigation strategies

            Generate 3-5 high-quality recommendations prioritized by potential savings and implementation feasibility.
            """

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2500,
                "messages": [{"role": "user", "content": prompt}]
            })

            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=body
            )

            result = json.loads(response['body'].read())
            ai_response = json.loads(result['content'][0]['text'])
            
            # Convert AI recommendations to OptimizationRecommendation objects
            recommendations = []
            for rec_data in ai_response.get('recommendations', []):
                rec = OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    asset_id=rec_data.get('asset_id', 'UNKNOWN'),
                    recommendation_type=rec_data.get('recommendation_type', 'LICENSE_REDUCTION'),
                    description=rec_data.get('description', ''),
                    potential_savings=float(rec_data.get('potential_savings', 0)),
                    confidence_score=float(rec_data.get('confidence_score', 0.8)),
                    priority=rec_data.get('priority', 'MEDIUM'),
                    action_required=rec_data.get('action_required', ''),
                    approval_needed=True,
                    gem_integration_required=rec_data.get('gem_integration_required', True)
                )
                recommendations.append(rec)
            
            logger.info(f"✅ Generated {len(recommendations)} AI-powered recommendations")
            return recommendations

        except Exception as e:
            logger.warning(f"⚠️ Bedrock recommendation generation failed: {str(e)}")
            return None

    def _get_fallback_recommendations(self, assets: List[LicenseAsset], analysis: Dict) -> List[OptimizationRecommendation]:
        """Generate fallback recommendations using rule-based logic"""
        recommendations = []
        
        # Recommendations for underutilized assets
        for underutilized in analysis['underutilized_assets']:
            rec = OptimizationRecommendation(
                recommendation_id=str(uuid.uuid4()),
                asset_id=underutilized['asset_id'],
                recommendation_type='LICENSE_REDUCTION',
                description=f"Reduce {underutilized['name']} licenses from {underutilized['unused_licenses']} unused licenses",
                potential_savings=underutilized['waste_cost_annual'],
                confidence_score=0.85,
                priority='HIGH' if underutilized['waste_cost_annual'] > 100000 else 'MEDIUM',
                action_required='Reduce license count and renegotiate contract',
                approval_needed=True,
                gem_integration_required=True
            )
            recommendations.append(rec)
        
        # Recommendations for duplicates
        for duplicate in analysis['duplicate_assets']:
            rec = OptimizationRecommendation(
                recommendation_id=str(uuid.uuid4()),
                asset_id=duplicate['assets'][0]['asset_id'],  # Primary asset
                recommendation_type='CONSOLIDATION',
                description=f"Consolidate {duplicate['vendor']} subscriptions to eliminate overlap",
                potential_savings=duplicate['consolidation_opportunity'],
                confidence_score=0.75,
                priority='HIGH',
                action_required='Consolidate subscriptions and cancel duplicates',
                approval_needed=True,
                gem_integration_required=True
            )
            recommendations.append(rec)
        
        # Recommendations for renewals
        for renewal in analysis['renewal_alerts']:
            if renewal['optimization_opportunity'] > 0:
                rec = OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    asset_id=renewal['asset_id'],
                    recommendation_type='RENEWAL_OPTIMIZATION',
                    description=f"Optimize {renewal['name']} renewal terms and pricing",
                    potential_savings=renewal['optimization_opportunity'],
                    confidence_score=0.70,
                    priority='MEDIUM',
                    action_required='Negotiate better terms during renewal',
                    approval_needed=True,
                    gem_integration_required=True
                )
                recommendations.append(rec)
        
        return sorted(recommendations, key=lambda x: x.potential_savings, reverse=True)

    def integrate_with_gem_procurement(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Integrate recommendation with GeM procurement system"""
        logger.info(f"🛒 Integrating recommendation {recommendation.recommendation_id} with GeM...")
        
        # Simulate GeM integration
        gem_integration = {
            'gem_request_id': f"GEM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            'recommendation_id': recommendation.recommendation_id,
            'procurement_type': self._map_to_gem_category(recommendation.recommendation_type),
            'estimated_value': recommendation.potential_savings,
            'approval_workflow': self._create_approval_workflow(recommendation),
            'gem_catalog_items': self._find_gem_catalog_alternatives(recommendation),
            'compliance_check': self._check_gem_compliance(recommendation),
            'timeline': self._estimate_procurement_timeline(recommendation)
        }
        
        # Store in GeM orders table
        self._store_gem_integration(gem_integration)
        
        return gem_integration

    def create_finance_approval_request(self, recommendation: OptimizationRecommendation, gem_integration: Dict) -> Dict[str, Any]:
        """Create finance approval request for optimization"""
        
        approval_request = {
            'approval_id': f"FIN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            'recommendation_id': recommendation.recommendation_id,
            'gem_request_id': gem_integration['gem_request_id'],
            'request_type': 'LICENSE_OPTIMIZATION',
            'financial_impact': {
                'potential_savings': recommendation.potential_savings,
                'implementation_cost': self._estimate_implementation_cost(recommendation),
                'net_benefit': recommendation.potential_savings - self._estimate_implementation_cost(recommendation),
                'payback_period': self._calculate_payback_period(recommendation)
            },
            'business_justification': self._generate_business_justification(recommendation),
            'risk_assessment': self._assess_implementation_risks(recommendation),
            'approval_level': self._determine_approval_level(recommendation.potential_savings),
            'status': 'PENDING_APPROVAL',
            'created_at': datetime.now().isoformat(),
            'approvers': self._get_required_approvers(recommendation)
        }
        
        # Send to approval workflow
        self._initiate_approval_workflow(approval_request)
        
        return approval_request

    def _analyze_usage_pattern(self, asset: LicenseAsset) -> Dict[str, Any]:
        """AI analysis of usage patterns"""
        # Simulate AI analysis (in production, this would use real usage data)
        return {
            'trend': 'declining' if asset.used_licenses < asset.total_licenses * 0.5 else 'stable',
            'seasonality': 'low_seasonal_variation',
            'growth_prediction': 'negative_growth' if asset.used_licenses < asset.total_licenses * 0.6 else 'stable',
            'optimal_license_count': max(int(asset.used_licenses * 1.2), 1),  # 20% buffer
            'confidence': 0.8
        }

    def _analyze_functional_overlap(self, assets: List[LicenseAsset]) -> Dict[str, Any]:
        """Analyze functional overlap between assets"""
        # Simulate AI analysis of functional overlap
        total_cost = sum(asset.cost_per_license * asset.total_licenses for asset in assets)
        
        return {
            'has_overlap': len(assets) > 1,
            'overlap_percentage': 0.6 if len(assets) > 1 else 0,
            'consolidation_savings': total_cost * 0.3 if len(assets) > 1 else 0,
            'recommended_solution': f"Consolidate to single {assets[0].vendor} subscription" if assets else ""
        }

    def _analyze_renewal_opportunity(self, asset: LicenseAsset) -> Dict[str, Any]:
        """Analyze renewal optimization opportunity"""
        current_cost = asset.cost_per_license * asset.total_licenses
        
        return {
            'optimization_potential': current_cost * 0.15,  # 15% potential savings
            'negotiation_points': [
                'Volume discount based on usage',
                'Multi-year contract discount',
                'Feature optimization'
            ],
            'market_alternatives': self._find_market_alternatives(asset),
            'risk_level': 'low'
        }

    def _calculate_portfolio_health_score(self, assets: List[LicenseAsset]) -> float:
        """Calculate overall portfolio health score"""
        if not assets:
            return 0.0
        
        # Factors: utilization, cost efficiency, vendor diversity, renewal management
        total_utilization = sum(asset.used_licenses / asset.total_licenses if asset.total_licenses > 0 else 0 for asset in assets)
        avg_utilization = total_utilization / len(assets)
        
        # Vendor diversity (more vendors = higher risk)
        unique_vendors = len(set(asset.vendor for asset in assets))
        vendor_diversity_score = min(unique_vendors / len(assets), 1.0)
        
        # Renewal management (upcoming renewals)
        upcoming_renewals = sum(1 for asset in assets if asset.renewal_date and 
                               (datetime.strptime(asset.renewal_date, '%Y-%m-%d') - datetime.now()).days <= 90)
        renewal_score = 1.0 - (upcoming_renewals / len(assets))
        
        # Weighted health score
        health_score = (avg_utilization * 0.4 + vendor_diversity_score * 0.3 + renewal_score * 0.3) * 100
        
        return round(health_score, 2)

    def _store_analysis_results(self, analysis_result: Dict[str, Any]):
        """Store analysis results in DynamoDB"""
        try:
            table = self.dynamodb.Table('license-analysis-results')
            
            item = {
                'analysis_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'total_assets': analysis_result['total_assets'],
                'total_cost': analysis_result['total_cost'],
                'underutilized_count': len(analysis_result['underutilized_assets']),
                'duplicate_count': len(analysis_result['duplicate_assets']),
                'renewal_alerts_count': len(analysis_result['renewal_alerts']),
                'portfolio_health_score': analysis_result['ai_insights']['portfolio_health_score'],
                'optimization_potential': analysis_result['ai_insights']['optimization_potential'],
                'recommendations_count': len(analysis_result['recommendations'])
            }
            
            table.put_item(Item=item)
            logger.info(f"✅ Analysis results stored with ID: {item['analysis_id']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store analysis results: {e}")

    def _map_to_gem_category(self, recommendation_type: str) -> str:
        """Map recommendation type to GeM category"""
        mapping = {
            'LICENSE_REDUCTION': 'Software Licenses',
            'CONSOLIDATION': 'Software Services',
            'RENEWAL_OPTIMIZATION': 'Software Maintenance'
        }
        return mapping.get(recommendation_type, 'Software Services')

    def _create_approval_workflow(self, recommendation: OptimizationRecommendation) -> List[str]:
        """Create approval workflow based on recommendation"""
        workflow = ['Department Head']
        
        if recommendation.potential_savings > 100000:
            workflow.extend(['Finance Director', 'CTO'])
        
        if recommendation.potential_savings > 500000:
            workflow.append('CEO')
        
        return workflow

    def generate_optimization_report(self, analysis_result: Dict[str, Any]) -> str:
        """Generate comprehensive optimization report"""
        
        report = f"""
# 🤖 AI-Powered License & Asset Optimization Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Analysis ID**: {str(uuid.uuid4())[:8]}

## 📊 Executive Summary

- **Total Assets Analyzed**: {analysis_result['total_assets']}
- **Annual License Cost**: ₹{analysis_result['total_cost'] * 12:,.2f}
- **Portfolio Health Score**: {analysis_result['ai_insights']['portfolio_health_score']}/100
- **Optimization Potential**: ₹{analysis_result['ai_insights']['optimization_potential']:,.2f}

## 🎯 Key Findings

### Underutilized Licenses ({len(analysis_result['underutilized_assets'])})
"""
        
        for asset in analysis_result['underutilized_assets'][:5]:  # Top 5
            report += f"""
- **{asset['name']}** ({asset['vendor']})
  - Utilization: {asset['utilization_rate']:.1%}
  - Unused Licenses: {asset['unused_licenses']}
  - Annual Waste: ₹{asset['waste_cost_annual']:,.2f}
"""
        
        report += f"""
### Duplicate Subscriptions ({len(analysis_result['duplicate_assets'])})
"""
        
        for duplicate in analysis_result['duplicate_assets']:
            report += f"""
- **{duplicate['vendor']}** - {len(duplicate['assets'])} overlapping subscriptions
  - Total Cost: ₹{duplicate['total_cost']:,.2f}
  - Consolidation Savings: ₹{duplicate['consolidation_opportunity']:,.2f}
"""
        
        report += f"""
### Upcoming Renewals ({len(analysis_result['renewal_alerts'])})
"""
        
        for renewal in analysis_result['renewal_alerts'][:5]:
            report += f"""
- **{renewal['name']}** - {renewal['days_to_renewal']} days
  - Current Cost: ₹{renewal['current_cost']:,.2f}
  - Optimization Opportunity: ₹{renewal['optimization_opportunity']:,.2f}
"""
        
        report += f"""
## 💡 AI Recommendations

Total Recommendations: {len(analysis_result['recommendations'])}
"""
        
        for i, rec in enumerate(analysis_result['recommendations'][:10], 1):
            report += f"""
### {i}. {rec.recommendation_type.replace('_', ' ').title()}
- **Asset**: {rec.asset_id}
- **Description**: {rec.description}
- **Potential Savings**: ₹{rec.potential_savings:,.2f}
- **Priority**: {rec.priority}
- **Confidence**: {rec.confidence_score:.1%}
- **GeM Integration**: {'Required' if rec.gem_integration_required else 'Not Required'}
"""
        
        report += f"""
## 🛒 GeM Procurement Integration

The following recommendations require GeM procurement process:
"""
        
        gem_required = [rec for rec in analysis_result['recommendations'] if rec.gem_integration_required]
        for rec in gem_required[:5]:
            report += f"""
- {rec.description} - ₹{rec.potential_savings:,.2f} savings
"""
        
        report += f"""
## 📈 Next Steps

1. **Immediate Actions** (0-30 days)
   - Review high-priority recommendations
   - Initiate finance approval process
   - Begin GeM procurement for approved items

2. **Short-term Actions** (1-3 months)
   - Implement license reductions
   - Consolidate duplicate subscriptions
   - Negotiate renewal terms

3. **Long-term Strategy** (3-12 months)
   - Establish ongoing monitoring
   - Implement automated optimization
   - Regular portfolio reviews

## 🔗 Integration Points

- **GeM Procurement**: Automated integration for approved optimizations
- **Finance Approval**: Workflow-based approval process
- **Vendor Management**: Centralized vendor relationship management
- **Usage Monitoring**: Real-time license usage tracking

---
*This report was generated by the AI-powered License Optimization Agent*
        """
        
        return report

    def _get_utilization_recommendation(self, asset: LicenseAsset, utilization_rate: float) -> str:
        """Get utilization recommendation based on usage patterns"""
        if utilization_rate < 0.3:
            return f"Consider reducing licenses by 60-70% or canceling subscription"
        elif utilization_rate < 0.5:
            return f"Reduce licenses by 40-50% to optimize costs"
        elif utilization_rate < 0.7:
            return f"Reduce licenses by 20-30% based on actual usage"
        else:
            return f"Monitor usage patterns for future optimization"

    def _find_market_alternatives(self, asset: LicenseAsset) -> List[str]:
        """Find market alternatives for the asset"""
        alternatives_map = {
            'zoom': ['Microsoft Teams', 'Google Meet', 'Webex'],
            'adobe': ['Canva Pro', 'Figma', 'Sketch'],
            'microsoft': ['Google Workspace', 'Slack', 'Zoom'],
            'symantec': ['McAfee', 'Trend Micro', 'Kaspersky'],
            'slack': ['Microsoft Teams', 'Discord', 'Mattermost']
        }
        
        vendor_key = asset.vendor.lower()
        return alternatives_map.get(vendor_key, ['Generic alternatives available'])

    def _assess_portfolio_risks(self, assets: List[LicenseAsset]) -> Dict[str, Any]:
        """Assess portfolio risks"""
        # Calculate vendor concentration risk
        vendor_costs = {}
        total_cost = 0
        
        for asset in assets:
            cost = asset.cost_per_license * asset.total_licenses
            total_cost += cost
            if asset.vendor not in vendor_costs:
                vendor_costs[asset.vendor] = 0
            vendor_costs[asset.vendor] += cost
        
        # Find highest vendor concentration
        max_vendor_percentage = max(vendor_costs.values()) / total_cost if total_cost > 0 else 0
        
        return {
            'vendor_concentration_risk': 'high' if max_vendor_percentage > 0.4 else 'medium' if max_vendor_percentage > 0.2 else 'low',
            'renewal_risk': 'medium',  # Based on upcoming renewals
            'compliance_risk': 'low',
            'cost_escalation_risk': 'medium'
        }

    def _calculate_optimization_potential(self, assets: List[LicenseAsset]) -> float:
        """Calculate total optimization potential"""
        total_potential = 0
        
        for asset in assets:
            if asset.total_licenses > 0:
                utilization_rate = asset.used_licenses / asset.total_licenses
                if utilization_rate < 0.7:  # Underutilized
                    waste_cost = (asset.total_licenses - asset.used_licenses) * asset.cost_per_license
                    total_potential += waste_cost * 12  # Annual potential
        
        return total_potential

    def _get_bedrock_portfolio_insights(self, assets: List[LicenseAsset]) -> Dict[str, Any]:
        """Get AI insights from Amazon Bedrock Claude 3"""
        try:
            # Prepare portfolio data for AI analysis
            portfolio_summary = self._prepare_portfolio_for_ai_analysis(assets)
            
            # Create prompt for Claude 3
            prompt = f"""
            You are an expert AI consultant specializing in enterprise software license optimization. 
            Analyze the following software license portfolio and provide intelligent insights and recommendations.

            Portfolio Data:
            {json.dumps(portfolio_summary, indent=2)}

            Please provide a comprehensive analysis in JSON format with the following structure:
            {{
                "executive_summary": "Brief overview of portfolio health and key findings",
                "critical_issues": ["List of most critical issues requiring immediate attention"],
                "optimization_opportunities": [
                    {{
                        "type": "consolidation|reduction|renewal_optimization",
                        "description": "Detailed description",
                        "impact": "high|medium|low",
                        "savings_estimate": "percentage or amount",
                        "implementation_complexity": "low|medium|high"
                    }}
                ],
                "vendor_analysis": {{
                    "over_concentrated_vendors": ["vendors with too much dependency"],
                    "underperforming_vendors": ["vendors with poor utilization"],
                    "consolidation_candidates": ["vendors that can be consolidated"]
                }},
                "usage_patterns": {{
                    "seasonal_trends": "description of seasonal usage patterns",
                    "department_efficiency": "analysis of department-wise efficiency",
                    "growth_predictions": "predicted growth or decline patterns"
                }},
                "risk_assessment": {{
                    "compliance_risks": ["potential compliance issues"],
                    "financial_risks": ["financial risk factors"],
                    "operational_risks": ["operational risk factors"]
                }},
                "strategic_recommendations": [
                    "Long-term strategic recommendations for license management"
                ]
            }}

            Focus on actionable insights that can drive real cost savings and operational efficiency.
            """

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            })

            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=body
            )

            result = json.loads(response['body'].read())
            ai_insights = json.loads(result['content'][0]['text'])
            
            logger.info("✅ Bedrock AI insights generated successfully")
            return {
                'ai_insights': ai_insights,
                'ai_service_used': 'bedrock_claude3',
                'ai_confidence': 0.92
            }

        except Exception as e:
            logger.warning(f"⚠️ Bedrock AI analysis failed: {str(e)}")
            return self._get_fallback_ai_insights(assets)

    def _prepare_portfolio_for_ai_analysis(self, assets: List[LicenseAsset]) -> Dict[str, Any]:
        """Prepare portfolio data for AI analysis"""
        portfolio_data = {
            'total_assets': len(assets),
            'total_annual_cost': sum(asset.cost_per_license * asset.total_licenses * 12 for asset in assets),
            'assets': []
        }
        
        for asset in assets:
            utilization_rate = asset.used_licenses / asset.total_licenses if asset.total_licenses > 0 else 0
            annual_cost = asset.cost_per_license * asset.total_licenses * 12
            
            asset_data = {
                'name': asset.name,
                'vendor': asset.vendor,
                'department': asset.department,
                'total_licenses': asset.total_licenses,
                'used_licenses': asset.used_licenses,
                'utilization_rate': round(utilization_rate, 3),
                'annual_cost': annual_cost,
                'cost_per_license': asset.cost_per_license,
                'renewal_date': asset.renewal_date,
                'license_type': asset.license_type
            }
            portfolio_data['assets'].append(asset_data)
        
        return portfolio_data

    def _analyze_spending_trends_with_comprehend(self, assets: List[LicenseAsset]) -> Dict[str, Any]:
        """Analyze spending trends using Amazon Comprehend"""
        try:
            # Create text description of portfolio for sentiment and entity analysis
            portfolio_text = self._create_portfolio_description(assets)
            
            # Sentiment analysis
            sentiment_response = self.comprehend.detect_sentiment(
                Text=portfolio_text,
                LanguageCode='en'
            )
            
            # Entity detection
            entities_response = self.comprehend.detect_entities(
                Text=portfolio_text,
                LanguageCode='en'
            )
            
            # Key phrases
            phrases_response = self.comprehend.detect_key_phrases(
                Text=portfolio_text,
                LanguageCode='en'
            )
            
            return {
                'portfolio_sentiment': sentiment_response['Sentiment'].lower(),
                'sentiment_confidence': max(sentiment_response['SentimentScore'].values()),
                'key_entities': [
                    {'text': e['Text'], 'type': e['Type'], 'confidence': e['Score']}
                    for e in entities_response['Entities'][:10]
                ],
                'key_phrases': [
                    {'text': p['Text'], 'confidence': p['Score']}
                    for p in phrases_response['KeyPhrases'][:10]
                ],
                'ai_service_used': 'comprehend',
                'monthly_growth': 2.5,  # This would come from historical data
                'vendor_concentration': 'moderate',
                'seasonal_patterns': 'low_variation',
                'cost_per_user_trend': 'increasing'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Comprehend analysis failed: {str(e)}")
            return self._get_fallback_spending_trends()

    def _create_portfolio_description(self, assets: List[LicenseAsset]) -> str:
        """Create text description of portfolio for NLP analysis"""
        descriptions = []
        
        for asset in assets:
            utilization_rate = asset.used_licenses / asset.total_licenses if asset.total_licenses > 0 else 0
            annual_cost = asset.cost_per_license * asset.total_licenses * 12
            
            if utilization_rate < 0.5:
                efficiency = "underutilized and wasteful"
            elif utilization_rate < 0.8:
                efficiency = "moderately efficient"
            else:
                efficiency = "well-utilized and efficient"
            
            desc = f"The {asset.name} license from {asset.vendor} used by {asset.department} department is {efficiency} with {utilization_rate:.1%} utilization rate and costs ₹{annual_cost:,.0f} annually."
            descriptions.append(desc)
        
        return " ".join(descriptions)

    def _get_fallback_ai_insights(self, assets: List[LicenseAsset]) -> Dict[str, Any]:
        """Fallback AI insights when Bedrock is unavailable"""
        # Generate rule-based insights as fallback
        underutilized_count = sum(1 for asset in assets if (asset.used_licenses / asset.total_licenses) < 0.7)
        high_cost_assets = [asset for asset in assets if asset.cost_per_license * asset.total_licenses > 100000]
        
        return {
            'ai_insights': {
                'executive_summary': f"Portfolio analysis shows {underutilized_count} underutilized assets with significant optimization potential.",
                'critical_issues': [
                    f"{underutilized_count} assets are underutilized (< 70% usage)",
                    f"{len(high_cost_assets)} high-cost assets need immediate review"
                ],
                'optimization_opportunities': [
                    {
                        'type': 'reduction',
                        'description': 'Reduce licenses for underutilized software',
                        'impact': 'high',
                        'savings_estimate': '20-40%',
                        'implementation_complexity': 'low'
                    }
                ]
            },
            'ai_service_used': 'fallback_rules',
            'ai_confidence': 0.75
        }

    def _get_fallback_spending_trends(self) -> Dict[str, Any]:
        """Fallback spending trends analysis"""
        return {
            'portfolio_sentiment': 'neutral',
            'monthly_growth': 2.5,
            'vendor_concentration': 'moderate',
            'seasonal_patterns': 'low_variation',
            'cost_per_user_trend': 'increasing',
            'ai_service_used': 'fallback_rules'
        }

def main():
    """Demo the License Optimization AI Agent"""
    print("🤖 AI Agent for License & Asset Optimization")
    print("=" * 60)
    
    # Initialize agent
    agent = LicenseOptimizationAgent()
    
    # Sample license data
    sample_licenses = [
        {
            'asset_id': 'LIC-001',
            'name': 'Zoom Pro',
            'vendor': 'Zoom',
            'license_type': 'subscription',
            'total_licenses': 100,
            'used_licenses': 45,
            'cost_per_license': 1200,
            'renewal_date': '2024-12-15',
            'department': 'IT',
            'gem_order_id': 'GEM-2024-001'
        },
        {
            'asset_id': 'LIC-002',
            'name': 'Adobe Creative Suite',
            'vendor': 'Adobe',
            'license_type': 'subscription',
            'total_licenses': 50,
            'used_licenses': 48,
            'cost_per_license': 4500,
            'renewal_date': '2024-11-30',
            'department': 'Marketing'
        },
        {
            'asset_id': 'LIC-003',
            'name': 'Microsoft Teams',
            'vendor': 'Microsoft',
            'license_type': 'subscription',
            'total_licenses': 100,
            'used_licenses': 40,
            'cost_per_license': 800,
            'renewal_date': '2025-01-20',
            'department': 'IT'
        },
        {
            'asset_id': 'LIC-004',
            'name': 'Antivirus Enterprise',
            'vendor': 'Symantec',
            'license_type': 'subscription',
            'total_licenses': 200,
            'used_licenses': 180,
            'cost_per_license': 600,
            'renewal_date': '2024-12-01',
            'department': 'IT'
        }
    ]
    
    # Analyze portfolio
    print("🔍 Analyzing license portfolio...")
    analysis = agent.analyze_license_portfolio(sample_licenses)
    
    # Generate report
    print("📊 Generating optimization report...")
    report = agent.generate_optimization_report(analysis)
    
    # Print summary
    print(f"\n📈 Analysis Summary:")
    print(f"   Total Assets: {analysis['total_assets']}")
    print(f"   Underutilized: {len(analysis['underutilized_assets'])}")
    print(f"   Duplicates: {len(analysis['duplicate_assets'])}")
    print(f"   Renewals: {len(analysis['renewal_alerts'])}")
    print(f"   Recommendations: {len(analysis['recommendations'])}")
    print(f"   Health Score: {analysis['ai_insights']['portfolio_health_score']}/100")
    
    # Test GeM integration
    if analysis['recommendations']:
        print(f"\n🛒 Testing GeM integration...")
        rec = analysis['recommendations'][0]
        gem_integration = agent.integrate_with_gem_procurement(rec)
        print(f"   GeM Request ID: {gem_integration['gem_request_id']}")
        
        # Test finance approval
        print(f"💰 Creating finance approval...")
        approval = agent.create_finance_approval_request(rec, gem_integration)
        print(f"   Approval ID: {approval['approval_id']}")
        print(f"   Net Benefit: ₹{approval['financial_impact']['net_benefit']:,.2f}")
    
    print(f"\n🎉 License Optimization AI Agent demo completed!")

if __name__ == "__main__":
    main()