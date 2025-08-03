#!/usr/bin/env python3
"""
ZMQ Fire Integration - Connects BITTEN fire commands to ZMQ controller
Replaces file-based execution with ZMQ commands to EA v7
"""

import json
import logging
from typing import Dict, Optional
from zmq_trade_controller import ZMQTradeController

logger = logging.getLogger('ZMQFireIntegration')

# Global controller instance
_controller = None

def get_controller() -> ZMQTradeController:
    """Get or create the ZMQ controller instance"""
    global _controller
    if _controller is None:
        _controller = ZMQTradeController()
        _controller.start()
    return _controller

def execute_zmq_fire(user_id: str, signal_data: Dict) -> Dict:
    """
    Execute a fire command via ZMQ
    Drop-in replacement for file-based fire.txt execution
    
    Args:
        user_id: User identifier
        signal_data: Signal data from fire router
        
    Returns:
        Dict with success status and message
    """
    controller = get_controller()
    
    # Convert BITTEN signal format to EA format
    zmq_signal = {
        'signal_id': signal_data.get('signal_id', f'FIRE_{user_id}_{int(time.time())}'),
        'symbol': signal_data.get('symbol', 'EURUSD'),
        'action': signal_data.get('side', 'buy').lower(),
        'lot': float(signal_data.get('volume', 0.01)),
        'sl': float(signal_data.get('sl_pips', 0)),
        'tp': float(signal_data.get('tp_pips', 0))
    }
    
    # Send via ZMQ
    success = controller.send_signal(zmq_signal)
    
    if success:
        logger.info(f"✅ ZMQ fire sent for user {user_id}: {zmq_signal['symbol']} {zmq_signal['action']}")
        return {
            'success': True,
            'message': 'Signal sent to MT5',
            'signal_id': zmq_signal['signal_id']
        }
    else:
        logger.error(f"❌ ZMQ fire failed for user {user_id}")
        return {
            'success': False,
            'message': 'Failed to send signal',
            'signal_id': zmq_signal['signal_id']
        }

def close_user_positions(user_id: str, symbol: Optional[str] = None) -> Dict:
    """Close positions for a user"""
    controller = get_controller()
    
    if symbol:
        # Close specific symbol
        signal = {
            'signal_id': f'CLOSE_{user_id}_{int(time.time())}',
            'symbol': symbol,
            'action': 'close'
        }
    else:
        # Close all positions
        signal = {
            'signal_id': f'CLOSEALL_{user_id}_{int(time.time())}',
            'symbol': '',
            'action': 'close_all'
        }
    
    success = controller.send_signal(signal)
    
    return {
        'success': success,
        'message': 'Close command sent' if success else 'Failed to send close command'
    }

def get_ea_status() -> Dict:
    """Get EA status"""
    controller = get_controller()
    success = controller.send_command('status')
    
    return {
        'success': success,
        'message': 'Status requested' if success else 'Failed to request status'
    }

# Update fire_router.py to use this:
"""
# In fire_router.py, replace:

# OLD:
fire_path = f"/containers/mt5_user_{user_id}/fire.txt"
with open(fire_path, 'w') as f:
    json.dump(trade_data, f)

# NEW:
from zmq_fire_integration import execute_zmq_fire
result = execute_zmq_fire(user_id, trade_data)
if not result['success']:
    logger.error(f"Fire execution failed: {result['message']}")
"""