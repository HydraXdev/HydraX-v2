#!/usr/bin/env python3
"""
🧪 ATHENA GROUP DISPATCH TEST
Test the short tactical messaging system for @bitten_signals group
"""

import sys
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

import time
from athena_group_dispatcher import athena_group_dispatcher

def test_group_dispatch():
    """Test ATHENA group signal dispatch"""
    print("🧪 Testing ATHENA Group Dispatch System")
    print("=" * 60)
    
    # Test different confidence levels
    test_signals = [
        {
            'signal_id': f'TEST_LOW_TCS_{int(time.time())}',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'tcs_score': 75.5,
            'entry_price': 1.0875,
            'take_profit': 1.0925,
            'stop_loss': 1.0825
        },
        {
            'signal_id': f'TEST_MID_TCS_{int(time.time())}',
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'tcs_score': 85.2,
            'entry_price': 1.2650,
            'take_profit': 1.2600,
            'stop_loss': 1.2700
        },
        {
            'signal_id': f'TEST_HIGH_TCS_{int(time.time())}',
            'symbol': 'USDJPY',
            'direction': 'BUY',
            'tcs_score': 92.8,
            'entry_price': 150.25,
            'take_profit': 150.75,
            'stop_loss': 149.75
        }
    ]
    
    results = []
    
    for i, signal in enumerate(test_signals, 1):
        print(f"\n🎯 Test {i}/3: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%)")
        
        try:
            result = athena_group_dispatcher.dispatch_group_signal(signal)
            
            if result['success']:
                print(f"✅ Group dispatch successful!")
                print(f"   Signal ID: {result['signal_id']}")
                print(f"   Message ID: {result.get('message_id', 'N/A')}")
                print(f"   HUD URL: {result['hud_url']}")
                print(f"   Tactical Line: {result['tactical_line']}")
            else:
                print(f"❌ Group dispatch failed: {result.get('error')}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append({'success': False, 'error': str(e)})
        
        # Wait between tests to avoid rate limiting
        if i < len(test_signals):
            print("   ⏳ Waiting 3 seconds...")
            time.sleep(3)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ATHENA GROUP DISPATCH TEST RESULTS")
    print("=" * 60)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print(f"📊 Success Rate: {(len(successful)/len(results))*100:.1f}%")
    
    # Group stats
    stats = athena_group_dispatcher.get_group_stats()
    print(f"\n📡 Group Statistics:")
    print(f"   Target Group: {stats['group_chat_id']}")
    print(f"   Total Signals Sent: {stats['total_signals_sent']}")
    print(f"   ATHENA Available: {stats['athena_available']}")
    print(f"   Dispatcher Active: {stats['dispatcher_active']}")
    
    if stats['last_signal']:
        last = stats['last_signal']
        print(f"   Last Signal: {last['symbol']} {last['direction']} ({last['confidence']}%)")
    
    if len(successful) == len(results):
        print("\n🎯 ALL TESTS PASSED - ATHENA GROUP DISPATCH OPERATIONAL! 🏛️")
    else:
        print(f"\n⚠️ {len(failed)} TESTS FAILED - CHECK CONFIGURATION")
    
    print("=" * 60)

def test_tactical_update():
    """Test sending a general tactical update"""
    print("\n🧪 Testing Tactical Update...")
    
    update_message = "🎯 Market conditions optimal. All operatives maintain tactical readiness."
    
    try:
        result = athena_group_dispatcher.send_tactical_update(update_message)
        
        if result['success']:
            print(f"✅ Tactical update sent successfully!")
            print(f"   Message ID: {result.get('message_id', 'N/A')}")
        else:
            print(f"❌ Tactical update failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Tactical update test failed: {e}")

if __name__ == "__main__":
    print("🏛️ ATHENA GROUP DISPATCH TEST SUITE")
    print("🎯 Testing short tactical messages for @bitten_signals")
    print("=" * 60)
    
    # Test signal dispatch
    test_group_dispatch()
    
    # Test tactical update
    test_tactical_update()
    
    print("\n🏛️ ATHENA GROUP DISPATCH TESTING COMPLETE")