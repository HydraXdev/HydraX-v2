#!/usr/bin/env python3
"""
Inject realistic market data to trigger VENOM stream pipeline signals
"""

import requests
import json
import time
import random
from datetime import datetime

def inject_realistic_market_data():
    """Inject realistic market data with volatility to trigger signals"""
    print("📡 Injecting realistic market data to trigger VENOM signals...")
    
    # Base prices for major pairs
    base_prices = {
        "EURUSD": {"bid": 1.0845, "ask": 1.0847},
        "GBPUSD": {"bid": 1.2735, "ask": 1.2737},
        "USDJPY": {"bid": 153.25, "ask": 153.27},
        "USDCAD": {"bid": 1.3842, "ask": 1.3844},
        "AUDUSD": {"bid": 0.6534, "ask": 0.6536},
        "USDCHF": {"bid": 0.8765, "ask": 0.8767},
        "NZDUSD": {"bid": 0.5892, "ask": 0.5894},
        "EURGBP": {"bid": 0.8512, "ask": 0.8514},
        "EURJPY": {"bid": 166.15, "ask": 166.17},
        "GBPJPY": {"bid": 195.22, "ask": 195.24},
        "GBPNZD": {"bid": 2.1634, "ask": 2.1636},
        "GBPAUD": {"bid": 1.9487, "ask": 1.9489},
        "EURAUD": {"bid": 1.6602, "ask": 1.6604},
        "GBPCHF": {"bid": 1.1172, "ask": 1.1174},
        "AUDJPY": {"bid": 100.12, "ask": 100.14}
    }
    
    url = "http://localhost:8001/market-data"
    
    for cycle in range(5):  # 5 cycles of data injection
        print(f"\n🔄 Cycle {cycle + 1}/5 - Injecting volatile market data...")
        
        for tick in range(20):  # 20 ticks per cycle
            # Create realistic volatility patterns
            volatility_factor = random.uniform(0.8, 1.2)  # ±20% volatility
            momentum_factor = 1.0 + (tick - 10) * 0.001  # Trending movement
            
            ticks_data = []
            
            for symbol, prices in base_prices.items():
                # Create realistic price movement
                base_volatility = random.uniform(-0.0005, 0.0005)  # Base volatility
                trend_movement = (tick - 10) * random.uniform(-0.0002, 0.0002)  # Trend
                
                new_bid = prices["bid"] + base_volatility + trend_movement
                new_ask = new_bid + random.uniform(0.0001, 0.0003)  # Realistic spread
                
                # Higher volume during volatile periods
                volume = int(1000 + (volatility_factor * 500) + random.randint(-200, 200))
                
                tick_data = {
                    "symbol": symbol,
                    "bid": round(new_bid, 5),
                    "ask": round(new_ask, 5),
                    "spread": round((new_ask - new_bid) * 10000, 1),  # Spread in pips
                    "volume": volume,
                    "timestamp": time.time()
                }
                
                ticks_data.append(tick_data)
                
                # Update base prices for next iteration (trending)
                base_prices[symbol]["bid"] = new_bid
                base_prices[symbol]["ask"] = new_ask
            
            # Send batch of ticks
            payload = {
                "uuid": "live_data_injector",
                "broker": "market_simulator",
                "account_balance": 10000.0,
                "ticks": ticks_data
            }
            
            try:
                response = requests.post(url, json=payload, timeout=3)
                if response.status_code == 200:
                    print(f"✅ Tick {tick + 1:2d}: Injected {len(ticks_data)} symbols")
                else:
                    print(f"❌ Tick {tick + 1:2d}: Failed ({response.status_code})")
            except Exception as e:
                print(f"❌ Tick {tick + 1:2d}: Error - {e}")
            
            time.sleep(0.2)  # 200ms between ticks for high frequency
        
        print(f"🔄 Cycle {cycle + 1} complete - letting signals process...")
        time.sleep(5)  # Let signals process between cycles
    
    print("\n✅ Market data injection complete!")
    print("🎯 Check VENOM stream pipeline for signal generation")

def check_market_data_status():
    """Check current market data status"""
    try:
        response = requests.get("http://localhost:8001/market-data/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Market Data Status:")
            print(f"   Active symbols: {data.get('active_symbols', 0)}")
            print(f"   Total sources: {data.get('total_sources', 0)}")
            print(f"   Status: {data.get('status', 'unknown')}")
            return True
    except Exception as e:
        print(f"❌ Market data receiver not accessible: {e}")
        return False

def main():
    print("🚀 LIVE MARKET DATA INJECTION")
    print("=" * 50)
    
    # Check market data receiver status
    if not check_market_data_status():
        print("❌ Market data receiver not available")
        return
    
    # Inject market data
    inject_realistic_market_data()
    
    # Final status check
    print("\n" + "=" * 50)
    check_market_data_status()
    
    print("\n🎯 Data injection complete - signals should be generating!")

if __name__ == "__main__":
    main()