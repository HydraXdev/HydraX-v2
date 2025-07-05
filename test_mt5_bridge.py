#!/usr/bin/env python3
"""
Test script for MT5 Bridge integration
Tests the complete flow from Python to MT5 EA
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add project path
sys.path.append('/root/HydraX-v2/src')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MT5_Bridge_Test')

def test_bridge_adapter():
    """Test the MT5 bridge adapter directly"""
    logger.info("Testing MT5 Bridge Adapter...")
    
    from bitten_core.mt5_bridge_adapter import get_bridge_adapter
    
    # Create adapter
    adapter = get_bridge_adapter()
    
    # Wait for initial status
    time.sleep(2)
    
    # Check status
    status = adapter.get_status()
    if status:
        logger.info(f"Bridge Status: {status}")
    else:
        logger.warning("No status available from bridge")
    
    # Test trade execution
    logger.info("Executing test trade...")
    result = adapter.execute_trade(
        symbol="XAUUSD",
        direction="buy",
        volume=0.01,
        stop_loss=1950.00,
        take_profit=1970.00
    )
    
    logger.info(f"Trade Result: {result}")
    
    return result['success'] if result else False

def test_fire_router_integration():
    """Test the complete fire router integration"""
    logger.info("Testing Fire Router MT5 Integration...")
    
    # Set environment variables
    os.environ['USE_MT5_BRIDGE'] = 'true'
    os.environ['USE_LIVE_BRIDGE'] = 'false'  # Disable HTTP bridge
    
    from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, FireMode
    from bitten_core.fire_modes import TierLevel
    
    # Create fire router
    router = FireRouter()
    
    # Set user tier
    test_user_id = 123456
    router.user_tiers[test_user_id] = TierLevel.FANG
    
    # Create trade request
    request = TradeRequest(
        user_id=test_user_id,
        symbol="XAUUSD",
        direction=TradeDirection.BUY,
        volume=0.01,
        stop_loss=1950.00,
        take_profit=1970.00,
        comment="MT5 Bridge Test",
        tcs_score=85,
        fire_mode=FireMode.SINGLE_SHOT
    )
    
    # Execute trade
    logger.info(f"Executing trade request: {request}")
    result = router.execute_trade(request)
    
    logger.info(f"Execution Result: {result}")
    
    return result

def test_file_communication():
    """Test direct file communication"""
    logger.info("Testing file communication...")
    
    # Check if we can write to a test directory
    test_dir = "./mt5_files"
    os.makedirs(test_dir, exist_ok=True)
    
    test_file = os.path.join(test_dir, "test_instruction.txt")
    test_content = "TEST123,EURUSD,BUY,0.01,0,1.1000,1.0900"
    
    try:
        with open(test_file, 'w') as f:
            f.write(test_content)
        logger.info(f"Successfully wrote test file: {test_file}")
        
        # Read it back
        with open(test_file, 'r') as f:
            content = f.read()
        logger.info(f"Read back: {content}")
        
        # Clean up
        os.remove(test_file)
        
        return True
    except Exception as e:
        logger.error(f"File communication test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("BITTEN MT5 Bridge Integration Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("File Communication", test_file_communication),
        ("Bridge Adapter", test_bridge_adapter),
        ("Fire Router Integration", test_fire_router_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running: {test_name} ---")
        try:
            success = test_func()
            results[test_name] = "PASSED" if success else "FAILED"
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = "ERROR"
        
        time.sleep(1)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status_icon = "✅" if result == "PASSED" else "❌"
        logger.info(f"{status_icon} {test_name}: {result}")
    
    # Integration notes
    logger.info("\n" + "=" * 60)
    logger.info("INTEGRATION NOTES")
    logger.info("=" * 60)
    logger.info("1. Set USE_MT5_BRIDGE=true to enable MT5 bridge")
    logger.info("2. Set MT5_FILES_PATH to your MT5 terminal Files folder")
    logger.info("3. Install BITTENBridge_HYBRID_v1.2_PRODUCTION.mq5 in MT5")
    logger.info("4. The EA will create/read these files:")
    logger.info("   - bitten_instructions.txt (trades from Python)")
    logger.info("   - bitten_results.txt (execution results)")
    logger.info("   - bitten_status.txt (EA status/heartbeat)")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()