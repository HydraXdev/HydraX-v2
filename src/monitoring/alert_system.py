#!/usr/bin/env python3
"""
BITTEN Alert System
Comprehensive alerting system for monitoring critical issues and thresholds
with multiple notification channels (email, Slack, webhook, SMS).
"""

import asyncio
import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from collections import defaultdict, deque
import statistics

from .logging_config import setup_service_logging
from .health_check import HealthStatus

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

@dataclass
class Alert:
    """Alert definition"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    service: str
    metric: str
    threshold: float
    current_value: float
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    tags: Optional[Dict[str, str]] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    description: str
    service: str
    metric: str
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    severity: AlertSeverity
    duration_seconds: int  # How long condition must persist
    cooldown_seconds: int  # Minimum time between alerts
    tags: Optional[Dict[str, str]] = None
    enabled: bool = True

class AlertNotifier:
    """Base class for alert notifiers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_service_logging("alert-notifier")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert notification - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send resolution notification - to be implemented by subclasses"""
        raise NotImplementedError

class EmailNotifier(AlertNotifier):
    """Email alert notifier"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        try:
            smtp_server = self.config.get('smtp_server', 'localhost')
            smtp_port = self.config.get('smtp_port', 587)
            smtp_username = self.config.get('smtp_username')
            smtp_password = self.config.get('smtp_password')
            from_email = self.config.get('from_email')
            to_emails = self.config.get('to_emails', [])
            
            if not to_emails:
                self.logger.warning("No email recipients configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] BITTEN Alert: {alert.title}"
            
            # Email body
            body = f"""
BITTEN System Alert

Alert ID: {alert.id}
Service: {alert.service}
Severity: {alert.severity.value.upper()}
Timestamp: {alert.timestamp.isoformat()}

Title: {alert.title}
Description: {alert.description}

Metric: {alert.metric}
Threshold: {alert.threshold}
Current Value: {alert.current_value}

Details:
{json.dumps(alert.details, indent=2) if alert.details else 'None'}

Tags:
{json.dumps(alert.tags, indent=2) if alert.tags else 'None'}

Status: {alert.status.value}

--
BITTEN Trading System
Automated Alert System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            if smtp_username and smtp_password:
                server.starttls()
                server.login(smtp_username, smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send email resolution notification"""
        try:
            smtp_server = self.config.get('smtp_server', 'localhost')
            smtp_port = self.config.get('smtp_port', 587)
            smtp_username = self.config.get('smtp_username')
            smtp_password = self.config.get('smtp_password')
            from_email = self.config.get('from_email')
            to_emails = self.config.get('to_emails', [])
            
            if not to_emails:
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[RESOLVED] BITTEN Alert: {alert.title}"
            
            # Email body
            body = f"""
BITTEN System Alert - RESOLVED

Alert ID: {alert.id}
Service: {alert.service}
Severity: {alert.severity.value.upper()}
Resolved: {datetime.now().isoformat()}

Title: {alert.title}
Description: {alert.description}

The alert condition has been resolved.

--
BITTEN Trading System
Automated Alert System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            if smtp_username and smtp_password:
                server.starttls()
                server.login(smtp_username, smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email resolution sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email resolution: {e}")
            return False

class SlackNotifier(AlertNotifier):
    """Slack alert notifier"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                self.logger.warning("No Slack webhook URL configured")
                return False
            
            # Color based on severity
            color_map = {
                AlertSeverity.LOW: '#36a64f',      # Green
                AlertSeverity.MEDIUM: '#ffaa00',   # Orange
                AlertSeverity.HIGH: '#ff6600',     # Red-orange
                AlertSeverity.CRITICAL: '#ff0000'  # Red
            }
            
            # Create Slack message
            message = {
                "text": f"BITTEN Alert: {alert.title}",
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, '#36a64f'),
                        "fields": [
                            {
                                "title": "Service",
                                "value": alert.service,
                                "short": True
                            },
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Metric",
                                "value": alert.metric,
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert.current_value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert.threshold),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": True
                            }
                        ],
                        "text": alert.description,
                        "footer": "BITTEN Alert System",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Slack alert sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send Slack resolution notification"""
        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                return False
            
            # Create Slack message
            message = {
                "text": f"✅ RESOLVED: {alert.title}",
                "attachments": [
                    {
                        "color": "#36a64f",  # Green
                        "fields": [
                            {
                                "title": "Service",
                                "value": alert.service,
                                "short": True
                            },
                            {
                                "title": "Resolved",
                                "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": True
                            }
                        ],
                        "text": f"Alert {alert.id} has been resolved.",
                        "footer": "BITTEN Alert System"
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Slack resolution sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack resolution: {e}")
            return False

class WebhookNotifier(AlertNotifier):
    """Generic webhook alert notifier"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send webhook alert"""
        try:
            url = self.config.get('url')
            if not url:
                self.logger.warning("No webhook URL configured")
                return False
            
            headers = self.config.get('headers', {'Content-Type': 'application/json'})
            auth = self.config.get('auth')
            
            # Create payload
            payload = {
                'alert_id': alert.id,
                'title': alert.title,
                'description': alert.description,
                'severity': alert.severity.value,
                'service': alert.service,
                'metric': alert.metric,
                'threshold': alert.threshold,
                'current_value': alert.current_value,
                'timestamp': alert.timestamp.isoformat(),
                'status': alert.status.value,
                'tags': alert.tags,
                'details': alert.details
            }
            
            # Send webhook
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=auth if auth else None,
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info(f"Webhook alert sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send webhook resolution notification"""
        try:
            url = self.config.get('url')
            if not url:
                return False
            
            headers = self.config.get('headers', {'Content-Type': 'application/json'})
            auth = self.config.get('auth')
            
            # Create payload
            payload = {
                'alert_id': alert.id,
                'title': alert.title,
                'service': alert.service,
                'status': 'resolved',
                'resolved_at': datetime.now().isoformat()
            }
            
            # Send webhook
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=auth if auth else None,
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info(f"Webhook resolution sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook resolution: {e}")
            return False

class TelegramNotifier(AlertNotifier):
    """Telegram alert notifier"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send Telegram alert"""
        try:
            bot_token = self.config.get('bot_token')
            chat_id = self.config.get('chat_id')
            
            if not bot_token or not chat_id:
                self.logger.warning("Telegram bot token or chat ID not configured")
                return False
            
            # Format message
            severity_emoji = {
                AlertSeverity.LOW: '🟢',
                AlertSeverity.MEDIUM: '🟡',
                AlertSeverity.HIGH: '🟠',
                AlertSeverity.CRITICAL: '🔴'
            }
            
            message = f"""
{severity_emoji.get(alert.severity, '⚠️')} *BITTEN Alert*

*Service:* {alert.service}
*Severity:* {alert.severity.value.upper()}
*Metric:* {alert.metric}
*Current Value:* {alert.current_value}
*Threshold:* {alert.threshold}
*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

*Description:*
{alert.description}

*Alert ID:* `{alert.id}`
"""
            
            # Send message
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Telegram alert sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send Telegram resolution notification"""
        try:
            bot_token = self.config.get('bot_token')
            chat_id = self.config.get('chat_id')
            
            if not bot_token or not chat_id:
                return False
            
            message = f"""
✅ *RESOLVED*

*Service:* {alert.service}
*Alert:* {alert.title}
*Resolved:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

*Alert ID:* `{alert.id}`
"""
            
            # Send message
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Telegram resolution sent for {alert.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram resolution: {e}")
            return False

class AlertDatabase:
    """SQLite database for alerts"""
    
    def __init__(self, db_path: str = "/var/log/bitten/alerts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    severity TEXT,
                    service TEXT,
                    metric TEXT,
                    threshold REAL,
                    current_value REAL,
                    timestamp TEXT,
                    status TEXT,
                    tags TEXT,
                    details TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    service TEXT,
                    metric TEXT,
                    condition TEXT,
                    threshold REAL,
                    severity TEXT,
                    duration_seconds INTEGER,
                    cooldown_seconds INTEGER,
                    tags TEXT,
                    enabled BOOLEAN,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alert_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT,
                    notifier_type TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    timestamp TEXT
                )
            ''')
    
    def store_alert(self, alert: Alert):
        """Store alert in database"""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            conn.execute('''
                INSERT OR REPLACE INTO alerts (
                    id, title, description, severity, service, metric,
                    threshold, current_value, timestamp, status, tags,
                    details, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id,
                alert.title,
                alert.description,
                alert.severity.value,
                alert.service,
                alert.metric,
                alert.threshold,
                alert.current_value,
                alert.timestamp.isoformat(),
                alert.status.value,
                json.dumps(alert.tags) if alert.tags else None,
                json.dumps(alert.details) if alert.details else None,
                now,
                now
            ))
    
    def update_alert_status(self, alert_id: str, status: AlertStatus):
        """Update alert status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE alerts 
                SET status = ?, updated_at = ?
                WHERE id = ?
            ''', (status.value, datetime.now().isoformat(), alert_id))
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM alerts 
                WHERE status = 'active'
                ORDER BY timestamp DESC
            ''')
            
            alerts = []
            for row in cursor.fetchall():
                alert = Alert(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    severity=AlertSeverity(row['severity']),
                    service=row['service'],
                    metric=row['metric'],
                    threshold=row['threshold'],
                    current_value=row['current_value'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    status=AlertStatus(row['status']),
                    tags=json.loads(row['tags']) if row['tags'] else None,
                    details=json.loads(row['details']) if row['details'] else None
                )
                alerts.append(alert)
            
            return alerts
    
    def store_alert_rule(self, rule: AlertRule):
        """Store alert rule in database"""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            conn.execute('''
                INSERT OR REPLACE INTO alert_rules (
                    id, name, description, service, metric, condition,
                    threshold, severity, duration_seconds, cooldown_seconds,
                    tags, enabled, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.id,
                rule.name,
                rule.description,
                rule.service,
                rule.metric,
                rule.condition,
                rule.threshold,
                rule.severity.value,
                rule.duration_seconds,
                rule.cooldown_seconds,
                json.dumps(rule.tags) if rule.tags else None,
                rule.enabled,
                now,
                now
            ))
    
    def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM alert_rules 
                WHERE enabled = 1
                ORDER BY name
            ''')
            
            rules = []
            for row in cursor.fetchall():
                rule = AlertRule(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    service=row['service'],
                    metric=row['metric'],
                    condition=row['condition'],
                    threshold=row['threshold'],
                    severity=AlertSeverity(row['severity']),
                    duration_seconds=row['duration_seconds'],
                    cooldown_seconds=row['cooldown_seconds'],
                    tags=json.loads(row['tags']) if row['tags'] else None,
                    enabled=bool(row['enabled'])
                )
                rules.append(rule)
            
            return rules
    
    def log_notification(self, alert_id: str, notifier_type: str, success: bool, error_message: str = None):
        """Log notification attempt"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO alert_notifications (
                    alert_id, notifier_type, success, error_message, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                alert_id,
                notifier_type,
                success,
                error_message,
                datetime.now().isoformat()
            ))

class AlertManager:
    """Main alert management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_service_logging("alert-manager")
        self.db = AlertDatabase(config.get('db_path', '/var/log/bitten/alerts.db'))
        
        # Initialize notifiers
        self.notifiers: Dict[str, AlertNotifier] = {}
        self._initialize_notifiers()
        
        # Alert state tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.last_alert_time: Dict[str, datetime] = {}
        
        # Load existing rules
        self._load_alert_rules()
        
        # Background tasks
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _initialize_notifiers(self):
        """Initialize notification channels"""
        notifier_configs = self.config.get('notifiers', {})
        
        if 'email' in notifier_configs:
            self.notifiers['email'] = EmailNotifier(notifier_configs['email'])
        
        if 'slack' in notifier_configs:
            self.notifiers['slack'] = SlackNotifier(notifier_configs['slack'])
        
        if 'webhook' in notifier_configs:
            self.notifiers['webhook'] = WebhookNotifier(notifier_configs['webhook'])
        
        if 'telegram' in notifier_configs:
            self.notifiers['telegram'] = TelegramNotifier(notifier_configs['telegram'])
    
    def _load_alert_rules(self):
        """Load alert rules from database"""
        rules = self.db.get_alert_rules()
        for rule in rules:
            self.alert_rules[rule.id] = rule
        
        self.logger.info(f"Loaded {len(rules)} alert rules")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add new alert rule"""
        self.alert_rules[rule.id] = rule
        self.db.store_alert_rule(rule)
        self.logger.info(f"Added alert rule: {rule.name}")
    
    def check_metric(self, service: str, metric: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Check metric against alert rules"""
        # Store metric history
        metric_key = f"{service}:{metric}"
        self.metric_history[metric_key].append((datetime.now(), value))
        
        # Check all rules for this metric
        for rule in self.alert_rules.values():
            if rule.service == service and rule.metric == metric:
                self._evaluate_rule(rule, value, tags)
    
    def _evaluate_rule(self, rule: AlertRule, current_value: float, tags: Optional[Dict[str, str]] = None):
        """Evaluate alert rule against current value"""
        # Check condition
        condition_met = False
        if rule.condition == '>':
            condition_met = current_value > rule.threshold
        elif rule.condition == '<':
            condition_met = current_value < rule.threshold
        elif rule.condition == '>=':
            condition_met = current_value >= rule.threshold
        elif rule.condition == '<=':
            condition_met = current_value <= rule.threshold
        elif rule.condition == '==':
            condition_met = current_value == rule.threshold
        elif rule.condition == '!=':
            condition_met = current_value != rule.threshold
        
        alert_id = f"{rule.service}:{rule.metric}:{rule.id}"
        
        if condition_met:
            # Check if we need to wait for duration
            if rule.duration_seconds > 0:
                # Check if condition has been met for required duration
                metric_key = f"{rule.service}:{rule.metric}"
                history = self.metric_history.get(metric_key, deque())
                
                if len(history) < 2:
                    return
                
                # Check if condition has been consistently met
                duration_start = datetime.now() - timedelta(seconds=rule.duration_seconds)
                consistent = True
                
                for timestamp, value in history:
                    if timestamp >= duration_start:
                        if not self._check_condition(rule.condition, value, rule.threshold):
                            consistent = False
                            break
                
                if not consistent:
                    return
            
            # Check cooldown
            if alert_id in self.last_alert_time:
                time_since_last = datetime.now() - self.last_alert_time[alert_id]
                if time_since_last.total_seconds() < rule.cooldown_seconds:
                    return
            
            # Create alert
            alert = Alert(
                id=alert_id,
                title=f"{rule.name} - {rule.service}",
                description=f"{rule.description}. Current value: {current_value}, Threshold: {rule.threshold}",
                severity=rule.severity,
                service=rule.service,
                metric=rule.metric,
                threshold=rule.threshold,
                current_value=current_value,
                timestamp=datetime.now(),
                tags=tags
            )
            
            self._trigger_alert(alert)
            
        else:
            # Check if we need to resolve an existing alert
            if alert_id in self.active_alerts:
                self._resolve_alert(alert_id)
    
    def _check_condition(self, condition: str, value: float, threshold: float) -> bool:
        """Check if condition is met"""
        if condition == '>':
            return value > threshold
        elif condition == '<':
            return value < threshold
        elif condition == '>=':
            return value >= threshold
        elif condition == '<=':
            return value <= threshold
        elif condition == '==':
            return value == threshold
        elif condition == '!=':
            return value != threshold
        return False
    
    def _trigger_alert(self, alert: Alert):
        """Trigger a new alert"""
        # Store alert
        self.active_alerts[alert.id] = alert
        self.db.store_alert(alert)
        self.last_alert_time[alert.id] = alert.timestamp
        
        # Log alert
        self.logger.error(
            f"Alert triggered: {alert.title} - {alert.description}",
            extra={
                'alert_id': alert.id,
                'service': alert.service,
                'metric': alert.metric,
                'severity': alert.severity.value,
                'current_value': alert.current_value,
                'threshold': alert.threshold
            }
        )
        
        # Send notifications
        self._send_notifications(alert)
    
    def _resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        
        # Update database
        self.db.update_alert_status(alert_id, AlertStatus.RESOLVED)
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Log resolution
        self.logger.info(
            f"Alert resolved: {alert.title}",
            extra={
                'alert_id': alert_id,
                'service': alert.service,
                'metric': alert.metric
            }
        )
        
        # Send resolution notifications
        self._send_resolution_notifications(alert)
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications"""
        for notifier_type, notifier in self.notifiers.items():
            self.executor.submit(self._send_notification, notifier_type, notifier, alert)
    
    def _send_resolution_notifications(self, alert: Alert):
        """Send resolution notifications"""
        for notifier_type, notifier in self.notifiers.items():
            self.executor.submit(self._send_resolution_notification, notifier_type, notifier, alert)
    
    def _send_notification(self, notifier_type: str, notifier: AlertNotifier, alert: Alert):
        """Send notification via specific notifier"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(notifier.send_alert(alert))
            loop.close()
            
            # Log notification attempt
            self.db.log_notification(
                alert.id,
                notifier_type,
                success,
                None if success else "Unknown error"
            )
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to send {notifier_type} notification: {error_msg}")
            
            # Log failed notification
            self.db.log_notification(
                alert.id,
                notifier_type,
                False,
                error_msg
            )
    
    def _send_resolution_notification(self, notifier_type: str, notifier: AlertNotifier, alert: Alert):
        """Send resolution notification via specific notifier"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(notifier.send_resolution(alert))
            loop.close()
            
            # Log notification attempt
            self.db.log_notification(
                alert.id,
                f"{notifier_type}_resolution",
                success,
                None if success else "Unknown error"
            )
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to send {notifier_type} resolution: {error_msg}")
            
            # Log failed notification
            self.db.log_notification(
                alert.id,
                f"{notifier_type}_resolution",
                False,
                error_msg
            )
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            self.db.update_alert_status(alert_id, AlertStatus.ACKNOWLEDGED)
            
            self.logger.info(f"Alert acknowledged: {alert_id}")
    
    def suppress_alert(self, alert_id: str):
        """Suppress an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.SUPPRESSED
            self.db.update_alert_status(alert_id, AlertStatus.SUPPRESSED)
            
            self.logger.info(f"Alert suppressed: {alert_id}")
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        active_alerts = self.get_active_alerts()
        
        severity_counts = defaultdict(int)
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'total_active': len(active_alerts),
            'by_severity': dict(severity_counts),
            'alert_rules': len(self.alert_rules),
            'notifiers': list(self.notifiers.keys()),
            'timestamp': datetime.now().isoformat()
        }

