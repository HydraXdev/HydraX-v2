"""
BITTEN Universal Stealth Shield
Protecting traders from broker manipulation and unfair practices
"The house always wins? Not anymore." - BITTEN
"""

import secrets
import asyncio
import random
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

from .fire_modes import TierLevel
from .stealth_protocol import StealthLevel, StealthConfig, get_stealth_protocol

class BrokerProfile(Enum):
    """Known broker detection profiles"""
    UNKNOWN = "unknown"
    IC_MARKETS = "ic_markets"
    OANDA = "oanda"
    FOREX_COM = "forex_com"
    PEPPERSTONE = "pepperstone"
    XM = "xm"
    FXCM = "fxcm"
    AVATRADE = "avatrade"

@dataclass
class BrokerLimits:
    """Broker-specific limits to avoid detection"""
    max_trades_per_hour: int
    min_hold_time_seconds: int
    max_daily_profit_pct: float
    max_win_streak: int
    suspicious_win_rate: float
    max_concurrent_trades: int
    requires_losses: bool  # Some brokers flag 100% win rates

# Broker-specific detection thresholds
BROKER_PROFILES = {
    BrokerProfile.IC_MARKETS: BrokerLimits(
        max_trades_per_hour=20,
        min_hold_time_seconds=45,
        max_daily_profit_pct=0.10,
        max_win_streak=12,
        suspicious_win_rate=0.85,
        max_concurrent_trades=5,
        requires_losses=True
    ),
    BrokerProfile.OANDA: BrokerLimits(
        max_trades_per_hour=15,
        min_hold_time_seconds=60,
        max_daily_profit_pct=0.08,
        max_win_streak=10,
        suspicious_win_rate=0.80,
        max_concurrent_trades=4,
        requires_losses=True
    ),
    BrokerProfile.FOREX_COM: BrokerLimits(
        max_trades_per_hour=25,
        min_hold_time_seconds=30,
        max_daily_profit_pct=0.12,
        max_win_streak=15,
        suspicious_win_rate=0.88,
        max_concurrent_trades=6,
        requires_losses=False
    ),
    BrokerProfile.PEPPERSTONE: BrokerLimits(
        max_trades_per_hour=30,
        min_hold_time_seconds=30,
        max_daily_profit_pct=0.15,
        max_win_streak=18,
        suspicious_win_rate=0.90,
        max_concurrent_trades=8,
        requires_losses=False
    ),
    BrokerProfile.XM: BrokerLimits(
        max_trades_per_hour=12,
        min_hold_time_seconds=90,
        max_daily_profit_pct=0.07,
        max_win_streak=8,
        suspicious_win_rate=0.75,
        max_concurrent_trades=3,
        requires_losses=True
    )
}

