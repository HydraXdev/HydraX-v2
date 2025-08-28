#!/usr/bin/env python3
"""
ZMQ Telemetry Bridge with Debug Logging
Receives telemetry on port 5556 and republishes on port 5560
"""

import zmq
import json
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TelemetryBridge')

def main():
    context = zmq.Context()
    
    # PULL socket - receives telemetry from EA
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5556")
    logger.info("✅ Bound to port 5556 (PULL from EA)")
    
    # PUB socket - publishes to Elite Guard
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5560")
    logger.info("✅ Bound to port 5560 (PUB to subscribers)")
    
    logger.info("📡 Bridging telemetry...")
    
    message_count = 0
    last_log_time = time.time()
    
    while True:
        try:
            # Receive message
            message = receiver.recv_string()
            message_count += 1
            
            # Parse and log first few messages or every 100th message
            try:
                data = json.loads(message)
                
                # Log first 5 messages in detail, then every 100th message
                if message_count <= 5:
                    logger.info(f"📊 Message {message_count}:")
                    logger.info(f"   Type: {data.get('type', 'unknown')}")
                    logger.info(f"   Keys: {list(data.keys())}")
                    if 'symbol' in data:
                        logger.info(f"   Symbol: {data['symbol']}")
                    if 'bid' in data and 'ask' in data:
                        logger.info(f"   Tick: {data['bid']}/{data['ask']}")
                elif message_count % 100 == 0:
                    # Log summary every 100 messages
                    logger.info(f"📊 Processed {message_count} messages, latest: {data.get('symbol', 'unknown')} at {data.get('timestamp', 'unknown')}")
                elif time.time() - last_log_time > 30:
                    # Also log every 30 seconds to show it's alive
                    logger.info(f"📡 Telemetry bridge active: {message_count} messages processed")
                    last_log_time = time.time()
                
                # Republish as JSON
                publisher.send_json(data)
                
            except json.JSONDecodeError:
                logger.warning(f"Non-JSON message {message_count}: {message[:100]}...")
                # Still republish as string
                publisher.send_string(message)
                
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()