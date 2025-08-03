#!/usr/bin/env python3
"""
Test Elite Guard Signal Flow
Injects a liquidity sweep pattern to trigger signal generation
"""

import zmq
import json
import time
from datetime import datetime

def main():
    context = zmq.Context()
    
    # Connect to telemetry input (where EA would normally send)
    publisher = context.socket(zmq.PUSH)
    publisher.connect("tcp://127.0.0.1:5556")
    
    print("🎯 Elite Guard Signal Flow Test")
    print("=" * 60)
    print("Injecting liquidity sweep pattern on EURUSD...")
    print("This should trigger Elite Guard → Fire Publisher → EA")
    print("=" * 60)
    
    # Base price for EURUSD
    base_bid = 1.15500
    base_ask = 1.15513
    
    # Phase 1: Normal movement (5 ticks)
    print("\n📊 Phase 1: Normal price movement...")
    for i in range(5):
        tick = {
            "type": "tick",
            "symbol": "EURUSD",
            "bid": base_bid + (i * 0.00001),
            "ask": base_ask + (i * 0.00001),
            "spread": 1.3,
            "volume": 100,
            "timestamp": int(time.time())
        }
        publisher.send_json(tick)
        print(f"   Tick {i+1}: {tick['bid']:.5f}/{tick['ask']:.5f}")
        time.sleep(0.5)
    
    # Phase 2: Liquidity sweep (spike up)
    print("\n💥 Phase 2: Liquidity sweep spike...")
    spike_bid = base_bid + 0.0015  # 15 pip spike
    spike_ask = spike_bid + 0.00013
    
    for i in range(3):
        tick = {
            "type": "tick",
            "symbol": "EURUSD",
            "bid": spike_bid,
            "ask": spike_ask,
            "spread": 1.3,
            "volume": 800 + (i * 100),  # High volume
            "timestamp": int(time.time())
        }
        publisher.send_json(tick)
        print(f"   SPIKE {i+1}: {tick['bid']:.5f}/{tick['ask']:.5f} vol={tick['volume']}")
        time.sleep(0.5)
    
    # Phase 3: Quick reversal
    print("\n🔄 Phase 3: Reversal after sweep...")
    reversal_bid = base_bid - 0.0008  # 8 pip below original
    reversal_ask = reversal_bid + 0.00013
    
    for i in range(5):
        tick = {
            "type": "tick",
            "symbol": "EURUSD",
            "bid": reversal_bid + (i * 0.00002),
            "ask": reversal_ask + (i * 0.00002),
            "spread": 1.3,
            "volume": 600,
            "timestamp": int(time.time())
        }
        publisher.send_json(tick)
        print(f"   Reversal {i+1}: {tick['bid']:.5f}/{tick['ask']:.5f}")
        time.sleep(0.5)
    
    print("\n✅ Pattern injection complete!")
    print("\n📋 Expected flow:")
    print("1. Telemetry Bridge receives ticks on 5556")
    print("2. Publishes to Elite Guard on 5560")
    print("3. Elite Guard detects liquidity sweep pattern")
    print("4. Publishes signal on 5557")
    print("5. Fire Publisher receives and forwards to 5555")
    print("6. EA receives fire command")
    
    print("\n👀 Check these logs:")
    print("- /tmp/elite_guard.log (pattern detection)")
    print("- /tmp/final_fire_publisher.log (signal forwarding)")
    print("- EA logs for fire command execution")
    
    publisher.close()
    context.term()

if __name__ == "__main__":
    main()