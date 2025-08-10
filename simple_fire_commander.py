#\!/usr/bin/env python3
import zmq
import json
import time

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.bind("tcp://*:5555")
print("✅ Fire command socket BOUND on port 5555 (EA will PULL from here)")

# Wait for EA to reconnect
time.sleep(3)
print("⏳ Sending test fire command...")

# Send fire command
fire_command = {
    "type": "fire",
    "signal_id": "TEST_FIRE_001", 
    "symbol": "XAUUSD",
    "direction": "BUY",
    "lot_size": 0.01,
    "sl_pips": 20,
    "tp_pips": 40,
    "timestamp": int(time.time())
}

msg = json.dumps(fire_command)
socket.send_string(msg)
print(f"🔥 Fire command sent: {msg}")

# Keep socket alive
print("\nKeeping socket alive for EA connection...")
try:
    while True:
        time.sleep(10)
        # Send heartbeat
        heartbeat = {"type": "heartbeat", "timestamp": int(time.time())}
        socket.send_string(json.dumps(heartbeat))
        print(f"💓 Heartbeat sent: {heartbeat['timestamp']}")
except KeyboardInterrupt:
    print("\n👋 Shutting down")
    socket.close()
