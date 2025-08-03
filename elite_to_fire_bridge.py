#!/usr/bin/env python3
"""
Elite Guard to Fire Bridge
Listens for signals from Elite Guard on port 5557
Converts them to fire commands and sends to port 5555
"""

import zmq
import json
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EliteToFireBridge')

def main():
    context = zmq.Context()
    
    # SUB socket to receive Elite Guard signals
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5557")
    subscriber.subscribe(b'')  # Subscribe to all messages
    
    # PUSH socket to send fire commands (connects to existing publisher)
    # Note: We connect, not bind, because fire_heartbeat.py already binds to 5555
    fire_sender = context.socket(zmq.PUSH)
    fire_sender.connect("tcp://127.0.0.1:5555")
    
    logger.info("✅ Elite Guard to Fire Bridge started")
    logger.info("📡 Listening for Elite Guard signals on port 5557")
    logger.info("🔥 Will forward fire commands to port 5555")
    
    try:
        while True:
            try:
                # Receive Elite Guard signal with timeout
                subscriber.setsockopt(zmq.RCVTIMEO, 1000)
                message = subscriber.recv_string()
                
                # Parse the signal
                signal = json.loads(message)
                
                logger.info(f"🎯 Received Elite Guard signal: {signal.get('signal_id', 'N/A')}")
                logger.info(f"   Symbol: {signal.get('symbol')} | Direction: {signal.get('direction')} | Confidence: {signal.get('confidence')}%")
                
                # Convert to fire command format
                fire_command = {
                    "type": "signal",
                    "signal_id": signal.get('signal_id'),
                    "symbol": signal.get('symbol'),
                    "action": signal.get('direction', '').lower(),  # buy/sell
                    "lot": 0.01,  # Default lot size
                    "sl": signal.get('stop_loss_pips', 50),
                    "tp": signal.get('target_pips', 100),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "elite_guard",
                    "confidence": signal.get('confidence', 0)
                }
                
                # Send fire command
                fire_sender.send_json(fire_command)
                logger.info(f"🔥 Forwarded fire command to port 5555")
                
            except zmq.Again:
                # No message received, continue
                pass
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse signal: {e}")
            except Exception as e:
                logger.error(f"Bridge error: {e}")
                
    except KeyboardInterrupt:
        logger.info("\n✅ Bridge stopped")
    finally:
        subscriber.close()
        fire_sender.close()
        context.term()

if __name__ == "__main__":
    main()