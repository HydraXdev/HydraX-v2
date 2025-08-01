#!/usr/bin/env python3
# telemetry_pubbridge.py
# 🔁 ZMQ Telemetry Repeater Bridge
# PULL from port 5556 (EA telemetry) → PUB to port 5560 (subscribers)

import zmq
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZMQ-Telemetry-Bridge")

def main():
    context = zmq.Context()

    # Pull from telemetry receiver (which binds to 5556)
    # Since the receiver binds, we need to create another PULL that also binds
    # Or we modify to use PAIR sockets. For now, let's read the log file
    # Actually, we need a different approach - let's use PUB/SUB internally
    
    # For now, let's just bind another PULL on a different port
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5558")  # Temporary internal port
    logger.info("📥 Bound: PULL on port 5558 for internal telemetry")

    # Pub to Elite Guard, Truth Tracker, etc.
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5560")
    logger.info("📡 Bound: PUB on port 5560 for all ZMQ subscribers")

    while True:
        try:
            msg = receiver.recv_json()
            publisher.send_json(msg)
            logger.info(f"🔁 Rebroadcast: {msg.get('symbol', '?')} @ {msg.get('timestamp', '')}")
        except Exception as e:
            logger.error(f"❌ Error rebroadcasting: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()