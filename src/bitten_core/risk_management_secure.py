"""
BITTEN Risk Management System - SECURE VERSION
Dynamic position sizing and XP-based unlockable trade management features
Enhanced with security features from security_utils.py
"""

import math
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import logging
from decimal import Decimal, ROUND_DOWN, InvalidOperation

from .security_utils import (
    validate_symbol, validate_account_balance, validate_risk_percent,
    validate_price, ValidationError, SecurityError
)

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

@dataclass
class AccountInfo:
    """Account information for risk calculations"""
    balance: Decimal
    equity: Decimal
    margin: Decimal
    free_margin: Decimal
    currency: str = "USD"
    leverage: int = 100
    
    def __post_init__(self):
        """Validate account info"""
        self.balance = validate_account_balance(self.balance)
        self.equity = validate_account_balance(self.equity)
        self.margin = Decimal(str(self.margin))
        self.free_margin = Decimal(str(self.free_margin))
        
        if self.leverage < 1 or self.leverage > 1000:
            raise ValidationError(f"Invalid leverage: {self.leverage}")

@dataclass
class RiskProfile:
    """User's risk profile and preferences"""
    user_id: int
    max_risk_percent: Decimal = Decimal('2.0')      # Default 2% per BITTEN rules
    max_positions: int = 3                          # Max concurrent positions
    daily_loss_limit: Decimal = Decimal('7.0')      # -7% daily drawdown limit
    win_rate: Decimal = Decimal('0.5')              # Historical win rate
    avg_rr_ratio: Decimal = Decimal('1.5')          # Average risk/reward ratio
    current_xp: int = 0                             # User's current XP
    tier_level: str = "NIBBLER"                     # User's tier
    
    def __post_init__(self):
        """Validate risk profile"""
        self.max_risk_percent = validate_risk_percent(self.max_risk_percent)
        self.daily_loss_limit = validate_risk_percent(self.daily_loss_limit)
        
        if self.max_positions < 1 or self.max_positions > 50:
            raise ValidationError(f"Invalid max positions: {self.max_positions}")
        
        if self.win_rate < Decimal('0') or self.win_rate > Decimal('1'):
            raise ValidationError(f"Invalid win rate: {self.win_rate}")
        
        if self.avg_rr_ratio < Decimal('0.1') or self.avg_rr_ratio > Decimal('100'):
            raise ValidationError(f"Invalid RR ratio: {self.avg_rr_ratio}")
        
        if self.current_xp < 0:
            raise ValidationError(f"Invalid XP: {self.current_xp}")
        
        valid_tiers = ['NIBBLER', 'FANG', 'COMMANDER', 'APEX']
        if self.tier_level not in valid_tiers:
            raise ValidationError(f"Invalid tier: {self.tier_level}")
    
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
    breakeven_trigger_pips: Decimal = Decimal('0')
    breakeven_plus_pips: Decimal = Decimal('0')
    trailing_start_pips: Decimal = Decimal('0')
    trailing_step_pips: Decimal = Decimal('0')
    trailing_distance_pips: Decimal = Decimal('0')
    partial_close_percent: Decimal = Decimal('0')
    partial_close_at_pips: Decimal = Decimal('0')
    runner_target_rr: Decimal = Decimal('0')  # Risk/Reward for runner
    
    def __post_init__(self):
        """Validate management plan parameters"""
        # Validate all numeric fields are non-negative
        for field_name in ['breakeven_trigger_pips', 'breakeven_plus_pips', 
                          'trailing_start_pips', 'trailing_step_pips',
                          'trailing_distance_pips', 'partial_close_at_pips',
                          'runner_target_rr']:
            value = getattr(self, field_name)
            if value < 0:
                raise ValidationError(f"{field_name} cannot be negative: {value}")
        
        # Validate percentage
        if self.partial_close_percent < 0 or self.partial_close_percent > 100:
            raise ValidationError(f"Invalid partial close percent: {self.partial_close_percent}")

