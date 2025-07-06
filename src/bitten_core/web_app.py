"""
BITTEN Web Application
Serves landing page and handles Stripe webhooks
"""

from flask import Flask, render_template_string, send_from_directory, request, jsonify
import os
# from .stripe_webhook_endpoint import stripe_webhook
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Register Stripe webhook blueprint
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
    """Serve landing page"""
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

# Health check endpoint
@app.route('/health')
def health():
    """Health check for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'BITTEN',
        'version': '2.0'
    }), 200

# Stripe webhook is already registered via blueprint
# It will be available at /stripe/webhook

if __name__ == '__main__':
    # Run the app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)