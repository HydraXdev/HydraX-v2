#!/usr/bin/env python3
"""
Inject a fire command by publishing to port 5557 where final_fire_publisher listens
This mimics what Elite Guard does
"""

import zmq
import json
import time
from datetime import datetime

def inject_via_elite_guard_port():
    print("=" * 60)
    print("INJECTING VIA ELITE GUARD PORT 5557")
    print("=" * 60)
    
    context = zmq.Context()
    
    # Publish to port 5557 where final_fire_publisher subscribes
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5559")  # Bind to a different port first
    time.sleep(0.5)  # Let socket settle
    
    # Now connect to 5557 as publisher
    elite_publisher = context.socket(zmq.PUB)
    elite_publisher.connect("tcp://127.0.0.1:5557")
    print("✅ Connected to Elite Guard signal port 5557")
    
    # Create signal in Elite Guard format
    elite_signal = {
        "signal_id": f"MANUAL_TEST_{int(time.time())}",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "sl": 1.0830,
        "tp": 1.0890,
        "lot_size": 0.01,
        "confidence": 90,
        "target_uuid": "COMMANDER_DEV_001"
    }
    
    # Send in Elite Guard format
    message = f"ELITE_GUARD_SIGNAL {json.dumps(elite_signal)}"
    
    print(f"\n📤 Sending signal at {datetime.now()}:")
    print(message)
    
    # Send multiple times to ensure delivery
    for i in range(3):
        elite_publisher.send_string(message)
        print(f"✅ Attempt {i+1}/3 sent")
        time.sleep(0.5)
    
    # Also try sending just the JSON
    print("\n📤 Sending raw JSON format:")
    for i in range(3):
        elite_publisher.send_json(elite_signal)
        print(f"✅ JSON attempt {i+1}/3 sent")
        time.sleep(0.5)
    
    print("\n✅ Signals injected to port 5557")
    print("final_fire_publisher should pick these up and forward to EA")
    
    # Set up confirmation listener
    confirm_puller = context.socket(zmq.PULL)
    try:
        confirm_puller.bind("tcp://*:5558")
    except zmq.error.ZMQError:
        confirm_puller.connect("tcp://localhost:5558")
    confirm_puller.setsockopt(zmq.RCVTIMEO, 1000)
    print("\n📡 Listening for EA confirmations on 5558...")
    
    for i in range(10):
        try:
            msg = confirm_puller.recv_string()
            print(f"\n🎯🎯🎯 EA CONFIRMATION:")
            print(msg)
            break
        except zmq.error.Again:
            print(".", end="", flush=True)
    else:
        print("\n\n⚠️ No confirmation received")
    
    # Check if EA is connected
    import subprocess
    result = subprocess.run("netstat -ant | grep 5555 | grep ESTABLISHED", shell=True, capture_output=True, text=True)
    print(f"\n📊 Port 5555 connections:")
    print(result.stdout if result.stdout else "No connections")
    
    result = subprocess.run("netstat -ant | grep 5558 | grep ESTABLISHED", shell=True, capture_output=True, text=True)
    print(f"\n📊 Port 5558 connections:")
    print(result.stdout if result.stdout else "No connections")
    
    publisher.close()
    elite_publisher.close()
    confirm_puller.close()
    context.term()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    inject_via_elite_guard_port()