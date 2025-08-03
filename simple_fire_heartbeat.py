#!/usr/bin/env python3
"""
Simple Fire Heartbeat Publisher
Sends periodic heartbeats on port 5555 to keep EA alive
"""

import zmq
import json
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FireHeartbeat')

def main():
    context = zmq.Context()
    
    # PUSH socket - EA connects to this
    publisher = context.socket(zmq.PUSH)
    publisher.bind("tcp://*:5555")
    
    logger.info("✅ Fire heartbeat publisher started on port 5555")
    logger.info("📡 Sending heartbeats every 10 seconds")
    
    try:
        while True:
            # Send heartbeat
            heartbeat = {
                "type": "heartbeat",
                "msg": "still alive",
                "timestamp": int(time.time())
            }
            
            publisher.send_json(heartbeat)
            logger.info("💓 Heartbeat sent")
            
            # Wait 10 seconds
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        publisher.close()
        context.term()

if __name__ == "__main__":
    main()