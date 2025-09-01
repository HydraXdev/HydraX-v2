#!/usr/bin/env python3
"""
Outcome Tracker - Checks what happens to signals 30/60 minutes later
Updates comprehensive_tracking.jsonl with actual market outcomes
"""

import json
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
import zmq
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/outcome_tracker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OutcomeTracker:
    """Tracks actual market outcomes for signals"""
    
    def __init__(self):
        self.tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
        self.context = zmq.Context()
        self.market_subscriber = None
        self.running = False
        self.current_prices = {}
        self.pending_signals = []
        
        # Connect to market data feed
        self.setup_market_feed()
        
    def setup_market_feed(self):
        """Setup ZMQ subscription to market data"""
        try:
            self.market_subscriber = self.context.socket(zmq.SUB)
            self.market_subscriber.connect("tcp://localhost:5560")
            self.market_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
            self.market_subscriber.setsockopt(zmq.RCVTIMEO, 1000)
            logger.info("✅ Connected to market data feed on port 5560")
        except Exception as e:
            logger.error(f"❌ Failed to connect to market data: {e}")
            
    def calculate_pips(self, price_diff: float, pair: str) -> float:
        """Calculate pips based on currency pair"""
        if pair in ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY', 'CADJPY', 'CHFJPY']:
            return abs(price_diff * 100)  # JPY pairs
        elif 'XAU' in pair or 'GOLD' in pair:
            return abs(price_diff * 10)   # Gold
        else:
            return abs(price_diff * 10000)  # Major pairs
            
    def load_pending_signals(self):
        """Load signals that need outcome tracking"""
        pending = []
        current_time = time.time()
        
        try:
            with open(self.tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        signal_time = signal.get('timestamp', 0)
                        
                        # Check if we need to track 30min or 60min outcomes
                        age_minutes = (current_time - signal_time) / 60
                        
                        needs_30min = age_minutes >= 30 and signal.get('outcome_30min') is None
                        needs_60min = age_minutes >= 60 and signal.get('outcome_60min') is None
                        
                        if needs_30min or needs_60min:
                            signal['needs_30min'] = needs_30min
                            signal['needs_60min'] = needs_60min
                            pending.append(signal)
                            
        except FileNotFoundError:
            logger.warning("No tracking file found")
        except Exception as e:
            logger.error(f"Error loading signals: {e}")
            
        logger.info(f"📊 Loaded {len(pending)} signals needing outcome tracking")
        return pending
        
    def update_market_prices(self):
        """Update current market prices from ZMQ feed"""
        try:
            message = self.market_subscriber.recv_string(zmq.NOBLOCK)
            
            # Parse tick data (format: SYMBOL,BID,ASK,TIME)
            if "," in message:
                parts = message.split(",")
                if len(parts) >= 3:
                    symbol = parts[0]
                    bid = float(parts[1])
                    ask = float(parts[2])
                    
                    # Store mid price
                    self.current_prices[symbol] = (bid + ask) / 2
                    
        except zmq.Again:
            pass  # No message available
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
            
    def check_signal_outcome(self, signal: Dict, current_price: float) -> Dict:
        """Check if signal hit TP, SL, or is still pending"""
        direction = signal.get('direction', '').upper()
        entry_price = signal.get('entry_price', 0)
        tp_price = signal.get('tp_price', 0)
        sl_price = signal.get('sl_price', 0)
        pair = signal.get('pair', '')
        
        # Calculate price movement in pips
        price_diff = current_price - entry_price
        pips_moved = self.calculate_pips(price_diff, pair)
        
        # Adjust for direction
        if direction == 'SELL':
            pips_moved = -pips_moved
            
        # Check outcomes based on direction
        outcome = None
        if direction == 'BUY':
            if current_price >= tp_price:
                outcome = 'TP_HIT'
            elif current_price <= sl_price:
                outcome = 'SL_HIT'
            else:
                outcome = 'PENDING'
        elif direction == 'SELL':
            if current_price <= tp_price:
                outcome = 'TP_HIT'
            elif current_price >= sl_price:
                outcome = 'SL_HIT'
            else:
                outcome = 'PENDING'
                
        return {
            'outcome': outcome,
            'pips_moved': pips_moved,
            'current_price': current_price
        }
        
    def update_signal_outcomes(self):
        """Update outcomes for all pending signals"""
        updated_signals = []
        
        for signal in self.pending_signals:
            pair = signal.get('pair', '')
            current_price = self.current_prices.get(pair)
            
            if current_price is None:
                continue  # No price data for this pair
                
            # Check outcome
            result = self.check_signal_outcome(signal, current_price)
            updated = False
            
            # Update 30min outcome if needed
            if signal.get('needs_30min', False) and signal.get('outcome_30min') is None:
                signal['outcome_30min'] = result['outcome']
                signal['pips_moved_30min'] = result['pips_moved']
                updated = True
                logger.info(f"📊 30min outcome: {pair} {signal.get('direction')} -> {result['outcome']} ({result['pips_moved']:.1f} pips)")
                
            # Update 60min outcome if needed  
            if signal.get('needs_60min', False) and signal.get('outcome_60min') is None:
                signal['outcome_60min'] = result['outcome']
                signal['pips_moved_60min'] = result['pips_moved']
                updated = True
                logger.info(f"📊 60min outcome: {pair} {signal.get('direction')} -> {result['outcome']} ({result['pips_moved']:.1f} pips)")
                
            if updated:
                # Remove tracking flags
                signal.pop('needs_30min', None)
                signal.pop('needs_60min', None)
                updated_signals.append(signal)
                
        return updated_signals
        
    def save_updated_signals(self, updated_signals: List[Dict]):
        """Save updated signals back to tracking file"""
        if not updated_signals:
            return
            
        try:
            # Read all current signals
            all_signals = []
            with open(self.tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        all_signals.append(json.loads(line))
                        
            # Update the signals that have new outcomes
            updated_ids = {s.get('signal_id') for s in updated_signals}
            for i, signal in enumerate(all_signals):
                if signal.get('signal_id') in updated_ids:
                    # Find the updated version
                    for updated in updated_signals:
                        if updated.get('signal_id') == signal.get('signal_id'):
                            all_signals[i] = updated
                            break
                            
            # Write back to file
            with open(self.tracking_file, 'w') as f:
                for signal in all_signals:
                    json.dump(signal, f)
                    f.write('\n')
                    
            logger.info(f"💾 Updated {len(updated_signals)} signal outcomes")
            
        except Exception as e:
            logger.error(f"❌ Error saving updated signals: {e}")
            
    def run_outcome_tracking(self):
        """Main outcome tracking loop"""
        logger.info("🎯 Starting outcome tracking...")
        self.running = True
        
        while self.running:
            try:
                # Update market prices
                self.update_market_prices()
                
                # Load pending signals (every 30 seconds)
                if int(time.time()) % 30 == 0:
                    self.pending_signals = self.load_pending_signals()
                    
                # Check and update outcomes
                if self.pending_signals:
                    updated = self.update_signal_outcomes()
                    if updated:
                        self.save_updated_signals(updated)
                        # Remove updated signals from pending list
                        updated_ids = {s.get('signal_id') for s in updated}
                        self.pending_signals = [s for s in self.pending_signals 
                                              if s.get('signal_id') not in updated_ids]
                        
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"❌ Error in outcome tracking loop: {e}")
                time.sleep(5)
                
    def start_tracking(self):
        """Start outcome tracking in background thread"""
        tracking_thread = threading.Thread(target=self.run_outcome_tracking, daemon=True)
        tracking_thread.start()
        logger.info("✅ Outcome tracker started")
        
    def stop_tracking(self):
        """Stop outcome tracking"""
        self.running = False
        if self.market_subscriber:
            self.market_subscriber.close()
        logger.info("🛑 Outcome tracker stopped")
        
    def get_outcome_stats(self) -> Dict:
        """Get outcome tracking statistics"""
        try:
            stats = {
                'total_tracked': 0,
                'outcomes_30min': {'TP_HIT': 0, 'SL_HIT': 0, 'PENDING': 0},
                'outcomes_60min': {'TP_HIT': 0, 'SL_HIT': 0, 'PENDING': 0},
                'win_rate_30min': 0.0,
                'win_rate_60min': 0.0
            }
            
            with open(self.tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        stats['total_tracked'] += 1
                        
                        # Count 30min outcomes
                        outcome_30 = signal.get('outcome_30min')
                        if outcome_30 in stats['outcomes_30min']:
                            stats['outcomes_30min'][outcome_30] += 1
                            
                        # Count 60min outcomes  
                        outcome_60 = signal.get('outcome_60min')
                        if outcome_60 in stats['outcomes_60min']:
                            stats['outcomes_60min'][outcome_60] += 1
                            
            # Calculate win rates
            total_30 = stats['outcomes_30min']['TP_HIT'] + stats['outcomes_30min']['SL_HIT']
            if total_30 > 0:
                stats['win_rate_30min'] = round(stats['outcomes_30min']['TP_HIT'] / total_30 * 100, 1)
                
            total_60 = stats['outcomes_60min']['TP_HIT'] + stats['outcomes_60min']['SL_HIT']
            if total_60 > 0:
                stats['win_rate_60min'] = round(stats['outcomes_60min']['TP_HIT'] / total_60 * 100, 1)
                
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting outcome stats: {e}")
            return {}

def main():
    """Main function for standalone operation"""
    tracker = OutcomeTracker()
    
    try:
        tracker.start_tracking()
        logger.info("🎯 Outcome tracker running...")
        logger.info("Press Ctrl+C to stop")
        
        # Show stats every 5 minutes
        while True:
            time.sleep(300)
            stats = tracker.get_outcome_stats()
            if stats:
                logger.info(f"📊 OUTCOME STATS: {stats['total_tracked']} tracked, "
                           f"30min win rate: {stats['win_rate_30min']}%, "
                           f"60min win rate: {stats['win_rate_60min']}%")
                
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    finally:
        tracker.stop_tracking()

if __name__ == "__main__":
    main()