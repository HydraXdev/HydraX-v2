#!/usr/bin/env python3
"""
Test Press Pass Integration
Tests the press pass claiming and tracking functionality
"""

import asyncio
from datetime import datetime
from src.bitten_core.press_pass_manager import PressPassManager


async def test_press_pass():
    """Test press pass functionality"""
    print("🎖️  TESTING PRESS PASS SYSTEM")
    print("=" * 50)
    
    # Initialize manager
    manager = PressPassManager()
    
    # Test 1: Check daily remaining
    print("\n1. Checking daily press passes remaining...")
    remaining = manager.get_daily_remaining()
    print(f"   Press passes available today: {remaining}/{manager.daily_limit}")
    
    # Test 2: Claim a press pass
    print("\n2. Testing press pass claim...")
    test_user_id = 123456789
    test_username = "test_trader"
    
    result = await manager.claim_press_pass(test_user_id, test_username)
    
    if result["success"]:
        print(f"   ✅ Press pass claimed successfully!")
        print(f"   - Tier granted: {result['tier']}")
        print(f"   - Duration: {result['days']} days")
        print(f"   - Expires: {result['expiry_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   - Spots remaining today: {result['spots_remaining']}")
    else:
        print(f"   ❌ Failed to claim: {result['error']}")
    
    # Test 3: Check user status
    print("\n3. Checking user press pass status...")
    status = manager.get_user_press_pass_status(test_user_id)
    
    if status:
        print(f"   Press Pass Status:")
        print(f"   - Active: {'Yes' if status['active'] else 'No'}")
        print(f"   - Days remaining: {status.get('days_remaining', 'N/A')}")
        print(f"   - Urgency level: {status.get('urgency_level', 'N/A')}")
        print(f"   - Tier: {status.get('tier', 'N/A')}")
    else:
        print("   No active press pass found")
    
    # Test 4: Try to claim again (should fail)
    print("\n4. Testing duplicate claim prevention...")
    result2 = await manager.claim_press_pass(test_user_id, test_username)
    
    if not result2["success"]:
        print(f"   ✅ Correctly prevented duplicate claim")
        print(f"   - Reason: {result2['error']}")
        if 'days_remaining' in result2:
            print(f"   - Days remaining on current pass: {result2['days_remaining']}")
    else:
        print("   ❌ ERROR: Duplicate claim was allowed!")
    
    # Test 5: Check expiring passes
    print("\n5. Checking for expiring passes...")
    expiring = await manager.check_expiring_passes()
    print(f"   Found {len(expiring)} expiring passes")
    
    # Test 6: Test conversion
    print("\n6. Testing conversion to paid subscription...")
    conversion = await manager.convert_to_paid(test_user_id, "APEX", discount_applied=True)
    
    if conversion["success"]:
        print(f"   ✅ Successfully converted to {conversion['tier']}")
        print(f"   - Lifetime discount applied: Yes")
    else:
        print(f"   ❌ Conversion failed: {conversion.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    print("✅ Press Pass system test completed!")


if __name__ == "__main__":
    asyncio.run(test_press_pass())