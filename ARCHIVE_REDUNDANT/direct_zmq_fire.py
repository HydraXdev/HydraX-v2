#!/usr/bin/env python3
"""
Direct ZMQ Fire Test - Bypasses all Redis/IPC complexity
Sends directly to EA on port 5555 like the old working system
"""
import zmq
import json
import time
import sys

def send_direct_fire(uuid="COMMANDER_DEV_001"):
    """Send fire command directly to EA via ZMQ ROUTER socket"""
    
    ctx = zmq.Context()
    
    # Connect as DEALER to the ROUTER on 5555
    dealer = ctx.socket(zmq.DEALER)
    
    # Set identity to match what EA expects
    dealer.setsockopt_string(zmq.IDENTITY, uuid)
    
    # Connect to command router
    dealer.connect("tcp://localhost:5555")
    
    print(f"🔌 Connected to tcp://localhost:5555 as {uuid}")
    
    # Wait for connection
    time.sleep(1)
    
    # Send HELLO first (like EA does)
    hello = {
        "type": "HELLO",
        "target_uuid": uuid,
        "node_id": "DIRECT_TEST",
        "timestamp": str(int(time.time()))
    }
    dealer.send_json(hello)
    print(f"👋 Sent HELLO")
    
    # Wait a bit
    time.sleep(1)
    
    # Send fire command
    fire_cmd = {
        "type": "fire",
        "fire_id": f"DIRECT_{int(time.time())}",
        "target_uuid": uuid,
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry": 1.1700,
        "sl": 1.1650,
        "tp": 1.1750,
        "lot": 0.01
    }
    
    dealer.send_json(fire_cmd)
    print(f"🔥 Sent fire command: {fire_cmd['fire_id']}")
    print(f"   Symbol: {fire_cmd['symbol']}")
    print(f"   Direction: {fire_cmd['direction']}")
    print(f"   Entry: {fire_cmd['entry']}")
    print(f"   SL: {fire_cmd['sl']}")
    print(f"   TP: {fire_cmd['tp']}")
    print(f"   Lot: {fire_cmd['lot']}")
    
    # Try to receive response
    try:
        dealer.setsockopt(zmq.RCVTIMEO, 3000)  # 3 second timeout
        response = dealer.recv_json()
        print(f"✅ Got response: {response}")
    except zmq.Again:
        print("⏱️ No response after 3 seconds")
    
    dealer.close()
    ctx.term()

if __name__ == "__main__":
    uuid = sys.argv[1] if len(sys.argv) > 1 else "COMMANDER_DEV_001"
    send_direct_fire(uuid)