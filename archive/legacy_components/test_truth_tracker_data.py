#!/usr/bin/env python3
"""
Test script to inject sample market data and verify truth_tracker connectivity
"""

import requests
import json
import time

# Sample market data for testing (in enhanced format)
test_data = {
    "uuid": "test_terminal_001",
    "broker": "TestBroker",
    "account_balance": 10000.0,
    "ticks": [
        {
            "symbol": "EURUSD",
            "bid": 1.08234,
            "ask": 1.08245,
            "volume": 1000,
            "timestamp": time.time()
        },
        {
            "symbol": "GBPUSD", 
            "bid": 1.27156,
            "ask": 1.27168,
            "volume": 800,
            "timestamp": time.time()
        },
        {
            "symbol": "USDJPY",
            "bid": 149.843,
            "ask": 149.856,
            "volume": 1200,
            "timestamp": time.time()
        }
    ]
}

def inject_test_data():
    """Inject test market data to verify truth_tracker connectivity"""
    try:
        response = requests.post(
            "http://127.0.0.1:8001/market-data",
            json=test_data,
            timeout=5
        )
        print(f"Data injection response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Test data injected successfully")
        else:
            print(f"❌ Injection failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error injecting data: {e}")

def check_data_availability():
    """Check if data is now available"""
    try:
        response = requests.get("http://127.0.0.1:8001/market-data/all", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\nCurrent market data: {json.dumps(data, indent=2)}")
            if data:
                print("✅ Market data is available for truth_tracker")
            else:
                print("❌ No market data available")
        else:
            print(f"❌ Failed to get data: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking data: {e}")

def main():
    print("🧪 Testing Truth Tracker Market Data Connection")
    print("=" * 50)
    
    print("\n1. Injecting test market data...")
    inject_test_data()
    
    print("\n2. Checking data availability...")
    time.sleep(1)  # Give it a moment to process
    check_data_availability()
    
    print("\n3. Checking health status...")
    try:
        response = requests.get("http://127.0.0.1:8001/market-data/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"Health status: {json.dumps(health, indent=2)}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    main()