#!/usr/bin/env python3
"""
Test the clean data flow from MT5 -> Market Service -> VENOM
"""

import requests
import json
import time
import sys

def test_market_service():
    """Test if market service is running"""
    print("1. Testing Market Service...")
    try:
        response = requests.get("http://127.0.0.1:8001/market-data/health", timeout=2)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Market service healthy: {health}")
            return True
        else:
            print(f"❌ Market service error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach market service: {e}")
        return False

def inject_test_data():
    """Inject test market data"""
    print("\n2. Injecting test data...")
    
    # Test data for all 15 pairs
    pairs = [
        "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
        "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
        "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
    ]
    
    base_prices = {
        "EURUSD": 1.0850, "GBPUSD": 1.2700, "USDJPY": 157.50,
        "USDCAD": 1.3650, "AUDUSD": 0.6450, "USDCHF": 0.8950,
        "NZDUSD": 0.5850, "EURGBP": 0.8540, "EURJPY": 170.85,
        "GBPJPY": 200.05, "GBPNZD": 2.1710, "GBPAUD": 1.9685,
        "EURAUD": 1.6820, "GBPCHF": 1.1365, "AUDJPY": 101.60
    }
    
    ticks = []
    for pair in pairs:
        base = base_prices[pair]
        bid = base + (0.0001 * (hash(pair) % 10 - 5))
        ask = bid + 0.0002
        
        tick = {
            "symbol": pair,
            "bid": round(bid, 5),
            "ask": round(ask, 5),
            "spread": 2.0,
            "volume": 1000,
            "time": int(time.time())
        }
        ticks.append(tick)
    
    payload = {
        "uuid": "test_clean_flow",
        "timestamp": int(time.time()),
        "ticks": ticks
    }
    
    try:
        response = requests.post("http://127.0.0.1:8001/market-data", json=payload, timeout=2)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Data injected: {result}")
            return True
        else:
            print(f"❌ Injection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Injection error: {e}")
        return False

def verify_data_available():
    """Verify data is available in market service"""
    print("\n3. Verifying data availability...")
    
    try:
        response = requests.get("http://127.0.0.1:8001/market-data/all", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data available for {len(data)} pairs")
            
            # Show sample
            if data:
                sample_pair = list(data.keys())[0]
                print(f"   Sample: {sample_pair} = {data[sample_pair]}")
            return True
        else:
            print(f"❌ No data available: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking data: {e}")
        return False

def test_single_pair():
    """Test getting data for a single pair"""
    print("\n4. Testing single pair data retrieval...")
    
    try:
        response = requests.get("http://127.0.0.1:8001/market-data/get/EURUSD", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ EURUSD data: {data}")
            return True
        else:
            print(f"❌ Cannot get EURUSD data: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting EURUSD: {e}")
        return False

def check_webapp():
    """Check if webapp is ready to receive signals"""
    print("\n5. Checking WebApp signal endpoint...")
    
    try:
        response = requests.get("http://127.0.0.1:8888/api/signals", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ WebApp ready: {data}")
            return True
        else:
            print(f"❌ WebApp error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach WebApp: {e}")
        return False

def main():
    print("🧪 Testing Clean Data Flow Architecture")
    print("=" * 50)
    
    # Run all tests
    tests = [
        test_market_service,
        inject_test_data,
        verify_data_available,
        test_single_pair,
        check_webapp
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        if not result:
            print("\n⚠️  Fix the above issue before proceeding")
            break
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! System ready for VENOM integration")
        print("\nNext steps:")
        print("1. Start the clean VENOM scanner: python3 venom_clean_integration.py")
        print("2. Monitor logs for signal generation")
        print("3. Check WebApp for received signals")
    else:
        print("\n❌ Some tests failed. Fix issues before proceeding.")

if __name__ == "__main__":
    main()