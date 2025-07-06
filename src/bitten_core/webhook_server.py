# webhook_server.py
# BITTEN Telegram Webhook Server

import json
import os
from flask import Flask, request, jsonify
from typing import Dict, Any

from .bitten_core import BittenCore
from .risk_management import RiskManager
from .news_scheduler import NewsScheduler
from .webhook_security import (
    verify_webhook_token, verify_telegram_signature, rate_limit,
    validate_request_size, add_security_headers, validate_json_request
)

class WebhookServer:
    """Telegram webhook server for BITTEN"""
    
    def __init__(self, bitten_core: BittenCore = None, risk_manager: RiskManager = None):
        self.app = Flask(__name__)
        self.bitten_core = bitten_core or BittenCore()
        self.risk_manager = risk_manager or RiskManager()
        self.news_scheduler = NewsScheduler(self.risk_manager)
        
        # Link webhook server to bitten_core
        self.bitten_core.webhook_server = self
        
        self.setup_routes()
        self.setup_security()
        
        # Start news scheduler
        self.news_scheduler.start()
    
    def setup_security(self):
        """Setup security middleware"""
        @self.app.after_request
        def apply_security_headers(response):
            return add_security_headers(response)
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            # Log the actual error but don't expose it
            self.app.logger.error(f"Internal error: {error}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/webhook', methods=['POST'])
        @verify_telegram_signature
        @rate_limit(max_requests=30, window=60)  # 30 requests per minute
        @validate_request_size(max_size=1024 * 1024)  # 1MB max
        @validate_json_request
        def webhook():
            """Handle Telegram webhook updates"""
            try:
                # Use sanitized data
                update_data = request.sanitized_json
                
                # Process update through BITTEN core
                result = self.bitten_core.process_telegram_update(update_data)
                
                return jsonify(result)
                
            except Exception as e:
                self.app.logger.error(f"Webhook processing error: {e}")
                # Don't expose internal errors
                return jsonify({'success': False, 'error': 'Processing failed'}), 500
        
        @self.app.route('/health', methods=['GET'])
        @rate_limit(max_requests=60, window=60)  # 60 requests per minute
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'BITTEN Trading Operations Center',
                'version': '1.0.0'
            })
        
        @self.app.route('/stats', methods=['GET'])
        @verify_webhook_token
        @rate_limit(max_requests=20, window=60)
        def stats():
            """System statistics endpoint"""
            try:
                stats = self.bitten_core.get_core_stats()
                return jsonify(stats)
            except Exception as e:
                self.app.logger.error(f"Stats error: {e}")
                return jsonify({'error': 'Failed to retrieve stats'}), 500
        
        @self.app.route('/news', methods=['GET'])
        @verify_webhook_token
        @rate_limit(max_requests=20, window=60)
        def news():
            """Get news events status"""
            try:
                # Get scheduler status
                status = self.news_scheduler.get_status()
                
                # Get upcoming events
                upcoming = self.news_scheduler.get_upcoming_events(hours=48)
                events_data = [
                    {
                        'time': event.event_time.isoformat(),
                        'currency': event.currency,
                        'impact': event.impact.value,
                        'name': event.event_name,
                        'forecast': event.forecast,
                        'previous': event.previous
                    }
                    for event in upcoming
                ]
                
                return jsonify({
                    'scheduler': status,
                    'upcoming_events': events_data,
                    'total_events': len(events_data)
                })
            except Exception as e:
                self.app.logger.error(f"News endpoint error: {e}")
                return jsonify({'error': 'Failed to retrieve news data'}), 500
    
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