#!/usr/bin/env python3
"""
Test ZMQ Signal Flow
Verifies the complete signal path from core to EA
"""

import os
import time
from zmq_bitten_controller import get_bitten_controller

# Ensure ZMQ is enabled
os.environ['USE_ZMQ'] = 'true'

def test_signal_flow():
    """Test complete signal flow"""
    print("🧪 Testing ZMQ Signal Flow")
    print("="*50)
    
    # Use execute_bitten_trade directly (controller already running)
    from zmq_bitten_controller import execute_bitten_trade
    
    # Test signal
    test_signal = {
        'signal_id': 'TEST_ZMQ_001',
        'symbol': 'EURUSD',
        'action': 'buy',
        'lot': 0.01,
        'sl': 50,
        'tp': 100
    }
    
    print(f"\n📤 Sending test signal: {test_signal['signal_id']}")
    print(f"   Symbol: {test_signal['symbol']}")
    print(f"   Action: {test_signal['action'].upper()}")
    print(f"   Lot: {test_signal['lot']}")
    
    # Define result callback
    result_received = False
    def on_result(result):
        nonlocal result_received
        result_received = True
        print(f"\n📥 Trade result received!")
        print(f"   Status: {result.status}")
        print(f"   Message: {result.message}")
        if result.status == 'success':
            print(f"   Ticket: {result.ticket}")
            print(f"   Price: {result.price}")
    
    # Send signal
    success = execute_bitten_trade(test_signal, callback=on_result)
    
    if success:
        print("✅ Signal sent successfully via ZMQ")
        
        # Wait for result
        print("\n⏳ Waiting for trade result...")
        for i in range(10):
            if result_received:
                break
            time.sleep(1)
            print(".", end="", flush=True)
        
        if not result_received:
            print("\n⚠️ No trade result received (EA may not be connected)")
    else:
        print("❌ Failed to send signal via ZMQ")
    
    # Check if we can access controller stats via the global instance
    print("\n📊 Checking controller status...")
    try:
        from zmq_bitten_controller import _controller_instance
        if _controller_instance:
            telemetry = _controller_instance.get_all_telemetry()
            if telemetry:
                for uuid, data in telemetry.items():
                    print(f"\n📈 User: {uuid}")
                    print(f"   Balance: ${data.balance:.2f}")
                    print(f"   Equity: ${data.equity:.2f}")
                    print(f"   Positions: {data.positions}")
            else:
                print("   No telemetry data received yet")
            
            # Check pending trades
            pending = _controller_instance.get_pending_trades()
            if pending:
                print(f"\n⏳ Pending trades: {len(pending)}")
                for signal_id, trade in pending.items():
                    print(f"   - {signal_id}: {trade['symbol']} {trade['action']}")
        else:
            print("   Controller instance not accessible")
    except Exception as e:
        print(f"   Could not access controller: {e}")
    
    print("\n" + "="*50)
    print("✅ Test complete")

if __name__ == "__main__":
    test_signal_flow()