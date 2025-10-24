#!/usr/bin/env python3
"""
BITTEN Tier Configuration - Usage Examples

Demonstrates common tier management operations for integration with other BITTEN systems.
"""

import sys
sys.path.insert(0, '/root/HydraX-v2')

from src.bitten_core.tier_config import (
    get_tier_defaults,
    initialize_user_caps,
    upgrade_user_tier,
    get_user_tier_info,
    validate_tier_limits,
    reset_daily_usage,
)


def example_1_initialize_new_user():
    """Example 1: Initialize a new user with tier defaults"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Initialize New User")
    print("="*70)

    user_id = "7176191872"  # Telegram ID
    tier = "COMMANDER"

    # Additional user data (optional)
    user_data = {
        'gamer_tag': 'WarRoomCommander',
        'email': 'commander@bitten.dev',
        'telegram_username': '@commander_dev'
    }

    success, message = initialize_user_caps(user_id, tier, user_data)

    print(f"\nResult: {'✅ Success' if success else '❌ Failed'}")
    print(f"Message: {message}")

    # Verify initialization
    success, info = get_user_tier_info(user_id)
    if success:
        print(f"\nUser {user_id} initialized:")
        print(f"  Tier: {info['tier']}")
        print(f"  Max Slots: {info['limits']['max_slots']}")
        print(f"  Risk per Trade: {info['limits']['risk_per_trade']*100:.1f}%")
        print(f"  AUTO Fire: {'Enabled' if info['features']['auto_fire_enabled'] else 'Disabled'}")


def example_2_validate_before_fire():
    """Example 2: Validate user permissions before executing fire command"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Validate Fire Command")
    print("="*70)

    user_id = "7176191872"

    # Check if user can fire
    allowed, reason = validate_tier_limits(user_id, 'fire')

    print(f"\nFire Command for {user_id}:")
    print(f"  Status: {'✅ Allowed' if allowed else '❌ Blocked'}")
    print(f"  Reason: {reason}")

    # Check AUTO fire availability
    allowed, reason = validate_tier_limits(user_id, 'enable_auto_fire')
    print(f"\nAUTO Fire:")
    print(f"  Status: {'✅ Available' if allowed else '❌ Unavailable'}")
    print(f"  Reason: {reason}")

    # Check BITMODE availability
    allowed, reason = validate_tier_limits(user_id, 'enable_bitmode')
    print(f"\nBITMODE:")
    print(f"  Status: {'✅ Available' if allowed else '❌ Unavailable'}")
    print(f"  Reason: {reason}")


def example_3_upgrade_user():
    """Example 3: Upgrade user tier (e.g., after payment)"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Upgrade User Tier")
    print("="*70)

    # Initialize test user as NIBBLER
    user_id = "TEST_USER_UPGRADE"
    initialize_user_caps(user_id, "NIBBLER")

    # Get initial state
    success, info = get_user_tier_info(user_id)
    print(f"\nBefore Upgrade:")
    print(f"  Tier: {info['tier']}")
    print(f"  Max Slots: {info['limits']['max_slots']}")
    print(f"  Risk: {info['limits']['risk_per_trade']*100:.1f}%")

    # Upgrade to COMMANDER
    success, message = upgrade_user_tier(user_id, "COMMANDER", preserve_custom_settings=False)

    print(f"\n{message}")

    # Get new state
    success, info = get_user_tier_info(user_id)
    print(f"\nAfter Upgrade:")
    print(f"  Tier: {info['tier']}")
    print(f"  Max Slots: {info['limits']['max_slots']}")
    print(f"  Risk: {info['limits']['risk_per_trade']*100:.1f}%")
    print(f"  Can Change Risk: {'Yes' if info['permissions']['can_change_risk'] else 'No'}")


def example_4_check_tier_limits():
    """Example 4: Check user's current tier limits and usage"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Check Tier Limits & Usage")
    print("="*70)

    user_id = "7176191872"

    success, info = get_user_tier_info(user_id)

    if success:
        print(f"\nUser: {user_id}")
        print(f"Tier: {info['tier']}")

        print(f"\n📊 LIMITS:")
        print(f"  Concurrent Positions: {info['current_usage']['slots_in_use']}/{info['limits']['max_slots']}")
        print(f"  AUTO Slots: {info['current_usage']['auto_slots_in_use']}/{info['limits']['max_auto_slots']}")
        print(f"  Daily Trades: {info['current_usage']['trades_used_today']}/{info['limits']['max_trades_per_day']}")
        print(f"  Risk per Trade: {info['limits']['risk_per_trade']*100:.1f}%")

        print(f"\n🎯 FEATURES:")
        print(f"  AUTO Fire: {'✅' if info['features']['auto_fire_enabled'] else '❌'}")
        print(f"  BITMODE: {'✅' if info['features']['bitmode_enabled'] else '❌'}")
        print(f"  Trading: {'✅' if info['features']['trading_enabled'] else '❌'}")

        print(f"\n🔓 PERMISSIONS:")
        print(f"  Change Risk: {'✅' if info['permissions']['can_change_risk'] else '❌'}")
        print(f"  Change Confidence: {'✅' if info['permissions']['can_change_confidence'] else '❌'}")
        print(f"  Change Daily Limit: {'✅' if info['permissions']['can_change_daily_limit'] else '❌'}")


