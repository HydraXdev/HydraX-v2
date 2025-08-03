#!/usr/bin/env python3
"""Test script for offshore user setup and DM signal functionality"""

import sys
sys.path.append('/root/HydraX-v2')

from src.bitten_core.user_registry_manager import get_user_registry_manager

def test_offshore_setup():
    """Test the offshore user setup"""
    
    print("🧪 Testing Offshore User Setup")
    print("=" * 60)
    
    # Get registry manager
    registry = get_user_registry_manager()
    
    # Test user IDs
    test_user_us = "111111111"  # US user
    test_user_intl = "222222222"  # INTL user
    test_user_chris = "7176191872"  # Chris (existing user)
    
    # Register test users if they don't exist
    if test_user_us not in registry.registry_data:
        print(f"📝 Registering US test user: {test_user_us}")
        registry.register_user(test_user_us, "test_us", f"mt5_user_{test_user_us}")
    
    if test_user_intl not in registry.registry_data:
        print(f"📝 Registering INTL test user: {test_user_intl}")
        registry.register_user(test_user_intl, "test_intl", f"mt5_user_{test_user_intl}")
    
    # Update regions
    print("\n🌍 Setting user regions...")
    registry.update_user_region(test_user_us, "US")
    registry.update_user_region(test_user_intl, "INTL")
    
    # Check if Chris exists and update
    if test_user_chris in registry.registry_data:
        print(f"📝 Updating Chris to INTL region with offshore opt-in")
        registry.update_user_region(test_user_chris, "INTL")
        registry.update_offshore_opt_in(test_user_chris, True)
    
    # Update offshore opt-in
    print("\n🔐 Setting offshore opt-in...")
    registry.update_offshore_opt_in(test_user_intl, True)
    registry.update_offshore_opt_in(test_user_us, False)  # US users can't opt in
    
    # Test getting user info
    print("\n📊 User Info:")
    for user_id in [test_user_us, test_user_intl, test_user_chris]:
        info = registry.get_user_info(user_id)
        if info:
            print(f"\nUser {user_id}:")
            print(f"  Region: {info.get('user_region', 'Not set')}")
            print(f"  Offshore Opt-in: {info.get('offshore_opt_in', False)}")
            print(f"  Status: {info.get('status', 'Unknown')}")
    
    # Test eligibility check manually
    print("\n🎯 Testing Offshore Eligibility:")
    
    for user_id in [test_user_us, test_user_intl, test_user_chris]:
        info = registry.get_user_info(user_id)
        if info:
            user_region = info.get("user_region", "US")
            offshore_opt_in = info.get("offshore_opt_in", False)
            eligible = user_region == "INTL" and offshore_opt_in
            print(f"  User {user_id}: {'✅ ELIGIBLE' if eligible else '❌ NOT ELIGIBLE'}")
    
    print("\n✅ Offshore setup test complete!")
    
    # Show sample DM signal
    print("\n📨 Sample DM Signal Test:")
    sample_signal = """
🎯 **ELITE SIGNAL - XAUUSD** 🎯

📊 **Pattern**: Liquidity Sweep Reversal
💰 **Symbol**: XAUUSD (GOLD)
📈 **Direction**: BUY
💵 **Entry**: 2411.50
🛑 **Stop Loss**: 2405.00 (65 pips)
🎯 **Take Profit**: 2424.50 (130 pips)
📐 **Risk/Reward**: 1:2

⚡ **Signal Type**: PRECISION_STRIKE
🛡️ **CITADEL Score**: 8.5/10

*Trade at your own risk. Offshore markets only.*
    """
    
    print("Sample signal that would be sent to offshore users:")
    print("-" * 60)
    print(sample_signal)
    print("-" * 60)

if __name__ == "__main__":
    test_offshore_setup()