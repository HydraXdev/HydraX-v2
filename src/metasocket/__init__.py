"""
MetaSocket → BITTEN Integration Package

Provides normalized data streams from MetaSocket to Elite Guard, XP, and UI systems.
"""

from . import mission_state_worker
from .backfill import MetaSocketBackfill
from .bootstrap import MetaSocketBootstrap
from .normalizers.positions import PositionEventNormalizer
from .pollers.account import AccountSummaryPoller
from .signal_snapshots import SignalSnapshotProducer
from .subscriptions import MetaSocketSubscriptions
from .web.healthz import MetaSocketHealthCheck

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
    "mission_state_worker",
]
