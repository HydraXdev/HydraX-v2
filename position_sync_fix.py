#!/usr/bin/env python3
"""
Position Synchronization Fix
Aligns live_positions table with fires table status
"""

import sqlite3
import time
from datetime import datetime

def sync_positions():
    """Sync live_positions table with fires table status"""
    
    db_path = "/root/HydraX-v2/bitten.db"
    current_time = int(time.time())
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Find positions marked as CLOSED in fires but still OPEN in live_positions
        cursor.execute("""
            SELECT lp.fire_id, f.status, lp.status as lp_status
            FROM live_positions lp
            JOIN fires f ON lp.fire_id = f.fire_id
            WHERE lp.status = 'OPEN' 
            AND f.status IN ('CLOSED', 'CLOSED_AUTO_DETECTED', 'FAILED')
        """)
        
        mismatched_positions = cursor.fetchall()
        
        if not mismatched_positions:
            print("✅ All positions are synchronized")
            return
        
        print(f"🔄 Found {len(mismatched_positions)} positions to sync:")
        
        for fire_id, fires_status, lp_status in mismatched_positions:
            print(f"  - {fire_id}: fires={fires_status}, live_positions={lp_status}")
            
            # Update live_positions to match fires status
            new_status = 'CLOSED' if fires_status in ['CLOSED', 'CLOSED_AUTO_DETECTED'] else 'FAILED'
            
            cursor.execute("""
                UPDATE live_positions 
                SET status = ?, last_update = ?
                WHERE fire_id = ?
            """, (new_status, current_time, fire_id))
            
            print(f"    ✅ Updated to {new_status}")
        
        conn.commit()
        print(f"\n✅ Synchronized {len(mismatched_positions)} positions")
        
        # Show current open positions after sync
        cursor.execute("""
            SELECT COUNT(*) FROM live_positions WHERE status = 'OPEN'
        """)
        open_count = cursor.fetchone()[0]
        print(f"📊 Current open positions: {open_count}")

if __name__ == "__main__":
    print("🔄 Starting position synchronization...")
    sync_positions()
    print("✅ Position synchronization complete")