#!/usr/bin/env python3
"""
Event Bus Slot Manager - Real-time slot tracking with event bus integration
Automatically manages slot allocation and release based on trade confirmations
"""

import json
import sqlite3
import logging
import time
from datetime import datetime
from typing import Dict, Optional

# Event bus imports
import sys
sys.path.append('/root/HydraX-v2/src')
from event_bus.consumer import EventConsumer
from src.bitten_core.fire_mode_database import FireModeDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EventBusSlotManager:
    """Real-time slot management using event bus confirmations"""
    
    def __init__(self):
        self.fire_mode_db = FireModeDatabase()
        self.bitten_db_path = "/root/HydraX-v2/bitten.db"
        self.consumer = EventConsumer()
        
        # Subscribe to confirmation events
        self.consumer.subscribe_to_schema("execution.confirmation.v1", self.handle_confirmation)
        
        # Track slot allocations per user
        self.user_slots = {}  # user_id -> {'manual': count, 'auto': count}
        
        logger.info("Event Bus Slot Manager initialized")
    
    def get_tier_limits(self, user_tier: str) -> Dict[str, int]:
        """Get slot limits based on user tier per ARCHITECTURE.md"""
        # Using the original ARCHITECTURE.md specification
        tier_limits = {
            'PRESS': {'manual': 0, 'auto': 0},           # Read-only
            'GLADIATOR': {'manual': 1, 'auto': 0},       # 1 manual slot
            'REAPER': {'manual': 2, 'auto': 0},          # 2 manual slots  
            'COMMANDER': {'manual': 3, 'auto': 3},       # 3 slots (can be manual or auto)
            'FANG': {'manual': 3, 'auto': 3},            # 3 slots (can be manual or auto)
            'FANG+': {'manual': 5, 'auto': 5}            # 5 slots (elite tier)
        }
        return tier_limits.get(user_tier.upper(), {'manual': 1, 'auto': 0})
    
    def handle_confirmation(self, event_data: Dict):
        """Handle trade confirmation events for slot management"""
        try:
            fire_id = event_data.get('fire_id')
            status = event_data.get('status', '').upper()
            ticket = event_data.get('ticket', 0)
            
            logger.info(f"📨 Confirmation received: {fire_id} | Status: {status} | Ticket: {ticket}")
            
            if status == 'FILLED' and ticket > 0:
                # Position opened - slot already allocated during fire command
                self.confirm_slot_allocation(fire_id, ticket)
                
            elif status == 'FAILED' or ticket == 0:
                # Trade failed - release the allocated slot
                self.release_slot_for_fire(fire_id, reason="TRADE_FAILED")
                
        except Exception as e:
            logger.error(f"Error handling confirmation: {e}")
    
    def confirm_slot_allocation(self, fire_id: str, ticket: int):
        """Confirm slot allocation when trade is filled"""
        try:
            conn = sqlite3.connect(self.bitten_db_path)
            cur = conn.cursor()
            
            # Get fire details
            cur.execute("""
                SELECT user_id, symbol, direction 
                FROM fires 
                WHERE fire_id = ?
            """, (fire_id,))
            fire_data = cur.fetchone()
            
            if fire_data:
                user_id, symbol, direction = fire_data
                
                # Update active_slots with ticket number for tracking
                cur.execute("""
                    UPDATE active_slots 
                    SET ticket = ?, status = 'FILLED'
                    WHERE user_id = ? AND mission_id = ?
                """, (ticket, user_id, fire_id))
                
                conn.commit()
                logger.info(f"✅ Slot confirmed for {fire_id}: User {user_id}, Ticket {ticket}")
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Error confirming slot allocation: {e}")
    
    def release_slot_for_fire(self, fire_id: str, reason: str = "POSITION_CLOSED"):
        """Release slot when position closes or fails"""
        try:
            conn = sqlite3.connect(self.bitten_db_path)
            cur = conn.cursor()
            
            # Get fire details and slot info
            cur.execute("""
                SELECT f.user_id, s.slot_type, s.slot_id
                FROM fires f
                LEFT JOIN active_slots s ON f.fire_id = s.mission_id
                WHERE f.fire_id = ?
            """, (fire_id,))
            slot_data = cur.fetchone()
            
            if slot_data:
                user_id, slot_type, slot_id = slot_data
                
                # Mark slot as closed
                cur.execute("""
                    UPDATE active_slots 
                    SET closed_at = CURRENT_TIMESTAMP, status = 'CLOSED'
                    WHERE slot_id = ?
                """, (slot_id,))
                
                # Decrement slot counter
                if slot_type == 'AUTO':
                    cur.execute("""
                        UPDATE user_fire_modes 
                        SET auto_slots_in_use = MAX(0, auto_slots_in_use - 1),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (user_id,))
                else:  # MANUAL
                    cur.execute("""
                        UPDATE user_fire_modes 
                        SET manual_slots_in_use = MAX(0, manual_slots_in_use - 1),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (user_id,))
                
                conn.commit()
                logger.info(f"🔓 Slot released for {fire_id}: User {user_id}, Type {slot_type}, Reason: {reason}")
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Error releasing slot: {e}")
    
    def get_real_time_slot_status(self, user_id: str, user_tier: str) -> Dict:
        """Get current slot usage with real-time data"""
        try:
            conn = sqlite3.connect(self.bitten_db_path)
            cur = conn.cursor()
            
            # Get current slot usage from active_slots table
            cur.execute("""
                SELECT slot_type, COUNT(*) 
                FROM active_slots 
                WHERE user_id = ? AND status = 'OPEN'
                GROUP BY slot_type
            """, (user_id,))
            active_slots = dict(cur.fetchall())
            
            # Get tier limits
            limits = self.get_tier_limits(user_tier)
            
            # Calculate available slots
            manual_used = active_slots.get('MANUAL', 0)
            auto_used = active_slots.get('AUTO', 0)
            
            status = {
                'user_id': user_id,
                'tier': user_tier,
                'manual': {
                    'used': manual_used,
                    'limit': limits['manual'],
                    'available': max(0, limits['manual'] - manual_used)
                },
                'auto': {
                    'used': auto_used,
                    'limit': limits['auto'],
                    'available': max(0, limits['auto'] - auto_used)
                },
                'total': {
                    'used': manual_used + auto_used,
                    'limit': limits['manual'] + limits['auto'],
                    'available': max(0, (limits['manual'] + limits['auto']) - (manual_used + auto_used))
                }
            }
            
            conn.close()
            return status
            
        except Exception as e:
            logger.error(f"Error getting slot status: {e}")
            return {}
    
    def allocate_slot(self, user_id: str, fire_id: str, symbol: str, slot_type: str, user_tier: str) -> bool:
        """Allocate a slot for new fire command"""
        try:
            # Check if slot is available
            status = self.get_real_time_slot_status(user_id, user_tier)
            
            if slot_type == 'AUTO':
                available = status['auto']['available']
            else:
                available = status['manual']['available']
            
            if available <= 0:
                logger.warning(f"❌ No {slot_type} slots available for user {user_id}")
                return False
            
            # Allocate the slot
            return self.fire_mode_db.occupy_slot(user_id, fire_id, symbol, slot_type, user_tier)
            
        except Exception as e:
            logger.error(f"Error allocating slot: {e}")
            return False
    
    def run(self):
        """Run the event bus slot manager"""
        logger.info("🎯 Event Bus Slot Manager starting...")
        logger.info("📡 Listening for confirmation events...")
        
        try:
            # Start consuming events
            self.consumer.start()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down Event Bus Slot Manager...")
            self.consumer.stop()
        except Exception as e:
            logger.error(f"Error in slot manager: {e}")

if __name__ == "__main__":
    manager = EventBusSlotManager()
    manager.run()