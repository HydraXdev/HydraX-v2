#!/usr/bin/env python3
"""Test Elite Guard data reception on port 5560"""

import zmq
import json
import time

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5560")
subscriber.setsockopt(zmq.SUBSCRIBE, b"")
subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout

print("🔍 Testing Elite Guard data reception on port 5560...")
print("⏳ Waiting for tick data...")

received = 0
start_time = time.time()
symbols_seen = set()

while time.time() - start_time < 30:  # Run for 30 seconds
    try:
        # Try receiving as JSON directly
        try:
            message = subscriber.recv_json(zmq.NOBLOCK)
            received += 1
            symbol = message.get('symbol', 'UNKNOWN')
            symbols_seen.add(symbol)
            
            if received <= 5 or received % 100 == 0:
                print(f"📡 JSON message {received}: {symbol} @ {message.get('bid', 'N/A')}/{message.get('ask', 'N/A')}")
        except:
            # Fall back to string
            message = subscriber.recv_string(zmq.NOBLOCK)
            received += 1
            
            if received <= 5:
                print(f"📡 String message {received}: {message[:100]}...")
                
    except zmq.Again:
        # No message, just wait
        time.sleep(0.1)
        continue
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(0.1)

print(f"\n📊 Summary after 30 seconds:")
print(f"   Messages received: {received}")
print(f"   Symbols seen: {', '.join(sorted(symbols_seen)) if symbols_seen else 'None'}")

if received > 0:
    print("✅ Elite Guard data feed is ACTIVE!")
    print("🎯 Ready to hunt for SMC patterns")
else:
    print("⚠️ No data received - checking telemetry bridge...")

context.term()