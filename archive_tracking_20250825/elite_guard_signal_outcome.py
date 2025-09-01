#!/usr/bin/env python3
"""
Signal Outcome Monitor - Tracks all signals to TP/SL completion
NO TIMEOUTS - We track every signal until it hits TP or SL
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignalOutcomeMonitor:
    def __init__(self, signal: Dict):
        self.signal = signal
        self.signal_id = signal['signal_id']
        self.symbol = signal['symbol']
        self.entry_price = signal['entry_price']
        self.stop_loss = signal['stop_loss']
        self.take_profit = signal['take_profit']
        self.direction = signal['direction']
        self.start_time = time.time()
        self.outcome = None
        self.completion_time = None
        self.running = True
        
        # ZMQ setup to monitor market data
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://127.0.0.1:5560")
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)
        
        logger.info(f"📊 Monitoring {self.signal_id}: {self.symbol} {self.direction} Entry:{self.entry_price:.5f} SL:{self.stop_loss:.5f} TP:{self.take_profit:.5f}")
    
    def check_outcome(self, current_price: float):
        """Check if signal hit TP or SL"""
        if self.direction == "BUY":
            if current_price >= self.take_profit:
                self.outcome = "WIN"
                self.completion_time = time.time()
                self.running = False
                logger.info(f"✅ WIN: {self.signal_id} hit TP at {current_price:.5f} after {self.completion_time - self.start_time:.0f}s")
                self.log_outcome()
                return True
            elif current_price <= self.stop_loss:
                self.outcome = "LOSS"
                self.completion_time = time.time()
                self.running = False
                logger.info(f"❌ LOSS: {self.signal_id} hit SL at {current_price:.5f} after {self.completion_time - self.start_time:.0f}s")
                self.log_outcome()
                return True
        else:  # SELL
            if current_price <= self.take_profit:
                self.outcome = "WIN"
                self.completion_time = time.time()
                self.running = False
                logger.info(f"✅ WIN: {self.signal_id} hit TP at {current_price:.5f} after {self.completion_time - self.start_time:.0f}s")
                self.log_outcome()
                return True
            elif current_price >= self.stop_loss:
                self.outcome = "LOSS"
                self.completion_time = time.time()
                self.running = False
                logger.info(f"❌ LOSS: {self.signal_id} hit SL at {current_price:.5f} after {self.completion_time - self.start_time:.0f}s")
                self.log_outcome()
                return True
        
        return False
    
    def log_outcome(self):
        """Log the outcome to truth_log.jsonl"""
        try:
            outcome_data = {
                'type': 'signal_outcome',
                'signal_id': self.signal_id,
                'symbol': self.symbol,
                'direction': self.direction,
                'entry_price': self.entry_price,
                'stop_loss': self.stop_loss,
                'take_profit': self.take_profit,
                'outcome': self.outcome,
                'duration_seconds': self.completion_time - self.start_time if self.completion_time else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # Write to truth log
            with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
                f.write(json.dumps(outcome_data) + '\n')
            
            logger.info(f"📝 Outcome logged: {self.signal_id} = {self.outcome}")
            
        except Exception as e:
            logger.error(f"Error logging outcome: {e}")
    
    def monitor_loop(self):
        """Monitor market data until signal completes"""
        logger.info(f"🎯 Starting outcome monitor for {self.signal_id}")
        
        last_log_time = time.time()
        
        while self.running:
            try:
                # Receive market data
                try:
                    data = self.subscriber.recv_json(zmq.NOBLOCK)
                    
                    # Check if this is our symbol
                    if 'symbol' in data and data['symbol'] == self.symbol:
                        if 'bid' in data and 'ask' in data:
                            # Use mid price for outcome determination
                            current_price = (data['bid'] + data['ask']) / 2
                            
                            # Check if we hit TP or SL
                            if self.check_outcome(current_price):
                                break
                            
                            # Log progress every 60 seconds
                            if time.time() - last_log_time >= 60:
                                distance_to_tp = abs(current_price - self.take_profit)
                                distance_to_sl = abs(current_price - self.stop_loss)
                                logger.debug(f"📍 {self.signal_id} Progress: Current={current_price:.5f} TP_dist={distance_to_tp:.5f} SL_dist={distance_to_sl:.5f}")
                                last_log_time = time.time()
                    
                except zmq.Again:
                    # No message, continue
                    time.sleep(0.1)
                    
            except Exception as e:
                if "Resource temporarily unavailable" not in str(e):
                    logger.error(f"Error in monitor loop: {e}")
                time.sleep(1)
        
        # Clean up
        self.subscriber.close()
        self.context.term()
        logger.info(f"🏁 Monitor stopped for {self.signal_id}: Outcome={self.outcome}")

def start_outcome_monitor(signal: Dict):
    """Start monitoring a signal in a separate thread"""
    try:
        monitor = SignalOutcomeMonitor(signal)
        thread = threading.Thread(target=monitor.monitor_loop, daemon=True)
        thread.start()
        logger.info(f"🚀 Outcome monitor started for {signal['signal_id']}")
    except Exception as e:
        logger.error(f"Error starting outcome monitor: {e}")