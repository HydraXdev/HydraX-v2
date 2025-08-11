#!/usr/bin/env python3
"""
Send a properly formatted fire command matching what the EA expects
Based on the actual EA code and zmq_bitten_controller format
"""

import zmq
import json
import time
from datetime import datetime

def send_proper_fire():
    """Send fire command in the exact format EA expects"""
    
    print("=" * 60)
    print("SENDING PROPERLY FORMATTED FIRE COMMAND")
    print("=" * 60)
    
    context = zmq.Context()
    
    # Connect to command port where final_fire_publisher is bound
    command_pusher = context.socket(zmq.PUSH)
    command_pusher.connect("tcp://localhost:5555")
    print("✅ Connected to command port 5555")
    
    # Set up confirmation listener first
    confirm_puller = context.socket(zmq.PULL)
    try:
        confirm_puller.bind("tcp://*:5558")
        print("✅ Confirmation receiver bound on port 5558")
        bound = True
    except:
        confirm_puller.connect("tcp://localhost:5558")
        print("✅ Connected to existing port 5558")
        bound = False
    
    confirm_puller.setsockopt(zmq.RCVTIMEO, 500)
    
    # The EA expects these exact fields based on ExecuteFireCommand function:
    # - type: "fire" (line 701 of EA)
    # - target_uuid: must match EA's UUID (line 687-692)
    # - symbol: trading symbol (line 741)
    # - entry: entry price, 0 for market (line 742)
    # - sl: stop loss price (line 743)
    # - tp: take profit price (line 744)
    # - lot: lot size (line 745)
    
    # Create properly formatted command
    fire_command = {
        "type": "fire",
        "target_uuid": "COMMANDER_DEV_001",  # We confirmed this UUID from market data
        "symbol": "EURUSD",
        "entry": 0,  # 0 means market execution - EA will use current price
        "sl": 0,     # 0 means no stop loss initially
        "tp": 0,     # 0 means no take profit initially
        "lot": 0.01, # Minimum lot size
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"\n📤 Sending fire command at {datetime.now()}:")
    print(json.dumps(fire_command, indent=2))
    
    # Send the command
    command_pusher.send_json(fire_command)
    print("✅ Command sent!")
    
    # Also try sending with SL/TP set based on current price estimate
    # EURUSD is typically around 1.08-1.09
    fire_with_sl_tp = {
        "type": "fire",
        "target_uuid": "COMMANDER_DEV_001",
        "symbol": "EURUSD",
        "entry": 0,      # Market execution
        "sl": 1.0800,    # SL below current price
        "tp": 1.0900,    # TP above current price
        "lot": 0.01,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"\n📤 Sending second command with SL/TP:")
    print(json.dumps(fire_with_sl_tp, indent=2))
    command_pusher.send_json(fire_with_sl_tp)
    print("✅ Second command sent!")
    
    # Listen for confirmations
    print(f"\n📡 Listening for EA confirmations...")
    
    confirmations = 0
    start_time = time.time()
    
    while time.time() - start_time < 5:
        try:
            response = confirm_puller.recv_string()
            confirmations += 1
            
            print(f"\n🎯 CONFIRMATION #{confirmations} RECEIVED:")
            print(response)
            
            try:
                data = json.loads(response)
                
                if data.get('type') == 'confirmation':
                    print(f"\n📋 Fire confirmation:")
                    print(f"  Status: {data.get('status')}")
                    print(f"  UUID: {data.get('user_uuid')}")
                    print(f"  Message: {data.get('message')}")
                    
                    if data.get('status') == 'success':
                        print(f"\n✅✅✅ TRADE EXECUTED!")
                        print(f"  Ticket: #{data.get('ticket')}")
                        print(f"  Price: {data.get('price')}")
                    elif 'market' in str(data.get('message', '')).lower():
                        print("\n📅 Market is closed (weekend)")
                        print("EA received command but cannot trade on weekends")
                        
            except json.JSONDecodeError:
                pass
                
        except zmq.error.Again:
            print(".", end="", flush=True)
    
    if confirmations == 0:
        print(f"\n\n⏱️ No confirmations received")
        print("\nCheck MT5 Experts tab for:")
        print("- '⚡ UNIFIED COMMAND received for UUID: COMMANDER_DEV_001'")
        print("- Any error messages about the trade")
    else:
        print(f"\n\n✅ Received {confirmations} confirmation(s)")
    
    # Cleanup
    command_pusher.close()
    if bound:
        confirm_puller.unbind("tcp://*:5558")
    confirm_puller.close()
    context.term()
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    send_proper_fire()