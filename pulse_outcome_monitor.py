#!/usr/bin/env python3
"""
Pulse Outcome Monitor
=====================
Monitors signals table and updates adaptive system when TP/SL hit.
Completes the feedback loop for self-learning.

Author: Claude Code
Date: October 21, 2025
"""

import sqlite3
import time
import json
from datetime import datetime
from pulse_adaptive_system import get_adaptive_system

DB_PATH = "/root/HydraX-v2/bitten.db"
CHECK_INTERVAL = 30  # Check every 30 seconds

def calculate_pips(symbol, price_diff):
    """Calculate pips from price difference."""
    if 'JPY' in symbol:
        return price_diff * 100  # JPY pairs: 0.01 = 1 pip
    else:
        return price_diff * 10000  # Others: 0.0001 = 1 pip

def monitor_outcomes():
    """Monitor signals table for completed Pulse v3 signals."""
    adaptive_system = get_adaptive_system()
    processed_signals = set()

    print("=" * 60)
    print("🔍 PULSE OUTCOME MONITOR STARTING")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Check Interval: {CHECK_INTERVAL}s")
    print("=" * 60)

    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Find completed Pulse v3 signals with outcomes
            # Note: Using only columns that exist in signals table
            query = """
                SELECT
                    signal_id,
                    symbol,
                    direction,
                    entry_price,
                    tp,
                    sl,
                    outcome,
                    pips_result,
                    created_at,
                    resolution_time
                FROM signals
                WHERE pattern_type LIKE '%PULSE_V3%'
                  AND outcome IN ('WIN', 'LOSS')
                  AND signal_id NOT IN ({})
                ORDER BY created_at DESC
                LIMIT 50
            """.format(','.join(['?' for _ in processed_signals]) if processed_signals else '""')

            params = tuple(processed_signals) if processed_signals else ()
            cursor.execute(query, params)

            rows = cursor.fetchall()

            for row in rows:
                signal_id, symbol, direction, entry, tp, sl, outcome, pips_result, created_at, resolution_time = row

                # Skip if already processed
                if signal_id in processed_signals:
                    continue

                # Use pips_result from database if available
                if pips_result is not None:
                    profit_pips = pips_result
                else:
                    # Estimate based on outcome
                    if outcome == 'WIN':
                        profit_pips = calculate_pips(symbol, abs(tp - entry))
                    else:
                        profit_pips = -calculate_pips(symbol, abs(entry - sl))

                # Calculate duration from resolution_time (already in minutes or seconds)
                duration_min = resolution_time / 60 if resolution_time and resolution_time > 1000 else (resolution_time or 0)

                # Update adaptive system
                print(f"\n📊 Processing outcome: {signal_id}")
                print(f"   Symbol: {symbol} | Direction: {direction}")
                print(f"   Outcome: {outcome} | Profit: {profit_pips:+.1f} pips")
                print(f"   Duration: {duration_min:.1f} min")

                try:
                    adaptive_system.update_outcome(
                        signal_id=signal_id,
                        outcome=outcome,
                        profit_pips=profit_pips,
                        duration_min=duration_min
                    )

                    # Mark as processed
                    processed_signals.add(signal_id)

                except Exception as e:
                    print(f"❌ Error updating outcome: {e}")

            conn.close()

            # Clean old processed signals (keep last 1000)
            if len(processed_signals) > 1000:
                processed_signals = set(list(processed_signals)[-1000:])

            # Show stats periodically
            if int(time.time()) % 300 == 0:  # Every 5 minutes
                stats = adaptive_system.get_stats()
                print("\n" + "=" * 60)
                print("📊 ADAPTIVE SYSTEM STATS")
                print("-" * 60)
                print(f"Total Signals: {stats['total_signals']}")
                print(f"Completed: {stats['completed']}")
                print(f"Win Rate: {stats['win_rate']:.1%}")
                print(f"Current Threshold: {stats['current_threshold']:.2f}x")
                print(f"Optimizations: {stats['optimizations']}")
                print("=" * 60 + "\n")

        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                print(f"⚠️ Database locked, retrying...")
                time.sleep(1)
            else:
                print(f"❌ Database error: {e}")
                time.sleep(10)

        except KeyboardInterrupt:
            print("\n⏹️ Outcome monitor stopped by user")
            break

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

        # Wait before next check
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_outcomes()
