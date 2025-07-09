"""
Flask Integration Example for Fire Router TOC

This example shows how to integrate the Fire Router TOC with a Flask application,
including proper error handling, authentication, and monitoring endpoints.
"""

from flask import Flask, request, jsonify
from functools import wraps
import logging
from datetime import datetime
from typing import Dict, Any

from fire_router_toc import (
    FireRouterTOC, TradeSignal, SignalType, DeliveryMethod,
    create_fire_endpoint
)
from terminal_assignment import TerminalType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize Fire Router TOC
router = FireRouterTOC(
    terminal_db_path="production_terminals.db",
    config_path="fire_router_config.json"
)


# Authentication decorator (simplified for example)
def require_auth(f):
    """Simple authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        # In production, validate against your auth system
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Extract user_id from token (simplified)
        # In production, decode and validate JWT token
        try:
            token = auth_header.split(' ')[1]
            # For demo purposes, we'll use the token as user_id
            request.user_id = token
        except:
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function


# Rate limiting decorator (simplified)
from functools import lru_cache
from collections import defaultdict
import time

rate_limit_storage = defaultdict(list)

def rate_limit(max_requests=10, window_seconds=60):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = getattr(request, 'user_id', 'anonymous')
            now = time.time()
            
            # Clean old entries
            rate_limit_storage[user_id] = [
                timestamp for timestamp in rate_limit_storage[user_id]
                if now - timestamp < window_seconds
            ]
            
            # Check rate limit
            if len(rate_limit_storage[user_id]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window_seconds
                }), 429
            
            # Record request
            rate_limit_storage[user_id].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/fire', methods=['POST'])
@require_auth
@rate_limit(max_requests=50, window_seconds=60)
def fire_signal():
    """
    Fire a new trade signal
    
    Expected JSON payload:
    {
        "symbol": "GBPUSD",
        "direction": "buy",
        "volume": 0.1,
        "stop_loss": 1.2450,  // optional
        "take_profit": 1.2550,  // optional
        "comment": "My trade",  // optional
        "terminal_type": "press_pass",  // optional, defaults to press_pass
        "delivery_method": "hybrid"  // optional: http_post, file_write, hybrid
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['symbol', 'direction', 'volume']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate data types and ranges
        try:
            volume = float(data['volume'])
            if volume <= 0 or volume > 100:
                raise ValueError("Volume must be between 0 and 100")
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid volume: {str(e)}'
            }), 400
        
        # Validate direction
        if data['direction'] not in ['buy', 'sell']:
            return jsonify({
                'success': False,
                'error': 'Direction must be "buy" or "sell"'
            }), 400
        
        # Create trade signal
        signal = TradeSignal(
            user_id=request.user_id,
            signal_type=SignalType.OPEN_POSITION,
            symbol=data['symbol'].upper(),
            direction=data['direction'],
            volume=volume,
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
            comment=data.get('comment', f'API trade {datetime.now().strftime("%Y%m%d_%H%M%S")}'),
            metadata={
                'source': 'flask_api',
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
        )
        
        # Determine terminal type
        terminal_type = TerminalType(data.get('terminal_type', 'press_pass'))
        
        # Determine delivery method
        delivery_method = None
        if 'delivery_method' in data:
            delivery_map = {
                'http_post': DeliveryMethod.HTTP_POST,
                'file_write': DeliveryMethod.FILE_WRITE,
                'hybrid': DeliveryMethod.HYBRID
            }
            delivery_method = delivery_map.get(data['delivery_method'])
        
        # Route the signal
        response = router.route_signal(
            signal=signal,
            terminal_type=terminal_type,
            delivery_method=delivery_method
        )
        
        # Log the attempt
        logger.info(f"Signal routing for {request.user_id}: {response.success} - {response.message}")
        
        # Return response
        return jsonify({
            'success': response.success,
            'message': response.message,
            'terminal_id': response.terminal_id,
            'terminal_name': response.terminal_name,
            'delivery_method': response.delivery_method,
            'timestamp': datetime.now().isoformat()
        }), 200 if response.success else 500
        
    except Exception as e:
        logger.error(f"Fire endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e) if app.debug else 'An error occurred'
        }), 500