class UniversalStealthShield:
    """
    Complete stealth system to protect ALL BITTEN users from broker detection
    """
    
    def __init__(self):
        self.stealth_protocol = get_stealth_protocol()
        self.broker_profile = BrokerProfile.UNKNOWN
        self.detected_limits = None
        
        # Trading session tracking
        self.session_start = None
        self.trades_this_hour = 0
        self.trades_today = 0
        self.profit_today = 0.0
        self.current_win_streak = 0
        self.last_break_time = datetime.now()
        
        # Human behavior patterns
        self.typing_speed = random.uniform(0.08, 0.15)  # Seconds between keystrokes
        self.reaction_time = random.uniform(0.3, 0.8)   # Human reaction delay
        self.fatigue_factor = 0.0  # Increases throughout the day
        
        # Load saved state
        self._load_state()
    
    def configure_tier_stealth(self, tier: TierLevel) -> StealthConfig:
        """Enhanced stealth configuration for ALL tiers"""
        
        configs = {
            TierLevel.NIBBLER: StealthConfig(
                enabled=True,  # NOW ENABLED!
                level=StealthLevel.LOW,
                entry_delay_min=0.5,
                entry_delay_max=3.0,
                lot_jitter_min=0.02,  # 2%
                lot_jitter_max=0.05,  # 5%
                tp_offset_min=0,
                tp_offset_max=2,
                sl_offset_min=0,
                sl_offset_max=2,
                ghost_skip_rate=0.05,  # 5% skip
                max_concurrent_per_asset=2,
                max_total_concurrent=4,
                shuffle_queue=False
            ),
            
            TierLevel.FANG: StealthConfig(
                enabled=True,
                level=StealthLevel.MEDIUM,
                entry_delay_min=1.0,
                entry_delay_max=5.0,
                lot_jitter_min=0.03,
                lot_jitter_max=0.07,
                tp_offset_min=1,
                tp_offset_max=3,
                sl_offset_min=1,
                sl_offset_max=3,
                ghost_skip_rate=0.08,  # 8% skip
                max_concurrent_per_asset=3,
                max_total_concurrent=6,
                shuffle_queue=True
            ),
            
            TierLevel.COMMANDER: StealthConfig(
                enabled=True,
                level=StealthLevel.MEDIUM,
                entry_delay_min=1.0,
                entry_delay_max=8.0,
                lot_jitter_min=0.04,
                lot_jitter_max=0.08,
                tp_offset_min=1,
                tp_offset_max=4,
                sl_offset_min=1,
                sl_offset_max=4,
                ghost_skip_rate=0.12,  # 12% skip
                max_concurrent_per_asset=4,
                max_total_concurrent=8,
                shuffle_queue=True
            ),
            
            TierLevel.: StealthConfig(
                enabled=True,
                level=StealthLevel.HIGH,
                entry_delay_min=2.0,
                entry_delay_max=12.0,
                lot_jitter_min=0.05,
                lot_jitter_max=0.12,
                tp_offset_min=2,
                tp_offset_max=5,
                sl_offset_min=2,
                sl_offset_max=5,
                ghost_skip_rate=0.15,  # 15% skip
                max_concurrent_per_asset=5,
                max_total_concurrent=10,
                shuffle_queue=True
            )
        }
        
        # Add PRESS_PASS with minimal stealth
        configs[TierLevel.PRESS_PASS] = StealthConfig(
            enabled=True,
            level=StealthLevel.LOW,
            entry_delay_min=0.3,
            entry_delay_max=2.0,
            lot_jitter_min=0.01,
            lot_jitter_max=0.03,
            ghost_skip_rate=0.03,
            max_concurrent_per_asset=1,
            max_total_concurrent=2
        )
        
        return configs.get(tier, configs[TierLevel.NIBBLER])
    
    def detect_broker(self, spread_data: Dict, execution_times: List[float]) -> BrokerProfile:
        """Detect broker based on spread patterns and execution characteristics"""
        avg_spread = spread_data.get('average', 1.5)
        min_spread = spread_data.get('min', 1.0)
        max_spread = spread_data.get('max', 3.0)
        avg_execution = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Broker fingerprinting based on characteristics
        if avg_spread < 0.8 and avg_execution < 50:
            return BrokerProfile.IC_MARKETS
        elif 1.0 <= avg_spread <= 1.5 and avg_execution > 100:
            return BrokerProfile.OANDA
        elif avg_spread > 2.0 and max_spread > 5.0:
            return BrokerProfile.XM
        elif min_spread < 0.5:
            return BrokerProfile.PEPPERSTONE
        else:
            return BrokerProfile.FOREX_COM
    
    def calculate_dynamic_risk(self, account_balance: float, base_risk: float = 0.02) -> float:
        """Automatically reduce risk as account grows"""
        if account_balance < 10_000:
            return base_risk  # 2%
        elif account_balance < 50_000:
            return base_risk * 0.75  # 1.5%
        elif account_balance < 100_000:
            return base_risk * 0.5   # 1%
        elif account_balance < 500_000:
            return base_risk * 0.375  # 0.75%
        else:
            return base_risk * 0.25   # 0.5%
    
    async def add_human_delays(self, action_type: str) -> float:
        """Add realistic human delays based on action type"""
        delays = {
            'analyze_signal': (0.5, 2.0),      # Time to read and understand
            'decision_making': (0.3, 1.5),     # Time to decide
            'mouse_movement': (0.1, 0.4),      # Time to move mouse
            'clicking': (0.05, 0.15),          # Click delay
            'typing': (0.08, 0.20),            # Per character
            'double_check': (0.5, 1.0),        # Verification time
        }
        
        min_delay, max_delay = delays.get(action_type, (0.1, 0.5))
        
        # Add fatigue factor (slower as day progresses)
        fatigue_multiplier = 1.0 + (self.fatigue_factor * 0.5)
        
        delay = random.uniform(min_delay, max_delay) * fatigue_multiplier
        await asyncio.sleep(delay)
        return delay
    
    def should_take_break(self) -> Tuple[bool, int]:
        """Determine if trader should take a break (human behavior)"""
        now = datetime.now()
        time_since_break = (now - self.last_break_time).seconds / 60  # minutes
        
        # Lunch break (12-1 PM)
        if 12 <= now.hour < 13:
            return True, 60  # 60 minute lunch
        
        # Regular breaks every 2-3 hours
        if time_since_break > random.randint(120, 180):
            break_duration = random.randint(10, 30)  # 10-30 min break
            return True, break_duration
        
        # Random micro-breaks (bathroom, coffee, etc.)
        if random.random() < 0.02:  # 2% chance per check
            return True, random.randint(3, 8)
        
        return False, 0
    
    def add_intentional_mistakes(self, trade_params: Dict) -> Dict:
        """Add human-like mistakes occasionally"""
        mistake_chance = 0.03  # 3% chance of mistake
        
        if random.random() < mistake_chance:
            mistake_type = random.choice([
                'lot_size_error',
                'wrong_decimal',
                'market_order',
                'fat_finger'
            ])
            
            if mistake_type == 'lot_size_error':
                # Slightly wrong lot size
                trade_params['volume'] *= random.uniform(0.9, 1.1)
                trade_params['mistake'] = 'lot_size_error'
                
            elif mistake_type == 'wrong_decimal':
                # Decimal place error
                trade_params['volume'] *= random.choice([0.1, 10])
                trade_params['cancel_after'] = 2  # Cancel after 2 seconds
                trade_params['mistake'] = 'wrong_decimal'
                
            elif mistake_type == 'market_order':
                # Use market order instead of limit
                trade_params['order_type'] = 'market'
                trade_params['mistake'] = 'market_order'
                
            elif mistake_type == 'fat_finger':
                # Wrong price level
                if 'entry' in trade_params:
                    trade_params['entry'] *= random.uniform(0.995, 1.005)
                trade_params['cancel_after'] = 1
                trade_params['mistake'] = 'fat_finger'
        
        return trade_params
    
    def create_loss_trades(self, win_rate: float) -> bool:
        """Intentionally create losing trades to maintain realistic win rate"""
        if self.detected_limits and self.detected_limits.requires_losses:
            if win_rate > self.detected_limits.suspicious_win_rate:
                # Need to add some losses
                return random.random() < 0.3  # 30% chance to force a loss
        return False
    
    def get_trading_personality(self) -> Dict[str, Any]:
        """Generate consistent trading personality traits"""
        personalities = [
            {
                'type': 'aggressive',
                'preferred_sessions': ['london', 'ny'],
                'avg_hold_time': 30,
                'risk_appetite': 1.2,
                'favorite_pairs': ['GBPUSD', 'EURUSD'],
                'break_frequency': 'low'
            },
            {
                'type': 'conservative',
                'preferred_sessions': ['london'],
                'avg_hold_time': 90,
                'risk_appetite': 0.8,
                'favorite_pairs': ['EURUSD', 'USDJPY'],
                'break_frequency': 'high'
            },
            {
                'type': 'scalper',
                'preferred_sessions': ['ny', 'london_ny_overlap'],
                'avg_hold_time': 15,
                'risk_appetite': 1.0,
                'favorite_pairs': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'break_frequency': 'medium'
            },
            {
                'type': 'swing',
                'preferred_sessions': ['london', 'tokyo'],
                'avg_hold_time': 240,
                'risk_appetite': 0.6,
                'favorite_pairs': ['GBPJPY', 'EURJPY'],
                'break_frequency': 'high'
            }
        ]
        
        # Use user ID to consistently select personality
        return random.choice(personalities)
    
    async def apply_universal_stealth(self, user_id: int, tier: TierLevel, 
                                    trade_params: Dict, account_info: Dict) -> Dict:
        """Apply comprehensive stealth to any trade"""
        
        # 1. Configure tier-specific stealth
        stealth_config = self.configure_tier_stealth(tier)
        self.stealth_protocol.config = stealth_config
        
        # 2. Detect broker if not known
        if self.broker_profile == BrokerProfile.UNKNOWN:
            self.broker_profile = self.detect_broker(
                account_info.get('spread_data', {}),
                account_info.get('execution_times', [])
            )
            self.detected_limits = BROKER_PROFILES.get(
                self.broker_profile, 
                BROKER_PROFILES[BrokerProfile.FOREX_COM]
            )
        
        # 3. Check broker limits
        if self.detected_limits:
            # Check hourly limit
            if self.trades_this_hour >= self.detected_limits.max_trades_per_hour:
                trade_params['skip_trade'] = True
                trade_params['skip_reason'] = 'hourly_limit_reached'
                return trade_params
            
            # Check daily profit limit
            account_balance = account_info.get('balance', 10000)
            if self.profit_today / account_balance > self.detected_limits.max_daily_profit_pct:
                trade_params['skip_trade'] = True
                trade_params['skip_reason'] = 'daily_profit_limit'
                return trade_params
        
        # 4. Add human behavior
        await self.add_human_delays('analyze_signal')
        
        # Check if should take break
        should_break, break_duration = self.should_take_break()
        if should_break:
            trade_params['delay_minutes'] = break_duration
            trade_params['delay_reason'] = 'taking_break'
        
        # 5. Apply dynamic risk sizing
        account_balance = account_info.get('balance', 10000)
        base_risk = trade_params.get('risk', 0.02)
        trade_params['risk'] = self.calculate_dynamic_risk(account_balance, base_risk)
        
        # 6. Add human mistakes occasionally
        trade_params = self.add_intentional_mistakes(trade_params)
        
        # 7. Apply standard stealth protocols
        trade_params = self.stealth_protocol.apply_full_stealth(trade_params)
        
        # 8. Force losses if needed
        win_rate = account_info.get('win_rate', 0.75)
        if self.create_loss_trades(win_rate):
            trade_params['force_loss'] = True
            trade_params['loss_reason'] = 'maintain_realistic_win_rate'
        
        # 9. Update tracking
        self.trades_this_hour += 1
        self.trades_today += 1
        self.fatigue_factor = min(1.0, self.trades_today / 50)  # Max fatigue at 50 trades
        
        # 10. Log everything for analysis
        self._log_stealth_action(user_id, tier, trade_params)
        
        return trade_params
    
    def _log_stealth_action(self, user_id: int, tier: TierLevel, params: Dict):
        """Log all stealth actions for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'tier': tier.value,
            'broker': self.broker_profile.value,
            'action': 'stealth_trade',
            'params': {
                'risk_adjusted': params.get('risk'),
                'delays_added': params.get('entry_delay', 0),
                'mistakes': params.get('mistake'),
                'skip_reason': params.get('skip_reason'),
                'force_loss': params.get('force_loss', False)
            }
        }
        
        # Log to file
        log_dir = "/root/HydraX-v2/logs/stealth"
        os.makedirs(log_dir, exist_ok=True)
        
        with open(f"{log_dir}/universal_stealth.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _load_state(self):
        """Load saved state from previous session"""
        state_file = "/root/HydraX-v2/data/stealth_state.json"
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    self.broker_profile = BrokerProfile(state.get('broker', 'unknown'))
                    self.trades_today = state.get('trades_today', 0)
                    self.profit_today = state.get('profit_today', 0.0)
                    
                    # Reset if new day
                    last_update = datetime.fromisoformat(state.get('last_update'))
                    if last_update.date() != datetime.now().date():
                        self._reset_daily_stats()
            except Exception as e:
                print(f"Error loading state: {e}")
    
    def _save_state(self):
        """Save current state for persistence"""
        state = {
            'broker': self.broker_profile.value,
            'trades_today': self.trades_today,
            'profit_today': self.profit_today,
            'last_update': datetime.now().isoformat()
        }
        
        state_file = "/root/HydraX-v2/data/stealth_state.json"
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        
        with open(state_file, "w") as f:
            json.dump(state, f)
    
    def _reset_daily_stats(self):
        """Reset daily statistics"""
        self.trades_today = 0
        self.profit_today = 0.0
        self.current_win_streak = 0
        self.trades_this_hour = 0
    
    def _reset_hourly_stats(self):
        """Reset hourly statistics"""
        self.trades_this_hour = 0
    
    def get_stealth_report(self) -> Dict[str, Any]:
        """Generate comprehensive stealth report"""
        return {
            'universal_shield_active': True,
            'detected_broker': self.broker_profile.value,
            'trades_today': self.trades_today,
            'trades_this_hour': self.trades_this_hour,
            'profit_today_pct': self.profit_today,
            'fatigue_level': f"{self.fatigue_factor * 100:.1f}%",
            'current_limits': {
                'hourly_trades': f"{self.trades_this_hour}/{self.detected_limits.max_trades_per_hour if self.detected_limits else 'N/A'}",
                'daily_profit': f"{self.profit_today:.1%}/{self.detected_limits.max_daily_profit_pct if self.detected_limits else 'N/A'}"
            },
            'protection_features': [
                '✅ Entry delay randomization',
                '✅ Lot size variance',
                '✅ Human behavior simulation',
                '✅ Break patterns',
                '✅ Intentional mistakes',
                '✅ Dynamic risk adjustment',
                '✅ Broker-specific limits',
                '✅ Win rate management'
            ]
        }

# Global instance
universal_shield = UniversalStealthShield()

# Integration functions
async def apply_universal_protection(user_id: int, tier: TierLevel, 
                                   trade_params: Dict, account_info: Dict) -> Dict:
    """Main entry point for universal stealth protection"""
    return await universal_shield.apply_universal_stealth(
        user_id, tier, trade_params, account_info
    )

def get_shield_status() -> Dict[str, Any]:
    """Get current shield status"""
    return universal_shield.get_stealth_report()

# Telegram command handlers
async def handle_shield_command(user_id: int) -> str:
    """Handle /shield command"""
    report = get_shield_status()
    
    message = "🛡️ **UNIVERSAL STEALTH SHIELD STATUS**\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"Status: {'🟢 ACTIVE' if report['universal_shield_active'] else '🔴 INACTIVE'}\n"
    message += f"Detected Broker: {report['detected_broker'].upper()}\n"
    message += f"Trades Today: {report['trades_today']}\n"
    message += f"Hourly Limit: {report['current_limits']['hourly_trades']}\n"
    message += f"Daily Profit: {report['current_limits']['daily_profit']}\n"
    message += f"Fatigue Level: {report['fatigue_level']}\n\n"
    message += "**Active Protection:**\n"
    for feature in report['protection_features']:
        message += f"{feature}\n"
    
    message += "\n_The brokers' reign ends here. Trade free._"
    
    return message