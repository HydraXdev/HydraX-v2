#!/usr/bin/env python3
"""
Test market data injection to verify complete signal flow
"""

import requests
import json
import time
from datetime import datetime

# Test data for all 15 pairs (NO XAUUSD)
PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

def inject_test_data():
    """Inject test market data to simulate MT5 feed"""
    
    print("🚀 Starting test market data injection...")
    
    # Base prices for each pair
    base_prices = {
        "EURUSD": 1.0850, "GBPUSD": 1.2700, "USDJPY": 157.50,
        "USDCAD": 1.3650, "AUDUSD": 0.6450, "USDCHF": 0.8950,
        "NZDUSD": 0.5850, "EURGBP": 0.8540, "EURJPY": 170.85,
        "GBPJPY": 200.05, "GBPNZD": 2.1710, "GBPAUD": 1.9685,
        "EURAUD": 1.6820, "GBPCHF": 1.1365, "AUDJPY": 101.60
    }
    
    # Create tick data
    ticks = []
    for pair in PAIRS:
        base = base_prices[pair]
        # Add some variation
        bid = base + (0.0001 * (hash(pair) % 10 - 5))
        ask = bid + 0.0002  # 2 pip spread
        
        tick = {
            "symbol": pair,
            "bid": round(bid, 5),
            "ask": round(ask, 5),
            "spread": 2.0,
            "volume": 1000,
            "time": int(time.time())
        }
        ticks.append(tick)
    
    # Prepare payload
    payload = {
        "uuid": "test_mt5_terminal_001",
        "timestamp": int(time.time()),
        "broker": "TestBroker-Demo",
        "account_balance": 10000.0,
        "ticks": ticks
    }
    
    # Send to enhanced market data receiver
    try:
        response = requests.post(
            "http://127.0.0.1:8001/market-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Data injected successfully: {result}")
        else:
            print(f"❌ Failed to inject data: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error injecting data: {e}")
    
    # Check if data is available
    try:
        health_response = requests.get("http://127.0.0.1:8001/market-data/health")
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"📊 Market data health: {health}")
    except Exception as e:
        print(f"❌ Error checking health: {e}")

if __name__ == "__main__":
    # Inject data multiple times to ensure VENOM picks it up
    for i in range(3):
        print(f"\n🔄 Injection round {i+1}/3")
        inject_test_data()
        time.sleep(2)
    
    print("\n✅ Test injection complete. Check VENOM+CITADEL logs for signal generation.")