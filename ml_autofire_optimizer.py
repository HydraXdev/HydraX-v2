#!/usr/bin/env python3
"""
ML Auto-Fire Optimizer
Real-time machine learning optimization for per-user auto-fire profiles
Learns from event bus data and continuously adjusts parameters for best odds
"""

import json
import logging
import os
import pickle
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLAutoFireOptimizer:
    def __init__(self, user_id: str = "7176191872"):
        self.user_id = user_id
        self.event_bus_db = "/root/HydraX-v2/event_bus.db"
        self.bitten_db = "/root/HydraX-v2/bitten.db"
        self.profile_db = "/root/HydraX-v2/data/auto_fire_profiles.db"

        # ML State tracking
        self.session_performance = defaultdict(lambda: {"wins": 0, "losses": 0, "total_pips": 0})
        self.pattern_performance = defaultdict(lambda: {"wins": 0, "losses": 0, "avg_confidence": 0})
        self.pair_performance = defaultdict(lambda: {"wins": 0, "losses": 0, "streak": 0})
        self.confidence_buckets = defaultdict(lambda: {"wins": 0, "losses": 0})

        # Dynamic thresholds
        self.dynamic_confidence_threshold = 80.0
        self.session_boost = {"LONDON": 0, "NY": 0, "ASIAN": 0, "OVERLAP": 0}

        # Recent performance tracking (last 20 trades per category)
        self.recent_pattern_outcomes = defaultdict(lambda: deque(maxlen=20))
        self.recent_pair_outcomes = defaultdict(lambda: deque(maxlen=20))
        self.recent_session_outcomes = defaultdict(lambda: deque(maxlen=20))

        # Real-time adjustments
        self.blocked_pairs_temporary = set()  # Pairs blocked until performance improves
        self.boosted_patterns = set()  # Patterns performing exceptionally well

        # Load saved state if exists
        self.state_file = f"/root/HydraX-v2/ml_states/autofire_{user_id}.pkl"
        self.load_state()

    def load_state(self):
        """Load previous ML state if available"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "rb") as f:
                    state = pickle.load(f)
                    self.session_performance = state.get("session_performance", self.session_performance)
                    self.pattern_performance = state.get("pattern_performance", self.pattern_performance)
                    self.pair_performance = state.get("pair_performance", self.pair_performance)
                    self.dynamic_confidence_threshold = state.get("dynamic_confidence_threshold", 80.0)
                    logger.info(f"✅ Loaded ML state for user {self.user_id}")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")

    def save_state(self):
        """Save current ML state"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            state = {
                "session_performance": dict(self.session_performance),
                "pattern_performance": dict(self.pattern_performance),
                "pair_performance": dict(self.pair_performance),
                "dynamic_confidence_threshold": self.dynamic_confidence_threshold,
                "timestamp": time.time(),
            }
            with open(self.state_file, "wb") as f:
                pickle.dump(state, f)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def get_current_session(self) -> str:
        """Determine current trading session"""
        now = datetime.utcnow()
        hour = now.hour

        # Trading sessions (UTC)
        if 7 <= hour < 9:
            return "LONDON"
        elif 9 <= hour < 12:
            return "OVERLAP"  # London/NY overlap
        elif 12 <= hour < 16:
            return "NY"
        elif 22 <= hour or hour < 7:
            return "ASIAN"
        else:
            return "NY"  # Default

    def analyze_recent_outcomes(self):
        """Analyze recent trading outcomes from event bus"""
        try:
            # Get recent trade outcomes
            conn = sqlite3.connect(self.bitten_db)
            cursor = conn.cursor()

            # Get trades from last 24 hours
            cursor.execute(
                """
                SELECT f.fire_id, f.symbol, f.status, s.pattern_type, s.confidence
                FROM fires f
                LEFT JOIN signals s ON f.fire_id = s.signal_id
                WHERE f.user_id = ?
                AND f.created_at > strftime('%s', 'now', '-24 hours')
                AND f.status IN ('FILLED', 'CLOSED', 'CLOSED_AUTO_DETECTED')
            """,
                (self.user_id,),
            )

            trades = cursor.fetchall()
            conn.close()

            # Process each trade
            for fire_id, symbol, status, pattern_type, confidence in trades:
                # Check outcome from tracking
                outcome = self.get_trade_outcome(fire_id)
                if outcome:
                    self.update_performance_metrics(symbol, pattern_type, confidence, outcome)

        except Exception as e:
            logger.error(f"Error analyzing outcomes: {e}")

    def get_trade_outcome(self, fire_id: str) -> Optional[str]:
        """Get trade outcome from comprehensive tracking"""
        try:
            with open("/root/HydraX-v2/comprehensive_tracking.jsonl", "r") as f:
                for line in f:
                    if fire_id in line:
                        data = json.loads(line)
                        return data.get("outcome")
        except:
            pass
        return None

    def update_performance_metrics(self, symbol: str, pattern: str, confidence: float, outcome: str):
        """Update ML performance metrics"""
        session = self.get_current_session()

        # Update session performance
        if outcome == "WIN":
            self.session_performance[session]["wins"] += 1
            self.pair_performance[symbol]["wins"] += 1
            self.pattern_performance[pattern]["wins"] += 1
            self.pair_performance[symbol]["streak"] = max(0, self.pair_performance[symbol]["streak"]) + 1
        else:
            self.session_performance[session]["losses"] += 1
            self.pair_performance[symbol]["losses"] += 1
            self.pattern_performance[pattern]["losses"] += 1
            self.pair_performance[symbol]["streak"] = min(0, self.pair_performance[symbol]["streak"]) - 1

        # Update confidence buckets
        bucket = int(confidence // 5) * 5  # 80-84, 85-89, etc.
        if outcome == "WIN":
            self.confidence_buckets[bucket]["wins"] += 1
        else:
            self.confidence_buckets[bucket]["losses"] += 1

        # Track recent outcomes
        self.recent_pattern_outcomes[pattern].append(1 if outcome == "WIN" else 0)
        self.recent_pair_outcomes[symbol].append(1 if outcome == "WIN" else 0)
        self.recent_session_outcomes[session].append(1 if outcome == "WIN" else 0)

    def calculate_dynamic_thresholds(self) -> Dict:
        """Calculate dynamic thresholds based on recent performance"""
        thresholds = {}

        # Pattern-specific thresholds
        for pattern, outcomes in self.recent_pattern_outcomes.items():
            if len(outcomes) >= 5:
                win_rate = sum(outcomes) / len(outcomes)
                if win_rate >= 0.7:  # 70% win rate
                    thresholds[f"pattern_{pattern}_threshold"] = 75  # Lower threshold for good patterns
                elif win_rate <= 0.3:  # 30% win rate
                    thresholds[f"pattern_{pattern}_threshold"] = 90  # Higher threshold for bad patterns
                else:
                    thresholds[f"pattern_{pattern}_threshold"] = 80

        # Pair-specific adjustments
        for pair, outcomes in self.recent_pair_outcomes.items():
            if len(outcomes) >= 5:
                win_rate = sum(outcomes) / len(outcomes)
                if win_rate <= 0.25:  # Less than 25% win rate
                    self.blocked_pairs_temporary.add(pair)
                elif win_rate >= 0.75:  # More than 75% win rate
                    thresholds[f"pair_{pair}_boost"] = -5  # Lower threshold by 5

        # Session adjustments
        current_session = self.get_current_session()
        for session, outcomes in self.recent_session_outcomes.items():
            if len(outcomes) >= 3:
                win_rate = sum(outcomes) / len(outcomes)
                if session == current_session:
                    if win_rate >= 0.6:
                        self.session_boost[session] = -3  # Lower threshold in winning sessions
                    elif win_rate <= 0.4:
                        self.session_boost[session] = 3  # Higher threshold in losing sessions

        # Global confidence adjustment based on overall performance
        total_recent = []
        for outcomes in self.recent_pair_outcomes.values():
            total_recent.extend(outcomes)

        if len(total_recent) >= 10:
            overall_win_rate = sum(total_recent) / len(total_recent)
            if overall_win_rate >= 0.65:
                self.dynamic_confidence_threshold = max(75, self.dynamic_confidence_threshold - 1)
            elif overall_win_rate <= 0.45:
                self.dynamic_confidence_threshold = min(89, self.dynamic_confidence_threshold + 1)

        return thresholds

    def should_fire_ml(self, signal_data: Dict) -> Tuple[bool, str, float]:
        """
        ML-driven decision on whether to auto-fire
        Returns: (should_fire, reason, confidence_adjustment)
        """
        symbol = signal_data.get("symbol", "")
        pattern = signal_data.get("pattern_type", "")
        confidence = signal_data.get("confidence", 0)
        session = self.get_current_session()

        # Check if pair is temporarily blocked
        if symbol in self.blocked_pairs_temporary:
            return False, f"ML: {symbol} temporarily blocked due to poor performance", 0

        # Calculate dynamic adjustments
        thresholds = self.calculate_dynamic_thresholds()

        # Get pattern-specific threshold
        pattern_threshold = thresholds.get(f"pattern_{pattern}_threshold", self.dynamic_confidence_threshold)

        # Apply session boost
        session_adjustment = self.session_boost.get(session, 0)

        # Apply pair boost if exists
        pair_boost = thresholds.get(f"pair_{symbol}_boost", 0)

        # Calculate final threshold
        final_threshold = pattern_threshold + session_adjustment + pair_boost

        # Check recent streak for this pair
        if symbol in self.pair_performance:
            streak = self.pair_performance[symbol]["streak"]
            if streak >= 3:  # 3+ wins in a row
                final_threshold -= 2  # Lower threshold for hot pairs
            elif streak <= -3:  # 3+ losses in a row
                final_threshold += 5  # Higher threshold for cold pairs

        # Make decision
        if confidence >= final_threshold:
            # Calculate confidence adjustment for position sizing
            confidence_adjustment = 0

            # Boost confidence for exceptional patterns
            if pattern in self.boosted_patterns:
                confidence_adjustment += 5

            # Adjust based on session performance
            if session in self.session_performance:
                sess_data = self.session_performance[session]
                if sess_data["wins"] + sess_data["losses"] > 0:
                    sess_win_rate = sess_data["wins"] / (sess_data["wins"] + sess_data["losses"])
                    if sess_win_rate > 0.6:
                        confidence_adjustment += 2

            return True, f"ML: Approved at {final_threshold:.1f}% threshold (session: {session})", confidence_adjustment
        else:
            return False, f"ML: Below dynamic threshold {final_threshold:.1f}% (session: {session})", 0

    def update_profile_realtime(self):
        """Update the user's auto-fire profile based on ML analysis"""
        try:
            # Prepare blocked pairs list (excluding temporarily blocked)
            blocked_pairs = list(self.blocked_pairs_temporary)

            # Identify best performing patterns
            allowed_patterns = []
            for pattern, data in self.pattern_performance.items():
                total = data["wins"] + data["losses"]
                if total >= 5:  # Minimum sample size
                    win_rate = data["wins"] / total
                    if win_rate >= 0.5:  # 50% or better
                        allowed_patterns.append(pattern)

            # Update profile in database
            conn = sqlite3.connect(self.profile_db)
            cursor = conn.cursor()

            # Update confidence range
            cursor.execute(
                """
                UPDATE auto_fire_profiles
                SET min_confidence = ?,
                    max_confidence = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """,
                (self.dynamic_confidence_threshold, 89.0, self.user_id),
            )

            # Store ML adjustments as JSON in notes field
            ml_data = {
                "blocked_pairs": blocked_pairs,
                "session_boosts": dict(self.session_boost),
                "dynamic_threshold": self.dynamic_confidence_threshold,
                "last_update": datetime.utcnow().isoformat(),
            }

            cursor.execute(
                """
                UPDATE auto_fire_profiles
                SET notes = ?
                WHERE user_id = ?
            """,
                (json.dumps(ml_data), self.user_id),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"✅ Updated profile - Threshold: {self.dynamic_confidence_threshold:.1f}%, Blocked: {blocked_pairs}"
            )

        except Exception as e:
            logger.error(f"Error updating profile: {e}")

    def run_continuous_optimization(self):
        """Main loop for continuous ML optimization"""
        logger.info(f"🚀 ML Auto-Fire Optimizer started for user {self.user_id}")

        while True:
            try:
                # Analyze recent outcomes
                self.analyze_recent_outcomes()

                # Calculate dynamic thresholds
                thresholds = self.calculate_dynamic_thresholds()

                # Update profile in real-time
                self.update_profile_realtime()

                # Save state
                self.save_state()

                # Log current status
                logger.info(
                    f"""
                📊 ML Status Update:
                - Dynamic Threshold: {self.dynamic_confidence_threshold:.1f}%
                - Session: {self.get_current_session()} (Boost: {self.session_boost[self.get_current_session()]:+d})
                - Blocked Pairs: {list(self.blocked_pairs_temporary)}
                - Recent Win Rate: {self.calculate_recent_win_rate():.1%}
                """
                )

                # Sleep for 30 seconds before next optimization
                time.sleep(30)

            except Exception as e:
                logger.error(f"Optimization error: {e}")
                time.sleep(60)

    def calculate_recent_win_rate(self) -> float:
        """Calculate overall recent win rate"""
        all_outcomes = []
        for outcomes in self.recent_pair_outcomes.values():
            all_outcomes.extend(outcomes)

        if all_outcomes:
            return sum(all_outcomes) / len(all_outcomes)
        return 0.5


if __name__ == "__main__":
    import sys

    user_id = sys.argv[1] if len(sys.argv) > 1 else "7176191872"

    optimizer = MLAutoFireOptimizer(user_id)
    optimizer.run_continuous_optimization()
