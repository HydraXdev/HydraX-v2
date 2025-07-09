# __init__.py
# Order Flow and Microstructure Analysis Package

"""
Market Microstructure Analysis Components

This package provides comprehensive tools for detecting and analyzing
market microstructure patterns, institutional activity, and potential
market manipulation.

Components:
- IcebergDetector: Identifies hidden institutional orders
- SpoofingDetector: Detects market manipulation via fake orders
- HFTActivityDetector: Tracks high-frequency trading patterns
- QuoteStuffingIdentifier: Identifies quote spam attacks
- HiddenLiquidityScanner: Finds dark pools and hidden orders
- MarketMakerAnalyzer: Analyzes professional liquidity providers
- MicrostructureScorer: Comprehensive market quality scoring

Usage:
    from order_flow import MicrostructureScorer
    
    scorer = MicrostructureScorer('EURUSD', 0.0001)
    score = scorer.update_market_data(timestamp, bid_book, ask_book, trades, quotes)
    
    if score.manipulation_risk > 60:
        print("High manipulation risk detected!")
"""

from .iceberg_detector import IcebergDetector, IcebergSignal
from .spoofing_detector import SpoofingDetector, SpoofingEvent, OrderBookSnapshot
from .hft_activity_detector import HFTActivityDetector, HFTSignature, MicrostructureEvent
from .quote_stuffing_identifier import QuoteStuffingIdentifier, QuoteStuffingEvent, QuoteMessage
from .hidden_liquidity_scanner import HiddenLiquidityScanner, HiddenLiquiditySignal, ExecutionAnomaly
from .market_maker_analyzer import MarketMakerAnalyzer, MarketMakerProfile, MarketMakerAction
from .microstructure_scorer import (
    MicrostructureScorer, 
    MicrostructureScore, 
    MarketMicrostructureState
)

__all__ = [
    # Main scorer
    'MicrostructureScorer',
    'MicrostructureScore',
    'MarketMicrostructureState',
    
    # Individual detectors
    'IcebergDetector',
    'IcebergSignal',
    'SpoofingDetector',
    'SpoofingEvent',
    'OrderBookSnapshot',
    'HFTActivityDetector',
    'HFTSignature',
    'MicrostructureEvent',
    'QuoteStuffingIdentifier',
    'QuoteStuffingEvent',
    'QuoteMessage',
    'HiddenLiquidityScanner',
    'HiddenLiquiditySignal',
    'ExecutionAnomaly',
    'MarketMakerAnalyzer',
    'MarketMakerProfile',
    'MarketMakerAction',
]

# Version info
__version__ = '1.0.0'
__author__ = 'HydraX Trading Systems'