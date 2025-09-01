#!/usr/bin/env python3
"""
Emergency fix for EA heartbeat issue
Updates EA timestamp based on handshake data when heartbeats stop
"""

import json
import sqlite3
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_ea_from_handshake():
    """Update EA timestamp from handshake data"""
    try:
        # Read latest handshake data
        with open('/root/HydraX-v2/captured_handshakes.json', 'r') as f:
            handshakes = json.load(f)
        
        # Check if we have COMMANDER_DEV_001 handshake
        if 'COMMANDER_DEV_001' in handshakes:
            handshake_data = handshakes['COMMANDER_DEV_001']
            captured_at = handshake_data.get('captured_at')
            
            if captured_at:
                # Parse timestamp
                captured_time = datetime.fromisoformat(captured_at.replace('Z', '+00:00'))
                captured_timestamp = int(captured_time.timestamp())
                
                # Check if handshake is recent (within 5 minutes)
                current_time = int(time.time())
                age_seconds = current_time - captured_timestamp
                
                logger.info(f"Handshake age: {age_seconds} seconds")
                
                if age_seconds < 300:  # 5 minutes
                    # Update EA instance timestamp
                    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
                    cursor = conn.cursor()
                    
                    # Update both last_seen and updated_at
                    cursor.execute("""
                        UPDATE ea_instances 
                        SET last_seen = ?, 
                            updated_at = ?,
                            last_balance = ?,
                            last_equity = ?
                        WHERE target_uuid = 'COMMANDER_DEV_001'
                    """, (
                        captured_timestamp,
                        current_time, 
                        handshake_data.get('balance', 0),
                        handshake_data.get('equity', 0)
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    logger.info(f"✅ Updated EA timestamp to {captured_at} (balance: ${handshake_data.get('balance', 0)})")
                    return True
                else:
                    logger.warning(f"⚠️ Handshake too old: {age_seconds} seconds")
            else:
                logger.warning("⚠️ No captured_at timestamp in handshake")
        else:
            logger.warning("⚠️ No COMMANDER_DEV_001 handshake found")
            
    except FileNotFoundError:
        logger.error("❌ Handshake file not found")
    except Exception as e:
        logger.error(f"❌ Error updating EA from handshake: {e}")
    
    return False

def main():
    """Run the fix"""
    logger.info("🔧 Emergency EA heartbeat fix starting...")
    
    # Try to update from handshake
    if update_ea_from_handshake():
        logger.info("✅ EA timestamp updated from handshake data")
        
        # Check EA freshness
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT target_uuid, (strftime('%s','now') - last_seen) AS age_seconds 
            FROM ea_instances 
            WHERE target_uuid = 'COMMANDER_DEV_001'
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            age = result[1]
            logger.info(f"EA age after update: {age} seconds ({'FRESH' if age < 120 else 'STALE'})")
        
    else:
        logger.error("❌ Failed to update EA timestamp")

if __name__ == "__main__":
    main()