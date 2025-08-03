#!/usr/bin/env python3
"""
Complete End-to-End Flow Test
Simulates EA -> Market Service -> VENOM -> WebApp
"""

import requests
import json
import time
import sys
from datetime import datetime

def step1_inject_ea_data():
    """Step 1: Simulate EA sending market data"""
    print("=" * 60)
    print("STEP 1: Simulating EA Market Data Stream")
    print("=" * 60)
    
    # Simulate realistic market data from EA
    pairs_data = {
        "EURUSD": {"bid": 1.0856, "ask": 1.0858, "spread": 2.0},
        "GBPUSD": {"bid": 1.2712, "ask": 1.2714, "spread": 2.0},
        "USDJPY": {"bid": 157.45, "ask": 157.47, "spread": 2.0},
        "AUDUSD": {"bid": 0.6448, "ask": 0.6450, "spread": 2.0},
        "USDCAD": {"bid": 1.3654, "ask": 1.3656, "spread": 2.0}
    }
    
    ticks = []
    for symbol, data in pairs_data.items():
        tick = {
            "symbol": symbol,
            "bid": data["bid"],
            "ask": data["ask"],
            "spread": data["spread"],
            "volume": 1500,
            "time": int(time.time())
        }
        ticks.append(tick)
        print(f"  {symbol}: Bid={data['bid']}, Ask={data['ask']}")
    
    # Send to market service
    payload = {
        "uuid": "mt5_user_12345",
        "broker": "MetaQuotes-Demo",
        "account_balance": 10000.0,
        "ticks": ticks
    }
    
    try:
        response = requests.post("http://127.0.0.1:8001/market-data", json=payload)
        if response.status_code == 200:
            print(f"\n✅ Market data sent successfully: {response.json()}")
            return True
        else:
            print(f"\n❌ Failed to send data: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def step2_verify_market_data():
    """Step 2: Verify data is available in market service"""
    print("\n" + "=" * 60)
    print("STEP 2: Verifying Market Data Availability")
    print("=" * 60)
    
    try:
        # Check specific symbol
        response = requests.get("http://127.0.0.1:8001/market-data/get/EURUSD")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ EURUSD data available:")
            print(f"   Bid: {data['bid']}")
            print(f"   Ask: {data['ask']}")
            print(f"   Spread: {data['spread']}")
            print(f"   Real Data: {data['is_real']}")
        
        # Check all data
        response = requests.get("http://127.0.0.1:8001/market-data/all")
        if response.status_code == 200:
            all_data = response.json()
            print(f"\n✅ Total pairs with data: {len(all_data)}")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def step3_trigger_venom_scan():
    """Step 3: Manually trigger VENOM scan"""
    print("\n" + "=" * 60)
    print("STEP 3: Manual VENOM Signal Generation Test")
    print("=" * 60)
    
    # Import VENOM components
    sys.path.insert(0, '/root/HydraX-v2')
    from venom_clean_integration import VenomCleanIntegration
    
    try:
        scanner = VenomCleanIntegration()
        print("✅ VENOM scanner initialized")
        
        # Run one scan
        signals = scanner.scan_for_signals()
        
        if signals:
            print(f"\n🎯 Generated {len(signals)} signals:")
            for sig in signals[:3]:  # Show first 3
                shield = sig.get('citadel_shield', {})
                print(f"   {sig['pair']} {sig['direction']} @ {sig['confidence']}%")
                print(f"   Shield Score: {shield.get('score', 0)}/10")
                print(f"   Signal Type: {sig['signal_type']}")
            return signals
        else:
            print("❌ No signals generated")
            return []
    except Exception as e:
        print(f"❌ Error in VENOM scan: {e}")
        import traceback
        traceback.print_exc()
        return []

def step4_check_webapp():
    """Step 4: Check if signals reached webapp"""
    print("\n" + "=" * 60)
    print("STEP 4: Checking WebApp Signal Reception")
    print("=" * 60)
    
    try:
        response = requests.get("http://127.0.0.1:8888/api/signals")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 WebApp signals: {data['count']} signals")
            if data['count'] > 0:
                print("✅ Signals successfully reached WebApp!")
                for sig in data['signals'][:3]:
                    print(f"   Signal ID: {sig.get('signal_id', 'unknown')}")
            else:
                print("⚠️  No signals in WebApp yet")
            return True
    except Exception as e:
        print(f"❌ Error checking webapp: {e}")
        return False

def main():
    print("\n🧪 COMPLETE END-TO-END FLOW TEST")
    print("Testing: EA → Market Service → VENOM → CITADEL → WebApp")
    print("\n")
    
    # Run all steps
    if step1_inject_ea_data():
        time.sleep(1)
        if step2_verify_market_data():
            time.sleep(1)
            signals = step3_trigger_venom_scan()
            if signals:
                time.sleep(1)
                step4_check_webapp()
    
    print("\n" + "=" * 60)
    print("📊 TEST COMPLETE")
    print("=" * 60)
    
    print("\nDiagnostic Summary:")
    print("- Market Service: http://127.0.0.1:8001/market-data/health")
    print("- WebApp Signals: http://127.0.0.1:8888/api/signals")
    print("- VENOM Logs: tail -f venom_clean.log")
    print("- Market Logs: tail -f unified_market.log")

if __name__ == "__main__":
    main()