def create_default_alert_rules() -> List[AlertRule]:
    """Create default alert rules for BITTEN system"""
    rules = [
        # Signal generation rules
        AlertRule(
            id="signals_below_target",
            name="Signal Generation Below Target",
            description="Daily signal generation is below 65 signals target",
            service="signal-generator",
            metric="signals_today",
            condition="<",
            threshold=52,  # 80% of target
            severity=AlertSeverity.MEDIUM,
            duration_seconds=3600,  # 1 hour
            cooldown_seconds=7200   # 2 hours
        ),
        
        AlertRule(
            id="signals_severely_below_target",
            name="Signal Generation Severely Below Target",
            description="Daily signal generation is severely below target",
            service="signal-generator",
            metric="signals_today",
            condition="<",
            threshold=39,  # 60% of target
            severity=AlertSeverity.HIGH,
            duration_seconds=1800,  # 30 minutes
            cooldown_seconds=3600   # 1 hour
        ),
        
        # Win rate rules
        AlertRule(
            id="win_rate_below_target",
            name="Win Rate Below Target",
            description="Win rate is below 85% target",
            service="trade-executor",
            metric="win_rate",
            condition="<",
            threshold=80.0,  # 5% below target
            severity=AlertSeverity.MEDIUM,
            duration_seconds=3600,  # 1 hour
            cooldown_seconds=7200   # 2 hours
        ),
        
        AlertRule(
            id="win_rate_severely_below_target",
            name="Win Rate Severely Below Target",
            description="Win rate is severely below target",
            service="trade-executor",
            metric="win_rate",
            condition="<",
            threshold=70.0,
            severity=AlertSeverity.HIGH,
            duration_seconds=1800,  # 30 minutes
            cooldown_seconds=3600   # 1 hour
        ),
        
        # System health rules
        AlertRule(
            id="high_cpu_usage",
            name="High CPU Usage",
            description="CPU usage is above 80%",
            service="system",
            metric="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.MEDIUM,
            duration_seconds=300,   # 5 minutes
            cooldown_seconds=1800   # 30 minutes
        ),
        
        AlertRule(
            id="high_memory_usage",
            name="High Memory Usage",
            description="Memory usage is above 85%",
            service="system",
            metric="memory_usage",
            condition=">",
            threshold=85.0,
            severity=AlertSeverity.MEDIUM,
            duration_seconds=300,   # 5 minutes
            cooldown_seconds=1800   # 30 minutes
        ),
        
        AlertRule(
            id="service_down",
            name="Service Down",
            description="Service health check failed",
            service="health-monitor",
            metric="service_status",
            condition="==",
            threshold=0,  # 0 = down, 1 = up
            severity=AlertSeverity.CRITICAL,
            duration_seconds=60,    # 1 minute
            cooldown_seconds=300    # 5 minutes
        ),
        
        # Error rate rules
        AlertRule(
            id="high_error_rate",
            name="High Error Rate",
            description="Error rate is above 5%",
            service="bitten-core",
            metric="error_rate",
            condition=">",
            threshold=5.0,
            severity=AlertSeverity.HIGH,
            duration_seconds=300,   # 5 minutes
            cooldown_seconds=1800   # 30 minutes
        ),
        
        # Response time rules
        AlertRule(
            id="slow_response_time",
            name="Slow Response Time",
            description="Average response time is above 1000ms",
            service="bitten-core",
            metric="response_time_ms",
            condition=">",
            threshold=1000.0,
            severity=AlertSeverity.MEDIUM,
            duration_seconds=300,   # 5 minutes
            cooldown_seconds=1800   # 30 minutes
        ),
        
        # MT5 farm rules
        AlertRule(
            id="mt5_farm_down",
            name="MT5 Farm Down",
            description="MT5 farm is not responding",
            service="mt5-farm",
            metric="status",
            condition="==",
            threshold=0,  # 0 = down, 1 = up
            severity=AlertSeverity.CRITICAL,
            duration_seconds=60,    # 1 minute
            cooldown_seconds=300    # 5 minutes
        ),
        
        AlertRule(
            id="mt5_low_accounts",
            name="MT5 Low Active Accounts",
            description="MT5 farm has less than 3 active accounts",
            service="mt5-farm",
            metric="active_accounts",
            condition="<",
            threshold=3,
            severity=AlertSeverity.HIGH,
            duration_seconds=600,   # 10 minutes
            cooldown_seconds=1800   # 30 minutes
        )
    ]
    
    return rules

