"""
Simplified Stripe Payment Integration - Monthly Only
"""

import stripe
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class SimpleStripeProcessor:
    """Simplified Stripe processor for monthly subscriptions only"""
    
    def __init__(self):
        # Use the live key you provided
        self.stripe_secret_key = os.getenv('STRIPE_SECRET_KEY', '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')
        stripe.api_key = self.stripe_secret_key
        
        # Monthly prices for each tier
        self.tier_prices = {
            'NIBBLER': 39,
            'FANG': 89,
            'COMMANDER': 189
        }
        
        # Price IDs will be set after creating products
        self.price_ids = {}
        
        logger.info("Simple Stripe processor initialized")
    
    async def setup_products(self) -> Dict[str, str]:
        """One-time setup to create products and prices in Stripe"""
        
        try:
            created_prices = {}
            
            for tier, price_cents in [
                ('NIBBLER', 3900),      # $39.00
                ('FANG', 8900),         # $89.00
                ('COMMANDER', 18900)    # $189.00
            ]:
                # Create product
                product = stripe.Product.create(
                    name=f'BITTEN {tier.title()}',
                    description=f'{tier} tier subscription',
                    metadata={'tier': tier}
                )
                
                # Create monthly price
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=price_cents,
                    currency='usd',
                    recurring={'interval': 'month'},
                    metadata={'tier': tier}
                )
                
                created_prices[tier] = price.id
                logger.info(f"Created {tier} product and price: {price.id}")
            
            # Save to environment or config
            self.price_ids = created_prices
            
            return {
                'success': True,
                'prices': created_prices,
                'message': 'Products created successfully! Save these price IDs to your .env file.'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating products: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_customer(self, user_id: int, email: Optional[str] = None) -> Dict:
        """Create a Stripe customer"""
        
        try:
            customer = stripe.Customer.create(
                metadata={
                    'bitten_user_id': str(user_id),
                    'platform': 'telegram'
                },
                email=email
            )
            
            return {
                'success': True,
                'customer_id': customer.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating customer: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_payment_link(self, customer_id: str, tier: str) -> Dict:
        """Create a payment link for subscription"""
        
        try:
            price_id = self.price_ids.get(tier)
            if not price_id:
                # Try to get from environment
                price_id = os.getenv(f'STRIPE_PRICE_{tier}')
                
            if not price_id:
                return {
                    'success': False,
                    'error': f'Price not configured for {tier}. Run setup_products first.'
                }
            
            # Create payment link
            link = stripe.PaymentLink.create(
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                metadata={
                    'tier': tier,
                    'customer_id': customer_id
                },
                subscription_data={
                    'trial_period_days': 15,
                    'metadata': {
                        'tier': tier
                    }
                },
                after_completion={
                    'type': 'redirect',
                    'redirect': {
                        'url': 'https://t.me/your_bot?start=payment_success'
                    }
                }
            )
            
            return {
                'success': True,
                'payment_url': link.url,
                'payment_link_id': link.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment link: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_checkout_session(self, customer_id: str, tier: str,
                                    success_url: str, cancel_url: str) -> Dict:
        """Create a checkout session"""
        
        try:
            price_id = self.price_ids.get(tier) or os.getenv(f'STRIPE_PRICE_{tier}')
            
            if not price_id:
                return {
                    'success': False,
                    'error': f'Price not configured for {tier}'
                }
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    'trial_period_days': 15,
                    'metadata': {
                        'tier': tier
                    }
                }
            )
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout: {e}")
            return {'success': False, 'error': str(e)}
    
    async def cancel_subscription(self, subscription_id: str) -> Dict:
        """Cancel subscription at period end"""
        
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            
            return {
                'success': True,
                'cancelled_at': datetime.now(),
                'ends_at': datetime.fromtimestamp(subscription.current_period_end)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    async def reactivate_subscription(self, subscription_id: str) -> Dict:
        """Reactivate a cancelled subscription"""
        
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            return {'success': True}
            
        except stripe.error.StripeError as e:
            logger.error(f"Error reactivating subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    async def update_subscription_tier(self, subscription_id: str, new_tier: str) -> Dict:
        """Change subscription tier (upgrade/downgrade)"""
        
        try:
            # Get subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Get new price ID
            new_price_id = self.price_ids.get(new_tier) or os.getenv(f'STRIPE_PRICE_{new_tier}')
            
            if not new_price_id:
                return {
                    'success': False,
                    'error': f'Price not configured for {new_tier}'
                }
            
            # Update subscription
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription.items.data[0].id,
                    'price': new_price_id
                }],
                proration_behavior='always_invoice',
                metadata={
                    'tier': new_tier,
                    'upgraded_at': datetime.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'new_tier': new_tier,
                'effective_date': datetime.now()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error updating subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """Handle Stripe webhooks"""
        
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            logger.warning("No webhook secret configured")
            return {'success': False, 'error': 'Webhook not configured'}
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle the event
            if event['type'] == 'customer.subscription.created':
                subscription = event['data']['object']
                return {
                    'success': True,
                    'event': 'subscription_created',
                    'subscription_id': subscription['id'],
                    'customer_id': subscription['customer'],
                    'tier': subscription['metadata'].get('tier'),
                    'trial_end': datetime.fromtimestamp(subscription['trial_end']) if subscription.get('trial_end') else None
                }
            
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                return {
                    'success': True,
                    'event': 'subscription_cancelled',
                    'subscription_id': subscription['id'],
                    'customer_id': subscription['customer']
                }
            
            elif event['type'] == 'customer.subscription.updated':
                subscription = event['data']['object']
                return {
                    'success': True,
                    'event': 'subscription_updated',
                    'subscription_id': subscription['id'],
                    'status': subscription['status']
                }
            
            elif event['type'] == 'invoice.payment_succeeded':
                invoice = event['data']['object']
                return {
                    'success': True,
                    'event': 'payment_succeeded',
                    'amount': invoice['amount_paid'] / 100,
                    'customer_id': invoice['customer']
                }
            
            elif event['type'] == 'invoice.payment_failed':
                invoice = event['data']['object']
                return {
                    'success': True,
                    'event': 'payment_failed',
                    'customer_id': invoice['customer'],
                    'next_attempt': datetime.fromtimestamp(invoice['next_payment_attempt']) if invoice.get('next_payment_attempt') else None
                }
            
            else:
                logger.info(f"Unhandled webhook type: {event['type']}")
                return {'success': True, 'event': 'unhandled'}
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {'success': False, 'error': str(e)}

# Singleton
_processor = None

def get_stripe_processor() -> SimpleStripeProcessor:
    """Get or create processor instance"""
    global _processor
    if _processor is None:
        _processor = SimpleStripeProcessor()
    return _processor