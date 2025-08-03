#!/usr/bin/env python3
"""Monitor ZMQ port 5560 for candle_batch messages"""

import zmq
import json
import time

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5560")
subscriber.subscribe(b"")  # Subscribe to all messages

print("🔍 Monitoring port 5560 for candle_batch messages...")
print("=" * 60)

candle_count = 0
tick_count = 0
other_count = 0

while True:
    try:
        # Receive with timeout
        subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        message = subscriber.recv_json()
        
        msg_type = message.get('type', 'unknown')
        
        if msg_type == 'candle_batch':
            candle_count += 1
            print(f"\n✅ CANDLE BATCH #{candle_count} from {message.get('symbol', 'unknown')}")
            print(f"   Timestamp: {message.get('timestamp', 'N/A')}")
            
            # Show timeframes available
            for tf in ['M1', 'M5', 'M15']:
                if tf in message:
                    candle_data = message[tf]
                    if candle_data:
                        print(f"   {tf}: {len(candle_data)} candles")
                        # Show first candle
                        first = candle_data[0]
                        print(f"      Latest: O={first.get('open')} H={first.get('high')} L={first.get('low')} C={first.get('close')}")
                        
        elif msg_type == 'tick':
            tick_count += 1
            if tick_count % 10 == 0:  # Show every 10th tick
                print(f"📊 Tick #{tick_count}: {message.get('symbol')} {message.get('bid')}/{message.get('ask')}")
                
        elif msg_type == 'heartbeat':
            # Skip heartbeats
            pass
        else:
            other_count += 1
            print(f"❓ Other message type: {msg_type}")
            
    except zmq.error.Again:
        # Timeout - no message received
        print(".", end="", flush=True)
    except json.JSONDecodeError:
        print("❌ Non-JSON message received")
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(1)