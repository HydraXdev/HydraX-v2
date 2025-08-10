#!/usr/bin/env python3
"""
Network Latency Monitor - Monitor and optimize network performance

Tracks latency between signal generation, user notification, and trade execution
to identify bottlenecks and optimize the entire signal delivery pipeline.
"""

import json
import time
import redis
import logging
import statistics
import threading
import requests
import socket
import subprocess
import psutil
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import zmq
import asyncio
import websockets

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NetworkLatencyMonitor')

@dataclass
class LatencyMeasurement:
    """Network latency measurement data point"""
    component: str
    source: str
    destination: str
    latency_ms: float
    timestamp: float
    measurement_type: str  # 'ping', 'tcp_connect', 'http_request', 'zmq_roundtrip'
    packet_loss: Optional[float] = None
    additional_info: Optional[Dict] = None

@dataclass
class SignalLatencyTrace:
    """Complete latency trace for a signal from generation to execution"""
    signal_id: str
    generation_time: float
    notification_time: Optional[float]
    user_action_time: Optional[float]
    execution_start_time: Optional[float]
    execution_complete_time: Optional[float]
    total_latency: Optional[float]
    bottleneck_component: Optional[str]
    latency_breakdown: Dict[str, float]

class NetworkLatencyMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.truth_log_path = '/root/HydraX-v2/truth_log.jsonl'
        
        # Latency measurement storage
        self.latency_measurements = defaultdict(lambda: deque(maxlen=1000))
        self.signal_traces = {}  # signal_id -> SignalLatencyTrace
        self.component_health = {}
        
        # Network endpoints to monitor
        self.endpoints = {
            'telegram_api': 'https://api.telegram.org',
            'webapp_server': 'http://localhost:8888',
            'redis_server': 'localhost:6379',
            'zmq_telemetry': 'tcp://localhost:5560',
            'zmq_signals': 'tcp://localhost:5557',
            'zmq_fire': 'tcp://localhost:5555',
            'external_broker': 'api.coinexx.com',
            'dns_resolver': '8.8.8.8',
            'cloudflare_edge': '1.1.1.1'
        }
        
        # Monitoring thresholds
        self.latency_thresholds = {
            'excellent': 50,    # <50ms
            'good': 100,       # 50-100ms
            'acceptable': 250,  # 100-250ms
            'poor': 500,       # 250-500ms
            'critical': 1000   # >500ms
        }
        
        # ZMQ context for ZMQ latency measurements
        self.zmq_context = zmq.Context()
        
        # Monitoring control
        self.monitoring_active = False
        self.monitoring_thread = None
        
        logger.info("📡 Network Latency Monitor initialized")

    def start_monitoring(self):
        """Start continuous network latency monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🔄 Network latency monitoring started")

    def stop_monitoring(self):
        """Stop network latency monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            
        logger.info("🛑 Network latency monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Measure different types of latency
                self.measure_ping_latencies()
                self.measure_http_latencies()
                self.measure_tcp_latencies()
                self.measure_zmq_latencies()
                self.measure_redis_latency()
                
                # Update component health scores
                self.update_component_health()
                
                # Clean old measurements
                self.cleanup_old_measurements()
                
                time.sleep(30)  # Run every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

    def measure_ping_latencies(self):
        """Measure ICMP ping latencies"""
        ping_targets = [
            ('dns_resolver', '8.8.8.8'),
            ('cloudflare_edge', '1.1.1.1'),
            ('external_broker', 'api.coinexx.com')
        ]
        
        for name, target in ping_targets:
            try:
                start_time = time.time()
                
                # Use system ping command
                result = subprocess.run(
                    ['ping', '-c', '3', '-W', '2000', target],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Parse ping output for latency
                    output_lines = result.stdout.split('\n')
                    times = []
                    packet_loss = 0
                    
                    for line in output_lines:
                        if 'time=' in line:
                            time_part = line.split('time=')[1].split(' ')[0]
                            try:
                                times.append(float(time_part))
                            except ValueError:
                                continue
                        elif 'packet loss' in line:
                            try:
                                loss_part = line.split('%')[0].split()[-1]
                                packet_loss = float(loss_part)
                            except (ValueError, IndexError):
                                pass
                    
                    if times:
                        avg_latency = statistics.mean(times)
                        
                        measurement = LatencyMeasurement(
                            component=name,
                            source='local',
                            destination=target,
                            latency_ms=avg_latency,
                            timestamp=time.time(),
                            measurement_type='ping',
                            packet_loss=packet_loss,
                            additional_info={'min': min(times), 'max': max(times), 'count': len(times)}
                        )
                        
                        self.latency_measurements[name].append(measurement)
                        
            except Exception as e:
                logger.debug(f"Ping measurement failed for {name}: {e}")

    def measure_http_latencies(self):
        """Measure HTTP request latencies"""
        http_targets = [
            ('telegram_api', 'https://api.telegram.org/bot'),
            ('webapp_server', 'http://localhost:8888/health')
        ]
        
        for name, url in http_targets:
            try:
                start_time = time.time()
                
                response = requests.get(url, timeout=5)
                latency = (time.time() - start_time) * 1000
                
                measurement = LatencyMeasurement(
                    component=name,
                    source='local',
                    destination=url,
                    latency_ms=latency,
                    timestamp=time.time(),
                    measurement_type='http_request',
                    additional_info={
                        'status_code': response.status_code,
                        'response_size': len(response.content) if response.content else 0
                    }
                )
                
                self.latency_measurements[name].append(measurement)
                
            except requests.RequestException as e:
                # Log failed requests as high latency measurements
                measurement = LatencyMeasurement(
                    component=name,
                    source='local',
                    destination=url,
                    latency_ms=5000,  # 5 second timeout = very high latency
                    timestamp=time.time(),
                    measurement_type='http_request',
                    additional_info={'error': str(e)}
                )
                
                self.latency_measurements[name].append(measurement)
            except Exception as e:
                logger.debug(f"HTTP measurement failed for {name}: {e}")

    def measure_tcp_latencies(self):
        """Measure TCP connection latencies"""
        tcp_targets = [
            ('redis_server', 'localhost', 6379),
            ('webapp_server_tcp', 'localhost', 8888)
        ]
        
        for name, host, port in tcp_targets:
            try:
                start_time = time.time()
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                result = sock.connect_ex((host, port))
                latency = (time.time() - start_time) * 1000
                
                sock.close()
                
                measurement = LatencyMeasurement(
                    component=name,
                    source='local',
                    destination=f"{host}:{port}",
                    latency_ms=latency,
                    timestamp=time.time(),
                    measurement_type='tcp_connect',
                    additional_info={'connection_result': result}
                )
                
                self.latency_measurements[name].append(measurement)
                
            except Exception as e:
                logger.debug(f"TCP measurement failed for {name}: {e}")

    def measure_zmq_latencies(self):
        """Measure ZMQ socket latencies"""
        zmq_targets = [
            ('zmq_telemetry', 'tcp://localhost:5560', zmq.SUB),
            ('zmq_signals', 'tcp://localhost:5557', zmq.SUB)
        ]
        
        for name, endpoint, socket_type in zmq_targets:
            try:
                start_time = time.time()
                
                # Create socket and attempt connection
                socket = self.zmq_context.socket(socket_type)
                socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
                
                if socket_type == zmq.SUB:
                    socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
                
                socket.connect(endpoint)
                
                # For subscribers, try to receive a message to test actual connectivity
                if socket_type == zmq.SUB:
                    try:
                        socket.recv(zmq.NOBLOCK)
                    except zmq.Again:
                        pass  # No message available, but connection is working
                
                latency = (time.time() - start_time) * 1000
                socket.close()
                
                measurement = LatencyMeasurement(
                    component=name,
                    source='local',
                    destination=endpoint,
                    latency_ms=latency,
                    timestamp=time.time(),
                    measurement_type='zmq_roundtrip',
                    additional_info={'socket_type': str(socket_type)}
                )
                
                self.latency_measurements[name].append(measurement)
                
            except Exception as e:
                logger.debug(f"ZMQ measurement failed for {name}: {e}")

    def measure_redis_latency(self):
        """Measure Redis operation latencies"""
        try:
            # PING command latency
            start_time = time.time()
            self.redis_client.ping()
            ping_latency = (time.time() - start_time) * 1000
            
            measurement = LatencyMeasurement(
                component='redis_ping',
                source='local',
                destination='localhost:6379',
                latency_ms=ping_latency,
                timestamp=time.time(),
                measurement_type='redis_operation',
                additional_info={'operation': 'ping'}
            )
            
            self.latency_measurements['redis_ping'].append(measurement)
            
            # SET/GET operation latency
            start_time = time.time()
            test_key = f"latency_test_{int(time.time())}"
            self.redis_client.set(test_key, "test_value", ex=10)
            value = self.redis_client.get(test_key)
            self.redis_client.delete(test_key)
            operation_latency = (time.time() - start_time) * 1000
            
            measurement = LatencyMeasurement(
                component='redis_operations',
                source='local',
                destination='localhost:6379',
                latency_ms=operation_latency,
                timestamp=time.time(),
                measurement_type='redis_operation',
                additional_info={'operation': 'set_get_delete'}
            )
            
            self.latency_measurements['redis_operations'].append(measurement)
            
        except Exception as e:
            logger.debug(f"Redis latency measurement failed: {e}")

    def track_signal_latency(self, signal_id: str, event_type: str, timestamp: float = None):
        """Track latency events for a specific signal"""
        if timestamp is None:
            timestamp = time.time()
            
        if signal_id not in self.signal_traces:
            self.signal_traces[signal_id] = SignalLatencyTrace(
                signal_id=signal_id,
                generation_time=timestamp if event_type == 'generated' else None,
                notification_time=None,
                user_action_time=None,
                execution_start_time=None,
                execution_complete_time=None,
                total_latency=None,
                bottleneck_component=None,
                latency_breakdown={}
            )
        
        trace = self.signal_traces[signal_id]
        
        if event_type == 'generated':
            trace.generation_time = timestamp
        elif event_type == 'notified':
            trace.notification_time = timestamp
            if trace.generation_time:
                trace.latency_breakdown['generation_to_notification'] = (timestamp - trace.generation_time) * 1000
        elif event_type == 'user_action':
            trace.user_action_time = timestamp
            if trace.notification_time:
                trace.latency_breakdown['notification_to_action'] = (timestamp - trace.notification_time) * 1000
        elif event_type == 'execution_start':
            trace.execution_start_time = timestamp
            if trace.user_action_time:
                trace.latency_breakdown['action_to_execution'] = (timestamp - trace.user_action_time) * 1000
        elif event_type == 'execution_complete':
            trace.execution_complete_time = timestamp
            if trace.execution_start_time:
                trace.latency_breakdown['execution_duration'] = (timestamp - trace.execution_start_time) * 1000
            
            # Calculate total latency if we have generation time
            if trace.generation_time:
                trace.total_latency = (timestamp - trace.generation_time) * 1000
                trace.bottleneck_component = self.identify_bottleneck(trace)

    def identify_bottleneck(self, trace: SignalLatencyTrace) -> str:
        """Identify the bottleneck component in signal processing"""
        if not trace.latency_breakdown:
            return 'unknown'
        
        # Find the component with highest latency
        max_latency = 0
        bottleneck = 'unknown'
        
        for component, latency in trace.latency_breakdown.items():
            if latency > max_latency:
                max_latency = latency
                bottleneck = component
        
        return bottleneck

    def update_component_health(self):
        """Update health scores for all monitored components"""
        current_time = time.time()
        
        for component, measurements in self.latency_measurements.items():
            if not measurements:
                continue
            
            # Get recent measurements (last 5 minutes)
            recent_measurements = [
                m for m in measurements 
                if current_time - m.timestamp < 300
            ]
            
            if not recent_measurements:
                continue
            
            latencies = [m.latency_ms for m in recent_measurements]
            
            # Calculate health metrics
            avg_latency = statistics.mean(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
            
            # Calculate packet loss (if applicable)
            packet_loss_measurements = [m.packet_loss for m in recent_measurements if m.packet_loss is not None]
            avg_packet_loss = statistics.mean(packet_loss_measurements) if packet_loss_measurements else 0
            
            # Determine health score (0-100)
            health_score = 100
            
            # Latency penalties
            if avg_latency > self.latency_thresholds['critical']:
                health_score -= 60
            elif avg_latency > self.latency_thresholds['poor']:
                health_score -= 40
            elif avg_latency > self.latency_thresholds['acceptable']:
                health_score -= 20
            elif avg_latency > self.latency_thresholds['good']:
                health_score -= 10
            
            # P95 latency penalty (variability)
            if p95_latency > avg_latency * 2:
                health_score -= 15
            
            # Packet loss penalty
            health_score -= avg_packet_loss * 2  # 2 points per % packet loss
            
            health_score = max(0, health_score)
            
            # Determine health status
            if health_score >= 90:
                status = 'excellent'
            elif health_score >= 75:
                status = 'good'
            elif health_score >= 60:
                status = 'acceptable'
            elif health_score >= 30:
                status = 'poor'
            else:
                status = 'critical'
            
            self.component_health[component] = {
                'score': health_score,
                'status': status,
                'avg_latency': round(avg_latency, 1),
                'p95_latency': round(p95_latency, 1),
                'packet_loss': round(avg_packet_loss, 2),
                'measurement_count': len(recent_measurements),
                'last_updated': current_time
            }

    def cleanup_old_measurements(self):
        """Clean up old measurements and signal traces"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep last hour
        
        # Clean up old signal traces
        old_traces = [
            signal_id for signal_id, trace in self.signal_traces.items()
            if trace.generation_time and trace.generation_time < cutoff_time
        ]
        
        for signal_id in old_traces:
            del self.signal_traces[signal_id]

    def get_network_health_summary(self) -> Dict:
        """Get overall network health summary"""
        if not self.component_health:
            return {'status': 'unknown', 'message': 'No health data available'}
        
        all_scores = [health['score'] for health in self.component_health.values()]
        overall_score = statistics.mean(all_scores)
        
        # Count components by status
        status_counts = defaultdict(int)
        for health in self.component_health.values():
            status_counts[health['status']] += 1
        
        # Identify critical issues
        critical_components = [
            name for name, health in self.component_health.items()
            if health['status'] in ['critical', 'poor']
        ]
        
        # Overall status determination
        if overall_score >= 85:
            overall_status = 'excellent'
        elif overall_score >= 70:
            overall_status = 'good'
        elif overall_score >= 55:
            overall_status = 'acceptable'
        elif overall_score >= 30:
            overall_status = 'poor'
        else:
            overall_status = 'critical'
        
        return {
            'overall_score': round(overall_score, 1),
            'overall_status': overall_status,
            'total_components': len(self.component_health),
            'status_breakdown': dict(status_counts),
            'critical_components': critical_components,
            'best_performing': self.get_best_performing_components(),
            'worst_performing': self.get_worst_performing_components(),
            'recommendations': self.generate_network_recommendations()
        }

    def get_best_performing_components(self) -> List[Dict]:
        """Get best performing network components"""
        sorted_components = sorted(
            self.component_health.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        return [
            {'name': name, 'score': health['score'], 'latency': health['avg_latency']}
            for name, health in sorted_components[:3]
        ]

    def get_worst_performing_components(self) -> List[Dict]:
        """Get worst performing network components"""
        sorted_components = sorted(
            self.component_health.items(),
            key=lambda x: x[1]['score']
        )
        
        return [
            {'name': name, 'score': health['score'], 'latency': health['avg_latency'], 'status': health['status']}
            for name, health in sorted_components[:3]
            if health['score'] < 80
        ]

    def generate_network_recommendations(self) -> List[str]:
        """Generate network optimization recommendations"""
        recommendations = []
        
        # Check for high latency components
        high_latency_components = [
            (name, health) for name, health in self.component_health.items()
            if health['avg_latency'] > 200
        ]
        
        if high_latency_components:
            recommendations.append(f"🐌 High latency detected in {len(high_latency_components)} components")
            for name, health in high_latency_components:
                recommendations.append(f"   • {name}: {health['avg_latency']:.1f}ms avg latency")
        
        # Check for packet loss
        packet_loss_components = [
            (name, health) for name, health in self.component_health.items()
            if health['packet_loss'] > 1
        ]
        
        if packet_loss_components:
            recommendations.append("📡 Packet loss detected:")
            for name, health in packet_loss_components:
                recommendations.append(f"   • {name}: {health['packet_loss']:.1f}% packet loss")
        
        # Check Redis performance
        redis_components = [name for name in self.component_health.keys() if 'redis' in name]
        if redis_components:
            redis_health = [self.component_health[name] for name in redis_components]
            avg_redis_latency = statistics.mean([h['avg_latency'] for h in redis_health])
            
            if avg_redis_latency > 50:
                recommendations.append(f"🗄️ Redis latency high: {avg_redis_latency:.1f}ms - consider optimization")
        
        # Check ZMQ performance
        zmq_components = [name for name in self.component_health.keys() if 'zmq' in name]
        if zmq_components:
            zmq_health = [self.component_health[name] for name in zmq_components]
            zmq_issues = [h for h in zmq_health if h['score'] < 70]
            
            if zmq_issues:
                recommendations.append("⚡ ZMQ connectivity issues detected - check message queue health")
        
        # General recommendations
        overall_score = statistics.mean([h['score'] for h in self.component_health.values()])
        
        if overall_score < 70:
            recommendations.append("🔧 Overall network performance needs attention")
            recommendations.append("   • Consider upgrading network infrastructure")
            recommendations.append("   • Review server resource allocation")
            recommendations.append("   • Optimize database queries and connections")
        
        if not recommendations:
            recommendations.append("✅ Network performance is healthy - all systems optimal")
        
        return recommendations

    def analyze_signal_delivery_performance(self) -> Dict:
        """Analyze signal delivery pipeline performance"""
        if not self.signal_traces:
            return {'message': 'No signal trace data available'}
        
        # Analyze completed traces
        completed_traces = [
            trace for trace in self.signal_traces.values()
            if trace.total_latency is not None
        ]
        
        if not completed_traces:
            return {'message': 'No completed signal traces available'}
        
        # Calculate performance metrics
        total_latencies = [trace.total_latency for trace in completed_traces]
        avg_total_latency = statistics.mean(total_latencies)
        p95_total_latency = sorted(total_latencies)[int(len(total_latencies) * 0.95)]
        
        # Breakdown analysis
        breakdown_analysis = defaultdict(list)
        for trace in completed_traces:
            for component, latency in trace.latency_breakdown.items():
                breakdown_analysis[component].append(latency)
        
        breakdown_stats = {}
        for component, latencies in breakdown_analysis.items():
            breakdown_stats[component] = {
                'avg_latency': round(statistics.mean(latencies), 1),
                'max_latency': round(max(latencies), 1),
                'occurrence_count': len(latencies)
            }
        
        # Bottleneck analysis
        bottleneck_counts = defaultdict(int)
        for trace in completed_traces:
            if trace.bottleneck_component:
                bottleneck_counts[trace.bottleneck_component] += 1
        
        return {
            'total_signals_traced': len(completed_traces),
            'avg_total_latency': round(avg_total_latency, 1),
            'p95_total_latency': round(p95_total_latency, 1),
            'latency_breakdown': breakdown_stats,
            'common_bottlenecks': dict(bottleneck_counts),
            'performance_rating': self.rate_signal_delivery_performance(avg_total_latency),
            'optimization_suggestions': self.suggest_signal_delivery_optimizations(breakdown_stats, bottleneck_counts)
        }

    def rate_signal_delivery_performance(self, avg_latency: float) -> str:
        """Rate overall signal delivery performance"""
        if avg_latency < 1000:  # <1 second
            return 'EXCELLENT'
        elif avg_latency < 3000:  # <3 seconds
            return 'GOOD'
        elif avg_latency < 5000:  # <5 seconds
            return 'ACCEPTABLE'
        elif avg_latency < 10000:  # <10 seconds
            return 'POOR'
        else:
            return 'CRITICAL'

    def suggest_signal_delivery_optimizations(self, breakdown_stats: Dict, bottleneck_counts: Dict) -> List[str]:
        """Suggest optimizations for signal delivery"""
        suggestions = []
        
        # Identify slowest components
        if breakdown_stats:
            slowest_component = max(breakdown_stats.items(), key=lambda x: x[1]['avg_latency'])
            if slowest_component[1]['avg_latency'] > 1000:
                suggestions.append(f"🎯 Optimize {slowest_component[0]} - avg {slowest_component[1]['avg_latency']:.1f}ms")
        
        # Analyze bottlenecks
        if bottleneck_counts:
            most_common_bottleneck = max(bottleneck_counts.items(), key=lambda x: x[1])
            suggestions.append(f"🔧 Address {most_common_bottleneck[0]} bottleneck - affects {most_common_bottleneck[1]} signals")
        
        # Specific optimizations
        if 'generation_to_notification' in breakdown_stats:
            notification_latency = breakdown_stats['generation_to_notification']['avg_latency']
            if notification_latency > 500:
                suggestions.append("📱 Telegram notification latency high - consider webhook optimization")
        
        if 'action_to_execution' in breakdown_stats:
            execution_latency = breakdown_stats['action_to_execution']['avg_latency']
            if execution_latency > 1000:
                suggestions.append("⚡ Trade execution latency high - optimize broker API calls")
        
        return suggestions

    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive network latency report"""
        
        network_health = self.get_network_health_summary()
        signal_performance = self.analyze_signal_delivery_performance()
        
        # System resource analysis
        system_resources = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections()),
            'active_processes': len(psutil.pids())
        }
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'monitoring_status': 'active' if self.monitoring_active else 'inactive',
            'network_health': network_health,
            'signal_delivery_performance': signal_performance,
            'component_details': self.component_health,
            'system_resources': system_resources,
            'recent_measurements_count': sum(len(measurements) for measurements in self.latency_measurements.values()),
            'active_signal_traces': len(self.signal_traces),
            'optimization_priority': self.determine_optimization_priority(network_health, signal_performance)
        }
        
        return report

    def determine_optimization_priority(self, network_health: Dict, signal_performance: Dict) -> List[Dict]:
        """Determine optimization priorities based on performance data"""
        
        priorities = []
        
        # Network health priorities
        if network_health.get('overall_score', 100) < 70:
            priorities.append({
                'priority': 'HIGH',
                'component': 'network_infrastructure',
                'issue': f"Overall network score {network_health['overall_score']}/100",
                'impact': 'System-wide performance degradation'
            })
        
        critical_components = network_health.get('critical_components', [])
        for component in critical_components:
            health = self.component_health.get(component, {})
            priorities.append({
                'priority': 'HIGH',
                'component': component,
                'issue': f"Critical status - {health.get('avg_latency', 0):.1f}ms avg latency",
                'impact': 'Component failure or severe performance impact'
            })
        
        # Signal delivery priorities
        if 'avg_total_latency' in signal_performance:
            avg_latency = signal_performance['avg_total_latency']
            if avg_latency > 5000:  # >5 seconds
                priorities.append({
                    'priority': 'HIGH',
                    'component': 'signal_delivery_pipeline',
                    'issue': f"High signal delivery latency: {avg_latency:.1f}ms",
                    'impact': 'Poor user experience, missed trading opportunities'
                })
        
        # Sort by priority
        priority_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        priorities.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return priorities[:10]  # Top 10 priorities

