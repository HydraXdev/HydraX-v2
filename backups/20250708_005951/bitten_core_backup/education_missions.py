"""
Education Missions System - Gaming-Style Trading Education
Inspired by Apex Legends, Warzone mission structure with story-driven content
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from src.bitten_core.database import Database
from src.bitten_core.logger import Logger
from src.bitten_core.xp_calculator import XPCalculator
from src.bitten_core.reward_system import RewardSystem


class MissionType(Enum):
    """Mission types inspired by FPS games"""
    STORY = "story"  # Story-driven campaign missions
    SURVIVAL = "survival"  # Market crash survival scenarios
    HUNT = "hunt"  # Pattern recognition challenges
    BOOTCAMP = "bootcamp"  # Risk management training
    SQUAD = "squad"  # Group learning missions
    DAILY = "daily"  # Daily challenges
    WEEKLY = "weekly"  # Weekly operations
    SPECIAL = "special"  # Limited-time events


class MissionDifficulty(Enum):
    """Dynamic difficulty levels"""
    RECRUIT = 1  # Beginner
    REGULAR = 2  # Normal
    HARDENED = 3  # Hard
    VETERAN = 4  # Very Hard
    LEGENDARY = 5  # Extreme


class MissionStatus(Enum):
    """Mission progress states"""
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class MissionObjective:
    """Individual mission objectives"""
    id: str
    description: str
    target_value: float
    current_value: float = 0.0
    is_bonus: bool = False
    xp_reward: int = 0
    completed: bool = False
    
    def check_completion(self) -> bool:
        """Check if objective is completed"""
        self.completed = self.current_value >= self.target_value
        return self.completed


@dataclass
class Mission:
    """Gaming-style mission structure"""
    mission_id: str
    type: MissionType
    title: str
    briefing: str  # Mission story/context
    difficulty: MissionDifficulty
    objectives: List[MissionObjective]
    bonus_objectives: List[MissionObjective] = field(default_factory=list)
    xp_reward: int = 100
    bonus_xp: int = 50
    time_limit: Optional[timedelta] = None
    squad_size: int = 1  # 1 for solo, >1 for squad missions
    prerequisites: List[str] = field(default_factory=list)
    story_dialogue: Dict[str, str] = field(default_factory=dict)
    completion_rate: float = 0.0
    status: MissionStatus = MissionStatus.AVAILABLE
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def is_squad_mission(self) -> bool:
        return self.squad_size > 1
    
    @property
    def total_xp_possible(self) -> int:
        """Calculate total possible XP including bonuses"""
        base = self.xp_reward
        for obj in self.objectives + self.bonus_objectives:
            base += obj.xp_reward
        return base + self.bonus_xp
    
    def check_time_limit(self) -> bool:
        """Check if mission has expired"""
        if not self.time_limit or not self.started_at:
            return True
        return datetime.utcnow() - self.started_at < self.time_limit


@dataclass
class MissionProgress:
    """Track user progress in missions"""
    user_id: str
    mission_id: str
    status: MissionStatus
    objectives_completed: List[str] = field(default_factory=list)
    bonus_objectives_completed: List[str] = field(default_factory=list)
    attempts: int = 0
    best_score: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    squad_members: List[str] = field(default_factory=list)


class EducationMissions:
    """Gaming-style education missions system"""
    
    def __init__(self, database: Database, logger: Logger, xp_calculator: XPCalculator, reward_system: RewardSystem):
        self.db = database
        self.logger = logger
        self.xp_calc = xp_calculator
        self.reward_system = reward_system
        
        # Mission catalog
        self.missions: Dict[str, Mission] = {}
        
        # User progress tracking
        self.user_progress: Dict[str, Dict[str, MissionProgress]] = defaultdict(dict)
        
        # Squad tracking for multiplayer missions
        self.active_squads: Dict[str, List[str]] = {}
        
        # Dynamic difficulty adjustment
        self.user_skill_ratings: Dict[str, float] = {}
        
        # Initialize missions
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize mission system"""
        await self._create_database_tables()
        await self._load_mission_catalog()
        await self._load_user_progress()
    
    async def _create_database_tables(self):
        """Create mission-related database tables"""
        try:
            # Mission progress table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS mission_progress (
                    user_id TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    objectives_data TEXT,
                    attempts INTEGER DEFAULT 0,
                    best_score REAL DEFAULT 0.0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    squad_members TEXT,
                    PRIMARY KEY (user_id, mission_id)
                )
            """)
            
            # Mission completion history
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS mission_history (
                    history_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    completion_time REAL,
                    xp_earned INTEGER,
                    objectives_completed INTEGER,
                    bonus_completed INTEGER,
                    difficulty INTEGER,
                    squad_members TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User skill ratings for dynamic difficulty
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS user_skill_ratings (
                    user_id TEXT PRIMARY KEY,
                    overall_rating REAL DEFAULT 1000.0,
                    story_rating REAL DEFAULT 1000.0,
                    survival_rating REAL DEFAULT 1000.0,
                    hunt_rating REAL DEFAULT 1000.0,
                    bootcamp_rating REAL DEFAULT 1000.0,
                    games_played INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.logger.info("Education missions database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize missions database: {e}")
    
    async def _load_mission_catalog(self):
        """Load all available missions"""
        # Story Campaign Missions
        self.missions.update(self._create_story_missions())
        
        # Survival Missions
        self.missions.update(self._create_survival_missions())
        
        # Hunt Missions
        self.missions.update(self._create_hunt_missions())
        
        # Bootcamp Missions
        self.missions.update(self._create_bootcamp_missions())
        
        # Squad Missions
        self.missions.update(self._create_squad_missions())
        
        self.logger.info(f"Loaded {len(self.missions)} missions")
    
    def _create_story_missions(self) -> Dict[str, Mission]:
        """Create story-driven campaign missions"""
        missions = {}
        
        # Chapter 1: The Rookie Trader
        missions["story_1_1"] = Mission(
            mission_id="story_1_1",
            type=MissionType.STORY,
            title="Episode 1: First Blood",
            briefing="""
