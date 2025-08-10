#!/usr/bin/env python3
"""
HEARTBEAT MONITOR v1.0
Monitor node heartbeats and clean up dead connections

Author: BITTEN Trading System
Date: August 6, 2025
Purpose: Detect dead EA connections and maintain system health
"""

import redis
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict

# Optional email imports - only import if needed
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - HEARTBEAT_MONITOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/heartbeat_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HeartbeatMonitor:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.timeout = 60  # seconds - consider node dead after 60s without heartbeat
        self.check_interval = 30  # seconds - check every 30 seconds
        self.alert_cooldown = 300  # seconds - don't spam alerts for same node
        self.running = True
        
        # Alert configuration
        self.enable_email_alerts = False  # Set to True to enable email alerts
        self.smtp_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'username': '',  # Configure if email alerts needed
            'password': '',  # Configure if email alerts needed
            'from_email': '',
            'to_emails': []
        }
        
        # Statistics tracking
        self.disconnection_stats = defaultdict(int)
        self.connection_stability = {}
        self.recent_alerts = {}  # Track recent alerts to avoid spam
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Connected to Redis server")
        except redis.ConnectionError:
            logger.error("❌ Failed to connect to Redis server")
            raise
        
        logger.info("💓 Heartbeat Monitor v1.0 initialized")

    def check_all_nodes(self):
        """Check heartbeat status of all nodes"""
        try:
            active_node_ids = self.redis_client.smembers("active_nodes")
            
            if not active_node_ids:
                logger.debug("No active nodes to check")
                return {'checked': 0, 'timeouts': 0, 'healthy': 0}
            
            timeout_nodes = []
            healthy_nodes = []
            current_time = time.time()
            
            for node_id in active_node_ids:
                node_data = self.redis_client.hgetall(f"node:{node_id}")
                
                if not node_data:
                    # Node data missing - clean up
                    logger.warning(f"⚠️ Node data missing for {node_id}, cleaning up")
                    self._cleanup_missing_node(node_id)
                    continue
                
                last_heartbeat = float(node_data.get('last_heartbeat', 0))
                time_since_heartbeat = current_time - last_heartbeat
                
                if time_since_heartbeat > self.timeout:
                    timeout_nodes.append({
                        'node_id': node_id,
                        'account': node_data.get('account', 'UNKNOWN'),
                        'broker': node_data.get('broker', 'UNKNOWN'),
                        'time_since_heartbeat': time_since_heartbeat,
                        'last_heartbeat': last_heartbeat
                    })
                    self._handle_node_timeout(node_id, time_since_heartbeat)
                else:
                    healthy_nodes.append(node_id)
                    self._update_connection_stability(node_id, time_since_heartbeat)
            
            logger.debug(f"💓 Heartbeat check: {len(healthy_nodes)} healthy, {len(timeout_nodes)} timeouts")
            
            return {
                'checked': len(active_node_ids),
                'healthy': len(healthy_nodes),
                'timeouts': len(timeout_nodes),
                'timeout_nodes': timeout_nodes
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking nodes: {str(e)}")
            return {'error': str(e)}

    def _handle_node_timeout(self, node_id: str, time_since_heartbeat: float):
        """Handle a node that has timed out"""
        try:
            node_data = self.redis_client.hgetall(f"node:{node_id}")
            
            if not node_data:
                self._cleanup_missing_node(node_id)
                return
            
            account = node_data.get('account', 'UNKNOWN')
            broker = node_data.get('broker', 'UNKNOWN')
            
            # Calculate uptime before disconnection
            connected_at = float(node_data.get('connected_at', time.time()))
            uptime = time.time() - connected_at
            
            # Update node status
            disconnect_updates = {
                'status': 'timeout',
                'disconnected_at': str(time.time()),
                'total_uptime': str(uptime),
                'disconnect_reason': 'heartbeat_timeout',
                'time_since_last_heartbeat': str(time_since_heartbeat)
            }
            
            self.redis_client.hset(f"node:{node_id}", mapping=disconnect_updates)
            
            # Remove from active nodes
            self.redis_client.srem("active_nodes", node_id)
            
            # Remove account mapping if this is the current active node
            current_node = self.redis_client.hget("account_to_node", account)
            if current_node == node_id:
                self.redis_client.hdel("account_to_node", account)
            
            # Update statistics
            self.disconnection_stats['total_timeouts'] += 1
            self.disconnection_stats[f'broker_{broker}'] += 1
            
            # Log disconnection event
            self._log_disconnection_event(node_id, 'timeout', {
                'account': account,
                'broker': broker,
                'uptime_seconds': uptime,
                'time_since_heartbeat': time_since_heartbeat
            })
            
            # Send alert if not recently sent for this node
            self._send_timeout_alert(node_id, account, broker, time_since_heartbeat, uptime)
            
            logger.warning(f"⏰ Node timeout: {node_id} (Account: {account}, {time_since_heartbeat:.1f}s since heartbeat)")
            
        except Exception as e:
            logger.error(f"Error handling node timeout for {node_id}: {str(e)}")

    def _cleanup_missing_node(self, node_id: str):
        """Clean up references to a node with missing data"""
        try:
            # Remove from active nodes
            self.redis_client.srem("active_nodes", node_id)
            
            # Check and clean account mappings
            account_mappings = self.redis_client.hgetall("account_to_node")
            for account, mapped_node in account_mappings.items():
                if mapped_node == node_id:
                    self.redis_client.hdel("account_to_node", account)
                    break
            
            logger.warning(f"🧹 Cleaned up missing node: {node_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up missing node {node_id}: {str(e)}")

    def _update_connection_stability(self, node_id: str, heartbeat_latency: float):
        """Track connection stability metrics"""
        try:
            if node_id not in self.connection_stability:
                self.connection_stability[node_id] = {
                    'avg_latency': heartbeat_latency,
                    'max_latency': heartbeat_latency,
                    'check_count': 1,
                    'first_seen': time.time()
                }
            else:
                stats = self.connection_stability[node_id]
                stats['check_count'] += 1
                stats['avg_latency'] = (stats['avg_latency'] * (stats['check_count'] - 1) + heartbeat_latency) / stats['check_count']
                stats['max_latency'] = max(stats['max_latency'], heartbeat_latency)
            
            # Store in Redis for persistence
            stability_key = f"connection_stability:{node_id}"
            self.redis_client.hset(stability_key, mapping={
                'avg_latency': str(self.connection_stability[node_id]['avg_latency']),
                'max_latency': str(self.connection_stability[node_id]['max_latency']),
                'check_count': str(self.connection_stability[node_id]['check_count']),
                'last_updated': str(time.time())
            })
            self.redis_client.expire(stability_key, 86400)  # Keep for 24 hours
            
        except Exception as e:
            logger.error(f"Error updating connection stability for {node_id}: {str(e)}")

    def _log_disconnection_event(self, node_id: str, event_type: str, event_data: Dict):
        """Log disconnection events"""
        try:
            event_record = {
                'timestamp': time.time(),
                'event_type': 'node_disconnection',
                'disconnect_reason': event_type,
                'node_id': node_id,
                'event_data': event_data
            }
            
            # Store in Redis
            self.redis_client.lpush("disconnection_events", json.dumps(event_record))
            self.redis_client.ltrim("disconnection_events", 0, 9999)  # Keep last 10k events
            
            # Store in file
            with open('/root/HydraX-v2/logs/disconnection_events.jsonl', 'a') as f:
                f.write(json.dumps(event_record) + '\n')
        
        except Exception as e:
            logger.error(f"Error logging disconnection event: {str(e)}")

    def _send_timeout_alert(self, node_id: str, account: str, broker: str, time_since_heartbeat: float, uptime: float):
        """Send alert for node timeout (respects cooldown)"""
        try:
            current_time = time.time()
            alert_key = f"alert_{node_id}"
            
            # Check if we recently sent an alert for this node
            if alert_key in self.recent_alerts:
                if current_time - self.recent_alerts[alert_key] < self.alert_cooldown:
                    logger.debug(f"Skipping alert for {node_id} (cooldown active)")
                    return
            
            # Record alert time
            self.recent_alerts[alert_key] = current_time
            
            # Create alert message
            alert_data = {
                'type': 'node_timeout_alert',
                'timestamp': current_time,
                'node_id': node_id,
                'account': account,
                'broker': broker,
                'time_since_heartbeat': time_since_heartbeat,
                'uptime_minutes': uptime / 60,
                'severity': 'HIGH' if time_since_heartbeat > 300 else 'MEDIUM'  # 5+ minutes is high severity
            }
            
            # Store alert in Redis
            self.redis_client.lpush("system_alerts", json.dumps(alert_data))
            self.redis_client.ltrim("system_alerts", 0, 999)  # Keep last 1000 alerts
            
            # Send email if configured
            if self.enable_email_alerts and self.smtp_config['username']:
                self._send_email_alert(alert_data)
            
            # Log to file
            with open('/root/HydraX-v2/logs/system_alerts.jsonl', 'a') as f:
                f.write(json.dumps(alert_data) + '\n')
            
            logger.info(f"🚨 ALERT: Node timeout - {account} ({broker}) - {time_since_heartbeat:.1f}s offline")
            
        except Exception as e:
            logger.error(f"Error sending timeout alert: {str(e)}")

    def _send_email_alert(self, alert_data: Dict):
        """Send email alert (if configured)"""
        try:
            if not EMAIL_AVAILABLE:
                logger.warning("Email functionality not available - skipping email alert")
                return
                
            if not self.smtp_config['to_emails']:
                return
            
            subject = f"BITTEN Alert: Node Timeout - {alert_data['account']}"
            
            body = f"""
BITTEN Trading System Alert

Node Timeout Detected:
- Account: {alert_data['account']}
- Broker: {alert_data['broker']}
- Node ID: {alert_data['node_id']}
- Time Since Heartbeat: {alert_data['time_since_heartbeat']:.1f} seconds
- Previous Uptime: {alert_data['uptime_minutes']:.1f} minutes
- Severity: {alert_data['severity']}
- Time: {datetime.fromtimestamp(alert_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}

Please check the EA connection and system logs.
"""
            
            msg = MimeMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.smtp_config['to_emails'])
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"📧 Email alert sent for node {alert_data['node_id']}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")

    def get_disconnection_stats(self) -> Dict:
        """Get disconnection and connection health statistics"""
        try:
            # Basic disconnection stats
            stats = dict(self.disconnection_stats)
            
            # Recent disconnection rate (last hour)
            one_hour_ago = time.time() - 3600
            recent_events = []
            
            disconnect_events = self.redis_client.lrange("disconnection_events", 0, 999)
            for event_str in disconnect_events:
                try:
                    event = json.loads(event_str)
                    if event['timestamp'] > one_hour_ago:
                        recent_events.append(event)
                except json.JSONDecodeError:
                    continue
            
            stats['recent_disconnections_1h'] = len(recent_events)
            stats['disconnection_rate_per_hour'] = len(recent_events)
            
            # Connection stability stats
            active_nodes = self.redis_client.smembers("active_nodes")
            
            if active_nodes:
                stability_stats = []
                for node_id in active_nodes:
                    stability_data = self.redis_client.hgetall(f"connection_stability:{node_id}")
                    if stability_data:
                        stability_stats.append({
                            'node_id': node_id,
                            'avg_latency': float(stability_data.get('avg_latency', 0)),
                            'max_latency': float(stability_data.get('max_latency', 0)),
                            'check_count': int(stability_data.get('check_count', 0))
                        })
                
                if stability_stats:
                    avg_latencies = [s['avg_latency'] for s in stability_stats]
                    max_latencies = [s['max_latency'] for s in stability_stats]
                    
                    stats['connection_health'] = {
                        'nodes_tracked': len(stability_stats),
                        'avg_heartbeat_latency': round(sum(avg_latencies) / len(avg_latencies), 2),
                        'max_heartbeat_latency': round(max(max_latencies), 2),
                        'healthy_connections': len([s for s in stability_stats if s['avg_latency'] < 30])
                    }
            
            # System health score (0-100)
            health_score = self._calculate_system_health_score(stats)
            stats['system_health_score'] = health_score
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting disconnection stats: {str(e)}")
            return {'error': str(e)}

    def _calculate_system_health_score(self, stats: Dict) -> int:
        """Calculate overall system health score 0-100"""
        try:
            score = 100
            
            # Penalize recent disconnections
            recent_disconnects = stats.get('recent_disconnections_1h', 0)
            if recent_disconnects > 0:
                score -= min(recent_disconnects * 10, 50)  # Max 50 point penalty
            
            # Reward connection stability
            connection_health = stats.get('connection_health', {})
            if connection_health:
                avg_latency = connection_health.get('avg_heartbeat_latency', 60)
                if avg_latency < 10:
                    score += 5  # Bonus for very fast heartbeats
                elif avg_latency > 45:
                    score -= 15  # Penalty for slow heartbeats
            
            # Penalize if too many total timeouts
            total_timeouts = stats.get('total_timeouts', 0)
            if total_timeouts > 10:
                score -= min((total_timeouts - 10) * 2, 20)
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {str(e)}")
            return 50  # Default middle score

    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent system alerts"""
        try:
            alert_strings = self.redis_client.lrange("system_alerts", 0, limit - 1)
            alerts = []
            
            for alert_str in alert_strings:
                try:
                    alert = json.loads(alert_str)
                    alerts.append(alert)
                except json.JSONDecodeError:
                    continue
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []

    def cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            current_time = time.time()
            cleaned_count = 0
            
            # Clean old connection stability data (older than 24 hours)
            stability_keys = self.redis_client.keys("connection_stability:*")
            for key in stability_keys:
                last_updated = self.redis_client.hget(key, "last_updated")
                if last_updated and current_time - float(last_updated) > 86400:
                    self.redis_client.delete(key)
                    cleaned_count += 1
            
            # Clean old alert cooldowns
            expired_alerts = []
            for alert_key, timestamp in self.recent_alerts.items():
                if current_time - timestamp > self.alert_cooldown * 2:
                    expired_alerts.append(alert_key)
            
            for alert_key in expired_alerts:
                del self.recent_alerts[alert_key]
            
            if cleaned_count > 0:
                logger.debug(f"🧹 Cleaned up {cleaned_count} old monitoring records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")

    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        try:
            logger.debug("🔄 Starting monitoring cycle")
            
            # Check all nodes for timeouts
            check_results = self.check_all_nodes()
            
            # Clean up old data periodically
            if int(time.time()) % 3600 == 0:  # Every hour
                self.cleanup_old_data()
            
            # Report summary if there were timeouts
            if check_results.get('timeouts', 0) > 0:
                logger.warning(f"⚠️ Monitoring cycle: {check_results['timeouts']} nodes timed out")
            
            return check_results
            
        except Exception as e:
            logger.error(f"❌ Error in monitoring cycle: {str(e)}")
            return {'error': str(e)}

    def monitor_continuously(self):
        """Continuous monitoring loop"""
        logger.info("🔄 Starting continuous heartbeat monitoring...")
        
        while self.running:
            try:
                # Run monitoring cycle
                results = self.run_monitoring_cycle()
                
                # Log status every 5 minutes
                if int(time.time()) % 300 == 0:
                    stats = self.get_disconnection_stats()
                    health_score = stats.get('system_health_score', 50)
                    active_nodes = len(self.redis_client.smembers("active_nodes"))
                    
                    logger.info(f"💓 Monitor Status: {active_nodes} active nodes, "
                              f"Health Score: {health_score}/100, "
                              f"Recent disconnects: {stats.get('recent_disconnections_1h', 0)}")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in continuous monitoring: {str(e)}")
                time.sleep(self.check_interval)

    def start_monitoring(self):
        """Start heartbeat monitoring in background thread"""
        logger.info("💓 Starting heartbeat monitoring...")
        monitor_thread = threading.Thread(target=self.monitor_continuously, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def stop_monitoring(self):
        """Stop heartbeat monitoring"""
        logger.info("🛑 Stopping heartbeat monitoring...")
        self.running = False

    def force_cleanup_node(self, node_id: str) -> bool:
        """Force cleanup of a specific node (admin function)"""
        try:
            # Get node data before cleanup
            node_data = self.redis_client.hgetall(f"node:{node_id}")
            
            if not node_data:
                logger.warning(f"Node {node_id} not found")
                return False
            
            account = node_data.get('account', 'UNKNOWN')
            
            # Force timeout handling
            self._handle_node_timeout(node_id, 9999)  # Large timeout value
            
            logger.info(f"🧹 Force cleaned up node: {node_id} (Account: {account})")
            return True
            
        except Exception as e:
            logger.error(f"Error force cleaning node {node_id}: {str(e)}")
            return False

    def get_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        try:
            stats = self.get_disconnection_stats()
            active_nodes = len(self.redis_client.smembers("active_nodes"))
            recent_alerts = self.get_recent_alerts(10)
            
            report = {
                'timestamp': time.time(),
                'active_nodes': active_nodes,
                'health_score': stats.get('system_health_score', 50),
                'recent_disconnections_1h': stats.get('recent_disconnections_1h', 0),
                'total_timeouts': stats.get('total_timeouts', 0),
                'connection_health': stats.get('connection_health', {}),
                'recent_alerts_count': len(recent_alerts),
                'system_status': 'HEALTHY' if stats.get('system_health_score', 0) >= 80 else 
                               'WARNING' if stats.get('system_health_score', 0) >= 60 else 'CRITICAL'
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {'error': str(e)}

# API wrapper for easy integration
class HeartbeatMonitorAPI:
    def __init__(self):
        self.monitor = HeartbeatMonitor()
        self.monitor.start_monitoring()
    
    def get_stats(self) -> Dict:
        return self.monitor.get_disconnection_stats()
    
    def get_health_report(self) -> Dict:
        return self.monitor.get_health_report()
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        return self.monitor.get_recent_alerts(limit)
    
    def force_cleanup(self, node_id: str) -> bool:
        return self.monitor.force_cleanup_node(node_id)

if __name__ == "__main__":
    # Example usage and testing
    monitor = HeartbeatMonitor()
    
    # Start monitoring
    monitor_thread = monitor.start_monitoring()
    
    try:
        logger.info("💓 Heartbeat Monitor running... Press Ctrl+C to stop")
        
        while True:
            time.sleep(60)
            
            # Show health report every minute
            health_report = monitor.get_health_report()
            logger.info(f"Health: {health_report['system_status']} "
                       f"(Score: {health_report['health_score']}/100, "
                       f"Nodes: {health_report['active_nodes']})")
    
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        monitor.stop_monitoring()