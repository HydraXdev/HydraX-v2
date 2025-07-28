"""
BITTEN Social Brag Notification System
Sends military-themed squad notifications when soldiers unlock tactical strategies
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

# Import existing systems
try:
    from .referral_system import ReferralSystem
    REFERRAL_SYSTEM_AVAILABLE = True
except ImportError:
    REFERRAL_SYSTEM_AVAILABLE = False

try:
    from .notification_handler import NotificationHandler, NotificationType
    NOTIFICATION_HANDLER_AVAILABLE = True
except ImportError:
    NOTIFICATION_HANDLER_AVAILABLE = False

try:
    from .chat_notifications import ChatNotificationService, NotificationType as ChatNotificationType, NotificationPriority
    CHAT_NOTIFICATIONS_AVAILABLE = True
except ImportError:
    CHAT_NOTIFICATIONS_AVAILABLE = False

logger = logging.getLogger(__name__)

class BragType(Enum):
    """Types of brag-worthy achievements"""
    TACTICAL_STRATEGY_UNLOCK = "tactical_strategy_unlock"
    RANK_PROMOTION = "rank_promotion"
    PRESTIGE_ACHIEVEMENT = "prestige_achievement"
    MILESTONE_REACHED = "milestone_reached"

@dataclass
class BragNotification:
    """Structure for brag notifications"""
    user_id: str
    username: str
    achievement_type: BragType
    achievement_name: str
    achievement_description: str
    brag_message: str
    drill_sergeant_message: str
    squad_members: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]

class SocialBragSystem:
    """Military-themed social brag notification system for squad achievements"""
    
    # Military drill sergeant style messages for tactical strategy unlocks
    TACTICAL_STRATEGY_MESSAGES = {
        "FIRST_BLOOD": {
            "brag_message": "🎯 {username} just unlocked FIRST BLOOD! This soldier is ready for combat!",
            "drill_sergeant": "LISTEN UP, MAGGOTS! {username} just earned their FIRST BLOOD strategy! They're learning to strike fast and strike hard. The enemy won't know what hit 'em! HOORAH!",
            "celebration_emoji": "⚔️"
        },
        "DOUBLE_TAP": {
            "brag_message": "🎯 {username} just unlocked DOUBLE TAP! Precision firepower at its finest!",
            "drill_sergeant": "OUTSTANDING, {username}! You've mastered the DOUBLE TAP technique! Two shots, two kills - that's how we roll in this squad! Show these rookies how it's done!",
            "celebration_emoji": "🔫"
        },
        "TACTICAL_COMMAND": {
            "brag_message": "🎯 {username} just unlocked TACTICAL COMMAND! Another leader emerges from the ranks!",
            "drill_sergeant": "ATTENTION SQUAD! {username} has achieved TACTICAL COMMAND status! This soldier now has the strategic mind of a true battlefield commander! Salute your new tactical leader!",
            "celebration_emoji": "⭐"
        },
        "ADVANCED_MANEUVERS": {
            "brag_message": "🎯 {username} just unlocked ADVANCED MANEUVERS! Elite tactics now at their disposal!",
            "drill_sergeant": "MOVE ASIDE, RECRUITS! {username} has unlocked ADVANCED MANEUVERS! This warrior can now execute combat techniques that would make a Navy SEAL jealous! SEMPER FI!",
            "celebration_emoji": "🚁"
        }
    }
    
    # Messages for rank promotions
    RANK_PROMOTION_MESSAGES = {
        "FANG": {
            "brag_message": "🏆 {username} just achieved FANG rank! Sharp teeth, sharper trades!",
            "drill_sergeant": "DROP AND GIVE ME TWENTY! {username} just made FANG rank! Those trading skills are getting DEADLY! Time to show these NIBBLERS how it's done!",
            "celebration_emoji": "🦷"
        },
        "COMMANDER": {
            "brag_message": "🏆 {username} just achieved COMMANDER rank! Leadership through firepower!",
            "drill_sergeant": "ALL HANDS ON DECK! {username} is now a COMMANDER! This soldier has proven they can lead from the front lines! The market trembles before their tactical prowess!",
            "celebration_emoji": "🎖️"
        },
        "APEX": {
            "brag_message": "🏆 {username} just achieved APEX rank! The pinnacle of trading warfare!",
            "drill_sergeant": "SOUND THE VICTORY HORN! {username} has reached APEX rank! This is the elite of the elite! The market is their battlefield and victory is their only option! ALL HAIL THE APEX PREDATOR!",
            "celebration_emoji": "👑"
        }
    }
    
    # Messages for prestige achievements
    PRESTIGE_MESSAGES = {
        1: {
            "brag_message": "⭐ {username} just achieved PRESTIGE LEVEL 1! Legendary status unlocked!",
            "drill_sergeant": "HOLY SMOKES! {username} just went PRESTIGE! This warrior has reset their XP to prove they're the real deal! That's the kind of dedication that wins wars!",
            "celebration_emoji": "🌟"
        },
        2: {
            "brag_message": "⭐ {username} just achieved PRESTIGE LEVEL 2! Double legendary!",
            "drill_sergeant": "MOTHER OF ALL TRADES! {username} hit PRESTIGE LEVEL 2! This soldier is rewriting the book on tactical excellence! The legends will speak of this day!",
            "celebration_emoji": "✨"
        },
        3: {
            "brag_message": "⭐ {username} just achieved PRESTIGE LEVEL 3! Triple threat activated!",
            "drill_sergeant": "BY THE GHOST OF PATTON! {username} reached PRESTIGE LEVEL 3! This is the stuff of legends! Three times they've proven their worth! ULTIMATE WARRIOR STATUS ACHIEVED!",
            "celebration_emoji": "💫"
        }
    }
    
    def __init__(self, referral_system: Optional[Any] = None, 
                 notification_handler: Optional[Any] = None,
                 chat_notification_service: Optional[Any] = None):
        """Initialize the social brag system"""
        self.referral_system = referral_system
        self.notification_handler = notification_handler
        self.chat_notification_service = chat_notification_service
        
        # Cache recent notifications to avoid spam
        self.recent_notifications: Dict[str, Set[str]] = {}
        self.notification_cooldown = 300  # 5 minutes
        
        logger.info("Social Brag System initialized")
    
    def notify_tactical_strategy_unlock(
        self, 
        user_id: str, 
        username: str, 
        strategy_name: str,
        strategy_display_name: str,
        strategy_description: str,
        xp_amount: int
    ) -> Optional[BragNotification]:
        """Send squad notification for tactical strategy unlock"""
        try:
            # Get squad members
            squad_members = self._get_squad_members(user_id)
            if not squad_members:
                logger.info(f"No squad members found for {user_id}, skipping brag notification")
                return None
            
            # Check cooldown
            if self._is_on_cooldown(user_id, strategy_name):
                logger.info(f"Strategy unlock {strategy_name} for {user_id} is on cooldown")
                return None
            
            # Get message templates
            messages = self.TACTICAL_STRATEGY_MESSAGES.get(strategy_name, {
                "brag_message": "🎯 {username} just unlocked {strategy_name}! Another soldier advances through the ranks!",
                "drill_sergeant": "ATTENTION SQUAD! {username} has unlocked a new tactical strategy: {strategy_name}! This soldier is getting sharper by the day!",
                "celebration_emoji": "🎯"
            })
            
            # Format messages
            brag_message = messages["brag_message"].format(
                username=username, 
                strategy_name=strategy_display_name
            )
            drill_sergeant_message = messages["drill_sergeant"].format(
                username=username, 
                strategy_name=strategy_display_name
            )
            
            # Create brag notification
            brag_notification = BragNotification(
                user_id=user_id,
                username=username,
                achievement_type=BragType.TACTICAL_STRATEGY_UNLOCK,
                achievement_name=strategy_display_name,
                achievement_description=strategy_description,
                brag_message=brag_message,
                drill_sergeant_message=drill_sergeant_message,
                squad_members=squad_members,
                timestamp=datetime.now(),
                metadata={
                    "strategy_name": strategy_name,
                    "xp_amount": xp_amount,
                    "celebration_emoji": messages.get("celebration_emoji", "🎯")
                }
            )
            
            # Send notifications to squad members
            self._send_squad_notifications(brag_notification)
            
            # Update cooldown
            self._update_cooldown(user_id, strategy_name)
            
            logger.info(f"Sent tactical strategy unlock brag for {username}: {strategy_name}")
            return brag_notification
            
        except Exception as e:
            logger.error(f"Error sending tactical strategy unlock brag: {e}")
            return None
    
    def notify_rank_promotion(
        self, 
        user_id: str, 
        username: str, 
        new_rank: str,
        old_rank: str
    ) -> Optional[BragNotification]:
        """Send squad notification for rank promotion"""
        try:
            # Only notify for significant rank ups
            if new_rank not in self.RANK_PROMOTION_MESSAGES:
                return None
            
            # Get squad members
            squad_members = self._get_squad_members(user_id)
            if not squad_members:
                return None
            
            # Check cooldown
            if self._is_on_cooldown(user_id, f"rank_{new_rank}"):
                return None
            
            # Get message templates
            messages = self.RANK_PROMOTION_MESSAGES[new_rank]
            
            # Format messages
            brag_message = messages["brag_message"].format(username=username)
            drill_sergeant_message = messages["drill_sergeant"].format(username=username)
            
            # Create brag notification
            brag_notification = BragNotification(
                user_id=user_id,
                username=username,
                achievement_type=BragType.RANK_PROMOTION,
                achievement_name=f"{new_rank} Rank",
                achievement_description=f"Promoted from {old_rank} to {new_rank}",
                brag_message=brag_message,
                drill_sergeant_message=drill_sergeant_message,
                squad_members=squad_members,
                timestamp=datetime.now(),
                metadata={
                    "new_rank": new_rank,
                    "old_rank": old_rank,
                    "celebration_emoji": messages.get("celebration_emoji", "🏆")
                }
            )
            
            # Send notifications
            self._send_squad_notifications(brag_notification)
            
            # Update cooldown
            self._update_cooldown(user_id, f"rank_{new_rank}")
            
            logger.info(f"Sent rank promotion brag for {username}: {old_rank} -> {new_rank}")
            return brag_notification
            
        except Exception as e:
            logger.error(f"Error sending rank promotion brag: {e}")
            return None
    
    def notify_prestige_achievement(
        self, 
        user_id: str, 
        username: str, 
        prestige_level: int
    ) -> Optional[BragNotification]:
        """Send squad notification for prestige achievement"""
        try:
            # Get squad members
            squad_members = self._get_squad_members(user_id)
            if not squad_members:
                return None
            
            # Check cooldown
            if self._is_on_cooldown(user_id, f"prestige_{prestige_level}"):
                return None
            
            # Get message templates
            messages = self.PRESTIGE_MESSAGES.get(prestige_level, {
                "brag_message": f"⭐ {{username}} just achieved PRESTIGE LEVEL {prestige_level}! Legendary warrior!",
                "drill_sergeant": f"INCREDIBLE! {{username}} has reached PRESTIGE LEVEL {prestige_level}! This soldier keeps pushing the limits of excellence!",
                "celebration_emoji": "⭐"
            })
            
            # Format messages
            brag_message = messages["brag_message"].format(username=username)
            drill_sergeant_message = messages["drill_sergeant"].format(username=username)
            
            # Create brag notification
            brag_notification = BragNotification(
                user_id=user_id,
                username=username,
                achievement_type=BragType.PRESTIGE_ACHIEVEMENT,
                achievement_name=f"Prestige Level {prestige_level}",
                achievement_description=f"Achieved prestige level {prestige_level}",
                brag_message=brag_message,
                drill_sergeant_message=drill_sergeant_message,
                squad_members=squad_members,
                timestamp=datetime.now(),
                metadata={
                    "prestige_level": prestige_level,
                    "celebration_emoji": messages.get("celebration_emoji", "⭐")
                }
            )
            
            # Send notifications
            self._send_squad_notifications(brag_notification)
            
            # Update cooldown
            self._update_cooldown(user_id, f"prestige_{prestige_level}")
            
            logger.info(f"Sent prestige achievement brag for {username}: Level {prestige_level}")
            return brag_notification
            
        except Exception as e:
            logger.error(f"Error sending prestige achievement brag: {e}")
            return None
    
    def _get_squad_members(self, user_id: str) -> List[str]:
        """Get squad members for a user"""
        try:
            if not self.referral_system:
                return []
            
            # Get all recruits of this user
            genealogy = self.referral_system.get_squad_genealogy(user_id, max_depth=2)
            squad_members = []
            
            # Add direct recruits
            for recruit in genealogy.get('recruits', []):
                squad_members.append(recruit['user_id'])
                
                # Add their recruits too (2 levels deep)
                for sub_recruit in recruit.get('sub_recruits', []):
                    squad_members.append(sub_recruit['user_id'])
            
            # Also try to find who referred this user (their squad leader)
            try:
                import sqlite3
                if hasattr(self.referral_system, 'db_path'):
                    conn = sqlite3.connect(self.referral_system.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        'SELECT referrer_id FROM recruits WHERE recruit_id = ?',
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    if result and result[0]:
                        squad_members.append(result[0])
                    conn.close()
            except Exception as e:
                logger.debug(f"Could not lookup referrer for {user_id}: {e}")
            
            return list(set(squad_members))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting squad members for {user_id}: {e}")
            return []
    
    def _send_squad_notifications(self, brag_notification: BragNotification):
        """Send notifications to all squad members"""
        try:
            # Send via notification handler (for webapp/game notifications)
            if self.notification_handler:
                for member_id in brag_notification.squad_members:
                    self.notification_handler.send_notification(
                        user_id=member_id,
                        notification_type=NotificationType.ACHIEVEMENT,
                        title="Squad Achievement!",
                        message=brag_notification.brag_message,
                        data={
                            "brag_type": brag_notification.achievement_type.value,
                            "achievement_user": brag_notification.username,
                            "drill_sergeant_message": brag_notification.drill_sergeant_message,
                            "celebration_emoji": brag_notification.metadata.get("celebration_emoji", "🎯")
                        },
                        priority=7  # High priority for achievements
                    )
            
            # Send via chat notification service (for email/telegram/push)
            if self.chat_notification_service:
                self.chat_notification_service.create_squad_notification(
                    squad_id=f"squad_{brag_notification.user_id}",
                    user_ids=brag_notification.squad_members,
                    title="🎖️ Squad Achievement Alert!",
                    message=brag_notification.drill_sergeant_message,
                    notification_type=ChatNotificationType.SQUAD_MESSAGE,
                    priority=NotificationPriority.HIGH,
                    exclude_user_id=brag_notification.user_id,  # Don't notify the achiever
                    metadata={
                        "brag_type": brag_notification.achievement_type.value,
                        "achievement_name": brag_notification.achievement_name,
                        "achievement_user": brag_notification.username,
                        "celebration_emoji": brag_notification.metadata.get("celebration_emoji", "🎯")
                    }
                )
            
            logger.info(f"Sent brag notifications to {len(brag_notification.squad_members)} squad members")
            
        except Exception as e:
            logger.error(f"Error sending squad notifications: {e}")
    
    def _is_on_cooldown(self, user_id: str, achievement_key: str) -> bool:
        """Check if achievement notification is on cooldown"""
        try:
            if user_id not in self.recent_notifications:
                return False
            
            # For now, simple check - don't send same achievement twice
            return achievement_key in self.recent_notifications[user_id]
            
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False
    
    def _update_cooldown(self, user_id: str, achievement_key: str):
        """Update cooldown for achievement notification"""
        try:
            if user_id not in self.recent_notifications:
                self.recent_notifications[user_id] = set()
            
            self.recent_notifications[user_id].add(achievement_key)
            
            # Clean up old cooldowns (basic implementation)
            # In a production system, you'd want to use timestamps and cleanup properly
            if len(self.recent_notifications[user_id]) > 50:
                # Keep only last 50 achievements to prevent memory bloat
                old_achievements = list(self.recent_notifications[user_id])[:25]
                for old_achievement in old_achievements:
                    self.recent_notifications[user_id].discard(old_achievement)
            
        except Exception as e:
            logger.error(f"Error updating cooldown: {e}")
    
    def get_recent_brags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent brag notifications (for leaderboard/feed display)"""
        try:
            # This would typically come from a database
            # For now, return empty list as this is just the notification system
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent brags: {e}")
            return []
    
    def format_brag_for_telegram(self, brag_notification: BragNotification) -> str:
        """Format brag notification for Telegram display"""
        try:
            emoji = brag_notification.metadata.get("celebration_emoji", "🎯")
            
            lines = [
                f"{emoji} **SQUAD ACHIEVEMENT ALERT** {emoji}",
                "",
                f"**{brag_notification.achievement_name}**",
                f"Achieved by: **{brag_notification.username}**",
                "",
                brag_notification.drill_sergeant_message,
                "",
                f"_{brag_notification.achievement_description}_",
                "",
                "🎖️ *Keep pushing forward, soldiers!* 🎖️"
            ]
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error formatting brag for Telegram: {e}")
            return f"🎯 {brag_notification.username} achieved {brag_notification.achievement_name}!"
    
    def format_brag_for_webapp(self, brag_notification: BragNotification) -> Dict[str, Any]:
        """Format brag notification for WebApp display"""
        try:
            return {
                "id": f"brag_{brag_notification.user_id}_{brag_notification.timestamp.timestamp()}",
                "type": "squad_achievement",
                "user_id": brag_notification.user_id,
                "username": brag_notification.username,
                "achievement_type": brag_notification.achievement_type.value,
                "achievement_name": brag_notification.achievement_name,
                "brag_message": brag_notification.brag_message,
                "drill_sergeant_message": brag_notification.drill_sergeant_message,
                "celebration_emoji": brag_notification.metadata.get("celebration_emoji", "🎯"),
                "timestamp": brag_notification.timestamp.isoformat(),
                "metadata": brag_notification.metadata
            }
            
        except Exception as e:
            logger.error(f"Error formatting brag for WebApp: {e}")
            return {}