Welcome to the trading battlefield, Recruit. I'm Commander Bit, and I'll be your guide through this warzone we call the markets.

Your first mission is simple: survive your first trade and live to tell the tale. The markets don't care about your feelings, your rent money, or your dreams. They only respect discipline and skill.

Today, you'll learn the most important rule of trading: protect your capital at all costs. Without ammo, you can't fight. Without capital, you can't trade.
            """,
            difficulty=MissionDifficulty.RECRUIT,
            objectives=[
                MissionObjective(
                    id="place_first_trade",
                    description="Place your first trade with proper stop loss",
                    target_value=1,
                    xp_reward=50
                ),
                MissionObjective(
                    id="risk_management",
                    description="Risk no more than 1% of your account",
                    target_value=1,
                    xp_reward=100
                ),
                MissionObjective(
                    id="exit_discipline",
                    description="Exit at your predetermined level (win or loss)",
                    target_value=1,
                    xp_reward=75
                )
            ],
            bonus_objectives=[
                MissionObjective(
                    id="profit_bonus",
                    description="Close the trade with profit",
                    target_value=1,
                    is_bonus=True,
                    xp_reward=50
                ),
                MissionObjective(
                    id="journal_entry",
                    description="Document your trade reasoning",
                    target_value=1,
                    is_bonus=True,
                    xp_reward=25
                )
            ],
            xp_reward=200,
            bonus_xp=75,
            story_dialogue={
                "intro": "Every legend starts somewhere. Today, you take your first shot.",
                "success": "Not bad, Rookie. You followed orders and survived. That's more than most can say on day one.",
                "failure": "The markets claimed another victim. Learn from this and try again."
            }
        )
        
        missions["story_1_2"] = Mission(
            mission_id="story_1_2",
            type=MissionType.STORY,
            title="Episode 2: The Sniper's Patience",
            briefing="""
Good to see you survived your first encounter. Now it's time to learn what separates the pros from the cannon fodder: patience.

A sniper doesn't fire at every movement. They wait for the perfect shot. In trading, we call these 'A+ setups'. Everything else is noise designed to separate you from your money.

Your mission: demonstrate the discipline to wait for quality over quantity.
            """,
            difficulty=MissionDifficulty.RECRUIT,
            objectives=[
                MissionObjective(
                    id="identify_setups",
                    description="Identify 3 A+ setups without trading",
                    target_value=3,
                    xp_reward=75
                ),
                MissionObjective(
                    id="avoid_fomo",
                    description="Pass on 5 marginal setups",
                    target_value=5,
                    xp_reward=100
                ),
                MissionObjective(
                    id="execute_quality",
                    description="Execute 1 high-quality trade",
                    target_value=1,
                    xp_reward=150
                )
            ],
            bonus_objectives=[
                MissionObjective(
                    id="document_passed",
                    description="Document why you passed on trades",
                    target_value=3,
                    is_bonus=True,
                    xp_reward=50
                )
            ],
            prerequisites=["story_1_1"],
            xp_reward=300,
            bonus_xp=50
        )
        
        missions["story_1_3"] = Mission(
            mission_id="story_1_3",
            type=MissionType.STORY,
            title="Episode 3: When Markets Attack",
            briefing="""
