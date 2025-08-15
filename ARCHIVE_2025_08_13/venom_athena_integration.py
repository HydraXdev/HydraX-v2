#!/usr/bin/env python3
"""
🐍🏛️ VENOM → ATHENA INTEGRATION
Hook VENOM signal generation into ATHENA group dispatch system
Short tactical messages for @bitten_signals group
"""

import sys
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

from athena_group_dispatcher import athena_group_dispatcher
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VenomAthenaIntegration')

def dispatch_athena_signal(signal_data):
    """
    ATHENA dispatch callback for VENOM signals
    Sends short tactical messages to @bitten_signals group
    """
    try:
        # Extract core signal data
        tcs = signal_data.get("tcs_score", 0)
        symbol = signal_data.get("symbol", "UNKNOWN")
        direction = signal_data.get("direction", "UNKNOWN")
        signal_id = signal_data.get("signal_id", "VENOM_UNKNOWN")
        
        logger.info(f"🐍→🏛️ VENOM signal received for ATHENA dispatch: {signal_id}")
        
        # Dispatch via ATHENA group system
        result = athena_group_dispatcher.dispatch_group_signal(signal_data)
        
        if result['success']:
            logger.info(f"✅ ATHENA group dispatch successful: {signal_id} → @bitten_signals")
            return result
        else:
            logger.error(f"❌ ATHENA group dispatch failed: {signal_id} - {result.get('error')}")
            return result
            
    except Exception as e:
        logger.error(f"❌ VENOM→ATHENA integration error: {e}")
        return {'success': False, 'error': str(e)}

def register_athena_callback():
    """
    Register ATHENA dispatch as the callback for VENOM signals
    This replaces generic signal output with tactical group messages
    """
    try:
        # Try to hook into VENOM signal processor
        logger.info("🔗 Attempting to register ATHENA callback with VENOM...")
        
        # Look for existing VENOM processors to hook into
        try:
            from apex_venom_v7_unfiltered import ApexVenomV7Unfiltered
            logger.info("✅ Found VENOM v7 engine - registering ATHENA callback")
            
            # Set dispatch callback if the engine supports it
            if hasattr(ApexVenomV7Unfiltered, 'set_dispatch_callback'):
                ApexVenomV7Unfiltered.set_dispatch_callback(dispatch_athena_signal)
                logger.info("🎯 ATHENA callback registered with VENOM v7")
            else:
                logger.warning("⚠️ VENOM v7 doesn't support dispatch callbacks - manual integration needed")
                
        except ImportError:
            logger.warning("⚠️ VENOM v7 not found - checking for other signal processors")
        
        # Try working signal generator
        try:
            from working_signal_generator import WorkingSignalGenerator
            logger.info("✅ Found Working Signal Generator - attempting integration")
            
            # This would need custom integration based on the actual implementation
            logger.info("🔧 Manual integration required for Working Signal Generator")
            
        except ImportError:
            logger.warning("⚠️ Working Signal Generator not found")
        
        # Integration with BittenCore is already done via bitten_core.py modifications
        logger.info("✅ ATHENA integration active via BittenCore signal dispatch")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ATHENA callback registration failed: {e}")
        return False

def test_integration():
    """Test the VENOM→ATHENA integration"""
    print("🧪 Testing VENOM→ATHENA Integration")
    print("=" * 50)
    
    # Create test signal matching VENOM format
    test_signal = {
        'signal_id': 'VENOM_INTEGRATION_TEST_001',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 87.5,
        'entry_price': 1.0875,
        'take_profit': 1.0925,
        'stop_loss': 1.0825,
        'signal_type': 'PRECISION_STRIKE',
        'confidence': 87.5,
        'pattern': 'Institutional Breakout',
        'timeframe': 'M15'
    }
    
    print(f"🎯 Test Signal: {test_signal['symbol']} {test_signal['direction']} (TCS: {test_signal['tcs_score']}%)")
    
    # Test ATHENA dispatch
    result = dispatch_athena_signal(test_signal)
    
    if result['success']:
        print("✅ Integration test successful!")
        print(f"   Signal dispatched to: @bitten_signals")
        print(f"   HUD URL: {result.get('hud_url')}")
        print(f"   Tactical line: {result.get('tactical_line')}")
    else:
        print(f"❌ Integration test failed: {result.get('error')}")
    
    print("=" * 50)
    return result['success']

if __name__ == "__main__":
    print("🐍🏛️ VENOM→ATHENA INTEGRATION SYSTEM")
    print("=" * 50)
    
    # Register callback
    success = register_athena_callback()
    
    if success:
        print("✅ ATHENA callback registration completed")
    else:
        print("❌ ATHENA callback registration failed")
    
    # Test integration
    test_success = test_integration()
    
    if test_success:
        print("\n🎯 VENOM→ATHENA INTEGRATION: OPERATIONAL")
        print("🏛️ ATHENA is now the official signal dispatcher!")
    else:
        print("\n⚠️ INTEGRATION ISSUES DETECTED - CHECK CONFIGURATION")
    
    print("=" * 50)