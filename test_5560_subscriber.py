#!/usr/bin/env python3
"""Test subscriber for port 5560"""

import zmq
import time

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://localhost:5560")
subscriber.setsockopt(zmq.SUBSCRIBE, b"")
subscriber.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout

print("🔍 Testing ZMQ subscriber on port 5560...")
print("⏳ Waiting for data (10 seconds)...")

received = 0
start_time = time.time()

while time.time() - start_time < 10:
    try:
        message = subscriber.recv_string(zmq.NOBLOCK)
        received += 1
        if received <= 3:
            print(f"📡 Got message {received}: {message[:100]}...")
    except zmq.Again:
        time.sleep(0.1)
        continue
    except Exception as e:
        print(f"Error: {e}")
        break

if received > 0:
    print(f"\n✅ SUCCESS: Received {received} messages on port 5560")
    print("📊 Data is flowing through the telemetry bridge!")
else:
    print("\n⚠️ No messages received on port 5560")
    print("🔍 Possible issues:")
    print("   - EA may not be sending data to port 5556")
    print("   - Telemetry republisher may not be forwarding")
    print("   - Market may be closed")

context.term()