The markets have teeth, Recruit. Today you'll learn what happens when trades go against you. It's not about avoiding losses - that's impossible. It's about controlling them.

I've seen too many good traders become corpses because they couldn't accept a small loss. Their ego wrote checks their account couldn't cash.

Your mission: face adversity and prove you can take a hit without losing your mind.
            """,
            difficulty=MissionDifficulty.REGULAR,
            objectives=[
                MissionObjective(
                    id="stop_loss_execution",
                    description="Let a stop loss execute without interference",
                    target_value=1,
                    xp_reward=200
                ),
                MissionObjective(
                    id="no_revenge",
                    description="Avoid revenge trading after a loss",
                    target_value=1,
                    xp_reward=150
                ),
                MissionObjective(
                    id="loss_analysis",
                    description="Complete post-loss analysis",
                    target_value=1,
                    xp_reward=100
                )
            ],
            prerequisites=["story_1_2"],
            xp_reward=400,
            time_limit=timedelta(days=7)
        )
        
        return missions
    
    def _create_survival_missions(self) -> Dict[str, Mission]:
        """Create market crash survival scenarios"""
        missions = {}
        
        missions["survival_crash_1"] = Mission(
            mission_id="survival_crash_1",
            type=MissionType.SURVIVAL,
            title="Black Monday Simulator",
            briefing="""
EMERGENCY BROADCAST: Markets are in freefall. Panic selling has triggered a cascade of stop losses. Your mission is simple: SURVIVE.

This simulation recreates the chaos of a major market crash. You'll need to:
- Protect your capital
- Identify safe havens
- Avoid the falling knives
- Keep your cool while others panic

Remember: In a crash, cash is king and survival is victory.
            """,
            difficulty=MissionDifficulty.HARDENED,
            objectives=[
                MissionObjective(
                    id="capital_preservation",
                    description="Preserve 90% of starting capital",
                    target_value=0.90,
                    xp_reward=300
                ),
                MissionObjective(
                    id="avoid_knives",
                    description="Avoid catching falling knives (0 bottom fishing)",
                    target_value=0,
                    xp_reward=200
                ),
                MissionObjective(
                    id="safe_haven",
                    description="Identify and use 1 safe haven asset",
                    target_value=1,
                    xp_reward=150
                )
            ],
            bonus_objectives=[
                MissionObjective(
                    id="profit_chaos",
                    description="Profit from volatility (short or hedge)",
                    target_value=1,
                    is_bonus=True,
                    xp_reward=200
                )
            ],
            xp_reward=500,
            bonus_xp=200,
            time_limit=timedelta(hours=4)
        )
        
        missions["survival_whipsaw"] = Mission(
            mission_id="survival_whipsaw",
            type=MissionType.SURVIVAL,
            title="Whipsaw Wasteland",
            briefing="""
The market's turned into a meat grinder. Every breakout is a fakeout. Every support becomes resistance. This is where traders come to die.

Your mission: Navigate the whipsaw without getting chopped up. Trust nothing, verify everything, and keep your position sizes small.
            """,
            difficulty=MissionDifficulty.VETERAN,
            objectives=[
                MissionObjective(
                    id="avoid_fakeouts",
                    description="Identify 3 false breakouts before entry",
                    target_value=3,
                    xp_reward=200
                ),
                MissionObjective(
                    id="position_control",
                    description="Keep all positions under 0.5% risk",
                    target_value=1,
                    xp_reward=150
                ),
                MissionObjective(
                    id="win_rate",
                    description="Maintain 50%+ win rate in chaos",
                    target_value=0.50,
                    xp_reward=250
                )
            ],
            xp_reward=450,
            time_limit=timedelta(hours=6)
        )
        
        return missions
    
    def _create_hunt_missions(self) -> Dict[str, Mission]:
        """Create pattern recognition challenges"""
        missions = {}
        
        missions["hunt_breakout_1"] = Mission(
            mission_id="hunt_breakout_1",
            type=MissionType.HUNT,
            title="Breakout Hunter: Dawn Patrol",
            briefing="""
Time to hunt, soldier. Your prey: breakout patterns. They're elusive, often false, but when you catch a real one, the rewards are substantial.

Your hunting grounds: major currency pairs during the London-NY overlap. Your weapons: volume analysis and price action. Your mission: bag three confirmed breakouts.

