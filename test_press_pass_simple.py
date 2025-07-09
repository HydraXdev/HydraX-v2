#!/usr/bin/env python3
"""
Simple test to verify PRESS_PASS tier is properly defined
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Test fire_modes.py
print("Testing PRESS_PASS in fire_modes.py...")
print("=" * 50)

try:
    from src.bitten_core.fire_modes import TierLevel, TIER_CONFIGS
    
    # Check enum
    print("\n1. TierLevel enum values:")
    for tier in TierLevel:
        print(f"   - {tier.name}: {tier.value}")
    
    # Check TIER_CONFIGS
    print("\n2. TIER_CONFIGS entries:")
    for tier, config in TIER_CONFIGS.items():
        print(f"\n   {tier.name} ({config.name}):")
        print(f"     - Price: ${config.price}")
        print(f"     - Daily shots: {config.daily_shots}")
        print(f"     - Min TCS: {config.min_tcs}%")
        print(f"     - Risk per shot: {config.risk_per_shot}%")
        
except Exception as e:
    print(f"Error loading fire_modes: {e}")

# Test database models
print("\n\nTesting PRESS_PASS in database models...")
print("=" * 50)

try:
    from src.database.models import TierLevel as DBTierLevel
    
    print("\nDatabase TierLevel enum values:")
    for tier in DBTierLevel:
        print(f"   - {tier.name}: {tier.value}")
        
except Exception as e:
    print(f"Error loading database models: {e}")

# Test YAML configuration
print("\n\nTesting PRESS_PASS in tier_settings.yml...")
print("=" * 50)

try:
    import yaml
    
    config_path = os.path.join(project_root, "config", "tier_settings.yml")
    with open(config_path, 'r') as f:
        tier_config = yaml.safe_load(f)
    
    if 'tiers' in tier_config and 'PRESS_PASS' in tier_config['tiers']:
        pp = tier_config['tiers']['PRESS_PASS']
        print("\nPRESS_PASS configuration in tier_settings.yml:")
        print(f"  - Monthly price: ${pp['pricing']['monthly_price']}")
        print(f"  - Daily shots: {pp['fire_settings']['daily_shots']}")
        print(f"  - Min TCS: {pp['fire_settings']['min_tcs']}%")
        print(f"  - Risk per shot: {pp['fire_settings']['risk_per_shot']}%")
        print(f"  - Max open trades: {pp['risk_control']['max_open_trades']}")
        print(f"  - XP reset nightly: {pp['features'].get('xp_reset_nightly', False)}")
    else:
        print("PRESS_PASS not found in tier_settings.yml")
        
except Exception as e:
    print(f"Error loading tier_settings.yml: {e}")

print("\n" + "=" * 50)
print("PRESS_PASS Integration Test Complete!")