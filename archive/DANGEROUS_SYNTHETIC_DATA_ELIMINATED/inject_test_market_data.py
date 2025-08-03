#!/usr/bin/env python3
"""
Inject test market data to restore truth tracker functionality
"""
import requests
import json
import time

# Test market data in correct format for the receiver
test_data = {
    "uuid": "test_mt5_instance",
    "broker": "test_broker", 
    "account_balance": 10000.0,
    "ticks": [
        {
            "symbol": "EURUSD",
            "bid": 1.0864,
            "ask": 1.0866,
            "spread": 2.0,
            "volume": 1000,
            "timestamp": time.time()
        },
        {
            "symbol": "GBPUSD", 
            "bid": 1.2735,
            "ask": 1.2737,
            "spread": 2.0,
            "volume": 1000,
            "timestamp": time.time()
        },
        {
            "symbol": "USDJPY",
            "bid": 153.25,
            "ask": 153.27,
            "spread": 2.0,
            "volume": 1000,
            "timestamp": time.time()
        }
    ]
}

def inject_data():
    """Inject test data into market data receiver"""
    url = "http://localhost:8001/market-data"
    
    print("🔌 Injecting test market data...")
    try:
        response = requests.post(url, json=test_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Injected {result.get('processed', 0)} ticks from {result.get('broker', 'unknown')}")
        else:
            print(f"❌ Failed to inject data: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error injecting data: {e}")
    
    # Verify injection
    print("\n🔍 Verifying market data...")
    try:
        health_response = requests.get("http://localhost:8001/market-data/health", timeout=5)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ Active symbols: {health['active_symbols']}")
            print(f"✅ Total sources: {health['total_sources']}")
        else:
            print("❌ Health check failed")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    inject_data()