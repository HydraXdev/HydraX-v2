"""
Test Stripe Connection with current keys
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stripe_connection():
    """Test different Stripe keys to see what works"""
    
    print("Testing Stripe Connection")
    print("="*60)
    
    # Test 1: Try the restricted key
    restricted_key = os.getenv('STRIPE_RESTRICTED_KEY')
    if restricted_key:
        print(f"\n1. Testing RESTRICTED KEY (starts with: {restricted_key[:10]}...)")
        stripe.api_key = restricted_key
        try:
            # Restricted keys can only read certain resources
            account = stripe.Account.retrieve()
            print(f"   ✅ Success! Connected to: {account.settings.dashboard.display_name}")
            print(f"   Mode: {'LIVE' if 'live' in restricted_key else 'TEST'}")
        except stripe.error.PermissionError as e:
            print(f"   ⚠️  Permission error (expected for restricted keys): {e}")
            # Try a different endpoint that might work with restricted key
            try:
                products = stripe.Product.list(limit=1)
                print(f"   ✅ Can read products! Found {len(products.data)} products")
            except Exception as e2:
                print(f"   ❌ Cannot read products: {e2}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 2: Try the secret key if available
    secret_key = os.getenv('STRIPE_SECRET_KEY')
    if secret_key and secret_key != 'sk_live_YOUR_SECRET_KEY_HERE':
        print(f"\n2. Testing SECRET KEY (starts with: {secret_key[:10]}...)")
        stripe.api_key = secret_key
        try:
            account = stripe.Account.retrieve()
            print(f"   ✅ Success! Connected to: {account.settings.dashboard.display_name}")
            print(f"   Mode: {'LIVE' if 'live' in secret_key else 'TEST'}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 3: Check what we can do with the restricted key
    if restricted_key:
        print(f"\n3. Testing restricted key capabilities...")
        stripe.api_key = restricted_key
        
        # Test various endpoints
        endpoints = [
            ('Products', lambda: stripe.Product.list(limit=1)),
            ('Prices', lambda: stripe.Price.list(limit=1)),
            ('Customers', lambda: stripe.Customer.list(limit=1)),
            ('Subscriptions', lambda: stripe.Subscription.list(limit=1)),
        ]
        
        for name, func in endpoints:
            try:
                result = func()
                print(f"   ✅ Can access {name}: {len(result.data)} found")
            except stripe.error.PermissionError:
                print(f"   ❌ No permission for {name}")
            except Exception as e:
                print(f"   ❌ Error accessing {name}: {type(e).__name__}")
    
    # Show current configuration
    print(f"\n4. Current Environment Configuration:")
    print(f"   STRIPE_PUBLISHABLE_KEY: {os.getenv('STRIPE_PUBLISHABLE_KEY', 'Not set')[:20]}...")
    print(f"   STRIPE_SECRET_KEY: {os.getenv('STRIPE_SECRET_KEY', 'Not set')[:20]}...")
    print(f"   STRIPE_RESTRICTED_KEY: {os.getenv('STRIPE_RESTRICTED_KEY', 'Not set')[:20]}...")
    print(f"   STRIPE_WEBHOOK_SECRET: {os.getenv('STRIPE_WEBHOOK_SECRET', 'Not set')[:20]}...")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    print("\nBased on the tests above:")
    print("1. Restricted keys (rk_*) have limited permissions")
    print("2. To create products/prices, you need a SECRET key (sk_*)")
    print("3. For production, use sk_live_* keys")
    print("4. For testing, use sk_test_* keys")
    print("\nNext steps:")
    print("- Get your secret key from https://dashboard.stripe.com/apikeys")
    print("- Update STRIPE_SECRET_KEY in .env file")
    print("- Run setup_stripe_products.py to create products")

if __name__ == "__main__":
    test_stripe_connection()