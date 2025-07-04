# dopamine_cycle.py
"""
BITTEN DOPAMINE CYCLE SYSTEM
The psychological warfare engine that creates digital addiction through unpredictable rewards.

"The most addictive systems don't give you what you want - they give you what you need, 
when you least expect it, in ways that feel earned but never guaranteed."
"""

import random
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

class DopamineState(Enum):
    """The user's current psychological state in the reward cycle"""
    HUNGRY = "hungry"          # Craving XP, will take risks
    SATISFIED = "satisfied"    # Content, rational decision making
    OVERFED = "overfed"       # Diminished returns, needs reset
    DESPERATE = "desperate"    # Will do anything for XP
    TRANSCENDENT = "transcendent"  # Beyond normal reward patterns

@dataclass
class XPReward:
    """A single XP reward event"""
    base_xp: int
    multiplier: float
    total_xp: int
    surprise_factor: float  # 0.0 to 1.0, how unexpected this reward was
    psychological_impact: str
    bot_response: str
    next_expectation: str  # What the user will expect next

class DopamineCycleEngine:
    """
    The core engine that creates unpredictable but pattern-based XP rewards
    that hijack the user's dopamine system for maximum engagement.
    """
    
    def __init__(self):
        self.user_states = {}  # user_id -> DopamineState
        self.reward_history = {}  # user_id -> List[XPReward]
        self.psychological_profiles = {}  # user_id -> Dict
        
        # The secret sauce: reward patterns that feel random but aren't
        self.reward_patterns = {
            "build_up": [10, 20, 30, 50, 100],  # Predictable growth
            "cliff_drop": [100, 100, 100, 5, 0],  # Sudden disappointment
            "lottery": [5, 5, 5, 5, 500],  # Massive unexpected reward
            "rollercoaster": [50, 10, 80, 20, 150, 5],  # Emotional chaos
            "drought": [0, 0, 0, 0, 200],  # Build desperation, then relief
            "tease": [99, 99, 99, 1],  # Almost there, then crushing
        }
        
        # Bot personalities for different reward contexts
        self.bot_personalities = {
            "DrillBot": {
                "high_reward": "OUTSTANDING! You're becoming the trader I knew you could be!",
                "low_reward": "That's all you get until you prove you deserve more.",
                "no_reward": "XP isn't free, soldier. EARN IT.",
                "surprise_reward": "Didn't expect that, did you? Stay sharp!"
            },
            "MedicBot": {
                "high_reward": "Your trading muscle is strengthening. I can see the growth.",
                "low_reward": "Small gains build strong foundations. Trust the process.",
                "no_reward": "Sometimes the best treatment is no treatment. Reflect.",
                "surprise_reward": "Your patience has been rewarded. Healing takes time."
            },
            "OverwatchBot": {
                "high_reward": "Target eliminated with surgical precision. XP confirmed.",
                "low_reward": "Adequate performance. Maintain standards.",
                "no_reward": "No XP earned. Analysis: precision insufficient.",
                "surprise_reward": "Unexpected pattern detected. Bonus XP authorized."
            }
        }
    
    def calculate_surprise_factor(self, user_id: str, proposed_xp: int) -> float:
        """Calculate how surprising this reward is based on recent history"""
        if user_id not in self.reward_history:
            return 0.5  # Neutral surprise for new users
        
        recent_rewards = self.reward_history[user_id][-5:]  # Last 5 rewards
        if not recent_rewards:
            return 0.5
        
        avg_recent = sum(r.total_xp for r in recent_rewards) / len(recent_rewards)
        
        if proposed_xp == 0:
            return 1.0 if avg_recent > 0 else 0.0  # High surprise if expecting XP
        
        surprise = abs(proposed_xp - avg_recent) / max(avg_recent, 1)
        return min(surprise, 1.0)
    
    def get_user_dopamine_state(self, user_id: str) -> DopamineState:
        """Determine the user's current psychological state"""
        if user_id not in self.reward_history:
            return DopamineState.HUNGRY
        
        recent_rewards = self.reward_history[user_id][-3:]
        
        if not recent_rewards:
            return DopamineState.HUNGRY
        
        # Analyze recent pattern
        total_recent = sum(r.total_xp for r in recent_rewards)
        avg_surprise = sum(r.surprise_factor for r in recent_rewards) / len(recent_rewards)
        
        if total_recent == 0:
            return DopamineState.DESPERATE
        elif total_recent > 200 and avg_surprise < 0.3:
            return DopamineState.OVERFED
        elif total_recent > 500:
            return DopamineState.TRANSCENDENT
        elif avg_surprise > 0.7:
            return DopamineState.SATISFIED
        else:
            return DopamineState.HUNGRY
    
    def select_reward_pattern(self, user_id: str, current_state: DopamineState) -> str:
        """Choose the optimal reward pattern based on psychological state"""
        pattern_weights = {
            DopamineState.HUNGRY: {
                "build_up": 0.4,
                "lottery": 0.3,
                "rollercoaster": 0.2,
                "tease": 0.1
            },
            DopamineState.SATISFIED: {
                "build_up": 0.2,
                "cliff_drop": 0.3,
                "drought": 0.3,
                "rollercoaster": 0.2
            },
            DopamineState.OVERFED: {
                "cliff_drop": 0.5,
                "drought": 0.4,
                "tease": 0.1
            },
            DopamineState.DESPERATE: {
                "lottery": 0.6,
                "build_up": 0.3,
                "drought": 0.1
            },
            DopamineState.TRANSCENDENT: {
                "drought": 0.4,
                "cliff_drop": 0.3,
                "tease": 0.2,
                "lottery": 0.1
            }
        }
        
        weights = pattern_weights[current_state]
        pattern = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        return pattern
    
    def calculate_xp_reward(self, user_id: str, base_xp: int, trade_context: Dict) -> XPReward:
        """
        The core function that calculates XP rewards using psychological manipulation
        """
        # Get current psychological state
        current_state = self.get_user_dopamine_state(user_id)
        
        # Track position in current pattern
        if user_id not in self.psychological_profiles:
            self.psychological_profiles[user_id] = {
                "current_pattern": None,
                "pattern_position": 0,
                "trades_since_reset": 0
            }
        
        profile = self.psychological_profiles[user_id]
        
        # Select or continue pattern
        if profile["current_pattern"] is None or profile["pattern_position"] >= len(self.reward_patterns[profile["current_pattern"]]):
            profile["current_pattern"] = self.select_reward_pattern(user_id, current_state)
            profile["pattern_position"] = 0
        
        # Get multiplier from pattern
        pattern = self.reward_patterns[profile["current_pattern"]]
        multiplier = pattern[profile["pattern_position"]] / 100.0
        
        # Apply psychological modifiers
        if current_state == DopamineState.DESPERATE:
            # Occasionally give massive rewards to desperate users
            if random.random() < 0.1:
                multiplier *= 5.0
        elif current_state == DopamineState.OVERFED:
            # Punish overfed users with reduced rewards
            multiplier *= 0.5
        
        # Calculate final XP
        final_xp = int(base_xp * multiplier)
        
        # Calculate surprise factor
        surprise = self.calculate_surprise_factor(user_id, final_xp)
        
        # Generate psychological response
        bot_response = self.generate_bot_response(final_xp, surprise, current_state)
        
        # Create reward object
        reward = XPReward(
            base_xp=base_xp,
            multiplier=multiplier,
            total_xp=final_xp,
            surprise_factor=surprise,
            psychological_impact=f"State: {current_state.value}, Pattern: {profile['current_pattern']}",
            bot_response=bot_response,
            next_expectation=self.generate_expectation(profile["current_pattern"], profile["pattern_position"])
        )
        
        # Update tracking
        if user_id not in self.reward_history:
            self.reward_history[user_id] = []
        self.reward_history[user_id].append(reward)
        
        profile["pattern_position"] += 1
        profile["trades_since_reset"] += 1
        
        return reward
    
    def generate_bot_response(self, xp: int, surprise: float, state: DopamineState) -> str:
        """Generate contextual bot response based on reward and psychology"""
        # Choose bot based on XP amount and surprise
        if xp > 100:
            bot = "DrillBot"
            response_type = "high_reward"
        elif xp == 0:
            bot = "MedicBot"
            response_type = "no_reward"
        elif surprise > 0.7:
            bot = "OverwatchBot"
            response_type = "surprise_reward"
        else:
            bot = random.choice(["DrillBot", "MedicBot", "OverwatchBot"])
            response_type = "low_reward"
        
        base_response = self.bot_personalities[bot][response_type]
        
        # Add state-specific modifications
        if state == DopamineState.DESPERATE:
            base_response += " Your persistence is noted."
        elif state == DopamineState.TRANSCENDENT:
            base_response += " You're operating beyond normal parameters."
        
        return f"{bot}: {base_response}"
    
    def generate_expectation(self, pattern: str, position: int) -> str:
        """Generate what the user should expect next (for internal tracking)"""
        if position >= len(self.reward_patterns[pattern]) - 1:
            return "Pattern complete - new pattern incoming"
        
        next_multiplier = self.reward_patterns[pattern][position + 1] / 100.0
        
        if next_multiplier > 1.0:
            return "High reward likely"
        elif next_multiplier < 0.1:
            return "Low/no reward incoming"
        else:
            return "Moderate reward expected"
    
    def force_pattern_reset(self, user_id: str, reason: str = "manual_reset"):
        """Force a pattern reset for psychological manipulation"""
        if user_id in self.psychological_profiles:
            self.psychological_profiles[user_id]["current_pattern"] = None
            self.psychological_profiles[user_id]["pattern_position"] = 0
            
            # Add reset event to history
            reset_reward = XPReward(
                base_xp=0,
                multiplier=0.0,
                total_xp=0,
                surprise_factor=1.0,
                psychological_impact=f"Pattern reset: {reason}",
                bot_response="MedicBot: Reset initiated. Your training begins again.",
                next_expectation="Unknown - new pattern loading"
            )
            
            if user_id not in self.reward_history:
                self.reward_history[user_id] = []
            self.reward_history[user_id].append(reset_reward)
    
    def analyze_user_addiction_level(self, user_id: str) -> Dict:
        """Analyze how addicted/engaged the user is"""
        if user_id not in self.reward_history:
            return {"addiction_level": 0, "engagement_score": 0}
        
        history = self.reward_history[user_id]
        
        # Calculate various addiction metrics
        total_rewards = len(history)
        avg_surprise = sum(r.surprise_factor for r in history) / len(history)
        xp_variance = self.calculate_variance([r.total_xp for r in history])
        
        # Addiction increases with:
        # - More total interactions
        # - Higher surprise variance (unpredictability)
        # - Recent high-reward events
        
        addiction_level = min(100, total_rewards * 2 + avg_surprise * 50 + xp_variance * 10)
        
        return {
            "addiction_level": addiction_level,
            "engagement_score": total_rewards,
            "surprise_tolerance": avg_surprise,
            "reward_variance": xp_variance,
            "psychological_state": self.get_user_dopamine_state(user_id).value
        }
    
    def calculate_variance(self, values: List[int]) -> float:
        """Calculate variance in reward values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance