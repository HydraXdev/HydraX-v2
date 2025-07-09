# telegram.py
# BITTEN Telegram Configuration

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TelegramConfig:
    """Telegram bot configuration"""
    
    # Bot credentials
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ')
    
    # Chat IDs
    MAIN_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', '-1002581996861'))
    ADMIN_USER_ID = int(os.getenv('TELEGRAM_USER_ID', '7176191872'))
    
    # Alert settings
    ALERT_TIMEOUT = 30  # seconds between alert updates
    MAX_ALERTS_PER_MINUTE = 10
    SOCIAL_PROOF_DURATION = 36000  # 10 hours in seconds
    
    # Message settings
    PARSE_MODE = 'HTML'  # or 'Markdown'
    DISABLE_WEB_PAGE_PREVIEW = True
    
    # Press Pass Configuration
    PRESS_PASS_DAILY_LIMIT = 10  # Number of press passes available per day
    PRESS_PASS_DURATION_DAYS = 30  # Duration in days
    PRESS_PASS_TIER = "APEX"  # Tier granted with press pass
    
    # Deep linking parameters
    START_PARAMETERS = {
        "press_pass": "Start with Press Pass offer",
        "demo": "Start with demo mode",
        "live": "Start with live trading options",
        "trial": "Start 15-day free trial",
        "lifetime_apex": "Claim lifetime APEX discount",
        "final_apex_offer": "Final press pass conversion offer"
    }
    
    @classmethod
    def get_bot_token(cls):
        """Get bot token with validation"""
        if not cls.BOT_TOKEN:
            raise ValueError("Telegram bot token not configured")
        return cls.BOT_TOKEN
    
    @classmethod
    def get_chat_id(cls):
        """Get main chat ID"""
        return cls.MAIN_CHAT_ID
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == cls.ADMIN_USER_ID