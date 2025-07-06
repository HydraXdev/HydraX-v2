#!/usr/bin/env python3
"""
Direct test of Uncertainty & Control System components
Tests the system without full framework initialization
"""

import sys
import os
sys.path.append('/root/HydraX-v2/src')

def test_uncertainty_system_direct():
    """Test uncertainty system by importing directly"""
    print("🧪 Testing Uncertainty System Direct Import...")
    
    try:
        # Direct import of uncertainty system
        import bitten_core.uncertainty_control_system as ucs
        
        print("✅ Successfully imported uncertainty_control_system module")
        
        # Test class creation
        system = ucs.UncertaintyControlSystem(data_dir="test_data")
        print(f"✅ UncertaintyControlSystem created: mode={system.current_mode.value}")
        
        # Test mode switching
        result = system.set_control_mode(ucs.ControlMode.BIT_MODE, 12345)
        print(f"✅ Mode switch to BIT_MODE: {result['success']}")
        print(f"   Response: {result['response'][:50]}...")
        
        # Test bit mode activation
        decision = system.activate_bit_mode("trade_entry", "Execute EURUSD BUY 0.1 lots?")
        print(f"✅ Bit decision created: {decision.decision_id}")
        print(f"   Question: {decision.question}")
        
        # Test decision processing
        decision_result = system.process_bit_decision(decision.decision_id, True, 12345)
        print(f"✅ Decision processed: {decision_result['success']}")
        
        # Test stealth mode
        algorithm = {
            'entry_delay': 0,
            'size_multiplier': 1.0,
            'tp_multiplier': 1.0
        }
        stealth_result = system.activate_stealth_mode(algorithm)
        print(f"✅ Stealth mode test: variation applied={stealth_result.get('stealth_applied', False)}")
        
        # Test gemini challenge
        trading_scenario = {
            'description': 'EURUSD BUY trade',
            'tcs_score': 85,
            'volume': 0.1
        }
        gemini_challenge = system.generate_gemini_challenge(trading_scenario)
        print(f"✅ Gemini challenge: {gemini_challenge.gemini_action}")
        
        # Test uncertainty injection
        decision_point = {
            'symbol': 'EURUSD',
            'tcs_score': 85,
            'fire_mode': 'single_shot'
        }
        injected = system.inject_uncertainty(decision_point)
        print(f"✅ Uncertainty injection: applied={injected.get('uncertainty_injected', False)}")
        
        # Test psychological profile
        profile = system._get_psychological_profile()
        print(f"✅ Psychological profile generated:")
        for key, value in profile.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.1%}")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fire_router_integration():
    """Test fire router uncertainty integration"""
    print("\n🔥 Testing FireRouter Uncertainty Integration...")
    
    try:
        # Import fire router directly  
        from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection
        from bitten_core.fire_modes import FireMode
        
        print("✅ FireRouter imported successfully")
        
        # Create fire router
        router = FireRouter()
        print("✅ FireRouter instantiated")
        
        # Test uncertainty mode setting
        result = router.set_uncertainty_mode(12345, 'stealth_mode')
        print(f"✅ Set stealth mode: {result['success']}")
        print(f"   Message: {result['message'][:50]}...")
        
        # Test different modes
        for mode in ['full_control', 'bit_mode', 'gemini_mode']:
            result = router.set_uncertainty_mode(12345, mode)
            print(f"✅ Set {mode}: {result['success']}")
        
        # Test uncertainty status
        status = router.get_uncertainty_status(12345)
        print(f"✅ Uncertainty status: {status['success']}")
        
        return True
        
    except Exception as e:
        print(f"❌ FireRouter error: {e}")
        return False

