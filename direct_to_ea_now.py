#!/usr/bin/env python3
"""
Send fire command DIRECTLY to EA on port 5555
Exactly like we did before when it worked
"""

import zmq
import json
import time
from datetime import datetime

context = zmq.Context()

# Connect as PUSH to port 5555 (where EA is PULL client)
pusher = context.socket(zmq.PUSH)
pusher.connect("tcp://localhost:5555")
time.sleep(0.5)  # Let connection establish

# Create fire command EXACTLY like the EA expects
fire_command = {
    "type": "fire",
    "target_uuid": "COMMANDER_DEV_001",
    "symbol": "EURUSD",
    "entry": 0,  # Market order
    "sl": 20,    # 20 pips SL
    "tp": 40,    # 40 pips TP
    "lot": 0.01,
    "timestamp": datetime.utcnow().isoformat()
}

print("=" * 60)
print("SENDING DIRECT FIRE COMMAND TO EA")
print("=" * 60)
print(f"Sending at {datetime.now()}:")
print(json.dumps(fire_command, indent=2))

# Send it!
pusher.send_json(fire_command)
print("\n✅ Sent directly to port 5555")

# Listen for confirmation
puller = context.socket(zmq.PULL)
try:
    puller.bind("tcp://*:5558")
    print("📡 Listening for confirmation on 5558...")
except:
    puller.connect("tcp://localhost:5558")
    print("📡 Connected to existing listener on 5558...")

puller.setsockopt(zmq.RCVTIMEO, 10000)

try:
    msg = puller.recv_string()
    print(f"\n🎯🎯🎯 EA CONFIRMATION RECEIVED:")
    print(msg)
    
    data = json.loads(msg)
    if data.get('status') == 'success':
        print(f"\n✅✅✅ TRADE EXECUTED!")
        print(f"  Ticket: {data.get('ticket')}")
        print(f"  Price: {data.get('price')}")
except zmq.error.Again:
    print("\n⏱️ No confirmation in 10 seconds")
    print("Check MT5 terminal for trade execution")

pusher.close()
puller.close()
context.term()