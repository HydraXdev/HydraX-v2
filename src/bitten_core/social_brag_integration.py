"""
BITTEN Social Brag System Integration
Handles initialization and connection of the social brag system with other BITTEN systems
"""

import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SocialBragIntegration:
    """Integration manager for the social brag system"""
    
    def __init__(self):
        self.social_brag_system = None
        self.xp_economy = None
        self.referral_system = None
        self.notification_handler = None
        self.chat_notification_service = None
        
    def initialize(
        self,
        xp_economy=None,
        referral_system=None,
        notification_handler=None,
        chat_notification_service=None,
        username_lookup_func: Optional[Callable[[str], str]] = None
    ):
        """Initialize the social brag system with all dependencies"""
        try:
            # Import here to avoid circular imports
            from .social_brag_system import initialize_social_brag_system
            
            # Store references
            self.xp_economy = xp_economy
            self.referral_system = referral_system
            self.notification_handler = notification_handler
            self.chat_notification_service = chat_notification_service
            
            # Initialize the social brag system
            self.social_brag_system = initialize_social_brag_system(
                referral_system=referral_system,
                notification_handler=notification_handler,
                chat_notification_service=chat_notification_service
            )
            
            # Set up username lookup function in XP economy if provided
            if xp_economy and username_lookup_func:
                xp_economy.set_username_lookup_function(username_lookup_func)
            
            logger.info("Social brag system integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize social brag integration: {e}")
            return False
    
    def notify_rank_promotion(self, user_id: str, username: str, new_rank: str, old_rank: str):
        """Handle rank promotion notifications"""
        try:
            if self.social_brag_system:
                return self.social_brag_system.notify_rank_promotion(
                    user_id, username, new_rank, old_rank
                )
        except Exception as e:
            logger.error(f"Error notifying rank promotion: {e}")
        return None
    
    def notify_prestige_achievement(self, user_id: str, username: str, prestige_level: int):
        """Handle prestige achievement notifications"""
        try:
            if self.social_brag_system:
                return self.social_brag_system.notify_prestige_achievement(
                    user_id, username, prestige_level
                )
        except Exception as e:
            logger.error(f"Error notifying prestige achievement: {e}")
        return None
    
    def get_recent_brags(self, limit: int = 10):
        """Get recent brag notifications for display"""
        try:
            if self.social_brag_system:
                return self.social_brag_system.get_recent_brags(limit)
        except Exception as e:
            logger.error(f"Error getting recent brags: {e}")
        return []


# Global integration instance
social_brag_integration = SocialBragIntegration()


def initialize_social_brag_integration(**kwargs):
    """Initialize the global social brag integration"""
    return social_brag_integration.initialize(**kwargs)


def get_social_brag_integration() -> SocialBragIntegration:
    """Get the global social brag integration instance"""
    return social_brag_integration


# Example integration setup
def setup_bitten_social_brags(
    xp_economy,
    referral_system,
    notification_handler,
    chat_notification_service,
    user_manager=None
):
    """
    Complete setup function for BITTEN social brag system
    
    Args:
        xp_economy: XPEconomy instance
        referral_system: ReferralSystem instance  
        notification_handler: NotificationHandler instance
        chat_notification_service: ChatNotificationService instance
        user_manager: Optional user manager with get_username method
    """
    try:
        # Define username lookup function
        username_lookup_func = None
        if user_manager and hasattr(user_manager, 'get_username'):
            username_lookup_func = user_manager.get_username
        elif user_manager and hasattr(user_manager, 'get_user_display_name'):
            username_lookup_func = user_manager.get_user_display_name
        
        # Initialize the integration
        success = initialize_social_brag_integration(
            xp_economy=xp_economy,
            referral_system=referral_system,
            notification_handler=notification_handler,
            chat_notification_service=chat_notification_service,
            username_lookup_func=username_lookup_func
        )
        
        if success:
            logger.info("BITTEN Social Brag System fully configured and ready!")
            return True
        else:
            logger.error("Failed to setup BITTEN social brag system")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up BITTEN social brags: {e}")
        return False


# Helper function for rank promotions in other systems
def handle_user_rank_promotion(user_id: str, new_rank: str, old_rank: str, username: str = None):
    """Helper to handle rank promotions from other systems"""
    try:
        integration = get_social_brag_integration()
        if not username:
            username = user_id  # Fallback
        
        return integration.notify_rank_promotion(user_id, username, new_rank, old_rank)
        
    except Exception as e:
        logger.error(f"Error handling rank promotion: {e}")
        return None


# Helper function for prestige achievements
def handle_user_prestige(user_id: str, prestige_level: int, username: str = None):
    """Helper to handle prestige achievements from other systems"""
    try:
        integration = get_social_brag_integration()
        if not username:
            username = user_id  # Fallback
        
        return integration.notify_prestige_achievement(user_id, username, prestige_level)
        
    except Exception as e:
        logger.error(f"Error handling prestige achievement: {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    # Mock systems for testing
    class MockUserManager:
        def get_username(self, user_id: str) -> str:
            callsigns = {
                "user123": "ALPHA-1",
                "user456": "BRAVO-2", 
                "user789": "CHARLIE-3"
            }
            return callsigns.get(user_id, f"OPERATOR-{user_id[-3:]}")
    
    class MockXPEconomy:
        def set_username_lookup_function(self, func):
            self.get_username_func = func
            print(f"Username lookup function set: {func}")
    
    class MockReferralSystem:
        def get_squad_genealogy(self, user_id, max_depth=2):
            return {'recruits': [{'user_id': 'recruit1'}, {'user_id': 'recruit2'}]}
    
    # Test setup
    user_manager = MockUserManager()
    xp_economy = MockXPEconomy()
    referral_system = MockReferralSystem()
    
    print("Testing BITTEN Social Brag Integration...")
    
    success = setup_bitten_social_brags(
        xp_economy=xp_economy,
        referral_system=referral_system,
        notification_handler=None,
        chat_notification_service=None,
        user_manager=user_manager
    )
    
    print(f"Setup result: {success}")
    
    # Test rank promotion
    result = handle_user_rank_promotion("user123", "FANG", "NIBBLER", "ALPHA-1")
    print(f"Rank promotion result: {result}")
    
    # Test prestige
    result = handle_user_prestige("user456", 1, "BRAVO-2")
    print(f"Prestige result: {result}")