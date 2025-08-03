#!/usr/bin/env python3
"""Test ZMQ data flow"""

import zmq
import time
import json

context = zmq.Context()

# Test telemetry subscriber
print("🔍 Testing ZMQ telemetry flow on port 5556...")
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5556")
subscriber.setsockopt(zmq.SUBSCRIBE, b"")
subscriber.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout

received = 0
print("⏳ Waiting for data (10 seconds)...")

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
    print(f"\n✅ SUCCESS: Received {received} messages in 10 seconds")
    print("📊 ZMQ telemetry stream is ACTIVE and flowing!")
else:
    print("\n❌ WARNING: No messages received")
    print("🔍 Possible issues:")
    print("   - Telemetry daemon may not be sending data")
    print("   - Market may be closed (weekend)")
    print("   - EA may not be connected")

# Check signal publisher
print("\n🔍 Checking Elite Guard publisher on port 5557...")
pub_sub = context.socket(zmq.SUB)
pub_sub.connect("tcp://127.0.0.1:5557")
pub_sub.setsockopt(zmq.SUBSCRIBE, b"")
pub_sub.setsockopt(zmq.RCVTIMEO, 2000)

try:
    signal = pub_sub.recv_string()
    print("✅ Elite Guard is publishing signals!")
except zmq.Again:
    print("⏳ No signals yet (this is normal if no patterns detected)")

context.term()