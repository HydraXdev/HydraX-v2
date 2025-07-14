#!/usr/bin/env python3
"""
BITTEN Game Rules Engine for Backtesting
Enforces ALL game mechanics and rules during backtesting
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import logging
from enum import Enum
import sys

# Import BITTEN components
sys.path.append('/root/HydraX-v2/src')
from bitten_core.fire_modes import TierLevel, FireMode, TIER_CONFIGS, get_tcs_threshold_for_mode

class GameRuleViolation(Exception):
    """Raised when a game rule is violated"""
    pass

@dataclass
class UserGameState:
    """Track user's game state during backtesting"""
    user_id: str
    tier: TierLevel
    account_balance: float
    daily_shots_used: int = 0
    daily_risk_used: float = 0.0  # Percentage of account
    last_shot_time: Optional[datetime] = None
    active_positions: List[str] = field(default_factory=list)
    chaingun_sequences_today: int = 0
    current_chaingun_shot: int = 0
    chaingun_start_time: Optional[datetime] = None
    in_cooldown_until: Optional[datetime] = None
    daily_drawdown: float = 0.0
    starting_daily_balance: float = 0.0
    stealth_mode_active: bool = False
    auto_fire_enabled: bool = False
    news_pause_until: Optional[datetime] = None
    
    def __post_init__(self):
        if self.starting_daily_balance == 0.0:
            self.starting_daily_balance = self.account_balance

@dataclass  
class NewsEvent:
    """News event that affects trading"""
    timestamp: datetime
    currency: str
    impact: str  # LOW, MEDIUM, HIGH
    event_name: str
    duration_minutes: int = 30  # How long to pause trading

@dataclass
class TradeAttempt:
    """Represents an attempt to execute a trade"""
    user_id: str
    symbol: str
    direction: str
    volume: float
    tcs_score: int
    fire_mode: FireMode
    timestamp: datetime
    signal_type: str  # ARCADE, SNIPER
    entry_price: float
    stop_loss: float
    take_profit: float
    
