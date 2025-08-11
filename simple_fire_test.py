#!/usr/bin/env python3
"""
Simple fire test - connects to existing publisher
"""

import zmq
import json
import time
from datetime import datetime

def send_test_fire():
    """Send a test fire command through the existing infrastructure"""
    
    print("=" * 60)
    print("BITTEN SIMPLE FIRE TEST")
    print("=" * 60)
    
    context = zmq.Context()
    
    # Connect to the existing PUSH socket on 5555
    # final_fire_publisher.py has bound this port
    push_socket = context.socket(zmq.PUSH)
    push_socket.connect("tcp://localhost:5555")
    
    print(f"[{datetime.now()}] Connected to fire publisher on port 5555")
    
    # Create test trade command in EA format
    test_command = {
        "type": "fire",
        "command": "FIRE",
        "signal_id": f"TEST_{int(time.time())}",
        "target_uuid": "MANUAL_TEST",
        "symbol": "EURUSD",
        "action": "BUY",
        "direction": "BUY",
        "entry": 1.0850,
        "sl": 1.0830,
        "tp": 1.0890,
        "lot": 0.01,
        "lot_size": 0.01,
        "sl_pips": 20,
        "tp_pips": 40,
        "magic_number": 12345,
        "comment": "BITTEN_TEST",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "manual_test"
    }
    
    print(f"\n[{datetime.now()}] Sending test fire command:")
    print(json.dumps(test_command, indent=2))
    
    # Send the command
    push_socket.send_json(test_command)
    print(f"\n✅ Fire command sent to EA via port 5555")
    
    # Listen for confirmation on port 5558
    pull_socket = context.socket(zmq.PULL)
    pull_socket.connect("tcp://localhost:5558")
    pull_socket.setsockopt(zmq.RCVTIMEO, 10000)  # 10 second timeout
    
    print(f"\n[{datetime.now()}] Listening for EA confirmation on port 5558...")
    
    try:
        # Try to receive confirmation
        response = pull_socket.recv_string()
        print(f"\n[{datetime.now()}] 🎯 EA RESPONSE RECEIVED:")
        print(response)
        
        # Try to parse as JSON
        try:
            response_data = json.loads(response)
            print("\nParsed response:")
            print(json.dumps(response_data, indent=2))
            
            if response_data.get('status') == 'success':
                print(f"\n✅ TRADE EXECUTED SUCCESSFULLY!")
                print(f"   Ticket: {response_data.get('ticket')}")
                print(f"   Price: {response_data.get('price')}")
            else:
                print(f"\n⚠️ Trade failed: {response_data.get('message')}")
                
        except json.JSONDecodeError:
            pass
            
    except zmq.error.Again:
        print(f"\n⏱️ No confirmation received in 10 seconds")
        print("The EA might not be connected or the trade might have been executed without confirmation")
        print("\n📋 Next steps:")
        print("1. Check if MT5 terminal is running")
        print("2. Check if BITTEN EA is attached to a chart")
        print("3. Check MT5 Experts tab for any error messages")
        print("4. Check Journal tab for trade execution")
    
    # Clean up
    push_socket.close()
    pull_socket.close()
    context.term()
    
    print("\n" + "=" * 60)
    print("Test complete. Check MT5 terminal for trade execution.")

if __name__ == "__main__":
    send_test_fire()