#!/usr/bin/env python3
"""
Monitor ZMQ data coming from EA on port 5555
"""
import zmq
import json
import time
import sys

def monitor_zmq_data(port=5555):
    context = zmq.Context()
    
    # Connect as PULL to see what's being sent to port 5555
    socket = context.socket(zmq.PULL) 
    socket.connect(f"tcp://localhost:{port}")
    socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout
    
    print(f"🔍 Monitoring ZMQ data on port {port}...")
    print("Press Ctrl+C to stop")
    
    message_count = 0
    start_time = time.time()
    
    try:
        while True:
            try:
                # Try to receive message
                message = socket.recv_string()
                message_count += 1
                
                print(f"\n📨 Message #{message_count} received:")
                print("-" * 50)
                
                # Try to parse as JSON
                try:
                    data = json.loads(message)
                    print(f"JSON Keys: {list(data.keys())}")
                    
                    # If it has ticks, show tick info
                    if 'ticks' in data:
                        ticks = data['ticks']
                        print(f"Ticks count: {len(ticks)}")
                        if len(ticks) > 0:
                            first_tick = ticks[0]
                            print(f"First tick: {first_tick.get('symbol')} {first_tick.get('bid')}/{first_tick.get('ask')}")
                    
                    # If it's a single tick
                    elif 'symbol' in data:
                        print(f"Single tick: {data.get('symbol')} {data.get('bid')}/{data.get('ask')}")
                    
                    # Show full data if small
                    if len(message) < 500:
                        print(f"Full data: {message}")
                    else:
                        print(f"Large message ({len(message)} chars), truncated...")
                        
                except json.JSONDecodeError:
                    print(f"Non-JSON message: {message[:200]}...")
                
                # Show stats every 10 messages
                if message_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = message_count / elapsed if elapsed > 0 else 0
                    print(f"\n📊 Stats: {message_count} messages, {rate:.2f} msg/sec")
                    
            except zmq.Again:
                print("⏳ No message received (timeout)")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print(f"\n🛑 Stopped. Total messages: {message_count}")
    
    socket.close()
    context.term()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5555
    monitor_zmq_data(port)