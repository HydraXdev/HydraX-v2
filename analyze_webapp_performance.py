#!/usr/bin/env python3
"""
Comprehensive performance analysis for webapp_server_optimized.py
Identifies bottlenecks and provides optimization roadmap
"""

import os
import sys
import re
import ast
import time
import requests
import subprocess
from pathlib import Path
from collections import defaultdict, Counter

class WebAppPerformanceAnalyzer:
    """
    Analyzes webapp performance and identifies optimization opportunities
    """
    
    def __init__(self, webapp_file="/root/HydraX-v2/webapp_server_optimized.py"):
        self.webapp_file = Path(webapp_file)
        self.analysis_results = {}
        
    def analyze_code_structure(self):
        """Analyze code structure for performance issues"""
        print("🔍 Analyzing code structure...")
        
        with open(self.webapp_file, 'r') as f:
            content = f.read()
        
        # Parse AST for detailed analysis
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"❌ Syntax error in webapp file: {e}")
            return {}
        
        analysis = {
            'route_count': 0,
            'function_definitions': 0,
            'file_operations': 0,
            'json_operations': 0,
            'database_operations': 0,
            'synchronous_operations': 0,
            'potential_bottlenecks': []
        }
        
        class PerformanceVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                analysis['function_definitions'] += 1
                
                # Check for route decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if hasattr(decorator.func, 'attr') and decorator.func.attr == 'route':
                            analysis['route_count'] += 1
                
                # Look for performance-sensitive operations in function body
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Call):
                        call_name = self._get_call_name(stmt)
                        
                        if call_name in ['open', 'json.load', 'json.loads']:
                            analysis['file_operations'] += 1
                            if 'mission' in content[stmt.lineno-10:stmt.lineno+10]:
                                analysis['potential_bottlenecks'].append({
                                    'type': 'file_io',
                                    'function': node.name,
                                    'line': stmt.lineno,
                                    'description': f'File I/O in {node.name}() - consider caching'
                                })
                        
                        if call_name.startswith('json.'):
                            analysis['json_operations'] += 1
                        
                        if any(db_term in call_name.lower() for db_term in ['db', 'query', 'execute', 'fetch']):
                            analysis['database_operations'] += 1
                
                self.generic_visit(node)
            
            def _get_call_name(self, call_node):
                """Extract function call name from AST node"""
                if isinstance(call_node.func, ast.Name):
                    return call_node.func.id
                elif isinstance(call_node.func, ast.Attribute):
                    if isinstance(call_node.func.value, ast.Name):
                        return f"{call_node.func.value.id}.{call_node.func.attr}"
                return "unknown"
        
        visitor = PerformanceVisitor()
        visitor.visit(tree)
        
        return analysis
    
    def analyze_route_complexity(self):
        """Analyze individual route complexity"""
        print("📊 Analyzing route complexity...")
        
        with open(self.webapp_file, 'r') as f:
            content = f.read()
        
        # Extract route functions
        route_pattern = r'@app\.route\([\'"]([^\'"]*)[\'"][^)]*\)\s*def\s+(\w+)\([^)]*\):'
        routes = re.findall(route_pattern, content, re.MULTILINE)
        
        route_analysis = {}
        
        for route_path, function_name in routes:
            # Find function content
            func_pattern = rf'def {function_name}\([^)]*\):(.*?)(?=def\s+\w+|\Z)'
            func_match = re.search(func_pattern, content, re.DOTALL)
            
            if func_match:
                func_content = func_match.group(1)
                
                # Analyze function complexity
                complexity_score = 0
                bottlenecks = []
                
                # File operations
                file_ops = len(re.findall(r'open\(|json\.load|json\.dump', func_content))
                complexity_score += file_ops * 3
                if file_ops > 0:
                    bottlenecks.append(f"{file_ops} file operations")
                
                # Database operations  
                db_ops = len(re.findall(r'\.query\(|\.execute\(|\.fetch|handle_fire_action', func_content))
                complexity_score += db_ops * 2
                if db_ops > 0:
                    bottlenecks.append(f"{db_ops} database operations")
                
                # Template rendering
                template_ops = len(re.findall(r'render_template', func_content))
                complexity_score += template_ops * 1
                if template_ops > 0:
                    bottlenecks.append(f"{template_ops} template renders")
                
                # External API calls
                api_calls = len(re.findall(r'requests\.|urllib|http', func_content))
                complexity_score += api_calls * 4
                if api_calls > 0:
                    bottlenecks.append(f"{api_calls} external API calls")
                
                # Loops and iterations
                loops = len(re.findall(r'for\s+\w+\s+in|while\s+', func_content))
                complexity_score += loops * 1
                
                # Exception handling (good, but adds complexity)
                try_blocks = len(re.findall(r'try:', func_content))
                
                route_analysis[route_path] = {
                    'function_name': function_name,
                    'complexity_score': complexity_score,
                    'bottlenecks': bottlenecks,
                    'file_operations': file_ops,
                    'database_operations': db_ops,
                    'template_operations': template_ops,
                    'api_calls': api_calls,
                    'loops': loops,
                    'exception_handling': try_blocks,
                    'lines_of_code': len(func_content.split('\n')),
                    'priority': self._calculate_priority(route_path, complexity_score)
                }
        
        return route_analysis
    
    def _calculate_priority(self, route_path, complexity_score):
        """Calculate optimization priority based on route importance and complexity"""
        high_traffic_routes = ['/hud', '/api/fire', '/api/signals', '/', '/me']
        
        priority_score = 0
        
        # High traffic routes get higher priority
        if any(important in route_path for important in high_traffic_routes):
            priority_score += 10
        
        # Complexity adds to priority
        priority_score += min(complexity_score, 20)
        
        if priority_score >= 15:
            return 'HIGH'
        elif priority_score >= 8:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def test_endpoint_performance(self):
        """Test actual endpoint performance"""
        print("⚡ Testing endpoint performance...")
        
        base_url = "http://localhost:8888"
        
        test_endpoints = [
            {'url': '/', 'name': 'Landing Page'},
            {'url': '/api/health', 'name': 'Health Check'},
            {'url': '/hud?mission_id=test&user_id=12345', 'name': 'HUD Endpoint'},
            {'url': '/me?user_id=12345', 'name': 'War Room'},
            {'url': '/learn', 'name': 'Learn Center'},
            {'url': '/tiers', 'name': 'Tier Comparison'}
        ]
        
        performance_results = {}
        
        for endpoint in test_endpoints:
            try:
                # Warm up request
                requests.get(f"{base_url}{endpoint['url']}", timeout=5)
                
                # Measure performance
                times = []
                for _ in range(3):
                    start_time = time.time()
                    response = requests.get(f"{base_url}{endpoint['url']}", timeout=10)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        times.append(end_time - start_time)
                
                if times:
                    avg_time = sum(times) / len(times)
                    performance_results[endpoint['name']] = {
                        'url': endpoint['url'],
                        'avg_response_time': round(avg_time, 3),
                        'min_response_time': round(min(times), 3),
                        'max_response_time': round(max(times), 3),
                        'status': 'SLOW' if avg_time > 2.0 else 'OK'
                    }
                else:
                    performance_results[endpoint['name']] = {
                        'url': endpoint['url'],
                        'status': 'ERROR',
                        'error': 'No successful requests'
                    }
                    
            except requests.exceptions.RequestException as e:
                performance_results[endpoint['name']] = {
                    'url': endpoint['url'],
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"⚠️  Failed to test {endpoint['name']}: {e}")
        
        return performance_results
    
    def analyze_dependencies(self):
        """Analyze imports and dependencies for performance impact"""
        print("📦 Analyzing dependencies...")
        
        with open(self.webapp_file, 'r') as f:
            content = f.read()
        
        # Extract imports
        import_pattern = r'^(?:from\s+[\w.]+\s+)?import\s+(.+)$'
        imports = re.findall(import_pattern, content, re.MULTILINE)
        
        heavy_imports = [
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'sklearn',
            'tensorflow', 'torch', 'cv2', 'PIL'
        ]
        
        slow_imports = []
        for imp_line in imports:
            for heavy in heavy_imports:
                if heavy in imp_line:
                    slow_imports.append(heavy)
        
        # Check for lazy loading patterns
        lazy_patterns = ['LazyImports', 'lazy.', '@property']
        lazy_loading_used = any(pattern in content for pattern in lazy_patterns)
        
        return {
            'total_imports': len(imports),
            'heavy_imports': list(set(slow_imports)),
            'lazy_loading_used': lazy_loading_used,
            'recommendations': [
                'Use lazy loading for heavy imports',
                'Consider dynamic imports for rarely used modules',
                'Move development-only imports inside debug blocks'
            ]
        }
    
    def generate_optimization_report(self):
        """Generate comprehensive optimization report"""
        print("📋 Generating optimization report...")
        
        code_analysis = self.analyze_code_structure()
        route_analysis = self.analyze_route_complexity()
        dependency_analysis = self.analyze_dependencies()
        
        # Try to get performance data
        try:
            performance_data = self.test_endpoint_performance()
        except Exception as e:
            print(f"⚠️  Could not test endpoints: {e}")
            performance_data = {}
        
        # Generate prioritized recommendations
        recommendations = []
        
        # High priority routes with complexity issues
        high_priority_routes = [r for r in route_analysis.values() if r['priority'] == 'HIGH']
        for route in high_priority_routes:
            if route['complexity_score'] > 10:
                recommendations.append({
                    'priority': 'HIGH',
                    'target': route['function_name'],
                    'route': f"Route with {route['complexity_score']} complexity points",
                    'issues': route['bottlenecks'],
                    'recommendations': [
                        'Implement caching for file operations',
                        'Move database operations to background threads',
                        'Add response caching headers'
                    ]
                })
        
        # File I/O intensive operations
        if code_analysis['file_operations'] > 10:
            recommendations.append({
                'priority': 'HIGH',
                'target': 'File Operations',
                'route': f"{code_analysis['file_operations']} file operations detected",
                'issues': ['Excessive file I/O operations'],
                'recommendations': [
                    'Implement mission file caching',
                    'Use in-memory caching for frequently accessed files',
                    'Consider database storage for mission data'
                ]
            })
        
        # Heavy imports
        if dependency_analysis['heavy_imports']:
            recommendations.append({
                'priority': 'MEDIUM',
                'target': 'Import Optimization',
                'route': f"Heavy imports: {dependency_analysis['heavy_imports']}",
                'issues': ['Slow startup time', 'High memory usage'],
                'recommendations': [
                    'Implement lazy loading for heavy imports',
                    'Use dynamic imports where possible',
                    'Consider microservice architecture'
                ]
            })
        
        report = {
            'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'webapp_file': str(self.webapp_file),
            'summary': {
                'total_routes': code_analysis['route_count'],
                'total_functions': code_analysis['function_definitions'],
                'file_operations': code_analysis['file_operations'],
                'potential_bottlenecks': len(code_analysis['potential_bottlenecks'])
            },
            'code_analysis': code_analysis,
            'route_analysis': route_analysis,
            'dependency_analysis': dependency_analysis,
            'performance_data': performance_data,
            'recommendations': recommendations,
            'quick_wins': [
                {
                    'optimization': 'Implement mission caching',
                    'effort': 'Medium',
                    'impact': 'High',
                    'description': 'Cache mission JSON files in memory with TTL'
                },
                {
                    'optimization': 'Add response time logging',
                    'effort': 'Low',
                    'impact': 'High',
                    'description': 'Add performance monitoring to identify slow requests'
                },
                {
                    'optimization': 'Enable response caching',
                    'effort': 'Low',
                    'impact': 'Medium',
                    'description': 'Add cache headers for static content'
                },
                {
                    'optimization': 'Lazy load heavy modules',
                    'effort': 'Medium',
                    'impact': 'Medium',
                    'description': 'Reduce startup time and memory usage'
                }
            ]
        }
        
        return report
    
    def save_report(self, report, filename='/tmp/webapp_performance_analysis.json'):
        """Save analysis report to file"""
        import json
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Report saved to: {filename}")
        return filename

