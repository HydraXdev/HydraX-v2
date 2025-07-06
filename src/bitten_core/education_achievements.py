"""
Education Achievement System for HydraX - Gaming-Style Learning Milestones
Inspired by Xbox/PlayStation achievement systems with hidden achievements,
progressive chains, and competitive leaderboards
"""

import json
import logging
import random
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass, field
import hashlib
from collections import defaultdict
import asyncio

from src.bitten_core.database import Database
from src.bitten_core.logger import Logger
from src.utils import send_discord_message


class AchievementRarity(Enum):
    """Achievement rarity tiers based on unlock percentage"""
    COMMON = "common"  # 50%+ of players
    UNCOMMON = "uncommon"  # 20-50% of players
    RARE = "rare"  # 5-20% of players
    EPIC = "epic"  # 1-5% of players
    LEGENDARY = "legendary"  # <1% of players
    MYTHIC = "mythic"  # <0.1% of players


class AchievementCategory(Enum):
    """Achievement categories for education"""
    KNOWLEDGE = "knowledge"  # Learning and quiz completion
    PRACTICE = "practice"  # Paper trading and exercises
    PERFORMANCE = "performance"  # Trading performance metrics
    DEDICATION = "dedication"  # Daily/weekly streaks
    SOCIAL = "social"  # Community and sharing
    MASTERY = "mastery"  # Advanced techniques
    SPECIAL = "special"  # Hidden and event achievements
    SEASONAL = "seasonal"  # Time-limited achievements


@dataclass
class Achievement:
    """Gaming-style achievement definition"""
    id: str
    name: str
    description: str
    hidden_description: str  # Shown when locked if hidden
    category: AchievementCategory
    rarity: AchievementRarity
    points: int  # Gamerscore/Trophy points
    icon: str
    badge_tier: str  # bronze, silver, gold, platinum
    hidden: bool = False
    secret: bool = False  # Ultra-hidden, no hints
    requirements: Dict[str, Any] = field(default_factory=dict)
    chain_id: Optional[str] = None  # For progressive achievements
    chain_order: int = 0
    unlock_sound: str = "achievement_unlock"
    particle_effect: str = "standard"
    time_limited: bool = False
    available_until: Optional[datetime] = None
    prerequisite_achievements: List[str] = field(default_factory=list)
    rewards: Dict[str, Any] = field(default_factory=dict)
    
    def get_display_name(self, unlocked: bool = False) -> str:
        """Get display name based on unlock status"""
        if self.secret and not unlocked:
            return "???"
        return self.name
    
    def get_display_description(self, unlocked: bool = False) -> str:
        """Get display description based on unlock status"""
        if self.secret and not unlocked:
            return "Hidden achievement - Keep playing to discover!"
        elif self.hidden and not unlocked:
            return self.hidden_description
        return self.description


@dataclass
class AchievementProgress:
    """Track progress towards an achievement"""
    achievement_id: str
    user_id: str
    current_progress: Dict[str, Any] = field(default_factory=dict)
    unlocked: bool = False
    unlock_date: Optional[datetime] = None
    progress_percentage: float = 0.0
    near_completion: bool = False  # For 80%+ progress notifications
    
    def is_near_completion(self) -> bool:
        """Check if achievement is almost unlocked"""
        return self.progress_percentage >= 80 and not self.unlocked


@dataclass
class DailyChallenge:
    """Daily achievement challenge"""
    id: str
    date: date
    achievement_ids: List[str]  # Achievements featured today
    bonus_multiplier: float = 2.0
    description: str = ""
    special_reward: Optional[Dict[str, Any]] = None


@dataclass
class WeeklyChallenge:
    """Weekly achievement challenge"""
    id: str
    week_start: date
    week_end: date
    required_achievements: List[str]
    reward_achievement_id: str  # Special achievement for completing
    bonus_xp: int = 1000
    description: str = ""


