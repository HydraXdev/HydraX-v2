#!/usr/bin/env python3
"""
🔗 CONNECTION MANAGER - Redundant connections for critical services
"""

import time
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage redundant connections with failover"""
    
    def __init__(self):
        self.connections = {}
        self.fallback_handlers = {}
    
    def register_fallback(self, service: str, handler: Callable):
        """Register fallback handler for service"""
        self.fallback_handlers[service] = handler
    
    def with_fallback(self, service: str, max_retries: int = 3, delay: float = 1.0):
        """Decorator for automatic failover"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"{service} attempt {attempt + 1} failed: {e}")
                        
                        if attempt < max_retries - 1:
                            time.sleep(delay * (2 ** attempt))  # Exponential backoff
                
                # All retries failed, try fallback
                if service in self.fallback_handlers:
                    logger.info(f"Using fallback handler for {service}")
                    try:
                        return self.fallback_handlers[service](*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed for {service}: {fallback_error}")
                
                # Re-raise the last exception
                raise last_exception
            
            return wrapper
        return decorator

# Global connection manager
connection_manager = ConnectionManager()

# Telegram fallback
def telegram_fallback(*args, **kwargs):
    """Fallback for Telegram failures"""
    logger.info("Telegram service unavailable - logging message locally")
    with open('/root/HydraX-v2/logs/telegram_fallback.log', 'a') as f:
        f.write(f"{time.time()}: Telegram message failed - {args} {kwargs}\n")

# WebApp fallback  
def webapp_fallback(*args, **kwargs):
    """Fallback for WebApp failures"""
    logger.info("WebApp service unavailable - using minimal response")
    return {"status": "service_unavailable", "message": "Please try again later"}

# Register fallbacks
connection_manager.register_fallback('telegram', telegram_fallback)
connection_manager.register_fallback('webapp', webapp_fallback)
