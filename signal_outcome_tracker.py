#!/usr/bin/env python3
"""
SIGNAL OUTCOME TRACKER
Tracks ALL signals to their theoretical outcome regardless of execution
Monitors market prices to determine if TP or SL would have been hit
"""

import zmq
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SignalOutcomeTracker')

class SignalOutcomeTracker:
    def __init__(self):
        self.context = zmq.Context()
        self.truth_log = "/root/HydraX-v2/truth_log.jsonl"
        self.active_signals = {}  # Track all active signals
        self.running = True
        
        # Subscribe to market data
        self.market_subscriber = self.context.socket(zmq.SUB)
        self.market_subscriber.connect("tcp://127.0.0.1:5560")
        self.market_subscriber.subscribe(b'')
        self.market_subscriber.setsockopt(zmq.RCVTIMEO, 1000)
        
        # Current market prices
        self.current_prices = {}
        
    def load_active_signals(self):
        """Load all pending signals from truth log"""
        try:
            with open(self.truth_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        # Track signals that are pending and not completed
                        if entry.get('signal_id') and entry.get('status') == 'pending' and not entry.get('completed'):
                            signal_id = entry['signal_id']
                            if signal_id not in self.active_signals:
                                self.active_signals[signal_id] = entry
                                logger.info(f"📊 Tracking signal: {signal_id} - {entry.get('symbol')} {entry.get('direction')}")
                        # Remove completed signals
                        elif entry.get('completed') == True:
                            signal_id = entry.get('signal_id')
                            if signal_id in self.active_signals:
                                del self.active_signals[signal_id]
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            logger.error(f"Truth log not found: {self.truth_log}")
            
    def market_data_loop(self):
        """Monitor market prices"""
        while self.running:
            try:
                message = self.market_subscriber.recv_string()
                
                # Parse market data
                if "tick" in message.lower():
                    data = json.loads(message.split(maxsplit=1)[1] if ' ' in message else message)
                    symbol = data.get('symbol')
                    bid = data.get('bid')
                    ask = data.get('ask')
                    
                    if symbol and bid and ask:
                        self.current_prices[symbol] = {
                            'bid': bid,
                            'ask': ask,
                            'mid': (bid + ask) / 2,
                            'timestamp': datetime.now()
                        }
                        
                        # Check if any signals hit their targets
                        self.check_signal_outcomes(symbol)
                        
            except zmq.Again:
                pass
            except Exception as e:
                logger.debug(f"Market data error: {e}")
                
    def check_signal_outcomes(self, symbol: str):
        """Check if any signals for this symbol hit TP or SL"""
        current_price = self.current_prices.get(symbol, {}).get('mid')
        if not current_price:
            return
            
        for signal_id, signal in list(self.active_signals.items()):
            if signal.get('symbol') != symbol:
                continue
                
            # Check if signal has been active for at least 1 minute
            generated_at = signal.get('generated_at')
            if generated_at:
                signal_time = datetime.fromisoformat(generated_at)
                if (datetime.now() - signal_time).total_seconds() < 60:
                    continue  # Too early to check
                    
            direction = signal.get('direction', '').upper()
            entry_price = signal.get('entry_price', 0)
            sl = signal.get('sl', 0)
            tp = signal.get('tp', 0)
            
            if not all([entry_price, sl, tp]):
                continue
                
            # Check if TP or SL hit
            outcome = None
            pips = 0
            
            if direction == 'BUY':
                if current_price >= tp:
                    outcome = 'win'
                    pips = round((tp - entry_price) * 10000, 1)  # Convert to pips
                    logger.info(f"🎯 WIN: {signal_id} hit TP at {current_price} (+{pips} pips)")
                elif current_price <= sl:
                    outcome = 'loss'
                    pips = round((sl - entry_price) * 10000, 1)  # Negative pips
                    logger.info(f"❌ LOSS: {signal_id} hit SL at {current_price} ({pips} pips)")
                    
            elif direction == 'SELL':
                if current_price <= tp:
                    outcome = 'win'
                    pips = round((entry_price - tp) * 10000, 1)
                    logger.info(f"🎯 WIN: {signal_id} hit TP at {current_price} (+{pips} pips)")
                elif current_price >= sl:
                    outcome = 'loss'
                    pips = round((entry_price - sl) * 10000, 1)  # Negative pips
                    logger.info(f"❌ LOSS: {signal_id} hit SL at {current_price} ({pips} pips)")
                    
            if outcome:
                self.log_signal_outcome(signal_id, outcome, pips, current_price)
                del self.active_signals[signal_id]
                
    def log_signal_outcome(self, signal_id: str, outcome: str, pips: float, exit_price: float):
        """Log the outcome to truth log"""
        try:
            outcome_entry = {
                'signal_id': signal_id,
                'status': 'completed',
                'completed': True,
                'outcome': outcome,
                'completed_at': datetime.now().isoformat(),
                'exit_price': exit_price,
                'pips_result': pips,
                'exit_type': 'tp_hit' if outcome == 'win' else 'sl_hit',
                'theoretical': True  # Mark as theoretical outcome
            }
            
            with open(self.truth_log, 'a') as f:
                f.write(json.dumps(outcome_entry) + '\n')
                
            logger.info(f"📝 Logged {outcome} for {signal_id}: {pips} pips")
            
        except Exception as e:
            logger.error(f"Failed to log outcome: {e}")
            
    def check_timeouts(self):
        """Check for signals that should timeout"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for signal_id, signal in list(self.active_signals.items()):
                    generated_at = signal.get('generated_at')
                    if not generated_at:
                        continue
                        
                    signal_time = datetime.fromisoformat(generated_at)
                    runtime = (current_time - signal_time).total_seconds()
                    
                    # Check 2h5m timeout
                    if runtime >= 7500:  # 2 hours 5 minutes
                        logger.info(f"⏰ Timeout: {signal_id} after {runtime/3600:.1f} hours")
                        
                        # Log timeout
                        timeout_entry = {
                            'signal_id': signal_id,
                            'status': 'timeout_closed',
                            'completed': True,
                            'outcome': 'timeout',
                            'completed_at': current_time.isoformat(),
                            'runtime_seconds': runtime,
                            'runtime_hours': runtime / 3600,
                            'exit_type': 'timeout',
                            'pips_result': 0,
                            'theoretical': True
                        }
                        
                        with open(self.truth_log, 'a') as f:
                            f.write(json.dumps(timeout_entry) + '\n')
                            
                        del self.active_signals[signal_id]
                        
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Timeout check error: {e}")
                time.sleep(60)
                
    def periodic_reload(self):
        """Periodically reload signals from truth log"""
        while self.running:
            time.sleep(30)  # Reload every 30 seconds
            self.load_active_signals()
            logger.debug(f"📊 Tracking {len(self.active_signals)} active signals")
            
    def run(self):
        """Run the outcome tracker"""
        logger.info("🎯 Signal Outcome Tracker started")
        logger.info("📊 Tracking ALL signals to theoretical outcomes")
        
        # Load initial signals
        self.load_active_signals()
        logger.info(f"📋 Loaded {len(self.active_signals)} active signals")
        
        # Start threads
        market_thread = threading.Thread(target=self.market_data_loop, daemon=True)
        timeout_thread = threading.Thread(target=self.check_timeouts, daemon=True)
        reload_thread = threading.Thread(target=self.periodic_reload, daemon=True)
        
        market_thread.start()
        timeout_thread.start()
        reload_thread.start()
        
        logger.info("✅ All tracking threads started")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Tracker stopped")
            self.running = False
        finally:
            self.context.term()

if __name__ == "__main__":
    tracker = SignalOutcomeTracker()
    tracker.run()