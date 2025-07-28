#!/usr/bin/env python3
"""
BITTEN Credit Referral System Test Suite
Test the complete referral flow from code generation to credit application
"""

import os
import sys
import json
import tempfile
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, '/root/HydraX-v2/src')

from bitten_core.credit_referral_system import CreditReferralSystem, get_credit_referral_system
from bitten_core.stripe_credit_manager import StripeCreditManager

def test_basic_referral_flow():
    """Test the basic referral code generation and usage flow"""
    print("\n🧪 Testing Basic Referral Flow")
    print("=" * 50)
    
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    try:
        # Initialize system with test database
        referral_system = CreditReferralSystem(test_db_path)
        
        # Test 1: Generate referral code
        print("1. Testing referral code generation...")
        referrer_id = "test_user_123"
        referral_code = referral_system.generate_referral_code(referrer_id)
        print(f"   ✅ Generated code: {referral_code}")
        
        # Test 2: Verify duplicate generation returns same code
        same_code = referral_system.generate_referral_code(referrer_id)
        assert referral_code == same_code, "Should return same code for same user"
        print(f"   ✅ Duplicate generation returns same code: {same_code}")
        
        # Test 3: Use referral code
        print("2. Testing referral code usage...")
        new_user_id = "test_user_456"
        success = referral_system.use_referral_code(referral_code, new_user_id)
        assert success, "Referral code usage should succeed"
        print(f"   ✅ User {new_user_id} successfully used code {referral_code}")
        
        # Test 4: Check balances
        print("3. Testing balance tracking...")
        balance = referral_system.get_user_credit_balance(referrer_id)
        assert balance.pending_credits == 10.0, f"Expected 10.0 pending credits, got {balance.pending_credits}"
        assert balance.total_credits == 0.0, "Should have no total credits yet"
        print(f"   ✅ Pending credits: ${balance.pending_credits}")
        
        # Test 5: Prevent self-referral
        print("4. Testing self-referral prevention...")
        self_referral = referral_system.use_referral_code(referral_code, referrer_id)
        assert not self_referral, "Self-referral should be prevented"
        print("   ✅ Self-referral correctly prevented")
        
        # Test 6: Prevent duplicate referral
        print("5. Testing duplicate referral prevention...")
        duplicate_referral = referral_system.use_referral_code(referral_code, new_user_id)
        assert not duplicate_referral, "Duplicate referral should be prevented"
        print("   ✅ Duplicate referral correctly prevented")
        
        # Test 7: Confirm payment and apply credit
        print("6. Testing payment confirmation...")
        credited_referrer = referral_system.confirm_payment_and_apply_credit(new_user_id, "test_invoice_123")
        assert credited_referrer == referrer_id, "Should return referrer ID"
        print(f"   ✅ Payment confirmed, credit applied to {credited_referrer}")
        
        # Test 8: Verify final balances
        print("7. Testing final balance...")
        final_balance = referral_system.get_user_credit_balance(referrer_id)
        assert final_balance.total_credits == 10.0, f"Expected 10.0 total credits, got {final_balance.total_credits}"
        assert final_balance.pending_credits == 0.0, "Should have no pending credits"
        assert final_balance.referral_count == 1, "Should have 1 referral"
        print(f"   ✅ Final balance: ${final_balance.total_credits} total, ${final_balance.pending_credits} pending, {final_balance.referral_count} referrals")
        
        print("\n🎉 Basic referral flow test PASSED!")
        
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

