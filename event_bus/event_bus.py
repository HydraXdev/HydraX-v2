#!/usr/bin/env python3
"""
BITTEN Event Bus - Professional ZMQ Publisher
Runs on port 5570 (parallel to existing system)
"""

import zmq
import json
import time
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/event_bus.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EventBus')


class EventType(Enum):
    """Standard event types for the BITTEN system"""
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_EXPIRED = "signal_expired"
    FIRE_COMMAND = "fire_command"
    TRADE_EXECUTED = "trade_executed"
    TRADE_CONFIRMED = "trade_confirmed"
    BALANCE_UPDATE = "balance_update"
    SYSTEM_HEALTH = "system_health"
    USER_ACTION = "user_action"
    MARKET_DATA = "market_data"
    PATTERN_DETECTED = "pattern_detected"


@dataclass
class Event:
    """Standard event structure for the BITTEN event bus"""
    event_type: str
    timestamp: float
    source: str
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())


class EventBus:
    """Professional ZMQ Event Bus Broker - Receives and forwards events"""
    
    def __init__(self, pub_port: int = 5570, pull_port: int = 5571):
        self.pub_port = pub_port
        self.pull_port = pull_port
        self.context = None
        self.publisher = None
        self.receiver = None
        self.running = False
        self.stats = {
            'events_published': 0,
            'events_received': 0,
            'start_time': None,
            'last_event_time': None
        }
    
    def start(self):
        """Initialize and start the event bus broker"""
        try:
            logger.info(f"🚀 Starting BITTEN Event Bus Broker - PUB:{self.pub_port}, PULL:{self.pull_port}")
            
            # Initialize ZMQ context
            self.context = zmq.Context()
            
            # Publisher socket (for broadcasting events to subscribers)
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(f"tcp://*:{self.pub_port}")
            
            # Receiver socket (for receiving events from clients)
            self.receiver = self.context.socket(zmq.PULL)
            self.receiver.bind(f"tcp://*:{self.pull_port}")
            
            # Set socket options for reliability
            self.publisher.setsockopt(zmq.SNDHWM, 1000)  # High water mark
            self.publisher.setsockopt(zmq.LINGER, 100)   # Linger time
            self.receiver.setsockopt(zmq.RCVHWM, 1000)   # High water mark
            
            self.running = True
            self.stats['start_time'] = time.time()
            
            logger.info(f"✅ Event Bus Broker started - Receiving on :{self.pull_port}, Publishing on :{self.pub_port}")
            
            # Publish startup event
            self.publish_event(
                event_type=EventType.SYSTEM_HEALTH.value,
                source="event_bus",
                data={
                    "component": "event_bus",
                    "status": "started",
                    "pub_port": self.pub_port,
                    "pull_port": self.pull_port,
                    "message": "Event Bus Broker initialized successfully"
                }
            )
            
            # Run the main broker loop
            self.run_broker_loop()
            
        except Exception as e:
            logger.error(f"❌ Failed to start Event Bus Broker: {e}")
            self.stop()
            raise
    
    def publish_event(self, event_type: str, source: str, data: Dict[str, Any], 
                     correlation_id: Optional[str] = None, user_id: Optional[str] = None):
        """Publish an event to the bus"""
        if not self.running or not self.publisher:
            logger.warning("⚠️ Event Bus not running, cannot publish event")
            return False
        
        try:
            # Create event
            event = Event(
                event_type=event_type,
                timestamp=time.time(),
                source=source,
                data=data,
                correlation_id=correlation_id,
                user_id=user_id
            )
            
            # Publish event
            topic = f"bitten.{event_type}"
            message = event.to_json()
            
            self.publisher.send_multipart([
                topic.encode('utf-8'),
                message.encode('utf-8')
            ])
            
            # Update stats
            self.stats['events_published'] += 1
            self.stats['last_event_time'] = time.time()
            
            logger.debug(f"📡 Published event: {topic}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            return False
    
    def run_broker_loop(self):
        """Run the main broker loop - receive events and forward them"""
        logger.info("🔄 Starting broker loop - Receiving from PULL, Publishing to PUB")
        
        # Use a poller to handle multiple sockets
        poller = zmq.Poller()
        poller.register(self.receiver, zmq.POLLIN)
        
        last_heartbeat = time.time()
        
        while self.running:
            try:
                # Poll for events with 1 second timeout
                socks = dict(poller.poll(1000))
                
                # Check for received events
                if self.receiver in socks:
                    # Receive the event (expecting topic and message)
                    message = self.receiver.recv_string()
                    
                    try:
                        # Parse the received event
                        event_data = json.loads(message)
                        
                        # Extract event details
                        event_type = event_data.get('event_type', 'unknown')
                        topic = f"bitten.{event_type}"
                        
                        # Forward the event to all subscribers
                        self.publisher.send_multipart([
                            topic.encode('utf-8'),
                            message.encode('utf-8')
                        ])
                        
                        # Update stats
                        self.stats['events_received'] += 1
                        self.stats['events_published'] += 1
                        self.stats['last_event_time'] = time.time()
                        
                        logger.debug(f"📡 Forwarded event: {topic} from {event_data.get('source', 'unknown')}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON received: {e}")
                    except Exception as e:
                        logger.error(f"❌ Error forwarding event: {e}")
                
                # Send periodic heartbeat (every 30 seconds)
                current_time = time.time()
                if current_time - last_heartbeat >= 30:
                    self.publish_event(
                        event_type=EventType.SYSTEM_HEALTH.value,
                        source="event_bus",
                        data={
                            "component": "event_bus",
                            "status": "running",
                            "uptime": current_time - self.stats['start_time'],
                            "events_published": self.stats['events_published'],
                            "events_received": self.stats['events_received'],
                            "pub_port": self.pub_port,
                            "pull_port": self.pull_port
                        }
                    )
                    last_heartbeat = current_time
                
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"❌ Broker loop error: {e}")
                time.sleep(1)
        
        self.stop()
    
    def stop(self):
        """Gracefully stop the event bus broker"""
        logger.info("🛑 Stopping Event Bus Broker")
        
        if self.running:
            # Publish shutdown event
            try:
                self.publish_event(
                    event_type=EventType.SYSTEM_HEALTH.value,
                    source="event_bus",
                    data={
                        "component": "event_bus",
                        "status": "stopping",
                        "uptime": time.time() - self.stats['start_time'] if self.stats['start_time'] else 0,
                        "events_published": self.stats['events_published'],
                        "events_received": self.stats['events_received']
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to publish shutdown event: {e}")
        
        self.running = False
        
        # Clean up ZMQ resources
        if self.publisher:
            self.publisher.close()
        if self.receiver:
            self.receiver.close()
        if self.context:
            self.context.term()
        
        logger.info("✅ Event Bus Broker stopped successfully")


# Event Bus API for other components to use
class EventBusClient:
    """Client interface for sending events to the event bus broker"""
    
    def __init__(self, push_port: int = 5571):
        self.push_port = push_port
        self.context = zmq.Context()
        self.pusher = self.context.socket(zmq.PUSH)
        self.pusher.connect(f"tcp://localhost:{push_port}")
        
        # Give ZMQ time to establish connection
        time.sleep(0.1)
    
    def publish(self, event_type: str, source: str, data: Dict[str, Any], 
               correlation_id: Optional[str] = None, user_id: Optional[str] = None):
        """Send an event to the event bus broker"""
        try:
            event = Event(
                event_type=event_type,
                timestamp=time.time(),
                source=source,
                data=data,
                correlation_id=correlation_id,
                user_id=user_id
            )
            
            # Send the event as JSON to the broker
            message = event.to_json()
            self.pusher.send_string(message)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Client send failed: {e}")
            return False
    
    def close(self):
        """Close the client connection"""
        if self.pusher:
            self.pusher.close()
        if self.context:
            self.context.term()


def main():
    """Main entry point for the event bus broker"""
    logger.info("🚀 BITTEN Event Bus Broker starting...")
    
    try:
        event_bus = EventBus(pub_port=5570, pull_port=5571)
        event_bus.start()
    except KeyboardInterrupt:
        logger.info("👋 Event Bus Broker shutdown requested")
    except Exception as e:
        logger.error(f"💥 Event Bus Broker crashed: {e}")
        raise


if __name__ == "__main__":
    main()