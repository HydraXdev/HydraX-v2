"""
Daily Login Streak System for BITTEN Platform
Comprehensive streak tracking with timezone handling, grace periods, and user retention features
"""

import json
import pytz
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import logging

# Note: These imports would be used in production with actual database
# from .database.models import UserLoginStreak, RewardClaim
# from .database.connection import get_db_session

logger = logging.getLogger(__name__)


class StreakStatus(Enum):
    """Streak status types"""
    ACTIVE = "active"
    BROKEN = "broken"
    GRACE_PERIOD = "grace_period"
    COMEBACK = "comeback"
    PROTECTED = "protected"


class StreakProtectionType(Enum):
    """Types of streak protection"""
    FREE_MONTHLY = "free_monthly"  # 1 free miss per month
    PREMIUM = "premium"           # Premium protection items
    WEEKEND_PASS = "weekend_pass" # Special weekend protection


@dataclass
class StreakData:
    """Complete streak information"""
    user_id: str
    current_streak: int
    longest_streak: int
    last_login_date: str
    timezone: str
    status: StreakStatus
    grace_period_ends: Optional[str]
    protection_used: bool
    comeback_bonus_eligible: bool
    next_milestone: Optional[int]
    days_until_milestone: Optional[int]
    total_login_days: int
    streak_freeze_available: bool
    monthly_protection_used: bool


@dataclass
class LoginReward:
    """Login reward information"""
    base_xp: int
    streak_multiplier: float
    milestone_bonus: int
    comeback_bonus: int
    total_xp: int
    badges_unlocked: List[str]
    special_rewards: List[Dict[str, Any]]


