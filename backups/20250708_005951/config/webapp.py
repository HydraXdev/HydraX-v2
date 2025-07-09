"""WebApp Configuration for BITTEN"""

import os
from typing import Dict, Any

class WebAppConfig:
    """Centralized WebApp configuration"""
    
    # Production URLs
    PRODUCTION_BASE_URL = "https://joinbitten.com"
    
    # WebApp endpoints
    HUD_URL = f"{PRODUCTION_BASE_URL}/hud"
    MISSION_BRIEF_URL = f"{PRODUCTION_BASE_URL}/mission"
    STATS_DASHBOARD_URL = f"{PRODUCTION_BASE_URL}/stats"
    SETTINGS_URL = f"{PRODUCTION_BASE_URL}/settings"
    PROFILE_URL = f"{PRODUCTION_BASE_URL}/profile"
    
    # Development URLs (fallback)
    DEV_BASE_URL = os.getenv('DEV_WEBAPP_URL', 'http://localhost:5000')
    
    @classmethod
    def get_hud_url(cls, environment: str = 'production') -> str:
        """Get HUD URL based on environment"""
        if environment == 'production':
            return cls.HUD_URL
        elif environment == 'development':
            return f"{cls.DEV_BASE_URL}/hud"
        else:
            return cls.HUD_URL  # Default to production
    
    @classmethod
    def get_webapp_data_url(cls, endpoint: str, data: Dict[str, Any], environment: str = 'production') -> str:
        """Build webapp URL with data parameters"""
        import json
        import urllib.parse
        
        base_url = cls.get_hud_url(environment)
        if endpoint != 'hud':
            base_url = base_url.replace('/hud', f'/{endpoint}')
        
        # Encode data as URL parameter
        encoded_data = urllib.parse.quote(json.dumps(data))
        return f"{base_url}?data={encoded_data}"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate webapp configuration"""
        try:
            # Check if URLs are properly formatted
            assert cls.PRODUCTION_BASE_URL.startswith('https://')
            assert 'joinbitten.com' in cls.PRODUCTION_BASE_URL
            return True
        except AssertionError:
            return False

# Singleton instance
webapp_config = WebAppConfig()