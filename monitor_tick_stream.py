#!/usr/bin/env python3
"""
Quick monitor to see what tick data looks like from the ZMQ stream
"""
import zmq
import json
import time
import sys

def monitor_ticks():
    ctx = zmq.Context()

    # Connect to both potential tick ports
    sock1 = ctx.socket(zmq.SUB)
    sock1.connect("tcp://localhost:5556")  # EA input
    sock1.setsockopt(zmq.SUBSCRIBE, b"")
    sock1.setsockopt(zmq.RCVTIMEO, 500)

    sock2 = ctx.socket(zmq.SUB)
    sock2.connect("tcp://localhost:5560")  # Redistributed
    sock2.setsockopt(zmq.SUBSCRIBE, b"")
    sock2.setsockopt(zmq.RCVTIMEO, 500)

    print("🔍 Monitoring tick streams on ports 5556 & 5560...")
    print("=" * 60)

    start_time = time.time()
    tick_count = 0

    try:
        while time.time() - start_time < 15:  # Monitor for 15 seconds
            # Check port 5556
            try:
                msg = sock1.recv_string()
                print(f"📥 PORT 5556: {msg[:200]}...")
                tick_count += 1
            except zmq.Again:
                pass

            # Check port 5560
            try:
                msg = sock2.recv_string()
                print(f"📤 PORT 5560: {msg[:200]}...")

                # Try to parse as JSON and look for tick-like data
                try:
                    data = json.loads(msg)
                    msg_type = data.get('type', 'unknown')

                    if 'tick' in msg_type.lower() or 'bid' in data or 'ask' in data:
                        tick_count += 1
                        print(f"🎯 TICK #{tick_count}: {json.dumps(data, indent=2)}")
                        print("-" * 40)
                    elif msg_type == "HEARTBEAT_METRICS":
                        print(f"💰 METRICS: Account={data.get('account')}, Equity=${data.get('equity', 0):.2f}, Positions={data.get('open_positions', 0)}")
                    else:
                        print(f"📋 OTHER: {msg_type}")

                except json.JSONDecodeError:
                    print(f"📄 NON-JSON: {msg[:100]}...")

            except zmq.Again:
                pass

    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")

    print(f"\n📊 Summary: Received {tick_count} messages in 15 seconds")
    sock1.close()
    sock2.close()
    ctx.term()

if __name__ == "__main__":
    monitor_ticks()