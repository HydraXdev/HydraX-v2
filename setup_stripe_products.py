"""
Setup Stripe Products for BITTEN
Run this once to create all products and prices
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your live key
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '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')
stripe.api_key = STRIPE_SECRET_KEY

def create_products():
    """Create all BITTEN products and prices"""
    
    products_config = [
        {
            'tier': 'NIBBLER',
            'name': 'BITTEN Nibbler',
            'description': 'Entry tier - 6 trades/day, manual trading only',
            'price_cents': 3900,  # $39.00
            'features': [
                '6 trades per day',
                '75% TCS minimum',
                'Manual trading only',
                'Basic risk management',
                'Perfect for beginners'
            ]
        },
        {
            'tier': 'FANG',
            'name': 'BITTEN Fang',
            'description': 'Advanced tier - 10 trades/day, sniper mode unlocked',
            'price_cents': 8900,  # $89.00
            'features': [
                '10 trades per day',
                '85% TCS for sniper',
                'Chaingun mode unlocked',
                'Advanced filters',
                'Sniper mode access'
            ]
        },
        {
            'tier': 'COMMANDER',
            'name': 'BITTEN Commander',
            'description': 'Pro tier - 20 trades/day, full automation',
            'price_cents': 18900,  # $189.00
            'features': [
                '20 trades per day',
                '90% TCS auto / 75% semi',
                'Full automation',
                'Stealth mode',
                'All strategies unlocked'
            ]
        },
        {
            'tier': '',
            'name': 'BITTEN Apex',
            'description': 'Elite tier - Unlimited trades, priority support',
            'price_cents': ,  # .00
            'features': [
                'Unlimited trades',
                '91% TCS minimum',
                'Midnight Hammer',
                'Priority support',
                'Elite network access'
            ]
        }
    ]
    
    created_prices = {}
    
    print("Creating Stripe products and prices...\n")
    
    for config in products_config:
        try:
            # Create product
            product = stripe.Product.create(
                name=config['name'],
                description=config['description'],
                metadata={
                    'tier': config['tier'],
                    'features': ', '.join(config['features'])
                }
            )
            
            print(f"✅ Created product: {config['name']} (ID: {product.id})")
            
            # Create monthly price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=config['price_cents'],
                currency='usd',
                recurring={'interval': 'month'},
                metadata={
                    'tier': config['tier']
                }
            )
            
            created_prices[config['tier']] = price.id
            print(f"✅ Created price: ${config['price_cents']/100}/month (ID: {price.id})")
            print(f"   Features: {', '.join(config['features'][:2])}...\n")
            
        except stripe.error.StripeError as e:
            print(f"❌ Error creating {config['tier']}: {e}\n")
    
    # Print environment variables to add
    print("\n" + "="*60)
    print("ADD THESE TO YOUR .env FILE:")
    print("="*60 + "\n")
    
    for tier, price_id in created_prices.items():
        print(f"STRIPE_PRICE_{tier}={price_id}")
    
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    
    return created_prices

def setup_webhook_endpoint():
    """Instructions for webhook setup"""
    
    print("\n" + "="*60)
    print("WEBHOOK SETUP INSTRUCTIONS:")
    print("="*60 + "\n")
    
    print("1. Go to https://dashboard.stripe.com/webhooks")
    print("2. Click 'Add endpoint'")
    print("3. Enter your endpoint URL:")
    print("   https://your-domain.com/stripe/webhook")
    print("\n4. Select these events:")
    print("   - customer.subscription.created")
    print("   - customer.subscription.updated")
    print("   - customer.subscription.deleted")
    print("   - customer.subscription.trial_will_end")
    print("   - invoice.payment_succeeded")
    print("   - invoice.payment_failed")
    print("\n5. Copy the signing secret and add to .env:")
    print("   STRIPE_WEBHOOK_SECRET=whsec_...")

def check_existing_products():
    """Check if products already exist"""
    
    print("Checking existing products...\n")
    
    try:
        products = stripe.Product.list(limit=100)
        
        existing_tiers = set()
        for product in products.data:
            tier = product.metadata.get('tier')
            if tier:
                existing_tiers.add(tier)
                print(f"Found existing product: {product.name} (Tier: {tier})")
        
        if existing_tiers:
            print(f"\n⚠️  Found existing products for tiers: {', '.join(existing_tiers)}")
            response = input("\nDo you want to create new products anyway? (y/N): ")
            return response.lower() == 'y'
        
        return True
        
    except stripe.error.StripeError as e:
        print(f"Error checking products: {e}")
        return False

if __name__ == "__main__":
    print("BITTEN Stripe Setup Script")
    print("="*60 + "\n")
    
    # Verify API key
    try:
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe account: {account.settings.dashboard.display_name}")
        print(f"   Mode: {'LIVE' if 'live' in STRIPE_SECRET_KEY else 'TEST'}")
        print(f"   Country: {account.country}")
        print(f"   Currency: {account.default_currency.upper()}\n")
    except stripe.error.AuthenticationError:
        print("❌ Invalid Stripe API key!")
        print("   Make sure STRIPE_SECRET_KEY is set correctly in .env")
        exit(1)
    
    # Check existing products
    if check_existing_products():
        # Create products
        create_products()
        
        # Show webhook instructions
        setup_webhook_endpoint()
    else:
        print("\nSetup cancelled.")