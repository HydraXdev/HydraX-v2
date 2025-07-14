"""
Mock Telegram Router for Testing
This is a simplified version for testing purposes only.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TelegramUpdate:
    """Mock telegram update object"""
    user_id: str
    chat_id: str
    message: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class CommandResult:
    """Mock command result object"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

class TelegramRouter:
    """Mock telegram router for testing"""
    
    def __init__(self, bitten_core=None):
        self.bitten_core = bitten_core
        self.commands = {}
        logger.info("Mock Telegram Router initialized")
    
    def parse_telegram_update(self, update_data: Dict) -> TelegramUpdate:
        """Parse telegram update data"""
        return TelegramUpdate(
            user_id=update_data.get('user_id', 'test_user'),
            chat_id=update_data.get('chat_id', 'test_chat'),
            message=update_data.get('message', '')
        )
    
    def process_command(self, update: TelegramUpdate) -> CommandResult:
        """Process a telegram command"""
        return CommandResult(
            success=True,
            message="Command processed successfully",
            data={"command": update.message}
        )
    
    def send_message(self, chat_id: str, message: str) -> bool:
        """Mock send message"""
        logger.info(f"Mock telegram message sent to {chat_id}: {message}")
        return True
    
    def send_admin_message(self, message: str) -> bool:
        """Mock send admin message"""
        logger.info(f"Mock admin message: {message}")
        return True
    
    def get_user_positions(self, user_id: str) -> Dict:
        """Mock get user positions"""
        return {"positions": [], "total": 0}
    
    def send_mission_alert(self, alert_data: Dict) -> bool:
        """Mock send mission alert"""
        logger.info(f"Mock mission alert sent: {alert_data}")
        return True