Remember: patience and precision. One clean shot beats ten wild sprays.
            """,
            difficulty=MissionDifficulty.REGULAR,
            objectives=[
                MissionObjective(
                    id="identify_patterns",
                    description="Identify 5 potential breakout setups",
                    target_value=5,
                    xp_reward=100
                ),
                MissionObjective(
                    id="confirm_volume",
                    description="Confirm 3 with volume analysis",
                    target_value=3,
                    xp_reward=150
                ),
                MissionObjective(
                    id="successful_trades",
                    description="Execute 2 profitable breakout trades",
                    target_value=2,
                    xp_reward=200
                )
            ],
            bonus_objectives=[
                MissionObjective(
                    id="risk_reward",
                    description="Achieve 3:1 risk/reward on a trade",
                    target_value=3.0,
                    is_bonus=True,
                    xp_reward=100
                )
            ],
            xp_reward=350,
            bonus_xp=100
        )
        
        missions["hunt_reversal_1"] = Mission(
            mission_id="hunt_reversal_1",
            type=MissionType.HUNT,
            title="Reversal Recon",
            briefing="""
New targets, Hunter. We're tracking reversal patterns at key levels. These are dangerous prey - many traders get gored trying to catch them. But with proper technique, they're highly rewarding.

Use multiple confluences: support/resistance, divergences, and market structure. One indicator is a guess. Three indicators is a thesis.
            """,
            difficulty=MissionDifficulty.HARDENED,
            objectives=[
                MissionObjective(
                    id="identify_levels",
                    description="Map 5 key reversal levels",
                    target_value=5,
                    xp_reward=100
                ),
                MissionObjective(
                    id="spot_divergence",
                    description="Identify 3 momentum divergences",
                    target_value=3,
                    xp_reward=150
                ),
                MissionObjective(
                    id="execute_reversal",
                    description="Successfully trade 1 major reversal",
                    target_value=1,
                    xp_reward=250
                )
            ],
            xp_reward=400
        )
        
        return missions
    
    def _create_bootcamp_missions(self) -> Dict[str, Mission]:
        """Create risk management training missions"""
        missions = {}
        
        missions["bootcamp_risk_1"] = Mission(
            mission_id="bootcamp_risk_1",
            type=MissionType.BOOTCAMP,
            title="Risk Management: Basic Training",
            briefing="""
Listen up, Maggot! This is Risk Management Bootcamp. Here, we separate the future millionaires from the future homeless.

You will learn to calculate position sizes in your sleep. You will never risk more than you can afford to lose. And you will ALWAYS use a stop loss.

Drop and give me twenty... profitable trades with proper risk management!
            """,
            difficulty=MissionDifficulty.RECRUIT,
            objectives=[
                MissionObjective(
                    id="position_calc",
                    description="Calculate position sizes for 10 scenarios",
                    target_value=10,
                    xp_reward=100
                ),
                MissionObjective(
                    id="risk_limit",
                    description="Complete 5 trades with <1% risk each",
                    target_value=5,
                    xp_reward=150
                ),
                MissionObjective(
                    id="stop_discipline",
                    description="Honor all stop losses (no manual closes)",
                    target_value=1,
                    xp_reward=200
                )
            ],
            xp_reward=300,
            story_dialogue={
                "success": "Outstanding, Soldier! You might just survive this market after all.",
                "failure": "Pathetic! The market would eat you alive. Try again!"
            }
        )
        
        missions["bootcamp_psychology"] = Mission(
            mission_id="bootcamp_psychology",
            type=MissionType.BOOTCAMP,
            title="Mental Warfare Training",
            briefing="""
The greatest enemy you'll face isn't the market - it's the trader in the mirror. Fear, greed, hope, and revenge will kill your account faster than any bad strategy.

This course will test your mental fortitude. You'll face your demons and learn to trade like a machine, not a monkey.
            """,
            difficulty=MissionDifficulty.HARDENED,
            objectives=[
                MissionObjective(
                    id="fear_control",
                    description="Take a valid trade after 2 losses",
                    target_value=1,
                    xp_reward=200
                ),
                MissionObjective(
                    id="greed_control",
                    description="Exit at target (not hoping for more) 3 times",
                    target_value=3,
                    xp_reward=200
                ),
                MissionObjective(
                    id="revenge_avoid",
                    description="Wait 30min after any loss before next trade",
                    target_value=5,
                    xp_reward=150
                )
            ],
            xp_reward=400
        )
        
        return missions
    
    def _create_squad_missions(self) -> Dict[str, Mission]:
        """Create multiplayer squad missions"""
        missions = {}
        
        missions["squad_coordination_1"] = Mission(
            mission_id="squad_coordination_1",
            type=MissionType.SQUAD,
            title="Squad Tactics: Market Reconnaissance",
            briefing="""
