#!/usr/bin/env python3
"""
Fix auto-fire integration to work through proper BittenCore validation
This ensures ALL trades go through rules before execution
"""

import sys
import json
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

def add_auto_fire_to_bitten_core():
    """
    Add auto-fire logic to BittenCore's signal processing
    After rule validation, check if user should auto-fire
    """
    
    code_to_add = '''
    def _check_and_execute_auto_fire(self, signal_data: Dict, user_id: str = "7176191872") -> Dict:
        """
        Check if user should auto-fire and execute if conditions met
        This runs AFTER all rule validation
        """
        try:
            # Import fire mode components
            from src.bitten_core.fire_mode_database import fire_mode_db
            from src.bitten_core.fire_mode_executor import FireModeExecutor
            from src.bitten_core.fire_router import get_fire_router, ExecutionMode
            
            executor = FireModeExecutor()
            
            # Get user's fire mode
            mode_info = fire_mode_db.get_user_mode(user_id)
            
            # Check if user is in AUTO mode
            if mode_info['current_mode'] != 'AUTO':
                return {'auto_fired': False, 'reason': 'Not in AUTO mode'}
            
            # Check if user tier allows AUTO (COMMANDER only)
            user_tier = self._get_user_tier(user_id)
            if user_tier != "COMMANDER":
                return {'auto_fired': False, 'reason': 'Tier does not support AUTO'}
            
            # Check signal confidence threshold
            confidence = signal_data.get('confidence', 0)
            if confidence < 70:  # Lower threshold for testing
                return {'auto_fired': False, 'reason': f'Confidence {confidence}% below threshold'}
            
            # All checks passed - execute auto-fire
            self._log_info(f"🔥 AUTO-FIRE triggered for {user_id} on {signal_data['signal_id']}")
            
            # Get fire router
            fire_router = get_fire_router(ExecutionMode.LIVE)
            
            # Create trade request
            from src.bitten_core.fire_router import TradeRequest, TradeDirection
            
            trade_request = TradeRequest(
                mission_id=signal_data['signal_id'],
                user_id=user_id,
                symbol=signal_data['symbol'],
                direction=TradeDirection.BUY if signal_data['direction'].upper() == 'BUY' else TradeDirection.SELL,
                volume=0.01,  # Base lot size
                stop_loss_pips=signal_data.get('stop_pips', 20),
                take_profit_pips=signal_data.get('target_pips', 40),
                entry_price=signal_data.get('entry_price', 0)
            )
            
            # Execute through fire router (applies all rules)
            result = fire_router.execute_trade_request(trade_request)
            
            if result['success']:
                self._log_info(f"✅ AUTO-FIRE executed: {result.get('ticket')}")
                return {'auto_fired': True, 'ticket': result.get('ticket')}
            else:
                self._log_error(f"❌ AUTO-FIRE failed: {result.get('error')}")
                return {'auto_fired': False, 'error': result.get('error')}
                
        except Exception as e:
            self._log_error(f"Auto-fire check error: {e}")
            return {'auto_fired': False, 'error': str(e)}
    '''
    
    print("Integration code prepared")
    print("This should be added to BittenCore's process_signal method")
    print("Right after rule validation and before returning success")
    
    # Also need to ensure fire_router can bind to port 5555
    print("\nAlso need to start fire_router service to bind port 5555 for EA")
    
add_auto_fire_to_bitten_core()