def main():
    """Main analysis function"""
    print("🚀 Starting webapp performance analysis...")
    print("=" * 60)
    
    analyzer = WebAppPerformanceAnalyzer()
    report = analyzer.generate_optimization_report()
    
    # Print key findings
    print("\n🎯 KEY FINDINGS:")
    print(f"• Total routes: {report['summary']['total_routes']}")
    print(f"• File operations: {report['summary']['file_operations']}")
    print(f"• Potential bottlenecks: {report['summary']['potential_bottlenecks']}")
    
    # Print top slow routes
    route_analysis = report['route_analysis']
    slow_routes = sorted(
        [(k, v) for k, v in route_analysis.items()],
        key=lambda x: x[1]['complexity_score'],
        reverse=True
    )[:3]
    
    print("\n🐌 SLOWEST ROUTES:")
    for route_path, analysis in slow_routes:
        print(f"• {route_path} ({analysis['function_name']})")
        print(f"  Complexity: {analysis['complexity_score']}, Priority: {analysis['priority']}")
        if analysis['bottlenecks']:
            print(f"  Issues: {', '.join(analysis['bottlenecks'])}")
    
    # Print performance data if available
    if 'performance_data' in report and report['performance_data']:
        print("\n⚡ ENDPOINT PERFORMANCE:")
        perf_data = report['performance_data']
        for endpoint, data in perf_data.items():
            if 'avg_response_time' in data:
                status_icon = "🐌" if data['status'] == 'SLOW' else "✅"
                print(f"{status_icon} {endpoint}: {data['avg_response_time']}s avg")
    
    # Print recommendations
    print("\n💡 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(report['quick_wins'][:3], 1):
        print(f"{i}. {rec['optimization']} (Impact: {rec['impact']}, Effort: {rec['effort']})")
        print(f"   {rec['description']}")
    
    # Save detailed report
    report_file = analyzer.save_report(report)
    
    print(f"\n📋 Detailed analysis saved to: {report_file}")
    print("\n🔧 Next steps:")
    print("1. Review the detailed report")
    print("2. Implement mission caching")
    print("3. Add performance monitoring")
    print("4. Optimize slowest routes")
    
    return report

if __name__ == "__main__":
    main()