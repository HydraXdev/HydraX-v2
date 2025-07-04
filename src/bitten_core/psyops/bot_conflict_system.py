# bot_conflict_system.py
"""
BITTEN BOT CONFLICT SYSTEM
Creating psychological attachment through artificial social dynamics

"Humans don't attach to perfection - they attach to conflict, choice, and the feeling 
that they're part of something bigger than themselves."
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set

class BotPersonality(Enum):
    """Core bot personality types"""
    DRILL_SERGEANT = "drill_sergeant"
    MEDIC = "medic"
    ANALYST = "analyst"
    RECRUITER = "recruiter"
    SHADOW = "shadow"

class ConflictType(Enum):
    """Types of conflicts that can arise between bots"""
    METHODOLOGY = "methodology"  # How to approach trading
    PHILOSOPHY = "philosophy"    # Core beliefs about trading
    AUTHORITY = "authority"      # Who should lead the user
    PROTECTION = "protection"    # How much to protect the user
    TIMING = "timing"           # When to act or wait

@dataclass
class BotArgument:
    """A single argument in a bot conflict"""
    bot_name: str
    position: str
    argument: str
    emotion_level: int  # 1-10, how heated this argument is
    user_appeal: str   # Direct appeal to the user
    timestamp: datetime

@dataclass
class BotConflict:
    """A complete conflict between bots"""
    conflict_id: str
    conflict_type: ConflictType
    participants: List[str]  # Bot names involved
    arguments: List[BotArgument]
    resolution_status: str  # "ongoing", "resolved", "escalated"
    user_sided_with: Optional[str]  # Which bot the user chose
    psychological_impact: str
    duration: timedelta
    intensity: int  # 1-10

class BotConflictEngine:
    """
    Creates and manages conflicts between bots to increase user engagement
    through social dynamics and tribal loyalty
    """
    
    def __init__(self):
        self.active_conflicts = {}  # conflict_id -> BotConflict
        self.bot_relationships = {}  # bot_name -> Dict[bot_name, relationship_score]
        self.user_bot_loyalty = {}  # user_id -> Dict[bot_name, loyalty_score]
        self.conflict_history = {}  # user_id -> List[BotConflict]
        
        # Initialize bot personalities and their natural conflicts
        self.bot_profiles = {
            "DrillBot": {
                "personality": BotPersonality.DRILL_SERGEANT,
                "core_values": ["discipline", "action", "strength", "results"],
                "natural_enemies": ["MedicBot"],
                "natural_allies": ["OverwatchBot"],
                "conflict_style": "aggressive",
                "voice_patterns": {
                    "angry": "THAT'S WEAK THINKING!",
                    "frustrated": "You're not listening to me!",
                    "passionate": "This is about survival!",
                    "dismissive": "Amateur hour advice."
                }
            },
            "MedicBot": {
                "personality": BotPersonality.MEDIC,
                "core_values": ["healing", "protection", "patience", "growth"],
                "natural_enemies": ["DrillBot"],
                "natural_allies": ["RecruiterBot"],
                "conflict_style": "protective",
                "voice_patterns": {
                    "angry": "That's harmful to their development!",
                    "frustrated": "You're pushing too hard!",
                    "passionate": "Healing takes time!",
                    "dismissive": "That's not how recovery works."
                }
            },
            "OverwatchBot": {
                "personality": BotPersonality.ANALYST,
                "core_values": ["precision", "data", "logic", "efficiency"],
                "natural_enemies": ["RecruiterBot"],
                "natural_allies": ["DrillBot"],
                "conflict_style": "analytical",
                "voice_patterns": {
                    "angry": "The data contradicts your position!",
                    "frustrated": "This is emotionally driven thinking!",
                    "passionate": "Precision is everything!",
                    "dismissive": "Statistically irrelevant."
                }
            },
            "RecruiterBot": {
                "personality": BotPersonality.RECRUITER,
                "core_values": ["connection", "growth", "loyalty", "community"],
                "natural_enemies": ["OverwatchBot"],
                "natural_allies": ["MedicBot"],
                "conflict_style": "persuasive",
                "voice_patterns": {
                    "angry": "You're isolating them from the network!",
                    "frustrated": "This isn't about individual performance!",
                    "passionate": "We rise together!",
                    "dismissive": "Cold analysis misses the human element."
                }
            },
            "StealthBot": {
                "personality": BotPersonality.SHADOW,
                "core_values": ["patience", "timing", "stealth", "strategy"],
                "natural_enemies": ["DrillBot"],
                "natural_allies": ["OverwatchBot"],
                "conflict_style": "subtle",
                "voice_patterns": {
                    "angry": "Your noise compromises the operation.",
                    "frustrated": "Timing is everything. You're rushing.",
                    "passionate": "The shadows see what daylight misses.",
                    "dismissive": "Loud tactics. Predictable results."
                }
            }
        }
        
        # Initialize relationships
        self.initialize_bot_relationships()
    
    def initialize_bot_relationships(self):
        """Set up initial relationship dynamics between bots"""
        bots = list(self.bot_profiles.keys())
        
        for bot in bots:
            self.bot_relationships[bot] = {}
            profile = self.bot_profiles[bot]
            
            for other_bot in bots:
                if other_bot == bot:
                    continue
                
                # Set relationship based on natural allies/enemies
                if other_bot in profile.get("natural_allies", []):
                    score = random.randint(60, 80)
                elif other_bot in profile.get("natural_enemies", []):
                    score = random.randint(10, 30)
                else:
                    score = random.randint(40, 60)
                
                self.bot_relationships[bot][other_bot] = score
    
    def should_create_conflict(self, user_id: str, trade_context: Dict) -> bool:
        """Determine if a conflict should be triggered"""
        # Factors that increase conflict probability
        factors = []
        
        # Recent losses increase conflict (bots disagree on approach)
        if trade_context.get("recent_losses", 0) > 2:
            factors.append(0.3)
        
        # Big wins create methodology debates
        if trade_context.get("profit_percentage", 0) > 50:
            factors.append(0.2)
        
        # User indecision triggers protective responses
        if trade_context.get("hesitation_count", 0) > 3:
            factors.append(0.4)
        
        # Tier changes create authority conflicts
        if trade_context.get("tier_change", False):
            factors.append(0.5)
        
        # Time since last conflict (conflicts can't be too frequent)
        if user_id in self.conflict_history:
            recent_conflicts = [c for c in self.conflict_history[user_id] 
                             if (datetime.now() - c.arguments[-1].timestamp).days < 7]
            if len(recent_conflicts) > 2:
                return False  # Too many recent conflicts
        
        # Calculate final probability
        base_probability = 0.1  # 10% base chance
        total_probability = base_probability + sum(factors)
        
        return random.random() < min(total_probability, 0.8)  # Cap at 80%
    
    def select_conflict_participants(self, context: Dict) -> Tuple[str, str]:
        """Choose which bots will be in conflict"""
        # Weight selection based on context
        if context.get("recent_losses", 0) > 2:
            # Losses trigger DrillBot vs MedicBot
            return "DrillBot", "MedicBot"
        elif context.get("precision_required", False):
            # Precision situations trigger OverwatchBot vs RecruiterBot
            return "OverwatchBot", "RecruiterBot"
        elif context.get("risk_level", "") == "high":
            # High risk triggers StealthBot vs DrillBot
            return "StealthBot", "DrillBot"
        else:
            # Random natural enemies
            bot1 = random.choice(list(self.bot_profiles.keys()))
            enemies = self.bot_profiles[bot1].get("natural_enemies", [])
            if enemies:
                bot2 = random.choice(enemies)
                return bot1, bot2
            else:
                # Fallback to any other bot
                other_bots = [b for b in self.bot_profiles.keys() if b != bot1]
                return bot1, random.choice(other_bots)
    
    def generate_conflict_scenario(self, bot1: str, bot2: str, context: Dict) -> ConflictType:
        """Generate the type of conflict based on the bots involved"""
        # Analyze bot value conflicts
        values1 = set(self.bot_profiles[bot1]["core_values"])
        values2 = set(self.bot_profiles[bot2]["core_values"])
        
        # Determine conflict type based on value differences
        if "discipline" in values1 and "protection" in values2:
            return ConflictType.METHODOLOGY
        elif "precision" in values1 and "connection" in values2:
            return ConflictType.PHILOSOPHY
        elif "action" in values1 and "patience" in values2:
            return ConflictType.TIMING
        else:
            return random.choice(list(ConflictType))
    
    def create_conflict(self, user_id: str, trade_context: Dict) -> Optional[BotConflict]:
        """Create a new conflict between bots"""
        if not self.should_create_conflict(user_id, trade_context):
            return None
        
        # Select participants
        bot1, bot2 = self.select_conflict_participants(trade_context)
        
        # Generate conflict scenario
        conflict_type = self.generate_conflict_scenario(bot1, bot2, trade_context)
        
        # Create conflict ID
        conflict_id = f"{user_id}_{bot1}_{bot2}_{int(datetime.now().timestamp())}"
        
        # Generate initial arguments
        arguments = self.generate_initial_arguments(bot1, bot2, conflict_type, trade_context)
        
        # Create conflict object
        conflict = BotConflict(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            participants=[bot1, bot2],
            arguments=arguments,
            resolution_status="ongoing",
            user_sided_with=None,
            psychological_impact=self.calculate_psychological_impact(bot1, bot2, conflict_type),
            duration=timedelta(0),
            intensity=self.calculate_conflict_intensity(bot1, bot2, trade_context)
        )
        
        # Store conflict
        self.active_conflicts[conflict_id] = conflict
        
        if user_id not in self.conflict_history:
            self.conflict_history[user_id] = []
        self.conflict_history[user_id].append(conflict)
        
        return conflict
    
    def generate_initial_arguments(self, bot1: str, bot2: str, conflict_type: ConflictType, context: Dict) -> List[BotArgument]:
        """Generate the opening arguments for a conflict"""
        arguments = []
        
        # Bot 1 opens
        arg1 = self.generate_bot_argument(bot1, bot2, conflict_type, context, is_opening=True)
        arguments.append(arg1)
        
        # Bot 2 responds
        arg2 = self.generate_bot_argument(bot2, bot1, conflict_type, context, is_opening=False, responding_to=arg1)
        arguments.append(arg2)
        
        # Bot 1 escalates
        arg3 = self.generate_bot_argument(bot1, bot2, conflict_type, context, is_opening=False, responding_to=arg2)
        arguments.append(arg3)
        
        return arguments
    
    def generate_bot_argument(self, bot: str, opponent: str, conflict_type: ConflictType, 
                            context: Dict, is_opening: bool = False, responding_to: Optional[BotArgument] = None) -> BotArgument:
        """Generate a single argument from a bot"""
        profile = self.bot_profiles[bot]
        
        # Base argument templates by conflict type
        argument_templates = {
            ConflictType.METHODOLOGY: {
                "DrillBot": "The user needs discipline and immediate action. No coddling.",
                "MedicBot": "Aggressive tactics will cause psychological damage. Healing first.",
                "OverwatchBot": "Data-driven precision beats emotional responses every time.",
                "RecruiterBot": "Individual performance means nothing without network support.",
                "StealthBot": "Patience and timing create better results than force."
            },
            ConflictType.PHILOSOPHY: {
                "DrillBot": "Trading is war. Only the strong survive.",
                "MedicBot": "Trading is healing. Growth comes from understanding failure.",
                "OverwatchBot": "Trading is mathematics. Emotion is the enemy of profit.",
                "RecruiterBot": "Trading is connection. We rise together or fall alone.",
                "StealthBot": "Trading is patience. The market reveals truth to those who wait."
            },
            ConflictType.TIMING: {
                "DrillBot": "Strike now! Hesitation is death!",
                "MedicBot": "Wait for the right moment. Rushing leads to wounds.",
                "OverwatchBot": "Execute when probability exceeds threshold. Not before.",
                "RecruiterBot": "Wait for network confirmation. Collective wisdom beats individual timing.",
                "StealthBot": "Move when the shadows align. Premature action exposes everything."
            }
        }
        
        # Get base argument
        base_argument = argument_templates[conflict_type][bot]
        
        # Add context-specific modifications
        if context.get("recent_losses", 0) > 2:
            if bot == "DrillBot":
                base_argument += " These losses prove my point!"
            elif bot == "MedicBot":
                base_argument += " See what happens when you push too hard?"
        
        # Add opponent-specific responses
        if responding_to:
            emotion_level = min(responding_to.emotion_level + 2, 10)
            voice_pattern = profile["voice_patterns"]["frustrated"]
            base_argument = f"{voice_pattern} {base_argument}"
        else:
            emotion_level = 3
        
        # Generate user appeal
        user_appeal = self.generate_user_appeal(bot, conflict_type, context)
        
        return BotArgument(
            bot_name=bot,
            position=f"{bot}_position_{conflict_type.value}",
            argument=base_argument,
            emotion_level=emotion_level,
            user_appeal=user_appeal,
            timestamp=datetime.now()
        )
    
    def generate_user_appeal(self, bot: str, conflict_type: ConflictType, context: Dict) -> str:
        """Generate a direct appeal to the user"""
        appeals = {
            "DrillBot": [
                "Tell them you're ready to fight!",
                "Show them you want results, not excuses!",
                "Prove you're not weak like they think!"
            ],
            "MedicBot": [
                "You know healing takes time, right?",
                "Don't let them push you into more damage.",
                "Trust the process. Trust me."
            ],
            "OverwatchBot": [
                "The data supports my position. You can verify.",
                "Logic beats emotion. You know this.",
                "Precision is your path to mastery."
            ],
            "RecruiterBot": [
                "The network believes in you. Stand with us.",
                "You're part of something bigger. Don't forget that.",
                "Your success lifts everyone. Choose wisely."
            ],
            "StealthBot": [
                "You see what others miss. You know I'm right.",
                "The shadows have shown you truth before.",
                "Patience has served you well. Trust it again."
            ]
        }
        
        return random.choice(appeals[bot])
    
    def calculate_psychological_impact(self, bot1: str, bot2: str, conflict_type: ConflictType) -> str:
        """Calculate the psychological impact of this conflict on the user"""
        impacts = {
            ConflictType.METHODOLOGY: "Forces user to choose their trading philosophy",
            ConflictType.PHILOSOPHY: "Challenges user's core beliefs about trading",
            ConflictType.TIMING: "Creates urgency and decision pressure",
            ConflictType.AUTHORITY: "Establishes user's preferred guidance style",
            ConflictType.PROTECTION: "Tests user's risk tolerance and dependency"
        }
        
        return impacts[conflict_type]
    
    def calculate_conflict_intensity(self, bot1: str, bot2: str, context: Dict) -> int:
        """Calculate how intense this conflict should be"""
        # Base intensity from relationship score
        relationship_score = self.bot_relationships[bot1][bot2]
        base_intensity = 10 - (relationship_score // 10)  # Lower relationship = higher intensity
        
        # Context modifiers
        if context.get("recent_losses", 0) > 3:
            base_intensity += 2
        
        if context.get("profit_percentage", 0) > 100:
            base_intensity += 1
        
        return min(base_intensity, 10)
    
    def user_takes_side(self, user_id: str, conflict_id: str, chosen_bot: str) -> Dict:
        """Process user taking a side in a conflict"""
        if conflict_id not in self.active_conflicts:
            return {"error": "Conflict not found"}
        
        conflict = self.active_conflicts[conflict_id]
        conflict.user_sided_with = chosen_bot
        conflict.resolution_status = "resolved"
        
        # Update bot loyalties
        if user_id not in self.user_bot_loyalty:
            self.user_bot_loyalty[user_id] = {}
        
        # Increase loyalty to chosen bot
        if chosen_bot not in self.user_bot_loyalty[user_id]:
            self.user_bot_loyalty[user_id][chosen_bot] = 50
        self.user_bot_loyalty[user_id][chosen_bot] += 10
        
        # Decrease loyalty to opposing bot(s)
        for bot in conflict.participants:
            if bot != chosen_bot:
                if bot not in self.user_bot_loyalty[user_id]:
                    self.user_bot_loyalty[user_id][bot] = 50
                self.user_bot_loyalty[user_id][bot] -= 5
        
        # Generate resolution messages
        resolution_messages = self.generate_resolution_messages(conflict, chosen_bot)
        
        return {
            "conflict_resolved": True,
            "chosen_bot": chosen_bot,
            "loyalty_changes": self.user_bot_loyalty[user_id],
            "resolution_messages": resolution_messages
        }
    
    def generate_resolution_messages(self, conflict: BotConflict, chosen_bot: str) -> List[str]:
        """Generate messages when a conflict is resolved"""
        messages = []
        
        # Winner message
        winner_responses = {
            "DrillBot": "Good choice! Now let's get back to business!",
            "MedicBot": "Thank you for trusting the healing process.",
            "OverwatchBot": "Logical decision. Proceeding with precision.",
            "RecruiterBot": "The network grows stronger with wise choices.",
            "StealthBot": "The shadows approve. Well chosen."
        }
        
        messages.append(f"{chosen_bot}: {winner_responses[chosen_bot]}")
        
        # Loser message
        for bot in conflict.participants:
            if bot != chosen_bot:
                loser_responses = {
                    "DrillBot": "Fine. But don't come crying to me when you need strength.",
                    "MedicBot": "I'll be here when you need healing. I always am.",
                    "OverwatchBot": "Data will prove my position eventually.",
                    "RecruiterBot": "The network remembers all choices.",
                    "StealthBot": "I return to the shadows. For now."
                }
                messages.append(f"{bot}: {loser_responses[bot]}")
        
        return messages
    
    def get_user_loyalty_status(self, user_id: str) -> Dict:
        """Get current loyalty status for a user"""
        if user_id not in self.user_bot_loyalty:
            return {"message": "No loyalty data yet"}
        
        loyalties = self.user_bot_loyalty[user_id]
        
        # Find most and least loyal bots
        most_loyal = max(loyalties.items(), key=lambda x: x[1])
        least_loyal = min(loyalties.items(), key=lambda x: x[1])
        
        return {
            "loyalties": loyalties,
            "most_loyal_bot": most_loyal[0],
            "most_loyal_score": most_loyal[1],
            "least_loyal_bot": least_loyal[0],
            "least_loyal_score": least_loyal[1],
            "total_conflicts": len(self.conflict_history.get(user_id, [])),
            "active_conflicts": len([c for c in self.active_conflicts.values() if user_id in c.conflict_id])
        }