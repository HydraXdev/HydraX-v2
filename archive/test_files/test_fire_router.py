#!/usr/bin/env python3
"""
Test script for the new fire_router.py implementation
Tests both simulation and live modes with various scenarios
"""

import sys
import os
import time
import json
from datetime import datetime

# Add the src directory to path
sys.path.insert(0, '/root/HydraX-v2/src')

from bitten_core.fire_router import (
    FireRouter, 
    TradeRequest, 
    TradeDirection, 
    ExecutionMode,
    FireMode,
    TierLevel,
    execute_trade
)

def test_legacy_interface():
    """Test the legacy execute_trade function"""
    
    print("=" * 60)
    print("TESTING LEGACY INTERFACE")
    print("=" * 60)
    
    # Set simulation mode
    os.environ["BITTEN_SIMULATION_MODE"] = "true"
    
    # Test basic mission
    mission = {
        "symbol": "EURUSD",
        "type": "buy",
        "lot_size": 0.01,
        "tp": 1.1000,
        "sl": 1.0950,
        "comment": "Test trade",
        "mission_id": "test_001",
        "user_id": "test_user",
        "tcs": 85,
        "fire_mode": "single_shot",
        "tier": "nibbler"
    }
    
    print(f"Executing legacy mission: {mission}")
    result = execute_trade(mission)
    print(f"Result: {result}")
    
    return result == "sent_to_bridge"

