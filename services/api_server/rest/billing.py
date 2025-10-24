"""
BITTEN Stripe Billing Endpoints
Handles tier upgrades and Stripe checkout session creation
"""
from flask import Blueprint, request, jsonify
import logging
import asyncio

logger = logging.getLogger(__name__)

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/api/billing/create-checkout', methods=['POST'])
def create_checkout():
    """
    Create Stripe checkout session for tier upgrade

    Body: {
        user_id: str,
        tier: "NIBBLER" | "FANG" | "COMMANDER",
        success_url: str,
        cancel_url: str
    }

    Returns: {
        success: bool,
        checkout_url: str,
        session_id: str
    }
    """
    try:
        # Import here to avoid circular dependency
        from src.bitten_core.stripe_payment_simple import get_stripe_processor

        data = request.get_json()
        user_id = data.get('user_id')
        tier = data.get('tier', '').upper()
        success_url = data.get('success_url')
        cancel_url = data.get('cancel_url')

        # Validate
        if not all([user_id, tier, success_url, cancel_url]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: user_id, tier, success_url, cancel_url'
            }), 400

        if tier not in ['NIBBLER', 'FANG', 'COMMANDER']:
            return jsonify({
                'success': False,
                'error': f'Invalid tier: {tier}. Must be NIBBLER, FANG, or COMMANDER'
            }), 400

        # Get Stripe processor
        processor = get_stripe_processor()

        # Create or get Stripe customer
        # TODO: Check if user already has customer_id in database
        # For now, create new customer each time
        customer_result = asyncio.run(processor.create_customer(user_id, email=None))

        if not customer_result['success']:
            logger.error(f"Failed to create Stripe customer for user {user_id}: {customer_result.get('error')}")
            return jsonify({
                'success': False,
                'error': customer_result.get('error', 'Failed to create customer')
            }), 500

        customer_id = customer_result['customer_id']
        logger.info(f"Created Stripe customer {customer_id} for user {user_id}")

        # Create checkout session
        checkout_result = asyncio.run(processor.create_checkout_session(
            customer_id=customer_id,
            tier=tier,
            success_url=success_url,
            cancel_url=cancel_url
        ))

        if not checkout_result['success']:
            logger.error(f"Failed to create checkout session for {tier}: {checkout_result.get('error')}")
            return jsonify({
                'success': False,
                'error': checkout_result.get('error', 'Failed to create checkout session')
            }), 500

        logger.info(f"Created checkout session {checkout_result['session_id']} for user {user_id} tier {tier}")

        return jsonify({
            'success': True,
            'checkout_url': checkout_result['checkout_url'],
            'session_id': checkout_result['session_id']
        }), 200

    except Exception as e:
        logger.error(f'Checkout creation error: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@billing_bp.route('/api/billing/health', methods=['GET'])
def billing_health():
    """Health check for billing endpoints"""
    return jsonify({
        'success': True,
        'service': 'billing',
        'endpoints': ['/api/billing/create-checkout']
    }), 200