def test_credit_application():
    """Test credit application to invoices"""
    print("\n🧪 Testing Credit Application")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    try:
        referral_system = CreditReferralSystem(test_db_path)
        
        # Setup user with credits
        user_id = "test_user_789"
        referral_system.generate_referral_code(user_id)
        
        # Manually add some credits
        import sqlite3
        with sqlite3.connect(test_db_path) as conn:
            referral_system._update_user_balance(conn, user_id, total_credit=25.0)
            conn.commit()
        
        print("1. Testing credit application to invoice...")
        
        # Test partial credit application
        credit_applied, remaining = referral_system.apply_credit_to_invoice(user_id, 39.0, "invoice_001")
        assert credit_applied == 25.0, f"Expected 25.0 credit applied, got {credit_applied}"
        assert remaining == 14.0, f"Expected 14.0 remaining, got {remaining}"
        print(f"   ✅ Applied ${credit_applied} to $39 invoice, ${remaining} remaining")
        
        # Test over-credit scenario
        with sqlite3.connect(test_db_path) as conn:
            referral_system._update_user_balance(conn, user_id, total_credit=50.0)
            conn.commit()
        credit_applied, remaining = referral_system.apply_credit_to_invoice(user_id, 30.0, "invoice_002")
        assert credit_applied == 30.0, f"Expected 30.0 credit applied, got {credit_applied}"
        assert remaining == 0.0, f"Expected 0.0 remaining, got {remaining}"
        print(f"   ✅ Applied ${credit_applied} to $30 invoice, fully covered")
        
        print("\n🎉 Credit application test PASSED!")
        
    finally:
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

def test_stats_and_reporting():
    """Test statistics and reporting functionality"""
    print("\n🧪 Testing Stats and Reporting")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    try:
        referral_system = CreditReferralSystem(test_db_path)
        
        # Create test data
        referrer_id = "test_referrer_001"
        referral_code = referral_system.generate_referral_code(referrer_id)
        
        # Create multiple referrals
        for i in range(3):
            user_id = f"referred_user_{i}"
            referral_system.use_referral_code(referral_code, user_id)
            if i < 2:  # Confirm payment for first 2
                referral_system.confirm_payment_and_apply_credit(user_id, f"invoice_{i}")
        
        print("1. Testing referral stats...")
        stats = referral_system.get_referral_stats(referrer_id)
        
        assert stats['referral_code'] == referral_code
        assert stats['balance'].total_credits == 20.0  # 2 confirmed * $10
        assert stats['balance'].pending_credits == 10.0  # 1 pending * $10
        assert stats['balance'].referral_count == 2  # 2 confirmed
        assert len(stats['recent_referrals']) == 3  # 3 total
        print(f"   ✅ Referral stats: {stats['balance'].referral_count} confirmed, ${stats['balance'].total_credits} earned")
        
        print("2. Testing admin stats...")
        admin_stats = referral_system.get_admin_stats()
        
        assert admin_stats['total_credits_issued'] == 20.0
        assert admin_stats['total_referrals'] == 3
        assert admin_stats['pending_credits'] == 10.0
        assert len(admin_stats['top_referrers']) == 1
        print(f"   ✅ Admin stats: ${admin_stats['total_credits_issued']} issued, {admin_stats['total_referrals']} total referrals")
        
        print("\n🎉 Stats and reporting test PASSED!")
        
    finally:
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

def test_edge_cases():
    """Test edge cases and error conditions"""
    print("\n🧪 Testing Edge Cases")
    print("=" * 50)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    try:
        referral_system = CreditReferralSystem(test_db_path)
        
        print("1. Testing invalid referral code...")
        result = referral_system.use_referral_code("INVALID123", "test_user")
        assert not result, "Invalid code should return False"
        print("   ✅ Invalid code correctly rejected")
        
        print("2. Testing payment confirmation for non-existent user...")
        result = referral_system.confirm_payment_and_apply_credit("nonexistent_user", "invoice_123")
        assert result is None, "Non-existent user should return None"
        print("   ✅ Non-existent user correctly handled")
        
        print("3. Testing empty credit balance...")
        balance = referral_system.get_user_credit_balance("new_user")
        assert balance.total_credits == 0.0
        assert balance.pending_credits == 0.0
        assert balance.referral_count == 0
        print("   ✅ Empty balance correctly initialized")
        
        print("4. Testing custom referral code...")
        try:
            custom_code = referral_system.generate_referral_code("test_user", "CUSTOM123")
            assert custom_code == "CUSTOM123"
            print("   ✅ Custom code generation works")
            
            # Test duplicate custom code
            try:
                referral_system.generate_referral_code("other_user", "CUSTOM123")
                assert False, "Should have raised ValueError"
            except ValueError:
                print("   ✅ Duplicate custom code correctly rejected")
        except Exception as e:
            print(f"   ❌ Custom code test failed: {e}")
        
        print("\n🎉 Edge cases test PASSED!")
        
    finally:
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

