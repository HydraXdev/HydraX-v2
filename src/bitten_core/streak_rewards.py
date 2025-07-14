"""
Escalating Streak Reward System for BITTEN Platform
Advanced reward mechanics with milestone rewards, exclusive badges, titles, and special items
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RewardTier(Enum):
    """Reward tier classifications"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


class BadgeType(Enum):
    """Types of badges"""
    STREAK = "streak"
    MILESTONE = "milestone"
    SPECIAL = "special"
    SEASONAL = "seasonal"
    ACHIEVEMENT = "achievement"


class TitleRank(Enum):
    """Title rankings"""
    RECRUIT = "recruit"
    SOLDIER = "soldier"
    VETERAN = "veteran"
    ELITE = "elite"
    LEGEND = "legend"
    MYTHIC = "mythic"


@dataclass
class RewardItem:
    """Individual reward item"""
    id: str
    name: str
    type: str
    tier: RewardTier
    description: str
    icon: str
    quantity: int = 1
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class Badge:
    """Badge information"""
    id: str
    name: str
    description: str
    icon: str
    badge_type: BadgeType
    tier: RewardTier
    unlock_condition: str
    xp_bonus: float = 0.0  # Permanent XP bonus
    trading_bonus: float = 0.0  # Trading reward bonus


@dataclass
class Title:
    """Title information"""
    id: str
    name: str
    description: str
    rank: TitleRank
    prestige_level: int
    unlock_condition: str
    effects: Dict[str, float]  # Various bonuses
    display_color: str


@dataclass
class StreakRewardBundle:
    """Complete reward bundle for streak milestone"""
    milestone_day: int
    xp_base: int
    xp_multiplier: float
    items: List[RewardItem]
    badges: List[Badge]
    titles: List[Title]
    special_privileges: List[str]
    celebration_message: str


