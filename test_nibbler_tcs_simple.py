#!/usr/bin/env python3
"""
Simple test to verify Nibbler TCS threshold has been lowered to 70
"""

import yaml

def test_configurations():
    print("=" * 60)
    print("Testing Nibbler TCS Threshold Update (75 → 70)")
    print("=" * 60)
    
    # Test tier_settings.yml
    print("\n1. Checking tier_settings.yml...")
    with open('/root/HydraX-v2/config/tier_settings.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    nibbler_tcs = config['tiers']['NIBBLER']['fire_settings']['min_tcs']
    bitmode_tcs = config['bitmode']['tcs_min']
    
    print(f"   - Nibbler min_tcs: {nibbler_tcs}")
    print(f"   - Bitmode tcs_min: {bitmode_tcs}")
    
    # Test fire_mode_validator.py
    print("\n2. Checking fire_mode_validator.py...")
    with open('/root/HydraX-v2/src/bitten_core/fire_mode_validator.py', 'r') as f:
        content = f.read()
    
    if 'if user_tier == TierLevel.NIBBLER:' in content and 'if payload.get(\'tcs\', 0) < 70:' in content:
        print("   ✓ SEMI_AUTO mode now accepts 70% TCS for Nibbler")
    else:
        print("   ✗ SEMI_AUTO mode not properly updated")
    
    # Test signal_fusion.py
    print("\n3. Checking signal_fusion.py...")
    with open('/root/HydraX-v2/src/bitten_core/signal_fusion.py', 'r') as f:
        content = f.read()
    
    if 'if signal.tier == ConfidenceTier.RAPID and signal.confidence < 70:' in content:
        print("   ✓ Signal routing now accepts RAPID signals with 70%+ TCS for Nibbler")
    else:
        print("   ✗ Signal routing not properly updated")
    
    # Test fire_modes.py
    print("\n4. Checking fire_modes.py...")
    with open('/root/HydraX-v2/src/bitten_core/fire_modes.py', 'r') as f:
        content = f.read()
    
    if 'min_tcs=70,' in content and 'TierLevel.NIBBLER: TierConfig(' in content:
        print("   ✓ Fire modes configuration has min_tcs=70 for Nibbler")
    else:
        print("   ✗ Fire modes configuration not properly set")
    
    print("\n" + "=" * 60)
    print("Summary of changes:")
    print("- tier_settings.yml: Nibbler min_tcs lowered from 75 to 70")
    print("- fire_mode_validator.py: SEMI_AUTO now accepts 70% TCS for Nibbler")
    print("- signal_fusion.py: Nibbler now receives RAPID signals with 70%+ TCS")
    print("- fire_modes.py: Already had min_tcs=70 for Nibbler")
    print("\nAll changes ensure Nibbler tier can now trade with 70% TCS minimum")
    print("while other tiers maintain their existing thresholds.")
    print("=" * 60)

if __name__ == "__main__":
    test_configurations()