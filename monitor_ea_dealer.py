#!/usr/bin/env python3
"""
Monitor for EA DEALER socket connection in real-time
"""

import json
import threading
import time
from datetime import datetime

import zmq

print("=" * 70)
print("🔍 MONITORING FOR EA DEALER CONNECTION")
print("=" * 70)
print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
print("\n📡 Monitoring multiple channels for EA activity...")
print("=" * 70)

context = zmq.Context()

# Flag to track if we found the DEALER
dealer_found = threading.Event()
heartbeat_count = 0
tick_count = 0


def monitor_port_5560():
    """Monitor for heartbeats and ticks"""
    global heartbeat_count, tick_count

    sub = context.socket(zmq.SUB)
    sub.connect("tcp://localhost:5560")
    sub.subscribe(b"")
    sub.setsockopt(zmq.RCVTIMEO, 100)

    while not dealer_found.is_set():
        try:
            msg = sub.recv_string()
            data = json.loads(msg)

            if data.get("type") == "heartbeat":
                heartbeat_count += 1
                if heartbeat_count == 1:
                    print(f"\n💓 HEARTBEAT DETECTED! Balance: ${data.get('balance')}")

            elif data.get("type") == "tick":
                tick_count += 1

        except (zmq.Again, json.JSONDecodeError):
            pass

    sub.close()


def monitor_router_logs():
    """Check router logs for DEALER registration"""
    import subprocess

    checked = set()
    while not dealer_found.is_set():
        result = subprocess.run(
            ["pm2", "logs", "command_router", "--lines", "30", "--nostream"],
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL,
        )

        for line in result.stdout.split("\n"):
            if line and line not in checked:
                checked.add(line)

                if "COMMANDER_DEV_001" in line and any(x in line for x in ["learned", "identity", "DEALER"]):
                    print(f"\n🎯 DEALER REGISTERED: COMMANDER_DEV_001 connected!")
                    print(f"   Log: {line}")
                    dealer_found.set()
                    return

        time.sleep(1)


# Start monitoring threads
t1 = threading.Thread(target=monitor_port_5560, daemon=True)
t2 = threading.Thread(target=monitor_router_logs, daemon=True)

t1.start()
t2.start()

# Main monitoring loop
start_time = time.time()
last_status = 0

try:
    while not dealer_found.is_set():
        elapsed = int(time.time() - start_time)

        # Print status every 5 seconds
        if elapsed % 5 == 0 and elapsed != last_status:
            last_status = elapsed
            print(f"[{elapsed}s] Ticks: {tick_count} | Heartbeats: {heartbeat_count} | DEALER: Not connected")

            # Send another ping to try triggering registration
            if elapsed % 10 == 0:
                sender = context.socket(zmq.PUSH)
                sender.connect("ipc:///tmp/bitten_cmdqueue")
                ping = {
                    "type": "ping",
                    "target_uuid": "COMMANDER_DEV_001",
                    "ping_id": f"MONITOR_PING_{int(time.time())}",
                }
                sender.send_json(ping)
                sender.close()
                print(f"       → Sent ping to trigger DEALER registration")

        time.sleep(0.1)

        # Timeout after 60 seconds
        if elapsed > 60:
            print("\n⏱️ Timeout: No DEALER registration after 60 seconds")
            break

except KeyboardInterrupt:
    print("\n\n🛑 Monitoring stopped by user")

# Final status
print("\n" + "=" * 70)
print("📊 FINAL STATUS:")
print(f"  Ticks received: {tick_count}")
print(f"  Heartbeats received: {heartbeat_count}")
print(f"  DEALER connected: {'YES ✅' if dealer_found.is_set() else 'NO ❌'}")

if not dealer_found.is_set():
    print("\n🔧 TROUBLESHOOTING STEPS:")
    print("  1. Check MT5 Experts tab for errors")
    print("  2. Look for 'Socket DEALER' connection message")
    print("  3. Verify identity is set to 'COMMANDER_DEV_001'")
    print("  4. EA may need modification to send initial hello message")

    if heartbeat_count == 0 and tick_count > 0:
        print("\n  ⚠️ Note: Ticks flowing but no heartbeats - OnTimer() issue")

context.term()
print("=" * 70)