# Global instance (will be initialized by the main application)
social_brag_system: Optional[SocialBragSystem] = None

def initialize_social_brag_system(
    referral_system: Optional[Any] = None,
    notification_handler: Optional[Any] = None,
    chat_notification_service: Optional[Any] = None
) -> SocialBragSystem:
    """Initialize the global social brag system"""
    global social_brag_system
    
    social_brag_system = SocialBragSystem(
        referral_system=referral_system,
        notification_handler=notification_handler,
        chat_notification_service=chat_notification_service
    )
    
    logger.info("Global social brag system initialized")
    return social_brag_system

def get_social_brag_system() -> Optional[SocialBragSystem]:
    """Get the global social brag system instance"""
    return social_brag_system

# Helper functions for easy integration
def notify_tactical_strategy_unlock(
    user_id: str, 
    username: str, 
    strategy_name: str,
    strategy_display_name: str,
    strategy_description: str,
    xp_amount: int
) -> Optional[BragNotification]:
    """Quick helper to notify tactical strategy unlock"""
    if social_brag_system:
        return social_brag_system.notify_tactical_strategy_unlock(
            user_id, username, strategy_name, strategy_display_name, strategy_description, xp_amount
        )
    return None

def notify_rank_promotion(
    user_id: str, 
    username: str, 
    new_rank: str,
    old_rank: str
) -> Optional[BragNotification]:
    """Quick helper to notify rank promotion"""
    if social_brag_system:
        return social_brag_system.notify_rank_promotion(user_id, username, new_rank, old_rank)
    return None

