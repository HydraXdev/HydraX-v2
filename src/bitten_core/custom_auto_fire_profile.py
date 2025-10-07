"""
Custom Auto-Fire Profile for User 7176191872
==============================================
Optimized based on 12-hour performance analysis
Updated: September 16, 2025

This module provides personalized auto-fire filtering based on actual
performance data, allowing fine-tuned control over which signals trigger
automatic execution.
"""

from datetime import datetime
from typing import Dict, Tuple, Optional

class CustomAutoFireProfile:
    """
    Personalized auto-fire profile that learns from actual trading performance
    and adapts to optimize win rates and profitability.
    """

    def __init__(self, user_id: str = "7176191872"):
        self.user_id = user_id
        self.last_update = datetime.now()

        # Based on 12-hour analysis (September 16, 2025)
        # These showed 70%+ win rate in 80-89% confidence range
        self.allowed_pairs = {
            'USDCNH',    # 100% win rate (11W/0L) in auto range
            'XAUUSD',    # 100% win rate (6W/0L) in auto range
            'USDJPY',    # 100% win rate (5W/0L) in auto range
            'EURJPY',    # 100% win rate (2W/0L) in auto range
            'GBPCAD',    # 100% win rate (3W/0L) in auto range
            'NZDUSD',    # 100% win rate (2W/0L) in auto range
            'EURAUD',    # 100% win rate (2W/0L) in auto range
            # 'GBPUSD',  # 75% win rate (3W/1L) - borderline, monitoring
        }

        # Pairs to block from auto-fire (but still signal)
        self.blocked_pairs = {
            'GBPJPY',    # 50% in 12h, 40% in 24h - needs optimization
            'GBPUSD',    # 55.6% in 12h, 50% in 24h - inconsistent
            'EURUSD',    # 42.9% in 24h - poor performance
            'EURAUD',    # Conflicting data, needs review
        }

        # Patterns with proven performance
        self.allowed_patterns = {
            'KALMAN_QUICKFIRE',  # 76.7% win rate in 12h
            'BB_SCALP',          # 66.7% win rate in 12h
        }

        # Patterns to block from auto-fire
        self.blocked_patterns = {
            'FAIR_VALUE_GAP_FILL',    # 25% win rate - major issue
            'ORDER_BLOCK_BOUNCE',     # 53.8% win rate - needs tuning
            'LIQUIDITY_SWEEP_REVERSAL',  # Limited data, poor performance
        }

        # Optimal confidence ranges based on analysis
        self.confidence_ranges = {
            'primary': (80, 84),     # Best performance zone
            'secondary': (75, 79),   # Good performance, can enable if needed
            'avoid': (85, 89),       # Currently underperforming (51.1% WR)
        }

        # Track performance for continuous optimization
        self.performance_stats = {
            'total_signals': 0,
            'auto_fired': 0,
            'wins': 0,
            'losses': 0,
            'last_reset': datetime.now()
        }

    def should_auto_fire(self, signal_data: Dict) -> Tuple[bool, str]:
        """
        Determine if a signal should trigger auto-fire based on custom profile.

        Args:
            signal_data: Dictionary containing signal information
                - symbol: Trading pair
                - pattern_type: Pattern that generated signal
                - confidence: Confidence score (0-100)
                - signal_id: Unique identifier

        Returns:
            Tuple of (should_fire: bool, reason: str)
        """
        symbol = signal_data.get('symbol', '')
        pattern = signal_data.get('pattern_type', '')
        confidence = float(signal_data.get('confidence', 0))

        # Check if pair is blocked
        if symbol in self.blocked_pairs:
            return False, f"Pair {symbol} blocked (poor performance)"

        # Check if pattern is blocked
        if pattern in self.blocked_patterns:
            return False, f"Pattern {pattern} blocked (low win rate)"

        # Check if pair is in allowed list
        if symbol not in self.allowed_pairs:
            return False, f"Pair {symbol} not in allowed list"

        # Check if pattern is in allowed list
        if pattern not in self.allowed_patterns:
            return False, f"Pattern {pattern} not in allowed list"

        # Check confidence range
        primary_min, primary_max = self.confidence_ranges['primary']
        secondary_min, secondary_max = self.confidence_ranges['secondary']

        if primary_min <= confidence <= primary_max:
            return True, f"Optimal range {primary_min}-{primary_max}%"

        # Optional: Enable secondary range if needed for volume
        # if secondary_min <= confidence <= secondary_max:
        #     return True, f"Secondary range {secondary_min}-{secondary_max}%"

        # Avoid the problematic 85-89% range
        avoid_min, avoid_max = self.confidence_ranges['avoid']
        if avoid_min <= confidence <= avoid_max:
            return False, f"Avoiding {avoid_min}-{avoid_max}% range (underperforming)"

        return False, f"Confidence {confidence}% outside optimal ranges"

    def update_performance(self, signal_id: str, outcome: str):
        """
        Update performance statistics for continuous learning.

        Args:
            signal_id: The signal that was auto-fired
            outcome: 'WIN' or 'LOSS'
        """
        if outcome == 'WIN':
            self.performance_stats['wins'] += 1
        elif outcome == 'LOSS':
            self.performance_stats['losses'] += 1

        self.performance_stats['total_signals'] += 1

    def get_win_rate(self) -> Optional[float]:
        """Calculate current win rate for custom profile."""
        total = self.performance_stats['wins'] + self.performance_stats['losses']
        if total == 0:
            return None
        return (self.performance_stats['wins'] / total) * 100

    def get_profile_summary(self) -> Dict:
        """Get a summary of the current profile settings."""
        return {
            'user_id': self.user_id,
            'allowed_pairs': list(self.allowed_pairs),
            'blocked_pairs': list(self.blocked_pairs),
            'allowed_patterns': list(self.allowed_patterns),
            'blocked_patterns': list(self.blocked_patterns),
            'confidence_ranges': self.confidence_ranges,
            'current_win_rate': self.get_win_rate(),
            'stats': self.performance_stats,
            'last_update': self.last_update.isoformat()
        }

    def should_update_profile(self) -> bool:
        """
        Determine if profile should be updated based on new data.
        Typically every 12 hours or after 50+ signals.
        """
        hours_since_update = (datetime.now() - self.last_update).total_seconds() / 3600
        signals_since_update = self.performance_stats['total_signals']

        return hours_since_update >= 12 or signals_since_update >= 50


# Global instance for user 7176191872
commander_profile = CustomAutoFireProfile("7176191872")


def should_auto_fire_custom(signal_data: Dict, user_id: str = "7176191872") -> Tuple[bool, str]:
    """
    Main entry point for custom auto-fire decisions.

    This function can be integrated into webapp_server_optimized.py
    to override standard auto-fire logic for specific users.
    """
    if user_id != "7176191872":
        return True, "No custom profile, using standard rules"

    return commander_profile.should_auto_fire(signal_data)