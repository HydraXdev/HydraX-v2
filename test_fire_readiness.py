#!/usr/bin/env python3
"""
Test Fire Readiness - Verify enhanced bridge is ready for trade execution
"""

import socket
import json
import sys
import time
sys.path.append('/root/HydraX-v2/src/bitten_core')

from fire_router import FireRouter, TradeRequest, TradeDirection

def test_socket_connection():
    """Test direct socket connection to enhanced bridge"""
    print("🧪 Testing Socket Connection...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('3.145.84.187', 9000))
        
        # Send ping command
        ping_command = json.dumps({'command': 'ping'})
        sock.send(ping_command.encode('utf-8'))
        
        # Receive response
        response = sock.recv(4096)
        result = json.loads(response.decode('utf-8'))
        
        sock.close()
        
        print("✅ Socket Connection: SUCCESS")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Account: {result.get('account', 'N/A')}")
        print(f"   Broker: {result.get('broker', 'N/A')}")
        print(f"   Balance: {result.get('balance', 'N/A')}")
        print(f"   Symbols: {len(result.get('symbols', []))} available")
        return True
        
    except Exception as e:
        print(f"❌ Socket Connection: FAILED - {e}")
        return False

def test_fire_execution():
    """Test fire execution through FireRouter"""
    print("\n🔥 Testing Fire Execution...")
    
    try:
        # Create FireRouter pointing to AWS bridge
        router = FireRouter(
            bridge_host='3.145.84.187',
            bridge_port=5555  # HTTP port, will route to socket
        )
        
        # Create test trade request
        test_request = TradeRequest(
            symbol="EURUSD",
            direction=TradeDirection.BUY,
            volume=0.01,
            stop_loss=1.0800,
            take_profit=1.0950,
            comment="Fire readiness test",
            user_id="test_user",
            mission_id="readiness_test_001",
            tcs_score=85.0
        )
        
        # Execute trade
        result = router.execute_trade_request(test_request)
        
        if result.success:
            print("✅ Fire Execution: SUCCESS")
            print(f"   Message: {result.message}")
            print(f"   Ticket: {result.ticket}")
            print(f"   Execution Time: {result.execution_time_ms}ms")
            return True
        else:
            print("❌ Fire Execution: FAILED")
            print(f"   Error: {result.message}")
            print(f"   Error Code: {result.error_code}")
            return False
            
    except Exception as e:
        print(f"❌ Fire Execution: EXCEPTION - {e}")
        return False

def main():
    """Main test function"""
    print("🎯 FIRE READINESS TEST")
    print("=" * 40)
    print("Testing enhanced MT5 bridge for trade execution")
    print()
    
    # Test 1: Socket connection
    socket_ok = test_socket_connection()
    
    # Test 2: Fire execution
    fire_ok = test_fire_execution()
    
    # Results
    print("\n📊 READINESS RESULTS")
    print("=" * 20)
    print(f"Socket Connection: {'✅ READY' if socket_ok else '❌ NOT READY'}")
    print(f"Fire Execution: {'✅ READY' if fire_ok else '❌ NOT READY'}")
    
    if socket_ok and fire_ok:
        print("\n🎉 BRIDGE IS READY FOR LIVE TRADING!")
        print("🔥 Fire commands will execute real MT5 trades")
    else:
        print("\n⚠️ BRIDGE NOT READY")
        print("Complete the Windows RDT setup steps")
    
    return socket_ok and fire_ok

if __name__ == "__main__":
    main()