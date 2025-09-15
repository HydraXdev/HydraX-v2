#!/usr/bin/env python3
"""
Position Slot Manager - Processes enhanced EA heartbeats with position tracking
Manages slot availability for AUTO fire based on actual positions
"""

import json
import sqlite3
import time
import zmq
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class PositionSlotManager:
    """Manages position tracking and slot availability from EA heartbeats"""
    
    def __init__(self, db_path="/root/HydraX-v2/bitten.db"):
        self.db_path = db_path
        self.context = zmq.Context()
        self.subscriber = None
        self.position_cache = {}  # user_id -> position list
        self.last_update = {}  # user_id -> timestamp
        
        # Initialize database tables
        self._init_database()
        
    def _init_database(self):
        """Create position tracking tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced ea_instances table with position data
        try:
            cursor.execute("""
                ALTER TABLE ea_instances 
                ADD COLUMN open_positions INTEGER DEFAULT 0
            """)
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("""
                ALTER TABLE ea_instances 
                ADD COLUMN position_data TEXT DEFAULT '{}'
            """)
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create position tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS position_tracking (
                ticket INTEGER PRIMARY KEY,
                fire_id TEXT,
                user_id TEXT,
                symbol TEXT,
                direction TEXT,
                open_price REAL,
                current_price REAL,
                volume REAL,
                pnl REAL,
                opened_at INTEGER,
                updated_at INTEGER,
                status TEXT DEFAULT 'OPEN'
            )
        """)
        
        # Create slot tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS slot_tracking (
                user_id TEXT PRIMARY KEY,
                max_slots INTEGER DEFAULT 10,
                used_slots INTEGER DEFAULT 0,
                auto_slots_available INTEGER DEFAULT 3,
                auto_slots_in_use INTEGER DEFAULT 0,
                positions_json TEXT DEFAULT '[]',
                updated_at INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
        
    def process_heartbeat(self, heartbeat_data: Dict):
        """Process enhanced heartbeat with position details"""
        uuid = heartbeat_data.get("target_uuid")
        if not uuid:
            return
            
        # Get user_id from EA mapping
        user_id = self._get_user_for_ea(uuid)
        if not user_id:
            print(f"⚠️ No user mapping for EA {uuid}")
            return
            
        # Extract position data
        open_positions = heartbeat_data.get("open_positions", 0)
        positions = heartbeat_data.get("positions", [])
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update EA instance with position count
            cursor.execute("""
                UPDATE ea_instances 
                SET open_positions = ?,
                    position_data = ?,
                    last_seen = ?
                WHERE target_uuid = ?
            """, (open_positions, json.dumps(positions), int(time.time()), uuid))
            
            # Clear old positions for this user
            cursor.execute("""
                UPDATE position_tracking 
                SET status = 'CLOSED_STALE'
                WHERE user_id = ? AND status = 'OPEN'
            """, (user_id,))
            
            # Insert/update current positions
            for pos in positions:
                cursor.execute("""
                    INSERT OR REPLACE INTO position_tracking
                    (ticket, fire_id, user_id, symbol, direction, 
                     open_price, current_price, volume, pnl, 
                     opened_at, updated_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """, (
                    pos.get("ticket"),
                    pos.get("fire_id", ""),
                    user_id,
                    pos.get("symbol"),
                    pos.get("direction"),
                    pos.get("open_price", 0),
                    pos.get("current_price", 0),
                    pos.get("volume", 0),
                    pos.get("pnl", 0),
                    int(time.time()),
                    int(time.time())
                ))
            
            # Update slot tracking
            cursor.execute("""
                INSERT OR REPLACE INTO slot_tracking
                (user_id, used_slots, positions_json, updated_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, open_positions, json.dumps(positions), int(time.time())))
            
            conn.commit()
            
            # Update cache
            self.position_cache[user_id] = positions
            self.last_update[user_id] = time.time()
            
            print(f"✅ Updated positions for user {user_id}: {open_positions} open positions")
            
        except Exception as e:
            print(f"❌ Error updating positions: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def process_position_closed(self, close_data: Dict):
        """Process position closed notification from EA"""
        ticket = close_data.get("ticket")
        fire_id = close_data.get("fire_id")
        uuid = close_data.get("uuid")
        profit = close_data.get("profit", 0)
        reason = close_data.get("reason", "UNKNOWN")
        
        if not ticket:
            return
            
        user_id = self._get_user_for_ea(uuid)
        if not user_id:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update position status
            cursor.execute("""
                UPDATE position_tracking
                SET status = ?,
                    pnl = ?,
                    updated_at = ?
                WHERE ticket = ?
            """, (f"CLOSED_{reason}", profit, int(time.time()), ticket))
            
            # Update fire record if we have fire_id
            if fire_id:
                cursor.execute("""
                    UPDATE fires
                    SET status = ?,
                        updated_at = ?
                    WHERE fire_id = ?
                """, (f"CLOSED_{reason}", int(time.time()), fire_id))
                
            # Free the slot
            self._free_slot_for_user(cursor, user_id)
            
            conn.commit()
            print(f"📊 Position closed: Ticket={ticket}, Fire={fire_id}, Reason={reason}, P&L={profit}")
            
        except Exception as e:
            print(f"❌ Error processing position close: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def can_auto_fire(self, user_id: str, symbol: str) -> Tuple[bool, str]:
        """Check if user can auto-fire based on current positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current position count
            cursor.execute("""
                SELECT COUNT(*) FROM position_tracking
                WHERE user_id = ? AND status = 'OPEN'
            """, (user_id,))
            position_count = cursor.fetchone()[0]
            
            # Check max positions (10 hard limit)
            if position_count >= 10:
                return False, f"Max positions reached ({position_count}/10)"
                
            # Check if position already exists on symbol (hedge prevention)
            cursor.execute("""
                SELECT direction FROM position_tracking
                WHERE user_id = ? AND symbol = ? AND status = 'OPEN'
            """, (user_id, symbol))
            existing = cursor.fetchone()
            
            if existing:
                return False, f"Position already open on {symbol}"
                
            # Check AUTO slots for COMMANDER tier
            cursor.execute("""
                SELECT auto_slots_available, auto_slots_in_use
                FROM slot_tracking
                WHERE user_id = ?
            """, (user_id,))
            slot_data = cursor.fetchone()
            
            if slot_data:
                available, in_use = slot_data
                if in_use >= available:
                    return False, f"No AUTO slots available ({in_use}/{available} used)"
                    
            return True, "OK"
            
        except Exception as e:
            print(f"❌ Error checking auto-fire: {e}")
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
            
    def _free_slot_for_user(self, cursor, user_id: str):
        """Free a slot when position closes"""
        cursor.execute("""
            UPDATE slot_tracking
            SET used_slots = MAX(0, used_slots - 1),
                auto_slots_in_use = MAX(0, auto_slots_in_use - 1),
                updated_at = ?
            WHERE user_id = ?
        """, (int(time.time()), user_id))
        
    def _get_user_for_ea(self, uuid: str) -> Optional[str]:
        """Get user_id for EA UUID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id FROM ea_instances
            WHERE target_uuid = ?
        """, (uuid,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
        
    def get_position_summary(self, user_id: str) -> Dict:
        """Get position summary for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count,
                   SUM(pnl) as total_pnl
            FROM position_tracking
            WHERE user_id = ? AND status = 'OPEN'
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "open_positions": result[0] if result else 0,
            "total_pnl": result[1] if result and result[1] else 0.0,
            "slots_available": 10 - (result[0] if result else 0)
        }
        
    def monitor_heartbeats(self):
        """Monitor heartbeats from command router logs"""
        # This would connect to ZMQ or parse logs
        # For now, we'll integrate with command_router.py
        print("🛡️ Position Slot Manager initialized")
        print("Waiting for enhanced heartbeats with position data...")
        
if __name__ == "__main__":
    manager = PositionSlotManager()
    
    # Test with sample heartbeat
    sample_heartbeat = {
        "type": "HEARTBEAT",
        "target_uuid": "COMMANDER_DEV_001",
        "open_positions": 3,
        "positions": [
            {
                "ticket": 12345,
                "fire_id": "ELITE_GUARD_EURUSD_123456",
                "symbol": "EURUSD",
                "direction": "BUY",
                "open_price": 1.1000,
                "current_price": 1.1025,
                "volume": 0.10,
                "pnl": 25.00
            }
        ]
    }
    
    manager.process_heartbeat(sample_heartbeat)
    
    # Check if user can auto-fire
    can_fire, reason = manager.can_auto_fire("7176191872", "GBPUSD")
    print(f"Can auto-fire GBPUSD: {can_fire} - {reason}")
    
    # Get position summary
    summary = manager.get_position_summary("7176191872")
    print(f"Position summary: {summary}")