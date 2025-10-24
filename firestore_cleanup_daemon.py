#!/usr/bin/env python3
"""
Firestore Active Trades Cleanup Daemon

PROBLEM: EA v3.013 doesn't send position_closed events, so Firestore active_trades
         accumulates closed positions forever, causing Battlefield to show wrong count.

SOLUTION: Every 60 seconds, sync Firestore with database live_positions table.
          Delete any Firestore documents where database says CLOSED or doesn't exist.

Author: Claude Code
Date: October 21, 2025
"""

import sqlite3
import time
import sys
from datetime import datetime

# Add HydraX-v2 to path for firebase_backend import
sys.path.insert(0, '/root/HydraX-v2')
import firebase_backend

DB_PATH = '/root/HydraX-v2/bitten.db'
SYNC_INTERVAL = 60  # seconds

def get_database_position_status(user_id: str) -> dict:
    """
    Query database for all positions and their status.

    Returns:
        dict: {fire_id: 'OPEN' or 'CLOSED'}
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()

        # Get all positions for user from live_positions table (TRUTH source)
        cursor.execute("""
            SELECT fire_id, status
            FROM live_positions
            WHERE user_id = ?
        """, (user_id,))

        positions = {}
        for fire_id, status in cursor.fetchall():
            positions[fire_id] = status

        conn.close()
        return positions

    except Exception as e:
        print(f"❌ Database query error: {e}")
        return {}


def cleanup_firestore_for_user(user_id: str, dry_run: bool = False):
    """
    Sync Firestore active_trades with database live_positions.
    Delete any Firestore documents that are CLOSED or don't exist in database.

    Args:
        user_id: Firebase UID
        dry_run: If True, only report what would be deleted
    """
    try:
        db = firebase_backend.get_firestore_client()
        if not db:
            print("❌ Firebase not initialized")
            return

        # Get database position status (TRUTH)
        db_positions = get_database_position_status(user_id)

        # Get all Firestore active_trades for this user
        firestore_trades = db.collection('active_trades').where('user_id', '==', user_id).stream()

        deleted_count = 0
        kept_count = 0

        for doc in firestore_trades:
            fire_id = doc.id
            db_status = db_positions.get(fire_id)

            # DELETE if: position CLOSED in database OR doesn't exist in database
            should_delete = (db_status == 'CLOSED') or (db_status is None)

            if should_delete:
                reason = "CLOSED in database" if db_status == 'CLOSED' else "NOT IN DATABASE"

                if dry_run:
                    print(f"🗑️  WOULD DELETE: {fire_id} ({reason})")
                else:
                    doc.reference.delete()
                    print(f"✅ DELETED: {fire_id} ({reason})")

                deleted_count += 1
            else:
                # Keep it (status is OPEN)
                kept_count += 1

        print(f"\n📊 SYNC COMPLETE for {user_id}:")
        print(f"   - Deleted: {deleted_count} closed/stale trades")
        print(f"   - Kept: {kept_count} open positions")
        print(f"   - Database has {len([s for s in db_positions.values() if s == 'OPEN'])} OPEN positions")

    except Exception as e:
        print(f"❌ Firestore cleanup error: {e}")


def run_continuous_sync(user_id: str):
    """Run cleanup every 60 seconds forever."""
    print(f"🚀 Firestore Cleanup Daemon Started")
    print(f"   User: {user_id}")
    print(f"   Sync Interval: {SYNC_INTERVAL} seconds")
    print(f"   Database: {DB_PATH}")
    print(f"   Press Ctrl+C to stop\n")

    while True:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{'='*60}")
            print(f"🔄 Starting sync at {timestamp}")
            print(f"{'='*60}")

            cleanup_firestore_for_user(user_id, dry_run=False)

            print(f"\n⏳ Next sync in {SYNC_INTERVAL} seconds...")
            time.sleep(SYNC_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n🛑 Daemon stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error in sync loop: {e}")
            print(f"⏳ Retrying in {SYNC_INTERVAL} seconds...")
            time.sleep(SYNC_INTERVAL)


if __name__ == '__main__':
    # Default user (can be overridden via command line)
    user_id = 'wlJ5lafBqRSLwHIUBxJQMr4SBtk1'

    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # Run once and exit (useful for cron)
            print("🔄 Running ONE-TIME sync")
            cleanup_firestore_for_user(user_id, dry_run=False)
        elif sys.argv[1] == '--dry-run':
            # Dry run mode
            print("🔍 DRY RUN MODE (no deletions)")
            cleanup_firestore_for_user(user_id, dry_run=True)
        elif sys.argv[1] == '--user':
            # Custom user
            user_id = sys.argv[2]
            run_continuous_sync(user_id)
        else:
            print("Usage:")
            print("  python3 firestore_cleanup_daemon.py           # Run continuously")
            print("  python3 firestore_cleanup_daemon.py --once    # Run once and exit")
            print("  python3 firestore_cleanup_daemon.py --dry-run # Show what would be deleted")
            print("  python3 firestore_cleanup_daemon.py --user UID # Custom user")
    else:
        # Default: run continuously
        run_continuous_sync(user_id)
