#!/usr/bin/env python3
"""
Position Close Monitor
Monitors open positions and detects when they close to release slots
Runs continuously, checking every 30 seconds
"""

import time
import sqlite3
import json
from datetime import datetime
import sys
import os
sys.path.append('/root/HydraX-v2')

def check_for_closed_positions():
    """Check if any positions have closed and release their slots"""
    
    bitten_db = '/root/HydraX-v2/bitten.db'
    fire_db = '/root/HydraX-v2/data/fire_modes.db'
    
    try:
        # Connect to databases
        conn = sqlite3.connect(bitten_db)
        cursor = conn.cursor()
        
        # Get all FILLED trades that don't have a CLOSE event yet
        cursor.execute("""
            SELECT f.fire_id, f.user_id, f.ticket, m.signal_id
            FROM fires f
            LEFT JOIN missions m ON f.mission_id = m.mission_id
            WHERE f.status = 'FILLED'
            AND f.ticket IS NOT NULL
            AND f.ticket != 0
            AND f.fire_id NOT IN (
                SELECT DISTINCT fire_id 
                FROM position_events 
                WHERE event_type = 'CLOSE'
            )
            AND f.created_at > strftime('%s', 'now', '-48 hours')
        """)
        
        open_positions = cursor.fetchall()
        print(f"[{datetime.now()}] Monitoring {len(open_positions)} open positions")
        
        # Check each position to see if it's still open
        # For now, we'll check if there are any new signals that would indicate old ones closed
        # In production, this would query MT5 or check market data
        
        # Get recent signal outcomes to detect closes
        cursor.execute("""
            SELECT signal_id, outcome, resolution_time
            FROM signal_outcomes
            WHERE resolution_time > strftime('%s', 'now', '-2 hours')
            AND outcome IN ('WIN', 'LOSS', 'TIMEOUT')
        """)
        
        closed_signals = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Check positions against closed signals
        positions_to_close = []
        for fire_id, user_id, ticket, signal_id in open_positions:
            if signal_id in closed_signals:
                positions_to_close.append((fire_id, user_id, signal_id, closed_signals[signal_id]))
        
        if positions_to_close:
            print(f"Found {len(positions_to_close)} positions to close")
            
            # Release slots for closed positions
            fire_conn = sqlite3.connect(fire_db)
            fire_cursor = fire_conn.cursor()
            
            for fire_id, user_id, signal_id, outcome in positions_to_close:
                print(f"  Closing {fire_id}: {outcome}")
                
                # Add close event
                cursor.execute("""
                    INSERT INTO position_events (fire_id, event_type, event_data, created_at)
                    VALUES (?, 'CLOSE', ?, strftime('%s', 'now'))
                """, (fire_id, json.dumps({'outcome': outcome, 'auto_detected': True})))
                
                # Release slot
                fire_cursor.execute("""
                    UPDATE user_fire_modes 
                    SET auto_slots_in_use = MAX(0, auto_slots_in_use - 1),
                        slots_in_use = MAX(0, slots_in_use - 1),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                
                # Remove from active_slots
                fire_cursor.execute("""
                    UPDATE active_slots 
                    SET status = 'CLOSED',
                        closed_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? 
                    AND mission_id = ?
                    AND status = 'OPEN'
                """, (user_id, fire_id))
            
            conn.commit()
            fire_conn.commit()
            fire_conn.close()
            print(f"Released {len(positions_to_close)} slots")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking positions: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main monitoring loop"""
    print("🔍 Position Close Monitor started")
    print("Checking every 30 seconds for closed positions...")
    
    while True:
        try:
            check_for_closed_positions()
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            print("\n👋 Position monitor stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(30)  # Continue after error

if __name__ == '__main__':
    main()