No trader is an island. Today you'll learn to work as a unit. Your squad will scout different markets and share intelligence to identify the best opportunities.

Communication is key. Share your analysis, confirm each other's setups, and watch each other's backs. One person's blind spot is another's clear view.
            """,
            difficulty=MissionDifficulty.REGULAR,
            squad_size=3,
            objectives=[
                MissionObjective(
                    id="market_coverage",
                    description="Squad covers 10 different markets",
                    target_value=10,
                    xp_reward=200
                ),
                MissionObjective(
                    id="setup_confirmation",
                    description="Confirm 5 setups as a team",
                    target_value=5,
                    xp_reward=150
                ),
                MissionObjective(
                    id="profitable_collaboration",
                    description="Each member profits from shared intel",
                    target_value=3,
                    xp_reward=300
                )
            ],
            bonus_objectives=[
                MissionObjective(
                    id="perfect_sync",
                    description="All members profit on same trade",
                    target_value=1,
                    is_bonus=True,
                    xp_reward=200
                )
            ],
            xp_reward=500,
            bonus_xp=200
        )
        
        missions["squad_competition"] = Mission(
            mission_id="squad_competition",
            type=MissionType.SQUAD,
            title="Squad Wars: Trading Tournament",
            briefing="""
Time for some friendly competition. Squads will compete in a trading tournament with a twist - your squad's success depends on EVERYONE performing well.

