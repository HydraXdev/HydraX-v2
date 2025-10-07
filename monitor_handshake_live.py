#!/usr/bin/env python3
"""
Monitor for EA v3.003 handshake in real-time
"""

import zmq
import json
import time
from datetime import datetime

print("=" * 70)
print("🔍 MONITORING FOR EA v3.003 HANDSHAKE")
print("=" * 70)
print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
print("\n✅ Router is ready on port 5555")
print("📡 Monitoring port 5560 for handshake and heartbeat...")
print("\n⚠️ NOW REMOVE AND RE-ATTACH THE EA IN MT5")
print("=" * 70)

context = zmq.Context()

# Monitor the published stream on port 5560
sub = context.socket(zmq.SUB)
sub.connect('tcp://localhost:5560')
sub.subscribe(b'')
sub.setsockopt(zmq.RCVTIMEO, 100)

handshake_found = False
heartbeat_found = False
tick_count = 0
start_time = time.time()

try:
    while True:
        try:
            msg = sub.recv_string()

            # Try to parse as JSON
            try:
                data = json.loads(msg)
                msg_type = data.get('type', 'unknown')

                # HANDSHAKE DETECTION
                if msg_type == 'handshake' and not handshake_found:
                    print(f"\n🎯🎯🎯 HANDSHAKE DETECTED at {datetime.now().strftime('%H:%M:%S')} 🎯🎯🎯")
                    print(json.dumps(data, indent=2))
                    print("\n✅ Key information extracted:")
                    print(f"   UUID: {data.get('uuid')}")
                    print(f"   Account: {data.get('account')}")
                    print(f"   Balance: ${data.get('balance')}")
                    print(f"   Equity: ${data.get('equity')}")
                    print(f"   Currency: {data.get('currency')}")
                    print(f"   Broker: {data.get('broker')}")
                    print(f"   Version: {data.get('version')}")
                    print("=" * 70)
                    handshake_found = True

                # HEARTBEAT DETECTION
                elif msg_type == 'heartbeat' and not heartbeat_found:
                    print(f"\n💓 HEARTBEAT DETECTED at {datetime.now().strftime('%H:%M:%S')}")
                    print(f"   Balance: ${data.get('balance')}")
                    print(f"   Equity: ${data.get('equity')}")
                    print(f"   Margin: ${data.get('margin')}")
                    print(f"   Free Margin: ${data.get('free_margin')}")
                    print(f"   Open Positions: {data.get('open_positions')}")
                    print(f"   Tick Count: {data.get('tick_count')}")
                    heartbeat_found = True

                # TICK COUNTING
                elif msg_type == 'tick':
                    tick_count += 1
                    if tick_count == 1:
                        print(f"\n📊 Ticks confirmed flowing (UUID: {data.get('uuid')})")

                # Exit if we found everything
                if handshake_found and heartbeat_found:
                    print("\n" + "=" * 70)
                    print("✅ COMPLETE: Both handshake and heartbeat received!")
                    print("=" * 70)
                    break

            except json.JSONDecodeError:
                pass

        except zmq.Again:
            # Timeout - print status
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                status = []
                if not handshake_found:
                    status.append("⏳ Waiting for handshake...")
                if not heartbeat_found:
                    status.append("⏳ Waiting for heartbeat...")
                if tick_count > 0:
                    status.append(f"✅ {tick_count} ticks received")

                if status:
                    print(f"[{elapsed}s] " + " | ".join(status))

except KeyboardInterrupt:
    print("\n\n🛑 Monitoring stopped")

finally:
    if not handshake_found:
        print("❌ No handshake detected - EA may need to be restarted")
    if not heartbeat_found:
        print("❌ No heartbeat detected - check OnTimer() in EA")

    sub.close()
    context.term()