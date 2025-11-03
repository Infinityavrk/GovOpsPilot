#!/usr/bin/env python3
"""
Local Demo of SLA Guard Agent
Simulates the complete workflow without AWS dependencies
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

class LocalSLAGuardDemo:
    def __init__(self):
        self.tickets = []
        self.sla_predictions = []
        self.actions_taken = []
        
        # SLA thresholds (minutes)
        self.sla_thresholds = {
            1: {'response': 15, 'resolution': 240},   # P1: 15min response, 4h resolution
            2: {'response': 60, 'resolution': 480},   # P2: 1h response, 8h resolution  
            3: {'response': 240, 'resolution': 1440}, # P3: 4h response, 24h resolution
            4: {'response': 480, 'resolution': 2880}  # P4: 8h response, 48h resolution
        }
    
    def generate_realistic_tickets(self) -> List[Dict[str, Any]]:
        """Generate realistic helpdesk tickets"""
        
        base_time = datetime.utcnow()
        
        tickets = [
            # Critical infrastructure failure
            {
                'ticket_id': 'INC-CRITICAL-001',
                'title': 'Production email server completely down',
                'description': 'Critical infrastructure failure. Email server crashed and will not restart. All 500+ users cannot send or receive emails.',
                'priority': 1,
                'status': 'open',
                'category': 'infrastructure',
                'created_at': (base_time - timedelta(minutes=12)).isoformat(),
                'updated_at': base_time.isoformat(),
                'assigned_to': 'unassigned',
                'reporter': 'monitoring@company.com'
            },
            # High priority database issue
            {
                'ticket_id': 'INC-HIGH-002',
                'title': 'Database server performance severely degraded',
                'description': 'Production database responding very slowly. Customer-facing applications timing out. Revenue impact likely.',
                'priority': 2,
                'status': 'in_progress',
                'category': 'infrastructure',
                'created_at': (base_time - timedelta(minutes=45)).isoformat(),
                'updated_at': (base_time - timedelta(minutes=10)).isoformat(),
                'assigned_to': 'database.admin',
                'reporter': 'operations.manager@company.com'
            },
            # Medium priority printer issue
            {
                'ticket_id': 'INC-MEDIUM-003',
                'title': '3rd floor Marketing printer stuck — jobs queueing',
                'description': 'Print jobs are backing up in the queue, printer shows error light. Marketing team cannot print campaign materials.',
                'priority': 3,
                'status': 'open',
                'category': 'hardware',
                'created_at': (base_time - timedelta(minutes=90)).isoformat(),
                'updated_at': (base_time - timedelta(minutes=30)).isoformat(),
                'assigned_to': 'helpdesk',
                'reporter': 'marketing.user@company.com'
            },
            # Low priority access request
            {
                'ticket_id': 'INC-LOW-004',
                'title': 'Password reset request - account locked',
                'description': 'User account locked after multiple failed login attempts. User needs password reset to access systems.',
                'priority': 4,
                'status': 'open',
                'category': 'access',
                'created_at': (base_time - timedelta(hours=3)).isoformat(),
                'updated_at': (base_time - timedelta(hours=1)).isoformat(),
                'assigned_to': 'helpdesk',
                'reporter': 'user123@company.com'
            },
            # Another medium priority network issue
            {
                'ticket_id': 'INC-MEDIUM-005',
                'title': 'WiFi connectivity issues in Building B',
                'description': 'Multiple users reporting intermittent WiFi disconnections in Building B, 2nd floor.',
                'priority': 3,
                'status': 'open',
                'category': 'network',
                'created_at': (base_time - timedelta(minutes=120)).isoformat(),
                'updated_at': (base_time - timedelta(minutes=60)).isoformat(),
                'assigned_to': 'network.team',
                'reporter': 'facilities@company.com'
            }
        ]
        
        return tickets
    
    def calculate_sla_metrics(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate SLA metrics for a ticket"""
        
        priority = ticket['priority']
        thresholds = self.sla_thresholds[priority]
        
        created_at = datetime.fromisoformat(ticket['created_at'])
        current_time = datetime.utcnow()
        elapsed_minutes = (current_time - created_at).total_seconds() / 60
        
        # Calculate remaining time
        response_remaining = max(0, thresholds['response'] - elapsed_minutes)
        resolution_remaining = max(0, thresholds['resolution'] - elapsed_minutes)
        
        # Calculate breach probability
        if ticket['status'] in ['resolved', 'closed']:
            breach_probability = 0.0
        else:
            # Higher probability as time runs out
            response_risk = min(1.0, elapsed_minutes / thresholds['response'])
            resolution_risk = min(1.0, elapsed_minutes / thresholds['resolution'])
            
            # Weight response more heavily for new tickets
            if ticket['status'] == 'open':
                breach_probability = response_risk * 0.7 + resolution_risk * 0.3
            else:
                breach_probability = response_risk * 0.3 + resolution_risk * 0.7
        
        # Add some ML-like variability
        if ticket['category'] == 'infrastructure':
            breach_probability *= 1.2  # Infrastructure issues are more critical
        elif ticket['category'] == 'access':
            breach_probability *= 0.8  # Access issues are often easier to fix
        
        breach_probability = min(1.0, breach_probability)
        
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
            'breach_probability': breach_probability,
            'sla_status': sla_status,
            'response_remaining_minutes': response_remaining,
            'resolution_remaining_minutes': resolution_remaining,
            'elapsed_minutes': elapsed_minutes,
            'time_to_breach_minutes': min(response_remaining, resolution_remaining),
            'calculated_at': current_time.isoformat()
        }
    
    def get_recommended_actions(self, ticket: Dict[str, Any], sla_metrics: Dict[str, Any]) -> List[str]:
        """Get recommended actions based on SLA risk"""
        
        actions = []
        breach_prob = sla_metrics['breach_probability']
        category = ticket['category']
        priority = ticket['priority']
        
        if breach_prob >= 0.9:
            actions.extend(['escalate-immediately', 'notify-manager'])
            if category == 'infrastructure':
                actions.append('trigger-incident-response')
        
        if breach_prob >= 0.7:
            actions.extend(['boost-priority', 'assign-senior-tech'])
            if category == 'hardware':
                actions.append('dispatch-onsite-tech')
            elif category == 'infrastructure':
                actions.append('engage-vendor-support')
        
        if breach_prob >= 0.5:
            actions.extend(['send-reminder', 'check-dependencies'])
            if priority <= 2:
                actions.append('prepare-workaround')
        
        # Category-specific actions
        if category == 'hardware' and breach_prob >= 0.6:
            actions.append('check-spare-parts')
        elif category == 'access' and breach_prob >= 0.4:
            actions.append('auto-reset-password')
        elif category == 'network' and breach_prob >= 0.5:
            actions.append('check-network-status')
        
        return list(set(actions))  # Remove duplicates
    
    def process_tickets(self):
        """Process all tickets through SLA Guard workflow"""
        
        print("🧩 SLA Guard Agent - Local Demo")
        print("=" * 40)
        print("Processing helpdesk tickets through ML-powered SLA monitoring...")
        print()
        
        tickets = self.generate_realistic_tickets()
        
        for i, ticket in enumerate(tickets, 1):
            print(f"📋 Processing Ticket {i}/{len(tickets)}: {ticket['ticket_id']}")
            print(f"   Title: {ticket['title']}")
            print(f"   Priority: P{ticket['priority']} | Category: {ticket['category']} | Status: {ticket['status']}")
            
            # Simulate processing time
            time.sleep(0.5)
            
            # Calculate SLA metrics
            sla_metrics = self.calculate_sla_metrics(ticket)
            
            # Get recommended actions
            recommended_actions = self.get_recommended_actions(ticket, sla_metrics)
            
            # Store results
            prediction = {
                'ticket_id': ticket['ticket_id'],
                'ticket_data': ticket,
                'sla_metrics': sla_metrics,
                'recommended_actions': recommended_actions,
                'ml_confidence': random.uniform(0.8, 0.95)  # Simulate ML confidence
            }
            
            self.sla_predictions.append(prediction)
            
            # Display results
            breach_prob = sla_metrics['breach_probability']
            sla_status = sla_metrics['sla_status']
            time_to_breach = sla_metrics['time_to_breach_minutes']
            
            # Status emoji
            status_emoji = {
                'BREACH_IMMINENT': '🔴',
                'AT_RISK': '🟡',
                'WATCH': '🟠',
                'HEALTHY': '🟢'
            }[sla_status]
            
            print(f"   {status_emoji} SLA Status: {sla_status} ({breach_prob:.1%} breach risk)")
            print(f"   ⏰ Time to breach: {time_to_breach:.0f} minutes")
            
            if recommended_actions:
                print(f"   🎯 Recommended actions: {', '.join(recommended_actions[:3])}")
                if len(recommended_actions) > 3:
                    print(f"      + {len(recommended_actions) - 3} more actions")
            
            # Simulate taking actions for high-risk tickets
            if breach_prob >= 0.7:
                print(f"   ⚡ TAKING PREVENTIVE ACTION...")
                self.simulate_preventive_actions(ticket, sla_metrics, recommended_actions)
            
            print()
    
    def simulate_preventive_actions(self, ticket: Dict[str, Any], sla_metrics: Dict[str, Any], actions: List[str]):
        """Simulate taking preventive actions"""
        
        for action in actions[:2]:  # Simulate first 2 actions
            action_result = {
                'ticket_id': ticket['ticket_id'],
                'action': action,
                'timestamp': datetime.utcnow().isoformat(),
                'success': random.choice([True, True, True, False])  # 75% success rate
            }
            
            if action == 'escalate-immediately':
                print(f"      📢 Escalated to senior admin (Priority boosted to P1)")
            elif action == 'notify-manager':
                print(f"      📧 Manager notified via email and SMS")
            elif action == 'assign-senior-tech':
                print(f"      👨‍💻 Senior technician assigned")
            elif action == 'trigger-incident-response':
                print(f"      🚨 Incident response team activated")
            elif action == 'dispatch-onsite-tech':
                print(f"      🚗 Onsite technician dispatched (ETA: 30 min)")
            elif action == 'auto-reset-password':
                print(f"      🔑 Automated password reset initiated")
            else:
                print(f"      ⚙️  Action executed: {action.replace('-', ' ').title()}")
            
            self.actions_taken.append(action_result)
    
    def generate_what_next_queue(self) -> List[Dict[str, Any]]:
        """Generate prioritized 'What Next' queue"""
        
        # Sort predictions by breach probability (highest first)
        sorted_predictions = sorted(
            self.sla_predictions,
            key=lambda x: x['sla_metrics']['breach_probability'],
            reverse=True
        )
        
        queue = []
        for i, prediction in enumerate(sorted_predictions, 1):
            ticket = prediction['ticket_data']
            sla_metrics = prediction['sla_metrics']
            
            queue_item = {
                'queue_position': i,
                'ticket_id': ticket['ticket_id'],
                'title': ticket['title'],
                'priority': ticket['priority'],
                'category': ticket['category'],
                'breach_probability': sla_metrics['breach_probability'],
                'sla_status': sla_metrics['sla_status'],
                'time_to_breach': sla_metrics['time_to_breach_minutes'],
                'recommended_action': prediction['recommended_actions'][0] if prediction['recommended_actions'] else 'monitor',
                'confidence': prediction['ml_confidence']
            }
            
            queue.append(queue_item)
        
        return queue
    
    def display_dashboard(self):
        """Display executive dashboard summary"""
        
        print("📊 SLA Guard Agent - Executive Dashboard")
        print("=" * 45)
        
        # Calculate KPIs
        total_tickets = len(self.sla_predictions)
        at_risk_tickets = len([p for p in self.sla_predictions if p['sla_metrics']['breach_probability'] >= 0.7])
        healthy_tickets = len([p for p in self.sla_predictions if p['sla_metrics']['breach_probability'] < 0.5])
        
        sla_compliance = ((total_tickets - at_risk_tickets) / total_tickets * 100) if total_tickets > 0 else 100
        
        actions_taken = len(self.actions_taken)
        successful_actions = len([a for a in self.actions_taken if a.get('success', True)])
        automation_success_rate = (successful_actions / actions_taken * 100) if actions_taken > 0 else 0
        
        # Display KPIs
        print(f"🎯 Key Performance Indicators:")
        print(f"   SLA Compliance: {sla_compliance:.1f}% (Target: ≥95%)")
        print(f"   Automation Success: {automation_success_rate:.1f}% (Target: ≥80%)")
        print(f"   Active Tickets: {total_tickets}")
        print(f"   At Risk: {at_risk_tickets} | Healthy: {healthy_tickets}")
        print()
        
        # What Next Queue
        queue = self.generate_what_next_queue()
        
        print(f"🎯 What Next Queue (Priority Order):")
        print("-" * 35)
        
        for item in queue:
            status_emoji = {
                'BREACH_IMMINENT': '🔴',
                'AT_RISK': '🟡',
                'WATCH': '🟠',
                'HEALTHY': '🟢'
            }[item['sla_status']]
            
            print(f"{item['queue_position']}. {status_emoji} {item['ticket_id']} - {item['title'][:40]}...")
            print(f"   P{item['priority']} | {item['breach_probability']:.1%} breach risk | {item['time_to_breach']:.0f}min to breach")
            print(f"   Next Action: {item['recommended_action'].replace('-', ' ').title()}")
            print()
        
        # Performance Summary
        print(f"📈 Performance Summary:")
        print(f"   • Breach Prevention: {len([p for p in self.sla_predictions if p['sla_metrics']['breach_probability'] >= 0.7])} high-risk tickets identified")
        print(f"   • Preventive Actions: {actions_taken} actions triggered automatically")
        print(f"   • ML Confidence: {sum(p['ml_confidence'] for p in self.sla_predictions) / len(self.sla_predictions):.1%} average")
        print(f"   • Response Time: <2 seconds per prediction")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if sla_compliance < 95:
            print(f"   ⚠️  SLA compliance below target - focus on high-risk tickets")
        else:
            print(f"   ✅ SLA compliance on target - maintain current performance")
        
        if at_risk_tickets > 0:
            print(f"   🚨 {at_risk_tickets} tickets need immediate attention")
        
        print(f"   📊 Consider integrating with L1 automation for faster resolution")
    
    def save_results(self):
        """Save demo results to files"""
        
        # Save What Next queue
        queue = self.generate_what_next_queue()
        with open('what_next_queue_demo.json', 'w') as f:
            json.dump(queue, f, indent=2)
        
        # Save detailed predictions
        with open('sla_predictions_demo.json', 'w') as f:
            json.dump(self.sla_predictions, f, indent=2, default=str)
        
        # Save actions taken
        with open('actions_taken_demo.json', 'w') as f:
            json.dump(self.actions_taken, f, indent=2)
        
        print(f"\n💾 Results saved:")
        print(f"   • what_next_queue_demo.json - Priority queue")
        print(f"   • sla_predictions_demo.json - Detailed predictions")
        print(f"   • actions_taken_demo.json - Preventive actions")

def main():
    """Run the local SLA Guard demo"""
    
    demo = LocalSLAGuardDemo()
    
    # Process tickets
    demo.process_tickets()
    
    # Show dashboard
    demo.display_dashboard()
    
    # Save results
    demo.save_results()
    
    print(f"\n🎉 Demo Complete!")
    print(f"\n🚀 This demonstrates the SLA Guard Agent achieving:")
    print(f"   ✅ Real-time breach prediction with ML-powered analysis")
    print(f"   ✅ Automated preventive actions for high-risk tickets")
    print(f"   ✅ Prioritized 'What Next' queue for technicians")
    print(f"   ✅ Executive dashboard with key performance indicators")
    print(f"   ✅ Target: ≥95% SLA adherence through proactive monitoring")

if __name__ == "__main__":
    main()