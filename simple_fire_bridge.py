#!/usr/bin/env python3
"""
Simple Fire Bridge - Direct webapp to EA bridge
Receives fire commands on port 5554, forwards to EA on port 5555
"""

import zmq
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SimpleFire')

def main():
    context = zmq.Context()
    
    # Receive commands from webapp
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://127.0.0.1:5554")
    logger.info("📡 Listening for webapp commands on port 5554")
    
    # Send to EA
    sender = context.socket(zmq.PUSH)
    sender.bind("tcp://*:5555")
    logger.info("🎯 Ready to send to EA on port 5555")
    
    while True:
        try:
            # Get command from webapp
            cmd = receiver.recv_json()
            logger.info(f"📨 Received: {cmd.get('symbol')} {cmd.get('direction')} signal_id={cmd.get('signal_id')}")
            
            # Convert to EA format
            ea_cmd = {
                "type": "fire",
                "target_uuid": cmd.get("target_uuid", "COMMANDER_DEV_001"),
                "symbol": cmd.get("symbol"),
                "direction": cmd.get("direction", "BUY").upper(),
                "entry": cmd.get("entry_price", 0),
                "sl": cmd.get("stop_loss", 0),
                "tp": cmd.get("take_profit", 0),
                "lot": cmd.get("lot_size", 0.01),
                "timestamp": datetime.utcnow().isoformat(),
                "signal_id": cmd.get("signal_id"),
                "fire_id": cmd.get("fire_id"),
                "user_id": cmd.get("user_id")
            }
            
            # Send to EA
            sender.send_json(ea_cmd)
            logger.info(f"✅ Forwarded to EA: {ea_cmd['symbol']} {ea_cmd['direction']} lot={ea_cmd['lot']}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            
if __name__ == "__main__":
    logger.info("🚀 Starting Simple Fire Bridge")
    main()