Weakest link scoring: Your squad score is based on your lowest performer. Help each other, share strategies, and ensure no one gets left behind.
            """,
            difficulty=MissionDifficulty.VETERAN,
            squad_size=4,
            objectives=[
                MissionObjective(
                    id="min_performance",
                    description="All members achieve 40%+ win rate",
                    target_value=0.40,
                    xp_reward=300
                ),
                MissionObjective(
                    id="risk_discipline",
                    description="No member exceeds 2% risk per trade",
                    target_value=1,
                    xp_reward=200
                ),
                MissionObjective(
                    id="profit_target",
                    description="Squad achieves collective 5% gain",
                    target_value=0.05,
                    xp_reward=400
                )
            ],
            xp_reward=600,
            time_limit=timedelta(days=3)
        )
        
        return missions
    
    async def _load_user_progress(self):
        """Load user progress from database"""
        try:
            progress_data = await self.db.fetch_all("""
                SELECT user_id, mission_id, status, objectives_data, 
                       attempts, best_score, started_at, completed_at, squad_members
                FROM mission_progress
            """)
            
            for row in progress_data:
                user_id = row['user_id']
                mission_id = row['mission_id']
                
                progress = MissionProgress(
                    user_id=user_id,
                    mission_id=mission_id,
                    status=MissionStatus(row['status']),
                    attempts=row['attempts'],
                    best_score=row['best_score'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at']
                )
                
                if row['objectives_data']:
                    obj_data = json.loads(row['objectives_data'])
                    progress.objectives_completed = obj_data.get('completed', [])
                    progress.bonus_objectives_completed = obj_data.get('bonus_completed', [])
                
                if row['squad_members']:
                    progress.squad_members = json.loads(row['squad_members'])
                
                self.user_progress[user_id][mission_id] = progress
            
        except Exception as e:
            self.logger.error(f"Failed to load user progress: {e}")
    
    async def get_available_missions(self, user_id: str) -> List[Mission]:
        """Get missions available to a user based on their progress"""
        available = []
        user_skill = await self._get_user_skill_rating(user_id)
        
        for mission in self.missions.values():
            # Check if mission is locked by prerequisites
            if mission.prerequisites:
                prereqs_met = all(
                    self.user_progress.get(user_id, {}).get(prereq, MissionProgress(
                        user_id=user_id,
                        mission_id=prereq,
                        status=MissionStatus.LOCKED
                    )).status == MissionStatus.COMPLETED
                    for prereq in mission.prerequisites
                )
                if not prereqs_met:
                    continue
            
            # Check if already completed (except repeatable missions)
            user_mission_progress = self.user_progress.get(user_id, {}).get(mission.mission_id)
            if user_mission_progress and user_mission_progress.status == MissionStatus.COMPLETED:
                if mission.type not in [MissionType.DAILY, MissionType.WEEKLY, MissionType.SURVIVAL]:
                    continue
            
            # Adjust difficulty based on user skill
            if await self._is_appropriate_difficulty(mission.difficulty, user_skill):
                available.append(mission)
        
        return available
    
    async def _get_user_skill_rating(self, user_id: str) -> float:
        """Get user's skill rating for dynamic difficulty"""
        if user_id in self.user_skill_ratings:
            return self.user_skill_ratings[user_id]
        
        # Load from database
        rating_data = await self.db.fetch_one(
            "SELECT overall_rating FROM user_skill_ratings WHERE user_id = ?",
            (user_id,)
        )
        
        if rating_data:
            self.user_skill_ratings[user_id] = rating_data['overall_rating']
            return rating_data['overall_rating']
        
        # New user starts at 1000 (like ELO)
        self.user_skill_ratings[user_id] = 1000.0
        await self.db.execute(
            "INSERT INTO user_skill_ratings (user_id) VALUES (?)",
            (user_id,)
        )
        return 1000.0
    
    async def _is_appropriate_difficulty(self, mission_difficulty: MissionDifficulty, user_skill: float) -> bool:
        """Check if mission difficulty is appropriate for user skill"""
        skill_ranges = {
            MissionDifficulty.RECRUIT: (0, 1200),
            MissionDifficulty.REGULAR: (800, 1400),
            MissionDifficulty.HARDENED: (1200, 1800),
            MissionDifficulty.VETERAN: (1600, 2200),
            MissionDifficulty.LEGENDARY: (2000, float('inf'))
        }
        
        min_skill, max_skill = skill_ranges[mission_difficulty]
        return min_skill <= user_skill <= max_skill
    
    async def start_mission(self, user_id: str, mission_id: str, squad_members: Optional[List[str]] = None) -> Dict[str, Any]:
        """Start a mission for a user"""
        mission = self.missions.get(mission_id)
        if not mission:
            return {"success": False, "error": "Mission not found"}
        
        # Check prerequisites
        if mission.prerequisites:
            for prereq in mission.prerequisites:
                prereq_progress = self.user_progress.get(user_id, {}).get(prereq)
                if not prereq_progress or prereq_progress.status != MissionStatus.COMPLETED:
                    return {"success": False, "error": f"Prerequisite mission {prereq} not completed"}
        
        # Check squad requirements
        if mission.is_squad_mission:
            if not squad_members or len(squad_members) < mission.squad_size - 1:
                return {
                    "success": False, 
                    "error": f"Squad mission requires {mission.squad_size} members total"
                }
            
            # Create squad
            squad_id = f"squad_{mission_id}_{datetime.utcnow().timestamp()}"
            self.active_squads[squad_id] = [user_id] + squad_members
        
        # Create or update progress
        progress = MissionProgress(
            user_id=user_id,
            mission_id=mission_id,
            status=MissionStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            squad_members=squad_members or []
        )
        
        self.user_progress[user_id][mission_id] = progress
        
        # Save to database
        await self._save_progress(progress)
        
        # Return mission briefing
        return {
            "success": True,
            "mission": mission,
            "dialogue": mission.story_dialogue.get("intro", mission.briefing),
            "objectives": [
                {
                    "id": obj.id,
                    "description": obj.description,
                    "target": obj.target_value,
                    "is_bonus": obj.is_bonus,
                    "xp_reward": obj.xp_reward
                }
                for obj in mission.objectives + mission.bonus_objectives
            ]
        }
    
    async def update_mission_progress(self, user_id: str, mission_id: str, objective_id: str, value: float) -> Dict[str, Any]:
        """Update progress on a mission objective"""
        mission = self.missions.get(mission_id)
        if not mission:
            return {"success": False, "error": "Mission not found"}
        
        progress = self.user_progress.get(user_id, {}).get(mission_id)
        if not progress or progress.status != MissionStatus.IN_PROGRESS:
            return {"success": False, "error": "Mission not in progress"}
        
        # Check time limit
        if not mission.check_time_limit():
            await self._fail_mission(user_id, mission_id, "Time limit exceeded")
            return {"success": False, "error": "Mission time limit exceeded"}
        
        # Find and update objective
        all_objectives = mission.objectives + mission.bonus_objectives
        objective = next((obj for obj in all_objectives if obj.id == objective_id), None)
        
        if not objective:
            return {"success": False, "error": "Objective not found"}
        
        # Update objective progress
        objective.current_value = value
        was_completed = objective.completed
        is_completed = objective.check_completion()
        
        # Track completion
        if is_completed and not was_completed:
            if objective.is_bonus:
                progress.bonus_objectives_completed.append(objective_id)
            else:
                progress.objectives_completed.append(objective_id)
        
        # Check mission completion
        main_objectives_complete = all(
            obj.id in progress.objectives_completed 
            for obj in mission.objectives
        )
        
        if main_objectives_complete:
            await self._complete_mission(user_id, mission_id)
            return {
                "success": True,
                "mission_complete": True,
                "rewards": await self._calculate_mission_rewards(user_id, mission, progress)
            }
        
        # Save progress
        await self._save_progress(progress)
        
        return {
            "success": True,
            "objective_complete": is_completed,
            "progress": {
                "completed": len(progress.objectives_completed),
                "total": len(mission.objectives),
                "bonus_completed": len(progress.bonus_objectives_completed)
            }
        }
    
    async def _complete_mission(self, user_id: str, mission_id: str):
        """Mark mission as completed and award rewards"""
        mission = self.missions[mission_id]
        progress = self.user_progress[user_id][mission_id]
        
        progress.status = MissionStatus.COMPLETED
        progress.completed_at = datetime.utcnow()
        
        # Calculate completion time
        completion_time = (progress.completed_at - progress.started_at).total_seconds()
        
        # Award XP
        rewards = await self._calculate_mission_rewards(user_id, mission, progress)
        total_xp = rewards['total_xp']
        
        # Update user skill rating
        await self._update_skill_rating(user_id, mission, True)
        
        # Save to history
        await self.db.execute("""
            INSERT INTO mission_history 
            (history_id, user_id, mission_id, completion_time, xp_earned,
             objectives_completed, bonus_completed, difficulty, squad_members)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"history_{mission_id}_{user_id}_{datetime.utcnow().timestamp()}",
            user_id, mission_id, completion_time, total_xp,
            len(progress.objectives_completed),
            len(progress.bonus_objectives_completed),
            mission.difficulty.value,
            json.dumps(progress.squad_members) if progress.squad_members else None
        ))
        
        # Update progress
        await self._save_progress(progress)
        
        # Trigger celebration
        self.logger.info(f"User {user_id} completed mission {mission_id} earning {total_xp} XP")
    
    async def _fail_mission(self, user_id: str, mission_id: str, reason: str):
        """Mark mission as failed"""
        progress = self.user_progress[user_id][mission_id]
        progress.status = MissionStatus.FAILED
        
        # Update skill rating (decrease for failure)
        mission = self.missions[mission_id]
        await self._update_skill_rating(user_id, mission, False)
        
        await self._save_progress(progress)
        
        self.logger.info(f"User {user_id} failed mission {mission_id}: {reason}")
    
    async def _calculate_mission_rewards(self, user_id: str, mission: Mission, progress: MissionProgress) -> Dict[str, Any]:
        """Calculate rewards for mission completion"""
        base_xp = mission.xp_reward
        
        # Add objective XP
        objective_xp = sum(
            obj.xp_reward 
            for obj in mission.objectives 
            if obj.id in progress.objectives_completed
        )
        
        # Add bonus objective XP
        bonus_xp = sum(
            obj.xp_reward 
            for obj in mission.bonus_objectives 
            if obj.id in progress.bonus_objectives_completed
        )
        
        # Perfect completion bonus
        perfect_bonus = 0
        if len(progress.bonus_objectives_completed) == len(mission.bonus_objectives):
            perfect_bonus = mission.bonus_xp
        
        # Difficulty multiplier
        difficulty_multiplier = mission.difficulty.value * 0.5
        
        total_xp = int((base_xp + objective_xp + bonus_xp + perfect_bonus) * difficulty_multiplier)
        
        return {
            "base_xp": base_xp,
            "objective_xp": objective_xp,
            "bonus_xp": bonus_xp,
            "perfect_bonus": perfect_bonus,
            "difficulty_multiplier": difficulty_multiplier,
            "total_xp": total_xp
        }
    
    async def _update_skill_rating(self, user_id: str, mission: Mission, success: bool):
        """Update user skill rating based on mission performance"""
        current_rating = await self._get_user_skill_rating(user_id)
        
        # Expected performance based on mission difficulty
        mission_rating = 1000 + (mission.difficulty.value - 1) * 200
        expected_score = 1 / (1 + 10 ** ((mission_rating - current_rating) / 400))
        
        # Actual score (1 for success, 0 for failure)
        actual_score = 1 if success else 0
        
        # ELO-style rating update
        k_factor = 32  # Learning rate
        rating_change = k_factor * (actual_score - expected_score)
        
        new_rating = current_rating + rating_change
        self.user_skill_ratings[user_id] = new_rating
        
        # Update database
        await self.db.execute("""
            UPDATE user_skill_ratings 
            SET overall_rating = ?, games_played = games_played + 1, last_updated = ?
            WHERE user_id = ?
        """, (new_rating, datetime.utcnow(), user_id))
    
    async def _save_progress(self, progress: MissionProgress):
        """Save mission progress to database"""
        objectives_data = json.dumps({
            "completed": progress.objectives_completed,
            "bonus_completed": progress.bonus_objectives_completed
        })
        
        await self.db.execute("""
            INSERT INTO mission_progress 
            (user_id, mission_id, status, objectives_data, attempts, 
             best_score, started_at, completed_at, squad_members)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, mission_id) DO UPDATE SET
                status = excluded.status,
                objectives_data = excluded.objectives_data,
                attempts = excluded.attempts,
                best_score = excluded.best_score,
                completed_at = excluded.completed_at
        """, (
            progress.user_id, progress.mission_id, progress.status.value,
            objectives_data, progress.attempts, progress.best_score,
            progress.started_at, progress.completed_at,
            json.dumps(progress.squad_members) if progress.squad_members else None
        ))
    
    async def get_mission_leaderboard(self, mission_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for a specific mission"""
        results = await self.db.fetch_all("""
            SELECT user_id, completion_time, xp_earned, difficulty, created_at
            FROM mission_history
            WHERE mission_id = ?
            ORDER BY completion_time ASC, xp_earned DESC
            LIMIT ?
        """, (mission_id, limit))
        
        leaderboard = []
        for i, row in enumerate(results):
            leaderboard.append({
                "rank": i + 1,
                "user_id": row['user_id'],
                "completion_time": row['completion_time'],
                "xp_earned": row['xp_earned'],
                "difficulty": row['difficulty'],
                "completed_at": row['created_at']
            })
        
        return leaderboard
    
    async def get_user_mission_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive mission statistics for a user"""
        # Overall stats
        total_completed = await self.db.fetch_one("""
            SELECT COUNT(*) as count, SUM(xp_earned) as total_xp
            FROM mission_history
            WHERE user_id = ?
        """, (user_id,))
        
        # By mission type
        type_stats = await self.db.fetch_all("""
            SELECT m.type, COUNT(*) as completed, AVG(h.completion_time) as avg_time
            FROM mission_history h
            JOIN missions m ON h.mission_id = m.mission_id
            WHERE h.user_id = ?
            GROUP BY m.type
        """, (user_id,))
        
        # Current skill rating
        skill_rating = await self._get_user_skill_rating(user_id)
        
        # Active missions
        active_missions = [
            progress 
            for progress in self.user_progress.get(user_id, {}).values()
            if progress.status == MissionStatus.IN_PROGRESS
        ]
        
        return {
            "total_completed": total_completed['count'] or 0,
            "total_xp_earned": total_completed['total_xp'] or 0,
            "skill_rating": skill_rating,
            "type_breakdown": {
                row['type']: {
                    "completed": row['completed'],
                    "avg_completion_time": row['avg_time']
                }
                for row in type_stats
            },
            "active_missions": len(active_missions),
            "available_missions": len(await self.get_available_missions(user_id))
        }
    
    async def generate_daily_missions(self):
        """Generate daily challenge missions"""
        # This would be called by a scheduler to create fresh daily missions
        daily_challenges = [
            {
                "title": "Sharp Shooter",
                "objective": "Achieve 80% win rate with minimum 5 trades",
                "xp": 200
            },
            {
                "title": "Risk Discipline",
                "objective": "Complete 10 trades without exceeding 1% risk",
                "xp": 150
            },
            {
                "title": "Pattern Hunter",
                "objective": "Identify and trade 3 different chart patterns",
                "xp": 250
            }
        ]
        
        for i, challenge in enumerate(daily_challenges):
            mission_id = f"daily_{datetime.utcnow().strftime('%Y%m%d')}_{i}"
            
            self.missions[mission_id] = Mission(
                mission_id=mission_id,
                type=MissionType.DAILY,
                title=f"Daily Challenge: {challenge['title']}",
                briefing=f"Today's challenge: {challenge['objective']}",
                difficulty=MissionDifficulty.REGULAR,
                objectives=[
                    MissionObjective(
                        id="daily_objective",
                        description=challenge['objective'],
                        target_value=1,
                        xp_reward=challenge['xp']
                    )
                ],
                xp_reward=challenge['xp'],
                time_limit=timedelta(days=1)
            )