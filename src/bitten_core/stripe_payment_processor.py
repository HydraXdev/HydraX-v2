"""
BITTEN Stripe Payment Integration
Handles all payment processing through Stripe
"""

import stripe
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import os
from decimal import Decimal

logger = logging.getLogger(__name__)

class StripePaymentProcessor:
    """Stripe payment processor for BITTEN subscriptions"""
    
    def __init__(self):
        # Initialize Stripe with API key from environment
        self.stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        self.stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if not self.stripe_secret_key:
            logger.warning("Stripe secret key not found in environment")
        else:
            stripe.api_key = self.stripe_secret_key
            
        # Price IDs for subscription plans (monthly only)
        self.price_ids = {
            'NIBBLER': os.getenv('STRIPE_PRICE_NIBBLER', 'price_nibbler_monthly'),
            'FANG': os.getenv('STRIPE_PRICE_FANG', 'price_fang_monthly'),
            'COMMANDER': os.getenv('STRIPE_PRICE_COMMANDER', 'price_commander_monthly')
        }
        
        logger.info("Stripe payment processor initialized")
    
    async def create_customer(self, user_id: int, email: Optional[str] = None,
                            metadata: Optional[Dict] = None) -> Dict:
        """Create Stripe customer for user"""
        
        try:
            customer_data = {
                'metadata': {
                    'bitten_user_id': str(user_id),
                    'platform': 'telegram',
                    **(metadata or {})
                }
            }
            
            if email:
                customer_data['email'] = email
            
            customer = stripe.Customer.create(**customer_data)
            
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            
            return {
                'success': True,
                'customer_id': customer.id,
                'customer': customer
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_setup_intent(self, customer_id: str) -> Dict:
        """Create setup intent for saving payment method"""
        
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                usage='off_session',
                metadata={
                    'type': 'subscription_payment_method'
                }
            )
            
            return {
                'success': True,
                'client_secret': setup_intent.client_secret,
                'setup_intent_id': setup_intent.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating setup intent: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_subscription(self, customer_id: str, tier: str, 
                                billing_cycle: str = 'monthly') -> Dict:
        """Create subscription for customer"""
        
        try:
            # Get price ID
            price_key = f"{tier.upper()}_{billing_cycle.upper()}"
            price_id = self.price_ids.get(price_key)
            
            if not price_id:
                return {
                    'success': False,
                    'error': f'Invalid tier/billing combination: {tier}/{billing_cycle}'
                }
            
            # Create subscription with 15-day trial
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=15,  # 15-day free trial
                payment_behavior='default_incomplete',
                payment_settings={
                    'save_default_payment_method': 'on_subscription'
                },
                metadata={
                    'tier': tier,
                    'billing_cycle': billing_cycle
                }
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'trial_end': datetime.fromtimestamp(subscription.trial_end),
                'subscription': subscription
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_subscription(self, subscription_id: str, new_tier: str,
                                new_billing_cycle: str = None) -> Dict:
        """Update existing subscription (upgrade/downgrade)"""
        
        try:
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Get new price ID
            billing_cycle = new_billing_cycle or ('annual' if 'annual' in subscription.items.data[0].price.id else 'monthly')
            price_key = f"{new_tier.upper()}_{billing_cycle.upper()}"
            new_price_id = self.price_ids.get(price_key)
            
            if not new_price_id:
                return {
                    'success': False,
                    'error': f'Invalid tier/billing combination: {new_tier}/{billing_cycle}'
                }
            
            # Update subscription
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription.items.data[0].id,
                    'price': new_price_id}],
                proration_behavior='always_invoice',  # Charge/credit immediately
                metadata={
                    'tier': new_tier,
                    'billing_cycle': billing_cycle,
                    'upgraded_at': datetime.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'subscription': updated_subscription,
                'new_tier': new_tier,
                'billing_cycle': billing_cycle
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> Dict:
        """Cancel subscription"""
        
        try:
            if immediate:
                # Cancel immediately
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                # Cancel at period end
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                    metadata={
                        'cancelled_at': datetime.now().isoformat()
                    }
                )
            
            return {
                'success': True,
                'subscription': subscription,
                'cancelled_at': datetime.now(),
                'effective_date': datetime.now() if immediate else datetime.fromtimestamp(subscription.current_period_end)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def reactivate_subscription(self, subscription_id: str) -> Dict:
        """Reactivate cancelled subscription"""
        
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
                metadata={
                    'reactivated_at': datetime.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'subscription': subscription
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error reactivating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_checkout_session(self, customer_id: str, tier: str,
                                    billing_cycle: str, success_url: str,
                                    cancel_url: str) -> Dict:
        """Create Stripe Checkout session for payment collection"""
        
        try:
            price_key = f"{tier.upper()}_{billing_cycle.upper()}"
            price_id = self.price_ids.get(price_key)
            
            if not price_id:
                return {
                    'success': False,
                    'error': f'Invalid tier/billing combination: {tier}/{billing_cycle}'
                }
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1}],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    'trial_period_days': 15,
                    'metadata': {
                        'tier': tier,
                        'billing_cycle': billing_cycle
                    }
                }
            )
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_portal_session(self, customer_id: str, return_url: str) -> Dict:
        """Create customer portal session for managing subscription"""
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                'success': True,
                'portal_url': session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """Handle Stripe webhook events"""
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.stripe_webhook_secret
            )
            
            logger.info(f"Received Stripe webhook: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'customer.subscription.created':
                return self._handle_subscription_created(event)
            
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event)
            
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event)
            
            elif event['type'] == 'customer.subscription.trial_will_end':
                return self._handle_trial_ending(event)
            
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event)
            
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event)
            
            else:
                logger.info(f"Unhandled webhook type: {event['type']}")
                return {'success': True, 'handled': False}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_created(self, event: Dict) -> Dict:
        """Handle subscription created event"""
        
        subscription = event['data']['object']
        customer_id = subscription['customer']
        user_id = subscription['metadata'].get('bitten_user_id')
        
        logger.info(f"Subscription created for user {user_id}: {subscription['id']}")
        
        return {
            'success': True,
            'event_type': 'subscription_created',
            'user_id': user_id,
            'subscription_id': subscription['id'],
            'status': subscription['status'],
            'trial_end': datetime.fromtimestamp(subscription['trial_end']) if subscription['trial_end'] else None
        }
    
    def _handle_subscription_updated(self, event: Dict) -> Dict:
        """Handle subscription updated event"""
        
        subscription = event['data']['object']
        previous = event['data'].get('previous_attributes', {})
        
        user_id = subscription['metadata'].get('bitten_user_id')
        
        logger.info(f"Subscription updated for user {user_id}: {subscription['id']}")
        
        return {
            'success': True,
            'event_type': 'subscription_updated',
            'user_id': user_id,
            'subscription_id': subscription['id'],
            'changes': previous
        }
    
    def _handle_subscription_deleted(self, event: Dict) -> Dict:
        """Handle subscription deleted event"""
        
        subscription = event['data']['object']
        user_id = subscription['metadata'].get('bitten_user_id')
        
        logger.info(f"Subscription deleted for user {user_id}: {subscription['id']}")
        
        return {
            'success': True,
            'event_type': 'subscription_deleted',
            'user_id': user_id,
            'subscription_id': subscription['id']
        }
    
    def _handle_trial_ending(self, event: Dict) -> Dict:
        """Handle trial ending event (3 days before end)"""
        
        subscription = event['data']['object']
        user_id = subscription['metadata'].get('bitten_user_id')
        
        logger.info(f"Trial ending soon for user {user_id}: {subscription['id']}")
        
        return {
            'success': True,
            'event_type': 'trial_ending',
            'user_id': user_id,
            'subscription_id': subscription['id'],
            'trial_end': datetime.fromtimestamp(subscription['trial_end'])
        }
    
    def _handle_payment_succeeded(self, event: Dict) -> Dict:
        """Handle successful payment"""
        
        invoice = event['data']['object']
        user_id = invoice.get('metadata', {}).get('bitten_user_id')
        
        logger.info(f"Payment succeeded for user {user_id}: ${invoice['amount_paid'] / 100}")
        
        return {
            'success': True,
            'event_type': 'payment_succeeded',
            'user_id': user_id,
            'amount': invoice['amount_paid'] / 100,
            'invoice_id': invoice['id']
        }
    
    def _handle_payment_failed(self, event: Dict) -> Dict:
        """Handle failed payment"""
        
        invoice = event['data']['object']
        user_id = invoice.get('metadata', {}).get('bitten_user_id')
        
        logger.error(f"Payment failed for user {user_id}: ${invoice['amount_due'] / 100}")
        
        return {
            'success': True,
            'event_type': 'payment_failed',
            'user_id': user_id,
            'amount': invoice['amount_due'] / 100,
            'invoice_id': invoice['id'],
            'next_payment_attempt': datetime.fromtimestamp(invoice['next_payment_attempt']) if invoice.get('next_payment_attempt') else None
        }

# Singleton instance
_stripe_processor = None

def get_stripe_processor() -> StripePaymentProcessor:
    """Get or create Stripe processor instance"""
    global _stripe_processor
    if _stripe_processor is None:
        _stripe_processor = StripePaymentProcessor()
    return _stripe_processor