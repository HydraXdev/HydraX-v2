#!/usr/bin/env python3
"""
Send DIRECTLY to EA - bypass all publishers and routers
The EA is a PULL client on 5555, so we need to PUSH to it
"""

import zmq
import json
import time
from datetime import datetime

def direct_ea_test():
    print("=" * 60)
    print("DIRECT TO EA TEST - BYPASSING ALL MIDDLEWARE")
    print("=" * 60)
    
    context = zmq.Context()
    
    # Kill the final_fire_publisher first to free port 5555
    import os
    os.system("pkill -f final_fire_publisher")
    time.sleep(1)
    print("✅ Killed final_fire_publisher to free port 5555")
    
    # Now WE bind port 5555 as PUSH (EA connects as PULL)
    command_socket = context.socket(zmq.PUSH)
    command_socket.bind("tcp://*:5555")
    print("✅ We bound port 5555 as PUSH")
    
    # Also bind 5558 to receive confirmations (EA pushes to this)
    confirm_socket = context.socket(zmq.PULL)
    confirm_socket.bind("tcp://*:5558")
    confirm_socket.setsockopt(zmq.RCVTIMEO, 1000)
    print("✅ We bound port 5558 as PULL for confirmations")
    
    # Wait for EA to connect
    print("\n⏳ Waiting 2 seconds for EA to reconnect...")
    time.sleep(2)
    
    # Send test command DIRECTLY to EA
    test_command = {
        "type": "fire",
        "target_uuid": "COMMANDER_DEV_001",
        "symbol": "EURUSD",
        "entry": 0,  # Market order
        "sl": 0,
        "tp": 0,
        "lot": 0.01,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"\n🔥 SENDING DIRECT TO EA at {datetime.now()}:")
    print(json.dumps(test_command, indent=2))
    
    command_socket.send_string(json.dumps(test_command))
    print("✅ Command sent directly to EA on port 5555")
    
    # Listen for ANY response
    print("\n📡 Listening for EA response on 5558...")
    
    for i in range(10):
        try:
            msg = confirm_socket.recv_string()
            print(f"\n🎯🎯🎯 EA RESPONDED:")
            print(msg)
            
            try:
                data = json.loads(msg)
                print("\nParsed response:")
                for k, v in data.items():
                    print(f"  {k}: {v}")
            except:
                pass
            break
            
        except zmq.error.Again:
            print(".", end="", flush=True)
    else:
        print("\n\n❌ No response from EA after 10 seconds")
        print("The EA is not pulling from port 5555 or not pushing to 5558")
    
    # Clean up
    command_socket.close()
    confirm_socket.close()
    context.term()
    
    # Restart final_fire_publisher
    os.system("nohup python3 final_fire_publisher.py > /dev/null 2>&1 &")
    print("\n✅ Restarted final_fire_publisher")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    direct_ea_test()