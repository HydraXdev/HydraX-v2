#!/usr/bin/env python3
"""
Slot Monitor - Prevents slot tracking drift
Runs periodically to sync slot tracking with reality
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlotMonitor:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/fire_modes.db"
        self.check_interval = 300  # 5 minutes
        
    def get_slot_counts(self, user_id):
        """Get current slot counts from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT auto_slots_in_use, manual_slots_in_use 
            FROM user_fire_modes 
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], result[1]  # auto, manual
        return 0, 0
    
    def count_open_slots(self, user_id):
        """Count actually open slots in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT slot_type, COUNT(*) 
            FROM active_slots 
            WHERE user_id = ? AND (status IS NULL OR status = 'OPEN')
            GROUP BY slot_type
        """, (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        auto_count = 0
        manual_count = 0
        
        for slot_type, count in results:
            if slot_type == 'AUTO':
                auto_count = count
            elif slot_type == 'MANUAL':
                manual_count = count
                
        return auto_count, manual_count
    
    def sync_slot_counts(self, user_id):
        """Sync slot counts with actual open slots"""
        # Get what the counters say
        counter_auto, counter_manual = self.get_slot_counts(user_id)
        
        # Get what's actually open
        actual_auto, actual_manual = self.count_open_slots(user_id)
        
        # Check for drift
        auto_drift = abs(counter_auto - actual_auto)
        manual_drift = abs(counter_manual - actual_manual)
        
        if auto_drift > 0 or manual_drift > 0:
            logger.warning(f"Slot drift detected for user {user_id}:")
            logger.warning(f"  AUTO: Counter={counter_auto}, Actual={actual_auto} (drift: {auto_drift})")
            logger.warning(f"  MANUAL: Counter={counter_manual}, Actual={actual_manual} (drift: {manual_drift})")
            
            # Sync the counters
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_fire_modes 
                SET auto_slots_in_use = ?, manual_slots_in_use = ?
                WHERE user_id = ?
            """, (actual_auto, actual_manual, user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Synced slot counters for user {user_id}")
            return True
            
        return False
    
    def cleanup_stale_slots(self, user_id, max_age_hours=24):
        """Mark very old OPEN slots as CLOSED (they're likely stale)"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE active_slots 
            SET status = 'CLOSED', closed_at = datetime('now')
            WHERE user_id = ? 
            AND (status IS NULL OR status = 'OPEN')
            AND opened_at < ?
        """, (user_id, cutoff_time.isoformat()))
        
        stale_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if stale_count > 0:
            logger.info(f"🧹 Cleaned up {stale_count} stale slots older than {max_age_hours}h")
            return stale_count
            
        return 0
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("🔍 Slot Monitor starting...")
        
        while True:
            try:
                # Monitor the main user
                user_id = '7176191872'
                
                # Clean up stale slots first
                stale_cleaned = self.cleanup_stale_slots(user_id)
                
                # Sync counters
                synced = self.sync_slot_counts(user_id)
                
                if synced or stale_cleaned:
                    auto, manual = self.get_slot_counts(user_id)
                    logger.info(f"📊 Current slots: AUTO={auto}, MANUAL={manual}")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Slot Monitor stopped")
                break
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                time.sleep(60)  # Wait a minute on error

if __name__ == "__main__":
    monitor = SlotMonitor()
    monitor.monitor_loop()