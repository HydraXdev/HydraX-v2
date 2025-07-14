# fire_modes.py
# BITTEN Fire Mode Implementation - THE LAW OF ENGAGEMENT

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

class FireMode(Enum):
    """Fire modes as defined in RULES_OF_ENGAGEMENT.md"""
    SINGLE_SHOT = "single_shot"
    CHAINGUN = "chaingun"
    AUTO_FIRE = "auto_fire"
    SEMI_AUTO = "semi_auto"  # Commander tier manual mode with lower TCS
    STEALTH = "stealth"
    MIDNIGHT_HAMMER = "midnight_hammer"

class TierLevel(Enum):
    """Subscription tiers"""
    PRESS_PASS = "press_pass"  # Tier 0 - Press/Trial tier
    NIBBLER = "nibbler"
    FANG = "fang"
    COMMANDER = "commander"
    APEX = "apex"

@dataclass
class TierConfig:
    """Tier configuration as per THE LAW"""
    name: str
    price: int
    daily_shots: int
    min_tcs: int
    has_chaingun: bool
    has_autofire: bool
    has_stealth: bool
    risk_per_shot: float = 0.02  # 2%
    auto_mode_min_tcs: Optional[int] = None  # Separate TCS for auto mode (COMMANDER)

# THE LAW - Tier Configurations
TIER_CONFIGS = {
    TierLevel.PRESS_PASS: TierConfig(
        name="PRESS_PASS",
        price=0,  # Free tier
        daily_shots=1,
        min_tcs=50,  # Lowered from 70 to 50
        has_chaingun=False,
        has_autofire=False,
        has_stealth=False
    ),
    TierLevel.NIBBLER: TierConfig(
        name="NIBBLER",
        price=39,
        daily_shots=6,
        min_tcs=50,  # Lowered from 70 to 50
        has_chaingun=False,
        has_autofire=False,
        has_stealth=False
    ),
    TierLevel.FANG: TierConfig(
        name="FANG",
        price=89,
        daily_shots=10,  # 8-10, using max
        min_tcs=50,  # Lowered from 85 to 50
        has_chaingun=True,
        has_autofire=False,
        has_stealth=False
    ),
    TierLevel.COMMANDER: TierConfig(
        name="COMMANDER",
        price=139,
        daily_shots=12,  # 12+
        min_tcs=50,  # Minimum TCS to fire (lowered from 85)
        has_chaingun=True,
        has_autofire=True,
        has_stealth=False,
        auto_mode_min_tcs=80  # AUTO mode requires 80% TCS (lowered from 91)
    ),
    TierLevel.APEX: TierConfig(
        name="APEX",
        price=188,
        daily_shots=9999,  # Unlimited
        min_tcs=50,  # Lowered from 91 to 50
        has_chaingun=True,
        has_autofire=True,
        has_stealth=True
    )
}

# Import centralized configuration
try:
    from .config_manager import get_trading_config
except ImportError:
    # Fallback for backtesting
    def get_trading_config():
        class MockConfig:
            def get_pair_specific_tcs(self):
                return {}
        return MockConfig()

# Pair-specific TCS requirements loaded from centralized config
def get_pair_specific_tcs() -> Dict[str, Optional[int]]:
    """Get pair-specific TCS requirements from centralized configuration"""
    return get_trading_config().get_pair_specific_tcs()

# Legacy support - will be dynamically loaded
PAIR_SPECIFIC_TCS = get_pair_specific_tcs()

def get_tcs_threshold_for_mode(tier: TierLevel, fire_mode: FireMode) -> int:
    """Get the correct TCS threshold based on tier and fire mode"""
    config = TIER_CONFIGS[tier]
    
    # COMMANDER has dual thresholds
    if tier == TierLevel.COMMANDER and fire_mode == FireMode.AUTO_FIRE:
        return config.auto_mode_min_tcs or config.min_tcs
    
    return config.min_tcs

@dataclass
class ChaingunState:
    """CHAINGUN sequence state"""
    sequence_id: str
    user_id: int
    shot_number: int  # 1-4
    total_risk: float
    wins: List[bool]
    start_time: datetime
    parachute_available: bool = True
    
    def get_next_risk(self) -> float:
        """Get risk for next shot"""
        risks = [0.02, 0.04, 0.08, 0.16]  # 2%, 4%, 8%, 16%
        if self.shot_number <= 4:
            return risks[self.shot_number - 1]
        return 0.16  # Cap at 16%

