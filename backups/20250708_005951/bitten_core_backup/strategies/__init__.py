# BITTEN Trading Strategies Package
"""
Master Trading Strategies Implementation
Institutional-grade algorithms with 20+ years of market expertise
"""

from .london_breakout import LondonBreakoutStrategy
from .support_resistance import SupportResistanceStrategy
from .momentum_continuation import MomentumContinuationStrategy
from .mean_reversion import MeanReversionStrategy
from .strategy_base import StrategyBase, SignalType, SignalDirection, MarketData, TechnicalIndicators, TradingSignal

__all__ = [
    'LondonBreakoutStrategy',
    'SupportResistanceStrategy', 
    'MomentumContinuationStrategy',
    'MeanReversionStrategy',
    'StrategyBase',
    'SignalType',
    'SignalDirection'
]