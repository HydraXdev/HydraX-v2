#!/usr/bin/env python3
"""
Elite Guard Configuration Loader
Loads configuration from JSON with fallback to hardcoded defaults
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Load Elite Guard configuration from JSON with fallbacks"""
    
    def __init__(self, config_path: str = "/root/HydraX-v2/config/elite_guard_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with fallback to defaults"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"✅ Elite Guard config loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"⚠️ Config file not found at {self.config_path}, using defaults")
                return self._get_default_config()
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback configuration - exact copy of original hardcoded values"""
        return {
            "pip_sizes": {
                "JPY": 0.01,
                "GOLD": 0.1,
                "SILVER": 0.001,
                "BTC": 1.0,
                "ETH": 0.1,
                "DEFAULT": 0.0001
            },
            "min_stop_requirements": {
                "USDMXN": 60, "USDSEK": 20, "USDCNH": 30,
                "XAGUSD": 25, "XAUUSD": 30, "USDNOK": 20,
                "USDDKK": 20, "USDTRY": 50, "USDZAR": 30,
                "USDJPY": 15, "EURJPY": 18, "GBPJPY": 20,
                "AUDJPY": 15, "NZDJPY": 15
            },
            "session_bonuses": {
                "LONDON": 10, "OVERLAP": 8, "NEWYORK": 6, "ASIAN": 2
            },
            "risk_management": {
                "default_risk_percent": 0.03,
                "default_account_balance": 1000.0
            },
            "pattern_thresholds": {
                "LIQUIDITY_SWEEP_REVERSAL": {
                    "pip_sweep": 3.0, "min_conf": 75, "vol_gate": 1.3, "rejection_required": True
                },
                "ORDER_BLOCK_BOUNCE": {
                    "body_ratio": 0.6, "min_conf": 70, "vol_gate": 1.2, "zone_tolerance": 0.3
                },
                "FAIR_VALUE_GAP_FILL": {
                    "gap_size": 0.5, "min_conf": 65, "vol_gate": 1.1, "fill_ratio": 0.5
                },
                "VCB_BREAKOUT": {
                    "compression_ratio": 0.7, "min_conf": 70, "vol_gate": 1.5, "breakout_mult": 1.0
                },
                "SWEEP_RETURN": {
                    "wick_ratio": 0.7, "min_conf": 72, "vol_gate": 1.3, "sweep_pips": 2.0
                },
                "MOMENTUM_BURST": {
                    "breakout_pips": 1.0, "min_conf": 68, "vol_gate": 1.2, "momentum_mult": 1.0
                }
            }
        }
    
    def get_pip_sizes(self) -> Dict[str, float]:
        """Get pip sizes configuration"""
        return self.config.get("pip_sizes", self._get_default_config()["pip_sizes"])
    
    def get_min_stop_requirements(self) -> Dict[str, int]:
        """Get minimum stop requirements"""
        return self.config.get("min_stop_requirements", self._get_default_config()["min_stop_requirements"])
    
    def get_session_bonuses(self) -> Dict[str, int]:
        """Get session bonuses"""
        return self.config.get("session_bonuses", self._get_default_config()["session_bonuses"])
    
    def get_risk_management(self) -> Dict[str, float]:
        """Get risk management settings"""
        return self.config.get("risk_management", self._get_default_config()["risk_management"])
    
    def get_pattern_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Get pattern threshold configurations"""
        return self.config.get("pattern_thresholds", self._get_default_config()["pattern_thresholds"])
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.config = self._load_config()
        logger.info("🔄 Elite Guard configuration reloaded")

# Global instance
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """Get global config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader