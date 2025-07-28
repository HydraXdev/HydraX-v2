"""
CITADEL Shield System - Intelligent Signal Protection & Education Platform

CITADEL transforms signal filtering from restriction to protection, showing ALL signals 
while intelligently scoring and tagging them. This creates trust, transparency, and 
teaches users to think like institutions.

Core Philosophy:
- Show Everything: All 20-25 signals visible (no FOMO)
- Guide Intelligently: Clear visual hierarchy with shield status
- Teach Through Transparency: Every score is explainable
- Evolve Continuously: Real-time updates as conditions change

Author: HydraX Strategic Defense Initiative
Version: 1.0.0
"""

from .analyzers.signal_inspector import SignalInspector
from .analyzers.market_regime import MarketRegimeAnalyzer
from .analyzers.liquidity_mapper import LiquidityMapper
from .analyzers.cross_tf_validator import CrossTimeframeValidator
from .scoring.shield_engine import ShieldScoringEngine
from .formatters.telegram_formatter import TelegramShieldFormatter
from .storage.shield_logger import ShieldLogger

__version__ = "1.0.0"
__all__ = [
    "SignalInspector",
    "MarketRegimeAnalyzer", 
    "LiquidityMapper",
    "CrossTimeframeValidator",
    "ShieldScoringEngine",
    "TelegramShieldFormatter",
    "ShieldLogger"
]