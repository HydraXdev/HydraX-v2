#!/usr/bin/env python3
"""
Firestore Active Trades Sync Daemon
Runs every 60 seconds to sync Firestore with database positions
"""
import sys
sys.path.insert(0, '/root/HydraX-v2')

import time
import sqlite3
from firebase_backend import get_firestore_client
from sync_firestore_positions import sync_positions_for_user

DB_PATH = "/root/HydraX-v2/bitten.db"

def get_all_active_users():
    """Get list of users with open positions in last 24 hours"""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT user_id FROM live_positions
        WHERE last_update > (strftime('%s', 'now') - 86400)
    """)
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def main():
    print("🚀 Firestore Sync Daemon starting...")
    print("   Running every 60 seconds to keep Firestore in sync")

    while True:
        try:
            users = get_all_active_users()

            for user_id in users:
                sync_positions_for_user(user_id)

            print(f"✅ Sync complete - Synced {len(users)} users\n")

        except Exception as e:
            print(f"❌ Sync error: {e}")

        time.sleep(60)

if __name__ == '__main__':
    main()
