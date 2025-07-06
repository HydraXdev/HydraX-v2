"""
News API Client for Economic Calendar Integration

This module handles fetching economic calendar events from various providers
and integrating them with the BITTEN trading system.
"""

import json
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from .input_validators import (
    validate_currency_code, sanitize_event_name, sanitize_numeric_string,
    validate_datetime_string, validate_news_event, sanitize_log_message
)

from config.news_api import (
    get_api_config, 
    get_headers, 
    is_high_impact_event,
    MONITORED_CURRENCIES,
    NEWS_BUFFER_BEFORE,
    NEWS_BUFFER_AFTER,
    NEWS_CACHE_DURATION,
    NEWS_API_PROVIDER
)

logger = logging.getLogger(__name__)


class NewsImpact(Enum):
    """News event impact levels"""
    HIGH = "high"
    MEDIUM = "medium"  
    LOW = "low"


@dataclass
class EconomicEvent:
    """Economic calendar event"""
    event_time: datetime
    currency: str
    impact: NewsImpact
    event_name: str
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None
    provider: str = "unknown"
    
    def __post_init__(self):
        """Ensure datetime is timezone aware"""
        if self.event_time.tzinfo is None:
            self.event_time = self.event_time.replace(tzinfo=timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching"""
        return {
            'event_time': self.event_time.isoformat(),
            'currency': self.currency,
            'impact': self.impact.value,
            'event_name': self.event_name,
            'forecast': self.forecast,
            'previous': self.previous,
            'actual': self.actual,
            'provider': self.provider
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EconomicEvent':
        """Create from dictionary"""
        data['event_time'] = datetime.fromisoformat(data['event_time'])
        data['impact'] = NewsImpact(data['impact'])
        return cls(**data)


class NewsAPIClient:
    """Client for fetching economic calendar events"""
    
    def __init__(self):
        self.config = get_api_config()
        self.provider = NEWS_API_PROVIDER
        self._cache: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None
        self._max_cache_size = 10  # Maximum number of cache entries
        
    def fetch_events(self, days_ahead: int = 7) -> List[EconomicEvent]:
        """
        Fetch economic events for the next N days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of economic events
        """
        # Check cache
        cache_key = f"events_{days_ahead}"
        if self._is_cache_valid(cache_key):
            logger.info("Returning cached news events")
            return self._get_from_cache(cache_key)
        
        try:
            # Fetch based on provider
            if self.provider == 'forexfactory':
                events = self._fetch_forexfactory_events()
            else:
                logger.warning(f"Provider {self.provider} not implemented, using ForexFactory")
                events = self._fetch_forexfactory_events()
            
            # Filter events
            filtered_events = self._filter_events(events, days_ahead)
            
            # Cache results
            self._cache_events(cache_key, filtered_events)
            
            logger.info(f"Fetched {len(filtered_events)} economic events")
            return filtered_events
            
        except Exception as e:
            logger.error(f"Error fetching economic events: {e}")
            # Return cached data if available, even if expired
            if cache_key in self._cache:
                logger.warning("Returning expired cache due to fetch error")
                return self._cache[cache_key]['data']
            return []
    
    def _fetch_forexfactory_events(self) -> List[EconomicEvent]:
        """Fetch events from ForexFactory API"""
        events = []
        
        try:
            url = self.config['base_url'] + self.config['calendar']
            headers = get_headers()
            
            # Reduce timeout to prevent slowloris attacks
            response = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
            response.raise_for_status()
            
            data = response.json()
            
            # Limit number of events to prevent memory exhaustion
            if isinstance(data, list) and len(data) > 1000:
                logger.warning("API returned too many events, limiting to 1000")
                data = data[:1000]
            
            for item in data:
                try:
                    # Validate and parse event
                    validated_item = validate_news_event(item)
                    if validated_item:
                        event = self._parse_forexfactory_event(validated_item)
                        if event:
                            events.append(event)
                except Exception as e:
                    logger.warning(f"Error parsing event: {sanitize_log_message(str(e))}")
                    continue
                    
        except requests.RequestException as e:
            logger.error(f"Error fetching from ForexFactory: {e}")
            # Return mock data for testing if API fails
            if "Connection" in str(e) or "timed out" in str(e):
                logger.warning("Using mock data due to connection error")
                return self._get_mock_events()
            
        return events
    
    def _parse_forexfactory_event(self, item: Dict[str, Any]) -> Optional[EconomicEvent]:
        """Parse ForexFactory event format"""
        try:
            # Extract date and time
            date_str = item.get('date', '')
            time_str = item.get('time', '')
            
            if not date_str:
                return None
                
            # Parse datetime
            if time_str and time_str != 'All Day':
                datetime_str = f"{date_str} {time_str}"
                # ForexFactory times are in EST/EDT
                event_time = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M%p")
                # Convert to UTC (assuming EST for now, -5 hours)
                event_time = event_time.replace(tzinfo=timezone.utc) + timedelta(hours=5)
            else:
                # All day event - set to midnight UTC
                event_time = datetime.strptime(date_str, "%Y-%m-%d")
                event_time = event_time.replace(tzinfo=timezone.utc)
            
            # Extract and validate currency
            currency = item.get('country', '').upper()
            if not validate_currency_code(currency) or currency not in MONITORED_CURRENCIES:
                return None
            
            # Extract impact
            impact_raw = item.get('impact', '').lower()
            impact = self._map_impact(impact_raw)
            
            # Extract and sanitize event details
            event_name = sanitize_event_name(item.get('title', ''))
            if not event_name:
                return None
            
            # Check if it's a high impact event by name
            if impact == NewsImpact.MEDIUM and is_high_impact_event(event_name):
                impact = NewsImpact.HIGH
            
            return EconomicEvent(
                event_time=event_time,
                currency=currency,
                impact=impact,
                event_name=event_name,
                forecast=sanitize_numeric_string(item.get('forecast')),
                previous=sanitize_numeric_string(item.get('previous')),
                actual=sanitize_numeric_string(item.get('actual')),
                provider='forexfactory'
            )
            
        except Exception as e:
            logger.debug(f"Error parsing ForexFactory event: {e}")
            return None
    
    def _map_impact(self, impact_raw: str) -> NewsImpact:
        """Map provider impact levels to our standard levels"""
        impact_mapping = self.config.get('impact_mapping', {})
        
        for level, values in impact_mapping.items():
            if impact_raw in [str(v).lower() for v in values]:
                return NewsImpact(level)
        
        # Default to medium if not mapped
        return NewsImpact.MEDIUM
    
    def _filter_events(self, events: List[EconomicEvent], days_ahead: int) -> List[EconomicEvent]:
        """Filter events by date range and currencies"""
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=days_ahead)
        
        filtered = []
        for event in events:
            # Date range filter
            if event.event_time < now or event.event_time > end_date:
                continue
            
            # Currency filter
            if event.currency not in MONITORED_CURRENCIES:
                continue
            
            # Only include medium and high impact
            if event.impact == NewsImpact.LOW:
                continue
            
            filtered.append(event)
        
        # Sort by time
        filtered.sort(key=lambda x: x.event_time)
        
        return filtered
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self._cache:
            return False
        
        cache_entry = self._cache[cache_key]
        cache_time = cache_entry.get('timestamp')
        
        if not cache_time:
            return False
        
        age = (datetime.now() - cache_time).total_seconds()
        return age < NEWS_CACHE_DURATION
    
    def _get_from_cache(self, cache_key: str) -> List[EconomicEvent]:
        """Get events from cache"""
        cache_data = self._cache.get(cache_key, {}).get('data', [])
        return [EconomicEvent.from_dict(item) for item in cache_data]
    
    def _cache_events(self, cache_key: str, events: List[EconomicEvent]):
        """Cache events with size limit"""
        # Enforce cache size limit
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), 
                           key=lambda k: self._cache[k].get('timestamp', datetime.min))
            del self._cache[oldest_key]
        
        self._cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': [event.to_dict() for event in events]
        }
        self._last_update = datetime.now()
    
    def get_upcoming_high_impact(self, hours_ahead: int = 24) -> List[EconomicEvent]:
        """Get upcoming high impact events within the next N hours"""
        all_events = self.fetch_events(days_ahead=2)
        
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours_ahead)
        
        high_impact = [
            event for event in all_events
            if event.impact == NewsImpact.HIGH and now <= event.event_time <= cutoff
        ]
        
        return high_impact
    
    def is_news_blackout_period(self) -> tuple[bool, Optional[EconomicEvent]]:
        """
        Check if we're currently in a news blackout period
        
        Returns:
            Tuple of (is_blackout, next_event)
        """
        events = self.fetch_events(days_ahead=1)
        now = datetime.now(timezone.utc)
        
        for event in events:
            if event.impact != NewsImpact.HIGH:
                continue
            
            # Calculate blackout window
            blackout_start = event.event_time - timedelta(minutes=NEWS_BUFFER_BEFORE)
            blackout_end = event.event_time + timedelta(minutes=NEWS_BUFFER_AFTER)
            
            if blackout_start <= now <= blackout_end:
                return True, event
        
        return False, None
    
    def get_next_blackout_window(self) -> Optional[tuple[datetime, datetime, EconomicEvent]]:
        """Get the next news blackout window"""
        events = self.get_upcoming_high_impact(hours_ahead=48)
        
        if not events:
            return None
        
        next_event = events[0]
        blackout_start = next_event.event_time - timedelta(minutes=NEWS_BUFFER_BEFORE)
        blackout_end = next_event.event_time + timedelta(minutes=NEWS_BUFFER_AFTER)
        
        return blackout_start, blackout_end, next_event
    
    def _get_mock_events(self) -> List[EconomicEvent]:
        """Generate mock events for testing when API is unavailable"""
        events = []
        now = datetime.now(timezone.utc)
        
        # Add some mock high impact events
        mock_events_data = [
            {"hours": 2, "currency": "USD", "name": "Non-Farm Payrolls"},
            {"hours": 6, "currency": "EUR", "name": "ECB Rate Decision"},
            {"hours": 24, "currency": "GBP", "name": "UK GDP"},
            {"hours": 48, "currency": "JPY", "name": "BoJ Policy Rate"},
        ]
        
        for mock_data in mock_events_data:
            event_time = now + timedelta(hours=mock_data["hours"])
            events.append(EconomicEvent(
                event_time=event_time,
                currency=mock_data["currency"],
                impact=NewsImpact.HIGH,
                event_name=mock_data["name"],
                forecast="0.2%",
                previous="0.1%",
                provider="mock"
            ))
        
        logger.info(f"Generated {len(events)} mock events for testing")
        return events