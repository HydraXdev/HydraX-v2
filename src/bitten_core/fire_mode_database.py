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
                max_auto_slots INTEGER DEFAULT 75,
                auto_slots_in_use INTEGER DEFAULT 0,
                manual_slots_in_use INTEGER DEFAULT 0,
                last_mode_change TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Slot tracking for both AUTO and MANUAL trades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_slots (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                slot_type TEXT NOT NULL DEFAULT 'MANUAL',  -- MANUAL or AUTO
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
        
        # Migration: Add new columns if they don't exist
        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN max_auto_slots INTEGER DEFAULT 75")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN auto_slots_in_use INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN manual_slots_in_use INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE active_slots ADD COLUMN slot_type TEXT DEFAULT 'MANUAL'")
        except sqlite3.OperationalError:
            pass
            
# [DISABLED BITMODE]         # BITMODE Migration: Add BITMODE column
        try:
            cursor.execute("ALTER TABLE user_fire_modes ADD COLUMN bitmode_enabled BOOLEAN DEFAULT FALSE")
        except sqlite3.OperationalError:
            pass
            
        # Migrate old slots_in_use to auto_slots_in_use
        cursor.execute('''
            UPDATE user_fire_modes 
            SET auto_slots_in_use = slots_in_use 
            WHERE auto_slots_in_use = 0 AND slots_in_use > 0
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
                SELECT current_mode, max_auto_slots, auto_slots_in_use, manual_slots_in_use, last_mode_change, bitmode_enabled
                FROM user_fire_modes
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                conn.close()
                return {
                    'current_mode': result[0],
                    'max_auto_slots': result[1],
                    'auto_slots_in_use': result[2],
                    'manual_slots_in_use': result[3],
                    'last_mode_change': result[4],
                    'bitmode_enabled': bool(result[5]) if len(result) > 5 else False,
                    # For backward compatibility
                    'max_slots': result[1],
                    'slots_in_use': result[2]
                }
            else:
                # Create default entry - CRITICAL FIX: Keep connection open
                logger.info(f"Creating default fire mode entry for new user {user_id}")
                cursor.execute('''
                    INSERT INTO user_fire_modes (user_id, current_mode, max_auto_slots, auto_slots_in_use, manual_slots_in_use)
                    VALUES (?, 'SELECT', 75, 0, 0)
                ''', (user_id,))
                conn.commit()
                conn.close()
                return {
                    'current_mode': 'SELECT',
                    'max_auto_slots': 75,
                    'auto_slots_in_use': 0,
                    'manual_slots_in_use': 0,
                    'last_mode_change': None,
                    'bitmode_enabled': False,
                    # For backward compatibility
                    'max_slots': 75,
                    'slots_in_use': 0
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
    
    @staticmethod
    def get_tier_slot_limits(tier: str) -> Dict[str, int]:
        """Get maximum allowed slots based on user tier"""
        tier_limits = {
            'NIBBLER': {'manual': 1, 'auto': 0},      # 1 manual slot only, no auto
            'FANG': {'manual': 2, 'auto': 0},         # 2 manual slots only, no auto
            'COMMANDER': {'manual': 10, 'auto': 5}    # 10 manual slots, 5 auto slots (testing)
        }
        return tier_limits.get(tier.upper(), {'manual': 1, 'auto': 0})
    
    def set_max_auto_slots(self, user_id: str, max_slots: int, user_tier: str = 'COMMANDER') -> bool:
        """Set user's maximum auto slots (only for COMMANDER tier)"""
        limits = self.get_tier_slot_limits(user_tier)
        max_allowed = limits['auto']
        
        if user_tier != 'COMMANDER':
            logger.error(f"Only COMMANDER tier can set auto slots")
            return False
            
        if max_slots < 1 or max_slots > max_allowed:
            logger.error(f"Invalid max_slots value: {max_slots} (max allowed for {user_tier}: {max_allowed})")
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE user_fire_modes 
                SET max_auto_slots = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (max_slots, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error setting max slots: {e}")
            conn.close()
            return False
    
    def check_slot_available(self, user_id: str, slot_type: str = 'AUTO', user_tier: str = 'COMMANDER') -> bool:
        """Check if user has available slot for specified type"""
        mode_info = self.get_user_mode(user_id)
        limits = self.get_tier_slot_limits(user_tier)
        
        if slot_type == 'AUTO':
            # Auto slots only for COMMANDER in AUTO mode
            if user_tier != 'COMMANDER' or mode_info['current_mode'] != 'AUTO':
                return False
            return mode_info['auto_slots_in_use'] < mode_info['max_auto_slots']
        else:  # MANUAL
            # Check manual slot limit based on tier
            return mode_info['manual_slots_in_use'] < limits['manual']
    
    def occupy_slot(self, user_id: str, mission_id: str, symbol: str, slot_type: str = 'AUTO', user_tier: str = 'COMMANDER') -> bool:
        """Occupy a slot for trade (AUTO or MANUAL)"""
        if not self.check_slot_available(user_id, slot_type, user_tier):
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Add active slot with type
            cursor.execute('''
                INSERT INTO active_slots (user_id, mission_id, symbol, slot_type)
                VALUES (?, ?, ?, ?)
            ''', (user_id, mission_id, symbol, slot_type))
            
            # Increment appropriate slot counter
            if slot_type == 'AUTO':
                cursor.execute('''
                    UPDATE user_fire_modes 
                    SET auto_slots_in_use = auto_slots_in_use + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
            else:  # MANUAL
                cursor.execute('''
                    UPDATE user_fire_modes 
                    SET manual_slots_in_use = manual_slots_in_use + 1,
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
            # First get the slot type before closing
            cursor.execute('''
                SELECT slot_type FROM active_slots
                WHERE user_id = ? AND mission_id = ? AND status = 'OPEN'
            ''', (user_id, mission_id))
            
            result = cursor.fetchone()
            if not result:
                logger.warning(f"No open slot found for user {user_id}, mission {mission_id}")
                conn.close()
                return False
                
            slot_type = result[0]
            
            # Mark slot as closed
            cursor.execute('''
                UPDATE active_slots 
                SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND mission_id = ? AND status = 'OPEN'
            ''', (user_id, mission_id))
            
            # Decrement appropriate slot counter
            if slot_type == 'AUTO':
                cursor.execute('''
                    UPDATE user_fire_modes 
                    SET auto_slots_in_use = MAX(0, auto_slots_in_use - 1),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
            else:  # MANUAL
                cursor.execute('''
                    UPDATE user_fire_modes 
                    SET manual_slots_in_use = MAX(0, manual_slots_in_use - 1),
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
            SELECT slot_id, mission_id, symbol, opened_at, slot_type
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
                'opened_at': row[3],
                'slot_type': row[4] if len(row) > 4 else 'MANUAL'
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
    
    def toggle_bitmode(self, user_id: str, enabled: bool, user_tier: str = 'COMMANDER') -> bool:
# [DISABLED BITMODE]         """Toggle BITMODE for user (FANG+ tiers only)"""
# [DISABLED BITMODE]         # Only FANG+ tiers can use BITMODE
        allowed_tiers = ['FANG', 'COMMANDER']
        if user_tier not in allowed_tiers:
# [DISABLED BITMODE]             logger.error(f"BITMODE not available for tier {user_tier} - FANG+ required")
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO user_fire_modes 
                (user_id, bitmode_enabled, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    bitmode_enabled = excluded.bitmode_enabled,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, enabled))
            
            conn.commit()
            conn.close()
            
# [DISABLED BITMODE]             logger.info(f"User {user_id} BITMODE {'enabled' if enabled else 'disabled'}")
            return True
            
        except Exception as e:
# [DISABLED BITMODE]             logger.error(f"Error toggling BITMODE: {e}")
            conn.close()
            return False
    
    def is_bitmode_enabled(self, user_id: str) -> bool:
# [DISABLED BITMODE]         """Check if BITMODE is enabled for user"""
        user_mode = self.get_user_mode(user_id)
        return user_mode.get('bitmode_enabled', False)

# Create singleton instance
fire_mode_db = FireModeDatabase()