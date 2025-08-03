#!/usr/bin/env python3
"""
🧪 ATHENA MISSION SYSTEM TEST SUITE
Complete validation of ATHENA migration and integration
"""

import sys
import time
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

def test_athena_personality():
    """Test ATHENA personality system"""
    print("🧪 Testing ATHENA Personality...")
    try:
        from src.bitten_core.personality.athena_personality import AthenaPersonality
        athena = AthenaPersonality()
        
        # Test mission briefing
        test_signal = {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.0875,
            'take_profit': 1.0925,
            'stop_loss': 1.0825,
            'tcs_score': 91.2
        }
        
        briefing = athena.get_mission_briefing(test_signal, "COMMANDER", "TEST_001")
        assert "MISSION BRIEFING" in briefing
        assert "EURUSD BUY" in briefing
        assert "91.2%" in briefing
        
        print("✅ ATHENA Personality: PASS")
        return True
    except Exception as e:
        print(f"❌ ATHENA Personality: FAIL - {e}")
        return False

def test_athena_mission_bot():
    """Test ATHENA Mission Bot initialization"""
    print("🧪 Testing ATHENA Mission Bot...")
    try:
        from athena_mission_bot import AthenaMissionBot
        bot = AthenaMissionBot()
        
        assert bot.athena_available == True
        assert len(bot.authorized_users) > 0
        assert bot.mission_counter == 0
        
        print("✅ ATHENA Mission Bot: PASS")
        return True
    except Exception as e:
        print(f"❌ ATHENA Mission Bot: FAIL - {e}")
        return False

def test_athena_signal_dispatcher():
    """Test ATHENA Signal Dispatcher"""
    print("🧪 Testing ATHENA Signal Dispatcher...")
    try:
        from athena_signal_dispatcher import athena_dispatcher
        
        test_signal = {
            'signal_id': f'TEST_DISPATCHER_{int(time.time())}',
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'confidence': 88.5,
            'entry_price': 1.2650,
            'take_profit': 1.2600,
            'stop_loss': 1.2700,
            'citadel_shield': {
                'score': 8.2,
                'classification': 'SHIELD_APPROVED',
                'insights': 'Institutional breakout detected'
            }
        }
        
        result = athena_dispatcher.dispatch_signal_via_athena(test_signal)
        assert result['success'] == True
        assert result['dispatched_to'] > 0
        
        print("✅ ATHENA Signal Dispatcher: PASS")
        return True
    except Exception as e:
        print(f"❌ ATHENA Signal Dispatcher: FAIL - {e}")
        return False

def test_bitten_core_integration():
    """Test BittenCore → ATHENA integration"""
    print("🧪 Testing BittenCore Integration...")
    try:
        from src.bitten_core.bitten_core import BittenCore
        
        core = BittenCore()
        
        test_signal = {
            'signal_id': f'INTEGRATION_TEST_{int(time.time())}',
            'symbol': 'USDJPY',
            'direction': 'BUY',
            'signal_type': 'PRECISION_STRIKE',
            'confidence': 89.7,
            'target_pips': 30,
            'stop_pips': 15,
            'risk_reward': 2.0,
            'entry_price': 150.25,
            'timestamp': '2025-07-30T15:50:00Z'
        }
        
        result = core.process_venom_signal(test_signal)
        assert result['success'] == True
        assert 'athena_dispatch' in result['delivery_result']
        
        print("✅ BittenCore Integration: PASS")
        return True
    except Exception as e:
        print(f"❌ BittenCore Integration: FAIL - {e}")
        return False

def test_voice_bot_athena_removal():
    """Test that ATHENA was properly removed from voice bot"""
    print("🧪 Testing Voice Bot ATHENA Removal...")
    try:
        with open('/root/HydraX-v2/bitten_voice_personality_bot.py', 'r') as f:
            voice_bot_content = f.read()
        
        # Should NOT contain active ATHENA handlers
        assert '@self.bot.message_handler(commands=[\'athena\'])' not in voice_bot_content
        
        # Should contain notification about ATHENA being moved
        assert 'ATHENA - Strategic Commander now operates via dedicated Mission Bot' in voice_bot_content
        
        print("✅ Voice Bot ATHENA Removal: PASS")
        return True
    except Exception as e:
        print(f"❌ Voice Bot ATHENA Removal: FAIL - {e}")
        return False

def main():
    """Run complete ATHENA migration test suite"""
    print("🏛️ ATHENA MISSION SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_athena_personality,
        test_athena_mission_bot,
        test_athena_signal_dispatcher,
        test_bitten_core_integration,
        test_voice_bot_athena_removal
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"🧪 ATHENA MIGRATION TEST RESULTS")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📊 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎯 ATHENA MIGRATION: ✅ COMPLETE AND OPERATIONAL")
        print("🏛️ ATHENA is now the official mission commander for BITTEN signals")
    else:
        print("⚠️ ATHENA MIGRATION: Issues detected - review failed tests")
    
    print("=" * 60)

if __name__ == "__main__":
    main()