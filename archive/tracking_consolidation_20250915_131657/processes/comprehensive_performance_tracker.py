#!/usr/bin/env python3
"""
Comprehensive Performance Tracker
Uses unified logging to /root/HydraX-v2/logs/comprehensive_tracking.jsonl
"""

import zmq
import json
import time
import logging
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent directory for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensivePerformanceTracker:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.stats = defaultdict(lambda: defaultdict(int))
        self.running = False
        
    def process_signal(self, signal_data):
        """Process signal and log using unified function"""
        try:
            # Map signal data to unified format
            trade_data = {
                'signal_id': signal_data.get('signal_id'),
                'pattern': signal_data.get('pattern'),
                'confidence': signal_data.get('confidence'),
                'symbol': signal_data.get('symbol'),
                'direction': signal_data.get('direction'),
                'entry': signal_data.get('entry'),
                'sl': signal_data.get('sl'),
                'tp': signal_data.get('tp'),
                'session': signal_data.get('session'),
                'citadel_score': signal_data.get('citadel_score', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            # Use unified logging
            log_trade(trade_data)
            
            # Update stats
            self.stats['total']['count'] += 1
            self.stats['patterns'][signal_data.get('pattern', 'UNKNOWN')] += 1
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    def run(self):
        """Main tracking loop"""
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5557")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        self.running = True
        logger.info("Performance tracker running with unified logging...")
        
        while self.running:
            try:
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                if message.startswith("ELITE_"):
                    parts = message.split(' ', 1)
                    if len(parts) > 1:
                        signal_data = json.loads(parts[1])
                        self.process_signal(signal_data)
            except zmq.Again:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error: {e}")

if __name__ == "__main__":
    tracker = ComprehensivePerformanceTracker()
    tracker.run()
