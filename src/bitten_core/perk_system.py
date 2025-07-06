"""
BITTEN Perk Unlock System
Call of Duty-inspired perk system with meaningful choices and unique playstyles
"""

import json
import time
import sqlite3
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PerkBranch(Enum):
    """Perk tree branches"""
    TRADING = "TRADING"  # Trading perks (fees, spreads)
    ANALYSIS = "ANALYSIS"  # Analysis perks (signals, indicators)
    SOCIAL = "SOCIAL"  # Social perks (squad, mentor)
    ECONOMY = "ECONOMY"  # Economy perks (XP, rewards)


class PerkTier(Enum):
    """Perk tiers"""
    BASIC = 1  # Level 1-20
    ADVANCED = 2  # Level 21-50
    ELITE = 3  # Level 51-100
    LEGENDARY = 4  # Level 100+
    
    @property
    def min_level(self) -> int:
        """Get minimum level for tier"""
        tier_levels = {
            PerkTier.BASIC: 1,
            PerkTier.ADVANCED: 21,
            PerkTier.ELITE: 51,
            PerkTier.LEGENDARY: 101
        }
        return tier_levels[self]
    
    @property
    def point_cost(self) -> int:
        """Get point cost for perks in this tier"""
        tier_costs = {
            PerkTier.BASIC: 1,
            PerkTier.ADVANCED: 2,
            PerkTier.ELITE: 3,
            PerkTier.LEGENDARY: 5
        }
        return tier_costs[self]


class PerkType(Enum):
    """Perk activation types"""
    PASSIVE = "PASSIVE"  # Always active once unlocked
    ACTIVE = "ACTIVE"  # Must be equipped in loadout
    TRIGGERED = "TRIGGERED"  # Activates under conditions
    SEASONAL = "SEASONAL"  # Time-limited availability


@dataclass
class PerkEffect:
    """Defines a perk's effect"""
    effect_type: str  # fee_reduction, xp_multiplier, etc.
    value: float  # Effect magnitude
    description: str  # Human-readable description
    stacks: bool = False  # Can stack with similar effects
    max_stack: int = 1  # Maximum stack count


@dataclass
class Perk:
    """Defines a perk"""
    perk_id: str
    name: str
    description: str
    icon: str
    branch: PerkBranch
    tier: PerkTier
    perk_type: PerkType
    effects: List[PerkEffect]
    prerequisites: List[str] = field(default_factory=list)  # Required perk IDs
    synergies: List[str] = field(default_factory=list)  # Synergy perk IDs
    conflicts: List[str] = field(default_factory=list)  # Conflicting perk IDs
    max_rank: int = 1  # For multi-rank perks
    xp_requirement: int = 0  # Additional XP requirement
    achievement_requirement: Optional[str] = None  # Required achievement
    seasonal_end: Optional[datetime] = None  # For seasonal perks
    elite_only: bool = False  # Requires elite tier access


@dataclass
class PerkLoadout:
    """Player's active perk loadout"""
    loadout_id: str
    name: str
    active_perks: Dict[PerkBranch, str]  # Branch -> perk_id
    created_at: datetime
    last_modified: datetime
    is_active: bool = True


@dataclass
class PlayerPerkData:
    """Player's perk progression data"""
    user_id: int
    level: int
    available_points: int
    spent_points: int
    unlocked_perks: Dict[str, int]  # perk_id -> rank
    active_loadout: Optional[str] = None
    loadouts: List[PerkLoadout] = field(default_factory=list)
    respec_count: int = 0
    last_respec: Optional[datetime] = None
    seasonal_perks: List[str] = field(default_factory=list)


