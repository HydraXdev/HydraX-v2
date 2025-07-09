#!/usr/bin/env python3
"""
Test script to verify Nibbler TCS threshold has been lowered to 70
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bitten_core.fire_modes import TIER_CONFIGS, TierLevel
from src.bitten_core.fire_mode_validator import FireModeValidator
from src.bitten_core.signal_fusion import TierBasedRouter, ConfidenceTier, FusedSignal
from src.bitten_core.config_manager import ConfigManager
import yaml

def test_tier_settings_config():
    """Test that tier_settings.yml has correct TCS for Nibbler"""
    print("\n1. Testing tier_settings.yml configuration...")
    
    with open('/root/HydraX-v2/config/tier_settings.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    nibbler_tcs = config['tiers']['NIBBLER']['fire_settings']['min_tcs']
    bitmode_tcs = config['bitmode']['tcs_min']
    
    print(f"   - Nibbler min_tcs: {nibbler_tcs}")
    print(f"   - Bitmode tcs_min: {bitmode_tcs}")
    
    assert nibbler_tcs == 70, f"Expected Nibbler min_tcs to be 70, got {nibbler_tcs}"
    assert bitmode_tcs == 70, f"Expected bitmode tcs_min to be 70, got {bitmode_tcs}"
    print("   ✓ Configuration file updated correctly")

def test_fire_modes():
    """Test that fire_modes.py has correct TCS for Nibbler"""
    print("\n2. Testing fire_modes.py configuration...")
    
    nibbler_config = TIER_CONFIGS[TierLevel.NIBBLER]
    print(f"   - Nibbler min_tcs: {nibbler_config.min_tcs}")
    
    assert nibbler_config.min_tcs == 70, f"Expected Nibbler min_tcs to be 70, got {nibbler_config.min_tcs}"
    print("   ✓ Fire modes configuration correct")

def test_fire_mode_validator():
    """Test that FireModeValidator accepts 70% TCS for Nibbler in SEMI_AUTO mode"""
    print("\n3. Testing FireModeValidator for Nibbler SEMI_AUTO...")
    
    validator = FireModeValidator()
    
    # Test with 70% TCS for Nibbler
    test_payload = {
        'fire_mode': 'semi_auto',
        'tcs': 70,
        'volume': 0.01,
        'stop_loss': 10,
        'take_profit': 20
    }
    
    nibbler_profile = {
        'tier': 'nibbler',
        'user_id': 'test_nibbler',
        'account_balance': 1000,
        'shots_today': 0,
        'open_positions': 0,
        'total_exposure_percent': 0
    }
    
    # Test 70% TCS (should pass)
    result = validator._validate_semi_auto(test_payload, nibbler_profile)
    print(f"   - Testing 70% TCS: {'PASS' if result.valid else 'FAIL'}")
    if not result.valid:
        print(f"     Reason: {result.reason}")
    assert result.valid, "Nibbler should accept 70% TCS in SEMI_AUTO mode"
    
    # Test 69% TCS (should fail)
    test_payload['tcs'] = 69
    result = validator._validate_semi_auto(test_payload, nibbler_profile)
    print(f"   - Testing 69% TCS: {'PASS' if result.valid else 'FAIL'} (expected to fail)")
    assert not result.valid, "Nibbler should reject TCS below 70%"
    
    # Test Commander tier still requires 75%
    commander_profile = {
        'tier': 'commander',
        'user_id': 'test_commander',
        'account_balance': 5000,
        'shots_today': 0,
        'open_positions': 0,
        'total_exposure_percent': 0
    }
    
    test_payload['tcs'] = 74
    result = validator._validate_semi_auto(test_payload, commander_profile)
    print(f"   - Testing Commander with 74% TCS: {'PASS' if result.valid else 'FAIL'} (expected to fail)")
    assert not result.valid, "Commander should still require 75% TCS"
    
    test_payload['tcs'] = 75
    result = validator._validate_semi_auto(test_payload, commander_profile)
    print(f"   - Testing Commander with 75% TCS: {'PASS' if result.valid else 'FAIL'}")
    assert result.valid, "Commander should accept 75% TCS"
    
    print("   ✓ FireModeValidator updated correctly")

def test_signal_fusion_routing():
    """Test that signal fusion routes 70%+ TCS signals to Nibbler"""
    print("\n4. Testing SignalFusion tier routing for Nibbler...")
    
    router = TierBasedRouter()
    
    # Create mock sources for signal
    from src.bitten_core.signal_fusion import IntelSource
    sources = [
        IntelSource(
            source_id='test1',
            source_type='technical',
            signal='BUY',
            confidence=70,
            weight=1.0
        ),
        IntelSource(
            source_id='test2',
            source_type='sentiment',
            signal='BUY',
            confidence=70,
            weight=1.0
        ),
        IntelSource(
            source_id='test3',
            source_type='ai_bot',
            signal='BUY',
            confidence=70,
            weight=1.0
        )
    ]
    
    # Test RAPID tier signal with 70% confidence
    rapid_signal = FusedSignal(
        signal_id='TEST_RAPID_70',
        pair='EURUSD',
        direction='BUY',
        confidence=70,
        tier=ConfidenceTier.RAPID,
        entry=1.0800,
        sl=1.0790,
        tp=1.0820,
        sources=sources,
        fusion_scores={'weighted_confidence': 70}
    )
    
    # Reset daily counts
    router._check_daily_reset()
    
    # Test routing
    should_route = router.route_signal(rapid_signal, 'nibbler')
    print(f"   - RAPID signal (70% TCS) to Nibbler: {'ROUTED' if should_route else 'BLOCKED'}")
    assert should_route, "Nibbler should receive RAPID signals with 70%+ TCS"
    
    # Test signal below 70%
    rapid_signal.confidence = 69
    should_route = router.route_signal(rapid_signal, 'nibbler')
    print(f"   - RAPID signal (69% TCS) to Nibbler: {'ROUTED' if should_route else 'BLOCKED'} (expected to block)")
    assert not should_route, "Nibbler should not receive RAPID signals below 70% TCS"
    
    print("   ✓ Signal fusion routing updated correctly")

def test_tcs_validation():
    """Test the general TCS validation in FireModeValidator"""
    print("\n5. Testing general TCS validation...")
    
    validator = FireModeValidator()
    
    # Test Nibbler tier TCS validation
    result = validator._validate_tcs(70, TierLevel.NIBBLER, 'single_shot')
    print(f"   - Nibbler 70% TCS validation: {'PASS' if result.valid else 'FAIL'}")
    assert result.valid, "Nibbler should accept 70% TCS"
    
    result = validator._validate_tcs(69, TierLevel.NIBBLER, 'single_shot')
    print(f"   - Nibbler 69% TCS validation: {'PASS' if result.valid else 'FAIL'} (expected to fail)")
    assert not result.valid, "Nibbler should reject TCS below 70%"
    
    print("   ✓ TCS validation working correctly")

def main():
    print("=" * 60)
    print("Testing Nibbler TCS Threshold Update (75 → 70)")
    print("=" * 60)
    
    try:
        test_tier_settings_config()
        test_fire_modes()
        test_fire_mode_validator()
        test_signal_fusion_routing()
        test_tcs_validation()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("Nibbler tier TCS threshold successfully lowered to 70%")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()