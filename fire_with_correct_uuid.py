#!/usr/bin/env python3
"""
Fire command with the correct UUID we just discovered
"""

import zmq
import json
import time
from datetime import datetime

def fire_and_listen():
    """Send fire command and listen for confirmation"""
    
    print("=" * 60)
    print("FIRE COMMAND WITH CORRECT UUID")
    print("=" * 60)
    
    context = zmq.Context()
    
    # First, set up confirmation listener on 5558
    confirm_puller = context.socket(zmq.PULL)
    confirm_puller.bind("tcp://*:5558")
    confirm_puller.setsockopt(zmq.RCVTIMEO, 100)  # 100ms timeout for non-blocking
    print("✅ Confirmation listener bound on port 5558")
    
    # Connect to command port
    command_pusher = context.socket(zmq.PUSH)
    command_pusher.connect("tcp://localhost:5555")
    print("✅ Connected to command port 5555")
    
    # Send fire command with the UUID we found
    fire_command = {
        "type": "fire",
        "target_uuid": "COMMANDER_DEV_001",  # The UUID we discovered
        "symbol": "EURUSD",
        "entry": 1.0850,
        "sl": 1.0830,
        "tp": 1.0890,
        "lot": 0.01,
        "timestamp": datetime.utcnow().isoformat(),
        "signal_id": f"VERIFIED_TEST_{int(time.time())}"
    }
    
    print(f"\n🔥 Sending fire command at {datetime.now()}:")
    print(json.dumps(fire_command, indent=2))
    
    command_pusher.send_json(fire_command)
    print("✅ Command sent!\n")
    
    # Listen for confirmation
    print("📡 Listening for EA confirmation on port 5558...")
    
    start_time = time.time()
    timeout = 10  # 10 seconds total
    
    while time.time() - start_time < timeout:
        try:
            response = confirm_puller.recv_string()
            print(f"\n🎯🎯🎯 EA CONFIRMATION RECEIVED at {datetime.now()}:")
            print(response)
            
            try:
                data = json.loads(response)
                print("\n📋 Parsed confirmation:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                
                if data.get('status') == 'success':
                    print(f"\n✅✅✅ TRADE EXECUTED SUCCESSFULLY!")
                    print(f"  Ticket: #{data.get('ticket')}")
                    print(f"  Price: {data.get('price')}")
                    print(f"  UUID confirmed: {data.get('user_uuid')}")
                elif data.get('status') == 'failed':
                    print(f"\n⚠️ Trade failed!")
                    print(f"  Reason: {data.get('message')}")
                    if 'market' in data.get('message', '').lower() or 'closed' in data.get('message', '').lower():
                        print("\n📅 Market is closed (weekend). This is expected.")
                        print("The EA received the command but cannot execute trades on weekends.")
                
                break
                
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                
        except zmq.error.Again:
            # No data available, continue
            print(".", end="", flush=True)
            time.sleep(0.5)
    
    else:
        print(f"\n\n⏱️ No confirmation after {timeout} seconds")
        print("\nPossible reasons:")
        print("1. EA received command but market is closed")
        print("2. EA is not sending confirmations on port 5558")
        print("3. Check MT5 Experts tab for '⚡ UNIFIED COMMAND received'")
    
    # Cleanup
    command_pusher.close()
    confirm_puller.close()
    context.term()
    
    print("\n" + "=" * 60)
    print("Check MT5 Experts tab for any EA messages")
    print("=" * 60)

if __name__ == "__main__":
    fire_and_listen()