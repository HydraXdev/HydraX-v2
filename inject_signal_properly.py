#!/usr/bin/env python3
"""
Properly inject signal by publishing to port 5557
Acts as a replacement for Elite Guard for testing
"""

import zmq
import json
import time
from datetime import datetime

print("=" * 60)
print("SIGNAL INJECTION TEST")
print("=" * 60)

context = zmq.Context()

# We need to temporarily replace Elite Guard as publisher
# First check if Elite Guard is running
import subprocess
result = subprocess.run("netstat -lnp | grep 5557", shell=True, capture_output=True, text=True)
if "LISTEN" in result.stdout:
    print("⚠️ Elite Guard is already binding port 5557")
    print("Kill it first: pkill -f elite_guard_with_citadel")
    exit(1)

# Now bind as publisher (replacing Elite Guard)
publisher = context.socket(zmq.PUB)
publisher.bind("tcp://*:5557")
print("✅ Bound to port 5557 as publisher")
time.sleep(1)  # Let subscribers connect

# Create test signal
test_signal = {
    "signal_id": f"TEST_INJECT_{int(time.time())}",
    "symbol": "GBPUSD",
    "direction": "BUY",
    "entry_price": 1.2650,
    "sl": 1.2630,
    "tp": 1.2690,
    "lot_size": 0.01,
    "confidence": 85,
    "target_uuid": "COMMANDER_DEV_001"
}

# Send in Elite Guard format
message = f"ELITE_GUARD_SIGNAL {json.dumps(test_signal)}"

print(f"\n📤 Publishing signal at {datetime.now()}:")
print(json.dumps(test_signal, indent=2))

# Send multiple times to ensure delivery
for i in range(5):
    publisher.send_string(message)
    print(f"✅ Sent attempt {i+1}/5")
    time.sleep(0.5)

print("\n✅ Signal published to all subscribers on 5557")
print("Check final_fire_publisher logs for processing")

# Keep publisher alive briefly for late subscribers
time.sleep(3)

publisher.close()
context.term()
print("\n" + "=" * 60)