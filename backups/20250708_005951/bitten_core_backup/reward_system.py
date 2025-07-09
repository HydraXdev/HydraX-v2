# reward_system.py
# Dynamic reward system with risk tiers, XP bonuses, and streak tracking

import json
import time
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

class RiskTier(Enum):
    """Risk tier definitions"""
    STANDARD = "STANDARD"
    APEX = "APEX"
    
    @property
    def base_reward_rate(self) -> float:
        """Get base reward rate for tier"""
        return 0.03 if self == RiskTier.APEX else 0.02
    
    @property
    def xp_bonus(self) -> float:
        """Get XP bonus multiplier for tier"""
        tier_bonuses = {
            RiskTier.STANDARD: 0.0,   # 0% bonus
            RiskTier.APEX: 0.15        # 15% bonus
        }
        return tier_bonuses.get(self, 0.0)

class RewardPeriod(Enum):
    """Reward calculation periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class StreakInfo:
    """Streak tracking information"""
    current_streak: int = 0
    best_streak: int = 0
    last_activity: int = 0
    streak_type: str = "daily"  # daily, weekly
    
    @property
    def is_active(self) -> bool:
        """Check if streak is still active"""
        if self.streak_type == "daily":
            # Daily streak breaks after 24 hours
            return (time.time() - self.last_activity) < 86400
        else:
            # Weekly streak breaks after 7 days
            return (time.time() - self.last_activity) < 604800

@dataclass
class RewardCalculation:
    """Reward calculation result"""
    base_amount: float
    tier_bonus: float
    xp_bonus: float
    streak_bonus: float
    achievement_bonus: float
    total_amount: float
    breakdown: Dict[str, float]

class RewardSystem:
    """Manages dynamic rewards, streaks, and bonuses"""
    
    # XP tier thresholds and bonuses
    XP_TIERS = [
        {"min_xp": 0, "name": "Recruit", "bonus": 0.0},      # 0% bonus
        {"min_xp": 1000, "name": "Soldier", "bonus": 0.15},  # 15% bonus  
        {"min_xp": 5000, "name": "Veteran", "bonus": 0.30},  # 30% bonus
        {"min_xp": 20000, "name": "Elite", "bonus": 0.50}    # 50% bonus
    ]
    
    # Streak bonuses
    STREAK_BONUSES = {
        'daily': {
            3: 0.05,    # 5% bonus at 3 days
            7: 0.10,    # 10% bonus at 7 days
            14: 0.15,   # 15% bonus at 14 days
            30: 0.25,   # 25% bonus at 30 days
            60: 0.35,   # 35% bonus at 60 days
            90: 0.50    # 50% bonus at 90 days
        },
        'weekly': {
            4: 0.10,    # 10% bonus at 4 weeks
            8: 0.20,    # 20% bonus at 8 weeks
            12: 0.30,   # 30% bonus at 12 weeks
            24: 0.50    # 50% bonus at 24 weeks
        }
    }
    
    # Achievement reward multipliers
    ACHIEVEMENT_MULTIPLIERS = {
        'first_blood': 0.05,
        'marksman': 0.10,
        'elite_sniper': 0.15,
        'legendary_sniper': 0.25,
        'mogul': 0.20,
        'commander': 0.30,
        'general': 0.50
    }
    
    def __init__(self, db_path: str = "bitten_rewards.db", 
                 profile_manager=None):
        self.db_path = db_path
        self.profile_manager = profile_manager
        self._init_database()
    
    def _init_database(self):
        """Initialize reward database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Streak tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streaks (
                user_id INTEGER PRIMARY KEY,
                daily_streak INTEGER DEFAULT 0,
                daily_best INTEGER DEFAULT 0,
                daily_last_activity INTEGER DEFAULT 0,
                weekly_streak INTEGER DEFAULT 0,
                weekly_best INTEGER DEFAULT 0,
                weekly_last_activity INTEGER DEFAULT 0
            )
        ''')
        
        # Reward history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reward_history (
                reward_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                period_type TEXT,
                period_start INTEGER,
                period_end INTEGER,
                base_reward REAL,
                total_reward REAL,
                trades_count INTEGER,
                profit_earned REAL,
                xp_earned INTEGER,
                bonuses_applied TEXT,
                created_at INTEGER
            )
        ''')
        
        # Daily/weekly/monthly aggregations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reward_aggregations (
                user_id INTEGER,
                period_type TEXT,
                period_key TEXT,
                total_trades INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                total_rewards REAL DEFAULT 0,
                last_updated INTEGER,
                PRIMARY KEY (user_id, period_type, period_key)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_reward(self, user_id: int, profit_amount: float, 
                        risk_tier: RiskTier = RiskTier.STANDARD) -> RewardCalculation:
        """Calculate reward with all bonuses applied"""
        # Get user profile data
        user_xp = 0
        earned_medals = []
        
        if self.profile_manager:
            user_stats = self.profile_manager.get_user_stats(user_id)
            if user_stats:
                user_xp = user_stats.total_xp
            
            medals = self.profile_manager.get_user_medals(user_id)
            earned_medals = [m['id'] for m in medals if m['earned']]
        
        # Base reward calculation
        base_reward = profit_amount * risk_tier.base_reward_rate
        
        # Calculate tier bonus (risk tier)
        tier_bonus = base_reward * risk_tier.xp_bonus
        
        # Calculate XP tier bonus
        xp_tier_bonus = self._get_xp_tier_bonus(user_xp)
        xp_bonus = base_reward * xp_tier_bonus
        
        # Calculate streak bonuses
        daily_streak_bonus = self._calculate_streak_bonus(user_id, 'daily')
        weekly_streak_bonus = self._calculate_streak_bonus(user_id, 'weekly')
        streak_bonus = base_reward * max(daily_streak_bonus, weekly_streak_bonus)
        
        # Calculate achievement bonuses
        achievement_bonus = self._calculate_achievement_bonus(base_reward, earned_medals)
        
        # Calculate total
        total_reward = (base_reward + tier_bonus + xp_bonus + 
                       streak_bonus + achievement_bonus)
        
        # Build breakdown
        breakdown = {
            'base': base_reward,
            'risk_tier_bonus': tier_bonus,
            'xp_tier_bonus': xp_bonus,
            'streak_bonus': streak_bonus,
            'achievement_bonus': achievement_bonus,
            'multipliers': {
                'risk_tier': risk_tier.xp_bonus,
                'xp_tier': xp_tier_bonus,
                'daily_streak': daily_streak_bonus,
                'weekly_streak': weekly_streak_bonus,
                'achievements': sum(self.ACHIEVEMENT_MULTIPLIERS.get(m, 0) 
                                  for m in earned_medals)
            }
        }
        
        return RewardCalculation(
            base_amount=base_reward,
            tier_bonus=tier_bonus,
            xp_bonus=xp_bonus,
            streak_bonus=streak_bonus,
            achievement_bonus=achievement_bonus,
            total_amount=total_reward,
            breakdown=breakdown
        )
    
    def _get_xp_tier_bonus(self, user_xp: int) -> float:
        """Get XP tier bonus based on total XP"""
        for tier in reversed(self.XP_TIERS):
            if user_xp >= tier['min_xp']:
                return tier['bonus']
        return 0.0
    
    def _calculate_streak_bonus(self, user_id: int, streak_type: str) -> float:
        """Calculate streak bonus multiplier"""
        streak_info = self.get_streak_info(user_id, streak_type)
        
        if not streak_info.is_active:
            return 0.0
        
        # Find applicable bonus
        bonuses = self.STREAK_BONUSES.get(streak_type, {})
        applicable_bonus = 0.0
        
        for days, bonus in sorted(bonuses.items()):
            if streak_info.current_streak >= days:
                applicable_bonus = bonus
        
        return applicable_bonus
    
    def _calculate_achievement_bonus(self, base_reward: float, 
                                   earned_medals: List[str]) -> float:
        """Calculate achievement-based bonus"""
        total_multiplier = 0.0
        
        for medal_id in earned_medals:
            if medal_id in self.ACHIEVEMENT_MULTIPLIERS:
                total_multiplier += self.ACHIEVEMENT_MULTIPLIERS[medal_id]
        
        # Cap at 100% bonus from achievements
        total_multiplier = min(total_multiplier, 1.0)
        
        return base_reward * total_multiplier
    
    def update_streak(self, user_id: int, streak_type: str = 'daily'):
        """Update user's streak"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current streak info
        streak_info = self.get_streak_info(user_id, streak_type)
        current_time = int(time.time())
        
        # Check if streak continues or resets
        if streak_info.is_active:
            new_streak = streak_info.current_streak + 1
            best_streak = max(streak_info.best_streak, new_streak)
        else:
            new_streak = 1
            best_streak = max(streak_info.best_streak, 1)
        
        # Update database
        if streak_type == 'daily':
            cursor.execute('''
                INSERT INTO streaks (user_id, daily_streak, daily_best, daily_last_activity)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    daily_streak = ?,
                    daily_best = ?,
                    daily_last_activity = ?
            ''', (user_id, new_streak, best_streak, current_time,
                  new_streak, best_streak, current_time))
        else:  # weekly
            cursor.execute('''
                INSERT INTO streaks (user_id, weekly_streak, weekly_best, weekly_last_activity)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    weekly_streak = ?,
                    weekly_best = ?,
                    weekly_last_activity = ?
            ''', (user_id, new_streak, best_streak, current_time,
                  new_streak, best_streak, current_time))
        
        conn.commit()
        conn.close()
        
        # Award streak XP if profile manager available
        if self.profile_manager and new_streak in self.STREAK_BONUSES.get(streak_type, {}):
            bonus_xp = 100 * new_streak  # 100 XP per streak day/week
            self.profile_manager.award_xp(
                user_id, 
                bonus_xp, 
                f"{streak_type.title()} streak milestone: {new_streak}"
            )
    
    def get_streak_info(self, user_id: int, streak_type: str = 'daily') -> StreakInfo:
        """Get user's streak information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM streaks WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return StreakInfo(streak_type=streak_type)
        
        if streak_type == 'daily':
            return StreakInfo(
                current_streak=row[1],
                best_streak=row[2],
                last_activity=row[3],
                streak_type='daily'
            )
        else:  # weekly
            return StreakInfo(
                current_streak=row[4],
                best_streak=row[5],
                last_activity=row[6],
                streak_type='weekly'
            )
    
    def record_period_activity(self, user_id: int, trades: int, 
                             profit: float, xp: int, rewards: float):
        """Record activity for period aggregations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = int(time.time())
        
        # Update daily
        daily_key = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
        self._update_aggregation(cursor, user_id, 'daily', daily_key, 
                               trades, profit, xp, rewards)
        
        # Update weekly
        weekly_key = datetime.fromtimestamp(current_time).strftime('%Y-W%U')
        self._update_aggregation(cursor, user_id, 'weekly', weekly_key,
                               trades, profit, xp, rewards)
        
        # Update monthly
        monthly_key = datetime.fromtimestamp(current_time).strftime('%Y-%m')
        self._update_aggregation(cursor, user_id, 'monthly', monthly_key,
                               trades, profit, xp, rewards)
        
        conn.commit()
        conn.close()
    
    def _update_aggregation(self, cursor, user_id: int, period_type: str,
                          period_key: str, trades: int, profit: float,
                          xp: int, rewards: float):
        """Update period aggregation"""
        cursor.execute('''
            INSERT INTO reward_aggregations 
            (user_id, period_type, period_key, total_trades, total_profit,
             total_xp, total_rewards, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, period_type, period_key) DO UPDATE SET
                total_trades = total_trades + ?,
                total_profit = total_profit + ?,
                total_xp = total_xp + ?,
                total_rewards = total_rewards + ?,
                last_updated = ?
        ''', (user_id, period_type, period_key, trades, profit, xp, rewards,
              int(time.time()), trades, profit, xp, rewards, int(time.time())))
    
    def get_period_summary(self, user_id: int, 
                          period: RewardPeriod) -> Dict:
        """Get reward summary for a specific period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine period key
        current_time = datetime.now()
        if period == RewardPeriod.DAILY:
            period_key = current_time.strftime('%Y-%m-%d')
        elif period == RewardPeriod.WEEKLY:
            period_key = current_time.strftime('%Y-W%U')
        else:  # monthly
            period_key = current_time.strftime('%Y-%m')
        
        # Get aggregation
        cursor.execute('''
            SELECT total_trades, total_profit, total_xp, total_rewards
            FROM reward_aggregations
            WHERE user_id = ? AND period_type = ? AND period_key = ?
        ''', (user_id, period.value, period_key))
        
        row = cursor.fetchone()
        
        if row:
            summary = {
                'period': period.value,
                'period_key': period_key,
                'total_trades': row[0],
                'total_profit': row[1],
                'total_xp': row[2],
                'total_rewards': row[3],
                'average_reward_per_trade': row[3] / row[0] if row[0] > 0 else 0
            }
        else:
            summary = {
                'period': period.value,
                'period_key': period_key,
                'total_trades': 0,
                'total_profit': 0.0,
                'total_xp': 0,
                'total_rewards': 0.0,
                'average_reward_per_trade': 0.0
            }
        
        # Get historical comparison
        historical = self._get_historical_comparison(cursor, user_id, 
                                                   period, period_key)
        summary['historical'] = historical
        
        conn.close()
        return summary
    
    def _get_historical_comparison(self, cursor, user_id: int,
                                  period: RewardPeriod, 
                                  current_key: str) -> Dict:
        """Get historical comparison data"""
        # Get last 5 periods
        cursor.execute('''
            SELECT period_key, total_trades, total_profit, total_rewards
            FROM reward_aggregations
            WHERE user_id = ? AND period_type = ? AND period_key < ?
            ORDER BY period_key DESC
            LIMIT 5
        ''', (user_id, period.value, current_key))
        
        historical = []
        for row in cursor.fetchall():
            historical.append({
                'period_key': row[0],
                'trades': row[1],
                'profit': row[2],
                'rewards': row[3]
            })
        
        # Calculate averages
        if historical:
            avg_trades = sum(h['trades'] for h in historical) / len(historical)
            avg_profit = sum(h['profit'] for h in historical) / len(historical)
            avg_rewards = sum(h['rewards'] for h in historical) / len(historical)
        else:
            avg_trades = avg_profit = avg_rewards = 0
        
        return {
            'periods': historical,
            'average_trades': avg_trades,
            'average_profit': avg_profit,
            'average_rewards': avg_rewards
        }
    
    def get_achievement_rewards_summary(self, user_id: int) -> Dict:
        """Get summary of achievement-based rewards"""
        earned_medals = []
        total_xp_from_achievements = 0
        
        if self.profile_manager:
            medals = self.profile_manager.get_user_medals(user_id)
            for medal in medals:
                if medal['earned']:
                    earned_medals.append({
                        'id': medal['id'],
                        'name': medal['name'],
                        'xp_reward': medal['xp_reward'],
                        'reward_multiplier': self.ACHIEVEMENT_MULTIPLIERS.get(
                            medal['id'], 0
                        )
                    })
                    total_xp_from_achievements += medal['xp_reward']
        
        # Calculate total reward multiplier
        total_multiplier = sum(
            self.ACHIEVEMENT_MULTIPLIERS.get(m['id'], 0) 
            for m in earned_medals
        )
        
        return {
            'earned_achievements': len(earned_medals),
            'total_xp_earned': total_xp_from_achievements,
            'total_reward_multiplier': min(total_multiplier, 1.0),
            'achievements': earned_medals,
            'potential_multiplier': sum(self.ACHIEVEMENT_MULTIPLIERS.values())
        }
    
    def calculate_tier_upgrade_benefit(self, user_id: int, 
                                     current_profit: float) -> Dict:
        """Calculate benefit of upgrading to APEX tier"""
        # Calculate rewards for both tiers
        standard_reward = self.calculate_reward(
            user_id, current_profit, RiskTier.STANDARD
        )
        apex_reward = self.calculate_reward(
            user_id, current_profit, RiskTier.APEX
        )
        
        # Calculate difference
        additional_reward = apex_reward.total_amount - standard_reward.total_amount
        percentage_increase = (additional_reward / standard_reward.total_amount) * 100
        
        return {
            'standard_reward': standard_reward.total_amount,
            'apex_reward': apex_reward.total_amount,
            'additional_reward': additional_reward,
            'percentage_increase': percentage_increase,
            'breakdowns': {
                'standard': standard_reward.breakdown,
                'apex': apex_reward.breakdown
            }
        }
    
    def get_comprehensive_rewards_dashboard(self, user_id: int) -> Dict:
        """Get comprehensive rewards dashboard for user"""
        # Get period summaries
        daily = self.get_period_summary(user_id, RewardPeriod.DAILY)
        weekly = self.get_period_summary(user_id, RewardPeriod.WEEKLY)
        monthly = self.get_period_summary(user_id, RewardPeriod.MONTHLY)
        
        # Get streak info
        daily_streak = self.get_streak_info(user_id, 'daily')
        weekly_streak = self.get_streak_info(user_id, 'weekly')
        
        # Get achievement summary
        achievements = self.get_achievement_rewards_summary(user_id)
        
        # Get current tier info
        user_xp = 0
        current_tier = None
        next_tier = None
        
        if self.profile_manager:
            user_stats = self.profile_manager.get_user_stats(user_id)
            if user_stats:
                user_xp = user_stats.total_xp
        
        # Find current and next tier
        for i, tier in enumerate(self.XP_TIERS):
            if user_xp >= tier['min_xp']:
                current_tier = tier
                if i + 1 < len(self.XP_TIERS):
                    next_tier = self.XP_TIERS[i + 1]
        
        return {
            'user_id': user_id,
            'current_xp': user_xp,
            'xp_tier': {
                'current': current_tier,
                'next': next_tier,
                'progress_to_next': (user_xp - current_tier['min_xp']) / 
                                   (next_tier['min_xp'] - current_tier['min_xp']) * 100
                                   if next_tier else 100
            },
            'periods': {
                'daily': daily,
                'weekly': weekly,
                'monthly': monthly
            },
            'streaks': {
                'daily': asdict(daily_streak),
                'weekly': asdict(weekly_streak),
                'next_bonuses': {
                    'daily': self._get_next_streak_bonus(daily_streak.current_streak, 'daily'),
                    'weekly': self._get_next_streak_bonus(weekly_streak.current_streak, 'weekly')
                }
            },
            'achievements': achievements,
            'total_multipliers': {
                'xp_tier': current_tier['bonus'] if current_tier else 0,
                'daily_streak': self._calculate_streak_bonus(user_id, 'daily'),
                'weekly_streak': self._calculate_streak_bonus(user_id, 'weekly'),
                'achievements': achievements['total_reward_multiplier']
            }
        }
    
    def _get_next_streak_bonus(self, current_streak: int, 
                              streak_type: str) -> Optional[Dict]:
        """Get next streak milestone and bonus"""
        bonuses = self.STREAK_BONUSES.get(streak_type, {})
        
        for days, bonus in sorted(bonuses.items()):
            if current_streak < days:
                return {
                    'days_required': days,
                    'days_remaining': days - current_streak,
                    'bonus_percentage': bonus * 100
                }
        
        return None
    
    def simulate_reward(self, user_id: int, profit: float,
                       risk_tier: str = "STANDARD") -> Dict:
        """Simulate reward calculation for planning"""
        tier = RiskTier.APEX if risk_tier == "APEX" else RiskTier.STANDARD
        calculation = self.calculate_reward(user_id, profit, tier)
        
        return {
            'profit': profit,
            'risk_tier': risk_tier,
            'total_reward': calculation.total_amount,
            'effective_rate': (calculation.total_amount / profit) * 100,
            'breakdown': calculation.breakdown
        }