#!/usr/bin/env python3
"""
BITTEN News Intelligence Gate - Production News Filter
Integrates with Forex Factory to intelligently filter trading during high-impact news events
Designed for seamless integration into existing BITTEN architecture
"""

import json
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import threading
import os

@dataclass
class EconomicEvent:
    """Economic calendar event structure"""
    country: str
    impact: str
    date: str
    time: str
    title: str
    forecast: str
    previous: str
    event_timestamp: float
    
class NewsIntelligenceGate:
    """
    Production-ready news filter for BITTEN trading engine
    
    Features:
    - Three-tier filtering: BLOCK/REDUCE/NORMAL
    - Free Forex Factory integration
    - Graceful error handling
    - Configurable time windows
    - Toggle on/off for A/B testing
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.enabled = True  # Master toggle for testing
        
        # Economic calendar data
        self.economic_calendar: List[EconomicEvent] = []
        self.last_update = 0
        self.update_interval = 86400  # 24 hours
        self.calendar_cache_file = "/root/HydraX-v2/economic_calendar_cache.json"
        
        # High-impact events that block trading
        self.tier1_block_events = [
            'Nonfarm Payrolls', 'FOMC', 'CPI', 'GDP', 'Interest Rate Decision',
            'Employment Change', 'Core CPI', 'Retail Sales', 'Fed Chair Speech'
        ]
        
        # Medium-impact events that reduce confidence
        self.tier2_reduce_events = [
            'PMI', 'Manufacturing PMI', 'Services PMI', 'Consumer Confidence',
            'Industrial Production', 'PPI', 'Trade Balance', 'Current Account',
            'Employment Claims', 'Building Permits', 'Housing Starts'
        ]
        
        # Time windows for filtering
        self.tier1_window_minutes = 15  # BLOCK: 15 minutes before/after
        self.tier2_window_minutes = 30  # REDUCE: 30 minutes before/after
        
        # Penalty values
        self.tier2_confidence_penalty = 10  # Reduce confidence by 10 points
        
        # Network settings
        self.request_timeout = 10
        self.max_retries = 3
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics tracking
        self.stats = {
            'total_evaluations': 0,
            'blocked_cycles': 0,
            'reduced_confidence': 0,
            'normal_trading': 0,
            'calendar_updates': 0,
            'network_errors': 0
        }
        
        # Load cached calendar on initialization
        self._load_cached_calendar()
        
        self.logger.info("🗞️ News Intelligence Gate initialized")
        
    def _load_cached_calendar(self):
        """Load cached economic calendar from disk"""
        try:
            if os.path.exists(self.calendar_cache_file):
                with open(self.calendar_cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                # Convert to EconomicEvent objects
                self.economic_calendar = []
                for event_data in cached_data.get('events', []):
                    event = EconomicEvent(**event_data)
                    self.economic_calendar.append(event)
                
                self.last_update = cached_data.get('last_update', 0)
                self.logger.info(f"📅 Loaded {len(self.economic_calendar)} cached economic events")
                
        except Exception as e:
            self.logger.warning(f"Failed to load cached calendar: {e}")
            self.economic_calendar = []
    
    def _save_calendar_cache(self):
        """Save economic calendar to disk cache"""
        try:
            cache_data = {
                'last_update': self.last_update,
                'events': [event.__dict__ for event in self.economic_calendar]
            }
            
            with open(self.calendar_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            self.logger.debug("💾 Economic calendar cached to disk")
            
        except Exception as e:
            self.logger.error(f"Failed to save calendar cache: {e}")
    
    def update_economic_calendar(self) -> bool:
        """
        Fetch latest economic calendar from Forex Factory
        Returns True if successful, False otherwise
        """
        if not self.enabled:
            return True
            
        current_time = time.time()
        
        # Check if update is needed
        if current_time - self.last_update < self.update_interval:
            return True
            
        try:
            self.logger.info("📡 Fetching economic calendar from Forex Factory...")
            
            # Forex Factory free API endpoint  
            url = 'https://nfs.faireconomy.media/ff_calendar_thisweek.json'
            
            # Make request with timeout and retries
            for attempt in range(self.max_retries):
                try:
                    response = requests.get(
                        url, 
                        timeout=self.request_timeout,
                        headers={'User-Agent': 'BITTEN-Trading-Engine/1.0'}
                    )
                    response.raise_for_status()
                    break
                    
                except requests.RequestException as e:
                    if attempt == self.max_retries - 1:
                        raise e
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            # Parse JSON response
            calendar_data = response.json()
            
            with self._lock:
                self.economic_calendar = []
                
                for event_data in calendar_data:
                    try:
                        # Parse event datetime
                        event_date_str = f"{event_data.get('date', '')} {event_data.get('time', '')}"
                        
                        # Handle various date formats
                        for date_format in ['%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M', '%d.%m.%Y %H:%M']:
                            try:
                                event_datetime = datetime.strptime(event_date_str.strip(), date_format)
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format matches, skip this event
                            continue
                        
                        event = EconomicEvent(
                            country=event_data.get('country', ''),
                            impact=event_data.get('impact', ''),
                            date=event_data.get('date', ''),
                            time=event_data.get('time', ''),
                            title=event_data.get('title', ''),
                            forecast=event_data.get('forecast', ''),
                            previous=event_data.get('previous', ''),
                            event_timestamp=event_datetime.timestamp()
                        )
                        
                        self.economic_calendar.append(event)
                        
                    except Exception as e:
                        self.logger.debug(f"Skipping malformed event: {e}")
                        continue
                
                self.last_update = current_time
                self.stats['calendar_updates'] += 1
            
            # Save to cache
            self._save_calendar_cache()
            
            self.logger.info(f"✅ Updated economic calendar: {len(self.economic_calendar)} events loaded")
            return True
            
        except Exception as e:
            self.stats['network_errors'] += 1
            self.logger.error(f"❌ Failed to update economic calendar: {e}")
            
            # If we have cached data, continue with that
            if self.economic_calendar:
                self.logger.info("📅 Continuing with cached economic calendar")
                return True
            else:
                self.logger.warning("⚠️ No economic calendar data available - trading unrestricted")
                return False
    
    def _is_high_impact_event(self, event: EconomicEvent) -> bool:
        """Check if event is high-impact (Tier 1 - BLOCK)"""
        if event.impact.lower() != 'high':
            return False
            
        # Focus on USD events primarily
        if event.country not in ['USD', 'US', 'United States']:
            return False
            
        # Check if title matches high-impact events
        for high_impact in self.tier1_block_events:
            if high_impact.lower() in event.title.lower():
                return True
                
        return False
    
    def _is_medium_impact_event(self, event: EconomicEvent) -> bool:
        """Check if event is medium-impact (Tier 2 - REDUCE)"""
        if event.impact.lower() not in ['medium', 'high']:
            return False
            
        # Include USD and EUR events
        if event.country not in ['USD', 'US', 'EUR', 'EU', 'United States', 'European Union']:
            return False
            
        # Check if title matches medium-impact events
        for medium_impact in self.tier2_reduce_events:
            if medium_impact.lower() in event.title.lower():
                return True
                
        return False
    
    def evaluate_trading_environment(self) -> Dict[str, Any]:
        """
        Evaluate current trading environment based on economic events
        
        Returns:
        {
            'action': 'BLOCK'|'REDUCE'|'NORMAL',
            'penalty': int,
            'reason': str,
            'next_event': Optional[Dict],
            'minutes_to_event': Optional[int]
        }
        """
        if not self.enabled:
            return {
                'action': 'NORMAL',
                'penalty': 0,
                'reason': 'News filter disabled',
                'next_event': None,
                'minutes_to_event': None
            }
        
        self.stats['total_evaluations'] += 1
        
        # Update calendar if needed
        self.update_economic_calendar()
        
        current_time = time.time()
        current_dt = datetime.now()
        
        # Check for events within filtering windows
        for event in self.economic_calendar:
            time_to_event = (event.event_timestamp - current_time) / 60  # Minutes
            time_since_event = (current_time - event.event_timestamp) / 60  # Minutes
            
            # Check if we're within the event window
            if self._is_high_impact_event(event):
                # Tier 1: BLOCK trading
                if abs(time_to_event) <= self.tier1_window_minutes or abs(time_since_event) <= self.tier1_window_minutes:
                    self.stats['blocked_cycles'] += 1
                    return {
                        'action': 'BLOCK',
                        'penalty': 0,
                        'reason': f"High-impact {event.country} event: {event.title}",
                        'next_event': event.__dict__,
                        'minutes_to_event': int(time_to_event)
                    }
            
            elif self._is_medium_impact_event(event):
                # Tier 2: REDUCE confidence
                if abs(time_to_event) <= self.tier2_window_minutes or abs(time_since_event) <= self.tier2_window_minutes:
                    self.stats['reduced_confidence'] += 1
                    return {
                        'action': 'REDUCE',
                        'penalty': self.tier2_confidence_penalty,
                        'reason': f"Medium-impact {event.country} event: {event.title}",
                        'next_event': event.__dict__,
                        'minutes_to_event': int(time_to_event)
                    }
        
        # No events affecting trading
        self.stats['normal_trading'] += 1
        return {
            'action': 'NORMAL',
            'penalty': 0,
            'reason': 'Clear trading environment',
            'next_event': None,
            'minutes_to_event': None
        }
    
    def get_upcoming_events(self, hours_ahead: int = 24) -> List[EconomicEvent]:
        """Get upcoming high/medium impact events within specified hours"""
        current_time = time.time()
        future_cutoff = current_time + (hours_ahead * 3600)
        
        upcoming_events = []
        for event in self.economic_calendar:
            if current_time <= event.event_timestamp <= future_cutoff:
                if self._is_high_impact_event(event) or self._is_medium_impact_event(event):
                    upcoming_events.append(event)
        
        # Sort by timestamp
        upcoming_events.sort(key=lambda x: x.event_timestamp)
        return upcoming_events
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get news filter statistics"""
        total_evals = self.stats['total_evaluations']
        if total_evals == 0:
            return self.stats
        
        return {
            **self.stats,
            'block_rate': (self.stats['blocked_cycles'] / total_evals) * 100,
            'reduce_rate': (self.stats['reduced_confidence'] / total_evals) * 100,
            'normal_rate': (self.stats['normal_trading'] / total_evals) * 100,
            'calendar_age_hours': (time.time() - self.last_update) / 3600,
            'events_loaded': len(self.economic_calendar)
        }
    
    def enable(self):
        """Enable news filtering"""
        self.enabled = True
        self.logger.info("🗞️ News Intelligence Gate ENABLED")
    
    def disable(self):
        """Disable news filtering"""
        self.enabled = False
        self.logger.info("🗞️ News Intelligence Gate DISABLED")
    
    def force_calendar_update(self):
        """Force immediate calendar update (for testing)"""
        self.last_update = 0
        return self.update_economic_calendar()