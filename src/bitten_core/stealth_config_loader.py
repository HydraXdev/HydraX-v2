# stealth_config_loader.py
# Configuration loader for stealth protocol settings

import os
import yaml
from typing import Dict, Any, Optional
from datetime import datetime
from .stealth_protocol import StealthConfig, StealthLevel

class StealthConfigLoader:
    """Loads and manages stealth protocol configuration"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = "/root/HydraX-v2/config/stealth_settings.yml"
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Stealth config not found at {self.config_path}, using defaults")
            return self._get_default_config()
        except Exception as e:
            print(f"Error loading stealth config: {e}, using defaults")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'stealth': {
                'enabled': True,
                'default_level': 'medium',
                'entry_delay': {
                    'low': {'min': 0.5, 'max': 3.0},
                    'medium': {'min': 1.0, 'max': 6.0},
                    'high': {'min': 2.0, 'max': 9.0},
                    'ghost': {'min': 3.0, 'max': 12.0}
                },
                'lot_jitter': {
                    'low': {'min': 0.01, 'max': 0.03},
                    'medium': {'min': 0.03, 'max': 0.07},
                    'high': {'min': 0.05, 'max': 0.10},
                    'ghost': {'min': 0.07, 'max': 0.15}
                },
                'ghost_skip': {
                    'low': 0.05,
                    'medium': 0.167,
                    'high': 0.25,
                    'ghost': 0.33
                },
                'volume_cap': {
                    'max_per_asset': 3,
                    'max_total': 10
                }
            }
        }
        
    def get_stealth_config(self, level: StealthLevel = None) -> StealthConfig:
        """Get StealthConfig object for specified level"""
        stealth_settings = self.config.get('stealth', {})
        
        # Use provided level or default
        if level is None:
            level_str = stealth_settings.get('default_level', 'medium')
            level = StealthLevel(level_str)
            
        level_key = level.value
        
        # Create config object
        config = StealthConfig()
        config.enabled = stealth_settings.get('enabled', True)
        config.level = level
        
        # Load level-specific settings
        if 'entry_delay' in stealth_settings and level_key in stealth_settings['entry_delay']:
            delay_settings = stealth_settings['entry_delay'][level_key]
            config.entry_delay_min = delay_settings.get('min', 1.0)
            config.entry_delay_max = delay_settings.get('max', 12.0)
            
        if 'lot_jitter' in stealth_settings and level_key in stealth_settings['lot_jitter']:
            jitter_settings = stealth_settings['lot_jitter'][level_key]
            config.lot_jitter_min = jitter_settings.get('min', 0.03)
            config.lot_jitter_max = jitter_settings.get('max', 0.07)
            
        if 'tp_sl_offset' in stealth_settings and level_key in stealth_settings['tp_sl_offset']:
            offset_settings = stealth_settings['tp_sl_offset'][level_key]
            config.tp_offset_min = offset_settings.get('tp_min', 1)
            config.tp_offset_max = offset_settings.get('tp_max', 3)
            config.sl_offset_min = offset_settings.get('sl_min', 1)
            config.sl_offset_max = offset_settings.get('sl_max', 3)
            
        if 'ghost_skip' in stealth_settings and level_key in stealth_settings['ghost_skip']:
            config.ghost_skip_rate = stealth_settings['ghost_skip'][level_key]
            
        if 'volume_cap' in stealth_settings:
            vol_settings = stealth_settings['volume_cap']
            config.max_concurrent_per_asset = vol_settings.get('max_per_asset', 3)
            config.max_total_concurrent = vol_settings.get('max_total', 10)
            
        if 'execution_shuffle' in stealth_settings:
            shuffle_settings = stealth_settings['execution_shuffle']
            config.shuffle_queue = shuffle_settings.get('enabled', True)
            config.shuffle_delay_min = shuffle_settings.get('delay_min', 0.5)
            config.shuffle_delay_max = shuffle_settings.get('delay_max', 2.0)
            
        return config
        
    def get_tier_permissions(self, tier: str) -> Dict[str, Any]:
        """Get stealth permissions for a specific tier"""
        tier_settings = self.config.get('tier_stealth', {})
        return tier_settings.get(tier.lower(), {
            'enabled': False,
            'max_level': 'off'
        })
        
    def can_use_stealth(self, tier: str, mode: str) -> bool:
        """Check if a tier can use stealth with a specific mode"""
        permissions = self.get_tier_permissions(tier)
        
        if not permissions.get('enabled', False):
            return False
            
        allowed_modes = permissions.get('modes', [])
        return 'all' in allowed_modes or mode.lower() in allowed_modes
        
    def get_special_behavior(self, behavior_type: str) -> Dict[str, Any]:
        """Get special behavior configuration"""
        behaviors = self.config.get('special_behaviors', {})
        return behaviors.get(behavior_type, {})
        
    def get_time_multipliers(self) -> Dict[str, float]:
        """Get time-based multipliers for current market session"""
        time_vars = self.get_special_behavior('time_variations')
        
        if not time_vars.get('enabled', True):
            return {'entry_delay': 1.0, 'lot_jitter': 1.0}
            
        # Determine current market session
        now = datetime.utcnow()
        hour = now.hour
        
        if 0 <= hour < 8:  # Asian session
            session = 'asian_session'
        elif 8 <= hour < 16:  # London session
            session = 'london_session'
        else:  # NY session
            session = 'ny_session'
            
        session_settings = time_vars.get(session, {})
        return {
            'entry_delay': session_settings.get('entry_delay_multiplier', 1.0),
            'lot_jitter': session_settings.get('lot_jitter_multiplier', 1.0)
        }
        
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        
# Singleton instance
_config_loader = None

def get_stealth_config_loader() -> StealthConfigLoader:
    """Get or create config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = StealthConfigLoader()
    return _config_loader