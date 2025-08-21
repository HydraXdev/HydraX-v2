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
    
    while True:
        try:
            # Receive message
            message = receiver.recv_string()
            message_count += 1
            
            # Check for OHLC messages first
            if message.startswith("OHLC "):
                # OHLC message format: "OHLC {json}"
                publisher.send_string(message)  # Republish as-is for Elite Guard
                
                # Log OHLC messages
                if message_count % 100 == 1:  # Log every 100th OHLC
                    try:
                        ohlc_data = json.loads(message[5:])
                        logger.info(f"📊 OHLC: {ohlc_data.get('symbol')} {ohlc_data.get('timeframe')}")
                    except:
                        pass
                        
            elif message.startswith("HEARTBEAT"):
                # Republish heartbeat
                publisher.send_string(message)
                if message_count % 30 == 0:
                    logger.info(f"💓 Heartbeat #{message_count}")
                    
            else:
                # Try to parse as JSON (tick data)
                try:
                    data = json.loads(message)
                    
                    # Log first 5 messages in detail
                    if message_count <= 5:
                        logger.info(f"📊 Message {message_count}:")
                        logger.info(f"   Type: {data.get('type', 'unknown')}")
                        logger.info(f"   Keys: {list(data.keys())}")
                        if 'symbol' in data:
                            logger.info(f"   Symbol: {data['symbol']}")
                        if 'bid' in data and 'ask' in data:
                            logger.info(f"   Tick: {data['bid']}/{data['ask']}")
                    
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