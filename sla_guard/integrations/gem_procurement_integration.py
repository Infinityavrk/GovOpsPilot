#!/usr/bin/env python3
"""
GeM Procurement Integration Module
Integrates license optimization recommendations with Government e-Marketplace (GeM)
"""

import json
import requests
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import uuid
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GeMProcurementRequest:
    """GeM procurement request structure"""
    gem_request_id: str
    recommendation_id: str
    category: str
    subcategory: str
    estimated_value: float
    description: str
    technical_specifications: Dict[str, Any]
    delivery_timeline: str
    approval_status: str
    gem_order_id: Optional[str] = None
    vendor_quotes: Optional[List[Dict]] = None

@dataclass
class FinanceApproval:
    """Finance approval structure"""
    approval_id: str
    request_id: str
    approval_level: str
    approvers: List[str]
    financial_impact: Dict[str, float]
    business_justification: str
    status: str
    approved_amount: Optional[float] = None

class GeMProcurementIntegrator:
    def __init__(self, region='us-east-1'):
        """Initialize GeM Procurement Integrator"""
        self.region = region
        
        # Initialize AWS clients
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.stepfunctions = boto3.client('stepfunctions', region_name=region)
        
        # GeM API configuration (mock endpoints for demo)
        self.gem_api_base = "https://api.gem.gov.in/v1"
        self.gem_api_key = "your-gem-api-key"
        
        # Table names
        self.gem_requests_table = 'gem-procurement-requests'
        self.finance_approvals_table = 'finance-approvals'
        self.vendor_catalog_table = 'gem-vendor-catalog'
        
        logger.info("🛒 GeM Procurement Integrator initialized")

    def create_gem_procurement_request(self, recommendation: Dict[str, Any]) -> GeMProcurementRequest:
        """Create GeM procurement request from optimization recommendation"""
        logger.info(f"🛒 Creating GeM procurement request for recommendation {recommendation.get('recommendation_id')}")
        
        # Map recommendation to GeM categories
        gem_category = self._map_to_gem_category(recommendation['recommendation_type'])
        
        # Generate technical specifications
        tech_specs = self._generate_technical_specifications(recommendation)
        
        # Create procurement request
        gem_request = GeMProcurementRequest(
            gem_request_id=f"GEM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            recommendation_id=recommendation['recommendation_id'],
            category=gem_category['category'],
            subcategory=gem_category['subcategory'],
            estimated_value=recommendation['potential_savings'],
            description=self._generate_procurement_description(recommendation),
            technical_specifications=tech_specs,
            delivery_timeline=self._calculate_delivery_timeline(recommendation),
            approval_status='PENDING_FINANCE_APPROVAL'
        )
        
        # Store in DynamoDB
        self._store_gem_request(gem_request)
        
        # Initiate finance approval workflow
        finance_approval = self._initiate_finance_approval(gem_request, recommendation)
        
        return gem_request

    def _map_to_gem_category(self, recommendation_type: str) -> Dict[str, str]:
        """Map recommendation type to GeM category"""
        category_mapping = {
            'LICENSE_REDUCTION': {
                'category': 'Information Technology',
                'subcategory': 'Software Licenses',
                'gem_code': 'IT-SW-001'
            },
            'CONSOLIDATION': {
                'category': 'Information Technology',
                'subcategory': 'Software Services',
                'gem_code': 'IT-SV-002'
            },
            'RENEWAL_OPTIMIZATION': {
                'category': 'Information Technology',
                'subcategory': 'Software Maintenance',
                'gem_code': 'IT-MT-003'
            }
        }
        
        return category_mapping.get(recommendation_type, {
            'category': 'Information Technology',
            'subcategory': 'Software Services',
            'gem_code': 'IT-SV-000'
        })

    def _generate_technical_specifications(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate technical specifications for GeM procurement"""
        
        base_specs = {
            'software_type': 'Enterprise Software License',
            'deployment_model': 'Cloud/On-Premise',
            'user_capacity': 'As per requirement',
            'support_level': '24x7 Premium Support',
            'compliance_requirements': [
                'ISO 27001 Certified',
                'SOC 2 Type II Compliant',
                'GDPR Compliant',
                'Government Security Standards'
            ],
            'integration_requirements': [
                'Single Sign-On (SSO)',
                'Active Directory Integration',
                'API Access',
                'Audit Logging'
            ],
            'performance_requirements': {
                'availability': '99.9%',
                'response_time': '<2 seconds',
                'concurrent_users': 'As per license count',
                'data_backup': 'Daily automated backups'
            }
        }
        
        # Customize based on recommendation type
        if recommendation['recommendation_type'] == 'LICENSE_REDUCTION':
            base_specs['license_optimization'] = {
                'current_licenses': recommendation.get('current_count', 0),
                'optimized_licenses': recommendation.get('recommended_count', 0),
                'reduction_percentage': recommendation.get('reduction_percentage', 0)
            }
        
        elif recommendation['recommendation_type'] == 'CONSOLIDATION':
            base_specs['consolidation_requirements'] = {
                'platforms_to_consolidate': recommendation.get('platforms', []),
                'unified_platform_features': recommendation.get('required_features', []),
                'migration_support': 'Full migration assistance required'
            }
        
        return base_specs

    def _generate_procurement_description(self, recommendation: Dict[str, Any]) -> str:
        """Generate detailed procurement description"""
        
        description = f"""
PROCUREMENT REQUEST: {recommendation['recommendation_type'].replace('_', ' ').title()}

Objective: {recommendation['description']}

Business Justification:
- Estimated Annual Savings: ₹{recommendation['potential_savings']:,.2f}
- Optimization Type: {recommendation['recommendation_type']}
- Priority Level: {recommendation['priority']}
- Confidence Score: {recommendation['confidence_score']:.1%}

Current State:
- Asset ID: {recommendation['asset_id']}
- Current Cost Impact: High
- Utilization Efficiency: Suboptimal

Proposed Solution:
{recommendation['description']}

Expected Outcomes:
- Cost Reduction: ₹{recommendation['potential_savings']:,.2f} annually
- Improved License Utilization
- Enhanced Operational Efficiency
- Better Vendor Management

Compliance Requirements:
- Government Procurement Guidelines
- Financial Approval Process
- Vendor Empanelment Verification
- Security and Audit Standards

Timeline: {self._calculate_delivery_timeline(recommendation)}
        """
        
        return description.strip()

    def _calculate_delivery_timeline(self, recommendation: Dict[str, Any]) -> str:
        """Calculate delivery timeline based on recommendation complexity"""
        
        complexity_mapping = {
            'LICENSE_REDUCTION': '30-45 days',
            'CONSOLIDATION': '60-90 days',
            'RENEWAL_OPTIMIZATION': '15-30 days'
        }
        
        return complexity_mapping.get(recommendation['recommendation_type'], '45-60 days')

    def _initiate_finance_approval(self, gem_request: GeMProcurementRequest, recommendation: Dict[str, Any]) -> FinanceApproval:
        """Initiate finance approval workflow"""
        
        # Determine approval level based on amount
        approval_level = self._determine_approval_level(gem_request.estimated_value)
        
        # Get required approvers
        approvers = self._get_required_approvers(approval_level)
        
        # Calculate financial impact
        financial_impact = {
            'potential_savings': gem_request.estimated_value,
            'implementation_cost': self._estimate_implementation_cost(recommendation),
            'net_benefit': gem_request.estimated_value - self._estimate_implementation_cost(recommendation),
            'payback_period_months': self._calculate_payback_period(recommendation),
            'roi_percentage': self._calculate_roi(recommendation)
        }
        
        # Create finance approval request
        finance_approval = FinanceApproval(
            approval_id=f"FIN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            request_id=gem_request.gem_request_id,
            approval_level=approval_level,
            approvers=approvers,
            financial_impact=financial_impact,
            business_justification=self._generate_business_justification(recommendation, financial_impact),
            status='PENDING_APPROVAL'
        )
        
        # Store finance approval
        self._store_finance_approval(finance_approval)
        
        # Start approval workflow
        self._start_approval_workflow(finance_approval)
        
        return finance_approval

    def _determine_approval_level(self, amount: float) -> str:
        """Determine approval level based on amount"""
        if amount >= 5000000:  # 50 Lakhs
            return 'LEVEL_4_CEO'
        elif amount >= 2000000:  # 20 Lakhs
            return 'LEVEL_3_CTO'
        elif amount >= 500000:  # 5 Lakhs
            return 'LEVEL_2_FINANCE_DIRECTOR'
        else:
            return 'LEVEL_1_DEPARTMENT_HEAD'

    def _get_required_approvers(self, approval_level: str) -> List[str]:
        """Get required approvers for approval level"""
        approver_mapping = {
            'LEVEL_1_DEPARTMENT_HEAD': ['dept_head@organization.gov.in'],
            'LEVEL_2_FINANCE_DIRECTOR': ['dept_head@organization.gov.in', 'finance_director@organization.gov.in'],
            'LEVEL_3_CTO': ['dept_head@organization.gov.in', 'finance_director@organization.gov.in', 'cto@organization.gov.in'],
            'LEVEL_4_CEO': ['dept_head@organization.gov.in', 'finance_director@organization.gov.in', 'cto@organization.gov.in', 'ceo@organization.gov.in']
        }
        
        return approver_mapping.get(approval_level, ['dept_head@organization.gov.in'])

    def _estimate_implementation_cost(self, recommendation: Dict[str, Any]) -> float:
        """Estimate implementation cost"""
        base_cost = recommendation['potential_savings'] * 0.05  # 5% of savings
        
        complexity_multiplier = {
            'LICENSE_REDUCTION': 1.0,
            'CONSOLIDATION': 2.0,
            'RENEWAL_OPTIMIZATION': 0.5
        }
        
        multiplier = complexity_multiplier.get(recommendation['recommendation_type'], 1.0)
        
        return base_cost * multiplier

    def _calculate_payback_period(self, recommendation: Dict[str, Any]) -> int:
        """Calculate payback period in months"""
        implementation_cost = self._estimate_implementation_cost(recommendation)
        monthly_savings = recommendation['potential_savings'] / 12
        
        if monthly_savings > 0:
            return max(int(implementation_cost / monthly_savings), 1)
        return 12

    def _calculate_roi(self, recommendation: Dict[str, Any]) -> float:
        """Calculate ROI percentage"""
        implementation_cost = self._estimate_implementation_cost(recommendation)
        annual_savings = recommendation['potential_savings']
        
        if implementation_cost > 0:
            return ((annual_savings - implementation_cost) / implementation_cost) * 100
        return 0.0

    def _generate_business_justification(self, recommendation: Dict[str, Any], financial_impact: Dict[str, float]) -> str:
        """Generate business justification"""
        
        justification = f"""
BUSINESS JUSTIFICATION FOR LICENSE OPTIMIZATION

1. FINANCIAL BENEFITS:
   - Annual Savings: ₹{financial_impact['potential_savings']:,.2f}
   - Implementation Cost: ₹{financial_impact['implementation_cost']:,.2f}
   - Net Annual Benefit: ₹{financial_impact['net_benefit']:,.2f}
   - ROI: {financial_impact['roi_percentage']:.1f}%
   - Payback Period: {financial_impact['payback_period_months']} months

2. OPERATIONAL BENEFITS:
   - Improved license utilization efficiency
   - Reduced vendor management complexity
   - Enhanced compliance and audit readiness
   - Streamlined procurement processes

3. STRATEGIC ALIGNMENT:
   - Supports digital transformation initiatives
   - Aligns with cost optimization mandates
   - Enhances IT governance and oversight
   - Improves budget predictability

4. RISK MITIGATION:
   - Reduces over-licensing costs
   - Eliminates duplicate subscriptions
   - Improves vendor relationship management
   - Ensures compliance with licensing terms

5. IMPLEMENTATION APPROACH:
   - Phased implementation to minimize disruption
   - Comprehensive change management
   - User training and support
   - Continuous monitoring and optimization

This optimization initiative directly supports the organization's mandate for efficient resource utilization and cost-effective IT operations while maintaining service quality and compliance standards.
        """
        
        return justification.strip()

    def search_gem_catalog(self, category: str, specifications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search GeM catalog for matching products/services"""
        logger.info(f"🔍 Searching GeM catalog for category: {category}")
        
        # Mock GeM catalog search (in production, this would call actual GeM APIs)
        mock_catalog_results = [
            {
                'gem_product_id': 'GEM-SW-001',
                'product_name': 'Enterprise Software License - Tier 1',
                'vendor_name': 'Approved Vendor A',
                'vendor_rating': 4.5,
                'price_per_license': 1000,
                'minimum_quantity': 10,
                'delivery_timeline': '15-30 days',
                'compliance_certifications': ['ISO 27001', 'SOC 2'],
                'support_level': '24x7 Premium'
            },
            {
                'gem_product_id': 'GEM-SW-002',
                'product_name': 'Enterprise Software License - Tier 2',
                'vendor_name': 'Approved Vendor B',
                'vendor_rating': 4.2,
                'price_per_license': 850,
                'minimum_quantity': 25,
                'delivery_timeline': '20-35 days',
                'compliance_certifications': ['ISO 27001'],
                'support_level': 'Business Hours'
            }
        ]
        
        return mock_catalog_results

    def create_gem_bid_request(self, gem_request: GeMProcurementRequest, catalog_items: List[Dict]) -> Dict[str, Any]:
        """Create GeM bid request"""
        logger.info(f"📝 Creating GeM bid request for {gem_request.gem_request_id}")
        
        bid_request = {
            'bid_request_id': f"BID-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}",
            'gem_request_id': gem_request.gem_request_id,
            'category': gem_request.category,
            'subcategory': gem_request.subcategory,
            'estimated_value': gem_request.estimated_value,
            'technical_specifications': gem_request.technical_specifications,
            'bid_submission_deadline': (datetime.now() + timedelta(days=15)).isoformat(),
            'evaluation_criteria': {
                'technical_score_weightage': 70,
                'commercial_score_weightage': 30,
                'minimum_technical_score': 60
            },
            'eligible_vendors': [item['vendor_name'] for item in catalog_items],
            'bid_validity_period': '90 days',
            'delivery_timeline': gem_request.delivery_timeline,
            'payment_terms': 'As per GeM guidelines',
            'status': 'PUBLISHED'
        }
        
        return bid_request

    def process_vendor_quotes(self, bid_request_id: str, quotes: List[Dict]) -> Dict[str, Any]:
        """Process and evaluate vendor quotes"""
        logger.info(f"📊 Processing vendor quotes for bid {bid_request_id}")
        
        evaluation_results = []
        
        for quote in quotes:
            # Technical evaluation
            technical_score = self._evaluate_technical_compliance(quote)
            
            # Commercial evaluation
            commercial_score = self._evaluate_commercial_terms(quote)
            
            # Overall score
            overall_score = (technical_score * 0.7) + (commercial_score * 0.3)
            
            evaluation_results.append({
                'vendor_name': quote['vendor_name'],
                'quote_id': quote['quote_id'],
                'technical_score': technical_score,
                'commercial_score': commercial_score,
                'overall_score': overall_score,
                'quoted_price': quote['total_price'],
                'delivery_timeline': quote['delivery_timeline'],
                'compliance_status': technical_score >= 60,
                'recommendation': 'ACCEPT' if overall_score >= 70 else 'REJECT'
            })
        
        # Sort by overall score
        evaluation_results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return {
            'bid_request_id': bid_request_id,
            'total_quotes_received': len(quotes),
            'qualified_quotes': len([r for r in evaluation_results if r['compliance_status']]),
            'evaluation_results': evaluation_results,
            'recommended_vendor': evaluation_results[0] if evaluation_results else None,
            'evaluation_completed_at': datetime.now().isoformat()
        }

    def _evaluate_technical_compliance(self, quote: Dict[str, Any]) -> float:
        """Evaluate technical compliance of vendor quote"""
        # Mock technical evaluation
        compliance_factors = [
            quote.get('iso_certified', False),
            quote.get('soc2_compliant', False),
            quote.get('api_support', False),
            quote.get('sso_integration', False),
            quote.get('audit_logging', False)
        ]
        
        compliance_score = sum(compliance_factors) / len(compliance_factors) * 100
        return min(compliance_score, 100)

    def _evaluate_commercial_terms(self, quote: Dict[str, Any]) -> float:
        """Evaluate commercial terms of vendor quote"""
        # Mock commercial evaluation based on price competitiveness
        base_price = quote.get('total_price', 0)
        market_price = base_price * 1.2  # Assume 20% higher market price
        
        if base_price <= market_price * 0.8:  # 20% below market
            return 100
        elif base_price <= market_price:
            return 80
        elif base_price <= market_price * 1.1:  # 10% above market
            return 60
        else:
            return 40

    def _store_gem_request(self, gem_request: GeMProcurementRequest):
        """Store GeM request in DynamoDB"""
        try:
            table = self.dynamodb.Table(self.gem_requests_table)
            
            item = {
                'gem_request_id': gem_request.gem_request_id,
                'recommendation_id': gem_request.recommendation_id,
                'category': gem_request.category,
                'subcategory': gem_request.subcategory,
                'estimated_value': gem_request.estimated_value,
                'description': gem_request.description,
                'technical_specifications': json.dumps(gem_request.technical_specifications),
                'delivery_timeline': gem_request.delivery_timeline,
                'approval_status': gem_request.approval_status,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            table.put_item(Item=item)
            logger.info(f"✅ GeM request stored: {gem_request.gem_request_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store GeM request: {e}")

    def _store_finance_approval(self, finance_approval: FinanceApproval):
        """Store finance approval in DynamoDB"""
        try:
            table = self.dynamodb.Table(self.finance_approvals_table)
            
            item = {
                'approval_id': finance_approval.approval_id,
                'request_id': finance_approval.request_id,
                'approval_level': finance_approval.approval_level,
                'approvers': finance_approval.approvers,
                'financial_impact': finance_approval.financial_impact,
                'business_justification': finance_approval.business_justification,
                'status': finance_approval.status,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            table.put_item(Item=item)
            logger.info(f"✅ Finance approval stored: {finance_approval.approval_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store finance approval: {e}")

    def _start_approval_workflow(self, finance_approval: FinanceApproval):
        """Start Step Functions approval workflow"""
        try:
            # Mock Step Functions workflow execution
            workflow_input = {
                'approval_id': finance_approval.approval_id,
                'approvers': finance_approval.approvers,
                'approval_level': finance_approval.approval_level,
                'estimated_value': finance_approval.financial_impact['potential_savings']
            }
            
            logger.info(f"🔄 Started approval workflow for {finance_approval.approval_id}")
            
            # Send notification to first approver
            self._send_approval_notification(finance_approval)
            
        except Exception as e:
            logger.error(f"❌ Failed to start approval workflow: {e}")

    def _send_approval_notification(self, finance_approval: FinanceApproval):
        """Send approval notification via SNS"""
        try:
            message = f"""
Finance Approval Required

Approval ID: {finance_approval.approval_id}
Request ID: {finance_approval.request_id}
Approval Level: {finance_approval.approval_level}

Financial Impact:
- Potential Savings: ₹{finance_approval.financial_impact['potential_savings']:,.2f}
- Net Benefit: ₹{finance_approval.financial_impact['net_benefit']:,.2f}
- ROI: {finance_approval.financial_impact['roi_percentage']:.1f}%

Please review and approve via the finance portal.
            """
            
            # Mock SNS publish
            logger.info(f"📧 Approval notification sent for {finance_approval.approval_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send approval notification: {e}")

def main():
    """Demo GeM Procurement Integration"""
    print("🛒 GeM Procurement Integration Demo")
    print("=" * 50)
    
    # Initialize integrator
    integrator = GeMProcurementIntegrator()
    
    # Sample recommendation
    sample_recommendation = {
        'recommendation_id': 'REC-001',
        'asset_id': 'LIC-001',
        'recommendation_type': 'LICENSE_REDUCTION',
        'description': 'Reduce Zoom Pro licenses from 100 to 60 based on usage patterns',
        'potential_savings': 576000,
        'confidence_score': 0.85,
        'priority': 'HIGH'
    }
    
    # Create GeM procurement request
    print("🛒 Creating GeM procurement request...")
    gem_request = integrator.create_gem_procurement_request(sample_recommendation)
    print(f"   GeM Request ID: {gem_request.gem_request_id}")
    
    # Search GeM catalog
    print("🔍 Searching GeM catalog...")
    catalog_items = integrator.search_gem_catalog(gem_request.category, gem_request.technical_specifications)
    print(f"   Found {len(catalog_items)} matching items")
    
    # Create bid request
    print("📝 Creating bid request...")
    bid_request = integrator.create_gem_bid_request(gem_request, catalog_items)
    print(f"   Bid Request ID: {bid_request['bid_request_id']}")
    
    print(f"\n🎉 GeM Procurement Integration demo completed!")

if __name__ == "__main__":
    main()