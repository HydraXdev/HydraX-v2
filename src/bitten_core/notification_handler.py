"""
Notification Handler for BITTEN
Manages notifications with sound support
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .user_settings import should_play_sound

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications"""
    SIGNAL = "signal"
    TRADE_OPEN = "trade_open"
    TRADE_CLOSE = "trade_close"
    TP_HIT = "tp_hit"
    SL_HIT = "sl_hit"
    ACHIEVEMENT = "achievement"
    XP_GAIN = "xp_gain"
    WARNING = "warning"
    SYSTEM = "system"


@dataclass
class Notification:
    """Notification data structure"""
    user_id: str
    type: NotificationType
    title: str
    message: str
    timestamp: datetime
    data: Dict[str, Any]
    sound_type: Optional[str] = None
    priority: int = 5  # 1-10, higher = more important
    icon: Optional[str] = None


class NotificationHandler:
    """Handles notifications and sound triggers"""
    
    # Sound mappings
    NOTIFICATION_SOUNDS = {
        NotificationType.TP_HIT: "cash_register",
        NotificationType.ACHIEVEMENT: "achievement",
        NotificationType.XP_GAIN: "xp_gain",
        NotificationType.WARNING: "warning",
        NotificationType.SL_HIT: "loss",
        NotificationType.SIGNAL: "signal_alert"
    }
    
    # Icon mappings
    NOTIFICATION_ICONS = {
        NotificationType.TP_HIT: "🎯",
        NotificationType.SL_HIT: "❌",
        NotificationType.ACHIEVEMENT: "🏆",
        NotificationType.XP_GAIN: "⭐",
        NotificationType.WARNING: "⚠️",
        NotificationType.SIGNAL: "📡",
        NotificationType.TRADE_OPEN: "🔫",
        NotificationType.TRADE_CLOSE: "✅"
    }
    
    def __init__(self):
        self.notification_queue: List[Notification] = []
        self.handlers = {}
    
    def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        custom_sound: Optional[str] = None,
        priority: Optional[int] = None
    ) -> Notification:
        """Send a notification to user"""
        # Determine sound
        sound_type = custom_sound or self.NOTIFICATION_SOUNDS.get(notification_type)
        
        # Check if sound should play
        should_play = False
        if sound_type:
            should_play = should_play_sound(user_id, sound_type)
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            data=data or {},
            sound_type=sound_type if should_play else None,
            priority=priority or 5,
            icon=self.NOTIFICATION_ICONS.get(notification_type)
        )
        
        # Add to queue
        self.notification_queue.append(notification)
        
        # Process handlers
        self._process_handlers(notification)
        
        logger.info(f"Notification sent: {notification_type.value} for user {user_id}")
        
        return notification
    
    def send_tp_hit_notification(
        self,
        user_id: str,
        symbol: str,
        profit_pips: float,
        profit_currency: Optional[float] = None
    ) -> Notification:
        """Send take profit hit notification with cash register sound"""
        title = f"🎯 TAKE PROFIT HIT!"
        message = f"{symbol} closed at +{profit_pips:.1f} pips"
        
        if profit_currency:
            message += f" (${profit_currency:,.2f})"
        
        return self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TP_HIT,
            title=title,
            message=message,
            data={
                "symbol": symbol,
                "profit_pips": profit_pips,
                "profit_currency": profit_currency
            },
            priority=8  # High priority
        )
    
    def send_achievement_notification(
        self,
        user_id: str,
        achievement_name: str,
        xp_reward: int,
        description: Optional[str] = None
    ) -> Notification:
        """Send achievement unlocked notification"""
        title = f"🏆 {achievement_name} Unlocked!"
        message = f"+{xp_reward} XP"
        
        if description:
            message += f" - {description}"
        
        return self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.ACHIEVEMENT,
            title=title,
            message=message,
            data={
                "achievement": achievement_name,
                "xp_reward": xp_reward
            },
            priority=7
        )
    
    def send_xp_gain_notification(
        self,
        user_id: str,
        xp_amount: int,
        reason: str,
        is_combo: bool = False
    ) -> Notification:
        """Send XP gain notification"""
        title = f"{'🔥 COMBO! ' if is_combo else ''}+{xp_amount} XP"
        message = reason
        
        # Only play sound for significant XP gains
        custom_sound = "xp_gain" if xp_amount >= 100 else None
        
        return self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.XP_GAIN,
            title=title,
            message=message,
            data={
                "xp_amount": xp_amount,
                "is_combo": is_combo
            },
            custom_sound=custom_sound,
            priority=5 if xp_amount < 100 else 6
        )
    
    def send_warning_notification(
        self,
        user_id: str,
        warning_type: str,
        message: str,
        severity: str = "medium"  # low, medium, high, critical
    ) -> Notification:
        """Send warning notification"""
        severity_icons = {
            "low": "💡",
            "medium": "⚠️",
            "high": "🚨",
            "critical": "🔴"
        }
        
        title = f"{severity_icons.get(severity, '⚠️')} {warning_type}"
        
        priority_map = {
            "low": 4,
            "medium": 6,
            "high": 8,
            "critical": 10
        }
        
        return self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.WARNING,
            title=title,
            message=message,
            data={
                "warning_type": warning_type,
                "severity": severity
            },
            priority=priority_map.get(severity, 5)
        )
    
    def register_handler(self, handler_name: str, handler_func):
        """Register a notification handler"""
        self.handlers[handler_name] = handler_func
    
    def _process_handlers(self, notification: Notification):
        """Process registered handlers"""
        for handler_name, handler_func in self.handlers.items():
            try:
                handler_func(notification)
            except Exception as e:
                logger.error(f"Error in handler {handler_name}: {e}")
    
    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 10,
        notification_type: Optional[NotificationType] = None
    ) -> List[Notification]:
        """Get recent notifications for user"""
        user_notifications = [
            n for n in self.notification_queue
            if n.user_id == user_id
        ]
        
        if notification_type:
            user_notifications = [
                n for n in user_notifications
                if n.type == notification_type
            ]
        
        # Sort by timestamp descending
        user_notifications.sort(key=lambda n: n.timestamp, reverse=True)
        
        return user_notifications[:limit]
    
    def clear_old_notifications(self, hours: int = 24):
        """Clear notifications older than specified hours"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        self.notification_queue = [
            n for n in self.notification_queue
            if n.timestamp.timestamp() > cutoff
        ]
        
        logger.info(f"Cleared notifications older than {hours} hours")
    
    def format_for_telegram(self, notification: Notification) -> Dict[str, Any]:
        """Format notification for Telegram display"""
        formatted_message = f"{notification.icon} **{notification.title}**\n\n{notification.message}"
        
        return {
            "message": formatted_message,
            "parse_mode": "Markdown",
            "disable_notification": notification.priority < 7,
            "metadata": {
                "type": notification.type.value,
                "sound": notification.sound_type,
                "data": notification.data
            }
        }
    
    def format_for_webapp(self, notification: Notification) -> Dict[str, Any]:
        """Format notification for WebApp display"""
        return {
            "id": f"{notification.user_id}_{notification.timestamp.timestamp()}",
            "type": notification.type.value,
            "title": notification.title,
            "message": notification.message,
            "icon": notification.icon,
            "timestamp": notification.timestamp.isoformat(),
            "priority": notification.priority,
            "sound": notification.sound_type,
            "data": notification.data
        }


# Global instance
notification_handler = NotificationHandler()


# Helper functions
def notify_tp_hit(user_id: str, symbol: str, profit_pips: float, profit_currency: Optional[float] = None):
    """Quick helper to notify TP hit"""
    return notification_handler.send_tp_hit_notification(
        user_id, symbol, profit_pips, profit_currency
    )


def notify_achievement(user_id: str, achievement: str, xp: int, description: Optional[str] = None):
    """Quick helper to notify achievement"""
    return notification_handler.send_achievement_notification(
        user_id, achievement, xp, description
    )


def notify_xp_gain(user_id: str, xp: int, reason: str, combo: bool = False):
    """Quick helper to notify XP gain"""
    return notification_handler.send_xp_gain_notification(
        user_id, xp, reason, combo
    )


# Example usage
if __name__ == "__main__":
    # Simulate TP hit
    notify_tp_hit(
        user_id="test_user",
        symbol="EURUSD",
        profit_pips=25.5,
        profit_currency=127.50
    )
    
    # Simulate achievement
    notify_achievement(
        user_id="test_user",
        achievement="First Blood",
        xp=100,
        description="Your first successful trade!"
    )
    
    # Get user notifications
    notifications = notification_handler.get_user_notifications("test_user")
    for notif in notifications:
        print(f"{notif.icon} {notif.title}: {notif.message}")