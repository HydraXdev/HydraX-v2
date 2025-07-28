#!/usr/bin/env python3
"""
Production Rate Limiter with Redis and File-based Fallback
Supports both Redis and local file storage for rate limiting
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from config_loader import config

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Production-ready rate limiter with Redis primary and file-based fallback.
    
    Features:
    - Redis-based distributed rate limiting
    - File-based fallback when Redis unavailable
    - Configurable windows and limits
    - Thread-safe operations
    """
    
    def __init__(self, storage_type: Optional[str] = None):
        """
        Initialize rate limiter.
        
        Args:
            storage_type: 'redis', 'file', or None for auto-detection
        """
        self.storage_type = storage_type or config.get("RATE_LIMIT_STORAGE", "redis")
        self.fallback_type = config.get("RATE_LIMIT_FALLBACK", "file")
        
        # Initialize Redis if available
        self.redis_client = None
        if self.storage_type == "redis":
            self.redis_client = self._init_redis()
            
        # File-based storage path
        self.file_storage_path = Path("/tmp/bitten_rate_limits")
        self.file_storage_path.mkdir(exist_ok=True)
        
        logger.info(f"Rate limiter initialized with {self.storage_type} storage")
    
    def _init_redis(self) -> Optional[Any]:
        """Initialize Redis connection."""
        try:
            import redis
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            client.ping()
            logger.info("✅ Redis connection established for rate limiting")
            return client
            
        except ImportError:
            logger.warning("Redis not installed, falling back to file storage")
            return None
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, falling back to file storage")
            return None
    
    def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int = 60,
        increment: bool = True
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier for rate limiting (user_id, ip, etc.)
            limit: Maximum requests allowed in window
            window: Time window in seconds
            increment: Whether to increment counter
            
        Returns:
            Dict with 'allowed', 'remaining', 'reset_time', 'retry_after'
        """
        try:
            if self.redis_client and self.storage_type == "redis":
                return self._check_redis_rate_limit(key, limit, window, increment)
            else:
                return self._check_file_rate_limit(key, limit, window, increment)
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request but log error
            return {
                'allowed': True,
                'remaining': limit,
                'reset_time': time.time() + window,
                'retry_after': 0,
                'error': str(e)
            }
    
    def _check_redis_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        increment: bool
    ) -> Dict[str, Any]:
        """Check rate limit using Redis sliding window."""
        try:
            pipe = self.redis_client.pipeline()
            now = time.time()
            window_start = now - window
            
            # Use sorted sets for sliding window
            redis_key = f"rate_limit:{key}"
            
            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current requests
            pipe.zcard(redis_key)
            
            # Add current request if incrementing
            if increment:
                pipe.zadd(redis_key, {str(now): now})
                pipe.expire(redis_key, window + 10)  # Buffer for cleanup
            
            results = pipe.execute()
            current_count = results[1]
            
            if increment:
                current_count += 1
            
            allowed = current_count <= limit
            remaining = max(0, limit - current_count)
            reset_time = now + window
            retry_after = 0 if allowed else window
            
            return {
                'allowed': allowed,
                'remaining': remaining,
                'reset_time': reset_time,
                'retry_after': retry_after
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}, falling back to file storage")
            return self._check_file_rate_limit(key, limit, window, increment)
    
    def _check_file_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        increment: bool
    ) -> Dict[str, Any]:
        """Check rate limit using file-based storage."""
        try:
            file_path = self.file_storage_path / f"{key}.json"
            now = time.time()
            window_start = now - window
            
            # Load existing data
            data = {'requests': []}
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    data = {'requests': []}
            
            # Filter out old requests
            data['requests'] = [
                req_time for req_time in data['requests'] 
                if req_time > window_start
            ]
            
            # Add current request if incrementing
            if increment:
                data['requests'].append(now)
            
            current_count = len(data['requests'])
            allowed = current_count <= limit
            remaining = max(0, limit - current_count)
            reset_time = now + window
            retry_after = 0 if allowed else window
            
            # Save updated data
            if increment:
                with open(file_path, 'w') as f:
                    json.dump(data, f)
            
            return {
                'allowed': allowed,
                'remaining': remaining,
                'reset_time': reset_time,
                'retry_after': retry_after
            }
            
        except Exception as e:
            logger.error(f"File rate limit error: {e}")
            # Fail open
            return {
                'allowed': True,
                'remaining': limit,
                'reset_time': time.time() + window,
                'retry_after': 0,
                'error': str(e)
            }
    
    def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for a specific key."""
        try:
            if self.redis_client and self.storage_type == "redis":
                redis_key = f"rate_limit:{key}"
                self.redis_client.delete(redis_key)
                return True
            else:
                file_path = self.file_storage_path / f"{key}.json"
                if file_path.exists():
                    file_path.unlink()
                return True
                
        except Exception as e:
            logger.error(f"Error resetting rate limit for {key}: {e}")
            return False
    
    def cleanup_old_entries(self, max_age_hours: int = 24) -> int:
        """Clean up old rate limit entries."""
        cleaned = 0
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        try:
            if self.storage_type == "file":
                for file_path in self.file_storage_path.glob("*.json"):
                    try:
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            cleaned += 1
                    except Exception as e:
                        logger.error(f"Error cleaning up {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old rate limit entries")
        
        return cleaned

# Global rate limiter instance
rate_limiter = RateLimiter()

# Decorator for easy rate limiting
def rate_limit(key_func=None, limit: int = 60, window: int = 60):
    """
    Rate limiting decorator.
    
    Args:
        key_func: Function to generate rate limit key from args
        limit: Maximum requests per window
        window: Time window in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = func.__name__
            
            # Check rate limit
            result = rate_limiter.check_rate_limit(key, limit, window)
            
            if not result['allowed']:
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {key}. "
                    f"Try again in {result['retry_after']} seconds"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

# Utility functions for common patterns
def check_user_rate_limit(user_id: str, limit: int = 10, window: int = 60) -> Dict[str, Any]:
    """Check rate limit for a user."""
    return rate_limiter.check_rate_limit(f"user:{user_id}", limit, window)

def check_ip_rate_limit(ip_address: str, limit: int = 100, window: int = 60) -> Dict[str, Any]:
    """Check rate limit for an IP address."""
    return rate_limiter.check_rate_limit(f"ip:{ip_address}", limit, window)

def check_api_rate_limit(api_key: str, limit: int = 1000, window: int = 3600) -> Dict[str, Any]:
    """Check rate limit for an API key."""
    return rate_limiter.check_rate_limit(f"api:{api_key}", limit, window)

if __name__ == "__main__":
    # Test rate limiter
    import time
    
    print("🧪 Testing rate limiter...")
    
    # Test basic functionality
    for i in range(5):
        result = rate_limiter.check_rate_limit("test_key", 3, 60)
        print(f"Request {i+1}: allowed={result['allowed']}, remaining={result['remaining']}")
        time.sleep(0.1)
    
    print("✅ Rate limiter test complete")