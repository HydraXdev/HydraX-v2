#!/usr/bin/env python3
"""
Check real market data volatility to understand why signals don't fire
"""

import json
import requests
import time
import statistics
from collections import defaultdict, deque

# Store recent ticks for each symbol
tick_history = defaultdict(lambda: deque(maxlen=10))

def check_real_volatility():
    """Monitor real market data volatility over time"""
    print("🔍 MONITORING REAL MARKET DATA VOLATILITY")
    print("=" * 60)
    
    for iteration in range(20):  # Monitor for 20 iterations
        try:
            response = requests.get("http://localhost:8001/market-data/all?fast=true", timeout=2.0)
            if response.status_code == 200:
                market_data = response.json()
                data_section = market_data.get('data', market_data)
                
                print(f"\n📊 Iteration {iteration + 1}:")
                
                for symbol, data in data_section.items():
                    if isinstance(data, dict) and 'bid' in data and 'ask' in data:
                        bid = float(data['bid'])
                        ask = float(data['ask'])
                        
                        # Store this tick
                        tick_history[symbol].append({
                            'bid': bid,
                            'ask': ask,
                            'time': time.time()
                        })
                        
                        # Calculate volatility if we have enough data
                        if len(tick_history[symbol]) >= 5:
                            prices = [t['bid'] for t in tick_history[symbol]]
                            price_change = prices[-1] - prices[0]
                            volatility = statistics.stdev(prices) if len(prices) > 1 else 0
                            
                            # Same calculation as VENOM
                            if volatility > 0:
                                momentum_raw = abs(price_change) / volatility
                                momentum_score = min(momentum_raw * 100, 100.0)
                                
                                # Volume boost (assume high volume)
                                volume_boost = 1.15
                                
                                # Spread penalty
                                spread = round((ask - bid) / 0.0001, 1)
                                spread_penalty = 0.85 if spread > 3.0 else 1.0
                                
                                confidence = min(momentum_score * volume_boost * spread_penalty, 100.0)
                                
                                print(f"  {symbol}: price_change={price_change:.6f}, vol={volatility:.6f}, confidence={confidence:.1f}%")
                            else:
                                print(f"  {symbol}: ZERO VOLATILITY - no signal possible")
                        else:
                            print(f"  {symbol}: Not enough data yet ({len(tick_history[symbol])}/5)")
            
            time.sleep(0.5)  # Wait 500ms like VENOM
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1.0)

if __name__ == "__main__":
    check_real_volatility()