class DailyStreakSystem:
    """Comprehensive daily login streak tracking system"""
    
    # Milestone rewards (days: reward_multiplier)
    MILESTONE_REWARDS = {
        7: {"xp_multiplier": 1.5, "badge": "week_warrior", "special": "streak_freeze"},
        30: {"xp_multiplier": 2.0, "badge": "monthly_master", "special": "xp_booster"},
        90: {"xp_multiplier": 2.5, "badge": "quarterly_champion", "special": "premium_signals"},
        180: {"xp_multiplier": 3.0, "badge": "half_year_hero", "special": "exclusive_analysis"},
        365: {"xp_multiplier": 5.0, "badge": "annual_legend", "special": "vip_access"}
    }
    
    # XP multipliers based on streak length
    STREAK_MULTIPLIERS = {
        1: 1.0,   # Base
        3: 1.1,   # 10% bonus at 3 days
        7: 1.2,   # 20% bonus at 1 week
        14: 1.3,  # 30% bonus at 2 weeks
        30: 1.5,  # 50% bonus at 1 month
        60: 1.8,  # 80% bonus at 2 months
        90: 2.0,  # 100% bonus at 3 months
        180: 2.5, # 150% bonus at 6 months
        365: 3.0  # 200% bonus at 1 year
    }
    
    # Comeback bonuses (days_away: bonus_multiplier)
    COMEBACK_BONUSES = {
        1: 1.2,   # 20% bonus for 1 day away
        2: 1.5,   # 50% bonus for 2 days away
        3: 1.8,   # 80% bonus for 3 days away
        7: 2.0,   # 100% bonus for 1 week away
        14: 2.5,  # 150% bonus for 2 weeks away
        30: 3.0   # 200% bonus for 1 month away
    }
    
    # Base daily login XP
    BASE_LOGIN_XP = 50
    
    # Grace period hours (24 hours + 6 hour grace)
    GRACE_PERIOD_HOURS = 30
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "bitten_streaks.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize streak tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Streak protection tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streak_protection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                protection_type TEXT NOT NULL,
                used_date TEXT NOT NULL,
                streak_saved INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Daily login history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                login_date TEXT NOT NULL,
                login_timestamp TEXT NOT NULL,
                timezone TEXT NOT NULL,
                streak_day INTEGER NOT NULL,
                xp_earned INTEGER NOT NULL,
                bonuses_applied TEXT DEFAULT '[]',
                UNIQUE(user_id, login_date)
            )
        ''')
        
        # Milestone achievements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streak_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                milestone_day INTEGER NOT NULL,
                achieved_date TEXT NOT NULL,
                rewards_claimed TEXT DEFAULT '[]',
                special_rewards TEXT DEFAULT '[]',
                UNIQUE(user_id, milestone_day)
            )
        ''')
        
        # Streak calendar (for visual representation)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streak_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                calendar_date TEXT NOT NULL,
                status TEXT NOT NULL,  -- 'login', 'missed', 'protected', 'grace'
                streak_count INTEGER,
                notes TEXT,
                UNIQUE(user_id, calendar_date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_login(self, user_id: str, user_timezone: str = "UTC") -> Tuple[StreakData, LoginReward]:
        """
        Record a user login and calculate streak/rewards
        
        Args:
            user_id: User identifier
            user_timezone: User's timezone (e.g., 'America/New_York')
            
        Returns:
            Tuple of (StreakData, LoginReward)
        """
        try:
            tz = pytz.timezone(user_timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            tz = pytz.UTC
            user_timezone = "UTC"
        
        now = datetime.now(tz)
        today_date = now.date().isoformat()
        
        # Get or create user streak record (simplified for demo)
        # In production, this would use the database models
        user_streak = {
            'user_id': user_id,
            'current_streak': 0,
            'longest_streak': 0,
            'total_logins': 0,
            'last_login': None
        }
        
        # Check if already logged in today
        if self._already_logged_today(user_id, today_date):
            streak_data = self._get_current_streak_data(user_id, user_timezone)
            return streak_data, LoginReward(0, 1.0, 0, 0, 0, [], [])
        
        # Calculate new streak
        last_login_date = user_streak.last_login.date().isoformat() if user_streak.last_login else None
        streak_data = self._calculate_new_streak(user_id, last_login_date, today_date, user_timezone)
        
        # Calculate rewards
        login_reward = self._calculate_login_rewards(user_id, streak_data)
        
        # Update database
        self._update_streak_record(user_id, streak_data, now)
        self._record_daily_login(user_id, today_date, now.isoformat(), user_timezone, 
                               streak_data.current_streak, login_reward.total_xp)
        self._update_calendar(user_id, today_date, "login", streak_data.current_streak)
        
        # Check for milestone achievements
        self._check_and_award_milestones(user_id, streak_data.current_streak, today_date)
        
        return streak_data, login_reward
    
    def _already_logged_today(self, user_id: str, date: str) -> bool:
        """Check if user already logged in today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 1 FROM daily_logins 
            WHERE user_id = ? AND login_date = ?
        ''', (user_id, date))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def _calculate_new_streak(self, user_id: str, last_login_date: Optional[str], 
                            today_date: str, timezone: str) -> StreakData:
        """Calculate the new streak after login"""
        
        if not last_login_date:
            # First login ever
            return StreakData(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_login_date=today_date,
                timezone=timezone,
                status=StreakStatus.ACTIVE,
                grace_period_ends=None,
                protection_used=False,
                comeback_bonus_eligible=False,
                next_milestone=self._get_next_milestone(1),
                days_until_milestone=self._get_next_milestone(1) - 1 if self._get_next_milestone(1) else None,
                total_login_days=1,
                streak_freeze_available=False,
                monthly_protection_used=self._check_monthly_protection_used(user_id)
            )
        
        # Calculate days between logins
        last_date = datetime.fromisoformat(last_login_date).date()
        current_date = datetime.fromisoformat(today_date).date()
        days_gap = (current_date - last_date).days
        
        # Get current streak info
        current_streak_data = self._get_current_streak_data(user_id, timezone)
        
        if days_gap == 1:
            # Consecutive day login
            new_streak = current_streak_data.current_streak + 1
            status = StreakStatus.ACTIVE
            comeback_bonus = False
            
        elif days_gap <= 2 and self._can_use_grace_period(user_id, current_streak_data.current_streak):
            # Grace period save
            new_streak = current_streak_data.current_streak + 1
            status = StreakStatus.GRACE_PERIOD
            comeback_bonus = False
            
        elif self._can_use_protection(user_id, days_gap):
            # Protection item save
            new_streak = current_streak_data.current_streak + 1
            status = StreakStatus.PROTECTED
            comeback_bonus = False
            self._use_protection(user_id, days_gap, current_streak_data.current_streak)
            
        else:
            # Streak broken, calculate comeback bonus
            new_streak = 1
            status = StreakStatus.COMEBACK
            comeback_bonus = True
        
        longest_streak = max(current_streak_data.longest_streak, new_streak)
        
        return StreakData(
            user_id=user_id,
            current_streak=new_streak,
            longest_streak=longest_streak,
            last_login_date=today_date,
            timezone=timezone,
            status=status,
            grace_period_ends=None,
            protection_used=status == StreakStatus.PROTECTED,
            comeback_bonus_eligible=comeback_bonus,
            next_milestone=self._get_next_milestone(new_streak),
            days_until_milestone=self._get_next_milestone(new_streak) - new_streak if self._get_next_milestone(new_streak) else None,
            total_login_days=current_streak_data.total_login_days + 1,
            streak_freeze_available=self._has_streak_freeze(user_id),
            monthly_protection_used=self._check_monthly_protection_used(user_id)
        )
    
    def _calculate_login_rewards(self, user_id: str, streak_data: StreakData) -> LoginReward:
        """Calculate rewards for the login"""
        
        # Base XP
        base_xp = self.BASE_LOGIN_XP
        
        # Streak multiplier
        streak_multiplier = self._get_streak_multiplier(streak_data.current_streak)
        
        # Milestone bonus
        milestone_bonus = 0
        if streak_data.current_streak in self.MILESTONE_REWARDS:
            milestone_bonus = base_xp * 2  # Double XP for milestones
        
        # Comeback bonus
        comeback_bonus = 0
        if streak_data.comeback_bonus_eligible:
            # Calculate days away for comeback bonus
            last_login = self._get_last_real_login_date(user_id)
            if last_login:
                days_away = (datetime.now().date() - datetime.fromisoformat(last_login).date()).days
                comeback_multiplier = self._get_comeback_bonus(days_away)
                comeback_bonus = int(base_xp * comeback_multiplier)
        
        # Calculate total XP
        streak_xp = int(base_xp * streak_multiplier)
        total_xp = streak_xp + milestone_bonus + comeback_bonus
        
        # Badges unlocked
        badges = []
        special_rewards = []
        
        if streak_data.current_streak in self.MILESTONE_REWARDS:
            milestone_info = self.MILESTONE_REWARDS[streak_data.current_streak]
            badges.append(milestone_info["badge"])
            special_rewards.append({
                "type": "special_item",
                "item": milestone_info["special"],
                "description": f"Unlocked at {streak_data.current_streak} day streak"
            })
        
        return LoginReward(
            base_xp=base_xp,
            streak_multiplier=streak_multiplier,
            milestone_bonus=milestone_bonus,
            comeback_bonus=comeback_bonus,
            total_xp=total_xp,
            badges_unlocked=badges,
            special_rewards=special_rewards
        )
    
    def _get_streak_multiplier(self, streak_days: int) -> float:
        """Get XP multiplier based on streak length"""
        multiplier = 1.0
        for days, mult in sorted(self.STREAK_MULTIPLIERS.items()):
            if streak_days >= days:
                multiplier = mult
        return multiplier
    
    def _get_comeback_bonus(self, days_away: int) -> float:
        """Get comeback bonus multiplier"""
        for days, bonus in sorted(self.COMEBACK_BONUSES.items(), reverse=True):
            if days_away >= days:
                return bonus
        return 1.0
    
    def _get_next_milestone(self, current_streak: int) -> Optional[int]:
        """Get the next milestone to achieve"""
        for milestone in sorted(self.MILESTONE_REWARDS.keys()):
            if current_streak < milestone:
                return milestone
        return None
    
    def _can_use_grace_period(self, user_id: str, current_streak: int) -> bool:
        """Check if user can use grace period"""
        # Grace period only available for streaks >= 7 days
        return current_streak >= 7
    
    def _can_use_protection(self, user_id: str, days_gap: int) -> bool:
        """Check if user can use streak protection"""
        # Check if monthly protection is available
        if not self._check_monthly_protection_used(user_id) and days_gap <= 3:
            return True
        
        # Check for premium protection items
        return self._has_premium_protection(user_id)
    
    def _use_protection(self, user_id: str, days_gap: int, streak_saved: int):
        """Use streak protection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine protection type
        if not self._check_monthly_protection_used(user_id):
            protection_type = StreakProtectionType.FREE_MONTHLY.value
        else:
            protection_type = StreakProtectionType.PREMIUM.value
        
        cursor.execute('''
            INSERT INTO streak_protection 
            (user_id, protection_type, used_date, streak_saved)
            VALUES (?, ?, ?, ?)
        ''', (user_id, protection_type, datetime.now().isoformat(), streak_saved))
        
        conn.commit()
        conn.close()
    
    def _check_monthly_protection_used(self, user_id: str) -> bool:
        """Check if monthly free protection was used this month"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            SELECT 1 FROM streak_protection 
            WHERE user_id = ? AND protection_type = ? 
            AND strftime('%Y-%m', used_date) = ?
        ''', (user_id, StreakProtectionType.FREE_MONTHLY.value, current_month))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def _has_premium_protection(self, user_id: str) -> bool:
        """Check if user has premium protection items"""
        # This would integrate with your inventory/item system
        # For now, return False
        return False
    
    def _has_streak_freeze(self, user_id: str) -> bool:
        """Check if user has streak freeze available"""
        # This would check user's inventory for streak freeze items
        # For now, return True if they have a 7+ day streak
        streak_data = self._get_current_streak_data(user_id, "UTC")
        return streak_data.current_streak >= 7
    
    def _get_current_streak_data(self, user_id: str, timezone: str) -> StreakData:
        """Get current streak data for user"""
        with get_db_session() as session:
            user_streak = session.query(UserLoginStreak).filter_by(user_id=user_id).first()
            
            if not user_streak:
                return StreakData(
                    user_id=user_id,
                    current_streak=0,
                    longest_streak=0,
                    last_login_date="",
                    timezone=timezone,
                    status=StreakStatus.ACTIVE,
                    grace_period_ends=None,
                    protection_used=False,
                    comeback_bonus_eligible=False,
                    next_milestone=7,
                    days_until_milestone=7,
                    total_login_days=0,
                    streak_freeze_available=False,
                    monthly_protection_used=False
                )
            
            last_login_date = user_streak.last_login.date().isoformat() if user_streak.last_login else ""
            
            return StreakData(
                user_id=user_id,
                current_streak=user_streak.current_streak,
                longest_streak=user_streak.longest_streak,
                last_login_date=last_login_date,
                timezone=timezone,
                status=StreakStatus.ACTIVE,
                grace_period_ends=None,
                protection_used=False,
                comeback_bonus_eligible=False,
                next_milestone=self._get_next_milestone(user_streak.current_streak),
                days_until_milestone=self._get_next_milestone(user_streak.current_streak) - user_streak.current_streak if self._get_next_milestone(user_streak.current_streak) else None,
                total_login_days=user_streak.total_logins,
                streak_freeze_available=self._has_streak_freeze(user_id),
                monthly_protection_used=self._check_monthly_protection_used(user_id)
            )
    
    def _update_streak_record(self, user_id: str, streak_data: StreakData, timestamp: datetime):
        """Update the main streak record"""
        with get_db_session() as session:
            user_streak = session.query(UserLoginStreak).filter_by(user_id=user_id).first()
            
            if user_streak:
                user_streak.current_streak = streak_data.current_streak
                user_streak.longest_streak = streak_data.longest_streak
                user_streak.last_login = timestamp
                user_streak.total_logins += 1
                user_streak.updated_at = timestamp
            else:
                user_streak = UserLoginStreak(
                    user_id=user_id,
                    current_streak=streak_data.current_streak,
                    longest_streak=streak_data.longest_streak,
                    last_login=timestamp,
                    total_logins=1,
                    created_at=timestamp,
                    updated_at=timestamp
                )
                session.add(user_streak)
            
            session.commit()
    
    def _record_daily_login(self, user_id: str, login_date: str, timestamp: str, 
                           timezone: str, streak_day: int, xp_earned: int):
        """Record daily login in history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO daily_logins 
            (user_id, login_date, login_timestamp, timezone, streak_day, xp_earned)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, login_date, timestamp, timezone, streak_day, xp_earned))
        
        conn.commit()
        conn.close()
    
    def _update_calendar(self, user_id: str, date: str, status: str, streak_count: int):
        """Update streak calendar"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO streak_calendar 
            (user_id, calendar_date, status, streak_count)
            VALUES (?, ?, ?, ?)
        ''', (user_id, date, status, streak_count))
        
        conn.commit()
        conn.close()
    
    def _check_and_award_milestones(self, user_id: str, streak_days: int, date: str):
        """Check and award milestone achievements"""
        if streak_days in self.MILESTONE_REWARDS:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if milestone already awarded
            cursor.execute('''
                SELECT 1 FROM streak_milestones 
                WHERE user_id = ? AND milestone_day = ?
            ''', (user_id, streak_days))
            
            if not cursor.fetchone():
                milestone_info = self.MILESTONE_REWARDS[streak_days]
                rewards = [milestone_info["badge"], milestone_info["special"]]
                
                cursor.execute('''
                    INSERT INTO streak_milestones 
                    (user_id, milestone_day, achieved_date, rewards_claimed)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, streak_days, date, json.dumps(rewards)))
                
                conn.commit()
            
            conn.close()
    
    def _get_last_real_login_date(self, user_id: str) -> Optional[str]:
        """Get the last actual login date (not protected)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT login_date FROM daily_logins 
            WHERE user_id = ? 
            ORDER BY login_date DESC 
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_streak_calendar(self, user_id: str, year: int, month: int) -> Dict[str, Any]:
        """Get visual streak calendar for a specific month"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get calendar data for the month
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month+1:02d}-01"
        
        cursor.execute('''
            SELECT calendar_date, status, streak_count, notes
            FROM streak_calendar 
            WHERE user_id = ? AND calendar_date >= ? AND calendar_date < ?
            ORDER BY calendar_date
        ''', (user_id, start_date, end_date))
        
        calendar_data = {}
        for row in cursor.fetchall():
            calendar_data[row[0]] = {
                "status": row[1],
                "streak_count": row[2],
                "notes": row[3]
            }
        
        # Get summary stats for the month
        cursor.execute('''
            SELECT COUNT(*), AVG(streak_count), MAX(streak_count)
            FROM streak_calendar 
            WHERE user_id = ? AND calendar_date >= ? AND calendar_date < ?
            AND status = 'login'
        ''', (user_id, start_date, end_date))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            "year": year,
            "month": month,
            "calendar_data": calendar_data,
            "stats": {
                "login_days": stats[0] or 0,
                "average_streak": round(stats[1] or 0, 1),
                "max_streak": stats[2] or 0
            }
        }
    
    def get_user_streak_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive streak summary for user"""
        streak_data = self._get_current_streak_data(user_id, "UTC")
        
        # Get milestone progress
        milestones = []
        for milestone_day, info in self.MILESTONE_REWARDS.items():
            achieved = milestone_day <= streak_data.current_streak
            milestones.append({
                "day": milestone_day,
                "achieved": achieved,
                "badge": info["badge"],
                "special_reward": info["special"],
                "xp_multiplier": info["xp_multiplier"],
                "days_remaining": max(0, milestone_day - streak_data.current_streak) if not achieved else 0
            })
        
        # Get recent login history
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT login_date, streak_day, xp_earned
            FROM daily_logins 
            WHERE user_id = ?
            ORDER BY login_date DESC 
            LIMIT 30
        ''', (user_id,))
        
        recent_logins = [
            {"date": row[0], "streak_day": row[1], "xp_earned": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Get protection usage
        cursor.execute('''
            SELECT protection_type, used_date, streak_saved
            FROM streak_protection 
            WHERE user_id = ?
            ORDER BY used_date DESC 
            LIMIT 10
        ''', (user_id,))
        
        protection_history = [
            {"type": row[0], "date": row[1], "streak_saved": row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "current_streak": asdict(streak_data),
            "milestones": milestones,
            "recent_logins": recent_logins,
            "protection_history": protection_history,
            "stats": {
                "total_xp_from_streaks": self._calculate_total_streak_xp(user_id),
                "average_streak_length": self._calculate_average_streak(user_id),
                "streak_recovery_rate": self._calculate_recovery_rate(user_id)
            }
        }
    
    def _calculate_total_streak_xp(self, user_id: str) -> int:
        """Calculate total XP earned from streaks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(xp_earned) FROM daily_logins WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] or 0
    
    def _calculate_average_streak(self, user_id: str) -> float:
        """Calculate average streak length"""
        # This would require more complex logic to identify streak periods
        # For now, return a simple calculation
        streak_data = self._get_current_streak_data(user_id, "UTC")
        return streak_data.longest_streak / 2.0  # Simplified
    
    def _calculate_recovery_rate(self, user_id: str) -> float:
        """Calculate how quickly user recovers from broken streaks"""
        # This would analyze historical data to see how quickly user gets back to long streaks
        # For now, return a default value
        return 0.75  # 75% recovery rate
    
    def use_streak_freeze(self, user_id: str) -> bool:
        """Use a streak freeze item to protect current streak"""
        if not self._has_streak_freeze(user_id):
            return False
        
        # This would integrate with inventory system to consume the item
        # For now, just return True
        logger.info(f"User {user_id} used streak freeze")
        return True
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get streak leaderboard"""
        with get_db_session() as session:
            top_streaks = session.query(UserLoginStreak).order_by(
                UserLoginStreak.current_streak.desc(),
                UserLoginStreak.longest_streak.desc()
            ).limit(limit).all()
            
            leaderboard = []
            for i, streak in enumerate(top_streaks, 1):
                leaderboard.append({
                    "rank": i,
                    "user_id": streak.user_id,
                    "current_streak": streak.current_streak,
                    "longest_streak": streak.longest_streak,
                    "total_logins": streak.total_logins,
                    "next_milestone": self._get_next_milestone(streak.current_streak)
                })
            
            return leaderboard


# Example usage and testing
if __name__ == "__main__":
    # Initialize streak system
    streak_system = DailyStreakSystem()
    
    # Simulate user login
    user_id = "test_user_123"
    timezone = "America/New_York"
    
    print("=== BITTEN Daily Streak System Demo ===\n")
    
    # Record login
    streak_data, login_reward = streak_system.record_login(user_id, timezone)
    
    print(f"Login recorded for user: {user_id}")
    print(f"Current streak: {streak_data.current_streak} days")
    print(f"Longest streak: {streak_data.longest_streak} days")
    print(f"Status: {streak_data.status.value}")
    print(f"XP earned: {login_reward.total_xp}")
    print(f"Streak multiplier: {login_reward.streak_multiplier}x")
    
    if login_reward.badges_unlocked:
        print(f"Badges unlocked: {', '.join(login_reward.badges_unlocked)}")
    
    if streak_data.next_milestone:
        print(f"Next milestone: {streak_data.next_milestone} days ({streak_data.days_until_milestone} days remaining)")
    
    # Get user summary
    print("\n=== User Streak Summary ===")
    summary = streak_system.get_user_streak_summary(user_id)
    print(f"Total streak XP: {summary['stats']['total_xp_from_streaks']}")
    print(f"Average streak: {summary['stats']['average_streak_length']:.1f} days")
    
    # Show milestones
    print("\n=== Milestone Progress ===")
    for milestone in summary['milestones'][:3]:  # Show first 3
        status = "✅" if milestone['achieved'] else f"⏳ {milestone['days_remaining']} days"
        print(f"{milestone['day']} days: {milestone['badge']} {status}")
    
    print("\n=== Streak System Ready! ===")