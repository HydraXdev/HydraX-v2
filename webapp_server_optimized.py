#!/usr/bin/env python3
"""
Optimized Flask server with lazy loading and consolidated imports
Reduced memory footprint and improved performance
"""

import os
import sys
import json
import logging
from datetime import datetime

# Core Flask imports (always needed)
from flask import Flask, render_template_string, request, jsonify, redirect
from flask_socketio import SocketIO

# Load environment early
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy import manager
class LazyImports:
    """Manages lazy loading of heavy modules to reduce memory usage"""
    
    def __init__(self):
        self._stripe = None
        self._signal_storage = None
        self._engagement_db = None
        self._mission_api = None
        self._press_pass_api = None
        self._referral_system = None
        self._live_trade_api = None
        self._timer_integration = None
    
    @property
    def stripe(self):
        if self._stripe is None:
            import stripe
            self._stripe = stripe
            logger.info("Stripe module loaded")
        return self._stripe
    
    @property
    def signal_storage(self):
        if self._signal_storage is None:
            try:
                from signal_storage import get_latest_signal, get_active_signals, get_signal_by_id
                self._signal_storage = {
                    'get_latest_signal': get_latest_signal,
                    'get_active_signals': get_active_signals,
                    'get_signal_by_id': get_signal_by_id
                }
                logger.info("Signal storage loaded")
            except ImportError as e:
                logger.warning(f"Signal storage not available: {e}")
                self._signal_storage = {}
        return self._signal_storage
    
    @property
    def engagement_db(self):
        if self._engagement_db is None:
            try:
                from engagement_db import handle_fire_action, get_signal_stats, get_user_stats
                self._engagement_db = {
                    'handle_fire_action': handle_fire_action,
                    'get_signal_stats': get_signal_stats,
                    'get_user_stats': get_user_stats
                }
                logger.info("Engagement DB loaded")
            except ImportError as e:
                logger.warning(f"Engagement DB not available: {e}")
                self._engagement_db = {}
        return self._engagement_db
    
    @property
    def referral_system(self):
        if self._referral_system is None:
            try:
                from standalone_referral_system import StandaloneReferralSystem
                self._referral_system = StandaloneReferralSystem()
                logger.info("Referral system loaded")
            except ImportError as e:
                logger.warning(f"Referral system not available: {e}")
                self._referral_system = None
        return self._referral_system

# Global lazy imports instance
lazy = LazyImports()

# Create Flask app with optimized config
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'bitten-tactical-2025'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max upload
    'SEND_FILE_MAX_AGE_DEFAULT': 31536000,   # 1 year cache for static files
})

# Initialize SocketIO with optimized settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,  # Disable socketio logging to reduce overhead
    engineio_logger=False
)

# Basic routes with lazy loading
@app.route('/')
def index():
    """Main entry point with minimal memory usage"""
    try:
        # Only load signal storage if needed
        if 'signals' in request.args:
            signals = lazy.signal_storage.get('get_active_signals', lambda: [])()
        else:
            signals = []
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BITTEN - Tactical Trading HUD</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <div id="bitten-hud">
                <h1>🎯 BITTEN TACTICAL TRADING HUD</h1>
                <div id="signals-container">
                    {% for signal in signals %}
                    <div class="signal-card">{{ signal }}</div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        """, signals=signals)
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return "BITTEN HUD - Loading...", 200

@app.route('/api/signals')
def api_signals():
    """API endpoint with lazy loading"""
    try:
        get_signals = lazy.signal_storage.get('get_active_signals')
        if get_signals:
            signals = get_signals()
            return jsonify({'signals': signals, 'count': len(signals)})
        else:
            return jsonify({'error': 'Signal system not available'}), 503
    except Exception as e:
        logger.error(f"Signals API error: {e}")
        return jsonify({'error': 'Signal retrieval failed'}), 500

@app.route('/api/health')
def health_check():
    """Lightweight health check"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'version': '2.1',
        'memory_optimized': True
    })

# SocketIO events with lazy loading
@socketio.on('connect')
def handle_connect():
    """Handle client connections"""
    logger.info(f"Client connected: {request.sid}")
    socketio.emit('status', {'connected': True, 'server': 'BITTEN-OPTIMIZED'})

@socketio.on('get_signals')
def handle_get_signals():
    """Handle signal requests via WebSocket"""
    try:
        get_signals = lazy.signal_storage.get('get_active_signals')
        if get_signals:
            signals = get_signals()
            socketio.emit('signals_update', {'signals': signals})
        else:
            socketio.emit('error', {'message': 'Signal system unavailable'})
    except Exception as e:
        logger.error(f"WebSocket signals error: {e}")
        socketio.emit('error', {'message': 'Signal retrieval failed'})

# Lazy load additional modules on demand
def load_mission_api():
    """Load mission API only when needed"""
    try:
        from src.api.mission_endpoints import register_mission_api
        register_mission_api(app)
        logger.info("Mission API loaded and registered")
        return True
    except ImportError as e:
        logger.warning(f"Mission API not available: {e}")
        return False

def load_press_pass_api():
    """Load press pass API only when needed"""
    try:
        from src.api.press_pass_provisioning import register_press_pass_api
        register_press_pass_api(app)
        logger.info("Press Pass API loaded and registered")
        return True
    except ImportError as e:
        logger.warning(f"Press Pass API not available: {e}")
        return False

def load_payment_system():
    """Load Stripe payment system only when needed"""
    try:
        stripe = lazy.stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        logger.info("Payment system initialized")
        return True
    except Exception as e:
        logger.warning(f"Payment system not available: {e}")
        return False

# Route to trigger module loading
@app.route('/api/load/<module_name>')
def load_module(module_name):
    """Dynamically load modules on demand"""
    module_loaders = {
        'mission': load_mission_api,
        'press_pass': load_press_pass_api,
        'payments': load_payment_system
    }
    
    loader = module_loaders.get(module_name)
    if loader:
        success = loader()
        return jsonify({
            'module': module_name,
            'loaded': success,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': f'Unknown module: {module_name}'}), 400

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Development/Debug routes
if os.getenv('FLASK_ENV') == 'development':
    @app.route('/debug/memory')
    def debug_memory():
        """Debug endpoint to check memory usage"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return jsonify({
            'memory_rss': f"{memory_info.rss / 1024 / 1024:.1f} MB",
            'memory_vms': f"{memory_info.vms / 1024 / 1024:.1f} MB",
            'cpu_percent': process.cpu_percent(),
            'loaded_modules': {
                'stripe': lazy._stripe is not None,
                'signal_storage': lazy._signal_storage is not None,
                'engagement_db': lazy._engagement_db is not None,
                'referral_system': lazy._referral_system is not None
            }
        })

if __name__ == '__main__':
    # Production-ready configuration
    host = os.getenv('WEBAPP_HOST', '0.0.0.0')
    port = int(os.getenv('WEBAPP_PORT', 8888))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting BITTEN WebApp Server (Optimized)")
    logger.info(f"📍 Host: {host}:{port}")
    logger.info(f"🔧 Debug Mode: {debug_mode}")
    logger.info(f"💾 Lazy Loading: Enabled")
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            use_reloader=False,  # Disable reloader for production
            log_output=False if not debug_mode else True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)