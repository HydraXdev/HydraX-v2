#!/usr/bin/env python3
"""
Position Reality Check - Manual position verification system
Since EA position monitoring is limited, create a smart detection system
"""

import logging
import sqlite3
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_position_reality():
    """Smart position verification based on multiple indicators"""

    db_path = "/root/HydraX-v2/bitten.db"
    current_time = int(time.time())

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get current open positions with age analysis
        cursor.execute(
            """
            SELECT
                lp.fire_id,
                lp.symbol,
                lp.direction,
                f.ticket,
                f.price as entry_price,
                lp.last_update,
                datetime(lp.last_update, 'unixepoch') as readable_time,
                (? - lp.last_update) as age_seconds,
                ((? - lp.last_update) / 60.0) as age_minutes
            FROM live_positions lp
            JOIN fires f ON lp.fire_id = f.fire_id
            WHERE lp.status = 'OPEN'
            ORDER BY lp.last_update DESC
        """,
            (current_time, current_time),
        )

        positions = cursor.fetchall()

        logger.info("📊 POSITION REALITY CHECK")
        logger.info("=" * 50)
        logger.info("Current time: %s", time.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("Total positions in database: %d", len(positions))

        if not positions:
            logger.info("✅ No open positions - database is clean")
            return

        stale_positions = []
        recent_positions = []

        for pos in positions:
            fire_id, symbol, direction, ticket, entry, last_update, readable, age_sec, age_min = pos

            logger.info("")
            logger.info("🎯 %s", fire_id)
            logger.info("   %s %s (ticket: %s)", symbol, direction, ticket)
            logger.info("   Entry: %s", entry)
            logger.info("   Last Update: %s (%.1f minutes ago)", readable, age_min)

            if age_min > 10:  # More than 10 minutes old
                stale_positions.append(pos)
                logger.info("   ⚠️ STALE - No activity for %.1f minutes", age_min)
            else:
                recent_positions.append(pos)
                logger.info("   ✅ RECENT - Updated %.1f minutes ago", age_min)

        logger.info("")
        logger.info("📈 SUMMARY:")
        logger.info("   Recent positions (< 10 min): %d", len(recent_positions))
        logger.info("   Stale positions (> 10 min): %d", len(stale_positions))

        # Analysis and recommendations
        if stale_positions:
            logger.info("")
            logger.info("🔍 STALE POSITION ANALYSIS:")

            for pos in stale_positions:
                fire_id, symbol, direction, ticket, entry, last_update, readable, age_sec, age_min = pos

                if age_min > 60:  # More than 1 hour
                    logger.info("   🔴 %s - Very stale (%.1f hours) - Likely manually closed", fire_id, age_min / 60)
                elif age_min > 30:  # More than 30 minutes
                    logger.info("   🟡 %s - Moderately stale (%.1f min) - Check MT5 status", fire_id, age_min)
                else:
                    logger.info("   🟠 %s - Recently stale (%.1f min) - Monitor closely", fire_id, age_min)

        # Auto-cleanup recommendation
        very_stale = [p for p in stale_positions if (current_time - p[5]) > 3600]  # 1 hour

        if very_stale:
            logger.info("")
            logger.info("🧹 AUTO-CLEANUP RECOMMENDATION:")
            logger.info("   Found %d positions stale for >1 hour", len(very_stale))
            logger.info("   These are likely manually closed and should be synced")

            response = input("\n❓ Auto-close these stale positions? (y/N): ").strip().lower()

            if response == "y":
                for pos in very_stale:
                    fire_id = pos[0]
                    ticket = pos[3]

                    # Update fires table
                    cursor.execute("UPDATE fires SET status = 'CLOSED_AUTO_CLEANUP' WHERE fire_id = ?", (fire_id,))

                    # Update live_positions table
                    cursor.execute(
                        """
                        UPDATE live_positions
                        SET status = 'CLOSED', last_update = ?
                        WHERE fire_id = ?
                    """,
                        (current_time, fire_id),
                    )

                    logger.info("✅ Auto-closed: %s (ticket %s)", fire_id, ticket)

                conn.commit()

                # Show new count
                cursor.execute("SELECT COUNT(*) FROM live_positions WHERE status = 'OPEN'")
                new_count = cursor.fetchone()[0]

                logger.info("")
                logger.info("🎯 CLEANUP COMPLETE:")
                logger.info("   Closed %d stale positions", len(very_stale))
                logger.info("   Remaining open positions: %d", new_count)

        conn.close()

    except Exception as e:
        logger.error("Position reality check failed: %s", e)


if __name__ == "__main__":
    check_position_reality()
