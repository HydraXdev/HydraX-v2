#!/usr/bin/env python3
"""
Firebase Outcome Tracker - Bridges BITTEN signal outcomes to Firestore

Listens to the definitive_signal_tracker output and updates Firebase with outcomes.
This ensures Firestore stays in sync with the BITTEN tracking system.

Architecture:
- Tails unified_tracking.jsonl for new outcomes
- Updates Firestore /signals/{signalId} with outcome data
- Triggers metrics rollup updates
"""

import os
import sys
import time
import json
from pathlib import Path

# Set Firebase credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/root/bitten-firebase-sa.json'

from firebase_bridge import update_signal_outcome

# Tracking file location
TRACKING_FILE = Path('/root/HydraX-v2/unified_tracking.jsonl')

def tail_outcomes():
    """
    Tail unified_tracking.jsonl and update Firestore with outcomes
    """
    print("🔥 Firebase Outcome Tracker Started")
    print(f"📁 Watching: {TRACKING_FILE}")
    print("=" * 60)

    # Keep track of processed signals to avoid duplicates
    processed = set()

    # Read existing outcomes first (in case we're starting after signals already completed)
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    signal_id = data.get('signal_id')
                    outcome = data.get('outcome')

                    if signal_id and outcome and signal_id not in processed:
                        # Update Firestore
                        exit_price = data.get('exit_price', 0)
                        pnl_pips = data.get('pnl_pips', 0)

                        update_signal_outcome(signal_id, outcome, exit_price, pnl_pips)
                        processed.add(signal_id)

                except json.JSONDecodeError:
                    continue

    print(f"✅ Loaded {len(processed)} existing outcomes")
    print("👂 Listening for new outcomes...")

    # Now tail for new outcomes
    file_position = TRACKING_FILE.stat().st_size if TRACKING_FILE.exists() else 0

    while True:
        try:
            if not TRACKING_FILE.exists():
                time.sleep(5)
                continue

            current_size = TRACKING_FILE.stat().st_size

            if current_size < file_position:
                # File was truncated/rotated
                file_position = 0

            if current_size > file_position:
                # New data available
                with open(TRACKING_FILE, 'r') as f:
                    f.seek(file_position)

                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            signal_id = data.get('signal_id')
                            outcome = data.get('outcome')

                            if signal_id and outcome and signal_id not in processed:
                                # New outcome detected
                                exit_price = data.get('exit_price', 0)
                                pnl_pips = data.get('pnl_pips', 0)

                                print(f"\n🎯 New outcome: {signal_id} → {outcome} ({pnl_pips:+.1f} pips)")

                                update_signal_outcome(signal_id, outcome, exit_price, pnl_pips)
                                processed.add(signal_id)

                        except json.JSONDecodeError:
                            continue

                    file_position = f.tell()

            # Sleep before next check
            time.sleep(2)

        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown signal received")
            break
        except Exception as e:
            print(f"❌ Error in tail loop: {e}")
            time.sleep(5)

    print("=" * 60)
    print(f"📊 Total outcomes processed: {len(processed)}")
    print("🔒 Firebase Outcome Tracker stopped")


if __name__ == "__main__":
    tail_outcomes()