class EducationAchievementSystem:
    """Gaming-style achievement system for educational milestones"""
    
    # Rarity thresholds (percentage of players who have unlocked)
    RARITY_THRESHOLDS = {
        AchievementRarity.COMMON: 0.5,
        AchievementRarity.UNCOMMON: 0.2,
        AchievementRarity.RARE: 0.05,
        AchievementRarity.EPIC: 0.01,
        AchievementRarity.LEGENDARY: 0.001,
        AchievementRarity.MYTHIC: 0.0001
    }
    
    # Points by rarity
    RARITY_POINTS = {
        AchievementRarity.COMMON: 10,
        AchievementRarity.UNCOMMON: 25,
        AchievementRarity.RARE: 50,
        AchievementRarity.EPIC: 100,
        AchievementRarity.LEGENDARY: 250,
        AchievementRarity.MYTHIC: 1000
    }
    
    # Visual effects by rarity
    RARITY_EFFECTS = {
        AchievementRarity.COMMON: {"particle": "sparkle", "sound": "ding", "duration": 2},
        AchievementRarity.UNCOMMON: {"particle": "stars", "sound": "chime", "duration": 3},
        AchievementRarity.RARE: {"particle": "explosion", "sound": "fanfare", "duration": 4},
        AchievementRarity.EPIC: {"particle": "lightning", "sound": "epic_unlock", "duration": 5},
        AchievementRarity.LEGENDARY: {"particle": "rainbow", "sound": "legendary_unlock", "duration": 7},
        AchievementRarity.MYTHIC: {"particle": "cosmic", "sound": "mythic_unlock", "duration": 10}
    }
    
    def __init__(self, database: Database, logger: Logger):
        self.db = database
        self.logger = logger
        
        # Achievement storage
        self.achievements: Dict[str, Achievement] = {}
        self.achievement_chains: Dict[str, List[str]] = defaultdict(list)
        self.user_progress: Dict[str, Dict[str, AchievementProgress]] = defaultdict(dict)
        
        # Challenge tracking
        self.daily_challenges: Dict[date, DailyChallenge] = {}
        self.weekly_challenges: Dict[str, WeeklyChallenge] = {}
        self.active_monthly_theme: Optional[str] = None
        
        # Leaderboard cache
        self.leaderboard_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.cache_timestamp: Optional[datetime] = None
        
        # Initialize achievements and database
        asyncio.create_task(self._initialize_system())
    
    async def _initialize_system(self):
        """Initialize achievement system"""
        await self._initialize_database()
        self._register_all_achievements()
        await self._load_user_progress()
        await self._generate_daily_challenge()
        await self._generate_weekly_challenge()
    
    async def _initialize_database(self):
        """Initialize achievement database tables"""
        try:
            # Achievement unlocks table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS achievement_unlocks (
                    unlock_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    achievement_id TEXT NOT NULL,
                    unlock_date TIMESTAMP NOT NULL,
                    progress_data TEXT,
                    points_earned INTEGER,
                    rarity_at_unlock TEXT,
                    UNIQUE(user_id, achievement_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Achievement progress table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS achievement_progress (
                    user_id TEXT NOT NULL,
                    achievement_id TEXT NOT NULL,
                    progress_data TEXT NOT NULL,
                    progress_percentage REAL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, achievement_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Daily challenges table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS daily_challenges (
                    challenge_date DATE PRIMARY KEY,
                    challenge_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Weekly challenges table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS weekly_challenges (
                    challenge_id TEXT PRIMARY KEY,
                    week_start DATE NOT NULL,
                    week_end DATE NOT NULL,
                    challenge_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Achievement leaderboard table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS achievement_leaderboard (
                    user_id TEXT PRIMARY KEY,
                    total_points INTEGER DEFAULT 0,
                    total_unlocked INTEGER DEFAULT 0,
                    rare_unlocked INTEGER DEFAULT 0,
                    epic_unlocked INTEGER DEFAULT 0,
                    legendary_unlocked INTEGER DEFAULT 0,
                    mythic_unlocked INTEGER DEFAULT 0,
                    completion_percentage REAL DEFAULT 0,
                    last_unlock_date TIMESTAMP,
                    prestige_level INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Achievement showcase table (for profile display)
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS achievement_showcase (
                    user_id TEXT NOT NULL,
                    slot_number INTEGER NOT NULL,
                    achievement_id TEXT NOT NULL,
                    showcase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, slot_number),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            self.logger.info("Education achievement database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize achievement database: {e}")
    
    def _register_all_achievements(self):
        """Register all achievement definitions"""
        # Knowledge Achievements
        self._register_knowledge_achievements()
        
        # Practice Achievements
        self._register_practice_achievements()
        
        # Performance Achievements
        self._register_performance_achievements()
        
        # Dedication Achievements
        self._register_dedication_achievements()
        
        # Social Achievements
        self._register_social_achievements()
        
        # Mastery Achievements
        self._register_mastery_achievements()
        
        # Hidden Achievements
        self._register_hidden_achievements()
        
        # Special Event Achievements
        self._register_special_achievements()
        
        # Build achievement chains
        self._build_achievement_chains()
    
    def _register_knowledge_achievements(self):
        """Register knowledge-based achievements"""
        # Quiz achievements
        self.register_achievement(Achievement(
            id="first_lesson",
            name="First Steps",
            description="Complete your first educational lesson",
            hidden_description="Complete a lesson to unlock",
            category=AchievementCategory.KNOWLEDGE,
            rarity=AchievementRarity.COMMON,
            points=10,
            icon="book_bronze",
            badge_tier="bronze",
            requirements={"lessons_completed": 1},
            rewards={"xp": 100, "title": "Student"}
        ))
        
        self.register_achievement(Achievement(
            id="knowledge_seeker",
            name="Knowledge Seeker",
            description="Complete 10 educational lessons",
            hidden_description="Complete more lessons",
            category=AchievementCategory.KNOWLEDGE,
            rarity=AchievementRarity.UNCOMMON,
            points=25,
            icon="book_silver",
            badge_tier="silver",
            requirements={"lessons_completed": 10},
            chain_id="knowledge_chain",
            chain_order=1,
            prerequisite_achievements=["first_lesson"]
        ))
        
        self.register_achievement(Achievement(
            id="scholar",
            name="Scholar",
            description="Complete 50 educational lessons",
            hidden_description="Keep learning!",
            category=AchievementCategory.KNOWLEDGE,
            rarity=AchievementRarity.RARE,
            points=50,
            icon="book_gold",
            badge_tier="gold",
            requirements={"lessons_completed": 50},
            chain_id="knowledge_chain",
            chain_order=2,
            rewards={"xp": 500, "title": "Scholar"}
        ))
        
        self.register_achievement(Achievement(
            id="sage",
            name="Sage",
            description="Complete 100 educational lessons",
            hidden_description="The path to wisdom is long",
            category=AchievementCategory.KNOWLEDGE,
            rarity=AchievementRarity.EPIC,
            points=100,
            icon="book_platinum",
            badge_tier="platinum",
            requirements={"lessons_completed": 100},
            chain_id="knowledge_chain",
            chain_order=3,
            particle_effect="epic_books",
            rewards={"xp": 1000, "title": "Sage", "special_badge": "sage_aura"}
        ))
        
        # Quiz mastery
        self.register_achievement(Achievement(
            id="quiz_ace",
            name="Quiz Ace",
            description="Score 100% on 5 quizzes in a row",
            hidden_description="Perfect scores required",
            category=AchievementCategory.KNOWLEDGE,
            rarity=AchievementRarity.RARE,
            points=75,
            icon="perfect_score",
            badge_tier="gold",
            requirements={"perfect_quiz_streak": 5},
            unlock_sound="perfect_fanfare"
        ))
        
        self.register_achievement(Achievement(
            id="speed_learner",
            name="Speed Learner",
            description="Complete a lesson in under 5 minutes with 90%+ score",
            hidden_description="Fast and accurate",
            category=AchievementCategory.KNOWLEDGE,
            rarity=AchievementRarity.UNCOMMON,
            points=30,
            icon="lightning_book",
            badge_tier="silver",
            requirements={"speed_lesson": True}
        ))
    
    def _register_practice_achievements(self):
        """Register practice and paper trading achievements"""
        # Paper trading chain
        self.register_achievement(Achievement(
            id="paper_trader",
            name="Paper Trader",
            description="Complete your first paper trade",
            hidden_description="Try paper trading",
            category=AchievementCategory.PRACTICE,
            rarity=AchievementRarity.COMMON,
            points=10,
            icon="paper_bronze",
            badge_tier="bronze",
            requirements={"paper_trades_completed": 1}
        ))
        
        self.register_achievement(Achievement(
            id="practice_makes_perfect",
            name="Practice Makes Perfect",
            description="Complete 50 paper trades",
            hidden_description="Keep practicing",
            category=AchievementCategory.PRACTICE,
            rarity=AchievementRarity.UNCOMMON,
            points=25,
            icon="paper_silver",
            badge_tier="silver",
            requirements={"paper_trades_completed": 50},
            chain_id="practice_chain",
            chain_order=1
        ))
        
        self.register_achievement(Achievement(
            id="simulation_master",
            name="Simulation Master",
            description="Complete 200 paper trades with 60%+ win rate",
            hidden_description="Master the simulation",
            category=AchievementCategory.PRACTICE,
            rarity=AchievementRarity.RARE,
            points=50,
            icon="paper_gold",
            badge_tier="gold",
            requirements={"paper_trades_completed": 200, "paper_win_rate": 0.6},
            chain_id="practice_chain",
            chain_order=2,
            rewards={"xp": 750, "unlock": "advanced_paper_strategies"}
        ))
        
        # Strategy practice
        self.register_achievement(Achievement(
            id="strategy_explorer",
            name="Strategy Explorer",
            description="Test 5 different trading strategies in paper trading",
            hidden_description="Try different approaches",
            category=AchievementCategory.PRACTICE,
            rarity=AchievementRarity.UNCOMMON,
            points=35,
            icon="compass",
            badge_tier="silver",
            requirements={"unique_strategies_tested": 5}
        ))
    
    def _register_performance_achievements(self):
        """Register performance-based achievements"""
        # Win streaks
        self.register_achievement(Achievement(
            id="hot_streak",
            name="Hot Streak",
            description="Win 5 trades in a row",
            hidden_description="Build a winning streak",
            category=AchievementCategory.PERFORMANCE,
            rarity=AchievementRarity.UNCOMMON,
            points=30,
            icon="fire",
            badge_tier="silver",
            requirements={"win_streak": 5},
            particle_effect="fire_burst"
        ))
        
        self.register_achievement(Achievement(
            id="unstoppable",
            name="Unstoppable",
            description="Win 10 trades in a row",
            hidden_description="Keep the streak alive",
            category=AchievementCategory.PERFORMANCE,
            rarity=AchievementRarity.RARE,
            points=75,
            icon="fire_gold",
            badge_tier="gold",
            requirements={"win_streak": 10},
            chain_id="streak_chain",
            chain_order=1,
            particle_effect="inferno"
        ))
        
        self.register_achievement(Achievement(
            id="legendary_streak",
            name="Legendary Streak",
            description="Win 20 trades in a row",
            hidden_description="???",
            category=AchievementCategory.PERFORMANCE,
            rarity=AchievementRarity.LEGENDARY,
            points=250,
            icon="fire_legendary",
            badge_tier="platinum",
            requirements={"win_streak": 20},
            chain_id="streak_chain",
            chain_order=2,
            hidden=True,
            particle_effect="legendary_flames",
            unlock_sound="legendary_streak",
            rewards={"xp": 2500, "title": "Unstoppable Force", "special_effect": "flame_aura"}
        ))
        
        # Profit achievements
        self.register_achievement(Achievement(
            id="first_profit",
            name="First Profit",
            description="Make your first profitable trade",
            hidden_description="Turn a profit",
            category=AchievementCategory.PERFORMANCE,
            rarity=AchievementRarity.COMMON,
            points=10,
            icon="coin_bronze",
            badge_tier="bronze",
            requirements={"profitable_trades": 1}
        ))
        
        self.register_achievement(Achievement(
            id="consistent_earner",
            name="Consistent Earner",
            description="Maintain 50%+ win rate over 100 trades",
            hidden_description="Consistency is key",
            category=AchievementCategory.PERFORMANCE,
            rarity=AchievementRarity.RARE,
            points=100,
            icon="balance_gold",
            badge_tier="gold",
            requirements={"total_trades": 100, "win_rate": 0.5}
        ))
        
        # Risk management
        self.register_achievement(Achievement(
            id="risk_manager",
            name="Risk Manager",
            description="Complete 50 trades without exceeding 2% risk per trade",
            hidden_description="Control your risk",
            category=AchievementCategory.PERFORMANCE,
            rarity=AchievementRarity.RARE,
            points=75,
            icon="shield_gold",
            badge_tier="gold",
            requirements={"risk_controlled_trades": 50},
            rewards={"xp": 1000, "title": "Risk Manager"}
        ))
    
    def _register_dedication_achievements(self):
        """Register dedication and streak achievements"""
        # Daily login streaks
        self.register_achievement(Achievement(
            id="daily_dedication",
            name="Daily Dedication",
            description="Log in for 7 consecutive days",
            hidden_description="Show daily commitment",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.COMMON,
            points=15,
            icon="calendar_bronze",
            badge_tier="bronze",
            requirements={"login_streak": 7}
        ))
        
        self.register_achievement(Achievement(
            id="monthly_dedication",
            name="Monthly Dedication",
            description="Log in for 30 consecutive days",
            hidden_description="A month of dedication",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.UNCOMMON,
            points=50,
            icon="calendar_silver",
            badge_tier="silver",
            requirements={"login_streak": 30},
            chain_id="dedication_chain",
            chain_order=1
        ))
        
        self.register_achievement(Achievement(
            id="yearly_dedication",
            name="Yearly Dedication",
            description="Log in for 365 consecutive days",
            hidden_description="???",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.LEGENDARY,
            points=500,
            icon="calendar_legendary",
            badge_tier="platinum",
            requirements={"login_streak": 365},
            chain_id="dedication_chain",
            chain_order=2,
            hidden=True,
            particle_effect="golden_calendar",
            rewards={"xp": 5000, "title": "Eternal Student", "special_badge": "dedication_crown"}
        ))
        
        # Study streaks
        self.register_achievement(Achievement(
            id="weekend_warrior",
            name="Weekend Warrior",
            description="Complete lessons every weekend for a month",
            hidden_description="Study on weekends",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.UNCOMMON,
            points=40,
            icon="weekend_badge",
            badge_tier="silver",
            requirements={"weekend_streak": 4}
        ))
        
        # Time-based achievements
        self.register_achievement(Achievement(
            id="night_owl",
            name="Night Owl",
            description="Complete 10 lessons between midnight and 6 AM",
            hidden_description="???",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.RARE,
            points=60,
            icon="owl",
            badge_tier="gold",
            requirements={"night_lessons": 10},
            hidden=True,
            unlock_sound="hoot"
        ))
        
        self.register_achievement(Achievement(
            id="early_bird",
            name="Early Bird",
            description="Complete 10 lessons between 5 AM and 7 AM",
            hidden_description="???",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.RARE,
            points=60,
            icon="bird",
            badge_tier="gold",
            requirements={"early_lessons": 10},
            hidden=True,
            unlock_sound="chirp"
        ))
    
    def _register_social_achievements(self):
        """Register social and community achievements"""
        self.register_achievement(Achievement(
            id="helpful_trader",
            name="Helpful Trader",
            description="Share 5 educational resources with other traders",
            hidden_description="Help others learn",
            category=AchievementCategory.SOCIAL,
            rarity=AchievementRarity.UNCOMMON,
            points=30,
            icon="handshake",
            badge_tier="silver",
            requirements={"resources_shared": 5}
        ))
        
        self.register_achievement(Achievement(
            id="mentor",
            name="Mentor",
            description="Help 10 new traders with their questions",
            hidden_description="Become a mentor",
            category=AchievementCategory.SOCIAL,
            rarity=AchievementRarity.RARE,
            points=75,
            icon="teacher",
            badge_tier="gold",
            requirements={"traders_helped": 10},
            rewards={"xp": 1000, "title": "Mentor"}
        ))
        
        self.register_achievement(Achievement(
            id="community_champion",
            name="Community Champion",
            description="Participate in 20 community discussions",
            hidden_description="Engage with the community",
            category=AchievementCategory.SOCIAL,
            rarity=AchievementRarity.UNCOMMON,
            points=40,
            icon="community",
            badge_tier="silver",
            requirements={"discussions_participated": 20}
        ))
    
    def _register_mastery_achievements(self):
        """Register mastery and advanced achievements"""
        self.register_achievement(Achievement(
            id="strategy_master",
            name="Strategy Master",
            description="Master all basic trading strategies",
            hidden_description="Master the fundamentals",
            category=AchievementCategory.MASTERY,
            rarity=AchievementRarity.EPIC,
            points=150,
            icon="chess_master",
            badge_tier="platinum",
            requirements={"strategies_mastered": ["trend_following", "breakout", "mean_reversion", "momentum"]},
            particle_effect="strategic_aura"
        ))
        
        self.register_achievement(Achievement(
            id="risk_guru",
            name="Risk Management Guru",
            description="Complete advanced risk management certification",
            hidden_description="Master risk control",
            category=AchievementCategory.MASTERY,
            rarity=AchievementRarity.EPIC,
            points=200,
            icon="shield_master",
            badge_tier="platinum",
            requirements={"risk_certification": True},
            rewards={"xp": 2000, "title": "Risk Guru", "unlock": "advanced_risk_tools"}
        ))
        
        self.register_achievement(Achievement(
            id="market_sage",
            name="Market Sage",
            description="Correctly predict 10 major market movements",
            hidden_description="???",
            category=AchievementCategory.MASTERY,
            rarity=AchievementRarity.LEGENDARY,
            points=500,
            icon="crystal_ball",
            badge_tier="platinum",
            requirements={"correct_predictions": 10},
            hidden=True,
            secret=True,
            particle_effect="mystical_aura",
            rewards={"xp": 5000, "title": "Market Sage", "special_ability": "market_insight"}
        ))
    
    def _register_hidden_achievements(self):
        """Register hidden and secret achievements"""
        # Easter eggs
        self.register_achievement(Achievement(
            id="konami_code",
            name="Up, Up, Down, Down...",
            description="You know what you did",
            hidden_description="???",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.EPIC,
            points=100,
            icon="secret_code",
            badge_tier="gold",
            requirements={"konami_entered": True},
            hidden=True,
            secret=True,
            unlock_sound="retro_unlock",
            particle_effect="pixels"
        ))
        
        self.register_achievement(Achievement(
            id="persistence",
            name="Never Give Up",
            description="Come back after 10 consecutive losses",
            hidden_description="???",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.RARE,
            points=100,
            icon="phoenix",
            badge_tier="gold",
            requirements={"comeback_after_losses": 10},
            hidden=True,
            particle_effect="phoenix_rise",
            rewards={"xp": 1500, "title": "Phoenix"}
        ))
        
        self.register_achievement(Achievement(
            id="perfect_month",
            name="Perfect Month",
            description="Maintain 100% win rate for an entire month (min 20 trades)",
            hidden_description="???",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.MYTHIC,
            points=1000,
            icon="perfect_crown",
            badge_tier="platinum",
            requirements={"perfect_month": True, "monthly_trades": 20},
            hidden=True,
            secret=True,
            particle_effect="divine_light",
            unlock_sound="angelic_choir",
            rewards={"xp": 10000, "title": "Perfection", "special_effect": "golden_aura"}
        ))
        
        # Fun hidden achievements
        self.register_achievement(Achievement(
            id="butterfly_effect",
            name="Butterfly Effect",
            description="Make exactly $0.01 profit on a trade",
            hidden_description="???",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.RARE,
            points=50,
            icon="butterfly",
            badge_tier="silver",
            requirements={"penny_profit": True},
            hidden=True,
            unlock_sound="flutter"
        ))
        
        self.register_achievement(Achievement(
            id="lucky_seven",
            name="Lucky Seven",
            description="Win exactly $777.77 on a single trade",
            hidden_description="???",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.EPIC,
            points=77,
            icon="slot_machine",
            badge_tier="gold",
            requirements={"lucky_profit": 777.77},
            hidden=True,
            secret=True,
            particle_effect="slot_jackpot",
            unlock_sound="slot_win"
        ))
    
    def _register_special_achievements(self):
        """Register special event and seasonal achievements"""
        # Seasonal achievements
        self.register_achievement(Achievement(
            id="summer_trader",
            name="Summer Trader",
            description="Complete 50 trades during summer months",
            hidden_description="Trade in the summer",
            category=AchievementCategory.SEASONAL,
            rarity=AchievementRarity.UNCOMMON,
            points=40,
            icon="sun",
            badge_tier="silver",
            requirements={"summer_trades": 50},
            time_limited=True,
            particle_effect="sunshine"
        ))
        
        self.register_achievement(Achievement(
            id="holiday_spirit",
            name="Holiday Spirit",
            description="Log in on December 25th",
            hidden_description="???",
            category=AchievementCategory.SEASONAL,
            rarity=AchievementRarity.RARE,
            points=50,
            icon="gift",
            badge_tier="gold",
            requirements={"christmas_login": True},
            hidden=True,
            time_limited=True,
            unlock_sound="jingle_bells",
            particle_effect="snowfall"
        ))
        
        # Event achievements
        self.register_achievement(Achievement(
            id="beta_tester",
            name="Beta Tester",
            description="Participated in the platform beta",
            hidden_description="Be part of history",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.LEGENDARY,
            points=500,
            icon="beta_badge",
            badge_tier="platinum",
            requirements={"beta_participant": True},
            particle_effect="holographic",
            rewards={"xp": 5000, "title": "Beta Tester", "exclusive_badge": "beta_hologram"}
        ))
        
        # Challenge completion
        self.register_achievement(Achievement(
            id="challenge_accepted",
            name="Challenge Accepted",
            description="Complete your first daily challenge",
            hidden_description="Accept the challenge",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.COMMON,
            points=20,
            icon="challenge_bronze",
            badge_tier="bronze",
            requirements={"daily_challenges_completed": 1}
        ))
        
        self.register_achievement(Achievement(
            id="challenge_master",
            name="Challenge Master",
            description="Complete 30 daily challenges",
            hidden_description="Master the challenges",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.RARE,
            points=100,
            icon="challenge_gold",
            badge_tier="gold",
            requirements={"daily_challenges_completed": 30},
            chain_id="challenge_chain",
            chain_order=1
        ))
        
        # Ultimate achievements
        self.register_achievement(Achievement(
            id="completionist",
            name="Completionist",
            description="Unlock every other achievement",
            hidden_description="???",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.MYTHIC,
            points=2000,
            icon="infinity",
            badge_tier="platinum",
            requirements={"all_achievements": True},
            hidden=True,
            secret=True,
            particle_effect="cosmic_explosion",
            unlock_sound="epic_finale",
            rewards={
                "xp": 20000,
                "title": "Completionist",
                "special_effect": "rainbow_aura",
                "exclusive_badge": "infinity_badge",
                "unlock": "prestige_system"
            }
        ))
    
    def _build_achievement_chains(self):
        """Build achievement chains for progressive unlocks"""
        for achievement in self.achievements.values():
            if achievement.chain_id:
                self.achievement_chains[achievement.chain_id].append(achievement.id)
        
        # Sort chains by order
        for chain_id, achievement_ids in self.achievement_chains.items():
            self.achievement_chains[chain_id] = sorted(
                achievement_ids,
                key=lambda aid: self.achievements[aid].chain_order
            )
    
    def register_achievement(self, achievement: Achievement):
        """Register a new achievement"""
        self.achievements[achievement.id] = achievement
        self.logger.info(f"Registered achievement: {achievement.name} ({achievement.rarity.value})")
    
    async def _load_user_progress(self):
        """Load user progress from database"""
        try:
            progress_data = await self.db.fetch_all(
                "SELECT * FROM achievement_progress"
            )
            
            for row in progress_data:
                user_id = row['user_id']
                achievement_id = row['achievement_id']
                
                progress = AchievementProgress(
                    achievement_id=achievement_id,
                    user_id=user_id,
                    current_progress=json.loads(row['progress_data']),
                    progress_percentage=row['progress_percentage']
                )
                
                self.user_progress[user_id][achievement_id] = progress
            
            # Load unlocked achievements
            unlocks = await self.db.fetch_all(
                "SELECT * FROM achievement_unlocks"
            )
            
            for unlock in unlocks:
                user_id = unlock['user_id']
                achievement_id = unlock['achievement_id']
                
                if user_id in self.user_progress and achievement_id in self.user_progress[user_id]:
                    self.user_progress[user_id][achievement_id].unlocked = True
                    self.user_progress[user_id][achievement_id].unlock_date = unlock['unlock_date']
            
            self.logger.info(f"Loaded progress for {len(self.user_progress)} users")
            
        except Exception as e:
            self.logger.error(f"Failed to load user progress: {e}")
    
    async def update_progress(self, user_id: str, progress_data: Dict[str, Any]) -> List[Achievement]:
        """Update user's achievement progress and check for unlocks"""
        unlocked_achievements = []
        
        # Initialize user if needed
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
            await self._initialize_user_achievements(user_id)
        
        # Check each achievement
        for achievement_id, achievement in self.achievements.items():
            progress = self.user_progress[user_id].get(achievement_id)
            
            if not progress:
                progress = AchievementProgress(
                    achievement_id=achievement_id,
                    user_id=user_id
                )
                self.user_progress[user_id][achievement_id] = progress
            
            if progress.unlocked:
                continue
            
            # Check prerequisites
            if not await self._check_prerequisites(user_id, achievement):
                continue
            
            # Update progress
            progress_updated = False
            for req_key, req_value in achievement.requirements.items():
                if req_key in progress_data:
                    progress.current_progress[req_key] = progress_data[req_key]
                    progress_updated = True
            
            if progress_updated:
                # Calculate progress percentage
                progress.progress_percentage = self._calculate_progress_percentage(
                    progress, achievement
                )
                
                # Check for near completion
                if progress.is_near_completion() and not progress.near_completion:
                    progress.near_completion = True
                    await self._notify_near_completion(user_id, achievement)
                
                # Check if unlocked
                if self._check_unlock_conditions(progress, achievement):
                    await self._unlock_achievement(user_id, achievement)
                    unlocked_achievements.append(achievement)
                
                # Save progress
                await self._save_progress(user_id, achievement_id, progress)
        
        # Check for chain unlocks
        for unlocked in unlocked_achievements:
            if unlocked.chain_id:
                await self._check_chain_progress(user_id, unlocked.chain_id)
        
        # Check completionist achievement
        if unlocked_achievements:
            await self._check_completionist(user_id)
        
        return unlocked_achievements
    
    async def _check_prerequisites(self, user_id: str, achievement: Achievement) -> bool:
        """Check if prerequisites are met"""
        for prereq_id in achievement.prerequisite_achievements:
            prereq_progress = self.user_progress[user_id].get(prereq_id)
            if not prereq_progress or not prereq_progress.unlocked:
                return False
        return True
    
    def _calculate_progress_percentage(self, progress: AchievementProgress, 
                                     achievement: Achievement) -> float:
        """Calculate completion percentage"""
        if not achievement.requirements:
            return 100.0
        
        total_requirements = len(achievement.requirements)
        completed_requirements = 0.0
        
        for req_key, req_value in achievement.requirements.items():
            current_value = progress.current_progress.get(req_key, 0)
            
            if isinstance(req_value, bool):
                if current_value == req_value:
                    completed_requirements += 1
            elif isinstance(req_value, (int, float)):
                if current_value >= req_value:
                    completed_requirements += 1
                else:
                    completed_requirements += min(current_value / req_value, 1.0)
            elif isinstance(req_value, list):
                # For list requirements (e.g., master multiple strategies)
                if isinstance(current_value, list):
                    completed = len(set(current_value) & set(req_value))
                    completed_requirements += completed / len(req_value)
        
        return (completed_requirements / total_requirements) * 100
    
    def _check_unlock_conditions(self, progress: AchievementProgress, 
                               achievement: Achievement) -> bool:
        """Check if achievement should unlock"""
        for req_key, req_value in achievement.requirements.items():
            current_value = progress.current_progress.get(req_key, 0)
            
            if isinstance(req_value, bool):
                if current_value != req_value:
                    return False
            elif isinstance(req_value, (int, float)):
                if current_value < req_value:
                    return False
            elif isinstance(req_value, list):
                if isinstance(current_value, list):
                    if not all(item in current_value for item in req_value):
                        return False
        
        return True
    
    async def _unlock_achievement(self, user_id: str, achievement: Achievement):
        """Unlock an achievement for a user"""
        progress = self.user_progress[user_id][achievement.id]
        progress.unlocked = True
        progress.unlock_date = datetime.utcnow()
        progress.progress_percentage = 100.0
        
        # Calculate rarity at unlock
        total_users = await self.db.fetch_one(
            "SELECT COUNT(DISTINCT user_id) as count FROM users"
        )
        unlocked_count = await self.db.fetch_one(
            "SELECT COUNT(*) as count FROM achievement_unlocks WHERE achievement_id = ?",
            (achievement.id,)
        )
        
        unlock_percentage = (unlocked_count['count'] + 1) / total_users['count']
        rarity_at_unlock = self._calculate_rarity(unlock_percentage)
        
        # Store unlock
        await self.db.execute(
            """INSERT INTO achievement_unlocks 
               (unlock_id, user_id, achievement_id, unlock_date, progress_data, 
                points_earned, rarity_at_unlock)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (f"{user_id}_{achievement.id}_{datetime.utcnow().timestamp()}",
             user_id, achievement.id, datetime.utcnow(),
             json.dumps(progress.current_progress),
             self._calculate_points(achievement, rarity_at_unlock),
             rarity_at_unlock.value)
        )
        
        # Update leaderboard
        await self._update_leaderboard(user_id, achievement, rarity_at_unlock)
        
        # Send notification
        await self._notify_achievement_unlock(user_id, achievement, rarity_at_unlock)
        
        # Apply rewards
        if achievement.rewards:
            await self._apply_achievement_rewards(user_id, achievement)
        
        self.logger.info(f"Achievement unlocked: {achievement.name} for user {user_id}")
    
    def _calculate_rarity(self, unlock_percentage: float) -> AchievementRarity:
        """Calculate dynamic rarity based on unlock percentage"""
        for rarity, threshold in sorted(self.RARITY_THRESHOLDS.items(), 
                                      key=lambda x: x[1]):
            if unlock_percentage >= threshold:
                return rarity
        return AchievementRarity.MYTHIC
    
    def _calculate_points(self, achievement: Achievement, 
                         rarity_at_unlock: AchievementRarity) -> int:
        """Calculate points with rarity bonus"""
        base_points = achievement.points
        rarity_multiplier = {
            AchievementRarity.COMMON: 1.0,
            AchievementRarity.UNCOMMON: 1.2,
            AchievementRarity.RARE: 1.5,
            AchievementRarity.EPIC: 2.0,
            AchievementRarity.LEGENDARY: 3.0,
            AchievementRarity.MYTHIC: 5.0
        }
        
        return int(base_points * rarity_multiplier.get(rarity_at_unlock, 1.0))
    
    async def _notify_achievement_unlock(self, user_id: str, achievement: Achievement, 
                                       rarity: AchievementRarity):
        """Send achievement unlock notification"""
        effects = self.RARITY_EFFECTS[rarity]
        
        notification = {
            "type": "achievement_unlock",
            "achievement": {
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "rarity": rarity.value,
                "points": achievement.points,
                "icon": achievement.icon,
                "badge_tier": achievement.badge_tier
            },
            "effects": {
                "particle": achievement.particle_effect or effects["particle"],
                "sound": achievement.unlock_sound or effects["sound"],
                "duration": effects["duration"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send via appropriate channel (Discord, WebSocket, etc.)
        message = f"""🏆 **ACHIEVEMENT UNLOCKED!** 🏆

**{achievement.name}**
*{achievement.description}*

Rarity: **{rarity.value.upper()}**
Points: **{achievement.points}**

{self._get_rarity_emoji(rarity)} Congratulations! {self._get_rarity_emoji(rarity)}"""
        
        await send_discord_message(user_id, message)
    
    def _get_rarity_emoji(self, rarity: AchievementRarity) -> str:
        """Get emoji for rarity level"""
        emojis = {
            AchievementRarity.COMMON: "⭐",
            AchievementRarity.UNCOMMON: "✨",
            AchievementRarity.RARE: "💎",
            AchievementRarity.EPIC: "🔮",
            AchievementRarity.LEGENDARY: "👑",
            AchievementRarity.MYTHIC: "🌟"
        }
        return emojis.get(rarity, "🏆")
    
    async def _apply_achievement_rewards(self, user_id: str, achievement: Achievement):
        """Apply achievement rewards to user"""
        rewards = achievement.rewards
        
        if "xp" in rewards:
            # Add XP to user account
            await self.db.execute(
                "UPDATE users SET experience = experience + ? WHERE user_id = ?",
                (rewards["xp"], user_id)
            )
        
        if "title" in rewards:
            # Unlock title
            await self.db.execute(
                """INSERT OR IGNORE INTO user_titles (user_id, title, source)
                   VALUES (?, ?, ?)""",
                (user_id, rewards["title"], f"achievement_{achievement.id}")
            )
        
        if "unlock" in rewards:
            # Unlock feature or content
            await self.db.execute(
                """INSERT OR IGNORE INTO user_unlocks (user_id, unlock_type, unlock_id)
                   VALUES (?, ?, ?)""",
                (user_id, "achievement_reward", rewards["unlock"])
            )
    
    async def _notify_near_completion(self, user_id: str, achievement: Achievement):
        """Notify user when achievement is almost complete"""
        if achievement.hidden or achievement.secret:
            return
        
        progress = self.user_progress[user_id][achievement.id]
        
        message = f"""🎯 **Achievement Almost Complete!**

**{achievement.name}**
Progress: {progress.progress_percentage:.0f}%

You're so close! Keep going! 💪"""
        
        await send_discord_message(user_id, message)
    
    async def _check_chain_progress(self, user_id: str, chain_id: str):
        """Check progress in achievement chain"""
        chain = self.achievement_chains.get(chain_id, [])
        if not chain:
            return
        
        # Find highest unlocked in chain
        highest_unlocked = -1
        for i, achievement_id in enumerate(chain):
            progress = self.user_progress[user_id].get(achievement_id)
            if progress and progress.unlocked:
                highest_unlocked = i
        
        # Notify about next in chain
        if highest_unlocked < len(chain) - 1:
            next_achievement = self.achievements[chain[highest_unlocked + 1]]
            if not next_achievement.hidden:
                message = f"""🔗 **Achievement Chain Progress!**

Next in chain: **{next_achievement.name}**
*{next_achievement.description}*

Keep progressing to unlock! 🚀"""
                
                await send_discord_message(user_id, message)
    
    async def _check_completionist(self, user_id: str):
        """Check if user has unlocked all achievements"""
        total_achievements = len([a for a in self.achievements.values() 
                                if not a.id == "completionist"])
        unlocked_count = len([p for p in self.user_progress[user_id].values() 
                            if p.unlocked and p.achievement_id != "completionist"])
        
        if unlocked_count >= total_achievements:
            await self.update_progress(user_id, {"all_achievements": True})
    
    async def _save_progress(self, user_id: str, achievement_id: str, 
                           progress: AchievementProgress):
        """Save achievement progress to database"""
        await self.db.execute(
            """INSERT OR REPLACE INTO achievement_progress 
               (user_id, achievement_id, progress_data, progress_percentage, last_updated)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, achievement_id, json.dumps(progress.current_progress),
             progress.progress_percentage, datetime.utcnow())
        )
    
    async def _update_leaderboard(self, user_id: str, achievement: Achievement, 
                                rarity: AchievementRarity):
        """Update achievement leaderboard"""
        # Fetch current stats
        stats = await self.db.fetch_one(
            "SELECT * FROM achievement_leaderboard WHERE user_id = ?",
            (user_id,)
        )
        
        if not stats:
            # Create new entry
            await self.db.execute(
                """INSERT INTO achievement_leaderboard 
                   (user_id, total_points, total_unlocked, rare_unlocked, 
                    epic_unlocked, legendary_unlocked, mythic_unlocked, 
                    completion_percentage, last_unlock_date)
                   VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)""",
                (user_id, achievement.points,
                 1 if rarity == AchievementRarity.RARE else 0,
                 1 if rarity == AchievementRarity.EPIC else 0,
                 1 if rarity == AchievementRarity.LEGENDARY else 0,
                 1 if rarity == AchievementRarity.MYTHIC else 0,
                 (1 / len(self.achievements)) * 100,
                 datetime.utcnow())
            )
        else:
            # Update existing
            rarity_column = f"{rarity.value}_unlocked"
            total_unlocked = stats['total_unlocked'] + 1
            completion = (total_unlocked / len(self.achievements)) * 100
            
            await self.db.execute(
                f"""UPDATE achievement_leaderboard 
                    SET total_points = total_points + ?,
                        total_unlocked = total_unlocked + 1,
                        {rarity_column} = {rarity_column} + 1,
                        completion_percentage = ?,
                        last_unlock_date = ?
                    WHERE user_id = ?""",
                (achievement.points, completion, datetime.utcnow(), user_id)
            )
    
    # Daily/Weekly/Monthly Challenges
    
    async def _generate_daily_challenge(self):
        """Generate daily achievement challenge"""
        today = date.today()
        
        # Check if already generated
        existing = await self.db.fetch_one(
            "SELECT * FROM daily_challenges WHERE challenge_date = ?",
            (today,)
        )
        
        if existing:
            challenge_data = json.loads(existing['challenge_data'])
            self.daily_challenges[today] = DailyChallenge(**challenge_data)
            return
        
        # Select random achievements for daily challenge
        eligible = [a for a in self.achievements.values() 
                   if not a.hidden and not a.time_limited 
                   and a.rarity in [AchievementRarity.COMMON, AchievementRarity.UNCOMMON]]
        
        selected = random.sample(eligible, min(3, len(eligible)))
        
        challenge = DailyChallenge(
            id=f"daily_{today.isoformat()}",
            date=today,
            achievement_ids=[a.id for a in selected],
            description=f"Complete these achievements today for bonus points!",
            special_reward={"xp": 500, "title": "Daily Champion"} if random.random() < 0.1 else None
        )
        
        self.daily_challenges[today] = challenge
        
        # Store in database
        await self.db.execute(
            "INSERT INTO daily_challenges (challenge_date, challenge_data) VALUES (?, ?)",
            (today, json.dumps(challenge.__dict__, default=str))
        )
    
    async def _generate_weekly_challenge(self):
        """Generate weekly achievement challenge"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_id = f"week_{week_start.isoformat()}"
        
        # Check if already generated
        existing = await self.db.fetch_one(
            "SELECT * FROM weekly_challenges WHERE challenge_id = ?",
            (week_id,)
        )
        
        if existing:
            challenge_data = json.loads(existing['challenge_data'])
            self.weekly_challenges[week_id] = WeeklyChallenge(**challenge_data)
            return
        
        # Create themed weekly challenge
        themes = [
            {
                "name": "Knowledge Week",
                "category": AchievementCategory.KNOWLEDGE,
                "reward_achievement": "weekly_scholar"
            },
            {
                "name": "Practice Week",
                "category": AchievementCategory.PRACTICE,
                "reward_achievement": "weekly_practitioner"
            },
            {
                "name": "Performance Week",
                "category": AchievementCategory.PERFORMANCE,
                "reward_achievement": "weekly_performer"
            }
        ]
        
        theme = random.choice(themes)
        eligible = [a.id for a in self.achievements.values() 
                   if a.category == theme["category"] and not a.hidden]
        
        selected = random.sample(eligible, min(5, len(eligible)))
        
        challenge = WeeklyChallenge(
            id=week_id,
            week_start=week_start,
            week_end=week_end,
            required_achievements=selected,
            reward_achievement_id=theme["reward_achievement"],
            description=f"{theme['name']}: Complete 5 {theme['category'].value} achievements!"
        )
        
        self.weekly_challenges[week_id] = challenge
        
        # Store in database
        await self.db.execute(
            """INSERT INTO weekly_challenges 
               (challenge_id, week_start, week_end, challenge_data) 
               VALUES (?, ?, ?, ?)""",
            (week_id, week_start, week_end, 
             json.dumps(challenge.__dict__, default=str))
        )
    
    async def check_daily_challenge_completion(self, user_id: str, achievement_id: str):
        """Check if achievement completes daily challenge"""
        today = date.today()
        challenge = self.daily_challenges.get(today)
        
        if not challenge or achievement_id not in challenge.achievement_ids:
            return
        
        # Check if all daily achievements completed
        completed = []
        for aid in challenge.achievement_ids:
            progress = self.user_progress[user_id].get(aid)
            if progress and progress.unlocked:
                completed.append(aid)
        
        if len(completed) == len(challenge.achievement_ids):
            # Daily challenge complete!
            await self.update_progress(user_id, {"daily_challenges_completed": 1})
            
            message = f"""🌟 **DAILY CHALLENGE COMPLETE!** 🌟

You've completed all achievements in today's challenge!
Bonus Points: {int(sum(self.achievements[aid].points for aid in completed) * 0.5)}

Keep the streak going tomorrow! 🔥"""
            
            await send_discord_message(user_id, message)
    
    # Leaderboard Functions
    
    async def get_leaderboard(self, leaderboard_type: str = "total_points", 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get achievement leaderboard"""
        # Check cache
        cache_key = f"{leaderboard_type}_{limit}"
        if (self.cache_timestamp and 
            datetime.utcnow() - self.cache_timestamp < timedelta(minutes=5) and
            cache_key in self.leaderboard_cache):
            return self.leaderboard_cache[cache_key]
        
        # Fetch from database
        valid_types = [
            "total_points", "total_unlocked", "completion_percentage",
            "rare_unlocked", "epic_unlocked", "legendary_unlocked", 
            "mythic_unlocked", "prestige_level"
        ]
        
        if leaderboard_type not in valid_types:
            leaderboard_type = "total_points"
        
        leaderboard = await self.db.fetch_all(
            f"""SELECT l.*, u.username, u.avatar_url
                FROM achievement_leaderboard l
                JOIN users u ON l.user_id = u.user_id
                ORDER BY l.{leaderboard_type} DESC
                LIMIT ?""",
            (limit,)
        )
        
        # Format leaderboard
        formatted = []
        for i, entry in enumerate(leaderboard):
            formatted.append({
                "rank": i + 1,
                "user_id": entry['user_id'],
                "username": entry['username'],
                "avatar_url": entry['avatar_url'],
                "total_points": entry['total_points'],
                "total_unlocked": entry['total_unlocked'],
                "completion_percentage": entry['completion_percentage'],
                "rare_unlocked": entry['rare_unlocked'],
                "epic_unlocked": entry['epic_unlocked'],
                "legendary_unlocked": entry['legendary_unlocked'],
                "mythic_unlocked": entry['mythic_unlocked'],
                "prestige_level": entry['prestige_level'],
                "last_unlock_date": entry['last_unlock_date']
            })
        
        # Cache results
        self.leaderboard_cache[cache_key] = formatted
        self.cache_timestamp = datetime.utcnow()
        
        return formatted
    
    async def get_user_achievements(self, user_id: str) -> Dict[str, Any]:
        """Get all achievements and progress for a user"""
        if user_id not in self.user_progress:
            await self._initialize_user_achievements(user_id)
        
        # Get user stats
        stats = await self.db.fetch_one(
            "SELECT * FROM achievement_leaderboard WHERE user_id = ?",
            (user_id,)
        )
        
        # Get showcase achievements
        showcase = await self.db.fetch_all(
            """SELECT * FROM achievement_showcase 
               WHERE user_id = ? 
               ORDER BY slot_number""",
            (user_id,)
        )
        
        # Format achievements by category
        achievements_by_category = defaultdict(list)
        
        for achievement_id, achievement in self.achievements.items():
            progress = self.user_progress[user_id].get(achievement_id, 
                                                      AchievementProgress(achievement_id, user_id))
            
            # Skip completely hidden achievements unless unlocked
            if achievement.secret and not progress.unlocked:
                continue
            
            achievement_data = {
                "id": achievement.id,
                "name": achievement.get_display_name(progress.unlocked),
                "description": achievement.get_display_description(progress.unlocked),
                "category": achievement.category.value,
                "rarity": achievement.rarity.value,
                "points": achievement.points,
                "icon": achievement.icon,
                "badge_tier": achievement.badge_tier,
                "hidden": achievement.hidden,
                "unlocked": progress.unlocked,
                "unlock_date": progress.unlock_date.isoformat() if progress.unlock_date else None,
                "progress_percentage": progress.progress_percentage,
                "chain_id": achievement.chain_id,
                "chain_order": achievement.chain_order
            }
            
            achievements_by_category[achievement.category.value].append(achievement_data)
        
        # Calculate category completion
        category_stats = {}
        for category in AchievementCategory:
            category_achievements = [a for a in self.achievements.values() 
                                   if a.category == category and not a.secret]
            unlocked = len([p for aid, p in self.user_progress[user_id].items() 
                          if p.unlocked and self.achievements.get(aid) and 
                          self.achievements[aid].category == category])
            
            category_stats[category.value] = {
                "total": len(category_achievements),
                "unlocked": unlocked,
                "percentage": (unlocked / len(category_achievements) * 100) 
                            if category_achievements else 0
            }
        
        return {
            "user_id": user_id,
            "stats": {
                "total_points": stats['total_points'] if stats else 0,
                "total_unlocked": stats['total_unlocked'] if stats else 0,
                "completion_percentage": stats['completion_percentage'] if stats else 0,
                "prestige_level": stats['prestige_level'] if stats else 0,
                "global_rank": await self._get_user_rank(user_id)
            },
            "achievements": dict(achievements_by_category),
            "category_stats": category_stats,
            "showcase": [s['achievement_id'] for s in showcase],
            "daily_challenge": self.daily_challenges.get(date.today()),
            "recent_unlocks": await self._get_recent_unlocks(user_id)
        }
    
    async def _initialize_user_achievements(self, user_id: str):
        """Initialize achievements for new user"""
        for achievement_id in self.achievements:
            self.user_progress[user_id][achievement_id] = AchievementProgress(
                achievement_id=achievement_id,
                user_id=user_id
            )
    
    async def _get_user_rank(self, user_id: str) -> int:
        """Get user's global rank"""
        result = await self.db.fetch_one(
            """SELECT COUNT(*) + 1 as rank 
               FROM achievement_leaderboard 
               WHERE total_points > (
                   SELECT total_points 
                   FROM achievement_leaderboard 
                   WHERE user_id = ?
               )""",
            (user_id,)
        )
        return result['rank'] if result else 0
    
    async def _get_recent_unlocks(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's recent achievement unlocks"""
        unlocks = await self.db.fetch_all(
            """SELECT * FROM achievement_unlocks 
               WHERE user_id = ? 
               ORDER BY unlock_date DESC 
               LIMIT ?""",
            (user_id, limit)
        )
        
        recent = []
        for unlock in unlocks:
            achievement = self.achievements.get(unlock['achievement_id'])
            if achievement:
                recent.append({
                    "achievement_id": achievement.id,
                    "name": achievement.name,
                    "icon": achievement.icon,
                    "rarity": unlock['rarity_at_unlock'],
                    "points": unlock['points_earned'],
                    "unlock_date": unlock['unlock_date'].isoformat()
                })
        
        return recent
    
    async def set_showcase_achievement(self, user_id: str, slot: int, 
                                     achievement_id: str) -> bool:
        """Set achievement in user's showcase"""
        if slot < 1 or slot > 5:
            return False
        
        # Check if user has unlocked the achievement
        progress = self.user_progress[user_id].get(achievement_id)
        if not progress or not progress.unlocked:
            return False
        
        # Update showcase
        await self.db.execute(
            """INSERT OR REPLACE INTO achievement_showcase 
               (user_id, slot_number, achievement_id) 
               VALUES (?, ?, ?)""",
            (user_id, slot, achievement_id)
        )
        
        return True
    
    # Special achievement hunters rewards
    
    async def check_achievement_hunter_rewards(self, user_id: str):
        """Check and apply special rewards for achievement hunters"""
        stats = await self.db.fetch_one(
            "SELECT * FROM achievement_leaderboard WHERE user_id = ?",
            (user_id,)
        )
        
        if not stats:
            return
        
        # Milestone rewards
        milestones = [
            (10, "Achievement Hunter", 500),
            (25, "Achievement Collector", 1000),
            (50, "Achievement Master", 2500),
            (100, "Achievement Legend", 5000),
            (len(self.achievements) * 0.5, "Halfway There", 10000),
            (len(self.achievements) * 0.75, "Almost There", 15000),
            (len(self.achievements) * 0.9, "Completionist Elite", 20000)
        ]
        
        for threshold, title, xp_reward in milestones:
            if stats['total_unlocked'] >= threshold:
                # Check if already rewarded
                existing = await self.db.fetch_one(
                    """SELECT 1 FROM user_titles 
                       WHERE user_id = ? AND title = ?""",
                    (user_id, title)
                )
                
                if not existing:
                    # Award title and XP
                    await self.db.execute(
                        """INSERT INTO user_titles (user_id, title, source)
                           VALUES (?, ?, ?)""",
                        (user_id, title, "achievement_milestone")
                    )
                    
                    await self.db.execute(
                        "UPDATE users SET experience = experience + ? WHERE user_id = ?",
                        (xp_reward, user_id)
                    )
                    
                    message = f"""🎊 **MILESTONE REACHED!** 🎊

You've unlocked {stats['total_unlocked']} achievements!

New Title: **{title}**
Bonus XP: **{xp_reward}**

Keep hunting those achievements! 🏆"""
                    
                    await send_discord_message(user_id, message)
    
    # Integration with education system
    
    async def track_education_progress(self, user_id: str, event_type: str, 
                                     event_data: Dict[str, Any]):
        """Track education-related events for achievements"""
        progress_updates = {}
        
        if event_type == "lesson_completed":
            progress_updates["lessons_completed"] = event_data.get("total_lessons", 0)
            
            # Check for speed completion
            if event_data.get("duration_minutes", 0) < 5 and event_data.get("score", 0) >= 90:
                progress_updates["speed_lesson"] = True
        
        elif event_type == "quiz_completed":
            if event_data.get("score", 0) == 100:
                progress_updates["perfect_quiz_streak"] = event_data.get("perfect_streak", 0)
        
        elif event_type == "paper_trade_completed":
            progress_updates["paper_trades_completed"] = event_data.get("total_paper_trades", 0)
            progress_updates["paper_win_rate"] = event_data.get("win_rate", 0)
            
            if "strategy" in event_data:
                current_strategies = progress_updates.get("unique_strategies_tested", [])
                if event_data["strategy"] not in current_strategies:
                    current_strategies.append(event_data["strategy"])
                    progress_updates["unique_strategies_tested"] = len(current_strategies)
        
        elif event_type == "real_trade_completed":
            progress_updates["total_trades"] = event_data.get("total_trades", 0)
            progress_updates["win_rate"] = event_data.get("win_rate", 0)
            
            if event_data.get("profitable", False):
                progress_updates["profitable_trades"] = event_data.get("profitable_trades", 0)
            
            # Check for streaks
            if "current_streak" in event_data:
                progress_updates["win_streak"] = event_data["current_streak"]
            
            # Check for special conditions
            if event_data.get("pnl") == 0.01:
                progress_updates["penny_profit"] = True
            elif event_data.get("pnl") == 777.77:
                progress_updates["lucky_profit"] = 777.77
        
        elif event_type == "daily_login":
            progress_updates["login_streak"] = event_data.get("streak", 0)
            
            # Check for special times
            hour = datetime.utcnow().hour
            if 0 <= hour < 6:
                progress_updates["night_lessons"] = event_data.get("night_activities", 0)
            elif 5 <= hour < 7:
                progress_updates["early_lessons"] = event_data.get("early_activities", 0)
        
        # Update progress and check for unlocks
        if progress_updates:
            unlocked = await self.update_progress(user_id, progress_updates)
            
            # Check for achievement hunter rewards
            if unlocked:
                await self.check_achievement_hunter_rewards(user_id)
            
            return unlocked
        
        return []