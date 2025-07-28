"""
XP Celebration System for BITTEN
Dynamic, immersive celebrations for every XP gain and achievement
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import random
import logging

# Removed references to manipulation systems
# from .psyops.adaptive_bot_system import NPCPersonality, NPCResponse
from enum import Enum
from dataclasses import dataclass

class NPCPersonality(Enum):
    """Basic NPC personalities for positive interaction"""
    DRILL_INSTRUCTOR = "drill_instructor"
    TACTICAL_ANALYST = "tactical_analyst"
    PSYCHOLOGIST = "psychologist"
    MYSTERIOUS_INSIDER = "mysterious_insider"

@dataclass
class NPCResponse:
    """Simple NPC response structure"""
    personality: NPCPersonality
    message: str
    emotion: str

logger = logging.getLogger(__name__)

class CelebrationTier(Enum):
    """Tiers of celebration intensity"""
    MICRO = "micro"          # 1-50 XP
    SMALL = "small"          # 51-200 XP
    MEDIUM = "medium"        # 201-500 XP
    LARGE = "large"          # 501-1000 XP
    EPIC = "epic"            # 1001-5000 XP
    LEGENDARY = "legendary"  # 5000+ XP

class EventType(Enum):
    """Types of XP earning events"""
    TRADE_WIN = "trade_win"
    TRADE_TP_HIT = "trade_tp_hit"
    CHALLENGE_COMPLETE = "challenge_complete"
    MEDAL_EARNED = "medal_earned"
    LEVEL_UP = "level_up"
    PRESTIGE = "prestige"
    PURCHASE = "purchase"
    STREAK = "streak"
    RECRUIT_MILESTONE = "recruit_milestone"

@dataclass
class CelebrationEvent:
    """A celebration event with all its components"""
    event_type: EventType
    xp_amount: int
    tier: CelebrationTier
    title: str
    message: str
    npc_reactions: List[NPCResponse]
    sound_effect: str
    visual_effect: str
    duration_ms: int
    metadata: Dict[str, Any]

class XPCelebrationSystem:
    """Manages immersive celebrations for XP gains"""
    
    # Sound effect configurations
    SOUND_EFFECTS = {
        CelebrationTier.MICRO: {
            "name": "coin_drop",
            "config": {
                "type": "coin",
                "pitch": 1.0,
                "duration": 200
            }
        },
        CelebrationTier.SMALL: {
            "name": "coin_cascade",
            "config": {
                "type": "coin_cascade",
                "count": 3,
                "pitch_variance": 0.1,
                "duration": 500
            }
        },
        CelebrationTier.MEDIUM: {
            "name": "cash_register",
            "config": {
                "type": "kaching",
                "pitch": 1.0,
                "bell_count": 1,
                "duration": 800
            }
        },
        CelebrationTier.LARGE: {
            "name": "cash_register_jackpot",
            "config": {
                "type": "kaching_multi",
                "pitch": 1.1,
                "bell_count": 3,
                "coin_shower": True,
                "duration": 1500
            }
        },
        CelebrationTier.EPIC: {
            "name": "victory_fanfare",
            "config": {
                "type": "fanfare",
                "cash_register": True,
                "duration": 2000
            }
        },
        CelebrationTier.LEGENDARY: {
            "name": "legendary_achievement",
            "config": {
                "type": "legendary",
                "orchestral": True,
                "duration": 3000
            }
        }
    }
    
    # Visual effect configurations
    VISUAL_EFFECTS = {
        CelebrationTier.MICRO: "sparkle_burst",
        CelebrationTier.SMALL: "coin_fountain",
        CelebrationTier.MEDIUM: "golden_explosion",
        CelebrationTier.LARGE: "rainbow_cascade",
        CelebrationTier.EPIC: "screen_takeover",
        CelebrationTier.LEGENDARY: "matrix_rain_gold"
    }
    
    # NPC celebration responses by personality
    NPC_CELEBRATIONS = {
        NPCPersonality.DRILL_INSTRUCTOR: {
            CelebrationTier.MICRO: [
                "That's it, maggot! Every XP counts!",
                "Keep stacking those points, soldier!",
                "Small wins build champions!"
            ],
            CelebrationTier.MEDIUM: [
                "NOW WE'RE TALKING! THAT'S HOW YOU EARN!",
                "OUTSTANDING! You're becoming a MACHINE!",
                "That's what I'm TALKING ABOUT! HOORAH!"
            ],
            CelebrationTier.EPIC: [
                "HOLY MOTHER OF GAINS! YOU'RE A BEAST!",
                "THAT'S MY SOLDIER! CRUSHING IT!",
                "I'VE CREATED A MONSTER! MAGNIFICENT!"
            ]
        },
        NPCPersonality.TACTICAL_ANALYST: {
            CelebrationTier.MICRO: [
                "Efficient XP accumulation detected. Trajectory: positive.",
                "Small gains compound. Mathematical certainty.",
                "Data point registered. Progress: measurable."
            ],
            CelebrationTier.MEDIUM: [
                "Significant XP influx! Statistical anomaly in your favor.",
                "Calculation complete: You're exceeding projections by 47%.",
                "This earning rate suggests elite-tier performance metrics."
            ],
            CelebrationTier.EPIC: [
                "ALERT: Extreme positive variance detected! This is statistically beautiful!",
                "My algorithms are overheating! This performance is... optimal!",
                "You've broken my models! In the best possible way!"
            ]
        },
        NPCPersonality.PSYCHOLOGIST: {
            CelebrationTier.MICRO: [
                "Feel that dopamine hit? Your brain loves progress! 🧠",
                "Small wins trigger big momentum. You're building habits!",
                "Notice how good that feels? That's success programming itself."
            ],
            CelebrationTier.MEDIUM: [
                "Your confidence must be SOARING! This is transformative!",
                "I'm seeing a warrior emerge! Your mindset is evolving!",
                "This is more than XP - this is self-actualization!"
            ],
            CelebrationTier.EPIC: [
                "THIS IS BREAKTHROUGH TERRITORY! You've shattered your limits!",
                "I'm witnessing psychological evolution in real-time! INCREDIBLE!",
                "You're not the same trader who started! You've TRANSFORMED!"
            ]
        },
        NPCPersonality.MYSTERIOUS_INSIDER: {
            CelebrationTier.MICRO: [
                "*whispers* They notice everything... even small gains...",
                "The system rewards those who persist... interesting...",
                "Every XP brings you deeper into the circle..."
            ],
            CelebrationTier.MEDIUM: [
                "The watchers are impressed... few earn this quickly...",
                "You're attracting attention from... higher places...",
                "This rate of gain? You're marked for something greater..."
            ],
            CelebrationTier.EPIC: [
                "THE INNER CIRCLE IS WATCHING! You've caught their eye!",
                "Legends speak of traders like you... the chosen ones...",
                "I've never seen anyone rise this fast... what ARE you?"
            ]
        }
    }
    
    def __init__(self):
        self.recent_celebrations = []  # Track recent celebrations to avoid repetition
        self.combo_multiplier = 1.0    # Increases with rapid gains
        self.last_celebration = None
    
    def celebrate_xp_gain(
        self,
        event_type: EventType,
        xp_amount: int,
        user_data: Dict[str, Any],
        event_metadata: Optional[Dict[str, Any]] = None
    ) -> CelebrationEvent:
        """Create a dynamic celebration for XP gain"""
        tier = self._calculate_tier(xp_amount)
        
        # Generate celebration components
        title = self._generate_title(event_type, xp_amount, tier)
        message = self._generate_message(event_type, xp_amount, user_data, event_metadata)
        npc_reactions = self._generate_npc_reactions(tier, event_type)
        
        # Get effects
        sound_effect = self.SOUND_EFFECTS[tier]
        visual_effect = self.VISUAL_EFFECTS[tier]
        
        # Calculate duration based on tier
        duration_ms = 500 + (tier.value.count('e') * 500)  # Longer for epic/legendary
        
        # Check for combo
        if self._is_combo():
            self.combo_multiplier = min(self.combo_multiplier + 0.1, 2.0)
            title = f"🔥 COMBO x{self.combo_multiplier:.1f}! {title}"
            duration_ms = int(duration_ms * 1.2)
        else:
            self.combo_multiplier = 1.0
        
        celebration = CelebrationEvent(
            event_type=event_type,
            xp_amount=xp_amount,
            tier=tier,
            title=title,
            message=message,
            npc_reactions=npc_reactions,
            sound_effect=sound_effect["name"],
            visual_effect=visual_effect,
            duration_ms=duration_ms,
            metadata=event_metadata or {}
        )
        
        self.recent_celebrations.append(celebration)
        self.last_celebration = datetime.now()
        
        # Keep only last 10 celebrations
        if len(self.recent_celebrations) > 10:
            self.recent_celebrations.pop(0)
        
        return celebration
    
    def _calculate_tier(self, xp_amount: int) -> CelebrationTier:
        """Calculate celebration tier based on XP amount"""
        if xp_amount >= 5000:
            return CelebrationTier.LEGENDARY
        elif xp_amount >= 1001:
            return CelebrationTier.EPIC
        elif xp_amount >= 501:
            return CelebrationTier.LARGE
        elif xp_amount >= 201:
            return CelebrationTier.MEDIUM
        elif xp_amount >= 51:
            return CelebrationTier.SMALL
        else:
            return CelebrationTier.MICRO
    
    def _generate_title(self, event_type: EventType, xp_amount: int, tier: CelebrationTier) -> str:
        """Generate dynamic celebration title"""
        base_titles = {
            EventType.TRADE_WIN: [
                f"💰 +{xp_amount} XP! Trade Victory!",
                f"🎯 Target Hit! +{xp_amount} XP!",
                f"💸 Profit Secured! +{xp_amount} XP!"
            ],
            EventType.TRADE_TP_HIT: [
                f"🎯 PERFECT TP! +{xp_amount} XP!",
                f"💯 Take Profit SMASHED! +{xp_amount} XP!",
                f"🏆 TP Achievement! +{xp_amount} XP!"
            ],
            EventType.CHALLENGE_COMPLETE: [
                f"✅ Challenge Crushed! +{xp_amount} XP!",
                f"🏅 Mission Accomplished! +{xp_amount} XP!",
                f"⚡ Challenge Dominated! +{xp_amount} XP!"
            ],
            EventType.MEDAL_EARNED: [
                f"🏆 NEW MEDAL! +{xp_amount} XP!",
                f"🥇 Achievement Unlocked! +{xp_amount} XP!",
                f"🌟 Medal Secured! +{xp_amount} XP!"
            ],
            EventType.PRESTIGE: [
                f"👑 PRESTIGE ACHIEVED! +{xp_amount} XP!",
                f"⭐ LEGENDARY STATUS! +{xp_amount} XP!",
                f"🌟 ASCENSION COMPLETE! +{xp_amount} XP!"
            ]
        }
        
        titles = base_titles.get(event_type, [f"🎉 +{xp_amount} XP!"])
        title = random.choice(titles)
        
        # Add tier-specific flair
        if tier == CelebrationTier.LEGENDARY:
            title = f"🌟💎🌟 {title} 🌟💎🌟"
        elif tier == CelebrationTier.EPIC:
            title = f"⚡🔥 {title} 🔥⚡"
        
        return title
    
    def _generate_message(
        self,
        event_type: EventType,
        xp_amount: int,
        user_data: Dict[str, Any],
        event_metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Generate contextual celebration message"""
        rank = user_data.get("rank", "RECRUIT")
        total_xp = user_data.get("total_xp", 0)
        
        if event_type == EventType.TRADE_WIN:
            profit = event_metadata.get("profit", 0) if event_metadata else 0
            return f"{rank}, you've earned {xp_amount} XP from a ${profit:.2f} victory! Total: {total_xp + xp_amount:} XP"
        
        elif event_type == EventType.TRADE_TP_HIT:
            accuracy = event_metadata.get("accuracy_percent", 100) if event_metadata else 100
            return f"TP hit with {accuracy:.1f}% accuracy! {xp_amount} XP earned! Precision pays!"
        
        elif event_type == EventType.CHALLENGE_COMPLETE:
            challenge_name = event_metadata.get("challenge_name", "Daily Challenge") if event_metadata else "Daily Challenge"
            return f"'{challenge_name}' completed! {xp_amount} XP secured! Keep crushing those goals!"
        
        elif event_type == EventType.PRESTIGE:
            new_level = event_metadata.get("prestige_level", 1) if event_metadata else 1
            return f"Welcome to Prestige Level {new_level}! Your legacy grows stronger!"
        
        else:
            return f"Exceptional performance rewarded! +{xp_amount} XP!"
    
    def _generate_npc_reactions(self, tier: CelebrationTier, event_type: EventType) -> List[NPCResponse]:
        """Generate dynamic NPC reactions"""
        reactions = []
        
        # Always include drill instructor
        drill_responses = self.NPC_CELEBRATIONS[NPCPersonality.DRILL_INSTRUCTOR].get(
            tier, 
            self.NPC_CELEBRATIONS[NPCPersonality.DRILL_INSTRUCTOR][CelebrationTier.MICRO]
        )
        reactions.append(NPCResponse(
            personality=NPCPersonality.DRILL_INSTRUCTOR,
            message=random.choice(drill_responses),
            emotion="excited" if tier.value in ["epic", "legendary"] else "proud"
        ))
        
        # Add other NPCs for bigger celebrations
        if tier.value in ["medium", "large", "epic", "legendary"]:
            # Add tactical analyst
            analyst_responses = self.NPC_CELEBRATIONS[NPCPersonality.TACTICAL_ANALYST].get(tier, [])
            if analyst_responses:
                reactions.append(NPCResponse(
                    personality=NPCPersonality.TACTICAL_ANALYST,
                    message=random.choice(analyst_responses),
                    emotion="analytical"
                ))
        
        if tier.value in ["large", "epic", "legendary"]:
            # Add psychologist
            psych_responses = self.NPC_CELEBRATIONS[NPCPersonality.PSYCHOLOGIST].get(tier, [])
            if psych_responses:
                reactions.append(NPCResponse(
                    personality=NPCPersonality.PSYCHOLOGIST,
                    message=random.choice(psych_responses),
                    emotion="inspired"
                ))
        
        if tier.value in ["epic", "legendary"]:
            # Add mysterious insider for epic moments
            insider_responses = self.NPC_CELEBRATIONS[NPCPersonality.MYSTERIOUS_INSIDER].get(tier, [])
            if insider_responses:
                reactions.append(NPCResponse(
                    personality=NPCPersonality.MYSTERIOUS_INSIDER,
                    message=random.choice(insider_responses),
                    emotion="intrigued"
                ))
        
        return reactions
    
    def _is_combo(self) -> bool:
        """Check if this is a combo celebration"""
        if self.last_celebration:
            time_diff = (datetime.now() - self.last_celebration).total_seconds()
            return time_diff < 10  # Within 10 seconds
        return False
    
    def get_milestone_celebration(
        self,
        milestone_type: str,
        user_data: Dict[str, Any]
    ) -> CelebrationEvent:
        """Special celebrations for major milestones"""
        milestone_configs = {
            "first_trade": {
                "xp": 100,
                "title": "🎖️ FIRST BLOOD! Welcome to the battlefield!",
                "message": "You've taken your first shot! The journey begins!"
            },
            "first_win": {
                "xp": 250,
                "title": "🏆 FIRST VICTORY! You're officially dangerous!",
                "message": "First win secured! Many more to come!"
            },
            "10k_xp": {
                "xp": 1000,
                "title": "💎 10,000 XP MILESTONE! You're becoming elite!",
                "message": "Five figures! You're in rare company now!"
            },
            "50k_xp": {
                "xp": 5000,
                "title": "👑 50,000 XP! PRESTIGE AWAITS!",
                "message": "Half way to six figures! Legends are watching!"
            },
            "100k_xp": {
                "xp": 10000,
                "title": "🌟 100,000 XP! YOU ARE LEGENDARY!",
                "message": "Six figure trader! You've joined the elite!"
            }
        }
        
        config = milestone_configs.get(milestone_type, {
            "xp": 500,
            "title": "🎉 MILESTONE REACHED!",
            "message": "Incredible achievement unlocked!"
        })
        
        return self.celebrate_xp_gain(
            EventType.LEVEL_UP,
            config["xp"],
            user_data,
            {"milestone": milestone_type, "special": True}
        )

