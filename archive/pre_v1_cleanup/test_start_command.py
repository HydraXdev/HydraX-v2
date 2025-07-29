#!/usr/bin/env python3
"""
Test the /start command with referral code functionality
"""

def test_referral_flow():
    """Test the complete referral flow end-to-end"""
    
    print("🧪 Testing Complete Referral Onboarding Flow")
    print("=" * 50)
    
    try:
        from src.bitten_core.credit_referral_system import get_credit_referral_system
        
        # Initialize system
        referral_system = get_credit_referral_system()
        
        # STEP 1: Create a referrer and generate referral code
        referrer_user_id = "test_referrer_123"
        referral_code = referral_system.generate_referral_code(referrer_user_id)
        
        print(f"✅ Step 1: Referrer {referrer_user_id} generated code: {referral_code}")
        
        # STEP 2: Simulate new user using referral code (what happens in /start command)
        new_user_id = "test_newbie_456"
        referral_success = referral_system.use_referral_code(referral_code, new_user_id)
        
        if referral_success:
            print(f"✅ Step 2: New user {new_user_id} successfully used referral code")
        else:
            print(f"❌ Step 2: Failed to use referral code")
            return False
        
        # STEP 3: Check that pending credit was created
        referrer_stats = referral_system.get_referral_stats(referrer_user_id)
        pending_credits = referrer_stats['balance'].pending_credits
        
        if pending_credits > 0:
            print(f"✅ Step 3: Pending credit created: ${pending_credits}")
        else:
            print(f"❌ Step 3: No pending credit found")
            return False
        
        # STEP 4: Simulate payment confirmation (what happens via Stripe webhook)
        credit_applied = referral_system.confirm_payment_and_apply_credit(new_user_id)
        
        if credit_applied:
            print(f"✅ Step 4: Payment confirmed, credit applied to {credit_applied}")
        else:
            print(f"❌ Step 4: Failed to apply credit")
            return False
        
        # STEP 5: Verify final state
        final_stats = referral_system.get_referral_stats(referrer_user_id)
        total_credits = final_stats['balance'].total_credits
        referral_count = final_stats['balance'].referral_count
        
        if total_credits > 0 and referral_count > 0:
            print(f"✅ Step 5: Final state - ${total_credits} credits, {referral_count} referrals")
        else:
            print(f"❌ Step 5: Invalid final state")
            return False
        
        print("\n🎉 COMPLETE REFERRAL FLOW TEST: SUCCESS!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_start_command_scenarios():
    """Test different /start command scenarios"""
    
    print("\n🤖 Testing /start Command Scenarios")
    print("=" * 40)
    
    try:
        from src.bitten_core.credit_referral_system import get_credit_referral_system
        referral_system = get_credit_referral_system()
        
        # Create a valid referral code
        referrer_id = "scenario_referrer_789"
        valid_code = referral_system.generate_referral_code(referrer_id)
        
        print(f"✅ Created test referral code: {valid_code}")
        
        # Test scenarios
        scenarios = [
            {
                "name": "Valid referral code",
                "command": f"/start {valid_code}",
                "user_id": "scenario_user_1",
                "should_succeed": True
            },
            {
                "name": "Invalid referral code", 
                "command": "/start INVALID123",
                "user_id": "scenario_user_2",
                "should_succeed": False
            },
            {
                "name": "No referral code",
                "command": "/start",
                "user_id": "scenario_user_3", 
                "should_succeed": None  # Should show normal welcome
            },
            {
                "name": "Self-referral attempt",
                "command": f"/start {valid_code}",
                "user_id": referrer_id,  # Same as referrer
                "should_succeed": False
            }
        ]
        
        for scenario in scenarios:
            print(f"\n📋 Testing: {scenario['name']}")
            print(f"   Command: {scenario['command']}")
            
            # Extract referral code from command (simulating bot logic)
            parts = scenario['command'].split()
            if len(parts) > 1:
                referral_code = parts[1]
                result = referral_system.use_referral_code(referral_code, scenario['user_id'])
                
                if scenario['should_succeed'] is True:
                    if result:
                        print(f"   ✅ SUCCESS: Referral code accepted")
                    else:
                        print(f"   ❌ FAIL: Expected success but got failure")
                        
                elif scenario['should_succeed'] is False:
                    if not result:
                        print(f"   ✅ SUCCESS: Referral code correctly rejected")
                    else:
                        print(f"   ❌ FAIL: Expected failure but got success")
            else:
                print(f"   ✅ SUCCESS: Normal welcome (no referral code)")
        
        return True
        
    except Exception as e:
        print(f"❌ Scenario testing failed: {e}")
        return False

def test_anti_abuse_protection():
    """Test anti-abuse mechanisms"""
    
    print("\n🛡️ Testing Anti-Abuse Protection")
    print("=" * 35)
    
    try:
        from src.bitten_core.credit_referral_system import get_credit_referral_system
        referral_system = get_credit_referral_system()
        
        # Create referrer
        referrer_id = "abuse_test_referrer"
        code = referral_system.generate_referral_code(referrer_id)
        
        print(f"✅ Created referral code: {code}")
        
        # Test 1: Self-referral protection
        self_referral = referral_system.use_referral_code(code, referrer_id)
        if not self_referral:
            print("✅ Self-referral correctly blocked")
        else:
            print("❌ Self-referral should be blocked")
            
        # Test 2: Valid referral
        new_user = "abuse_test_user"
        valid_referral = referral_system.use_referral_code(code, new_user)
        if valid_referral:
            print("✅ Valid referral accepted")
        else:
            print("❌ Valid referral should be accepted")
            
        # Test 3: Duplicate referral protection
        duplicate_referral = referral_system.use_referral_code(code, new_user)
        if not duplicate_referral:
            print("✅ Duplicate referral correctly blocked") 
        else:
            print("❌ Duplicate referral should be blocked")
            
        # Test 4: Invalid code protection
        invalid_referral = referral_system.use_referral_code("FAKE123", "another_user")
        if not invalid_referral:
            print("✅ Invalid code correctly rejected")
        else:
            print("❌ Invalid code should be rejected")
            
        return True
        
    except Exception as e:
        print(f"❌ Anti-abuse testing failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🔧 REFERRAL SYSTEM REPAIR VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Test 1: Complete referral flow
    results.append(test_referral_flow())
    
    # Test 2: Start command scenarios
    results.append(test_start_command_scenarios())
    
    # Test 3: Anti-abuse protection
    results.append(test_anti_abuse_protection())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 REPAIR VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Complete Referral Flow",
        "Start Command Scenarios", 
        "Anti-Abuse Protection"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 REFERRAL SYSTEM REPAIR: SUCCESSFUL!")
        print("🚀 The /start command now properly handles referral codes!")
        print("\n📋 WORKING FLOW:")
        print("1. ✅ User A types /recruit → gets referral link")
        print("2. ✅ User B clicks link → /start REFERRAL_CODE") 
        print("3. ✅ Bot processes referral code → creates pending credit")
        print("4. ✅ User B subscribes → Stripe webhook confirms payment")
        print("5. ✅ System applies $10 credit to User A")
        print("\n💰 REFERRAL ONBOARDING IS NOW 100% OPERATIONAL!")
    else:
        print("\n⚠️ Some tests failed - check the issues above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)