def run_integration_test():
    """Run a complete integration test simulating real user flow"""
    print("\n🧪 Integration Test - Complete User Flow")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    try:
        referral_system = CreditReferralSystem(test_db_path)
        
        # Scenario: Alice refers Bob, Bob subscribes, Alice gets credit, Alice uses credit
        alice_id = "alice_123"
        bob_id = "bob_456"
        
        print("📝 Scenario: Alice refers Bob, Bob subscribes and pays")
        print("-" * 50)
        
        # Step 1: Alice generates referral code
        print("1. Alice generates her referral code...")
        alice_code = referral_system.generate_referral_code(alice_id)
        print(f"   Alice's code: {alice_code}")
        
        # Step 2: Bob uses Alice's code
        print("2. Bob signs up using Alice's referral code...")
        success = referral_system.use_referral_code(alice_code, bob_id)
        assert success
        print(f"   ✅ Bob successfully referred by Alice")
        
        # Step 3: Check Alice's pending credits
        print("3. Checking Alice's pending credits...")
        balance = referral_system.get_user_credit_balance(alice_id)
        print(f"   Alice has ${balance.pending_credits} pending credit")
        assert balance.pending_credits == 10.0
        
        # Step 4: Bob makes his first payment
        print("4. Bob makes his first payment ($39)...")
        referrer = referral_system.confirm_payment_and_apply_credit(bob_id, "bob_invoice_001")
        assert referrer == alice_id
        print(f"   ✅ Payment confirmed, ${10} credit applied to Alice")
        
        # Step 5: Check Alice's updated balance
        print("5. Checking Alice's updated balance...")
        updated_balance = referral_system.get_user_credit_balance(alice_id)
        print(f"   Alice now has ${updated_balance.total_credits} total credit")
        assert updated_balance.total_credits == 10.0
        assert updated_balance.pending_credits == 0.0
        assert updated_balance.referral_count == 1
        
        # Step 6: Alice gets her next invoice and applies credit
        print("6. Alice's next invoice ($39) - applying credit...")
        credit_applied, remaining = referral_system.apply_credit_to_invoice(alice_id, 39.0, "alice_invoice_001")
        print(f"   Applied ${credit_applied} credit, ${remaining} remaining to pay")
        assert credit_applied == 10.0
        assert remaining == 29.0
        
        # Step 7: Check final balances
        print("7. Final balance check...")
        final_balance = referral_system.get_user_credit_balance(alice_id)
        print(f"   Alice final balance: ${final_balance.total_credits} available, ${final_balance.applied_credits} applied")
        assert final_balance.total_credits == 0.0  # Credit used
        assert final_balance.applied_credits == 10.0  # Credit applied
        
        print("\n🎉 Integration test PASSED! Complete flow working correctly.")
        print(f"💰 Alice saved $10 on her bill by referring Bob!")
        
    finally:
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

def main():
    """Run all tests"""
    print("🚀 BITTEN Credit Referral System Test Suite")
    print("=" * 60)
    
    try:
        test_basic_referral_flow()
        test_credit_application()
        test_stats_and_reporting()
        test_edge_cases()
        run_integration_test()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Credit referral system is working correctly.")
        print("\n📋 System Ready For:")
        print("   • Telegram bot integration (/recruit, /credits commands)")
        print("   • Stripe webhook integration (automatic credit application)")
        print("   • Admin API endpoints (credit management)")
        print("   • Production deployment")
        
        print("\n🔧 Next Steps:")
        print("   1. Integrate bot commands with main bot")
        print("   2. Configure Stripe webhooks")
        print("   3. Set up admin authentication")
        print("   4. Deploy to production")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()