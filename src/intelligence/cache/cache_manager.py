"""
High-performance caching system for intelligence components
Supports multiple backends and provides real-time data access
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set, Callable
import asyncio
import json
import pickle
import hashlib
import time
from collections import OrderedDict
from enum import Enum, auto
import redis.asyncio as redis
from functools import wraps

from ..monitoring.logger import LoggerManager, timed_operation
from ..config.manager import CacheConfig

class CacheBackend(Enum):
    """Available cache backends"""
    MEMORY = auto()
    REDIS = auto()
    HYBRID = auto()  # Memory + Redis

@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    value: Any
    created_at: datetime
    ttl: int  # seconds
    hits: int = 0
    size: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl <= 0:
            return False
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl
        
    def time_to_live(self) -> float:
        """Get remaining TTL in seconds"""
        if self.ttl <= 0:
            return float('inf')
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return max(0, self.ttl - age)

class CacheStats:
    """Cache statistics"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
        self.total_size = 0
        
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'evictions': self.evictions,
            'hit_rate': self.hit_rate,
            'total_size': self.total_size
        }

class BaseCacheBackend(ABC):
    """Base class for cache backends"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.stats = CacheStats()
        self.logger = LoggerManager.get_logger(f"cache.{self.__class__.__name__}")
        
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
        
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries"""
        pass
        
    @abstractmethod
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern"""
        pass
        
    @abstractmethod
    async def size(self) -> int:
        """Get cache size in bytes"""
        pass
        
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first (more portable)
            return json.dumps(value).encode()
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
            
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)

class MemoryCacheBackend(BaseCacheBackend):
    """In-memory cache backend using LRU eviction"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_size = config.get('max_size', 1000)
        self.max_memory = config.get('max_memory', 100 * 1024 * 1024)  # 100MB
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self.stats.misses += 1
                return None
                
            if entry.is_expired():
                del self._cache[key]
                self.stats.misses += 1
                return None
                
            # Update LRU order
            self._cache.move_to_end(key)
            entry.hits += 1
            self.stats.hits += 1
            
            return entry.value
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        async with self._lock:
            # Serialize to get size
            serialized = self._serialize(value)
            size = len(serialized)
            
            # Check if we need to evict
            await self._evict_if_needed(size)
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                ttl=ttl or 0,
                size=size
            )
            
            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            self.stats.sets += 1
            self.stats.total_size += size
            
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self.stats.deletes += 1
                self.stats.total_size -= entry.size
                return True
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        async with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            return not entry.is_expired()
            
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self.stats.total_size = 0
            
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern"""
        async with self._lock:
            keys = list(self._cache.keys())
            
            if pattern:
                import fnmatch
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
                
            return keys
            
    async def size(self) -> int:
        """Get cache size in bytes"""
        return self.stats.total_size
        
    async def _evict_if_needed(self, new_size: int) -> None:
        """Evict entries if cache is full"""
        # Evict by count
        while len(self._cache) >= self.max_size:
            key, entry = self._cache.popitem(last=False)
            self.stats.evictions += 1
            self.stats.total_size -= entry.size
            
        # Evict by memory
        while self.stats.total_size + new_size > self.max_memory:
            if not self._cache:
                break
            key, entry = self._cache.popitem(last=False)
            self.stats.evictions += 1
            self.stats.total_size -= entry.size
            
        # Evict expired entries
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
                
        for key in expired_keys:
            entry = self._cache.pop(key)
            self.stats.evictions += 1
            self.stats.total_size -= entry.size

class RedisCacheBackend(BaseCacheBackend):
    """Redis cache backend"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._redis: Optional[redis.Redis] = None
        self._connected = False
        
    async def connect(self) -> None:
        """Connect to Redis"""
        if self._connected:
            return
            
        try:
            connection_params = self.config.get('connection_params', {})
            self._redis = await redis.from_url(
                connection_params.get('url', 'redis://localhost:6379'),
                decode_responses=False
            )
            
            # Test connection
            await self._redis.ping()
            self._connected = True
            self.logger.info("Connected to Redis")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._redis and self._connected:
            await self._redis.close()
            self._connected = False
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._connected:
            await self.connect()
            
        try:
            data = await self._redis.get(key)
            
            if data is None:
                self.stats.misses += 1
                return None
                
            self.stats.hits += 1
            return self._deserialize(data)
            
        except Exception as e:
            self.logger.error(f"Redis get error: {e}")
            self.stats.misses += 1
            return None
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if not self._connected:
            await self.connect()
            
        try:
            serialized = self._serialize(value)
            
            if ttl and ttl > 0:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
                
            self.stats.sets += 1
            
        except Exception as e:
            self.logger.error(f"Redis set error: {e}")
            raise
            
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._connected:
            await self.connect()
            
        try:
            result = await self._redis.delete(key)
            if result > 0:
                self.stats.deletes += 1
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Redis delete error: {e}")
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._connected:
            await self.connect()
            
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            self.logger.error(f"Redis exists error: {e}")
            return False
            
    async def clear(self) -> None:
        """Clear all cache entries"""
        if not self._connected:
            await self.connect()
            
        try:
            await self._redis.flushdb()
        except Exception as e:
            self.logger.error(f"Redis clear error: {e}")
            
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern"""
        if not self._connected:
            await self.connect()
            
        try:
            pattern = pattern or '*'
            keys = await self._redis.keys(pattern)
            return [k.decode() if isinstance(k, bytes) else k for k in keys]
        except Exception as e:
            self.logger.error(f"Redis keys error: {e}")
            return []
            
    async def size(self) -> int:
        """Get cache size in bytes"""
        if not self._connected:
            await self.connect()
            
        try:
            info = await self._redis.info('memory')
            return info.get('used_memory', 0)
        except Exception as e:
            self.logger.error(f"Redis size error: {e}")
            return 0

class HybridCacheBackend(BaseCacheBackend):
    """Hybrid cache using memory as L1 and Redis as L2"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # L1 cache (memory)
        memory_config = config.get('memory_config', {})
        self.l1_cache = MemoryCacheBackend(memory_config)
        
        # L2 cache (Redis)
        redis_config = config.get('redis_config', {})
        self.l2_cache = RedisCacheBackend(redis_config)
        
        # L1 TTL multiplier (L1 TTL = L2 TTL * multiplier)
        self.l1_ttl_multiplier = config.get('l1_ttl_multiplier', 0.1)
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (check L1 first, then L2)"""
        # Check L1
        value = await self.l1_cache.get(key)
        if value is not None:
            self.stats.hits += 1
            return value
            
        # Check L2
        value = await self.l2_cache.get(key)
        if value is not None:
            # Promote to L1
            await self.l1_cache.set(key, value, ttl=60)  # Short TTL for L1
            self.stats.hits += 1
            return value
            
        self.stats.misses += 1
        return None
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in both L1 and L2"""
        # Set in L2 (persistent)
        await self.l2_cache.set(key, value, ttl)
        
        # Set in L1 with shorter TTL
        l1_ttl = int(ttl * self.l1_ttl_multiplier) if ttl else 60
        await self.l1_cache.set(key, value, l1_ttl)
        
        self.stats.sets += 1
        
    async def delete(self, key: str) -> bool:
        """Delete from both caches"""
        l1_result = await self.l1_cache.delete(key)
        l2_result = await self.l2_cache.delete(key)
        
        if l1_result or l2_result:
            self.stats.deletes += 1
            return True
        return False
        
    async def exists(self, key: str) -> bool:
        """Check if key exists in either cache"""
        return await self.l1_cache.exists(key) or await self.l2_cache.exists(key)
        
    async def clear(self) -> None:
        """Clear both caches"""
        await self.l1_cache.clear()
        await self.l2_cache.clear()
        
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get keys from L2 (authoritative)"""
        return await self.l2_cache.keys(pattern)
        
    async def size(self) -> int:
        """Get total size of both caches"""
        l1_size = await self.l1_cache.size()
        l2_size = await self.l2_cache.size()
        return l1_size + l2_size

class CacheManager:
    """Main cache manager for intelligence system"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = LoggerManager.get_logger("cache.manager")
        self._backend: Optional[BaseCacheBackend] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize cache manager"""
        if self._initialized:
            return
            
        self.logger.info("Initializing cache manager")
        
        # Create backend based on config
        backend_type = self.config.backend.lower()
        
        if backend_type == 'memory':
            self._backend = MemoryCacheBackend(self.config.connection_params)
        elif backend_type == 'redis':
            self._backend = RedisCacheBackend(self.config.connection_params)
            await self._backend.connect()
        elif backend_type == 'hybrid':
            self._backend = HybridCacheBackend(self.config.connection_params)
            await self._backend.l2_cache.connect()
        else:
            raise ValueError(f"Unknown cache backend: {backend_type}")
            
        self._initialized = True
        self.logger.info(f"Cache manager initialized with {backend_type} backend")
        
    async def close(self) -> None:
        """Close cache manager"""
        if self._backend:
            if isinstance(self._backend, RedisCacheBackend):
                await self._backend.disconnect()
            elif isinstance(self._backend, HybridCacheBackend):
                await self._backend.l2_cache.disconnect()
                
    @timed_operation("cache_get")
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._initialized:
            await self.initialize()
        return await self._backend.get(key)
        
    @timed_operation("cache_set")
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if not self._initialized:
            await self.initialize()
            
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.config.ttl_default
            
        await self._backend.set(key, value, ttl)
        
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._initialized:
            await self.initialize()
        return await self._backend.delete(key)
        
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._initialized:
            await self.initialize()
        return await self._backend.exists(key)
        
    async def clear(self) -> None:
        """Clear all cache entries"""
        if not self._initialized:
            await self.initialize()
        await self._backend.clear()
        
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern"""
        if not self._initialized:
            await self.initialize()
        return await self._backend.keys(pattern)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._backend:
            return {}
        return self._backend.stats.to_dict()
        
    def generate_key(self, *args) -> str:
        """Generate cache key from arguments"""
        key_parts = [str(arg) for arg in args]
        return ':'.join(key_parts)
        
    def cache_key_hash(self, data: Any) -> str:
        """Generate hash-based cache key"""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()

def cached(ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Check if object has cache manager
            if not hasattr(self, 'cache_manager'):
                return await func(self, *args, **kwargs)
                
            # Generate cache key
            cache_key_parts = [key_prefix or func.__name__]
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ':'.join(cache_key_parts)
            
            # Try to get from cache
            cached_value = await self.cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
                
            # Call function
            result = await func(self, *args, **kwargs)
            
            # Cache result
            await self.cache_manager.set(cache_key, result, ttl)
            
            return result
            
        return wrapper
    return decorator