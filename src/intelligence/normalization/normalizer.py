"""
Data normalization layer for standardizing data from different sources
Ensures consistent data format across all intelligence components
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Type, Callable
from decimal import Decimal
import json
from enum import Enum
import re
import pandas as pd
import numpy as np

from ..core.base import DataProcessor, ProcessingError
from ..monitoring.logger import timed_operation

@dataclass
class NormalizedData:
    """Standardized data format for all sources"""
    source: str
    symbol: Optional[str] = None
    timestamp: Optional[datetime] = None
    data_type: Optional[str] = None
    value: Optional[Union[float, Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source': self.source,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data_type': self.data_type,
            'value': self.value,
            'metadata': self.metadata
        }

class DataNormalizer(DataProcessor):
    """Base class for data normalizers"""
    
    def __init__(self, name: str, source_type: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.source_type = source_type
        self._field_mappings = self._get_field_mappings()
        self._transformers = self._get_transformers()
        
    def _get_field_mappings(self) -> Dict[str, str]:
        """Get field mappings for this source type"""
        # Default mappings - override in subclasses
        return {
            'symbol': 'symbol',
            'timestamp': 'timestamp',
            'price': 'price',
            'volume': 'volume'
        }
        
    def _get_transformers(self) -> Dict[str, Callable]:
        """Get field transformers"""
        return {
            'timestamp': self._normalize_timestamp,
            'symbol': self._normalize_symbol,
            'price': self._normalize_price,
            'volume': self._normalize_volume
        }
        
    async def initialize(self) -> None:
        """Initialize normalizer"""
        self.logger.info(f"Initializing {self.name} normalizer")
        
    async def start(self) -> None:
        """Start normalizer"""
        self._running = True
        self.logger.info(f"Started {self.name} normalizer")
        
    async def stop(self) -> None:
        """Stop normalizer"""
        self._running = False
        self.logger.info(f"Stopped {self.name} normalizer")
        
    @timed_operation("data_validation")
    async def validate(self, data: Any) -> bool:
        """Validate incoming data"""
        if not data:
            return False
            
        # Check required fields based on source type
        required_fields = self.config.get('required_fields', [])
        if required_fields:
            if isinstance(data, dict):
                for field in required_fields:
                    if field not in data:
                        self.logger.warning(f"Missing required field: {field}")
                        return False
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for field in required_fields:
                            if field not in item:
                                return False
                                
        return True
        
    @timed_operation("data_transformation")
    async def transform(self, data: Any) -> Union[NormalizedData, List[NormalizedData]]:
        """Transform data to normalized format"""
        if isinstance(data, list):
            normalized = []
            for item in data:
                norm_item = await self._transform_single(item)
                if norm_item:
                    normalized.append(norm_item)
            return normalized
        else:
            return await self._transform_single(data)
            
    async def _transform_single(self, data: Dict[str, Any]) -> Optional[NormalizedData]:
        """Transform single data item"""
        try:
            normalized = NormalizedData(
                source=self.source_type,
                raw_data=data
            )
            
            # Apply field mappings
            for target_field, source_field in self._field_mappings.items():
                if source_field in data:
                    value = data[source_field]
                    
                    # Apply transformer if exists
                    if target_field in self._transformers:
                        value = self._transformers[target_field](value)
                        
                    setattr(normalized, target_field, value)
                    
            # Extract metadata
            normalized.metadata = self._extract_metadata(data)
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            return None
            
    @timed_operation("data_enrichment")
    async def enrich(self, data: Union[NormalizedData, List[NormalizedData]]) -> Union[NormalizedData, List[NormalizedData]]:
        """Enrich normalized data with additional information"""
        if isinstance(data, list):
            enriched = []
            for item in data:
                enriched_item = await self._enrich_single(item)
                enriched.append(enriched_item)
            return enriched
        else:
            return await self._enrich_single(data)
            
    async def _enrich_single(self, data: NormalizedData) -> NormalizedData:
        """Enrich single data item"""
        # Add source metadata
        data.metadata['normalizer'] = self.name
        data.metadata['normalized_at'] = datetime.utcnow().isoformat()
        
        # Add data quality metrics
        data.metadata['quality_score'] = self._calculate_quality_score(data)
        
        return data
        
    async def process(self, data: Any) -> Union[NormalizedData, List[NormalizedData]]:
        """Process data through validation, transformation and enrichment"""
        # Validate
        if not await self.validate(data):
            raise ProcessingError("Data validation failed")
            
        # Transform
        normalized = await self.transform(data)
        
        # Enrich
        enriched = await self.enrich(normalized)
        
        return enriched
        
    def _normalize_timestamp(self, value: Any) -> Optional[datetime]:
        """Normalize timestamp to datetime object"""
        if isinstance(value, datetime):
            return value
        elif isinstance(value, (int, float)):
            # Assume unix timestamp
            return datetime.fromtimestamp(value)
        elif isinstance(value, str):
            # Try common formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None
        
    def _normalize_symbol(self, value: Any) -> str:
        """Normalize trading symbol"""
        if not value:
            return ""
            
        # Convert to uppercase and remove special characters
        symbol = str(value).upper()
        symbol = re.sub(r'[^A-Z0-9]', '', symbol)
        
        # Handle common variations
        symbol_mappings = self.config.get('symbol_mappings', {})
        return symbol_mappings.get(symbol, symbol)
        
    def _normalize_price(self, value: Any) -> Optional[float]:
        """Normalize price value"""
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                value = re.sub(r'[$,€£¥]', '', value)
            return float(value)
        except (ValueError, TypeError):
            return None
            
    def _normalize_volume(self, value: Any) -> Optional[float]:
        """Normalize volume value"""
        try:
            if isinstance(value, str):
                # Handle K, M, B suffixes
                multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
                for suffix, multiplier in multipliers.items():
                    if value.endswith(suffix):
                        return float(value[:-1]) * multiplier
            return float(value)
        except (ValueError, TypeError):
            return None
            
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw data"""
        metadata = {}
        
        # Extract non-standard fields as metadata
        standard_fields = set(self._field_mappings.values())
        for key, value in data.items():
            if key not in standard_fields:
                metadata[key] = value
                
        return metadata
        
    def _calculate_quality_score(self, data: NormalizedData) -> float:
        """Calculate data quality score (0-1)"""
        score = 1.0
        
        # Check for missing required fields
        if not data.timestamp:
            score -= 0.2
        if not data.symbol:
            score -= 0.2
        if not data.value:
            score -= 0.3
            
        # Check data age
        if data.timestamp:
            age = (datetime.utcnow() - data.timestamp).total_seconds()
            if age > 3600:  # Older than 1 hour
                score -= 0.1
            if age > 86400:  # Older than 1 day
                score -= 0.2
                
        return max(0.0, score)

