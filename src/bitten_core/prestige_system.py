"""
Prestige System for BITTEN
Handles prestige resets, rewards, and progression
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PrestigeRank(Enum):
    """Prestige rank levels"""
    NONE = (0, "Recruit", "⚪")
    BRONZE = (1, "Bronze Star", "🥉")
    SILVER = (2, "Silver Star", "🥈")
    GOLD = (3, "Gold Star", "🥇")
    PLATINUM = (4, "Platinum Star", "💎")
    DIAMOND = (5, "Diamond Star", "💠")
    MASTER = (6, "Master Sergeant", "🌟")
    
    def __init__(self, level: int, title: str, icon: str):
        self.level = level
        self.title = title
        self.icon = icon
    
    @classmethod
    def from_level(cls, level: int) -> 'PrestigeRank':
        """Get rank from prestige level"""
        for rank in cls:
            if rank.level == level:
                return rank
        # Return highest rank if level exceeds defined ranks
        return cls.MASTER if level > 6 else cls.NONE

@dataclass
class PrestigeReward:
    """Reward for achieving prestige"""
    rank: PrestigeRank
    xp_multiplier_bonus: float  # Permanent XP multiplier
    signal_access: List[str]    # Special signal categories
    badge_icon: str             # Visual badge
    chat_color: str             # Special chat color
    perks: List[str]            # Additional perks

@dataclass
class PrestigeProgress:
    """User's prestige progression data"""
    user_id: str
    current_level: int = 0
    total_prestiges: int = 0
    xp_at_prestige: List[int] = field(default_factory=list)
    prestige_dates: List[datetime] = field(default_factory=list)
    lifetime_xp: int = 0
    unlocked_rewards: List[str] = field(default_factory=list)
    active_multiplier: float = 1.0

