# stealth_integration.py
# Integration of Stealth Protocol with BITTEN Fire Modes

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio

from .fire_modes import FireMode, TierLevel, TIER_CONFIGS
from .stealth_protocol import (
    StealthProtocol, StealthLevel, StealthConfig, 
    get_stealth_protocol
)
from .trade_manager import TradeManager
from .signal_alerts import send_signal_alert

class StealthFireModeIntegration:
    """Integrates stealth protocol with fire modes"""
    
    def __init__(self):
        self.stealth = get_stealth_protocol()
        self.fire_mode_stealth_levels = {
            FireMode.SINGLE_SHOT: StealthLevel.LOW,
            FireMode.CHAINGUN: StealthLevel.MEDIUM,
            FireMode.AUTO_FIRE: StealthLevel.HIGH,
            FireMode.SEMI_AUTO: StealthLevel.MEDIUM,
            FireMode.STEALTH: StealthLevel.GHOST,
            FireMode.MIDNIGHT_HAMMER: StealthLevel.OFF  # Community event, no stealth
        }
        
    def configure_stealth_for_tier(self, tier: TierLevel) -> StealthConfig:
        """Configure stealth based on subscription tier"""
        config = StealthConfig()
        
        if tier == TierLevel.NIBBLER:
            # Nibbler: NOW HAS STEALTH PROTECTION!
            config.enabled = True
            config.level = StealthLevel.LOW
            config.entry_delay_max = 3.0  # Max 3 seconds
            config.lot_jitter_max = 0.05  # Max 5% jitter
            config.tp_offset_max = 2      # Max 2 pip offset
            config.ghost_skip_rate = 0.05  # 5% skip rate
            
        elif tier == TierLevel.FANG:
            # Fang: Basic stealth only with CHAINGUN
            config.enabled = True
            config.level = StealthLevel.LOW
            config.entry_delay_max = 5.0  # Max 5 seconds
            config.lot_jitter_max = 0.05  # Max 5% jitter
            
        elif tier == TierLevel.COMMANDER:
            # Commander: Medium stealth capabilities
            config.enabled = True
            config.level = StealthLevel.MEDIUM
            config.entry_delay_max = 8.0
            config.lot_jitter_max = 0.07
            
        elif tier == TierLevel.APEX:
            # Apex: Full stealth capabilities
            config.enabled = True
            config.level = StealthLevel.HIGH
            config.entry_delay_max = 12.0
            config.lot_jitter_max = 0.10
            config.ghost_skip_rate = 0.20  # Higher skip rate
            
        return config
        
    async def execute_stealth_trade(self, user_id: int, tier: TierLevel, 
                                  fire_mode: FireMode, trade_params: Dict) -> Dict:
        """Execute a trade with appropriate stealth protocols"""
        
        # Configure stealth for tier
        stealth_config = self.configure_stealth_for_tier(tier)
        self.stealth.config = stealth_config
        
        # Set stealth level based on fire mode
        if fire_mode in self.fire_mode_stealth_levels:
            self.stealth.set_level(self.fire_mode_stealth_levels[fire_mode])
            
        # Special handling for STEALTH mode (APEX only)
        if fire_mode == FireMode.STEALTH:
            if tier != TierLevel.APEX:
                return {
                    'success': False,
                    'error': 'STEALTH mode is APEX-exclusive'
                }
            # Use maximum stealth
            self.stealth.set_level(StealthLevel.GHOST)
            
        # Apply stealth protocols
        stealth_params = self.stealth.apply_full_stealth(trade_params)
        
        # Check if trade was skipped
        if stealth_params.get('skip_trade'):
            reason = stealth_params.get('skip_reason', 'ghost_skip')
            await self._notify_skip(user_id, reason, trade_params)
            return {
                'success': True,
                'skipped': True,
                'reason': reason
            }
            
        # Apply entry delay if specified
        if 'entry_delay' in stealth_params and stealth_params['entry_delay'] > 0:
            await asyncio.sleep(stealth_params['entry_delay'])
            
        # Execute the trade
        result = await self._execute_trade(stealth_params)
        
        # Track for volume management
        if result.get('success'):
            asset = stealth_params.get('symbol')
            trade_id = result.get('trade_id')
            if asset and trade_id:
                self.stealth.active_trades.setdefault(asset, []).append(trade_id)
                
        return result
        
    async def execute_stealth_batch(self, user_id: int, tier: TierLevel,
                                  fire_mode: FireMode, trades: List[Dict]) -> List[Dict]:
        """Execute multiple trades with stealth shuffle"""
        
        # Configure stealth
        stealth_config = self.configure_stealth_for_tier(tier)
        self.stealth.config = stealth_config
        
        # Apply execution shuffle
        shuffled_trades = self.stealth.execution_shuffle(trades)
        
        results = []
        for i, trade in enumerate(shuffled_trades):
            # Apply shuffle delay if specified
            if i > 0 and 'shuffle_delay' in trade:
                await asyncio.sleep(trade['shuffle_delay'])
                
            # Execute with stealth
            result = await self.execute_stealth_trade(
                user_id, tier, fire_mode, trade
            )
            results.append(result)
            
        return results
        
    async def _execute_trade(self, trade_params: Dict) -> Dict:
        """Execute the actual trade (placeholder for real implementation)"""
        # This would connect to your actual trade execution system
        # For now, returning a mock result
        return {
            'success': True,
            'trade_id': f"STEALTH_{datetime.now().timestamp()}",
            'symbol': trade_params.get('symbol'),
            'volume': trade_params.get('volume'),
            'entry_price': trade_params.get('entry_price'),
            'tp': trade_params.get('tp'),
            'sl': trade_params.get('sl'),
            'stealth_applied': True
        }
        
    async def _notify_skip(self, user_id: int, reason: str, trade_params: Dict):
        """Notify user that trade was skipped"""
        message = f"⚡ STEALTH PROTOCOL: Trade skipped\n"
        message += f"Reason: {reason}\n"
        message += f"Pair: {trade_params.get('symbol', 'N/A')}"
        
        # Send notification (would use your actual notification system)
        await send_signal_alert(user_id, message)
        
    def get_stealth_report(self, user_id: int) -> Dict:
        """Generate stealth protocol report for user"""
        stats = self.stealth.get_stealth_stats()
        
        report = {
            'stealth_enabled': stats['enabled'],
            'current_level': stats['level'],
            'active_trades': stats['total_active'],
            'actions_today': len([
                a for a in stats['recent_actions']
                if datetime.fromisoformat(a['timestamp']).date() == datetime.now().date()
            ]),
            'last_action': stats['recent_actions'][-1] if stats['recent_actions'] else None
        }
        
        return report

