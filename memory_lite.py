#!/usr/bin/env python3
"""
BITTEN Memory-Lite System
Short-term memory with hysteresis to prevent whipsaws and improve signal quality.

Based on Grok's proposal with tuned parameters for forex scalping.
Integrates between pattern detection and ML confidence checks.
"""

import numpy as np
import pandas as pd
from typing import Optional


class MemoryLite:
    """
    Memory-Lite filter for signal generators.

    Tracks recent price action and last trade outcome to provide
    bias scoring with hysteresis threshold to prevent whipsaws.
    """

    def __init__(self, window_size: int = 15, threshold: float = 0.0004):
        """
        Initialize Memory-Lite system.

        Args:
            window_size: Number of bars to look back (default: 15)
            threshold: Hysteresis threshold for bias (default: 0.0004)
        """
        self.N = window_size
        self.T = threshold

        # State tracking per symbol
        self.last_action = {}  # 1=long, -1=short, 0=neutral
        self.last_pnl_pct = {}  # Last trade PnL percentage
        self.signal_count = {}  # Number of signals generated
        self.filter_count = {}  # Number of signals filtered

    def calculate_bias(
        self,
        df: pd.DataFrame,
        symbol: str,
        i: int = -1
    ) -> float:
        """
        Calculate memory bias score for given bar.

        Args:
            df: DataFrame with OHLC + indicators (must have: close, rsi, atr)
            symbol: Trading pair symbol
            i: Bar index (-1 for latest)

        Returns:
            Bias score (positive=bullish, negative=bearish, near-zero=neutral)
        """
        # Use last bar if index not specified
        if i == -1:
            i = len(df) - 1

        # Need minimum bars
        if i < self.N or len(df) < self.N + 1:
            return 0.0

        # Required columns
        if not all(col in df.columns for col in ['close', 'rsi', 'atr']):
            return 0.0

        # Extract window
        window = df.iloc[i-self.N:i]

        # Calculate return momentum
        returns = window['close'].pct_change().fillna(0)
        avg_return = returns.mean()

        # RSI slope (momentum direction)
        rsi_current = df['rsi'].iloc[i]
        rsi_3bars_ago = df['rsi'].iloc[max(0, i-3)]
        rsi_slope = rsi_current - rsi_3bars_ago

        # ATR normalization (volatility adjustment)
        atr_current = df['atr'].iloc[i]
        close_current = df['close'].iloc[i]
        atr_norm = atr_current / close_current if close_current != 0 else 0.01

        # Prevent division by zero
        if atr_norm == 0:
            atr_norm = 0.01

        # Base score: return momentum * RSI direction / volatility
        score = (avg_return * rsi_slope) / atr_norm

        # Initialize state for new symbol
        if symbol not in self.last_action:
            self.last_action[symbol] = 0
            self.last_pnl_pct[symbol] = 0
            self.signal_count[symbol] = 0
            self.filter_count[symbol] = 0

        # Post-loss cooldown (reduce aggression after losing trade)
        last_pnl = self.last_pnl_pct[symbol]
        if last_pnl < -0.01:  # Lost >1%
            score *= 0.8

        # Hysteresis: make it harder to reverse position
        last_action = self.last_action[symbol]

        if last_action == 1 and score < 0:  # Was long, now bearish
            # If barely bearish (within 1.5x threshold), dampen signal
            if abs(score) < self.T * 1.5:
                score *= 0.7
        elif last_action == -1 and score > 0:  # Was short, now bullish
            # If barely bullish (within 1.5x threshold), dampen signal
            if abs(score) < self.T * 1.5:
                score *= 0.7

        return score

    def should_fire(
        self,
        df: pd.DataFrame,
        symbol: str,
        direction: str,
        confidence: float,
        i: int = -1
    ) -> tuple[bool, float, str]:
        """
        Decide if signal should fire based on memory bias.

        Args:
            df: DataFrame with OHLC + indicators
            symbol: Trading pair symbol
            direction: "BUY" or "SELL"
            confidence: Pattern confidence (0-100)
            i: Bar index (-1 for latest)

        Returns:
            (should_fire, adjusted_confidence, reason)
        """
        # 🚨 MEMORY FILTER BYPASSED FOR SIGNAL FLOW VERIFICATION 🚨
        # TEMPORARY BYPASS - FORCE ALL SIGNALS TO PASS
        return True, confidence, "MEMORY FILTER BYPASSED"

        # Calculate bias
        bias = self.calculate_bias(df, symbol, i)

        # Initialize stats
        if symbol not in self.signal_count:
            self.signal_count[symbol] = 0
            self.filter_count[symbol] = 0

        # Increment signal counter
        self.signal_count[symbol] += 1

        # Direction numeric mapping
        dir_numeric = 1 if direction == "BUY" else -1

        # Check alignment
        if dir_numeric == 1 and bias < -self.T:
            # Wants to buy but memory is bearish
            self.filter_count[symbol] += 1
            return False, confidence, f"Memory bearish (bias={bias:.6f})"

        elif dir_numeric == -1 and bias > self.T:
            # Wants to sell but memory is bullish
            self.filter_count[symbol] += 1
            return False, confidence, f"Memory bullish (bias={bias:.6f})"

        # Signal aligned with memory
        # Boost confidence if strongly aligned
        adjusted_conf = confidence
        if abs(bias) > self.T * 2:
            boost = min(5, abs(bias) * 1000)  # Up to +5% confidence boost
            adjusted_conf = min(100, confidence + boost)
            reason = f"Memory aligned (bias={bias:.6f}, boost=+{boost:.1f}%)"
        else:
            reason = f"Memory neutral (bias={bias:.6f})"

        return True, adjusted_conf, reason

    def update_state(
        self,
        symbol: str,
        action: int,
        pnl_pct: Optional[float] = None
    ):
        """
        Update memory state after trade execution.

        Args:
            symbol: Trading pair symbol
            action: 1=long, -1=short, 0=flat
            pnl_pct: Trade PnL percentage (if trade closed)
        """
        self.last_action[symbol] = action

        if pnl_pct is not None:
            self.last_pnl_pct[symbol] = pnl_pct

    def get_stats(self, symbol: str) -> dict:
        """
        Get memory statistics for symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Dict with signal_count, filter_count, filter_rate
        """
        signal_count = self.signal_count.get(symbol, 0)
        filter_count = self.filter_count.get(symbol, 0)
        filter_rate = (filter_count / signal_count * 100) if signal_count > 0 else 0

        return {
            'signal_count': signal_count,
            'filter_count': filter_count,
            'filter_rate': filter_rate,
            'last_action': self.last_action.get(symbol, 0),
            'last_pnl': self.last_pnl_pct.get(symbol, 0)
        }

    def reset_stats(self, symbol: Optional[str] = None):
        """
        Reset statistics (for testing/debugging).

        Args:
            symbol: Symbol to reset (or None for all)
        """
        if symbol:
            self.signal_count[symbol] = 0
            self.filter_count[symbol] = 0
        else:
            self.signal_count.clear()
            self.filter_count.clear()


