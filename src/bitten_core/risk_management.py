"""
BITTEN Risk Management System
Dynamic position sizing and XP-based unlockable trade management features
"""

import math
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta, time
import json

# Import the new risk controller
from .risk_controller import get_risk_controller, TierLevel as RiskTierLevel, RiskMode as RiskControlMode

logger = logging.getLogger(__name__)

class RiskMode(Enum):
    """Risk calculation modes"""
    FIXED = "fixed"          # Fixed lot size
    PERCENTAGE = "percentage" # Percentage of account
    KELLY = "kelly"          # Kelly Criterion (advanced)
    MARTINGALE = "martingale" # Martingale (DANGER!)
    ANTI_MARTINGALE = "anti_martingale" # Increase on wins

class TradeManagementFeature(Enum):
    """XP-locked trade management features"""
    BASIC_SL_TP = "basic_sl_tp"                    # XP: 0
    BREAKEVEN = "breakeven"                        # XP: 100
    BREAKEVEN_PLUS = "breakeven_plus"             # XP: 500
    TRAILING_STOP = "trailing_stop"                # XP: 1000
    PARTIAL_CLOSE = "partial_close"                # XP: 2000
    RUNNER_MODE = "runner_mode"                    # XP: 5000
    DYNAMIC_TRAIL = "dynamic_trail"                # XP: 10000
    ZERO_RISK_RUNNER = "zero_risk_runner"         # XP: 15000
    LEROY_JENKINS = "leroy_jenkins"               # XP: 20000
    APEX_PREDATOR = "apex_predator"               # XP: 50000

class TradingState(Enum):
    """Trading states for risk management"""
    NORMAL = "normal"
    TILT_WARNING = "tilt_warning"
    TILT_LOCKOUT = "tilt_lockout"
    MEDIC_MODE = "medic_mode"
    WEEKEND_LIMITED = "weekend_limited"
    NEWS_LOCKOUT = "news_lockout"
    DAILY_LIMIT_HIT = "daily_limit_hit"

@dataclass
class TradingSession:
    """Tracks current trading session statistics"""
    start_time: datetime
    trades_taken: int = 0
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    daily_pnl: float = 0.0
    daily_pnl_percent: float = 0.0
    last_trade_time: Optional[datetime] = None
    tilt_strikes: int = 0
    state: TradingState = TradingState.NORMAL
    medic_activated_at: Optional[datetime] = None
    
@dataclass
class NewsEvent:
    """High impact news event"""
    event_time: datetime
    currency: str
    impact: str  # "high", "medium", "low"
    event_name: str

@dataclass
class AccountInfo:
    """Account information for risk calculations"""
    balance: float
    equity: float
    margin: float
    free_margin: float
    currency: str = "USD"
    leverage: int = 100
    starting_balance: float = None  # For daily loss calculation
    
    def __post_init__(self):
        if self.starting_balance is None:
            self.starting_balance = self.balance

@dataclass
class RiskProfile:
    """User's risk profile and preferences"""
    user_id: int
    max_risk_percent: float = 2.0      # Default 2% per BITTEN rules
    max_positions: int = 3             # Max concurrent positions
    daily_loss_limit: float = 7.0      # Default -7% for NIBBLER
    win_rate: float = 0.5              # Historical win rate
    avg_rr_ratio: float = 1.5          # Average risk/reward ratio
    current_xp: int = 0                # User's current XP
    tier_level: str = "NIBBLER"        # User's tier
    weekend_max_positions: int = 1     # Reduced for weekends
    weekend_risk_multiplier: float = 0.5  # 50% risk on weekends
    tilt_threshold: int = 3            # Consecutive losses before tilt
    medic_mode_threshold: float = 5.0  # -5% triggers medic mode
    
    def get_daily_loss_limit(self) -> float:
        """Get tier-based daily loss limit from risk controller"""
        # Use the new risk controller limits
        tier_limits = {
            'NIBBLER': 6.0,     # NEW: -6% daily limit (was 7%)
            'FANG': 8.5,        # NEW: -8.5% daily limit (was 10%)
            'COMMANDER': 8.5,   # NEW: -8.5% daily limit (was 10%)
            'APEX': 8.5         # NEW: -8.5% daily limit (was 10%)
        }
        return tier_limits.get(self.tier_level, 6.0)
    
    def get_unlocked_features(self) -> List[TradeManagementFeature]:
        """Get list of unlocked trade management features based on XP"""
        unlocked = []
        xp_requirements = {
            TradeManagementFeature.BASIC_SL_TP: 0,
            TradeManagementFeature.BREAKEVEN: 100,
            TradeManagementFeature.BREAKEVEN_PLUS: 500,
            TradeManagementFeature.TRAILING_STOP: 1000,
            TradeManagementFeature.PARTIAL_CLOSE: 2000,
            TradeManagementFeature.RUNNER_MODE: 5000,
            TradeManagementFeature.DYNAMIC_TRAIL: 10000,
            TradeManagementFeature.ZERO_RISK_RUNNER: 15000,
            TradeManagementFeature.LEROY_JENKINS: 20000,
            TradeManagementFeature.APEX_PREDATOR: 50000
        }
        
        for feature, required_xp in xp_requirements.items():
            if self.current_xp >= required_xp:
                unlocked.append(feature)
        
        return unlocked

