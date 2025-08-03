"""
Mock Telegram Bot Controls for Testing
This is a simplified version for testing purposes only.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MockDisclaimerManager:
    """Mock disclaimer manager for testing"""
    def get_onboarding_disclaimer(self):
        return "Mock disclaimer for testing"
    
    def accept_disclaimer(self, user_id):
        logger.info(f"Mock disclaimer accepted for user {user_id}")
        return True

class TelegramBotControls:
    """Mock telegram bot controls for testing"""
    
    def __init__(self):
        self.active_bots = {}
        self.bot_status = {}
        self.disclaimer_manager = MockDisclaimerManager()  # Add missing disclaimer_manager
        logger.info("Mock Telegram Bot Controls initialized")
    
    def start_bot(self, bot_id: str, config: Dict[str, Any]) -> bool:
        """Mock start bot"""
        self.active_bots[bot_id] = config
        self.bot_status[bot_id] = "running"
        logger.info(f"Mock bot started: {bot_id}")
        return True
    
    def stop_bot(self, bot_id: str) -> bool:
        """Mock stop bot"""
        if bot_id in self.active_bots:
            self.bot_status[bot_id] = "stopped"
            logger.info(f"Mock bot stopped: {bot_id}")
            return True
        return False
    
    def get_bot_status(self, bot_id: str) -> str:
        """Mock get bot status"""
        return self.bot_status.get(bot_id, "unknown")
    
    def list_active_bots(self) -> List[str]:
        """Mock list active bots"""
        return [bot_id for bot_id, status in self.bot_status.items() if status == "running"]
    
    def send_bot_message(self, bot_id: str, message: str) -> bool:
        """Mock send bot message"""
        logger.info(f"Mock bot message sent via {bot_id}: {message}")
        return True
        
    def handle_disclaimer_command(self, user_id: str) -> dict:
        """Mock disclaimer command handler"""
        logger.info(f"Mock disclaimer command for user {user_id}")
        return {"status": "success", "message": "Mock disclaimer handled"}
        
    def handle_botcontrol_command(self, user_id: str, args: list = None) -> dict:
        """Mock bot control command handler"""
        logger.info(f"Mock bot control command for user {user_id}")
        return {"status": "success", "message": "Mock bot control handled"}

def should_show_bot_message(message: str, user_context: Dict[str, Any] = None) -> bool:
    """Mock function to determine if bot message should be shown"""
    return True

def format_bot_message(message: str, format_type: str = "default") -> str:
    """Mock function to format bot message"""
    if format_type == "markdown":
        return f"**{message}**"
    elif format_type == "html":
        return f"<b>{message}</b>"
    else:
        return message