# Global instance for shared use
memory = MemoryLite(window_size=15, threshold=0.0004)


# Convenience functions for easy integration
def calculate_memory_bias(df: pd.DataFrame, symbol: str) -> float:
    """Calculate memory bias for latest bar."""
    return memory.calculate_bias(df, symbol)


def filter_signal(
    df: pd.DataFrame,
    symbol: str,
    direction: str,
    confidence: float
) -> tuple[bool, float, str]:
    """Check if signal should fire based on memory."""
    return memory.should_fire(df, symbol, direction, confidence)


def update_memory(symbol: str, action: int, pnl_pct: Optional[float] = None):
    """Update memory state after trade."""
    memory.update_state(symbol, action, pnl_pct)


def get_memory_stats(symbol: str) -> dict:
    """Get memory statistics."""
    return memory.get_stats(symbol)


if __name__ == "__main__":
    # Test module
    print("Memory-Lite Module Test")
    print("=" * 50)

    # Create test data
    test_data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 1.1000,
        'rsi': np.random.rand(100) * 100,
        'atr': np.random.rand(100) * 0.001
    })

    mem = MemoryLite()

    # Test bias calculation
    bias = mem.calculate_bias(test_data, "EURUSD")
    print(f"Test bias: {bias:.6f}")

    # Test signal filtering
    should_fire, adj_conf, reason = mem.should_fire(
        test_data, "EURUSD", "BUY", 85.0
    )
    print(f"Should fire: {should_fire}")
    print(f"Adjusted confidence: {adj_conf:.1f}%")
    print(f"Reason: {reason}")

    # Test state update
    mem.update_state("EURUSD", 1, 0.015)

    # Test stats
    stats = mem.get_stats("EURUSD")
    print(f"Stats: {stats}")

    print("\n✅ Memory-Lite module test complete")
