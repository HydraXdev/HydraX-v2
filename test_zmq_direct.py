#!/usr/bin/env python3
"""
Direct ZMQ test to verify signal flow
"""

import zmq
import json
import time

def test_direct_zmq():
    """Test ZMQ directly"""
    context = zmq.Context()
    
    # Connect to command socket
    command_socket = context.socket(zmq.PUSH)
    command_socket.connect("tcp://localhost:5555")
    
    # Test signal
    signal = {
        "type": "signal",
        "signal_id": "DIRECT_TEST_001",
        "symbol": "EURUSD",
        "action": "buy",
        "lot": 0.01,
        "sl": 50,
        "tp": 100,
        "timestamp": time.time()
    }
    
    print("🧪 Direct ZMQ Test")
    print("="*50)
    print(f"📤 Sending signal: {signal['signal_id']}")
    print(f"   Symbol: {signal['symbol']} {signal['action'].upper()}")
    
    # Send signal
    command_socket.send_string(json.dumps(signal))
    print("✅ Signal sent to port 5555")
    
    # Test command
    command = {
        "type": "command",
        "command": "ping",
        "timestamp": time.time()
    }
    
    print("\n📤 Sending ping command")
    command_socket.send_string(json.dumps(command))
    print("✅ Ping sent")
    
    # Check controller logs
    print("\n📊 Check the fire publisher log for confirmation:")
    print("   tail -f zmq_fire_publisher.log")
    
    # Cleanup
    command_socket.close()
    context.term()
    
    print("\n✅ Test complete")

if __name__ == "__main__":
    test_direct_zmq()