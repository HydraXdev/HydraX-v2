"""
BITTEN Risk Management System v5.0 - Engine Optimized
Ultra-aggressive risk parameters for v5.0 (40+ signals/day @ 89% WR)
Enhanced position sizing and advanced trade management for maximum extraction
"""

import math
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta, time
import json

# Import the enhanced risk controller
from .risk_controller import get_risk_controller, TierLevel as RiskTierLevel, RiskMode as RiskControlMode

logger = logging.getLogger(__name__)

class v5RiskMode(Enum):
    """v5.0 Risk calculation modes"""
    CONSERVATIVE = "conservative"    # 0.5% risk per trade
    STANDARD = "standard"           # 1.0% risk per trade (v5.0 default)
    AGGRESSIVE = "aggressive"       # 1.5% risk per trade
    ULTRA = "ultra"                # 2.0% risk per trade
    _BEAST = "apex_beast"      # 3.0% risk per trade (tier only)

class v5SignalType(Enum):
    """v5.0 Signal types with optimized risk"""
    M1_RAID = "m1_raid"            # M1 ultra-fast, lower risk
    M3_RAID = "m3_raid"            # M3 primary signal type
    M5_ENHANCED = "m5_enhanced"     # M5 enhanced patterns
    M15_SNIPER = "m15_sniper"      # M15 high-quality snipers
    MEGA_CONFLUENCE = "mega_confluence"  # 2+ pattern confluence
    ULTRA_CONFLUENCE = "ultra_confluence" # 4+ pattern confluence

class v5TradeManagement(Enum):
    """v5.0 Enhanced trade management features"""
    # Standard features (all tiers)
    BASIC_SL_TP = "basic_sl_tp"                    # XP: 0
    BREAKEVEN = "breakeven"                        # XP: 100
    BREAKEVEN_PLUS = "breakeven_plus"             # XP: 500
    TRAILING_STOP = "trailing_stop"                # XP: 1000
    
    # Advanced features (COMMANDER+)
    PARTIAL_CLOSE = "partial_close"                # XP: 2000
    RUNNER_MODE = "runner_mode"                    # XP: 5000
    DYNAMIC_TRAIL = "dynamic_trail"                # XP: 10000
    
    # v5.0 exclusive features (only)
    CONFLUENCE_SCALING = "confluence_scaling"      # XP: 15000
    SESSION_BOOST_MANAGEMENT = "session_boost"     # XP: 20000
    ULTRA_VOLUME_MODE = "ultra_volume"            # XP: 30000
    _BEAST_MODE = "apex_beast_mode"           # XP: 50000

class v5TradingState(Enum):
    """v5.0 Enhanced trading states"""
    NORMAL = "normal"
    TILT_WARNING = "tilt_warning"
    TILT_LOCKOUT = "tilt_lockout"
    MEDIC_MODE = "medic_mode"
    
    # v5.0 Enhanced states
    ULTRA_VOLUME_ACTIVE = "ultra_volume_active"   # 40+ signals/day mode
    SESSION_BOOST_ACTIVE = "session_boost"        # OVERLAP 3x boost active
    CONFLUENCE_HUNTER = "confluence_hunter"       # Hunting for confluence signals
    _BEAST_UNLEASHED = "apex_beast"          # Maximum extraction mode

