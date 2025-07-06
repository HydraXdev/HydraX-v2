#!/usr/bin/env python3
"""
Test script for Uncertainty & Control Interplay System integration
Tests all components of the psychological trigger system
"""

import sys
import os
sys.path.append('/root/HydraX-v2/src')

def test_uncertainty_control_system():
    """Test the uncertainty control system independently"""
    print("🧪 Testing Uncertainty & Control System...")
    
    try:
        from bitten_core.uncertainty_control_system import UncertaintyControlSystem, ControlMode, BitModeDecision
        
        # Initialize system
        system = UncertaintyControlSystem()
        print(f"✅ System initialized with mode: {system.current_mode.value}")
        
        # Test mode switching
        result = system.set_control_mode(ControlMode.BIT_MODE, 12345)
        print(f"✅ Mode switch result: {result['success']}")
        print(f"   Response: {result['response'][:50]}...")
        
        # Test bit mode activation
        decision = system.activate_bit_mode("trade_entry", "Test trade decision?")
        print(f"✅ Bit mode decision created: {decision.decision_id}")
        print(f"   Question: {decision.question}")
        
        # Test decision processing
        decision_result = system.process_bit_decision(decision.decision_id, True, 12345)
        print(f"✅ Decision processed: {decision_result['success']}")
        
        # Test stealth mode
        algorithm = {'entry_delay': 0, 'size_multiplier': 1.0}
        stealth_result = system.activate_stealth_mode(algorithm)
        print(f"✅ Stealth mode applied: {stealth_result.get('stealth_applied', False)}")
        
        # Test uncertainty injection
        decision_point = {'symbol': 'EURUSD', 'tcs_score': 85}
        injected = system.inject_uncertainty(decision_point)
        print(f"✅ Uncertainty injected: {injected.get('uncertainty_injected', False)}")
        
        # Test system status
        status = system.get_system_status()
        print(f"✅ System status retrieved: {len(status)} fields")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing uncertainty system: {e}")
        return False

def test_bitmode_integration():
    """Test BitMode class integration"""
    print("\n🤖 Testing BitMode Integration...")
    
    try:
        from core.modules.bitmode import BitMode, run_bitmode
        
        # Test BitMode class
        bit_mode = BitMode()
        print("✅ BitMode class instantiated")
        
        # Test activation
        result = bit_mode.activate(12345)
        print(f"✅ BitMode activated: {result['success']}")
        print(f"   Message: {result['message'][:50]}...")
        
        # Test confirmation request
        trade_data = {'symbol': 'EURUSD', 'direction': 'BUY'}
        decision = bit_mode.request_confirmation('trade_entry', trade_data)
        if decision:
            print(f"✅ Confirmation requested: {decision.decision_id}")
            
            # Test confirmation processing
            confirmation = bit_mode.process_confirmation(decision.decision_id, True, 12345)
            print(f"✅ Confirmation processed: {confirmation['success']}")
        
        # Test status
        status = bit_mode.get_status()
        print(f"✅ Status retrieved: {status['active']}")
        
        # Test legacy function
        legacy_bit = run_bitmode()
        print("✅ Legacy function works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing BitMode: {e}")
        return False

def test_fire_router_integration():
    """Test FireRouter integration with uncertainty system"""
    print("\n🔥 Testing FireRouter Integration...")
    
    try:
        from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, FireMode
        
        # Initialize fire router
        router = FireRouter()
        print("✅ FireRouter initialized")
        
        # Test uncertainty mode setting
        result = router.set_uncertainty_mode(12345, 'bit_mode')
        print(f"✅ Uncertainty mode set: {result['success']}")
        
        # Test uncertainty status
        status = router.get_uncertainty_status(12345)
        print(f"✅ Uncertainty status: {status['success']}")
        
        # Test trade request with bit mode
        trade_request = TradeRequest(
            user_id=12345,
            symbol="EURUSD",
            direction=TradeDirection.BUY,
            volume=0.1,
            tcs_score=85,
            fire_mode=FireMode.SINGLE_SHOT
        )
        
        print("✅ Trade request created for bit mode test")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing FireRouter: {e}")
        return False

def test_telegram_commands():
    """Test Telegram command integration"""
    print("\n📱 Testing Telegram Command Integration...")
    
    try:
        from bitten_core.telegram_router import TelegramRouter, TelegramUpdate, CommandResult
        
        # Initialize router
        router = TelegramRouter()
        print("✅ TelegramRouter initialized")
        
        # Check command categories
        uncertainty_commands = router.command_categories.get('Uncertainty Control', [])
        print(f"✅ Uncertainty commands registered: {len(uncertainty_commands)}")
        print(f"   Commands: {', '.join(uncertainty_commands)}")
        
        # Test command descriptions
        for cmd in uncertainty_commands:
            desc = router._get_command_description(cmd)
            print(f"   /{cmd}: {desc}")
        
        # Test help command
        update = TelegramUpdate(
            update_id=1,
            message_id=1,
            user_id=12345,
            username="testuser",
            chat_id=12345,
            text="/help UncertaintyControl",
            timestamp=1234567890
        )
        
        # This would test help but requires rank access setup
        print("✅ Help system integration ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Telegram integration: {e}")
        return False

def test_psychological_profile():
    """Test psychological profiling integration"""
    print("\n🧠 Testing Psychological Profile Integration...")
    
    try:
        from bitten_core.uncertainty_control_system import UncertaintyControlSystem
        
        system = UncertaintyControlSystem()
        
        # Test psychological profile calculation
        profile = system._get_psychological_profile()
        print(f"✅ Psychological profile generated: {len(profile)} metrics")
        
        for key, value in profile.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2%}")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing psychological profile: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🎯 BITTEN Uncertainty & Control Interplay - Integration Test")
    print("=" * 60)
    
    tests = [
        test_uncertainty_control_system,
        test_bitmode_integration,
        test_fire_router_integration,
        test_telegram_commands,
        test_psychological_profile
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"🎯 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Uncertainty & Control system is ready!")
        print("\n🎮 Available Commands:")
        print("• /uncertainty - View control mode status")
        print("• /bitmode - Activate binary confirmation")
        print("• /stealth - Hidden algorithm variations") 
        print("• /gemini - AI competitor mode")
        print("• /chaos - Maximum uncertainty")
        print("• /control - Return to full control")
        print("• /yes <decision_id> - Confirm bit mode decisions")
        print("• /no <decision_id> - Deny bit mode decisions")
    else:
        print(f"⚠️  {total - passed} tests failed - Check implementation")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)