@dataclass
class TradeManagementPlan:
    """Advanced trade management plan"""
    feature: TradeManagementFeature
    breakeven_trigger_pips: float = 0
    breakeven_plus_pips: float = 0
    trailing_start_pips: float = 0
    trailing_step_pips: float = 0
    trailing_distance_pips: float = 0
    partial_close_percent: float = 0
    partial_close_at_pips: float = 0
    runner_target_rr: float = 0  # Risk/Reward for runner
    
class RiskManager:
    """
    Advanced risk management system with safety features
    Handles tilt detection, daily limits, medic mode, and trading restrictions
    """
    
    def __init__(self):
        self.sessions: Dict[int, TradingSession] = {}  # user_id -> session
        self.news_events: List[NewsEvent] = []
        self.news_lockout_minutes = 30  # Lock trading 30 mins before/after high impact news
        
    def get_or_create_session(self, user_id: int) -> TradingSession:
        """Get current trading session or create new one"""
        now = datetime.now()
        
        # Check if we need a new session (new day)
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if session.start_time.date() != now.date():
                # New day, create new session
                session = TradingSession(start_time=now)
                self.sessions[user_id] = session
        else:
            # First session
            session = TradingSession(start_time=now)
            self.sessions[user_id] = session
            
        return session
    
    def check_trading_restrictions(self, 
                                 profile: RiskProfile,
                                 account: AccountInfo,
                                 symbol: str) -> Dict[str, any]:
        """
        Check all trading restrictions and return status
        
        Returns dict with:
        - can_trade: bool
        - reason: str (if can't trade)
        - state: TradingState
        - restrictions: dict of active restrictions
        """
        session = self.get_or_create_session(profile.user_id)
        now = datetime.now()
        restrictions = {}
        
        # 1. Check daily loss limit
        daily_loss_limit = profile.get_daily_loss_limit()
        daily_loss_percent = ((account.starting_balance - account.balance) / account.starting_balance) * 100
        
        if daily_loss_percent >= daily_loss_limit:
            session.state = TradingState.DAILY_LIMIT_HIT
            return {
                'can_trade': False,
                'reason': f'Daily loss limit hit: -{daily_loss_percent:.1f}% (limit: -{daily_loss_limit}%)',
                'state': session.state,
                'restrictions': {'daily_limit_hit': True}
            }
        
        # 2. Check tilt detection
        if session.consecutive_losses >= profile.tilt_threshold:
            if session.tilt_strikes >= 2:
                # Full tilt lockout - need 1 hour break
                if session.last_trade_time and (now - session.last_trade_time).seconds < 3600:
                    session.state = TradingState.TILT_LOCKOUT
                    time_left = 3600 - (now - session.last_trade_time).seconds
                    return {
                        'can_trade': False,
                        'reason': f'Tilt lockout active. Take a break! ({time_left//60} minutes remaining)',
                        'state': session.state,
                        'restrictions': {'tilt_lockout': True, 'time_remaining': time_left}
                    }
            else:
                session.state = TradingState.TILT_WARNING
                restrictions['tilt_warning'] = True
                session.tilt_strikes += 1
        
        # 3. Check medic mode
        if daily_loss_percent >= profile.medic_mode_threshold:
            session.state = TradingState.MEDIC_MODE
            restrictions['medic_mode'] = True
            restrictions['reduced_risk'] = 0.5  # 50% risk in medic mode
            restrictions['max_positions'] = 1  # Only 1 position in medic mode
            
            if not session.medic_activated_at:
                session.medic_activated_at = now
                logger.warning(f"Medic mode activated for user {profile.user_id} at -{daily_loss_percent:.1f}%")
        
        # 4. Check weekend restrictions
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            session.state = TradingState.WEEKEND_LIMITED
            restrictions['weekend_mode'] = True
            restrictions['max_positions'] = profile.weekend_max_positions
            restrictions['risk_multiplier'] = profile.weekend_risk_multiplier
        
        # 5. Check news lockouts
        if self._is_news_lockout(symbol, now):
            return {
                'can_trade': False,
                'reason': 'High impact news event lockout active',
                'state': TradingState.NEWS_LOCKOUT,
                'restrictions': {'news_lockout': True}
            }
        
        # Update session
        session.daily_pnl_percent = daily_loss_percent
        
        # Can trade with any active restrictions
        return {
            'can_trade': True,
            'reason': None,
            'state': session.state,
            'restrictions': restrictions
        }
    
    def _is_news_lockout(self, symbol: str, check_time: datetime) -> bool:
        """Check if trading is locked due to news events"""
        # Extract currencies from symbol (e.g., EURUSD -> EUR, USD)
        currencies = []
        if len(symbol) >= 6:
            currencies = [symbol[:3], symbol[3:6]]
        
        for event in self.news_events:
            if event.impact != 'high':
                continue
                
            if event.currency in currencies:
                # Check if we're within lockout window
                time_to_event = abs((event.event_time - check_time).total_seconds() / 60)
                if time_to_event <= self.news_lockout_minutes:
                    return True
        
        return False
    
    def update_trade_result(self, profile: RiskProfile, won: bool, pnl: float):
        """Update session after trade closes"""
        session = self.get_or_create_session(profile.user_id)
        
        session.trades_taken += 1
        session.daily_pnl += pnl
        session.last_trade_time = datetime.now()
        
        if won:
            session.consecutive_wins += 1
            session.consecutive_losses = 0
            session.tilt_strikes = 0  # Reset tilt on win
        else:
            session.consecutive_losses += 1
            session.consecutive_wins = 0
        
        # Log significant events
        if session.consecutive_losses >= profile.tilt_threshold:
            logger.warning(f"User {profile.user_id} on tilt warning: {session.consecutive_losses} losses in a row")
        
        if session.consecutive_wins >= 3:
            logger.info(f"User {profile.user_id} on hot streak: {session.consecutive_wins} wins in a row!")
    
    def add_news_event(self, event: NewsEvent):
        """Add news event to monitor"""
        self.news_events.append(event)
        # Clean old events
        cutoff = datetime.now() - timedelta(hours=2)
        self.news_events = [e for e in self.news_events if e.event_time > cutoff]
    
    def get_adjusted_risk_params(self, 
                                profile: RiskProfile,
                                account: AccountInfo,
                                base_risk_percent: float) -> Dict[str, float]:
        """Get risk parameters adjusted for current restrictions"""
        status = self.check_trading_restrictions(profile, account, "")
        restrictions = status.get('restrictions', {})
        
        adjusted_risk = base_risk_percent
        max_positions = profile.max_positions
        
        # Apply medic mode reduction
        if restrictions.get('medic_mode'):
            adjusted_risk *= restrictions.get('reduced_risk', 0.5)
            max_positions = min(max_positions, restrictions.get('max_positions', 1))
            
        # Apply weekend reduction
        if restrictions.get('weekend_mode'):
            adjusted_risk *= restrictions.get('risk_multiplier', 0.5)
            max_positions = min(max_positions, restrictions.get('max_positions', 1))
        
        return {
            'risk_percent': adjusted_risk,
            'max_positions': max_positions,
            'active_restrictions': restrictions,
            'trading_state': status.get('state')
        }

