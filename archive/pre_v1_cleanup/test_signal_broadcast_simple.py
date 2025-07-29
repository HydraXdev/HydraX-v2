#!/usr/bin/env python3
"""
Simple test for VENOM signal broadcasting changes
Tests the core logic without full system dependencies
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

def test_signal_delivery_method():
    """Test the modified _deliver_signal_to_users method directly"""
    
    print("🧪 Testing Signal Delivery Method Changes")
    print("=" * 50)
    
    try:
        # Mock the dependencies to avoid full system initialization
        class MockUserRegistry:
            def get_all_ready_users(self):
                # Return empty dict to simulate no ready users
                return {}
        
        class MockProductionBot:
            def __init__(self):
                self.sent_messages = []
                
            def send_adaptive_response(self, chat_id, message_text, user_tier, user_action):
                self.sent_messages.append({
                    'chat_id': chat_id,
                    'message': message_text,
                    'tier': user_tier,
                    'action': user_action
                })
                print(f"📤 Mock message sent to {chat_id} ({user_tier})")
                if chat_id == -1002581996861:
                    print("✅ PUBLIC GROUP MESSAGE SENT!")
                return True
        
        # Create minimal core instance with mocked dependencies
        from src.bitten_core.bitten_core import BittenCore
        
        core = BittenCore()
        core.user_registry = MockUserRegistry()
        core.production_bot = MockProductionBot()
        core.user_active_signals = {}
        core.user_signal_history = {}
        
        # Create test signal
        test_signal = {
            'signal_id': 'VENOM_TEST_PUBLIC_BROADCAST',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'signal_type': 'RAPID_ASSAULT',
            'confidence': 89.5,
            'target_pips': 20,
            'stop_pips': 10,
            'risk_reward': 2.0,
            'countdown_minutes': 30
        }
        
        print(f"🎯 Testing with signal: {test_signal['signal_id']}")
        print(f"   No ready users in registry (empty dict)")
        
        # Test the delivery method
        print("\n🔬 Calling _deliver_signal_to_users...")
        result = core._deliver_signal_to_users(test_signal)
        
        print(f"\n📊 Delivery Result:")
        print(f"   Success: {result.get('success')}")
        print(f"   Public Broadcast: {result.get('public_broadcast')}")
        print(f"   Total Delivered: {result.get('total_delivered')}")
        print(f"   Signal ID: {result.get('signal_id')}")
        
        # Check if public group got the message
        public_messages = [msg for msg in core.production_bot.sent_messages 
                          if msg['chat_id'] == -1002581996861]
        
        if public_messages:
            print("✅ PUBLIC GROUP RECEIVED SIGNAL")
            print(f"   Message count: {len(public_messages)}")
            for msg in public_messages:
                print(f"   Tier: {msg['tier']}")
                print(f"   Action: {msg['action']}")
                print(f"   Message preview: {msg['message'][:100]}...")
        else:
            print("❌ PUBLIC GROUP DID NOT RECEIVE SIGNAL")
            
        # Test message format
        print(f"\n📱 Testing Message Format...")
        formatted_msg = core._format_signal_for_hud(test_signal)
        
        required_elements = [
            "VENOM v7 Signal",
            test_signal['symbol'],
            test_signal['direction'],
            str(test_signal['confidence']),
            test_signal['signal_id'],
            "/fire"
        ]
        
        print("🔍 Checking message format:")
        all_found = True
        for element in required_elements:
            if element in formatted_msg:
                print(f"   ✅ Contains: {element}")
            else:
                print(f"   ❌ Missing: {element}")
                all_found = False
                
        if all_found:
            print("\n✅ MESSAGE FORMAT CORRECT")
        else:
            print("\n❌ MESSAGE FORMAT INCOMPLETE")
            
        # Overall test result
        public_broadcast_works = result.get('public_broadcast', False)
        
        if public_broadcast_works and all_found:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Signals broadcast to public group even with no ready users")
            print("✅ Message format is correct")
            return True
        else:
            print("\n❌ TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fire_command_error_message():
    """Test the new error message for non-ready users"""
    
    print("\n🔒 Testing Fire Command Error Message")
    print("=" * 40)
    
    try:
        # Mock dependencies
        class MockUserRegistry:
            def is_user_ready_for_fire(self, user_id):
                return False  # Always return false to test error message
        
        from src.bitten_core.bitten_core import BittenCore
        
        core = BittenCore()
        core.user_registry = MockUserRegistry()
        core.processed_signals = {
            'TEST_SIGNAL_123': {
                'signal_id': 'TEST_SIGNAL_123',
                'symbol': 'EURUSD',
                'direction': 'BUY'
            }
        }
        
        print("🔬 Testing execute_fire_command for non-ready user...")
        result = core.execute_fire_command("test_user_not_ready", "TEST_SIGNAL_123")
        
        print(f"📊 Fire Command Result:")
        print(f"   Success: {result.get('success')}")
        print(f"   Error Type: {result.get('error')}")
        
        if result.get('error') == 'not_ready_for_fire':
            print("✅ Correct error type returned")
            
            message = result.get('message', '')
            if 'not ready to fire' in message.lower() and 'joinbitten.com' in message:
                print("✅ Correct error message format")
                print(f"   Message preview: {message[:100]}...")
                return True
            else:
                print("❌ Incorrect error message format")
                print(f"   Message: {message}")
                return False
        else:
            print("❌ Incorrect error type")
            print(f"   Expected: 'not_ready_for_fire'")
            print(f"   Got: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error message test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple Signal Broadcasting Tests\n")
    
    # Run tests
    test1_passed = test_signal_delivery_method()
    test2_passed = test_fire_command_error_message()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ Public group broadcasting works even with no ready users")
        print("✅ Non-ready users get proper error message for /fire")
        print("\n🎯 IMPLEMENTATION COMPLETE:")
        print("   • VENOM signals always broadcast to public group")
        print("   • Ready user check only affects /fire execution")
        print("   • Message format includes signal ID and /fire button")
        exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not test1_passed:
            print("❌ Public broadcasting test failed")
        if not test2_passed:
            print("❌ Error message test failed")
        exit(1)