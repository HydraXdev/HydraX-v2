#!/usr/bin/env python3
"""
ZMQ Telemetry Receiver with Publisher
Receives telemetry on port 5556 (PULL) and republishes on port 5560 (PUB)
"""

import zmq
import json
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TelemetryReceiverPub')

def main():
    context = zmq.Context()
    
    # PULL socket - binds to receive telemetry from EA
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5556")
    logger.info("✅ Telemetry Receiver bound to port 5556 (PULL from EA)")
    
    # PUB socket - publishes to Elite Guard and other subscribers
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5560")
    logger.info("✅ Telemetry Publisher bound to port 5560 (PUB to subscribers)")
    
    logger.info("📡 Bridging telemetry from EA (5556) to subscribers (5560)...")
    
    message_count = 0
    symbols_seen = set()
    last_log_time = time.time()
    
    while True:
        try:
            # Receive message from EA
            message = receiver.recv_string()
            
            # Parse and republish
            try:
                data = json.loads(message)
                message_count += 1
                
                # Track symbols
                if 'symbol' in data:
                    symbols_seen.add(data['symbol'])
                
                # Republish to all subscribers
                publisher.send_json(data)
                
                # Log periodically (every 5 seconds)
                current_time = time.time()
                if current_time - last_log_time >= 5:
                    logger.info(f"📊 Bridged {message_count} messages | "
                              f"Symbols: {', '.join(sorted(symbols_seen))}")
                    last_log_time = current_time
                    
            except json.JSONDecodeError:
                logger.warning(f"Non-JSON message: {message[:100]}...")
                # Still republish as string
                publisher.send_string(message)
                
        except zmq.ZMQError as e:
            logger.error(f"ZMQ Error: {e}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()