class FireModeValidator:
    """Validates fire mode access based on THE LAW"""
    
    def __init__(self):
        self.shot_cooldown = timedelta(minutes=30)
        self.chaingun_sequences: Dict[int, List[ChaingunState]] = {}
        self.daily_shots: Dict[int, int] = {}
        self.last_shot_time: Dict[int, datetime] = {}
        
    def can_fire(self, user_id: int, tier: TierLevel, mode: FireMode, 
                 tcs_score: int, pair: str = None) -> Tuple[bool, str]:
        """Check if user can fire based on THE LAW"""
        
        config = TIER_CONFIGS[tier]
        
        # Check pair-specific TCS requirement first
        if pair:
            pair_tcs_requirement = get_trading_config().get_pair_tcs_requirement(pair)
            if pair_tcs_requirement and tcs_score < pair_tcs_requirement:
                return False, f"TCS too low for {pair}: {tcs_score} < {pair_tcs_requirement}"
        
        # Check standard TCS requirement
        if tcs_score < config.min_tcs:
            return False, f"TCS too low: {tcs_score} < {config.min_tcs}"
        
        # Check mode access
        if mode == FireMode.CHAINGUN and not config.has_chaingun:
            return False, f"{config.name} tier cannot use CHAINGUN"
        
        if mode == FireMode.AUTO_FIRE and not config.has_autofire:
            return False, f"{config.name} tier cannot use AUTO-FIRE"
            
        if mode == FireMode.STEALTH and not config.has_stealth:
            return False, f"{config.name} tier cannot use STEALTH MODE"
        
        # Check daily shot limit (except for auto modes)
        if mode == FireMode.SINGLE_SHOT:
            shots_today = self.daily_shots.get(user_id, 0)
            if shots_today >= config.daily_shots:
                return False, f"Daily shot limit reached: {shots_today}/{config.daily_shots}"
        
        # Check cooldown for SINGLE_SHOT
        if mode == FireMode.SINGLE_SHOT:
            last_shot = self.last_shot_time.get(user_id)
            if last_shot and datetime.now() - last_shot < self.shot_cooldown:
                remaining = self.shot_cooldown - (datetime.now() - last_shot)
                return False, f"Cooldown active: {remaining.seconds//60} minutes remaining"
        
        # Check CHAINGUN limits
        if mode == FireMode.CHAINGUN:
            sequences_today = self._get_chaingun_sequences_today(user_id)
            if len(sequences_today) >= 2:
                return False, "Daily CHAINGUN limit reached (2 sequences)"
        
        # Check specific TCS for CHAINGUN shots
        if mode == FireMode.CHAINGUN:
            active_sequence = self._get_active_chaingun(user_id)
            if active_sequence:
                required_tcs = [85, 87, 89, 91]
                shot_num = active_sequence.shot_number
                if shot_num <= 4 and tcs_score < required_tcs[shot_num - 1]:
                    return False, f"CHAINGUN shot {shot_num} requires {required_tcs[shot_num - 1]}% TCS"
        
        # AUTO-FIRE specific checks
        if mode == FireMode.AUTO_FIRE:
            if tcs_score < 91:
                return False, "AUTO-FIRE requires 91%+ TCS"
        
        # MIDNIGHT HAMMER checks
        if mode == FireMode.MIDNIGHT_HAMMER:
            if tcs_score < 95:
                return False, "MIDNIGHT HAMMER requires 95%+ TCS"
        
        return True, "Fire authorized"
    
    def record_shot(self, user_id: int, mode: FireMode):
        """Record a shot was fired"""
        if mode == FireMode.SINGLE_SHOT:
            self.daily_shots[user_id] = self.daily_shots.get(user_id, 0) + 1
            self.last_shot_time[user_id] = datetime.now()
    
    def start_chaingun(self, user_id: int) -> ChaingunState:
        """Start a new CHAINGUN sequence"""
        import secrets
        
        # Security: Use cryptographically secure random ID instead of predictable timestamp
        random_id = secrets.token_hex(8)
        sequence = ChaingunState(
            sequence_id=f"CG_{user_id}_{random_id}",
            user_id=user_id,
            shot_number=1,
            total_risk=0.0,
            wins=[],
            start_time=datetime.now()
        )
        
        if user_id not in self.chaingun_sequences:
            self.chaingun_sequences[user_id] = []
        
        self.chaingun_sequences[user_id].append(sequence)
        return sequence
    
    def _get_chaingun_sequences_today(self, user_id: int) -> List[ChaingunState]:
        """Get today's CHAINGUN sequences"""
        if user_id not in self.chaingun_sequences:
            return []
        
        today = datetime.now().date()
        return [s for s in self.chaingun_sequences[user_id] 
                if s.start_time.date() == today]
    
    def _get_active_chaingun(self, user_id: int) -> Optional[ChaingunState]:
        """Get active CHAINGUN sequence if any"""
        sequences = self._get_chaingun_sequences_today(user_id)
        for seq in sequences:
            if seq.shot_number <= 4 and len(seq.wins) < 4:
                # Check if within time limit (4 hours)
                if datetime.now() - seq.start_time < timedelta(hours=4):
                    return seq
        return None
    
    def reset_daily_counters(self):
        """Reset daily shot counters"""
        self.daily_shots.clear()
        # Keep chaingun sequences for history
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user's firing stats"""
        return {
            'shots_today': self.daily_shots.get(user_id, 0),
            'chaingun_sequences': len(self._get_chaingun_sequences_today(user_id)),
            'last_shot': self.last_shot_time.get(user_id),
            'active_chaingun': self._get_active_chaingun(user_id) is not None
        }