@dataclass
class v5RiskParameters:
    """v5.0 Risk parameters optimized for ultra-aggressive trading"""
    
    # Base risk settings (optimized for v5.0 performance)
    base_risk_percent: float = 1.0         # 1% base risk (up from 0.5%)
    max_risk_percent: float = 3.0          # 3% max risk for BEAST mode
    min_risk_percent: float = 0.3          # 0.3% minimum risk
    
    # v5.0 Signal volume management
    max_concurrent_pairs: int = 8          # Max 8 pairs (up from 5)
    max_signals_per_hour: int = 15         # Max 15 signals/hour
    max_signals_per_day: int = 200         # Max 200 signals/day
    
    # Emergency stops
    emergency_stop_drawdown: float = 10.0  # 10% emergency stop
    daily_loss_limit: float = 7.0         # 7% daily loss limit
    tilt_detection_threshold: float = 5.0  # 5% tilt threshold
    
    # Correlation limits
    max_pair_correlation: float = 0.7      # 70% max correlation
    max_usd_exposure: float = 60.0         # 60% max USD exposure
    max_eur_exposure: float = 40.0         # 40% max EUR exposure
    max_gbp_exposure: float = 30.0         # 30% max GBP exposure
    
    # v5.0 Session-based risk adjustments
    session_risk_multipliers: Dict[str, float] = field(default_factory=lambda: {
        'ASIAN': 0.9,      # 90% during Asian session
        'LONDON': 1.1,     # 110% during London session
        'NY': 1.0,         # 100% during NY session
        'OVERLAP': 1.3     # 130% during OVERLAP (3x boost session)
    })
    
    # Signal type risk multipliers
    signal_risk_multipliers: Dict[str, float] = field(default_factory=lambda: {
        'M1_RAID': 0.7,           # 70% for M1 signals (faster, lower risk)
        'M3_RAID': 1.0,           # 100% for M3 signals (primary)
        'M5_ENHANCED': 1.1,       # 110% for M5 signals
        'M15_SNIPER': 1.3,        # 130% for M15 snipers
        'MEGA_CONFLUENCE': 1.4,   # 140% for 2+ confluence
        'ULTRA_CONFLUENCE': 1.6   # 160% for 4+ confluence
    })
    
    # TCS-based risk scaling (optimized for v5.0 lower TCS)
    tcs_risk_multipliers: Dict[str, float] = field(default_factory=lambda: {
        '90+': 1.5,    # 150% for TCS 90+
        '80+': 1.3,    # 130% for TCS 80-89
        '70+': 1.2,    # 120% for TCS 70-79
        '60+': 1.1,    # 110% for TCS 60-69
        '50+': 1.0,    # 100% for TCS 50-59
        '40+': 0.9,    # 90% for TCS 40-49 (v5.0 minimum)
        '35+': 0.8     # 80% for TCS 35-39 (M3 minimum)
    })

