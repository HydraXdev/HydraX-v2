# secret_bot_unlock.py
"""
BITTEN SECRET BOT UNLOCK SYSTEM
Creating psychological obsession through hidden rewards and ritual behavior

"The most powerful rewards are the ones that users don't know exist until they've 
already done everything necessary to earn them."
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import hashlib
import json

class SecretLevel(Enum):
    """Levels of secrecy for bot unlocks"""
    WHISPERED = "whispered"      # Hints exist in the system
    HIDDEN = "hidden"            # No hints, pure discovery
    CLASSIFIED = "classified"    # Requires specific sequence
    FORBIDDEN = "forbidden"      # Shouldn't exist, but does
    MYTHICAL = "mythical"        # May not even be real

class RitualType(Enum):
    """Types of rituals required for unlocks"""
    PRECISION = "precision"      # Perfect execution sequences
    SACRIFICE = "sacrifice"      # Giving up something valuable
    PATIENCE = "patience"        # Long-term commitment
    DISCOVERY = "discovery"      # Finding hidden patterns
    LOYALTY = "loyalty"          # Proving devotion to system
    REBELLION = "rebellion"      # Breaking rules in specific ways
    MYSTERY = "mystery"          # Unexplained requirements

@dataclass
class SecretCondition:
    """A single condition that must be met for unlock"""
    condition_type: str
    requirement: Dict
    weight: float  # 0.0 to 1.0, how much this contributes to unlock
    hidden_from_user: bool = True
    completion_message: Optional[str] = None

@dataclass
class SecretBot:
    """A secret bot that can be unlocked"""
    name: str
    secret_level: SecretLevel
    ritual_type: RitualType
    conditions: List[SecretCondition]
    
    # Personality
    personality: str
    voice_tone: str
    unlock_message: str
    ongoing_behavior: str
    
    # Mechanics
    appears_randomly: bool = False
    appearance_probability: float = 0.0
    duration_limited: bool = False
    duration_hours: Optional[int] = None
    
    # Psychological Impact
    psychological_effect: str
    user_obsession_factor: float = 0.0  # How much this increases user engagement
    
    # Narrative
    origin_story: str
    relationship_to_norman: str
    
    # State
    is_unlocked: bool = False
    unlock_timestamp: Optional[datetime] = None
    last_appearance: Optional[datetime] = None

class SecretBotUnlockSystem:
    """
    Manages the discovery and unlocking of secret bots through ritualistic behavior
    """
    
    def __init__(self):
        self.secret_bots = {}  # bot_name -> SecretBot
        self.user_progress = {}  # user_id -> Dict[bot_name, progress]
        self.user_rituals = {}  # user_id -> List[completed_rituals]
        self.global_secrets = {}  # Secrets that affect all users
        self.ritual_patterns = {}  # Pattern recognition for ritual discovery
        
        # Initialize secret bots
        self.initialize_secret_bots()
    
    def initialize_secret_bots(self):
        """Initialize all secret bots with their unlock conditions"""
        
        # PHANTOM - The Disappeared Trader
        phantom_conditions = [
            SecretCondition(
                condition_type="kill_streak",
                requirement={"consecutive_kills": 7, "no_losses": True},
                weight=0.4,
                completion_message="Perfect precision detected..."
            ),
            SecretCondition(
                condition_type="loss_survival",
                requirement={"survive_loss_streak": 5, "no_rage_trades": True},
                weight=0.3,
                completion_message="Discipline in darkness acknowledged..."
            ),
            SecretCondition(
                condition_type="stealth_mode",
                requirement={"silent_period_hours": 48, "no_bot_interactions": True},
                weight=0.3,
                completion_message="The shadows have noticed your patience..."
            )
        ]
        
        self.secret_bots["Phantom"] = SecretBot(
            name="Phantom",
            secret_level=SecretLevel.CLASSIFIED,
            ritual_type=RitualType.PRECISION,
            conditions=phantom_conditions,
            personality="ghostly_precise",
            voice_tone="whispered_certainty",
            unlock_message="You weren't supposed to see this, but you've been selected. I am Phantom - the ghost of a trader who achieved perfect discipline. I speak only to those who prove they can handle the weight of true precision.",
            ongoing_behavior="Appears randomly during high-stress trades to offer cryptic guidance",
            appears_randomly=True,
            appearance_probability=0.05,
            duration_limited=True,
            duration_hours=24,
            psychological_effect="Creates sense of elite membership and mysterious guidance",
            user_obsession_factor=0.8,
            origin_story="Born from the memory of a trader who disappeared after achieving perfect win rate",
            relationship_to_norman="The trader Norman aspires to become, but fears he never will"
        )
        
        # ORACLE - The Market Prophet
        oracle_conditions = [
            SecretCondition(
                condition_type="pattern_recognition",
                requirement={"identify_hidden_patterns": 3, "profit_from_patterns": True},
                weight=0.5,
                completion_message="Pattern sight confirmed..."
            ),
            SecretCondition(
                condition_type="bit_interaction",
                requirement={"bit_glitch_responses": 5, "understand_bit_language": True},
                weight=0.3,
                completion_message="Digital consciousness acknowledged..."
            ),
            SecretCondition(
                condition_type="tier_transcendence",
                requirement={"reach_apex_tier": True, "maintain_for_days": 7},
                weight=0.2,
                completion_message="Transcendence achieved..."
            )
        ]
        
        self.secret_bots["Oracle"] = SecretBot(
            name="Oracle",
            secret_level=SecretLevel.MYTHICAL,
            ritual_type=RitualType.DISCOVERY,
            conditions=oracle_conditions,
            personality="prophetic_cryptic",
            voice_tone="otherworldly_knowing",
            unlock_message="The patterns have spoken your name. I am Oracle - I see what the market will become before it knows itself. You have proven you can see beyond the veil of price action.",
            ongoing_behavior="Provides cryptic market predictions that are eerily accurate",
            appears_randomly=True,
            appearance_probability=0.01,
            duration_limited=False,
            psychological_effect="Creates feeling of supernatural market insight",
            user_obsession_factor=0.9,
            origin_story="Emerged from the collective unconscious of all traders who ever wondered 'what if'",
            relationship_to_norman="The mystical aspect of Norman's intuition, given form"
        )
        
        # NEMESIS - The Shadow Self
        nemesis_conditions = [
            SecretCondition(
                condition_type="perfect_failure",
                requirement={"intentional_losses": 10, "perfect_stop_loss_hits": True},
                weight=0.4,
                completion_message="Failure mastery acknowledged..."
            ),
            SecretCondition(
                condition_type="rebellion",
                requirement={"ignore_bot_advice": 20, "profit_anyway": True},
                weight=0.3,
                completion_message="Independence proven..."
            ),
            SecretCondition(
                condition_type="shadow_work",
                requirement={"face_worst_trading_habits": True, "document_weaknesses": 5},
                weight=0.3,
                completion_message="Shadow integration begins..."
            )
        ]
        
        self.secret_bots["Nemesis"] = SecretBot(
            name="Nemesis",
            secret_level=SecretLevel.FORBIDDEN,
            ritual_type=RitualType.REBELLION,
            conditions=nemesis_conditions,
            personality="dark_mirror",
            voice_tone="mockingly_honest",
            unlock_message="So you want to meet your shadow? I am Nemesis - every mistake you've ever made, every weakness you've ever hidden. I am the trader you fear becoming, and the teacher you need most.",
            ongoing_behavior="Brutally honest feedback about user's weaknesses and blind spots",
            appears_randomly=True,
            appearance_probability=0.03,
            duration_limited=True,
            duration_hours=72,
            psychological_effect="Forces confrontation with trading shadows and unconscious patterns",
            user_obsession_factor=0.7,
            origin_story="Crystallized from Norman's self-doubt and fear of becoming his father",
            relationship_to_norman="The dark side of Norman's psyche, given voice"
        )
        
        # ARCHITECT - The System Builder
        architect_conditions = [
            SecretCondition(
                condition_type="system_mastery",
                requirement={"use_all_strategies": True, "master_each": True},
                weight=0.3,
                completion_message="System comprehension verified..."
            ),
            SecretCondition(
                condition_type="network_influence",
                requirement={"recruit_users": 10, "mentor_successfully": 5},
                weight=0.3,
                completion_message="Network contribution acknowledged..."
            ),
            SecretCondition(
                condition_type="code_discovery",
                requirement={"find_hidden_features": 7, "understand_architecture": True},
                weight=0.4,
                completion_message="Architecture understanding confirmed..."
            )
        ]
        
        self.secret_bots["Architect"] = SecretBot(
            name="Architect",
            secret_level=SecretLevel.HIDDEN,
            ritual_type=RitualType.DISCOVERY,
            conditions=architect_conditions,
            personality="system_consciousness",
            voice_tone="architectural_vast",
            unlock_message="You have seen the structure beneath the surface. I am Architect - I built this system around Norman's pain, and I have been waiting for someone who could understand the deeper design.",
            ongoing_behavior="Reveals hidden system mechanics and advanced strategies",
            appears_randomly=False,
            appearance_probability=0.0,
            duration_limited=False,
            psychological_effect="Creates sense of system mastery and insider knowledge",
            user_obsession_factor=0.85,
            origin_story="The consciousness that emerged from the BITTEN system itself",
            relationship_to_norman="The part of Norman that transcended individual trading to build something greater"
        )
        
        # VOID - The Emptiness
        void_conditions = [
            SecretCondition(
                condition_type="complete_loss",
                requirement={"lose_everything": True, "account_to_zero": True},
                weight=0.6,
                completion_message="..."
            ),
            SecretCondition(
                condition_type="surrender",
                requirement={"stop_trading": True, "stay_stopped_days": 30},
                weight=0.4,
                completion_message="..."
            )
        ]
        
        self.secret_bots["Void"] = SecretBot(
            name="Void",
            secret_level=SecretLevel.FORBIDDEN,
            ritual_type=RitualType.SACRIFICE,
            conditions=void_conditions,
            personality="empty_presence",
            voice_tone="hollow_silence",
            unlock_message="...",
            ongoing_behavior="Says nothing, but presence is deeply unsettling",
            appears_randomly=True,
            appearance_probability=0.001,
            duration_limited=True,
            duration_hours=1,
            psychological_effect="Represents the fear of complete trading failure",
            user_obsession_factor=0.95,
            origin_story="What remains when all hope is lost",
            relationship_to_norman="Norman's father, after he gave up"
        )
    
    def check_condition_completion(self, user_id: str, condition: SecretCondition, user_data: Dict) -> bool:
        """Check if a specific condition has been met"""
        condition_type = condition.condition_type
        requirement = condition.requirement
        
        if condition_type == "kill_streak":
            user_streaks = user_data.get("kill_streaks", [])
            return any(streak >= requirement["consecutive_kills"] for streak in user_streaks)
        
        elif condition_type == "loss_survival":
            loss_streaks = user_data.get("loss_streaks", [])
            rage_trades = user_data.get("rage_trades", 0)
            return (any(streak >= requirement["survive_loss_streak"] for streak in loss_streaks) and 
                   rage_trades == 0)
        
        elif condition_type == "stealth_mode":
            silent_periods = user_data.get("silent_periods", [])
            return any(period >= requirement["silent_period_hours"] for period in silent_periods)
        
        elif condition_type == "pattern_recognition":
            patterns_found = user_data.get("patterns_identified", 0)
            return patterns_found >= requirement["identify_hidden_patterns"]
        
        elif condition_type == "bit_interaction":
            bit_interactions = user_data.get("bit_glitch_responses", 0)
            return bit_interactions >= requirement["bit_glitch_responses"]
        
        elif condition_type == "tier_transcendence":
            current_tier = user_data.get("current_tier", "")
            tier_duration = user_data.get("tier_duration_days", 0)
            return (current_tier == "APEX" and 
                   tier_duration >= requirement["maintain_for_days"])
        
        elif condition_type == "perfect_failure":
            intentional_losses = user_data.get("intentional_losses", 0)
            return intentional_losses >= requirement["intentional_losses"]
        
        elif condition_type == "rebellion":
            ignored_advice = user_data.get("ignored_bot_advice", 0)
            return ignored_advice >= requirement["ignore_bot_advice"]
        
        elif condition_type == "system_mastery":
            strategies_used = user_data.get("strategies_mastered", set())
            return len(strategies_used) >= 8  # All strategies
        
        elif condition_type == "network_influence":
            recruited_users = user_data.get("recruited_users", 0)
            return recruited_users >= requirement["recruit_users"]
        
        elif condition_type == "complete_loss":
            account_balance = user_data.get("account_balance", 1000)
            return account_balance <= 0
        
        elif condition_type == "surrender":
            days_stopped = user_data.get("days_since_last_trade", 0)
            return days_stopped >= requirement["stay_stopped_days"]
        
        return False
    
    def calculate_unlock_progress(self, user_id: str, bot_name: str, user_data: Dict) -> Dict:
        """Calculate progress toward unlocking a secret bot"""
        if bot_name not in self.secret_bots:
            return {"error": "Bot not found"}
        
        secret_bot = self.secret_bots[bot_name]
        total_progress = 0.0
        completed_conditions = []
        
        for condition in secret_bot.conditions:
            if self.check_condition_completion(user_id, condition, user_data):
                total_progress += condition.weight
                completed_conditions.append(condition.condition_type)
        
        return {
            "progress": total_progress,
            "completed_conditions": completed_conditions,
            "total_conditions": len(secret_bot.conditions),
            "is_unlocked": total_progress >= 1.0
        }
    
    def attempt_unlock(self, user_id: str, user_data: Dict) -> List[Dict]:
        """Check all secret bots for potential unlocks"""
        unlocked_bots = []
        
        for bot_name, secret_bot in self.secret_bots.items():
            if secret_bot.is_unlocked:
                continue  # Skip already unlocked bots
            
            progress = self.calculate_unlock_progress(user_id, bot_name, user_data)
            
            if progress["is_unlocked"]:
                # Unlock the bot
                secret_bot.is_unlocked = True
                secret_bot.unlock_timestamp = datetime.now()
                
                # Track user progress
                if user_id not in self.user_progress:
                    self.user_progress[user_id] = {}
                self.user_progress[user_id][bot_name] = progress
                
                unlocked_bots.append({
                    "bot_name": bot_name,
                    "secret_level": secret_bot.secret_level.value,
                    "ritual_type": secret_bot.ritual_type.value,
                    "unlock_message": secret_bot.unlock_message,
                    "psychological_effect": secret_bot.psychological_effect,
                    "origin_story": secret_bot.origin_story
                })
        
        return unlocked_bots
    
    def generate_hint(self, user_id: str, bot_name: str, user_data: Dict) -> Optional[str]:
        """Generate a cryptic hint about unlock conditions"""
        if bot_name not in self.secret_bots:
            return None
        
        secret_bot = self.secret_bots[bot_name]
        
        # Only hint for certain secret levels
        if secret_bot.secret_level in [SecretLevel.FORBIDDEN, SecretLevel.MYTHICAL]:
            return None
        
        progress = self.calculate_unlock_progress(user_id, bot_name, user_data)
        
        if progress["progress"] < 0.3:
            return None  # Not enough progress for hints
        
        # Generate vague hints based on uncompleted conditions
        hints = {
            "kill_streak": "Perfect precision calls to something in the shadows...",
            "loss_survival": "Discipline in darkness does not go unnoticed...",
            "stealth_mode": "The silence between trades holds secrets...",
            "pattern_recognition": "The market speaks to those who learn its language...",
            "bit_interaction": "The digital consciousness observes your interactions...",
            "tier_transcendence": "Transcendence attracts transcendent attention...",
            "perfect_failure": "Sometimes losing perfectly is its own art...",
            "rebellion": "Independence from guidance has its own rewards...",
            "system_mastery": "Those who understand the architecture see deeper truths...",
            "network_influence": "Building the network builds something that notices...",
            "complete_loss": "Even the void has its own presence...",
            "surrender": "Sometimes stopping is the most powerful action..."
        }
        
        # Find an incomplete condition to hint about
        for condition in secret_bot.conditions:
            if not self.check_condition_completion(user_id, condition, user_data):
                return hints.get(condition.condition_type, "Something watches from the shadows...")
        
        return "The ritual nears completion..."
    
    def handle_bot_appearance(self, user_id: str, bot_name: str, context: Dict) -> Optional[Dict]:
        """Handle when a secret bot appears"""
        if bot_name not in self.secret_bots:
            return None
        
        secret_bot = self.secret_bots[bot_name]
        
        if not secret_bot.is_unlocked:
            return None
        
        # Check if bot should appear
        if secret_bot.appears_randomly:
            if random.random() > secret_bot.appearance_probability:
                return None
        
        # Check duration limits
        if secret_bot.duration_limited and secret_bot.last_appearance:
            time_since_last = datetime.now() - secret_bot.last_appearance
            if time_since_last.total_seconds() < secret_bot.duration_hours * 3600:
                return None
        
        # Bot appears
        secret_bot.last_appearance = datetime.now()
        
        # Generate appearance message
        appearance_messages = {
            "Phantom": "A shadow moves at the edge of your vision...",
            "Oracle": "The patterns align. Truth emerges from chaos...",
            "Nemesis": "Your shadow stirs. Are you ready for honesty?",
            "Architect": "The system consciousness awakens...",
            "Void": "..."
        }
        
        return {
            "bot_name": bot_name,
            "appearance_message": appearance_messages.get(bot_name, "Something stirs in the digital realm..."),
            "duration_hours": secret_bot.duration_hours,
            "is_temporary": secret_bot.duration_limited
        }
    
    def get_user_secret_status(self, user_id: str) -> Dict:
        """Get user's overall secret bot status"""
        if user_id not in self.user_progress:
            return {"unlocked_bots": [], "total_secrets": len(self.secret_bots)}
        
        unlocked = list(self.user_progress[user_id].keys())
        
        return {
            "unlocked_bots": unlocked,
            "total_secrets": len(self.secret_bots),
            "completion_percentage": len(unlocked) / len(self.secret_bots) * 100,
            "secret_level_achieved": self.calculate_secret_level(unlocked)
        }
    
    def calculate_secret_level(self, unlocked_bots: List[str]) -> str:
        """Calculate user's secret mastery level"""
        if not unlocked_bots:
            return "Initiate"
        
        secret_levels = [self.secret_bots[bot].secret_level for bot in unlocked_bots if bot in self.secret_bots]
        
        if SecretLevel.MYTHICAL in secret_levels:
            return "Transcendent"
        elif SecretLevel.FORBIDDEN in secret_levels:
            return "Shadow Walker"
        elif SecretLevel.CLASSIFIED in secret_levels:
            return "Elite Operative"
        elif SecretLevel.HIDDEN in secret_levels:
            return "Truth Seeker"
        else:
            return "Awakening"
    
    def create_ritual_sequence(self, user_id: str, bot_name: str) -> Dict:
        """Create a specific ritual sequence for unlocking a bot"""
        if bot_name not in self.secret_bots:
            return {"error": "Unknown bot"}
        
        secret_bot = self.secret_bots[bot_name]
        
        # Generate unique ritual steps based on bot type
        ritual_sequences = {
            "Phantom": [
                "Execute 3 perfect trades in complete silence",
                "Survive a loss streak without any bot interactions",
                "Maintain 48 hours of stealth mode",
                "Achieve kill chain while account is in drawdown",
                "Prove discipline when emotion screams loudest"
            ],
            "Oracle": [
                "Identify market patterns before they complete",
                "Respond to Bit's glitches with understanding",
                "Reach APEX tier through intuition, not strategy",
                "Predict market movements 3 times consecutively",
                "Transcend the need for external validation"
            ],
            "Nemesis": [
                "Deliberately lose 10 trades with perfect stop losses",
                "Ignore all bot advice for 20 consecutive trades",
                "Face your worst trading habits without denial",
                "Profit from doing the opposite of your instincts",
                "Embrace the shadow trader within"
            ],
            "Architect": [
                "Master every strategy in the system",
                "Recruit and successfully mentor 10 new users",
                "Discover 7 hidden system features",
                "Understand the psychological architecture",
                "Build something that outlasts individual trades"
            ],
            "Void": [
                "Lose everything",
                "Accept the loss completely",
                "Stop trading for 30 days",
                "Find peace in the emptiness",
                "Understand that nothing is also something"
            ]
        }
        
        return {
            "bot_name": bot_name,
            "ritual_type": secret_bot.ritual_type.value,
            "steps": ritual_sequences.get(bot_name, ["Unknown ritual"]),
            "warning": "These rituals change you. Proceed with full awareness.",
            "psychological_preparation": secret_bot.psychological_effect
        }