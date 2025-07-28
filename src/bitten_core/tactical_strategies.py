"""
NIBBLER Tactical Strategy System
4 military-style tactics for signal execution with progressive skill building

CONSTRAINTS:
- 2% risk per trade (fixed)
- Max 6 shots per day total
- 1:2 max R:R (RAPID RAID signals only)
- Hard 6% drawdown limit
- 1 trade open at a time
- TCS filtering (74-99 range)
- Daily tactic selection, locked until midnight
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class TacticalStrategy(Enum):
    """4 Tactical strategies for NIBBLER signal execution"""
    LONE_WOLF = "LONE_WOLF"           # Training wheels - 4 shots, any 74+ TCS
    FIRST_BLOOD = "FIRST_BLOOD"       # Escalation - 4 shots, escalating requirements
    DOUBLE_TAP = "DOUBLE_TAP"         # Precision - 2 shots, 85+ TCS, same direction
    TACTICAL_COMMAND = "TACTICAL_COMMAND"  # Mastery - choice between sniper or volume

@dataclass
class ShotRequirement:
    """Requirements for each shot in a strategy"""
    shot_number: int
    min_tcs: int
    risk_reward_ratio: float
    description: str

@dataclass
class TacticalConfig:
    """Configuration for each tactical strategy"""
    strategy: TacticalStrategy
    display_name: str
    description: str
    unlock_xp: int
    max_shots: int
    shot_requirements: List[ShotRequirement]
    stop_conditions: List[str]
    daily_potential: str
    teaching_focus: str
    psychology: str

@dataclass
class DailyTacticalState:
    """User's daily tactical state"""
    user_id: str
    selected_strategy: TacticalStrategy
    shots_fired: int = 0
    wins_today: int = 0
    losses_today: int = 0
    daily_pnl: float = 0.0
    shots_taken: List[Dict] = field(default_factory=list)
    locked_until: Optional[datetime] = None
    last_reset: datetime = field(default_factory=datetime.now)

