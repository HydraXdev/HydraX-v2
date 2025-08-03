#!/usr/bin/env python3
"""
Force Elite Guard Signal
Creates a strong liquidity sweep pattern that should trigger detection
"""

import zmq
import json
import time
from datetime import datetime

def main():
    context = zmq.Context()
    
    # Connect to telemetry input
    publisher = context.socket(zmq.PUSH)
    publisher.connect("tcp://127.0.0.1:5556")
    
    print("🚀 Forcing Elite Guard Signal Generation")
    print("=" * 60)
    print("Creating STRONG liquidity sweep on EURUSD...")
    print("Pattern: 30 pip spike + high volume + quick reversal")
    print("=" * 60)
    
    # Send some normal ticks first to build buffer
    print("\n📊 Building tick buffer...")
    base_bid = 1.15500
    base_ask = 1.15513
    
    for i in range(20):
        tick = {
            "type": "tick",
            "symbol": "EURUSD",
            "bid": base_bid + (i * 0.00001),
            "ask": base_ask + (i * 0.00001),
            "spread": 1.3,
            "volume": 100 + (i * 10),
            "timestamp": int(time.time() * 1000)
        }
        publisher.send_json(tick)
        if i % 5 == 0:
            print(f"   Buffer tick {i+1}: {tick['bid']:.5f}")
        time.sleep(0.1)
    
    # Now create a MASSIVE liquidity sweep
    print("\n💥 LIQUIDITY SWEEP EVENT...")
    
    # Spike up 30 pips with huge volume
    spike_bid = base_bid + 0.0030  # 30 pip spike!
    spike_ask = spike_bid + 0.00013
    
    for i in range(5):
        tick = {
            "type": "tick",
            "symbol": "EURUSD",
            "bid": spike_bid,
            "ask": spike_ask,
            "spread": 1.3,
            "volume": 2000 + (i * 500),  # HUGE volume spike
            "timestamp": int(time.time() * 1000)
        }
        publisher.send_json(tick)
        print(f"   💥 SPIKE: {tick['bid']:.5f} vol={tick['volume']}")
        time.sleep(0.2)
    
    # Quick reversal - drop 40 pips
    print("\n🔻 REVERSAL AFTER SWEEP...")
    reversal_bid = base_bid - 0.0010  # 10 pips below original
    reversal_ask = reversal_bid + 0.00013
    
    for i in range(10):
        tick = {
            "type": "tick",
            "symbol": "EURUSD",
            "bid": reversal_bid - (i * 0.00005),
            "ask": reversal_ask - (i * 0.00005),
            "spread": 1.3,
            "volume": 1500,
            "timestamp": int(time.time() * 1000)
        }
        publisher.send_json(tick)
        if i % 2 == 0:
            print(f"   🔻 Reversal: {tick['bid']:.5f}")
        time.sleep(0.2)
    
    print("\n✅ Strong pattern injected!")
    print("\n⏰ Waiting for next Elite Guard scan cycle...")
    print("   (scans every 30 seconds)")
    
    # Send a few more normal ticks to keep data flowing
    for i in range(10):
        tick = {
            "type": "tick",
            "symbol": "EURUSD",
            "bid": reversal_bid + (i * 0.00001),
            "ask": reversal_ask + (i * 0.00001),
            "spread": 1.3,
            "volume": 200,
            "timestamp": int(time.time() * 1000)
        }
        publisher.send_json(tick)
        time.sleep(1)
    
    print("\n👀 Monitor logs for signal generation!")
    
    publisher.close()
    context.term()

if __name__ == "__main__":
    main()