class RiskCalculator:
    """
    Advanced risk calculator with XP-based features
    Handles position sizing and trade management planning
    """
    
    def __init__(self, risk_manager: Optional[RiskManager] = None):
        # Symbol specifications (would come from broker in production)
        self.symbol_specs = {
            # Core pairs
            'EURUSD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'GBPUSD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'USDJPY': {'pip_value': 0.01, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'USDCAD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'GBPJPY': {'pip_value': 0.01, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            # Extra pairs
            'AUDUSD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'NZDUSD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'AUDJPY': {'pip_value': 0.01, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'EURJPY': {'pip_value': 0.01, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'EURGBP': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'GBPCHF': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'USDCHF': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100}
        }
        
        # Tier-based risk adjustments
        self.tier_multipliers = {
            'NIBBLER': 1.0,      # Standard risk
            'FANG': 1.1,         # 10% more risk allowed
            'COMMANDER': 1.2,    # 20% more risk allowed
            'APEX': 1.5          # 50% more risk allowed (elite)
        }
        
        # Risk manager for safety checks
        self.risk_manager = risk_manager or RiskManager()
    
    def calculate_position_size(self,
                              account: AccountInfo,
                              profile: RiskProfile,
                              symbol: str,
                              entry_price: float,
                              stop_loss_price: float,
                              risk_mode: RiskMode = RiskMode.PERCENTAGE) -> Dict[str, float]:
        """
        Calculate optimal position size based on risk parameters
        
        Returns:
            Dictionary with position details:
            - lot_size: Calculated lot size
            - risk_amount: Dollar amount at risk
            - pip_risk: Pips from entry to SL
            - potential_loss: Maximum potential loss
            - can_trade: Whether trade is allowed
            - restrictions: Any active restrictions
        """
        try:
            # Check trading restrictions first
            trade_status = self.risk_manager.check_trading_restrictions(profile, account, symbol)
            if not trade_status['can_trade']:
                return {
                    'lot_size': 0,
                    'risk_amount': 0,
                    'actual_risk': 0,
                    'pip_risk': 0,
                    'risk_percent': 0,
                    'can_trade': False,
                    'reason': trade_status['reason'],
                    'restrictions': trade_status.get('restrictions', {})
                }
            # Get symbol specifications
            specs = self.symbol_specs.get(symbol, self.symbol_specs['EURUSD'])
            
            # Calculate pip risk
            pip_risk = abs(entry_price - stop_loss_price) / specs['pip_value']
            
            # Get risk controller instance
            risk_controller = get_risk_controller()
            
            # Convert tier level to risk controller enum
            tier_enum = RiskTierLevel[profile.tier_level.upper()]
            
            # Get risk percentage from risk controller (overrides old system)
            risk_percent, risk_reason = risk_controller.get_user_risk_percent(profile.user_id, tier_enum)
            
            # Check if trade is allowed by risk controller
            potential_loss = account.balance * (risk_percent / 100)
            trade_allowed, block_reason = risk_controller.check_trade_allowed(
                profile.user_id, tier_enum, potential_loss, account.balance
            )
            
            if not trade_allowed:
                return {
                    'lot_size': 0,
                    'risk_amount': 0,
                    'actual_risk': 0,
                    'pip_risk': 0,
                    'risk_percent': 0,
                    'can_trade': False,
                    'reason': block_reason,
                    'restrictions': {'risk_controller_blocked': True}
                }
            
            # Get adjusted risk parameters from risk manager (for other restrictions)
            risk_params = self.risk_manager.get_adjusted_risk_params(profile, account, risk_percent)
            
            # Calculate risk amount based on mode
            if risk_mode == RiskMode.PERCENTAGE:
                # Use risk controller's percentage
                risk_amount = account.balance * (risk_percent / 100)
                
            elif risk_mode == RiskMode.KELLY:
                # Kelly Criterion for advanced users (XP > 10000)
                if profile.current_xp < 10000:
                    # Fallback to percentage mode
                    risk_percent = profile.max_risk_percent
                    risk_amount = account.balance * (risk_percent / 100)
                else:
                    # Kelly formula: f = (p*b - q) / b
                    # where p = win rate, q = loss rate, b = avg win/loss ratio
                    kelly_percent = (profile.win_rate * profile.avg_rr_ratio - (1 - profile.win_rate)) / profile.avg_rr_ratio
                    kelly_percent = max(0, min(kelly_percent * 100, 25))  # Cap at 25%
                    
                    # Apply Kelly fraction (usually 0.25 for safety)
                    risk_percent = kelly_percent * 0.25 * tier_mult
                    risk_amount = account.balance * (risk_percent / 100)
                    
            elif risk_mode == RiskMode.ANTI_MARTINGALE:
                # Increase risk on winning streaks (requires trade history)
                # For now, use standard risk
                risk_percent = profile.max_risk_percent * tier_mult
                risk_amount = account.balance * (risk_percent / 100)
                
            else:  # FIXED or fallback
                risk_amount = 100  # Default $100 risk
            
            # Calculate pip value per lot
            # Forex pairs
            if symbol.endswith('USD'):
                pip_value_per_lot = 10  # Standard for XXX/USD pairs
            else:
                # Would need current price for exact calculation
                pip_value_per_lot = 10  # Approximation
            
            # Calculate lot size
            if pip_risk > 0:
                lot_size = risk_amount / (pip_risk * pip_value_per_lot)
            else:
                lot_size = specs['min_lot']
            
            # Apply lot size constraints
            lot_size = max(specs['min_lot'], min(lot_size, specs['max_lot']))
            
            # Round to broker's lot step (usually 0.01)
            lot_size = round(lot_size, 2)
            
            # Calculate actual risk with final lot size
            actual_risk = lot_size * pip_risk * pip_value_per_lot
            
            return {
                'lot_size': lot_size,
                'risk_amount': risk_amount,
                'actual_risk': actual_risk,
                'pip_risk': pip_risk,
                'risk_percent': (actual_risk / account.balance) * 100,
                'tier_multiplier': tier_mult,
                'mode': risk_mode.value,
                'can_trade': True,
                'restrictions': risk_params.get('active_restrictions', {}),
                'trading_state': risk_params.get('trading_state', TradingState.NORMAL).value
            }
            
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
            # Return minimum safe position
            return {
                'lot_size': 0.01,
                'risk_amount': 0,
                'actual_risk': 0,
                'pip_risk': 0,
                'risk_percent': 0,
                'error': str(e)
            }
    
    def create_trade_management_plan(self,
                                   profile: RiskProfile,
                                   entry_price: float,
                                   stop_loss_price: float,
                                   take_profit_price: float,
                                   symbol: str) -> List[TradeManagementPlan]:
        """
        Create advanced trade management plan based on unlocked features
        
        Returns list of management actions to execute at different price levels
        """
        plans = []
        unlocked = profile.get_unlocked_features()
        specs = self.symbol_specs.get(symbol, self.symbol_specs['EURUSD'])
        
        # Calculate key levels
        sl_pips = abs(entry_price - stop_loss_price) / specs['pip_value']
        tp_pips = abs(take_profit_price - entry_price) / specs['pip_value']
        
        # Basic SL/TP (always available)
        if TradeManagementFeature.BASIC_SL_TP in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.BASIC_SL_TP
            ))
        
        # Breakeven (XP: 100+)
        if TradeManagementFeature.BREAKEVEN in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.BREAKEVEN,
                breakeven_trigger_pips=sl_pips * 0.5  # Move to BE at 50% of SL distance
            ))
        
        # Breakeven Plus (XP: 500+)
        if TradeManagementFeature.BREAKEVEN_PLUS in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.BREAKEVEN_PLUS,
                breakeven_trigger_pips=sl_pips * 0.75,
                breakeven_plus_pips=sl_pips * 0.1  # Lock in 10% of risk as profit
            ))
        
        # Trailing Stop (XP: 1000+)
        if TradeManagementFeature.TRAILING_STOP in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.TRAILING_STOP,
                trailing_start_pips=sl_pips,  # Start trailing at 1R
                trailing_distance_pips=sl_pips * 0.5,  # Trail by 50% of initial risk
                trailing_step_pips=5  # Update every 5 pips
            ))
        
        # Partial Close (XP: 2000+)
        if TradeManagementFeature.PARTIAL_CLOSE in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.PARTIAL_CLOSE,
                partial_close_percent=50,  # Close 50% at 1R
                partial_close_at_pips=sl_pips
            ))
        
        # Runner Mode (XP: 5000+)
        if TradeManagementFeature.RUNNER_MODE in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.RUNNER_MODE,
                partial_close_percent=75,  # Close 75% at 1.5R
                partial_close_at_pips=sl_pips * 1.5,
                runner_target_rr=5.0  # Let 25% run to 5R
            ))
        
        # Zero Risk Runner (XP: 15000+) - The Holy Grail
        if TradeManagementFeature.ZERO_RISK_RUNNER in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.ZERO_RISK_RUNNER,
                partial_close_percent=50,  # Close 50% at 2R (covers risk + profit)
                partial_close_at_pips=sl_pips * 2,
                breakeven_trigger_pips=sl_pips * 2,  # Move SL to BE after partial
                runner_target_rr=10.0  # Let runner go for 10R+
            ))
        
        # Leroy Jenkins Mode (XP: 20000+) - YOLO with strategy
        if TradeManagementFeature.LEROY_JENKINS in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.LEROY_JENKINS,
                trailing_start_pips=sl_pips * 0.5,  # Aggressive early trailing
                trailing_distance_pips=sl_pips * 0.25,  # Tight trail
                partial_close_percent=25,  # Take 25% quickly
                partial_close_at_pips=sl_pips * 0.5,
                runner_target_rr=20.0  # Moon or bust
            ))
        
        return plans
    
    def calculate_scaled_entry(self,
                             account: AccountInfo,
                             profile: RiskProfile,
                             symbol: str,
                             zones: List[float],
                             total_risk_percent: float = 2.0) -> List[Dict]:
        """
        Calculate scaled entry positions across multiple price zones
        Advanced feature for distributing risk across levels
        """
        if profile.current_xp < 5000:
            # Not unlocked yet
            return []
        
        positions = []
        risk_per_zone = total_risk_percent / len(zones)
        
        for i, zone_price in enumerate(zones):
            # Adjust risk for each zone
            zone_risk = risk_per_zone * (1 + i * 0.1)  # Slightly increase risk for better zones
            
            positions.append({
                'zone': i + 1,
                'price': zone_price,
                'risk_percent': zone_risk,
                'lot_size': 0  # Would calculate based on actual SL
            })
        
        return positions


