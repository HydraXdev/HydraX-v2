"""
Exchange Manager

Handles connections to multiple exchanges with rate limiting and fallback strategies.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from collections import defaultdict
import logging
from datetime import datetime, timedelta
import aiohttp
import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float
    requests_per_minute: int
    weight_per_request: int = 1
    burst_capacity: int = 10

@dataclass
class ExchangeConfig:
    """Configuration for an exchange"""
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None  # For exchanges like Coinbase
    testnet: bool = False
    rate_limits: Optional[RateLimitConfig] = None
    custom_options: Dict[str, Any] = None

class RateLimiter:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_capacity
        self.last_update = time.time()
        self.minute_requests = defaultdict(int)
        self.lock = asyncio.Lock()
    
    async def acquire(self, weight: int = 1):
        """Acquire permission to make a request"""
        async with self.lock:
            now = time.time()
            
            # Refill tokens based on time passed
            time_passed = now - self.last_update
            new_tokens = time_passed * self.config.requests_per_second
            self.tokens = min(self.config.burst_capacity, self.tokens + new_tokens)
            self.last_update = now
            
            # Check minute limit
            current_minute = int(now // 60)
            self.minute_requests[current_minute] += weight
            
            # Clean old minute entries
            cutoff = current_minute - 2
            self.minute_requests = defaultdict(int, {
                k: v for k, v in self.minute_requests.items() if k > cutoff
            })
            
            # Check if we exceed minute limit
            if self.minute_requests[current_minute] > self.config.requests_per_minute:
                wait_time = 60 - (now % 60)
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                return await self.acquire(weight)
            
            # Check token bucket
            if self.tokens < weight:
                wait_time = (weight - self.tokens) / self.config.requests_per_second
                logger.debug(f"Rate limiting, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                return await self.acquire(weight)
            
            self.tokens -= weight

class ExchangeConnection:
    """Manages a single exchange connection with rate limiting"""
    
    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.exchange = None
        self.rate_limiter = RateLimiter(config.rate_limits) if config.rate_limits else None
        self.connected = False
        self.last_error = None
        self.error_count = 0
        self.backoff_until = None
    
    async def connect(self):
        """Initialize exchange connection"""
        try:
            exchange_class = getattr(ccxt, self.config.name)
            
            options = {
                'apiKey': self.config.api_key,
                'secret': self.config.api_secret,
                'enableRateLimit': True}
            
            if self.config.passphrase:
                options['password'] = self.config.passphrase
            
            if self.config.testnet:
                options['test'] = True
            
            if self.config.custom_options:
                options.update(self.config.custom_options)
            
            self.exchange = exchange_class(options)
            
            # Test connection
            await self.exchange.load_markets()
            self.connected = True
            self.error_count = 0
            logger.info(f"Connected to {self.config.name}")
            
        except Exception as e:
            self.last_error = e
            self.error_count += 1
            logger.error(f"Failed to connect to {self.config.name}: {e}")
            raise
    
    async def disconnect(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            self.connected = False
    
    async def execute_with_retry(self, func: Callable, *args, max_retries: int = 3, **kwargs):
        """Execute a function with retry logic and rate limiting"""
        
        # Check if we're in backoff period
        if self.backoff_until and datetime.now() < self.backoff_until:
            wait_time = (self.backoff_until - datetime.now()).total_seconds()
            await asyncio.sleep(wait_time)
        
        for attempt in range(max_retries):
            try:
                # Apply rate limiting
                if self.rate_limiter:
                    await self.rate_limiter.acquire()
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Reset error tracking on success
                self.error_count = 0
                self.backoff_until = None
                
                return result
                
            except ccxt.RateLimitExceeded as e:
                # Exponential backoff for rate limit errors
                wait_time = min(300, 2 ** attempt * 10)  # Max 5 minutes
                logger.warning(f"Rate limit exceeded on {self.config.name}, waiting {wait_time}s")
                self.backoff_until = datetime.now() + timedelta(seconds=wait_time)
                await asyncio.sleep(wait_time)
                
            except ccxt.NetworkError as e:
                # Network errors - retry with exponential backoff
                wait_time = min(60, 2 ** attempt * 5)
                logger.warning(f"Network error on {self.config.name}: {e}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                # Other errors - log and retry
                logger.error(f"Error on {self.config.name}: {e}")
                self.last_error = e
                self.error_count += 1
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        raise Exception(f"Max retries exceeded for {self.config.name}")

class ExchangeManager:
    """Manages multiple exchange connections with failover and load balancing"""
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeConnection] = {}
        self.primary_exchange: Optional[str] = None
        self.active_exchanges: List[str] = []
        self._lock = asyncio.Lock()
    
    async def add_exchange(self, config: ExchangeConfig):
        """Add an exchange to the manager"""
        async with self._lock:
            conn = ExchangeConnection(config)
            try:
                await conn.connect()
                self.exchanges[config.name] = conn
                self.active_exchanges.append(config.name)
                
                if not self.primary_exchange:
                    self.primary_exchange = config.name
                    
                logger.info(f"Added exchange: {config.name}")
                
            except Exception as e:
                logger.error(f"Failed to add exchange {config.name}: {e}")
                raise
    
    async def remove_exchange(self, name: str):
        """Remove an exchange from the manager"""
        async with self._lock:
            if name in self.exchanges:
                await self.exchanges[name].disconnect()
                del self.exchanges[name]
                
                if name in self.active_exchanges:
                    self.active_exchanges.remove(name)
                
                if self.primary_exchange == name:
                    self.primary_exchange = self.active_exchanges[0] if self.active_exchanges else None
    
    async def get_order_book(self, symbol: str, limit: int = 100, exchange: str = None) -> Dict:
        """Get order book from specified exchange or primary"""
        exchange_name = exchange or self.primary_exchange
        
        if not exchange_name or exchange_name not in self.exchanges:
            raise ValueError(f"Exchange {exchange_name} not available")
        
        conn = self.exchanges[exchange_name]
        
        async def fetch():
            return await conn.exchange.fetch_order_book(symbol, limit)
        
        return await conn.execute_with_retry(fetch)
    
    async def get_trades(self, symbol: str, since: Optional[int] = None, limit: int = 100, exchange: str = None) -> List[Dict]:
        """Get recent trades from specified exchange"""
        exchange_name = exchange or self.primary_exchange
        
        if not exchange_name or exchange_name not in self.exchanges:
            raise ValueError(f"Exchange {exchange_name} not available")
        
        conn = self.exchanges[exchange_name]
        
        async def fetch():
            return await conn.exchange.fetch_trades(symbol, since, limit)
        
        return await conn.execute_with_retry(fetch)
    
    async def get_ticker(self, symbol: str, exchange: str = None) -> Dict:
        """Get ticker data from specified exchange"""
        exchange_name = exchange or self.primary_exchange
        
        if not exchange_name or exchange_name not in self.exchanges:
            raise ValueError(f"Exchange {exchange_name} not available")
        
        conn = self.exchanges[exchange_name]
        
        async def fetch():
            return await conn.exchange.fetch_ticker(symbol)
        
        return await conn.execute_with_retry(fetch)
    
    async def get_all_order_books(self, symbol: str, limit: int = 100) -> Dict[str, Dict]:
        """Get order books from all active exchanges"""
        tasks = {}
        
        for name in self.active_exchanges:
            tasks[name] = self.get_order_book(symbol, limit, name)
        
        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Failed to get order book from {name}: {e}")
                results[name] = None
        
        return results
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all exchanges"""
        health = {}
        
        for name, conn in self.exchanges.items():
            try:
                # Simple ping test
                await conn.execute_with_retry(conn.exchange.fetch_ticker, 'BTC/USDT')
                health[name] = True
            except Exception:
                health[name] = False
                
                # Remove from active if unhealthy
                if name in self.active_exchanges:
                    self.active_exchanges.remove(name)
        
        return health
    
    async def close_all(self):
        """Close all exchange connections"""
        for conn in self.exchanges.values():
            await conn.disconnect()
        
        self.exchanges.clear()
        self.active_exchanges.clear()
        self.primary_exchange = None

# Example usage
async def main():
    manager = ExchangeManager()
    
    # Add exchanges with rate limiting
    await manager.add_exchange(ExchangeConfig(
        name='binance',
        rate_limits=RateLimitConfig(
            requests_per_second=10,
            requests_per_minute=1200,
            burst_capacity=20
        )
    ))
    
    await manager.add_exchange(ExchangeConfig(
        name='kraken',
        rate_limits=RateLimitConfig(
            requests_per_second=1,
            requests_per_minute=60,
            burst_capacity=5
        )
    ))
    
    # Get order book
    order_book = await manager.get_order_book('BTC/USDT')
    print(f"Order book depth: {len(order_book['bids'])} bids, {len(order_book['asks'])} asks")
    
    # Get from all exchanges
    all_books = await manager.get_all_order_books('BTC/USDT')
    for exchange, book in all_books.items():
        if book:
            print(f"{exchange}: {len(book['bids'])} bids, {len(book['asks'])} asks")
    
    await manager.close_all()

if __name__ == "__main__":
    asyncio.run(main())