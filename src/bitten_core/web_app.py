"""
BITTEN Web Application
Serves landing page and handles Stripe webhooks
"""

from flask import Flask, render_template_string, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
import time
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
# from .stripe_webhook_endpoint import stripe_webhook
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Redis connection for real-time data
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
    redis_client = None

# In-memory storage fallback
memory_store = {
    'fire_counts': {},
    'user_stats': {},
    'mission_data': {}
}

# Import Press Pass API
from .press_pass_api import press_pass_api
from .analytics_tracker import track_event

# Register blueprints
app.register_blueprint(press_pass_api)
# app.register_blueprint(stripe_webhook)

# Simple webhook endpoint for now
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    # For now, just acknowledge receipt
    logger.info(f"Received Stripe webhook")
    return jsonify({'received': True}), 200

# Serve landing pages
@app.route('/')
def index():
    """Serve enhanced landing page with A/B testing"""
    try:
        # Track page view
        track_event('landing_page_view', {
            'page': 'home',
            'referrer': request.referrer,
            'user_agent': request.headers.get('User-Agent')
        })
        
        # Use the new enhanced landing page
        with open('/root/HydraX-v2/landing/index_v2.html', 'r') as f:
            return f.read()
    except:
        # Fallback to original
        try:
            with open('/root/HydraX-v2/landing/index.html', 'r') as f:
                return f.read()
        except:
            return "BITTEN - Coming Soon", 200

@app.route('/terms')
def terms():
    """Serve terms of service"""
    try:
        with open('/root/HydraX-v2/landing/terms.html', 'r') as f:
            return f.read()
    except:
        return "Terms of Service", 200

@app.route('/privacy')
def privacy():
    """Serve privacy policy"""
    try:
        with open('/root/HydraX-v2/landing/privacy.html', 'r') as f:
            return f.read()
    except:
        return "Privacy Policy", 200

@app.route('/refund')
def refund():
    """Serve refund policy"""
    try:
        with open('/root/HydraX-v2/landing/refund.html', 'r') as f:
            return f.read()
    except:
        return "Refund Policy", 200

# Data storage helpers
def get_data(key: str, default=None):
    """Get data from Redis or memory store"""
    try:
        if redis_client:
            data = redis_client.get(key)
            return json.loads(data) if data else default
        else:
            return memory_store.get(key, default)
    except Exception as e:
        logger.error(f"Error getting data for key {key}: {e}")
        return default

def set_data(key: str, value: Any, expiration: Optional[int] = None):
    """Set data in Redis or memory store"""
    try:
        if redis_client:
            redis_client.set(key, json.dumps(value), ex=expiration)
        else:
            memory_store[key] = value
    except Exception as e:
        logger.error(f"Error setting data for key {key}: {e}")

def increment_data(key: str, amount: int = 1):
    """Increment numeric data"""
    try:
        if redis_client:
            return redis_client.incr(key, amount)
        else:
            current = memory_store.get(key, 0)
            memory_store[key] = current + amount
            return memory_store[key]
    except Exception as e:
        logger.error(f"Error incrementing data for key {key}: {e}")
        return 0

# API Endpoints

