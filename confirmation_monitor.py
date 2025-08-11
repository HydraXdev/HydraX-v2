#!/usr/bin/env python3
"""
Visible confirmation receiver - shows what's being received
"""

import zmq
import json
from datetime import datetime

def main():
    context = zmq.Context()
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5558")
    
    print("=" * 60)
    print("📡 CONFIRMATION RECEIVER STARTED")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print("Listening on port 5558 for EA confirmations...")
    print("-" * 60)
    
    while True:
        try:
            # Set timeout to show we're alive
            receiver.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Receive message
            message = receiver.recv_json()
            
            print(f"\n✅✅✅ CONFIRMATION RECEIVED at {datetime.now().strftime('%H:%M:%S')}:")
            print("-" * 40)
            print(json.dumps(message, indent=2))
            print("-" * 40)
            
            # Check what type of confirmation
            if message.get('type') == 'confirmation':
                if message.get('status') == 'success':
                    print(f"🎉 TRADE EXECUTED SUCCESSFULLY!")
                    print(f"  Ticket: {message.get('ticket')}")
                    print(f"  Price: {message.get('price')}")
                    print(f"  Symbol: {message.get('symbol', 'N/A')}")
                else:
                    print(f"❌ TRADE FAILED!")
                    print(f"  Message: {message.get('message')}")
            
            # Save to file for verification
            with open("/root/HydraX-v2/confirmations_received.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - {json.dumps(message)}\n")
            
        except zmq.Again:
            print(".", end="", flush=True)  # Show we're still listening
            
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            break
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    receiver.close()
    context.term()

if __name__ == "__main__":
    main()