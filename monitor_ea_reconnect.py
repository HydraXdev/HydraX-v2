#!/usr/bin/env python3
"""
Monitor EA reconnection when market opens
Watches for fresh heartbeats and tick flow
"""

import sqlite3
import subprocess
import time
from datetime import datetime

print("🔄 Monitoring EA reconnection (Ctrl+C to stop)")
print("=" * 60)

last_tick_count = 22
last_heartbeat_count = 1
last_db_age = 99999

while True:
    try:
        # Check telemetry stats
        result = subprocess.run(
            ["tail", "-1", "/root/.pm2/logs/telemetry-bridge-v207-error.log"], capture_output=True, text=True
        )

        if "STATS:" in result.stdout:
            stats_line = result.stdout.split("STATS:")[1].strip()
            # Parse: Ticks: X, Heartbeats: Y, Metrics: Z, Positions: W
            parts = stats_line.split(",")
            ticks = int(parts[0].split(":")[1].strip())
            heartbeats = int(parts[1].split(":")[1].strip())

            # Check database for EA freshness
            conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT (strftime('%s','now') - last_seen) AS age_seconds
                FROM ea_instances
                WHERE target_uuid = 'COMMANDER_DEV_001'
            """
            )
            result = cursor.fetchone()
            db_age = result[0] if result else 99999
            conn.close()

            # Detect changes
            tick_delta = ticks - last_tick_count
            hb_delta = heartbeats - last_heartbeat_count

            # Print status
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Clear line and print status
            status_parts = []

            if tick_delta > 0:
                status_parts.append(f"🟢 +{tick_delta} ticks")
            if hb_delta > 0:
                status_parts.append(f"💚 +{hb_delta} heartbeats")
            if db_age < 120:
                status_parts.append(f"✅ EA fresh ({db_age}s)")
            elif db_age < last_db_age - 100:
                status_parts.append(f"🔄 EA updating ({db_age}s)")

            if status_parts:
                print(f"[{timestamp}] " + " | ".join(status_parts))
                if db_age < 120:
                    print("\n🎉 EA RECONNECTED! System ready for trading")
                    print("Run: python3 /root/HydraX-v2/test_fire_v207.py")
                    break
            else:
                print(f"[{timestamp}] Waiting... (Ticks: {ticks}, HB: {heartbeats}, Age: {db_age}s)", end="\r")

            # Update last values
            last_tick_count = ticks
            last_heartbeat_count = heartbeats
            last_db_age = db_age

        time.sleep(5)  # Check every 5 seconds

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