# XP-based feature descriptions for UI
FEATURE_DESCRIPTIONS = {
    TradeManagementFeature.BREAKEVEN: {
        'name': 'Breakeven Shield',
        'description': 'Move stop loss to entry when trade reaches 50% of target',
        'xp_required': 100,
        'icon': '🛡️'
    },
    TradeManagementFeature.BREAKEVEN_PLUS: {
        'name': 'Profit Lock',
        'description': 'Lock in small profit when trade moves in your favor',
        'xp_required': 500,
        'icon': '🔒'
    },
    TradeManagementFeature.TRAILING_STOP: {
        'name': 'Hunter Protocol',
        'description': 'Stop loss follows price to capture trending moves',
        'xp_required': 1000,
        'icon': '🎯'
    },
    TradeManagementFeature.PARTIAL_CLOSE: {
        'name': 'Tactical Harvest',
        'description': 'Take partial profits while letting winners run',
        'xp_required': 2000,
        'icon': '🌾'
    },
    TradeManagementFeature.RUNNER_MODE: {
        'name': 'Marathon Mode',
        'description': 'Close 75% at target, let 25% run for massive gains',
        'xp_required': 5000,
        'icon': '🏃'
    },
    TradeManagementFeature.DYNAMIC_TRAIL: {
        'name': 'Adaptive Stalker',
        'description': 'AI-powered trailing stop that adapts to volatility',
        'xp_required': 10000,
        'icon': '🤖'
    },
    TradeManagementFeature.ZERO_RISK_RUNNER: {
        'name': 'Free Money Glitch',
        'description': 'Close enough to cover risk, run the rest risk-free',
        'xp_required': 15000,
        'icon': '💎'
    },
    TradeManagementFeature.LEROY_JENKINS: {
        'name': 'LEROY JENKINS!',
        'description': 'Ultra-aggressive management for maximum gains',
        'xp_required': 20000,
        'icon': '🔥'
    },
    TradeManagementFeature.APEX_PREDATOR: {
        'name': 'Apex Predator',
        'description': 'Full suite of elite features with AI optimization',
        'xp_required': 50000,
        'icon': '👑'
    }
}