class StreakRewardSystem:
    """Advanced streak reward system with escalating benefits"""
    
    # XP Multiplier Progression (more aggressive scaling)
    XP_MULTIPLIERS = {
        1: 1.0,    # Day 1: Base
        2: 1.05,   # Day 2: +5%
        3: 1.1,    # Day 3: +10%
        7: 1.2,    # Week 1: +20%
        14: 1.35,  # Week 2: +35%
        21: 1.5,   # Week 3: +50%
        30: 1.75,  # Month 1: +75%
        45: 2.0,   # 45 days: +100%
        60: 2.25,  # 60 days: +125%
        90: 2.5,   # Quarter: +150%
        120: 2.75, # 4 months: +175%
        180: 3.0,  # Half year: +200%
        270: 3.5,  # 9 months: +250%
        365: 4.0   # Full year: +300%
    }
    
    # Milestone reward definitions
    MILESTONE_REWARDS = {
        # Week milestones (7, 14, 21, 28)
        7: {
            "xp_base": 500,
            "xp_multiplier": 1.5,
            "celebration": "🔥 WEEK WARRIOR! Your dedication is noticed!",
            "items": [
                {"id": "streak_freeze", "name": "Streak Freeze", "type": "protection", "tier": "uncommon", "quantity": 1},
                {"id": "xp_booster_small", "name": "XP Booster (24h)", "type": "booster", "tier": "common", "quantity": 1}
            ],
            "badges": [
                {"id": "week_warrior", "name": "Week Warrior", "type": "streak", "tier": "uncommon", "xp_bonus": 0.05}
            ],
            "privileges": ["streak_protection_available"]
        },
        
        14: {
            "xp_base": 750,
            "xp_multiplier": 1.75,
            "celebration": "💪 TWO WEEKS STRONG! Elite performance unlocked!",
            "items": [
                {"id": "premium_signals_day", "name": "Premium Signals (24h)", "type": "access", "tier": "rare", "quantity": 1},
                {"id": "streak_freeze", "name": "Streak Freeze", "type": "protection", "tier": "uncommon", "quantity": 2}
            ],
            "badges": [
                {"id": "fortnight_fighter", "name": "Fortnight Fighter", "type": "streak", "tier": "rare", "xp_bonus": 0.08}
            ],
            "privileges": ["premium_signals_preview", "priority_support"]
        },
        
        21: {
            "xp_base": 1000,
            "xp_multiplier": 2.0,
            "celebration": "🎯 THREE WEEKS! Sniper precision achieved!",
            "items": [
                {"id": "exclusive_indicator", "name": "Exclusive Indicator Access", "type": "tool", "tier": "epic", "quantity": 1},
                {"id": "xp_booster_large", "name": "XP Booster (72h)", "type": "booster", "tier": "rare", "quantity": 1}
            ],
            "badges": [
                {"id": "three_week_sniper", "name": "Three Week Sniper", "type": "milestone", "tier": "epic", "xp_bonus": 0.12}
            ],
            "titles": [
                {"id": "consistent_trader", "name": "Consistent Trader", "rank": "soldier", "prestige": 1}
            ],
            "privileges": ["advanced_analytics", "custom_alerts"]
        },
        
        # Monthly milestones
        30: {
            "xp_base": 2000,
            "xp_multiplier": 2.5,
            "celebration": "👑 MONTHLY MASTER! You've reached elite status!",
            "items": [
                {"id": "monthly_master_badge", "name": "Monthly Master Badge", "type": "cosmetic", "tier": "epic", "quantity": 1},
                {"id": "streak_shield", "name": "Streak Shield (7 days)", "type": "protection", "tier": "epic", "quantity": 1},
                {"id": "premium_course_access", "name": "Premium Course Access", "type": "education", "tier": "epic", "quantity": 1}
            ],
            "badges": [
                {"id": "monthly_master", "name": "Monthly Master", "type": "milestone", "tier": "epic", "xp_bonus": 0.15, "trading_bonus": 0.05}
            ],
            "titles": [
                {"id": "dedicated_trader", "name": "Dedicated Trader", "rank": "veteran", "prestige": 2}
            ],
            "privileges": ["vip_chat_access", "monthly_webinar_exclusive", "priority_signal_delivery"]
        },
        
        45: {
            "xp_base": 2500,
            "xp_multiplier": 2.75,
            "celebration": "🚀 45 DAYS! Rocket trajectory maintained!",
            "items": [
                {"id": "rocket_badge", "name": "Rocket Trajectory Badge", "type": "cosmetic", "tier": "epic", "quantity": 1},
                {"id": "double_xp_weekend", "name": "Double XP Weekend Pass", "type": "booster", "tier": "rare", "quantity": 1}
            ],
            "badges": [
                {"id": "rocket_trader", "name": "Rocket Trader", "type": "special", "tier": "epic", "xp_bonus": 0.18}
            ],
            "privileges": ["weekend_exclusive_signals"]
        },
        
        60: {
            "xp_base": 3000,
            "xp_multiplier": 3.0,
            "celebration": "💎 TWO MONTHS! Diamond hands proven!",
            "items": [
                {"id": "diamond_hands_trophy", "name": "Diamond Hands Trophy", "type": "trophy", "tier": "legendary", "quantity": 1},
                {"id": "premium_indicators_month", "name": "Premium Indicators (30 days)", "type": "tool", "tier": "legendary", "quantity": 1}
            ],
            "badges": [
                {"id": "diamond_hands", "name": "Diamond Hands", "type": "milestone", "tier": "legendary", "xp_bonus": 0.20, "trading_bonus": 0.08}
            ],
            "titles": [
                {"id": "elite_trader", "name": "Elite Trader", "rank": "elite", "prestige": 3}
            ],
            "privileges": ["diamond_tier_signals", "personal_analyst_consultation"]
        },
        
        # Quarterly milestone
        90: {
            "xp_base": 5000,
            "xp_multiplier": 3.5,
            "celebration": "🏆 QUARTERLY CHAMPION! Legendary status achieved!",
            "items": [
                {"id": "quarterly_champion_crown", "name": "Quarterly Champion Crown", "type": "cosmetic", "tier": "legendary", "quantity": 1},
                {"id": "exclusive_strategy_guide", "name": "Exclusive Strategy Guide", "type": "education", "tier": "legendary", "quantity": 1},
                {"id": "unlimited_streak_protection", "name": "Unlimited Streak Protection (30 days)", "type": "protection", "tier": "legendary", "quantity": 1}
            ],
            "badges": [
                {"id": "quarterly_champion", "name": "Quarterly Champion", "type": "milestone", "tier": "legendary", "xp_bonus": 0.25, "trading_bonus": 0.12}
            ],
            "titles": [
                {"id": "market_veteran", "name": "Market Veteran", "rank": "elite", "prestige": 4}
            ],
            "privileges": ["quarterly_vip_access", "private_trading_room", "strategy_development_input"]
        },
        
        120: {
            "xp_base": 6000,
            "xp_multiplier": 3.75,
            "celebration": "🌟 FOUR MONTHS! Stellar performance maintained!",
            "items": [
                {"id": "stellar_performance_star", "name": "Stellar Performance Star", "type": "cosmetic", "tier": "legendary", "quantity": 1},
                {"id": "ai_trading_assistant", "name": "AI Trading Assistant (Beta)", "type": "tool", "tier": "mythic", "quantity": 1}
            ],
            "badges": [
                {"id": "stellar_performer", "name": "Stellar Performer", "type": "special", "tier": "legendary", "xp_bonus": 0.28}
            ],
            "privileges": ["ai_assistant_access", "beta_feature_testing"]
        },
        
        # Half-year milestone
        180: {
            "xp_base": 8000,
            "xp_multiplier": 4.0,
            "celebration": "🎖️ HALF-YEAR HERO! Your commitment is extraordinary!",
            "items": [
                {"id": "half_year_medal", "name": "Half-Year Hero Medal", "type": "trophy", "tier": "mythic", "quantity": 1},
                {"id": "custom_trading_bot", "name": "Custom Trading Bot Setup", "type": "service", "tier": "mythic", "quantity": 1},
                {"id": "vip_mentorship", "name": "VIP Mentorship Program", "type": "service", "tier": "mythic", "quantity": 1}
            ],
            "badges": [
                {"id": "half_year_hero", "name": "Half-Year Hero", "type": "milestone", "tier": "mythic", "xp_bonus": 0.30, "trading_bonus": 0.15}
            ],
            "titles": [
                {"id": "trading_legend", "name": "Trading Legend", "rank": "legend", "prestige": 5}
            ],
            "privileges": ["legend_tier_access", "personal_trading_bot", "mentorship_program", "platform_development_input"]
        },
        
        270: {
            "xp_base": 10000,
            "xp_multiplier": 4.5,
            "celebration": "🌌 NINE MONTHS! Cosmic consistency achieved!",
            "items": [
                {"id": "cosmic_consistency_orb", "name": "Cosmic Consistency Orb", "type": "cosmetic", "tier": "mythic", "quantity": 1},
                {"id": "platform_profit_share", "name": "Platform Profit Share (1 month)", "type": "reward", "tier": "mythic", "quantity": 1}
            ],
            "badges": [
                {"id": "cosmic_trader", "name": "Cosmic Trader", "type": "special", "tier": "mythic", "xp_bonus": 0.35, "trading_bonus": 0.18}
            ],
            "privileges": ["profit_sharing_program", "cosmic_tier_signals"]
        },
        
        # Annual milestone
        365: {
            "xp_base": 15000,
            "xp_multiplier": 5.0,
            "celebration": "🎆 ANNUAL LEGEND! You are among the elite few! Welcome to immortality!",
            "items": [
                {"id": "annual_legend_trophy", "name": "Annual Legend Trophy", "type": "trophy", "tier": "mythic", "quantity": 1},
                {"id": "platform_ownership_share", "name": "Platform Ownership Share", "type": "equity", "tier": "mythic", "quantity": 1},
                {"id": "custom_feature_request", "name": "Custom Feature Request", "type": "service", "tier": "mythic", "quantity": 1},
                {"id": "hall_of_fame_entry", "name": "Hall of Fame Entry", "type": "honor", "tier": "mythic", "quantity": 1}
            ],
            "badges": [
                {"id": "annual_legend", "name": "Annual Legend", "type": "milestone", "tier": "mythic", "xp_bonus": 0.50, "trading_bonus": 0.25}
            ],
            "titles": [
                {"id": "immortal_trader", "name": "Immortal Trader", "rank": "mythic", "prestige": 10}
            ],
            "privileges": ["immortal_tier_access", "platform_ownership", "hall_of_fame", "unlimited_everything", "personal_developer"]
        }
    }
    
    # Special streak protection items
    PROTECTION_ITEMS = {
        "streak_freeze": {
            "name": "Streak Freeze",
            "description": "Pause your streak for 24 hours without losing progress",
            "duration_hours": 24,
            "tier": RewardTier.UNCOMMON
        },
        "streak_shield": {
            "name": "Streak Shield", 
            "description": "Protect your streak for up to 7 days",
            "duration_hours": 168,  # 7 days
            "tier": RewardTier.EPIC
        },
        "unlimited_streak_protection": {
            "name": "Unlimited Streak Protection",
            "description": "Complete streak protection for 30 days",
            "duration_hours": 720,  # 30 days
            "tier": RewardTier.LEGENDARY
        }
    }
    
    # Comeback bonus tiers
    COMEBACK_BONUSES = {
        1: {"multiplier": 1.5, "message": "Welcome back! Here's a small boost."},
        2: {"multiplier": 2.0, "message": "We missed you! Double XP today."},
        3: {"multiplier": 2.5, "message": "Great to see you return! Extra rewards."},
        7: {"multiplier": 3.0, "message": "Welcome back, warrior! Triple XP bonus."},
        14: {"multiplier": 4.0, "message": "The legend returns! Massive comeback bonus."},
        30: {"multiplier": 5.0, "message": "EPIC COMEBACK! You're unstoppable!"}
    }
    
    def __init__(self):
        self.active_boosters = {}  # Track active XP boosters
        self.seasonal_events = {}  # Track seasonal multipliers
    
    def get_streak_multiplier(self, streak_days: int) -> float:
        """Get XP multiplier for current streak"""
        multiplier = 1.0
        for days, mult in sorted(self.XP_MULTIPLIERS.items()):
            if streak_days >= days:
                multiplier = mult
        return multiplier
    
    def calculate_milestone_rewards(self, milestone_day: int) -> Optional[StreakRewardBundle]:
        """Calculate complete reward bundle for milestone"""
        if milestone_day not in self.MILESTONE_REWARDS:
            return None
        
        milestone_data = self.MILESTONE_REWARDS[milestone_day]
        
        # Convert items to RewardItem objects
        items = []
        for item_data in milestone_data.get("items", []):
            tier = RewardTier(item_data.get("tier", "common"))
            items.append(RewardItem(
                id=item_data["id"],
                name=item_data["name"],
                type=item_data["type"],
                tier=tier,
                description=item_data.get("description", ""),
                icon=item_data.get("icon", "🎁"),
                quantity=item_data.get("quantity", 1),
                metadata=item_data.get("metadata", {})
            ))
        
        # Convert badges to Badge objects
        badges = []
        for badge_data in milestone_data.get("badges", []):
            tier = RewardTier(badge_data.get("tier", "common"))
            badge_type = BadgeType(badge_data.get("type", "streak"))
            badges.append(Badge(
                id=badge_data["id"],
                name=badge_data["name"],
                description=badge_data.get("description", ""),
                icon=badge_data.get("icon", "🏆"),
                badge_type=badge_type,
                tier=tier,
                unlock_condition=f"Achieve {milestone_day} day streak",
                xp_bonus=badge_data.get("xp_bonus", 0.0),
                trading_bonus=badge_data.get("trading_bonus", 0.0)
            ))
        
        # Convert titles to Title objects
        titles = []
        for title_data in milestone_data.get("titles", []):
            rank = TitleRank(title_data.get("rank", "recruit"))
            titles.append(Title(
                id=title_data["id"],
                name=title_data["name"],
                description=title_data.get("description", ""),
                rank=rank,
                prestige_level=title_data.get("prestige", 1),
                unlock_condition=f"Achieve {milestone_day} day streak",
                effects=title_data.get("effects", {}),
                display_color=title_data.get("color", "#FFD700")
            ))
        
        return StreakRewardBundle(
            milestone_day=milestone_day,
            xp_base=milestone_data["xp_base"],
            xp_multiplier=milestone_data["xp_multiplier"],
            items=items,
            badges=badges,
            titles=titles,
            special_privileges=milestone_data.get("privileges", []),
            celebration_message=milestone_data["celebration"]
        )
    
    def calculate_comeback_bonus(self, days_away: int) -> Dict[str, Any]:
        """Calculate comeback bonus for returning users"""
        bonus_multiplier = 1.0
        message = "Welcome back!"
        
        # Find applicable comeback bonus
        for days, bonus_data in sorted(self.COMEBACK_BONUSES.items(), reverse=True):
            if days_away >= days:
                bonus_multiplier = bonus_data["multiplier"]
                message = bonus_data["message"]
                break
        
        # Add random bonus items for longer absences
        bonus_items = []
        if days_away >= 7:
            bonus_items.append(RewardItem(
                id="comeback_xp_booster",
                name="Comeback XP Booster",
                type="booster",
                tier=RewardTier.RARE,
                description="Extra XP for your triumphant return",
                icon="🚀",
                quantity=1,
                expires_at=(datetime.now() + timedelta(days=7)).isoformat()
            ))
        
        if days_away >= 30:
            bonus_items.append(RewardItem(
                id="legendary_comeback_package",
                name="Legendary Comeback Package",
                type="package",
                tier=RewardTier.LEGENDARY,
                description="Special rewards for dedicated warriors",
                icon="📦",
                quantity=1
            ))
        
        return {
            "multiplier": bonus_multiplier,
            "message": message,
            "bonus_items": bonus_items,
            "days_away": days_away
        }
    
    def get_user_badges(self, user_id: str, achieved_milestones: List[int]) -> List[Badge]:
        """Get all badges user has unlocked"""
        unlocked_badges = []
        
        for milestone in achieved_milestones:
            if milestone in self.MILESTONE_REWARDS:
                milestone_bundle = self.calculate_milestone_rewards(milestone)
                if milestone_bundle:
                    unlocked_badges.extend(milestone_bundle.badges)
        
        return unlocked_badges
    
    def get_user_titles(self, user_id: str, achieved_milestones: List[int]) -> List[Title]:
        """Get all titles user has unlocked"""
        unlocked_titles = []
        
        for milestone in achieved_milestones:
            if milestone in self.MILESTONE_REWARDS:
                milestone_bundle = self.calculate_milestone_rewards(milestone)
                if milestone_bundle:
                    unlocked_titles.extend(milestone_bundle.titles)
        
        return unlocked_titles
    
    def calculate_total_badge_bonuses(self, user_badges: List[Badge]) -> Dict[str, float]:
        """Calculate total bonuses from all badges"""
        total_xp_bonus = 0.0
        total_trading_bonus = 0.0
        
        for badge in user_badges:
            total_xp_bonus += badge.xp_bonus
            total_trading_bonus += badge.trading_bonus
        
        return {
            "xp_bonus": total_xp_bonus,
            "trading_bonus": total_trading_bonus,
            "badge_count": len(user_badges)
        }
    
    def get_next_milestone_info(self, current_streak: int) -> Optional[Dict[str, Any]]:
        """Get information about the next milestone"""
        next_milestone = None
        
        for milestone in sorted(self.MILESTONE_REWARDS.keys()):
            if current_streak < milestone:
                next_milestone = milestone
                break
        
        if not next_milestone:
            return None
        
        milestone_bundle = self.calculate_milestone_rewards(next_milestone)
        days_remaining = next_milestone - current_streak
        
        return {
            "milestone_day": next_milestone,
            "days_remaining": days_remaining,
            "rewards_preview": {
                "xp_base": milestone_bundle.xp_base,
                "xp_multiplier": milestone_bundle.xp_multiplier,
                "item_count": len(milestone_bundle.items),
                "badge_count": len(milestone_bundle.badges),
                "title_count": len(milestone_bundle.titles),
                "celebration": milestone_bundle.celebration_message
            },
            "progress_percentage": (current_streak / next_milestone) * 100
        }
    
    def get_streak_protection_options(self, user_streak: int) -> List[Dict[str, Any]]:
        """Get available streak protection options based on streak length"""
        options = []
        
        # Basic protection available at 7+ day streak
        if user_streak >= 7:
            options.append({
                "id": "streak_freeze",
                "name": "Streak Freeze",
                "description": "Pause your streak for 24 hours",
                "cost": "Free (1 per month)",
                "protection_hours": 24,
                "available": True
            })
        
        # Enhanced protection at 30+ day streak
        if user_streak >= 30:
            options.append({
                "id": "streak_shield",
                "name": "Streak Shield",
                "description": "Protect your streak for up to 7 days",
                "cost": "Premium Feature",
                "protection_hours": 168,
                "available": True
            })
        
        # Ultimate protection at 90+ day streak
        if user_streak >= 90:
            options.append({
                "id": "unlimited_protection",
                "name": "Unlimited Protection",
                "description": "Complete streak protection for 30 days",
                "cost": "VIP Exclusive",
                "protection_hours": 720,
                "available": True
            })
        
        return options
    
    def generate_milestone_celebration(self, milestone_day: int, user_name: str = "Warrior") -> Dict[str, Any]:
        """Generate celebration content for milestone achievement"""
        milestone_bundle = self.calculate_milestone_rewards(milestone_day)
        if not milestone_bundle:
            return {}
        
        # Create celebration animation data
        celebration = {
            "title": f"🎉 {milestone_day} DAY STREAK! 🎉",
            "message": milestone_bundle.celebration_message,
            "user_name": user_name,
            "milestone_day": milestone_day,
            "rewards_summary": {
                "xp_earned": milestone_bundle.xp_base,
                "xp_multiplier": milestone_bundle.xp_multiplier,
                "items_received": len(milestone_bundle.items),
                "badges_unlocked": len(milestone_bundle.badges),
                "titles_unlocked": len(milestone_bundle.titles)
            },
            "animation_effects": self._get_celebration_effects(milestone_day),
            "sound_effects": self._get_celebration_sounds(milestone_day),
            "social_share_text": f"Just achieved a {milestone_day} day streak on BITTEN! 🔥 #BittenStreak #TradingLife"
        }
        
        return celebration
    
    def _get_celebration_effects(self, milestone_day: int) -> List[str]:
        """Get visual effects for celebration"""
        if milestone_day >= 365:
            return ["fireworks", "golden_rain", "rainbow_flash", "screen_shake"]
        elif milestone_day >= 180:
            return ["confetti_burst", "golden_sparks", "pulse_glow"]
        elif milestone_day >= 90:
            return ["star_burst", "glitter_fall", "flash_border"]
        elif milestone_day >= 30:
            return ["confetti", "sparkles", "glow_pulse"]
        else:
            return ["sparkles", "gentle_glow"]
    
    def _get_celebration_sounds(self, milestone_day: int) -> List[str]:
        """Get sound effects for celebration"""
        if milestone_day >= 365:
            return ["epic_fanfare", "fireworks_boom", "crowd_cheer"]
        elif milestone_day >= 180:
            return ["victory_fanfare", "applause", "success_chime"]
        elif milestone_day >= 90:
            return ["achievement_sound", "fanfare", "applause"]
        elif milestone_day >= 30:
            return ["success_chime", "positive_ding"]
        else:
            return ["gentle_chime"]
    
    def get_leaderboard_streak_data(self, user_streaks: List[Tuple[str, int, int]]) -> List[Dict[str, Any]]:
        """Format streak data for leaderboards"""
        leaderboard = []
        
        for i, (user_id, current_streak, longest_streak) in enumerate(user_streaks, 1):
            # Get user's badges and titles
            milestones = [m for m in self.MILESTONE_REWARDS.keys() if m <= current_streak]
            badges = self.get_user_badges(user_id, milestones)
            titles = self.get_user_titles(user_id, milestones)
            
            # Get highest title
            highest_title = None
            if titles:
                highest_title = max(titles, key=lambda t: t.prestige_level)
            
            # Calculate streak tier
            tier = self._calculate_streak_tier(current_streak)
            
            leaderboard.append({
                "rank": i,
                "user_id": user_id,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "streak_tier": tier,
                "xp_multiplier": self.get_streak_multiplier(current_streak),
                "badge_count": len(badges),
                "highest_title": highest_title.name if highest_title else "Recruit",
                "next_milestone": self.get_next_milestone_info(current_streak),
                "streak_status": self._get_streak_status_emoji(current_streak)
            })
        
        return leaderboard
    
    def _calculate_streak_tier(self, streak_days: int) -> str:
        """Calculate streak tier based on days"""
        if streak_days >= 365:
            return "IMMORTAL"
        elif streak_days >= 180:
            return "LEGEND"
        elif streak_days >= 90:
            return "EPIC"
        elif streak_days >= 30:
            return "VETERAN"
        elif streak_days >= 7:
            return "WARRIOR"
        else:
            return "RECRUIT"
    
    def _get_streak_status_emoji(self, streak_days: int) -> str:
        """Get emoji representing streak status"""
        if streak_days >= 365:
            return "👑"  # Crown for immortals
        elif streak_days >= 180:
            return "🌟"  # Star for legends
        elif streak_days >= 90:
            return "🔥"  # Fire for epic streaks
        elif streak_days >= 30:
            return "⚡"  # Lightning for veterans
        elif streak_days >= 7:
            return "💪"  # Muscle for warriors
        else:
            return "🌱"  # Seedling for recruits
    
    def simulate_reward_progression(self, target_days: int) -> Dict[str, Any]:
        """Simulate reward progression up to target days"""
        progression = {
            "target_days": target_days,
            "total_milestones": 0,
            "total_xp_earned": 0,
            "total_items": 0,
            "total_badges": 0,
            "total_titles": 0,
            "milestones_achieved": [],
            "final_multiplier": self.get_streak_multiplier(target_days)
        }
        
        base_daily_xp = 50  # Base login XP
        
        for day in range(1, target_days + 1):
            # Calculate daily XP with multiplier
            daily_multiplier = self.get_streak_multiplier(day)
            daily_xp = int(base_daily_xp * daily_multiplier)
            progression["total_xp_earned"] += daily_xp
            
            # Check for milestone
            if day in self.MILESTONE_REWARDS:
                milestone_bundle = self.calculate_milestone_rewards(day)
                if milestone_bundle:
                    progression["total_milestones"] += 1
                    progression["total_xp_earned"] += milestone_bundle.xp_base
                    progression["total_items"] += len(milestone_bundle.items)
                    progression["total_badges"] += len(milestone_bundle.badges)
                    progression["total_titles"] += len(milestone_bundle.titles)
                    
                    progression["milestones_achieved"].append({
                        "day": day,
                        "xp_bonus": milestone_bundle.xp_base,
                        "celebration": milestone_bundle.celebration_message,
                        "items": len(milestone_bundle.items),
                        "badges": len(milestone_bundle.badges),
                        "titles": len(milestone_bundle.titles)
                    })
        
        return progression


