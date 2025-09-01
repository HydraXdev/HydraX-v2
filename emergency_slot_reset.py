#!/usr/bin/env python3
"""
Emergency slot reset for user 7176191872
Resets slot counts to match actual open positions
"""

import sqlite3
import json
from datetime import datetime

def reset_slots():
    """Reset slot tracking for commander"""
    user_id = '7176191872'
    
    # Connect to databases
    bitten_db = sqlite3.connect('/root/HydraX-v2/bitten.db')
    fire_db = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
    
    # Count actual open positions (trades without close events)
    cursor = bitten_db.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM fires 
        WHERE user_id = ? 
        AND status = 'FILLED' 
        AND fire_id NOT IN (
            SELECT DISTINCT fire_id 
            FROM position_events 
            WHERE event_type = 'CLOSE'
        )
        AND created_at > strftime('%s', 'now', '-24 hours')
    """, (user_id,))
    
    open_trades = cursor.fetchone()[0]
    print(f"Found {open_trades} open trades in last 24 hours")
    
    # Reset slot counts in fire_mode database
    fire_cursor = fire_db.cursor()
    
    # First ensure user exists
    fire_cursor.execute("""
        INSERT OR IGNORE INTO user_fire_modes 
        (user_id, current_mode, manual_slots_in_use, auto_slots_in_use, 
         max_auto_slots, slots_in_use, max_slots, created_at, updated_at)
        VALUES (?, 'AUTO', 0, 0, 5, 0, 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (user_id,))
    
    # Update slot counts - set auto slots to actual open trades (max 5)
    actual_slots = min(open_trades, 5)
    fire_cursor.execute("""
        UPDATE user_fire_modes 
        SET auto_slots_in_use = ?,
            manual_slots_in_use = 0,
            slots_in_use = ?,
            max_auto_slots = 5,
            max_slots = 5,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (actual_slots, actual_slots, user_id))
    
    fire_db.commit()
    
    # Clear old active_slots table and rebuild
    fire_cursor.execute("DELETE FROM active_slots WHERE user_id = ?", (user_id,))
    
    # Get the most recent filled trades to populate active slots
    cursor.execute("""
        SELECT fire_id, mission_id 
        FROM fires 
        WHERE user_id = ? 
        AND status = 'FILLED'
        AND fire_id NOT IN (
            SELECT DISTINCT fire_id 
            FROM position_events 
            WHERE event_type = 'CLOSE'
        )
        AND created_at > strftime('%s', 'now', '-24 hours')
        ORDER BY created_at DESC
        LIMIT 5
    """, (user_id,))
    
    active_fires = cursor.fetchall()
    
    # Populate active_slots
    for idx, (fire_id, mission_id) in enumerate(active_fires, 1):
        # Extract symbol from fire_id (e.g., ELITE_SNIPER_GBPUSD_xxx)
        parts = fire_id.split('_')
        if len(parts) >= 4:
            symbol = parts[2]
        else:
            symbol = 'UNKNOWN'
            
        fire_cursor.execute("""
            INSERT INTO active_slots 
            (user_id, mission_id, symbol, opened_at, slot_type, status)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'AUTO', 'OPEN')
        """, (user_id, mission_id or fire_id, symbol))
    
    fire_db.commit()
    
    print(f"Reset complete:")
    print(f"- Set auto_slots_in_use to {actual_slots}")
    print(f"- Populated {len(active_fires)} active slots")
    print(f"- Max slots set to 5")
    
    # Verify the update
    fire_cursor.execute("""
        SELECT current_mode, manual_slots_in_use, auto_slots_in_use, max_auto_slots
        FROM user_fire_modes WHERE user_id = ?
    """, (user_id,))
    
    mode_info = fire_cursor.fetchone()
    if mode_info:
        print(f"\nCurrent settings:")
        print(f"  Mode: {mode_info[0]}")
        print(f"  Manual slots used: {mode_info[1]}")
        print(f"  Auto slots used: {mode_info[2]}")
        print(f"  Max auto slots: {mode_info[3]}")
    
    bitten_db.close()
    fire_db.close()
    print("\n✅ Slot management reset complete")

if __name__ == '__main__':
    reset_slots()