def main():
    """Run network latency monitoring and analysis"""
    
    monitor = NetworkLatencyMonitor()
    
    print("=== NETWORK LATENCY MONITOR ===")
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Wait for some measurements
    print("Collecting measurements...")
    time.sleep(60)  # Wait 1 minute for data collection
    
    # Generate report
    report = monitor.generate_comprehensive_report()
    
    print(f"\nNetwork Health: {report['network_health']['overall_status'].upper()} ({report['network_health']['overall_score']}/100)")
    
    if report['signal_delivery_performance'].get('performance_rating'):
        print(f"Signal Delivery: {report['signal_delivery_performance']['performance_rating']}")
        print(f"Average Latency: {report['signal_delivery_performance'].get('avg_total_latency', 0):.1f}ms")
    
    print(f"\nComponent Health:")
    for name, health in report['component_details'].items():
        status_emoji = {
            'excellent': '🟢',
            'good': '🔵', 
            'acceptable': '🟡',
            'poor': '🟠',
            'critical': '🔴'
        }.get(health['status'], '⚪')
        
        print(f"  {status_emoji} {name}: {health['score']}/100 ({health['avg_latency']:.1f}ms)")
    
    print(f"\n🎯 Top Optimization Priorities:")
    for i, priority in enumerate(report['optimization_priority'][:3], 1):
        print(f"{i}. [{priority['priority']}] {priority['component']}: {priority['issue']}")
    
    # Save detailed report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f'/root/HydraX-v2/reports/network_latency_report_{timestamp}.json'
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Detailed report saved to: {report_path}")
    
    # Stop monitoring
    monitor.stop_monitoring()

if __name__ == "__main__":
    main()