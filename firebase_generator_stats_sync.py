#!/usr/bin/env python3
"""
Firebase Signal Generator Stats Sync
=====================================
Syncs signal generator performance to Firestore for Trading Intelligence dashboard.

Updates every 60 seconds to signal_generators collection with:
- Signals generated in last 24h
- Win rate
- Average confidence
- Last signal timestamp
- Status (online/offline based on recent activity)

Author: BITTEN System
Date: October 23, 2025
"""

import sqlite3
import time
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore


class GeneratorStatsSync:
    """Syncs generator stats to Firestore"""

    def __init__(self):
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("/root/bitten-firebase-sa.json")
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.sqlite_db = "/root/HydraX-v2/bitten.db"
        print("🚀 Firebase Generator Stats Sync initialized")

    def get_generator_stats_by_patterns(self, gen_id, pattern_prefixes):
        """Get stats for a specific generator using actual pattern names"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()

            # Get 24h stats
            timestamp_24h_ago = int((datetime.now() - timedelta(hours=24)).timestamp())

            # Build WHERE clause for multiple pattern prefixes
            pattern_conditions = " OR ".join([f"pattern_type LIKE '{prefix}%'" for prefix in pattern_prefixes])

            query = f"""
                SELECT
                    COUNT(*) as total_signals,
                    AVG(confidence) as avg_confidence,
                    MAX(created_at) as last_signal,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses
                FROM signals
                WHERE ({pattern_conditions})
                AND created_at > ?
            """

            cursor.execute(query, (timestamp_24h_ago,))
            row = cursor.fetchone()
            conn.close()

            if row:
                total, avg_conf, last_signal, wins, losses = row
                win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

                # Determine status based on last signal
                now = int(time.time())
                is_online = last_signal and (now - last_signal) < 3600  # Active in last hour

                return {
                    "signals_24h": total or 0,
                    "win_rate": round(win_rate, 1),
                    "avg_confidence": round(avg_conf or 0, 1),
                    "last_signal": last_signal or 0,
                    "status": "online" if is_online else "offline",
                    "updated_at": now,
                }

            return None

        except Exception as e:
            print(f"❌ Error getting stats for {gen_id}: {e}")
            return None

    def sync_to_firestore(self):
        """Sync all generator stats to Firestore"""
        try:
            # Map Firestore IDs to actual pattern prefixes in database
            generators = {
                "ELITE_GUARD": ["LIQUIDITY_SWEEP", "BB_SCALP", "EMA_RSI_BB", "KALMAN_"],
                "RAPIDPULSE": ["PULSE_V3_"],
                "APEX_SENTINEL": ["APEX_ENGULFING"],
            }

            for gen_id, pattern_prefixes in generators.items():
                stats = self.get_generator_stats_by_patterns(gen_id, pattern_prefixes)

                if stats:
                    # Update Firestore
                    self.db.collection("signal_generators").document(gen_id).set(stats, merge=True)
                    print(f"✅ Synced {gen_id}: {stats['signals_24h']} signals, {stats['win_rate']}% win rate")
                else:
                    # Create default document if no stats
                    self.db.collection("signal_generators").document(gen_id).set(
                        {
                            "signals_24h": 0,
                            "win_rate": 0,
                            "avg_confidence": 0,
                            "last_signal": 0,
                            "status": "offline",
                            "updated_at": int(time.time()),
                        },
                        merge=True,
                    )
                    print(f"⚠️  {gen_id}: No stats found, created default")

        except Exception as e:
            print(f"❌ Error syncing to Firestore: {e}")

    def run(self):
        """Main loop - sync every 60 seconds"""
        print("🔄 Starting generator stats sync loop (60s interval)")

        while True:
            try:
                self.sync_to_firestore()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n⛔ Stopping generator stats sync")
                break
            except Exception as e:
                print(f"❌ Loop error: {e}")
                time.sleep(60)


if __name__ == "__main__":
    sync = GeneratorStatsSync()
    sync.run()
