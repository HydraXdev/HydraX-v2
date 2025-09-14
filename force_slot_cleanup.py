#!/usr/bin/env python3
"""
Force cleanup of phantom slots that should be closed
Checks actual trade status vs slot status and fixes mismatches
"""

import sqlite3
from datetime import datetime, timedelta
import sys
sys.path.append('/root/HydraX-v2/src')
from src.bitten_core.fire_mode_database import FireModeDatabase

def force_cleanup_phantom_slots():
    bitten_db = "/root/HydraX-v2/bitten.db"
    fire_db = FireModeDatabase()
    
    print("🧹 FORCE CLEANUP: Checking for phantom slots...")
    
    # Get all slots marked as OPEN
    conn = sqlite3.connect("/root/HydraX-v2/data/fire_modes.db")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT user_id, mission_id, slot_type, opened_at 
        FROM active_slots 
        WHERE status = 'OPEN'
        ORDER BY opened_at DESC
    """)
    
    open_slots = cur.fetchall()
    conn.close()
    
    print(f"Found {len(open_slots)} slots marked as OPEN")
    
    # Check each slot against fires table
    bitten_conn = sqlite3.connect(bitten_db)
    bitten_cur = bitten_conn.cursor()
    
    cleaned = 0
    for user_id, mission_id, slot_type, opened_at in open_slots:
        # Check if this trade is actually closed
        bitten_cur.execute("""
            SELECT fire_id, status, created_at
            FROM fires 
            WHERE mission_id = ? AND user_id = ?
        """, (mission_id, user_id))
        
        fire_data = bitten_cur.fetchone()
        
        if fire_data:
            fire_id, status, created_at = fire_data
            
            # Check if trade is old (>2 hours) and marked as FILLED
            trade_time = datetime.fromtimestamp(created_at)
            hours_old = (datetime.now() - trade_time).total_seconds() / 3600
            
            should_close = False
            reason = ""
            
            if status in ['CLOSED_AUTO_DETECTED', 'CLOSED_MANUAL', 'FAILED', 'CANCELLED']:
                should_close = True
                reason = f"Trade status is {status}"
            elif status == 'FILLED' and hours_old > 1:
                should_close = True
                reason = f"FILLED trade is {hours_old:.1f} hours old - likely closed"
            
            if should_close:
                print(f"🔧 CLEANING: {user_id} {mission_id} ({slot_type}) - {reason}")
                
                if fire_db.release_slot(user_id, mission_id):
                    cleaned += 1
                    print(f"  ✅ Released {slot_type} slot")
                else:
                    print(f"  ❌ Failed to release slot")
            else:
                print(f"  ℹ️ KEEPING: {mission_id} (status={status}, age={hours_old:.1f}h)")
        else:
            print(f"🔧 ORPHANED SLOT: {mission_id} not found in fires table")
            if fire_db.release_slot(user_id, mission_id):
                cleaned += 1
                print(f"  ✅ Released orphaned {slot_type} slot")
    
    bitten_conn.close()
    
    print(f"\n✅ Cleanup complete: Released {cleaned} phantom slots")
    
    # Show updated counts
    conn = sqlite3.connect("/root/HydraX-v2/data/fire_modes.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, auto_slots_in_use, max_auto_slots, manual_slots_in_use
        FROM user_fire_modes 
        WHERE user_id = '7176191872'
    """)
    
    result = cur.fetchone()
    if result:
        user_id, auto_used, auto_max, manual_used = result
        print(f"\n📊 Updated slot counts for {user_id}:")
        print(f"  AUTO: {auto_used}/{auto_max}")
        print(f"  MANUAL: {manual_used}")
    
    conn.close()
    return cleaned

if __name__ == "__main__":
    cleaned = force_cleanup_phantom_slots()
    print(f"\n🎯 Result: {cleaned} phantom slots cleaned up")