class v5RiskManager:
    """v5.0 Risk Manager - Optimized for ultra-aggressive trading"""
    
    def __init__(self, tier: str = risk_mode: v5RiskMode = v5RiskMode.STANDARD):
        self.tier = tier
        self.risk_mode = risk_mode
        self.params = v5RiskParameters()
        self.current_state = v5TradingState.NORMAL
        
        # v5.0 Enhanced tracking
        self.daily_signals = 0
        self.hourly_signals = 0
        self.active_pairs = set()
        self.session_signals = {'ASIAN': 0, 'LONDON': 0, 'NY': 0, 'OVERLAP': 0}
        self.confluence_signals = 0
        
        # Performance tracking
        self.daily_pips = 0.0
        self.win_rate = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        logger.info(f"v5.0 Risk Manager initialized - Tier: {tier}, Mode: {risk_mode.value}")
    
    def calculate_position_size(self, signal: Dict, account_balance: float, 
                              current_session: str = "NORMAL") -> float:
        """Calculate optimal position size for v5.0 signals"""
        try:
            # Get base risk percentage
            base_risk = self._get_base_risk_percent()
            
            # Extract signal parameters
            pair = signal.get('symbol', 'EURUSD')
            tcs = signal.get('tcs', 50)
            signal_type = signal.get('pattern', 'M3_RAID')
            timeframe = signal.get('timeframe', 'M3')
            confluence_count = signal.get('confluence_count', 1)
            sl_pips = signal.get('stop_loss', 10)
            
            # Apply session multiplier
            session_mult = self.params.session_risk_multipliers.get(current_session, 1.0)
            adjusted_risk = base_risk * session_mult
            
            # Apply signal type multiplier
            signal_mult = self._get_signal_risk_multiplier(signal_type, timeframe)
            adjusted_risk *= signal_mult
            
            # Apply TCS-based multiplier
            tcs_mult = self._get_tcs_risk_multiplier(tcs)
            adjusted_risk *= tcs_mult
            
            # Apply confluence bonus
            if confluence_count >= 4:
                adjusted_risk *= 1.6  # ULTRA confluence
            elif confluence_count >= 2:
                adjusted_risk *= 1.4  # MEGA confluence
            
            # Tier-based adjustments
            if self.tier == :
                adjusted_risk *= 1.2  # 20% bonus
            elif self.tier == "COMMANDER":
                adjusted_risk *= 1.1  # 10% COMMANDER bonus
            
            # Apply risk mode multiplier
            mode_multipliers = {
                v5RiskMode.CONSERVATIVE: 0.5v5RiskMode.STANDARD: 1.0v5RiskMode.AGGRESSIVE: 1.5v5RiskMode.ULTRA: 2.0v5RiskMode._BEAST: 3.0
            }
            adjusted_risk *= mode_multipliers.get(self.risk_mode, 1.0)
            
            # Cap at maximum risk
            adjusted_risk = min(adjusted_risk, self.params.max_risk_percent)
            adjusted_risk = max(adjusted_risk, self.params.min_risk_percent)
            
            # Calculate position size in lots
            risk_amount = account_balance * (adjusted_risk / 100)
            
            # Convert to lot size (simplified calculation)
            pip_value = 10 if 'JPY' in pair else 1  # Approximate pip value
            lot_size = risk_amount / (sl_pips * pip_value)
            
            # Apply broker constraints (example values)
            min_lot = 0.01
            max_lot = min(10.0, account_balance * 0.1 / 1000)  # Max based on account
            lot_step = 0.01
            
            # Round to step and apply limits
            lot_size = round(lot_size / lot_step) * lot_step
            lot_size = max(min_lot, min(lot_size, max_lot))
            
            logger.info(f"Position calculated: {pair} - {lot_size} lots "
                       f"(Risk: {adjusted_risk:.1f}%, TCS: {tcs}, Session: {current_session})")
            
            return lot_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01  # Minimum fallback
    
    def check_signal_limits(self, current_session: str = "NORMAL") -> bool:
        """Check if we can accept more signals (v5.0 volume management)"""
        
        # Daily limit check
        if self.daily_signals >= self.params.max_signals_per_day:
            logger.warning(f"Daily signal limit reached: {self.daily_signals}")
            return False
        
        # Hourly limit check
        if self.hourly_signals >= self.params.max_signals_per_hour:
            logger.warning(f"Hourly signal limit reached: {self.hourly_signals}")
            return False
        
        # Concurrent pairs limit
        if len(self.active_pairs) >= self.params.max_concurrent_pairs:
            logger.warning(f"Max concurrent pairs reached: {len(self.active_pairs)}")
            return False
        
        # Session-specific limits
        session_limits = {
            'ASIAN': 50,      # 50 max in Asian session
            'LONDON': 60,     # 60 max in London session
            'NY': 50,         # 50 max in NY session
            'OVERLAP': 80     # 80 max in OVERLAP session (3x boost)
        }
        
        session_count = self.session_signals.get(current_session, 0)
        session_limit = session_limits.get(current_session, 40)
        
        if session_count >= session_limit:
            logger.warning(f"Session {current_session} limit reached: {session_count}")
            return False
        
        return True
    
    def update_signal_count(self, signal: Dict, current_session: str = "NORMAL"):
        """Update signal counters for v5.0 tracking"""
        self.daily_signals += 1
        self.hourly_signals += 1
        self.session_signals[current_session] = self.session_signals.get(current_session, 0) + 1
        
        pair = signal.get('symbol', 'EURUSD')
        self.active_pairs.add(pair)
        
        # Track confluence signals
        if signal.get('confluence_count', 1) > 1:
            self.confluence_signals += 1
        
        # Update trading state based on volume
        if self.daily_signals >= 150:
            self.current_state = v5TradingState.ULTRA_VOLUME_ACTIVE
        
        if current_session == 'OVERLAP':
            self.current_state = v5TradingState.SESSION_BOOST_ACTIVE
        
        logger.info(f"Signal counters updated - Daily: {self.daily_signals}, "
                   f"Hourly: {self.hourly_signals}, Session {current_session}: {self.session_signals[current_session]}")
    
    def check_correlation_limits(self, new_signal: Dict, active_trades: List[Dict]) -> bool:
        """Check correlation limits for v5.0 multi-pair trading"""
        new_pair = new_signal.get('symbol', 'EURUSD')
        
        # Count currency exposures
        usd_exposure = 0
        eur_exposure = 0
        gbp_exposure = 0
        
        for trade in active_trades:
            pair = trade.get('symbol', '')
            direction = trade.get('direction', 'BUY')
            
            # Count USD exposure
            if 'USD' in pair:
                if (pair.startswith('USD') and direction == 'BUY') or \
                   (pair.endswith('USD') and direction == 'SELL'):
                    usd_exposure += 1
                elif (pair.startswith('USD') and direction == 'SELL') or \
                     (pair.endswith('USD') and direction == 'BUY'):
                    usd_exposure -= 1
            
            # Count EUR exposure
            if 'EUR' in pair:
                if (pair.startswith('EUR') and direction == 'BUY') or \
                   (pair.endswith('EUR') and direction == 'SELL'):
                    eur_exposure += 1
                elif (pair.startswith('EUR') and direction == 'SELL') or \
                     (pair.endswith('EUR') and direction == 'BUY'):
                    eur_exposure -= 1
            
            # Count GBP exposure
            if 'GBP' in pair:
                if (pair.startswith('GBP') and direction == 'BUY') or \
                   (pair.endswith('GBP') and direction == 'SELL'):
                    gbp_exposure += 1
                elif (pair.startswith('GBP') and direction == 'SELL') or \
                     (pair.endswith('GBP') and direction == 'BUY'):
                    gbp_exposure -= 1
        
        # Check exposure limits (simplified)
        total_trades = len(active_trades)
        if total_trades > 0:
            usd_percent = abs(usd_exposure) / total_trades * 100
            eur_percent = abs(eur_exposure) / total_trades * 100
            gbp_percent = abs(gbp_exposure) / total_trades * 100
            
            if usd_percent > self.params.max_usd_exposure:
                logger.warning(f"USD exposure limit exceeded: {usd_percent:.1f}%")
                return False
            
            if eur_percent > self.params.max_eur_exposure:
                logger.warning(f"EUR exposure limit exceeded: {eur_percent:.1f}%")
                return False
            
            if gbp_percent > self.params.max_gbp_exposure:
                logger.warning(f"GBP exposure limit exceeded: {gbp_percent:.1f}%")
                return False
        
        return True
    
    def _get_base_risk_percent(self) -> float:
        """Get base risk percentage based on tier and performance"""
        # Base risk by tier
        tier_risk = {
            'PRESS_PASS': 0.5,
            'NIBBLER': 0.7,
            'FANG': 1.0,
            'COMMANDER': 1.2,
            '': 1.5
        }
        
        base = tier_risk.get(self.tier, 1.0)
        
        # Performance-based adjustment
        if self.win_rate >= 85 and self.total_trades >= 10:
            base *= 1.2  # 20% bonus for high performance
        elif self.win_rate >= 75 and self.total_trades >= 10:
            base *= 1.1  # 10% bonus for good performance
        elif self.win_rate < 60 and self.total_trades >= 10:
            base *= 0.8  # 20% reduction for poor performance
        
        return base
    
    def _get_signal_risk_multiplier(self, signal_type: str, timeframe: str) -> float:
        """Get risk multiplier based on signal type and timeframe"""
        # Timeframe-based multipliers
        timeframe_mult = {
            'M1': 0.7,   # Lower risk for fast M1 signals
            'M3': 1.0,   # Standard risk for M3 primary signals
            'M5': 1.1,   # Slightly higher for M5
            'M15': 1.3   # Higher risk for M15 snipers
        }
        
        base_mult = timeframe_mult.get(timeframe, 1.0)
        
        # Pattern-based adjustments
        if 'Ultra' in signal_type or 'Extreme' in signal_type:
            base_mult *= 1.2
        elif 'Quick' in signal_type or 'Hair' in signal_type:
            base_mult *= 1.1
        elif 'Lightning' in signal_type or 'Explosion' in signal_type:
            base_mult *= 1.15
        
        return base_mult
    
    def _get_tcs_risk_multiplier(self, tcs: float) -> float:
        """Get risk multiplier based on TCS using centralized threshold"""
        from tcs_controller import get_current_threshold
        threshold = get_current_threshold()
        
        if tcs >= (threshold + 20):
            return 1.5
        elif tcs >= (threshold + 10):
            return 1.3
        elif tcs >= threshold:
            return 1.2
        elif tcs >= (threshold - 10):
            return 1.1
        elif tcs >= (threshold - 20):
            return 1.0
        elif tcs >= (threshold - 30):
            return 0.9
        elif tcs >= (threshold - 35):
            return 0.8
        else:
            return 0.7  # Below minimum
    
    def reset_hourly_counters(self):
        """Reset hourly counters (called every hour)"""
        self.hourly_signals = 0
        logger.info("Hourly signal counters reset")
    
    def reset_daily_counters(self):
        """Reset daily counters (called daily at midnight)"""
        self.daily_signals = 0
        self.session_signals = {'ASIAN': 0, 'LONDON': 0, 'NY': 0, 'OVERLAP': 0}
        self.confluence_signals = 0
        self.active_pairs.clear()
        
        # Reset performance if needed
        if self.total_trades >= 100:  # Reset weekly
            self.total_trades = 0
            self.winning_trades = 0
            self.win_rate = 0.0
        
        logger.info("Daily signal counters reset")
    
    def update_performance(self, trade_result: Dict):
        """Update performance metrics"""
        self.total_trades += 1
        
        if trade_result.get('is_win', False):
            self.winning_trades += 1
        
        pips = trade_result.get('pips', 0)
        self.daily_pips += pips
        
        # Calculate win rate
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        logger.info(f"Performance updated - WR: {self.win_rate:.1f}%, "
                   f"Daily pips: {self.daily_pips:.1f}, Trades: {self.total_trades}")
    
    def get_risk_status(self) -> Dict:
        """Get current risk status for monitoring"""
        return {
            'tier': self.tier,
            'risk_mode': self.risk_mode.value,
            'current_state': self.current_state.value,
            'daily_signals': self.daily_signals,
            'hourly_signals': self.hourly_signals,
            'active_pairs': len(self.active_pairs),
            'confluence_signals': self.confluence_signals,
            'win_rate': self.win_rate,
            'daily_pips': self.daily_pips,
            'limits': {
                'max_daily': self.params.max_signals_per_day,
                'max_hourly': self.params.max_signals_per_hour,
                'max_pairs': self.params.max_concurrent_pairs
            }
        }

# Factory function for backward compatibility
def get_apex_v5_risk_manager(tier: str, risk_mode: str = "standard") -> v5RiskManager:
    """Factory function to create v5.0 risk manager"""
    mode_mapping = {
        'conservative': v5RiskMode.CONSERVATIVE,
        'standard': v5RiskMode.STANDARD,
        'aggressive': v5RiskMode.AGGRESSIVE,
        'ultra': v5RiskMode.ULTRA,
        'apex_beast': v5RiskMode._BEAST
    }
    
    risk_mode_enum = mode_mapping.get(risk_mode.lower()v5RiskMode.STANDARD)
    return v5RiskManager(tier=tier, risk_mode=risk_mode_enum)