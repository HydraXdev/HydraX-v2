"""
Webhook Security Module

Provides authentication, rate limiting, and security headers for the webhook server.
"""

import hmac
import hashlib
import time
import os
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, Dict[str, any]] = {}

def verify_webhook_token(f: Callable) -> Callable:
    """Decorator to verify webhook authentication token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header or query parameter
        auth_token = request.headers.get('X-Webhook-Token') or request.args.get('token')
        expected_token = os.getenv('WEBHOOK_AUTH_TOKEN')
        
        if not expected_token:
            logger.error("WEBHOOK_AUTH_TOKEN not configured")
            return jsonify({'error': 'Server configuration error'}), 500
        
        if not auth_token or not hmac.compare_digest(auth_token, expected_token):
            logger.warning(f"Unauthorized webhook access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def verify_telegram_signature(f: Callable) -> Callable:
    """Decorator to verify Telegram webhook signatures"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get bot token
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return jsonify({'error': 'Server configuration error'}), 500
        
        # Telegram sends a secret token in header for webhook verification
        secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        expected_token = os.getenv('TELEGRAM_WEBHOOK_SECRET')
        
        if expected_token and secret_token != expected_token:
            logger.warning(f"Invalid Telegram signature from {request.remote_addr}")
            return jsonify({'error': 'Invalid signature'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests: int = 10, window: int = 60) -> Callable:
    """Rate limiting decorator
    
    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP address or user ID)
            client_id = request.headers.get('X-Forwarded-For', request.remote_addr)
            current_time = time.time()
            
            # Initialize client storage if needed
            if client_id not in rate_limit_storage:
                rate_limit_storage[client_id] = {
                    'requests': [],
                    'blocked_until': 0
                }
            
            client_data = rate_limit_storage[client_id]
            
            # Check if client is blocked
            if current_time < client_data['blocked_until']:
                remaining = int(client_data['blocked_until'] - current_time)
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': remaining
                }), 429
            
            # Clean old requests outside the window
            client_data['requests'] = [
                req_time for req_time in client_data['requests']
                if current_time - req_time < window
            ]
            
            # Check rate limit
            if len(client_data['requests']) >= max_requests:
                client_data['blocked_until'] = current_time + window
                logger.warning(f"Rate limit exceeded for {client_id}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window
                }), 429
            
            # Add current request
            client_data['requests'].append(current_time)
            
            # Clean up old entries periodically
            if len(rate_limit_storage) > 1000:
                _cleanup_rate_limit_storage()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def _cleanup_rate_limit_storage():
    """Clean up old rate limit entries"""
    current_time = time.time()
    to_delete = []
    
    for client_id, data in rate_limit_storage.items():
        # Remove entries with no recent requests
        if not data['requests'] or all(current_time - req > 3600 for req in data['requests']):
            to_delete.append(client_id)
    
    for client_id in to_delete:
        del rate_limit_storage[client_id]

def validate_request_size(max_size: int = 1024 * 1024) -> Callable:
    """Decorator to validate request size"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.content_length and request.content_length > max_size:
                return jsonify({'error': 'Request too large'}), 413
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def add_security_headers(response):
    """Add security headers to response"""
    # Prevent content type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Force HTTPS
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Remove server header
    response.headers.pop('Server', None)
    
    return response

def sanitize_input(data: any, max_length: int = 1000) -> any:
    """Sanitize input data to prevent injection attacks"""
    if isinstance(data, str):
        # Remove any potential HTML/script tags
        import re
        data = re.sub(r'<[^>]+>', '', data)
        # Limit length
        data = data[:max_length]
        # Remove null bytes
        data = data.replace('\x00', '')
        # Normalize whitespace
        data = ' '.join(data.split())
    elif isinstance(data, dict):
        return {k: sanitize_input(v, max_length) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item, max_length) for item in data]
    
    return data

def validate_json_request(f: Callable) -> Callable:
    """Decorator to validate JSON requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        try:
            data = request.get_json(force=True)
            if not data:
                return jsonify({'error': 'Empty request body'}), 400
                
            # Sanitize input
            request.sanitized_json = sanitize_input(data)
            
        except Exception as e:
            logger.error(f"Invalid JSON in request: {e}")
            return jsonify({'error': 'Invalid JSON'}), 400
        
        return f(*args, **kwargs)
    return decorated_function