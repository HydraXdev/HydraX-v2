#!/usr/bin/env python3
"""
BITTEN Webapp - Modular Architecture Entry Point
This is a refactored version that uses blueprints and modules
Run this alongside the original to test before switching
"""

import sys
import os
import logging

# Add webapp module to path
sys.path.insert(0, '/root/HydraX-v2')

# Import the app factory
from webapp import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the app
app, socketio = create_app()

# Add any remaining routes that haven't been moved to blueprints yet
@app.route('/')
def index():
    """Simple landing page"""
    return '''
    <html>
    <head><title>BITTEN System</title></head>
    <body style="background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 40px;">
        <h1 style="color: #ff0000;">🎯 BITTEN TACTICAL TRADING SYSTEM</h1>
        <p>Bot-Integrated Tactical Trading Engine/Network</p>
        <div style="margin-top: 30px;">
            <a href="/me" style="color: #00ff00;">→ Enter War Room</a><br>
            <a href="/hud" style="color: #00ff00;">→ Mission HUD</a><br>
            <a href="/api/signals" style="color: #00ff00;">→ Signal API</a><br>
            <a href="/healthz" style="color: #00ff00;">→ Health Check</a>
        </div>
    </body>
    </html>
    '''

@app.route('/hud')
def hud():
    """Mission HUD - simplified version"""
    mission_id = request.args.get('mission_id', 'NO_MISSION')
    user_id = request.args.get('user_id', '7176191872')
    
    return f'''
    <html>
    <head><title>BITTEN HUD</title></head>
    <body style="background: #0a0a0a; color: #00ff00; font-family: monospace; padding: 40px;">
        <h1 style="color: #ff0000;">🎯 MISSION HUD</h1>
        <div style="background: #1a1a1a; padding: 20px; border: 1px solid #00ff00;">
            <p>MISSION ID: {mission_id}</p>
            <p>OPERATIVE: {user_id}</p>
            <p>STATUS: READY</p>
            <button onclick="fire()" style="background: #ff0000; color: white; padding: 10px 20px; border: none; cursor: pointer;">
                🔫 FIRE
            </button>
        </div>
        <script>
        function fire() {{
            fetch('/api/fire', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'X-User-ID': '{user_id}'
                }},
                body: JSON.stringify({{mission_id: '{mission_id}'}})
            }})
            .then(r => r.json())
            .then(data => alert(data.message || data.error))
            .catch(e => alert('Fire failed: ' + e));
        }}
        </script>
    </body>
    </html>
    '''

# Import needed for HUD
from flask import request

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("BITTEN WEBAPP - MODULAR ARCHITECTURE")
    logger.info("Starting on port 8889 (test port)")
    logger.info("=" * 60)
    
    # Run on different port for testing
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=8889,  # Different port for testing
                 debug=False,
                 use_reloader=False,
                 allow_unsafe_werkzeug=True)