def test_new_interface():
    """Test the new FireRouter interface"""
    
    print("=" * 60)
    print("TESTING NEW FIRE ROUTER INTERFACE")
    print("=" * 60)
    
    # Create router in simulation mode
    router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
    
    # Test with various scenarios
    test_cases = [
        {
            "name": "Valid Nibbler Trade",
            "request": TradeRequest(
                symbol="GBPUSD",
                direction=TradeDirection.BUY,
                volume=0.01,
                stop_loss=1.2950,
                take_profit=1.3050,
                comment="Test trade",
                tcs_score=85,
                fire_mode=FireMode.SINGLE_SHOT,
                user_id="test_user",
                mission_id="test_002",
                tier=TierLevel.NIBBLER
            ),
            "user_profile": {
                "user_id": "test_user",
                "tier": "nibbler",
                "account_balance": 10000,
                "shots_today": 0,
                "open_positions": 0,
                "total_exposure_percent": 0
            }
        },
        {
            "name": "Low TCS Trade (Should Fail)",
            "request": TradeRequest(
                symbol="USDJPY",
                direction=TradeDirection.SELL,
                volume=0.01,
                stop_loss=150.00,
                take_profit=149.00,
                comment="Low TCS test",
                tcs_score=60,  # Too low for nibbler
                fire_mode=FireMode.SINGLE_SHOT,
                user_id="test_user",
                mission_id="test_003",
                tier=TierLevel.NIBBLER
            ),
            "user_profile": {
                "user_id": "test_user",
                "tier": "nibbler",
                "account_balance": 10000,
                "shots_today": 0,
                "open_positions": 0,
                "total_exposure_percent": 0
            }
        },
        {
            "name": "Commander Auto-Fire",
            "request": TradeRequest(
                symbol="XAUUSD",
                direction=TradeDirection.BUY,
                volume=0.01,
                stop_loss=1950.00,
                take_profit=1970.00,
                comment="Commander auto-fire",
                tcs_score=92,
                fire_mode=FireMode.AUTO_FIRE,
                user_id="commander_user",
                mission_id="test_004",
                tier=TierLevel.COMMANDER
            ),
            "user_profile": {
                "user_id": "commander_user",
                "tier": "commander",
                "account_balance": 50000,
                "shots_today": 5,
                "open_positions": 1,
                "total_exposure_percent": 2
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\\n--- {test_case['name']} ---")
        
        start_time = time.time()
        result = router.execute_trade_request(
            test_case["request"],
            test_case["user_profile"]
        )
        execution_time = time.time() - start_time
        
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        print(f"Execution time: {execution_time:.3f}s")
        
        if result.validation_result:
            print(f"Validation reason: {result.validation_result.reason}")
            if result.validation_result.bot_responses:
                print(f"Bot responses: {result.validation_result.bot_responses}")
        
        if result.error_code:
            print(f"Error code: {result.error_code}")
        
        results.append({
            "test_name": test_case["name"],
            "success": result.success,
            "execution_time": execution_time,
            "message": result.message
        })
    
    return results

def test_system_status():
    """Test system status functionality"""
    
    print("=" * 60)
    print("TESTING SYSTEM STATUS")
    print("=" * 60)
    
    router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
    
    # Execute a few trades to populate statistics
    for i in range(3):
        request = TradeRequest(
            symbol="EURUSD",
            direction=TradeDirection.BUY,
            volume=0.01,
            tcs_score=85,
            user_id="test_user",
            mission_id=f"status_test_{i}",
            tier=TierLevel.NIBBLER
        )
        
        user_profile = {
            "user_id": "test_user",
            "tier": "nibbler",
            "account_balance": 10000,
            "shots_today": i,
            "open_positions": 0,
            "total_exposure_percent": 0
        }
        
        router.execute_trade_request(request, user_profile)
    
    # Get system status
    status = router.get_system_status()
    
    print("System Status:")
    print(json.dumps(status, indent=2, default=str))
    
    return status

def test_bridge_connection():
    """Test bridge connection handling"""
    
    print("=" * 60)
    print("TESTING BRIDGE CONNECTION")
    print("=" * 60)
    
    # Test with invalid bridge settings (should fail gracefully)
    router = FireRouter(
        bridge_host="127.0.0.1",
        bridge_port=9999,  # Invalid port
        execution_mode=ExecutionMode.LIVE
    )
    
    request = TradeRequest(
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.01,
        tcs_score=85,
        user_id="test_user",
        mission_id="bridge_test",
        tier=TierLevel.NIBBLER
    )
    
    user_profile = {
        "user_id": "test_user",
        "tier": "nibbler",
        "account_balance": 10000,
        "shots_today": 0,
        "open_positions": 0,
        "total_exposure_percent": 0
    }
    
    print("Testing with invalid bridge connection...")
    result = router.execute_trade_request(request, user_profile)
    
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print(f"Error code: {result.error_code}")
    
    # Check bridge health
    status = router.get_system_status()
    print(f"Bridge health: {status['bridge_health']}")
    
    return not result.success  # Should fail

def main():
    """Run all tests"""
    
    print("🔥 FIRE ROUTER COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Legacy Interface
    try:
        legacy_result = test_legacy_interface()
        test_results.append(("Legacy Interface", legacy_result))
        print(f"✅ Legacy Interface: {'PASSED' if legacy_result else 'FAILED'}")
    except Exception as e:
        test_results.append(("Legacy Interface", False))
        print(f"❌ Legacy Interface: FAILED - {e}")
    
    # Test 2: New Interface
    try:
        new_results = test_new_interface()
        all_passed = all(r["success"] for r in new_results if "Should Fail" not in r["test_name"])
        failed_as_expected = any(not r["success"] for r in new_results if "Should Fail" in r["test_name"])
        new_interface_passed = all_passed and failed_as_expected
        test_results.append(("New Interface", new_interface_passed))
        print(f"✅ New Interface: {'PASSED' if new_interface_passed else 'FAILED'}")
    except Exception as e:
        test_results.append(("New Interface", False))
        print(f"❌ New Interface: FAILED - {e}")
    
    # Test 3: System Status
    try:
        status = test_system_status()
        status_passed = status is not None and "trade_statistics" in status
        test_results.append(("System Status", status_passed))
        print(f"✅ System Status: {'PASSED' if status_passed else 'FAILED'}")
    except Exception as e:
        test_results.append(("System Status", False))
        print(f"❌ System Status: FAILED - {e}")
    
    # Test 4: Bridge Connection
    try:
        bridge_result = test_bridge_connection()
        test_results.append(("Bridge Connection", bridge_result))
        print(f"✅ Bridge Connection: {'PASSED' if bridge_result else 'FAILED'}")
    except Exception as e:
        test_results.append(("Bridge Connection", False))
        print(f"❌ Bridge Connection: FAILED - {e}")
    
    # Summary
    print("\\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Fire Router is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)