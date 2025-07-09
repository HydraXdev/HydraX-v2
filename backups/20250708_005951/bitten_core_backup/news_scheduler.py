"""
News Event Scheduler

This module handles periodic updates of economic calendar events
and integration with the BITTEN risk management system.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional, List
from threading import Lock

from .news_api_client import NewsAPIClient, EconomicEvent, NewsImpact
from .risk_management import RiskManager, NewsEvent
from config.news_api import NEWS_UPDATE_INTERVAL

logger = logging.getLogger(__name__)


class NewsScheduler:
    """Handles scheduled updates of economic news events"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.news_client = NewsAPIClient()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_update: Optional[datetime] = None
        self._update_interval = NEWS_UPDATE_INTERVAL
        self._lock = Lock()  # Thread safety for shared resources
        
    def start(self):
        """Start the news scheduler"""
        if self._running:
            logger.warning("News scheduler already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("News scheduler started")
        
        # Do initial update
        self._update_news_events()
    
    def stop(self):
        """Stop the news scheduler"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("News scheduler stopped")
    
    def _run(self):
        """Main scheduler loop"""
        while self._running:
            try:
                # Wait for update interval
                time.sleep(self._update_interval)
                
                if self._running:
                    self._update_news_events()
                    
            except Exception as e:
                logger.error(f"Error in news scheduler: {e}")
                # Continue running despite errors
    
    def _update_news_events(self):
        """Update news events in risk manager"""
        try:
            logger.info("Updating economic calendar events...")
            
            # Fetch events for next 7 days
            events = self.news_client.fetch_events(days_ahead=7)
            
            with self._lock:  # Thread safety
                # Clear old events from risk manager
                self._clear_old_events()
                
                # Add new events to risk manager
                added_count = 0
                for event in events:
                    if self._should_track_event(event):
                        self._add_event_to_risk_manager(event)
                        added_count += 1
                
                self._last_update = datetime.now(timezone.utc)
            
            logger.info(f"Added {added_count} news events to risk manager")
            
            # Log next high impact event
            self._log_next_event()
            
        except Exception as e:
            logger.error(f"Error updating news events: {e}")
    
    def _should_track_event(self, event: EconomicEvent) -> bool:
        """Determine if an event should be tracked"""
        # Only track medium and high impact events
        return event.impact in [NewsImpact.HIGH, NewsImpact.MEDIUM]
    
    def _add_event_to_risk_manager(self, event: EconomicEvent):
        """Convert and add event to risk manager"""
        # Convert to risk manager format
        news_event = NewsEvent(
            event_time=event.event_time,
            currency=event.currency,
            impact=event.impact.value,
            event_name=event.event_name
        )
        
        # Add to risk manager
        self.risk_manager.add_news_event(news_event)
        
        logger.debug(f"Added news event: {event.event_name} ({event.currency}) "
                    f"at {event.event_time} - Impact: {event.impact.value}")
    
    def _clear_old_events(self):
        """Clear old events from risk manager"""
        # The risk manager already has auto-cleanup for events older than 2 hours
        # This is just to ensure we don't accumulate too many events
        current_count = len(self.risk_manager.news_events)
        if current_count > 100:
            logger.warning(f"Too many news events ({current_count}), clearing old ones")
            # Keep only events from now onwards
            now = datetime.now(timezone.utc)
            self.risk_manager.news_events = [
                event for event in self.risk_manager.news_events
                if event.event_time > now
            ]
    
    def _log_next_event(self):
        """Log information about the next high impact event"""
        try:
            is_blackout, next_event = self.news_client.is_news_blackout_period()
            
            if is_blackout and next_event:
                logger.warning(f"Currently in NEWS BLACKOUT for: {next_event.event_name} "
                              f"({next_event.currency}) until {next_event.event_time}")
            else:
                # Get next blackout window
                next_window = self.news_client.get_next_blackout_window()
                if next_window:
                    start, end, event = next_window
                    logger.info(f"Next news blackout: {start} to {end} "
                               f"for {event.event_name} ({event.currency})")
                               
        except Exception as e:
            logger.error(f"Error logging next event: {e}")
    
    def force_update(self):
        """Force an immediate update of news events"""
        logger.info("Forcing news event update...")
        self._update_news_events()
    
    def get_upcoming_events(self, hours: int = 24) -> List[EconomicEvent]:
        """Get upcoming events for display"""
        return self.news_client.get_upcoming_high_impact(hours_ahead=hours)
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            'running': self._running,
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'update_interval': self._update_interval,
            'events_tracked': len(self.risk_manager.news_events),
            'in_blackout': self.news_client.is_news_blackout_period()[0]
        }