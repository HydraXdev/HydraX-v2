#!/usr/bin/env python3
"""
Debug analyzer for VENOM v8 stream pipeline to identify why signals aren't generating
"""

import json
import requests
import time
from collections import deque
import statistics

def analyze_market_data():
    """Analyze the market data structure and content"""
    print("🔍 ANALYZING MARKET DATA STRUCTURE")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8001/market-data/all?fast=true", timeout=2.0)
        if response.status_code == 200:
            market_data = response.json()
            data_section = market_data.get('data', market_data)
            
            print(f"📊 Market data contains {len(data_section)} symbols:")
            for symbol, data in data_section.items():
                if isinstance(data, dict) and 'bid' in data and 'ask' in data:
                    bid = float(data['bid'])
                    ask = float(data['ask'])
                    spread = round((ask - bid) / 0.0001, 1)
                    print(f"  {symbol}: bid={bid}, ask={ask}, spread={spread} pips")
            
            return data_section
        else:
            print(f"❌ Market data API error: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Market data fetch error: {e}")
        return {}

def test_signal_conditions(symbol_data, symbol):
    """Test the signal generation conditions for a symbol"""
    print(f"\n🧪 TESTING SIGNAL CONDITIONS FOR {symbol}")
    print("-" * 40)
    
    # Simulate tick buffer with some test data
    ticks = deque(maxlen=20)
    
    # Add 10 ticks with slight price variations
    base_bid = float(symbol_data['bid'])
    base_ask = float(symbol_data['ask'])
    
    for i in range(10):
        # Create price variations
        price_change = (i - 5) * 0.00001  # Small changes
        bid = base_bid + price_change
        ask = base_ask + price_change
        
        tick = {
            'symbol': symbol,
            'bid': bid,
            'ask': ask,
            'timestamp': time.time() - (10-i),
            'volume': 1000 + i * 100,
            'spread': round((ask - bid) / 0.0001, 1)
        }
        ticks.append(tick)
    
    print(f"📈 Created {len(ticks)} test ticks for {symbol}")
    
    # Test the conditions from _evaluate_live_conditions
    if len(ticks) < 5:
        print("❌ Not enough ticks (< 5)")
        return None
    
    prices = [t['bid'] for t in ticks]
    print(f"💰 Prices: {[round(p, 5) for p in prices[-5:]]}")
    
    # Calculate momentum
    price_change = prices[-1] - prices[0]
    print(f"📊 Price change: {price_change:.6f}")
    
    volatility = statistics.stdev(prices) if len(prices) > 1 else 0
    print(f"📈 Volatility (stdev): {volatility:.6f}")
    
    if volatility == 0:
        print("❌ Zero volatility - no signal possible")
        return None
    
    # Momentum score calculation
    momentum_raw = abs(price_change) / volatility
    momentum_score = min(momentum_raw * 100, 100.0)
    print(f"⚡ Momentum raw: {momentum_raw:.2f}")
    print(f"⚡ Momentum score: {momentum_score:.1f}%")
    
    # Volume boost
    volumes = [t['volume'] for t in ticks if t['volume'] > 0]
    volume_boost = 1.15 if volumes and statistics.mean(volumes) > 1000 else 1.0
    print(f"📊 Volume boost: {volume_boost}")
    
    # Spread penalty
    current_spread = ticks[-1]['spread']
    spread_penalty = 0.85 if current_spread > 3.0 else 1.0
    print(f"📏 Spread: {current_spread} pips, penalty: {spread_penalty}")
    
    # Final confidence
    confidence = min(momentum_score * volume_boost * spread_penalty, 100.0)
    print(f"🎯 FINAL CONFIDENCE: {confidence:.1f}%")
    
    fire_threshold = 79.0  # Increased from 70.0 to reduce signal rate
    print(f"🔥 Fire threshold: {fire_threshold}%")
    
    if confidence >= fire_threshold:
        print(f"✅ SIGNAL WOULD FIRE! ({confidence:.1f}% >= {fire_threshold}%)")
        return True
    else:
        print(f"❌ Signal blocked ({confidence:.1f}% < {fire_threshold}%)")
        return False

def test_multiple_symbols():
    """Test signal conditions for multiple symbols"""
    print("\n🎯 TESTING MULTIPLE SYMBOLS")
    print("=" * 50)
    
    # Get market data
    market_data = analyze_market_data()
    
    if not market_data:
        print("❌ No market data available for testing")
        return
    
    valid_symbols = [
        "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
        "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
        "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
    ]
    
    signals_found = 0
    symbols_tested = 0
    
    for symbol in valid_symbols:
        if symbol in market_data:
            symbols_tested += 1
            result = test_signal_conditions(market_data[symbol], symbol)
            if result:
                signals_found += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"  Symbols in market data: {len(market_data)}")
    print(f"  Valid symbols tested: {symbols_tested}")
    print(f"  Signals that would fire: {signals_found}")
    
    if signals_found == 0:
        print("\n❌ NO SIGNALS WOULD FIRE - This explains why VENOM v8 isn't generating signals!")
        print("💡 POSSIBLE SOLUTIONS:")
        print("  1. Lower the fire threshold below 70%")
        print("  2. Increase price variations in market data")
        print("  3. Check if volatility calculation needs adjustment")
    else:
        print(f"\n✅ {signals_found} signals would fire - VENOM should be working!")

if __name__ == "__main__":
    test_multiple_symbols()