#!/usr/bin/env python3
"""
Simple Press Pass Reset Script for Cron Jobs
Standalone script with minimal dependencies
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BITTEN_HOME = Path("/root/HydraX-v2")
DATABASE_PATH = BITTEN_HOME / "data" / "bitten_xp.db"

def warn_users(minutes_until_reset):
    """Send warning to Press Pass users"""
    logger.info(f"Warning: Press Pass XP reset in {minutes_until_reset} minutes")
    
    try:
        if DATABASE_PATH.exists():
            with sqlite3.connect(str(DATABASE_PATH)) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE tier = 'PRESS_PASS' AND last_active > datetime('now', '-1 day')
                """)
                active_users = cursor.fetchone()[0]
                logger.info(f"Warning sent to {active_users} active Press Pass users")
        else:
            logger.warning(f"Database not found at {DATABASE_PATH}")
            
    except Exception as e:
        logger.error(f"Warning failed: {e}")

def reset_press_pass_xp():
    """Reset XP for all Press Pass users"""
    logger.info("Starting Press Pass XP reset")
    
    try:
        if DATABASE_PATH.exists():
            with sqlite3.connect(str(DATABASE_PATH)) as conn:
                # Reset XP for Press Pass users
                cursor = conn.execute("""
                    UPDATE users 
                    SET xp = 0, daily_xp = 0 
                    WHERE tier = 'PRESS_PASS'
                """)
                affected_users = cursor.rowcount
                
                # Log reset event
                conn.execute("""
                    INSERT INTO xp_events (user_id, event_type, xp_change, timestamp)
                    SELECT user_id, 'PRESS_PASS_RESET', -xp, datetime('now')
                    FROM users WHERE tier = 'PRESS_PASS'
                """)
                
                logger.info(f"Reset XP for {affected_users} Press Pass users")
        else:
            logger.warning(f"Database not found at {DATABASE_PATH}")
            
    except Exception as e:
        logger.error(f"Reset failed: {e}")

def health_check():
    """Check if press pass system is healthy"""
    logger.info("Press Pass health check")
    
    try:
        if DATABASE_PATH.exists():
            with sqlite3.connect(str(DATABASE_PATH)) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM users WHERE tier = 'PRESS_PASS'")
                press_pass_users = cursor.fetchone()[0]
                logger.info(f"Health check: {press_pass_users} Press Pass users")
        else:
            logger.warning(f"Database not found at {DATABASE_PATH}")
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        logger.error("Usage: simple_press_pass_reset.py [warn_60|warn_15|reset|health]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "warn_60":
        warn_users(60)
    elif action == "warn_15":
        warn_users(15)
    elif action == "reset":
        reset_press_pass_xp()
    elif action == "health":
        health_check()
    else:
        logger.error(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()