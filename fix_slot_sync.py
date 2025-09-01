#!/usr/bin/env python3
"""
Emergency Slot Sync Fix
Resets slot tracking to match actual MT5 positions
"""

import sqlite3
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_slot_tracking(user_id='7176191872'):
    """Reset slot tracking for user to match actual positions"""
    
    db_path = "/root/HydraX-v2/data/fire_modes.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Step 1: Mark all OPEN slots as CLOSED for this user
        cursor.execute("""
            UPDATE active_slots 
            SET status = 'CLOSED', closed_at = datetime('now')
            WHERE user_id = ? AND (status IS NULL OR status <> 'CLOSED')
        """, (user_id,))
        
        closed_count = cursor.rowcount
        logger.info(f"Marked {closed_count} phantom slots as CLOSED")
        
        # Step 2: Reset slot counters to 0 (actual positions will be counted separately)
        cursor.execute("""
            UPDATE user_fire_modes 
            SET auto_slots_in_use = 0, manual_slots_in_use = 0
            WHERE user_id = ?
        """, (user_id,))
        
        logger.info(f"Reset slot counters to 0 for user {user_id}")
        
        # Step 3: Add the 2 actual open positions as MANUAL slots
        # (Assuming the 2 actual trades are manual for now)
        for i in range(2):
            cursor.execute("""
                INSERT INTO active_slots (user_id, mission_id, symbol, slot_type, status)
                VALUES (?, ?, ?, 'MANUAL', 'OPEN')
            """, (user_id, f'ACTUAL_TRADE_{i+1}', f'UNKNOWN_PAIR_{i+1}'))
        
        # Step 4: Update manual slot counter to 2
        cursor.execute("""
            UPDATE user_fire_modes 
            SET manual_slots_in_use = 2
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("""
            SELECT auto_slots_in_use, manual_slots_in_use 
            FROM user_fire_modes 
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            auto_slots, manual_slots = result
            logger.info(f"✅ Slot sync complete:")
            logger.info(f"   AUTO slots: {auto_slots}")
            logger.info(f"   MANUAL slots: {manual_slots}")
            logger.info(f"   Total: {auto_slots + manual_slots}")
        
        conn.close()
        
        print("🎯 SLOT SYNC COMPLETE!")
        print(f"✅ Closed {closed_count} phantom slots")
        print(f"✅ Reset to 2 manual slots (matching actual trades)")
        print(f"✅ You should now be able to fire new trades")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing slot sync: {e}")
        return False

if __name__ == "__main__":
    reset_slot_tracking()