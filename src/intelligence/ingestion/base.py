"""
Base classes for data ingestion from multiple sources
Provides framework for building scalable data ingestion pipelines
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, AsyncIterator
import asyncio
import aiohttp
from asyncio import Queue
import json
from enum import Enum, auto
import time
from contextlib import asynccontextmanager
import backoff

from ..core.base import DataIngestionComponent, DataSource, DataSourceType, IntelligenceError
from ..monitoring.logger import LoggerManager, timed_operation

class ConnectionStatus(Enum):
    """Connection status for data sources"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()
    RECONNECTING = auto()

@dataclass
class IngestionStats:
    """Statistics for data ingestion"""
    messages_received: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    bytes_received: int = 0
    last_message_time: Optional[datetime] = None
    connection_time: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.messages_received
        if total == 0:
            return 0.0
        return (self.messages_processed / total) * 100

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_second: float = 10.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
        self._lock = asyncio.Lock()
        
    async def acquire(self) -> None:
        """Acquire rate limit slot"""
        async with self._lock:
            now = time.time()
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            self.last_call = time.time()

class BaseDataIngester(DataIngestionComponent):
    """Base class for all data ingesters"""
    
    def __init__(self, name: str, data_source: DataSource, 
                 buffer_size: int = 1000, 
                 batch_size: int = 100,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, data_source, config)
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.status = ConnectionStatus.DISCONNECTED
        self.stats = IngestionStats()
        self._buffer: Queue = Queue(maxsize=buffer_size)
        self._rate_limiter: Optional[RateLimiter] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._processing_task: Optional[asyncio.Task] = None
        
        # Setup rate limiting if configured
        rate_limit = self.config.get('rate_limit')
        if rate_limit:
            self._rate_limiter = RateLimiter(rate_limit)
            
    async def initialize(self) -> None:
        """Initialize the ingester"""
        self.logger.info(f"Initializing {self.name} ingester")
        self.status = ConnectionStatus.CONNECTING
        
        try:
            # Create HTTP session if needed
            if self.config.get('use_http', True):
                timeout = aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
                self._session = aiohttp.ClientSession(timeout=timeout)
                
            # Perform any additional initialization
            await self._initialize()
            
            self.status = ConnectionStatus.CONNECTED
            self.stats.connection_time = datetime.utcnow()
            self.logger.info(f"{self.name} ingester initialized successfully")
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.stats.error_count += 1
            self.stats.last_error = str(e)
            self.logger.error(f"Failed to initialize {self.name} ingester: {e}")
            raise
            
    @abstractmethod
    async def _initialize(self) -> None:
        """Perform ingester-specific initialization"""
        pass
        
    async def start(self) -> None:
        """Start data ingestion"""
        if self.status != ConnectionStatus.CONNECTED:
            await self.initialize()
            
        self._running = True
        self.logger.info(f"Starting {self.name} ingester")
        
        # Start ingestion task
        ingestion_task = asyncio.create_task(self._ingestion_loop())
        self._tasks.append(ingestion_task)
        
        # Start processing task
        self._processing_task = asyncio.create_task(self._processing_loop())
        self._tasks.append(self._processing_task)
        
    async def stop(self) -> None:
        """Stop data ingestion"""
        self.logger.info(f"Stopping {self.name} ingester")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        # Close session
        if self._session:
            await self._session.close()
            
        self.status = ConnectionStatus.DISCONNECTED
        self.logger.info(f"{self.name} ingester stopped")
        
    @abstractmethod
    async def _ingestion_loop(self) -> None:
        """Main ingestion loop - must be implemented by subclasses"""
        pass
        
    async def _processing_loop(self) -> None:
        """Process data from buffer"""
        batch = []
        
        while self._running:
            try:
                # Get data from buffer with timeout
                try:
                    data = await asyncio.wait_for(self._buffer.get(), timeout=1.0)
                    batch.append(data)
                except asyncio.TimeoutError:
                    # Process partial batch if exists
                    if batch:
                        await self._process_batch(batch)
                        batch = []
                    continue
                    
                # Process batch when full
                if len(batch) >= self.batch_size:
                    await self._process_batch(batch)
                    batch = []
                    
            except asyncio.CancelledError:
                # Process remaining data before exiting
                if batch:
                    await self._process_batch(batch)
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                self.stats.error_count += 1
                
    async def _process_batch(self, batch: List[Any]) -> None:
        """Process a batch of data"""
        try:
            # Process data
            processed_data = await self.process(batch)
            
            # Update stats
            self.stats.messages_processed += len(batch)
            
            # Notify callbacks
            await self._notify_callbacks(processed_data)
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            self.stats.messages_failed += len(batch)
            self.stats.error_count += 1
            
    @timed_operation("data_processing")
    async def process(self, data: Any) -> Any:
        """Process incoming data"""
        # Default implementation - override in subclasses
        return data
        
    async def ingest_data(self, data: Any) -> None:
        """Add data to ingestion buffer"""
        try:
            # Update stats
            self.stats.messages_received += 1
            self.stats.last_message_time = datetime.utcnow()
            
            # Add to buffer (non-blocking)
            self._buffer.put_nowait(data)
            
        except asyncio.QueueFull:
            self.logger.warning(f"Buffer full for {self.name}, dropping message")
            self.stats.messages_failed += 1
            
    @asynccontextmanager
    async def rate_limited(self):
        """Context manager for rate-limited operations"""
        if self._rate_limiter:
            await self._rate_limiter.acquire()
        yield
        
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        max_time=300
    )
    async def _make_request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with retry logic"""
        async with self.rate_limited():
            async with self._session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return response
                
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = await super().health_check()
        health.update({
            'status': self.status.name,
            'stats': {
                'messages_received': self.stats.messages_received,
                'messages_processed': self.stats.messages_processed,
                'messages_failed': self.stats.messages_failed,
                'success_rate': self.stats.success_rate(),
                'buffer_size': self._buffer.qsize(),
                'error_count': self.stats.error_count
            }
        })
        return health

class HTTPDataIngester(BaseDataIngester):
    """Data ingester for HTTP/REST APIs"""
    
    async def _initialize(self) -> None:
        """Initialize HTTP ingester"""
        # Validate required config
        if 'endpoint' not in self.config:
            raise ValueError("HTTP ingester requires 'endpoint' configuration")
            
    async def _ingestion_loop(self) -> None:
        """Poll HTTP endpoint for data"""
        endpoint = self.config['endpoint']
        poll_interval = self.config.get('poll_interval', 60)
        headers = self.config.get('headers', {})
        
        while self._running:
            try:
                # Make request
                async with self._make_request('GET', endpoint, headers=headers) as response:
                    data = await response.json()
                    
                    # Update stats
                    self.stats.bytes_received += len(await response.read())
                    
                    # Ingest data
                    await self.ingest_data(data)
                    
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in HTTP ingestion: {e}")
                self.stats.error_count += 1
                self.stats.last_error = str(e)
                
                # Wait before retry
                await asyncio.sleep(min(poll_interval, 10))

class WebSocketDataIngester(BaseDataIngester):
    """Data ingester for WebSocket connections"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ws_connection = None
        
    async def _initialize(self) -> None:
        """Initialize WebSocket ingester"""
        # Validate required config
        if 'ws_url' not in self.config:
            raise ValueError("WebSocket ingester requires 'ws_url' configuration")
            
    async def _ingestion_loop(self) -> None:
        """Connect to WebSocket and receive data"""
        ws_url = self.config['ws_url']
        headers = self.config.get('headers', {})
        
        while self._running:
            try:
                async with self._session.ws_connect(ws_url, headers=headers) as ws:
                    self._ws_connection = ws
                    self.logger.info(f"Connected to WebSocket: {ws_url}")
                    
                    # Send authentication if required
                    auth_msg = self.config.get('auth_message')
                    if auth_msg:
                        await ws.send_json(auth_msg)
                        
                    # Subscribe to channels if required
                    subscribe_msg = self.config.get('subscribe_message')
                    if subscribe_msg:
                        await ws.send_json(subscribe_msg)
                        
                    # Receive messages
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await self.ingest_data(data)
                            
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            self.logger.error(f"WebSocket error: {ws.exception()}")
                            self.stats.error_count += 1
                            break
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}")
                self.stats.error_count += 1
                self.stats.last_error = str(e)
                
                # Wait before reconnecting
                await asyncio.sleep(5)
                
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message through WebSocket"""
        if self._ws_connection and not self._ws_connection.closed:
            await self._ws_connection.send_json(message)

class StreamDataIngester(BaseDataIngester):
    """Data ingester for streaming data sources"""
    
    @abstractmethod
    async def _get_stream(self) -> AsyncIterator[Any]:
        """Get data stream - must be implemented by subclasses"""
        pass
        
    async def _ingestion_loop(self) -> None:
        """Process streaming data"""
        while self._running:
            try:
                async for data in self._get_stream():
                    if not self._running:
                        break
                    await self.ingest_data(data)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Stream ingestion error: {e}")
                self.stats.error_count += 1
                self.stats.last_error = str(e)
                
                # Wait before reconnecting
                await asyncio.sleep(5)