class PerkSystem:
    """Main perk system manager"""
    
    # Points earned per level
    POINTS_PER_LEVEL = 1
    BONUS_POINT_LEVELS = [10, 25, 50, 75, 100, 150, 200]  # Extra point at these levels
    
    # Respec costs
    BASE_RESPEC_COST = 1000  # Base XP cost
    RESPEC_MULTIPLIER = 2  # Cost multiplier per respec
    RESPEC_COOLDOWN_HOURS = 168  # 1 week
    
    # Synergy bonuses
    SYNERGY_BONUS = 0.1  # 10% bonus per synergy
    MAX_SYNERGY_BONUS = 0.5  # 50% max
    
    # Loadout limits
    MAX_LOADOUTS = 5
    MAX_ACTIVE_PERKS_PER_BRANCH = 1  # COD-style: one perk per category
    
    def __init__(self, db_path: str = "bitten_perks.db"):
        self.db_path = db_path
        self.perk_catalog = self._initialize_perk_catalog()
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Player perk data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_perks (
                user_id INTEGER PRIMARY KEY,
                level INTEGER DEFAULT 1,
                available_points INTEGER DEFAULT 0,
                spent_points INTEGER DEFAULT 0,
                unlocked_perks TEXT DEFAULT '{}',
                active_loadout TEXT,
                respec_count INTEGER DEFAULT 0,
                last_respec INTEGER,
                seasonal_perks TEXT DEFAULT '[]'
            )
        ''')
        
        # Perk loadouts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS perk_loadouts (
                loadout_id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                active_perks TEXT,
                created_at INTEGER,
                last_modified INTEGER,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES player_perks(user_id)
            )
        ''')
        
        # Perk usage analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS perk_analytics (
                user_id INTEGER,
                perk_id TEXT,
                times_equipped INTEGER DEFAULT 0,
                time_equipped INTEGER DEFAULT 0,
                last_equipped INTEGER,
                performance_delta REAL DEFAULT 0,
                PRIMARY KEY (user_id, perk_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _initialize_perk_catalog(self) -> Dict[str, Perk]:
        """Initialize the perk catalog"""
        catalog = {}
        
        # TRADING BRANCH PERKS
        
        # Basic Tier
        catalog["reduced_fees_1"] = Perk(
            perk_id="reduced_fees_1",
            name="Efficient Trader",
            description="Reduce trading fees by 10%",
            icon="💰",
            branch=PerkBranch.TRADING,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("fee_reduction", 0.10, "-10% trading fees")
            ],
            max_rank=3
        )
        
        catalog["better_spreads_1"] = Perk(
            perk_id="better_spreads_1",
            name="Spread Hunter",
            description="Get 5% better spreads on entries",
            icon="📊",
            branch=PerkBranch.TRADING,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("spread_improvement", 0.05, "+5% spread improvement")
            ]
        )
        
        # Advanced Tier
        catalog["quick_fingers"] = Perk(
            perk_id="quick_fingers",
            name="Quick Fingers",
            description="Execute trades 2x faster",
            icon="⚡",
            branch=PerkBranch.TRADING,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("execution_speed", 2.0, "2x faster execution")
            ],
            prerequisites=["reduced_fees_1"],
            synergies=["priority_signals"]
        )
        
        catalog["risk_shield"] = Perk(
            perk_id="risk_shield",
            name="Risk Shield",
            description="First loss of the day reduced by 50%",
            icon="🛡️",
            branch=PerkBranch.TRADING,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.TRIGGERED,
            effects=[
                PerkEffect("loss_reduction", 0.50, "-50% on first daily loss")
            ],
            xp_requirement=5000
        )
        
        # Elite Tier
        catalog["ghost_trades"] = Perk(
            perk_id="ghost_trades",
            name="Ghost Protocol",
            description="Hide your trades from squad radar",
            icon="👻",
            branch=PerkBranch.TRADING,
            tier=PerkTier.ELITE,
            perk_type=PerkType.ACTIVE,
            effects=[
                PerkEffect("trade_privacy", 1.0, "Trades hidden from radar")
            ],
            elite_only=True
        )
        
        catalog["double_tap"] = Perk(
            perk_id="double_tap",
            name="Double Tap",
            description="Can take same signal twice with 30min cooldown",
            icon="🎯",
            branch=PerkBranch.TRADING,
            tier=PerkTier.ELITE,
            perk_type=PerkType.ACTIVE,
            effects=[
                PerkEffect("signal_reuse", 1.0, "Reuse signals after 30min")
            ],
            prerequisites=["quick_fingers"],
            conflicts=["conservative_trader"]
        )
        
        # Legendary Tier
        catalog["market_oracle"] = Perk(
            perk_id="market_oracle",
            name="Market Oracle",
            description="See win probability 1hr before signal",
            icon="🔮",
            branch=PerkBranch.TRADING,
            tier=PerkTier.LEGENDARY,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("early_insight", 1.0, "1hr early win probability")
            ],
            xp_requirement=50000,
            achievement_requirement="legendary_sniper"
        )
        
        # ANALYSIS BRANCH PERKS
        
        # Basic Tier
        catalog["priority_signals"] = Perk(
            perk_id="priority_signals",
            name="Priority Access",
            description="Get signals 30 seconds early",
            icon="⏰",
            branch=PerkBranch.ANALYSIS,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("signal_priority", 30, "30s early signal access")
            ]
        )
        
        catalog["enhanced_indicators"] = Perk(
            perk_id="enhanced_indicators",
            name="Enhanced Vision",
            description="See additional technical indicators",
            icon="📈",
            branch=PerkBranch.ANALYSIS,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("extra_indicators", 3, "+3 technical indicators")
            ]
        )
        
        # Advanced Tier
        catalog["pattern_recognition"] = Perk(
            perk_id="pattern_recognition",
            name="Pattern Master",
            description="AI highlights similar historical setups",
            icon="🧠",
            branch=PerkBranch.ANALYSIS,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("pattern_analysis", 1.0, "Historical pattern matching")
            ],
            prerequisites=["enhanced_indicators"]
        )
        
        catalog["volatility_radar"] = Perk(
            perk_id="volatility_radar",
            name="Volatility Radar",
            description="Real-time volatility alerts",
            icon="📡",
            branch=PerkBranch.ANALYSIS,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.ACTIVE,
            effects=[
                PerkEffect("volatility_alerts", 1.0, "Live volatility tracking")
            ],
            synergies=["risk_shield"]
        )
        
        # Elite Tier
        catalog["quantum_analysis"] = Perk(
            perk_id="quantum_analysis",
            name="Quantum Analysis",
            description="Multi-timeframe confluence scoring",
            icon="⚛️",
            branch=PerkBranch.ANALYSIS,
            tier=PerkTier.ELITE,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("confluence_score", 1.0, "MTF confluence analysis")
            ],
            prerequisites=["pattern_recognition"],
            elite_only=True
        )
        
        # Legendary Tier
        catalog["prophet_mode"] = Perk(
            perk_id="prophet_mode",
            name="Prophet Mode",
            description="See next 3 signals with 70% accuracy",
            icon="👁️",
            branch=PerkBranch.ANALYSIS,
            tier=PerkTier.LEGENDARY,
            perk_type=PerkType.ACTIVE,
            effects=[
                PerkEffect("signal_prediction", 3, "Predict next 3 signals")
            ],
            xp_requirement=75000,
            conflicts=["market_oracle"]
        )
        
        # SOCIAL BRANCH PERKS
        
        # Basic Tier
        catalog["squad_synergy"] = Perk(
            perk_id="squad_synergy",
            name="Squad Synergy",
            description="+5% XP when squad member wins",
            icon="🤝",
            branch=PerkBranch.SOCIAL,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("squad_xp_bonus", 0.05, "+5% XP from squad wins")
            ],
            max_rank=3
        )
        
        catalog["mentor_bonus"] = Perk(
            perk_id="mentor_bonus",
            name="Mentor",
            description="+10% XP from recruit activities",
            icon="🎓",
            branch=PerkBranch.SOCIAL,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("recruit_xp_bonus", 0.10, "+10% XP from recruits")
            ]
        )
        
        # Advanced Tier
        catalog["rally_cry"] = Perk(
            perk_id="rally_cry",
            name="Rally Cry",
            description="Boost squad's next trade by 10% (1/day)",
            icon="📢",
            branch=PerkBranch.SOCIAL,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.ACTIVE,
            effects=[
                PerkEffect("squad_boost", 0.10, "+10% squad trade boost")
            ],
            prerequisites=["squad_synergy"]
        )
        
        catalog["trade_sharing"] = Perk(
            perk_id="trade_sharing",
            name="Trade Sync",
            description="Share trades instantly with squad",
            icon="🔄",
            branch=PerkBranch.SOCIAL,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("instant_share", 1.0, "Instant trade sharing")
            ],
            synergies=["squad_synergy"]
        )
        
        # Elite Tier
        catalog["squad_leader"] = Perk(
            perk_id="squad_leader",
            name="Squad Leader",
            description="Squad gets 20% of your win bonuses",
            icon="⭐",
            branch=PerkBranch.SOCIAL,
            tier=PerkTier.ELITE,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("squad_reward_share", 0.20, "Share 20% win bonus")
            ],
            prerequisites=["rally_cry"],
            elite_only=True
        )
        
        # Legendary Tier
        catalog["legacy_builder"] = Perk(
            perk_id="legacy_builder",
            name="Legacy Builder",
            description="Recruits start at level 5 with bonus gear",
            icon="👑",
            branch=PerkBranch.SOCIAL,
            tier=PerkTier.LEGENDARY,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("recruit_boost", 5, "Recruits start level 5")
            ],
            achievement_requirement="general"
        )
        
        # ECONOMY BRANCH PERKS
        
        # Basic Tier
        catalog["xp_boost_1"] = Perk(
            perk_id="xp_boost_1",
            name="Fast Learner",
            description="+15% XP from all sources",
            icon="📚",
            branch=PerkBranch.ECONOMY,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("xp_multiplier", 0.15, "+15% XP gain")
            ],
            max_rank=3
        )
        
        catalog["reward_hunter"] = Perk(
            perk_id="reward_hunter",
            name="Reward Hunter",
            description="+10% reward points",
            icon="🎁",
            branch=PerkBranch.ECONOMY,
            tier=PerkTier.BASIC,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("reward_multiplier", 0.10, "+10% rewards")
            ]
        )
        
        # Advanced Tier
        catalog["compound_interest"] = Perk(
            perk_id="compound_interest",
            name="Compound Interest",
            description="Streak bonuses increase 2x faster",
            icon="📊",
            branch=PerkBranch.ECONOMY,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("streak_multiplier", 2.0, "2x streak progression")
            ],
            prerequisites=["reward_hunter"]
        )
        
        catalog["daily_compound"] = Perk(
            perk_id="daily_compound",
            name="Daily Compound",
            description="Yesterday's XP earns 5% interest",
            icon="💹",
            branch=PerkBranch.ECONOMY,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.TRIGGERED,
            effects=[
                PerkEffect("xp_interest", 0.05, "+5% on yesterday's XP")
            ],
            synergies=["xp_boost_1"]
        )
        
        # Elite Tier
        catalog["prestige_master"] = Perk(
            perk_id="prestige_master",
            name="Prestige Master",
            description="Keep 25% XP on prestige reset",
            icon="🌟",
            branch=PerkBranch.ECONOMY,
            tier=PerkTier.ELITE,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("prestige_retention", 0.25, "Keep 25% XP on prestige")
            ],
            elite_only=True
        )
        
        # Legendary Tier
        catalog["infinite_wealth"] = Perk(
            perk_id="infinite_wealth",
            name="Infinite Wealth",
            description="Generate 100 XP/hour while active",
            icon="♾️",
            branch=PerkBranch.ECONOMY,
            tier=PerkTier.LEGENDARY,
            perk_type=PerkType.PASSIVE,
            effects=[
                PerkEffect("passive_xp", 100, "100 XP/hour passive income")
            ],
            xp_requirement=100000
        )
        
        # SEASONAL PERKS (Limited Time)
        catalog["winter_warrior"] = Perk(
            perk_id="winter_warrior",
            name="Winter Warrior",
            description="+50% XP during winter months",
            icon="❄️",
            branch=PerkBranch.ECONOMY,
            tier=PerkTier.ADVANCED,
            perk_type=PerkType.SEASONAL,
            effects=[
                PerkEffect("seasonal_xp", 0.50, "+50% winter XP")
            ],
            seasonal_end=datetime(2024, 3, 1)
        )
        
        catalog["halloween_hunter"] = Perk(
            perk_id="halloween_hunter",
            name="Halloween Hunter",
            description="Spooky trades earn double rewards",
            icon="🎃",
            branch=PerkBranch.TRADING,
            tier=PerkTier.BASIC,
            perk_type=PerkType.SEASONAL,
            effects=[
                PerkEffect("spooky_bonus", 2.0, "2x rewards on Halloween")
            ],
            seasonal_end=datetime(2024, 11, 1)
        )
        
        return catalog
    
    def get_player_data(self, user_id: int) -> PlayerPerkData:
        """Get or create player perk data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM player_perks WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            # Create new player data
            player_data = PlayerPerkData(
                user_id=user_id,
                level=1,
                available_points=1,  # Start with 1 point
                spent_points=0,
                unlocked_perks={}
            )
            
            cursor.execute('''
                INSERT INTO player_perks 
                (user_id, level, available_points, spent_points, unlocked_perks)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, 1, 1, 0, '{}'))
            
            conn.commit()
        else:
            # Load existing data
            unlocked_perks = json.loads(row[4])
            seasonal_perks = json.loads(row[8])
            
            player_data = PlayerPerkData(
                user_id=row[0],
                level=row[1],
                available_points=row[2],
                spent_points=row[3],
                unlocked_perks=unlocked_perks,
                active_loadout=row[5],
                respec_count=row[6],
                last_respec=datetime.fromtimestamp(row[7]) if row[7] else None,
                seasonal_perks=seasonal_perks
            )
            
            # Load loadouts
            cursor.execute('''
                SELECT * FROM perk_loadouts 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            for loadout_row in cursor.fetchall():
                loadout = PerkLoadout(
                    loadout_id=loadout_row[0],
                    name=loadout_row[2],
                    active_perks=json.loads(loadout_row[3]),
                    created_at=datetime.fromtimestamp(loadout_row[4]),
                    last_modified=datetime.fromtimestamp(loadout_row[5]),
                    is_active=bool(loadout_row[6])
                )
                player_data.loadouts.append(loadout)
        
        conn.close()
        return player_data
    
    def update_player_level(self, user_id: int, new_level: int) -> Tuple[int, List[str]]:
        """Update player level and award perk points"""
        player_data = self.get_player_data(user_id)
        
        if new_level <= player_data.level:
            return player_data.available_points, []
        
        # Calculate points to award
        points_earned = 0
        milestones = []
        
        for level in range(player_data.level + 1, new_level + 1):
            points_earned += self.POINTS_PER_LEVEL
            
            # Check for bonus points
            if level in self.BONUS_POINT_LEVELS:
                points_earned += 1
                milestones.append(f"Bonus point at level {level}!")
            
            # Check for tier unlocks
            for tier in PerkTier:
                if level == tier.min_level:
                    milestones.append(f"Unlocked {tier.name} tier perks!")
        
        # Update player data
        player_data.level = new_level
        player_data.available_points += points_earned
        
        # Save to database
        self._save_player_data(player_data)
        
        return player_data.available_points, milestones
    
    def unlock_perk(self, user_id: int, perk_id: str, user_xp: int = 0,
                   user_achievements: List[str] = None) -> Tuple[bool, str]:
        """Unlock a perk for a player"""
        if perk_id not in self.perk_catalog:
            return False, "Invalid perk ID"
        
        perk = self.perk_catalog[perk_id]
        player_data = self.get_player_data(user_id)
        
        # Check if already maxed
        current_rank = player_data.unlocked_perks.get(perk_id, 0)
        if current_rank >= perk.max_rank:
            return False, f"{perk.name} already at max rank"
        
        # Check level requirement
        if player_data.level < perk.tier.min_level:
            return False, f"Requires level {perk.tier.min_level}"
        
        # Check available points
        if player_data.available_points < perk.tier.point_cost:
            return False, f"Insufficient perk points. Need {perk.tier.point_cost}"
        
        # Check prerequisites
        for prereq in perk.prerequisites:
            if prereq not in player_data.unlocked_perks:
                prereq_name = self.perk_catalog[prereq].name
                return False, f"Requires {prereq_name} first"
        
        # Check XP requirement
        if perk.xp_requirement > 0 and user_xp < perk.xp_requirement:
            return False, f"Requires {perk.xp_requirement} XP"
        
        # Check achievement requirement
        if perk.achievement_requirement:
            if not user_achievements or perk.achievement_requirement not in user_achievements:
                return False, f"Requires {perk.achievement_requirement} achievement"
        
        # Check if seasonal and still available
        if perk.perk_type == PerkType.SEASONAL:
            if perk.seasonal_end and datetime.now() > perk.seasonal_end:
                return False, "Seasonal perk no longer available"
        
        # Unlock the perk
        player_data.unlocked_perks[perk_id] = current_rank + 1
        player_data.available_points -= perk.tier.point_cost
        player_data.spent_points += perk.tier.point_cost
        
        # Add to seasonal perks list if applicable
        if perk.perk_type == PerkType.SEASONAL:
            player_data.seasonal_perks.append(perk_id)
        
        # Save to database
        self._save_player_data(player_data)
        
        # Track analytics
        self._track_perk_unlock(user_id, perk_id)
        
        rank_text = f" (Rank {current_rank + 1})" if perk.max_rank > 1 else ""
        return True, f"Unlocked {perk.name}{rank_text}!"
    
    def create_loadout(self, user_id: int, name: str,
                      perks: Dict[PerkBranch, str]) -> Tuple[bool, str]:
        """Create a new perk loadout"""
        player_data = self.get_player_data(user_id)
        
        # Check loadout limit
        if len(player_data.loadouts) >= self.MAX_LOADOUTS:
            return False, f"Maximum {self.MAX_LOADOUTS} loadouts allowed"
        
        # Validate perks
        for branch, perk_id in perks.items():
            if perk_id and perk_id not in player_data.unlocked_perks:
                return False, f"Perk {perk_id} not unlocked"
            
            if perk_id:
                perk = self.perk_catalog[perk_id]
                if perk.branch != branch:
                    return False, f"{perk.name} doesn't belong to {branch.value} branch"
        
        # Check for conflicts
        selected_perks = [p for p in perks.values() if p]
        for perk_id in selected_perks:
            perk = self.perk_catalog[perk_id]
            for conflict_id in perk.conflicts:
                if conflict_id in selected_perks:
                    conflict_name = self.perk_catalog[conflict_id].name
                    return False, f"{perk.name} conflicts with {conflict_name}"
        
        # Create loadout
        loadout_id = f"{user_id}_{int(time.time())}"
        loadout = PerkLoadout(
            loadout_id=loadout_id,
            name=name,
            active_perks=perks,
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
        
        player_data.loadouts.append(loadout)
        
        # Save to database
        self._save_loadout(user_id, loadout)
        
        return True, f"Created loadout: {name}"
    
    def activate_loadout(self, user_id: int, loadout_id: str) -> Tuple[bool, str]:
        """Activate a perk loadout"""
        player_data = self.get_player_data(user_id)
        
        # Find loadout
        loadout = None
        for l in player_data.loadouts:
            if l.loadout_id == loadout_id:
                loadout = l
                break
        
        if not loadout:
            return False, "Loadout not found"
        
        # Update active loadout
        player_data.active_loadout = loadout_id
        self._save_player_data(player_data)
        
        # Track perk usage
        for perk_id in loadout.active_perks.values():
            if perk_id:
                self._track_perk_equip(user_id, perk_id)
        
        return True, f"Activated loadout: {loadout.name}"
    
    def get_active_effects(self, user_id: int) -> Dict[str, List[PerkEffect]]:
        """Get all active perk effects for a player"""
        player_data = self.get_player_data(user_id)
        
        if not player_data.active_loadout:
            return {}
        
        # Find active loadout
        active_loadout = None
        for loadout in player_data.loadouts:
            if loadout.loadout_id == player_data.active_loadout:
                active_loadout = loadout
                break
        
        if not active_loadout:
            return {}
        
        # Collect effects
        effects = {}
        active_perk_ids = [p for p in active_loadout.active_perks.values() if p]
        
        for perk_id in active_perk_ids:
            if perk_id not in self.perk_catalog:
                continue
            
            perk = self.perk_catalog[perk_id]
            
            # Skip expired seasonal perks
            if perk.perk_type == PerkType.SEASONAL:
                if perk.seasonal_end and datetime.now() > perk.seasonal_end:
                    continue
            
            # Get perk rank
            rank = player_data.unlocked_perks.get(perk_id, 1)
            
            # Apply effects
            for effect in perk.effects:
                effect_type = effect.effect_type
                if effect_type not in effects:
                    effects[effect_type] = []
                
                # Scale effect by rank if applicable
                scaled_effect = PerkEffect(
                    effect_type=effect.effect_type,
                    value=effect.value * rank if perk.max_rank > 1 else effect.value,
                    description=effect.description,
                    stacks=effect.stacks,
                    max_stack=effect.max_stack
                )
                effects[effect_type].append(scaled_effect)
        
        # Calculate synergy bonuses
        synergy_bonus = self._calculate_synergy_bonus(active_perk_ids)
        if synergy_bonus > 0:
            effects["synergy_bonus"] = [
                PerkEffect("global_bonus", synergy_bonus, 
                          f"+{int(synergy_bonus * 100)}% synergy bonus")
            ]
        
        return effects
    
    def _calculate_synergy_bonus(self, active_perks: List[str]) -> float:
        """Calculate synergy bonus from active perks"""
        synergy_count = 0
        
        for perk_id in active_perks:
            if perk_id not in self.perk_catalog:
                continue
            
            perk = self.perk_catalog[perk_id]
            for synergy_id in perk.synergies:
                if synergy_id in active_perks:
                    synergy_count += 1
        
        # Each synergy pair counts once
        synergy_pairs = synergy_count // 2
        bonus = synergy_pairs * self.SYNERGY_BONUS
        
        return min(bonus, self.MAX_SYNERGY_BONUS)
    
    def respec_perks(self, user_id: int, current_xp: int) -> Tuple[bool, str, int]:
        """Reset all perk points"""
        player_data = self.get_player_data(user_id)
        
        # Check cooldown
        if player_data.last_respec:
            cooldown_end = player_data.last_respec + timedelta(hours=self.RESPEC_COOLDOWN_HOURS)
            if datetime.now() < cooldown_end:
                remaining = (cooldown_end - datetime.now()).total_seconds() / 3600
                return False, f"Respec on cooldown. {remaining:.1f} hours remaining", 0
        
        # Calculate cost
        cost = self.BASE_RESPEC_COST * (self.RESPEC_MULTIPLIER ** player_data.respec_count)
        
        # Check if player can afford
        if current_xp < cost:
            return False, f"Insufficient XP. Need {cost} XP", cost
        
        # Perform respec
        total_points = player_data.spent_points + player_data.available_points
        player_data.available_points = total_points
        player_data.spent_points = 0
        player_data.unlocked_perks = {}
        player_data.active_loadout = None
        player_data.respec_count += 1
        player_data.last_respec = datetime.now()
        
        # Clear loadouts
        player_data.loadouts = []
        
        # Save to database
        self._save_player_data(player_data)
        self._clear_user_loadouts(user_id)
        
        return True, f"Reset all perks! {total_points} points available", cost
    
    def get_perk_tree_display(self, user_id: int) -> Dict[str, Any]:
        """Get perk tree data for visual display"""
        player_data = self.get_player_data(user_id)
        
        tree = {}
        for branch in PerkBranch:
            tree[branch.value] = {
                "tiers": {}
            }
            
            for tier in PerkTier:
                tree[branch.value]["tiers"][tier.value] = {
                    "locked": player_data.level < tier.min_level,
                    "min_level": tier.min_level,
                    "perks": []
                }
        
        # Organize perks by branch and tier
        for perk_id, perk in self.perk_catalog.items():
            # Skip expired seasonal perks
            if perk.perk_type == PerkType.SEASONAL:
                if perk.seasonal_end and datetime.now() > perk.seasonal_end:
                    continue
            
            perk_info = {
                "perk_id": perk_id,
                "name": perk.name,
                "description": perk.description,
                "icon": perk.icon,
                "cost": perk.tier.point_cost,
                "type": perk.perk_type.value,
                "unlocked": perk_id in player_data.unlocked_perks,
                "rank": player_data.unlocked_perks.get(perk_id, 0),
                "max_rank": perk.max_rank,
                "prerequisites": perk.prerequisites,
                "synergies": perk.synergies,
                "conflicts": perk.conflicts,
                "effects": [asdict(e) for e in perk.effects],
                "requirements": {
                    "xp": perk.xp_requirement,
                    "achievement": perk.achievement_requirement
                },
                "seasonal": perk.perk_type == PerkType.SEASONAL,
                "seasonal_end": perk.seasonal_end.isoformat() if perk.seasonal_end else None,
                "elite_only": perk.elite_only
            }
            
            tree[perk.branch.value]["tiers"][perk.tier.value]["perks"].append(perk_info)
        
        return {
            "tree": tree,
            "player": {
                "level": player_data.level,
                "available_points": player_data.available_points,
                "spent_points": player_data.spent_points,
                "total_unlocked": len(player_data.unlocked_perks),
                "active_loadout": player_data.active_loadout,
                "loadouts": [
                    {
                        "id": l.loadout_id,
                        "name": l.name,
                        "perks": l.active_perks
                    } for l in player_data.loadouts
                ],
                "respec_count": player_data.respec_count,
                "can_respec": player_data.last_respec is None or 
                             (datetime.now() - player_data.last_respec).total_seconds() > 
                             self.RESPEC_COOLDOWN_HOURS * 3600
            }
        }
    
    def get_perk_recommendations(self, user_id: int, user_stats: Dict[str, Any]) -> List[Dict]:
        """Get personalized perk recommendations based on playstyle"""
        player_data = self.get_player_data(user_id)
        recommendations = []
        
        # Analyze playstyle
        win_rate = user_stats.get('win_rate', 0)
        trade_frequency = user_stats.get('trades_per_day', 0)
        avg_profit = user_stats.get('avg_profit', 0)
        squad_size = user_stats.get('squad_size', 0)
        
        # Recommend based on stats
        if win_rate > 0.7 and "quick_fingers" not in player_data.unlocked_perks:
            recommendations.append({
                "perk_id": "quick_fingers",
                "reason": "Your high win rate would benefit from faster execution",
                "priority": "high"
            })
        
        if trade_frequency > 10 and "reduced_fees_1" not in player_data.unlocked_perks:
            recommendations.append({
                "perk_id": "reduced_fees_1",
                "reason": "High trade volume means fee reduction has big impact",
                "priority": "high"
            })
        
        if squad_size > 5 and "squad_synergy" not in player_data.unlocked_perks:
            recommendations.append({
                "perk_id": "squad_synergy",
                "reason": "Large squad = more XP opportunities",
                "priority": "medium"
            })
        
        if avg_profit > 1000 and "compound_interest" not in player_data.unlocked_perks:
            recommendations.append({
                "perk_id": "compound_interest",
                "reason": "High profits compound into massive streak bonuses",
                "priority": "high"
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _save_player_data(self, player_data: PlayerPerkData):
        """Save player data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE player_perks SET
                level = ?,
                available_points = ?,
                spent_points = ?,
                unlocked_perks = ?,
                active_loadout = ?,
                respec_count = ?,
                last_respec = ?,
                seasonal_perks = ?
            WHERE user_id = ?
        ''', (
            player_data.level,
            player_data.available_points,
            player_data.spent_points,
            json.dumps(player_data.unlocked_perks),
            player_data.active_loadout,
            player_data.respec_count,
            int(player_data.last_respec.timestamp()) if player_data.last_respec else None,
            json.dumps(player_data.seasonal_perks),
            player_data.user_id
        ))
        
        conn.commit()
        conn.close()
    
    def _save_loadout(self, user_id: int, loadout: PerkLoadout):
        """Save loadout to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO perk_loadouts
            (loadout_id, user_id, name, active_perks, created_at, last_modified, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            loadout.loadout_id,
            user_id,
            loadout.name,
            json.dumps({k.value: v for k, v in loadout.active_perks.items()}),
            int(loadout.created_at.timestamp()),
            int(loadout.last_modified.timestamp()),
            1 if loadout.is_active else 0
        ))
        
        conn.commit()
        conn.close()
    
    def _clear_user_loadouts(self, user_id: int):
        """Clear all user loadouts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE perk_loadouts SET is_active = 0 WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def _track_perk_unlock(self, user_id: int, perk_id: str):
        """Track perk unlock for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO perk_analytics (user_id, perk_id, times_equipped)
            VALUES (?, ?, 0)
            ON CONFLICT(user_id, perk_id) DO NOTHING
        ''', (user_id, perk_id))
        
        conn.commit()
        conn.close()
    
    def _track_perk_equip(self, user_id: int, perk_id: str):
        """Track perk equip for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO perk_analytics 
            (user_id, perk_id, times_equipped, last_equipped)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(user_id, perk_id) DO UPDATE SET
                times_equipped = times_equipped + 1,
                last_equipped = ?
        ''', (user_id, perk_id, int(time.time()), int(time.time())))
        
        conn.commit()
        conn.close()
    
    def get_perk_analytics(self, perk_id: str) -> Dict[str, Any]:
        """Get analytics for a specific perk"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                SUM(times_equipped) as total_equips,
                AVG(performance_delta) as avg_performance
            FROM perk_analytics
            WHERE perk_id = ?
        ''', (perk_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "perk_id": perk_id,
            "total_users": row[0] or 0,
            "total_equips": row[1] or 0,
            "avg_performance_delta": row[2] or 0
        }
    
    def apply_perk_effects(self, user_id: int, context: str, 
                          base_value: float) -> Tuple[float, List[str]]:
        """Apply active perk effects to a value in a given context"""
        effects = self.get_active_effects(user_id)
        final_value = base_value
        applied_effects = []
        
        # Map contexts to effect types
        context_effects = {
            "trading_fee": ["fee_reduction"],
            "spread": ["spread_improvement"],
            "xp_gain": ["xp_multiplier", "seasonal_xp"],
            "reward": ["reward_multiplier"],
            "loss": ["loss_reduction"],
            "streak": ["streak_multiplier"],
            "execution": ["execution_speed"]
        }
        
        relevant_effects = context_effects.get(context, [])
        
        for effect_type in relevant_effects:
            if effect_type in effects:
                for effect in effects[effect_type]:
                    if effect_type in ["fee_reduction", "loss_reduction"]:
                        # Reductions
                        final_value *= (1 - effect.value)
                        applied_effects.append(f"{effect.description}")
                    else:
                        # Multipliers
                        final_value *= (1 + effect.value)
                        applied_effects.append(f"{effect.description}")
        
        # Apply global synergy bonus if present
        if "synergy_bonus" in effects:
            for effect in effects["synergy_bonus"]:
                final_value *= (1 + effect.value)
                applied_effects.append(effect.description)
        
        return final_value, applied_effects