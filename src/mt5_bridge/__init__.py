"""
🎯 MT5 Bridge Module
Handles communication between MT5 and BITTEN system
"""

from .bridge_integration import MT5BridgeIntegration, get_bridge_integration, process_mt5_result
from .mt5_bridge_adapter import TradeResult
from .result_parser import MT5ResultAggregator, MT5ResultParser, OrderType, TradeStatus, parse_mt5_result

__all__ = [
    # Parser
    "MT5ResultParser",
    "MT5ResultAggregator",
    "parse_mt5_result",
    "OrderType",
    "TradeStatus",
    # Models
    "TradeResult",
    # Integration
    "MT5BridgeIntegration",
    "get_bridge_integration",
    "process_mt5_result",
]
