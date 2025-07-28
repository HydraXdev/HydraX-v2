"""
NPC XP Integration for BITTEN
Connects NPCs with XP economy for immersive celebrations and guidance
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import random
import logging

from .xp_celebration_system import XPCelebrationSystem, EventType
# Removed references to manipulation systems
# from .psyops.adaptive_bot_system import AdaptiveBotSystem, NPCPersonality
from enum import Enum

class NPCPersonality(Enum):
    """Basic NPC personalities for positive interaction"""
    DRILL_INSTRUCTOR = "drill_instructor"
    TACTICAL_ANALYST = "tactical_analyst"
    PSYCHOLOGIST = "psychologist"
    MYSTERIOUS_INSIDER = "mysterious_insider"
from .xp_integration import XPIntegrationManager

logger = logging.getLogger(__name__)

class NPCMood(Enum):
    """NPC emotional states based on user performance"""
    ECSTATIC = "ecstatic"       # Amazing performance
    PROUD = "proud"             # Good performance
    ENCOURAGING = "encouraging"  # Average performance
    CONCERNED = "concerned"     # Poor performance
    URGENT = "urgent"           # Critical situation

@dataclass
class NPCDialogue:
    """Dynamic dialogue based on context"""
    personality: NPCPersonality
    mood: NPCMood
    message: str
    emotion: str
    priority: int  # 1-10, higher = more important
    visual_cue: Optional[str] = None  # Special visual effect

class NPCXPIntegration:
    """Manages NPC interactions with XP system"""
    
    # Shop guidance by NPC
    SHOP_GUIDANCE = {
        NPCPersonality.DRILL_INSTRUCTOR: {
            "heat_map": "Intel wins wars! This heat map shows you where the action is!",
            "trailing_guard": "Protect your gains like you protect your squad! Auto-trailing is ESSENTIAL!",
            "extended_mag": "More ammo means more opportunities! Lock and load!",
            "fortress_mode": "Defense wins championships! This will save your ass!"
        },
        NPCPersonality.TACTICAL_ANALYST: {
            "heat_map": "Statistical advantage: 23% better pair selection with heat map data.",
            "split_command": "Risk optimization protocol. Secure 50% profit, maximize remainder.",
            "stealth_entry": "Pending orders reduce slippage by 0.3 pips average. Significant.",
            "special_ammo": "3% risk yields 50% higher returns when TCS exceeds 91%."
        },
        NPCPersonality.PSYCHOLOGIST: {
            "confidence_boost": "Knowing the exact TCS removes doubt. Confidence is your edge!",
            "rapid_reload": "Patience fatigue is real. This helps you stay disciplined.",
            "fortress_mode": "Protecting gains after wins prevents revenge trading. Smart!",
            "prestige": "Prestige isn't about XP - it's about proving your evolution!"
        }
    }
    
    # Challenge encouragement
    CHALLENGE_MOTIVATION = {
        "perfect_exit": {
            NPCPersonality.DRILL_INSTRUCTOR: "Precision is the difference between good and GREAT!",
            NPCPersonality.TACTICAL_ANALYST: "TP accuracy correlates with 40% higher monthly returns.",
            NPCPersonality.PSYCHOLOGIST: "Perfect exits build unshakeable confidence!"
        },
        "winning_streak": {
            NPCPersonality.DRILL_INSTRUCTOR: "MOMENTUM IS EVERYTHING! Keep that streak ALIVE!",
            NPCPersonality.TACTICAL_ANALYST: "Probability of 4th win after 3: 68.2%. Favorable odds.",
            NPCPersonality.PSYCHOLOGIST: "You're in the zone! This is flow state!"
        },
        "patience_pays": {
            NPCPersonality.DRILL_INSTRUCTOR: "DISCIPLINE! Wait for your shot like a sniper!",
            NPCPersonality.TACTICAL_ANALYST: "Full cooldown adherence increases win rate by 15%.",
            NPCPersonality.PSYCHOLOGIST: "Patience is your superpower. Own it!"
        }
    }
    
    def __init__(self, celebration_system: XPCelebrationSystem):
        self.celebration_system = celebration_system
        self.user_moods = {}  # Track mood per user
        self.last_interactions = {}  # Prevent spam
    
    def handle_xp_event(
        self,
        user_id: str,
        event_type: EventType,
        xp_amount: int,
        user_data: Dict[str, Any],
        event_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle an XP event with full NPC integration"""
        # Get celebration
        celebration = self.celebration_system.celebrate_xp_gain(
            event_type, xp_amount, user_data, event_metadata
        )
        
        # Determine user mood
        user_mood = self._calculate_user_mood(user_id, user_data, event_type, xp_amount)
        
        # Get contextual NPC responses
        npc_responses = self._generate_contextual_responses(
            user_id, event_type, xp_amount, user_mood, user_data, event_metadata
        )
        
        # Add special interactions for milestones
        if self._is_milestone(user_data, event_type):
            npc_responses.extend(self._generate_milestone_responses(user_data))
        
        # Create response package
        return {
            "celebration": celebration,
            "npc_responses": npc_responses,
            "user_mood": user_mood,
            "special_effects": self._get_special_effects(celebration.tier, user_mood),
            "follow_up_actions": self._suggest_follow_up(user_id, user_data, event_type)
        }
    
    def provide_shop_guidance(
        self,
        user_id: str,
        affordable_items: List[Dict[str, Any]],
        user_profile: Dict[str, Any]
    ) -> List[NPCDialogue]:
        """NPCs provide personalized shop recommendations"""
        dialogues = []
        
        # Analyze user needs
        win_rate = user_profile.get("success_rate", 50)
        total_trades = user_profile.get("total_trades", 0)
        current_tier = user_profile.get("tier", "NIBBLER")
        
        # Drill instructor always has an opinion
        if affordable_items:
            top_pick = self._get_drill_instructor_pick(affordable_items, user_profile)
            if top_pick:
                dialogues.append(NPCDialogue(
                    personality=NPCPersonality.DRILL_INSTRUCTOR,
                    mood=NPCMood.URGENT,
                    message=f"Listen up! You NEED {top_pick['name']}! {self.SHOP_GUIDANCE[NPCPersonality.DRILL_INSTRUCTOR].get(top_pick['item_id'], 'This will make you LETHAL!')}",
                    emotion="commanding",
                    priority=8
                ))
        
        # Analyst provides data-driven recommendation
        if win_rate < 60 and any(item['item_id'] == 'trailing_guard' for item in affordable_items):
            dialogues.append(NPCDialogue(
                personality=NPCPersonality.TACTICAL_ANALYST,
                mood=NPCMood.ENCOURAGING,
                message="Analysis: Your 40% loss rate suggests profit protection priority. Trailing Guard recommended.",
                emotion="analytical",
                priority=7
            ))
        
        # Psychologist addresses mindset
        if total_trades > 50 and any(item['item_id'] == 'confidence_boost' for item in affordable_items):
            dialogues.append(NPCDialogue(
                personality=NPCPersonality.PSYCHOLOGIST,
                mood=NPCMood.ENCOURAGING,
                message="You've proven yourself with 50+ trades. Confidence Boost will eliminate second-guessing!",
                emotion="supportive",
                priority=6
            ))
        
        return dialogues
    
    def celebrate_challenge_progress(
        self,
        user_id: str,
        challenge_type: str,
        progress: int,
        target: int,
        completed: bool
    ) -> List[NPCDialogue]:
        """NPCs react to challenge progress"""
        dialogues = []
        progress_percent = (progress / target) * 100 if target > 0 else 0
        
        if completed:
            # Epic celebration from all NPCs
            dialogues.extend([
                NPCDialogue(
                    personality=NPCPersonality.DRILL_INSTRUCTOR,
                    mood=NPCMood.ECSTATIC,
                    message="OUTSTANDING! Challenge DOMINATED! You're becoming UNSTOPPABLE!",
                    emotion="celebrating",
                    priority=10,
                    visual_cue="explosion"
                ),
                NPCDialogue(
                    personality=NPCPersonality.TACTICAL_ANALYST,
                    mood=NPCMood.PROUD,
                    message=f"Challenge completion rate: 100%. Efficiency rating: EXCEPTIONAL.",
                    emotion="impressed",
                    priority=8
                ),
                NPCDialogue(
                    personality=NPCPersonality.PSYCHOLOGIST,
                    mood=NPCMood.ECSTATIC,
                    message="YES! You're proving that limits are just suggestions! Keep pushing!",
                    emotion="inspired",
                    priority=9
                )
            ])
        elif progress_percent >= 50:
            # Encouragement at halfway
            motivation = self.CHALLENGE_MOTIVATION.get(challenge_type, {})
            for personality, message in motivation.items():
                dialogues.append(NPCDialogue(
                    personality=personality,
                    mood=NPCMood.ENCOURAGING,
                    message=message,
                    emotion="motivating",
                    priority=6
                ))
        
        return dialogues
    
    def handle_prestige_moment(
        self,
        user_id: str,
        prestige_level: int,
        prestige_rank: str
    ) -> List[NPCDialogue]:
        """Special NPC reactions for prestige moments"""
        dialogues = []
        
        # Drill Instructor - Maximum hype
        dialogues.append(NPCDialogue(
            personality=NPCPersonality.DRILL_INSTRUCTOR,
            mood=NPCMood.ECSTATIC,
            message=f"ATTENTION ALL UNITS! We have a {prestige_rank} in our ranks! SALUTE THIS WARRIOR!",
            emotion="awestruck",
            priority=10,
            visual_cue="fireworks"
        ))
        
        # Tactical Analyst - Impressed by numbers
        dialogues.append(NPCDialogue(
            personality=NPCPersonality.TACTICAL_ANALYST,
            mood=NPCMood.PROUD,
            message=f"Prestige Level {prestige_level} achieved. You're in the top 0.1% of all traders. Statistically remarkable.",
            emotion="calculating",
            priority=9
        ))
        
        # Psychologist - Emotional moment
        dialogues.append(NPCDialogue(
            personality=NPCPersonality.PSYCHOLOGIST,
            mood=NPCMood.ECSTATIC,
            message="This isn't just about XP... You've transformed! The journey continues, but you're forever changed!",
            emotion="emotional",
            priority=10
        ))
        
        # Mysterious Insider appears
        dialogues.append(NPCDialogue(
            personality=NPCPersonality.MYSTERIOUS_INSIDER,
            mood=NPCMood.URGENT,
            message=f"*emerges from shadows* {prestige_rank}... The Inner Circle has been waiting for you. Check your messages.",
            emotion="mysterious",
            priority=10,
            visual_cue="glitch"
        ))
        
        return dialogues
    
    def _calculate_user_mood(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        event_type: EventType,
        xp_amount: int
    ) -> NPCMood:
        """Calculate overall mood based on performance"""
        # Recent performance
        win_rate = user_data.get("success_rate", 50)
        current_streak = user_data.get("current_streak", 0)
        
        # XP gain significance
        daily_average = user_data.get("daily_avg_xp", 1000)
        gain_ratio = xp_amount / daily_average if daily_average > 0 else 1
        
        if event_type == EventType.PRESTIGE:
            return NPCMood.ECSTATIC
        elif gain_ratio > 5 or current_streak >= 5:
            return NPCMood.ECSTATIC
        elif gain_ratio > 2 or win_rate > 70:
            return NPCMood.PROUD
        elif win_rate > 50:
            return NPCMood.ENCOURAGING
        elif win_rate < 40:
            return NPCMood.CONCERNED
        else:
            return NPCMood.ENCOURAGING
    
    def _generate_contextual_responses(
        self,
        user_id: str,
        event_type: EventType,
        xp_amount: int,
        mood: NPCMood,
        user_data: Dict[str, Any],
        event_metadata: Optional[Dict[str, Any]]
    ) -> List[NPCDialogue]:
        """Generate context-aware NPC responses"""
        responses = []
        
        # Always include drill instructor
        drill_message = self._get_drill_response(event_type, xp_amount, mood, user_data)
        responses.append(NPCDialogue(
            personality=NPCPersonality.DRILL_INSTRUCTOR,
            mood=mood,
            message=drill_message,
            emotion="intense",
            priority=7
        ))
        
        # Add analyst for data-heavy events
        if event_type in [EventType.TRADE_WIN, EventType.TRADE_TP_HIT]:
            analyst_message = self._get_analyst_response(event_type, xp_amount, event_metadata)
            responses.append(NPCDialogue(
                personality=NPCPersonality.TACTICAL_ANALYST,
                mood=mood,
                message=analyst_message,
                emotion="analytical",
                priority=6
            ))
        
        # Add psychologist for streaks and challenges
        if event_type in [EventType.CHALLENGE_COMPLETE, EventType.STREAK]:
            psych_message = self._get_psych_response(event_type, user_data)
            responses.append(NPCDialogue(
                personality=NPCPersonality.PSYCHOLOGIST,
                mood=mood,
                message=psych_message,
                emotion="supportive",
                priority=6
            ))
        
        return responses
    
    def _get_drill_response(
        self,
        event_type: EventType,
        xp_amount: int,
        mood: NPCMood,
        user_data: Dict[str, Any]
    ) -> str:
        """Get drill instructor's response"""
        rank = user_data.get("rank", "RECRUIT")
        
        if mood == NPCMood.ECSTATIC:
            return random.choice([
                f"HOLY HELL, {rank}! {xp_amount} XP?! YOU'RE A GODDAMN LEGEND!",
                f"THAT'S WHAT I'M TALKING ABOUT! {xp_amount} XP! UNSTOPPABLE!",
                f"SWEET MOTHER OF GAINS! {rank}, YOU'RE ON FIRE!"
            ])
        elif mood == NPCMood.PROUD:
            return random.choice([
                f"NOW THAT'S A SOLDIER! {xp_amount} XP earned like a PRO!",
                f"Outstanding work, {rank}! Keep stacking those gains!",
                f"That's my trader! {xp_amount} XP closer to greatness!"
            ])
        else:
            return random.choice([
                f"Every XP counts, {rank}! {xp_amount} in the bank!",
                f"Keep pushing! {xp_amount} XP is progress!",
                f"That's it! Build that momentum!"
            ])
    
    def _get_analyst_response(
        self,
        event_type: EventType,
        xp_amount: int,
        event_metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Get tactical analyst's response"""
        if event_type == EventType.TRADE_TP_HIT and event_metadata:
            accuracy = event_metadata.get("accuracy_percent", 100)
            return f"TP accuracy: {accuracy:.1f}%. XP efficiency: {xp_amount/accuracy:.1f} per percent. Optimal execution."
        elif event_type == EventType.TRADE_WIN and event_metadata:
            profit = event_metadata.get("profit", 0)
            roi = (xp_amount / profit * 100) if profit > 0 else 0
            return f"ROI analysis: ${profit:.2f} profit yielded {xp_amount} XP. Efficiency rating: {roi:.1f}%"
        else:
            return f"Data logged: {xp_amount} XP acquired. Performance metrics updating."
    
    def _get_psych_response(
        self,
        event_type: EventType,
        user_data: Dict[str, Any]
    ) -> str:
        """Get psychologist's response"""
        if event_type == EventType.STREAK:
            streak = user_data.get("current_streak", 0)
            return f"You're in flow state! {streak} wins in a row! Your confidence is becoming unshakeable!"
        elif event_type == EventType.CHALLENGE_COMPLETE:
            return "Challenge conquered! Notice how you're pushing past old limits? That's growth!"
        else:
            return "Feel that rush? Your brain is literally rewiring for success! Keep going!"
    
    def _is_milestone(self, user_data: Dict[str, Any], event_type: EventType) -> bool:
        """Check if this is a milestone moment"""
        total_xp = user_data.get("total_xp", 0)
        milestones = [1000, 5000, 10000, 25000, 50000, 100000]
        
        return (
            event_type == EventType.PRESTIGE or
            event_type == EventType.LEVEL_UP or
            any(abs(total_xp - m) < 100 for m in milestones)
        )
    
    def _generate_milestone_responses(self, user_data: Dict[str, Any]) -> List[NPCDialogue]:
        """Generate special milestone responses"""
        responses = []
        total_xp = user_data.get("total_xp", 0)
        
        if total_xp >= 100000:
            responses.append(NPCDialogue(
                personality=NPCPersonality.MYSTERIOUS_INSIDER,
                mood=NPCMood.URGENT,
                message="Six figures... You've transcended. The Inner Circle awaits. 🌟",
                emotion="cryptic",
                priority=10,
                visual_cue="matrix"
            ))
        
        return responses
    
    def _get_special_effects(self, tier: Any, mood: NPCMood) -> List[str]:
        """Get special effects based on celebration tier and mood"""
        effects = []
        
        if mood == NPCMood.ECSTATIC:
            effects.extend(["screen_shake", "rainbow_explosion", "max_haptic"])
        elif mood == NPCMood.PROUD:
            effects.extend(["golden_particles", "victory_flash"])
        
        if tier.value in ["epic", "legendary"]:
            effects.extend(["full_screen_takeover", "orchestral_fanfare"])
        
        return effects
    
    def _suggest_follow_up(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        event_type: EventType
    ) -> List[Dict[str, str]]:
        """Suggest next actions based on event"""
        suggestions = []
        
        if event_type == EventType.TRADE_WIN:
            suggestions.append({
                "action": "check_shop",
                "message": "New items available in XP Shop!",
                "npc": "DRILL_INSTRUCTOR"
            })
        
        if user_data.get("total_xp", 0) >= 50000 and user_data.get("prestige_level", 0) == 0:
            suggestions.append({
                "action": "prestige",
                "message": "PRESTIGE AVAILABLE! Transform and rise!",
                "npc": "ALL"
            })
        
        return suggestions

# Example usage
if __name__ == "__main__":
    celebration_system = XPCelebrationSystem()
    npc_integration = NPCXPIntegration(celebration_system)
    
    # Simulate a trade win
    user_data = {
        "rank": "SERGEANT",
        "total_xp": 15420,
        "success_rate": 72,
        "current_streak": 3,
        "tier": "FANG"
    }
    
    result = npc_integration.handle_xp_event(
        user_id="test_user",
        event_type=EventType.TRADE_WIN,
        xp_amount=500,
        user_data=user_data,
        event_metadata={"profit": 250.50}
    )
    
    print("Celebration:", result["celebration"].title)
    print("\nNPC Responses:")
    for dialogue in result["npc_responses"]:
        print(f"- {dialogue.personality.value}: {dialogue.message}")
    print(f"\nSpecial Effects: {result['special_effects']}")