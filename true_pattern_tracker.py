#!/usr/bin/env python3
"""
True Pattern Tracker
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

class TruePatternTracker:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.patterns = {}
        
    def track_pattern(self, signal_data):
        """Track pattern using unified logging"""
        try:
            trade_data = {
                'signal_id': signal_data.get('signal_id'),
                'pattern': signal_data.get('pattern'),
                'confidence': signal_data.get('confidence'),
                'symbol': signal_data.get('symbol'),
                'direction': signal_data.get('direction'),
                'entry': signal_data.get('entry'),
                'sl': signal_data.get('sl'),
                'tp': signal_data.get('tp'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Use unified logging
            log_trade(trade_data)
            
            # Track pattern frequency
            pattern = signal_data.get('pattern', 'UNKNOWN')
            self.patterns[pattern] = self.patterns.get(pattern, 0) + 1
            
        except Exception as e:
            logger.error(f"Error tracking pattern: {e}")
    
    def run(self):
        """Main loop"""
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5557")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        logger.info("True pattern tracker running with unified logging...")
        
        while True:
            try:
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                if message.startswith("ELITE_"):
                    parts = message.split(' ', 1)
                    if len(parts) > 1:
                        signal_data = json.loads(parts[1])
                        self.track_pattern(signal_data)
            except zmq.Again:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error: {e}")

if __name__ == "__main__":
    tracker = TruePatternTracker()
    tracker.run()
