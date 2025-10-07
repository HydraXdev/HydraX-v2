#!/usr/bin/env python3
"""
Monitor for EA v3.003 handshake and heartbeat messages
"""

import zmq
import json
import time
from datetime import datetime

def main():
    context = zmq.Context()

    # Connect to port 5556 directly (PULL pattern)
    print("🔌 Creating PULL socket to receive from EA...")
    receiver = context.socket(zmq.PULL)
    receiver.connect("tcp://localhost:5556")  # Connect to existing binding
    receiver.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout

    print(f"📡 Monitoring port 5556 for EA messages...")
    print(f"⏰ Started at {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

    message_types = {}
    last_handshake = None
    last_heartbeat = None

    try:
        for i in range(60):  # Monitor for up to 60 seconds
            try:
                # Receive message
                message = receiver.recv_string()

                # Try to parse as JSON
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')

                    # Count message types
                    message_types[msg_type] = message_types.get(msg_type, 0) + 1

                    # Handle special message types
                    if msg_type == 'handshake':
                        print(f"\n🤝 HANDSHAKE RECEIVED at {datetime.now().strftime('%H:%M:%S')}!")
                        print(f"   UUID: {data.get('uuid')}")
                        print(f"   Account: {data.get('account')}")
                        print(f"   Balance: {data.get('balance')}")
                        print(f"   Equity: {data.get('equity')}")
                        print(f"   Currency: {data.get('currency')}")
                        print(f"   Broker: {data.get('broker')}")
                        print(f"   Version: {data.get('version')}")
                        last_handshake = data

                    elif msg_type == 'heartbeat':
                        if not last_heartbeat:  # Only print first heartbeat
                            print(f"\n💓 HEARTBEAT RECEIVED at {datetime.now().strftime('%H:%M:%S')}!")
                            print(f"   Balance: {data.get('balance')}")
                            print(f"   Equity: {data.get('equity')}")
                            print(f"   Margin: {data.get('margin')}")
                            print(f"   Free Margin: {data.get('free_margin')}")
                            print(f"   Open Positions: {data.get('open_positions')}")
                        last_heartbeat = data

                    elif msg_type == 'tick' and len(message_types) == 1:
                        # Only show tick info if it's the only type we're seeing
                        if message_types['tick'] == 1:
                            print(f"\n📊 TICKS FLOWING (first tick at {datetime.now().strftime('%H:%M:%S')})")
                            print(f"   Symbol: {data.get('symbol')}")
                            print(f"   Bid: {data.get('bid')}")
                            print(f"   Ask: {data.get('ask')}")

                except json.JSONDecodeError:
                    # Not JSON, might be prefixed message
                    if message.startswith("HEARTBEAT") and "HEARTBEAT" not in message_types:
                        print(f"\n💓 HEARTBEAT (non-JSON) at {datetime.now().strftime('%H:%M:%S')}")
                        message_types["HEARTBEAT"] = 1

            except zmq.Again:
                # Timeout - no message received
                pass

            # Print status every 10 seconds
            if i > 0 and i % 10 == 0:
                print(f"\n📊 Status after {i} seconds:")
                for msg_type, count in message_types.items():
                    print(f"   {msg_type}: {count} messages")

    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")

    finally:
        # Print final summary
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)

        if last_handshake:
            print(f"✅ Handshake received from {last_handshake.get('uuid')}")
            print(f"   Account: {last_handshake.get('account')}")
            print(f"   Balance: ${last_handshake.get('balance')}")
        else:
            print("❌ No handshake received")

        if last_heartbeat:
            print(f"✅ Heartbeats active")
            print(f"   Last balance: ${last_heartbeat.get('balance')}")
            print(f"   Last equity: ${last_heartbeat.get('equity')}")
        else:
            print("❌ No heartbeats received")

        print(f"\n📊 Message type counts:")
        for msg_type, count in message_types.items():
            print(f"   {msg_type}: {count}")

        receiver.close()
        context.term()

if __name__ == "__main__":
    main()