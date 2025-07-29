#!/usr/bin/env python3
"""
Test script for the standalone fire_router implementation
"""

import sys
import os
import time
import json
from datetime import datetime

# Add the src directory to path
sys.path.insert(0, '/root/HydraX-v2/src')

from bitten_core.fire_router_standalone import (
    FireRouter, 
    TradeRequest, 
    TradeDirection, 
    ExecutionMode,
    execute_trade
)

def test_legacy_interface():
    """Test the legacy execute_trade function"""
    
    print("🔥 TESTING LEGACY INTERFACE")
    print("=" * 50)
    
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
        "tcs": 85
    }
    
    print(f"Executing legacy mission: {mission}")
    result = execute_trade(mission)
    print(f"Result: {result}")
    
    return result == "sent_to_bridge"

def test_new_interface():
    """Test the new FireRouter interface"""
    
    print("\\n🚀 TESTING NEW FIRE ROUTER INTERFACE")
    print("=" * 50)
    
    # Create router in simulation mode
    router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
    
    # Test with various scenarios
    test_cases = [
        {
            "name": "Valid Trade",
            "request": TradeRequest(
                symbol="GBPUSD",
                direction=TradeDirection.BUY,
                volume=0.01,
                stop_loss=1.2950,
                take_profit=1.3050,
                comment="Test trade",
                tcs_score=85,
                user_id="test_user",
                mission_id="test_002"
            )
        },
        {
            "name": "Invalid Symbol",
            "request": TradeRequest(
                symbol="XXX",  # Invalid symbol
                direction=TradeDirection.BUY,
                volume=0.01,
                tcs_score=85,
                user_id="test_user",
                mission_id="test_003"
            )
        },
        {
            "name": "Low TCS",
            "request": TradeRequest(
                symbol="USDJPY",
                direction=TradeDirection.SELL,
                volume=0.01,
                tcs_score=30,  # Too low
                user_id="test_user",
                mission_id="test_004"
            )
        },
        {
            "name": "Invalid Volume",
            "request": TradeRequest(
                symbol="EURUSD",
                direction=TradeDirection.BUY,
                volume=0,  # Invalid volume
                tcs_score=85,
                user_id="test_user",
                mission_id="test_005"
            )
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\\n--- {test_case['name']} ---")
        
        start_time = time.time()
        result = router.execute_trade_request(test_case["request"])
        execution_time = time.time() - start_time
        
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        print(f"Execution time: {execution_time:.3f}s")
        
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
    
    print("\\n📊 TESTING SYSTEM STATUS")
    print("=" * 50)
    
    router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
    
    # Execute a few trades to populate statistics
    for i in range(3):
        request = TradeRequest(
            symbol="EURUSD",
            direction=TradeDirection.BUY,
            volume=0.01,
            tcs_score=85,
            user_id="test_user",
            mission_id=f"status_test_{i}"
        )
        
        router.execute_trade_request(request)
    
    # Get system status
    status = router.get_system_status()
    
    print("System Status:")
    print(json.dumps(status, indent=2, default=str))
    
    return status

def test_bridge_connection():
    """Test bridge connection handling"""
    
    print("\\n🔌 TESTING BRIDGE CONNECTION")
    print("=" * 50)
    
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
        mission_id="bridge_test"
    )
    
    print("Testing with invalid bridge connection...")
    result = router.execute_trade_request(request)
    
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print(f"Error code: {result.error_code}")
    
    # Check bridge health
    status = router.get_system_status()
    print(f"Bridge health: {status['bridge_health']}")
    
    return not result.success  # Should fail

def test_mode_switching():
    """Test execution mode switching"""
    
    print("\\n🔄 TESTING MODE SWITCHING")
    print("=" * 50)
    
    router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
    
    request = TradeRequest(
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.01,
        tcs_score=85,
        user_id="test_user",
        mission_id="mode_test"
    )
    
    # Test simulation mode
    print("Testing simulation mode...")
    result_sim = router.execute_trade_request(request)
    print(f"Simulation result: {result_sim.success} - {result_sim.message}")
    
    # Switch to live mode
    router.set_execution_mode(ExecutionMode.LIVE)
    
    # Test live mode (should fail due to no bridge)
    print("Testing live mode...")
    result_live = router.execute_trade_request(request)
    print(f"Live result: {result_live.success} - {result_live.message}")
    
    return result_sim.success and not result_live.success

def main():
    """Run all tests"""
    
    print("🚀 STANDALONE FIRE ROUTER TEST SUITE")
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
        # Should have 1 success and 3 failures (validation failures)
        successes = sum(1 for r in new_results if r["success"])
        failures = sum(1 for r in new_results if not r["success"])
        new_interface_passed = successes == 1 and failures == 3
        test_results.append(("New Interface", new_interface_passed))
        print(f"✅ New Interface: {'PASSED' if new_interface_passed else 'FAILED'} ({successes} successes, {failures} failures)")
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
    
    # Test 5: Mode Switching
    try:
        mode_result = test_mode_switching()
        test_results.append(("Mode Switching", mode_result))
        print(f"✅ Mode Switching: {'PASSED' if mode_result else 'FAILED'}")
    except Exception as e:
        test_results.append(("Mode Switching", False))
        print(f"❌ Mode Switching: FAILED - {e}")
    
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