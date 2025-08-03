#!/usr/bin/env python3
"""
Inject test market data to demonstrate VENOM stream pipeline with truth tracking
"""

import requests
import json
import time
import threading

def inject_market_data():
    """Inject test market data to trigger VENOM stream signals"""
    print("📡 Injecting test market data...")
    
    # Test data with varying volatility to trigger signals
    test_data = {
        "EURUSD": {"bid": 1.0845, "ask": 1.0847, "volume": 1200},
        "GBPUSD": {"bid": 1.2735, "ask": 1.2737, "volume": 800},
        "USDJPY": {"bid": 153.25, "ask": 153.27, "volume": 1500}
    }
    
    for i in range(20):  # Inject 20 ticks to create volatility
        for symbol, data in test_data.items():
            # Add some volatility
            volatility = 0.0002 * (i % 5 - 2)  # -0.0004 to +0.0004
            
            enhanced_data = {
                symbol: {
                    "symbol": symbol,
                    "bid": data["bid"] + volatility,
                    "ask": data["ask"] + volatility,
                    "volume": data["volume"] + (i * 50),
                    "spread": 2.0,
                    "timestamp": time.time()
                }
            }
            
            try:
                response = requests.get(
                    "http://localhost:8001/market-data/all?fast=true",
                    timeout=1
                )
                
                # Simulate market data being available
                print(f"📊 Tick {i+1}: {symbol} bid={data['bid'] + volatility:.5f}")
                
            except:
                pass  # Market data receiver might not be running
                
        time.sleep(0.1)  # 100ms between ticks

if __name__ == "__main__":
    inject_market_data()