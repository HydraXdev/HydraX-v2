"""
MT5 Bridge Integration for BITTEN System
Integrates the MT5 Bridge Adapter with the existing fire_router
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .mt5_bridge_adapter import get_bridge_adapter, MT5BridgeAdapter
from ..bitten_core.fire_router import TradeRequest, TradeExecutionResult
from ..bitten_core.fire_modes import TierLevel

logger = logging.getLogger(__name__)

class MT5BridgeIntegration:
    """
    Integration layer between fire_router and MT5 bridge adapter
    Handles conversion between BITTEN trade requests and MT5 instructions
    """
    
    def __init__(self, mt5_files_path: Optional[str] = None):
        """
        Initialize the MT5 bridge integration
        
        Args:
            mt5_files_path: Optional custom path to MT5 Files folder
        """
        # Get or create adapter instance
        self.adapter = get_bridge_adapter(mt5_files_path)
        
        # Symbol mapping (if needed for broker-specific symbols)
        self.symbol_map = {
            'XAUUSD': 'XAUUSD',  # Gold
            'EURUSD': 'EURUSD',
            'GBPUSD': 'GBPUSD',
            'USDJPY': 'USDJPY',
            # Add more mappings as needed
        }
        
        logger.info("MT5 Bridge Integration initialized")
    
    def execute_trade(self, request: TradeRequest) -> TradeExecutionResult:
        """
        Execute a trade request through the MT5 bridge
        
        Args:
            request: TradeRequest object from fire_router
            
        Returns:
            TradeExecutionResult with execution details
        """
        try:
            # Map symbol if needed
            mt5_symbol = self.symbol_map.get(request.symbol, request.symbol)
            
            # Execute through adapter
            result = self.adapter.execute_trade(
                symbol=mt5_symbol,
                direction=request.direction.value,
                volume=request.volume,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit,
                comment=f"{request.comment} TCS:{request.tcs_score} {request.fire_mode.value}"
            )
            
            # Convert adapter result to TradeExecutionResult
            if result['success']:
                return TradeExecutionResult(
                    success=True,
                    trade_id=result['trade_id'],
                    execution_price=result.get('price', 0),
                    timestamp=result.get('timestamp', datetime.now().isoformat()),
                    tcs_score=request.tcs_score,
                    ticket=result.get('ticket', 0),
                    account_info=result.get('account', {})
                )
            else:
                return TradeExecutionResult(
                    success=False,
                    message=f"❌ {result.get('message', 'Trade execution failed')}",
                    error_code=result.get('error_code', 'MT5_ERROR')
                )
                
        except Exception as e:
            logger.error(f"Error executing trade through MT5 bridge: {e}")
            return TradeExecutionResult(
                success=False,
                message=f"❌ Bridge error: {str(e)}",
                error_code="BRIDGE_EXCEPTION"
            )
    
    def get_bridge_status(self) -> Dict[str, Any]:
        """Get current MT5 bridge status"""
        status = self.adapter.get_status()
        if status:
            return {
                'mt5_connected': status['connected'],
                'active_positions': status['positions'],
                'pending_orders': status['orders'],
                'last_update': status['timestamp'],
                'bridge_active': self.adapter.running
            }
        else:
            return {
                'mt5_connected': False,
                'bridge_active': self.adapter.running,
                'error': 'No status available from MT5'
            }
    
    def is_ready(self) -> bool:
        """Check if bridge is ready for trading"""
        return self.adapter.running and self.adapter.is_connected()

# Update fire_router.py to use the bridge
def update_fire_router_for_mt5():
    """
    This function shows how to update fire_router.py to use the MT5 bridge
    """
    code_snippet = '''
# In fire_router.py, update the _send_to_bridge method:

from .mt5_bridge_integration import MT5BridgeIntegration

class FireRouter:
    def __init__(self):
        # ... existing init code ...
        
        # Initialize MT5 bridge if enabled
        self.mt5_bridge = None
        if os.getenv('USE_MT5_BRIDGE', 'false').lower() == 'true':
            mt5_path = os.getenv('MT5_FILES_PATH')  # Optional custom path
            self.mt5_bridge = MT5BridgeIntegration(mt5_path)
            logger.info("MT5 Bridge enabled")
    
    def _send_to_bridge(self, request: TradeRequest) -> TradeExecutionResult:
        """Send trade to bridge with enhanced tier-based execution"""
        try:
            # ... existing tier logic ...
            
            # Check if MT5 bridge is enabled
            if self.mt5_bridge and self.mt5_bridge.is_ready():
                # Execute through MT5 bridge
                result = self.mt5_bridge.execute_trade(request)
                
                if result.success:
                    # Record shot for fire mode tracking
                    self.fire_validator.record_shot(request.user_id, request.fire_mode)
                
                return result
            
            # Fallback to HTTP bridge or simulation
            elif os.getenv('USE_LIVE_BRIDGE', 'false').lower() == 'true':
                # ... existing HTTP bridge code ...
            else:
                # ... existing simulation code ...
    '''
    
    return code_snippet

# Configuration helper
def create_mt5_config():
    """Create configuration for MT5 bridge"""
    config = {
        'mt5': {
            'enabled': True,
            'files_path': None,  # Auto-detect
            'check_interval_ms': 100,
            'trade_timeout': 30,
            'symbol_mapping': {
                'XAUUSD': 'XAUUSD',
                'EURUSD': 'EURUSD',
                'GBPUSD': 'GBPUSD',
                'USDJPY': 'USDJPY'
            }
        }
    }
    
    # Save to config file
    config_path = '/root/HydraX-v2/config/mt5_bridge.json'
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    import json
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create config
    config_path = create_mt5_config()
    print(f"MT5 config created at: {config_path}")
    
    # Show integration instructions
    print("\nTo integrate with fire_router.py:")
    print(update_fire_router_for_mt5())