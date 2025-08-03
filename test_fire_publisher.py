#!/usr/bin/env python3
"""
Test Fire Publisher
Sends a test signal directly to port 5557
"""

import zmq
import json
import time

def main():
    context = zmq.Context()
    
    # Create PUB socket (like Elite Guard would)
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5558")  # Use different port to not conflict
    
    print("🎯 Testing Fire Publisher")
    print("Waiting 2 seconds for subscribers to connect...")
    time.sleep(2)
    
    # Create a test signal
    test_signal = {
        "signal_id": "TEST_ELITE_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "confidence": 75.5,
        "stop_loss_pips": 30,
        "target_pips": 60,
        "signal_type": "LIQUIDITY_SWEEP",
        "timestamp": time.time()
    }
    
    print(f"\n📡 Publishing test signal: {test_signal['signal_id']}")
    print(f"   Symbol: {test_signal['symbol']}")
    print(f"   Direction: {test_signal['direction']}")
    print(f"   Confidence: {test_signal['confidence']}%")
    
    # Publish the signal
    publisher.send_string(json.dumps(test_signal))
    
    print("\n✅ Test signal sent!")
    print("Check /tmp/final_fire_publisher.log to see if it was received")
    
    publisher.close()
    context.term()

if __name__ == "__main__":
    main()