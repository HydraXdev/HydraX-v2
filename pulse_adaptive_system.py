#!/usr/bin/env python3
"""
Pulse Adaptive Threshold System
================================
Auto-optimizes volume threshold based on real signal outcomes.
Persists across restarts, self-learning from every fired signal.

Author: Claude Code (User Request)
Date: October 21, 2025
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime
import sqlite3
import pickle
import numpy as np

# Paths
OUTCOMES_FILE = "/root/HydraX-v2/pulse_outcomes.jsonl"
STATE_FILE = "/root/HydraX-v2/pulse_adaptive_state.pkl"
DB_PATH = "/root/HydraX-v2/bitten.db"

# Configuration
MIN_SIGNALS_FOR_OPTIMIZATION = 50  # Optimize every 50 signals
VOLUME_BUCKETS = [
    (1.0, 1.1, "1.0-1.1x"),
    (1.1, 1.2, "1.1-1.2x"),
    (1.2, 1.3, "1.2-1.3x"),
    (1.3, 2.0, "1.3+x")
]

class PulseAdaptiveSystem:
    """Self-optimizing threshold system with persistent state."""

    def __init__(self):
        self.outcomes = []
        self.current_threshold = 1.05  # Starting point (lowered from 1.1 for better signal generation)
        self.optimization_count = 0
        self.last_optimization_time = time.time()
        self.confidence_calibration = {}

        # Load persistent state
        self._load_state()

    def _load_state(self):
        """Load state from disk (restart-resistant)."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'rb') as f:
                    state = pickle.load(f)
                    self.current_threshold = state.get('threshold', 1.1)
                    self.optimization_count = state.get('opt_count', 0)
                    self.last_optimization_time = state.get('last_opt_time', time.time())
                    self.confidence_calibration = state.get('calibration', {})
                print(f"✅ Loaded adaptive state: threshold={self.current_threshold:.2f}x, {self.optimization_count} optimizations")
            except Exception as e:
                print(f"⚠️ Failed to load state: {e}, using defaults")

        # Load outcomes from JSONL
        if os.path.exists(OUTCOMES_FILE):
            try:
                with open(OUTCOMES_FILE, 'r') as f:
                    self.outcomes = [json.loads(line) for line in f]
                print(f"✅ Loaded {len(self.outcomes)} historical outcomes")
            except Exception as e:
                print(f"⚠️ Failed to load outcomes: {e}")

    def _save_state(self):
        """Save state to disk (persistent across restarts)."""
        state = {
            'threshold': self.current_threshold,
            'opt_count': self.optimization_count,
            'last_opt_time': self.last_optimization_time,
            'calibration': self.confidence_calibration
        }

        try:
            with open(STATE_FILE, 'wb') as f:
                pickle.dump(state, f)
            print(f"💾 Saved adaptive state: threshold={self.current_threshold:.2f}x")
        except Exception as e:
            print(f"❌ Failed to save state: {e}")

    def track_signal(self, signal_data):
        """
        Track a signal that was fired.

        Args:
            signal_data: {
                'signal_id': 'PULSE_EURUSD_123',
                'symbol': 'EURUSD',
                'vol_ratio': 1.15,
                'confidence': 78.5,
                'entry': 1.2000,
                'tp': 1.2015,
                'sl': 1.1985,
                'timestamp': 1761033000
            }
        """
        # Save to JSONL immediately (append-only, crash-resistant)
        try:
            with open(OUTCOMES_FILE, 'a') as f:
                f.write(json.dumps(signal_data) + '\n')
            print(f"📝 Tracked signal: {signal_data['signal_id']}")
        except Exception as e:
            print(f"❌ Failed to track signal: {e}")

    def update_outcome(self, signal_id, outcome, profit_pips, duration_min):
        """
        Update signal outcome when TP/SL hit.

        Args:
            signal_id: Signal identifier
            outcome: 'WIN' or 'LOSS'
            profit_pips: Profit in pips (positive for win, negative for loss)
            duration_min: Duration until TP/SL in minutes
        """
        # Find signal in outcomes
        for i, sig in enumerate(self.outcomes):
            if sig.get('signal_id') == signal_id:
                sig['outcome'] = outcome
                sig['profit_pips'] = profit_pips
                sig['duration_min'] = duration_min
                sig['completed_at'] = time.time()

                # Update JSONL file (rewrite entire file for simplicity)
                try:
                    with open(OUTCOMES_FILE, 'w') as f:
                        for outcome_data in self.outcomes:
                            f.write(json.dumps(outcome_data) + '\n')
                    print(f"✅ Updated outcome: {signal_id} = {outcome} ({profit_pips:+.1f} pips)")
                except Exception as e:
                    print(f"❌ Failed to update outcome: {e}")

                # Check if we should optimize
                completed_count = sum(1 for s in self.outcomes if 'outcome' in s)
                if completed_count >= MIN_SIGNALS_FOR_OPTIMIZATION and \
                   completed_count % MIN_SIGNALS_FOR_OPTIMIZATION == 0:
                    self.optimize_threshold()

                break

    def optimize_threshold(self):
        """Auto-optimize volume threshold based on outcomes."""
        print("\n" + "="*60)
        print("🔬 ADAPTIVE OPTIMIZATION STARTING")
        print("="*60)

        # Get completed signals only
        completed = [s for s in self.outcomes if 'outcome' in s]

        if len(completed) < MIN_SIGNALS_FOR_OPTIMIZATION:
            print(f"⏳ Need {MIN_SIGNALS_FOR_OPTIMIZATION} signals, have {len(completed)}")
            return

        # Bucket by volume ratio
        buckets = defaultdict(list)
        for sig in completed:
            vol = sig.get('vol_ratio', 1.0)
            for min_vol, max_vol, name in VOLUME_BUCKETS:
                if min_vol <= vol < max_vol:
                    buckets[name].append(sig)
                    break

        # Calculate metrics per bucket
        best_expectancy = -999
        best_threshold = self.current_threshold

        print("\n📊 VOLUME BUCKET ANALYSIS:")
        print("-" * 60)

        for bucket_name in sorted(buckets.keys()):
            signals = buckets[bucket_name]

            if len(signals) < 10:
                print(f"{bucket_name}: Only {len(signals)} signals (need 10+)")
                continue

            wins = sum(1 for s in signals if s.get('outcome') == 'WIN')
            wr = wins / len(signals)

            # Calculate expectancy
            win_pips = [s['profit_pips'] for s in signals if s.get('outcome') == 'WIN']
            loss_pips = [abs(s['profit_pips']) for s in signals if s.get('outcome') == 'LOSS']

            avg_win = np.mean(win_pips) if win_pips else 0
            avg_loss = np.mean(loss_pips) if loss_pips else 0

            expectancy = (wr * avg_win) - ((1 - wr) * avg_loss)

            print(f"{bucket_name}: {wr:.1%} WR | {len(signals)} signals | "
                  f"Exp: {expectancy:+.2f} pips/trade | "
                  f"Avg Win: {avg_win:.1f} | Avg Loss: {avg_loss:.1f}")

            # Track best bucket
            if expectancy > best_expectancy and len(signals) >= 10:
                best_expectancy = expectancy
                # Use midpoint of bucket as new threshold
                for min_vol, max_vol, name in VOLUME_BUCKETS:
                    if name == bucket_name:
                        best_threshold = (min_vol + max_vol) / 2
                        break

        # Apply optimization
        old_threshold = self.current_threshold

        # Smooth adjustment (don't jump too much)
        if abs(best_threshold - old_threshold) > 0.15:
            # Cap adjustment to ±0.15 per optimization
            if best_threshold > old_threshold:
                self.current_threshold = old_threshold + 0.15
            else:
                self.current_threshold = old_threshold - 0.15
        else:
            self.current_threshold = best_threshold

        # Round to 2 decimals
        self.current_threshold = round(self.current_threshold, 2)

        print("\n" + "="*60)
        print(f"🎯 OPTIMIZATION RESULT:")
        print(f"   Old Threshold: {old_threshold:.2f}x")
        print(f"   New Threshold: {self.current_threshold:.2f}x")
        print(f"   Best Expectancy: {best_expectancy:+.2f} pips/trade")
        print("="*60 + "\n")

        self.optimization_count += 1
        self.last_optimization_time = time.time()

        # Save state
        self._save_state()

        # Also calibrate confidence
        self.calibrate_confidence(completed)

    def calibrate_confidence(self, completed_signals):
        """Calibrate confidence scores to match actual win rates."""
        print("\n📏 CONFIDENCE CALIBRATION:")
        print("-" * 60)

        # Bucket by confidence
        conf_buckets = {
            '70-75%': [],
            '75-80%': [],
            '80-85%': [],
            '85-90%': [],
            '90-95%': [],
            '95-100%': []
        }

        for sig in completed_signals:
            conf = sig.get('confidence', 0)

            if 70 <= conf < 75:
                conf_buckets['70-75%'].append(sig)
            elif 75 <= conf < 80:
                conf_buckets['75-80%'].append(sig)
            elif 80 <= conf < 85:
                conf_buckets['80-85%'].append(sig)
            elif 85 <= conf < 90:
                conf_buckets['85-90%'].append(sig)
            elif 90 <= conf < 95:
                conf_buckets['90-95%'].append(sig)
            elif conf >= 95:
                conf_buckets['95-100%'].append(sig)

        self.confidence_calibration = {}

        for bucket_name, signals in conf_buckets.items():
            if len(signals) < 5:
                continue

            wins = sum(1 for s in signals if s.get('outcome') == 'WIN')
            actual_wr = wins / len(signals)
            expected_wr = float(bucket_name.split('-')[0]) / 100

            # Calculate calibration factor
            calibration_factor = actual_wr / expected_wr if expected_wr > 0 else 1.0
            self.confidence_calibration[bucket_name] = calibration_factor

            status = "✅" if abs(actual_wr - expected_wr) < 0.10 else "⚠️"
            print(f"{status} {bucket_name}: Expected {expected_wr:.0%}, Actual {actual_wr:.0%} "
                  f"({len(signals)} signals) | Factor: {calibration_factor:.3f}")

        print("-" * 60 + "\n")

    def get_current_threshold(self):
        """Get current optimized threshold."""
        return self.current_threshold

    def apply_confidence_calibration(self, raw_confidence):
        """Apply calibration to raw confidence score."""
        # Find appropriate bucket
        if 70 <= raw_confidence < 75:
            bucket = '70-75%'
        elif 75 <= raw_confidence < 80:
            bucket = '75-80%'
        elif 80 <= raw_confidence < 85:
            bucket = '80-85%'
        elif 85 <= raw_confidence < 90:
            bucket = '85-90%'
        elif 90 <= raw_confidence < 95:
            bucket = '90-95%'
        else:
            bucket = '95-100%'

        # Apply calibration factor
        factor = self.confidence_calibration.get(bucket, 1.0)
        calibrated = raw_confidence * factor

        # Cap at 95% (never 100%)
        return min(calibrated, 95.0)

    def get_stats(self):
        """Get system statistics."""
        completed = [s for s in self.outcomes if 'outcome' in s]

        if not completed:
            return {
                'total_signals': len(self.outcomes),
                'completed': 0,
                'win_rate': 0,
                'current_threshold': self.current_threshold,
                'optimizations': self.optimization_count
            }

        wins = sum(1 for s in completed if s.get('outcome') == 'WIN')
        wr = wins / len(completed)

        return {
            'total_signals': len(self.outcomes),
            'completed': len(completed),
            'pending': len(self.outcomes) - len(completed),
            'win_rate': wr,
            'current_threshold': self.current_threshold,
            'optimizations': self.optimization_count,
            'last_optimization': datetime.fromtimestamp(self.last_optimization_time).strftime('%Y-%m-%d %H:%M:%S')
        }


# Global instance (singleton)
_adaptive_system = None

def get_adaptive_system():
    """Get or create adaptive system instance."""
    global _adaptive_system
    if _adaptive_system is None:
        _adaptive_system = PulseAdaptiveSystem()
    return _adaptive_system


# CLI for testing/monitoring
if __name__ == "__main__":
    import sys

    system = get_adaptive_system()

    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            stats = system.get_stats()
            print("\n📊 PULSE ADAPTIVE SYSTEM STATS")
            print("="*60)
            for key, value in stats.items():
                print(f"{key}: {value}")
            print("="*60)

        elif sys.argv[1] == "optimize":
            print("🔬 Running manual optimization...")
            system.optimize_threshold()

        elif sys.argv[1] == "reset":
            confirm = input("⚠️ Reset all adaptive state? (yes/no): ")
            if confirm.lower() == 'yes':
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
                print("✅ State reset. Restart Pulse v3 to apply.")
    else:
        print("Usage:")
        print("  python3 pulse_adaptive_system.py stats     - Show statistics")
        print("  python3 pulse_adaptive_system.py optimize  - Run manual optimization")
        print("  python3 pulse_adaptive_system.py reset     - Reset adaptive state")
