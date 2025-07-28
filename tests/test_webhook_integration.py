#!/usr/bin/env python3
"""
Test Stripe Webhook Integration for Credit Referral System
Verifies that webhooks are properly integrated and credit system works
"""

import requests
import json
import os
from datetime import datetime

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible"""
    
    print("🔍 Testing Stripe webhook endpoint accessibility...")
    
    # Test payload (mock Stripe webhook)
    test_payload = {
        "id": "evt_test_webhook",
        "object": "event",
        "type": "invoice.created",
        "data": {
            "object": {
                "id": "in_test_123",
                "customer": "cus_test_123",
                "amount_due": 3900,
                "metadata": {
                    "user_id": "test_user_123",
                    "telegram_id": "123456789"
                }
            }
        }
    }
    
    try:
        # Test webhook endpoint
        response = requests.post(
            "http://localhost:8888/api/stripe/webhook",
            json=test_payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=test,v1=test_signature"
            },
            timeout=10
        )
        
        print(f"📡 Webhook endpoint response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Webhook endpoint is accessible")
            return True
        else:
            print(f"❌ Webhook endpoint returned {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webapp server on localhost:8888")
        print("💡 Make sure webapp_server_optimized.py is running")
        return False
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False

def test_credit_system_database():
    """Test credit referral system database operations"""
    
    print("\n🗄️ Testing credit referral system database...")
    
    try:
        from src.bitten_core.credit_referral_system import get_credit_referral_system
        
        # Initialize system
        referral_system = get_credit_referral_system()
        print("✅ Credit referral system initialized")
        
        # Test referral code generation
        test_user_id = "test_webhook_user_123"
        referral_code = referral_system.generate_referral_code(test_user_id)
        print(f"✅ Generated referral code: {referral_code}")
        
        # Test stats retrieval
        stats = referral_system.get_referral_stats(test_user_id)
        print(f"✅ Retrieved user stats: {stats['balance'].total_credits} credits")
        
        # Test admin functions
        admin_stats = referral_system.get_admin_stats()
        print(f"✅ Admin stats: {admin_stats['total_credits_issued']} total credits issued")
        
        return True
        
    except Exception as e:
        print(f"❌ Credit system test failed: {e}")
        return False

def test_stripe_credit_manager():
    """Test Stripe credit manager integration"""
    
    print("\n💳 Testing Stripe credit manager...")
    
    try:
        from src.bitten_core.stripe_credit_manager import get_stripe_credit_manager
        
        # Initialize manager
        credit_manager = get_stripe_credit_manager()
        print("✅ Stripe credit manager initialized")
        
        # Test mock invoice processing
        mock_invoice_data = {
            "id": "in_test_123",
            "customer": "cus_test_123", 
            "amount_due": 3900,
            "metadata": {
                "user_id": "test_user_123",
                "telegram_id": "123456789"
            }
        }
        
        # Test credit application
        result = credit_manager.handle_subscription_invoice_created(mock_invoice_data)
        print(f"✅ Invoice processing result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Stripe credit manager test failed: {e}")
        return False

def test_admin_api():
    """Test admin API endpoints"""
    
    print("\n🔧 Testing admin API endpoints...")
    
    try:
        # Test admin stats endpoint
        response = requests.get(
            "http://localhost:8888/api/admin/credits/stats",
            headers={"X-Admin-Token": "BITTEN_ADMIN_2025"},
            timeout=10
        )
        
        print(f"📊 Admin stats response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin stats: {data.get('total_credits_issued', 0)} credits issued")
            return True
        else:
            print(f"❌ Admin API returned {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webapp server for admin API test")
        return False
    except Exception as e:
        print(f"❌ Admin API test failed: {e}")
        return False

def main():
    """Run all webhook integration tests"""
    
    print("🚀 Starting Stripe Webhook Integration Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Webhook endpoint accessibility
    results.append(test_webhook_endpoint())
    
    # Test 2: Credit system database
    results.append(test_credit_system_database())
    
    # Test 3: Stripe credit manager
    results.append(test_stripe_credit_manager())
    
    # Test 4: Admin API
    results.append(test_admin_api())
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Webhook Endpoint",
        "Credit Database", 
        "Stripe Manager",
        "Admin API"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All webhook integration tests PASSED!")
        print("💰 Credit referral system is ready for production!")
    else:
        print("⚠️  Some tests failed - check the errors above")
        print("🔧 Fix the issues before deploying to production")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)