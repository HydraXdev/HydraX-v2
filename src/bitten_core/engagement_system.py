"""
Engagement System for HydraX v2
Manages daily login streaks, personal records, missions, rewards, and seasonal campaigns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import json
import asyncio
from collections import defaultdict

from .database import DatabaseManager
from .bot_personality import BotPersonality
from .reward_types import RewardType, Reward


class MissionType(Enum):
    """Types of daily missions"""
    BATTLE_COUNT = "battle_count"
    WIN_STREAK = "win_streak"
    USE_ABILITY = "use_ability"
    COLLECT_BITS = "collect_bits"
    SOCIAL_SHARE = "social_share"
    FRIEND_BATTLE = "friend_battle"
    EXPLORE_AREA = "explore_area"
    UPGRADE_BOT = "upgrade_bot"


class MysteryBoxRarity(Enum):
    """Mystery box rarity tiers"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class CampaignStatus(Enum):
    """Seasonal campaign status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLAIMED = "claimed"


@dataclass
class LoginStreak:
    """Tracks user login streak data"""
    user_id: str
    current_streak: int = 0
    longest_streak: int = 0
    last_login: Optional[datetime] = None
    total_logins: int = 0
    streak_rewards_claimed: List[int] = field(default_factory=list)


@dataclass
class PersonalRecord:
    """Stores personal best records"""
    record_type: str
    value: float
    achieved_at: datetime
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DailyMission:
    """Daily mission structure"""
    mission_id: str
    mission_type: MissionType
    bot_id: str  # Bot that gives this mission
    description: str
    target_value: int
    current_progress: int = 0
    rewards: List[Reward] = field(default_factory=list)
    is_completed: bool = False
    is_claimed: bool = False
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=1))


@dataclass
class MysteryBox:
    """Mystery box reward structure"""
    box_id: str
    rarity: MysteryBoxRarity
    contents: List[Reward] = field(default_factory=list)
    opened_at: Optional[datetime] = None
    source: str = ""  # How it was earned


@dataclass
class SeasonalCampaign:
    """Seasonal campaign data"""
    campaign_id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    current_progress: int = 0
    completed_milestones: List[int] = field(default_factory=list)
    total_rewards_claimed: int = 0


class EngagementSystem:
    """Main engagement system managing all user engagement features"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.user_streaks: Dict[str, LoginStreak] = {}
        self.user_records: Dict[str, List[PersonalRecord]] = defaultdict(list)
        self.daily_missions: Dict[str, List[DailyMission]] = defaultdict(list)
        self.mystery_boxes: Dict[str, List[MysteryBox]] = defaultdict(list)
        self.seasonal_campaigns: Dict[str, SeasonalCampaign] = {}
        self.current_season: Optional[SeasonalCampaign] = None
        
        # Streak milestone rewards (days -> rewards)
        self.streak_milestones = {
            3: [Reward(RewardType.BITS, 500), Reward(RewardType.XP, 100)],
            7: [Reward(RewardType.BITS, 1000), Reward(RewardType.MYSTERY_BOX, 1)],
            14: [Reward(RewardType.BITS, 2000), Reward(RewardType.RARE_ITEM, 1)],
            30: [Reward(RewardType.BITS, 5000), Reward(RewardType.LEGENDARY_BOX, 1)],
            60: [Reward(RewardType.BITS, 10000), Reward(RewardType.EXCLUSIVE_BOT, 1)],
            100: [Reward(RewardType.BITS, 20000), Reward(RewardType.TITLE, "Dedicated Player")]
        }
        
        # Mystery box drop rates
        self.mystery_box_rates = {
            MysteryBoxRarity.COMMON: 0.50,
            MysteryBoxRarity.UNCOMMON: 0.30,
            MysteryBoxRarity.RARE: 0.15,
            MysteryBoxRarity.EPIC: 0.04,
            MysteryBoxRarity.LEGENDARY: 0.01
        }
        
        # Record categories
        self.record_categories = [
            "highest_damage_dealt",
            "longest_win_streak",
            "fastest_victory",
            "most_bits_earned_day",
            "most_battles_day",
            "highest_combo",
            "most_perfect_blocks",
            "longest_survival_time"
        ]
    
    async def initialize(self):
        """Initialize engagement system from database"""
        await self._load_user_data()
        await self._load_current_campaign()
        await self._refresh_daily_missions()
    
    async def _load_user_data(self):
        """Load user engagement data from database"""
        # Implementation would load from database
        pass
    
    async def _load_current_campaign(self):
        """Load current seasonal campaign"""
        # For demo, create a sample campaign
        self.current_season = SeasonalCampaign(
            campaign_id="winter_2024",
            name="Winter Warriors",
            description="Battle through the frozen lands and earn exclusive winter rewards!",
            start_date=datetime.now() - timedelta(days=10),
            end_date=datetime.now() + timedelta(days=20),
            milestones=[
                {"level": 1, "xp_required": 100, "rewards": [Reward(RewardType.BITS, 100)]},
                {"level": 2, "xp_required": 250, "rewards": [Reward(RewardType.XP, 50)]},
                {"level": 3, "xp_required": 500, "rewards": [Reward(RewardType.MYSTERY_BOX, 1)]},
                {"level": 4, "xp_required": 1000, "rewards": [Reward(RewardType.RARE_ITEM, 1)]},
                {"level": 5, "xp_required": 2000, "rewards": [Reward(RewardType.EXCLUSIVE_BOT, 1)]},
            ]
        )
    
    async def record_login(self, user_id: str) -> Dict[str, Any]:
        """Record user login and update streak"""
        now = datetime.now()
        
        if user_id not in self.user_streaks:
            self.user_streaks[user_id] = LoginStreak(user_id=user_id)
        
        streak = self.user_streaks[user_id]
        streak_broken = False
        rewards_earned = []
        
        if streak.last_login:
            days_since_last = (now.date() - streak.last_login.date()).days
            
            if days_since_last == 1:
                # Continue streak
                streak.current_streak += 1
            elif days_since_last > 1:
                # Streak broken
                streak_broken = True
                streak.current_streak = 1
            # If same day, don't increment
        else:
            # First login
            streak.current_streak = 1
        
        streak.last_login = now
        streak.total_logins += 1
        
        # Update longest streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        
        # Check for milestone rewards
        for milestone, rewards in self.streak_milestones.items():
            if streak.current_streak == milestone and milestone not in streak.streak_rewards_claimed:
                streak.streak_rewards_claimed.append(milestone)
                rewards_earned.extend(rewards)
        
        # Save to database
        await self._save_login_streak(streak)
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "streak_broken": streak_broken,
            "rewards_earned": rewards_earned,
            "next_milestone": self._get_next_milestone(streak.current_streak)
        }
    
    def _get_next_milestone(self, current_streak: int) -> Optional[int]:
        """Get next streak milestone"""
        for milestone in sorted(self.streak_milestones.keys()):
            if milestone > current_streak:
                return milestone
        return None
    
    async def check_and_update_record(self, user_id: str, record_type: str, 
                                     value: float, details: Dict[str, Any] = None) -> Optional[PersonalRecord]:
        """Check if value is a new personal record and update if so"""
        user_records = self.user_records[user_id]
        
        # Find existing record of this type
        existing_record = None
        for record in user_records:
            if record.record_type == record_type:
                existing_record = record
                break
        
        # Check if new record
        if not existing_record or value > existing_record.value:
            new_record = PersonalRecord(
                record_type=record_type,
                value=value,
                achieved_at=datetime.now(),
                details=details or {}
            )
            
            if existing_record:
                user_records.remove(existing_record)
            user_records.append(new_record)
            
            # Save to database
            await self._save_personal_record(user_id, new_record)
            
            # Award achievement rewards
            await self._award_record_rewards(user_id, record_type, value)
            
            return new_record
        
        return None
    
    async def generate_daily_missions(self, user_id: str, user_bots: List[str]) -> List[DailyMission]:
        """Generate daily missions from user's bots"""
        missions = []
        mission_count = min(3, len(user_bots))  # Up to 3 daily missions
        
        selected_bots = random.sample(user_bots, mission_count)
        
        for bot_id in selected_bots:
            mission_type = random.choice(list(MissionType))
            mission = self._create_mission_for_type(bot_id, mission_type)
            missions.append(mission)
        
        self.daily_missions[user_id] = missions
        
        # Save to database
        await self._save_daily_missions(user_id, missions)
        
        return missions
    
    def _create_mission_for_type(self, bot_id: str, mission_type: MissionType) -> DailyMission:
        """Create a mission based on type"""
        mission_configs = {
            MissionType.BATTLE_COUNT: {
                "description": "Complete {target} battles today",
                "target": random.randint(3, 10),
                "rewards": [Reward(RewardType.BITS, 200), Reward(RewardType.XP, 50)]
            },
            MissionType.WIN_STREAK: {
                "description": "Win {target} battles in a row",
                "target": random.randint(2, 5),
                "rewards": [Reward(RewardType.BITS, 300), Reward(RewardType.XP, 75)]
            },
            MissionType.USE_ABILITY: {
                "description": "Use special abilities {target} times",
                "target": random.randint(10, 20),
                "rewards": [Reward(RewardType.BITS, 150), Reward(RewardType.XP, 40)]
            },
            MissionType.COLLECT_BITS: {
                "description": "Collect {target} $BITS",
                "target": random.randint(500, 2000),
                "rewards": [Reward(RewardType.MYSTERY_BOX, 1)]
            },
            MissionType.SOCIAL_SHARE: {
                "description": "Share your battle results",
                "target": 1,
                "rewards": [Reward(RewardType.BITS, 100), Reward(RewardType.XP, 25)]
            },
            MissionType.FRIEND_BATTLE: {
                "description": "Battle with {target} friends",
                "target": random.randint(1, 3),
                "rewards": [Reward(RewardType.BITS, 250), Reward(RewardType.XP, 60)]
            },
            MissionType.EXPLORE_AREA: {
                "description": "Explore {target} new areas",
                "target": random.randint(2, 5),
                "rewards": [Reward(RewardType.BITS, 200), Reward(RewardType.RARE_ITEM, 1)]
            },
            MissionType.UPGRADE_BOT: {
                "description": "Upgrade any bot {target} times",
                "target": random.randint(1, 3),
                "rewards": [Reward(RewardType.BITS, 300), Reward(RewardType.XP, 100)]
            }
        }
        
        config = mission_configs[mission_type]
        
        return DailyMission(
            mission_id=f"{bot_id}_{mission_type.value}_{datetime.now().date()}",
            mission_type=mission_type,
            bot_id=bot_id,
            description=config["description"].format(target=config["target"]),
            target_value=config["target"],
            rewards=config["rewards"]
        )
    
    async def update_mission_progress(self, user_id: str, mission_type: MissionType, 
                                    progress: int = 1) -> List[DailyMission]:
        """Update progress on daily missions"""
        completed_missions = []
        
        for mission in self.daily_missions.get(user_id, []):
            if mission.mission_type == mission_type and not mission.is_completed:
                mission.current_progress += progress
                
                if mission.current_progress >= mission.target_value:
                    mission.is_completed = True
                    completed_missions.append(mission)
        
        # Save progress
        await self._save_mission_progress(user_id)
        
        return completed_missions
    
    async def claim_mission_rewards(self, user_id: str, mission_id: str) -> List[Reward]:
        """Claim rewards from completed mission"""
        for mission in self.daily_missions.get(user_id, []):
            if mission.mission_id == mission_id and mission.is_completed and not mission.is_claimed:
                mission.is_claimed = True
                await self._save_mission_progress(user_id)
                return mission.rewards
        
        return []
    
    async def generate_mystery_box(self, user_id: str, source: str = "mission") -> MysteryBox:
        """Generate a mystery box with random rarity and contents"""
        # Determine rarity
        rarity = self._determine_box_rarity()
        
        # Generate contents based on rarity
        contents = self._generate_box_contents(rarity)
        
        box = MysteryBox(
            box_id=f"box_{user_id}_{datetime.now().timestamp()}",
            rarity=rarity,
            contents=contents,
            source=source
        )
        
        self.mystery_boxes[user_id].append(box)
        
        # Save to database
        await self._save_mystery_box(user_id, box)
        
        return box
    
    def _determine_box_rarity(self) -> MysteryBoxRarity:
        """Determine mystery box rarity based on drop rates"""
        rand = random.random()
        cumulative = 0
        
        for rarity, rate in self.mystery_box_rates.items():
            cumulative += rate
            if rand < cumulative:
                return rarity
        
        return MysteryBoxRarity.COMMON
    
    def _generate_box_contents(self, rarity: MysteryBoxRarity) -> List[Reward]:
        """Generate contents based on box rarity"""
        contents_config = {
            MysteryBoxRarity.COMMON: [
                Reward(RewardType.BITS, random.randint(50, 200)),
                Reward(RewardType.XP, random.randint(10, 50))
            ],
            MysteryBoxRarity.UNCOMMON: [
                Reward(RewardType.BITS, random.randint(200, 500)),
                Reward(RewardType.XP, random.randint(50, 100)),
                Reward(RewardType.COMMON_ITEM, 1)
            ],
            MysteryBoxRarity.RARE: [
                Reward(RewardType.BITS, random.randint(500, 1000)),
                Reward(RewardType.XP, random.randint(100, 200)),
                Reward(RewardType.RARE_ITEM, 1)
            ],
            MysteryBoxRarity.EPIC: [
                Reward(RewardType.BITS, random.randint(1000, 2000)),
                Reward(RewardType.XP, random.randint(200, 500)),
                Reward(RewardType.EPIC_ITEM, 1),
                Reward(RewardType.BOT_SKIN, 1)
            ],
            MysteryBoxRarity.LEGENDARY: [
                Reward(RewardType.BITS, random.randint(2000, 5000)),
                Reward(RewardType.XP, random.randint(500, 1000)),
                Reward(RewardType.LEGENDARY_ITEM, 1),
                Reward(RewardType.EXCLUSIVE_BOT, 1)
            ]
        }
        
        return contents_config[rarity]
    
    async def open_mystery_box(self, user_id: str, box_id: str) -> Optional[List[Reward]]:
        """Open a mystery box and return contents"""
        for box in self.mystery_boxes.get(user_id, []):
            if box.box_id == box_id and not box.opened_at:
                box.opened_at = datetime.now()
                await self._save_mystery_box(user_id, box)
                return box.contents
        
        return None
    
    async def update_campaign_progress(self, user_id: str, xp_gained: int) -> Dict[str, Any]:
        """Update seasonal campaign progress"""
        if not self.current_season:
            return {}
        
        campaign = self.current_season
        campaign.current_progress += xp_gained
        
        # Check for milestone completions
        newly_completed = []
        rewards_earned = []
        
        for i, milestone in enumerate(campaign.milestones):
            if i not in campaign.completed_milestones and campaign.current_progress >= milestone["xp_required"]:
                campaign.completed_milestones.append(i)
                newly_completed.append(milestone)
                rewards_earned.extend(milestone["rewards"])
        
        # Save progress
        await self._save_campaign_progress(user_id, campaign)
        
        return {
            "campaign_id": campaign.campaign_id,
            "current_progress": campaign.current_progress,
            "newly_completed_milestones": newly_completed,
            "rewards_earned": rewards_earned,
            "next_milestone": self._get_next_campaign_milestone(campaign)
        }
    
    def _get_next_campaign_milestone(self, campaign: SeasonalCampaign) -> Optional[Dict[str, Any]]:
        """Get next uncompleted milestone"""
        for i, milestone in enumerate(campaign.milestones):
            if i not in campaign.completed_milestones:
                return milestone
        return None
    
    def get_webapp_display_data(self, user_id: str) -> Dict[str, Any]:
        """Get all engagement data formatted for webapp display"""
        streak = self.user_streaks.get(user_id, LoginStreak(user_id=user_id))
        records = self.user_records.get(user_id, [])
        missions = self.daily_missions.get(user_id, [])
        unopened_boxes = [box for box in self.mystery_boxes.get(user_id, []) if not box.opened_at]
        
        return {
            "login_streak": {
                "current": streak.current_streak,
                "longest": streak.longest_streak,
                "last_login": streak.last_login.isoformat() if streak.last_login else None,
                "next_milestone": self._get_next_milestone(streak.current_streak),
                "total_logins": streak.total_logins
            },
            "personal_records": [
                {
                    "type": record.record_type,
                    "value": record.value,
                    "achieved_at": record.achieved_at.isoformat(),
                    "details": record.details
                }
                for record in sorted(records, key=lambda r: r.achieved_at, reverse=True)[:10]
            ],
            "daily_missions": [
                {
                    "mission_id": mission.mission_id,
                    "bot_id": mission.bot_id,
                    "description": mission.description,
                    "progress": f"{mission.current_progress}/{mission.target_value}",
                    "is_completed": mission.is_completed,
                    "is_claimed": mission.is_claimed,
                    "rewards": [{"type": r.reward_type.value, "amount": r.amount} for r in mission.rewards],
                    "expires_at": mission.expires_at.isoformat()
                }
                for mission in missions
            ],
            "mystery_boxes": {
                "unopened_count": len(unopened_boxes),
                "boxes": [
                    {
                        "box_id": box.box_id,
                        "rarity": box.rarity.value,
                        "source": box.source
                    }
                    for box in unopened_boxes[:5]  # Show up to 5 unopened boxes
                ]
            },
            "seasonal_campaign": self._get_campaign_display_data() if self.current_season else None
        }
    
    def _get_campaign_display_data(self) -> Dict[str, Any]:
        """Get campaign data for display"""
        campaign = self.current_season
        if not campaign:
            return {}
        
        total_milestones = len(campaign.milestones)
        completed_milestones = len(campaign.completed_milestones)
        
        return {
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "description": campaign.description,
            "progress": {
                "current_xp": campaign.current_progress,
                "milestones_completed": f"{completed_milestones}/{total_milestones}",
                "percentage": (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
            },
            "days_remaining": max(0, (campaign.end_date - datetime.now()).days),
            "next_milestone": self._get_next_campaign_milestone(campaign)
        }
    
    # Database save methods (placeholder implementations)
    async def _save_login_streak(self, streak: LoginStreak):
        """Save login streak to database"""
        pass
    
    async def _save_personal_record(self, user_id: str, record: PersonalRecord):
        """Save personal record to database"""
        pass
    
    async def _save_daily_missions(self, user_id: str, missions: List[DailyMission]):
        """Save daily missions to database"""
        pass
    
    async def _save_mission_progress(self, user_id: str):
        """Save mission progress to database"""
        pass
    
    async def _save_mystery_box(self, user_id: str, box: MysteryBox):
        """Save mystery box to database"""
        pass
    
    async def _save_campaign_progress(self, user_id: str, campaign: SeasonalCampaign):
        """Save campaign progress to database"""
        pass
    
    async def _award_record_rewards(self, user_id: str, record_type: str, value: float):
        """Award rewards for breaking personal records"""
        # Implementation would grant rewards based on record type
        pass
    
    async def _refresh_daily_missions(self):
        """Refresh daily missions for all users"""
        # Implementation would run daily to generate new missions
        pass


# Reward types that need to be defined
class RewardType(Enum):
    """Types of rewards in the system"""
    BITS = "bits"
    XP = "xp"
    MYSTERY_BOX = "mystery_box"
    COMMON_ITEM = "common_item"
    RARE_ITEM = "rare_item"
    EPIC_ITEM = "epic_item"
    LEGENDARY_ITEM = "legendary_item"
    LEGENDARY_BOX = "legendary_box"
    EXCLUSIVE_BOT = "exclusive_bot"
    BOT_SKIN = "bot_skin"
    TITLE = "title"


@dataclass
class Reward:
    """Reward structure"""
    reward_type: RewardType
    amount: Any  # Can be number, string (for titles), etc.
    metadata: Dict[str, Any] = field(default_factory=dict)