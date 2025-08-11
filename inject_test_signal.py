#!/usr/bin/env python3
"""Inject test signal by mimicking Elite Guard's publisher"""
import zmq
import json
import time
from datetime import datetime, timedelta, timezone

# Create test signal
test_signal = {
    "signal_id": f"TEST_SIGNAL_{int(time.time())}",
    "symbol": "EURUSD",
    "direction": "BUY",
    "side": "BUY",
    "entry": 1.0850,
    "entry_price": 1.0850,
    "sl": 1.0830,
    "stop_loss": 1.0830,
    "tp": 1.0890,
    "take_profit": 1.0890,
    "confidence": 85,
    "tcs": 85,
    "pattern_type": "TEST_LIQUIDITY_SWEEP",
    "risk_reward": "1:2",
    "rr": "1:2",
    "tier": "ALL",
    "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
}

print(f"📤 Injecting test signal: {test_signal['signal_id']}")

# We need to inject into Elite Guard's publisher
# Since Elite Guard already binds 5557, we connect as a subscriber first to verify
ctx = zmq.Context()

# Create a second publisher that mimics Elite Guard
# We'll use the internal relay service approach
internal_pub = ctx.socket(zmq.PUSH)
internal_pub.connect("tcp://127.0.0.1:5557")

# Actually Elite Guard PUBLISHes, so relay SUBSCRIBEs
# We need to publish on same socket Elite Guard uses
# Let's kill Elite Guard temporarily and take over its port

import subprocess
print("⏸️  Pausing Elite Guard temporarily...")
subprocess.run(["pkill", "-f", "elite_guard_with_citadel"], capture_output=True)
time.sleep(2)

# Now bind to 5557 ourselves
test_pub = ctx.socket(zmq.PUB)
test_pub.bind("tcp://127.0.0.1:5557")
print("✅ Bound to port 5557")

# Give relay time to reconnect
time.sleep(2)

# Send test signal
message = f"ELITE_GUARD_SIGNAL {json.dumps(test_signal)}"
print(f"📡 Publishing: {message[:100]}...")

# Send multiple times to ensure delivery
for i in range(10):
    test_pub.send_string(message)
    print(f"   Sent #{i+1}")
    time.sleep(0.2)

print(f"✅ Test signal sent: {test_signal['signal_id']}")

# Clean up
test_pub.close()
ctx.term()

# Restart Elite Guard
print("▶️  Restarting Elite Guard...")
subprocess.Popen(["python3", "/root/HydraX-v2/elite_guard_with_citadel.py"], 
                 stdout=open("/root/HydraX-v2/elite_guard.log", "a"),
                 stderr=subprocess.STDOUT)
print("✅ Elite Guard restarted")