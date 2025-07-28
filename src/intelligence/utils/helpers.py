"""
Utility functions for the intelligence system
"""

import asyncio
from typing import Any, Dict, List, Optional, TypeVar, Callable, Union
from datetime import datetime, timedelta
import hashlib
import json
from functools import wraps
import time
from contextlib import asynccontextmanager

T = TypeVar('T')

def get_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()

def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string"""
    return dt.isoformat() + 'Z'

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string"""
    # Remove 'Z' if present
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1]
    return datetime.fromisoformat(timestamp_str)

def calculate_hash(data: Any) -> str:
    """Calculate SHA256 hash of data"""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    elif not isinstance(data, (str, bytes)):
        data = str(data)
        
    if isinstance(data, str):
        data = data.encode('utf-8')
        
    return hashlib.sha256(data).hexdigest()

def batch_items(items: List[T], batch_size: int) -> List[List[T]]:
    """Split items into batches"""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches

async def retry_async(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_backoff: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """Retry async function with exponential backoff"""
    delay = 1.0
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise
                
            # Calculate next delay
            delay = min(delay * backoff_factor, max_backoff)
            
            # Add jitter
            jitter = delay * 0.1
            actual_delay = delay + (asyncio.get_event_loop().time() % jitter)
            
            await asyncio.sleep(actual_delay)

def rate_limit(calls_per_second: float):
    """Decorator for rate limiting function calls"""
    min_interval = 1.0 / calls_per_second
    last_called = {}
    lock = asyncio.Lock()
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with lock:
                key = id(func)
                now = time.time()
                
                if key in last_called:
                    elapsed = now - last_called[key]
                    if elapsed < min_interval:
                        await asyncio.sleep(min_interval - elapsed)
                        
                last_called[key] = time.time()
                
            return await func(*args, **kwargs)
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = id(func)
            now = time.time()
            
            if key in last_called:
                elapsed = now - last_called[key]
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                    
            last_called[key] = time.time()
            
            return func(*args, **kwargs)
            
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
    return decorator

class AsyncThrottle:
    """Async throttle for limiting concurrent operations"""
    
    def __init__(self, max_concurrent: int):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
    @asynccontextmanager
    async def acquire(self):
        """Acquire throttle slot"""
        async with self._semaphore:
            yield

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
                
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
            
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
        
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'closed'
        
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
            
    return result

def truncate_string(s: str, max_length: int, suffix: str = '...') -> str:
    """Truncate string to max length"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix

def format_number(num: Union[int, float], decimals: int = 2) -> str:
    """Format number with thousand separators"""
    if isinstance(num, float):
        return f"{num:,.{decimals}f}"
    return f"{num:}"

def time_window_key(timestamp: datetime, window_minutes: int) -> str:
    """Generate time window key for grouping"""
    window_start = timestamp.replace(
        minute=(timestamp.minute // window_minutes) * window_minutes,
        second=0,
        microsecond=0
    )
    return window_start.isoformat()

async def parallel_map(
    func: Callable[[T], Any],
    items: List[T],
    max_concurrent: int = 10
) -> List[Any]:
    """Map function over items with concurrency limit"""
    throttle = AsyncThrottle(max_concurrent)
    
    async def process_item(item):
        async with throttle.acquire():
            return await func(item)
            
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove invalid characters
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
        
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:max_length - len(ext) - 1] + '.' + ext if ext else name[:max_length]
        
    return filename

class ExpiringDict:
    """Dictionary with expiring entries"""
    
    def __init__(self, default_ttl: int = 3600):
        self._data: Dict[str, tuple] = {}
        self.default_ttl = default_ttl
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value with TTL"""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self._data[key] = (value, expiry)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value if not expired"""
        if key not in self._data:
            return default
            
        value, expiry = self._data[key]
        if time.time() > expiry:
            del self._data[key]
            return default
            
        return value
        
    def cleanup(self) -> None:
        """Remove expired entries"""
        now = time.time()
        expired_keys = [k for k, (_, expiry) in self._data.items() if now > expiry]
        for key in expired_keys:
            del self._data[key]
            
    def __len__(self) -> int:
        """Get number of non-expired entries"""
        self.cleanup()
        return len(self._data)