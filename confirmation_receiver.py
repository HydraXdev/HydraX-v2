#!/usr/bin/env python3
"""
Confirmation Receiver for Trade Results
According to the ZMQ pattern: PULL (central) ← PUSH (MT5)
This binds a PULL socket on port 5558 to receive confirmations from MT5
"""

import zmq
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ConfirmationReceiver')

class ConfirmationReceiver:
    def __init__(self):
        self.context = zmq.Context()
        self.running = True
        
    def run(self):
        """Run the confirmation receiver"""
        # PULL socket to receive confirmations from MT5
        # Pattern: PULL (central) ← PUSH (MT5)
        receiver = self.context.socket(zmq.PULL)
        receiver.bind("tcp://*:5558")
        
        logger.info("📡 Confirmation receiver started on port 5558")
        logger.info("🔄 Pattern: PULL (central) ← PUSH (MT5)")
        logger.info("⏳ Waiting for trade confirmations...")
        
        while self.running:
            try:
                # Set timeout to prevent blocking forever
                receiver.setsockopt(zmq.RCVTIMEO, 1000)
                
                # Receive the confirmation
                message = receiver.recv_json()
                
                logger.info(f"✅ Trade confirmation received!")
                logger.info(f"   Signal ID: {message.get('signal_id')}")
                logger.info(f"   Result: {message.get('result', 'UNKNOWN')}")
                logger.info(f"   Ticket: {message.get('ticket')}")
                logger.info(f"   Symbol: {message.get('symbol')}")
                logger.info(f"   Volume: {message.get('volume')}")
                logger.info(f"   Price: {message.get('price')}")
                logger.info(f"   Message: {message.get('message')}")
                
                # Log execution to truth log
                if message.get('status') == 'success':
                    import json
                    from datetime import datetime
                    execution_entry = {
                        'signal_id': message.get('signal_id', 'UNKNOWN'),
                        'action': 'trade_executed',
                        'ticket': message.get('ticket'),
                        'price': message.get('price'),
                        'executed_at': datetime.now().isoformat(),
                        'user_uuid': message.get('user_uuid'),
                        'status': 'executed'
                    }
                    with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
                        f.write(json.dumps(execution_entry) + '\n')
                    logger.info(f"   📝 Logged execution to truth log")
                logger.info(f"   Raw data: {json.dumps(message, indent=2)}")
                
                # Log to a file for persistence
                with open('/tmp/trade_confirmations.jsonl', 'a') as f:
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'confirmation': message
                    }
                    f.write(json.dumps(log_entry) + '\n')
                    
            except zmq.Again:
                # Timeout - no message received, continue
                pass
            except KeyboardInterrupt:
                logger.info("\n✅ Confirmation receiver stopped")
                break
            except Exception as e:
                logger.error(f"Error receiving confirmation: {e}")
                
        receiver.close()
        self.context.term()

if __name__ == "__main__":
    receiver = ConfirmationReceiver()
    receiver.run()