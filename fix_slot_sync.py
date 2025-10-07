#!/usr/bin/env python3
"""
Fix Slot Sync - Properly sync slots with actual open positions
Cleans up orphaned slots and ensures accurate count
"""

import json
import logging
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_slot_sync():
    """Fix the slot sync issue by closing slots for completed trades"""

    # Get all OPEN slots
    fire_conn = sqlite3.connect("/root/HydraX-v2/data/fire_modes.db")
    fire_cursor = fire_conn.cursor()

    fire_cursor.execute(
        """
        SELECT slot_id, user_id, mission_id, symbol, slot_type
        FROM active_slots
        WHERE status = 'OPEN'
        ORDER BY opened_at DESC
    """
    )

    open_slots = fire_cursor.fetchall()
    logger.info(f"Found {len(open_slots)} open slots to check")

    # Check each slot to see if the trade is actually closed
    closed_count = 0
    for slot_id, user_id, mission_id, symbol, slot_type in open_slots:
        # Check if trade has an outcome in tracking
        is_closed = False

        # Check comprehensive tracking
        try:
            with open("/root/HydraX-v2/comprehensive_tracking.jsonl", "r") as f:
                for line in f:
                    if mission_id in line and '"outcome"' in line:
                        data = json.loads(line)
                        if data.get("outcome") in ["WIN", "LOSS", "MANUAL_CLOSE", "TIMEOUT"]:
                            is_closed = True
                            break
        except:
            pass

        # Check fires table for CLOSED status
        if not is_closed:
            bitten_conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
            bitten_cursor = bitten_conn.cursor()
            bitten_cursor.execute(
                """
                SELECT status FROM fires
                WHERE fire_id = ?
            """,
                (mission_id,),
            )
            result = bitten_cursor.fetchone()
            if result and result[0] in ["CLOSED", "CLOSED_AUTO_DETECTED", "COMPLETED"]:
                is_closed = True
            bitten_conn.close()

        if is_closed:
            # Close the slot
            fire_cursor.execute(
                """
                UPDATE active_slots
                SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP
                WHERE slot_id = ?
            """,
                (slot_id,),
            )

            # Decrement the appropriate slot counter
            if slot_type == "AUTO":
                fire_cursor.execute(
                    """
                    UPDATE user_fire_modes
                    SET auto_slots_in_use = MAX(0, auto_slots_in_use - 1)
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
            else:
                fire_cursor.execute(
                    """
                    UPDATE user_fire_modes
                    SET manual_slots_in_use = MAX(0, manual_slots_in_use - 1)
                    WHERE user_id = ?
                """,
                    (user_id,),
                )

            closed_count += 1
            logger.info(f"✅ Closed orphaned slot: {mission_id} ({slot_type})")

    fire_conn.commit()

    # Now count actual open positions from fires table
    bitten_conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
    bitten_cursor = bitten_conn.cursor()

    bitten_cursor.execute(
        """
        SELECT COUNT(*)
        FROM fires
        WHERE user_id = '7176191872'
        AND status = 'FILLED'
        AND created_at > strftime('%s', 'now', '-24 hours')
    """
    )

    filled_count = bitten_cursor.fetchone()[0]

    # Get closed count from tracking
    closed_from_tracking = 0
    try:
        with open("/root/HydraX-v2/comprehensive_tracking.jsonl", "r") as f:
            recent_closes = []
            for line in f:
                if "7176191872" in line or "ELITE" in line:
                    try:
                        data = json.loads(line)
                        if data.get("outcome") in ["WIN", "LOSS", "MANUAL_CLOSE"]:
                            if data.get("timestamp", 0) > (time.time() - 86400):  # Last 24h
                                recent_closes.append(data.get("signal_id"))
                    except:
                        pass
            closed_from_tracking = len(set(recent_closes))
    except:
        pass

    actual_open = max(0, filled_count - closed_from_tracking)

    # Update to correct count
    fire_cursor.execute(
        """
        UPDATE user_fire_modes
        SET auto_slots_in_use = ?
        WHERE user_id = '7176191872'
    """,
        (actual_open,),
    )

    fire_conn.commit()

    # Get final status
    fire_cursor.execute(
        """
        SELECT auto_slots_in_use, max_auto_slots
        FROM user_fire_modes
        WHERE user_id = '7176191872'
    """
    )

    used, max_slots = fire_cursor.fetchone()

    fire_conn.close()
    bitten_conn.close()

    logger.info(f"\n🔧 FIXED: Closed {closed_count} orphaned slots")
    logger.info(f"📊 Current status: {used}/{max_slots} slots in use")
    logger.info(f"   Filled trades: {filled_count}")
    logger.info(f"   Closed trades: {closed_from_tracking}")
    logger.info(f"   Actual open: {actual_open}")

    return used, max_slots


if __name__ == "__main__":
    import time

    fix_slot_sync()
