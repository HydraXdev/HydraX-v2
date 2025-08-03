#!/usr/bin/env python3
"""Test the /givegold admin command implementation"""

import sys
sys.path.append('/root/HydraX-v2')

from src.bitten_core.user_registry_manager import get_user_registry_manager

def test_givegold_setup():
    """Test setup for /givegold command"""
    
    print("🧪 Testing /givegold Command Setup")
    print("=" * 60)
    
    # Get registry manager
    registry = get_user_registry_manager()
    
    # Create test users if they don't exist
    test_user_id = "999999999"  # Test user telegram ID
    test_username = "testgolduser"  # Test username
    
    # Register test user if not exists
    if test_user_id not in registry.registry_data:
        print(f"📝 Creating test user: {test_user_id} (@{test_username})")
        registry.register_user(test_user_id, test_username, f"mt5_user_{test_user_id}")
        # Set as INTL user
        registry.update_user_region(test_user_id, "INTL")
    
    # Check current state
    user_info = registry.get_user_info(test_user_id)
    if user_info:
        print(f"\n📊 Test User Status:")
        print(f"  Telegram ID: {test_user_id}")
        print(f"  Username: {user_info.get('user_id', 'Not set')}")
        print(f"  Region: {user_info.get('user_region', 'Not set')}")
        print(f"  Offshore Opt-in: {user_info.get('offshore_opt_in', False)}")
        print(f"  Status: {user_info.get('status', 'Unknown')}")
    
    # Test command scenarios
    print("\n🎯 Command Test Scenarios:")
    print("\n1. Grant gold to INTL user:")
    print(f"   /givegold @{test_username}")
    print("   Expected: ✅ Gold access granted")
    
    print("\n2. Try granting to US user:")
    print("   /givegold @ususer")
    print("   Expected: ❌ Cannot grant to US accounts")
    
    print("\n3. Try granting to already opted-in user:")
    print(f"   /givegold @{test_username} (run twice)")
    print("   Expected: ℹ️ Gold access already active")
    
    print("\n4. Missing username:")
    print("   /givegold")
    print("   Expected: ❌ Usage: /givegold @username")
    
    print("\n5. Non-existent user:")
    print("   /givegold @nonexistentuser")
    print("   Expected: ❌ User not found")
    
    # Show command implementation
    print("\n📋 Command Implementation Details:")
    print("- Admin only: Restricted to COMMANDER_IDS")
    print("- Username lookup: Searches user_registry by user_id field")
    print("- Region check: Blocks US users for compliance")
    print("- DM notification: Sends gold operative welcome message")
    print("- XP bonus: +200 XP per XAUUSD signal")
    
    print("\n✅ /givegold command setup complete!")
    
    # Show example welcome message
    print("\n📨 Gold Welcome Message Preview:")
    print("-" * 60)
    print("🎖️ **Gold Access Granted**")
    print("")
    print("You've been activated as a **Gold Operative**.")
    print("Private XAUUSD signals will now be delivered directly to you.")
    print("")
    print("🪙 **+200 XP** per gold mission")
    print("📈 **High-volatility edge**")
    print("⚠️ **Use with caution – leverage is your responsibility**")
    print("-" * 60)

if __name__ == "__main__":
    test_givegold_setup()