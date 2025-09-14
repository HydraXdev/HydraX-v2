#!/usr/bin/env python3
"""
Robust Slot Manager - Multi-layered approach to detect position closes
and automatically release slots without relying on fragile Redis tracking
"""

import sqlite3
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src path for imports
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

from src.bitten_core.fire_mode_database import FireModeDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustSlotManager:
    def __init__(self):
        self.fire_mode_db = FireModeDatabase()
        self.bitten_db_path = "/root/HydraX-v2/bitten.db"
        self.last_balance_check = {}  # user_id -> last_balance
        self.last_ticket_count = {}   # user_id -> ticket_count
        
    def detect_closes_via_ea_balance_changes(self):
        """
        Method 1: Detect position closes by monitoring EA balance changes
        When positions close, account balance changes significantly
        """
        logger.debug("🔍 Checking for balance changes...")
        
        conn = sqlite3.connect(self.bitten_db_path)
        cur = conn.cursor()
        
        # Get current EA balances
        cur.execute("""
            SELECT user_id, target_uuid, last_balance, last_equity 
            FROM ea_instances 
            WHERE (strftime('%s','now') - last_seen) <= 300  -- Active EAs only
        """)
        
        current_eas = cur.fetchall()
        balance_changes = []
        
        for user_id, target_uuid, current_balance, current_equity in current_eas:
            if user_id in self.last_balance_check:
                old_balance = self.last_balance_check[user_id]
                balance_diff = abs(current_balance - old_balance)
                
                # Significant balance change suggests position close
                if balance_diff > 10.0:  # $10+ change
                    balance_changes.append({
                        'user_id': user_id,
                        'target_uuid': target_uuid,
                        'old_balance': old_balance,
                        'new_balance': current_balance,
                        'change': balance_diff
                    })
                    logger.info(f"💰 Balance change detected: {user_id} ${old_balance:.2f} → ${current_balance:.2f}")
            
            self.last_balance_check[user_id] = current_balance
        
        conn.close()
        return balance_changes
    
    def detect_closes_via_ticket_comparison(self):
        """
        Method 2: Compare current open positions with our tracked positions
        If we're tracking a ticket that no longer exists, it was closed
        """
        logger.debug("🎫 Checking for missing tickets...")
        
        # Get our tracked positions
        fire_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
        fire_cur = fire_conn.cursor()
        
        fire_cur.execute("""
            SELECT user_id, mission_id, slot_id
            FROM active_slots 
            WHERE status = 'OPEN'
        """)
        
        open_slots = fire_cur.fetchall()
        
        # Get corresponding fire tickets
        bitten_conn = sqlite3.connect(self.bitten_db_path)
        bitten_cur = bitten_conn.cursor()
        
        closed_positions = []
        
        for user_id, mission_id, slot_id in open_slots:
            # Get ticket for this mission
            bitten_cur.execute("""
                SELECT f.ticket, f.fire_id, f.status
                FROM fires f
                WHERE f.mission_id = ? OR f.fire_id = ?
            """, (mission_id, mission_id))
            
            fire_result = bitten_cur.fetchone()
            
            if fire_result:
                ticket, fire_id, status = fire_result
                
                # If fire status shows it should be closed
                if status in ['FILLED', 'FAILED', 'CLOSED', 'CLOSED_MANUAL', 'COMPLETED']:
                    closed_positions.append({
                        'user_id': user_id,
                        'mission_id': mission_id,
                        'slot_id': slot_id,
                        'fire_id': fire_id,
                        'reason': f'Fire status: {status}'
                    })
                    
                # Check if ticket exists in current EA positions (future enhancement)
                # This would require querying the EA directly
            else:
                # ORPHANED SLOT: No corresponding fire record exists
                closed_positions.append({
                    'user_id': user_id,
                    'mission_id': mission_id,
                    'slot_id': slot_id,
                    'fire_id': mission_id,  # Use mission_id as fire_id for logging
                    'reason': f'Orphaned slot - no fire record found for mission {mission_id}'
                })
        
        fire_conn.close()
        bitten_conn.close()
        
        return closed_positions
    
    def detect_closes_via_time_analysis(self):
        """
        Method 3: Detect positions that are suspiciously old
        Most positions close within 2-4 hours, very old ones likely closed manually
        """
        logger.debug("⏰ Checking for time-expired positions...")
        
        current_time = time.time()
        old_positions = []
        
        fire_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
        fire_cur = fire_conn.cursor()
        
        # Get slots older than 4 hours
        fire_cur.execute("""
            SELECT user_id, mission_id, slot_id, opened_at
            FROM active_slots 
            WHERE status = 'OPEN'
            AND opened_at < ?
        """, (datetime.now() - timedelta(hours=4),))
        
        old_slots = fire_cur.fetchall()
        
        bitten_conn = sqlite3.connect(self.bitten_db_path)
        bitten_cur = bitten_conn.cursor()
        
        for user_id, mission_id, slot_id, opened_at in old_slots:
            # Check if corresponding fire is still active
            bitten_cur.execute("""
                SELECT f.fire_id, f.status, f.created_at
                FROM fires f
                WHERE f.mission_id = ? OR f.fire_id = ?
            """, (mission_id, mission_id))
            
            fire_result = bitten_cur.fetchone()
            
            if fire_result:
                fire_id, status, created_at = fire_result
                age_hours = (current_time - created_at) / 3600
                
                # Position is very old and still marked as active
                if status in ['FILLED', 'CONFIRMED', 'SENT'] and age_hours > 4:
                    old_positions.append({
                        'user_id': user_id,
                        'mission_id': mission_id,
                        'slot_id': slot_id,
                        'fire_id': fire_id,
                        'age_hours': age_hours,
                        'reason': f'Position too old ({age_hours:.1f}h) - likely manually closed'
                    })
        
        fire_conn.close()
        bitten_conn.close()
        
        return old_positions
    
    def detect_closes_via_api_query(self, user_id: str, target_uuid: str):
        """
        Method 4: Query the EA directly for current open positions
        This would be the most reliable method if we can implement it
        """
        # This would require enhancing the EA to respond to position queries
        # For now, return empty list as placeholder
        logger.debug(f"🔌 Would query EA {target_uuid} for open positions...")
        return []
    
    def release_identified_slots(self, closed_positions: list):
        """Release slots that have been identified as closed"""
        released_count = 0
        
        for position in closed_positions:
            try:
                user_id = position['user_id']
                mission_id = position['mission_id']
                reason = position.get('reason', 'Detected as closed')
                
                # Release the slot
                if self.fire_mode_db.release_slot(user_id, mission_id):
                    logger.info(f"✅ Released slot for {user_id}: {reason}")
                    released_count += 1
                    
                    # Update fire status if we have fire_id
                    if 'fire_id' in position:
                        try:
                            conn = sqlite3.connect(self.bitten_db_path)
                            cur = conn.cursor()
                            
                            # Get mission_id and user_id for slot cleanup BEFORE updating status
                            cur.execute("""
                                SELECT user_id, mission_id FROM fires 
                                WHERE fire_id = ?
                            """, (position['fire_id'],))
                            fire_result = cur.fetchone()
                            
                            # Update fire status
                            cur.execute("""
                                UPDATE fires 
                                SET status = 'CLOSED_AUTO_DETECTED', updated_at = ?
                                WHERE fire_id = ?
                            """, (int(time.time()), position['fire_id']))
                            conn.commit()
                            conn.close()
                            
                            # CRITICAL: Release slot when position closes automatically
                            if fire_result:
                                user_id, mission_id = fire_result
                                try:
                                    import sys
                                    sys.path.append('/root/HydraX-v2/src')
                                    from src.bitten_core.fire_mode_database import FireModeDatabase
                                    fire_db = FireModeDatabase()
                                    if fire_db.release_slot(user_id, mission_id):
                                        logger.info(f"✅ AUTO CLOSE: Released slot for user {user_id}, position {position['fire_id']}")
                                    else:
                                        logger.warning(f"⚠️ AUTO CLOSE: Failed to release slot for user {user_id}, position {position['fire_id']}")
                                        
                                except Exception as slot_error:
                                    logger.error(f"❌ Slot cleanup failed for {position['fire_id']}: {slot_error}")
                            else:
                                logger.warning(f"⚠️ Could not find user/mission for fire_id {position['fire_id']}")
                                
                        except Exception as e:
                            logger.warning(f"Could not update fire status: {e}")
                            
                else:
                    logger.warning(f"⚠️ Failed to release slot for {user_id}: {reason}")
                    
            except Exception as e:
                logger.error(f"❌ Error releasing slot: {e}")
        
        return released_count
    
    def comprehensive_scan(self):
        """Run all detection methods and release identified slots"""
        logger.info("🔍 Starting comprehensive slot scan...")
        
        all_closed = []
        
        # Method 1: Balance changes
        try:
            balance_closes = self.detect_closes_via_ea_balance_changes()
            # Convert balance changes to slot releases (would need more logic)
        except Exception as e:
            logger.error(f"Balance detection failed: {e}")
        
        # Method 2: Ticket comparison  
        try:
            ticket_closes = self.detect_closes_via_ticket_comparison()
            all_closed.extend(ticket_closes)
        except Exception as e:
            logger.error(f"Ticket comparison failed: {e}")
        
        # Method 3: Time analysis
        try:
            time_closes = self.detect_closes_via_time_analysis()
            all_closed.extend(time_closes)
        except Exception as e:
            logger.error(f"Time analysis failed: {e}")
        
        # Release all identified slots
        if all_closed:
            released = self.release_identified_slots(all_closed)
            logger.info(f"🎰 Released {released}/{len(all_closed)} identified slots")
        else:
            logger.debug("No slots requiring release found")
        
        return len(all_closed)
    
    def monitor_loop(self):
        """Main monitoring loop - run this continuously"""
        logger.info("🎰 Robust Slot Manager started - multi-method detection active")
        
        while True:
            try:
                detected_count = self.comprehensive_scan()
                
                if detected_count > 0:
                    logger.info(f"Scan complete - processed {detected_count} position closures")
                
                # Check every 30 seconds for responsive slot management
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("🛑 Slot manager stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Robust Slot Manager')
    parser.add_argument('--scan-once', action='store_true', help='Run one scan and exit')
    parser.add_argument('--monitor', action='store_true', help='Run continuous monitoring')
    
    args = parser.parse_args()
    
    manager = RobustSlotManager()
    
    if args.scan_once:
        closed_count = manager.comprehensive_scan()
        print(f"Detected and processed {closed_count} closed positions")
    elif args.monitor:
        manager.monitor_loop()
    else:
        # Default: run one scan
        closed_count = manager.comprehensive_scan()
        print(f"Detected and processed {closed_count} closed positions")