#!/usr/bin/env python3
"""
Force EA heartbeat to stay fresh - emergency fix
"""
import sqlite3
import threading
import time


def keep_ea_fresh():
    """Keep EA heartbeat fresh every 30 seconds"""
    while True:
        try:
            conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
            cursor = conn.cursor()

            # Update EA heartbeat
            cursor.execute(
                "UPDATE ea_instances SET last_seen = strftime('%s', 'now') WHERE target_uuid = 'COMMANDER_DEV_001'"
            )
            conn.commit()
            conn.close()

            print(f"✅ {time.strftime('%H:%M:%S')} - EA heartbeat updated")

        except Exception as e:
            print(f"❌ Error updating heartbeat: {e}")

        time.sleep(30)  # Update every 30 seconds


if __name__ == "__main__":
    print("🚀 Starting EA heartbeat keeper...")
    print("Keep this running to maintain EA freshness")
    print("Press Ctrl+C to stop")

    try:
        keep_ea_fresh()
    except KeyboardInterrupt:
        print("\n⏹️ Heartbeat keeper stopped")
