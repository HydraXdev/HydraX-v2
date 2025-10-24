"""
ZMQ Gateway Service for BITTEN v2.0

Consolidates 3 v1 processes into a single unified service:
- zmq_telemetry_bridge_debug.py (market data handling)
- command_router.py (fire command routing)
- confirm_listener_v207.py (trade confirmations)
"""

__version__ = "2.0.0"
