"""
MetaSocket → BITTEN Integration Package

Provides normalized data streams from MetaSocket to Elite Guard, XP, and UI systems.
"""

from .bootstrap import MetaSocketBootstrap
from .subscriptions import MetaSocketSubscriptions
from .backfill import MetaSocketBackfill
from .normalizers.positions import PositionEventNormalizer
from .pollers.account import AccountSummaryPoller
from .signal_snapshots import SignalSnapshotProducer
from .web.healthz import MetaSocketHealthCheck
from . import mission_state_worker

__version__ = "1.0.0"
__author__ = "BITTEN System"

__all__ = [
    "MetaSocketBootstrap",
    "MetaSocketSubscriptions",
    "MetaSocketBackfill",
    "PositionEventNormalizer",
    "AccountSummaryPoller",
    "SignalSnapshotProducer",
    "MetaSocketHealthCheck",
    "mission_state_worker"
]