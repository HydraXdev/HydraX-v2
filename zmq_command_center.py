#!/usr/bin/env python3
"""
ZMQ Command Center - Correct Architecture
We BIND as PUSH on port 5555 (EA connects as PULL)
We BIND as PULL on port 5558 (EA connects as PUSH for confirmations)
"""

import zmq
import json
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CommandCenter')

def main():
    context = zmq.Context()
    
    # PUSH socket for sending commands TO EA (we bind, EA connects)
    command_sender = context.socket(zmq.PUSH)
    command_sender.bind("tcp://*:5555")
    logger.info("✅ Command sender BOUND on port 5555 (EA will PULL from here)")
    
    # PULL socket for receiving confirmations FROM EA (we bind, EA connects)
    confirmation_receiver = context.socket(zmq.PULL)
    confirmation_receiver.bind("tcp://*:5558")
    logger.info("✅ Confirmation receiver BOUND on port 5558 (EA will PUSH to here)")
    
    # Send a test fire command
    fire_command = {
        "type": "fire",
        "signal_id": "FINAL_LIVE_TEST",
        "target_uuid": "COMMANDER_DEV_001",
        "symbol": "EURUSD",
        "action": "BUY",
        "entry": 1.0950,
        "sl": 1.0920,  # 30 pips below
        "tp": 1.1010,  # 60 pips above
        "lot": 0.01,
        "volume": 0.01,
        "sl_pips": 30,
        "tp_pips": 60,
        "magic": 12345,
        "comment": "BITTEN_FINAL",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    json_str = json.dumps(fire_command)
    command_sender.send_string(json_str)
    logger.info(f"🔥 LIVE FIRE COMMAND SENT: {fire_command['signal_id']}")
    logger.info(f"📋 Command details: {fire_command['symbol']} {fire_command['action']} {fire_command['lot']} lots")
    
    # Listen for confirmations
    logger.info("👂 Listening for confirmations on port 5558...")
    confirmation_receiver.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
    
    try:
        confirmation = confirmation_receiver.recv_string()
        logger.info(f"✅ CONFIRMATION RECEIVED: {confirmation}")
    except zmq.Again:
        logger.info("⏱️ No confirmation received within 5 seconds")
    
    # Keep sending heartbeats
    logger.info("💓 Sending heartbeats every 10 seconds...")
    while True:
        heartbeat = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat(),
            "msg": "Command center alive"
        }
        command_sender.send_string(json.dumps(heartbeat))
        logger.info("💓 Heartbeat sent")
        
        # Check for confirmations (non-blocking)
        try:
            confirmation_receiver.setsockopt(zmq.RCVTIMEO, 100)
            confirmation = confirmation_receiver.recv_string()
            logger.info(f"📨 Received: {confirmation}")
        except zmq.Again:
            pass
            
        time.sleep(10)

if __name__ == "__main__":
    main()