def example_5_daily_reset():
    """Example 5: Reset daily usage counters (scheduled job)"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Daily Usage Reset")
    print("="*70)

    # Reset all users (typically run at midnight UTC)
    success, message = reset_daily_usage()

    print(f"\nDaily Reset:")
    print(f"  Status: {'✅ Success' if success else '❌ Failed'}")
    print(f"  {message}")

    # Reset specific user (if needed)
    user_id = "7176191872"
    success, message = reset_daily_usage(user_id)

    print(f"\nUser-Specific Reset:")
    print(f"  User: {user_id}")
    print(f"  Status: {'✅ Success' if success else '❌ Failed'}")
    print(f"  {message}")


def example_6_integration_with_fire_system():
    """Example 6: Integration with fire execution system"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Fire System Integration")
    print("="*70)

    user_id = "7176191872"

    # Before executing fire command, validate:

    # 1. Check if user can fire (hasn't hit daily limit, has slots available)
    can_fire, reason = validate_tier_limits(user_id, 'fire')

    if not can_fire:
        print(f"\n❌ Fire blocked: {reason}")
        return

    # 2. Get user's tier info for position sizing
    success, info = get_user_tier_info(user_id)

    if not success:
        print("\n❌ Could not retrieve user info")
        return

    print(f"\n✅ Fire validation passed")
    print(f"\nUser: {user_id}")
    print(f"Tier: {info['tier']}")

    # 3. Calculate position size based on tier risk limits
    account_balance = 1000.00  # Example balance from EA
    max_risk = info['limits']['risk_per_trade']
    risk_amount = account_balance * max_risk

    print(f"\nPosition Sizing:")
    print(f"  Account Balance: ${account_balance:.2f}")
    print(f"  Max Risk per Trade: {max_risk*100:.1f}%")
    print(f"  Risk Amount: ${risk_amount:.2f}")

    # 4. Check permissions for special features
    if info['features']['auto_fire_enabled']:
        print(f"\n🎯 AUTO Fire: Enabled")
        print(f"   Confidence Range: {info['limits'].get('auto_fire_min_confidence', 80):.0f}%-{info['limits'].get('auto_fire_max_confidence', 89):.0f}%")

    if info['features']['bitmode_enabled']:
        print(f"\n⚡ BITMODE: Active (hybrid position management)")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("  BITTEN TIER CONFIGURATION - USAGE EXAMPLES")
    print("="*70)

    try:
        example_1_initialize_new_user()
        example_2_validate_before_fire()
        example_3_upgrade_user()
        example_4_check_tier_limits()
        example_5_daily_reset()
        example_6_integration_with_fire_system()

        print("\n" + "="*70)
        print("  ALL EXAMPLES COMPLETED")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
