#!/usr/bin/env python3
"""
Push fire command to the existing BITTEN circuit
Connects to the complete_bitten_circuit.py which is already running
"""

import zmq
import json
import time
from datetime import datetime

def push_fire_command():
    """Push a fire command through the existing circuit"""
    
    context = zmq.Context()
    
    # Connect as PUSH to send to the existing PULL socket in complete_bitten_circuit
    # We need to send TO the EA, not to the circuit script
    # The circuit script has a PUSH socket that the EA pulls from
    
    # Actually, we need to send the command in a way that the circuit will forward it
    # Let's check if there's another way to inject commands
    
    # Create a REQ socket to send command
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://localhost:5555")
    
    print(f"[{datetime.now()}] Connected to BITTEN circuit on port 5555")
    
    # Create fire command matching the format the EA expects
    fire_command = {
        "type": "fire",
        "command": "FIRE",
        "target_uuid": f"DIRECT_TEST_{int(time.time())}",
        "signal_id": f"TEST_{int(time.time())}",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry": 1.0850,  # Current market price (approximate)
        "sl": 1.0830,     # 20 pips below
        "tp": 1.0890,     # 40 pips above  
        "lot": 0.01,
        "lot_size": 0.01,
        "sl_pips": 20,
        "tp_pips": 40,
        "magic_number": 12345,
        "comment": "BITTEN_DIRECT_TEST",
        "timestamp": datetime.now().isoformat()
    }
    
    # Send the command
    message = json.dumps(fire_command)
    socket.send_string(message)
    print(f"[{datetime.now()}] ✅ Fire command pushed to circuit:")
    print(json.dumps(fire_command, indent=2))
    
    socket.close()
    context.term()
    
    print("\n✅ Command sent successfully")
    print("Now check the complete_bitten_circuit.py output and MT5 logs")

if __name__ == "__main__":
    print("=" * 60)
    print("BITTEN FIRE COMMAND PUSH TEST")
    print("=" * 60)
    print("\nPushing fire command to existing circuit on port 5555\n")
    
    push_fire_command()