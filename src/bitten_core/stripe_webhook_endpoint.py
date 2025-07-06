"""
Simple Stripe Webhook Endpoint
Add this to your main Flask app
"""

from flask import Blueprint, request, jsonify
import logging
from .stripe_payment_simple import get_stripe_processor
from .database.connection import get_db_session
from .database.models import User, UserSubscription, SubscriptionStatus

logger = logging.getLogger(__name__)

# Create blueprint
stripe_webhook = Blueprint('stripe_webhook', __name__)

@stripe_webhook.route('/stripe/webhook', methods=['POST'])
def handle_stripe_webhook():
    """Handle Stripe webhook events"""
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        return jsonify({'error': 'No signature'}), 400
    
    # Process webhook
    processor = get_stripe_processor()
    result = processor.handle_webhook(payload, sig_header)
    
    if not result['success']:
        return jsonify({'error': result.get('error')}), 400
    
    # Handle specific events
    event = result.get('event')
    
    if event == 'subscription_created':
        # Update user in database
        with get_db_session() as session:
            # Find user by Stripe customer ID
            user_sub = session.query(UserSubscription).filter(
                UserSubscription.stripe_customer_id == result['customer_id']
            ).first()
            
            if user_sub:
                user = session.query(User).filter(
                    User.user_id == user_sub.user_id
                ).first()
                
                if user:
                    # Activate subscription
                    user.subscription_status = SubscriptionStatus.ACTIVE.value
                    user.tier = result.get('tier', 'NIBBLER')
                    user.features_locked = False
                    
                    user_sub.stripe_subscription_id = result['subscription_id']
                    user_sub.status = SubscriptionStatus.ACTIVE.value
                    
                    session.commit()
                    logger.info(f"Activated subscription for user {user.user_id}")
    
    elif event == 'subscription_cancelled':
        # Handle cancellation
        with get_db_session() as session:
            user_sub = session.query(UserSubscription).filter(
                UserSubscription.stripe_subscription_id == result['subscription_id']
            ).first()
            
            if user_sub:
                user = session.query(User).filter(
                    User.user_id == user_sub.user_id
                ).first()
                
                if user:
                    # Cancel at period end
                    user.subscription_status = SubscriptionStatus.CANCELLED.value
                    user_sub.status = SubscriptionStatus.CANCELLED.value
                    
                    session.commit()
                    logger.info(f"Cancelled subscription for user {user.user_id}")
    
    elif event == 'payment_succeeded':
        # Unlock features on successful payment
        with get_db_session() as session:
            user_sub = session.query(UserSubscription).filter(
                UserSubscription.stripe_customer_id == result['customer_id']
            ).first()
            
            if user_sub:
                user = session.query(User).filter(
                    User.user_id == user_sub.user_id
                ).first()
                
                if user:
                    user.features_locked = False
                    user.subscription_status = SubscriptionStatus.ACTIVE.value
                    session.commit()
    
    elif event == 'payment_failed':
        # Enter grace period
        with get_db_session() as session:
            user_sub = session.query(UserSubscription).filter(
                UserSubscription.stripe_customer_id == result['customer_id']
            ).first()
            
            if user_sub:
                user = session.query(User).filter(
                    User.user_id == user_sub.user_id
                ).first()
                
                if user:
                    user.subscription_status = SubscriptionStatus.PAST_DUE.value
                    
                    # Lock features after grace period
                    if not result.get('next_attempt'):
                        user.features_locked = True
                    
                    session.commit()
    
    return jsonify({'success': True}), 200

# Helper function to add to your main app
def register_stripe_webhook(app):
    """Register the Stripe webhook blueprint"""
    app.register_blueprint(stripe_webhook)
    logger.info("Stripe webhook endpoint registered at /stripe/webhook")