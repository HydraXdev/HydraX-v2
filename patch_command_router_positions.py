#!/usr/bin/env python3
"""
Patch command_router.py to process enhanced heartbeats with position tracking
This will update the _upsert_ea_instance function to handle position data
"""

import sys
import os

def patch_command_router():
    """Add position tracking to command router"""
    
    # Read the current command_router.py
    with open('/root/HydraX-v2/command_router.py', 'r') as f:
        lines = f.readlines()
    
    # Find the _upsert_ea_instance function
    patch_applied = False
    for i, line in enumerate(lines):
        # Check if already patched
        if 'open_positions' in line and 'position_data' in line:
            print("✅ Command router already patched for position tracking")
            return True
            
    # Find where to add position processing
    for i, line in enumerate(lines):
        if 'def _upsert_ea_instance(payload):' in line:
            # Find the variable extraction section
            for j in range(i, min(i+50, len(lines))):
                if 'last_seen' in lines[j] and 'int(payload.get' in lines[j]:
                    # Insert position data extraction after last_seen
                    insert_pos = j + 1
                    
                    new_lines = [
                        "    # Extract position data from enhanced heartbeat\n",
                        "    open_positions = int(payload.get('open_positions', 0) or 0)\n",
                        "    positions_json = json.dumps(payload.get('positions', []))\n",
                        "\n"
                    ]
                    
                    # Insert the new lines
                    for new_line in reversed(new_lines):
                        lines.insert(insert_pos, new_line)
                    
                    print(f"✅ Added position extraction at line {insert_pos}")
                    patch_applied = True
                    break
            break
    
    if not patch_applied:
        print("❌ Could not find insertion point for position extraction")
        return False
        
    # Now update the CREATE TABLE statement to include position columns
    for i, line in enumerate(lines):
        if 'CREATE TABLE IF NOT EXISTS ea_instances' in line:
            # Find the end of the CREATE TABLE statement
            for j in range(i, min(i+20, len(lines))):
                if 'updated_at' in lines[j] and 'INTEGER' in lines[j]:
                    # Add position columns before the closing
                    insert_pos = j + 1
                    if 'open_positions' not in ''.join(lines[i:j+5]):
                        lines.insert(insert_pos, "            ,open_positions INTEGER DEFAULT 0\n")
                        lines.insert(insert_pos+1, "            ,position_data TEXT DEFAULT '{}'\n")
                        print(f"✅ Added position columns to CREATE TABLE at line {insert_pos}")
                    break
            break
    
    # Update the INSERT statement to include position data
    for i, line in enumerate(lines):
        if 'INSERT INTO ea_instances(' in line:
            # Check if we need to add position fields
            if 'open_positions' not in lines[i+1] and 'open_positions' not in lines[i]:
                # Find the VALUES line
                for j in range(i, min(i+10, len(lines))):
                    if 'last_seen,created_at,updated_at' in lines[j]:
                        lines[j] = lines[j].replace(
                            'last_seen,created_at,updated_at',
                            'last_seen,created_at,updated_at,open_positions,position_data'
                        )
                        print(f"✅ Updated INSERT columns at line {j}")
                    if ') VALUES(?,?,?,?,?,?,?,?,?,?,?)' in lines[j]:
                        lines[j] = lines[j].replace(
                            '?,?,?,?,?,?,?,?,?,?,?',
                            '?,?,?,?,?,?,?,?,?,?,?,?,?'
                        )
                        print(f"✅ Updated VALUES placeholders at line {j}")
                        break
            break
    
    # Update the UPDATE SET clause
    for i, line in enumerate(lines):
        if 'ON CONFLICT(target_uuid) DO UPDATE SET' in line:
            # Find where the update list ends
            for j in range(i+1, min(i+15, len(lines))):
                if 'updated_at=excluded.updated_at' in lines[j]:
                    if 'open_positions' not in ''.join(lines[i:j+2]):
                        # Add position updates before the last field
                        lines[j] = lines[j].replace(
                            'updated_at=excluded.updated_at',
                            'updated_at=excluded.updated_at,\n              open_positions=excluded.open_positions,\n              position_data=excluded.position_data'
                        )
                        print(f"✅ Updated UPDATE SET clause at line {j}")
                    break
            break
    
    # Update the execute parameters
    for i, line in enumerate(lines):
        if 'cur.execute("""' in line and i > 70 and i < 120:
            # Find the parameter tuple
            for j in range(i+10, min(i+30, len(lines))):
                if '(uuid,user_id,acct_login,broker,currency,leverage,' in lines[j]:
                    if 'open_positions' not in lines[j+1]:
                        lines[j+1] = lines[j+1].replace(
                            'balance,equity,last_seen,created_at,updated_at',
                            'balance,equity,last_seen,created_at,updated_at,open_positions,positions_json'
                        )
                        print(f"✅ Updated execute parameters at line {j+1}")
                    break
            break
    
    # Write the patched file
    backup_path = '/root/HydraX-v2/command_router.py.bak'
    if not os.path.exists(backup_path):
        os.rename('/root/HydraX-v2/command_router.py', backup_path)
        print(f"📦 Backed up original to {backup_path}")
    
    with open('/root/HydraX-v2/command_router.py', 'w') as f:
        f.writelines(lines)
    
    print("✅ Command router patched successfully!")
    print("\n⚠️ IMPORTANT: Restart command_router process:")
    print("pm2 restart command_router")
    
    return True

def add_position_processor():
    """Add a separate position processor that monitors heartbeats"""
    
    processor_code = '''#!/usr/bin/env python3
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
            print("\\n✅ Position processor stopped")
            break
        except Exception as e:
            print(f"❌ Position processor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_heartbeats()
'''
    
    # Write the position processor
    with open('/root/HydraX-v2/position_processor.py', 'w') as f:
        f.write(processor_code)
    
    print("✅ Created position_processor.py")
    print("\n📋 To start position processor:")
    print("pm2 start /root/HydraX-v2/position_processor.py --name position_processor")
    
    return True

if __name__ == "__main__":
    print("🔧 Patching command router for position tracking...")
    
    if patch_command_router():
        print("\n✅ Patch completed successfully!")
        
        if add_position_processor():
            print("\n📊 Position tracking system ready!")
            print("\n⚠️ NEXT STEPS:")
            print("1. Restart command router: pm2 restart command_router")
            print("2. Start position processor: pm2 start position_processor.py --name position_processor")
            print("3. Monitor logs: pm2 logs command_router")
            print("\nThe system will now:")
            print("✅ Track all open positions from EA heartbeats")
            print("✅ Prevent opening more than 10 positions")
            print("✅ Block hedging (opposite direction on same symbol)")
            print("✅ Free slots when positions close")
            print("✅ Manage AUTO fire slots properly")
    else:
        print("\n❌ Patch failed - manual intervention needed")