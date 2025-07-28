"""
Achievement System for HydraX Platform
Handles achievement definitions, progress tracking, unlocking, and rewards
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class AchievementTier(Enum):
    """Achievement tier levels"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    MASTER = "master"

class AchievementCategory(Enum):
    """Achievement categories"""
    COMBAT = "combat"
    EXPLORATION = "exploration"
    COLLECTION = "collection"
    SOCIAL = "social"
    PROGRESSION = "progression"
    MASTERY = "mastery"
    SPECIAL = "special"

@dataclass
class AchievementDefinition:
    """Defines an achievement"""
    id: str
    name: str
    description: str
    tier: AchievementTier
    category: AchievementCategory
    xp_reward: int
    icon: str
    hidden: bool = False
    requirements: Dict[str, Any] = field(default_factory=dict)
    prerequisite_achievements: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate achievement definition"""
        if self.xp_reward < 0:
            raise ValueError(f"XP reward must be non-negative: {self.xp_reward}")

@dataclass
class AchievementProgress:
    """Tracks progress towards an achievement"""
    achievement_id: str
    user_id: str
    current_progress: Dict[str, Any] = field(default_factory=dict)
    unlocked: bool = False
    unlock_date: Optional[datetime] = None
    progress_percentage: float = 0.0
    
    def update_progress(self, key: str, value: Any) -> None:
        """Update progress for a specific requirement"""
        self.current_progress[key] = value

@dataclass
class Badge:
    """Represents an achievement badge"""
    achievement_id: str
    tier: AchievementTier
    icon_path: str
    color_scheme: Dict[str, str]
    effects: List[str] = field(default_factory=list)
    
    def generate_badge_id(self) -> str:
        """Generate unique badge ID"""
        badge_string = f"{self.achievement_id}_{self.tier.value}"
        return hashlib.md5(badge_string.encode()).hexdigest()[:12]

class AchievementSystem:
    """Main achievement system manager"""
    
    # Tier-based XP multipliers
    TIER_XP_MULTIPLIERS = {
        AchievementTier.BRONZE: 1.0,
        AchievementTier.SILVER: 1.5,
        AchievementTier.GOLD: 2.0,
        AchievementTier.PLATINUM: 3.0,
        AchievementTier.DIAMOND: 5.0,
        AchievementTier.MASTER: 10.0
    }
    
    # Tier color schemes for badges
    TIER_COLORS = {
        AchievementTier.BRONZE: {"primary": "#CD7F32", "secondary": "#8B5A2B", "glow": "#FFB366"},
        AchievementTier.SILVER: {"primary": "#C0C0C0", "secondary": "#808080", "glow": "#E8E8E8"},
        AchievementTier.GOLD: {"primary": "#FFD700", "secondary": "#FFA500", "glow": "#FFED4E"},
        AchievementTier.PLATINUM: {"primary": "#E5E4E2", "secondary": "#BCC6CC", "glow": "#F8F8FF"},
        AchievementTier.DIAMOND: {"primary": "#B9F2FF", "secondary": "#00D4FF", "glow": "#E0FFFF"},
        AchievementTier.MASTER: {"primary": "#9400D3", "secondary": "#4B0082", "glow": "#DA70D6"}
    }
    
    def __init__(self, data_path: Optional[Path] = None):
        """Initialize achievement system"""
        self.data_path = data_path or Path("data/achievements")
        self.achievements: Dict[str, AchievementDefinition] = {}
        self.user_progress: Dict[str, Dict[str, AchievementProgress]] = {}
        self.badges: Dict[str, Badge] = {}
        
        self._initialize_achievements()
        
    def _initialize_achievements(self) -> None:
        """Initialize achievement definitions"""
        # Combat achievements
        self.register_achievement(AchievementDefinition(
            id="first_blood",
            name="First Blood",
            description="Win your first battle",
            tier=AchievementTier.BRONZE,
            category=AchievementCategory.COMBAT,
            xp_reward=100,
            icon="sword_bronze",
            requirements={"battles_won": 1}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="warrior_spirit",
            name="Warrior Spirit",
            description="Win 10 battles",
            tier=AchievementTier.SILVER,
            category=AchievementCategory.COMBAT,
            xp_reward=250,
            icon="sword_silver",
            requirements={"battles_won": 10},
            prerequisite_achievements=["first_blood"]
        ))
        
        self.register_achievement(AchievementDefinition(
            id="battle_master",
            name="Battle Master",
            description="Win 100 battles",
            tier=AchievementTier.GOLD,
            category=AchievementCategory.COMBAT,
            xp_reward=1000,
            icon="sword_gold",
            requirements={"battles_won": 100},
            prerequisite_achievements=["warrior_spirit"]
        ))
        
        # Exploration achievements
        self.register_achievement(AchievementDefinition(
            id="explorer",
            name="Explorer",
            description="Discover 5 hidden locations",
            tier=AchievementTier.BRONZE,
            category=AchievementCategory.EXPLORATION,
            xp_reward=150,
            icon="compass_bronze",
            requirements={"locations_discovered": 5}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="pathfinder",
            name="Pathfinder",
            description="Discover 25 hidden locations",
            tier=AchievementTier.SILVER,
            category=AchievementCategory.EXPLORATION,
            xp_reward=400,
            icon="compass_silver",
            requirements={"locations_discovered": 25}
        ))
        
        # Collection achievements
        self.register_achievement(AchievementDefinition(
            id="collector",
            name="Collector",
            description="Collect 10 unique items",
            tier=AchievementTier.BRONZE,
            category=AchievementCategory.COLLECTION,
            xp_reward=120,
            icon="chest_bronze",
            requirements={"unique_items": 10}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="hoarder",
            name="Hoarder",
            description="Collect 100 unique items",
            tier=AchievementTier.GOLD,
            category=AchievementCategory.COLLECTION,
            xp_reward=800,
            icon="chest_gold",
            requirements={"unique_items": 100}
        ))
        
        # Social achievements
        self.register_achievement(AchievementDefinition(
            id="social_butterfly",
            name="Social Butterfly",
            description="Make 5 friends",
            tier=AchievementTier.BRONZE,
            category=AchievementCategory.SOCIAL,
            xp_reward=100,
            icon="friendship_bronze",
            requirements={"friends_count": 5}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="community_leader",
            name="Community Leader",
            description="Have 50 friends and lead a guild",
            tier=AchievementTier.PLATINUM,
            category=AchievementCategory.SOCIAL,
            xp_reward=2000,
            icon="crown_platinum",
            requirements={"friends_count": 50, "guild_leader": True}
        ))
        
        # Progression achievements
        self.register_achievement(AchievementDefinition(
            id="level_10",
            name="Rising Star",
            description="Reach level 10",
            tier=AchievementTier.BRONZE,
            category=AchievementCategory.PROGRESSION,
            xp_reward=200,
            icon="star_bronze",
            requirements={"level": 10}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="level_50",
            name="Veteran",
            description="Reach level 50",
            tier=AchievementTier.GOLD,
            category=AchievementCategory.PROGRESSION,
            xp_reward=1500,
            icon="star_gold",
            requirements={"level": 50}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="level_100",
            name="Legend",
            description="Reach level 100",
            tier=AchievementTier.DIAMOND,
            category=AchievementCategory.PROGRESSION,
            xp_reward=5000,
            icon="star_diamond",
            requirements={"level": 100}
        ))
        
        # Tactical Strategy achievements
        self.register_achievement(AchievementDefinition(
            id="tactical_first_blood",
            name="Tactical First Blood",
            description="Unlock your first tactical strategy at 120 XP",
            tier=AchievementTier.BRONZE,
            category=AchievementCategory.PROGRESSION,
            xp_reward=150,
            icon="tactical_bronze",
            requirements={"total_xp": 120}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="tactical_double_tap",
            name="Tactical Double Tap",
            description="Unlock your second tactical strategy at 240 XP",
            tier=AchievementTier.SILVER,
            category=AchievementCategory.PROGRESSION,
            xp_reward=300,
            icon="tactical_silver",
            requirements={"total_xp": 240, "strategies_unlocked": 2}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="tactical_command",
            name="Tactical Command",
            description="Unlock advanced tactical strategies at 360 XP",
            tier=AchievementTier.GOLD,
            category=AchievementCategory.PROGRESSION,
            xp_reward=500,
            icon="tactical_gold",
            requirements={"total_xp": 360, "strategies_unlocked": 3}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="master_tactician",
            name="Master Tactician",
            description="Master all tactical strategies and become the ultimate field commander",
            tier=AchievementTier.PLATINUM,
            category=AchievementCategory.PROGRESSION,
            xp_reward=1000,
            icon="tactical_platinum",
            requirements={"all_strategies_mastered": True}
        ))
        
        # Mastery achievements
        self.register_achievement(AchievementDefinition(
            id="skill_master",
            name="Skill Master",
            description="Max out any skill tree",
            tier=AchievementTier.PLATINUM,
            category=AchievementCategory.MASTERY,
            xp_reward=3000,
            icon="skill_platinum",
            requirements={"maxed_skill_trees": 1}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="ultimate_master",
            name="Ultimate Master",
            description="Max out all skill trees",
            tier=AchievementTier.MASTER,
            category=AchievementCategory.MASTERY,
            xp_reward=10000,
            icon="skill_master",
            requirements={"maxed_skill_trees": 5}
        ))
        
        # Special achievements
        self.register_achievement(AchievementDefinition(
            id="beta_tester",
            name="Beta Tester",
            description="Participated in beta testing",
            tier=AchievementTier.PLATINUM,
            category=AchievementCategory.SPECIAL,
            xp_reward=2500,
            icon="beta_badge",
            hidden=True,
            requirements={"beta_participant": True}
        ))
        
        self.register_achievement(AchievementDefinition(
            id="perfectionist",
            name="Perfectionist",
            description="Complete all achievements",
            tier=AchievementTier.MASTER,
            category=AchievementCategory.SPECIAL,
            xp_reward=20000,
            icon="perfect_badge",
            hidden=True,
            requirements={"all_achievements": True}
        ))
        
    def register_achievement(self, achievement: AchievementDefinition) -> None:
        """Register a new achievement"""
        if achievement.id in self.achievements:
            logger.warning(f"Achievement {achievement.id} already registered")
            return
            
        self.achievements[achievement.id] = achievement
        
        # Generate badge
        badge = Badge(
            achievement_id=achievement.id,
            tier=achievement.tier,
            icon_path=f"badges/{achievement.icon}.png",
            color_scheme=self.TIER_COLORS[achievement.tier],
            effects=self._generate_badge_effects(achievement.tier)
        )
        self.badges[achievement.id] = badge
        
        logger.info(f"Registered achievement: {achievement.name} ({achievement.tier.value})")
        
    def _generate_badge_effects(self, tier: AchievementTier) -> List[str]:
        """Generate visual effects for badge based on tier"""
        effects = []
        
        if tier == AchievementTier.BRONZE:
            effects.append("subtle_glow")
        elif tier == AchievementTier.SILVER:
            effects.extend(["glow", "shine"])
        elif tier == AchievementTier.GOLD:
            effects.extend(["glow", "shine", "sparkle"])
        elif tier == AchievementTier.PLATINUM:
            effects.extend(["glow", "shine", "sparkle", "pulse"])
        elif tier == AchievementTier.DIAMOND:
            effects.extend(["glow", "shine", "sparkle", "pulse", "prismatic"])
        elif tier == AchievementTier.MASTER:
            effects.extend(["glow", "shine", "sparkle", "pulse", "prismatic", "legendary_aura"])
            
        return effects
        
    def initialize_user_progress(self, user_id: str) -> None:
        """Initialize achievement progress for a new user"""
        if user_id in self.user_progress:
            return
            
        self.user_progress[user_id] = {}
        
        for achievement_id, achievement in self.achievements.items():
            self.user_progress[user_id][achievement_id] = AchievementProgress(
                achievement_id=achievement_id,
                user_id=user_id
            )
            
        logger.info(f"Initialized achievement progress for user: {user_id}")
        
    def update_progress(self, user_id: str, progress_data: Dict[str, Any]) -> List[str]:
        """Update user's achievement progress and check for unlocks"""
        if user_id not in self.user_progress:
            self.initialize_user_progress(user_id)
            
        unlocked_achievements = []
        
        for achievement_id, achievement in self.achievements.items():
            progress = self.user_progress[user_id][achievement_id]
            
            if progress.unlocked:
                continue
                
            # Check prerequisites
            if not self._check_prerequisites(user_id, achievement):
                continue
                
            # Update progress
            progress_updated = False
            for req_key, req_value in achievement.requirements.items():
                if req_key in progress_data:
                    progress.update_progress(req_key, progress_data[req_key])
                    progress_updated = True
                    
            if progress_updated:
                # Calculate progress percentage
                progress.progress_percentage = self._calculate_progress_percentage(
                    progress, achievement
                )
                
                # Check if achievement is unlocked
                if self._check_unlock_conditions(progress, achievement):
                    unlocked_achievements.append(self._unlock_achievement(user_id, achievement_id))
                    
        return unlocked_achievements
        
    def _check_prerequisites(self, user_id: str, achievement: AchievementDefinition) -> bool:
        """Check if prerequisite achievements are unlocked"""
        for prereq_id in achievement.prerequisite_achievements:
            if prereq_id not in self.user_progress[user_id]:
                return False
            if not self.user_progress[user_id][prereq_id].unlocked:
                return False
        return True
        
    def _calculate_progress_percentage(self, progress: AchievementProgress, 
                                     achievement: AchievementDefinition) -> float:
        """Calculate completion percentage for an achievement"""
        if not achievement.requirements:
            return 100.0
            
        total_requirements = len(achievement.requirements)
        completed_requirements = 0
        
        for req_key, req_value in achievement.requirements.items():
            current_value = progress.current_progress.get(req_key, 0)
            
            if isinstance(req_value, bool):
                if current_value == req_value:
                    completed_requirements += 1
            elif isinstance(req_value, (int, float)):
                if current_value >= req_value:
                    completed_requirements += 1
                else:
                    # Partial progress for numeric requirements
                    completed_requirements += min(current_value / req_value, 1.0)
            elif req_key == "all_achievements":
                # Special case for perfectionist achievement
                total_achievements = len(self.achievements) - 1  # Exclude this achievement
                unlocked_count = sum(1 for p in self.user_progress[progress.user_id].values() 
                                   if p.unlocked and p.achievement_id != achievement.id)
                completed_requirements += unlocked_count / total_achievements
                
        return (completed_requirements / total_requirements) * 100
        
    def _check_unlock_conditions(self, progress: AchievementProgress, 
                               achievement: AchievementDefinition) -> bool:
        """Check if achievement unlock conditions are met"""
        for req_key, req_value in achievement.requirements.items():
            current_value = progress.current_progress.get(req_key, 0)
            
            if isinstance(req_value, bool):
                if current_value != req_value:
                    return False
            elif isinstance(req_value, (int, float)):
                if current_value < req_value:
                    return False
            elif req_key == "all_achievements":
                # Special case for perfectionist achievement
                total_achievements = len(self.achievements) - 1
                unlocked_count = sum(1 for p in self.user_progress[progress.user_id].values() 
                                   if p.unlocked and p.achievement_id != achievement.id)
                if unlocked_count < total_achievements:
                    return False
                    
        return True
        
    def _unlock_achievement(self, user_id: str, achievement_id: str) -> str:
        """Unlock an achievement for a user"""
        progress = self.user_progress[user_id][achievement_id]
        achievement = self.achievements[achievement_id]
        
        progress.unlocked = True
        progress.unlock_date = datetime.now()
        progress.progress_percentage = 100.0
        
        logger.info(f"Achievement unlocked: {achievement.name} for user {user_id}")
        
        return achievement_id
        
    def get_user_achievements(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all achievements and progress for a user"""
        if user_id not in self.user_progress:
            self.initialize_user_progress(user_id)
            
        result = {}
        
        for achievement_id, progress in self.user_progress[user_id].items():
            achievement = self.achievements[achievement_id]
            badge = self.badges[achievement_id]
            
            # Don't include hidden achievements unless unlocked
            if achievement.hidden and not progress.unlocked:
                continue
                
            result[achievement_id] = {
                "achievement": {
                    "id": achievement.id,
                    "name": achievement.name,
                    "description": achievement.description,
                    "tier": achievement.tier.value,
                    "category": achievement.category.value,
                    "xp_reward": achievement.xp_reward,
                    "hidden": achievement.hidden
                },
                "progress": {
                    "unlocked": progress.unlocked,
                    "unlock_date": progress.unlock_date.isoformat() if progress.unlock_date else None,
                    "progress_percentage": progress.progress_percentage,
                    "current_progress": progress.current_progress
                },
                "badge": {
                    "id": badge.generate_badge_id(),
                    "icon_path": badge.icon_path,
                    "color_scheme": badge.color_scheme,
                    "effects": badge.effects
                }
            }
            
        return result
        
    def get_unlocked_achievements(self, user_id: str) -> List[str]:
        """Get list of unlocked achievement IDs for a user"""
        if user_id not in self.user_progress:
            return []
            
        return [
            achievement_id 
            for achievement_id, progress in self.user_progress[user_id].items()
            if progress.unlocked
        ]
        
    def calculate_total_xp_rewards(self, user_id: str) -> int:
        """Calculate total XP earned from achievements"""
        total_xp = 0
        
        for achievement_id in self.get_unlocked_achievements(user_id):
            achievement = self.achievements[achievement_id]
            tier_multiplier = self.TIER_XP_MULTIPLIERS[achievement.tier]
            total_xp += int(achievement.xp_reward * tier_multiplier)
            
        return total_xp
        
    def get_achievement_stats(self, user_id: str) -> Dict[str, Any]:
        """Get achievement statistics for a user"""
        if user_id not in self.user_progress:
            self.initialize_user_progress(user_id)
            
        unlocked = self.get_unlocked_achievements(user_id)
        total_achievements = len([a for a in self.achievements.values() if not a.hidden])
        
        # Count by tier
        tier_counts = {tier: 0 for tier in AchievementTier}
        for achievement_id in unlocked:
            achievement = self.achievements[achievement_id]
            if not achievement.hidden:
                tier_counts[achievement.tier] += 1
                
        # Count by category
        category_counts = {category: 0 for category in AchievementCategory}
        for achievement_id in unlocked:
            achievement = self.achievements[achievement_id]
            category_counts[achievement.category] += 1
            
        return {
            "total_unlocked": len(unlocked),
            "total_available": total_achievements,
            "completion_percentage": (len(unlocked) / total_achievements * 100) if total_achievements > 0 else 0,
            "total_xp_earned": self.calculate_total_xp_rewards(user_id),
            "tier_breakdown": {tier.value: count for tier, count in tier_counts.items()},
            "category_breakdown": {cat.value: count for cat, count in category_counts.items()},
            "recent_unlocks": self._get_recent_unlocks(user_id, limit=5)
        }
        
    def _get_recent_unlocks(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently unlocked achievements"""
        unlocked_with_dates = []
        
        for achievement_id, progress in self.user_progress[user_id].items():
            if progress.unlocked and progress.unlock_date:
                achievement = self.achievements[achievement_id]
                unlocked_with_dates.append({
                    "id": achievement_id,
                    "name": achievement.name,
                    "tier": achievement.tier.value,
                    "unlock_date": progress.unlock_date
                })
                
        # Sort by unlock date (most recent first)
        unlocked_with_dates.sort(key=lambda x: x["unlock_date"], reverse=True)
        
        # Return limited list with formatted dates
        return [
            {
                "id": item["id"],
                "name": item["name"],
                "tier": item["tier"],
                "unlock_date": item["unlock_date"].isoformat()
            }
            for item in unlocked_with_dates[:limit]
        ]
        
    def integrate_with_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate achievement data with user profile"""
        achievement_stats = self.get_achievement_stats(user_id)
        unlocked_badges = []
        
        for achievement_id in self.get_unlocked_achievements(user_id):
            badge = self.badges[achievement_id]
            achievement = self.achievements[achievement_id]
            
            unlocked_badges.append({
                "id": badge.generate_badge_id(),
                "achievement_id": achievement_id,
                "name": achievement.name,
                "tier": achievement.tier.value,
                "icon_path": badge.icon_path,
                "effects": badge.effects
            })
            
        # Sort badges by tier (highest first)
        tier_order = [AchievementTier.MASTER, AchievementTier.DIAMOND, 
                     AchievementTier.PLATINUM, AchievementTier.GOLD,
                     AchievementTier.SILVER, AchievementTier.BRONZE]
        
        unlocked_badges.sort(
            key=lambda x: tier_order.index(AchievementTier(x["tier"]))
        )
        
        # Update profile with achievement data
        profile_data["achievements"] = {
            "stats": achievement_stats,
            "badges": unlocked_badges[:10],  # Top 10 badges for display
            "showcase": self._get_showcase_achievements(user_id),
            "achievement_score": self._calculate_achievement_score(user_id)
        }
        
        # Add achievement-based XP to profile
        if "experience" in profile_data:
            profile_data["experience"]["achievement_xp"] = achievement_stats["total_xp_earned"]
            
        return profile_data
        
    def _get_showcase_achievements(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get showcase achievements (highest tier unlocked)"""
        unlocked = []
        
        for achievement_id in self.get_unlocked_achievements(user_id):
            achievement = self.achievements[achievement_id]
            badge = self.badges[achievement_id]
            
            unlocked.append({
                "id": achievement_id,
                "name": achievement.name,
                "description": achievement.description,
                "tier": achievement.tier,
                "badge": {
                    "icon_path": badge.icon_path,
                    "color_scheme": badge.color_scheme,
                    "effects": badge.effects
                }
            })
            
        # Sort by tier (highest first)
        tier_order = [AchievementTier.MASTER, AchievementTier.DIAMOND, 
                     AchievementTier.PLATINUM, AchievementTier.GOLD,
                     AchievementTier.SILVER, AchievementTier.BRONZE]
        
        unlocked.sort(key=lambda x: tier_order.index(x["tier"]))
        
        # Convert tier enum to string for serialization
        showcase = []
        for item in unlocked[:limit]:
            item_copy = item.copy()
            item_copy["tier"] = item_copy["tier"].value
            showcase.append(item_copy)
            
        return showcase
        
    def _calculate_achievement_score(self, user_id: str) -> int:
        """Calculate overall achievement score based on tiers"""
        tier_scores = {
            AchievementTier.BRONZE: 10,
            AchievementTier.SILVER: 25,
            AchievementTier.GOLD: 50,
            AchievementTier.PLATINUM: 100,
            AchievementTier.DIAMOND: 250,
            AchievementTier.MASTER: 1000
        }
        
        total_score = 0
        
        for achievement_id in self.get_unlocked_achievements(user_id):
            achievement = self.achievements[achievement_id]
            total_score += tier_scores[achievement.tier]
            
        return total_score
        
    def save_progress(self, user_id: str, file_path: Optional[Path] = None) -> None:
        """Save user's achievement progress to file"""
        if user_id not in self.user_progress:
            return
            
        save_path = file_path or self.data_path / f"progress_{user_id}.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        progress_data = {}
        for achievement_id, progress in self.user_progress[user_id].items():
            progress_data[achievement_id] = {
                "current_progress": progress.current_progress,
                "unlocked": progress.unlocked,
                "unlock_date": progress.unlock_date.isoformat() if progress.unlock_date else None,
                "progress_percentage": progress.progress_percentage
            }
            
        with open(save_path, 'w') as f:
            json.dump(progress_data, f, indent=2)
            
        logger.info(f"Saved achievement progress for user {user_id}")
        
    def load_progress(self, user_id: str, file_path: Optional[Path] = None) -> None:
        """Load user's achievement progress from file"""
        load_path = file_path or self.data_path / f"progress_{user_id}.json"
        
        if not load_path.exists():
            logger.warning(f"No saved progress found for user {user_id}")
            return
            
        try:
            with open(load_path, 'r') as f:
                progress_data = json.load(f)
                
            if user_id not in self.user_progress:
                self.user_progress[user_id] = {}
                
            for achievement_id, data in progress_data.items():
                if achievement_id in self.achievements:
                    progress = AchievementProgress(
                        achievement_id=achievement_id,
                        user_id=user_id,
                        current_progress=data["current_progress"],
                        unlocked=data["unlocked"],
                        unlock_date=datetime.fromisoformat(data["unlock_date"]) if data["unlock_date"] else None,
                        progress_percentage=data["progress_percentage"]
                    )
                    self.user_progress[user_id][achievement_id] = progress
                    
            logger.info(f"Loaded achievement progress for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to load achievement progress: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize achievement system
    achievement_system = AchievementSystem()
    
    # Create a test user
    test_user_id = "user_123"
    achievement_system.initialize_user_progress(test_user_id)
    
    # Simulate progress updates
    print("Updating user progress...")
    
    # Win some battles
    unlocked = achievement_system.update_progress(test_user_id, {
        "battles_won": 1
    })
    print(f"Unlocked: {unlocked}")
    
    # Level up
    unlocked = achievement_system.update_progress(test_user_id, {
        "level": 10
    })
    print(f"Unlocked: {unlocked}")
    
    # Collect items
    unlocked = achievement_system.update_progress(test_user_id, {
        "unique_items": 15
    })
    print(f"Unlocked: {unlocked}")
    
    # Get achievement stats
    stats = achievement_system.get_achievement_stats(test_user_id)
    print(f"\nAchievement Stats:")
    print(f"Total Unlocked: {stats['total_unlocked']}/{stats['total_available']}")
    print(f"Completion: {stats['completion_percentage']:.1f}%")
    print(f"Total XP Earned: {stats['total_xp_earned']}")
    
    # Get user achievements
    achievements = achievement_system.get_user_achievements(test_user_id)
    print(f"\nUnlocked Achievements:")
    for achievement_id, data in achievements.items():
        if data["progress"]["unlocked"]:
            print(f"- {data['achievement']['name']} ({data['achievement']['tier']})")
    
    # Integrate with profile
    profile = {
        "user_id": test_user_id,
        "username": "TestPlayer",
        "level": 10,
        "experience": {
            "current_xp": 1000,
            "total_xp": 2500
        }
    }
    
    updated_profile = achievement_system.integrate_with_profile(test_user_id, profile)
    print(f"\nProfile Achievement Score: {updated_profile['achievements']['achievement_score']}")
    print(f"Profile Achievement XP: {updated_profile['experience']['achievement_xp']}")