#!/usr/bin/env python3
"""
Monitor Elite Guard signals on port 5557
"""

import zmq
import json
from datetime import datetime

def main():
    context = zmq.Context()
    
    # SUB socket to receive Elite Guard signals
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5557")
    subscriber.subscribe(b'')  # Subscribe to all messages
    
    print(f"📡 Monitoring Elite Guard signals on port 5557...")
    print(f"⏰ Started at {datetime.now()}")
    print("-" * 60)
    
    try:
        while True:
            # Receive message
            message = subscriber.recv_string()
            
            try:
                signal = json.loads(message)
                print(f"\n🎯 SIGNAL RECEIVED at {datetime.now().strftime('%H:%M:%S')}")
                print(f"   ID: {signal.get('signal_id', 'N/A')}")
                print(f"   Symbol: {signal.get('symbol', 'N/A')}")
                print(f"   Direction: {signal.get('direction', 'N/A')}")
                print(f"   Confidence: {signal.get('confidence', 'N/A')}%")
                print(f"   Type: {signal.get('signal_type', 'N/A')}")
                print("-" * 60)
            except json.JSONDecodeError:
                print(f"⚠️ Non-JSON message: {message}")
                
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")
    finally:
        subscriber.close()
        context.term()

if __name__ == "__main__":
    main()