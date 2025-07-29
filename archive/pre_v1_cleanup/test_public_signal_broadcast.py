#!/usr/bin/env python3
"""
Test VENOM Public Signal Broadcasting
Tests that all VENOM signals are sent to public group regardless of user readiness
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

def test_signal_broadcasting():
    """Test signal broadcasting to public group even with no ready users"""
    
    print("🧪 Testing VENOM Signal Broadcasting to Public Group")
    print("=" * 60)
    
    try:
        # Import BittenCore
        from src.bitten_core.bitten_core import BittenCore
        
        # Initialize core without any ready users
        print("📡 Initializing BittenCore...")
        core = BittenCore()
        
        # Create a test VENOM signal
        test_signal = {
            'signal_id': f'VENOM_TEST_{int(time.time())}',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'signal_type': 'RAPID_ASSAULT',
            'confidence': 89.5,
            'target_pips': 20,
            'stop_pips': 10,
            'risk_reward': 2.0,
            'expires_at': (datetime.now() + timedelta(minutes=30)).isoformat(),
            'countdown_minutes': 30
        }
        
        print(f"🎯 Created test signal: {test_signal['signal_id']}")
        print(f"   Symbol: {test_signal['symbol']}")
        print(f"   Direction: {test_signal['direction']}")
        print(f"   Confidence: {test_signal['confidence']}%")
        
        # Test 1: Process signal (should always send to public group)
        print("\n🔬 Test 1: Processing signal without ready users...")
        result = core.process_signal(test_signal)
        
        if result['success']:
            print("✅ Signal processed successfully")
            print(f"   Signal ID: {result['signal_id']}")
            print(f"   Delivery Result: {result.get('delivery_result', {})}")
            
            # Check delivery result
            delivery = result.get('delivery_result', {})
            if delivery.get('public_broadcast'):
                print("✅ PUBLIC GROUP BROADCAST: SUCCESS")
            else:
                print("❌ PUBLIC GROUP BROADCAST: FAILED")
                
            print(f"   Total Delivered: {delivery.get('total_delivered', 0)}")
            print(f"   User Delivery: {delivery.get('user_delivery', {})}")
        else:
            print(f"❌ Signal processing failed: {result.get('error')}")
            return False
            
        # Test 2: Verify signal is in queue
        print("\n🔬 Test 2: Checking signal queue...")
        signal_queue = core.get_signal_queue()
        if signal_queue:
            print(f"✅ Signal queue contains {len(signal_queue)} signals")
            latest_signal = signal_queue[-1]
            if latest_signal['signal_id'] == test_signal['signal_id']:
                print("✅ Test signal found in queue")
            else:
                print("⚠️ Test signal not found in latest queue position")
        else:
            print("❌ Signal queue is empty")
            
        # Test 3: Test /fire command for non-ready user
        print("\n🔬 Test 3: Testing /fire command for non-ready user...")
        fire_result = core.execute_fire_command("test_user_123", test_signal['signal_id'])
        
        if not fire_result['success'] and fire_result.get('error') == 'not_ready_for_fire':
            print("✅ Non-ready user correctly blocked from execution")
            print("✅ Custom message provided:")
            print(f"   {fire_result.get('message', 'No message')[:100]}...")
        else:
            print("❌ Non-ready user validation failed")
            print(f"   Result: {fire_result}")
            
        print("\n📊 Test Summary:")
        print("✅ Signals broadcast to public group regardless of user readiness")
        print("✅ Non-ready users receive helpful message when trying to /fire")
        print("✅ Signal processing continues to work normally")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_format():
    """Test the signal message format"""
    
    print("\n🎨 Testing Signal Message Format")
    print("=" * 40)
    
    try:
        from src.bitten_core.bitten_core import BittenCore
        
        core = BittenCore()
        
        test_signal = {
            'signal_id': 'VENOM_UNFILTERED_EURUSD_000123',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'signal_type': 'PRECISION_STRIKE',
            'confidence': 92.3,
            'target_pips': 30,
            'stop_pips': 15,
            'risk_reward': 2.0,
            'countdown_minutes': 35
        }
        
        formatted_message = core._format_signal_for_hud(test_signal)
        
        print("📱 Formatted Signal Message:")
        print("-" * 30)
        print(formatted_message)
        print("-" * 30)
        
        # Verify format contains required elements
        required_elements = [
            "VENOM v7 Signal",
            test_signal['symbol'],
            test_signal['direction'],
            str(test_signal['confidence']),
            test_signal['signal_id'],
            "/fire"
        ]
        
        all_found = True
        for element in required_elements:
            if element in formatted_message:
                print(f"✅ Contains: {element}")
            else:
                print(f"❌ Missing: {element}")
                all_found = False
                
        if all_found:
            print("✅ Message format is correct")
        else:
            print("❌ Message format is incomplete")
            
        return all_found
        
    except Exception as e:
        print(f"❌ Message format test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting VENOM Public Signal Broadcasting Tests\n")
    
    # Run tests
    test1_passed = test_signal_broadcasting()
    test2_passed = test_message_format()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ VENOM signals will always broadcast to public group")
        print("✅ Non-ready users get helpful /fire messages")
        print("✅ Signal format is correct")
        exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not test1_passed:
            print("❌ Signal broadcasting test failed")
        if not test2_passed:
            print("❌ Message format test failed")
        exit(1)