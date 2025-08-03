#!/usr/bin/env python3
"""
Performance profiler for webapp_server_optimized.py
Adds response time logging and identifies slow endpoints
"""

import time
import logging
import functools
import json
from datetime import datetime
from collections import defaultdict, deque
from flask import request, g

class RoutePerformanceProfiler:
    """
    Tracks route performance and provides optimization insights
    """
    
    def __init__(self, max_samples=1000):
        self.max_samples = max_samples
        self.route_stats = defaultdict(lambda: {
            'times': deque(maxlen=max_samples),
            'total_requests': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'slow_requests': 0,  # > 2 seconds
            'timeout_requests': 0,  # > 10 seconds
            'error_requests': 0
        })
        self.slow_threshold = 2.0  # seconds
        self.timeout_threshold = 10.0  # seconds
        
        # Setup performance logger
        self.perf_logger = logging.getLogger('performance')
        self.perf_logger.setLevel(logging.INFO)
        
        # File handler for performance logs
        perf_handler = logging.FileHandler('/tmp/webapp_performance.log')
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        )
        perf_handler.setFormatter(perf_formatter)
        self.perf_logger.addHandler(perf_handler)
        
        # Console handler for slow requests
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '🐌 SLOW: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.WARNING)
        self.perf_logger.addHandler(console_handler)
    
    def profile_route(self, func):
        """Decorator to profile route performance"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start timing
            start_time = time.time()
            g.request_start_time = start_time
            
            route = request.endpoint or func.__name__
            method = request.method
            route_key = f"{method} {route}"
            
            try:
                # Execute the route function
                result = func(*args, **kwargs)
                
                # Calculate response time
                end_time = time.time()
                response_time = end_time - start_time
                
                # Update statistics
                self._update_stats(route_key, response_time, success=True)
                
                # Log performance data
                self._log_request(route_key, response_time, success=True)
                
                return result
                
            except Exception as e:
                # Handle errors and still log performance
                end_time = time.time()
                response_time = end_time - start_time
                
                self._update_stats(route_key, response_time, success=False)
                self._log_request(route_key, response_time, success=False, error=str(e))
                
                raise  # Re-raise the exception
        
        return wrapper
    
    def _update_stats(self, route_key, response_time, success=True):
        """Update route statistics"""
        stats = self.route_stats[route_key]
        
        stats['times'].append(response_time)
        stats['total_requests'] += 1
        stats['total_time'] += response_time
        
        stats['min_time'] = min(stats['min_time'], response_time)
        stats['max_time'] = max(stats['max_time'], response_time)
        
        if not success:
            stats['error_requests'] += 1
        
        if response_time > self.slow_threshold:
            stats['slow_requests'] += 1
        
        if response_time > self.timeout_threshold:
            stats['timeout_requests'] += 1
    
    def _log_request(self, route_key, response_time, success=True, error=None):
        """Log individual request performance"""
        status = "SUCCESS" if success else "ERROR"
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'route': route_key,
            'response_time': round(response_time, 4),
            'status': status,
            'user_agent': request.headers.get('User-Agent', 'Unknown')[:100],
            'ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        }
        
        if error:
            log_data['error'] = error
        
        # Log as JSON for easy parsing
        self.perf_logger.info(json.dumps(log_data))
        
        # Warn on slow requests
        if response_time > self.slow_threshold:
            level = logging.ERROR if response_time > self.timeout_threshold else logging.WARNING
            self.perf_logger.log(
                level,
                f"{route_key} took {response_time:.3f}s - SLOW REQUEST"
            )
    
    def get_performance_report(self):
        """Generate comprehensive performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'routes': {}
        }
        
        for route_key, stats in self.route_stats.items():
            if stats['total_requests'] == 0:
                continue
                
            times = list(stats['times'])
            times.sort()
            
            # Calculate percentiles
            def percentile(data, p):
                if not data:
                    return 0
                k = (len(data) - 1) * p / 100
                f = int(k)
                c = k - f
                if f == len(data) - 1:
                    return data[f]
                return data[f] * (1 - c) + data[f + 1] * c
            
            avg_time = stats['total_time'] / stats['total_requests']
            
            route_report = {
                'total_requests': stats['total_requests'],
                'avg_response_time': round(avg_time, 4),
                'min_response_time': round(stats['min_time'], 4),
                'max_response_time': round(stats['max_time'], 4),
                'p50_response_time': round(percentile(times, 50), 4),
                'p95_response_time': round(percentile(times, 95), 4),
                'p99_response_time': round(percentile(times, 99), 4),
                'slow_requests': stats['slow_requests'],
                'timeout_requests': stats['timeout_requests'],
                'error_requests': stats['error_requests'],
                'error_rate': round(stats['error_requests'] / stats['total_requests'] * 100, 2),
                'slow_rate': round(stats['slow_requests'] / stats['total_requests'] * 100, 2),
                'requests_per_second': round(stats['total_requests'] / max(stats['total_time'], 0.001), 2)
            }
            
            report['routes'][route_key] = route_report
        
        # Sort by average response time (slowest first)
        sorted_routes = sorted(
            report['routes'].items(),
            key=lambda x: x[1]['avg_response_time'],
            reverse=True
        )
        
        report['slowest_routes'] = sorted_routes[:10]
        report['optimization_insights'] = self._generate_insights(sorted_routes)
        
        return report
    
    def _generate_insights(self, sorted_routes):
        """Generate optimization insights based on performance data"""
        insights = []
        
        for route_key, stats in sorted_routes[:5]:  # Top 5 slowest
            avg_time = stats['avg_response_time']
            slow_rate = stats['slow_rate']
            
            # Generate specific insights
            if '/hud' in route_key and avg_time > 1.0:
                insights.append({
                    'route': route_key,
                    'issue': 'HUD endpoint slow file I/O',
                    'avg_time': avg_time,
                    'recommendation': 'Implement mission file caching, reduce JSON parsing overhead',
                    'priority': 'HIGH',
                    'potential_improvement': '70% faster'
                })
            
            elif '/api/fire' in route_key and avg_time > 0.5:
                insights.append({
                    'route': route_key,
                    'issue': 'Fire API blocking operations',
                    'avg_time': avg_time,
                    'recommendation': 'Add async processing, cache user validation',
                    'priority': 'HIGH',
                    'potential_improvement': '60% faster'
                })
            
            elif '/notebook' in route_key and avg_time > 1.5:
                insights.append({
                    'route': route_key,
                    'issue': 'Notebook heavy imports',
                    'avg_time': avg_time,
                    'recommendation': 'Optimize imports, cache notebook data',
                    'priority': 'MEDIUM',
                    'potential_improvement': '50% faster'
                })
            
            elif '/me' in route_key and avg_time > 2.0:
                insights.append({
                    'route': route_key,
                    'issue': 'War Room database queries',
                    'avg_time': avg_time,
                    'recommendation': 'Cache user stats, optimize database queries',
                    'priority': 'MEDIUM',
                    'potential_improvement': '80% faster'
                })
            
            elif slow_rate > 20:
                insights.append({
                    'route': route_key,
                    'issue': f'High slow request rate ({slow_rate}%)',
                    'avg_time': avg_time,
                    'recommendation': 'Investigate bottlenecks, add caching',
                    'priority': 'MEDIUM',
                    'potential_improvement': 'Reduce slow rate to <5%'
                })
        
        return insights
    
    def save_report(self, filename='/tmp/webapp_performance_report.json'):
        """Save performance report to file"""
        report = self.get_performance_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filename