def get_default_alert_config() -> Dict[str, Any]:
    """Get default alert configuration"""
    return {
        'db_path': '/var/log/bitten/alerts.db',
        'notifiers': {
            'email': {
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'smtp_username': '',
                'smtp_password': '',
                'from_email': 'alerts@bitten.local',
                'to_emails': ['admin@bitten.local']
            },
            'slack': {
                'webhook_url': ''  # Set via environment
            },
            'telegram': {
                'bot_token': '',   # Set via environment
                'chat_id': ''      # Set via environment
            }
        }
    }

# Global alert manager instance
_alert_manager = None

def get_alert_manager(config: Optional[Dict[str, Any]] = None) -> AlertManager:
    """Get global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(config or get_default_alert_config())
        
        # Add default rules
        for rule in create_default_alert_rules():
            _alert_manager.add_alert_rule(rule)
    
    return _alert_manager

# Example usage
if __name__ == "__main__":
    # Create alert manager
    alert_manager = get_alert_manager()
    
    # Test alert
    alert_manager.check_metric(
        service="signal-generator",
        metric="signals_today",
        value=45,  # Below target
        tags={'environment': 'production'}
    )
    
    # Get alert summary
    summary = alert_manager.get_alert_summary()
    print(json.dumps(summary, indent=2, default=str))