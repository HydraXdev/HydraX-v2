#!/usr/bin/env python3
"""
Fire Mode Database Schema and Management
Handles user fire mode preferences and slot management
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

class FireModeDatabase:
    """Manages fire mode settings and slot tracking"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/fire_modes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User fire mode settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_fire_modes (
                user_id TEXT PRIMARY KEY,
                current_mode TEXT DEFAULT 'SELECT',
                max_slots INTEGER DEFAULT 1,
                slots_in_use INTEGER DEFAULT 0,
                last_mode_change TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Slot tracking for AUTO mode
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_slots (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                status TEXT DEFAULT 'OPEN',
                FOREIGN KEY (user_id) REFERENCES user_fire_modes(user_id)
            )
        ''')
        
        # Fire mode history for analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fire_mode_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                old_mode TEXT,
                new_mode TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT
            )
        ''')
        
        # Chaingun inventory
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chaingun_inventory (
                user_id TEXT PRIMARY KEY,
                chaingun_count INTEGER DEFAULT 0,
                last_awarded TIMESTAMP,
                total_earned INTEGER DEFAULT 0,
                total_used INTEGER DEFAULT 0
            )
        ''')
        
        # Chaingun sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chaingun_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                shots_fired INTEGER DEFAULT 0,
                max_risk_reached REAL DEFAULT 0.02,
                total_profit REAL DEFAULT 0,
                parachute_deployed BOOLEAN DEFAULT FALSE,
                end_reason TEXT,
                badge_earned TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Fire mode database initialized")
    
    def get_user_mode(self, user_id: str) -> Dict:
        """Get user's current fire mode settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT current_mode, max_slots, slots_in_use, last_mode_change
                FROM user_fire_modes
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                conn.close()
                return {
                    'current_mode': result[0],
                    'max_slots': result[1],
                    'slots_in_use': result[2],
                    'last_mode_change': result[3]
                }
            else:
                # Create default entry - CRITICAL FIX: Keep connection open
                logger.info(f"Creating default fire mode entry for new user {user_id}")
                cursor.execute('''
                    INSERT INTO user_fire_modes (user_id, current_mode, max_slots, slots_in_use)
                    VALUES (?, 'SELECT', 1, 0)
                ''', (user_id,))
                conn.commit()
                conn.close()
                return {
                    'current_mode': 'SELECT',
                    'max_slots': 1,
                    'slots_in_use': 0,
                    'last_mode_change': None
                }
        except Exception as e:
            logger.error(f"Critical error in get_user_mode for user {user_id}: {e}")
            conn.close()
            # Return safe defaults to prevent total failure
            return {
                'current_mode': 'SELECT',
                'max_slots': 1,
                'slots_in_use': 0,
                'last_mode_change': None
            }
    
    def set_user_mode(self, user_id: str, new_mode: str, reason: str = None) -> bool:
        """Set user's fire mode"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current mode for history without recursion
            cursor.execute('SELECT current_mode FROM user_fire_modes WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            old_mode = result[0] if result else 'SELECT'
            
            # Update or insert mode
            cursor.execute('''
                INSERT OR REPLACE INTO user_fire_modes 
                (user_id, current_mode, last_mode_change, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, new_mode))
            
            # Record history
            cursor.execute('''
                INSERT INTO fire_mode_history (user_id, old_mode, new_mode, reason)
                VALUES (?, ?, ?, ?)
            ''', (user_id, old_mode, new_mode, reason))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User {user_id} fire mode changed from {old_mode} to {new_mode}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting fire mode: {e}")
            conn.close()
            return False
    
    def set_max_slots(self, user_id: str, max_slots: int) -> bool:
        """Set user's maximum AUTO mode slots"""
        if max_slots < 1 or max_slots > 3:
            logger.error(f"Invalid max_slots value: {max_slots}")
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE user_fire_modes 
                SET max_slots = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (max_slots, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error setting max slots: {e}")
            conn.close()
            return False
    
    def check_slot_available(self, user_id: str) -> bool:
        """Check if user has available slot for AUTO mode"""
        mode_info = self.get_user_mode(user_id)
        return mode_info['slots_in_use'] < mode_info['max_slots']
    
    def occupy_slot(self, user_id: str, mission_id: str, symbol: str) -> bool:
        """Occupy a slot for AUTO mode trade"""
        if not self.check_slot_available(user_id):
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Add active slot
            cursor.execute('''
                INSERT INTO active_slots (user_id, mission_id, symbol)
                VALUES (?, ?, ?)
            ''', (user_id, mission_id, symbol))
            
            # Increment slots in use
            cursor.execute('''
                UPDATE user_fire_modes 
                SET slots_in_use = slots_in_use + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error occupying slot: {e}")
            conn.close()
            return False
    
    def release_slot(self, user_id: str, mission_id: str) -> bool:
        """Release a slot when trade closes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Mark slot as closed
            cursor.execute('''
                UPDATE active_slots 
                SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND mission_id = ? AND status = 'OPEN'
            ''', (user_id, mission_id))
            
            # Decrement slots in use
            cursor.execute('''
                UPDATE user_fire_modes 
                SET slots_in_use = MAX(0, slots_in_use - 1),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error releasing slot: {e}")
            conn.close()
            return False
    
    def get_active_slots(self, user_id: str) -> List[Dict]:
        """Get user's active slots"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT slot_id, mission_id, symbol, opened_at
            FROM active_slots
            WHERE user_id = ? AND status = 'OPEN'
            ORDER BY opened_at DESC
        ''', (user_id,))
        
        slots = []
        for row in cursor.fetchall():
            slots.append({
                'slot_id': row[0],
                'mission_id': row[1],
                'symbol': row[2],
                'opened_at': row[3]
            })
        
        conn.close()
        return slots
    
    def get_chaingun_inventory(self, user_id: str) -> int:
        """Get user's chaingun inventory count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT chaingun_count FROM chaingun_inventory WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def award_chaingun(self, user_id: str, count: int = 1) -> bool:
        """Award chaingun(s) to user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO chaingun_inventory (user_id, chaingun_count, total_earned)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    chaingun_count = chaingun_count + ?,
                    total_earned = total_earned + ?,
                    last_awarded = CURRENT_TIMESTAMP
            ''', (user_id, count, count, count, count))
            
            conn.commit()
            conn.close()
            logger.info(f"Awarded {count} chaingun(s) to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error awarding chaingun: {e}")
            conn.close()
            return False

# Create singleton instance
fire_mode_db = FireModeDatabase()