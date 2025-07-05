# user_profile.py
# BITTEN User Profile Manager - Stats, medals, recruiting system

import json
import time
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib

@dataclass
class UserStats:
    """User statistics tracking"""
    user_id: int
    total_xp: int = 0
    missions_completed: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_profit: float = 0.0
    largest_win: float = 0.0
    win_streak: int = 0
    current_streak: int = 0
    rank_achieved: str = "RECRUIT"
    joined_at: int = 0
    last_active: int = 0
    
    @property
    def success_rate(self) -> float:
        total = self.successful_trades + self.failed_trades
        if total == 0:
            return 0.0
        return (self.successful_trades / total) * 100

@dataclass
class Medal:
    """Medal/achievement structure"""
    id: str
    name: str
    description: str
    icon: str
    xp_reward: int
    requirement_type: str  # trades, profit, streak, recruits
    requirement_value: int
    tier: str  # bronze, silver, gold, platinum
    
@dataclass
class Recruit:
    """Recruit tracking"""
    recruit_id: int
    recruiter_id: int
    username: str
    joined_at: int
    is_active: bool = True
    trades_completed: int = 0
    xp_contributed: int = 0

class UserProfileManager:
    """Manages user profiles, stats, and recruiting"""
    
    # Define medals
    MEDALS = [
        # Trade-based medals
        Medal("first_blood", "First Blood", "Complete your first trade", "🩸", 50, "trades", 1, "bronze"),
        Medal("marksman", "Marksman", "Complete 10 successful trades", "🎯", 100, "trades", 10, "bronze"),
        Medal("sniper", "Sniper", "Complete 50 successful trades", "🔫", 250, "trades", 50, "silver"),
        Medal("elite_sniper", "Elite Sniper", "Complete 100 successful trades", "💀", 500, "trades", 100, "gold"),
        Medal("legendary_sniper", "Legendary Sniper", "Complete 500 successful trades", "⚡", 1000, "trades", 500, "platinum"),
        
        # Profit-based medals
        Medal("profitable", "Profitable", "Achieve $100 total profit", "💰", 100, "profit", 100, "bronze"),
        Medal("wealthy", "Wealthy", "Achieve $1,000 total profit", "💎", 300, "profit", 1000, "silver"),
        Medal("mogul", "Mogul", "Achieve $10,000 total profit", "👑", 1000, "profit", 10000, "gold"),
        
        # Streak-based medals
        Medal("hot_hand", "Hot Hand", "5 trade win streak", "🔥", 150, "streak", 5, "bronze"),
        Medal("on_fire", "On Fire", "10 trade win streak", "🌟", 300, "streak", 10, "silver"),
        Medal("unstoppable", "Unstoppable", "20 trade win streak", "⚡", 750, "streak", 20, "gold"),
        
        # Recruiting medals
        Medal("recruiter", "Recruiter", "Recruit 1 active trader", "🤝", 100, "recruits", 1, "bronze"),
        Medal("squad_leader", "Squad Leader", "Recruit 5 active traders", "👥", 300, "recruits", 5, "silver"),
        Medal("commander", "Commander", "Recruit 20 active traders", "🎖️", 1000, "recruits", 20, "gold"),
        Medal("general", "General", "Recruit 50 active traders", "⭐", 2500, "recruits", 50, "platinum"),
    ]
    
    # XP rewards
    XP_REWARDS = {
        'trade_executed': 10,
        'trade_success': 25,
        'trade_failed': 5,
        'recruit_joined': 50,
        'recruit_first_trade': 100,
        'recruit_milestone': 200,  # Every 10 trades by recruit
        'daily_login': 20,
        'weekly_streak': 100,
    }
    
    # Rank thresholds
    RANK_THRESHOLDS = {
        'RECRUIT': 0,
        'PRIVATE': 100,
        'CORPORAL': 500,
        'SERGEANT': 1000,
        'LIEUTENANT': 2500,
        'CAPTAIN': 5000,
        'MAJOR': 10000,
        'COLONEL': 25000,
        'GENERAL': 50000,
        'COMMANDER': 100000
    }
    
    def __init__(self, db_path: str = "bitten_profiles.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                total_xp INTEGER DEFAULT 0,
                missions_completed INTEGER DEFAULT 0,
                successful_trades INTEGER DEFAULT 0,
                failed_trades INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0.0,
                largest_win REAL DEFAULT 0.0,
                win_streak INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                rank_achieved TEXT DEFAULT 'RECRUIT',
                joined_at INTEGER,
                last_active INTEGER
            )
        ''')
        
        # Medals earned table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_medals (
                user_id INTEGER,
                medal_id TEXT,
                earned_at INTEGER,
                PRIMARY KEY (user_id, medal_id)
            )
        ''')
        
        # Recruiting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recruits (
                recruit_id INTEGER PRIMARY KEY,
                recruiter_id INTEGER,
                username TEXT,
                joined_at INTEGER,
                is_active INTEGER DEFAULT 1,
                trades_completed INTEGER DEFAULT 0,
                xp_contributed INTEGER DEFAULT 0,
                FOREIGN KEY (recruiter_id) REFERENCES user_stats(user_id)
            )
        ''')
        
        # XP transactions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS xp_transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                reason TEXT,
                timestamp INTEGER,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user_profile(self, user_id: int) -> UserStats:
        """Create new user profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = UserStats(
            user_id=user_id,
            joined_at=int(time.time()),
            last_active=int(time.time())
        )
        
        cursor.execute('''
            INSERT OR IGNORE INTO user_stats 
            (user_id, joined_at, last_active) 
            VALUES (?, ?, ?)
        ''', (user_id, stats.joined_at, stats.last_active))
        
        conn.commit()
        conn.close()
        
        return stats
    
    def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return self.create_user_profile(user_id)
        
        return UserStats(
            user_id=row[0],
            total_xp=row[1],
            missions_completed=row[2],
            successful_trades=row[3],
            failed_trades=row[4],
            total_profit=row[5],
            largest_win=row[6],
            win_streak=row[7],
            current_streak=row[8],
            rank_achieved=row[9],
            joined_at=row[10],
            last_active=row[11]
        )
    
    def record_trade_execution(self, user_id: int, signal_id: str, position_id: str):
        """Record trade execution"""
        stats = self.get_user_stats(user_id)
        if not stats:
            stats = self.create_user_profile(user_id)
        
        # Award XP for execution
        self.award_xp(user_id, self.XP_REWARDS['trade_executed'], 
                     f"Executed trade {position_id}")
        
        # Update last active
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_stats 
            SET last_active = ?, missions_completed = missions_completed + 1
            WHERE user_id = ?
        ''', (int(time.time()), user_id))
        
        conn.commit()
        conn.close()
        
        # Check for medal unlocks
        self._check_medal_progress(user_id)
    
    def record_trade_result(self, user_id: int, position_id: str, 
                          profit: float, is_success: bool):
        """Record trade result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stats
        stats = self.get_user_stats(user_id)
        
        # Update stats
        if is_success:
            new_streak = stats.current_streak + 1
            best_streak = max(stats.win_streak, new_streak)
            
            cursor.execute('''
                UPDATE user_stats 
                SET successful_trades = successful_trades + 1,
                    total_profit = total_profit + ?,
                    largest_win = MAX(largest_win, ?),
                    current_streak = ?,
                    win_streak = ?
                WHERE user_id = ?
            ''', (profit, profit, new_streak, best_streak, user_id))
            
            # Award success XP
            self.award_xp(user_id, self.XP_REWARDS['trade_success'], 
                         f"Successful trade: +${profit:.2f}")
        else:
            cursor.execute('''
                UPDATE user_stats 
                SET failed_trades = failed_trades + 1,
                    total_profit = total_profit + ?,
                    current_streak = 0
                WHERE user_id = ?
            ''', (profit, user_id))
            
            # Award consolation XP
            self.award_xp(user_id, self.XP_REWARDS['trade_failed'], 
                         "Trade completed")
        
        conn.commit()
        conn.close()
        
        # Update recruiter if this user was recruited
        self._update_recruiter_stats(user_id)
        
        # Check medals
        self._check_medal_progress(user_id)
    
    def register_recruit(self, recruiter_id: int, recruit_id: int, 
                        username: str) -> bool:
        """Register a new recruit"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if already recruited
            cursor.execute('''
                SELECT recruit_id FROM recruits WHERE recruit_id = ?
            ''', (recruit_id,))
            
            if cursor.fetchone():
                conn.close()
                return False  # Already recruited
            
            # Add recruit
            cursor.execute('''
                INSERT INTO recruits 
                (recruit_id, recruiter_id, username, joined_at)
                VALUES (?, ?, ?, ?)
            ''', (recruit_id, recruiter_id, username, int(time.time())))
            
            conn.commit()
            
            # Award XP to recruiter
            self.award_xp(recruiter_id, self.XP_REWARDS['recruit_joined'],
                         f"Recruited {username}")
            
            # Create profile for recruit
            self.create_user_profile(recruit_id)
            
            conn.close()
            
            # Check recruiting medals
            self._check_medal_progress(recruiter_id)
            
            return True
            
        except Exception as e:
            conn.close()
            print(f"Error registering recruit: {e}")
            return False
    
    def get_recruiting_stats(self, user_id: int) -> Dict:
        """Get user's recruiting statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recruits
        cursor.execute('''
            SELECT COUNT(*), SUM(trades_completed), SUM(xp_contributed)
            FROM recruits 
            WHERE recruiter_id = ? AND is_active = 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        total_recruits = row[0] or 0
        total_recruit_trades = row[1] or 0
        total_recruit_xp = row[2] or 0
        
        # Get recent recruits
        cursor.execute('''
            SELECT username, joined_at, trades_completed
            FROM recruits
            WHERE recruiter_id = ?
            ORDER BY joined_at DESC
            LIMIT 5
        ''', (user_id,))
        
        recent_recruits = [
            {
                'username': row[0],
                'joined_at': row[1],
                'trades_completed': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'total_recruits': total_recruits,
            'total_recruit_trades': total_recruit_trades,
            'total_recruit_xp': total_recruit_xp,
            'recent_recruits': recent_recruits
        }
    
    def award_xp(self, user_id: int, amount: int, reason: str, details: str = ""):
        """Award XP to user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update XP
        cursor.execute('''
            UPDATE user_stats 
            SET total_xp = total_xp + ?
            WHERE user_id = ?
        ''', (amount, user_id))
        
        # Log transaction
        cursor.execute('''
            INSERT INTO xp_transactions 
            (user_id, amount, reason, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, reason, int(time.time()), details))
        
        # Check for rank up
        cursor.execute('SELECT total_xp FROM user_stats WHERE user_id = ?', (user_id,))
        total_xp = cursor.fetchone()[0]
        
        new_rank = self._calculate_rank(total_xp)
        
        cursor.execute('''
            UPDATE user_stats 
            SET rank_achieved = ?
            WHERE user_id = ?
        ''', (new_rank, user_id))
        
        conn.commit()
        conn.close()
    
    def get_user_medals(self, user_id: int) -> List[Dict]:
        """Get user's earned medals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT medal_id, earned_at 
            FROM user_medals 
            WHERE user_id = ?
        ''', (user_id,))
        
        earned_medals = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        # Build medal list with earned status
        medals = []
        for medal in self.MEDALS:
            medal_dict = asdict(medal)
            medal_dict['earned'] = medal.id in earned_medals
            medal_dict['earned_at'] = earned_medals.get(medal.id, None)
            medals.append(medal_dict)
        
        return medals
    
    def _check_medal_progress(self, user_id: int):
        """Check and award medals based on progress"""
        stats = self.get_user_stats(user_id)
        recruiting_stats = self.get_recruiting_stats(user_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for medal in self.MEDALS:
            # Check if already earned
            cursor.execute('''
                SELECT 1 FROM user_medals 
                WHERE user_id = ? AND medal_id = ?
            ''', (user_id, medal.id))
            
            if cursor.fetchone():
                continue  # Already earned
            
            # Check requirements
            earned = False
            
            if medal.requirement_type == "trades":
                earned = stats.successful_trades >= medal.requirement_value
            elif medal.requirement_type == "profit":
                earned = stats.total_profit >= medal.requirement_value
            elif medal.requirement_type == "streak":
                earned = stats.win_streak >= medal.requirement_value
            elif medal.requirement_type == "recruits":
                earned = recruiting_stats['total_recruits'] >= medal.requirement_value
            
            if earned:
                # Award medal
                cursor.execute('''
                    INSERT INTO user_medals (user_id, medal_id, earned_at)
                    VALUES (?, ?, ?)
                ''', (user_id, medal.id, int(time.time())))
                
                # Award medal XP
                self.award_xp(user_id, medal.xp_reward, 
                            f"Medal earned: {medal.name}")
        
        conn.commit()
        conn.close()
    
    def _update_recruiter_stats(self, recruit_id: int):
        """Update recruiter stats when recruit completes trade"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recruit info
        cursor.execute('''
            SELECT recruiter_id, trades_completed 
            FROM recruits 
            WHERE recruit_id = ?
        ''', (recruit_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        
        recruiter_id, prev_trades = row
        new_trades = prev_trades + 1
        
        # Update recruit stats
        cursor.execute('''
            UPDATE recruits 
            SET trades_completed = ?
            WHERE recruit_id = ?
        ''', (new_trades, recruit_id))
        
        # Award XP to recruiter
        if new_trades == 1:
            # First trade bonus
            self.award_xp(recruiter_id, self.XP_REWARDS['recruit_first_trade'],
                         "Recruit completed first trade")
        elif new_trades % 10 == 0:
            # Milestone bonus
            self.award_xp(recruiter_id, self.XP_REWARDS['recruit_milestone'],
                         f"Recruit reached {new_trades} trades")
        
        # Update XP contributed
        xp_contribution = 5  # 5 XP per recruit trade
        cursor.execute('''
            UPDATE recruits 
            SET xp_contributed = xp_contributed + ?
            WHERE recruit_id = ?
        ''', (xp_contribution, recruit_id))
        
        conn.commit()
        conn.close()
    
    def _calculate_rank(self, total_xp: int) -> str:
        """Calculate rank based on XP"""
        for rank, threshold in reversed(list(self.RANK_THRESHOLDS.items())):
            if total_xp >= threshold:
                return rank
        return "RECRUIT"
    
    def get_full_profile(self, user_id: int) -> Dict:
        """Get complete user profile for display"""
        stats = self.get_user_stats(user_id)
        if not stats:
            stats = self.create_user_profile(user_id)
        
        medals = self.get_user_medals(user_id)
        recruiting = self.get_recruiting_stats(user_id)
        
        # Add recruitment analytics
        recruitment_analytics = self._get_recruitment_analytics(user_id, recruiting)
        
        return {
            'user_id': user_id,
            'rank': stats.rank_achieved,
            'total_xp': stats.total_xp,
            'next_rank_xp': self._get_next_rank_threshold(stats.total_xp),
            'missions_completed': stats.missions_completed,
            'success_rate': round(stats.success_rate, 1),
            'total_profit': round(stats.total_profit, 2),
            'largest_win': round(stats.largest_win, 2),
            'current_streak': stats.current_streak,
            'best_streak': stats.win_streak,
            'medals': medals,
            'medals_earned': sum(1 for m in medals if m['earned']),
            'medals_total': len(medals),
            'recruits_count': recruiting['total_recruits'],
            'recruit_xp': recruiting['total_recruit_xp'],
            'recent_recruits': recruiting['recent_recruits'],
            'recruitment_stats': recruitment_analytics,
            'joined_days_ago': (time.time() - stats.joined_at) // 86400
        }
    
    def _get_next_rank_threshold(self, current_xp: int) -> int:
        """Get XP needed for next rank"""
        for rank, threshold in self.RANK_THRESHOLDS.items():
            if current_xp < threshold:
                return threshold
        return 999999  # Max rank achieved
    
    def _get_recruitment_analytics(self, user_id: int, recruiting_stats: Dict) -> Dict:
        """Calculate detailed recruitment analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recruitment timeline
        cursor.execute('''
            SELECT DATE(joined_at, 'unixepoch') as date, COUNT(*) as count
            FROM recruits
            WHERE recruiter_id = ?
            GROUP BY DATE(joined_at, 'unixepoch')
            ORDER BY date DESC
            LIMIT 30
        ''', (user_id,))
        
        daily_recruits = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get recruit performance
        cursor.execute('''
            SELECT 
                AVG(trades_completed) as avg_trades,
                SUM(xp_contributed) as total_xp,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_count,
                COUNT(*) as total_count
            FROM recruits
            WHERE recruiter_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            avg_trades_per_recruit = row[0] or 0
            total_xp_earned = row[1] or 0
            active_recruits = row[2] or 0
            total_recruits = row[3] or 0
            retention_rate = (active_recruits / total_recruits * 100) if total_recruits > 0 else 0
        else:
            avg_trades_per_recruit = 0
            total_xp_earned = 0
            retention_rate = 0
        
        # Get best performing recruit
        cursor.execute('''
            SELECT username, trades_completed, xp_contributed
            FROM recruits
            WHERE recruiter_id = ?
            ORDER BY xp_contributed DESC
            LIMIT 1
        ''', (user_id,))
        
        best_recruit = cursor.fetchone()
        
        conn.close()
        
        return {
            'daily_timeline': daily_recruits,
            'avg_trades_per_recruit': round(avg_trades_per_recruit, 1),
            'total_xp_earned': total_xp_earned,
            'retention_rate': round(retention_rate, 1),
            'best_recruit': {
                'username': best_recruit[0] if best_recruit else None,
                'trades': best_recruit[1] if best_recruit else 0,
                'xp_contributed': best_recruit[2] if best_recruit else 0
            } if best_recruit else None,
            'recruitment_rank': self._calculate_recruitment_rank(recruiting_stats['total_recruits']),
            'next_milestone': self._get_next_recruitment_milestone(recruiting_stats['total_recruits'])
        }
    
    def _calculate_recruitment_rank(self, total_recruits: int) -> str:
        """Calculate recruitment rank based on total recruits"""
        if total_recruits >= 100:
            return "🌟 LEGENDARY RECRUITER"
        elif total_recruits >= 50:
            return "💎 MASTER RECRUITER"
        elif total_recruits >= 20:
            return "🥇 ELITE RECRUITER"
        elif total_recruits >= 10:
            return "🥈 SENIOR RECRUITER"
        elif total_recruits >= 5:
            return "🥉 ACTIVE RECRUITER"
        elif total_recruits >= 1:
            return "🎖️ RECRUITER"
        else:
            return "👤 NOT RECRUITING"
    
    def _get_next_recruitment_milestone(self, current_recruits: int) -> Dict:
        """Get next recruitment milestone and reward"""
        milestones = [
            {'count': 1, 'reward': 50, 'medal': 'Recruiter'},
            {'count': 5, 'reward': 300, 'medal': 'Squad Leader'},
            {'count': 10, 'reward': 500, 'medal': 'Team Builder'},
            {'count': 20, 'reward': 1000, 'medal': 'Commander'},
            {'count': 50, 'reward': 2500, 'medal': 'General'},
            {'count': 100, 'reward': 5000, 'medal': 'Legend'}
        ]
        
        for milestone in milestones:
            if current_recruits < milestone['count']:
                return {
                    'target': milestone['count'],
                    'remaining': milestone['count'] - current_recruits,
                    'xp_reward': milestone['reward'],
                    'medal': milestone['medal']
                }
        
        return {
            'target': 1000,
            'remaining': 1000 - current_recruits,
            'xp_reward': 10000,
            'medal': 'Mythical'
        }
    
    def track_recruitment_event(self, recruiter_id: int, event_type: str, event_data: Dict):
        """Track recruitment-related events for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create recruitment events table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recruitment_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recruiter_id INTEGER,
                event_type TEXT,
                event_data TEXT,
                timestamp INTEGER
            )
        ''')
        
        # Log event
        cursor.execute('''
            INSERT INTO recruitment_events 
            (recruiter_id, event_type, event_data, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (recruiter_id, event_type, json.dumps(event_data), int(time.time())))
        
        conn.commit()
        conn.close()
        
        # Award bonus XP for certain events
        if event_type == 'recruit_first_trade':
            self.award_xp(recruiter_id, 100, "Recruit completed first trade")
        elif event_type == 'recruit_milestone':
            trades = event_data.get('trades', 0)
            if trades % 10 == 0:
                self.award_xp(recruiter_id, 200, f"Recruit reached {trades} trades")