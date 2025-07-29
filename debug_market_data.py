#!/usr/bin/env python3
"""
Debug script to check what's in the market data store
"""

import requests
import json

def check_individual_endpoints():
    """Test individual endpoints to isolate the issue"""
    
    endpoints = [
        '/market-data/health',
        '/market-data/venom-feed?symbol=EURUSD',
        '/market-data/all'
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        try:
            response = requests.get(f"http://127.0.0.1:8001{endpoint}", timeout=5)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Data: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

def inject_simple_data():
    """Inject minimal test data"""
    minimal_data = {
        "uuid": "debug_test",
        "broker": "DebugBroker", 
        "account_balance": 1000.0,
        "ticks": [
            {
                "symbol": "EURUSD",
                "bid": 1.08000,
                "ask": 1.08010,
                "volume": 100,
                "timestamp": 1753789926
            }
        ]
    }
    
    print("🚀 Injecting minimal test data...")
    try:
        response = requests.post(
            "http://127.0.0.1:8001/market-data",
            json=minimal_data,
            timeout=5
        )
        print(f"Injection result: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("🐛 Market Data Debug Tool")
    print("=" * 40)
    
    inject_simple_data()
    check_individual_endpoints()