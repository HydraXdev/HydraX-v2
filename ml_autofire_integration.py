#!/usr/bin/env python3
"""
ML Auto-Fire Integration Module
Connects ML optimizer with real-time auto-fire decisions
"""

import json
import logging
from typing import Dict, Tuple

from ml_autofire_optimizer import MLAutoFireOptimizer

logger = logging.getLogger(__name__)


class MLAutoFireDecisionEngine:
    def __init__(self):
        self.optimizers = {}  # user_id -> MLAutoFireOptimizer instance

    def get_optimizer(self, user_id: str) -> MLAutoFireOptimizer:
        """Get or create optimizer for user"""
        if user_id not in self.optimizers:
            self.optimizers[user_id] = MLAutoFireOptimizer(user_id)
            # Run one analysis cycle to load recent data
            self.optimizers[user_id].analyze_recent_outcomes()
        return self.optimizers[user_id]

    def should_auto_fire_with_ml(self, user_id: str, signal_data: Dict) -> Tuple[bool, str, Dict]:
        """
        Make ML-enhanced auto-fire decision
        Returns: (should_fire, reason, adjustments)
        """
        try:
            optimizer = self.get_optimizer(user_id)

            # Get ML decision
            should_fire, reason, confidence_adjustment = optimizer.should_fire_ml(signal_data)

            # Get current session performance
            session = optimizer.get_current_session()
            session_stats = optimizer.session_performance.get(session, {})

            # Get pair performance
            symbol = signal_data.get("symbol", "")
            pair_stats = optimizer.pair_performance.get(symbol, {})

            # Get pattern performance
            pattern = signal_data.get("pattern_type", "")
            pattern_stats = optimizer.pattern_performance.get(pattern, {})

            # Build adjustments dictionary
            adjustments = {
                "confidence_adjustment": confidence_adjustment,
                "dynamic_threshold": optimizer.dynamic_confidence_threshold,
                "session": session,
                "session_boost": optimizer.session_boost.get(session, 0),
                "pair_streak": pair_stats.get("streak", 0),
                "pattern_win_rate": self.calculate_win_rate(pattern_stats),
                "recent_overall_win_rate": optimizer.calculate_recent_win_rate(),
                "ml_enhanced": True,
            }

            # Log ML decision details
            logger.info(
                f"""
            🤖 ML Auto-Fire Decision for {user_id}:
            Signal: {symbol} {pattern} @ {signal_data.get('confidence', 0)}%
            Decision: {'✅ FIRE' if should_fire else '❌ SKIP'}
            Reason: {reason}
            Dynamic Threshold: {optimizer.dynamic_confidence_threshold:.1f}%
            Session: {session} (Boost: {optimizer.session_boost.get(session, 0):+d})
            Pair Streak: {pair_stats.get('streak', 0)}
            """
            )

            return should_fire, reason, adjustments

        except Exception as e:
            logger.error(f"ML decision error: {e}")
            # Fallback to standard decision
            return True, "ML unavailable, using standard rules", {}

    def calculate_win_rate(self, stats: Dict) -> float:
        """Calculate win rate from stats"""
        wins = stats.get("wins", 0)
        losses = stats.get("losses", 0)
        total = wins + losses
        if total > 0:
            return wins / total
        return 0.5

    def update_with_outcome(self, user_id: str, fire_id: str, outcome: str, pips: float = 0):
        """Update ML model with trade outcome"""
        try:
            optimizer = self.get_optimizer(user_id)

            # Get trade details
            import sqlite3

            conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT f.symbol, s.pattern_type, s.confidence
                FROM fires f
                LEFT JOIN signals s ON f.fire_id = s.signal_id
                WHERE f.fire_id = ?
            """,
                (fire_id,),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                symbol, pattern, confidence = result
                optimizer.update_performance_metrics(symbol, pattern, confidence, outcome)
                optimizer.save_state()

                logger.info(f"📈 ML updated with {outcome} for {symbol} {pattern}")

        except Exception as e:
            logger.error(f"Error updating ML with outcome: {e}")


# Global instance
ml_engine = MLAutoFireDecisionEngine()


def should_auto_fire_ml(user_id: str, signal_data: Dict) -> Tuple[bool, str, Dict]:
    """Main entry point for ML-enhanced auto-fire decisions"""
    return ml_engine.should_auto_fire_with_ml(user_id, signal_data)


def update_ml_outcome(user_id: str, fire_id: str, outcome: str, pips: float = 0):
    """Update ML with trade outcome"""
    ml_engine.update_with_outcome(user_id, fire_id, outcome, pips)
