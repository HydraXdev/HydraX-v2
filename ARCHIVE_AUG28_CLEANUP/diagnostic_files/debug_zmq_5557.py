#!/usr/bin/env python3
"""
Debug what's being published to port 5557
"""

import zmq
import time

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5557")
subscriber.subscribe(b'')  # Subscribe to everything

print("🔍 Listening on port 5557 for 10 seconds...")
print("=" * 50)

start_time = time.time()
message_count = 0

while time.time() - start_time < 10:
    try:
        subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        message = subscriber.recv()  # Receive as bytes
        message_count += 1
        
        print(f"\n📨 Message {message_count}:")
        print(f"   Raw bytes: {message[:100]}...")  # First 100 bytes
        
        # Try to decode as string
        try:
            msg_str = message.decode('utf-8')
            print(f"   As string: {msg_str[:200]}...")  # First 200 chars
            
            # Check if it's empty
            if not msg_str or msg_str.strip() == "":
                print("   ⚠️ EMPTY MESSAGE!")
            elif msg_str.startswith("ELITE_GUARD_SIGNAL "):
                print("   ✅ Valid Elite Guard signal prefix detected")
                json_part = msg_str[19:]
                print(f"   JSON part: {json_part[:100]}...")
            else:
                print(f"   ❓ Unknown format")
                
        except UnicodeDecodeError:
            print("   ❌ Cannot decode as UTF-8")
            
    except zmq.Again:
        # Timeout - no message
        pass
    except Exception as e:
        print(f"   Error: {e}")

print(f"\n📊 Summary: Received {message_count} messages in 10 seconds")

subscriber.close()
context.term()