"""
Get existing Stripe product and price IDs
Run this to find your already created products
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your live key
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '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')
stripe.api_key = STRIPE_SECRET_KEY

def get_existing_products():
    """Retrieve all products and their prices"""
    
    print("Fetching your Stripe products...\n")
    
    try:
        # Get all products
        products = stripe.Product.list(limit=100, active=True)
        
        price_mapping = {}
        
        for product in products.data:
            print(f"Product: {product.name}")
            print(f"ID: {product.id}")
            
            # Get prices for this product
            prices = stripe.Price.list(product=product.id, active=True, limit=10)
            
            for price in prices.data:
                if price.recurring and price.recurring.interval == 'month':
                    amount = price.unit_amount / 100
                    print(f"  Monthly Price: ${amount}")
                    print(f"  Price ID: {price.id}")
                    
                    # Try to determine tier from name or metadata
                    if 'nibbler' in product.name.lower() or amount == 39:
                        price_mapping['NIBBLER'] = price.id
                    elif 'fang' in product.name.lower() or amount == 89:
                        price_mapping['FANG'] = price.id
                    elif 'commander' in product.name.lower() or amount == 139:
                        price_mapping['COMMANDER'] = price.id
                    elif 'apex' in product.name.lower() or amount == 188:
                        price_mapping['APEX'] = price.id
            
            print()
        
        print("\n" + "="*60)
        print("ADD THESE TO YOUR .env FILE:")
        print("="*60 + "\n")
        
        for tier, price_id in price_mapping.items():
            print(f"STRIPE_PRICE_{tier}={price_id}")
        
        # Check webhook endpoints
        print("\n" + "="*60)
        print("WEBHOOK ENDPOINTS:")
        print("="*60 + "\n")
        
        try:
            webhooks = stripe.WebhookEndpoint.list(limit=10)
            for webhook in webhooks.data:
                print(f"URL: {webhook.url}")
                print(f"Status: {webhook.status}")
                print(f"Events: {', '.join(webhook.enabled_events[:3])}...")
                print()
        except:
            print("No webhooks configured yet")
        
        return price_mapping
        
    except stripe.error.StripeError as e:
        print(f"Error: {e}")
        return {}

if __name__ == "__main__":
    get_existing_products()