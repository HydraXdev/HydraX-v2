#!/usr/bin/env python3
"""
Trigger EA DEALER socket registration with broadcast ping
"""

import json
import time

import zmq

print("=" * 60)
print("🎯 TRIGGERING EA DEALER HANDSHAKE")
print("=" * 60)

context = zmq.Context()

# Connect to IPC queue (same as webapp uses)
sender = context.socket(zmq.PUSH)
sender.connect("ipc:///tmp/bitten_cmdqueue")

# Send ping WITHOUT target_uuid to force broadcast
ping = {
    "type": "ping",
    "ping_id": f"BROADCAST_{int(time.time())}",
    # NO target_uuid - forces router to broadcast to all DEALERs
}

print(f"📤 Sending broadcast ping: {ping['ping_id']}")
sender.send_json(ping)
sender.close()

# Give router time to process
time.sleep(1)

# Check if COMMANDER_DEV_001 registered
print("\n🔍 Checking command router for EA identity...")

import subprocess

result = subprocess.run(
    ["pm2", "logs", "command_router", "--lines", "10", "--nostream"], capture_output=True, text=True
)

if "COMMANDER_DEV_001" in result.stdout and ("learned" in result.stdout or "pong" in result.stdout):
    print("✅ SUCCESS: COMMANDER_DEV_001 registered with router!")
    print("   EA DEALER socket is now active and routable")
elif "TEST_CLIENT_001" in result.stdout:
    print("⚠️ Still seeing TEST_CLIENT_001 only")
    print("   EA may not have responded to ping yet")
else:
    print("❌ No EA identity found in router logs")

# Also check for heartbeats on 5560
print("\n💓 Checking for heartbeats on port 5560...")

sub = context.socket(zmq.SUB)
sub.connect("tcp://localhost:5560")
sub.subscribe(b"")
sub.setsockopt(zmq.RCVTIMEO, 2000)

heartbeat_count = 0
tick_count = 0

for i in range(3):  # Check for 3 seconds
    try:
        msg = sub.recv_string()
        data = json.loads(msg)

        if data.get("type") == "heartbeat":
            heartbeat_count += 1
            print(f"✅ Heartbeat detected! Balance: ${data.get('balance')}, Equity: ${data.get('equity')}")
        elif data.get("type") == "tick":
            tick_count += 1
    except zmq.Again:
        pass
    except json.JSONDecodeError:
        pass

print(f"\n📊 Results in 3 seconds:")
print(f"   Heartbeats: {heartbeat_count}")
print(f"   Ticks: {tick_count}")

if heartbeat_count == 0 and tick_count > 0:
    print("\n⚠️ Ticks flowing but no heartbeats - OnTimer() may not be firing")
    print("   EA should send heartbeats every second via EventSetTimer(1)")

sub.close()
context.term()

print("\n" + "=" * 60)
print("Next: Try sending a fire command now that DEALER is registered")
print("=" * 60)
