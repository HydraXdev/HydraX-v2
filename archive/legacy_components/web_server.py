#!/usr/bin/env python3
"""
BITTEN Web Server - Simple standalone version
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'bitten-secret-key-change-in-production')

# Serve landing pages
@app.route('/')
def index():
    """Serve landing page"""
    return send_from_directory('landing', 'index.html')

@app.route('/terms')
def terms():
    """Serve terms of service"""
    return send_from_directory('landing', 'terms.html')

@app.route('/privacy')
def privacy():
    """Serve privacy policy"""
    return send_from_directory('landing', 'privacy.html')

@app.route('/refund')
def refund():
    """Serve refund policy"""
    return send_from_directory('landing', 'refund.html')

# Health check endpoint
@app.route('/health')
def health():
    """Health check for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'BITTEN',
        'version': '2.0'
    }), 200

# Stripe webhook endpoint
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    # Log the webhook
    logger.info(f"Received Stripe webhook")
    
    # TODO: Process webhook events here
    # For now, just acknowledge receipt
    
    return jsonify({'received': True}), 200

if __name__ == '__main__':
    # Run the app
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting BITTEN web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)