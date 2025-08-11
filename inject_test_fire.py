#!/usr/bin/env python3
"""
Inject a test fire command directly to the EA
This mimics what happens when a user fires a signal
"""

import zmq
import json
import time
from datetime import datetime

def inject_fire_command():
    """Send a fire command in the format the EA expects"""
    
    context = zmq.Context()
    
    # The final_fire_publisher.py is bound to 5555 as PUSH
    # The EA should be connected as PULL to receive commands
    # We need to send our command TO the EA
    
    # Actually, let's publish to port 5557 where Elite Guard signals go
    # final_fire_publisher subscribes to 5557 and forwards to EA
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5559")  # Use a different port to inject
    
    # Wait for socket to be ready
    time.sleep(0.5)
    
    # Create a test signal that looks like Elite Guard format
    test_signal = {
        "signal_id": f"TEST_FIRE_{int(time.time())}",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "sl": 1.0830,  # 20 pips below
        "tp": 1.0890,  # 40 pips above
        "sl_pips": 20,
        "tp_pips": 40,
        "lot_size": 0.01,
        "confidence": 85,
        "pattern_type": "TEST_PATTERN",
        "signal_type": "PRECISION_STRIKE",
        "target_uuid": "TEST_COMMAND"
    }
    
    # Send as Elite Guard format
    message = f"ELITE_GUARD_SIGNAL {json.dumps(test_signal)}"
    
    print(f"[{datetime.now()}] Publishing test signal:")
    print(json.dumps(test_signal, indent=2))
    
    # Actually, let's send directly to the EA format
    # Let me check what the EA expects
    
    # Create fire command in EA format
    ea_command = {
        "type": "fire",
        "command": "FIRE",
        "target_uuid": f"TEST_{int(time.time())}",
        "symbol": "EURUSD",
        "entry": 1.0850,
        "sl": 1.0830,
        "tp": 1.0890,
        "lot": 0.01,
        "direction": "BUY",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "manual_test",
        "comment": "BITTEN_TEST"
    }
    
    # Connect directly to where the EA is pulling from
    pusher = context.socket(zmq.PUSH)
    pusher.connect("tcp://localhost:5555")
    
    print(f"\n[{datetime.now()}] Sending direct fire command to EA:")
    print(json.dumps(ea_command, indent=2))
    
    pusher.send_json(ea_command)
    print(f"\n✅ Fire command sent!")
    
    # Listen for confirmation
    sub = context.socket(zmq.SUB)
    sub.connect("tcp://localhost:5558")
    sub.setsockopt_string(zmq.SUBSCRIBE, "")
    sub.setsockopt(zmq.RCVTIMEO, 5000)
    
    print(f"\n[{datetime.now()}] Waiting for EA confirmation on port 5558...")
    
    try:
        response = sub.recv_string()
        print(f"[{datetime.now()}] EA Response: {response}")
    except zmq.Again:
        print(f"[{datetime.now()}] No confirmation received in 5 seconds")
        print("Check MT5 terminal for trade execution")
    
    pusher.close()
    sub.close()
    publisher.close()
    context.term()

if __name__ == "__main__":
    print("=" * 60)
    print("BITTEN EA DIRECT FIRE TEST")
    print("=" * 60)
    inject_fire_command()