#!/usr/bin/env python3
"""
Cleanup Archived Signals
Deletes signals older than 8 hours that have completed (WIN/LOSS/EXPIRED)
Keeps active signals (no outcome) indefinitely
"""

import sqlite3
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "/root/HydraX-v2/bitten.db"
HOURS_TO_KEEP = 8  # Delete archived signals after 8 hours

def cleanup_archived_signals():
    """Delete archived signals older than configured hours"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Calculate cutoff time (8 hours ago)
    cutoff_time = int(time.time() - (HOURS_TO_KEEP * 3600))

    # Count signals to delete
    cursor.execute("""
        SELECT COUNT(*) FROM signals
        WHERE outcome IS NOT NULL
        AND outcome IN ('WIN', 'LOSS', 'EXPIRED', 'SL', 'TP', 'TP_HIT', 'SL_HIT')
        AND created_at < ?
    """, (cutoff_time,))

    count = cursor.fetchone()[0]

    if count == 0:
        logger.info("✅ No archived signals to delete")
        conn.close()
        return

    # Delete old archived signals
    cursor.execute("""
        DELETE FROM signals
        WHERE outcome IS NOT NULL
        AND outcome IN ('WIN', 'LOSS', 'EXPIRED', 'SL', 'TP', 'TP_HIT', 'SL_HIT')
        AND created_at < ?
    """, (cutoff_time,))

    conn.commit()
    conn.close()

    logger.info(f"🗑️  Deleted {count} archived signals older than {HOURS_TO_KEEP} hours")

if __name__ == "__main__":
    try:
        cleanup_archived_signals()
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
