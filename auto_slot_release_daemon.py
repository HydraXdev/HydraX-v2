#!/usr/bin/env python3
"""
Auto Slot Release Daemon
========================
Monitors closed trades and automatically releases fire slots.
Prevents slot exhaustion by ensuring slots are freed when trades complete.
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoSlotReleaseDaemon:
    def __init__(self):
        self.bitten_db = '/root/HydraX-v2/bitten.db'
        self.fire_modes_db = '/root/HydraX-v2/data/fire_modes.db'
        self.check_interval = 30  # Check every 30 seconds

    def get_active_fire_ids(self):
        """Get all fire IDs that are currently marked as FILLED (active trades)."""
        with sqlite3.connect(self.bitten_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT fire_id, user_id
                FROM fires
                WHERE status = 'FILLED'
                AND created_at > strftime('%s', 'now', '-24 hours')
            """)
            return cursor.fetchall()

    def check_if_trade_closed(self, fire_id):
        """Check if a trade has been closed (has an outcome in tracking or closures)."""
        # Check comprehensive tracking
        try:
            with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'r') as f:
                for line in f:
                    if fire_id in line and '"outcome"' in line:
                        if 'WIN' in line or 'LOSS' in line:
                            return True
        except:
            pass

        # Check trade closures table (simplified - just check if trade closed)
        # For now, rely on tracking file only since trade_closures doesn't have fire_id

        return False

    def release_slot(self, user_id, fire_id):
        """Release an auto slot for the user."""
        with sqlite3.connect(self.fire_modes_db) as conn:
            cursor = conn.cursor()

            # Decrease auto_slots_in_use
            cursor.execute("""
                UPDATE user_fire_modes
                SET auto_slots_in_use = MAX(0, auto_slots_in_use - 1)
                WHERE user_id = ?
            """, (user_id,))

            if cursor.rowcount > 0:
                logger.info(f"✅ Released slot for user {user_id}, fire_id: {fire_id}")
                return True
        return False

    def sync_slots_with_reality(self):
        """Sync slot counts with actual open positions."""
        # For user 7176191872, count actual FILLED trades from last 4 hours
        with sqlite3.connect(self.bitten_db) as conn:
            cursor = conn.cursor()

            # Get all users with their recent FILLED trades
            cursor.execute("""
                SELECT user_id, COUNT(*) as active_count
                FROM fires
                WHERE status = 'FILLED'
                AND created_at > strftime('%s', 'now', '-4 hours')
                GROUP BY user_id
            """)

            user_counts = cursor.fetchall()

        # Update fire_modes database
        with sqlite3.connect(self.fire_modes_db) as conn:
            cursor = conn.cursor()

            for user_id, active_count in user_counts:
                # Check closed trades
                closed_count = 0

                # Get fire IDs for this user
                with sqlite3.connect(self.bitten_db) as bitten_conn:
                    bitten_cursor = bitten_conn.cursor()
                    bitten_cursor.execute("""
                        SELECT fire_id FROM fires
                        WHERE user_id = ? AND status = 'FILLED'
                        AND created_at > strftime('%s', 'now', '-4 hours')
                    """, (user_id,))

                    fire_ids = bitten_cursor.fetchall()

                    for (fire_id,) in fire_ids:
                        if self.check_if_trade_closed(fire_id):
                            closed_count += 1

                # Real open positions
                real_open = active_count - closed_count

                # Update slot count to match reality
                cursor.execute("""
                    UPDATE user_fire_modes
                    SET auto_slots_in_use = ?
                    WHERE user_id = ?
                """, (max(0, real_open), user_id))

                if cursor.rowcount > 0:
                    logger.info(f"📊 User {user_id}: {real_open} actual open positions (was {active_count} filled, {closed_count} closed)")

    def run(self):
        """Main daemon loop."""
        logger.info("🚀 Auto Slot Release Daemon started")

        while True:
            try:
                # First sync with reality
                self.sync_slots_with_reality()

                # Check current slot usage
                with sqlite3.connect(self.fire_modes_db) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT user_id, auto_slots_in_use, max_auto_slots
                        FROM user_fire_modes
                        WHERE current_mode = 'AUTO'
                    """)

                    for user_id, used, max_slots in cursor.fetchall():
                        if used > 0:
                            logger.info(f"📍 User {user_id}: {used}/{max_slots} auto slots in use")

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Daemon error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    daemon = AutoSlotReleaseDaemon()
    daemon.run()