# Audio generation functions for web integration
def generate_cash_register_sound_config() -> Dict[str, Any]:
    """Generate configuration for cash register sound effect"""
    return {
        "type": "cash_register",
        "components": [
            {
                "type": "bell",
                "frequency": 2800,
                "duration": 100,
                "decay": 0.3,
                "volume": 0.8
            },
            {
                "type": "coins",
                "count": 5,
                "base_frequency": 4000,
                "frequency_variance": 500,
                "delay_between": 50,
                "duration": 30,
                "volume": 0.6
            },
            {
                "type": "drawer",
                "frequency": 150,
                "duration": 200,
                "attack": 0.01,
                "decay": 0.5,
                "volume": 0.4
            }
        ],
        "reverb": {
            "enabled": True,
            "roomSize": 0.3,
            "decay": 1.5,
            "wet": 0.2
        }
    }

def generate_tp_hit_celebration_sound() -> Dict[str, Any]:
    """Generate special sound for TP hits"""
    return {
        "type": "tp_celebration",
        "sequence": [
            {
                "type": "rise",
                "start_frequency": 400,
                "end_frequency": 800,
                "duration": 200,
                "volume": 0.5
            },
            {
                "type": "bell_cascade",
                "frequencies": [2093, 2637, 3136, 4186],  # C7, E7, G7, C8
                "duration": 150,
                "delay_between": 50,
                "volume": 0.7
            },
            {
                "type": "success_chord",
                "frequencies": [523, 659, 784, 1047],  # C5 major chord
                "duration": 500,
                "attack": 0.05,
                "decay": 0.4,
                "volume": 0.6
            }
        ]
    }

# Example usage
if __name__ == "__main__":
    celebration_system = XPCelebrationSystem()
    
    # Simulate a trade win
    user_data = {
        "rank": "SERGEANT",
        "total_xp": 5420
    }
    
    celebration = celebration_system.celebrate_xp_gain(
        EventType.TRADE_WIN,
        250,
        user_data,
        {"profit": 125.50}
    )
    
    print(f"Title: {celebration.title}")
    print(f"Message: {celebration.message}")
    print(f"Sound: {celebration.sound_effect}")
    print(f"Visual: {celebration.visual_effect}")
    print("\nNPC Reactions:")
    for reaction in celebration.npc_reactions:
        print(f"- {reaction.personality.value}: {reaction.message}")