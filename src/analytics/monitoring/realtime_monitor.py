"""
Real-time Monitoring System for Press Pass Metrics

Monitors key performance indicators in real-time and triggers
alerts for anomalies or important events.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from decimal import Decimal
import json
import redis
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics being monitored"""
    COUNTER = "counter"
    GAUGE = "gauge"
    RATE = "rate"
    HISTOGRAM = "histogram"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricThreshold:
    """Threshold configuration for alerts"""
    metric_name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    rate_of_change: Optional[float] = None
    severity: AlertSeverity = AlertSeverity.WARNING
    cooldown_minutes: int = 15

class RealtimeMonitor:
    """Real-time monitoring system for Press Pass conversion metrics"""
    
    def __init__(self, db_connection, redis_client: redis.Redis):
        self.db = db_connection
        self.redis = redis_client
        self.monitoring_interval = 60  # seconds
        self.metrics_buffer = {}
        self.alert_callbacks = []
        self.thresholds = self._initialize_thresholds()
        self.is_running = False
        
    def _initialize_thresholds(self) -> Dict[str, MetricThreshold]:
        """Initialize metric thresholds for alerting"""
        return {
            'press_pass_conversions': MetricThreshold(
                metric_name='press_pass_conversions',
                min_value=0.5,  # Alert if conversion rate drops below 0.5%
                severity=AlertSeverity.ERROR
            ),
            'activation_rate': MetricThreshold(
                metric_name='activation_rate',
                min_value=20.0,  # Alert if activation rate drops below 20%
                severity=AlertSeverity.WARNING
            ),
            'xp_reset_failures': MetricThreshold(
                metric_name='xp_reset_failures',
                max_value=5,  # Alert if more than 5 failures in a period
                severity=AlertSeverity.CRITICAL
            ),
            'churn_rate_spike': MetricThreshold(
                metric_name='churn_rate_spike',
                rate_of_change=50.0,  # Alert if churn increases by 50%
                severity=AlertSeverity.ERROR
            ),
            'upgrade_rate': MetricThreshold(
                metric_name='upgrade_rate',
                min_value=5.0,  # Alert if upgrade rate drops below 5%
                severity=AlertSeverity.WARNING
            ),
            'response_time': MetricThreshold(
                metric_name='response_time',
                max_value=1000,  # Alert if response time exceeds 1 second
                severity=AlertSeverity.WARNING
            ),
            'error_rate': MetricThreshold(
                metric_name='error_rate',
                max_value=5.0,  # Alert if error rate exceeds 5%
                severity=AlertSeverity.ERROR
            )
        }
    
    async def start_monitoring(self):
        """Start the real-time monitoring loop"""
        self.is_running = True
        logger.info("Starting real-time monitoring system")
        
        tasks = [
            self._monitor_conversions(),
            self._monitor_activations(),
            self._monitor_xp_resets(),
            self._monitor_churn(),
            self._monitor_system_health()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_running = False
        logger.info("Stopping real-time monitoring system")
    
    def add_alert_callback(self, callback: Callable):
        """Add a callback for alert notifications"""
        self.alert_callbacks.append(callback)
    
    async def _monitor_conversions(self):
        """Monitor Press Pass conversion metrics in real-time"""
        while self.is_running:
            try:
                # Get real-time conversion data
                query = """
                WITH recent_data AS (
                    SELECT 
                        COUNT(DISTINCT session_id) as views,
                        COUNT(DISTINCT CASE 
                            WHEN event_name = 'press_pass_claimed' THEN user_id 
                        END) as conversions
                    FROM analytics_events
                    WHERE created_at >= NOW() - INTERVAL '1 hour'
                        AND page_path = '/press-pass'
                )
                SELECT 
                    views,
                    conversions,
                    CASE 
                        WHEN views > 0 THEN ROUND(conversions::numeric / views * 100, 2)
                        ELSE 0
                    END as conversion_rate
                FROM recent_data;
                """
                
                result = await self.db.fetch_one(query)
                
                # Store metrics
                await self._store_metric('press_pass_views', result['views'], MetricType.COUNTER)
                await self._store_metric('press_pass_conversions', result['conversions'], MetricType.COUNTER)
                await self._store_metric('press_pass_conversion_rate', float(result['conversion_rate']), MetricType.GAUGE)
                
                # Check thresholds
                await self._check_threshold('press_pass_conversions', float(result['conversion_rate']))
                
                # Store in Redis for dashboard
                await self._update_redis_metrics({
                    'conversions': {
                        'views': result['views'],
                        'conversions': result['conversions'],
                        'rate': float(result['conversion_rate']),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error monitoring conversions: {e}")
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def _monitor_activations(self):
        """Monitor user activation metrics"""
        while self.is_running:
            try:
                query = """
                WITH recent_users AS (
                    SELECT 
                        u.user_id,
                        u.created_at,
                        MIN(t.created_at) as first_trade_at
                    FROM users u
                    LEFT JOIN trades t ON u.user_id = t.user_id
                    WHERE u.tier = 'PRESS_PASS'
                        AND u.created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY u.user_id, u.created_at
                )
                SELECT 
                    COUNT(*) as new_users,
                    COUNT(first_trade_at) as activated_users,
                    CASE 
                        WHEN COUNT(*) > 0 THEN 
                            ROUND(COUNT(first_trade_at)::numeric / COUNT(*) * 100, 2)
                        ELSE 0
                    END as activation_rate,
                    AVG(EXTRACT(EPOCH FROM (first_trade_at - created_at))/3600) as avg_hours_to_activate
                FROM recent_users;
                """
                
                result = await self.db.fetch_one(query)
                
                # Store metrics
                await self._store_metric('new_press_pass_users', result['new_users'], MetricType.COUNTER)
                await self._store_metric('activated_users', result['activated_users'], MetricType.COUNTER)
                await self._store_metric('activation_rate', float(result['activation_rate']), MetricType.GAUGE)
                await self._store_metric('avg_activation_time', float(result['avg_hours_to_activate'] or 0), MetricType.GAUGE)
                
                # Check thresholds
                await self._check_threshold('activation_rate', float(result['activation_rate']))
                
                # Update Redis
                await self._update_redis_metrics({
                    'activations': {
                        'new_users': result['new_users'],
                        'activated': result['activated_users'],
                        'rate': float(result['activation_rate']),
                        'avg_hours': float(result['avg_hours_to_activate'] or 0),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error monitoring activations: {e}")
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def _monitor_xp_resets(self):
        """Monitor XP reset operations"""
        while self.is_running:
            try:
                # Check if we're near midnight GMT
                now = datetime.utcnow()
                midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                next_midnight = midnight + timedelta(days=1)
                
                # Monitor reset status around midnight
                if (next_midnight - now).total_seconds() < 300:  # Within 5 minutes of midnight
                    query = """
                    SELECT 
                        COUNT(DISTINCT user_id) as pending_resets,
                        SUM(amount) as total_xp_to_reset
                    FROM xp_transactions
                    WHERE DATE(created_at) = CURRENT_DATE
                        AND user_id IN (
                            SELECT user_id FROM users 
                            WHERE tier = 'PRESS_PASS' 
                            AND subscription_status = 'ACTIVE'
                        );
                    """
                    
                    result = await self.db.fetch_one(query)
                    
                    await self._store_metric('pending_xp_resets', result['pending_resets'], MetricType.GAUGE)
                    await self._store_metric('pending_xp_amount', result['total_xp_to_reset'] or 0, MetricType.GAUGE)
                    
                    # Check for reset failures (stored in Redis)
                    failures = await self.redis.get('xp_reset_failures') or 0
                    await self._check_threshold('xp_reset_failures', int(failures))
                
            except Exception as e:
                logger.error(f"Error monitoring XP resets: {e}")
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def _monitor_churn(self):
        """Monitor churn indicators"""
        while self.is_running:
            try:
                query = """
                WITH churn_indicators AS (
                    SELECT 
                        COUNT(DISTINCT CASE 
                            WHEN last_login_at < NOW() - INTERVAL '3 days' THEN user_id 
                        END) as at_risk_users,
                        COUNT(DISTINCT CASE 
                            WHEN last_login_at < NOW() - INTERVAL '7 days' THEN user_id 
                        END) as churned_users,
                        COUNT(DISTINCT user_id) as total_active_users
                    FROM users
                    WHERE tier = 'PRESS_PASS'
                        AND subscription_status = 'ACTIVE'
                        AND created_at < NOW() - INTERVAL '7 days'
                )
                SELECT 
                    at_risk_users,
                    churned_users,
                    total_active_users,
                    CASE 
                        WHEN total_active_users > 0 THEN 
                            ROUND(churned_users::numeric / total_active_users * 100, 2)
                        ELSE 0
                    END as churn_rate
                FROM churn_indicators;
                """
                
                result = await self.db.fetch_one(query)
                
                # Store current metrics
                current_churn_rate = float(result['churn_rate'])
                await self._store_metric('at_risk_users', result['at_risk_users'], MetricType.GAUGE)
                await self._store_metric('churned_users', result['churned_users'], MetricType.GAUGE)
                await self._store_metric('churn_rate', current_churn_rate, MetricType.GAUGE)
                
                # Check for churn rate spike
                previous_churn_rate = await self._get_previous_metric('churn_rate')
                if previous_churn_rate and previous_churn_rate > 0:
                    rate_change = ((current_churn_rate - previous_churn_rate) / previous_churn_rate) * 100
                    await self._check_threshold('churn_rate_spike', rate_change)
                
                # Update Redis
                await self._update_redis_metrics({
                    'churn': {
                        'at_risk': result['at_risk_users'],
                        'churned': result['churned_users'],
                        'total_active': result['total_active_users'],
                        'rate': current_churn_rate,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Error monitoring churn: {e}")
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def _monitor_system_health(self):
        """Monitor system health metrics"""
        while self.is_running:
            try:
                # Monitor API response times
                response_times = await self._get_response_times()
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    await self._store_metric('response_time', avg_response_time, MetricType.GAUGE)
                    await self._check_threshold('response_time', avg_response_time)
                
                # Monitor error rates
                error_rate = await self._get_error_rate()
                await self._store_metric('error_rate', error_rate, MetricType.GAUGE)
                await self._check_threshold('error_rate', error_rate)
                
                # Monitor database performance
                db_metrics = await self._get_database_metrics()
                await self._store_metric('db_connection_count', db_metrics['connections'], MetricType.GAUGE)
                await self._store_metric('db_query_time', db_metrics['avg_query_time'], MetricType.GAUGE)
                
            except Exception as e:
                logger.error(f"Error monitoring system health: {e}")
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def _store_metric(self, name: str, value: float, metric_type: MetricType):
        """Store metric in buffer and Redis"""
        key = f"metric:{name}"
        
        # Store in memory buffer
        if name not in self.metrics_buffer:
            self.metrics_buffer[name] = []
        
        self.metrics_buffer[name].append({
            'value': value,
            'timestamp': datetime.utcnow(),
            'type': metric_type.value
        })
        
        # Keep only last hour of data
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.metrics_buffer[name] = [
            m for m in self.metrics_buffer[name] if m['timestamp'] > cutoff
        ]
        
        # Store in Redis with TTL
        await self.redis.setex(
            key,
            3600,  # 1 hour TTL
            json.dumps({
                'value': value,
                'type': metric_type.value,
                'timestamp': datetime.utcnow().isoformat()
            })
        )
    
    async def _get_previous_metric(self, name: str) -> Optional[float]:
        """Get previous value of a metric"""
        if name in self.metrics_buffer and len(self.metrics_buffer[name]) > 1:
            return self.metrics_buffer[name][-2]['value']
        return None
    
    async def _check_threshold(self, metric_name: str, value: float):
        """Check if metric exceeds thresholds and trigger alerts"""
        if metric_name not in self.thresholds:
            return
        
        threshold = self.thresholds[metric_name]
        alert_triggered = False
        alert_message = ""
        
        # Check minimum threshold
        if threshold.min_value is not None and value < threshold.min_value:
            alert_triggered = True
            alert_message = f"{metric_name} below threshold: {value} < {threshold.min_value}"
        
        # Check maximum threshold
        elif threshold.max_value is not None and value > threshold.max_value:
            alert_triggered = True
            alert_message = f"{metric_name} above threshold: {value} > {threshold.max_value}"
        
        # Check rate of change threshold
        elif threshold.rate_of_change is not None:
            previous = await self._get_previous_metric(metric_name)
            if previous and previous != 0:
                change_rate = abs((value - previous) / previous * 100)
                if change_rate > threshold.rate_of_change:
                    alert_triggered = True
                    alert_message = f"{metric_name} rate of change: {change_rate:.2f}% exceeds {threshold.rate_of_change}%"
        
        if alert_triggered:
            await self._trigger_alert(metric_name, value, threshold.severity, alert_message)
    
    async def _trigger_alert(self, metric_name: str, value: float, severity: AlertSeverity, message: str):
        """Trigger an alert"""
        # Check cooldown
        cooldown_key = f"alert_cooldown:{metric_name}"
        if await self.redis.exists(cooldown_key):
            return
        
        alert = {
            'metric': metric_name,
            'value': value,
            'severity': severity.value,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log alert
        if severity == AlertSeverity.CRITICAL:
            logger.critical(f"ALERT: {message}")
        elif severity == AlertSeverity.ERROR:
            logger.error(f"ALERT: {message}")
        elif severity == AlertSeverity.WARNING:
            logger.warning(f"ALERT: {message}")
        else:
            logger.info(f"ALERT: {message}")
        
        # Store alert in Redis
        await self.redis.lpush('alerts', json.dumps(alert))
        await self.redis.ltrim('alerts', 0, 999)  # Keep last 1000 alerts
        
        # Set cooldown
        threshold = self.thresholds[metric_name]
        await self.redis.setex(cooldown_key, threshold.cooldown_minutes * 60, 1)
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def _update_redis_metrics(self, metrics: Dict[str, Any]):
        """Update metrics in Redis for dashboard consumption"""
        for key, value in metrics.items():
            await self.redis.setex(
                f"realtime:{key}",
                300,  # 5 minute TTL
                json.dumps(value)
            )
    
    async def _get_response_times(self) -> List[float]:
        """Get recent API response times"""
        # This would integrate with your API monitoring
        # For now, return mock data
        return []
    
    async def _get_error_rate(self) -> float:
        """Get current error rate"""
        # This would integrate with your error tracking
        # For now, return mock data
        return 0.0
    
    async def _get_database_metrics(self) -> Dict[str, float]:
        """Get database performance metrics"""
        query = """
        SELECT 
            COUNT(*) as connections,
            AVG(query_duration_ms) as avg_query_time
        FROM pg_stat_statements
        WHERE query_start > NOW() - INTERVAL '5 minutes';
        """
        
        try:
            result = await self.db.fetch_one(query)
            return {
                'connections': result['connections'] or 0,
                'avg_query_time': float(result['avg_query_time'] or 0)
            }
        except:
            return {'connections': 0, 'avg_query_time': 0}
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current snapshot of all metrics"""
        metrics = {}
        
        for name, buffer in self.metrics_buffer.items():
            if buffer:
                latest = buffer[-1]
                metrics[name] = {
                    'value': latest['value'],
                    'type': latest['type'],
                    'timestamp': latest['timestamp'].isoformat()
                }
        
        return metrics
    
    async def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get historical data for a metric"""
        if metric_name not in self.metrics_buffer:
            return []
        
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            {
                'value': m['value'],
                'timestamp': m['timestamp'].isoformat()
            }
            for m in self.metrics_buffer[metric_name]
            if m['timestamp'] > cutoff
        ]