"""
Database operations for BITTEN webapp
Centralized database access layer
"""

import sqlite3
import json
import time
import logging
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

@contextmanager
def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class SignalOperations:
    """Operations related to signals"""
    
    @staticmethod
    def get_signal(signal_id):
        """Get signal from database"""
        with get_connection() as conn:
            result = conn.execute("""
                SELECT signal_id, symbol, direction, entry, sl, tp, 
                       confidence, payload_json, created_at
                FROM signals 
                WHERE signal_id = ?
            """, (signal_id,)).fetchone()
            
            if result:
                return dict(result)
            return None
    
    @staticmethod
    def get_recent_signals(limit=10):
        """Get recent signals"""
        with get_connection() as conn:
            results = conn.execute("""
                SELECT signal_id, symbol, direction, entry, sl, tp, 
                       confidence, created_at
                FROM signals 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(r) for r in results]
    
    @staticmethod
    def save_signal(signal_data):
        """Save signal to database"""
        with get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO signals 
                (signal_id, symbol, direction, entry, sl, tp, confidence, 
                 payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data['signal_id'],
                signal_data['symbol'],
                signal_data['direction'],
                signal_data.get('entry_price', 0),
                signal_data.get('sl', 0),
                signal_data.get('tp', 0),
                signal_data.get('confidence', 0),
                json.dumps(signal_data),
                int(time.time())
            ))
            conn.commit()

class MissionOperations:
    """Operations related to missions"""
    
    @staticmethod
    def create_mission(mission_id, signal_id, user_id, payload, expires_seconds=7200):
        """Create a new mission"""
        with get_connection() as conn:
            # Check if mission already exists
            existing = conn.execute(
                'SELECT mission_id FROM missions WHERE mission_id = ?',
                (mission_id,)
            ).fetchone()
            
            if not existing:
                conn.execute('''
                    INSERT INTO missions 
                    (mission_id, signal_id, payload_json, status, expires_at, created_at, target_uuid)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mission_id,
                    signal_id,
                    json.dumps(payload),
                    'PENDING',
                    int(time.time()) + expires_seconds,
                    int(time.time()),
                    user_id
                ))
                conn.commit()
                return True
            return False
    
    @staticmethod
    def get_mission(mission_id):
        """Get mission from database"""
        with get_connection() as conn:
            result = conn.execute("""
                SELECT mission_id, signal_id, payload_json, status, 
                       expires_at, created_at, target_uuid
                FROM missions 
                WHERE mission_id = ?
            """, (mission_id,)).fetchone()
            
            if result:
                mission = dict(result)
                if mission['payload_json']:
                    try:
                        mission['payload'] = json.loads(mission['payload_json'])
                    except:
                        mission['payload'] = {}
                return mission
            return None
    
    @staticmethod
    def update_mission_status(mission_id, status):
        """Update mission status"""
        with get_connection() as conn:
            conn.execute("""
                UPDATE missions 
                SET status = ?, updated_at = ?
                WHERE mission_id = ?
            """, (status, int(time.time()), mission_id))
            conn.commit()

class FireOperations:
    """Operations related to fire commands"""
    
    @staticmethod
    def create_fire_record(fire_data):
        """Create a fire record"""
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO fires 
                (fire_id, mission_id, user_id, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                fire_data.get('fire_id'),
                fire_data.get('mission_id'),
                fire_data.get('user_id'),
                'PENDING',
                int(time.time())
            ))
            conn.commit()
    
    @staticmethod
    def update_fire_status(fire_id, status, ticket=None, price=None):
        """Update fire record with execution result"""
        with get_connection() as conn:
            if ticket and price:
                conn.execute("""
                    UPDATE fires 
                    SET status = ?, ticket = ?, price = ?, updated_at = ?
                    WHERE fire_id = ?
                """, (status, ticket, price, int(time.time()), fire_id))
            else:
                conn.execute("""
                    UPDATE fires 
                    SET status = ?, updated_at = ?
                    WHERE fire_id = ?
                """, (status, int(time.time()), fire_id))
            conn.commit()
    
    @staticmethod
    def get_user_fires(user_id, limit=10):
        """Get recent fires for a user"""
        with get_connection() as conn:
            results = conn.execute("""
                SELECT fire_id, mission_id, status, ticket, price, created_at
                FROM fires 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()
            
            return [dict(r) for r in results]

class UserOperations:
    """Operations related to users"""
    
    @staticmethod
    def get_user(user_id):
        """Get user data"""
        with get_connection() as conn:
            result = conn.execute("""
                SELECT user_id, tier, xp, risk_pct_default, max_concurrent, 
                       daily_dd_limit, cooldown_s, balance_cache, streak, last_fire_at
                FROM users 
                WHERE user_id = ?
            """, (str(user_id),)).fetchone()
            
            if result:
                return dict(result)
            return None
    
    @staticmethod
    def create_or_update_user(user_id, tier='GRUNT'):
        """Create or update user"""
        with get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, tier, xp, risk_pct_default, max_concurrent, daily_dd_limit, cooldown_s, balance_cache, streak, last_fire_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(user_id), tier, 0, 2.0, 3, 10.0, 60, 0, 0, 0))
            conn.commit()
    
    @staticmethod
    def get_user_ea_instance(user_id):
        """Get user's EA instance data"""
        with get_connection() as conn:
            result = conn.execute("""
                SELECT target_uuid, account_login, broker, currency, leverage,
                       last_balance, last_equity, last_seen
                FROM ea_instances 
                WHERE user_id = ?
                ORDER BY last_seen DESC
                LIMIT 1
            """, (str(user_id),)).fetchone()
            
            if result:
                return dict(result)
            return None
    
    @staticmethod
    def update_user_auto_mode(user_id, auto_enabled):
        """Update user's auto fire mode"""
        # Store in separate config since users table doesn't have auto_fire column
        # This would be handled by fire mode system
        return True