# Utility functions for safety system integration
class SafetySystemIntegration:
    """Integration utilities for existing BITTEN safety systems"""
    
    @staticmethod
    def format_risk_warning(restrictions: Dict[str, any]) -> str:
        """Format risk restrictions into user-friendly warning"""
        warnings = []
        
        if restrictions.get('medic_mode'):
            warnings.append("⚠️ MEDIC MODE ACTIVE - Risk reduced to 50%")
        
        if restrictions.get('tilt_warning'):
            warnings.append("🤬 TILT WARNING - Take a break after next loss!")
        
        if restrictions.get('weekend_mode'):
            warnings.append("📅 WEEKEND MODE - Limited positions & reduced risk")
        
        if restrictions.get('news_lockout'):
            warnings.append("📰 NEWS LOCKOUT - High impact event approaching")
        
        if restrictions.get('daily_limit_hit'):
            warnings.append("🛑 DAILY LOSS LIMIT HIT - Trading disabled for today")
        
        return "\n".join(warnings) if warnings else "✅ All systems green"
    
    @staticmethod
    def get_session_stats(risk_manager: RiskManager, user_id: int) -> Dict:
        """Get current session statistics for UI display"""
        session = risk_manager.get_or_create_session(user_id)
        
        return {
            'trades_today': session.trades_taken,
            'consecutive_losses': session.consecutive_losses,
            'consecutive_wins': session.consecutive_wins,
            'daily_pnl': session.daily_pnl,
            'daily_pnl_percent': session.daily_pnl_percent,
            'tilt_strikes': session.tilt_strikes,
            'current_state': session.state.value,
            'medic_mode': session.state == TradingState.MEDIC_MODE,
            'can_trade': session.state not in [TradingState.TILT_LOCKOUT, TradingState.DAILY_LIMIT_HIT, TradingState.NEWS_LOCKOUT]
        }
    
    @staticmethod
    def should_force_exit(risk_manager: RiskManager, profile: RiskProfile, account: AccountInfo) -> Tuple[bool, str]:
        """Check if any positions should be force-closed"""
        session = risk_manager.get_or_create_session(profile.user_id)
        
        # Force exit on daily limit
        daily_loss_percent = ((account.starting_balance - account.balance) / account.starting_balance) * 100
        if daily_loss_percent >= profile.get_daily_loss_limit():
            return True, "Daily loss limit reached - closing all positions"
        
        # Force exit on severe tilt (optional)
        if session.consecutive_losses >= 5:
            return True, "Severe tilt detected - closing all positions for safety"
        
        return False, ""