@app.route('/api/fire', methods=['POST'])
def fire_trade():
    """Execute a trade (fire button)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        signal_id = data.get('signal_id')
        
        if not user_id or not signal_id:
            return jsonify({'error': 'Missing user_id or signal_id'}), 400
        
        # Check if user already fired for this signal
        fire_key = f"user_fired:{user_id}:{signal_id}"
        if get_data(fire_key):
            return jsonify({'error': 'Already fired for this signal'}), 409
        
        # Generate trade ID
        trade_id = f"T{int(time.time())}{user_id[-4:]}"
        
        # Record the fire
        set_data(fire_key, True, 3600)  # Expire in 1 hour
        
        # Increment fire count
        fire_count_key = f"fire_count:{signal_id}"
        new_count = increment_data(fire_count_key)
        
        # Update user stats
        user_stats = get_data(f"user_stats:{user_id}", {
            'trades_today': 0,
            'last_7d_pnl': 0,
            'win_rate': 75,
            'rank': 'WARRIOR'
        })
        user_stats['trades_today'] += 1
        set_data(f"user_stats:{user_id}", user_stats)
        
        # Emit real-time update to all users in this mission
        socketio.emit('fire_count_update', {
            'signal_id': signal_id,
            'count': new_count,
            'timestamp': time.time()
        }, room=f"mission_{signal_id}")
        
        # Emit user stats update
        socketio.emit('user_stats_update', {
            'user_id': user_id,
            'stats': user_stats,
            'timestamp': time.time()
        }, room=f"user_{user_id}")
        
        return jsonify({
            'success': True,
            'trade_id': trade_id,
            'fire_count': new_count,
            'user_stats': user_stats
        })
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/signals/<signal_id>/fire-count', methods=['GET'])
def get_fire_count(signal_id):
    """Get current fire count for a signal"""
    try:
        fire_count_key = f"fire_count:{signal_id}"
        count = get_data(fire_count_key, 0)
        
        return jsonify({
            'signal_id': signal_id,
            'count': count,
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error getting fire count: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Get current user statistics"""
    try:
        stats = get_data(f"user_stats:{user_id}", {
            'trades_today': 0,
            'last_7d_pnl': 0,
            'win_rate': 75,
            'rank': 'WARRIOR'
        })
        
        return jsonify({
            'user_id': user_id,
            'stats': stats,
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/missions/<signal_id>', methods=['GET'])
def get_mission_data(signal_id):
    """Get mission briefing data"""
    try:
        # Get mission data from storage or generate it
        mission_data = get_data(f"mission:{signal_id}")
        
        if not mission_data:
            # Generate mock mission data if not found
            mission_data = {
                'signal': {
                    'id': signal_id,
                    'symbol': 'EUR/USD',
                    'direction': 'BUY',
                    'entry_price': 1.0850,
                    'stop_loss': 1.0830,
                    'take_profit': 1.0880,
                    'tcs_score': 87,
                    'expires_at': int(time.time()) + 600
                },
                'user': {
                    'id': 'user_123',
                    'stats': {
                        'last_7d_pnl': 127.50,
                        'win_rate': 73,
                        'trades_today': 3,
                        'rank': 'WARRIOR'
                    }
                },
                'signal_stats': {
                    'time_remaining': 585,
                    'fire_count': get_data(f"fire_count:{signal_id}", 12)
                },
                'user_fired': False
            }
            
            # Cache the mission data
            set_data(f"mission:{signal_id}", mission_data, 3600)
        
        return jsonify(mission_data)
        
    except Exception as e:
        logger.error(f"Error getting mission data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Socket.IO Event Handlers

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_status', {'connected': True, 'timestamp': time.time()})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_mission')
def handle_join_mission(data):
    """Join a mission room for real-time updates"""
    try:
        signal_id = data.get('signal_id')
        user_id = data.get('user_id')
        
        if signal_id:
            # Join mission room
            join_room(f"mission_{signal_id}")
            
            # Join user room
            if user_id:
                join_room(f"user_{user_id}")
            
            logger.info(f"Client {request.sid} joined mission {signal_id}")
            
            # Send current fire count
            fire_count = get_data(f"fire_count:{signal_id}", 0)
            emit('fire_count_update', {
                'signal_id': signal_id,
                'count': fire_count,
                'timestamp': time.time()
            })
            
    except Exception as e:
        logger.error(f"Error joining mission: {e}")
        emit('error', {'message': 'Failed to join mission'})

@socketio.on('leave_mission')
def handle_leave_mission(data):
    """Leave a mission room"""
    try:
        signal_id = data.get('signal_id')
        user_id = data.get('user_id')
        
        if signal_id:
            leave_room(f"mission_{signal_id}")
            
        if user_id:
            leave_room(f"user_{user_id}")
            
        logger.info(f"Client {request.sid} left mission {signal_id}")
        
    except Exception as e:
        logger.error(f"Error leaving mission: {e}")

@app.route('/mission/<signal_id>')
def serve_mission_briefing(signal_id):
    """Serve mission briefing page"""
    try:
        # Get mission data
        mission_data = get_data(f"mission:{signal_id}")
        
        if not mission_data:
            return "Mission not found", 404
        
        # Read template
        template_path = os.path.join(os.path.dirname(__file__), '../../templates/mission_briefing.html')
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Render template with mission data
        return render_template_string(template_content, mission_data=mission_data)
        
    except Exception as e:
        logger.error(f"Error serving mission briefing: {e}")
        return "Internal server error", 500

# Health check endpoint
@app.route('/health')
def health():
    """Health check for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'BITTEN',
        'version': '2.0',
        'redis_connected': redis_client is not None,
        'timestamp': time.time()
    }), 200

# Stripe webhook is already registered via blueprint
# It will be available at /stripe/webhook

if __name__ == '__main__':
    # Run the app with Socket.IO
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)