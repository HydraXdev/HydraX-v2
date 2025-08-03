# xp_logger.py
# BITTEN Performance and XP Logging System

import json
import time
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import os
from pathlib import Path

# Import BITTEN components
from .rank_access import UserRank

class AchievementType(Enum):
    """Achievement categories"""
    FIRST_TRADE = "first_trade"
    PROFIT_STREAK = "profit_streak"
    VOLUME_MILESTONE = "volume_milestone"
    ACCURACY_MILESTONE = "accuracy_milestone"
    CONSECUTIVE_DAYS = "consecutive_days"
    RISK_MANAGEMENT = "risk_management"
    TIER_PROMOTION = "tier_promotion"
    SPECIAL_EVENT = "special_event"

class TradeOutcome(Enum):
    """Trade result types"""
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    PENDING = "pending"

@dataclass
class TradeLog:
    """Individual trade logging"""
    trade_id: str
    user_id: int
    symbol: str
    direction: str
    volume: float
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    tcs_score: int = 0
    outcome: TradeOutcome = TradeOutcome.PENDING
    profit_loss: float = 0.0
    open_time: str = ""
    close_time: Optional[str] = None
    hold_duration: int = 0  # seconds
    xp_earned: int = 0
    comment: str = ""

@dataclass
class Achievement:
    """User achievement"""
    achievement_id: str
    user_id: int
    achievement_type: AchievementType
    title: str
    description: str
    xp_reward: int
    unlock_date: str
    icon: str = "🏆"
    tier_required: UserRank = UserRank.USER

@dataclass
class UserPerformance:
    """User performance metrics"""
    user_id: int
    username: str
    current_xp: int
    current_rank: UserRank
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_volume: float
    total_profit: float
    best_trade: float
    worst_trade: float
    current_streak: int
    best_streak: int
    accuracy_rate: float
    profit_factor: float
    avg_hold_time: int
    trading_days: int
    last_trade_date: Optional[str] = None
    rank_up_date: Optional[str] = None