# Example usage and testing
if __name__ == "__main__":
    # Initialize reward system
    reward_system = StreakRewardSystem()
    
    print("=== BITTEN Streak Reward System Demo ===\n")
    
    # Test milestone rewards
    test_milestones = [7, 30, 90, 180, 365]
    
    for milestone in test_milestones:
        print(f"--- {milestone} Day Milestone ---")
        bundle = reward_system.calculate_milestone_rewards(milestone)
        
        if bundle:
            print(f"XP Base: {bundle.xp_base}")
            print(f"XP Multiplier: {bundle.xp_multiplier}x")
            print(f"Items: {len(bundle.items)}")
            print(f"Badges: {len(bundle.badges)}")
            print(f"Titles: {len(bundle.titles)}")
            print(f"Celebration: {bundle.celebration_message}")
            print()
    
    # Test streak progression simulation
    print("--- Progression Simulation (90 days) ---")
    progression = reward_system.simulate_reward_progression(90)
    print(f"Total XP: {progression['total_xp_earned']:,}")
    print(f"Milestones: {progression['total_milestones']}")
    print(f"Items: {progression['total_items']}")
    print(f"Badges: {progression['total_badges']}")
    print(f"Final Multiplier: {progression['final_multiplier']}x")
    
    # Test comeback bonus
    print("\n--- Comeback Bonus Test ---")
    comeback = reward_system.calculate_comeback_bonus(14)
    print(f"Days away: 14")
    print(f"Bonus multiplier: {comeback['multiplier']}x")
    print(f"Message: {comeback['message']}")
    print(f"Bonus items: {len(comeback['bonus_items'])}")
    
    print("\n=== Reward System Ready! ===")