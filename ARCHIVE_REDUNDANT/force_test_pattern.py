#!/usr/bin/env python3
"""
Force a test pattern to verify Elite Guard logic
"""
import zmq
import json
import time

# Create test conditions that should trigger a pattern
context = zmq.Context()
publisher = context.socket(zmq.PUB)
publisher.connect("tcp://127.0.0.1:5556")  # Send to telemetry bridge

print("🔧 Sending test pattern conditions...")

# Simulate a liquidity sweep on EURUSD
# Need rapid price movement to trigger detection
base_price = 1.1555

for i in range(30):
    # Create price spike
    if i == 15:
        # Big spike up (should trigger liquidity sweep)
        bid = base_price + 0.0010  # 10 pips up
        ask = bid + 0.00013
        volume = 1000  # High volume
    elif i == 16:
        # Quick reversal
        bid = base_price - 0.0005  # 5 pips down
        ask = bid + 0.00013
        volume = 800
    else:
        # Normal movement
        bid = base_price + (i * 0.00001)
        ask = bid + 0.00013
        volume = 100
    
    tick = {
        "type": "tick",
        "symbol": "EURUSD",
        "bid": bid,
        "ask": ask,
        "spread": round((ask - bid) * 10000, 1),
        "volume": volume,
        "timestamp": int(time.time())
    }
    
    publisher.send_json(tick)
    print(f"Sent tick {i+1}: EURUSD @ {bid:.5f} vol={volume}")
    time.sleep(0.5)  # Send every 500ms

print("\n✅ Test pattern sent. Check Elite Guard logs for detection.")