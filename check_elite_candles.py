#!/usr/bin/env python3
"""Check if Elite Guard is processing candle batches"""

import zmq
import json
import time
from datetime import datetime

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5560")
subscriber.subscribe(b"")

print("🔍 Monitoring Elite Guard data feed on port 5560...")
print("=" * 60)

candle_count = 0
tick_count = 0
start_time = time.time()

# Monitor for 10 seconds
while time.time() - start_time < 10:
    try:
        subscriber.setsockopt(zmq.RCVTIMEO, 100)
        message = subscriber.recv_json()
        
        msg_type = message.get('type', 'unknown')
        
        if msg_type == 'candle_batch':
            candle_count += 1
            symbol = message.get('symbol', 'unknown')
            timestamp = message.get('timestamp', 0)
            
            print(f"\n✅ CANDLE BATCH #{candle_count}")
            print(f"   Symbol: {symbol}")
            print(f"   Time: {datetime.fromtimestamp(timestamp)}")
            
            # Check timeframes
            for tf in ['M1', 'M5', 'M15']:
                if tf in message and message[tf]:
                    candles = message[tf]
                    print(f"   {tf}: {len(candles)} candles")
                    if candles:
                        latest = candles[0]
                        print(f"      Latest: {datetime.fromtimestamp(latest['time'])} O={latest['open']} H={latest['high']} L={latest['low']} C={latest['close']}")
                        
        elif msg_type == 'tick':
            tick_count += 1
            if tick_count % 20 == 0:
                print(f".", end="", flush=True)
                
    except zmq.error.Again:
        pass
    except Exception as e:
        print(f"\n❌ Error: {e}")

print(f"\n\n📊 Summary in 10 seconds:")
print(f"   Candle batches: {candle_count}")
print(f"   Ticks: {tick_count}")
print(f"   Candle rate: {candle_count/10:.1f} per second")

# Now check if Elite Guard has the data listener
print("\n🔍 Checking Elite Guard data structures...")
try:
    # Read the Elite Guard script to see if it has candle handling
    with open('/root/HydraX-v2/elite_guard_with_citadel.py', 'r') as f:
        content = f.read()
        if 'candle_batch' in content:
            print("✅ Elite Guard has candle_batch handling code")
        else:
            print("❌ Elite Guard missing candle_batch handling")
            
        if 'market_data' in content and 'buffer' in content:
            print("✅ Elite Guard has market data buffering")
        else:
            print("❌ Elite Guard missing data buffering")
            
except Exception as e:
    print(f"❌ Could not check Elite Guard code: {e}")