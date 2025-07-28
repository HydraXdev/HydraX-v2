#!/usr/bin/env python3
"""
BITTEN Configuration Loader
Centralized configuration management with environment variable support
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Centralized configuration loader with environment variable support."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            env_file: Optional path to .env file. Defaults to .env in project root.
        """
        if env_file is None:
            project_root = Path(__file__).parent.parent
            env_file = project_root / ".env"
        
        # Load environment variables from .env file
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded configuration from {env_file}")
        else:
            logger.warning(f"No .env file found at {env_file}")
    
    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Get configuration value from environment variables.
        
        Args:
            key: Environment variable key
            default: Default value if key not found
            required: Raise error if key is missing and no default provided
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If required key is missing
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Required configuration key '{key}' not found in environment")
        
        return value
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(key, str(default).lower())
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value for {key}: {value}, using default {default}")
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value for {key}: {value}, using default {default}")
            return default

# Global configuration instance
config = ConfigLoader()

# Common configuration getters for easy access
def get_bot_token() -> str:
    """Get main bot token."""
    token = config.get("BOT_TOKEN", required=True)
    if token in ("DISABLED_FOR_SECURITY", "your_main_trading_bot_token_here"):
        raise ValueError("BOT_TOKEN not properly configured in .env file")
    return token

def get_voice_bot_token() -> str:
    """Get voice bot token."""
    token = config.get("VOICE_BOT_TOKEN", required=True)
    if token in ("DISABLED_FOR_SECURITY", "your_voice_personality_bot_token_here"):
        raise ValueError("VOICE_BOT_TOKEN not properly configured in .env file")
    return token

def get_flask_secret_key() -> str:
    """Get Flask secret key."""
    key = config.get("FLASK_SECRET_KEY", required=True)
    if key == "your_flask_secret_key_here":
        raise ValueError("FLASK_SECRET_KEY not properly configured in .env file")
    return key

def get_database_url() -> str:
    """Get database URL."""
    return config.get("DATABASE_URL", "sqlite:///data/bitten_production.db")

def get_redis_url() -> str:
    """Get Redis URL."""
    return config.get("REDIS_URL", "redis://localhost:6379/0")

def get_stripe_keys() -> Dict[str, str]:
    """Get Stripe API keys."""
    secret_key = config.get("STRIPE_SECRET_KEY")
    publishable_key = config.get("STRIPE_PUBLISHABLE_KEY")
    webhook_secret = config.get("STRIPE_WEBHOOK_SECRET")
    
    keys = {}
    if secret_key and secret_key != "sk_test_your_stripe_secret_key_here":
        keys["secret_key"] = secret_key
    if publishable_key and publishable_key != "pk_test_your_stripe_publishable_key_here":
        keys["publishable_key"] = publishable_key
    if webhook_secret and webhook_secret != "whsec_your_webhook_secret_here":
        keys["webhook_secret"] = webhook_secret
    
    return keys

def get_mt5_config() -> Dict[str, str]:
    """Get MT5 configuration."""
    return {
        "login": config.get("MT5_LOGIN", ""),
        "password": config.get("MT5_PASSWORD", ""),
        "server": config.get("MT5_SERVER", ""),
        "broker": config.get("MT5_BROKER", ""),
        "path": config.get("MT5_PATH", "/opt/mt5/terminal64.exe")
    }

def is_production() -> bool:
    """Check if running in production mode."""
    return config.get("FLASK_ENV", "development").lower() == "production"

def get_webapp_config() -> Dict[str, Any]:
    """Get WebApp configuration."""
    return {
        "port": config.get_int("WEBAPP_PORT", 8888),
        "host": config.get("WEBAPP_HOST", "0.0.0.0"),
        "debug": not is_production()
    }

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration."""
    return {
        "level": config.get("LOG_LEVEL", "INFO"),
        "file_path": config.get("LOG_FILE_PATH", "/root/HydraX-v2/logs/production.log")
    }

def validate_required_config() -> None:
    """Validate that all required configuration is present."""
    required_keys = [
        "BOT_TOKEN",
        "VOICE_BOT_TOKEN", 
        "FLASK_SECRET_KEY"
    ]
    
    missing_keys = []
    for key in required_keys:
        try:
            if key == "BOT_TOKEN":
                get_bot_token()
            elif key == "VOICE_BOT_TOKEN":
                get_voice_bot_token()
            elif key == "FLASK_SECRET_KEY":
                get_flask_secret_key()
        except ValueError:
            missing_keys.append(key)
    
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {missing_keys}")

if __name__ == "__main__":
    # Test configuration loading
    try:
        validate_required_config()
        print("✅ All required configuration loaded successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")