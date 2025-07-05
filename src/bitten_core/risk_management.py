"""
BITTEN Risk Management System
Dynamic position sizing and XP-based unlockable trade management features
"""

import math
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import logging

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
    balance: float
    equity: float
    margin: float
    free_margin: float
    currency: str = "USD"
    leverage: int = 100

@dataclass
class RiskProfile:
    """User's risk profile and preferences"""
    user_id: int
    max_risk_percent: float = 2.0      # Default 2% per BITTEN rules
    max_positions: int = 3             # Max concurrent positions
    daily_loss_limit: float = 7.0      # -7% daily drawdown limit
    win_rate: float = 0.5              # Historical win rate
    avg_rr_ratio: float = 1.5          # Average risk/reward ratio
    current_xp: int = 0                # User's current XP
    tier_level: str = "NIBBLER"        # User's tier
    
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
    
class RiskCalculator:
    """
    Advanced risk calculator with XP-based features
    Handles position sizing and trade management planning
    """
    
    def __init__(self):
        # Symbol specifications (would come from broker in production)
        self.symbol_specs = {
            'XAUUSD': {'pip_value': 0.1, 'contract_size': 100, 'min_lot': 0.01, 'max_lot': 100},
            'EURUSD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'GBPUSD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'USDJPY': {'pip_value': 0.01, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'USDCAD': {'pip_value': 0.0001, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100},
            'GBPJPY': {'pip_value': 0.01, 'contract_size': 100000, 'min_lot': 0.01, 'max_lot': 100}
        }
        
        # Tier-based risk adjustments
        self.tier_multipliers = {
            'NIBBLER': 1.0,      # Standard risk
            'FANG': 1.1,         # 10% more risk allowed
            'COMMANDER': 1.2,    # 20% more risk allowed
            'APEX': 1.5          # 50% more risk allowed (elite)
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
            # Get symbol specifications
            specs = self.symbol_specs.get(symbol, self.symbol_specs['EURUSD'])
            
            # Calculate pip risk
            pip_risk = abs(entry_price - stop_loss_price) / specs['pip_value']
            
            # Get tier multiplier
            tier_mult = self.tier_multipliers.get(profile.tier_level, 1.0)
            
            # Calculate risk amount based on mode
            if risk_mode == RiskMode.PERCENTAGE:
                # Standard percentage risk with tier adjustment
                risk_percent = min(profile.max_risk_percent * tier_mult, 5.0)  # Cap at 5%
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
            if symbol == 'XAUUSD':
                # Gold has different calculation
                pip_value_per_lot = specs['pip_value'] * specs['contract_size']
            else:
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
                'mode': risk_mode.value
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