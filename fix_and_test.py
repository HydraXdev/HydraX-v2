#!/usr/bin/env python3
"""
Fix the missing confirmation receiver and test
"""

import zmq
import json
import time
import threading
from datetime import datetime

def confirmation_listener(context):
    """Run confirmation listener in background"""
    confirm_socket = context.socket(zmq.PULL)
    confirm_socket.bind("tcp://*:5558")
    print("✅ Confirmation receiver bound on port 5558")
    
    while True:
        try:
            msg = confirm_socket.recv_string()
            print(f"\n🎯🎯🎯 EA CONFIRMATION RECEIVED at {datetime.now()}:")
            print(msg)
            
            try:
                data = json.loads(msg)
                print("\n📋 Parsed confirmation:")
                for k, v in data.items():
                    print(f"  {k}: {v}")
                    
                if data.get('status') == 'success':
                    print(f"\n✅✅✅ TRADE EXECUTED SUCCESSFULLY!")
                    print(f"  Ticket: #{data.get('ticket')}")
                    print(f"  Price: {data.get('price')}")
            except:
                pass
                
        except Exception as e:
            print(f"Error in listener: {e}")
            break

def main():
    print("=" * 60)
    print("FIX CONFIRMATION PORT AND TEST")
    print("=" * 60)
    
    context = zmq.Context()
    
    # Start confirmation listener in background
    listener_thread = threading.Thread(target=confirmation_listener, args=(context,), daemon=True)
    listener_thread.start()
    
    # Wait for EA to connect to 5558
    print("\n⏳ Waiting for EA to connect to port 5558...")
    time.sleep(3)
    
    # Check if EA connected
    import subprocess
    result = subprocess.run("netstat -ant | grep 5558 | grep ESTABLISHED", shell=True, capture_output=True, text=True)
    if result.stdout:
        print("✅ EA connected to port 5558!")
        print(result.stdout)
    else:
        print("⚠️ EA not yet connected to 5558")
    
    # Now send fire command through existing publisher
    command_socket = context.socket(zmq.PUSH)
    command_socket.connect("tcp://localhost:5555")
    print("\n✅ Connected to command port 5555")
    
    # Send multiple test commands
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    for symbol in symbols:
        fire_command = {
            "type": "fire",
            "target_uuid": "COMMANDER_DEV_001",
            "symbol": symbol,
            "entry": 0,  # Market order
            "sl": 0,
            "tp": 0,
            "lot": 0.01,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"\n🔥 Sending {symbol} fire command at {datetime.now()}:")
        print(json.dumps(fire_command, indent=2))
        
        command_socket.send_string(json.dumps(fire_command))
        print(f"✅ {symbol} command sent")
        
        # Wait between commands
        time.sleep(2)
    
    # Keep listening for responses
    print("\n📡 Listening for confirmations (press Ctrl+C to stop)...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    command_socket.close()
    context.term()
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    main()