"""
🎯 BITTEN Sunday Training Operations

Double XP Sundays - Study the enemy when they're weakest
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TrainingType(Enum):
    """Sunday training operation types"""
    RECON = "recon"              # Watch only, no trades
    PAPER_DRILL = "paper_drill"   # Demo trades for practice
    LIVE_FIRE = "live_fire"       # Real trades, 2x XP
    STUDY_SESSION = "study"       # Educational content

@dataclass
class SundayMission:
    """Special Sunday training missions"""
    mission_id: str
    name: str
    description: str
    training_type: TrainingType
    xp_multiplier: float
    requirements: Dict
    duration_hours: int
    tier_requirement: str

class SundayTrainingOps:
    """
    Manages Sunday double XP training operations
    Turns weekend danger into learning opportunity
    """
    
    def __init__(self):
        self.active_missions = {}
        self.missions = self._initialize_missions()
    
    def _initialize_missions(self) -> Dict[str, SundayMission]:
        """Initialize all Sunday training missions"""
        return {
            "gap_hunter": SundayMission(
                mission_id="gap_hunter",
                name="Gap Hunter Training",
                description="Study and trade Sunday market gaps",
                training_type=TrainingType.LIVE_FIRE,
                xp_multiplier=2.0,
                requirements={"min_tcs": 85, "positions": 0},
                duration_hours=4,
                tier_requirement="FANG"
            ),
            "liquidity_recon": SundayMission(
                mission_id="liquidity_recon",
                name="Liquidity Reconnaissance",
                description="Map the thin liquidity patterns without trading",
                training_type=TrainingType.RECON,
                xp_multiplier=1.5,
                requirements={"screenshots": 5, "notes": True},
                duration_hours=2,
                tier_requirement="NIBBLER"
            ),
            "spread_analysis": SundayMission(
                mission_id="spread_analysis",
                name="Spread Analysis Drill",
                description="Document how spreads widen on weekends",
                training_type=TrainingType.STUDY_SESSION,
                xp_multiplier=1.5,
                requirements={"pairs_analyzed": 10},
                duration_hours=1,
                tier_requirement="NIBBLER"
            ),
            "chaos_navigation": SundayMission(
                mission_id="chaos_navigation",
                name="Chaos Navigation Exercise",
                description="Trade the Sunday open with reduced risk",
                training_type=TrainingType.LIVE_FIRE,
                xp_multiplier=2.5,
                requirements={"min_tcs": 88, "risk_reduction": 0.5},
                duration_hours=6,
                tier_requirement="COMMANDER"
            ),
            "paper_assault": SundayMission(
                mission_id="paper_assault",
                name="Paper Trading Assault",
                description="Practice trades on demo with real market conditions",
                training_type=TrainingType.PAPER_DRILL,
                xp_multiplier=1.0,
                requirements={"demo_trades": 5},
                duration_hours=3,
                tier_requirement="NIBBLER"
            )
        }
    
    def get_sunday_briefing(self, user_tier: str, has_positions: bool) -> str:
        """Generate Sunday training opportunities briefing"""
        
        base_message = (
            "🎯 **SUNDAY TRAINING OPERATIONS**\n"
            "════════════════════════\n"
            "**DOUBLE XP ACTIVE** 🎖️🎖️\n\n"
            "Turn weekend danger into knowledge.\n"
            "Study the enemy when they're weakest.\n\n"
        )
        
        # Check if user has positions
        if has_positions:
            base_message += (
                "⚠️ **WARNING**: You have open positions.\n"
                "Close them before joining training ops.\n\n"
            )
        
        # Get available missions for tier
        available_missions = self._get_tier_missions(user_tier)
        
        if not available_missions:
            return base_message + "_No missions available for your tier._"
        
        base_message += "**AVAILABLE MISSIONS:**\n\n"
        
        for mission in available_missions:
            emoji = self._get_mission_emoji(mission.training_type)
            base_message += (
                f"{emoji} **{mission.name}**\n"
                f"├ Type: {mission.training_type.value.upper()}\n"
                f"├ XP: {mission.xp_multiplier}x multiplier\n"
                f"├ Duration: {mission.duration_hours}h\n"
                f"└ Cmd: `/sunday_{mission.mission_id}`\n\n"
            )
        
        base_message += (
            "────────────────────\n"
            "💡 **INTEL**: Weekend spreads are 2-3x normal.\n"
            "Use this for education, not greed.\n\n"
            "_Knowledge is power. Power is profit._"
        )
        
        return base_message
    
    def _get_tier_missions(self, tier: str) -> List[SundayMission]:
        """Get missions available for user's tier"""
        tier_hierarchy = {
            "NIBBLER": 0,
            "FANG": 1,
            "COMMANDER": 2,
            "APEX": 3
        }
        
        user_level = tier_hierarchy.get(tier, 0)
        available = []
        
        for mission in self.missions.values():
            required_level = tier_hierarchy.get(mission.tier_requirement, 0)
            if user_level >= required_level:
                available.append(mission)
        
        return sorted(available, key=lambda m: m.xp_multiplier, reverse=True)
    
    def _get_mission_emoji(self, training_type: TrainingType) -> str:
        """Get emoji for mission type"""
        return {
            TrainingType.RECON: "👁️",
            TrainingType.PAPER_DRILL: "📝",
            TrainingType.LIVE_FIRE: "🔥",
            TrainingType.STUDY_SESSION: "📚"
        }.get(training_type, "🎯")
    
    def start_mission(self, user_id: int, mission_id: str) -> Tuple[bool, str]:
        """Start a Sunday training mission"""
        
        # Check if Sunday
        if datetime.now(timezone.utc).weekday() != 6:  # Sunday = 6
            return False, "Training operations only available on Sundays."
        
        # Check if mission exists
        if mission_id not in self.missions:
            return False, "Invalid mission ID."
        
        # Check if user already on mission
        if user_id in self.active_missions:
            return False, "Already on a mission. Complete it first."
        
        mission = self.missions[mission_id]
        
        # Start mission
        self.active_missions[user_id] = {
            'mission': mission,
            'start_time': datetime.now(timezone.utc),
            'progress': {},
            'xp_earned': 0
        }
        
        return True, self._get_mission_start_message(mission)
    
    def _get_mission_start_message(self, mission: SundayMission) -> str:
        """Generate mission start message"""
        
        messages = {
            TrainingType.RECON: (
                "👁️ **RECON MISSION STARTED**\n\n"
                "Observe without engaging.\n"
                "Document everything.\n"
                "Knowledge before action.\n\n"
                "_The ghost sees all._"
            ),
            TrainingType.PAPER_DRILL: (
                "📝 **PAPER DRILL COMMENCED**\n\n"
                "Demo account active.\n"
                "Real market conditions.\n"
                "No real risk, real lessons.\n\n"
                "_Train hard, fight easy._"
            ),
            TrainingType.LIVE_FIRE: (
                "🔥 **LIVE FIRE EXERCISE**\n\n"
                "⚠️ REAL MONEY AT RISK\n"
                "Double XP for the brave.\n"
                "Stay sharp, stay alive.\n\n"
                "_This is not a drill._"
            ),
            TrainingType.STUDY_SESSION: (
                "📚 **STUDY SESSION INITIATED**\n\n"
                "Analyze the patterns.\n"
                "Document the chaos.\n"
                "Understanding is power.\n\n"
                "_Know your enemy._"
            )
        }
        
        base = messages.get(mission.training_type, "Mission started.")
        
        requirements = "\n**OBJECTIVES:**\n"
        for key, value in mission.requirements.items():
            requirements += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        return (
            f"{base}\n"
            f"{requirements}\n"
            f"**Duration**: {mission.duration_hours} hours\n"
            f"**XP Multiplier**: {mission.xp_multiplier}x\n\n"
            f"_Report back with `/mission_status`_"
        )
    
    def check_mission_progress(self, user_id: int) -> Optional[Dict]:
        """Check user's mission progress"""
        if user_id not in self.active_missions:
            return None
        
        mission_data = self.active_missions[user_id]
        mission = mission_data['mission']
        elapsed = datetime.now(timezone.utc) - mission_data['start_time']
        
        # Check if mission expired
        if elapsed.total_seconds() > mission.duration_hours * 3600:
            # Mission failed - timeout
            self._complete_mission(user_id, success=False, reason="timeout")
            return None
        
        time_remaining = timedelta(hours=mission.duration_hours) - elapsed
        
        return {
            'mission': mission,
            'progress': mission_data['progress'],
            'time_remaining': time_remaining,
            'xp_earned': mission_data['xp_earned']
        }
    
    def update_mission_progress(self, user_id: int, progress_type: str, value: any) -> Tuple[bool, str]:
        """Update mission progress"""
        if user_id not in self.active_missions:
            return False, "No active mission."
        
        mission_data = self.active_missions[user_id]
        mission_data['progress'][progress_type] = value
        
        # Check if mission complete
        if self._is_mission_complete(user_id):
            return self._complete_mission(user_id, success=True)
        
        return True, f"Progress updated: {progress_type} = {value}"
    
    def _is_mission_complete(self, user_id: int) -> bool:
        """Check if mission objectives are complete"""
        mission_data = self.active_missions[user_id]
        mission = mission_data['mission']
        progress = mission_data['progress']
        
        for req_key, req_value in mission.requirements.items():
            if req_key not in progress:
                return False
            if isinstance(req_value, (int, float)):
                if progress[req_key] < req_value:
                    return False
            elif isinstance(req_value, bool):
                if not progress[req_key]:
                    return False
        
        return True
    
    def _complete_mission(self, user_id: int, success: bool, reason: str = "") -> Tuple[bool, str]:
        """Complete a mission"""
        if user_id not in self.active_missions:
            return False, "No active mission."
        
        mission_data = self.active_missions[user_id]
        mission = mission_data['mission']
        
        if success:
            # Calculate XP (would integrate with XP system)
            base_xp = 100  # Base mission XP
            total_xp = int(base_xp * mission.xp_multiplier)
            
            message = (
                f"✅ **MISSION COMPLETE: {mission.name}**\n\n"
                f"**XP Earned**: {total_xp} ({mission.xp_multiplier}x multiplier)\n"
                f"**Duration**: {mission.duration_hours}h\n\n"
                f"_Outstanding work, operator._"
            )
        else:
            message = (
                f"❌ **MISSION FAILED: {mission.name}**\n\n"
                f"**Reason**: {reason}\n"
                f"**XP Earned**: 0\n\n"
                f"_Failure is the best teacher. Try again._"
            )
        
        # Clean up
        del self.active_missions[user_id]
        
        return True, message
    
    def get_sunday_leaderboard(self) -> str:
        """Get Sunday training leaderboard"""
        # This would pull from database in production
        return (
            "🏆 **SUNDAY TRAINING LEADERBOARD**\n"
            "════════════════════════\n"
            "1. Apex_Hunter - 2,500 XP\n"
            "2. Weekend_Warrior - 2,100 XP\n"
            "3. Gap_Master - 1,800 XP\n"
            "4. Chaos_Navigator - 1,500 XP\n"
            "5. Sunday_Scholar - 1,200 XP\n\n"
            "_Train harder. Climb higher._"
        )


# Integration with weekend briefing
def enhance_weekend_briefing_with_sunday_ops(briefing_message: str, user_tier: str) -> str:
    """Add Sunday training teaser to Friday briefing"""
    
    sunday_teaser = (
        "\n\n"
        "🎯 **SUNDAY TRAINING PREVIEW**\n"
        "────────────────────\n"
        "Can't stay away from markets?\n"
        "Make it worth your while.\n\n"
        "**Sunday = 2X XP** on all training missions.\n"
        "Study the enemy when they're weak.\n\n"
        "_Use /sunday_ops for mission list._"
    )
    
    # Only add for FANG and above
    if user_tier in ["FANG", "COMMANDER", "APEX"]:
        return briefing_message + sunday_teaser
    
    return briefing_message