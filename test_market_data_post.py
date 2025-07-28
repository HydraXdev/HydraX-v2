#!/usr/bin/env python3
"""
Test script to simulate MT5 market data POST
"""

import requests
import json
import time

# Test data similar to what MT5 would send
test_data = {
    "uuid": "mt5_test_12345",
    "timestamp": int(time.time()),
    "account_balance": 10000.00,
    "ticks": [
        {
            "symbol": "EURUSD",
            "bid": 1.0865,
            "ask": 1.0867,
            "spread": 2.0,
            "volume": 100,
            "time": int(time.time())
        },
        {
            "symbol": "GBPUSD", 
            "bid": 1.2843,
            "ask": 1.2845,
            "spread": 2.0,
            "volume": 50,
            "time": int(time.time())
        }
    ]
}

print("🧪 Testing market data POST to receiver")
print(f"📡 URL: http://127.0.0.1:8001/market-data")
print(f"📊 Data: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(
        "http://127.0.0.1:8001/market-data",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"📄 Response: {response.text}")
    
    # Check if data was stored
    time.sleep(1)
    check = requests.get("http://127.0.0.1:8001/market-data/all")
    data = check.json()
    
    print(f"\n📊 Active Symbols: {data['active_symbols']}")
    if data['active_symbols'] > 0:
        print("✅ Market data successfully stored!")
        for symbol, info in data['symbols'].items():
            print(f"  {symbol}: bid={info['bid']}, spread={info['spread']}")
    
except Exception as e:
    print(f"❌ Error: {e}")