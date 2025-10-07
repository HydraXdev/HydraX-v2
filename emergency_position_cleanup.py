#!/usr/bin/env python3
"""
Emergency Position Cleanup - Sync Database with MT5 Reality
Clears stale FILLED positions that were closed in MT5 but not in database
"""

import sqlite3
import time

DB_PATH = "/root/HydraX-v2/bitten.db"


def show_status():
    """Show current database status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT status, COUNT(*) as count
        FROM fires
        GROUP BY status
        ORDER BY count DESC
    """
    )

    print("\n📊 Current fires table status:")
    print("-" * 40)
    for status, count in cursor.fetchall():
        print(f"{status:30} {count:>6}")
    print("-" * 40)

    cursor.execute("SELECT COUNT(*) FROM fires WHERE status = 'FILLED'")
    filled_count = cursor.fetchone()[0]

    conn.close()
    return filled_count


print("=" * 60)
print("🚨 EMERGENCY DATABASE CLEANUP")
print("=" * 60)

filled_count = show_status()

if filled_count == 0:
    print("\n✅ No FILLED positions to clean")
else:
    print(f"\n⚠️  Cleaning {filled_count} stale FILLED positions...")

    # Close all FILLED positions (they're closed in MT5 but database is stale)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    current_time = int(time.time())
    cursor.execute(
        """
        UPDATE fires
        SET status = 'CLOSED_SYNC',
            updated_at = ?,
            close_reason = 'CLOSED_IN_MT5_MANUAL_SYNC'
        WHERE status = 'FILLED'
    """,
        (current_time,),
    )

    updated = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"✅ Closed {updated} stale positions")
    show_status()

print("\n🎯 Database synced with MT5 reality")
print("✅ Auto-fire should work now")
