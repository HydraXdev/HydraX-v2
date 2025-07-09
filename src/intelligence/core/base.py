"""
Base classes and interfaces for the intelligence system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union, Callable
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging


class SignalType(Enum):
    """Types of trading signals"""
    BUY = auto()
    SELL = auto()
    HOLD = auto()
    CLOSE = auto()
    ALERT = auto()
    NEWS = auto()
    TECHNICAL = auto()
    SENTIMENT = auto()
    VOLUME = auto()
    PATTERN = auto()


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_WEAK = 1
    WEAK = 2
    NEUTRAL = 3
    STRONG = 4
    VERY_STRONG = 5


class DataSourceType(Enum):
    """Types of data sources"""
    MARKET_DATA = auto()
    NEWS_FEED = auto()
    SOCIAL_MEDIA = auto()
    TECHNICAL_INDICATORS = auto()
    ECONOMIC_CALENDAR = auto()
    SENTIMENT_ANALYSIS = auto()
    BLOCKCHAIN_DATA = auto()
    CUSTOM = auto()


@dataclass
class Signal:
    """Represents a trading signal"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: SignalType = SignalType.HOLD
    strength: SignalStrength = SignalStrength.NEUTRAL
    symbol: Optional[str] = None
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    expiry: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if signal is still valid"""
        if self.expiry and datetime.utcnow() > self.expiry:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            'id': self.id,
            'type': self.type.name,
            'strength': self.strength.value,
            'symbol': self.symbol,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'confidence': self.confidence,
            'expiry': self.expiry.isoformat() if self.expiry else None
        }


@dataclass
class DataSource:
    """Represents a data source"""
    name: str
    type: DataSourceType
    config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    last_update: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 5
    
    def should_retry(self) -> bool:
        """Check if source should be retried after errors"""
        return self.error_count < self.max_errors


class IntelligenceComponent(ABC):
    """Abstract base class for all intelligence components"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"intelligence.{name}")
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the component"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the component"""
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """Process data and return result"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            'name': self.name,
            'running': self._running,
            'active_tasks': len(self._tasks),
            'timestamp': datetime.utcnow().isoformat()
        }


class DataIngestionComponent(IntelligenceComponent):
    """Base class for data ingestion components"""
    
    def __init__(self, name: str, data_source: DataSource, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.data_source = data_source
        self.callbacks: List[Callable] = []
        
    def add_callback(self, callback: Callable) -> None:
        """Add callback for data updates"""
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable) -> None:
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    async def _notify_callbacks(self, data: Any) -> None:
        """Notify all callbacks with new data"""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")


class DataProcessor(IntelligenceComponent):
    """Base class for data processing components"""
    
    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """Validate incoming data"""
        pass
    
    @abstractmethod
    async def transform(self, data: Any) -> Any:
        """Transform data"""
        pass
    
    @abstractmethod
    async def enrich(self, data: Any) -> Any:
        """Enrich data with additional information"""
        pass


class SignalGenerator(IntelligenceComponent):
    """Base class for signal generation components"""
    
    @abstractmethod
    async def analyze(self, data: Any) -> List[Signal]:
        """Analyze data and generate signals"""
        pass
    
    @abstractmethod
    async def filter_signals(self, signals: List[Signal]) -> List[Signal]:
        """Filter signals based on criteria"""
        pass
    
    @abstractmethod
    async def rank_signals(self, signals: List[Signal]) -> List[Signal]:
        """Rank signals by importance"""
        pass


class IntelligenceError(Exception):
    """Base exception for intelligence system"""
    pass


class DataIngestionError(IntelligenceError):
    """Error during data ingestion"""
    pass


class ProcessingError(IntelligenceError):
    """Error during data processing"""
    pass


class ConfigurationError(IntelligenceError):
    """Configuration related error"""
    pass