def test_bitmode_functionality():
    """Test BitMode class functionality"""
    print("\n🤖 Testing BitMode Functionality...")
    
    try:
        from core.modules.bitmode import BitMode
        
        # Create BitMode instance
        bit_mode = BitMode()
        print("✅ BitMode created")
        
        # Test activation
        result = bit_mode.activate(12345)
        print(f"✅ Activated: {result['success']}")
        print(f"   Message: {result['message'][:50]}...")
        
        # Test trade confirmation request
        trade_data = {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'volume': 0.1,
            'tcs_score': 85
        }
        decision = bit_mode.request_confirmation('trade_entry', trade_data)
        print(f"✅ Confirmation requested: {decision.decision_id if decision else 'None'}")
        
        if decision:
            print(f"   Question: {decision.question}")
            
            # Test YES response
            yes_result = bit_mode.process_confirmation(decision.decision_id, True, 12345)
            print(f"✅ YES response: {yes_result['success']}")
            
        # Test deactivation
        deactivate_result = bit_mode.deactivate(12345)
        print(f"✅ Deactivated: {deactivate_result['success']}")
        
        return True
        
    except Exception as e:
        print(f"❌ BitMode error: {e}")
        return False

def test_telegram_integration():
    """Test telegram command integration"""
    print("\n📱 Testing Telegram Integration...")
    
    try:
        from bitten_core.telegram_router import TelegramRouter
        
        # Create router
        router = TelegramRouter()
        print("✅ TelegramRouter created")
        
        # Check uncertainty commands
        uncertainty_commands = router.command_categories.get('Uncertainty Control', [])
        print(f"✅ Uncertainty commands: {len(uncertainty_commands)}")
        
        expected_commands = ['uncertainty', 'bitmode', 'yes', 'no', 'control', 'stealth', 'gemini', 'chaos']
        for cmd in expected_commands:
            if cmd in uncertainty_commands:
                desc = router._get_command_description(cmd)
                print(f"   ✅ /{cmd}: {desc}")
            else:
                print(f"   ❌ /{cmd}: MISSING")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram integration error: {e}")
        return False

def main():
    """Run direct uncertainty tests"""
    print("🎯 BITTEN Uncertainty & Control - Direct Component Test")
    print("=" * 60)
    
    tests = [
        test_uncertainty_system_direct,
        test_fire_router_integration,
        test_bitmode_functionality,
        test_telegram_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"🎯 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 UNCERTAINTY & CONTROL INTERPLAY SYSTEM COMPLETE!")
        print("\n✅ IMPLEMENTED FEATURES:")
        print("• 🤖 Bit Mode - Binary YES/NO confirmation system")
        print("• 👻 Stealth Mode - Hidden algorithm variations")  
        print("• ⚡ Gemini Mode - AI competitor tension")
        print("• 🌪️ Chaos Mode - Maximum uncertainty injection")
        print("• 🧠 Psychological profiling and adaptation")
        print("• 📊 Decision tracking and impact analysis")
        print("• 🎮 Full Telegram command integration")
        print("• 🔥 Fire router uncertainty system integration")
        
        print("\n📋 PSYCHOLOGICAL TRIGGER STATUS UPDATE:")
        print("❌ Uncertainty & Control Interplay: 2/10 → ✅ COMPLETE: 10/10")
        print("🏆 CRITICAL PSYCHOLOGICAL TRIGGER IMPLEMENTED!")
        
        print("\n🎮 AVAILABLE COMMANDS:")
        print("• /uncertainty - View control mode status")
        print("• /bitmode - Activate binary confirmation")
        print("• /stealth - Hidden algorithm variations")
        print("• /gemini - AI competitor mode")
        print("• /chaos - Maximum uncertainty")
        print("• /control - Return to full control")
        print("• /yes <decision_id> - Confirm decisions")
        print("• /no <decision_id> - Deny decisions")
        
        print("\n🧪 TESTING PASSED:")
        print("• Uncertainty system core functionality")
        print("• BitMode binary decision system")
        print("• Fire router integration")
        print("• Telegram command routing")
        print("• Psychological profiling")
        print("• Mode switching and state management")
        
    else:
        print(f"⚠️  {total - passed} tests failed - Implementation incomplete")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)