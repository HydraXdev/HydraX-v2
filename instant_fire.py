#!/usr/bin/env python3
"""
Instant fire test - send immediately
"""
import json
import sys
import time
from collections import OrderedDict

import zmq

print("🚀 INSTANT FIRE TEST")
print("=" * 30)

# Create fire command directly
fire_cmd = OrderedDict(
    [
        ("type", "fire"),
        ("target_uuid", "COMMANDER_DEV_001"),
        ("fire_id", f"INSTANT_TEST_{int(time.time())}"),
        ("symbol", "EURUSD"),
        ("direction", "BUY"),
        ("entry", 0),
        ("sl", 1.1030),
        ("tp", 1.1080),
        ("lot", 0.01),
    ]
)

print(f"🔥 Fire ID: {fire_cmd['fire_id']}")
print(f"📊 Command: {dict(fire_cmd)}")

# Send directly to IPC queue
ctx = zmq.Context()
push = ctx.socket(zmq.PUSH)
push.connect("ipc:///tmp/bitten_cmdqueue")

push.send_json(dict(fire_cmd))
print("✅ Sent to command queue!")

push.close()
ctx.term()

print("\n⏱️ Check command_router logs in 2 seconds...")
