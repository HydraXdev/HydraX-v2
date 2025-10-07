#!/usr/bin/env python3
"""
Final Position Tracking Fix
Direct MT5 position query via command router to get ground truth
"""

import json
import logging
import sqlite3
import time

import zmq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_position_status_command():
    """Send a command to EA to get current position status"""

    context = zmq.Context()

    try:
        # Connect to command router (same path as fire commands)
        socket = context.socket(zmq.PUSH)
        socket.connect("ipc:///tmp/bitten_cmdqueue")

        # Send position status query command
        status_cmd = {
            "type": "position_status",
            "target_uuid": "COMMANDER_DEV_001",
            "fire_id": f"STATUS_QUERY_{int(time.time())}",
            "user_id": "7176191872",
        }

        socket.send_json(status_cmd)
        logger.info("📡 Sent position status query to EA")

        socket.close()
        context.term()

        # Wait a moment for EA to process
        time.sleep(3)

        return True

    except Exception as e:
        logger.error("Failed to send position status command: %s", e)
        return False


def clear_all_tracked_positions():
    """Clear all positions and start fresh - manual reality sync"""

    db_path = "/root/HydraX-v2/bitten.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get current open positions
        cursor.execute("SELECT COUNT(*) FROM live_positions WHERE status = 'OPEN'")
        open_count = cursor.fetchone()[0]

        logger.info("🔄 Current open positions in database: %d", open_count)

        if open_count > 0:
            logger.info("⚠️ System is unreliable - forcing manual sync")

            # Ask user for reality check
            actual_count = input(
                f"\n❓ How many positions do you ACTUALLY have open in MT5? (database shows {open_count}): "
            ).strip()

            try:
                actual_count = int(actual_count)
            except ValueError:
                logger.error("Invalid input. Exiting.")
                return False

            if actual_count == 0:
                logger.info("🧹 User confirms 0 open positions - clearing database")

                # Mark all as closed
                cursor.execute(
                    """
                    UPDATE live_positions
                    SET status = 'CLOSED_MANUAL_SYNC', last_update = ?
                    WHERE status = 'OPEN'
                """,
                    (int(time.time()),),
                )

                cursor.execute(
                    """
                    UPDATE fires
                    SET status = 'CLOSED_MANUAL_SYNC'
                    WHERE status IN ('FILLED', 'SENT')
                """
                )

                conn.commit()

                # Verify
                cursor.execute("SELECT COUNT(*) FROM live_positions WHERE status = 'OPEN'")
                final_count = cursor.fetchone()[0]

                logger.info("✅ Database cleared - now shows %d open positions", final_count)

            elif actual_count < open_count:
                logger.info("🔄 User has %d positions, database shows %d", actual_count, open_count)
                logger.info("   Need to close %d positions in database", open_count - actual_count)

                # Get positions ordered by age (oldest first)
                cursor.execute(
                    """
                    SELECT fire_id, symbol, direction, last_update
                    FROM live_positions
                    WHERE status = 'OPEN'
                    ORDER BY last_update ASC
                """
                )
                positions = cursor.fetchall()

                positions_to_close = open_count - actual_count

                logger.info("   Closing %d oldest positions:", positions_to_close)

                for i in range(positions_to_close):
                    fire_id, symbol, direction, last_update = positions[i]

                    cursor.execute(
                        """
                        UPDATE live_positions
                        SET status = 'CLOSED_MANUAL_SYNC', last_update = ?
                        WHERE fire_id = ?
                    """,
                        (int(time.time()), fire_id),
                    )

                    cursor.execute(
                        """
                        UPDATE fires
                        SET status = 'CLOSED_MANUAL_SYNC'
                        WHERE fire_id = ?
                    """,
                        (fire_id,),
                    )

                    logger.info("     ✅ Closed: %s (%s %s)", fire_id, symbol, direction)

                conn.commit()

                # Verify
                cursor.execute("SELECT COUNT(*) FROM live_positions WHERE status = 'OPEN'")
                final_count = cursor.fetchone()[0]

                logger.info("✅ Database synced - now shows %d open positions", final_count)

            else:
                logger.info("✅ Database count matches user report")

        conn.close()
        return True

    except Exception as e:
        logger.error("Manual sync failed: %s", e)
        return False


def show_current_status():
    """Show current database status"""

    db_path = "/root/HydraX-v2/bitten.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                lp.fire_id,
                lp.symbol,
                lp.direction,
                f.ticket,
                datetime(lp.last_update, 'unixepoch') as last_update
            FROM live_positions lp
            JOIN fires f ON lp.fire_id = f.fire_id
            WHERE lp.status = 'OPEN'
            ORDER BY lp.last_update DESC
        """
        )

        positions = cursor.fetchall()

        logger.info("\n📊 FINAL DATABASE STATUS:")
        logger.info("=" * 50)
        logger.info("Open positions: %d", len(positions))

        if positions:
            logger.info("\nRemaining positions:")
            for fire_id, symbol, direction, ticket, last_update in positions:
                logger.info("  • %s: %s %s (ticket %s) - %s", fire_id, symbol, direction, ticket, last_update)
        else:
            logger.info("✅ No open positions - database is clean")

        conn.close()

    except Exception as e:
        logger.error("Status check failed: %s", e)


def main():
    """Main function to fix position tracking"""

    logger.info("🔧 FINAL POSITION TRACKING FIX")
    logger.info("=" * 50)

    # Try to query EA first
    logger.info("1️⃣ Attempting to query EA for current positions...")
    if send_position_status_command():
        logger.info("   ✅ Command sent - check EA response")
    else:
        logger.info("   ❌ Command failed")

    # Manual reality sync
    logger.info("\n2️⃣ Manual reality sync...")
    if clear_all_tracked_positions():
        logger.info("   ✅ Manual sync completed")
    else:
        logger.info("   ❌ Manual sync failed")

    # Show final status
    logger.info("\n3️⃣ Final status check...")
    show_current_status()

    logger.info("\n🎯 Position tracking fix complete!")


if __name__ == "__main__":
    main()