class PrestigeSystem:
    """Manages the prestige system"""
    
    # XP required for prestige
    PRESTIGE_THRESHOLD = 50000
    
    # Base XP multiplier per prestige level
    BASE_MULTIPLIER_PER_LEVEL = 0.1  # 10% per level
    
    # Prestige rewards configuration
    PRESTIGE_REWARDS = {
        PrestigeRank.BRONZE: PrestigeReward(
            rank=PrestigeRank.BRONZE,
            xp_multiplier_bonus=0.1,
            signal_access=[],
            badge_icon="🥉",
            chat_color="#CD7F32",
            perks=["bronze_badge", "prestige_chat_access"]
        ),
        PrestigeRank.SILVER: PrestigeReward(
            rank=PrestigeRank.SILVER,
            xp_multiplier_bonus=0.2,
            signal_access=["prestige_signals"],
            badge_icon="🥈",
            chat_color="#C0C0C0",
            perks=["silver_badge", "priority_signals", "mentor_status"]
        ),
        PrestigeRank.GOLD: PrestigeReward(
            rank=PrestigeRank.GOLD,
            xp_multiplier_bonus=0.3,
            signal_access=["prestige_signals", "elite_signals"],
            badge_icon="🥇",
            chat_color="#FFD700",
            perks=["gold_badge", "vip_support", "custom_alerts"]
        ),
        PrestigeRank.PLATINUM: PrestigeReward(
            rank=PrestigeRank.PLATINUM,
            xp_multiplier_bonus=0.4,
            signal_access=["prestige_signals", "elite_signals", "classified_signals"],
            badge_icon="💎",
            chat_color="#E5E4E2",
            perks=["platinum_badge", "alpha_tester", "strategy_input"]
        ),
        PrestigeRank.DIAMOND: PrestigeReward(
            rank=PrestigeRank.DIAMOND,
            xp_multiplier_bonus=0.5,
            signal_access=["all_signals"],
            badge_icon="💠",
            chat_color="#B9F2FF",
            perks=["diamond_badge", "dev_chat_access", "feature_voting"]
        ),
        PrestigeRank.MASTER: PrestigeReward(
            rank=PrestigeRank.MASTER,
            xp_multiplier_bonus=0.75,
            signal_access=["all_signals", "dev_signals"],
            badge_icon="🌟",
            chat_color="#FFD700",
            perks=["master_badge", "legendary_status", "bitten_council"]
        )
    }
    
    def __init__(self, data_dir: str = "data/prestige"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # User prestige data cache
        self.user_progress: Dict[str, PrestigeProgress] = {}
        
        # Prestige leaderboard
        self.leaderboard: List[Tuple[str, int, int]] = []  # (user_id, level, lifetime_xp)
        
        # Load existing data
        self._load_prestige_data()
        self._update_leaderboard()
    
    def can_prestige(self, user_id: str, current_xp: int) -> Tuple[bool, str]:
        """Check if user can prestige"""
        if current_xp < self.PRESTIGE_THRESHOLD:
            xp_needed = self.PRESTIGE_THRESHOLD - current_xp
            return False, f"Need {xp_needed:} more XP to prestige (requires {self.PRESTIGE_THRESHOLD:})"
        
        return True, "Ready to prestige!"
    
    def execute_prestige(
        self, 
        user_id: str, 
        current_xp: int
    ) -> Tuple[bool, PrestigeProgress, Optional[PrestigeReward]]:
        """Execute prestige for a user"""
        can_do, message = self.can_prestige(user_id, current_xp)
        if not can_do:
            return False, None, None
        
        # Get or create progress
        if user_id not in self.user_progress:
            self.user_progress[user_id] = PrestigeProgress(user_id=user_id)
        
        progress = self.user_progress[user_id]
        
        # Record prestige
        progress.current_level += 1
        progress.total_prestiges += 1
        progress.xp_at_prestige.append(current_xp)
        progress.prestige_dates.append(datetime.now())
        progress.lifetime_xp += current_xp
        
        # Calculate new multiplier
        progress.active_multiplier = 1.0 + (progress.current_level * self.BASE_MULTIPLIER_PER_LEVEL)
        
        # Get rank and rewards
        rank = PrestigeRank.from_level(progress.current_level)
        reward = self.PRESTIGE_REWARDS.get(rank)
        
        if reward:
            # Add unlocked rewards
            for perk in reward.perks:
                if perk not in progress.unlocked_rewards:
                    progress.unlocked_rewards.append(perk)
        
        # Save progress
        self._save_user_progress(user_id)
        self._update_leaderboard()
        
        logger.info(f"User {user_id} prestiged to level {progress.current_level} ({rank.title})")
        
        return True, progress, reward
    
    def get_user_progress(self, user_id: str) -> PrestigeProgress:
        """Get user's prestige progress"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = PrestigeProgress(user_id=user_id)
        
        return self.user_progress[user_id]
    
    def get_prestige_benefits(self, user_id: str) -> Dict[str, Any]:
        """Get all active prestige benefits for a user"""
        progress = self.get_user_progress(user_id)
        rank = PrestigeRank.from_level(progress.current_level)
        
        benefits = {
            "prestige_level": progress.current_level,
            "rank": {
                "name": rank.title,
                "icon": rank.icon,
                "level": rank.level
            },
            "xp_multiplier": progress.active_multiplier,
            "total_multiplier_bonus": f"+{(progress.active_multiplier - 1) * 100:.0f}%",
            "unlocked_perks": progress.unlocked_rewards,
            "lifetime_xp": progress.lifetime_xp,
            "prestiges_completed": progress.total_prestiges
        }
        
        # Add current rank rewards
        reward = self.PRESTIGE_REWARDS.get(rank)
        if reward:
            benefits["signal_access"] = reward.signal_access
            benefits["chat_color"] = reward.chat_color
            benefits["badge"] = reward.badge_icon
        
        # Add next rank preview
        next_rank = self._get_next_rank(rank)
        if next_rank:
            next_reward = self.PRESTIGE_REWARDS.get(next_rank)
            if next_reward:
                benefits["next_rank"] = {
                    "name": next_rank.title,
                    "icon": next_rank.icon,
                    "new_perks": [p for p in next_reward.perks if p not in progress.unlocked_rewards]
                }
        
        return benefits
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get prestige leaderboard"""
        leaderboard_data = []
        
        for i, (user_id, level, lifetime_xp) in enumerate(self.leaderboard[:limit]):
            rank = PrestigeRank.from_level(level)
            leaderboard_data.append({
                "position": i + 1,
                "user_id": user_id,
                "prestige_level": level,
                "rank": {
                    "name": rank.title,
                    "icon": rank.icon
                },
                "lifetime_xp": lifetime_xp
            })
        
        return leaderboard_data
    
    def get_prestige_stats(self) -> Dict[str, Any]:
        """Get overall prestige system statistics"""
        total_users = len(self.user_progress)
        total_prestiges = sum(p.total_prestiges for p in self.user_progress.values())
        
        # Count users by rank
        rank_distribution = {}
        for progress in self.user_progress.values():
            rank = PrestigeRank.from_level(progress.current_level)
            rank_name = rank.title
            rank_distribution[rank_name] = rank_distribution.get(rank_name, 0) + 1
        
        # Average prestige level
        avg_level = sum(p.current_level for p in self.user_progress.values()) / total_users if total_users > 0 else 0
        
        return {
            "total_prestiged_users": total_users,
            "total_prestiges": total_prestiges,
            "average_prestige_level": round(avg_level, 2),
            "rank_distribution": rank_distribution,
            "highest_prestige": self.leaderboard[0] if self.leaderboard else None
        }
    
    def check_special_prestige_signals(self, user_id: str, signal_category: str) -> bool:
        """Check if user has access to special prestige signals"""
        progress = self.get_user_progress(user_id)
        rank = PrestigeRank.from_level(progress.current_level)
        reward = self.PRESTIGE_REWARDS.get(rank)
        
        if not reward:
            return False
        
        return signal_category in reward.signal_access or "all_signals" in reward.signal_access
    
    def _get_next_rank(self, current_rank: PrestigeRank) -> Optional[PrestigeRank]:
        """Get the next prestige rank"""
        for rank in PrestigeRank:
            if rank.level == current_rank.level + 1:
                return rank
        return None
    
    def _update_leaderboard(self) -> None:
        """Update the prestige leaderboard"""
        self.leaderboard = []
        
        for user_id, progress in self.user_progress.items():
            if progress.current_level > 0:
                self.leaderboard.append((
                    user_id,
                    progress.current_level,
                    progress.lifetime_xp
                ))
        
        # Sort by level (desc), then lifetime XP (desc)
        self.leaderboard.sort(key=lambda x: (-x[1], -x[2]))
        
        # Save leaderboard
        self._save_leaderboard()
    
    def _save_user_progress(self, user_id: str) -> None:
        """Save user's prestige progress"""
        progress = self.user_progress[user_id]
        progress_file = self.data_dir / f"user_{user_id}_prestige.json"
        
        data = {
            "user_id": progress.user_id,
            "current_level": progress.current_level,
            "total_prestiges": progress.total_prestiges,
            "xp_at_prestige": progress.xp_at_prestige,
            "prestige_dates": [d.isoformat() for d in progress.prestige_dates],
            "lifetime_xp": progress.lifetime_xp,
            "unlocked_rewards": progress.unlocked_rewards,
            "active_multiplier": progress.active_multiplier
        }
        
        with open(progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_leaderboard(self) -> None:
        """Save the leaderboard"""
        leaderboard_file = self.data_dir / "prestige_leaderboard.json"
        
        data = []
        for user_id, level, lifetime_xp in self.leaderboard:
            data.append({
                "user_id": user_id,
                "level": level,
                "lifetime_xp": lifetime_xp
            })
        
        with open(leaderboard_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_prestige_data(self) -> None:
        """Load all prestige data"""
        # Load user progress
        for progress_file in self.data_dir.glob("user_*_prestige.json"):
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                
                progress = PrestigeProgress(
                    user_id=data["user_id"],
                    current_level=data["current_level"],
                    total_prestiges=data["total_prestiges"],
                    xp_at_prestige=data["xp_at_prestige"],
                    prestige_dates=[datetime.fromisoformat(d) for d in data["prestige_dates"]],
                    lifetime_xp=data["lifetime_xp"],
                    unlocked_rewards=data["unlocked_rewards"],
                    active_multiplier=data["active_multiplier"]
                )
                
                self.user_progress[data["user_id"]] = progress
                
            except Exception as e:
                logger.error(f"Error loading prestige file {progress_file}: {e}")
        
        # Load leaderboard
        leaderboard_file = self.data_dir / "prestige_leaderboard.json"
        if leaderboard_file.exists():
            try:
                with open(leaderboard_file, 'r') as f:
                    data = json.load(f)
                
                self.leaderboard = [
                    (item["user_id"], item["level"], item["lifetime_xp"])
                    for item in data
                ]
            except Exception as e:
                logger.error(f"Error loading leaderboard: {e}")

# Example usage
if __name__ == "__main__":
    system = PrestigeSystem()
    
    # Simulate prestige
    user_id = "test_user"
    success, progress, reward = system.execute_prestige(user_id, 55000)
    
    if success:
        print(f"Prestiged to {progress.current_level}!")
        print(f"New rank: {PrestigeRank.from_level(progress.current_level).title}")
        if reward:
            print(f"Rewards: {reward.perks}")
    
    # Get benefits
    benefits = system.get_prestige_benefits(user_id)
    print(f"\nBenefits: {benefits}")
    
    # Check leaderboard
    leaderboard = system.get_leaderboard()
    print(f"\nLeaderboard: {leaderboard}")