#!/usr/bin/env python3
"""
Send a direct test command to EA through port 5555
The final_fire_publisher.py is bound to this port and EA should be pulling from it
"""

import zmq
import json
import time
from datetime import datetime

def send_test_to_ea():
    """Send test fire command to EA"""
    
    print("=" * 60)
    print("DIRECT EA FIRE TEST")
    print("=" * 60)
    print(f"Time: {datetime.now()}")
    print("Sending fire command directly to port 5555")
    print("=" * 60)
    
    context = zmq.Context()
    
    # Connect as PUSH to port 5555 (final_fire_publisher has bound it)
    pusher = context.socket(zmq.PUSH)
    pusher.connect("tcp://localhost:5555")
    
    # Create fire command in EA format
    fire_command = {
        "type": "fire",
        "target_uuid": f"TEST_{int(time.time())}",
        "symbol": "EURUSD",
        "entry": 1.0850,
        "sl": 1.0830,  # 20 pips below
        "tp": 1.0890,  # 40 pips above  
        "lot": 0.01,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "manual_test",
        "signal_id": f"MANUAL_TEST_{int(time.time())}"
    }
    
    print("\nFire Command:")
    print(json.dumps(fire_command, indent=2))
    
    # Send the command
    pusher.send_json(fire_command)
    print(f"\n✅ Command sent at {datetime.now()}")
    
    pusher.close()
    
    # Set up listener for confirmation on port 5558  
    puller = context.socket(zmq.PULL)
    puller.bind("tcp://*:5558")  # Bind to receive confirmations
    puller.setsockopt(zmq.RCVTIMEO, 10000)  # 10 second timeout
    
    print(f"\nListening for EA confirmation on port 5558...")
    print("Waiting 10 seconds for response...")
    
    try:
        response = puller.recv_string()
        print(f"\n🎯 EA CONFIRMATION RECEIVED at {datetime.now()}:")
        print(response)
        
        try:
            data = json.loads(response)
            print("\nParsed Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('status') == 'success':
                print(f"\n✅✅✅ TRADE EXECUTED SUCCESSFULLY!")
                print(f"Ticket: {data.get('ticket')}")
                print(f"Price: {data.get('price')}")
            else:
                print(f"\n⚠️ Trade failed: {data.get('message')}")
        except:
            pass
            
    except zmq.error.Again:
        print(f"\n⏱️ No confirmation received after 10 seconds")
        print("\nPossible reasons:")
        print("1. EA is not connected to port 5555")
        print("2. EA is not running on MT5")  
        print("3. Market is closed (it's weekend)")
        print("4. EA doesn't have confirmation sending enabled")
        
    puller.close()
    context.term()
    
    print("\n" + "=" * 60)
    print("Test complete. Check MT5 terminal for any activity.")
    print("=" * 60)

if __name__ == "__main__":
    send_test_to_ea()