class BittenGameRulesEngine:
    """Enforces all BITTEN game rules during backtesting"""
    
    def __init__(self):
        self.user_states: Dict[str, UserGameState] = {}
        self.news_events: List[NewsEvent] = []
        self.midnight_hammer_events: List[datetime] = []
        self.current_date: Optional[datetime] = None
        
        # Game constants from RULES_OF_ENGAGEMENT.md
        self.COOLDOWN_MINUTES = 30
        self.DAILY_DRAWDOWN_LIMIT = 0.07  # -7%
        self.AUTO_FIRE_DAILY_RISK_LIMIT = 0.10  # 10%
        self.MAX_CONCURRENT_POSITIONS = 3
        self.NEWS_PAUSE_MINUTES = 30
        self.CHAINGUN_TIME_LIMIT_HOURS = 4
        self.MAX_CHAINGUN_SEQUENCES_PER_DAY = 2
        self.MIDNIGHT_HAMMER_RISK = 0.05  # 5%
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for game rules violations"""
        self.logger = logging.getLogger("GameRules")
        
    def initialize_user(self, user_id: str, tier: TierLevel, initial_balance: float):
        """Initialize user game state"""
        self.user_states[user_id] = UserGameState(
            user_id=user_id,
            tier=tier,
            account_balance=initial_balance,
            starting_daily_balance=initial_balance
        )
        
    def reset_daily_limits(self, current_time: datetime):
        """Reset daily limits for all users"""
        if self.current_date and current_time.date() != self.current_date.date():
            self.logger.info(f"Resetting daily limits for {current_time.date()}")
            
            for user_state in self.user_states.values():
                user_state.daily_shots_used = 0
                user_state.daily_risk_used = 0.0
                user_state.chaingun_sequences_today = 0
                user_state.daily_drawdown = 0.0
                user_state.starting_daily_balance = user_state.account_balance
                
        self.current_date = current_time
        
    def add_news_event(self, timestamp: datetime, currency: str, impact: str, event_name: str):
        """Add a news event that affects trading"""
        duration = 60 if impact == "HIGH" else 30 if impact == "MEDIUM" else 15
        self.news_events.append(NewsEvent(
            timestamp=timestamp,
            currency=currency,
            impact=impact,
            event_name=event_name,
            duration_minutes=duration
        ))
        
    def check_news_restrictions(self, trade_attempt: TradeAttempt) -> bool:
        """Check if trading is restricted due to news events"""
        relevant_currencies = self._get_currencies_for_pair(trade_attempt.symbol)
        
        for event in self.news_events:
            if event.currency in relevant_currencies:
                event_end = event.timestamp + timedelta(minutes=event.duration_minutes)
                if event.timestamp <= trade_attempt.timestamp <= event_end:
                    if event.impact in ["HIGH", "MEDIUM"]:
                        self.logger.warning(f"Trade blocked due to {event.impact} news: {event.event_name}")
                        return False
        return True
        
    def _get_currencies_for_pair(self, symbol: str) -> List[str]:
        """Get currencies involved in trading pair"""
        if len(symbol) == 6:
            return [symbol[:3], symbol[3:]]
        return []
        
    def validate_trade_attempt(self, trade_attempt: TradeAttempt) -> Tuple[bool, str]:
        """Validate a trade attempt against all game rules"""
        user_state = self.user_states.get(trade_attempt.user_id)
        if not user_state:
            return False, "User not initialized"
            
        # Reset daily limits if new day
        self.reset_daily_limits(trade_attempt.timestamp)
        
        try:
            # 1. TCS Requirements
            self._validate_tcs_requirements(trade_attempt, user_state)
            
            # 2. Daily Shot Limits
            self._validate_daily_shot_limits(trade_attempt, user_state)
            
            # 3. Cooldown Restrictions
            self._validate_cooldown_restrictions(trade_attempt, user_state)
            
            # 4. Risk Management
            self._validate_risk_management(trade_attempt, user_state)
            
            # 5. Daily Drawdown Protection
            self._validate_drawdown_protection(trade_attempt, user_state)
            
            # 6. News Event Restrictions
            self._validate_news_restrictions(trade_attempt)
            
            # 7. Fire Mode Specific Rules
            self._validate_fire_mode_rules(trade_attempt, user_state)
            
            # 8. Position Limits
            self._validate_position_limits(trade_attempt, user_state)
            
            # 9. Tier Access Rights
            self._validate_tier_access(trade_attempt, user_state)
            
            return True, "Trade approved"
            
        except GameRuleViolation as e:
            return False, str(e)
            
    def _validate_tcs_requirements(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate TCS requirements per THE LAW"""
        required_tcs = get_tcs_threshold_for_mode(user_state.tier, trade_attempt.fire_mode)
        
        if trade_attempt.tcs_score < required_tcs:
            raise GameRuleViolation(
                f"TCS {trade_attempt.tcs_score}% below {user_state.tier.value} requirement of {required_tcs}%"
            )
            
    def _validate_daily_shot_limits(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate daily shot limits"""
        tier_config = TIER_CONFIGS[user_state.tier]
        
        # APEX has unlimited shots
        if user_state.tier == TierLevel.APEX:
            return
            
        if user_state.daily_shots_used >= tier_config.daily_shots:
            raise GameRuleViolation(
                f"Daily shot limit exceeded: {user_state.daily_shots_used}/{tier_config.daily_shots}"
            )
            
    def _validate_cooldown_restrictions(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate cooldown restrictions"""
        if user_state.in_cooldown_until and trade_attempt.timestamp < user_state.in_cooldown_until:
            remaining = (user_state.in_cooldown_until - trade_attempt.timestamp).total_seconds() / 60
            raise GameRuleViolation(f"Cooldown active: {remaining:.1f} minutes remaining")
            
        if user_state.last_shot_time:
            time_since_last = (trade_attempt.timestamp - user_state.last_shot_time).total_seconds() / 60
            if time_since_last < self.COOLDOWN_MINUTES:
                raise GameRuleViolation(
                    f"Cooldown violation: Only {time_since_last:.1f} minutes since last shot"
                )
                
    def _validate_risk_management(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate risk management rules"""
        # Calculate trade risk
        pip_value = 0.0001 if trade_attempt.symbol not in ['USDJPY', 'GBPJPY', 'EURJPY'] else 0.01
        risk_pips = abs(trade_attempt.entry_price - trade_attempt.stop_loss) / pip_value
        
        # Standard risk calculation (2% unless special mode)
        if trade_attempt.fire_mode == FireMode.CHAINGUN:
            # CHAINGUN progressive risk
            chaingun_multipliers = [1, 2, 4, 4]  # Capped at 4x
            shot_number = min(user_state.current_chaingun_shot, 3)
            risk_percent = 0.02 * chaingun_multipliers[shot_number]
        elif trade_attempt.fire_mode == FireMode.MIDNIGHT_HAMMER:
            risk_percent = self.MIDNIGHT_HAMMER_RISK
        else:
            risk_percent = 0.02  # Standard 2%
            
        # Check if risk would exceed daily limits
        new_daily_risk = user_state.daily_risk_used + risk_percent
        
        if trade_attempt.fire_mode == FireMode.AUTO_FIRE:
            if new_daily_risk > self.AUTO_FIRE_DAILY_RISK_LIMIT:
                raise GameRuleViolation(
                    f"AUTO-FIRE daily risk limit: {new_daily_risk:.1%} > {self.AUTO_FIRE_DAILY_RISK_LIMIT:.1%}"
                )
                
        # CHAINGUN cannot exceed 20% total risk
        if trade_attempt.fire_mode == FireMode.CHAINGUN:
            if new_daily_risk > 0.20:
                raise GameRuleViolation(
                    f"CHAINGUN risk limit: {new_daily_risk:.1%} > 20%"
                )
                
    def _validate_drawdown_protection(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate daily drawdown protection (-7% limit)"""
        current_drawdown = (user_state.starting_daily_balance - user_state.account_balance) / user_state.starting_daily_balance
        
        if current_drawdown >= self.DAILY_DRAWDOWN_LIMIT:
            raise GameRuleViolation(
                f"Daily drawdown limit reached: {current_drawdown:.1%} >= {self.DAILY_DRAWDOWN_LIMIT:.1%}"
            )
            
    def _validate_news_restrictions(self, trade_attempt: TradeAttempt):
        """Validate news event restrictions"""
        if not self.check_news_restrictions(trade_attempt):
            raise GameRuleViolation("Trading paused due to high-impact news event")
            
    def _validate_fire_mode_rules(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate specific fire mode rules"""
        
        if trade_attempt.fire_mode == FireMode.CHAINGUN:
            self._validate_chaingun_rules(trade_attempt, user_state)
        elif trade_attempt.fire_mode == FireMode.AUTO_FIRE:
            self._validate_auto_fire_rules(trade_attempt, user_state)
        elif trade_attempt.fire_mode == FireMode.STEALTH:
            self._validate_stealth_rules(trade_attempt, user_state)
        elif trade_attempt.fire_mode == FireMode.MIDNIGHT_HAMMER:
            self._validate_midnight_hammer_rules(trade_attempt, user_state)
            
    def _validate_chaingun_rules(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate CHAINGUN mode rules"""
        # Check daily sequence limit
        if user_state.chaingun_sequences_today >= self.MAX_CHAINGUN_SEQUENCES_PER_DAY:
            raise GameRuleViolation(f"CHAINGUN daily limit: {self.MAX_CHAINGUN_SEQUENCES_PER_DAY} sequences")
            
        # Check time limit if sequence is active
        if user_state.chaingun_start_time:
            elapsed = (trade_attempt.timestamp - user_state.chaingun_start_time).total_seconds() / 3600
            if elapsed > self.CHAINGUN_TIME_LIMIT_HOURS:
                raise GameRuleViolation(f"CHAINGUN time limit: {elapsed:.1f}h > {self.CHAINGUN_TIME_LIMIT_HOURS}h")
                
        # Progressive TCS requirements
        required_tcs_progression = [85, 87, 89, 91]
        shot_number = min(user_state.current_chaingun_shot, 3)
        required_tcs = required_tcs_progression[shot_number]
        
        if trade_attempt.tcs_score < required_tcs:
            raise GameRuleViolation(
                f"CHAINGUN shot {shot_number + 1} requires {required_tcs}% TCS, got {trade_attempt.tcs_score}%"
            )
            
    def _validate_auto_fire_rules(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate AUTO-FIRE mode rules"""
        # AUTO-FIRE requires 91%+ TCS
        if trade_attempt.tcs_score < 91:
            raise GameRuleViolation(f"AUTO-FIRE requires 91%+ TCS, got {trade_attempt.tcs_score}%")
            
    def _validate_stealth_rules(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate STEALTH mode rules"""
        # STEALTH is APEX exclusive
        if user_state.tier != TierLevel.APEX:
            raise GameRuleViolation("STEALTH mode is APEX exclusive")
            
    def _validate_midnight_hammer_rules(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate MIDNIGHT HAMMER event rules"""
        # Must be 95%+ TCS
        if trade_attempt.tcs_score < 95:
            raise GameRuleViolation(f"MIDNIGHT HAMMER requires 95%+ TCS, got {trade_attempt.tcs_score}%")
            
        # Must be during active event window
        event_active = False
        for event_time in self.midnight_hammer_events:
            if abs((trade_attempt.timestamp - event_time).total_seconds()) <= 300:  # 5 minute window
                event_active = True
                break
                
        if not event_active:
            raise GameRuleViolation("No active MIDNIGHT HAMMER event")
            
    def _validate_position_limits(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate position limits"""
        if trade_attempt.fire_mode == FireMode.AUTO_FIRE:
            if len(user_state.active_positions) >= self.MAX_CONCURRENT_POSITIONS:
                raise GameRuleViolation(
                    f"AUTO-FIRE position limit: {len(user_state.active_positions)}/{self.MAX_CONCURRENT_POSITIONS}"
                )
                
    def _validate_tier_access(self, trade_attempt: TradeAttempt, user_state: UserGameState):
        """Validate tier access to fire modes"""
        tier_config = TIER_CONFIGS[user_state.tier]
        
        if trade_attempt.fire_mode == FireMode.CHAINGUN and not tier_config.has_chaingun:
            raise GameRuleViolation(f"{user_state.tier.value} tier cannot access CHAINGUN mode")
            
        if trade_attempt.fire_mode == FireMode.AUTO_FIRE and not tier_config.has_autofire:
            raise GameRuleViolation(f"{user_state.tier.value} tier cannot access AUTO-FIRE mode")
            
        if trade_attempt.fire_mode == FireMode.STEALTH and not tier_config.has_stealth:
            raise GameRuleViolation(f"{user_state.tier.value} tier cannot access STEALTH mode")
            
    def execute_trade(self, trade_attempt: TradeAttempt) -> Dict[str, Any]:
        """Execute a validated trade and update game state"""
        user_state = self.user_states[trade_attempt.user_id]
        
        # Update game state
        user_state.daily_shots_used += 1
        user_state.last_shot_time = trade_attempt.timestamp
        user_state.in_cooldown_until = trade_attempt.timestamp + timedelta(minutes=self.COOLDOWN_MINUTES)
        
        # Calculate and add risk
        if trade_attempt.fire_mode == FireMode.CHAINGUN:
            chaingun_multipliers = [1, 2, 4, 4]
            shot_number = min(user_state.current_chaingun_shot, 3)
            risk_percent = 0.02 * chaingun_multipliers[shot_number]
            user_state.current_chaingun_shot += 1
        elif trade_attempt.fire_mode == FireMode.MIDNIGHT_HAMMER:
            risk_percent = self.MIDNIGHT_HAMMER_RISK
        else:
            risk_percent = 0.02
            
        user_state.daily_risk_used += risk_percent
        
        # Add to active positions
        trade_id = f"{trade_attempt.symbol}_{trade_attempt.timestamp.strftime('%Y%m%d_%H%M%S')}"
        user_state.active_positions.append(trade_id)
        
        # STEALTH mode modifications
        stealth_modifications = {}
        if trade_attempt.fire_mode == FireMode.STEALTH:
            # Entry delay randomization
            entry_delay = np.random.randint(2, 6)  # 2-5 minutes
            # Position size variation
            size_multiplier = 0.8 + np.random.random() * 0.4  # 80-120%
            # Intentional losses (5-8% of trades)
            force_loss = np.random.random() < 0.065  # 6.5% average
            
            stealth_modifications = {
                "entry_delay_minutes": entry_delay,
                "size_multiplier": size_multiplier,
                "force_loss": force_loss
            }
            
        return {
            "trade_id": trade_id,
            "approved": True,
            "risk_percent": risk_percent,
            "stealth_modifications": stealth_modifications,
            "user_state": user_state
        }
        
    def close_trade(self, user_id: str, trade_id: str, profit_loss: float):
        """Close a trade and update game state"""
        user_state = self.user_states.get(user_id)
        if not user_state:
            return
            
        # Remove from active positions
        if trade_id in user_state.active_positions:
            user_state.active_positions.remove(trade_id)
            
        # Update account balance
        user_state.account_balance += profit_loss
        
        # Update daily drawdown
        current_drawdown = (user_state.starting_daily_balance - user_state.account_balance) / user_state.starting_daily_balance
        user_state.daily_drawdown = max(user_state.daily_drawdown, current_drawdown)
        
        # CHAINGUN sequence management
        if user_state.current_chaingun_shot > 0:
            if profit_loss > 0:
                # Winning shot - offer parachute (for backtesting, continue sequence)
                pass
            else:
                # Losing shot - end sequence
                user_state.current_chaingun_shot = 0
                user_state.chaingun_start_time = None
                user_state.chaingun_sequences_today += 1
                
    def get_game_state_summary(self, user_id: str) -> Dict[str, Any]:
        """Get current game state summary for user"""
        user_state = self.user_states.get(user_id)
        if not user_state:
            return {}
            
        tier_config = TIER_CONFIGS[user_state.tier]
        
        return {
            "user_id": user_id,
            "tier": user_state.tier.value,
            "account_balance": user_state.account_balance,
            "daily_shots_used": user_state.daily_shots_used,
            "daily_shots_limit": tier_config.daily_shots,
            "daily_risk_used": user_state.daily_risk_used,
            "daily_drawdown": user_state.daily_drawdown,
            "active_positions": len(user_state.active_positions),
            "chaingun_sequences_today": user_state.chaingun_sequences_today,
            "in_cooldown": user_state.in_cooldown_until > datetime.now() if user_state.in_cooldown_until else False,
            "available_fire_modes": self._get_available_fire_modes(user_state)
        }
        
    def _get_available_fire_modes(self, user_state: UserGameState) -> List[str]:
        """Get available fire modes for user's tier"""
        tier_config = TIER_CONFIGS[user_state.tier]
        modes = ["SINGLE_SHOT"]
        
        if tier_config.has_chaingun:
            modes.append("CHAINGUN")
        if tier_config.has_autofire:
            modes.append("AUTO_FIRE")
        if tier_config.has_stealth:
            modes.append("STEALTH")
            
        return modes
        
    def generate_news_events(self, start_date: datetime, end_date: datetime):
        """Generate realistic news events for backtesting"""
        # Generate news events (simplified for backtesting)
        current = start_date
        while current < end_date:
            # Add some high-impact events
            if np.random.random() < 0.1:  # 10% chance per day
                hour = np.random.choice([8, 14, 16])  # Common news times
                event_time = current.replace(hour=hour, minute=30)
                
                currency = np.random.choice(["USD", "EUR", "GBP", "JPY"])
                impact = np.random.choice(["HIGH", "MEDIUM"], p=[0.3, 0.7])
                
                self.add_news_event(
                    timestamp=event_time,
                    currency=currency,
                    impact=impact,
                    event_name=f"{currency} Economic Data"
                )
                
            current += timedelta(days=1)
            
        self.logger.info(f"Generated {len(self.news_events)} news events")
        
    def generate_midnight_hammer_events(self, start_date: datetime, end_date: datetime):
        """Generate MIDNIGHT HAMMER events (1-2 per month)"""
        current = start_date
        while current < end_date:
            # 1-2 events per month
            if current.day in [15, 30] and np.random.random() < 0.7:
                # Random time during day
                hour = np.random.randint(8, 20)
                minute = np.random.randint(0, 60)
                event_time = current.replace(hour=hour, minute=minute)
                self.midnight_hammer_events.append(event_time)
                
            current += timedelta(days=1)
            
        self.logger.info(f"Generated {len(self.midnight_hammer_events)} MIDNIGHT HAMMER events")

# Integration functions for backtesting engine
def create_game_rules_engine() -> BittenGameRulesEngine:
    """Create and configure game rules engine"""
    return BittenGameRulesEngine()

def validate_backtesting_trade(game_engine: BittenGameRulesEngine, 
                             user_id: str, tier: str, signal: Dict) -> Tuple[bool, str, Dict]:
    """Validate a backtesting trade against game rules"""
    
    tier_enum = TierLevel(tier.lower())
    
    trade_attempt = TradeAttempt(
        user_id=user_id,
        symbol=signal['symbol'],
        direction=signal['direction'],
        volume=0.01,  # Standard lot
        tcs_score=signal['tcs_score'],
        fire_mode=FireMode.SINGLE_SHOT,  # Default mode
        timestamp=signal['timestamp'],
        signal_type=signal.get('signal_type', 'ARCADE'),
        entry_price=signal['entry_price'],
        stop_loss=signal['stop_loss'],
        take_profit=signal['take_profit']
    )
    
    # Validate the trade
    is_valid, message = game_engine.validate_trade_attempt(trade_attempt)
    
    execution_result = {}
    if is_valid:
        execution_result = game_engine.execute_trade(trade_attempt)
        
    return is_valid, message, execution_result