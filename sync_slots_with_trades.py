#!/usr/bin/env python3
"""
Real-time Slot Synchronization with Actual Trade Status
Ensures fire mode slots accurately reflect open/closed trades
"""

import sqlite3
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SlotSynchronizer:
    def __init__(self):
        self.bitten_db = "/root/HydraX-v2/bitten.db"
        self.fire_modes_db = "/root/HydraX-v2/data/fire_modes.db"
    
    def get_closed_trades_with_open_slots(self):
        """Find trades that are closed but still have open slots"""
        try:
            # Get trades marked as closed in fires table
            bitten_conn = sqlite3.connect(self.bitten_db)
            bitten_cur = bitten_conn.cursor()
            
            bitten_cur.execute("""
                SELECT fire_id, user_id, mission_id, status 
                FROM fires 
                WHERE status IN ('CLOSED_AUTO_DETECTED', 'CLOSED_MANUAL', 'FAILED', 'CANCELLED')
            """)
            closed_trades = bitten_cur.fetchall()
            bitten_conn.close()
            
            # Get slots still marked as open in fire_modes database
            slots_conn = sqlite3.connect(self.fire_modes_db)
            slots_cur = slots_conn.cursor()
            
            mismatched = []
            
            for fire_id, user_id, mission_id, status in closed_trades:
                slots_cur.execute("""
                    SELECT slot_id, mission_id, slot_type, status as slot_status
                    FROM active_slots 
                    WHERE user_id = ? AND mission_id = ? AND status = 'OPEN'
                """, (user_id, mission_id))
                
                open_slot = slots_cur.fetchone()
                if open_slot:
                    mismatched.append({
                        'fire_id': fire_id,
                        'user_id': user_id,
                        'mission_id': mission_id,
                        'trade_status': status,
                        'slot_id': open_slot[0],
                        'slot_type': open_slot[2]
                    })
            
            slots_conn.close()
            return mismatched
            
        except Exception as e:
            logger.error(f"Error finding mismatched slots: {e}")
            return []
    
    def sync_slot_status(self, user_id, mission_id, slot_type):
        """Close a slot and update counters"""
        try:
            conn = sqlite3.connect(self.fire_modes_db)
            cur = conn.cursor()
            
            # Close the slot
            cur.execute("""
                UPDATE active_slots 
                SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND mission_id = ? AND status = 'OPEN'
            """, (user_id, mission_id))
            
            # Update slot counters
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
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error syncing slot for {user_id}/{mission_id}: {e}")
            return False
    
    def check_stale_slots(self, hours_old=24):
        """Find and close slots older than specified hours without recent activity"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            
            conn = sqlite3.connect(self.fire_modes_db)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT user_id, mission_id, slot_type, opened_at
                FROM active_slots 
                WHERE status = 'OPEN' AND opened_at < ?
            """, (cutoff_time,))
            
            stale_slots = cur.fetchall()
            conn.close()
            
            logger.info(f"Found {len(stale_slots)} stale slots older than {hours_old} hours")
            
            for user_id, mission_id, slot_type, opened_at in stale_slots:
                logger.warning(f"Closing stale {slot_type} slot: {user_id}/{mission_id} (opened: {opened_at})")
                self.sync_slot_status(user_id, mission_id, slot_type)
            
            return len(stale_slots)
            
        except Exception as e:
            logger.error(f"Error checking stale slots: {e}")
            return 0
    
    def full_synchronization(self):
        """Complete slot synchronization process"""
        logger.info("🔄 Starting full slot synchronization...")
        
        # Step 1: Fix mismatched slots (closed trades with open slots)
        mismatched = self.get_closed_trades_with_open_slots()
        fixed_count = 0
        
        logger.info(f"Found {len(mismatched)} mismatched slots")
        
        for mismatch in mismatched:
            logger.info(f"Fixing slot: {mismatch['user_id']}/{mismatch['mission_id']} "
                       f"(trade: {mismatch['trade_status']}, slot: OPEN)")
            
            if self.sync_slot_status(mismatch['user_id'], mismatch['mission_id'], mismatch['slot_type']):
                fixed_count += 1
        
        # Step 2: Close stale slots (older than 24 hours)
        stale_count = self.check_stale_slots(24)
        
        # Step 3: Verify current slot counts
        try:
            conn = sqlite3.connect(self.fire_modes_db)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT user_id, current_mode, auto_slots_in_use, max_auto_slots,
                       manual_slots_in_use
                FROM user_fire_modes
            """)
            
            users = cur.fetchall()
            
            for user_id, mode, auto_used, auto_max, manual_used in users:
                # Count actual open slots
                cur.execute("""
                    SELECT 
                        SUM(CASE WHEN slot_type = 'AUTO' THEN 1 ELSE 0 END) as actual_auto,
                        SUM(CASE WHEN slot_type = 'MANUAL' THEN 1 ELSE 0 END) as actual_manual
                    FROM active_slots 
                    WHERE user_id = ? AND status = 'OPEN'
                """, (user_id,))
                
                actual_counts = cur.fetchone()
                actual_auto = actual_counts[0] or 0
                actual_manual = actual_counts[1] or 0
                
                # Fix counters if they don't match
                if actual_auto != auto_used or actual_manual != manual_used:
                    logger.warning(f"User {user_id} slot count mismatch:")
                    logger.warning(f"  AUTO: stored={auto_used}, actual={actual_auto}")  
                    logger.warning(f"  MANUAL: stored={manual_used}, actual={actual_manual}")
                    
                    cur.execute("""
                        UPDATE user_fire_modes 
                        SET auto_slots_in_use = ?, 
                            manual_slots_in_use = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (actual_auto, actual_manual, user_id))
                    
                    logger.info(f"✅ Fixed slot counts for user {user_id}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error verifying slot counts: {e}")
        
        logger.info(f"✅ Slot synchronization complete:")
        logger.info(f"  - Fixed {fixed_count} mismatched slots")
        logger.info(f"  - Closed {stale_count} stale slots")
        
        return fixed_count + stale_count

if __name__ == "__main__":
    sync = SlotSynchronizer()
    fixed = sync.full_synchronization()
    
    if fixed > 0:
        print(f"🔧 Fixed {fixed} slot issues")
    else:
        print("✅ All slots are synchronized")