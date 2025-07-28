"""
User Settings Management for BITTEN
Handles user preferences including sound toggles
"""

import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class UserSettings:
    """User preference settings"""
    user_id: str
    
    # Sound settings
    sounds_enabled: bool = True
    cash_register_sound: bool = True
    achievement_sounds: bool = True
    warning_sounds: bool = True
    
    # Notification settings
    signal_notifications: bool = True
    trade_notifications: bool = True
    achievement_notifications: bool = True
    recruitment_notifications: bool = True
    
    # Trading settings
    risk_percentage: float = 2.0
    max_positions: int = 3
    default_mode: str = "bit"
    auto_close: bool = False
    show_pnl_in_pips: bool = True
    
    # Display settings
    theme: str = "dark"
    language: str = "en"
    time_format: str = "24h"
    currency_display: str = "USD"
    reduced_motion: bool = False
    
    # Privacy settings
    show_in_leaderboard: bool = True
    allow_squad_visibility: bool = True
    
    # Last updated
    last_updated: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['last_updated'] = datetime.now().isoformat()
        return data

class UserSettingsManager:
    """Manages user settings with persistence"""
    
    def __init__(self, data_dir: str = "data/user_settings"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for loaded settings
        self.settings_cache: Dict[str, UserSettings] = {}
    
    def get_user_settings(self, user_id: str) -> UserSettings:
        """Get user settings, create default if not exists"""
        # Check cache first
        if user_id in self.settings_cache:
            return self.settings_cache[user_id]
        
        # Try to load from file
        settings_file = self.data_dir / f"user_{user_id}_settings.json"
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                    settings = UserSettings(**data)
                    self.settings_cache[user_id] = settings
                    return settings
            except Exception as e:
                logger.error(f"Error loading settings for {user_id}: {e}")
        
        # Create default settings
        settings = UserSettings(user_id=user_id)
        self.settings_cache[user_id] = settings
        self._save_settings(settings)
        
        return settings
    
    def update_user_settings(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> UserSettings:
        """Update specific user settings"""
        settings = self.get_user_settings(user_id)
        
        # Update only valid fields
        for key, value in updates.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.last_updated = datetime.now().isoformat()
        
        # Save to file
        self._save_settings(settings)
        
        logger.info(f"Updated settings for user {user_id}: {list(updates.keys())}")
        
        return settings
    
    def toggle_sounds(self, user_id: str, enabled: bool) -> UserSettings:
        """Toggle all sounds on/off"""
        return self.update_user_settings(user_id, {
            "sounds_enabled": enabled
        })
    
    def toggle_cash_register(self, user_id: str, enabled: bool) -> UserSettings:
        """Toggle cash register sound specifically"""
        return self.update_user_settings(user_id, {
            "cash_register_sound": enabled
        })
    
    def get_sound_settings(self, user_id: str) -> Dict[str, bool]:
        """Get just the sound settings"""
        settings = self.get_user_settings(user_id)
        
        return {
            "sounds_enabled": settings.sounds_enabled,
            "cash_register_sound": settings.cash_register_sound,
            "achievement_sounds": settings.achievement_sounds,
            "warning_sounds": settings.warning_sounds
        }
    
    def get_notification_settings(self, user_id: str) -> Dict[str, bool]:
        """Get notification preferences"""
        settings = self.get_user_settings(user_id)
        
        return {
            "signal_notifications": settings.signal_notifications,
            "trade_notifications": settings.trade_notifications,
            "achievement_notifications": settings.achievement_notifications,
            "recruitment_notifications": settings.recruitment_notifications
        }
    
    def get_trading_settings(self, user_id: str) -> Dict[str, Any]:
        """Get trading preferences"""
        settings = self.get_user_settings(user_id)
        
        return {
            "risk_percentage": settings.risk_percentage,
            "max_positions": settings.max_positions,
            "default_mode": settings.default_mode,
            "auto_close": settings.auto_close,
            "show_pnl_in_pips": settings.show_pnl_in_pips
        }
    
    def get_display_settings(self, user_id: str) -> Dict[str, Any]:
        """Get display preferences"""
        settings = self.get_user_settings(user_id)
        
        return {
            "theme": settings.theme,
            "language": settings.language,
            "time_format": settings.time_format,
            "currency_display": settings.currency_display,
            "reduced_motion": settings.reduced_motion
        }
    
    def format_for_webapp(self, user_id: str) -> Dict[str, Any]:
        """Format settings for webapp display"""
        settings = self.get_user_settings(user_id)
        
        return {
            "sounds": {
                "enabled": settings.sounds_enabled,
                "cash_register": settings.cash_register_sound,
                "achievements": settings.achievement_sounds,
                "warnings": settings.warning_sounds
            },
            "notifications": {
                "signals": settings.signal_notifications,
                "trades": settings.trade_notifications,
                "achievements": settings.achievement_notifications,
                "recruitment": settings.recruitment_notifications
            },
            "trading": {
                "risk_percentage": settings.risk_percentage,
                "max_positions": settings.max_positions,
                "default_mode": settings.default_mode,
                "auto_close": settings.auto_close,
                "show_pnl_in_pips": settings.show_pnl_in_pips
            },
            "display": {
                "theme": settings.theme,
                "language": settings.language,
                "time_format": settings.time_format,
                "currency_display": settings.currency_display,
                "reduced_motion": settings.reduced_motion
            },
            "privacy": {
                "show_in_leaderboard": settings.show_in_leaderboard,
                "allow_squad_visibility": settings.allow_squad_visibility
            },
            "last_updated": settings.last_updated
        }
    
    def _save_settings(self, settings: UserSettings) -> None:
        """Save settings to file"""
        settings_file = self.data_dir / f"user_{settings.user_id}_settings.json"
        
        with open(settings_file, 'w') as f:
            json.dump(settings.to_dict(), f, indent=2)
    
    def export_all_settings(self, user_id: str) -> str:
        """Export all settings as JSON string"""
        settings = self.get_user_settings(user_id)
        return json.dumps(settings.to_dict(), indent=2)
    
    def import_settings(self, user_id: str, json_str: str) -> UserSettings:
        """Import settings from JSON string"""
        try:
            data = json.loads(json_str)
            data['user_id'] = user_id  # Ensure correct user ID
            
            settings = UserSettings(**data)
            self.settings_cache[user_id] = settings
            self._save_settings(settings)
            
            return settings
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            raise ValueError(f"Invalid settings format: {e}")

# Global instance
settings_manager = UserSettingsManager()

# Helper functions for easy access
def get_user_settings(user_id: str) -> UserSettings:
    """Get user settings"""
    return settings_manager.get_user_settings(user_id)

def update_user_settings(user_id: str, updates: Dict[str, Any]) -> UserSettings:
    """Update user settings"""
    return settings_manager.update_user_settings(user_id, updates)

def should_play_sound(user_id: str, sound_type: str = "general") -> bool:
    """Check if a sound should be played for user"""
    settings = settings_manager.get_user_settings(user_id)
    
    if not settings.sounds_enabled:
        return False
    
    if sound_type == "cash_register":
        return settings.cash_register_sound
    elif sound_type == "achievement":
        return settings.achievement_sounds
    elif sound_type == "warning":
        return settings.warning_sounds
    
    return True

# Example usage
if __name__ == "__main__":
    # Get settings for a user
    user_settings = get_user_settings("test_user")
    print(f"Sounds enabled: {user_settings.sounds_enabled}")
    
    # Toggle sounds off
    updated = settings_manager.toggle_sounds("test_user", False)
    print(f"Sounds now: {updated.sounds_enabled}")
    
    # Update multiple settings
    updated = update_user_settings("test_user", {
        "cash_register_sound": False,
        "theme": "light",
        "risk_percentage": 1.5
    })
    
    # Check if sound should play
    should_play = should_play_sound("test_user", "cash_register")
    print(f"Should play cash register: {should_play}")