@app.route('/close', methods=['POST'])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def close_signal():
    """Close an existing position"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'ticket' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: ticket'
            }), 400
        
        # Create close signal
        signal = TradeSignal(
            user_id=request.user_id,
            signal_type=SignalType.CLOSE_POSITION,
            symbol=data.get('symbol', ''),
            direction='',
            volume=0,
            ticket=int(data['ticket']),
            comment=data.get('comment', 'API close'),
            metadata={
                'source': 'flask_api',
                'close_reason': data.get('reason', 'manual')
            }
        )
        
        # Route the signal
        response = router.route_signal(
            signal=signal,
            terminal_type=TerminalType(data.get('terminal_type', 'press_pass'))
        )
        
        return jsonify({
            'success': response.success,
            'message': response.message,
            'ticket': data['ticket'],
            'timestamp': datetime.now().isoformat()
        }), 200 if response.success else 500
        
    except Exception as e:
        logger.error(f"Close endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/modify', methods=['POST'])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def modify_signal():
    """Modify an existing position's SL/TP"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'ticket' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: ticket'
            }), 400
        
        if 'stop_loss' not in data and 'take_profit' not in data:
            return jsonify({
                'success': False,
                'error': 'Must provide stop_loss or take_profit to modify'
            }), 400
        
        # Create modify signal
        signal = TradeSignal(
            user_id=request.user_id,
            signal_type=SignalType.MODIFY_POSITION,
            symbol=data.get('symbol', ''),
            direction='',
            volume=0,
            ticket=int(data['ticket']),
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
            comment=data.get('comment', 'API modify'),
            metadata={
                'source': 'flask_api',
                'modify_reason': data.get('reason', 'manual')
            }
        )
        
        # Route the signal
        response = router.route_signal(
            signal=signal,
            terminal_type=TerminalType(data.get('terminal_type', 'press_pass'))
        )
        
        return jsonify({
            'success': response.success,
            'message': response.message,
            'ticket': data['ticket'],
            'timestamp': datetime.now().isoformat()
        }), 200 if response.success else 500
        
    except Exception as e:
        logger.error(f"Modify endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/routing/info', methods=['GET'])
@require_auth
def get_routing_info():
    """Get routing information for the authenticated user"""
    try:
        routing_info = router.get_user_routing_info(request.user_id)
        return jsonify({
            'success': True,
            'data': routing_info
        }), 200
    except Exception as e:
        logger.error(f"Routing info error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get routing info'
        }), 500


@app.route('/routing/stats', methods=['GET'])
@require_auth
def get_routing_stats():
    """Get overall routing statistics (admin only)"""
    # In production, check if user has admin role
    try:
        stats = router.get_routing_statistics()
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500


@app.route('/terminal/health/<int:terminal_id>', methods=['GET'])
@require_auth
def get_terminal_health(terminal_id):
    """Get health status of a specific terminal"""
    try:
        health = router.get_terminal_health(terminal_id)
        return jsonify({
            'success': True,
            'data': health
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check terminal health'
        }), 500


@app.route('/terminal/failover/<int:terminal_id>', methods=['POST'])
@require_auth
def failover_terminal(terminal_id):
    """Initiate failover for a terminal (admin only)"""
    # In production, check if user has admin role
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Manual failover initiated')
        
        result = router.failover_terminal(terminal_id, reason)
        
        return jsonify({
            'success': result['success'],
            'data': result
        }), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Failover error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to initiate failover'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'fire-router-toc',
        'timestamp': datetime.now().isoformat()
    }), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# WebSocket support for real-time updates (requires flask-socketio)
try:
    from flask_socketio import SocketIO, emit, join_room, leave_room
    
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'data': 'Connected to Fire Router TOC'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('subscribe_user')
    def handle_subscribe(data):
        """Subscribe to updates for a specific user"""
        user_id = data.get('user_id')
        if user_id:
            join_room(f"user_{user_id}")
            emit('subscribed', {'user_id': user_id})
    
    @socketio.on('unsubscribe_user')
    def handle_unsubscribe(data):
        """Unsubscribe from user updates"""
        user_id = data.get('user_id')
        if user_id:
            leave_room(f"user_{user_id}")
            emit('unsubscribed', {'user_id': user_id})
    
    # Function to emit signal routing updates
    def emit_routing_update(user_id: str, update_data: Dict[str, Any]):
        """Emit routing update to subscribed clients"""
        socketio.emit('routing_update', update_data, room=f"user_{user_id}")
    
except ImportError:
    logger.warning("flask-socketio not installed, WebSocket support disabled")
    socketio = None


if __name__ == '__main__':
    # Development server
    if socketio:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)