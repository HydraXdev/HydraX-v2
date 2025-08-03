#!/usr/bin/env python3
"""Final test of port 5560 subscriber"""

import zmq
import json
import time

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5560")
subscriber.setsockopt(zmq.SUBSCRIBE, b"")

print("🔍 Testing subscriber on port 5560...")
print("⏳ Waiting for data (10 seconds)...")

received = 0
start_time = time.time()
symbols = set()

while time.time() - start_time < 10:
    try:
        # Try to receive JSON
        data = subscriber.recv_json(zmq.NOBLOCK)
        received += 1
        
        if 'symbol' in data:
            symbols.add(data['symbol'])
            
        if received <= 3:
            print(f"✅ Message {received}: {data.get('type', 'unknown')} - "
                  f"{data.get('symbol', data.get('uuid', 'N/A'))}")
            if 'bid' in data:
                print(f"   Tick: {data['bid']}/{data['ask']}")
                
    except zmq.Again:
        time.sleep(0.1)
    except Exception as e:
        if received == 0:
            time.sleep(0.1)

print(f"\n📊 Summary:")
print(f"   Messages received: {received}")
print(f"   Symbols: {', '.join(sorted(symbols))}")

if received > 0:
    print("\n✅ SUCCESS! Elite Guard data feed is ACTIVE!")
    print("🎯 Elite Guard should now be receiving ticks and hunting for SMC patterns")
else:
    print("\n⚠️ No messages received on port 5560")

context.term()