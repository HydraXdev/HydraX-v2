"""
Advanced Signal Intelligence System for HydraX v2

This module provides a scalable architecture for ingesting, processing,
and analyzing data from multiple sources to generate trading signals.
"""

__version__ = "2.0.0"
__author__ = "HydraX Intelligence Team"

from .core.base import (
    IntelligenceComponent,
    DataSource,
    Signal,
    SignalType,
    SignalStrength
)

from .core.orchestrator import IntelligenceOrchestrator
from .config.manager import ConfigManager

__all__ = [
    'IntelligenceComponent',
    'DataSource', 
    'Signal',
    'SignalType',
    'SignalStrength',
    'IntelligenceOrchestrator',
    'ConfigManager'
]