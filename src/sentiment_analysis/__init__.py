"""
Advanced Sentiment Analysis System for HydraX

This module provides comprehensive market sentiment analysis by aggregating
data from multiple sources including Twitter/X, news outlets, Reddit WSB,
options flow, and market indicators.
"""

from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Version info
__version__ = "1.0.0"
__author__ = "HydraX Team"

# Export main components
from .aggregation.sentiment_aggregator import SentimentAggregator
from .api.sentiment_api import SentimentAPI

__all__ = [
    'SentimentAggregator',
    'SentimentAPI',
]