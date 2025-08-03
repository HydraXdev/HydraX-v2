#!/usr/bin/env python3
"""Test PULL from port 5556 to see what EA is sending"""

import zmq
import json
import time

context = zmq.Context()
puller = context.socket(zmq.PULL)
puller.connect("tcp://127.0.0.1:5556")

print("🔍 Testing PULL from port 5556 (EA telemetry)...")
print("⏳ Waiting for data (10 seconds)...")

received = 0
start_time = time.time()

while time.time() - start_time < 10:
    try:
        # Try to receive with non-blocking
        message = puller.recv(zmq.NOBLOCK)
        received += 1
        
        # Try to decode as string
        try:
            msg_str = message.decode('utf-8')
            print(f"📡 String message {received}: {msg_str[:100]}...")
            
            # Try to parse as JSON
            try:
                data = json.loads(msg_str)
                print(f"   ✅ Valid JSON: {data.get('type', 'unknown')} - {data.get('symbol', 'N/A')}")
            except:
                print("   ⚠️ Not valid JSON")
                
        except:
            print(f"📡 Binary message {received}: {len(message)} bytes")
            
    except zmq.Again:
        time.sleep(0.1)
        continue
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(0.1)

if received > 0:
    print(f"\n✅ Received {received} messages from EA on port 5556")
else:
    print("\n⚠️ No messages received from EA")
    print("🔍 Possible issues:")
    print("   - EA may not be connected to 134.199.204.67:5556")
    print("   - EA may not be sending telemetry")
    print("   - Socket binding conflict")

context.term()