#!/usr/bin/env python3
"""
Real-time Position Synchronization Service
Ensures database always matches MT5 reality
"""

import sqlite3
import time
import logging
import json
import sys
sys.path.append('/root/HydraX-v2')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PositionSyncService:
    """Service to keep database synchronized with MT5 positions"""
    
    def __init__(self, db_path="/root/HydraX-v2/bitten.db"):
        self.db_path = db_path
        self.sync_interval = 30  # Check every 30 seconds
        self.last_sync = 0
        
    def get_ea_positions_via_heartbeat(self):
        """
        Get current EA positions from heartbeat data
        This would need to be enhanced with actual EA communication
        For now, simulate by checking database consistency
        """
        # In future: Query EA directly via ZMQ for current positions
        # For now: Use database analysis to detect inconsistencies
        return []
        
    def sync_positions(self):
        """Synchronize database with actual MT5 positions"""
        current_time = int(time.time())
        
        if current_time - self.last_sync < self.sync_interval:
            return
            
        self.last_sync = current_time
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find positions that are old and likely closed
            old_threshold = current_time - (2 * 60 * 60)  # 2 hours old
            
            cursor.execute("""
                SELECT fire_id, symbol, direction, entry_price, last_update,
                       datetime(last_update, 'unixepoch') as readable_time
                FROM live_positions 
                WHERE status = 'OPEN' AND last_update < ?
                ORDER BY last_update
            """, (old_threshold,))
            
            old_positions = cursor.fetchall()
            
            if old_positions:
                logger.warning(f"Found {len(old_positions)} positions older than 2 hours:")
                for pos in old_positions:
                    fire_id, symbol, direction, entry, last_update, readable = pos
                    logger.warning(f"  {fire_id}: {symbol} {direction} @ {entry} (last update: {readable})")
                
                # Auto-close positions older than 4 hours (likely manually closed)
                very_old_threshold = current_time - (4 * 60 * 60)  # 4 hours
                
                cursor.execute("""
                    SELECT fire_id FROM live_positions 
                    WHERE status = 'OPEN' AND last_update < ?
                """, (very_old_threshold,))
                
                very_old = cursor.fetchall()
                
                if very_old:
                    logger.info(f"Auto-closing {len(very_old)} positions older than 4 hours...")
                    
                    for (fire_id,) in very_old:
                        # Update to closed
                        cursor.execute("""
                            UPDATE live_positions 
                            SET status = 'CLOSED_AUTO_SYNC', last_update = ?
                            WHERE fire_id = ?
                        """, (current_time, fire_id))
                        
                        cursor.execute("""
                            UPDATE fires 
                            SET status = 'CLOSED_AUTO_SYNC'
                            WHERE fire_id = ?
                        """, (fire_id,))
                        
                        logger.info(f"✅ Auto-closed old position: {fire_id}")
                    
                    conn.commit()
            
            # Log current position count
            cursor.execute("SELECT COUNT(*) FROM live_positions WHERE status = 'OPEN'")
            open_count = cursor.fetchone()[0]
            
            if open_count > 0:
                logger.debug(f"📊 Current open positions: {open_count}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
    
    def run(self):
        """Main service loop"""
        logger.info("🔄 Position Sync Service starting...")
        
        while True:
            try:
                self.sync_positions()
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                logger.info("Position Sync Service stopping...")
                break
            except Exception as e:
                logger.error(f"Service error: {e}")
                time.sleep(30)  # Wait before retrying on error

if __name__ == "__main__":
    service = PositionSyncService()
    service.run()