class MarketDataNormalizer(DataNormalizer):
    """Normalizer for market data"""
    
    def _get_field_mappings(self) -> Dict[str, str]:
        return {
            'symbol': 'ticker',
            'timestamp': 'time',
            'price': 'last',
            'volume': 'vol',
            'bid': 'bid',
            'ask': 'ask',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close'
        }
        
    async def _enrich_single(self, data: NormalizedData) -> NormalizedData:
        """Enrich market data"""
        data = await super()._enrich_single(data)
        
        # Calculate spread if bid/ask available
        if 'bid' in data.metadata and 'ask' in data.metadata:
            spread = data.metadata['ask'] - data.metadata['bid']
            data.metadata['spread'] = spread
            data.metadata['spread_pct'] = (spread / data.metadata['ask']) * 100
            
        # Set data type
        data.data_type = 'market_data'
        
        return data

class NewsDataNormalizer(DataNormalizer):
    """Normalizer for news data"""
    
    def _get_field_mappings(self) -> Dict[str, str]:
        return {
            'timestamp': 'published_at',
            'title': 'headline',
            'content': 'body',
            'source': 'provider',
            'url': 'link',
            'symbols': 'tickers'
        }
        
    async def _transform_single(self, data: Dict[str, Any]) -> Optional[NormalizedData]:
        """Transform news data"""
        normalized = NormalizedData(
            source=self.source_type,
            raw_data=data
        )
        
        # Extract basic fields
        normalized.timestamp = self._normalize_timestamp(data.get('published_at'))
        normalized.data_type = 'news'
        
        # Extract symbols
        symbols = data.get('tickers', [])
        if symbols:
            normalized.symbol = symbols[0] if isinstance(symbols, list) else symbols
            
        # Store news content in value
        normalized.value = {
            'title': data.get('headline', ''),
            'content': data.get('body', ''),
            'url': data.get('link', ''),
            'source': data.get('provider', '')
        }
        
        # Extract metadata
        normalized.metadata = {
            'sentiment': data.get('sentiment'),
            'relevance': data.get('relevance'),
            'all_symbols': symbols
        }
        
        return normalized

class SocialMediaNormalizer(DataNormalizer):
    """Normalizer for social media data"""
    
    def _get_field_mappings(self) -> Dict[str, str]:
        return {
            'timestamp': 'created_at',
            'content': 'text',
            'author': 'user',
            'engagement': 'metrics'
        }
        
    async def _enrich_single(self, data: NormalizedData) -> NormalizedData:
        """Enrich social media data"""
        data = await super()._enrich_single(data)
        
        # Extract mentions and hashtags
        if isinstance(data.value, dict) and 'content' in data.value:
            content = data.value['content']
            data.metadata['mentions'] = re.findall(r'@(\w+)', content)
            data.metadata['hashtags'] = re.findall(r'#(\w+)', content)
            data.metadata['cashtags'] = re.findall(r'\$([A-Z]+)', content)
            
        data.data_type = 'social_media'
        
        return data

class NormalizerFactory:
    """Factory for creating normalizers"""
    
    _normalizers: Dict[str, Type[DataNormalizer]] = {
        'market_data': MarketDataNormalizer,
        'news': NewsDataNormalizer,
        'social_media': SocialMediaNormalizer
    }
    
    @classmethod
    def create_normalizer(cls, source_type: str, name: str, config: Optional[Dict[str, Any]] = None) -> DataNormalizer:
        """Create normalizer for source type"""
        normalizer_class = cls._normalizers.get(source_type, DataNormalizer)
        return normalizer_class(name, source_type, config)
        
    @classmethod
    def register_normalizer(cls, source_type: str, normalizer_class: Type[DataNormalizer]) -> None:
        """Register custom normalizer"""
        cls._normalizers[source_type] = normalizer_class