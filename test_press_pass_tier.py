#!/usr/bin/env python3
"""
Test script to verify PRESS_PASS tier integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bitten_core.fire_modes import TierLevel, TIER_CONFIGS, FireMode, FireModeValidator
from src.bitten_core.config_manager import TradingPairsConfig
from src.database.models import TierLevel as DBTierLevel

def test_press_pass_tier():
    """Test PRESS_PASS tier configuration"""
    
    print("Testing PRESS_PASS Tier Integration...")
    print("=" * 50)
    
    # Test 1: Check if PRESS_PASS exists in TierLevel enum
    print("\n1. Testing TierLevel enum:")
    try:
        press_pass = TierLevel.PRESS_PASS
        print(f"✓ PRESS_PASS enum value: {press_pass.value}")
    except AttributeError:
        print("✗ PRESS_PASS not found in TierLevel enum")
        return False
    
    # Test 2: Check TIER_CONFIGS
    print("\n2. Testing TIER_CONFIGS:")
    if TierLevel.PRESS_PASS in TIER_CONFIGS:
        config = TIER_CONFIGS[TierLevel.PRESS_PASS]
        print(f"✓ PRESS_PASS configuration found:")
        print(f"  - Name: {config.name}")
        print(f"  - Price: ${config.price}")
        print(f"  - Daily shots: {config.daily_shots}")
        print(f"  - Min TCS: {config.min_tcs}%")
        print(f"  - Has chaingun: {config.has_chaingun}")
        print(f"  - Has autofire: {config.has_autofire}")
        print(f"  - Has stealth: {config.has_stealth}")
    else:
        print("✗ PRESS_PASS not found in TIER_CONFIGS")
        return False
    
    # Test 3: Check database model
    print("\n3. Testing Database TierLevel enum:")
    try:
        db_press_pass = DBTierLevel.PRESS_PASS
        print(f"✓ Database PRESS_PASS enum value: {db_press_pass.value}")
    except AttributeError:
        print("✗ PRESS_PASS not found in Database TierLevel enum")
        return False
    
    # Test 4: Test FireModeValidator with PRESS_PASS
    print("\n4. Testing FireModeValidator with PRESS_PASS:")
    validator = FireModeValidator()
    
    # Test allowed fire mode (SINGLE_SHOT)
    can_fire, msg = validator.can_fire(
        user_id=12345,
        tier=TierLevel.PRESS_PASS,
        mode=FireMode.SINGLE_SHOT,
        tcs_score=65  # Above 60% minimum
    )
    print(f"  - Single shot with 65% TCS: {can_fire} - {msg}")
    
    # Test TCS too low
    can_fire, msg = validator.can_fire(
        user_id=12345,
        tier=TierLevel.PRESS_PASS,
        mode=FireMode.SINGLE_SHOT,
        tcs_score=55  # Below 60% minimum
    )
    print(f"  - Single shot with 55% TCS: {can_fire} - {msg}")
    
    # Test forbidden fire mode (CHAINGUN)
    can_fire, msg = validator.can_fire(
        user_id=12345,
        tier=TierLevel.PRESS_PASS,
        mode=FireMode.CHAINGUN,
        tcs_score=80
    )
    print(f"  - Chaingun attempt: {can_fire} - {msg}")
    
    # Test 5: Load tier settings from YAML
    print("\n5. Testing tier_settings.yml configuration:")
    try:
        config_manager = TradingPairsConfig()
        tier_configs = config_manager.get_all_tier_configs()
        
        if 'PRESS_PASS' in tier_configs:
            pp_config = tier_configs['PRESS_PASS']
            print("✓ PRESS_PASS found in tier_settings.yml:")
            print(f"  - Monthly price: ${pp_config.monthly_price}")
            print(f"  - Daily shots: {pp_config.daily_shots}")
            print(f"  - Min TCS: {pp_config.min_tcs}%")
            print(f"  - Max open trades: {pp_config.max_open_trades}")
            print(f"  - Risk per shot: {pp_config.risk_per_shot}%")
        else:
            print("✗ PRESS_PASS not found in tier_settings.yml")
    except Exception as e:
        print(f"✗ Error loading tier settings: {e}")
    
    print("\n" + "=" * 50)
    print("PRESS_PASS Tier Integration Test Complete!")
    return True

if __name__ == "__main__":
    test_press_pass_tier()