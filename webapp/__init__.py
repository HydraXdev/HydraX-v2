"""
BITTEN Webapp - Modular Architecture
Main application initialization
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO

# Add parent directory to path for imports
sys.path.insert(0, '/root/HydraX-v2')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='/root/HydraX-v2/templates',  # Use existing templates directory
                static_folder='/root/HydraX-v2/src/ui')
    
    # Configure app
    app.config.update({
        'SECRET_KEY': os.environ.get('FLASK_SECRET_KEY', 'bitten-secret-key-2025'),
        'DEBUG': False,
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max request size
        'SEND_FILE_MAX_AGE_DEFAULT': 31536000,   # 1 year cache for static files
    })
    
    # Initialize SocketIO with optimizations
    socketio = SocketIO(app, 
                       cors_allowed_origins="*",
                       async_mode='threading',
                       logger=False,
                       engineio_logger=False,
                       ping_timeout=60,
                       ping_interval=25,
                       max_http_buffer_size=1000000)
    
    # Store socketio reference
    app.socketio = socketio
    
    # Register blueprints
    register_blueprints(app)
    
    return app, socketio

def register_blueprints(app):
    """Register all route blueprints"""
    # Import blueprints
    from webapp.blueprints.health import health_bp
    from webapp.blueprints.signals import signals_bp
    from webapp.blueprints.fire import fire_bp
    from webapp.blueprints.user import user_bp
    from webapp.blueprints.hud import hud_bp
    
    # Register with app
    app.register_blueprint(health_bp)
    app.register_blueprint(signals_bp)
    app.register_blueprint(fire_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(hud_bp)
    
    logger.info("✅ All blueprints registered")