def notify_prestige_achievement(
    user_id: str, 
    username: str, 
    prestige_level: int
) -> Optional[BragNotification]:
    """Quick helper to notify prestige achievement"""
    if social_brag_system:
        return social_brag_system.notify_prestige_achievement(user_id, username, prestige_level)
    return None

# Example usage
if __name__ == "__main__":
    # Initialize with mock systems
    brag_system = SocialBragSystem()
    
    # Test tactical strategy unlock
    brag = brag_system.notify_tactical_strategy_unlock(
        user_id="test_user_123",
        username="ALPHA-1",
        strategy_name="FIRST_BLOOD",
        strategy_display_name="First Blood",
        strategy_description="Strike fast and hard with precision timing",
        xp_amount=120
    )
    
    if brag:
        print("Tactical Strategy Unlock Brag:")
        print(f"Message: {brag.brag_message}")
        print(f"Drill Sergeant: {brag.drill_sergeant_message}")
        print(f"Squad Members: {len(brag.squad_members)}")
    
    # Test rank promotion
    rank_brag = brag_system.notify_rank_promotion(
        user_id="test_user_456",
        username="BRAVO-2", 
        new_rank="FANG",
        old_rank="NIBBLER"
    )
    
    if rank_brag:
        print("\nRank Promotion Brag:")
        print(f"Message: {rank_brag.brag_message}")
        print(f"Drill Sergeant: {rank_brag.drill_sergeant_message}")