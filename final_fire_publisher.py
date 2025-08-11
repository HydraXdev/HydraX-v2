#!/usr/bin/env python3
"""
Final Fire Publisher for EA
This binds to port 5555 and:
1. Sends periodic heartbeats
2. Receives fire signals from Elite Guard (via bridge)
3. Forwards everything to EA
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FirePublisher')

class FirePublisher:
    def __init__(self):
        self.context = zmq.Context()
        self.running = True
        self.signal_queue = deque()
        
    def signal_receiver_loop(self):
        """Receive signals from Elite Guard on port 5557"""
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect("tcp://127.0.0.1:5557")
        subscriber.subscribe(b'')
        
        logger.info("📡 Connected to Elite Guard signals on port 5557")
        
        while self.running:
            try:
                subscriber.setsockopt(zmq.RCVTIMEO, 1000)
                message = subscriber.recv_string()
                logger.info(f"🔍 RAW MESSAGE: {message[:100]}...")  # Debug log
                
                # Elite Guard sends "ELITE_GUARD_SIGNAL {json}"
                if message.startswith("ELITE_GUARD_SIGNAL "):
                    json_str = message[19:]  # Remove prefix
                    signal = json.loads(json_str)
                else:
                    # Try to parse as direct JSON
                    signal = json.loads(message)
                
                logger.info(f"🎯 Received Elite Guard signal: {signal.get('signal_id')}")
                logger.info(f"   Symbol: {signal.get('symbol')} | Direction: {signal.get('direction')}")
                logger.info(f"   Confidence: {signal.get('confidence')}%")
                
                # Create mission using existing athena_signal_dispatcher
                try:
                    from athena_signal_dispatcher import athena_dispatcher
                    mission_result = athena_dispatcher.dispatch_signal_via_athena(signal)
                    if mission_result.get('success'):
                        logger.info(f"📋 Created {mission_result.get('total_missions', 0)} missions")
                except Exception as e:
                    logger.warning(f"Mission creation failed: {e}")
                
                # Convert to fire command format - EA EXPECTS "type": "fire"
                fire_command = {
                    "type": "fire",
                    "target_uuid": signal.get('target_uuid', 'COMMANDER_DEV_001'),
                    "symbol": signal.get('symbol'),
                    "entry": signal.get('entry_price', 0),
                    "sl": signal.get('sl', 0),
                    "tp": signal.get('tp', 0),
                    "lot": signal.get('lot_size', 0.01),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "elite_guard",
                    "signal_id": signal.get('signal_id')
                }
                
                # Add to queue for sending
                self.signal_queue.append(fire_command)
                
            except zmq.Again:
                pass
            except Exception as e:
                logger.error(f"Signal receiver error: {e}")
                
        subscriber.close()
        
    def publisher_loop(self):
        """Send heartbeats and fire signals to EA on port 5555"""
        publisher = self.context.socket(zmq.PUSH)
        publisher.bind("tcp://*:5555")
        
        logger.info("🔥 Fire publisher started on port 5555")
        
        last_heartbeat = time.time()
        
        while self.running:
            # Send any queued signals
            while self.signal_queue:
                signal = self.signal_queue.popleft()
                publisher.send_json(signal)
                logger.info(f"🔥 Sent fire command to EA: {signal['signal_id']}")
                
            # Send heartbeat every 10 seconds
            if time.time() - last_heartbeat >= 10:
                heartbeat = {
                    "type": "heartbeat",
                    "msg": "still alive",
                    "timestamp": int(time.time())
                }
                publisher.send_json(heartbeat)
                logger.debug("💓 Heartbeat sent")
                last_heartbeat = time.time()
                
            time.sleep(0.1)  # Small sleep to prevent CPU spinning
            
        publisher.close()
        
    def run(self):
        """Run the fire publisher"""
        try:
            # Start signal receiver thread
            receiver_thread = threading.Thread(target=self.signal_receiver_loop)
            receiver_thread.start()
            
            # Start publisher thread
            publisher_thread = threading.Thread(target=self.publisher_loop)
            publisher_thread.start()
            
            logger.info("✅ Fire Publisher started successfully")
            logger.info("📡 Elite Guard → 5557 → Fire Publisher → 5555 → EA")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n✅ Fire Publisher stopped")
            self.running = False
        finally:
            self.context.term()

if __name__ == "__main__":
    publisher = FirePublisher()
    publisher.run()