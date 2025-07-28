#!/usr/bin/env python3
"""
🛡️ REDUNDANT CONFIG LOADER - Failsafe environment loading
"""

import os
from typing import Dict, Any

class RedundantConfig:
    """Load config with multiple fallback methods"""
    
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load config with fallbacks"""
        # Try .env.local first (real secrets)
        self._try_load_env_file('.env.local')
        
        # Fallback to .env if exists
        self._try_load_env_file('.env')
        
        # Apply defaults for critical values
        self._apply_defaults()
    
    def _try_load_env_file(self, filename: str):
        """Try to load environment file"""
        try:
            from dotenv import load_dotenv
            load_dotenv(filename)
        except ImportError:
            # Manual parsing if python-dotenv not available
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
        except Exception:
            pass
    
    def _apply_defaults(self):
        """Apply safe defaults for critical components"""
        defaults = {
            'BOT_TOKEN': 'DISABLED_FOR_SECURITY',
            'CHAT_ID': '-1002581996861',
            'ADMIN_USER_ID': '7176191872',
            'FLASK_SECRET_KEY': 'dev-key-change-in-production',
            'DATABASE_URL': 'sqlite:///data/bitten.db',
            'WEBAPP_PORT': '8888',
            'WEBAPP_HOST': '0.0.0.0'}
        
        for key, default_value in defaults.items():
            if not os.getenv(key):
                os.environ[key] = default_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with fallback"""
        return os.getenv(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer config value"""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return os.getenv('FLASK_ENV', 'development').lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return not self.is_production()

# Global config instance
config = RedundantConfig()
