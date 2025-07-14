"""Payment Configuration for BITTEN - Stripe Integration"""

import os
from typing import Dict, Optional

class PaymentConfig:
    """Centralized payment configuration for Stripe integration"""
    
    # Load from environment variables
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Subscription Price IDs
    PRICE_IDS = {
        'NIBBLER': os.getenv('STRIPE_PRICE_NIBBLER', 'price_nibbler_monthly'),
        'FANG': os.getenv('STRIPE_PRICE_FANG', 'price_fang_monthly'),
        'COMMANDER': os.getenv('STRIPE_PRICE_COMMANDER', 'price_commander_monthly'),
        'APEX': os.getenv('STRIPE_PRICE_APEX', 'price_apex_monthly')
    }
    
    # Subscription Pricing (in USD)
    TIER_PRICING = {
        'NIBBLER': 39,
        'FANG': 89,
        'COMMANDER': 139,
        'APEX': 188  # Includes all COMMANDER features + exclusive APEX features
    }
    
    # Trial Configuration
    TRIAL_ENABLED = os.getenv('ENABLE_TRIAL_SYSTEM', 'true').lower() == 'true'
    TRIAL_DURATION_DAYS = int(os.getenv('TRIAL_DURATION_DAYS', '15'))
    PAYMENT_PROMPT_DAY = int(os.getenv('PAYMENT_PROMPT_DAY', '14'))
    
    # Stripe Configuration
    STRIPE_API_VERSION = '2023-10-16'
    CURRENCY = 'usd'
    
    # Payment methods
    ACCEPTED_PAYMENT_METHODS = ['card']
    
    @classmethod
    def get_stripe_public_config(cls) -> Dict[str, str]:
        """Get public Stripe configuration for frontend"""
        return {
            'publishableKey': cls.STRIPE_PUBLISHABLE_KEY,
            'priceIds': cls.PRICE_IDS,
            'pricing': cls.TIER_PRICING,
            'currency': cls.CURRENCY,
            'trialEnabled': cls.TRIAL_ENABLED,
            'trialDays': cls.TRIAL_DURATION_DAYS
        }
    
    @classmethod
    def get_price_id_for_tier(cls, tier: str) -> Optional[str]:
        """Get Stripe price ID for a specific tier"""
        return cls.PRICE_IDS.get(tier.upper())
    
    @classmethod
    def get_price_for_tier(cls, tier: str) -> Optional[int]:
        """Get price in USD for a specific tier"""
        return cls.TIER_PRICING.get(tier.upper())
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate payment configuration"""
        try:
            # Check required environment variables
            assert cls.STRIPE_PUBLISHABLE_KEY is not None, "STRIPE_PUBLISHABLE_KEY not set"
            assert cls.STRIPE_PUBLISHABLE_KEY.startswith('pk_'), "Invalid publishable key format"
            
            # Check if secret key is configured (for server-side operations)
            if cls.STRIPE_SECRET_KEY:
                assert cls.STRIPE_SECRET_KEY.startswith('sk_'), "Invalid secret key format"
            
            return True
        except AssertionError as e:
            print(f"Payment configuration validation failed: {e}")
            return False

# Singleton instance
payment_config = PaymentConfig()

# Export commonly used values
STRIPE_PUBLISHABLE_KEY = payment_config.STRIPE_PUBLISHABLE_KEY
TIER_PRICING = payment_config.TIER_PRICING
PRICE_IDS = payment_config.PRICE_IDS