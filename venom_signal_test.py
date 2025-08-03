#!/usr/bin/env python3
"""
Direct test of VENOM signal generation with controlled data
Bypasses the market data receiver caching issues
"""

import sys
import os
sys.path.append('/root/HydraX-v2')

from venom_stream_pipeline import VenomStreamEngine
import time

def test_venom_with_controlled_data():
    """Test VENOM signal generation with controlled price data"""
    print("🐍 TESTING VENOM V8 SIGNAL GENERATION WITH CONTROLLED DATA")
    print("=" * 65)
    
    # Create VENOM engine
    venom = VenomStreamEngine()
    
    # Test symbols
    test_symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    # Base prices
    base_prices = {
        "EURUSD": 1.08800,
        "GBPUSD": 1.27450,
        "USDJPY": 153.15000
    }
    
    signals_generated = 0
    
    for symbol in test_symbols:
        print(f"\n🧪 Testing {symbol}")
        print("-" * 30)
        
        base_price = base_prices[symbol]
        
        # Inject 15 ticks with increasing price movement to create volatility
        for i in range(15):
            # Create substantial price movement (0.1% variation)
            if symbol == "USDJPY":
                price_change = (i - 7) * 0.015  # JPY pairs need larger changes
                bid = base_price + price_change
                ask = bid + 0.02  # 2 pip spread
            else:
                price_change = (i - 7) * 0.00015  # Major pairs
                bid = base_price + price_change
                ask = bid + 0.00002  # 2 pip spread
            
            tick_data = {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "volume": 1000 + i * 100,
                "timestamp": time.time() - (15-i)
            }
            
            # Process tick
            signal = venom.process_tick_stream(tick_data)
            
            if signal:
                print(f"🔥 SIGNAL GENERATED!")
                print(f"   Symbol: {signal.symbol}")
                print(f"   Direction: {signal.direction}")
                print(f"   Confidence: {signal.confidence:.1f}%")
                print(f"   Entry: {signal.entry_price:.5f}")
                print(f"   SL: {signal.stop_loss:.5f}")
                print(f"   TP: {signal.take_profit:.5f}")
                print(f"   Reason: {signal.fire_reason}")
                signals_generated += 1
                break
            else:
                print(f"   Tick {i+1}: bid={bid:.5f}, ask={ask:.5f} - No signal")
    
    print(f"\n📊 RESULTS:")
    print(f"   Symbols tested: {len(test_symbols)}")
    print(f"   Signals generated: {signals_generated}")
    
    if signals_generated > 0:
        print(f"\n✅ SUCCESS: VENOM v8 CAN generate signals with proper data volatility!")
        print(f"💡 The issue is in the market data receiver caching, not VENOM logic")
    else:
        print(f"\n❌ FAILURE: VENOM v8 still not generating signals")
        print(f"🔍 Need to investigate the confidence calculation logic further")

if __name__ == "__main__":
    test_venom_with_controlled_data()