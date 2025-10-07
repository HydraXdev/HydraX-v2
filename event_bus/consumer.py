#!/usr/bin/env python3
"""
Simple Event Bus Consumer
Basic implementation for slot management events
"""

import threading
import time
import logging
from typing import Dict, Callable, Any

logger = logging.getLogger(__name__)

class EventConsumer:
    def __init__(self):
        self.subscriptions: Dict[str, Callable] = {}
        self.running = False
        self.thread = None
        
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type with a handler function"""
        self.subscriptions[event_type] = handler
        logger.info(f"📥 Subscribed to event: {event_type}")
        
    def start(self):
        """Start the event consumer (placeholder for now)"""
        self.running = True
        logger.info("🎧 Event consumer started")
        
        # For now, we'll just run a simple heartbeat
        def event_loop():
            while self.running:
                time.sleep(5)
                
        self.thread = threading.Thread(target=event_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the event consumer"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("🛑 Event consumer stopped")
        
    def handle_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle incoming events"""
        if event_type in self.subscriptions:
            try:
                self.subscriptions[event_type](event_data)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {e}")