class TacticalStrategyManager:
    """Manager for NIBBLER tactical strategies"""
    
    # Strategy configurations
    TACTICAL_CONFIGS = {
        TacticalStrategy.LONE_WOLF: TacticalConfig(
            strategy=TacticalStrategy.LONE_WOLF,
            display_name="🐺 Lone Wolf",
            description="Training wheels - learn basics without getting hurt",
            unlock_xp=0,  # Always available
            max_shots=4,
            shot_requirements=[
                ShotRequirement(1, 74, 1.3, "Any signal 74+ TCS"),
                ShotRequirement(2, 74, 1.3, "Any signal 74+ TCS"), 
                ShotRequirement(3, 74, 1.3, "Any signal 74+ TCS"),
                ShotRequirement(4, 74, 1.3, "Any signal 74+ TCS")
            ],
            stop_conditions=["max_shots_reached", "6_percent_drawdown"],
            daily_potential="7.24%",
            teaching_focus="Signal recognition, basic execution, market rhythm",
            psychology="Learn the basics, take what you can get"
        ),
        
        TacticalStrategy.FIRST_BLOOD: TacticalConfig(
            strategy=TacticalStrategy.FIRST_BLOOD,
            display_name="🎯 First Blood",
            description="Escalation mastery - build momentum with house money",
            unlock_xp=120,
            max_shots=4,
            shot_requirements=[
                ShotRequirement(1, 75, 1.25, "Confidence builder - 75+ TCS"),
                ShotRequirement(2, 78, 1.5, "Momentum building - 78+ TCS"),
                ShotRequirement(3, 80, 1.75, "House money aggression - 80+ TCS"),
                ShotRequirement(4, 85, 1.9, "Elite execution - 85+ TCS")
            ],
            stop_conditions=["after_2_wins", "max_shots_reached", "6_percent_drawdown"],
            daily_potential="8-12%",
            teaching_focus="Momentum psychology, quality escalation, profit-taking discipline",
            psychology="Start easy, get confident, then swing bigger with house money"
        ),
        
        TacticalStrategy.DOUBLE_TAP: TacticalConfig(
            strategy=TacticalStrategy.DOUBLE_TAP,
            display_name="💥 Double Tap",
            description="Precision selection - quality over quantity",
            unlock_xp=240,
            max_shots=2,
            shot_requirements=[
                ShotRequirement(1, 85, 1.8, "Elite quality - 85+ TCS, note direction"),
                ShotRequirement(2, 85, 1.8, "Same direction as shot 1 - 85+ TCS")
            ],
            stop_conditions=["max_shots_reached", "6_percent_drawdown"],
            daily_potential="10.72%",
            teaching_focus="Patience, signal quality assessment, directional bias",
            psychology="Quality over quantity, directional conviction"
        ),
        
        TacticalStrategy.TACTICAL_COMMAND: TacticalConfig(
            strategy=TacticalStrategy.TACTICAL_COMMAND,
            display_name="⚡ Tactical Command",
            description="Earned mastery - choose your battlefield",
            unlock_xp=360,
            max_shots=6,  # Variable based on choice
            shot_requirements=[
                # Will be set dynamically based on user choice
            ],
            stop_conditions=["max_shots_reached", "6_percent_drawdown"],
            daily_potential="6.8% (sniper) or 12-15% (volume)",
            teaching_focus="Complete tactical flexibility based on market conditions",
            psychology="Master level - ultimate precision OR proven volume capability"
        )
    }
    
    def __init__(self, data_dir: str = "data/tactical_strategies"):
        self.data_dir = data_dir
        self.daily_states = {}  # Cache for user daily states
        
    def get_unlocked_strategies(self, user_xp: int) -> List[TacticalStrategy]:
        """Get strategies user has unlocked based on XP"""
        unlocked = []
        
        for strategy, config in self.TACTICAL_CONFIGS.items():
            if user_xp >= config.unlock_xp:
                unlocked.append(strategy)
        
        return sorted(unlocked, key=lambda s: self.TACTICAL_CONFIGS[s].unlock_xp)
    
    def get_daily_state(self, user_id: str) -> DailyTacticalState:
        """Get user's current daily tactical state"""
        if user_id not in self.daily_states:
            self._load_daily_state(user_id)
        
        state = self.daily_states[user_id]
        
        # Check if we need to reset for new day
        if self._should_reset_daily_state(state):
            state = self._reset_daily_state(user_id)
        
        return state
    
    def select_daily_strategy(self, user_id: str, strategy: TacticalStrategy, user_xp: int) -> Tuple[bool, str]:
        """Select strategy for the day (locked until midnight)"""
        
        # Check if strategy is unlocked
        if user_xp < self.TACTICAL_CONFIGS[strategy].unlock_xp:
            return False, f"Strategy not unlocked. Need {self.TACTICAL_CONFIGS[strategy].unlock_xp} XP."
        
        state = self.get_daily_state(user_id)
        
        # Check if already locked for today
        if state.locked_until and datetime.now() < state.locked_until:
            hours_remaining = (state.locked_until - datetime.now()).total_seconds() / 3600
            return False, f"Strategy locked until midnight ({hours_remaining:.1f} hours remaining)"
        
        # Set new strategy
        state.selected_strategy = strategy
        state.locked_until = self._get_next_midnight()
        state.shots_fired = 0
        state.wins_today = 0
        state.losses_today = 0
        state.daily_pnl = 0.0
        state.shots_taken = []
        
        # Handle Tactical Command special cases
        if strategy == TacticalStrategy.TACTICAL_COMMAND:
            # Will be set when user makes sub-choice
            pass
        
        self._save_daily_state(state)
        
        config = self.TACTICAL_CONFIGS[strategy]
        return True, f"✅ {config.display_name} selected for today!\n{config.psychology}"
    
    def can_fire_shot(self, user_id: str, signal_tcs: int, signal_direction: str) -> Tuple[bool, str, Optional[Dict]]:
        """Check if user can fire at this signal with current strategy"""
        
        state = self.get_daily_state(user_id)
        
        if not state.selected_strategy:
            return False, "No strategy selected for today", None
        
        config = self.TACTICAL_CONFIGS[state.selected_strategy]
        
        # Check if shots remaining
        if state.shots_fired >= config.max_shots:
            return False, f"No shots remaining (used {state.shots_fired}/{config.max_shots})", None
        
        # Check stop conditions
        stop_reason = self._check_stop_conditions(state, config)
        if stop_reason:
            return False, f"Stop condition triggered: {stop_reason}", None
        
        # Get next shot requirements
        next_shot_num = state.shots_fired + 1
        shot_req = self._get_shot_requirement(config, next_shot_num, state)
        
        if not shot_req:
            return False, "Invalid shot configuration", None
        
        # Check TCS requirement
        if signal_tcs < shot_req.min_tcs:
            return False, f"Shot {next_shot_num} needs {shot_req.min_tcs}+ TCS (signal: {signal_tcs})", None
        
        # Check special strategy requirements
        strategy_check = self._check_strategy_specific_requirements(state, signal_direction, config)
        if not strategy_check[0]:
            return False, strategy_check[1], None
        
        # Return shot info
        shot_info = {
            "shot_number": next_shot_num,
            "risk_reward": shot_req.risk_reward_ratio,
            "description": shot_req.description,
            "strategy": state.selected_strategy.value
        }
        
        return True, f"✅ FIRE SHOT {next_shot_num}!", shot_info
    
    def fire_shot(self, user_id: str, signal_data: Dict, trade_result: str) -> Dict:
        """Execute a shot and update daily state"""
        
        state = self.get_daily_state(user_id)
        config = self.TACTICAL_CONFIGS[state.selected_strategy]
        
        shot_number = state.shots_fired + 1
        shot_req = self._get_shot_requirement(config, shot_number, state)
        
        # Calculate PnL (2% risk per trade)
        risk_amount = 2.0  # 2% risk
        if trade_result == "WIN":
            pnl = risk_amount * shot_req.risk_reward_ratio
            state.wins_today += 1
        else:
            pnl = -risk_amount
            state.losses_today += 1
        
        state.daily_pnl += pnl
        
        # Record the shot
        shot_record = {
            "shot_number": shot_number,
            "signal_tcs": signal_data.get('tcs', 0),
            "signal_pair": signal_data.get('pair', ''),
            "signal_direction": signal_data.get('direction', ''),
            "risk_reward": shot_req.risk_reward_ratio,
            "result": trade_result,
            "pnl": pnl,
            "timestamp": datetime.now().isoformat()
        }
        
        state.shots_fired += 1
        state.shots_taken.append(shot_record)
        
        self._save_daily_state(state)
        
        # Check if should auto-stop
        should_stop = self._check_stop_conditions(state, config)
        
        return {
            "shot_fired": True,
            "shot_number": shot_number,
            "pnl": pnl,
            "daily_pnl": state.daily_pnl,
            "shots_remaining": config.max_shots - state.shots_fired,
            "wins_today": state.wins_today,
            "losses_today": state.losses_today,
            "should_stop": bool(should_stop),
            "stop_reason": should_stop if should_stop else None
        }
    
    def filter_signal_for_user(self, user_id: str, signal):
        """Filter signal based on user's tactical strategy requirements"""
        if not signal:
            return None
        
        try:
            # Check if user can fire at this signal with their current tactical strategy
            can_fire, reason, shot_info = self.can_fire_shot(
                user_id, 
                signal.tcs_score,
                signal.direction.value
            )
            
            if not can_fire:
                logger.info(f"Signal blocked by tactical strategy: {reason}")
                return None
            
            # Apply tactical modifications to signal
            if shot_info:
                signal.position_size_multiplier = 1.0  # Always 2% risk for NIBBLER
                
                # Adjust take profit based on tactical R:R
                if hasattr(signal, 'take_profit') and shot_info.get('risk_reward'):
                    # Calculate new TP based on tactical R:R requirement
                    entry_price = signal.entry_price
                    stop_loss = signal.stop_loss
                    risk_distance = abs(entry_price - stop_loss)
                    reward_distance = risk_distance * shot_info['risk_reward']
                    
                    if signal.direction.value == 'BUY':
                        signal.take_profit = entry_price + reward_distance
                    else:
                        signal.take_profit = entry_price - reward_distance
                
                # Add tactical metadata
                if not hasattr(signal, 'special_conditions') or signal.special_conditions is None:
                    signal.special_conditions = {}
                signal.special_conditions.update({
                    'tactical_strategy': shot_info['strategy'],
                    'shot_number': shot_info['shot_number'],
                    'tactical_rr': shot_info['risk_reward'],
                    'shot_description': shot_info['description']
                })
            
            return signal
            
        except Exception as e:
            logger.error(f"Error applying tactical strategy filter: {e}")
            # Return original signal if tactical processing fails
            return signal
    
    def get_strategy_stats(self, user_id: str, strategy: TacticalStrategy) -> Dict:
        """Get user's performance stats for a specific strategy"""
        # This would load historical data in production
        # For now, return placeholder stats
        return {
            "strategy": strategy.value,
            "total_days": 15,
            "total_shots": 45,
            "wins": 32,
            "losses": 13,
            "win_rate": 71.1,
            "avg_daily_pnl": 8.2,
            "best_day": 15.3,
            "worst_day": -4.1
        }
    
    def _get_shot_requirement(self, config: TacticalConfig, shot_number: int, state: DailyTacticalState) -> Optional[ShotRequirement]:
        """Get shot requirement for specific shot number"""
        
        if config.strategy == TacticalStrategy.TACTICAL_COMMAND:
            # Handle dynamic requirements for Tactical Command
            # This would be set based on user's sub-choice (sniper vs volume)
            # For now, default to volume mode
            return ShotRequirement(shot_number, 80, 1.5, f"Volume mode shot {shot_number}")
        
        if shot_number <= len(config.shot_requirements):
            return config.shot_requirements[shot_number - 1]
        
        return None
    
    def _check_strategy_specific_requirements(self, state: DailyTacticalState, signal_direction: str, config: TacticalConfig) -> Tuple[bool, str]:
        """Check strategy-specific requirements"""
        
        if config.strategy == TacticalStrategy.DOUBLE_TAP and state.shots_fired == 1:
            # Second shot must be same direction as first
            if state.shots_taken:
                first_direction = state.shots_taken[0].get('signal_direction', '')
                if signal_direction != first_direction:
                    return False, f"Double Tap requires same direction as Shot 1 ({first_direction})"
        
        return True, "OK"
    
    def _check_stop_conditions(self, state: DailyTacticalState, config: TacticalConfig) -> Optional[str]:
        """Check if any stop conditions are triggered"""
        
        # Check drawdown limit (6%)
        if state.daily_pnl <= -6.0:
            return "6% drawdown limit reached"
        
        # Check strategy-specific stop conditions
        if "after_2_wins" in config.stop_conditions and state.wins_today >= 2:
            return "2 wins achieved - profit protection"
        
        if "max_shots_reached" in config.stop_conditions and state.shots_fired >= config.max_shots:
            return "Maximum shots reached"
        
        return None
    
    def _should_reset_daily_state(self, state: DailyTacticalState) -> bool:
        """Check if daily state should reset (new day)"""
        now = datetime.now()
        last_reset = state.last_reset
        
        # Reset if it's a new day (past midnight)
        return now.date() > last_reset.date()
    
    def _reset_daily_state(self, user_id: str) -> DailyTacticalState:
        """Reset daily state for new day"""
        new_state = DailyTacticalState(
            user_id=user_id,
            selected_strategy=TacticalStrategy.LONE_WOLF,  # Default
            last_reset=datetime.now()
        )
        
        self.daily_states[user_id] = new_state
        self._save_daily_state(new_state)
        return new_state
    
    def _get_next_midnight(self) -> datetime:
        """Get next midnight UTC"""
        now = datetime.now()
        next_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_day
    
    def _load_daily_state(self, user_id: str) -> None:
        """Load user's daily state from storage"""
        try:
            state_file = f"{self.data_dir}/daily_{user_id}.json"
            with open(state_file, 'r') as f:
                data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if data.get('locked_until'):
                    data['locked_until'] = datetime.fromisoformat(data['locked_until'])
                if data.get('last_reset'):
                    data['last_reset'] = datetime.fromisoformat(data['last_reset'])
                else:
                    data['last_reset'] = datetime.now()
                
                # Convert strategy string back to enum
                if data.get('selected_strategy'):
                    data['selected_strategy'] = TacticalStrategy(data['selected_strategy'])
                
                self.daily_states[user_id] = DailyTacticalState(**data)
        except:
            # Create new state if file doesn't exist
            self.daily_states[user_id] = DailyTacticalState(
                user_id=user_id,
                selected_strategy=TacticalStrategy.LONE_WOLF
            )
    
    def _save_daily_state(self, state: DailyTacticalState) -> None:
        """Save daily state to storage"""
        try:
            import os
            os.makedirs(self.data_dir, exist_ok=True)
            
            state_file = f"{self.data_dir}/daily_{state.user_id}.json"
            
            # Convert to dict for JSON serialization
            data = {
                "user_id": state.user_id,
                "selected_strategy": state.selected_strategy.value if state.selected_strategy else None,
                "shots_fired": state.shots_fired,
                "wins_today": state.wins_today,
                "losses_today": state.losses_today,
                "daily_pnl": state.daily_pnl,
                "shots_taken": state.shots_taken,
                "locked_until": state.locked_until.isoformat() if state.locked_until else None,
                "last_reset": state.last_reset.isoformat()
            }
            
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving daily state: {e}")

# Global instance
tactical_strategy_manager = TacticalStrategyManager()