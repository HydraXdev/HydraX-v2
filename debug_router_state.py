#!/usr/bin/env python3
import zmq
import json
import time

# Connect to the router and check its state
ctx = zmq.Context()

# Try to see what the router is seeing
print("=== CHECKING ROUTER STATE ===")

# Test the IPC queue directly
try:
    test_socket = ctx.socket(zmq.PUSH)
    test_socket.setsockopt(zmq.LINGER, 0)
    test_socket.connect('ipc:///tmp/bitten_cmdqueue')
    
    debug_cmd = {
        'type': 'debug', 
        'fire_id': f'debug_{int(time.time())}',
        'target_uuid': 'COMMANDER_DEV_001',
        'symbol': 'EURUSD',
        'debug': True
    }
    
    print(f"Sending debug command: {debug_cmd}")
    test_socket.send_json(debug_cmd)
    test_socket.close()
    
except Exception as e:
    print(f"Error testing IPC queue: {e}")

# Check if we can connect as a DEALER
try:
    dealer = ctx.socket(zmq.DEALER)
    dealer.setsockopt_string(zmq.IDENTITY, "DEBUG_CLIENT")
    dealer.setsockopt(zmq.RCVTIMEO, 2000)
    dealer.connect("tcp://localhost:5555")
    
    # Send a hello to register
    hello = {
        "type": "HELLO",
        "target_uuid": "DEBUG_CLIENT", 
        "ts": int(time.time())
    }
    dealer.send_string(json.dumps(hello))
    
    # Try to receive anything
    try:
        response = dealer.recv_string()
        print(f"Router response: {response}")
    except zmq.Again:
        print("No response from router (expected)")
        
    dealer.close()
    
except Exception as e:
    print(f"Error testing DEALER connection: {e}")

ctx.term()
print("Debug complete")