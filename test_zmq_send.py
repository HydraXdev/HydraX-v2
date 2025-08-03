#!/usr/bin/env python3
"""Test ZMQ message sending to controller"""

import zmq
import json
import time

# Connect to controller
context = zmq.Context()
push_socket = context.socket(zmq.PUSH)
push_socket.connect("tcp://127.0.0.1:5555")

# Send test messages
for i in range(5):
    # Create proper EA message format
    message = {
        "ea_id": "TEST_EA_12345",
        "type": "market_data",
        "data": {
            "symbol": "EURUSD",
            "bid": 1.0850 + i * 0.0001,
            "ask": 1.0851 + i * 0.0001,
            "spread": 1.0,
            "volume": 1000,
            "timestamp": int(time.time()),
            "broker": "Test Broker",
            "source": "MT5_LIVE"
        }
    }
    
    # Send as JSON string
    json_str = json.dumps(message)
    push_socket.send_string(json_str)
    print(f"Sent: {json_str}")
    time.sleep(1)

# Send heartbeat
heartbeat = {
    "ea_id": "TEST_EA_12345",
    "type": "heartbeat",
    "timestamp": int(time.time())
}
push_socket.send_string(json.dumps(heartbeat))
print("Sent heartbeat")

push_socket.close()
context.term()
print("Test complete")