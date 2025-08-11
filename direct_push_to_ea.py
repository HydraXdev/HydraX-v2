#!/usr/bin/env python3
"""
BIND to port 5555 and push fire command to EA
EA is PULL client, we must be PUSH server
"""

import zmq
import json
import time
from datetime import datetime

context = zmq.Context()

# BIND as PUSH server (EA connects as PULL client)
pusher = context.socket(zmq.PUSH)
pusher.bind("tcp://*:5555")
print("✅ Bound to port 5555 as PUSH server")
print("⏳ Waiting for EA to connect...")
time.sleep(2)  # Give EA time to reconnect

# Create fire command
fire_command = {
    "type": "fire",
    "target_uuid": "COMMANDER_DEV_001",
    "symbol": "GBPUSD",
    "entry": 0,  # Market order
    "sl": 20,    # 20 pips SL
    "tp": 40,    # 40 pips TP
    "lot": 0.01,
    "timestamp": datetime.utcnow().isoformat()
}

print("\n" + "=" * 60)
print("SENDING FIRE COMMAND TO EA")
print("=" * 60)
print(f"Time: {datetime.now()}")
print(json.dumps(fire_command, indent=2))

# Send multiple times to ensure delivery
for i in range(3):
    pusher.send_json(fire_command)
    print(f"✅ Sent attempt {i+1}/3")
    time.sleep(0.5)

print("\n📡 Command sent to EA on port 5555")
print("Check MT5 terminal for execution")

# Keep socket open briefly
time.sleep(5)

pusher.close()
context.term()
print("\n✅ Done")