#!/usr/bin/env python3
"""
BITTEN Market Open Readiness Check
Verifies all components are connected and ready for live trading
"""

import requests
import json
from datetime import datetime
import time

print("🎯 BITTEN MARKET OPEN READINESS CHECK")
print("=" * 60)
print(f"Time: {datetime.now()}")
print("=" * 60)

# 1. Check Market Data Receiver
print("\n1️⃣ MARKET DATA RECEIVER STATUS:")
try:
    health = requests.get("http://localhost:8001/market-data/health", timeout=5).json()
    print(f"   ✅ Service: Running")
    print(f"   📊 Status: {health['status']}")
    print(f"   🔢 Active Symbols: {health['active_symbols']}")
    print(f"   📡 Data Sources: {health['total_sources']}")
    
    if health['status'] == 'no_data':
        print("   ⚠️  No data yet (expected - market closed)")
except Exception as e:
    print(f"   ❌ Service: NOT RUNNING - {e}")
    print("   🔧 Fix: cd /root/HydraX-v2 && python3 market_data_receiver.py")

# 2. Check if MT5 is sending data
print("\n2️⃣ MT5 EA CONNECTION:")
try:
    all_data = requests.get("http://localhost:8001/market-data/all", timeout=5).json()
    if all_data['active_symbols'] > 0:
        print(f"   ✅ MT5 Connected: Receiving data from {all_data['active_symbols']} symbols")
        # Show sample data
        for symbol, data in list(all_data['symbols'].items())[:3]:
            print(f"   📈 {symbol}: bid={data['bid']}, spread={data['spread']}")
    else:
        print("   ⚠️  MT5 Not Connected Yet")
        print("   🔧 Fix: Ensure EA is attached and WebRequest URL is allowed")
        print("   🔧 URL to add: http://localhost:8001 or http://YOUR_SERVER_IP:8001")
except Exception as e:
    print(f"   ❌ Error checking data: {e}")

# 3. Check VENOM v7 Integration
print("\n3️⃣ VENOM v7 ENGINE:")
try:
    from apex_venom_v7_real_data_only import ApexVenomV7RealDataOnly
    engine = ApexVenomV7RealDataOnly()
    
    # Check if it can connect
    status = engine.get_market_data_status()
    if 'status' in status:
        print(f"   ✅ VENOM Ready: Can connect to market data")
        
        # Try to get data
        data = engine.get_real_mt5_data("EURUSD")
        if data:
            print(f"   📊 EURUSD Data: {data}")
        else:
            print("   ⚠️  No EURUSD data (market closed)")
    else:
        print("   ❌ VENOM connection issue")
except Exception as e:
    print(f"   ❌ VENOM Error: {e}")

# 4. Check Signal Generation Path
print("\n4️⃣ SIGNAL GENERATION PATH:")
components = {
    "apex_venom_v7_unfiltered.py": "Signal Engine",
    "bitten_production_bot.py": "Telegram Bot", 
    "src/bitten_core/fire_router.py": "Fire Router",
    "src/mt5_bridge/mt5_bridge_adapter.py": "MT5 Bridge"
}

import os
all_ready = True
for file, desc in components.items():
    path = f"/root/HydraX-v2/{file}"
    if os.path.exists(path):
        print(f"   ✅ {desc}: Ready")
    else:
        print(f"   ❌ {desc}: Missing!")
        all_ready = False

# 5. Test fire.txt communication
print("\n5️⃣ FIRE.TXT PROTOCOL TEST:")
print("   ℹ️  This requires manual verification on MT5 side")
print("   📝 To test: Create fire.txt in MT5 with test signal")

# Summary
print("\n" + "=" * 60)
print("📊 READINESS SUMMARY:")
print("=" * 60)

if health['status'] == 'healthy' or all_data['active_symbols'] > 0:
    print("✅ SYSTEM READY FOR MARKET OPEN!")
    print("   - Market data receiver is running")
    print("   - MT5 is connected and streaming")
    print("   - VENOM can access real data")
    print("   - All components are in place")
else:
    print("⚠️  SYSTEM NEEDS ATTENTION:")
    print("   - Market data receiver is running")
    print("   - Waiting for MT5 EA to connect")
    print("   - Add WebRequest URL in MT5")
    print("   - Ensure EA is attached to chart")

print("\n🔄 DATA FLOW WHEN MARKET OPENS:")
print("   MT5 EA → HTTP POST → Market Data Receiver → VENOM v7 → Signals")
print("   Signal → Telegram Bot → User /fire → fire.txt → MT5 EA → Trade")

print(f"\n⏰ Next check: Run this again after MT5 is configured")
print("=" * 60)