#!/usr/bin/env python3
"""Test Elite Guard pattern detection with candle data"""

import zmq
import json
import time
from datetime import datetime

print("🧪 Testing Elite Guard Pattern Detection with Candle Data")
print("=" * 60)

# Connect to Elite Guard signal output
context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5557")
subscriber.subscribe(b"")
subscriber.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout

print("📡 Monitoring Elite Guard signals on port 5557...")
print("⏳ Waiting 60 seconds for pattern detection...")
print()

start_time = time.time()
signal_count = 0

while time.time() - start_time < 60:
    try:
        message = subscriber.recv_json()
        signal_count += 1
        
        print(f"\n🎯 SIGNAL #{signal_count} DETECTED!")
        print(f"Signal ID: {message.get('signal_id', 'unknown')}")
        print(f"Symbol: {message.get('symbol', 'unknown')}")
        print(f"Pattern: {message.get('pattern', 'unknown')}")
        print(f"Direction: {message.get('direction', 'unknown')}")
        print(f"Confidence: {message.get('confidence', 0)}%")
        print(f"Signal Type: {message.get('signal_type', 'unknown')}")
        print(f"Entry Price: {message.get('entry_price', 0)}")
        print(f"Stop Loss: {message.get('stop_loss', 0)}")
        print(f"Take Profit: {message.get('take_profit', 0)}")
        print(f"Risk/Reward: {message.get('risk_reward', 0)}")
        
    except zmq.error.Again:
        # No message, print status
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0:
            print(f"⏰ {elapsed}s elapsed... {signal_count} signals detected so far", end='\r')
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

print(f"\n\n📊 Test Complete!")
print(f"Total signals detected: {signal_count}")
print(f"Test duration: 60 seconds")

if signal_count == 0:
    print("\n⚠️ No signals detected. Possible issues:")
    print("1. Elite Guard may need more candle data to detect patterns")
    print("2. Market conditions may not match pattern criteria")
    print("3. Pattern detection thresholds may be too strict")
    print("4. Check Elite Guard logs for pattern scan activity")
else:
    print(f"\n✅ Success! Elite Guard is detecting patterns with candle data")
    print(f"Average signal rate: {signal_count / 60 * 60:.1f} signals per minute")