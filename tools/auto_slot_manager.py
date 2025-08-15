#!/usr/bin/env python3
"""
Auto Slot Manager - Monitors position closes and releases AUTO mode slots
"""

import redis
import json
import sqlite3
import time
import logging
from pathlib import Path
import sys

# Add src path for imports
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

from src.bitten_core.fire_mode_database import FireModeDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoSlotManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
        self.fire_mode_db = FireModeDatabase()
        self.bitten_db_path = "/root/HydraX-v2/bitten.db"
        self.monitored_positions = {}  # ticket -> {user_id, mission_id}
        
    def monitor_positions(self):
        """Main monitoring loop"""
        logger.info("🎰 Auto Slot Manager started - monitoring position closes")
        
        while True:
            try:
                # Get all active slots
                conn = sqlite3.connect(self.bitten_db_path)
                cur = conn.cursor()
                
                # Get active fires that might have slots
                cur.execute("""
                    SELECT f.fire_id, f.mission_id, f.user_id, f.ticket, f.status
                    FROM fires f
                    WHERE f.status IN ('SENT', 'CONFIRMED')
                      AND f.created_at > ?
                    ORDER BY f.created_at DESC
                """, (int(time.time()) - 86400,))  # Last 24 hours
                
                active_fires = cur.fetchall()
                
                for fire in active_fires:
                    fire_id, mission_id, user_id, ticket, status = fire
                    
                    if ticket and ticket not in self.monitored_positions:
                        # New position to monitor
                        self.monitored_positions[ticket] = {
                            'user_id': user_id,
                            'mission_id': mission_id,
                            'fire_id': fire_id
                        }
                        logger.info(f"📍 Monitoring position {ticket} for user {user_id}")
                    
                    # Check if position is closed
                    if ticket:
                        position_key = f"position:{ticket}"
                        position_data = self.redis_client.hgetall(position_key)
                        
                        if not position_data or position_data.get('status') == 'closed':
                            # Position closed - release slot
                            if ticket in self.monitored_positions:
                                pos_info = self.monitored_positions[ticket]
                                if self.fire_mode_db.release_slot(pos_info['user_id'], pos_info['mission_id']):
                                    logger.info(f"✅ Released slot for user {pos_info['user_id']}, mission {pos_info['mission_id']}")
                                    
                                    # Update fire status
                                    cur.execute("""
                                        UPDATE fires 
                                        SET status = 'COMPLETED', updated_at = ?
                                        WHERE fire_id = ?
                                    """, (int(time.time()), pos_info['fire_id']))
                                    conn.commit()
                                    
                                    # Remove from monitoring
                                    del self.monitored_positions[ticket]
                                else:
                                    logger.warning(f"⚠️ Failed to release slot for {pos_info['user_id']}")
                
                conn.close()
                
                # Log status
                active_slots = len(self.monitored_positions)
                if active_slots > 0:
                    logger.debug(f"🎰 Monitoring {active_slots} active positions")
                
                # Check every 10 seconds
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error

if __name__ == "__main__":
    manager = AutoSlotManager()
    manager.monitor_positions()