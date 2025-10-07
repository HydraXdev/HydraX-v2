#!/usr/bin/env python3
"""
Sync Fire Slots with EA Reality
Uses EA heartbeat (port 5556) as single source of truth
"""

import sqlite3
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_slots_from_ea():
    """Sync slot tracking with EA heartbeat reality"""
    
    # Get EA current state from database (updated every second by telemetry bridge)
    bitten_conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    bitten_cursor = bitten_conn.cursor()
    
    bitten_cursor.execute("""
        SELECT target_uuid, user_id, open_positions, last_balance, last_equity
        FROM ea_instances 
        WHERE target_uuid = 'COMMANDER_DEV_001'
    """)
    
    ea_data = bitten_cursor.fetchone()
    bitten_conn.close()
    
    if not ea_data:
        logger.error("❌ No EA instance found for COMMANDER_DEV_001")
        return False
    
    target_uuid, user_id, ea_open_positions, balance, equity = ea_data
    
    logger.info(f"📡 EA Heartbeat: {ea_open_positions} open positions for user {user_id}")
    logger.info(f"💰 Balance: ${balance:.2f} | Equity: ${equity:.2f}")
    
    # Update fire_modes database with EA reality
    fire_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
    fire_cursor = fire_conn.cursor()
    
    # Get max slots allowed
    fire_cursor.execute("""
        SELECT max_slots, max_auto_slots 
        FROM user_fire_modes 
        WHERE user_id = ?
    """, (user_id,))
    
    slot_config = fire_cursor.fetchone()
    
    if not slot_config:
        logger.warning(f"⚠️ No fire mode config for user {user_id}")
        fire_conn.close()
        return False
    
    max_slots, max_auto_slots = slot_config
    
    # Update slots in use to match EA reality
    fire_cursor.execute("""
        UPDATE user_fire_modes 
        SET auto_slots_in_use = ?
        WHERE user_id = ?
    """, (ea_open_positions, user_id))
    
    fire_conn.commit()
    fire_conn.close()
    
    available_slots = max_auto_slots - ea_open_positions
    
    logger.info(f"✅ Synced slots for user {user_id}:")
    logger.info(f"   EA Reality: {ea_open_positions} open positions")
    logger.info(f"   Max Slots: {max_auto_slots}")
    logger.info(f"   Available: {available_slots}")
    
    return True

if __name__ == "__main__":
    logger.info("🔄 Starting EA slot sync...")
    success = sync_slots_from_ea()
    
    if success:
        logger.info("✅ Slot sync complete")
    else:
        logger.error("❌ Slot sync failed")
