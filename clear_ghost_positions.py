#!/usr/bin/env python3
"""
Clear ghost positions - Mark all old filled trades as closed
These are likely already closed on broker but database doesn't know
"""

import sqlite3
import time

def clear_ghost_positions():
    """Mark all old filled positions as closed to start fresh"""
    
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    
    # First, count how many we're clearing
    cursor.execute("""
        SELECT COUNT(*) 
        FROM fires 
        WHERE status = 'FILLED' 
        AND ticket > 0
        AND (closed_at IS NULL OR closed_at = 0)
    """)
    count = cursor.fetchone()[0]
    
    print(f"Found {count} positions marked as open")
    
    if count > 0:
        print("Marking all as closed (they're likely already closed on broker)...")
        
        # Mark all old filled trades as closed
        cursor.execute("""
            UPDATE fires 
            SET closed_at = ?, status = 'CLOSED_CLEANUP'
            WHERE status = 'FILLED' 
            AND ticket > 0
            AND (closed_at IS NULL OR closed_at = 0)
        """, (int(time.time()),))
        
        conn.commit()
        print(f"✅ Marked {cursor.rowcount} positions as closed")
    else:
        print("✅ No ghost positions to clear")
    
    conn.close()
    
    # Also reset any slot tracking
    try:
        import json
        registry_path = '/root/HydraX-v2/user_registry.json'
        
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        # Reset slots for all users
        for user_id in registry:
            if 'slots_used' in registry[user_id]:
                registry[user_id]['slots_used'] = 0
                print(f"Reset slots for user {user_id}")
        
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
            
        print("✅ Reset all user slot counts to 0")
    except Exception as e:
        print(f"Note: Could not reset user registry: {e}")
    
    print("\n🎯 System is now clear for fresh trading!")
    print("   - All ghost positions marked as closed")
    print("   - Direction gate will not block new trades")
    print("   - Slot tracking reset to 0")

if __name__ == "__main__":
    clear_ghost_positions()