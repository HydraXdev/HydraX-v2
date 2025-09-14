#!/usr/bin/env python3
"""
Automatic Slot Cleaner Daemon
Runs every 15 minutes to clean up slots for trades that have closed
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta
import sys
import os

sys.path.append('/root/HydraX-v2/src')
from src.bitten_core.fire_mode_database import FireModeDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s - AUTO_SLOT_CLEANER - %(message)s")
logger = logging.getLogger(__name__)

class AutoSlotCleaner:
    def __init__(self):
        self.bitten_db = "/root/HydraX-v2/bitten.db"
        self.fire_db = FireModeDatabase()
        self.last_cleanup = datetime.now()
    
    def cleanup_old_filled_trades(self):
        """Clean up slots for FILLED trades older than 1 hour"""
        logger.info("🧹 Starting automatic slot cleanup...")
        
        try:
            # Get all open slots
            conn = sqlite3.connect("/root/HydraX-v2/data/fire_modes.db")
            cur = conn.cursor()
            
            cur.execute("""
                SELECT user_id, mission_id, slot_type, opened_at 
                FROM active_slots 
                WHERE status = 'OPEN'
            """)
            
            open_slots = cur.fetchall()
            conn.close()
            
            if not open_slots:
                logger.info("No open slots to check")
                return 0
            
            logger.info(f"Checking {len(open_slots)} open slots...")
            
            # Check each slot against fires table
            bitten_conn = sqlite3.connect(self.bitten_db)
            bitten_cur = bitten_conn.cursor()
            
            cleaned = 0
            for user_id, mission_id, slot_type, opened_at in open_slots:
                bitten_cur.execute("""
                    SELECT fire_id, status, created_at
                    FROM fires 
                    WHERE mission_id = ? AND user_id = ?
                """, (mission_id, user_id))
                
                fire_data = bitten_cur.fetchone()
                
                if fire_data:
                    fire_id, status, created_at = fire_data
                    trade_time = datetime.fromtimestamp(created_at)
                    hours_old = (datetime.now() - trade_time).total_seconds() / 3600
                    
                    should_close = False
                    reason = ""
                    
                    # More aggressive cleanup rules
                    if status in ['CLOSED_AUTO_DETECTED', 'CLOSED_MANUAL', 'FAILED', 'CANCELLED']:
                        should_close = True
                        reason = f"Status: {status}"
                    elif status == 'FILLED' and hours_old > 1:  # 1 hour for FILLED trades
                        should_close = True
                        reason = f"FILLED {hours_old:.1f}h old"
                    elif hours_old > 24:  # 24 hour absolute maximum
                        should_close = True
                        reason = f"Trade {hours_old:.1f}h old"
                    
                    if should_close:
                        logger.info(f"Cleaning slot: {user_id} {mission_id} ({reason})")
                        
                        if self.fire_db.release_slot(user_id, mission_id):
                            cleaned += 1
                            logger.info(f"  ✅ Released {slot_type} slot")
                        else:
                            logger.warning(f"  ❌ Failed to release {slot_type} slot")
                else:
                    # Orphaned slot - no matching fire record
                    logger.info(f"Cleaning orphaned slot: {mission_id}")
                    if self.fire_db.release_slot(user_id, mission_id):
                        cleaned += 1
                        logger.info(f"  ✅ Released orphaned {slot_type} slot")
            
            bitten_conn.close()
            
            if cleaned > 0:
                logger.info(f"✅ Cleaned {cleaned} phantom slots")
            else:
                logger.info("✅ All slots are current")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error in slot cleanup: {e}")
            return 0
    
    def run_daemon(self):
        """Run the daemon with 15-minute intervals"""
        logger.info("🚀 Auto Slot Cleaner Daemon started")
        logger.info("Will check for phantom slots every 15 minutes")
        
        while True:
            try:
                cleaned = self.cleanup_old_filled_trades()
                self.last_cleanup = datetime.now()
                
                # Log summary
                logger.info(f"Cleanup cycle complete. Next check in 15 minutes.")
                
                # Sleep for 15 minutes
                time.sleep(15 * 60)
                
            except KeyboardInterrupt:
                logger.info("Daemon stopped by user")
                break
            except Exception as e:
                logger.error(f"Daemon error: {e}")
                time.sleep(60)  # Sleep 1 minute on error

if __name__ == "__main__":
    cleaner = AutoSlotCleaner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit
        cleaned = cleaner.cleanup_old_filled_trades()
        print(f"One-time cleanup: {cleaned} slots cleaned")
    else:
        # Run as daemon
        cleaner.run_daemon()