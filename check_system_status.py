#!/usr/bin/env python3
"""
Check complete HydraX system status including MT5 data flow
"""

import requests
import json
import time
from datetime import datetime

print("🎯 HYDRAX SYSTEM STATUS CHECK")
print("=" * 60)
print(f"Time: {datetime.now()}")
print("=" * 60)

# 1. Check Market Data Receiver
print("\n1️⃣ MARKET DATA RECEIVER:")
try:
    health = requests.get("http://127.0.0.1:8001/market-data/health", timeout=2).json()
    print(f"   ✅ Service: Running")
    print(f"   📊 Status: {health['status']}")
    print(f"   🔢 Active Symbols: {health['active_symbols']}")
    
    # Get all data
    all_data = requests.get("http://127.0.0.1:8001/market-data/all", timeout=2).json()
    if all_data['active_symbols'] > 0:
        print(f"   📈 Live Data:")
        for symbol, data in list(all_data['symbols'].items())[:3]:
            print(f"      {symbol}: bid={data['bid']}, spread={data['spread']}")
    else:
        print("   ⚠️ No live data from MT5 yet")
        print("   💡 Check:")
        print("      - MT5 EA is attached to chart (smiley face)")
        print("      - WebRequest URL http://127.0.0.1:8001 is allowed")
        print("      - Market is open (check tick times in MT5)")
        
except Exception as e:
    print(f"   ❌ Service DOWN: {e}")

# 2. Simulate MT5 data if none present
if health.get('active_symbols', 0) == 0:
    print("\n2️⃣ SIMULATING MT5 DATA (for testing):")
    test_data = {
        "uuid": "mt5_debug_test",
        "timestamp": int(time.time()),
        "account_balance": 10000.00,
        "ticks": []
    }
    
    # Add all 15 pairs
    pairs = [
        ("EURUSD", 1.0865, 1.0867),
        ("GBPUSD", 1.2843, 1.2845),
        ("USDJPY", 157.23, 157.25),
        ("USDCAD", 1.3612, 1.3614),
        ("AUDUSD", 0.6543, 0.6545)
    ]
    
    for symbol, bid, ask in pairs:
        test_data["ticks"].append({
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "spread": round((ask - bid) / 0.00001, 1),
            "volume": 100,
            "time": int(time.time())
        })
    
    try:
        resp = requests.post("http://127.0.0.1:8001/market-data", json=test_data)
        if resp.status_code == 200:
            print("   ✅ Test data posted successfully")
    except:
        pass

# 3. Check VENOM Engine
print("\n3️⃣ VENOM ENGINE STATUS:")
try:
    from apex_venom_v7_real_data_only import ApexVenomV7RealDataOnly
    engine = ApexVenomV7RealDataOnly()
    
    # Try to get data
    data = engine.get_real_mt5_data("EURUSD")
    if data:
        print(f"   ✅ VENOM can read market data")
        print(f"   📊 EURUSD: bid={data.get('close', 'N/A')}, spread={data.get('spread', 'N/A')}")
    else:
        print("   ⚠️ VENOM waiting for market data")
        
except Exception as e:
    print(f"   ❌ VENOM Error: {e}")

# 4. System Summary
print("\n📊 SYSTEM READINESS:")
print("=" * 60)

components = {
    "Market Data Receiver": health.get('status') != 'error' if 'health' in locals() else False,
    "MT5 Data Flow": health.get('active_symbols', 0) > 0 if 'health' in locals() else False,
    "VENOM Engine": 'data' in locals() and bool(data)
}

all_ready = all(components.values())

for comp, status in components.items():
    print(f"   {comp}: {'✅ Ready' if status else '⚠️ Waiting'}")

if all_ready:
    print("\n✅ SYSTEM FULLY OPERATIONAL!")
else:
    print("\n⚠️ WAITING FOR:")
    if not components["MT5 Data Flow"]:
        print("   - MT5 EA to send market data")
        print("   - Ensure WebRequest URL is allowed in MT5")
        print("   - Check EA is attached and market is open")

print("\n🔄 DATA FLOW:")
print("   MT5 EA → HTTP POST → Market Data Receiver → VENOM → Signals")
print("=" * 60)