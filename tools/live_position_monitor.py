#!/usr/bin/env python3
"""
Live Position Monitor
Uses unified logging to /root/HydraX-v2/logs/comprehensive_tracking.jsonl
"""

import zmq
import json
import time
import logging
import sys
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LivePositionMonitor:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.positions = {}
        
    def monitor_position(self, position_data):
        """Monitor position using unified logging"""
        try:
            trade_data = {
                'ticket': position_data.get('ticket'),
                'symbol': position_data.get('symbol'),
                'direction': position_data.get('type', '').upper(),
                'entry': position_data.get('price_open'),
                'volume': position_data.get('volume'),
                'sl': position_data.get('sl'),
                'tp': position_data.get('tp'),
                'profit': position_data.get('profit'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Use unified logging
            log_trade(trade_data)
            
            # Track position
            ticket = position_data.get('ticket')
            if ticket:
                self.positions[ticket] = position_data
            
        except Exception as e:
            logger.error(f"Error monitoring position: {e}")
    
    def run(self):
        """Main loop"""
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5558")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        logger.info("Live position monitor running with unified logging...")
        
        while True:
            try:
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                data = json.loads(message)
                if 'ticket' in data:
                    self.monitor_position(data)
            except zmq.Again:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error: {e}")

if __name__ == "__main__":
    monitor = LivePositionMonitor()
    monitor.run()
