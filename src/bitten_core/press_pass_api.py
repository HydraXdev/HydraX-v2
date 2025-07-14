"""
BITTEN Press Pass API Endpoints
Handles email capture, activation, and conversion tracking
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, Any
from .press_pass_manager import press_pass_manager
from .analytics_tracker import track_event
import redis
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
press_pass_api = Blueprint('press_pass_api', __name__)

# Redis client for rate limiting
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis not available for rate limiting: {e}")
    redis_client = None

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_client_ip() -> str:
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'

def check_rate_limit(identifier: str, limit: int = 5, window: int = 3600) -> bool:
    """Check rate limit for identifier"""
    if not redis_client:
        return True
    
    try:
        key = f"rate_limit:{identifier}"
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, window)
        return current <= limit
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return True

@press_pass_api.route('/api/press-pass/claim', methods=['POST'])
def claim_press_pass():
    """Claim a Press Pass"""
    try:
        data = request.get_json()
        
        # Validate required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        
        if not name or not email:
            return jsonify({
                'success': False,
                'error': 'missing_fields',
                'message': 'Name and email are required'
            }), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'invalid_email',
                'message': 'Please enter a valid email address'
            }), 400
        
        # Check rate limit by IP
        client_ip = get_client_ip()
        if not check_rate_limit(f"press_pass_ip:{client_ip}", limit=3, window=3600):
            return jsonify({
                'success': False,
                'error': 'rate_limit',
                'message': 'Too many attempts. Please try again later.'
            }), 429
        
        # Check rate limit by email
        if not check_rate_limit(f"press_pass_email:{email}", limit=2, window=86400):
            return jsonify({
                'success': False,
                'error': 'rate_limit',
                'message': 'This email has already been used recently.'
            }), 429
        
        # Prepare claim data
        claim_data = {
            'email': email,
            'name': name,
            'source': data.get('source', 'web'),
            'utm_source': data.get('utm_source'),
            'utm_medium': data.get('utm_medium'),
            'utm_campaign': data.get('utm_campaign'),
            'referral_code': data.get('referral_code'),
            'user_agent': data.get('user_agent', request.headers.get('User-Agent')),
            'ip_address': client_ip
        }
        
        # Claim the Press Pass
        result = press_pass_manager.claim_press_pass(**claim_data)
        
        if result['success']:
            # Track analytics event
            track_event('press_pass_claimed', {
                'email': email,
                'source': claim_data['source'],
                'utm_campaign': claim_data['utm_campaign'],
                'ab_variant': result.get('ab_variant')
            })
            
            # Update daily counter in Redis
            if redis_client:
                redis_client.publish('press_pass:claimed', json.dumps({
                    'email': email,
                    'timestamp': datetime.utcnow().isoformat()
                }))
            
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error claiming Press Pass: {e}")
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'Unable to process your request. Please try again.'
        }), 500

@press_pass_api.route('/api/press-pass/remaining', methods=['GET'])
def get_remaining_passes():
    """Get remaining Press Passes"""
    try:
        weekly_remaining = press_pass_manager.get_weekly_remaining()
        daily_remaining = press_pass_manager.get_daily_remaining()
        
        return jsonify({
            'success': True,
            'weekly_remaining': weekly_remaining,
            'daily_remaining': daily_remaining,
            'weekly_limit': 200,
            'daily_display_limit': 30
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting remaining passes: {e}")
        return jsonify({
            'success': False,
            'error': 'server_error'
        }), 500

@press_pass_api.route('/api/press-pass/activate', methods=['POST'])
def activate_press_pass():
    """Activate a Press Pass"""
    try:
        data = request.get_json()
        claim_token = data.get('claim_token', '').strip()
        telegram_id = data.get('telegram_id')
        
        if not claim_token or not telegram_id:
            return jsonify({
                'success': False,
                'error': 'missing_fields',
                'message': 'Claim token and Telegram ID are required'
            }), 400
        
        # Activate the pass
        result = press_pass_manager.activate_press_pass(claim_token, telegram_id)
        
        if result['success']:
            # Track activation
            track_event('press_pass_activated', {
                'telegram_id': telegram_id
            })
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Error activating Press Pass: {e}")
        return jsonify({
            'success': False,
            'error': 'server_error'
        }), 500

@press_pass_api.route('/api/press-pass/convert', methods=['POST'])
def convert_press_pass():
    """Convert Press Pass to paid tier"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        new_tier = data.get('tier')
        
        if not telegram_id or not new_tier:
            return jsonify({
                'success': False,
                'error': 'missing_fields'
            }), 400
        
        # TODO: Integrate with actual user upgrade system
        # For now, just track the conversion
        track_event('press_pass_converted', {
            'telegram_id': telegram_id,
            'new_tier': new_tier,
            'conversion_value': {
                'NIBBLER': 39,
                'FANG': 89,
                'COMMANDER': 139,
                'APEX': 188
            }.get(new_tier, 0)
        })
        
        return jsonify({
            'success': True,
            'message': 'Conversion tracked successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error converting Press Pass: {e}")
        return jsonify({
            'success': False,
            'error': 'server_error'
        }), 500

@press_pass_api.route('/api/press-pass/metrics', methods=['GET'])
def get_metrics():
    """Get Press Pass conversion metrics (admin only)"""
    try:
        # TODO: Add authentication check
        api_key = request.headers.get('X-API-Key')
        if api_key != current_app.config.get('ADMIN_API_KEY'):
            return jsonify({'error': 'unauthorized'}), 401
        
        metrics = press_pass_manager.get_conversion_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'server_error'
        }), 500

@press_pass_api.route('/track/email/open/<int:claim_id>/<campaign_type>', methods=['GET'])
def track_email_open(claim_id: int, campaign_type: str):
    """Track email open (pixel tracking)"""
    try:
        # Track the open
        track_event('email_opened', {
            'claim_id': claim_id,
            'campaign_type': campaign_type
        })
        
        # Return 1x1 transparent pixel
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
        return pixel, 200, {'Content-Type': 'image/gif'}
        
    except Exception as e:
        logger.error(f"Error tracking email open: {e}")
        return '', 200

@press_pass_api.route('/track/email/click', methods=['POST'])
def track_email_click():
    """Track email click"""
    try:
        data = request.get_json()
        claim_id = data.get('claim_id')
        campaign_type = data.get('campaign_type')
        cta = data.get('cta')
        
        track_event('email_clicked', {
            'claim_id': claim_id,
            'campaign_type': campaign_type,
            'cta': cta
        })
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error tracking email click: {e}")
        return jsonify({'success': False}), 500

# WebSocket events for real-time updates
def emit_press_pass_update():
    """Emit Press Pass update via WebSocket"""
    try:
        if hasattr(current_app, 'socketio'):
            remaining = press_pass_manager.get_daily_remaining()
            current_app.socketio.emit('press_pass_update', {
                'daily_remaining': remaining,
                'timestamp': datetime.utcnow().isoformat()
            }, namespace='/live')
    except Exception as e:
        logger.error(f"Error emitting update: {e}")