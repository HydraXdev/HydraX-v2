# webhook_server.py
# BITTEN Telegram Webhook Server

import json
import os
from flask import Flask, request, jsonify
from typing import Dict, Any

from .bitten_core import BittenCore

class WebhookServer:
    """Telegram webhook server for BITTEN"""
    
    def __init__(self, bitten_core: BittenCore = None):
        self.app = Flask(__name__)
        self.bitten_core = bitten_core or BittenCore()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            """Handle Telegram webhook updates"""
            try:
                update_data = request.get_json()
                
                if not update_data:
                    return jsonify({'success': False, 'error': 'No data received'}), 400
                
                # Process update through BITTEN core
                result = self.bitten_core.process_telegram_update(update_data)
                
                return jsonify(result)
                
            except Exception as e:
                print(f"[WEBHOOK ERROR] {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'BITTEN Trading Operations Center',
                'version': '1.0.0'
            })
        
        @self.app.route('/stats', methods=['GET'])
        def stats():
            """System statistics endpoint"""
            try:
                stats = self.bitten_core.get_core_stats()
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def run(self, host='127.0.0.1', port=9001, debug=False):
        """Run the webhook server"""
        print(f"🤖 BITTEN Webhook Server starting on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point"""
    # Initialize BITTEN core
    bitten_core = BittenCore()
    
    # Create webhook server
    server = WebhookServer(bitten_core)
    
    # Get configuration from environment
    host = os.getenv('WEBHOOK_HOST', '127.0.0.1')
    port = int(os.getenv('WEBHOOK_PORT', '9001'))
    debug = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    # Start server
    server.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()