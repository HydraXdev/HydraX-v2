"""
BITTEN Battle Pass Seasonal Progression Framework
Military-themed battle pass system with seasonal rewards and tier progression
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class BattlePassType(Enum):
    FREE = "free"
    PREMIUM = "premium"
    ELITE = "elite"

class RewardType(Enum):
    XP_BOOST = "xp_boost"
    BADGE = "badge"
    TITLE = "title"
    AVATAR = "avatar"
    WEAPON_SKIN = "weapon_skin"
    EMOTE = "emote"
    CURRENCY = "currency"
    EXCLUSIVE_ACCESS = "exclusive_access"
    COSMETIC = "cosmetic"
    SPECIAL = "special"

@dataclass
class BattlePassReward:
    id: str
    name: str
    description: str
    type: RewardType
    tier_requirement: str  # press_pass, nibbler, fang, commander, apex
    rarity: str
    metadata: Dict
    image_url: str
    unlock_level: int
    xp_cost: int  # XP cost to claim reward (0 for automatic rewards)
    
    def to_dict(self):
        return asdict(self)

@dataclass
class BattlePassSeason:
    id: str
    name: str
    description: str
    theme: str
    start_date: datetime
    end_date: datetime
    max_level: int
    xp_per_level: int
    rewards: Dict[int, List[BattlePassReward]]
    challenges: List[Dict]
    metadata: Dict
    
    def to_dict(self):
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat()
        return data

@dataclass
class UserBattlePassProgress:
    user_id: str
    season_id: str
    level: int
    xp: int
    user_tier: str  # nibbler, fang, commander, apex - determines access level
    rewards_claimed: List[int]
    challenges_completed: List[str]
    last_updated: datetime
    
    def to_dict(self):
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data

class BittenBattlePass:
    """
    BITTEN Battle Pass System - Seasonal progression with military themes
    
    Features:
    - Seasonal themed content (12 weeks per season)
    - Tier-based access (based on user subscription tier)
    - 100 levels with escalating XP requirements
    - Weekly challenges for additional XP
    - XP-based reward unlocking
    - Time-limited content to drive engagement
    """
    
    def __init__(self, db_path: str = "data/battle_pass.db"):
        self.db_path = db_path
        self.current_season = None
        self.init_database()
        self.load_current_season()
    
    def init_database(self):
        """Initialize battle pass database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Battle pass seasons
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_pass_seasons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                theme TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                max_level INTEGER DEFAULT 100,
                xp_per_level INTEGER DEFAULT 1000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User battle pass progress
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_battle_pass_progress (
                user_id TEXT,
                season_id TEXT,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                user_tier TEXT DEFAULT 'press_pass',
                rewards_claimed TEXT DEFAULT '[]',
                challenges_completed TEXT DEFAULT '[]',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, season_id)
            )
        """)
        
        # Battle pass rewards
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_pass_rewards (
                id TEXT PRIMARY KEY,
                season_id TEXT,
                level INTEGER,
                tier TEXT,
                name TEXT,
                description TEXT,
                type TEXT,
                rarity TEXT,
                tier_requirement TEXT,
                xp_cost INTEGER DEFAULT 0,
                metadata TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Weekly challenges
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_pass_challenges (
                id TEXT PRIMARY KEY,
                season_id TEXT,
                week INTEGER,
                name TEXT,
                description TEXT,
                objective TEXT,
                xp_reward INTEGER,
                tier_requirement TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User challenge progress
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_challenge_progress (
                user_id TEXT,
                challenge_id TEXT,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                season_id TEXT,
                PRIMARY KEY (user_id, challenge_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_battle_pass_season 
            ON user_battle_pass_progress(user_id, season_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_battle_pass_rewards_season 
            ON battle_pass_rewards(season_id, level)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_challenges_season 
            ON battle_pass_challenges(season_id, week)
        """)
        
        conn.commit()
        conn.close()
    
    def create_season(self, season_data: BattlePassSeason) -> bool:
        """Create a new battle pass season"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO battle_pass_seasons 
                (id, name, description, theme, start_date, end_date, max_level, 
                 xp_per_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                season_data.id,
                season_data.name,
                season_data.description,
                season_data.theme,
                season_data.start_date,
                season_data.end_date,
                season_data.max_level,
                season_data.xp_per_level
            ))
            
            # Insert rewards
            for level, rewards in season_data.rewards.items():
                for reward in rewards:
                    cursor.execute("""
                        INSERT INTO battle_pass_rewards 
                        (id, season_id, level, tier, name, description, type, 
                         rarity, tier_requirement, xp_cost, metadata, image_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        reward.id,
                        season_data.id,
                        level,
                        reward.tier_requirement,  # Use tier_requirement
                        reward.name,
                        reward.description,
                        reward.type.value,
                        reward.rarity,
                        reward.tier_requirement,
                        reward.xp_cost,
                        json.dumps(reward.metadata),
                        reward.image_url
                    ))
            
            # Insert challenges
            for challenge in season_data.challenges:
                cursor.execute("""
                    INSERT INTO battle_pass_challenges 
                    (id, season_id, week, name, description, objective, 
                     xp_reward, tier_requirement, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    challenge['id'],
                    season_data.id,
                    challenge['week'],
                    challenge['name'],
                    challenge['description'],
                    challenge['objective'],
                    challenge['xp_reward'],
                    challenge.get('tier_requirement', 'free'),
                    json.dumps(challenge.get('metadata', {}))
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error creating season: {e}")
            return False
    
    def load_current_season(self) -> Optional[BattlePassSeason]:
        """Load the currently active season"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            cursor.execute("""
                SELECT * FROM battle_pass_seasons 
                WHERE start_date <= ? AND end_date >= ?
                ORDER BY start_date DESC LIMIT 1
            """, (now, now))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                season_dict = dict(zip(columns, row))
                
                # Load rewards
                cursor.execute("""
                    SELECT * FROM battle_pass_rewards 
                    WHERE season_id = ? ORDER BY level, tier
                """, (season_dict['id'],))
                
                reward_rows = cursor.fetchall()
                reward_columns = [desc[0] for desc in cursor.description]
                rewards_by_level = {}
                
                for reward_row in reward_rows:
                    reward_dict = dict(zip(reward_columns, reward_row))
                    level = reward_dict['level']
                    
                    reward = BattlePassReward(
                        id=reward_dict['id'],
                        name=reward_dict['name'],
                        description=reward_dict['description'],
                        type=RewardType(reward_dict['type']),
                        tier=reward_dict['tier'],
                        rarity=reward_dict['rarity'],
                        metadata=json.loads(reward_dict['metadata']),
                        image_url=reward_dict['image_url'],
                        unlock_level=level
                    )
                    
                    if level not in rewards_by_level:
                        rewards_by_level[level] = []
                    rewards_by_level[level].append(reward)
                
                # Load challenges
                cursor.execute("""
                    SELECT * FROM battle_pass_challenges 
                    WHERE season_id = ? ORDER BY week
                """, (season_dict['id'],))
                
                challenge_rows = cursor.fetchall()
                challenge_columns = [desc[0] for desc in cursor.description]
                challenges = []
                
                for challenge_row in challenge_rows:
                    challenge_dict = dict(zip(challenge_columns, challenge_row))
                    challenges.append({
                        'id': challenge_dict['id'],
                        'week': challenge_dict['week'],
                        'name': challenge_dict['name'],
                        'description': challenge_dict['description'],
                        'objective': challenge_dict['objective'],
                        'xp_reward': challenge_dict['xp_reward'],
                        'tier_requirement': challenge_dict['tier_requirement'],
                        'metadata': json.loads(challenge_dict['metadata'])
                    })
                
                season = BattlePassSeason(
                    id=season_dict['id'],
                    name=season_dict['name'],
                    description=season_dict['description'],
                    theme=season_dict['theme'],
                    start_date=datetime.fromisoformat(season_dict['start_date']),
                    end_date=datetime.fromisoformat(season_dict['end_date']),
                    max_level=season_dict['max_level'],
                    xp_per_level=season_dict['xp_per_level'],
                    premium_price=season_dict['premium_price'],
                    elite_price=season_dict['elite_price'],
                    rewards=rewards_by_level,
                    challenges=challenges,
                    metadata=json.loads(season_dict['metadata'])
                )
                
                self.current_season = season
                conn.close()
                return season
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error loading current season: {e}")
            return None
    
    def get_user_progress(self, user_id: str, season_id: str = None) -> Optional[UserBattlePassProgress]:
        """Get user's battle pass progress for a season"""
        if not season_id and self.current_season:
            season_id = self.current_season.id
        elif not season_id:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM user_battle_pass_progress 
                WHERE user_id = ? AND season_id = ?
            """, (user_id, season_id))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                progress_dict = dict(zip(columns, row))
                
                progress = UserBattlePassProgress(
                    user_id=progress_dict['user_id'],
                    season_id=progress_dict['season_id'],
                    level=progress_dict['level'],
                    xp=progress_dict['xp'],
                    user_tier=progress_dict['user_tier'],
                    rewards_claimed=json.loads(progress_dict['rewards_claimed']),
                    challenges_completed=json.loads(progress_dict['challenges_completed']),
                    last_updated=datetime.fromisoformat(progress_dict['last_updated'])
                )
                
                conn.close()
                return progress
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error getting user progress: {e}")
            return None
    
    def award_xp(self, user_id: str, xp_amount: int, source: str = "gameplay") -> Dict:
        """Award XP to user and handle level progression"""
        if not self.current_season:
            return {"success": False, "error": "No active season"}
        
        # Get or create user progress
        progress = self.get_user_progress(user_id)
        if not progress:
            progress = UserBattlePassProgress(
                user_id=user_id,
                season_id=self.current_season.id,
                level=1,
                xp=0,
                user_tier='press_pass',  # Default tier
                rewards_claimed=[],
                challenges_completed=[],
                last_updated=datetime.now()
            )
        
        # Add XP
        old_level = progress.level
        progress.xp += xp_amount
        
        # Check for level ups
        levels_gained = 0
        while (progress.xp >= self.current_season.xp_per_level and 
               progress.level < self.current_season.max_level):
            progress.xp -= self.current_season.xp_per_level
            progress.level += 1
            levels_gained += 1
        
        # Save progress
        self.save_user_progress(progress)
        
        result = {
            "success": True,
            "xp_awarded": xp_amount,
            "source": source,
            "old_level": old_level,
            "new_level": progress.level,
            "levels_gained": levels_gained,
            "current_xp": progress.xp,
            "xp_to_next": self.current_season.xp_per_level - progress.xp
        }
        
        # Check for new rewards
        if levels_gained > 0:
            new_rewards = self.get_level_rewards(old_level + 1, progress.level, progress.user_tier)
            result["new_rewards"] = new_rewards
        
        return result
    
    def get_level_rewards(self, start_level: int, end_level: int, user_tier: str) -> List[BattlePassReward]:
        """Get all rewards between two levels for a user tier"""
        if not self.current_season:
            return []
        
        # Define tier hierarchy for access control
        tier_hierarchy = ['press_pass', 'nibbler', 'fang', 'commander', 'apex']
        user_tier_level = tier_hierarchy.index(user_tier) if user_tier in tier_hierarchy else 0
        
        rewards = []
        for level in range(start_level, end_level + 1):
            if level in self.current_season.rewards:
                for reward in self.current_season.rewards[level]:
                    # Check if user has access to this tier
                    required_tier_level = tier_hierarchy.index(reward.tier_requirement) if reward.tier_requirement in tier_hierarchy else 0
                    if user_tier_level >= required_tier_level:
                        rewards.append(reward)
        
        return rewards
    
    def update_user_tier(self, user_id: str, new_tier: str) -> Dict:
        """Update user's subscription tier (affects battle pass access)"""
        if not self.current_season:
            return {"success": False, "error": "No active season"}
        
        progress = self.get_user_progress(user_id)
        if not progress:
            # Create new progress if user doesn't exist
            progress = UserBattlePassProgress(
                user_id=user_id,
                season_id=self.current_season.id,
                level=1,
                xp=0,
                user_tier=new_tier,
                rewards_claimed=[],
                challenges_completed=[],
                last_updated=datetime.now()
            )
        else:
            progress.user_tier = new_tier
            progress.last_updated = datetime.now()
        
        # Get newly available rewards due to tier upgrade
        newly_available = self.get_level_rewards(1, progress.level, new_tier)
        
        self.save_user_progress(progress)
        
        return {
            "success": True,
            "user_tier": new_tier,
            "level": progress.level,
            "newly_available_rewards": [r.to_dict() for r in newly_available]
        }
    
    def claim_reward(self, user_id: str, reward_id: str) -> Dict:
        """Claim a specific reward (may cost XP)"""
        progress = self.get_user_progress(user_id)
        if not progress:
            return {"success": False, "error": "User not found"}
        
        # Get reward details
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT level, name, xp_cost, tier_requirement 
                FROM battle_pass_rewards 
                WHERE id = ?
            """, (reward_id,))
            
            reward_row = cursor.fetchone()
            if not reward_row:
                conn.close()
                return {"success": False, "error": "Reward not found"}
            
            level, name, xp_cost, tier_requirement = reward_row
            
            # Check if user has reached the level
            if level > progress.level:
                conn.close()
                return {"success": False, "error": f"Must reach level {level} first"}
            
            # Check tier requirement
            tier_hierarchy = ['press_pass', 'nibbler', 'fang', 'commander', 'apex']
            user_tier_level = tier_hierarchy.index(progress.user_tier) if progress.user_tier in tier_hierarchy else 0
            required_tier_level = tier_hierarchy.index(tier_requirement) if tier_requirement in tier_hierarchy else 0
            
            if user_tier_level < required_tier_level:
                conn.close()
                return {"success": False, "error": f"Requires {tier_requirement} tier or higher"}
            
            # Check if already claimed
            if reward_id in progress.rewards_claimed:
                conn.close()
                return {"success": False, "error": "Reward already claimed"}
            
            # Check XP cost
            if xp_cost > 0 and progress.xp < xp_cost:
                conn.close()
                return {"success": False, "error": f"Need {xp_cost} XP to claim (you have {progress.xp})"}
            
            # Deduct XP and claim reward
            if xp_cost > 0:
                progress.xp -= xp_cost
            
            progress.rewards_claimed.append(reward_id)
            self.save_user_progress(progress)
            
            conn.close()
            
            return {
                "success": True,
                "reward_id": reward_id,
                "name": name,
                "xp_cost": xp_cost,
                "remaining_xp": progress.xp
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_user_progress(self, progress: UserBattlePassProgress):
        """Save user battle pass progress"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_battle_pass_progress
                (user_id, season_id, level, xp, user_tier, rewards_claimed, 
                 challenges_completed, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                progress.user_id,
                progress.season_id,
                progress.level,
                progress.xp,
                progress.user_tier,
                json.dumps(progress.rewards_claimed),
                json.dumps(progress.challenges_completed),
                progress.last_updated.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving user progress: {e}")
    
    def get_season_leaderboard(self, season_id: str = None, limit: int = 100) -> List[Dict]:
        """Get leaderboard for a season"""
        if not season_id and self.current_season:
            season_id = self.current_season.id
        elif not season_id:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, level, xp, user_tier
                FROM user_battle_pass_progress 
                WHERE season_id = ?
                ORDER BY level DESC, xp DESC
                LIMIT ?
            """, (season_id, limit))
            
            rows = cursor.fetchall()
            leaderboard = []
            
            for i, row in enumerate(rows):
                leaderboard.append({
                    "rank": i + 1,
                    "user_id": row[0],
                    "level": row[1],
                    "xp": row[2],
                    "user_tier": row[3]
                })
            
            conn.close()
            return leaderboard
            
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []

def create_sample_season() -> BattlePassSeason:
    """Create a sample battle pass season for testing"""
    season_id = f"season_1_{datetime.now().strftime('%Y%m')}"
    start_date = datetime.now()
    end_date = start_date + timedelta(days=84)  # 12 weeks
    
    # Create sample rewards
    rewards = {}
    for level in range(1, 101):
        level_rewards = []
        
        # Free rewards every 5 levels (available to all tiers)
        if level % 5 == 0:
            level_rewards.append(BattlePassReward(
                id=f"free_xp_boost_{level}",
                name=f"XP Boost Lv.{level//5}",
                description=f"50% XP boost for {level//5} hours",
                type=RewardType.XP_BOOST,
                tier_requirement="press_pass",
                rarity="common",
                metadata={"boost_percent": 50, "duration_hours": level//5},
                image_url=f"/static/rewards/xp_boost_{level//5}.png",
                unlock_level=level,
                xp_cost=0  # Free to claim
            ))
        
        # Nibbler+ rewards every 2 levels
        if level % 2 == 0:
            level_rewards.append(BattlePassReward(
                id=f"nibbler_badge_{level}",
                name=f"Elite Badge Lv.{level//2}",
                description=f"Exclusive badge for level {level}",
                type=RewardType.BADGE,
                tier_requirement="nibbler",
                rarity="rare" if level < 50 else "epic",
                metadata={"badge_tier": level//2},
                image_url=f"/static/rewards/badge_{level//2}.png",
                unlock_level=level,
                xp_cost=50  # Small XP cost for premium rewards
            ))
        
        # Commander+ rewards every 10 levels
        if level % 10 == 0:
            level_rewards.append(BattlePassReward(
                id=f"commander_title_{level}",
                name=f"Commander Title Lv.{level//10}",
                description=f"Elite title: 'Tactical Commander Lv.{level//10}'",
                type=RewardType.TITLE,
                tier_requirement="commander",
                rarity="legendary" if level >= 50 else "epic",
                metadata={"title": f"Tactical Commander Lv.{level//10}"},
                image_url=f"/static/rewards/title_{level//10}.png",
                unlock_level=level,
                xp_cost=200  # Higher XP cost for elite rewards
            ))
        
        # APEX exclusive rewards every 25 levels
        if level % 25 == 0:
            level_rewards.append(BattlePassReward(
                id=f"apex_exclusive_{level}",
                name=f"APEX Legendary Lv.{level//25}",
                description=f"Ultra-rare APEX exclusive item",
                type=RewardType.SPECIAL,
                tier_requirement="apex",
                rarity="legendary",
                metadata={"apex_tier": level//25},
                image_url=f"/static/rewards/apex_{level//25}.png",
                unlock_level=level,
                xp_cost=500  # Expensive XP cost for APEX exclusives
            ))
        
        if level_rewards:
            rewards[level] = level_rewards
    
    # Create sample challenges
    challenges = []
    for week in range(1, 13):
        challenges.extend([
            {
                "id": f"weekly_trades_{week}",
                "week": week,
                "name": f"Weekly Trader",
                "description": f"Execute 20 trades this week",
                "objective": "execute_trades:20",
                "xp_reward": 2000,
                "tier_requirement": "free",
                "metadata": {"target": 20, "type": "trades"}
            },
            {
                "id": f"weekly_wins_{week}",
                "week": week,
                "name": f"Victory Streak",
                "description": f"Win 15 trades this week",
                "objective": "win_trades:15",
                "xp_reward": 3000,
                "tier_requirement": "premium",
                "metadata": {"target": 15, "type": "wins"}
            }
        ])
    
    return BattlePassSeason(
        id=season_id,
        name="Operation: Market Domination",
        description="Elite tactical trading campaign with XP-based rewards",
        theme="military_ops",
        start_date=start_date,
        end_date=end_date,
        max_level=100,
        xp_per_level=1000,
        rewards=rewards,
        challenges=challenges,
        metadata={
            "background_image": "/static/seasons/season_1_bg.jpg",
            "theme_color": "#00ff88",
            "featured_rewards": ["commander_title_100", "nibbler_badge_50", "free_xp_boost_100"],
            "xp_economy": {
                "basic_rewards": 0,
                "premium_rewards": 50,
                "elite_rewards": 200,
                "legendary_rewards": 500
            }
        }
    )

# Global instance
battle_pass_system = BittenBattlePass()

if __name__ == "__main__":
    # Create and deploy sample season
    sample_season = create_sample_season()
    battle_pass_system.create_season(sample_season)
    print(f"Created sample season: {sample_season.name}")
    print(f"Season runs from {sample_season.start_date} to {sample_season.end_date}")
    print(f"Total rewards: {sum(len(rewards) for rewards in sample_season.rewards.values())}")
    print(f"Total challenges: {len(sample_season.challenges)}")