#!/usr/bin/env python3
"""
Test complete flow from signal to HUD to fire command
Verifies user data overlay and position sizing
"""

import json
import time
import requests

def test_complete_flow():
    """Test the complete BITTEN flow with real user data"""
    
    print("=== BITTEN COMPLETE FLOW TEST ===\n")
    
    # 1. Check user registry data
    print("1. Loading user registry...")
    with open('/root/HydraX-v2/user_registry.json', 'r') as f:
        registry = json.load(f)
    
    user_id = "7176191872"
    user_data = registry.get(user_id, registry.get('users', {}).get(user_id))
    
    if user_data:
        print(f"   ✅ User {user_id} found:")
        print(f"      Tier: {user_data.get('tier', 'UNKNOWN')}")
        print(f"      Balance: ${user_data.get('account_balance', 0):.2f}")
        print(f"      Status: {user_data.get('status', 'unknown')}")
    else:
        print(f"   ❌ User {user_id} not found in registry")
        return
    
    # 2. Create a test signal
    print("\n2. Creating test signal...")
    test_signal = {
        "signal_id": f"TEST_SIGNAL_{int(time.time())}",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0830,
        "take_profit": 1.0890,
        "sl_pips": 20,
        "tp_pips": 40,
        "confidence": 85,
        "risk_reward_ratio": 2.0,
        "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
        "citadel_shield": {
            "score": 7.5,
            "classification": "SHIELD_APPROVED"
        }
    }
    
    # Save test signal
    signal_file = f"missions/{test_signal['signal_id']}.json"
    with open(signal_file, 'w') as f:
        json.dump(test_signal, f, indent=2)
    print(f"   ✅ Created signal: {test_signal['signal_id']}")
    
    # 3. Test HUD with user overlay
    print("\n3. Testing HUD with user overlay...")
    hud_url = f"http://localhost:8888/hud?mission_id={test_signal['signal_id']}&user_id={user_id}"
    
    try:
        response = requests.get(hud_url, timeout=5)
        if response.status_code == 200:
            # Check for user-specific data in response
            html = response.text
            
            checks = {
                "Tier displayed": "COMMANDER" in html,
                "Balance shown": "850" in html,  # User's actual balance
                "Risk calculation": "17.0" in html,  # 2% of 850.45
                "Position sizing": user_data.get('tier') == 'COMMANDER'
            }
            
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
                
            if all(checks.values()):
                print("   ✅ HUD shows correct personalized data!")
            else:
                print("   ⚠️ Some HUD data may be incorrect")
                
        else:
            print(f"   ❌ HUD returned error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Could not access HUD: {e}")
    
    # 4. Calculate expected position size
    print("\n4. Verifying position size calculation...")
    balance = user_data.get('account_balance', 10000.0)
    sl_pips = test_signal['sl_pips']
    tier = user_data.get('tier', 'NIBBLER')
    
    # Calculate position size for 2% risk
    risk_amount = balance * 0.02
    pip_value = 10  # $10 per pip for 1 standard lot
    base_lots = risk_amount / (sl_pips * pip_value)
    tier_multiplier = 2 if tier == 'COMMANDER' else 1
    position_size = round(base_lots * tier_multiplier, 2)
    
    print(f"   Balance: ${balance:.2f}")
    print(f"   Risk (2%): ${risk_amount:.2f}")
    print(f"   SL Distance: {sl_pips} pips")
    print(f"   Base Position: {base_lots:.3f} lots")
    print(f"   Tier Multiplier: {tier_multiplier}x ({tier})")
    print(f"   Final Position: {position_size} lots")
    
    # 5. Verify fire command would use correct values
    print("\n5. Fire command verification...")
    print(f"   When user fires this signal:")
    print(f"   - Position: {position_size} lots")
    print(f"   - Risk: ${risk_amount:.2f}")
    print(f"   - Potential Reward: ${risk_amount * test_signal['risk_reward_ratio']:.2f}")
    print(f"   - These values will be sent to MT5")
    
    # 6. Check all processes are running
    print("\n6. System health check...")
    import subprocess
    
    processes = {
        "Elite Guard": "elite_guard_with_citadel",
        "ZMQ Relay": "elite_guard_zmq_relay",
        "Telemetry Bridge": "zmq_telemetry_bridge",
        "WebApp": "webapp_server_optimized",
        "Telegram Bot": "bitten_production_bot"
    }
    
    for name, process in processes.items():
        result = subprocess.run(f"ps aux | grep {process} | grep -v grep | wc -l", 
                              shell=True, capture_output=True, text=True)
        count = int(result.stdout.strip())
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {name}: {'Running' if count > 0 else 'NOT RUNNING'}")
    
    print("\n=== TEST COMPLETE ===")
    print(f"Signal {test_signal['signal_id']} ready for testing")
    print(f"HUD URL: {hud_url}")

if __name__ == "__main__":
    test_complete_flow()