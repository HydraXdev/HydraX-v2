#!/usr/bin/env python3
"""
Position processor - Monitors EA heartbeats and updates position tracking
Runs alongside command_router to process enhanced heartbeat data
"""

import json
import sqlite3
import time
import sys
sys.path.append('/root/HydraX-v2')

from position_slot_manager import PositionSlotManager

def monitor_heartbeats():
    """Monitor command router logs for enhanced heartbeats"""
    
    manager = PositionSlotManager()
    print("🛡️ Position processor started - monitoring heartbeats...")
    
    # In production, this would subscribe to ZMQ or tail logs
    # For now, we'll process from database updates
    
    last_check = 0
    while True:
        try:
            current_time = time.time()
            if current_time - last_check < 5:  # Check every 5 seconds
                time.sleep(1)
                continue
                
            last_check = current_time
            
            # Check for recent EA updates with position data
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT target_uuid, position_data, open_positions
                FROM ea_instances
                WHERE last_seen > ? AND position_data != '{}'
            """, (int(current_time - 60),))  # Last minute
            
            for row in cursor.fetchall():
                uuid, pos_json, count = row
                if pos_json and pos_json != '{}':
                    try:
                        positions = json.loads(pos_json)
                        heartbeat = {
                            "target_uuid": uuid,
                            "open_positions": count,
                            "positions": positions
                        }
                        manager.process_heartbeat(heartbeat)
                    except json.JSONDecodeError:
                        pass
                        
            conn.close()
            
        except KeyboardInterrupt:
            print("\n✅ Position processor stopped")
            break
        except Exception as e:
            print(f"❌ Position processor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_heartbeats()