# Import the new stealth protocol
from .stealth_protocol import get_stealth_protocol, StealthLevel

# Legacy Stealth Mode Implementation (kept for backward compatibility)
class StealthMode:
    """APEX-exclusive anti-detection system (Legacy - use stealth_protocol.py instead)"""
    
    def __init__(self):
        # Now uses the new stealth protocol
        self.stealth_protocol = get_stealth_protocol()
        self.entry_delay_range = (2, 5)  # minutes
        self.size_variation = (0.8, 1.2)  # 80-120% of calculated
        self.loss_injection_rate = 0.07  # 7% intentional losses
        self.win_streak_threshold = 12  # Trigger loss after 12 wins
        self.current_streak = 0
        
    def apply_stealth(self, trade_params: Dict) -> Dict:
        """Apply STEALTH modifications to trade (Legacy method)"""
        # Delegate to new stealth protocol
        self.stealth_protocol.set_level(StealthLevel.HIGH)
        return self.stealth_protocol.apply_full_stealth(trade_params)
    
    def _should_inject_loss(self) -> bool:
        """Determine if we should inject a loss"""
        import secrets
        
        # Check win streak
        if self.current_streak >= self.win_streak_threshold:
            self.current_streak = 0
            return True
        
        # Security: Use cryptographically secure random injection
        random_value = secrets.randbelow(10000) / 10000.0
        return random_value < self.loss_injection_rate

# Midnight Hammer Event Manager
class MidnightHammerEvent:
    """Community-wide trading event"""
    
    def __init__(self):
        self.active_event = None
        self.participants = []
        self.event_history = []
        
    def can_trigger(self, tcs_score: int, active_users: int, 
                   total_users: int) -> Tuple[bool, str]:
        """Check if MIDNIGHT HAMMER can be triggered"""
        
        # Check TCS
        if tcs_score < 95:
            return False, f"TCS too low: {tcs_score} < 95"
        
        # Check user participation
        participation_rate = active_users / total_users if total_users > 0 else 0
        if participation_rate < 0.7:
            return False, f"Not enough users online: {participation_rate:.0%} < 70%"
        
        # Check frequency (max 2 per month)
        events_this_month = self._get_events_this_month()
        if len(events_this_month) >= 2:
            return False, "Monthly event limit reached (2)"
        
        # Check if event already active
        if self.active_event:
            return False, "Event already in progress"
        
        return True, "MIDNIGHT HAMMER ready!"
    
    def _get_events_this_month(self) -> List:
        """Get events from current month"""
        current_month = datetime.now().month
        return [e for e in self.event_history 
                if e['timestamp'].month == current_month]