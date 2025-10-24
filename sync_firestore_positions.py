#!/usr/bin/env python3
"""
Sync Firestore active_trades with database live_positions
Deletes stale Firestore trades that aren't open in database
"""
import sys
sys.path.insert(0, '/root/HydraX-v2')

import sqlite3
from firebase_backend import get_firestore_client, close_active_trade

DB_PATH = "/root/HydraX-v2/bitten.db"

def get_database_open_positions(user_id: str) -> set:
    """Get set of fire_ids that are OPEN in database"""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fire_id FROM live_positions
        WHERE user_id = ? AND status = 'OPEN'
    """, (user_id,))
    open_positions = {row[0] for row in cursor.fetchall()}
    conn.close()
    return open_positions

def get_firestore_active_trades(user_id: str) -> dict:
    """Get dict of trade_id -> data from Firestore active_trades"""
    db = get_firestore_client()
    if not db:
        return {}

    active_trades = {}
    # CRITICAL FIX: .where() filter is BROKEN, get ALL trades and filter in Python
    for doc in db.collection('active_trades').stream():
        data = doc.to_dict()
        if data.get('user_id') == user_id:
            active_trades[doc.id] = data

    return active_trades

def sync_positions_for_user(user_id: str):
    """Sync Firestore active_trades with database for specific user"""
    print(f"🔄 Syncing positions for user: {user_id}")

    # Get current state
    db_open = get_database_open_positions(user_id)
    firestore_active = get_firestore_active_trades(user_id)

    print(f"  📊 Database: {len(db_open)} open positions")
    print(f"  📊 Firestore: {len(firestore_active)} active trades")

    # Find stale trades (in Firestore but not in database)
    stale_trades = set(firestore_active.keys()) - db_open

    if not stale_trades:
        print(f"  ✅ No stale trades found - Firestore is in sync")
        return

    print(f"  🗑️ Found {len(stale_trades)} stale trades to clean:")

    db = get_firestore_client()
    for trade_id in stale_trades:
        trade_data = firestore_active[trade_id]
        symbol = trade_data.get('pair') or trade_data.get('symbol') or 'UNKNOWN'
        equity = trade_data.get('equity', 0)

        print(f"    - {trade_id} | {symbol} | Equity: {equity}")

        # Delete from Firestore active_trades
        db.collection('active_trades').document(trade_id).delete()
        print(f"      ✅ Deleted from active_trades")

    print(f"  ✅ Cleanup complete")

def sync_all_users():
    """Sync all users' positions"""
    # Get all unique user_ids from database
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM live_positions WHERE status = 'OPEN'")
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"🔍 Found {len(user_ids)} users with open positions")

    for user_id in user_ids:
        sync_positions_for_user(user_id)
        print()

if __name__ == "__main__":
    print("🚀 Firestore Position Sync Tool\n")

    if len(sys.argv) > 1:
        # Sync specific user
        user_id = sys.argv[1]
        sync_positions_for_user(user_id)
    else:
        # Sync all users
        sync_all_users()

    print("\n✅ Sync complete!")
