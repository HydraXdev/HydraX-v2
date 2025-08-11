#!/usr/bin/env python3
"""
Monitor port 5558 for EA confirmations
"""

import zmq
import json
import time
from datetime import datetime

def monitor():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5558")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
    
    print("=" * 60)
    print("📡 MONITORING EA CONFIRMATIONS ON PORT 5558")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print("Waiting for confirmations from EA...")
    print("-" * 60)
    
    count = 0
    while count < 30:  # Monitor for 30 seconds
        try:
            message = socket.recv_string()
            print(f"\n✅ CONFIRMATION RECEIVED at {datetime.now().strftime('%H:%M:%S')}:")
            
            try:
                data = json.loads(message)
                print(json.dumps(data, indent=2))
                
                # Check what type of confirmation
                if data.get('type') == 'confirmation':
                    if data.get('status') == 'success':
                        print("\n🎉 TRADE EXECUTED SUCCESSFULLY!")
                        print(f"  Ticket: {data.get('ticket')}")
                        print(f"  Price: {data.get('price')}")
                    else:
                        print("\n❌ TRADE FAILED!")
                        print(f"  Message: {data.get('message')}")
                        
            except json.JSONDecodeError:
                print(f"Raw message: {message}")
                
        except zmq.Again:
            print(".", end="", flush=True)
            count += 1
            
    socket.close()
    context.term()
    
    print(f"\n\nMonitoring complete at {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    monitor()