class XPLogger:
    """Performance and XP tracking system"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "/root/HydraX-v2/data/bitten_xp.db"
        self.data_dir = Path(self.db_path).parent
        self.data_dir.mkdir(exist_ok=True)
        
        # XP thresholds for rank progression
        self.xp_thresholds = {
            UserRank.USER: 0,
            UserRank.AUTHORIZED: 1000,
            UserRank.ELITE: 5000,
            UserRank.ADMIN: 10000
        }
        
        # XP rewards configuration
        self.xp_rewards = {
            'base_trade': 10,
            'winning_trade': 25,
            'high_tcs_bonus': 15,  # TCS >= threshold + 15
            'volume_bonus': 5,     # >= 1.0 lot
            'streak_bonus': 10,    # per consecutive win
            'daily_bonus': 50,     # first trade of day
            'weekly_bonus': 200,   # 5+ trades in week
            'achievement_multiplier': 2.0
        }
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for XP tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Trade logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_logs (
                        trade_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        volume REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        tcs_score INTEGER DEFAULT 0,
                        outcome TEXT DEFAULT 'pending',
                        profit_loss REAL DEFAULT 0.0,
                        open_time TEXT NOT NULL,
                        close_time TEXT,
                        hold_duration INTEGER DEFAULT 0,
                        xp_earned INTEGER DEFAULT 0,
                        comment TEXT DEFAULT ''
                    )
                ''')
                
                # User performance table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_performance (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        current_xp INTEGER DEFAULT 0,
                        current_rank TEXT DEFAULT 'USER',
                        total_trades INTEGER DEFAULT 0,
                        winning_trades INTEGER DEFAULT 0,
                        losing_trades INTEGER DEFAULT 0,
                        total_volume REAL DEFAULT 0.0,
                        total_profit REAL DEFAULT 0.0,
                        best_trade REAL DEFAULT 0.0,
                        worst_trade REAL DEFAULT 0.0,
                        current_streak INTEGER DEFAULT 0,
                        best_streak INTEGER DEFAULT 0,
                        accuracy_rate REAL DEFAULT 0.0,
                        profit_factor REAL DEFAULT 0.0,
                        avg_hold_time INTEGER DEFAULT 0,
                        trading_days INTEGER DEFAULT 0,
                        last_trade_date TEXT,
                        rank_up_date TEXT
                    )
                ''')
                
                # Achievements table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS achievements (
                        achievement_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        achievement_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        xp_reward INTEGER NOT NULL,
                        unlock_date TEXT NOT NULL,
                        icon TEXT DEFAULT '🏆',
                        tier_required TEXT DEFAULT 'USER'
                    )
                ''')
                
                # XP history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS xp_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        xp_change INTEGER NOT NULL,
                        reason TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        trade_id TEXT,
                        achievement_id TEXT
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Database initialization failed: {e}")
    
    def log_trade_open(self, trade_log: TradeLog) -> bool:
        """Log trade opening"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert trade log
                cursor.execute('''
                    INSERT INTO trade_logs (
                        trade_id, user_id, symbol, direction, volume, entry_price,
                        stop_loss, take_profit, tcs_score, open_time, comment
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_log.trade_id,
                    trade_log.user_id,
                    trade_log.symbol,
                    trade_log.direction,
                    trade_log.volume,
                    trade_log.entry_price,
                    trade_log.stop_loss,
                    trade_log.take_profit,
                    trade_log.tcs_score,
                    trade_log.open_time,
                    trade_log.comment
                ))
                
                conn.commit()
                
                # Award opening trade XP
                xp_earned = self._calculate_opening_xp(trade_log)
                if xp_earned > 0:
                    self._add_xp(trade_log.user_id, xp_earned, f"Trade opened: {trade_log.symbol}", trade_log.trade_id)
                
                return True
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to log trade open: {e}")
            return False
    
    def log_trade_close(self, trade_id: str, exit_price: float, outcome: TradeOutcome, profit_loss: float) -> bool:
        """Log trade closing and calculate final XP"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get trade info
                cursor.execute('SELECT * FROM trade_logs WHERE trade_id = ?', (trade_id,))
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                # Calculate hold duration
                open_time = datetime.fromisoformat(row[11])  # open_time column
                close_time = datetime.now()
                hold_duration = int((close_time - open_time).total_seconds())
                
                # Calculate total XP for completed trade
                trade_log = TradeLog(
                    trade_id=row[0],
                    user_id=row[1],
                    symbol=row[2],
                    direction=row[3],
                    volume=row[4],
                    entry_price=row[5],
                    exit_price=exit_price,
                    stop_loss=row[7],
                    take_profit=row[8],
                    tcs_score=row[9],
                    outcome=outcome,
                    profit_loss=profit_loss,
                    open_time=row[11],
                    close_time=close_time.isoformat(),
                    hold_duration=hold_duration
                )
                
                total_xp = self._calculate_closing_xp(trade_log)
                
                # Update trade log
                cursor.execute('''
                    UPDATE trade_logs SET 
                        exit_price = ?, outcome = ?, profit_loss = ?, 
                        close_time = ?, hold_duration = ?, xp_earned = ?
                    WHERE trade_id = ?
                ''', (
                    exit_price, outcome.value, profit_loss,
                    close_time.isoformat(), hold_duration, total_xp, trade_id
                ))
                
                conn.commit()
                
                # Award closing XP
                if total_xp > 0:
                    self._add_xp(trade_log.user_id, total_xp, f"Trade closed: {outcome.value}", trade_id)
                
                # Update user performance
                self._update_user_performance(trade_log)
                
                # Check for achievements
                self._check_achievements(trade_log.user_id)
                
                return True
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to log trade close: {e}")
            return False
    
    def _calculate_opening_xp(self, trade_log: TradeLog) -> int:
        """Calculate XP for opening a trade"""
        xp = self.xp_rewards['base_trade']
        
        # High TCS bonus using centralized threshold
        from tcs_controller import get_current_threshold
        threshold = get_current_threshold()
        if trade_log.tcs_score >= (threshold + 15):
            xp += self.xp_rewards['high_tcs_bonus']
        
        # Volume bonus
        if trade_log.volume >= 1.0:
            xp += self.xp_rewards['volume_bonus']
        
        # Daily first trade bonus
        if self._is_first_trade_today(trade_log.user_id):
            xp += self.xp_rewards['daily_bonus']
        
        return xp
    
    def _calculate_closing_xp(self, trade_log: TradeLog) -> int:
        """Calculate XP for closing a trade"""
        xp = 0
        
        # Winning trade bonus
        if trade_log.outcome == TradeOutcome.WIN:
            xp += self.xp_rewards['winning_trade']
            
            # Streak bonus
            current_streak = self._get_current_streak(trade_log.user_id)
            if current_streak > 1:
                xp += self.xp_rewards['streak_bonus'] * (current_streak - 1)
        
        # Risk management bonus (hitting SL/TP instead of manual close)
        if trade_log.stop_loss and abs(trade_log.exit_price - trade_log.stop_loss) < 0.0001:
            xp += 5  # SL hit bonus for risk management
        elif trade_log.take_profit and abs(trade_log.exit_price - trade_log.take_profit) < 0.0001:
            xp += 10  # TP hit bonus
        
        return xp
    
    def _add_xp(self, user_id: int, xp_amount: int, reason: str, trade_id: str = None, achievement_id: str = None):
        """Add XP to user and log the change"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current XP
                cursor.execute('SELECT current_xp, current_rank FROM user_performance WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                
                current_xp = row[0] if row else 0
                current_rank = UserRank(row[1]) if row else UserRank.USER
                new_xp = current_xp + xp_amount
                
                # Check for rank up
                new_rank = self._check_rank_up(new_xp, current_rank)
                rank_up_bonus = 0
                
                if new_rank != current_rank:
                    rank_up_bonus = 500  # Rank up bonus
                    new_xp += rank_up_bonus
                    reason += f" (RANK UP TO {new_rank.name}!)"
                
                # Update user XP
                if row:
                    cursor.execute('''
                        UPDATE user_performance SET current_xp = ?, current_rank = ?, rank_up_date = ?
                        WHERE user_id = ?
                    ''', (new_xp, new_rank.value, datetime.now().isoformat() if new_rank != current_rank else row[1], user_id))
                else:
                    # Create new user performance record
                    cursor.execute('''
                        INSERT INTO user_performance (user_id, username, current_xp, current_rank, rank_up_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, f"user_{user_id}", new_xp, new_rank.value, datetime.now().isoformat()))
                
                # Log XP change
                cursor.execute('''
                    INSERT INTO xp_history (user_id, xp_change, reason, timestamp, trade_id, achievement_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, xp_amount + rank_up_bonus, reason, datetime.now().isoformat(), trade_id, achievement_id))
                
                conn.commit()
                
                print(f"[XP_LOGGER] User {user_id} earned {xp_amount + rank_up_bonus} XP: {reason}")
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to add XP: {e}")
    
    def _check_rank_up(self, xp: int, current_rank: UserRank) -> UserRank:
        """Check if user should rank up"""
        for rank in [UserRank.ADMIN, UserRank.ELITE, UserRank.AUTHORIZED, UserRank.USER]:
            if xp >= self.xp_thresholds[rank]:
                return rank
        return current_rank
    
    def _update_user_performance(self, trade_log: TradeLog):
        """Update comprehensive user performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current performance
                cursor.execute('SELECT * FROM user_performance WHERE user_id = ?', (trade_log.user_id,))
                row = cursor.fetchone()
                
                if not row:
                    # Initialize if not exists
                    cursor.execute('''
                        INSERT INTO user_performance (user_id, username) VALUES (?, ?)
                    ''', (trade_log.user_id, f"user_{trade_log.user_id}"))
                    cursor.execute('SELECT * FROM user_performance WHERE user_id = ?', (trade_log.user_id,))
                    row = cursor.fetchone()
                
                # Calculate updates
                total_trades = row[4] + 1
                winning_trades = row[5] + (1 if trade_log.outcome == TradeOutcome.WIN else 0)
                losing_trades = row[6] + (1 if trade_log.outcome == TradeOutcome.LOSS else 0)
                total_volume = row[7] + trade_log.volume
                total_profit = row[8] + trade_log.profit_loss
                best_trade = max(row[9], trade_log.profit_loss)
                worst_trade = min(row[10], trade_log.profit_loss)
                
                # Update streak
                if trade_log.outcome == TradeOutcome.WIN:
                    current_streak = row[11] + 1
                    best_streak = max(row[12], current_streak)
                else:
                    current_streak = 0
                    best_streak = row[12]
                
                # Calculate derived metrics
                accuracy_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
                
                total_gains = sum([log[10] for log in self._get_winning_trades(trade_log.user_id)])
                total_losses = abs(sum([log[10] for log in self._get_losing_trades(trade_log.user_id)]))
                profit_factor = total_gains / total_losses if total_losses > 0 else 0
                
                # Update database
                cursor.execute('''
                    UPDATE user_performance SET
                        total_trades = ?, winning_trades = ?, losing_trades = ?,
                        total_volume = ?, total_profit = ?, best_trade = ?, worst_trade = ?,
                        current_streak = ?, best_streak = ?, accuracy_rate = ?,
                        profit_factor = ?, last_trade_date = ?
                    WHERE user_id = ?
                ''', (
                    total_trades, winning_trades, losing_trades,
                    total_volume, total_profit, best_trade, worst_trade,
                    current_streak, best_streak, accuracy_rate,
                    profit_factor, trade_log.close_time, trade_log.user_id
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to update performance: {e}")
    
    def _check_achievements(self, user_id: int):
        """Check and award achievements"""
        try:
            performance = self.get_user_performance(user_id)
            if not performance:
                return
            
            achievements_to_award = []
            
            # First trade achievement
            if performance.total_trades == 1:
                achievements_to_award.append(Achievement(
                    achievement_id=f"first_trade_{user_id}_{int(time.time())}",
                    user_id=user_id,
                    achievement_type=AchievementType.FIRST_TRADE,
                    title="First Blood",
                    description="Executed your first trade",
                    xp_reward=100,
                    unlock_date=datetime.now().isoformat(),
                    icon="🎯"
                ))
            
            # Profit streak achievements
            if performance.current_streak == 5:
                achievements_to_award.append(Achievement(
                    achievement_id=f"streak_5_{user_id}_{int(time.time())}",
                    user_id=user_id,
                    achievement_type=AchievementType.PROFIT_STREAK,
                    title="Hot Streak",
                    description="5 consecutive winning trades",
                    xp_reward=250,
                    unlock_date=datetime.now().isoformat(),
                    icon="🔥"
                ))
            elif performance.current_streak == 10:
                achievements_to_award.append(Achievement(
                    achievement_id=f"streak_10_{user_id}_{int(time.time())}",
                    user_id=user_id,
                    achievement_type=AchievementType.PROFIT_STREAK,
                    title="Unstoppable",
                    description="10 consecutive winning trades",
                    xp_reward=500,
                    unlock_date=datetime.now().isoformat(),
                    icon="⚡"
                ))
            
            # Volume milestones
            if performance.total_volume >= 100 and not self._has_achievement(user_id, "volume_100"):
                achievements_to_award.append(Achievement(
                    achievement_id=f"volume_100_{user_id}_{int(time.time())}",
                    user_id=user_id,
                    achievement_type=AchievementType.VOLUME_MILESTONE,
                    title="Heavy Trader",
                    description="Traded 100 lots total volume",
                    xp_reward=300,
                    unlock_date=datetime.now().isoformat(),
                    icon="💪"
                ))
            
            # Accuracy achievements
            if performance.accuracy_rate >= 80 and performance.total_trades >= 20:
                if not self._has_achievement(user_id, "accuracy_80"):
                    achievements_to_award.append(Achievement(
                        achievement_id=f"accuracy_80_{user_id}_{int(time.time())}",
                        user_id=user_id,
                        achievement_type=AchievementType.ACCURACY_MILESTONE,
                        title="Sniper",
                        description="80%+ accuracy over 20+ trades",
                        xp_reward=400,
                        unlock_date=datetime.now().isoformat(),
                        icon="🎯",
                        tier_required=UserRank.AUTHORIZED
                    ))
            
            # Award achievements
            for achievement in achievements_to_award:
                self._award_achievement(achievement)
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Achievement check failed: {e}")
    
    def _award_achievement(self, achievement: Achievement):
        """Award achievement to user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert achievement
                cursor.execute('''
                    INSERT INTO achievements (
                        achievement_id, user_id, achievement_type, title, description,
                        xp_reward, unlock_date, icon, tier_required
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    achievement.achievement_id,
                    achievement.user_id,
                    achievement.achievement_type.value,
                    achievement.title,
                    achievement.description,
                    achievement.xp_reward,
                    achievement.unlock_date,
                    achievement.icon,
                    achievement.tier_required.value
                ))
                
                conn.commit()
                
                # Award XP
                self._add_xp(
                    achievement.user_id,
                    achievement.xp_reward,
                    f"Achievement unlocked: {achievement.title}",
                    achievement_id=achievement.achievement_id
                )
                
                print(f"[XP_LOGGER] Achievement awarded: {achievement.title} to user {achievement.user_id}")
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to award achievement: {e}")
    
    def get_user_performance(self, user_id: int) -> Optional[UserPerformance]:
        """Get comprehensive user performance"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM user_performance WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return UserPerformance(
                    user_id=row[0],
                    username=row[1],
                    current_xp=row[2],
                    current_rank=UserRank(row[3]),
                    total_trades=row[4],
                    winning_trades=row[5],
                    losing_trades=row[6],
                    total_volume=row[7],
                    total_profit=row[8],
                    best_trade=row[9],
                    worst_trade=row[10],
                    current_streak=row[11],
                    best_streak=row[12],
                    accuracy_rate=row[13],
                    profit_factor=row[14],
                    avg_hold_time=row[15],
                    trading_days=row[16],
                    last_trade_date=row[17],
                    rank_up_date=row[18]
                )
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to get performance: {e}")
            return None
    
    def get_user_achievements(self, user_id: int) -> List[Achievement]:
        """Get user's achievements"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM achievements WHERE user_id = ? ORDER BY unlock_date DESC', (user_id,))
                rows = cursor.fetchall()
                
                achievements = []
                for row in rows:
                    achievements.append(Achievement(
                        achievement_id=row[0],
                        user_id=row[1],
                        achievement_type=AchievementType(row[2]),
                        title=row[3],
                        description=row[4],
                        xp_reward=row[5],
                        unlock_date=row[6],
                        icon=row[7],
                        tier_required=UserRank(row[8])
                    ))
                
                return achievements
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to get achievements: {e}")
            return []
    
    def get_xp_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's XP history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT xp_change, reason, timestamp, trade_id, achievement_id
                    FROM xp_history WHERE user_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    history.append({
                        'xp_change': row[0],
                        'reason': row[1],
                        'timestamp': row[2],
                        'trade_id': row[3],
                        'achievement_id': row[4]
                    })
                
                return history
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to get XP history: {e}")
            return []
    
    def _is_first_trade_today(self, user_id: int) -> bool:
        """Check if this is user's first trade today"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                today = datetime.now().date().isoformat()
                cursor.execute('''
                    SELECT COUNT(*) FROM trade_logs 
                    WHERE user_id = ? AND DATE(open_time) = ?
                ''', (user_id, today))
                
                count = cursor.fetchone()[0]
                return count == 0
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to check first trade today: {e}")
            return False
    
    def _get_current_streak(self, user_id: int) -> int:
        """Get user's current winning streak"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT outcome FROM trade_logs 
                    WHERE user_id = ? AND outcome != 'pending'
                    ORDER BY close_time DESC LIMIT 10
                ''', (user_id,))
                
                rows = cursor.fetchall()
                streak = 0
                
                for row in rows:
                    if row[0] == 'win':
                        streak += 1
                    else:
                        break
                
                return streak
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to get streak: {e}")
            return 0
    
    def _get_winning_trades(self, user_id: int) -> List:
        """Get winning trades for profit factor calculation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT profit_loss FROM trade_logs 
                    WHERE user_id = ? AND outcome = 'win'
                ''', (user_id,))
                
                return cursor.fetchall()
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to get winning trades: {e}")
            return []
    
    def _get_losing_trades(self, user_id: int) -> List:
        """Get losing trades for profit factor calculation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT profit_loss FROM trade_logs 
                    WHERE user_id = ? AND outcome = 'loss'
                ''', (user_id,))
                
                return cursor.fetchall()
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to get losing trades: {e}")
            return []
    
    def _has_achievement(self, user_id: int, achievement_substring: str) -> bool:
        """Check if user has achievement containing substring"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM achievements 
                    WHERE user_id = ? AND achievement_id LIKE ?
                ''', (user_id, f"%{achievement_substring}%"))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to check achievement: {e}")
            return False
    
    def format_performance_report(self, user_id: int) -> str:
        """Format comprehensive performance report for Telegram"""
        try:
            performance = self.get_user_performance(user_id)
            if not performance:
                return "❌ No performance data available"
            
            achievements = self.get_user_achievements(user_id)
            recent_history = self.get_xp_history(user_id, 5)
            
            # Calculate next rank progress
            current_threshold = self.xp_thresholds[performance.current_rank]
            next_rank = None
            for rank in [UserRank.AUTHORIZED, UserRank.ELITE, UserRank.ADMIN]:
                if self.xp_thresholds[rank] > performance.current_xp:
                    next_rank = rank
                    break
            
            next_threshold = self.xp_thresholds[next_rank] if next_rank else None
            progress_pct = 0
            if next_threshold:
                progress_pct = ((performance.current_xp - current_threshold) / (next_threshold - current_threshold)) * 100
            
            report = f"""📊 **Performance Report**

👤 **{performance.username}** 
🏆 **Rank:** {performance.current_rank.name} ({performance.current_xp} XP)
{'📈 **Next Rank:** ' + next_rank.name + f' ({progress_pct:.1f}% progress)' if next_rank else '🎯 **MAX RANK ACHIEVED**'}

🎯 **Trading Stats:**
• Total Trades: {performance.total_trades}
• Win Rate: {performance.accuracy_rate:.1f}%
• Current Streak: {performance.current_streak}
• Best Streak: {performance.best_streak}
• Total Volume: {performance.total_volume:.2f} lots

💰 **P&L Summary:**
• Total Profit: ${performance.total_profit:.2f}
• Best Trade: ${performance.best_trade:.2f}
• Worst Trade: ${performance.worst_trade:.2f}
• Profit Factor: {performance.profit_factor:.2f}

🏆 **Achievements:** {len(achievements)}"""

            if achievements:
                recent_achievements = achievements[:3]
                report += "\n🎖️ **Recent Achievements:**\n"
                for ach in recent_achievements:
                    report += f"• {ach.icon} {ach.title} (+{ach.xp_reward} XP)\n"
            
            if recent_history:
                report += "\n📈 **Recent XP:**\n"
                for entry in recent_history[:3]:
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%m/%d %H:%M")
                    report += f"• +{entry['xp_change']} XP - {entry['reason'][:30]}... ({timestamp})\n"
            
            return report
            
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to format report: {e}")
            return "❌ Error generating performance report"
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get XP leaderboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT user_id, username, current_xp, current_rank, total_trades, accuracy_rate
                    FROM user_performance
                    ORDER BY current_xp DESC LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                leaderboard = []
                for i, row in enumerate(rows, 1):
                    leaderboard.append({
                        'rank': i,
                        'user_id': row[0],
                        'username': row[1],
                        'xp': row[2],
                        'tier': row[3],
                        'trades': row[4],
                        'accuracy': row[5]
                    })
                
                return leaderboard
                
        except Exception as e:
            print(f"[XP_LOGGER ERROR] Failed to get leaderboard: {e}")
            return []
