"""
Engagement Database Module
Provides database functions for webapp API endpoints
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random
import os

class EngagementDB:
    """Database interface for engagement tracking"""
    
    def __init__(self, db_path: str = "data/engagement.db"):
        """Initialize engagement database"""
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_tables()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _initialize_tables(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User engagement table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_engagement (
                    user_id TEXT PRIMARY KEY,
                    total_fires INTEGER DEFAULT 0,
                    total_signals_engaged INTEGER DEFAULT 0,
                    last_fire_time TEXT,
                    streak_days INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Fire actions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fire_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL,
                    fired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT DEFAULT 'fire'
                )
            """)
            
            # Signal engagement table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signal_engagement (
                    signal_id TEXT PRIMARY KEY,
                    total_fires INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    last_fire_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Active signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_signals (
                    signal_id TEXT PRIMARY KEY,
                    signal_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.commit()
    
    def handle_fire_action(self, user_id: str, signal_id: str) -> Dict[str, Any]:
        """Handle user fire action"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Record fire action
                cursor.execute("""
                    INSERT INTO fire_actions (user_id, signal_id, fired_at)
                    VALUES (?, ?, ?)
                """, (user_id, signal_id, datetime.now().isoformat()))
                
                # Update user engagement
                cursor.execute("""
                    INSERT INTO user_engagement (user_id, total_fires, total_signals_engaged, last_fire_time, updated_at)
                    VALUES (?, 1, 1, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        total_fires = total_fires + 1,
                        total_signals_engaged = total_signals_engaged + 1,
                        last_fire_time = ?,
                        updated_at = ?
                """, (user_id, datetime.now().isoformat(), datetime.now().isoformat(),
                     datetime.now().isoformat(), datetime.now().isoformat()))
                
                # Update signal engagement
                cursor.execute("""
                    INSERT INTO signal_engagement (signal_id, total_fires, unique_users, last_fire_time, updated_at)
                    VALUES (?, 1, 1, ?, ?)
                    ON CONFLICT(signal_id) DO UPDATE SET
                        total_fires = total_fires + 1,
                        last_fire_time = ?,
                        updated_at = ?
                """, (signal_id, datetime.now().isoformat(), datetime.now().isoformat(),
                     datetime.now().isoformat(), datetime.now().isoformat()))
                
                # Update unique users count for signal
                cursor.execute("""
                    UPDATE signal_engagement 
                    SET unique_users = (
                        SELECT COUNT(DISTINCT user_id) 
                        FROM fire_actions 
                        WHERE signal_id = ?
                    )
                    WHERE signal_id = ?
                """, (signal_id, signal_id))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Fire action recorded successfully",
                    "user_id": user_id,
                    "signal_id": signal_id,
                    "fired_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_signal_stats(self, signal_id: str) -> Dict[str, Any]:
        """Get live engagement data for a signal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get signal engagement stats
                cursor.execute("""
                    SELECT total_fires, unique_users, last_fire_time, created_at, updated_at
                    FROM signal_engagement 
                    WHERE signal_id = ?
                """, (signal_id,))
                
                result = cursor.fetchone()
                
                if result:
                    total_fires, unique_users, last_fire_time, created_at, updated_at = result
                    
                    # Get recent fire activity (last 24 hours)
                    cursor.execute("""
                        SELECT COUNT(*) as recent_fires
                        FROM fire_actions 
                        WHERE signal_id = ? 
                        AND fired_at > datetime('now', '-1 day')
                    """, (signal_id,))
                    
                    recent_fires = cursor.fetchone()[0]
                    
                    return {
                        "signal_id": signal_id,
                        "total_fires": total_fires,
                        "unique_users": unique_users,
                        "recent_fires_24h": recent_fires,
                        "last_fire_time": last_fire_time,
                        "engagement_rate": round((total_fires / max(unique_users, 1)), 2),
                        "created_at": created_at,
                        "updated_at": updated_at
                    }
                else:
                    return {
                        "signal_id": signal_id,
                        "total_fires": 0,
                        "unique_users": 0,
                        "recent_fires_24h": 0,
                        "last_fire_time": None,
                        "engagement_rate": 0.0,
                        "created_at": None,
                        "updated_at": None
                    }
                    
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user engagement stats
                cursor.execute("""
                    SELECT total_fires, total_signals_engaged, last_fire_time, streak_days, created_at, updated_at
                    FROM user_engagement 
                    WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    total_fires, total_signals_engaged, last_fire_time, streak_days, created_at, updated_at = result
                    
                    # Get recent activity (last 7 days)
                    cursor.execute("""
                        SELECT COUNT(*) as recent_fires
                        FROM fire_actions 
                        WHERE user_id = ? 
                        AND fired_at > datetime('now', '-7 days')
                    """, (user_id,))
                    
                    recent_fires = cursor.fetchone()[0]
                    
                    # Get unique signals fired
                    cursor.execute("""
                        SELECT COUNT(DISTINCT signal_id) as unique_signals
                        FROM fire_actions 
                        WHERE user_id = ?
                    """, (user_id,))
                    
                    unique_signals = cursor.fetchone()[0]
                    
                    # Calculate user tier based on activity
                    if total_fires >= 1000:
                        tier = "commander"
                    elif total_fires >= 100:
                        tier = "fang"
                    else:
                        tier = "nibbler"
                    
                    return {
                        "user_id": user_id,
                        "total_fires": total_fires,
                        "total_signals_engaged": total_signals_engaged,
                        "unique_signals_fired": unique_signals,
                        "recent_fires_7d": recent_fires,
                        "last_fire_time": last_fire_time,
                        "streak_days": streak_days,
                        "tier": tier,
                        "avg_fires_per_signal": round((total_fires / max(unique_signals, 1)), 2),
                        "created_at": created_at,
                        "updated_at": updated_at
                    }
                else:
                    return {
                        "user_id": user_id,
                        "total_fires": 0,
                        "total_signals_engaged": 0,
                        "unique_signals_fired": 0,
                        "recent_fires_7d": 0,
                        "last_fire_time": None,
                        "streak_days": 0,
                        "tier": "nibbler",
                        "avg_fires_per_signal": 0.0,
                        "created_at": None,
                        "updated_at": None
                    }
                    
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def get_active_signals(self) -> List[Dict[str, Any]]:
        """Get all active signals with engagement counts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get active signals with engagement data
                cursor.execute("""
                    SELECT 
                        a.signal_id,
                        a.signal_data,
                        a.created_at,
                        a.expires_at,
                        COALESCE(s.total_fires, 0) as total_fires,
                        COALESCE(s.unique_users, 0) as unique_users,
                        s.last_fire_time
                    FROM active_signals a
                    LEFT JOIN signal_engagement s ON a.signal_id = s.signal_id
                    WHERE a.is_active = 1 
                    AND (a.expires_at IS NULL OR a.expires_at > datetime('now'))
                    ORDER BY a.created_at DESC
                """)
                
                results = cursor.fetchall()
                
                signals = []
                for result in results:
                    signal_id, signal_data, created_at, expires_at, total_fires, unique_users, last_fire_time = result
                    
                    # Parse signal data if it's JSON
                    try:
                        parsed_signal_data = json.loads(signal_data) if signal_data else {}
                    except:
                        parsed_signal_data = {"raw_data": signal_data}
                    
                    signals.append({
                        "signal_id": signal_id,
                        "signal_data": parsed_signal_data,
                        "engagement": {
                            "total_fires": total_fires,
                            "unique_users": unique_users,
                            "last_fire_time": last_fire_time
                        },
                        "created_at": created_at,
                        "expires_at": expires_at
                    })
                
                return signals
                
        except Exception as e:
            return [{"error": str(e)}]
    
    def add_active_signal(self, signal_id: str, signal_data: Dict[str, Any], expires_in_hours: int = 24) -> bool:
        """Add a new active signal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO active_signals (signal_id, signal_data, expires_at)
                    VALUES (?, ?, ?)
                """, (signal_id, json.dumps(signal_data), expires_at.isoformat()))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding active signal: {e}")
            return False
    
    def cleanup_expired_signals(self):
        """Remove expired signals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE active_signals 
                    SET is_active = 0 
                    WHERE expires_at < datetime('now')
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"Error cleaning up expired signals: {e}")

# Create global instance
engagement_db = EngagementDB()

# Export functions for compatibility
def handle_fire_action(user_id: str, signal_id: str) -> Dict[str, Any]:
    """Handle user fire action"""
    return engagement_db.handle_fire_action(user_id, signal_id)

def get_signal_stats(signal_id: str) -> Dict[str, Any]:
    """Get live engagement data for a signal"""
    return engagement_db.get_signal_stats(signal_id)

def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get user statistics"""
    return engagement_db.get_user_stats(user_id)

def get_active_signals_with_engagement() -> List[Dict[str, Any]]:
    """Get all active signals with engagement counts"""
    return engagement_db.get_active_signals()

def add_active_signal(signal_id: str, signal_data: Dict[str, Any], expires_in_hours: int = 24) -> bool:
    """Add a new active signal"""
    return engagement_db.add_active_signal(signal_id, signal_data, expires_in_hours)

def cleanup_expired_signals():
    """Remove expired signals"""
    return engagement_db.cleanup_expired_signals()