class StealthModeCommands:
    """Telegram commands for stealth mode management"""
    
    def __init__(self):
        self.integration = StealthFireModeIntegration()
        
    async def handle_stealth_status(self, user_id: int, tier: TierLevel) -> str:
        """Handle /stealth_status command"""
        if tier not in [TierLevel.COMMANDER, TierLevel.APEX]:
            return "⚠️ Stealth protocols are available for COMMANDER and APEX tiers only."
            
        report = self.integration.get_stealth_report(user_id)
        
        message = "🥷 STEALTH PROTOCOL STATUS\n"
        message += "━━━━━━━━━━━━━━━━━━━\n"
        message += f"Status: {'ACTIVE' if report['stealth_enabled'] else 'INACTIVE'}\n"
        message += f"Level: {report['current_level'].upper()}\n"
        message += f"Active Trades: {report['active_trades']}\n"
        message += f"Actions Today: {report['actions_today']}\n"
        
        if report['last_action']:
            message += f"\nLast Action: {report['last_action']['type']}\n"
            message += f"Time: {report['last_action']['timestamp']}\n"
            
        return message
        
    async def handle_stealth_level(self, user_id: int, tier: TierLevel, 
                                 level: str) -> str:
        """Handle /stealth_level command"""
        if tier != TierLevel.APEX:
            return "⚠️ Manual stealth level control is APEX-exclusive."
            
        try:
            stealth_level = StealthLevel(level.lower())
        except ValueError:
            levels = [l.value for l in StealthLevel]
            return f"❌ Invalid level. Choose from: {', '.join(levels)}"
            
        self.integration.stealth.set_level(stealth_level)
        
        return f"✅ Stealth level set to: {stealth_level.value.upper()}"
        
    async def handle_stealth_logs(self, user_id: int, tier: TierLevel) -> str:
        """Handle /stealth_logs command"""
        if tier not in [TierLevel.COMMANDER, TierLevel.APEX]:
            return "⚠️ Stealth logs are available for COMMANDER and APEX tiers only."
            
        # Get recent logs
        logs = self.integration.stealth.export_logs()[-5:]  # Last 5 actions
        
        if not logs:
            return "📊 No stealth actions logged yet."
            
        message = "📊 RECENT STEALTH ACTIONS\n"
        message += "━━━━━━━━━━━━━━━━━━━\n"
        
        for log in logs:
            message += f"\n{log['action_type'].upper()}\n"
            message += f"Time: {log['timestamp']}\n"
            message += f"Level: {log['level']}\n"
            
            if log['action_type'] == 'lot_size_jitter':
                message += f"Original: {log['original']}\n"
                message += f"Modified: {log['modified']}\n"
            elif log['action_type'] == 'entry_delay':
                message += f"Delay: {log['modified']:.1f}s\n"
                
        return message

# Example integration with fire router
async def apply_stealth_to_fire_command(user_id: int, tier: TierLevel,
                                      fire_mode: FireMode, trade_params: Dict) -> Dict:
    """Apply stealth protocols when firing trades"""
    integration = StealthFireModeIntegration()
    
    # Check if stealth should be applied
    tier_config = TIER_CONFIGS.get(tier)
    if not tier_config:
        return {'success': False, 'error': 'Invalid tier'}
        
    # Apply stealth based on tier and mode
    if fire_mode == FireMode.STEALTH and not tier_config.has_stealth:
        return {'success': False, 'error': 'STEALTH mode not available for your tier'}
        
    # Execute with stealth
    result = await integration.execute_stealth_trade(
        user_id, tier, fire_mode, trade_params
    )
    
    return result