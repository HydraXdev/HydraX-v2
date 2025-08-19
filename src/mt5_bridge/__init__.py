"""
🎯 MT5 Bridge Module
Handles communication between MT5 and BITTEN system
"""

from .result_parser import (
    MT5ResultParser,
    MT5ResultAggregator,
    parse_mt5_result,
    OrderType,
    TradeStatus
)

from .mt5_bridge_adapter import (
    TradeResult
)

from .bridge_integration import (
    MT5BridgeIntegration,
    get_bridge_integration,
    process_mt5_result
)

__all__ = [
    # Parser
    'MT5ResultParser',
    'MT5ResultAggregator', 
    'parse_mt5_result',
    'OrderType',
    'TradeStatus',
    
    # Models
    'TradeResult',
    
    # Integration
    'MT5BridgeIntegration',
    'get_bridge_integration',
    'process_mt5_result'
]