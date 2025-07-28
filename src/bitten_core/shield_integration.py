"""
Shield Integration Module
Connects Universal Stealth Shield with BITTEN's core systems
"""

import asyncio
from typing import Dict, Optional, Any
from datetime import datetime

from .universal_stealth_shield import (
    universal_shield, 
    apply_universal_protection,
    get_shield_status
)
from .fire_modes import TierLevel, FireMode
from .bitten_core import bitten
from .advanced_signal_integration import advanced_integration

class ShieldIntegration:
    """
    Master integration class for Universal Stealth Shield
    """
    
    def __init__(self):
        self.shield = universal_shield
        self.enabled = True
        self.protection_stats = {
            'trades_protected': 0,
            'broker_limits_avoided': 0,
            'patterns_broken': 0,
            'losses_injected': 0
        }
    
    async def protect_trade(self, user_id: int, tier: TierLevel, 
                          trade_params: Dict, account_info: Dict) -> Dict:
        """Apply universal protection to any trade"""
        if not self.enabled:
            return trade_params
        
        # Get protected parameters
        protected_params = await apply_universal_protection(
            user_id, tier, trade_params, account_info
        )
        
        # Track protection stats
        if protected_params.get('skip_trade'):
            self.protection_stats['broker_limits_avoided'] += 1
        if protected_params.get('entry_delay', 0) > 0:
            self.protection_stats['patterns_broken'] += 1
        if protected_params.get('force_loss'):
            self.protection_stats['losses_injected'] += 1
        
        self.protection_stats['trades_protected'] += 1
        
        return protected_params
    
    async def hook_into_fire_router(self):
        """Hook shield into the fire router"""
        # This would modify fire_router.py to call protect_trade
        # before executing any trade
        pass
    
    async def hook_into_signal_flow(self):
        """Hook shield into signal flow"""
        # This would modify signal flow to apply protection
        # to all generated signals
        pass
    
    def get_protection_report(self, user_id: int) -> Dict[str, Any]:
        """Get user-specific protection report"""
        shield_status = get_shield_status()
        
        return {
            'shield_active': self.enabled,
            'broker_detected': shield_status['detected_broker'],
            'protection_level': 'MAXIMUM',
            'stats': self.protection_stats,
            'features_active': shield_status['protection_features'],
            'current_limits': shield_status['current_limits']
        }

# Global shield integration instance
shield_integration = ShieldIntegration()

# Monkey patch the fire router to add protection
def patch_fire_router():
    """Patch fire router to add shield protection"""
    from . import fire_router
    
    # Store original execute method
    original_execute = fire_router.FireRouter.execute_trade
    
    async def protected_execute(self, user_id: int, tier: TierLevel, 
                               fire_mode: FireMode, trade_params: Dict) -> Dict:
        """Protected trade execution"""
        # Get REAL account info - NO FAKE DATA
        try:
            from .real_account_balance import get_user_real_balance
            real_balance = get_user_real_balance(user_id)
            if not real_balance:
                raise Exception(f"CRITICAL: Cannot get real balance for user {user_id}")
            
            account_info = {
                'balance': real_balance,  # REAL balance from broker
                'win_rate': 0.75,  # TODO: Get real win rate from statistics
                'spread_data': {'average': 1.5, 'min': 1.0, 'max': 3.0},  # TODO: Get real spread data
                'execution_times': [45, 52, 48, 55]  # TODO: Get real execution data
            }
        except Exception as e:
            raise Exception(f"CRITICAL: Shield integration requires real account data - {e}")
        
        # Apply shield protection
        protected_params = await shield_integration.protect_trade(
            user_id, tier, trade_params, account_info
        )
        
        # Check if trade should be skipped
        if protected_params.get('skip_trade'):
            return {
                'success': False,
                'reason': protected_params.get('skip_reason', 'shield_protection'),
                'message': '🛡️ Trade blocked by Universal Shield for your protection'
            }
        
        # Execute with protection
        return await original_execute(self, user_id, tier, fire_mode, protected_params)
    
    # Replace with protected version
    fire_router.FireRouter.execute_trade = protected_execute

# Telegram command handlers
async def handle_shield_status(user_id: int, tier: TierLevel) -> str:
    """Handle /shield command"""
    report = shield_integration.get_protection_report(user_id)
    
    message = "🛡️ **UNIVERSAL STEALTH SHIELD**\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    message += f"**Status**: {'🟢 ACTIVE' if report['shield_active'] else '🔴 INACTIVE'}\n"
    message += f"**Your Tier**: {tier.value.upper()}\n"
    message += f"**Broker Detected**: {report['broker_detected'].upper()}\n"
    message += f"**Protection Level**: {report['protection_level']}\n\n"
    
    message += "**Protection Stats**:\n"
    message += f"• Trades Protected: {report['stats']['trades_protected']}\n"
    message += f"• Broker Limits Avoided: {report['stats']['broker_limits_avoided']}\n"
    message += f"• Patterns Broken: {report['stats']['patterns_broken']}\n"
    message += f"• Strategic Losses: {report['stats']['losses_injected']}\n\n"
    
    message += "**Active Features**:\n"
    for feature in report['features_active'][:5]:  # Show first 5
        message += f"{feature}\n"
    
    message += "\n_\"The house always wins? Not anymore.\"_\n"
    message += "_Power to the traders. 🚀_"
    
    return message

async def handle_shield_toggle(user_id: int, tier: TierLevel, enabled: bool) -> str:
    """Handle /shield on/off command (only)"""
    if tier != TierLevel.:
        return "⚠️ Shield control is -exclusive. Shield is always ON for your protection."
    
    shield_integration.enabled = enabled
    
    if enabled:
        return "🛡️ Universal Shield ACTIVATED. Maximum protection engaged."
    else:
        return "⚠️ Universal Shield DEACTIVATED. Trade at your own risk!"

# Auto-patch on import
patch_fire_router()

# Configuration for CLAUDE.md
SHIELD_CONFIG = {
    'enabled_by_default': True,
    'protects_all_tiers': True,
    'features': {
        'entry_delays': 'Randomized 0.5-12 second delays',
        'lot_variance': '2-15% size variation',
        'tp_sl_offset': '0-5 pip randomization',
        'ghost_trades': '5-15% strategic skips',
        'human_behavior': 'Breaks, mistakes, fatigue',
        'broker_detection': 'Automatic limit adjustment',
        'dynamic_risk': 'Auto-reduction for large accounts',
        'forced_losses': 'Maintains realistic win rates'
    },
    'broker_profiles': [
        'IC Markets', 'OANDA', 'Forex.com', 
        'Pepperstone', 'XM', 'FXCM', 'AvaTrade'
    ]
}