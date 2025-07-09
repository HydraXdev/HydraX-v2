"""
Anomaly Detection System for Press Pass Metrics

Detects anomalies in conversion metrics and triggers alerts
for unusual patterns or potential issues.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats
from collections import deque
import json

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Detects anomalies in Press Pass metrics using statistical methods"""
    
    def __init__(self, sensitivity: float = 2.5):
        """
        Initialize anomaly detector
        
        Args:
            sensitivity: Z-score threshold for anomaly detection (default 2.5)
        """
        self.sensitivity = sensitivity
        self.metric_history = {}
        self.anomaly_history = deque(maxlen=1000)
        self.models = {}
        
    def add_observation(self, metric_name: str, value: float, timestamp: datetime):
        """Add a new observation for a metric"""
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = deque(maxlen=168)  # 7 days of hourly data
        
        self.metric_history[metric_name].append({
            'value': value,
            'timestamp': timestamp
        })
        
        # Check for anomalies if we have enough history
        if len(self.metric_history[metric_name]) >= 24:  # At least 1 day of data
            anomaly = self._detect_anomaly(metric_name, value, timestamp)
            if anomaly:
                self.anomaly_history.append(anomaly)
                return anomaly
        
        return None
    
    def _detect_anomaly(self, metric_name: str, current_value: float, 
                       timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Detect if current value is anomalous"""
        
        history = list(self.metric_history[metric_name])
        values = [h['value'] for h in history[:-1]]  # Exclude current value
        
        # Multiple detection methods
        z_score_anomaly = self._z_score_detection(values, current_value)
        iqr_anomaly = self._iqr_detection(values, current_value)
        trend_anomaly = self._trend_detection(metric_name, values, current_value)
        seasonal_anomaly = self._seasonal_detection(metric_name, history, current_value, timestamp)
        
        # Combine detection methods
        anomaly_score = sum([
            z_score_anomaly[1] if z_score_anomaly[0] else 0,
            iqr_anomaly[1] if iqr_anomaly[0] else 0,
            trend_anomaly[1] if trend_anomaly[0] else 0,
            seasonal_anomaly[1] if seasonal_anomaly[0] else 0
        ]) / 4
        
        if anomaly_score > 0.5:  # Threshold for combined anomaly
            return {
                'metric': metric_name,
                'value': current_value,
                'timestamp': timestamp,
                'anomaly_score': anomaly_score,
                'expected_range': self._get_expected_range(values),
                'detection_methods': {
                    'z_score': z_score_anomaly,
                    'iqr': iqr_anomaly,
                    'trend': trend_anomaly,
                    'seasonal': seasonal_anomaly
                },
                'severity': self._calculate_severity(anomaly_score, metric_name, current_value),
                'recommendation': self._get_recommendation(metric_name, current_value, values)
            }
        
        return None
    
    def _z_score_detection(self, values: List[float], current_value: float) -> Tuple[bool, float]:
        """Detect anomalies using Z-score method"""
        if len(values) < 3:
            return False, 0.0
        
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return False, 0.0
        
        z_score = abs((current_value - mean) / std)
        is_anomaly = z_score > self.sensitivity
        confidence = min(z_score / self.sensitivity, 1.0) if is_anomaly else 0.0
        
        return is_anomaly, confidence
    
    def _iqr_detection(self, values: List[float], current_value: float) -> Tuple[bool, float]:
        """Detect anomalies using Interquartile Range method"""
        if len(values) < 4:
            return False, 0.0
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        if iqr == 0:
            return False, 0.0
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        is_anomaly = current_value < lower_bound or current_value > upper_bound
        
        if is_anomaly:
            if current_value < lower_bound:
                distance = lower_bound - current_value
            else:
                distance = current_value - upper_bound
            confidence = min(distance / iqr, 1.0)
        else:
            confidence = 0.0
        
        return is_anomaly, confidence
    
    def _trend_detection(self, metric_name: str, values: List[float], 
                        current_value: float) -> Tuple[bool, float]:
        """Detect anomalies in trend"""
        if len(values) < 12:  # Need at least 12 points for trend
            return False, 0.0
        
        # Calculate trend using linear regression
        x = np.arange(len(values))
        slope, intercept, r_value, _, _ = stats.linregress(x, values)
        
        # Expected value based on trend
        expected = slope * len(values) + intercept
        
        # Calculate residuals
        residuals = [values[i] - (slope * i + intercept) for i in range(len(values))]
        residual_std = np.std(residuals)
        
        if residual_std == 0:
            return False, 0.0
        
        # Current residual
        current_residual = current_value - expected
        z_score = abs(current_residual / residual_std)
        
        is_anomaly = z_score > self.sensitivity
        confidence = min(z_score / self.sensitivity, 1.0) if is_anomaly else 0.0
        
        return is_anomaly, confidence
    
    def _seasonal_detection(self, metric_name: str, history: List[Dict], 
                           current_value: float, timestamp: datetime) -> Tuple[bool, float]:
        """Detect seasonal anomalies"""
        if len(history) < 168:  # Need at least 1 week of hourly data
            return False, 0.0
        
        # Get same hour from previous days
        current_hour = timestamp.hour
        current_day = timestamp.weekday()
        
        same_hour_values = []
        for h in history[:-1]:  # Exclude current
            h_timestamp = h['timestamp']
            if h_timestamp.hour == current_hour:
                # Weight recent days more heavily
                days_ago = (timestamp - h_timestamp).days
                if days_ago < 7:
                    same_hour_values.append(h['value'])
        
        if len(same_hour_values) < 3:
            return False, 0.0
        
        # Check if current value is anomalous for this time period
        mean = np.mean(same_hour_values)
        std = np.std(same_hour_values)
        
        if std == 0:
            return False, 0.0
        
        z_score = abs((current_value - mean) / std)
        is_anomaly = z_score > self.sensitivity
        confidence = min(z_score / self.sensitivity, 1.0) if is_anomaly else 0.0
        
        return is_anomaly, confidence
    
    def _get_expected_range(self, values: List[float]) -> Dict[str, float]:
        """Calculate expected range for a metric"""
        if not values:
            return {'min': 0, 'max': 0, 'mean': 0}
        
        return {
            'min': np.percentile(values, 5),
            'max': np.percentile(values, 95),
            'mean': np.mean(values),
            'std': np.std(values)
        }
    
    def _calculate_severity(self, anomaly_score: float, metric_name: str, 
                           current_value: float) -> str:
        """Calculate severity of anomaly"""
        # Metric-specific severity rules
        critical_metrics = ['press_pass_conversions', 'activation_rate', 'error_rate']
        
        if metric_name in critical_metrics:
            if anomaly_score > 0.8:
                return 'critical'
            elif anomaly_score > 0.6:
                return 'high'
            else:
                return 'medium'
        else:
            if anomaly_score > 0.9:
                return 'high'
            elif anomaly_score > 0.7:
                return 'medium'
            else:
                return 'low'
    
    def _get_recommendation(self, metric_name: str, current_value: float, 
                           historical_values: List[float]) -> str:
        """Get recommendation based on anomaly"""
        mean = np.mean(historical_values) if historical_values else 0
        
        recommendations = {
            'press_pass_conversions': {
                'low': "Conversion rate anomaly detected. Check: 1) Landing page loading issues, 2) A/B test changes, 3) External traffic quality",
                'high': "Unusual spike in conversions. Verify: 1) Tracking accuracy, 2) Bot traffic, 3) Campaign effectiveness"
            },
            'activation_rate': {
                'low': "Low activation rate detected. Review: 1) Onboarding flow, 2) Demo account provisioning, 3) User communication",
                'high': "High activation rate spike. Check: 1) Quality of new users, 2) Onboarding changes impact"
            },
            'churn_rate': {
                'low': "Unusual retention improvement. Verify data accuracy and identify successful factors",
                'high': "Churn spike detected. Investigate: 1) Recent product changes, 2) Competitor actions, 3) User feedback"
            },
            'error_rate': {
                'low': "Error rate improvement detected. Document successful fixes",
                'high': "Error rate spike. Check: 1) System health, 2) Recent deployments, 3) External dependencies"
            },
            'response_time': {
                'low': "Performance improvement detected. Ensure it's sustainable",
                'high': "Performance degradation. Check: 1) Server load, 2) Database queries, 3) External API latency"
            }
        }
        
        direction = 'low' if current_value < mean else 'high'
        
        if metric_name in recommendations:
            return recommendations[metric_name].get(direction, f"Investigate {direction} {metric_name} anomaly")
        else:
            return f"Anomaly detected in {metric_name}. Current: {current_value:.2f}, Expected: {mean:.2f}"
    
    def get_recent_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get anomalies from the last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self.anomaly_history if a['timestamp'] > cutoff]
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get summary of recent anomalies"""
        recent = self.get_recent_anomalies(24)
        
        if not recent:
            return {
                'total_anomalies': 0,
                'by_metric': {},
                'by_severity': {},
                'trending_issues': []
            }
        
        # Group by metric
        by_metric = {}
        for anomaly in recent:
            metric = anomaly['metric']
            if metric not in by_metric:
                by_metric[metric] = []
            by_metric[metric].append(anomaly)
        
        # Group by severity
        by_severity = {
            'critical': len([a for a in recent if a['severity'] == 'critical']),
            'high': len([a for a in recent if a['severity'] == 'high']),
            'medium': len([a for a in recent if a['severity'] == 'medium']),
            'low': len([a for a in recent if a['severity'] == 'low'])
        }
        
        # Identify trending issues (multiple anomalies in same metric)
        trending = []
        for metric, anomalies in by_metric.items():
            if len(anomalies) >= 3:
                trending.append({
                    'metric': metric,
                    'count': len(anomalies),
                    'latest': anomalies[-1],
                    'trend': 'worsening' if anomalies[-1]['anomaly_score'] > anomalies[0]['anomaly_score'] else 'improving'
                })
        
        return {
            'total_anomalies': len(recent),
            'by_metric': {k: len(v) for k, v in by_metric.items()},
            'by_severity': by_severity,
            'trending_issues': sorted(trending, key=lambda x: x['count'], reverse=True)
        }

class AlertManager:
    """Manages alerts from anomaly detection"""
    
    def __init__(self, anomaly_detector: AnomalyDetector):
        self.detector = anomaly_detector
        self.alert_handlers = []
        self.alert_history = deque(maxlen=1000)
        self.suppression_rules = {}
        
    def add_handler(self, handler):
        """Add an alert handler"""
        self.alert_handlers.append(handler)
    
    def add_suppression_rule(self, metric: str, min_interval_minutes: int):
        """Add rule to suppress repeated alerts"""
        self.suppression_rules[metric] = min_interval_minutes
    
    async def check_and_alert(self, metric_name: str, value: float, timestamp: datetime):
        """Check for anomalies and send alerts"""
        anomaly = self.detector.add_observation(metric_name, value, timestamp)
        
        if anomaly and self._should_alert(anomaly):
            alert = self._create_alert(anomaly)
            self.alert_history.append(alert)
            
            # Send to all handlers
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"Error in alert handler: {e}")
            
            return alert
        
        return None
    
    def _should_alert(self, anomaly: Dict[str, Any]) -> bool:
        """Check if we should send an alert for this anomaly"""
        metric = anomaly['metric']
        
        # Check suppression rules
        if metric in self.suppression_rules:
            min_interval = self.suppression_rules[metric]
            
            # Find last alert for this metric
            for alert in reversed(self.alert_history):
                if alert['anomaly']['metric'] == metric:
                    time_since_last = (anomaly['timestamp'] - alert['timestamp']).total_seconds() / 60
                    if time_since_last < min_interval:
                        return False
                    break
        
        # Only alert for medium severity and above
        return anomaly['severity'] in ['medium', 'high', 'critical']
    
    def _create_alert(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert from anomaly"""
        return {
            'alert_id': f"{anomaly['metric']}_{int(anomaly['timestamp'].timestamp())}",
            'timestamp': anomaly['timestamp'],
            'severity': anomaly['severity'],
            'title': self._get_alert_title(anomaly),
            'message': self._get_alert_message(anomaly),
            'anomaly': anomaly,
            'actions': self._get_suggested_actions(anomaly)
        }
    
    def _get_alert_title(self, anomaly: Dict[str, Any]) -> str:
        """Generate alert title"""
        metric_names = {
            'press_pass_conversions': 'Press Pass Conversion Rate',
            'activation_rate': 'User Activation Rate',
            'churn_rate': 'User Churn Rate',
            'error_rate': 'System Error Rate',
            'response_time': 'API Response Time'
        }
        
        metric_display = metric_names.get(anomaly['metric'], anomaly['metric'])
        
        if anomaly['value'] < anomaly['expected_range']['mean']:
            direction = "Abnormally Low"
        else:
            direction = "Abnormally High"
        
        return f"{anomaly['severity'].upper()}: {direction} {metric_display}"
    
    def _get_alert_message(self, anomaly: Dict[str, Any]) -> str:
        """Generate detailed alert message"""
        expected = anomaly['expected_range']
        
        message = f"The {anomaly['metric']} is currently {anomaly['value']:.2f}, "
        message += f"which is outside the expected range of {expected['min']:.2f} - {expected['max']:.2f}. "
        message += f"Normal value is around {expected['mean']:.2f}.\n\n"
        message += f"Anomaly Score: {anomaly['anomaly_score']:.2f}\n"
        message += f"Recommendation: {anomaly['recommendation']}"
        
        return message
    
    def _get_suggested_actions(self, anomaly: Dict[str, Any]) -> List[str]:
        """Get suggested actions for the alert"""
        actions = []
        
        if anomaly['severity'] == 'critical':
            actions.append("Immediate investigation required")
            actions.append("Check system status and recent deployments")
            actions.append("Review error logs for the past hour")
        
        if anomaly['metric'] == 'press_pass_conversions' and anomaly['value'] < anomaly['expected_range']['mean']:
            actions.extend([
                "Check landing page performance metrics",
                "Verify tracking pixels are firing correctly",
                "Review recent A/B test changes",
                "Check for increased competition or market changes"
            ])
        
        elif anomaly['metric'] == 'activation_rate' and anomaly['value'] < anomaly['expected_range']['mean']:
            actions.extend([
                "Review onboarding funnel for drop-offs",
                "Check demo account provisioning logs",
                "Verify MT5 connection status",
                "Consider sending re-engagement emails"
            ])
        
        elif anomaly['metric'] == 'error_rate' and anomaly['value'] > anomaly['expected_range']['mean']:
            actions.extend([
                "Check application error logs",
                "Review recent code deployments",
                "Verify external service dependencies",
                "Consider rolling back recent changes"
            ])
        
        return actions

# Example alert handlers
async def log_alert_handler(alert: Dict[str, Any]):
    """Log alerts"""
    if alert['severity'] == 'critical':
        logger.critical(f"CRITICAL ALERT: {alert['title']} - {alert['message']}")
    elif alert['severity'] == 'high':
        logger.error(f"HIGH ALERT: {alert['title']} - {alert['message']}")
    else:
        logger.warning(f"ALERT: {alert['title']} - {alert['message']}")

async def webhook_alert_handler(alert: Dict[str, Any], webhook_url: str):
    """Send alerts to webhook"""
    import aiohttp
    
    payload = {
        'text': f"🚨 *{alert['title']}*",
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': alert['message']
                }
            },
            {
                'type': 'section',
                'fields': [
                    {
                        'type': 'mrkdwn',
                        'text': f"*Severity:* {alert['severity']}"
                    },
                    {
                        'type': 'mrkdwn',
                        'text': f"*Metric:* {alert['anomaly']['metric']}"
                    },
                    {
                        'type': 'mrkdwn',
                        'text': f"*Current Value:* {alert['anomaly']['value']:.2f}"
                    },
                    {
                        'type': 'mrkdwn',
                        'text': f"*Anomaly Score:* {alert['anomaly']['anomaly_score']:.2f}"
                    }
                ]
            }
        ]
    }
    
    if alert['actions']:
        payload['blocks'].append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*Suggested Actions:*\n' + '\n'.join(f"• {action}" for action in alert['actions'])
            }
        })
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)