"""
SQLite Database Infrastructure for User Engagement Tracking

This module provides comprehensive database management for tracking user engagement
with signals, including fire tracking, user statistics, and signal metrics.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = "/root/HydraX-v2/data/engagement.db"

@dataclass
class SignalFire:
    """Data class for signal fire records"""
    id: Optional[int] = None
    user_id: int = None
    signal_id: str = None
    timestamp: datetime = None
    executed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class UserStats:
    """Data class for user statistics"""
    user_id: int = None
    total_fires: int = 0
    win_rate: float = 0.0
    pnl: float = 0.0
    last_updated: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data

@dataclass
class SignalMetrics:
    """Data class for signal metrics"""
    signal_id: str = None
    total_fires: int = 0
    active_users: int = 0
    created_at: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

class EngagementDatabase:
    """
    SQLite database manager for user engagement tracking.
    
    Provides ORM-style functions for CRUD operations and real-time stats.
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.ensure_db_directory()
        
    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection with row factory
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self):
        """
        Initialize the database with required tables.
        
        Creates all necessary tables if they don't exist.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create signal_fires table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_fires (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    signal_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    executed BOOLEAN NOT NULL DEFAULT 0,
                    UNIQUE(user_id, signal_id)
                )
            ''')
            
            # Create user_stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_fires INTEGER NOT NULL DEFAULT 0,
                    win_rate REAL NOT NULL DEFAULT 0.0,
                    pnl REAL NOT NULL DEFAULT 0.0,
                    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create signal_metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_metrics (
                    signal_id TEXT PRIMARY KEY,
                    total_fires INTEGER NOT NULL DEFAULT 0,
                    active_users INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_fires_user_id ON signal_fires(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_fires_signal_id ON signal_fires(signal_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_fires_timestamp ON signal_fires(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_stats_last_updated ON user_stats(last_updated)')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    # CRUD Operations for Signal Fires
    
    def record_signal_fire(self, user_id: int, signal_id: str, executed: bool = False) -> bool:
        """
        Record a signal fire event.
        
        Args:
            user_id: User ID who fired the signal
            signal_id: ID of the signal that was fired
            executed: Whether the signal was executed
            
        Returns:
            bool: True if recorded successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO signal_fires (user_id, signal_id, timestamp, executed)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, signal_id, datetime.now(), executed))
                conn.commit()
                
                # Update related metrics
                self._update_user_stats(conn, user_id)
                self._update_signal_metrics(conn, signal_id)
                
                logger.info(f"Recorded signal fire: user={user_id}, signal={signal_id}, executed={executed}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error recording signal fire: {e}")
            return False
    
    def get_user_signal_fires(self, user_id: int, limit: int = 100) -> List[SignalFire]:
        """
        Get signal fires for a specific user.
        
        Args:
            user_id: User ID to get fires for
            limit: Maximum number of records to return
            
        Returns:
            List[SignalFire]: List of signal fire records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, user_id, signal_id, timestamp, executed
                    FROM signal_fires
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                return [
                    SignalFire(
                        id=row['id'],
                        user_id=row['user_id'],
                        signal_id=row['signal_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        executed=bool(row['executed'])
                    )
                    for row in rows
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting user signal fires: {e}")
            return []
    
    def get_signal_fires_by_signal(self, signal_id: str, limit: int = 100) -> List[SignalFire]:
        """
        Get all fires for a specific signal.
        
        Args:
            signal_id: Signal ID to get fires for
            limit: Maximum number of records to return
            
        Returns:
            List[SignalFire]: List of signal fire records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, user_id, signal_id, timestamp, executed
                    FROM signal_fires
                    WHERE signal_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (signal_id, limit))
                
                rows = cursor.fetchall()
                return [
                    SignalFire(
                        id=row['id'],
                        user_id=row['user_id'],
                        signal_id=row['signal_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        executed=bool(row['executed'])
                    )
                    for row in rows
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting signal fires: {e}")
            return []
    
    # CRUD Operations for User Stats
    
    def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """
        Get statistics for a specific user.
        
        Args:
            user_id: User ID to get stats for
            
        Returns:
            UserStats: User statistics or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, total_fires, win_rate, pnl, last_updated
                    FROM user_stats
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return UserStats(
                        user_id=row['user_id'],
                        total_fires=row['total_fires'],
                        win_rate=row['win_rate'],
                        pnl=row['pnl'],
                        last_updated=datetime.fromisoformat(row['last_updated'])
                    )
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error getting user stats: {e}")
            return None
    
    def update_user_pnl(self, user_id: int, pnl_change: float, is_win: bool = True) -> bool:
        """
        Update user's P&L and win rate.
        
        Args:
            user_id: User ID to update
            pnl_change: Change in P&L (positive or negative)
            is_win: Whether this trade was a win
            
        Returns:
            bool: True if updated successfully
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current stats
                cursor.execute('''
                    SELECT total_fires, win_rate, pnl
                    FROM user_stats
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    current_fires = row['total_fires']
                    current_win_rate = row['win_rate']
                    current_pnl = row['pnl']
                    
                    # Calculate new win rate
                    if current_fires > 0:
                        current_wins = current_fires * current_win_rate
                        new_wins = current_wins + (1 if is_win else 0)
                        new_win_rate = new_wins / current_fires
                    else:
                        new_win_rate = 1.0 if is_win else 0.0
                    
                    # Update stats
                    cursor.execute('''
                        UPDATE user_stats
                        SET pnl = ?, win_rate = ?, last_updated = ?
                        WHERE user_id = ?
                    ''', (current_pnl + pnl_change, new_win_rate, datetime.now(), user_id))
                    
                    conn.commit()
                    return True
                    
        except sqlite3.Error as e:
            logger.error(f"Error updating user PnL: {e}")
            return False
    
    def _update_user_stats(self, conn: sqlite3.Connection, user_id: int):
        """
        Internal method to update user statistics.
        
        Args:
            conn: Database connection
            user_id: User ID to update stats for
        """
        cursor = conn.cursor()
        
        # Count total fires for user
        cursor.execute('''
            SELECT COUNT(*) as total_fires
            FROM signal_fires
            WHERE user_id = ?
        ''', (user_id,))
        
        total_fires = cursor.fetchone()['total_fires']
        
        # Insert or update user stats
        cursor.execute('''
            INSERT OR REPLACE INTO user_stats (user_id, total_fires, last_updated)
            VALUES (?, ?, ?)
        ''', (user_id, total_fires, datetime.now()))
    
    # CRUD Operations for Signal Metrics
    
    def get_signal_metrics(self, signal_id: str) -> Optional[SignalMetrics]:
        """
        Get metrics for a specific signal.
        
        Args:
            signal_id: Signal ID to get metrics for
            
        Returns:
            SignalMetrics: Signal metrics or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT signal_id, total_fires, active_users, created_at
                    FROM signal_metrics
                    WHERE signal_id = ?
                ''', (signal_id,))
                
                row = cursor.fetchone()
                if row:
                    return SignalMetrics(
                        signal_id=row['signal_id'],
                        total_fires=row['total_fires'],
                        active_users=row['active_users'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error getting signal metrics: {e}")
            return None
    
    def _update_signal_metrics(self, conn: sqlite3.Connection, signal_id: str):
        """
        Internal method to update signal metrics.
        
        Args:
            conn: Database connection
            signal_id: Signal ID to update metrics for
        """
        cursor = conn.cursor()
        
        # Count fires and unique users for this signal
        cursor.execute('''
            SELECT COUNT(*) as total_fires, COUNT(DISTINCT user_id) as active_users
            FROM signal_fires
            WHERE signal_id = ?
        ''', (signal_id,))
        
        row = cursor.fetchone()
        total_fires = row['total_fires']
        active_users = row['active_users']
        
        # Insert or update signal metrics
        cursor.execute('''
            INSERT OR REPLACE INTO signal_metrics (signal_id, total_fires, active_users, created_at)
            VALUES (?, ?, ?, COALESCE(
                (SELECT created_at FROM signal_metrics WHERE signal_id = ?),
                ?
            ))
        ''', (signal_id, total_fires, active_users, signal_id, datetime.now()))
    
    # Real-time Engagement Statistics
    
    def get_real_time_engagement_stats(self) -> Dict[str, Any]:
        """
        Get real-time engagement statistics.
        
        Returns:
            Dict containing various engagement metrics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total fires today
                cursor.execute('''
                    SELECT COUNT(*) as total_fires_today
                    FROM signal_fires
                    WHERE DATE(timestamp) = DATE('now')
                ''')
                total_fires_today = cursor.fetchone()['total_fires_today']
                
                # Active users today
                cursor.execute('''
                    SELECT COUNT(DISTINCT user_id) as active_users_today
                    FROM signal_fires
                    WHERE DATE(timestamp) = DATE('now')
                ''')
                active_users_today = cursor.fetchone()['active_users_today']
                
                # Most fired signal today
                cursor.execute('''
                    SELECT signal_id, COUNT(*) as fire_count
                    FROM signal_fires
                    WHERE DATE(timestamp) = DATE('now')
                    GROUP BY signal_id
                    ORDER BY fire_count DESC
                    LIMIT 1
                ''')
                most_fired_row = cursor.fetchone()
                most_fired_signal = {
                    'signal_id': most_fired_row['signal_id'] if most_fired_row else None,
                    'fire_count': most_fired_row['fire_count'] if most_fired_row else 0
                }
                
                # Average fires per user
                cursor.execute('''
                    SELECT AVG(total_fires) as avg_fires_per_user
                    FROM user_stats
                    WHERE total_fires > 0
                ''')
                avg_fires_row = cursor.fetchone()
                avg_fires_per_user = avg_fires_row['avg_fires_per_user'] or 0
                
                # Execution rate
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_fires,
                        SUM(CASE WHEN executed = 1 THEN 1 ELSE 0 END) as executed_fires
                    FROM signal_fires
                    WHERE DATE(timestamp) = DATE('now')
                ''')
                execution_row = cursor.fetchone()
                execution_rate = 0
                if execution_row['total_fires'] > 0:
                    execution_rate = execution_row['executed_fires'] / execution_row['total_fires']
                
                return {
                    'total_fires_today': total_fires_today,
                    'active_users_today': active_users_today,
                    'most_fired_signal': most_fired_signal,
                    'avg_fires_per_user': round(avg_fires_per_user, 2),
                    'execution_rate': round(execution_rate, 2),
                    'timestamp': datetime.now().isoformat()
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting real-time stats: {e}")
            return {}
    
    def get_user_engagement_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive engagement summary for a user.
        
        Args:
            user_id: User ID to get summary for
            
        Returns:
            Dict containing user engagement summary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Basic stats
                user_stats = self.get_user_stats(user_id)
                
                # Recent activity (last 7 days)
                cursor.execute('''
                    SELECT COUNT(*) as recent_fires
                    FROM signal_fires
                    WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
                ''', (user_id,))
                recent_fires = cursor.fetchone()['recent_fires']
                
                # Most fired signal by user
                cursor.execute('''
                    SELECT signal_id, COUNT(*) as fire_count
                    FROM signal_fires
                    WHERE user_id = ?
                    GROUP BY signal_id
                    ORDER BY fire_count DESC
                    LIMIT 1
                ''', (user_id,))
                favorite_signal_row = cursor.fetchone()
                favorite_signal = {
                    'signal_id': favorite_signal_row['signal_id'] if favorite_signal_row else None,
                    'fire_count': favorite_signal_row['fire_count'] if favorite_signal_row else 0
                }
                
                # Streak calculation (consecutive days with fires)
                cursor.execute('''
                    SELECT DATE(timestamp) as fire_date
                    FROM signal_fires
                    WHERE user_id = ?
                    GROUP BY DATE(timestamp)
                    ORDER BY fire_date DESC
                    LIMIT 30
                ''', (user_id,))
                
                fire_dates = [row['fire_date'] for row in cursor.fetchall()]
                current_streak = self._calculate_streak(fire_dates)
                
                return {
                    'user_id': user_id,
                    'total_fires': user_stats.total_fires if user_stats else 0,
                    'win_rate': user_stats.win_rate if user_stats else 0,
                    'pnl': user_stats.pnl if user_stats else 0,
                    'recent_fires_7d': recent_fires,
                    'favorite_signal': favorite_signal,
                    'current_streak': current_streak,
                    'last_updated': user_stats.last_updated.isoformat() if user_stats and user_stats.last_updated else None
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting user engagement summary: {e}")
            return {}
    
    def _calculate_streak(self, fire_dates: List[str]) -> int:
        """
        Calculate consecutive days streak.
        
        Args:
            fire_dates: List of fire dates in descending order
            
        Returns:
            int: Current streak count
        """
        if not fire_dates:
            return 0
            
        streak = 0
        current_date = datetime.now().date()
        
        for date_str in fire_dates:
            fire_date = datetime.fromisoformat(date_str).date()
            
            if fire_date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif fire_date == current_date - timedelta(days=1):
                streak += 1
                current_date = fire_date - timedelta(days=1)
            else:
                break
                
        return streak
    
    def get_leaderboard(self, metric: str = 'total_fires', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user leaderboard based on specified metric.
        
        Args:
            metric: Metric to sort by ('total_fires', 'win_rate', 'pnl')
            limit: Number of top users to return
            
        Returns:
            List of user stats dictionaries
        """
        valid_metrics = ['total_fires', 'win_rate', 'pnl']
        if metric not in valid_metrics:
            metric = 'total_fires'
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    SELECT user_id, total_fires, win_rate, pnl, last_updated
                    FROM user_stats
                    WHERE total_fires > 0
                    ORDER BY {metric} DESC
                    LIMIT ?
                ''', (limit,))
                
                return [
                    {
                        'user_id': row['user_id'],
                        'total_fires': row['total_fires'],
                        'win_rate': row['win_rate'],
                        'pnl': row['pnl'],
                        'last_updated': row['last_updated']
                    }
                    for row in cursor.fetchall()
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Export all data for a specific user.
        
        Args:
            user_id: User ID to export data for
            
        Returns:
            Dict containing all user data
        """
        user_stats = self.get_user_stats(user_id)
        signal_fires = self.get_user_signal_fires(user_id, limit=1000)
        engagement_summary = self.get_user_engagement_summary(user_id)
        
        return {
            'user_stats': user_stats.to_dict() if user_stats else None,
            'signal_fires': [fire.to_dict() for fire in signal_fires],
            'engagement_summary': engagement_summary,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old signal fire data.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            int: Number of records deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete old signal fires
                cursor.execute('''
                    DELETE FROM signal_fires
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                ''', (days_to_keep,))
                
                deleted_count = cursor.rowcount
                
                # Update metrics after cleanup
                cursor.execute('SELECT DISTINCT signal_id FROM signal_metrics')
                signal_ids = [row['signal_id'] for row in cursor.fetchall()]
                
                for signal_id in signal_ids:
                    self._update_signal_metrics(conn, signal_id)
                
                # Update user stats
                cursor.execute('SELECT DISTINCT user_id FROM user_stats')
                user_ids = [row['user_id'] for row in cursor.fetchall()]
                
                for user_id in user_ids:
                    self._update_user_stats(conn, user_id)
                
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old records")
                return deleted_count
                
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0

# Migration and Helper Functions

def run_migration():
    """
    Run database migration to create tables.
    
    This function initializes the database and creates all required tables.
    """
    try:
        db = EngagementDatabase()
        db.initialize_database()
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

def get_engagement_stats():
    """
    Helper function to get real-time engagement statistics.
    
    Returns:
        Dict containing engagement statistics
    """
    db = EngagementDatabase()
    return db.get_real_time_engagement_stats()

def record_user_signal_fire(user_id: int, signal_id: str, executed: bool = False):
    """
    Helper function to record a signal fire.
    
    Args:
        user_id: User ID who fired the signal
        signal_id: Signal ID that was fired
        executed: Whether the signal was executed
        
    Returns:
        bool: True if recorded successfully
    """
    db = EngagementDatabase()
    return db.record_signal_fire(user_id, signal_id, executed)

def get_user_engagement_data(user_id: int):
    """
    Helper function to get comprehensive user engagement data.
    
    Args:
        user_id: User ID to get data for
        
    Returns:
        Dict containing user engagement data
    """
    db = EngagementDatabase()
    return db.get_user_engagement_summary(user_id)

def update_user_performance(user_id: int, pnl_change: float, is_win: bool = True):
    """
    Helper function to update user performance metrics.
    
    Args:
        user_id: User ID to update
        pnl_change: Change in P&L
        is_win: Whether this was a winning trade
        
    Returns:
        bool: True if updated successfully
    """
    db = EngagementDatabase()
    return db.update_user_pnl(user_id, pnl_change, is_win)

# Main execution
if __name__ == "__main__":
    # Run migration when script is executed directly
    print("Running database migration...")
    if run_migration():
        print("Database migration completed successfully!")
        
        # Test the database functionality
        print("\nTesting database functionality...")
        
        # Test recording a signal fire
        test_user_id = 12345
        test_signal_id = "EURUSD_LONG_001"
        
        if record_user_signal_fire(test_user_id, test_signal_id, executed=True):
            print(f"✓ Successfully recorded signal fire for user {test_user_id}")
        
        # Test getting engagement stats
        stats = get_engagement_stats()
        if stats:
            print(f"✓ Real-time engagement stats: {stats}")
        
        # Test getting user engagement data
        user_data = get_user_engagement_data(test_user_id)
        if user_data:
            print(f"✓ User engagement data: {user_data}")
        
        print("\nDatabase is ready for use!")
    else:
        print("Database migration failed!")