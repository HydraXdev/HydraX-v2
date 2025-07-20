#!/usr/bin/env python3
"""
Simple test script for the new fire_router.py implementation
Directly imports the module to avoid dependency issues
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to path
sys.path.insert(0, '/root/HydraX-v2/src')

def test_fire_router_basic():
    """Basic test of fire_router functionality"""
    
    print("🔥 FIRE ROUTER BASIC TEST")
    print("=" * 40)
    
    # Test 1: Import the module
    try:
        from bitten_core.fire_router import execute_trade
        print("✅ Successfully imported execute_trade function")
    except Exception as e:
        print(f"❌ Failed to import execute_trade: {e}")
        return False
    
    # Test 2: Set simulation mode
    os.environ["BITTEN_SIMULATION_MODE"] = "true"
    
    # Test 3: Create a simple mission
    mission = {
        "symbol": "EURUSD",
        "type": "buy",
        "lot_size": 0.01,
        "tp": 1.1000,
        "sl": 1.0950,
        "comment": "Test trade",
        "mission_id": "test_001"
    }
    
    print(f"Testing mission: {mission}")
    
    # Test 4: Execute trade
    try:
        result = execute_trade(mission)
        print(f"✅ Trade executed successfully: {result}")
        return result == "sent_to_bridge"
    except Exception as e:
        print(f"❌ Trade execution failed: {e}")
        return False

def test_socket_connection():
    """Test socket connection functionality"""
    
    print("\\n🔌 SOCKET CONNECTION TEST")
    print("=" * 40)
    
    try:
        # Import socket components
        from bitten_core.fire_router import BridgeConnectionManager
        
        # Create connection manager
        manager = BridgeConnectionManager(port=9999)  # Use invalid port to test error handling
        
        # Test health status
        health = manager.get_health_status()
        print(f"✅ Health status retrieved: {health}")
        
        # Test connection attempt (should fail gracefully)
        payload = {"test": "data"}
        result = manager.send_with_retry(payload)
        
        if not result["success"]:
            print(f"✅ Connection failed gracefully: {result['message']}")
            return True
        else:
            print(f"❌ Connection should have failed but succeeded: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Socket test failed: {e}")
        return False

def test_data_structures():
    """Test data structures and enums"""
    
    print("\\n📊 DATA STRUCTURES TEST")  
    print("=" * 40)
    
    try:
        from bitten_core.fire_router import (
            TradeRequest, 
            TradeDirection, 
            ExecutionMode,
            TradeExecutionResult
        )
        
        # Test TradeRequest creation
        request = TradeRequest(
            symbol="GBPUSD",
            direction=TradeDirection.BUY,
            volume=0.01,
            stop_loss=1.2950,
            take_profit=1.3050,
            comment="Test trade",
            mission_id="test_002"
        )
        
        print(f"✅ TradeRequest created: {request.symbol} {request.direction.value}")
        
        # Test payload conversion
        payload = request.to_bridge_payload()
        print(f"✅ Bridge payload created: {payload}")
        
        # Test result structure
        result = TradeExecutionResult(
            success=True,
            message="Test successful",
            trade_id="test_123"
        )
        
        print(f"✅ TradeExecutionResult created: {result.success} - {result.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data structures test failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 FIRE ROUTER SIMPLE TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_fire_router_basic),
        ("Socket Connection", test_socket_connection),
        ("Data Structures", test_data_structures)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Fire Router is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)