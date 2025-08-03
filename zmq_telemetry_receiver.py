#!/usr/bin/env python3
"""
ZMQ Telemetry Receiver
Binds to port 5556 to receive telemetry from EA
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
logger = logging.getLogger('TelemetryReceiver')

def main():
    context = zmq.Context()
    
    # PULL socket - binds to receive telemetry from EA
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5556")
    logger.info("✅ Telemetry Receiver bound to port 5556")
    logger.info("📡 Waiting for telemetry from EA...")
    
    message_count = 0
    symbols_seen = set()
    
    while True:
        try:
            # Receive message
            message = receiver.recv_string()
            
            # Parse JSON
            try:
                data = json.loads(message)
                message_count += 1
                
                # Extract key info
                msg_type = data.get('type', 'unknown')
                symbol = data.get('symbol', data.get('uuid', 'N/A'))
                
                if 'symbol' in data:
                    symbols_seen.add(data['symbol'])
                
                # Log periodically
                if message_count <= 5 or message_count % 100 == 0:
                    logger.info(f"📊 Message {message_count}: {msg_type} - {symbol}")
                    
                    if msg_type == 'telemetry' or msg_type == 'heartbeat':
                        logger.info(f"   Balance: ${data.get('balance', 0):.2f}, "
                                  f"Equity: ${data.get('equity', 0):.2f}, "
                                  f"Positions: {data.get('positions', 0)}")
                    elif 'bid' in data and 'ask' in data:
                        logger.info(f"   Tick: {data.get('bid')}/{data.get('ask')}")
                
                # Stats every 1000 messages
                if message_count % 1000 == 0:
                    logger.info(f"📈 Stats: {message_count} messages, "
                              f"Symbols: {', '.join(sorted(symbols_seen))}")
                    
            except json.JSONDecodeError:
                logger.warning(f"Non-JSON message: {message[:100]}...")
                
        except zmq.ZMQError as e:
            logger.error(f"ZMQ Error: {e}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()