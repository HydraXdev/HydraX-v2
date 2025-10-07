"""
Advanced Signal Intelligence System for HydraX v2

This module provides a scalable architecture for ingesting, processing,
and analyzing data from multiple sources to generate trading signals.
"""

__version__ = "2.0.0"
__author__ = "HydraX Intelligence Team"

from .config.manager import ConfigManager
from .core.base import DataSource, IntelligenceComponent, Signal, SignalStrength, SignalType
from .core.orchestrator import IntelligenceOrchestrator

__all__ = [
    "IntelligenceComponent",
    "DataSource",
    "Signal",
    "SignalType",
    "SignalStrength",
    "IntelligenceOrchestrator",
    "ConfigManager",
]
