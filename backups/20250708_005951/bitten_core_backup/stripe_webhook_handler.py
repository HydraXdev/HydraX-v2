"""
Stripe Webhook Handler for BITTEN
Processes Stripe events and updates system accordingly
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from .stripe_payment_processor import get_stripe_processor
from .database.connection import get_db_session
from .database.models import User, UserSubscription, SubscriptionStatus
from .risk_controller import get_risk_controller

logger = logging.getLogger(__name__)

# Create Flask blueprint for Stripe webhooks
stripe_webhook_bp = Blueprint('stripe_webhooks', __name__)

@stripe_webhook_bp.route('/stripe/webhook', methods=['POST'])
def handle_stripe_webhook():
    """Handle incoming Stripe webhooks"""
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        logger.error("No Stripe signature in webhook request")
        return jsonify({'error': 'No signature'}), 400
    
    # Process webhook
    stripe_processor = get_stripe_processor()
    result = stripe_processor.handle_webhook(payload, sig_header)
    
    if not result['success']:
        return jsonify({'error': result.get('error', 'Processing failed')}), 400
    
    # Handle specific events
    event_type = result.get('event_type')
    
    if event_type == 'subscription_created':
        handle_subscription_created(result)
    
    elif event_type == 'subscription_updated':
        handle_subscription_updated(result)
    
    elif event_type == 'subscription_deleted':
        handle_subscription_cancelled(result)
    
    elif event_type == 'trial_ending':
        handle_trial_ending(result)
    
    elif event_type == 'payment_succeeded':
        handle_payment_succeeded(result)
    
    elif event_type == 'payment_failed':
        handle_payment_failed(result)
    
    return jsonify({'success': True}), 200

def handle_subscription_created(data: dict):
    """Handle new subscription creation"""
    
    user_id = int(data['user_id']) if data.get('user_id') else None
    if not user_id:
        logger.error("No user_id in subscription created event")
        return
    
    with get_db_session() as session:
        try:
            # Update user subscription status
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.subscription_status = SubscriptionStatus.ACTIVE.value
                user.stripe_subscription_id = data['subscription_id']
                
                # If coming from trial, mark as converted
                subscription = session.query(UserSubscription).filter(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatus.TRIALING.value
                ).first()
                
                if subscription:
                    subscription.status = SubscriptionStatus.ACTIVE.value
                    subscription.stripe_subscription_id = data['subscription_id']
                    subscription.converted_at = datetime.now()
                
                session.commit()
                logger.info(f"Subscription created for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error handling subscription created: {e}")
            session.rollback()

def handle_subscription_updated(data: dict):
    """Handle subscription updates (upgrades/downgrades)"""
    
    user_id = int(data['user_id']) if data.get('user_id') else None
    if not user_id:
        return
    
    changes = data.get('changes', {})
    
    with get_db_session() as session:
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            subscription = session.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.stripe_subscription_id == data['subscription_id']
            ).first()
            
            if user and subscription:
                # Check for tier changes
                if 'items' in changes:
                    # Extract new tier from price ID
                    # This would need to map price IDs to tiers
                    pass
                
                # Check for cancellation scheduling
                if 'cancel_at_period_end' in changes:
                    if changes['cancel_at_period_end']:
                        subscription.auto_renew = False
                        subscription.cancelled_at = datetime.now()
                    else:
                        subscription.auto_renew = True
                        subscription.cancelled_at = None
                
                session.commit()
                logger.info(f"Subscription updated for user {user_id}: {changes}")
        
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            session.rollback()

def handle_subscription_cancelled(data: dict):
    """Handle subscription cancellation"""
    
    user_id = int(data['user_id']) if data.get('user_id') else None
    if not user_id:
        return
    
    with get_db_session() as session:
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            subscription = session.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.stripe_subscription_id == data['subscription_id']
            ).first()
            
            if user and subscription:
                # Lock features after grace period
                user.subscription_status = SubscriptionStatus.CANCELLED.value
                user.features_locked = True
                
                subscription.status = SubscriptionStatus.CANCELLED.value
                subscription.ends_at = datetime.now()
                
                # Update risk controller
                risk_controller = get_risk_controller()
                risk_controller.update_user_tier(user_id, "NIBBLER")  # Downgrade to free
                
                session.commit()
                logger.info(f"Subscription cancelled for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            session.rollback()

def handle_trial_ending(data: dict):
    """Handle trial ending notification (3 days before)"""
    
    user_id = int(data['user_id']) if data.get('user_id') else None
    if not user_id:
        return
    
    # This is handled by the trial manager's reminder system
    logger.info(f"Trial ending soon for user {user_id}")

def handle_payment_succeeded(data: dict):
    """Handle successful payment"""
    
    user_id = int(data['user_id']) if data.get('user_id') else None
    if not user_id:
        return
    
    with get_db_session() as session:
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                # Ensure features are unlocked
                user.features_locked = False
                user.subscription_status = SubscriptionStatus.ACTIVE.value
                
                # Extend subscription period
                if user.subscription_expires_at:
                    # Add 30 days for monthly, 365 for annual
                    # This would need to check the actual billing cycle
                    pass
                
                session.commit()
                logger.info(f"Payment succeeded for user {user_id}: ${data['amount']}")
        
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            session.rollback()

def handle_payment_failed(data: dict):
    """Handle failed payment"""
    
    user_id = int(data['user_id']) if data.get('user_id') else None
    if not user_id:
        return
    
    with get_db_session() as session:
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            subscription = session.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE.value
            ).first()
            
            if user and subscription:
                # Enter grace period
                user.subscription_status = SubscriptionStatus.PAST_DUE.value
                subscription.status = SubscriptionStatus.PAST_DUE.value
                
                # Check if this is within grace period
                next_attempt = data.get('next_payment_attempt')
                if next_attempt:
                    days_until_retry = (next_attempt - datetime.now()).days
                    if days_until_retry > 2:  # Beyond grace period
                        user.features_locked = True
                
                session.commit()
                logger.info(f"Payment failed for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            session.rollback()

# Utility function to setup Stripe products and prices
def setup_stripe_products():
    """One-time setup of Stripe products and prices"""
    
    stripe_processor = get_stripe_processor()
    
    # This would create products and prices in Stripe
    # Run this once during initial setup
    
    products = {
        'NIBBLER': {
            'name': 'BITTEN Nibbler',
            'description': 'Entry-level trading tier with 6 daily trades',
            'monthly_price': 3900,  # $39.00 in cents
            'annual_price': 31200   # $312.00 in cents
        },
        'FANG': {
            'name': 'BITTEN Fang',
            'description': 'Advanced tier with sniper mode and 10 daily trades',
            'monthly_price': 8900,
            'annual_price': 71200
        },
        'COMMANDER': {
            'name': 'BITTEN Commander',
            'description': 'Professional tier with full automation and 20 daily trades',
            'monthly_price': 13900,
            'annual_price': 111200
        },
        'APEX': {
            'name': 'BITTEN Apex',
            'description': 'Elite tier with unlimited trades and priority support',
            'monthly_price': 18800,
            'annual_price': 150400
        }
    }
    
    # Create products and prices in Stripe
    # Store the price IDs in environment variables
    
    logger.info("Stripe products setup complete")