class RiskCalculator:
    """
    Advanced risk calculator with XP-based features
    Handles position sizing and trade management planning
    """
    
    def __init__(self):
        # Symbol specifications (would come from broker in production)
        self.symbol_specs = {
            'XAUUSD': {
                'pip_value': Decimal('0.1'), 
                'contract_size': 100, 
                'min_lot': Decimal('0.01'), 
                'max_lot': Decimal('100')
            },
            'EURUSD': {
                'pip_value': Decimal('0.0001'), 
                'contract_size': 100000, 
                'min_lot': Decimal('0.01'), 
                'max_lot': Decimal('100')
            },
            'GBPUSD': {
                'pip_value': Decimal('0.0001'), 
                'contract_size': 100000, 
                'min_lot': Decimal('0.01'), 
                'max_lot': Decimal('100')
            },
            'USDJPY': {
                'pip_value': Decimal('0.01'), 
                'contract_size': 100000, 
                'min_lot': Decimal('0.01'), 
                'max_lot': Decimal('100')
            },
            'USDCAD': {
                'pip_value': Decimal('0.0001'), 
                'contract_size': 100000, 
                'min_lot': Decimal('0.01'), 
                'max_lot': Decimal('100')
            },
            'GBPJPY': {
                'pip_value': Decimal('0.01'), 
                'contract_size': 100000, 
                'min_lot': Decimal('0.01'), 
                'max_lot': Decimal('100')
            }
        }
        
        # Tier-based risk adjustments
        self.tier_multipliers = {
            'NIBBLER': Decimal('1.0'),      # Standard risk
            'FANG': Decimal('1.1'),         # 10% more risk allowed
            'COMMANDER': Decimal('1.2'),    # 20% more risk allowed
            'APEX': Decimal('1.5')          # 50% more risk allowed (elite)
        }
    
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
        """
        try:
            # Validate inputs
            symbol = validate_symbol(symbol)
            entry_price = validate_price(entry_price)
            stop_loss_price = validate_price(stop_loss_price)
            
            # Get symbol specifications
            specs = self.symbol_specs.get(symbol)
            if not specs:
                raise ValidationError(f"Unknown symbol: {symbol}")
            
            # Calculate pip risk
            pip_value = specs['pip_value']
            pip_risk = abs(entry_price - stop_loss_price) / pip_value
            
            # Prevent division by zero
            if pip_risk == 0:
                raise ValidationError("Stop loss cannot be at entry price")
            
            # Get tier multiplier
            tier_mult = self.tier_multipliers.get(profile.tier_level, Decimal('1.0'))
            
            # Calculate risk amount based on mode
            if risk_mode == RiskMode.PERCENTAGE:
                # Standard percentage risk with tier adjustment
                risk_percent = min(profile.max_risk_percent * tier_mult, Decimal('5.0'))  # Cap at 5%
                risk_amount = account.balance * (risk_percent / Decimal('100'))
                
            elif risk_mode == RiskMode.KELLY:
                # Kelly Criterion for advanced users (XP > 10000)
                if profile.current_xp < 10000:
                    # Fallback to percentage mode
                    risk_percent = profile.max_risk_percent
                    risk_amount = account.balance * (risk_percent / Decimal('100'))
                else:
                    # Kelly formula: f = (p*b - q) / b
                    # where p = win rate, q = loss rate, b = avg win/loss ratio
                    p = profile.win_rate
                    q = Decimal('1') - profile.win_rate
                    b = profile.avg_rr_ratio
                    
                    # Calculate Kelly fraction
                    try:
                        kelly_fraction = (p * b - q) / b
                    except (InvalidOperation, ZeroDivisionError):
                        kelly_fraction = Decimal('0')
                    
                    kelly_percent = max(Decimal('0'), min(kelly_fraction * Decimal('100'), Decimal('25')))  # Cap at 25%
                    
                    # Apply Kelly fraction (usually 0.25 for safety)
                    risk_percent = kelly_percent * Decimal('0.25') * tier_mult
                    risk_amount = account.balance * (risk_percent / Decimal('100'))
                    
            elif risk_mode == RiskMode.ANTI_MARTINGALE:
                # Increase risk on winning streaks (requires trade history)
                # For now, use standard risk
                risk_percent = profile.max_risk_percent * tier_mult
                risk_amount = account.balance * (risk_percent / Decimal('100'))
                
            else:  # FIXED or fallback
                risk_amount = Decimal('100')  # Default $100 risk
            
            # Calculate pip value per lot
            if symbol == 'XAUUSD':
                # Gold has different calculation
                pip_value_per_lot = pip_value * specs['contract_size']
            else:
                # Forex pairs
                if symbol.endswith('USD'):
                    pip_value_per_lot = Decimal('10')  # Standard for XXX/USD pairs
                else:
                    # Would need current price for exact calculation
                    pip_value_per_lot = Decimal('10')  # Approximation
            
            # Calculate lot size
            try:
                lot_size = risk_amount / (pip_risk * pip_value_per_lot)
            except (InvalidOperation, ZeroDivisionError):
                lot_size = specs['min_lot']
            
            # Apply lot size constraints
            lot_size = max(specs['min_lot'], min(lot_size, specs['max_lot']))
            
            # Round to broker's lot step (usually 0.01)
            lot_size = lot_size.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            
            # Calculate actual risk with final lot size
            actual_risk = lot_size * pip_risk * pip_value_per_lot
            
            # Ensure actual risk doesn't exceed maximum allowed
            max_allowed_risk = account.balance * (Decimal('5') / Decimal('100'))  # Hard cap at 5%
            if actual_risk > max_allowed_risk:
                # Recalculate lot size with hard cap
                lot_size = max_allowed_risk / (pip_risk * pip_value_per_lot)
                lot_size = lot_size.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                actual_risk = lot_size * pip_risk * pip_value_per_lot
            
            return {
                'lot_size': float(lot_size),
                'risk_amount': float(risk_amount),
                'actual_risk': float(actual_risk),
                'pip_risk': float(pip_risk),
                'risk_percent': float((actual_risk / account.balance) * Decimal('100')),
                'tier_multiplier': float(tier_mult),
                'mode': risk_mode.value
            }
            
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
            # Return minimum safe position
            min_lot = float(self.symbol_specs.get(symbol, {}).get('min_lot', Decimal('0.01')))
            return {
                'lot_size': min_lot,
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
        
        # Validate inputs
        symbol = validate_symbol(symbol)
        entry_price = validate_price(entry_price)
        stop_loss_price = validate_price(stop_loss_price)
        take_profit_price = validate_price(take_profit_price)
        
        specs = self.symbol_specs.get(symbol)
        if not specs:
            raise ValidationError(f"Unknown symbol: {symbol}")
        
        # Calculate key levels
        pip_value = specs['pip_value']
        sl_pips = abs(entry_price - stop_loss_price) / pip_value
        tp_pips = abs(take_profit_price - entry_price) / pip_value
        
        # Convert to Decimal for calculations
        sl_pips = Decimal(str(sl_pips))
        tp_pips = Decimal(str(tp_pips))
        
        # Basic SL/TP (always available)
        if TradeManagementFeature.BASIC_SL_TP in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.BASIC_SL_TP
            ))
        
        # Breakeven (XP: 100+)
        if TradeManagementFeature.BREAKEVEN in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.BREAKEVEN,
                breakeven_trigger_pips=sl_pips * Decimal('0.5')  # Move to BE at 50% of SL distance
            ))
        
        # Breakeven Plus (XP: 500+)
        if TradeManagementFeature.BREAKEVEN_PLUS in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.BREAKEVEN_PLUS,
                breakeven_trigger_pips=sl_pips * Decimal('0.75'),
                breakeven_plus_pips=sl_pips * Decimal('0.1')  # Lock in 10% of risk as profit
            ))
        
        # Trailing Stop (XP: 1000+)
        if TradeManagementFeature.TRAILING_STOP in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.TRAILING_STOP,
                trailing_start_pips=sl_pips,  # Start trailing at 1R
                trailing_distance_pips=sl_pips * Decimal('0.5'),  # Trail by 50% of initial risk
                trailing_step_pips=Decimal('5')  # Update every 5 pips
            ))
        
        # Partial Close (XP: 2000+)
        if TradeManagementFeature.PARTIAL_CLOSE in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.PARTIAL_CLOSE,
                partial_close_percent=Decimal('50'),  # Close 50% at 1R
                partial_close_at_pips=sl_pips
            ))
        
        # Runner Mode (XP: 5000+)
        if TradeManagementFeature.RUNNER_MODE in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.RUNNER_MODE,
                partial_close_percent=Decimal('75'),  # Close 75% at 1.5R
                partial_close_at_pips=sl_pips * Decimal('1.5'),
                runner_target_rr=Decimal('5.0')  # Let 25% run to 5R
            ))
        
        # Zero Risk Runner (XP: 15000+) - The Holy Grail
        if TradeManagementFeature.ZERO_RISK_RUNNER in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.ZERO_RISK_RUNNER,
                partial_close_percent=Decimal('50'),  # Close 50% at 2R (covers risk + profit)
                partial_close_at_pips=sl_pips * Decimal('2'),
                breakeven_trigger_pips=sl_pips * Decimal('2'),  # Move SL to BE after partial
                runner_target_rr=Decimal('10.0')  # Let runner go for 10R+
            ))
        
        # Leroy Jenkins Mode (XP: 20000+) - YOLO with strategy
        if TradeManagementFeature.LEROY_JENKINS in unlocked:
            plans.append(TradeManagementPlan(
                feature=TradeManagementFeature.LEROY_JENKINS,
                trailing_start_pips=sl_pips * Decimal('0.5'),  # Aggressive early trailing
                trailing_distance_pips=sl_pips * Decimal('0.25'),  # Tight trail
                partial_close_percent=Decimal('25'),  # Take 25% quickly
                partial_close_at_pips=sl_pips * Decimal('0.5'),
                runner_target_rr=Decimal('20.0')  # Moon or bust
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
        
        # Validate inputs
        symbol = validate_symbol(symbol)
        total_risk_percent = validate_risk_percent(total_risk_percent)
        
        if not zones:
            raise ValidationError("No price zones provided")
        
        if len(zones) > 10:
            raise ValidationError("Too many price zones (max 10)")
        
        positions = []
        risk_per_zone = total_risk_percent / Decimal(str(len(zones)))
        
        for i, zone_price in enumerate(zones):
            # Validate zone price
            zone_price = validate_price(zone_price)
            
            # Adjust risk for each zone
            zone_risk = risk_per_zone * (Decimal('1') + Decimal(str(i)) * Decimal('0.1'))  # Slightly increase risk for better zones
            
            positions.append({
                'zone': i + 1,
                'price': float(zone_price),
                'risk_percent': float(zone_risk),
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