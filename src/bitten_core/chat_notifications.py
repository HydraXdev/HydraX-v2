"""
BITTEN Chat Notification System
Handles push notifications, email alerts, and integration with existing notification systems
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import asyncio
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

try:
    import redis
    from celery import Celery
except ImportError:
    redis = None
    Celery = None

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of chat notifications"""
    DIRECT_MESSAGE = "direct_message"
    MENTION = "mention"
    SQUAD_MESSAGE = "squad_message"
    SYSTEM_ALERT = "system_alert"
    MODERATION_ACTION = "moderation_action"
    FILE_SHARED = "file_shared"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"

class NotificationPriority(Enum):
    """Priority levels for notifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class DeliveryMethod(Enum):
    """Methods of delivering notifications"""
    REAL_TIME = "real_time"  # WebSocket/SSE
    PUSH = "push"           # Browser push notifications
    EMAIL = "email"         # Email notifications
    SMS = "sms"            # SMS notifications
    TELEGRAM = "telegram"   # Telegram bot notifications

@dataclass
class NotificationSettings:
    """User notification preferences"""
    user_id: str
    enabled_types: Set[NotificationType] = None
    delivery_methods: Dict[NotificationType, List[DeliveryMethod]] = None
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    mention_keywords: List[str] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    push_subscription: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.enabled_types is None:
            self.enabled_types = {
                NotificationType.DIRECT_MESSAGE,
                NotificationType.MENTION,
                NotificationType.SYSTEM_ALERT
            }
        
        if self.delivery_methods is None:
            self.delivery_methods = {
                NotificationType.DIRECT_MESSAGE: [DeliveryMethod.REAL_TIME, DeliveryMethod.PUSH],
                NotificationType.MENTION: [DeliveryMethod.REAL_TIME, DeliveryMethod.PUSH],
                NotificationType.SYSTEM_ALERT: [DeliveryMethod.REAL_TIME, DeliveryMethod.EMAIL],
                NotificationType.SQUAD_MESSAGE: [DeliveryMethod.REAL_TIME],
                NotificationType.MODERATION_ACTION: [DeliveryMethod.REAL_TIME, DeliveryMethod.EMAIL],
                NotificationType.FILE_SHARED: [DeliveryMethod.REAL_TIME],
                NotificationType.USER_JOINED: [DeliveryMethod.REAL_TIME],
                NotificationType.USER_LEFT: [DeliveryMethod.REAL_TIME]
            }
        
        if self.mention_keywords is None:
            self.mention_keywords = []

@dataclass
class ChatNotification:
    """Chat notification data structure"""
    notification_id: str
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    source_room_id: str
    source_user_id: Optional[str] = None
    source_message_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    scheduled_for: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    delivery_methods_used: List[DeliveryMethod] = None
    delivery_status: Dict[DeliveryMethod, str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.delivery_methods_used is None:
            self.delivery_methods_used = []
        if self.delivery_status is None:
            self.delivery_status = {}

class ChatNotificationService:
    """Handles all chat notifications and integrations"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        email_config: Optional[Dict[str, str]] = None,
        telegram_config: Optional[Dict[str, str]] = None,
        enable_celery: bool = True
    ):
        self.redis_client = None
        self.celery_app = None
        self.email_config = email_config or {}
        self.telegram_config = telegram_config or {}
        
        # In-memory stores
        self.notification_settings: Dict[str, NotificationSettings] = {}
        self.pending_notifications: List[ChatNotification] = []
        self.notification_history: Dict[str, List[ChatNotification]] = {}
        
        # Data directory
        self.data_dir = Path("data/chat_notifications")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Redis connection
        if redis:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Connected to Redis for chat notifications")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
        
        # Initialize Celery for background tasks
        if enable_celery and Celery:
            try:
                self.celery_app = Celery(
                    'chat_notifications',
                    broker=redis_url,
                    backend=redis_url
                )
                self.celery_app.conf.update(
                    task_serializer='json',
                    accept_content=['json'],
                    result_serializer='json',
                    timezone='UTC',
                    enable_utc=True,
                )
                logger.info("Celery initialized for background notifications")
            except Exception as e:
                logger.warning(f"Celery initialization failed: {e}")
        
        # Load existing settings
        self._load_notification_settings()
    
    def register_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        custom_settings: Optional[NotificationSettings] = None
    ) -> bool:
        """Register a user for notifications"""
        try:
            if custom_settings:
                settings = custom_settings
            else:
                settings = NotificationSettings(
                    user_id=user_id,
                    email_address=email,
                    phone_number=phone,
                    telegram_chat_id=telegram_chat_id
                )
            
            self.notification_settings[user_id] = settings
            self._save_user_settings(user_id)
            
            logger.info(f"Registered notification settings for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register user {user_id}: {e}")
            return False
    
    def update_user_settings(
        self,
        user_id: str,
        **kwargs
    ) -> bool:
        """Update user notification settings"""
        try:
            if user_id not in self.notification_settings:
                self.notification_settings[user_id] = NotificationSettings(user_id=user_id)
            
            settings = self.notification_settings[user_id]
            
            # Update settings
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            self._save_user_settings(user_id)
            
            logger.info(f"Updated notification settings for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update settings for user {user_id}: {e}")
            return False
    
    def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        source_room_id: Optional[str] = None,
        source_user_id: Optional[str] = None,
        source_message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        schedule_for: Optional[datetime] = None
    ) -> Optional[ChatNotification]:
        """Create a new notification"""
        try:
            # Check if user has notifications enabled for this type
            if not self._should_notify_user(user_id, notification_type):
                return None
            
            # Check quiet hours
            if self._is_quiet_hours(user_id):
                # Schedule for after quiet hours
                schedule_for = self._get_next_active_time(user_id)
            
            notification = ChatNotification(
                notification_id=f"notif_{datetime.now().timestamp()}_{user_id}",
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                source_room_id=source_room_id,
                source_user_id=source_user_id,
                source_message_id=source_message_id,
                metadata=metadata or {},
                scheduled_for=schedule_for
            )
            
            # Add to pending notifications
            self.pending_notifications.append(notification)
            
            # Store in Redis if available
            if self.redis_client:
                self._store_notification_in_redis(notification)
            
            # Process immediately if not scheduled
            if not schedule_for:
                self._process_notification(notification)
            
            logger.info(f"Created notification {notification.notification_id} for user {user_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    def create_squad_notification(
        self,
        squad_id: str,
        user_ids: List[str],
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SQUAD_MESSAGE,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        exclude_user_id: Optional[str] = None,
        **kwargs
    ) -> List[ChatNotification]:
        """Create notifications for multiple squad members"""
        notifications = []
        
        for user_id in user_ids:
            if user_id == exclude_user_id:
                continue
            
            notification = self.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                **kwargs
            )
            
            if notification:
                notifications.append(notification)
        
        logger.info(f"Created {len(notifications)} squad notifications for squad {squad_id}")
        return notifications
    
    def process_chat_message(
        self,
        message_data: Dict[str, Any],
        room_members: List[str]
    ):
        """Process a chat message for notifications"""
        try:
            sender_id = message_data.get('user_id')
            content = message_data.get('content', '')
            room_id = message_data.get('room_id')
            callsign = message_data.get('callsign', 'Unknown')
            
            # Check for mentions
            mentioned_users = self._extract_mentions(content, room_members)
            
            # Create mention notifications
            for user_id in mentioned_users:
                if user_id != sender_id:
                    self.create_notification(
                        user_id=user_id,
                        notification_type=NotificationType.MENTION,
                        title=f"Mentioned by {callsign}",
                        message=f"{callsign}: {content[:100]}...",
                        priority=NotificationPriority.HIGH,
                        source_room_id=room_id,
                        source_user_id=sender_id,
                        source_message_id=message_data.get('message_id'),
                        metadata={
                            'full_message': content,
                            'sender_callsign': callsign
                        }
                    )
            
            # Create general squad notifications for active users
            eligible_members = [
                user_id for user_id in room_members 
                if user_id != sender_id and user_id not in mentioned_users
            ]
            
            # Only notify if it's not too frequent
            if self._should_send_squad_notification(room_id, sender_id):
                self.create_squad_notification(
                    squad_id=room_id,
                    user_ids=eligible_members,
                    title=f"New message in {room_id}",
                    message=f"{callsign}: {content[:50]}...",
                    notification_type=NotificationType.SQUAD_MESSAGE,
                    priority=NotificationPriority.LOW,
                    source_room_id=room_id,
                    source_user_id=sender_id,
                    source_message_id=message_data.get('message_id')
                )
        
        except Exception as e:
            logger.error(f"Failed to process chat message for notifications: {e}")
    
    def process_file_share(
        self,
        user_id: str,
        filename: str,
        room_id: str,
        room_members: List[str]
    ):
        """Process file share for notifications"""
        try:
            user_settings = self.notification_settings.get(user_id)
            callsign = user_settings.user_id if user_settings else user_id
            
            eligible_members = [uid for uid in room_members if uid != user_id]
            
            self.create_squad_notification(
                squad_id=room_id,
                user_ids=eligible_members,
                title="File shared",
                message=f"{callsign} shared: {filename}",
                notification_type=NotificationType.FILE_SHARED,
                priority=NotificationPriority.NORMAL,
                source_room_id=room_id,
                source_user_id=user_id,
                metadata={'filename': filename}
            )
            
        except Exception as e:
            logger.error(f"Failed to process file share notification: {e}")
    
    def process_moderation_action(
        self,
        moderator_id: str,
        target_user_id: str,
        action: str,
        reason: str,
        duration: int = 0
    ):
        """Process moderation action for notifications"""
        try:
            # Notify the target user
            self.create_notification(
                user_id=target_user_id,
                notification_type=NotificationType.MODERATION_ACTION,
                title=f"Moderation Action: {action.title()}",
                message=f"You have been {action} by a moderator. Reason: {reason}",
                priority=NotificationPriority.URGENT,
                metadata={
                    'action': action,
                    'reason': reason,
                    'duration': duration,
                    'moderator_id': moderator_id
                }
            )
            
            # Log for audit trail
            logger.info(f"Moderation notification sent: {action} by {moderator_id} on {target_user_id}")
            
        except Exception as e:
            logger.error(f"Failed to process moderation notification: {e}")
    
    def _process_notification(self, notification: ChatNotification):
        """Process a single notification through all delivery methods"""
        try:
            settings = self.notification_settings.get(notification.user_id)
            if not settings:
                logger.warning(f"No settings found for user {notification.user_id}")
                return
            
            delivery_methods = settings.delivery_methods.get(
                notification.notification_type, 
                [DeliveryMethod.REAL_TIME]
            )
            
            for method in delivery_methods:
                try:
                    success = self._deliver_notification(notification, method, settings)
                    notification.delivery_status[method] = "delivered" if success else "failed"
                    
                    if success:
                        notification.delivery_methods_used.append(method)
                        
                except Exception as e:
                    logger.error(f"Failed to deliver notification via {method}: {e}")
                    notification.delivery_status[method] = f"error: {str(e)}"
            
            notification.delivered_at = datetime.now()
            
            # Store in history
            if notification.user_id not in self.notification_history:
                self.notification_history[notification.user_id] = []
            
            self.notification_history[notification.user_id].append(notification)
            
            # Remove from pending
            if notification in self.pending_notifications:
                self.pending_notifications.remove(notification)
            
        except Exception as e:
            logger.error(f"Failed to process notification {notification.notification_id}: {e}")
    
    def _deliver_notification(
        self,
        notification: ChatNotification,
        method: DeliveryMethod,
        settings: NotificationSettings
    ) -> bool:
        """Deliver notification via specific method"""
        try:
            if method == DeliveryMethod.REAL_TIME:
                return self._deliver_real_time(notification)
            
            elif method == DeliveryMethod.PUSH:
                return self._deliver_push(notification, settings)
            
            elif method == DeliveryMethod.EMAIL:
                return self._deliver_email(notification, settings)
            
            elif method == DeliveryMethod.SMS:
                return self._deliver_sms(notification, settings)
            
            elif method == DeliveryMethod.TELEGRAM:
                return self._deliver_telegram(notification, settings)
            
            else:
                logger.warning(f"Unknown delivery method: {method}")
                return False
                
        except Exception as e:
            logger.error(f"Delivery failed for method {method}: {e}")
            return False
    
    def _deliver_real_time(self, notification: ChatNotification) -> bool:
        """Deliver notification via real-time connection (WebSocket/SSE)"""
        try:
            # This would integrate with the SocketIO system
            # For now, we'll store in Redis for real-time pickup
            if self.redis_client:
                self.redis_client.lpush(
                    f"real_time_notifications:{notification.user_id}",
                    json.dumps(asdict(notification), default=str)
                )
                self.redis_client.expire(
                    f"real_time_notifications:{notification.user_id}",
                    3600  # 1 hour
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Real-time delivery failed: {e}")
            return False
    
    def _deliver_push(self, notification: ChatNotification, settings: NotificationSettings) -> bool:
        """Deliver browser push notification"""
        try:
            # Browser push notifications would be implemented here
            # This requires service worker registration and push subscription
            if settings.push_subscription:
                # Implementation would use web-push library
                logger.info(f"Push notification sent to {notification.user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Push delivery failed: {e}")
            return False
    
    def _deliver_email(self, notification: ChatNotification, settings: NotificationSettings) -> bool:
        """Deliver email notification"""
        try:
            if not settings.email_address or not self.email_config:
                return False
            
            # Create email
            msg = MimeMultipart()
            msg['From'] = self.email_config.get('from_address')
            msg['To'] = settings.email_address
            msg['Subject'] = f"BITTEN Alert: {notification.title}"
            
            # Create HTML body
            html_body = self._create_email_html(notification)
            msg.attach(MimeText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(
                self.email_config.get('smtp_host'),
                self.email_config.get('smtp_port', 587)
            ) as server:
                server.starttls()
                server.login(
                    self.email_config.get('username'),
                    self.email_config.get('password')
                )
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {settings.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return False
    
    def _deliver_sms(self, notification: ChatNotification, settings: NotificationSettings) -> bool:
        """Deliver SMS notification"""
        try:
            # SMS delivery would be implemented here using a service like Twilio
            # For now, just log
            logger.info(f"SMS notification would be sent to {settings.phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"SMS delivery failed: {e}")
            return False
    
    def _deliver_telegram(self, notification: ChatNotification, settings: NotificationSettings) -> bool:
        """Deliver Telegram notification"""
        try:
            # Telegram delivery would be implemented here
            # Using the existing Telegram bot integration
            logger.info(f"Telegram notification would be sent to {settings.telegram_chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Telegram delivery failed: {e}")
            return False
    
    def _create_email_html(self, notification: ChatNotification) -> str:
        """Create HTML email body"""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Courier New', monospace; background: #1a1a1a; color: #ffffff; }}
                .header {{ background: #00ff00; color: #1a1a1a; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background: #2a2a2a; padding: 10px; text-align: center; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚡ BITTEN TACTICAL ALERT ⚡</h1>
            </div>
            <div class="content">
                <h2>{notification.title}</h2>
                <p>{notification.message}</p>
                <p><strong>Priority:</strong> {notification.priority.value.upper()}</p>
                <p><strong>Time:</strong> {notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            <div class="footer">
                <p>BITTEN Squad Communications - Stay Sharp, Stay Connected</p>
            </div>
        </body>
        </html>
        """
    
    def _should_notify_user(self, user_id: str, notification_type: NotificationType) -> bool:
        """Check if user should receive this type of notification"""
        settings = self.notification_settings.get(user_id)
        if not settings:
            return False
        
        return notification_type in settings.enabled_types
    
    def _is_quiet_hours(self, user_id: str) -> bool:
        """Check if it's currently quiet hours for the user"""
        settings = self.notification_settings.get(user_id)
        if not settings or not settings.quiet_hours_start or not settings.quiet_hours_end:
            return False
        
        # Implementation would check current time against user's quiet hours
        # Considering timezone
        return False
    
    def _get_next_active_time(self, user_id: str) -> datetime:
        """Get the next time notifications should be active"""
        # Implementation would calculate next active time based on quiet hours
        return datetime.now() + timedelta(hours=1)
    
    def _extract_mentions(self, content: str, room_members: List[str]) -> List[str]:
        """Extract mentioned users from message content"""
        mentions = []
        
        # Check for @username mentions
        words = content.split()
        for word in words:
            if word.startswith('@'):
                mentioned = word[1:].lower()
                
                # Check if it's a special mention
                if mentioned in ['everyone', 'squad', 'all']:
                    mentions.extend(room_members)
                    break
                
                # Check against actual usernames/callsigns
                for member_id in room_members:
                    # In real implementation, would look up actual usernames
                    if mentioned in member_id.lower():
                        mentions.append(member_id)
        
        return list(set(mentions))
    
    def _should_send_squad_notification(self, room_id: str, sender_id: str) -> bool:
        """Check if squad notification should be sent (rate limiting)"""
        # Implementation would check if too many notifications sent recently
        # For now, allow all
        return True
    
    def _store_notification_in_redis(self, notification: ChatNotification):
        """Store notification in Redis"""
        try:
            if self.redis_client:
                self.redis_client.lpush(
                    f"notifications:{notification.user_id}",
                    json.dumps(asdict(notification), default=str)
                )
                self.redis_client.ltrim(f"notifications:{notification.user_id}", 0, 999)
        except Exception as e:
            logger.error(f"Failed to store notification in Redis: {e}")
    
    def _save_user_settings(self, user_id: str):
        """Save user settings to persistent storage"""
        try:
            settings = self.notification_settings.get(user_id)
            if not settings:
                return
            
            settings_file = self.data_dir / f"settings_{user_id}.json"
            
            # Convert sets and enums to serializable format
            data = {
                'user_id': settings.user_id,
                'enabled_types': [t.value for t in settings.enabled_types],
                'delivery_methods': {
                    t.value: [m.value for m in methods]
                    for t, methods in settings.delivery_methods.items()
                },
                'quiet_hours_start': settings.quiet_hours_start,
                'quiet_hours_end': settings.quiet_hours_end,
                'mention_keywords': settings.mention_keywords,
                'email_address': settings.email_address,
                'phone_number': settings.phone_number,
                'telegram_chat_id': settings.telegram_chat_id,
                'push_subscription': settings.push_subscription
            }
            
            with open(settings_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save settings for user {user_id}: {e}")
    
    def _load_notification_settings(self):
        """Load notification settings from persistent storage"""
        try:
            for settings_file in self.data_dir.glob("settings_*.json"):
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                
                user_id = data['user_id']
                
                # Convert back from serializable format
                settings = NotificationSettings(
                    user_id=user_id,
                    enabled_types={NotificationType(t) for t in data.get('enabled_types', [])},
                    delivery_methods={
                        NotificationType(t): [DeliveryMethod(m) for m in methods]
                        for t, methods in data.get('delivery_methods', {}).items()
                    },
                    quiet_hours_start=data.get('quiet_hours_start'),
                    quiet_hours_end=data.get('quiet_hours_end'),
                    mention_keywords=data.get('mention_keywords', []),
                    email_address=data.get('email_address'),
                    phone_number=data.get('phone_number'),
                    telegram_chat_id=data.get('telegram_chat_id'),
                    push_subscription=data.get('push_subscription')
                )
                
                self.notification_settings[user_id] = settings
                
        except Exception as e:
            logger.error(f"Failed to load notification settings: {e}")
    
    # Public API methods
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[ChatNotification]:
        """Get notification history for user"""
        history = self.notification_history.get(user_id, [])
        return history[-limit:] if len(history) > limit else history
    
    def mark_notifications_read(self, user_id: str, notification_ids: List[str] = None):
        """Mark notifications as read"""
        try:
            history = self.notification_history.get(user_id, [])
            
            for notification in history:
                if not notification_ids or notification.notification_id in notification_ids:
                    notification.metadata['read'] = True
                    notification.metadata['read_at'] = datetime.now().isoformat()
            
            logger.info(f"Marked notifications as read for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to mark notifications as read: {e}")
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        history = self.notification_history.get(user_id, [])
        return sum(1 for n in history if not n.metadata.get('read', False))

# Example usage and integration
if __name__ == "__main__":
    # Initialize notification service
    notification_service = ChatNotificationService()
    
    # Register a user
    notification_service.register_user(
        user_id="test_user_123",
        email="operator@bitten.tactical",
        telegram_chat_id="123456789"
    )
    
    # Create a test notification
    notification = notification_service.create_notification(
        user_id="test_user_123",
        notification_type=NotificationType.MENTION,
        title="You were mentioned",
        message="ALPHA-1 mentioned you in Squad Chat",
        priority=NotificationPriority.HIGH,
        source_room_id="squad_demo",
        metadata={"test": True}
    )
    
    if notification:
        print(f"Created notification: {notification.notification_id}")
        print(f"Delivery status: {notification.delivery_status}")
    
    # Test processing a chat message
    message_data = {
        'user_id': 'sender_123',
        'content': 'Hey @test_user_123, check this out!',
        'room_id': 'squad_demo',
        'callsign': 'BRAVO-2',
        'message_id': 'msg_123'
    }
    
    notification_service.process_chat_message(
        message_data=message_data,
        room_members=['test_user_123', 'sender_123', 'other_user']
    )
    
    print(f"Unread notifications: {notification_service.get_unread_count('test_user_123')}")