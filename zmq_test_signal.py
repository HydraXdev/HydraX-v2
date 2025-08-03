#!/usr/bin/env python3
"""
Direct ZMQ Signal Test
Tests the complete flow by injecting a signal at port 5557
"""

import zmq
import json
import time

def main():
    context = zmq.Context()
    
    # First, let's listen to what Elite Guard is publishing
    print("📡 Monitoring Elite Guard output on port 5557...")
    
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5557")
    subscriber.subscribe(b'')
    subscriber.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
    
    print("Listening for 5 seconds to see what Elite Guard publishes...")
    
    try:
        while True:
            try:
                message = subscriber.recv()
                print(f"Received raw bytes: {message}")
                try:
                    # Try to decode as string
                    msg_str = message.decode('utf-8')
                    print(f"Decoded string: {msg_str}")
                    # Try to parse as JSON
                    data = json.loads(msg_str)
                    print(f"Parsed JSON: {data}")
                except:
                    print("Could not parse as JSON")
            except zmq.Again:
                print("No messages received in 5 seconds")
                break
    except KeyboardInterrupt:
        pass
    
    subscriber.close()
    
    # Now send a test signal
    print("\n\n🚀 Sending test signal to Fire Publisher...")
    
    # Connect as a publisher to inject signal
    publisher = context.socket(zmq.PUSH)
    publisher.connect("tcp://127.0.0.1:5557")
    
    test_signal = {
        "signal_id": "DIRECT_TEST_001",
        "symbol": "EURUSD",
        "direction": "SELL",
        "confidence": 85.0,
        "stop_loss_pips": 25,
        "target_pips": 50,
        "signal_type": "TEST_SIGNAL",
        "timestamp": time.time()
    }
    
    print(f"Sending: {json.dumps(test_signal, indent=2)}")
    
    # Send as JSON string
    publisher.send_string(json.dumps(test_signal))
    
    print("\n✅ Test signal sent!")
    print("Check /tmp/final_fire_publisher.log for results")
    
    publisher.close()
    context.term()

if __name__ == "__main__":
    main()