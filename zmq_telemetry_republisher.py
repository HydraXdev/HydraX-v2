#!/usr/bin/env python3
"""
ZMQ Telemetry Republisher - Bridges EA data to Elite Guard
Receives from EA on PULL socket, republishes on PUB socket
"""

import zmq
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TelemetryRepublisher')

def main():
    context = zmq.Context()
    
    # PULL from EA telemetry (same as telemetry daemon)
    receiver = context.socket(zmq.PULL)
    receiver.connect("tcp://localhost:5556")  # Connect to EA telemetry stream
    logger.info("✅ Connected to EA telemetry stream on port 5556")
    
    # PUB to subscribers (Elite Guard, Black Box, future sniper systems)
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5560")  # Shared feed port for all consumers
    logger.info("✅ Publishing telemetry on port 5560")
    
    messages = 0
    while True:
        try:
            # Get message from EA
            message = receiver.recv_string()
            messages += 1
            
            # Republish immediately
            publisher.send_string(message)
            
            if messages % 100 == 0:
                logger.info(f"📡 Republished {messages} messages")
                
        except Exception as e:
            logger.error(f"Error: {e}")
            
if __name__ == "__main__":
    main()