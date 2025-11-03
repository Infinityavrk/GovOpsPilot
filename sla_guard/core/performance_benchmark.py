#!/usr/bin/env python3
"""
SLA Guard Prototype Performance Benchmarking Tool
Comprehensive performance analysis and benchmarking for all system components
"""

import time
import json
import statistics
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import boto3
import requests
import concurrent.futures
import platform
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_claude_sonnet_integration import EnhancedClaudeSonnetIntegration

class SLAGuardPerformanceBenchmark:
    def __init__(self):
        """Initialize performance benchmarking suite"""
        self.results = {
            'system_info': self._get_system_info(),
            'ai_performance': {},
            'json_parsing_performance': {},
            'ui_response_times': {},
            'bedrock_performance': {},
            'overall_metrics': {},
            'benchmark_timestamp': datetime.now().isoformat()
        }
        
        # Initialize components
        self.claude_integration = EnhancedClaudeSonnetIntegration()
        
        # Test data sets
        self.test_tickets = self._generate_test_tickets()
        
        print("🚀 SLA Guard Performance Benchmark Suite Initialized")
        print(f"📊 System: {self.results['system_info']['platform']}")
        print(f"💾 RAM: {self.results['system_info']['memory_gb']}")
        print(f"🔧 CPU: {self.results['system_info']['cpu_count']} cores")

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context"""
        return {
            'platform': f"{platform.system()} {platform.release()}",
            'cpu_count': os.cpu_count() or 'Unknown',
            'memory_gb': 'Unknown',  # Simplified for compatibility
            'python_version': sys.version.split()[0],
            'timestamp': datetime.now().isoformat()
        }

    def _generate_test_tickets(self) -> List[Dict[str, str]]:
        """Generate diverse test tickets for benchmarking"""
        return [
            {
                'id': 'T001',
                'text': 'Aadhaar authentication failing for multiple users in Mumbai region. Biometric verification timeout after 30 seconds.',
                'expected_dept': 'UIDAI',
                'expected_category': 'Authentication',
                'expected_priority': 'P2'
            },
            {
                'id': 'T002', 
                'text': 'Payment gateway down completely. All transactions failing across MPOnline portal. Revenue impact critical.',
                'expected_dept': 'MeitY',
                'expected_category': 'Payment',
                'expected_priority': 'P1'
            },
            {
                'id': 'T003',
                'text': 'Certificate download slow on eDistrict portal. Users reporting 5+ minute wait times for income certificates.',
                'expected_dept': 'eDistrict',
                'expected_category': 'Certificate',
                'expected_priority': 'P3'
            },
            {
                'id': 'T004',
                'text': 'DigitalMP portal login page not loading. White screen error affecting citizen access to services.',
                'expected_dept': 'DigitalMP',
                'expected_category': 'Portal',
                'expected_priority': 'P2'
            },
            {
                'id': 'T005',
                'text': 'Network connectivity issues in rural areas. Citizens unable to access any online government services.',
                'expected_dept': 'MPOnline',
                'expected_category': 'Network',
                'expected_priority': 'P1'
            },
            {
                'id': 'T006',
                'text': 'API integration failing between departments. Data sync issues causing service disruptions.',
                'expected_dept': 'MPOnline',
                'expected_category': 'Integration',
                'expected_priority': 'P2'
            },
            {
                'id': 'T007',
                'text': 'Minor UI issue on portal homepage. Submit button slightly misaligned but functional.',
                'expected_dept': 'DigitalMP',
                'expected_category': 'Portal',
                'expected_priority': 'P4'
            },
            {
                'id': 'T008',
                'text': 'Complete system outage affecting all government services. Emergency response required immediately.',
                'expected_dept': 'MPOnline',
                'expected_category': 'Other',
                'expected_priority': 'P1'
            }
        ]

    def benchmark_ai_analysis_performance(self) -> Dict[str, Any]:
        """Benchmark AI analysis performance across different ticket types"""
        print("\n🧠 Benchmarking AI Analysis Performance...")
        
        results = {
            'individual_tickets': [],
            'batch_performance': {},
            'accuracy_metrics': {},
            'response_times': [],
            'success_rates': {}
        }
        
        # Individual ticket analysis
        for ticket in self.test_tickets:
            print(f"   Analyzing ticket {ticket['id']}...")
            
            start_time = time.time()
            try:
                analysis = self.claude_integration.analyze_ticket_with_claude_sonnet(
                    ticket['text'],
                    context={'ticket_id': ticket['id']}
                )
                end_time = time.time()
                
                response_time = end_time - start_time
                results['response_times'].append(response_time)
                
                # Check accuracy
                predicted_dept = analysis.get('analysis_summary', {}).get('department')
                predicted_category = analysis.get('analysis_summary', {}).get('category')
                predicted_priority = analysis.get('analysis_summary', {}).get('priority')
                
                accuracy = {
                    'department_correct': predicted_dept == ticket['expected_dept'],
                    'category_correct': predicted_category == ticket['expected_category'],
                    'priority_correct': predicted_priority == ticket['expected_priority']
                }
                
                ticket_result = {
                    'ticket_id': ticket['id'],
                    'response_time_seconds': response_time,
                    'success': True,
                    'accuracy': accuracy,
                    'predicted': {
                        'department': predicted_dept,
                        'category': predicted_category,
                        'priority': predicted_priority
                    },
                    'expected': {
                        'department': ticket['expected_dept'],
                        'category': ticket['expected_category'],
                        'priority': ticket['expected_priority']
                    }
                }
                
            except Exception as e:
                ticket_result = {
                    'ticket_id': ticket['id'],
                    'response_time_seconds': time.time() - start_time,
                    'success': False,
                    'error': str(e)
                }
            
            results['individual_tickets'].append(ticket_result)
        
        # Calculate aggregate metrics
        successful_analyses = [r for r in results['individual_tickets'] if r['success']]
        
        if successful_analyses:
            results['accuracy_metrics'] = {
                'department_accuracy': sum(1 for r in successful_analyses 
                                         if r.get('accuracy', {}).get('department_correct', False)) / len(successful_analyses),
                'category_accuracy': sum(1 for r in successful_analyses 
                                       if r.get('accuracy', {}).get('category_correct', False)) / len(successful_analyses),
                'priority_accuracy': sum(1 for r in successful_analyses 
                                       if r.get('accuracy', {}).get('priority_correct', False)) / len(successful_analyses),
                'overall_accuracy': sum(1 for r in successful_analyses 
                                      if all(r.get('accuracy', {}).values())) / len(successful_analyses)
            }
        
        if results['response_times']:
            results['performance_stats'] = {
                'avg_response_time': statistics.mean(results['response_times']),
                'median_response_time': statistics.median(results['response_times']),
                'min_response_time': min(results['response_times']),
                'max_response_time': max(results['response_times']),
                'std_dev': statistics.stdev(results['response_times']) if len(results['response_times']) > 1 else 0
            }
        
        results['success_rates'] = {
            'total_tickets': len(self.test_tickets),
            'successful_analyses': len(successful_analyses),
            'success_rate': len(successful_analyses) / len(self.test_tickets)
        }
        
        return results

    def benchmark_json_parsing_performance(self) -> Dict[str, Any]:
        """Benchmark JSON parsing performance with various response formats"""
        print("\n📝 Benchmarking JSON Parsing Performance...")
        
        # Test cases with different JSON formats
        test_cases = [
            {
                'name': 'valid_json',
                'content': '{"analysis_summary": {"department": "UIDAI", "priority": "P2"}}'
            },
            {
                'name': 'json_with_extra_data',
                'content': '{"analysis_summary": {"department": "MeitY", "priority": "P1"}} This is extra text that should be ignored.'
            },
            {
                'name': 'malformed_json_missing_commas',
                'content': '{"analysis_summary": {"department": "DigitalMP" "priority": "P3"}}'
            },
            {
                'name': 'json_in_markdown',
                'content': '```json\n{"analysis_summary": {"department": "eDistrict", "priority": "P2"}}\n```'
            },
            {
                'name': 'text_only_no_json',
                'content': 'This ticket appears to be related to payment issues in the MeitY department with high priority.'
            }
        ]
        
        results = {
            'test_cases': [],
            'parsing_times': [],
            'success_rates': {}
        }
        
        for test_case in test_cases:
            print(f"   Testing {test_case['name']}...")
            
            # Run multiple iterations for statistical significance
            times = []
            successes = 0
            
            for _ in range(10):  # 10 iterations per test case
                start_time = time.time()
                try:
                    parsed_result = self.claude_integration._parse_analysis_response(test_case['content'])
                    end_time = time.time()
                    
                    if parsed_result and 'analysis_summary' in parsed_result:
                        successes += 1
                    
                    times.append(end_time - start_time)
                    
                except Exception as e:
                    times.append(time.time() - start_time)
            
            avg_time = statistics.mean(times)
            success_rate = successes / 10
            
            results['test_cases'].append({
                'name': test_case['name'],
                'avg_parsing_time': avg_time,
                'success_rate': success_rate,
                'min_time': min(times),
                'max_time': max(times)
            })
            
            results['parsing_times'].extend(times)
        
        # Overall parsing performance
        if results['parsing_times']:
            results['overall_performance'] = {
                'avg_parsing_time': statistics.mean(results['parsing_times']),
                'median_parsing_time': statistics.median(results['parsing_times']),
                'total_success_rate': sum(tc['success_rate'] for tc in results['test_cases']) / len(results['test_cases'])
            }
        
        return results

    def benchmark_concurrent_performance(self) -> Dict[str, Any]:
        """Benchmark system performance under concurrent load"""
        print("\n⚡ Benchmarking Concurrent Performance...")
        
        results = {
            'concurrent_tests': [],
            'throughput_metrics': {}
        }
        
        # Test different concurrency levels
        concurrency_levels = [1, 2, 5, 10]
        
        for concurrency in concurrency_levels:
            print(f"   Testing {concurrency} concurrent requests...")
            
            start_time = time.time()
            
            def analyze_ticket(ticket):
                return self.claude_integration.analyze_ticket_with_claude_sonnet(
                    ticket['text'],
                    context={'concurrent_test': True}
                )
            
            # Use a subset of tickets for concurrent testing
            test_tickets = self.test_tickets[:4]  # Use first 4 tickets
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []
                for _ in range(concurrency):
                    for ticket in test_tickets:
                        futures.append(executor.submit(analyze_ticket, ticket))
                
                # Wait for all to complete
                completed = 0
                failed = 0
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        completed += 1
                    except Exception as e:
                        failed += 1
            
            end_time = time.time()
            total_time = end_time - start_time
            total_requests = len(futures)
            
            results['concurrent_tests'].append({
                'concurrency_level': concurrency,
                'total_requests': total_requests,
                'completed_requests': completed,
                'failed_requests': failed,
                'total_time_seconds': total_time,
                'requests_per_second': total_requests / total_time if total_time > 0 else 0,
                'avg_response_time': total_time / total_requests if total_requests > 0 else 0
            })
        
        return results

    def benchmark_bedrock_performance(self) -> Dict[str, Any]:
        """Benchmark AWS Bedrock integration performance"""
        print("\n🔧 Benchmarking Bedrock Performance...")
        
        results = {
            'connection_test': {},
            'model_performance': {},
            'error_rates': {}
        }
        
        # Test Bedrock connection
        start_time = time.time()
        try:
            # Test basic Bedrock connectivity
            if self.claude_integration.bedrock_available:
                connection_time = time.time() - start_time
                results['connection_test'] = {
                    'success': True,
                    'connection_time': connection_time,
                    'region': self.claude_integration.region,
                    'model_id': self.claude_integration.model_id
                }
            else:
                results['connection_test'] = {
                    'success': False,
                    'error': 'Bedrock not available'
                }
        except Exception as e:
            results['connection_test'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test model performance with different prompt sizes
        if results['connection_test']['success']:
            prompt_sizes = ['small', 'medium', 'large']
            
            for size in prompt_sizes:
                if size == 'small':
                    test_prompt = "Analyze this ticket: Payment issue"
                elif size == 'medium':
                    test_prompt = "Analyze this government service ticket: " + "Payment gateway timeout error. " * 10
                else:  # large
                    test_prompt = "Analyze this comprehensive government service ticket: " + "Complex payment gateway integration failure with multiple system dependencies. " * 20
                
                times = []
                successes = 0
                
                for _ in range(3):  # 3 iterations per size
                    start_time = time.time()
                    try:
                        response = self.claude_integration._call_claude_sonnet(test_prompt, 'test')
                        end_time = time.time()
                        
                        if response.get('success'):
                            successes += 1
                        
                        times.append(end_time - start_time)
                        
                    except Exception as e:
                        times.append(time.time() - start_time)
                
                results['model_performance'][size] = {
                    'avg_response_time': statistics.mean(times) if times else 0,
                    'success_rate': successes / 3,
                    'prompt_length': len(test_prompt)
                }
        
        return results

    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        print("\n📊 Generating Performance Report...")
        
        # Run all benchmarks
        self.results['ai_performance'] = self.benchmark_ai_analysis_performance()
        self.results['json_parsing_performance'] = self.benchmark_json_parsing_performance()
        self.results['concurrent_performance'] = self.benchmark_concurrent_performance()
        self.results['bedrock_performance'] = self.benchmark_bedrock_performance()
        
        # Calculate overall metrics
        self.results['overall_metrics'] = self._calculate_overall_metrics()
        
        # Generate report
        report = self._format_performance_report()
        
        return report

    def _calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall system performance metrics"""
        metrics = {}
        
        # AI Performance Summary
        ai_perf = self.results.get('ai_performance', {})
        if ai_perf.get('performance_stats'):
            metrics['avg_ai_response_time'] = ai_perf['performance_stats']['avg_response_time']
            metrics['ai_success_rate'] = ai_perf.get('success_rates', {}).get('success_rate', 0)
            metrics['overall_accuracy'] = ai_perf.get('accuracy_metrics', {}).get('overall_accuracy', 0)
        
        # JSON Parsing Summary
        json_perf = self.results.get('json_parsing_performance', {})
        if json_perf.get('overall_performance'):
            metrics['avg_parsing_time'] = json_perf['overall_performance']['avg_parsing_time']
            metrics['parsing_success_rate'] = json_perf['overall_performance']['total_success_rate']
        
        # Concurrent Performance Summary
        concurrent_perf = self.results.get('concurrent_performance', {})
        if concurrent_perf.get('concurrent_tests'):
            max_throughput = max(test['requests_per_second'] for test in concurrent_perf['concurrent_tests'])
            metrics['max_throughput_rps'] = max_throughput
        
        # System Health Score (0-100)
        health_factors = []
        if metrics.get('ai_success_rate'):
            health_factors.append(metrics['ai_success_rate'] * 100)
        if metrics.get('parsing_success_rate'):
            health_factors.append(metrics['parsing_success_rate'] * 100)
        if metrics.get('overall_accuracy'):
            health_factors.append(metrics['overall_accuracy'] * 100)
        
        if health_factors:
            metrics['system_health_score'] = statistics.mean(health_factors)
        
        return metrics

    def _format_performance_report(self) -> str:
        """Format the performance report as a readable string"""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("🚀 SLA GUARD PROTOTYPE PERFORMANCE BENCHMARK REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"💻 System: {self.results['system_info']['platform']}")
        report_lines.append(f"🔧 CPU: {self.results['system_info']['cpu_count']} cores")
        report_lines.append(f"💾 Memory: {self.results['system_info']['memory_gb']}")
        report_lines.append("")
        
        # Overall Metrics
        overall = self.results.get('overall_metrics', {})
        if overall:
            report_lines.append("📊 OVERALL PERFORMANCE SUMMARY")
            report_lines.append("-" * 40)
            if 'system_health_score' in overall:
                score = overall['system_health_score']
                status = "🟢 EXCELLENT" if score >= 90 else "🟡 GOOD" if score >= 70 else "🔴 NEEDS IMPROVEMENT"
                report_lines.append(f"System Health Score: {score:.1f}/100 {status}")
            
            if 'avg_ai_response_time' in overall:
                report_lines.append(f"Average AI Response Time: {overall['avg_ai_response_time']:.2f}s")
            if 'ai_success_rate' in overall:
                report_lines.append(f"AI Analysis Success Rate: {overall['ai_success_rate']*100:.1f}%")
            if 'overall_accuracy' in overall:
                report_lines.append(f"Classification Accuracy: {overall['overall_accuracy']*100:.1f}%")
            if 'max_throughput_rps' in overall:
                report_lines.append(f"Max Throughput: {overall['max_throughput_rps']:.1f} requests/second")
            report_lines.append("")
        
        # AI Performance Details
        ai_perf = self.results.get('ai_performance', {})
        if ai_perf:
            report_lines.append("🧠 AI ANALYSIS PERFORMANCE")
            report_lines.append("-" * 40)
            
            if 'performance_stats' in ai_perf:
                stats = ai_perf['performance_stats']
                report_lines.append(f"Average Response Time: {stats['avg_response_time']:.2f}s")
                report_lines.append(f"Median Response Time: {stats['median_response_time']:.2f}s")
                report_lines.append(f"Min/Max Response Time: {stats['min_response_time']:.2f}s / {stats['max_response_time']:.2f}s")
            
            if 'accuracy_metrics' in ai_perf:
                acc = ai_perf['accuracy_metrics']
                report_lines.append(f"Department Classification: {acc['department_accuracy']*100:.1f}%")
                report_lines.append(f"Category Classification: {acc['category_accuracy']*100:.1f}%")
                report_lines.append(f"Priority Classification: {acc['priority_accuracy']*100:.1f}%")
            
            if 'success_rates' in ai_perf:
                sr = ai_perf['success_rates']
                report_lines.append(f"Success Rate: {sr['success_rate']*100:.1f}% ({sr['successful_analyses']}/{sr['total_tickets']})")
            report_lines.append("")
        
        # JSON Parsing Performance
        json_perf = self.results.get('json_parsing_performance', {})
        if json_perf:
            report_lines.append("📝 JSON PARSING PERFORMANCE")
            report_lines.append("-" * 40)
            
            if 'overall_performance' in json_perf:
                perf = json_perf['overall_performance']
                report_lines.append(f"Average Parsing Time: {perf['avg_parsing_time']*1000:.1f}ms")
                report_lines.append(f"Overall Success Rate: {perf['total_success_rate']*100:.1f}%")
            
            if 'test_cases' in json_perf:
                report_lines.append("Test Case Results:")
                for case in json_perf['test_cases']:
                    report_lines.append(f"  • {case['name']}: {case['success_rate']*100:.0f}% success, {case['avg_parsing_time']*1000:.1f}ms avg")
            report_lines.append("")
        
        # Concurrent Performance
        concurrent_perf = self.results.get('concurrent_performance', {})
        if concurrent_perf and 'concurrent_tests' in concurrent_perf:
            report_lines.append("⚡ CONCURRENT PERFORMANCE")
            report_lines.append("-" * 40)
            
            for test in concurrent_perf['concurrent_tests']:
                report_lines.append(f"Concurrency {test['concurrency_level']}: {test['requests_per_second']:.1f} req/s, {test['avg_response_time']:.2f}s avg")
            report_lines.append("")
        
        # Bedrock Performance
        bedrock_perf = self.results.get('bedrock_performance', {})
        if bedrock_perf:
            report_lines.append("🔧 BEDROCK INTEGRATION PERFORMANCE")
            report_lines.append("-" * 40)
            
            if 'connection_test' in bedrock_perf:
                conn = bedrock_perf['connection_test']
                if conn['success']:
                    report_lines.append(f"✅ Connection: Success ({conn['connection_time']:.2f}s)")
                    report_lines.append(f"Region: {conn['region']}")
                    report_lines.append(f"Model: {conn['model_id']}")
                else:
                    report_lines.append(f"❌ Connection: Failed - {conn.get('error', 'Unknown error')}")
            
            if 'model_performance' in bedrock_perf:
                report_lines.append("Model Performance by Prompt Size:")
                for size, perf in bedrock_perf['model_performance'].items():
                    report_lines.append(f"  • {size.title()}: {perf['avg_response_time']:.2f}s avg, {perf['success_rate']*100:.0f}% success")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("💡 PERFORMANCE RECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        recommendations = []
        
        if overall.get('avg_ai_response_time', 0) > 10:
            recommendations.append("• Consider optimizing AI prompts to reduce response time")
        
        if overall.get('ai_success_rate', 1) < 0.95:
            recommendations.append("• Investigate AI analysis failures and improve error handling")
        
        if overall.get('overall_accuracy', 1) < 0.8:
            recommendations.append("• Review and refine AI classification prompts for better accuracy")
        
        if overall.get('parsing_success_rate', 1) < 0.9:
            recommendations.append("• Enhance JSON parsing robustness for edge cases")
        
        if not recommendations:
            recommendations.append("• System performance is excellent! Consider load testing for production readiness")
        
        report_lines.extend(recommendations)
        report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("End of Performance Report")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)

    def save_results(self, filename: str = None):
        """Save benchmark results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sla_guard_benchmark_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📁 Results saved to: {filename}")

def main():
    """Run the complete performance benchmark suite"""
    print("🎯 Starting SLA Guard Prototype Performance Benchmark")
    print("This may take several minutes to complete...")
    print()
    
    benchmark = SLAGuardPerformanceBenchmark()
    
    try:
        # Generate comprehensive report
        report = benchmark.generate_performance_report()
        
        # Display report
        print(report)
        
        # Save results
        benchmark.save_results()
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"sla_guard_performance_report_{timestamp}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Performance report saved to: {report_filename}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()