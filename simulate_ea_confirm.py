#!/usr/bin/env python3
"""Simulate EA confirmation on port 5558"""
import zmq
import json
import time

# Prepare confirmation
confirm = {
    "fire_id": "fir_b1fba4e534a9",
    "status": "FILLED",
    "ticket": 19059064,
    "price": 1.08505,
    "symbol": "EURUSD",
    "side": "BUY"
}

print(f"📤 Simulating EA confirmation for fire_id: {confirm['fire_id']}")

# Publish to port 5558
ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://127.0.0.1:5558")

# Give socket time to bind
time.sleep(1)

# Send confirmation
message = json.dumps(confirm)
print(f"📡 Publishing: {message}")

# Send multiple times to ensure delivery
for i in range(5):
    pub.send_string(message)
    print(f"   Sent #{i+1}")
    time.sleep(0.2)

print(f"✅ Confirmation sent for fire_id: {confirm['fire_id']}")

pub.close()
ctx.term()