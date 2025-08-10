#\!/usr/bin/env python3
import zmq
import json
import time
import sys

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.bind("tcp://*:5555")
print("✅ Fire command socket BOUND on port 5555")
print("⏳ Waiting for EA to connect...")

# Give EA time to connect
time.sleep(3)

# Try different command formats
commands = [
    # Format 1: Standard fire format
    {
        "type": "fire",
        "signal_id": "TEST_001",
        "symbol": "XAUUSD",
        "direction": "BUY",
        "lot_size": 0.01,
        "sl_pips": 20,
        "tp_pips": 40
    },
    # Format 2: Simple action format
    {
        "action": "BUY",
        "symbol": "XAUUSD",
        "lot": 0.01,
        "tp": 40,
        "sl": 20
    },
    # Format 3: UUID format
    {
        "uuid": "test-003",
        "action": "BUY",
        "symbol": "XAUUSD",
        "lot": 0.01,
        "tp": 40,
        "sl": 20
    }
]

for i, cmd in enumerate(commands, 1):
    cmd["timestamp"] = int(time.time())
    msg = json.dumps(cmd)
    socket.send_string(msg)
    print(f"🔥 Test {i}: {msg}")
    time.sleep(2)

print("\n✅ All test commands sent. Check MT5 Expert tab.")
print("Keeping socket alive... Press Ctrl+C to stop")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 Shutting down")
    socket.close()
