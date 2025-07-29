#!/usr/bin/env python3
"""
Test Commander Throne Credit Referral Integration
"""

def test_integration():
    """Test that the integration functions work properly"""
    
    print("🏛️ Testing Commander Throne Credit Referral Integration")
    print("=" * 60)
    
    # Test the helper function directly
    try:
        import sys
        sys.path.append('/root/HydraX-v2')
        
        # Import the helper function from commander_throne
        from commander_throne import get_credit_referral_stats
        
        print("✅ Successfully imported helper function")
        
        # Test the helper function
        stats = get_credit_referral_stats()
        print(f"✅ Helper function works: {stats}")
        
        # Test individual components
        from src.bitten_core.credit_referral_system import get_credit_referral_system
        referral_system = get_credit_referral_system()
        
        # Test new manual credit function
        test_result = referral_system.apply_manual_credit("test_throne_user", 25.0, "Throne integration test")
        print(f"✅ Manual credit function: {test_result}")
        
        # Test admin stats
        admin_stats = referral_system.get_admin_stats()
        print(f"✅ Admin stats: {admin_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_throne_endpoints():
    """Test that the throne has the new endpoints"""
    
    print("\n📡 Testing Throne Endpoint Registration")
    print("=" * 40)
    
    try:
        import sys
        sys.path.append('/root/HydraX-v2')
        
        # Import the Flask app from commander_throne
        from commander_throne import app
        
        # Get all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        
        # Check for credit referral routes
        credit_routes = [r for r in routes if 'credit' in r.lower()]
        
        print(f"✅ Total routes registered: {len(routes)}")
        print(f"✅ Credit-related routes: {len(credit_routes)}")
        
        for route in credit_routes:
            print(f"   📍 {route}")
        
        # Verify expected routes exist
        expected_routes = [
            '/throne/api/credit_referrals',
            '/throne/api/credit_referrals/top_referrers',
            '/throne/api/credit_referrals/apply',
            '/throne/api/credit_referrals/user/<user_id>'
        ]
        
        missing_routes = []
        for expected in expected_routes:
            # Check if route exists (handle dynamic routes)
            found = False
            for route in routes:
                if expected.replace('<user_id>', '<string:user_id>') == route:
                    found = True
                    break
            if not found:
                missing_routes.append(expected)
        
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        else:
            print("✅ All expected credit referral routes registered!")
            return True
            
    except Exception as e:
        print(f"❌ Route test failed: {e}")
        return False

def main():
    """Run all tests"""
    
    results = []
    
    # Test 1: Integration functions
    results.append(test_integration())
    
    # Test 2: Throne endpoints
    results.append(test_throne_endpoints())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 THRONE INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    test_names = ["Integration Functions", "Throne Endpoints"]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 COMMANDER THRONE INTEGRATION SUCCESSFUL!")
        print("👑 Credit referral management is now available in the throne!")
        print("\n📋 NEW THRONE FEATURES:")
        print("• 💰 Credit referral stats in subscription analytics")
        print("• 🏆 Top referrers leaderboard")
        print("• 🔧 Manual credit application (COMMANDER access)")
        print("• 👤 Individual user credit details")
        print("• 📊 Real-time credit system metrics")
    else:
        print("⚠️ Some integration tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)