# Global profiler instance
profiler = RoutePerformanceProfiler()

def profile_route(func):
    """Decorator for easy route profiling"""
    return profiler.profile_route(func)

# Flask middleware for automatic profiling
def init_performance_middleware(app):
    """Initialize performance middleware for Flask app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            route = request.endpoint or 'unknown'
            method = request.method
            
            # Log to performance file
            perf_data = {
                'timestamp': datetime.now().isoformat(),
                'route': f"{method} {route}",
                'response_time': round(response_time, 4),
                'status_code': response.status_code,
                'content_length': response.content_length or 0
            }
            
            with open('/tmp/webapp_requests.log', 'a') as f:
                f.write(json.dumps(perf_data) + '\n')
        
        return response
    
    # Add performance report endpoint
    @app.route('/debug/performance')
    def performance_report():
        """Return performance report (debug mode only)"""
        if not app.debug:
            return "Performance reporting only available in debug mode", 403
        
        report = profiler.get_performance_report()
        return jsonify(report)

if __name__ == "__main__":
    # Test the profiler
    import time
    
    @profile_route
    def test_fast_function():
        time.sleep(0.1)
        return "fast"
    
    @profile_route  
    def test_slow_function():
        time.sleep(2.5)
        return "slow"
    
    # Simulate some requests
    for _ in range(10):
        test_fast_function()
    
    for _ in range(5):
        test_slow_function()
    
    # Generate report
    report = profiler.get_performance_report()
    print(json.dumps(report, indent=2))