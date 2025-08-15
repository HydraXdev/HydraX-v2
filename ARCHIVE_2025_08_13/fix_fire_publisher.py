#!/usr/bin/env python3
"""
Fixed Fire Publisher - handles empty messages and heartbeats properly
The issue: ZMQ heartbeats or empty keepalive messages are being received
Solution: Filter out empty messages and only process valid signals
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
logger = logging.getLogger('FixedFirePublisher')

class FixedFirePublisher:
    def __init__(self):
        self.context = zmq.Context()
        self.running = True
        self.signal_queue = deque()
        
    def signal_receiver_loop(self):
        """Receive signals from Elite Guard on port 5557 - FIXED VERSION"""
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect("tcp://127.0.0.1:5557")
        subscriber.subscribe(b'')
        
        logger.info("📡 Connected to Elite Guard signals on port 5557")
        
        empty_count = 0
        valid_count = 0
        
        while self.running:
            try:
                subscriber.setsockopt(zmq.RCVTIMEO, 1000)
                message = subscriber.recv_string()
                
                # FIXED: Skip empty messages
                if not message or message.strip() == "":
                    empty_count += 1
                    if empty_count % 10 == 0:  # Log every 10th empty
                        logger.debug(f"Received {empty_count} empty messages (heartbeats/keepalives)")
                    continue
                
                # FIXED: Better parsing logic
                signal = None
                
                # Check for Elite Guard format
                if message.startswith("ELITE_GUARD_SIGNAL "):
                    json_str = message[19:]  # Remove prefix
                    if json_str.strip():  # Only parse if not empty
                        try:
                            signal = json.loads(json_str)
                            logger.info(f"✅ Parsed Elite Guard signal: {signal.get('signal_id')}")
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error for Elite Guard signal: {e}")
                            logger.debug(f"   Problematic JSON: {json_str[:100]}...")
                            continue
                            
                # Try direct JSON parsing
                elif message.startswith("{"):
                    try:
                        signal = json.loads(message)
                        logger.info(f"✅ Parsed direct JSON signal: {signal.get('signal_id')}")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error for direct message: {e}")
                        logger.debug(f"   Problematic message: {message[:100]}...")
                        continue
                        
                # Skip unknown formats
                else:
                    logger.debug(f"Unknown message format: {message[:50]}...")
                    continue
                
                # Process valid signal
                if signal and isinstance(signal, dict):
                    valid_count += 1
                    logger.info(f"🎯 Processing signal #{valid_count}: {signal.get('signal_id')}")
                    logger.info(f"   Symbol: {signal.get('symbol')} | Direction: {signal.get('direction')}")
                    logger.info(f"   Confidence: {signal.get('confidence')}%")
                    
                    # Convert to fire command format
                    fire_command = {
                        "type": "signal",
                        "signal_id": signal.get('signal_id'),
                        "symbol": signal.get('symbol', signal.get('pair')),  # Handle both fields
                        "action": signal.get('direction', '').lower(),
                        "lot": 0.01,
                        "sl": signal.get('stop_loss_pips', signal.get('stop_pips', 50)),
                        "tp": signal.get('target_pips', 100),
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "elite_guard",
                        "confidence": signal.get('confidence', 0)
                    }
                    
                    self.signal_queue.append(fire_command)
                    logger.info(f"📦 Queued fire command for EA")
                    
            except zmq.Again:
                # Timeout - normal
                pass
            except UnicodeDecodeError as e:
                logger.error(f"Unicode decode error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                
        logger.info(f"📊 Receiver stopped. Valid: {valid_count}, Empty: {empty_count}")
        subscriber.close()
        
    def publisher_loop(self):
        """Send fire commands to EA on port 5555"""
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
                    "msg": "fire_publisher_alive",
                    "timestamp": int(time.time())
                }
                publisher.send_json(heartbeat)
                last_heartbeat = time.time()
                logger.debug("💓 Heartbeat sent to EA")
                
            time.sleep(0.1)  # Small sleep to prevent CPU spinning
            
        publisher.close()
        
    def run(self):
        """Run both loops in threads"""
        receiver_thread = threading.Thread(target=self.signal_receiver_loop)
        publisher_thread = threading.Thread(target=self.publisher_loop)
        
        receiver_thread.start()
        publisher_thread.start()
        
        logger.info("✅ Fixed Fire Publisher started successfully")
        logger.info("📡 Elite Guard → 5557 → Fire Publisher → 5555 → EA")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False
            
        receiver_thread.join()
        publisher_thread.join()
        self.context.term()

if __name__ == "__main__":
    publisher = FixedFirePublisher()
    publisher.run()