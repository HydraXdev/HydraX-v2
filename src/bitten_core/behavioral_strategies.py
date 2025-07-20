"""
BITTEN Behavioral Gaming Strategies - NIBBLER Level
6 behavioral strategies with progressive unlock system and XP economy integration

DEFAULT: LONE_WOLF (always available for non-gamers)
UNLOCK PROGRESSION: 120 XP cycles between each strategy unlock
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json


class BehavioralStrategy(Enum):
    """6 Behavioral strategies for NIBBLER gamification level"""
    LONE_WOLF = "LONE_WOLF"                    # Default - Always available
    FIRST_BLOOD = "FIRST_BLOOD"                # Unlock at 120 XP
    CONVICTION_PLAY = "CONVICTION_PLAY"        # Unlock at 240 XP  
    DIAMOND_HANDS = "DIAMOND_HANDS"            # Unlock at 360 XP
    RESET_MASTER = "RESET_MASTER"              # Unlock at 480 XP
    STEADY_BUILDER = "STEADY_BUILDER"          # Unlock at 600 XP


@dataclass
class StrategyConfig:
    """Configuration for each behavioral strategy"""
    strategy: BehavioralStrategy
    display_name: str
    description: str
    unlock_xp: int
    tcs_modifier: float         # Multiplier for TCS filtering
    risk_modifier: float        # Multiplier for risk management  
    signal_filter: str          # Strategy-specific signal filtering
    unlock_message: str
    gameplay_mechanics: Dict[str, Any]


class BehavioralStrategyManager:
    """Manager for behavioral strategies and progression system"""
    
    # Strategy configurations with unlock progression
    STRATEGY_CONFIGS = {
        BehavioralStrategy.LONE_WOLF: StrategyConfig(
            strategy=BehavioralStrategy.LONE_WOLF,
            display_name="🐺 Lone Wolf",
            description="Solo operative - Standard signal filtering, no special mechanics",
            unlock_xp=0,  # Always available (default)
            tcs_modifier=1.0,
            risk_modifier=1.0,
            signal_filter="standard_60plus",
            unlock_message="🐺 LONE WOLF - Available by default. Hunt alone, trust your instincts.",
            gameplay_mechanics={
                "special_abilities": [],
                "signal_preference": "all_types",
                "risk_profile": "balanced"
            }
        ),
        
        BehavioralStrategy.FIRST_BLOOD: StrategyConfig(
            strategy=BehavioralStrategy.FIRST_BLOOD,
            display_name="🩸 First Blood",
            description="Aggressive first-strike specialist - Prefers opening session signals",
            unlock_xp=120,
            tcs_modifier=1.05,  # Slightly more selective
            risk_modifier=1.1,   # Slightly more aggressive
            signal_filter="session_opening_boost",
            unlock_message="🩸 FIRST BLOOD UNLOCKED! Hunt the opening bell - strike first, strike hard.",
            gameplay_mechanics={
                "special_abilities": ["session_opening_boost"],
                "signal_preference": "london_breakout",
                "risk_profile": "aggressive_early"
            }
        ),
        
        BehavioralStrategy.CONVICTION_PLAY: StrategyConfig(
            strategy=BehavioralStrategy.CONVICTION_PLAY,
            display_name="⚡ Conviction Play",
            description="High-confidence hunter - Only takes premium TCS signals (75+)",
            unlock_xp=240,
            tcs_modifier=1.25,  # Much more selective  
            risk_modifier=1.2,   # Higher risk on high conviction
            signal_filter="premium_75plus",
            unlock_message="⚡ CONVICTION PLAY UNLOCKED! Premium signals only - when you strike, make it count.",
            gameplay_mechanics={
                "special_abilities": ["premium_filter", "conviction_bonus"],
                "signal_preference": "high_confidence_only",
                "risk_profile": "high_conviction"
            }
        ),
        
        BehavioralStrategy.DIAMOND_HANDS: StrategyConfig(
            strategy=BehavioralStrategy.DIAMOND_HANDS,
            display_name="💎 Diamond Hands",
            description="Position holder - Extended TP targets, lower SL tolerance",
            unlock_xp=360,
            tcs_modifier=1.1,
            risk_modifier=0.9,   # More conservative risk
            signal_filter="extended_targets",
            unlock_message="💎 DIAMOND HANDS UNLOCKED! Hold the line - extended targets, unbreakable resolve.",
            gameplay_mechanics={
                "special_abilities": ["extended_tp", "tight_sl"],
                "signal_preference": "trend_continuation",
                "risk_profile": "conservative_hold"
            }
        ),
        
        BehavioralStrategy.RESET_MASTER: StrategyConfig(
            strategy=BehavioralStrategy.RESET_MASTER,
            display_name="🔄 Reset Master",
            description="Mean reversion specialist - Excels at market turning points",
            unlock_xp=480,
            tcs_modifier=1.15,
            risk_modifier=1.0,
            signal_filter="mean_reversion_focus",
            unlock_message="🔄 RESET MASTER UNLOCKED! Master the reversals - profit from the chaos.",
            gameplay_mechanics={
                "special_abilities": ["reversal_detection", "counter_trend"],
                "signal_preference": "mean_reversion",
                "risk_profile": "contrarian"
            }
        ),
        
        BehavioralStrategy.STEADY_BUILDER: StrategyConfig(
            strategy=BehavioralStrategy.STEADY_BUILDER,
            display_name="🏗️ Steady Builder",
            description="Consistency master - Frequent smaller wins, optimal compounding",
            unlock_xp=600,
            tcs_modifier=0.95,  # Less selective for more volume
            risk_modifier=0.8,   # Conservative risk per trade
            signal_filter="volume_consistency",
            unlock_message="🏗️ STEADY BUILDER UNLOCKED! Build your empire brick by brick - consistency is king.",
            gameplay_mechanics={
                "special_abilities": ["volume_boost", "compounding_bonus"],
                "signal_preference": "consistent_signals",
                "risk_profile": "conservative_volume"
            }
        )
    }
    
    def __init__(self, data_dir: str = "data/behavioral_strategies"):
        self.data_dir = data_dir
        self.user_strategies = {}  # Cache for user strategy data
        
    def get_user_strategy(self, user_id: str) -> BehavioralStrategy:
        """Get user's current behavioral strategy"""
        if user_id not in self.user_strategies:
            self._load_user_strategy(user_id)
        
        return self.user_strategies.get(user_id, BehavioralStrategy.LONE_WOLF)
    
    def get_unlocked_strategies(self, user_xp: int) -> List[BehavioralStrategy]:
        """Get list of strategies user has unlocked based on XP"""
        unlocked = []
        
        for strategy, config in self.STRATEGY_CONFIGS.items():
            if user_xp >= config.unlock_xp:
                unlocked.append(strategy)
        
        return sorted(unlocked, key=lambda s: self.STRATEGY_CONFIGS[s].unlock_xp)
    
    def can_unlock_strategy(self, user_xp: int, strategy: BehavioralStrategy) -> bool:
        """Check if user can unlock a specific strategy"""
        config = self.STRATEGY_CONFIGS.get(strategy)
        if not config:
            return False
            
        return user_xp >= config.unlock_xp
    
    def get_next_unlock(self, user_xp: int) -> Optional[Dict[str, Any]]:
        """Get info about the next strategy to unlock"""
        for strategy, config in self.STRATEGY_CONFIGS.items():
            if user_xp < config.unlock_xp:
                return {
                    "strategy": strategy,
                    "display_name": config.display_name,
                    "required_xp": config.unlock_xp,
                    "current_xp": user_xp,
                    "xp_needed": config.unlock_xp - user_xp,
                    "description": config.description
                }
        
        return None  # All strategies unlocked
    
    def set_user_strategy(self, user_id: str, strategy: BehavioralStrategy, user_xp: int) -> bool:
        """Set user's behavioral strategy if they have unlocked it"""
        if not self.can_unlock_strategy(user_xp, strategy):
            return False
        
        self.user_strategies[user_id] = strategy
        self._save_user_strategy(user_id, strategy)
        return True
    
    def apply_strategy_to_signal(self, signal_data: Dict, strategy: BehavioralStrategy) -> Dict:
        """Apply behavioral strategy modifications to signal"""
        config = self.STRATEGY_CONFIGS.get(strategy, self.STRATEGY_CONFIGS[BehavioralStrategy.LONE_WOLF])
        
        # Apply TCS modifier
        if 'tcs_score' in signal_data:
            signal_data['tcs_score'] = int(signal_data['tcs_score'] * config.tcs_modifier)
        
        # Apply risk modifier
        if 'position_size_multiplier' in signal_data:
            signal_data['position_size_multiplier'] *= config.risk_modifier
        else:
            signal_data['position_size_multiplier'] = config.risk_modifier
        
        # Apply strategy-specific filters
        signal_data = self._apply_strategy_filter(signal_data, config)
        
        # Add strategy metadata
        signal_data['behavioral_strategy'] = strategy.value
        signal_data['strategy_display_name'] = config.display_name
        
        return signal_data
    
    def _apply_strategy_filter(self, signal_data: Dict, config: StrategyConfig) -> Dict:
        """Apply strategy-specific signal filtering"""
        filter_type = config.signal_filter
        
        if filter_type == "standard_60plus":
            # Standard NIBBLER filtering (60+ TCS)
            if signal_data.get('tcs_score', 0) < 60:
                signal_data['filtered_out'] = True
                signal_data['filter_reason'] = "Below NIBBLER threshold (60+ TCS)"
        
        elif filter_type == "session_opening_boost":
            # FIRST BLOOD: Boost for session opening signals
            session = signal_data.get('session', '').upper()
            if session in ['LONDON', 'NY', 'OVERLAP']:
                signal_data['tcs_score'] = min(85, signal_data.get('tcs_score', 0) + 5)
                signal_data['first_blood_boost'] = True
        
        elif filter_type == "premium_75plus":
            # CONVICTION PLAY: Only premium signals
            if signal_data.get('tcs_score', 0) < 75:
                signal_data['filtered_out'] = True
                signal_data['filter_reason'] = "Below CONVICTION PLAY threshold (75+ TCS)"
        
        elif filter_type == "extended_targets":
            # DIAMOND HANDS: Extended TP, tighter SL
            if 'tp_pips' in signal_data:
                signal_data['tp_pips'] = int(signal_data['tp_pips'] * 1.5)
            if 'sl_pips' in signal_data:
                signal_data['sl_pips'] = int(signal_data['sl_pips'] * 0.8)
            signal_data['diamond_hands_modification'] = True
        
        elif filter_type == "mean_reversion_focus":
            # RESET MASTER: Boost mean reversion signals
            signal_type = signal_data.get('signal_type', '').lower()
            if 'reversion' in signal_type or 'support' in signal_type or 'resistance' in signal_type:
                signal_data['tcs_score'] = min(85, signal_data.get('tcs_score', 0) + 8)
                signal_data['reset_master_boost'] = True
        
        elif filter_type == "volume_consistency":
            # STEADY BUILDER: More frequent, smaller targets
            if 'tp_pips' in signal_data:
                signal_data['tp_pips'] = int(signal_data['tp_pips'] * 0.75)
            signal_data['steady_builder_consistency'] = True
        
        return signal_data
    
    def get_strategy_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's strategy usage statistics"""
        # In production, would track actual performance per strategy
        strategy = self.get_user_strategy(user_id)
        config = self.STRATEGY_CONFIGS[strategy]
        
        return {
            "current_strategy": strategy.value,
            "display_name": config.display_name,
            "description": config.description,
            "unlock_xp": config.unlock_xp,
            "gameplay_mechanics": config.gameplay_mechanics,
            "active_since": datetime.now().isoformat()  # Would track actual activation time
        }
    
    def _load_user_strategy(self, user_id: str) -> None:
        """Load user's strategy from storage"""
        try:
            strategy_file = f"{self.data_dir}/user_{user_id}_strategy.json"
            with open(strategy_file, 'r') as f:
                data = json.load(f)
                strategy_value = data.get('strategy', 'LONE_WOLF')
                self.user_strategies[user_id] = BehavioralStrategy(strategy_value)
        except:
            # Default to LONE_WOLF if file doesn't exist or is invalid
            self.user_strategies[user_id] = BehavioralStrategy.LONE_WOLF
    
    def _save_user_strategy(self, user_id: str, strategy: BehavioralStrategy) -> None:
        """Save user's strategy to storage"""
        try:
            import os
            os.makedirs(self.data_dir, exist_ok=True)
            
            strategy_file = f"{self.data_dir}/user_{user_id}_strategy.json"
            data = {
                "user_id": user_id,
                "strategy": strategy.value,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(strategy_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving user strategy: {e}")


# Global instance for easy access
behavioral_strategy_manager = BehavioralStrategyManager()