# Example usage
def example_usage():
    """Example of how to use the enhanced risk management system"""
    
    # Initialize risk manager
    risk_manager = RiskManager()
    
    # Create user profile
    profile = RiskProfile(
        user_id=12345,
        tier_level="NIBBLER",
        current_xp=1500,
        max_risk_percent=2.0
    )
    
    # Account info
    account = AccountInfo(
        balance=10000,
        equity=9800,
        margin=500,
        free_margin=9300
    )
    
    # Add a news event
    news_event = NewsEvent(
        event_time=datetime.now() + timedelta(minutes=20),
        currency="USD",
        impact="high",
        event_name="NFP Release"
    )
    risk_manager.add_news_event(news_event)
    
    # Create calculator
    calculator = RiskCalculator(risk_manager)
    
    # Calculate position size
    result = calculator.calculate_position_size(
        account=account,
        profile=profile,
        symbol="EURUSD",
        entry_price=1.0850,
        stop_loss_price=1.0800,
        risk_mode=RiskMode.PERCENTAGE
    )
    
    if result['can_trade']:
        print(f"Position size: {result['lot_size']} lots")
        print(f"Risk amount: ${result['risk_amount']:.2f}")
        print(f"Active restrictions: {result['restrictions']}")
    else:
        print(f"Cannot trade: {result['reason']}")
    
    # Update with trade result
    risk_manager.update_trade_result(profile, won=False, pnl=-200)
    
    # Get session stats
    stats = SafetySystemIntegration.get_session_stats(risk_manager, profile.user_id)
    print(f"Session stats: {stats}")
    
    # Check restrictions again
    warnings = SafetySystemIntegration.format_risk_warning(result['restrictions'])
    print(f"Warnings: {warnings}")