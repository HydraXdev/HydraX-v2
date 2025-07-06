"""
BITTEN Emergency Notification System
Comprehensive alert system for emergency stop events
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from .emergency_stop_controller import EmergencyStopEvent, EmergencyStopTrigger, EmergencyStopLevel

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Available notification channels"""
    TELEGRAM = "telegram"
    WEBAPP = "webapp"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SYSTEM_LOG = "system_log"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class NotificationTemplate:
    """Template for emergency notifications"""
    title: str
    message: str
    channels: List[NotificationChannel]
    priority: NotificationPriority
    sound_enabled: bool = True
    vibration_pattern: Optional[List[int]] = None
    auto_dismiss_seconds: Optional[int] = None

class EmergencyNotificationSystem:
    """
    Handles all emergency stop notifications across multiple channels
    """
    
    def __init__(self):
        self.notification_templates = self._load_notification_templates()
        self.active_notifications: List[Dict] = []
        self.notification_history: List[Dict] = []
        
        # Channel handlers (to be injected)
        self.telegram_handler = None
        self.webapp_handler = None
        self.email_handler = None
        self.sms_handler = None
        self.webhook_handler = None
        
        # Configuration
        self.config = {
            'max_active_notifications': 10,
            'max_history_size': 1000,
            'default_auto_dismiss': 300,  # 5 minutes
            'escalation_enabled': True,
            'escalation_delay_minutes': 5
        }
    
    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates for different emergency scenarios"""
        return {
            'manual_emergency_stop': NotificationTemplate(
                title="🛑 Emergency Stop Activated",
                message="Manual emergency stop has been activated by user {user_id}. All trading suspended.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.HIGH,
                sound_enabled=True,
                auto_dismiss_seconds=300
            ),
            'panic_stop': NotificationTemplate(
                title="🚨 PANIC MODE ACTIVATED",
                message="PANIC protocol engaged! All positions being closed immediately. Manual recovery required.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.EMAIL, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.EMERGENCY,
                sound_enabled=True,
                vibration_pattern=[200, 100, 200, 100, 200],
                auto_dismiss_seconds=None  # Manual dismiss only
            ),
            'drawdown_emergency': NotificationTemplate(
                title="📉 Drawdown Emergency Stop",
                message="Emergency stop triggered due to excessive drawdown ({drawdown}%). Trading suspended for safety.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.CRITICAL,
                sound_enabled=True,
                auto_dismiss_seconds=600
            ),
            'news_emergency': NotificationTemplate(
                title="📰 News Event Emergency Stop",
                message="Trading suspended due to high-impact news event: {event_name}. Auto-recovery in {duration} minutes.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.MEDIUM,
                sound_enabled=False,
                auto_dismiss_seconds=1800  # 30 minutes
            ),
            'system_error_emergency': NotificationTemplate(
                title="⚠️ System Error Emergency Stop",
                message="Emergency stop triggered by system error: {error_details}. Technical review required.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.EMAIL, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.CRITICAL,
                sound_enabled=True,
                auto_dismiss_seconds=900
            ),
            'admin_override_emergency': NotificationTemplate(
                title="🚨 Admin Override Emergency Stop",
                message="System-wide emergency halt activated by administrator {admin_id}. All users affected.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.EMAIL, NotificationChannel.WEBHOOK, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.EMERGENCY,
                sound_enabled=True,
                auto_dismiss_seconds=None
            ),
            'market_volatility_emergency': NotificationTemplate(
                title="📊 Market Volatility Emergency Stop",
                message="Extreme market volatility detected ({volatility}%). Trading suspended for safety.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.HIGH,
                sound_enabled=True,
                auto_dismiss_seconds=900
            ),
            'broker_connection_emergency': NotificationTemplate(
                title="🔌 Broker Connection Emergency Stop",
                message="Lost connection to broker. Trading suspended until connection restored.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.HIGH,
                sound_enabled=True,
                auto_dismiss_seconds=600
            ),
            'emergency_recovery': NotificationTemplate(
                title="✅ Emergency Recovery Completed",
                message="Emergency stop has been resolved. Trading systems restored and operational.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.MEDIUM,
                sound_enabled=True,
                auto_dismiss_seconds=180
            ),
            'recovery_failed': NotificationTemplate(
                title="❌ Emergency Recovery Failed",
                message="Attempted recovery from emergency stop failed: {error_reason}. Manual intervention required.",
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBAPP, NotificationChannel.EMAIL, NotificationChannel.SYSTEM_LOG],
                priority=NotificationPriority.CRITICAL,
                sound_enabled=True,
                auto_dismiss_seconds=None
            )
        }
    
    def inject_handlers(self, **handlers):
        """Inject notification channel handlers"""
        for name, handler in handlers.items():
            if hasattr(self, f"{name}_handler"):
                setattr(self, f"{name}_handler", handler)
    
    def send_emergency_notification(
        self,
        event: EmergencyStopEvent,
        affected_users: List[int] = None,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send emergency notification based on event type
        
        Args:
            event: Emergency stop event
            affected_users: List of user IDs to notify
            additional_data: Additional context for notification
            
        Returns:
            Dict with notification results
        """
        try:
            # Determine template based on trigger
            template_key = self._get_template_key(event.trigger)
            template = self.notification_templates.get(template_key)
            
            if not template:
                logger.error(f"No template found for trigger: {event.trigger}")
                return {'success': False, 'error': 'No template found'}
            
            # Prepare notification data
            notification_data = {
                'id': f"emergency_{event.timestamp.isoformat()}_{event.trigger.value}",
                'timestamp': datetime.now(),
                'event': event,
                'template': template,
                'affected_users': affected_users or [],
                'additional_data': additional_data or {},
                'status': 'sending',
                'delivery_results': {}
            }
            
            # Format message with event data
            formatted_message = self._format_message(template.message, event, additional_data)
            
            # Send to each channel
            delivery_results = {}
            for channel in template.channels:
                try:
                    result = self._send_to_channel(
                        channel, 
                        template.title, 
                        formatted_message, 
                        template, 
                        notification_data
                    )
                    delivery_results[channel.value] = result
                except Exception as e:
                    logger.error(f"Failed to send to {channel.value}: {e}")
                    delivery_results[channel.value] = {'success': False, 'error': str(e)}
            
            notification_data['delivery_results'] = delivery_results
            notification_data['status'] = 'sent'
            
            # Store notification
            self.active_notifications.append(notification_data)
            self._cleanup_notifications()
            
            # Log to history
            self.notification_history.append({
                'id': notification_data['id'],
                'timestamp': notification_data['timestamp'],
                'trigger': event.trigger.value,
                'level': event.level.value,
                'channels': [c.value for c in template.channels],
                'delivery_success': sum(1 for r in delivery_results.values() if r.get('success', False)),
                'delivery_total': len(delivery_results)
            })
            
            self._cleanup_history()
            
            logger.info(f"Emergency notification sent: {notification_data['id']}")
            
            return {
                'success': True,
                'notification_id': notification_data['id'],
                'delivery_results': delivery_results,
                'channels_sent': len(delivery_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to send emergency notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_recovery_notification(
        self,
        recovery_data: Dict[str, Any],
        affected_users: List[int] = None
    ) -> Dict[str, Any]:
        """Send notification when emergency is recovered"""
        try:
            template = self.notification_templates['emergency_recovery']
            
            notification_data = {
                'id': f"recovery_{datetime.now().isoformat()}",
                'timestamp': datetime.now(),
                'type': 'recovery',
                'template': template,
                'affected_users': affected_users or [],
                'recovery_data': recovery_data,
                'status': 'sending',
                'delivery_results': {}
            }
            
            # Format recovery message
            formatted_message = template.message.format(
                recovery_time=recovery_data.get('recovery_time', 'now'),
                user_id=recovery_data.get('user_id', 'system')
            )
            
            # Send to channels
            delivery_results = {}
            for channel in template.channels:
                try:
                    result = self._send_to_channel(
                        channel, 
                        template.title, 
                        formatted_message, 
                        template, 
                        notification_data
                    )
                    delivery_results[channel.value] = result
                except Exception as e:
                    delivery_results[channel.value] = {'success': False, 'error': str(e)}
            
            notification_data['delivery_results'] = delivery_results
            notification_data['status'] = 'sent'
            
            self.active_notifications.append(notification_data)
            self._cleanup_notifications()
            
            return {
                'success': True,
                'notification_id': notification_data['id'],
                'delivery_results': delivery_results
            }
            
        except Exception as e:
            logger.error(f"Failed to send recovery notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_template_key(self, trigger: EmergencyStopTrigger) -> str:
        """Map trigger to template key"""
        template_map = {
            EmergencyStopTrigger.MANUAL: 'manual_emergency_stop',
            EmergencyStopTrigger.PANIC: 'panic_stop',
            EmergencyStopTrigger.DRAWDOWN: 'drawdown_emergency',
            EmergencyStopTrigger.NEWS: 'news_emergency',
            EmergencyStopTrigger.SYSTEM_ERROR: 'system_error_emergency',
            EmergencyStopTrigger.MARKET_VOLATILITY: 'market_volatility_emergency',
            EmergencyStopTrigger.BROKER_CONNECTION: 'broker_connection_emergency',
            EmergencyStopTrigger.ADMIN_OVERRIDE: 'admin_override_emergency',
            EmergencyStopTrigger.SCHEDULED_MAINTENANCE: 'manual_emergency_stop'
        }
        return template_map.get(trigger, 'manual_emergency_stop')
    
    def _format_message(self, message: str, event: EmergencyStopEvent, additional_data: Dict[str, Any]) -> str:
        """Format message template with safe substitution"""
        try:
            # Sanitize format data to prevent injection
            format_data = {
                'user_id': self._sanitize_string(str(event.user_id)) if event.user_id else 'system',
                'trigger': self._sanitize_string(event.trigger.value),
                'level': self._sanitize_string(event.level.value),
                'reason': self._sanitize_string(event.reason),
                'timestamp': event.timestamp.strftime('%H:%M:%S UTC')
            }
            
            # Only allow whitelisted additional data keys
            if additional_data:
                allowed_keys = ['drawdown', 'event_name', 'duration', 'volatility', 'admin_id', 'error_details']
                for key in allowed_keys:
                    if key in additional_data:
                        format_data[key] = self._sanitize_string(str(additional_data[key]))
            
            # Use safe string formatting with error handling
            try:
                return message.format(**format_data)
            except KeyError as e:
                logger.warning(f"Missing format key {e} in message template")
                # Return message with placeholder for missing keys
                return message.replace(f"{{{e}}}", f"[{e}]")
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return "Emergency notification (formatting error)"
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string values for safe display"""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove potentially dangerous characters
        import re
        value = re.sub(r'[<>"\'{}\[\]\\]', '', value)
        
        # Limit length to prevent oversized messages
        return value[:200]
    
    def _send_to_channel(
        self,
        channel: NotificationChannel,
        title: str,
        message: str,
        template: NotificationTemplate,
        notification_data: Dict
    ) -> Dict[str, Any]:
        """Send notification to specific channel"""
        
        if channel == NotificationChannel.TELEGRAM:
            return self._send_telegram_notification(title, message, template, notification_data)
        elif channel == NotificationChannel.WEBAPP:
            return self._send_webapp_notification(title, message, template, notification_data)
        elif channel == NotificationChannel.EMAIL:
            return self._send_email_notification(title, message, template, notification_data)
        elif channel == NotificationChannel.SMS:
            return self._send_sms_notification(title, message, template, notification_data)
        elif channel == NotificationChannel.WEBHOOK:
            return self._send_webhook_notification(title, message, template, notification_data)
        elif channel == NotificationChannel.SYSTEM_LOG:
            return self._send_system_log_notification(title, message, template, notification_data)
        else:
            return {'success': False, 'error': 'Unknown channel'}
    
    def _send_telegram_notification(self, title: str, message: str, template: NotificationTemplate, notification_data: Dict) -> Dict[str, Any]:
        """Send Telegram notification"""
        if not self.telegram_handler:
            return {'success': False, 'error': 'Telegram handler not available'}
        
        try:
            # Format for Telegram
            telegram_message = f"🚨 **{title}**\n\n{message}"
            
            # Add inline keyboard for emergency actions
            keyboard_data = {
                'reply_markup': {
                    'inline_keyboard': [
                        [
                            {'text': '🚨 STATUS', 'callback_data': 'emergency_status'},
                            {'text': '🔄 RECOVER', 'callback_data': 'recover_emergency'}
                        ]
                    ]
                }
            }
            
            # Send to affected users
            affected_users = notification_data.get('affected_users', [])
            results = []
            
            for user_id in affected_users:
                try:
                    result = self.telegram_handler.send_message(
                        user_id, 
                        telegram_message, 
                        **keyboard_data
                    )
                    results.append({'user_id': user_id, 'success': True, 'result': result})
                except Exception as e:
                    results.append({'user_id': user_id, 'success': False, 'error': str(e)})
            
            successful_sends = sum(1 for r in results if r['success'])
            
            return {
                'success': successful_sends > 0,
                'sent_count': successful_sends,
                'total_count': len(affected_users),
                'results': results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_webapp_notification(self, title: str, message: str, template: NotificationTemplate, notification_data: Dict) -> Dict[str, Any]:
        """Send WebApp notification"""
        if not self.webapp_handler:
            return {'success': False, 'error': 'WebApp handler not available'}
        
        try:
            notification_payload = {
                'id': notification_data['id'],
                'title': title,
                'message': message,
                'priority': template.priority.value,
                'timestamp': notification_data['timestamp'].isoformat(),
                'sound_enabled': template.sound_enabled,
                'vibration_pattern': template.vibration_pattern,
                'auto_dismiss_seconds': template.auto_dismiss_seconds,
                'type': 'emergency_stop'
            }
            
            # Send to WebApp handler
            result = self.webapp_handler.broadcast_notification(notification_payload)
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_email_notification(self, title: str, message: str, template: NotificationTemplate, notification_data: Dict) -> Dict[str, Any]:
        """Send email notification"""
        if not self.email_handler:
            return {'success': False, 'error': 'Email handler not available'}
        
        # Placeholder for email implementation
        return {'success': False, 'error': 'Email not implemented'}
    
    def _send_sms_notification(self, title: str, message: str, template: NotificationTemplate, notification_data: Dict) -> Dict[str, Any]:
        """Send SMS notification"""
        if not self.sms_handler:
            return {'success': False, 'error': 'SMS handler not available'}
        
        # Placeholder for SMS implementation
        return {'success': False, 'error': 'SMS not implemented'}
    
    def _send_webhook_notification(self, title: str, message: str, template: NotificationTemplate, notification_data: Dict) -> Dict[str, Any]:
        """Send webhook notification"""
        if not self.webhook_handler:
            return {'success': False, 'error': 'Webhook handler not available'}
        
        try:
            webhook_payload = {
                'event_type': 'emergency_stop',
                'title': title,
                'message': message,
                'priority': template.priority.value,
                'timestamp': notification_data['timestamp'].isoformat(),
                'event_data': {
                    'trigger': notification_data['event'].trigger.value,
                    'level': notification_data['event'].level.value,
                    'user_id': notification_data['event'].user_id,
                    'reason': notification_data['event'].reason
                }
            }
            
            result = self.webhook_handler.send_webhook(webhook_payload)
            return {'success': True, 'result': result}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_system_log_notification(self, title: str, message: str, template: NotificationTemplate, notification_data: Dict) -> Dict[str, Any]:
        """Send system log notification"""
        try:
            log_level = logging.CRITICAL if template.priority == NotificationPriority.EMERGENCY else logging.ERROR
            logger.log(log_level, f"EMERGENCY NOTIFICATION: {title} - {message}")
            
            return {'success': True, 'logged': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _cleanup_notifications(self):
        """Clean up old active notifications"""
        max_active = self.config['max_active_notifications']
        if len(self.active_notifications) > max_active:
            # Remove oldest notifications
            self.active_notifications = self.active_notifications[-max_active:]
    
    def _cleanup_history(self):
        """Clean up old notification history"""
        max_history = self.config['max_history_size']
        if len(self.notification_history) > max_history:
            # Remove oldest history entries
            self.notification_history = self.notification_history[-max_history:]
    
    def get_active_notifications(self) -> List[Dict]:
        """Get list of active notifications"""
        return self.active_notifications.copy()
    
    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """Get notification history"""
        return self.notification_history[-limit:] if limit else self.notification_history.copy()
    
    def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss an active notification"""
        try:
            self.active_notifications = [
                n for n in self.active_notifications 
                if n['id'] != notification_id
            ]
            return True
        except Exception as e:
            logger.error(f"Failed to dismiss notification {notification_id}: {e}")
            return False
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        return {
            'active_notifications': len(self.active_notifications),
            'total_history': len(self.notification_history),
            'available_channels': len([h for h in [
                self.telegram_handler, self.webapp_handler, self.email_handler,
                self.sms_handler, self.webhook_handler
            ] if h is not None]),
            'templates_loaded': len(self.notification_templates),
            'config': self.config
        }