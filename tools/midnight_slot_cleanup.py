#!/usr/bin/env python3
"""
Midnight Slot Cleanup - Daily reset of fire mode slots
Runs at 00:00 market time to clean up any stuck slots
"""

import sqlite3
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append('/root/HydraX-v2')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/midnight_slot_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def cleanup_stuck_slots():
    """Clean up all stuck open slots and reset counters"""
    db_path = "/root/HydraX-v2/data/fire_modes.db"
    
    if not Path(db_path).exists():
        logger.error(f"Fire modes database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get count of stuck slots before cleanup
        cursor.execute("SELECT COUNT(*) FROM active_slots WHERE status = 'OPEN'")
        stuck_slots = cursor.fetchone()[0]
        
        if stuck_slots > 0:
            logger.info(f"🧹 Found {stuck_slots} stuck open slots, cleaning up...")
            
            # Close all stuck slots
            cursor.execute("UPDATE active_slots SET status = 'CLOSED' WHERE status = 'OPEN'")
            
            # Reset all user slot counters
            cursor.execute("""
                UPDATE user_fire_modes SET 
                manual_slots_in_use = 0,
                auto_slots_in_use = 0
                WHERE manual_slots_in_use > 0 OR auto_slots_in_use > 0
            """)
            
            # Get affected users
            cursor.execute("SELECT DISTINCT user_id FROM user_fire_modes WHERE manual_slots_in_use = 0 AND auto_slots_in_use = 0")
            users_cleaned = cursor.fetchall()
            
            conn.commit()
            logger.info(f"✅ Cleaned up {stuck_slots} slots for {len(users_cleaned)} users")
            
            # Log per-user cleanup
            for (user_id,) in users_cleaned:
                logger.info(f"   User {user_id}: All slots reset to available")
                
        else:
            logger.info("🟢 No stuck slots found - system is clean")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Slot cleanup failed: {e}")
        return False

def cleanup_old_closed_slots():
    """Remove old closed slots (older than 7 days) to keep database clean"""
    db_path = "/root/HydraX-v2/data/fire_modes.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Remove closed slots older than 7 days (check column exists first)
        cursor.execute("PRAGMA table_info(active_slots)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'created_at' in columns:
            cursor.execute("""
                DELETE FROM active_slots 
                WHERE status = 'CLOSED' 
                AND created_at < datetime('now', '-7 days')
            """)
        else:
            # Fallback: just count closed slots for info
            cursor.execute("SELECT COUNT(*) FROM active_slots WHERE status = 'CLOSED'")
            closed_count = cursor.fetchone()[0]
            if closed_count > 100:  # Only clean if many closed slots
                cursor.execute("DELETE FROM active_slots WHERE status = 'CLOSED'")
                logger.info(f"🗑️ Removed {closed_count} old closed slots (no timestamp column)")
            else:
                logger.info(f"🟢 {closed_count} closed slots kept (under limit)")
        
        removed = cursor.rowcount
        if removed > 0:
            logger.info(f"🗑️ Removed {removed} old closed slots (>7 days old)")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"⚠️ Old slot cleanup failed: {e}")

def main():
    """Main cleanup routine"""
    logger.info("🌙 MIDNIGHT SLOT CLEANUP STARTED")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Clean up stuck slots
    if cleanup_stuck_slots():
        logger.info("✅ Stuck slot cleanup completed")
    else:
        logger.error("❌ Stuck slot cleanup failed")
    
    # Clean up old records
    cleanup_old_closed_slots()
    
    logger.info("🌙 MIDNIGHT SLOT CLEANUP COMPLETED")
    logger.info("-" * 50)

if __name__ == "__main__":
    main()