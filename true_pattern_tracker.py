#!/usr/bin/env python3
"""
TRUE PATTERN TRACKER - The ONLY tracker that matters
Tracks every signal from birth to death and calculates if patterns are profitable
"""

import zmq
import json
import time
from datetime import datetime
from collections import defaultdict
import os
import sys

class TruePatternTracker:
    def __init__(self):
        self.context = zmq.Context()
        self.active_signals = {}  # Tracking live signals
        self.pattern_stats = defaultdict(lambda: {
            'total': 0, 'wins': 0, 'losses': 0, 'pending': 0,
            'total_r_won': 0, 'total_r_lost': 0,
            'by_session': defaultdict(lambda: {'wins': 0, 'losses': 0}),
            'by_volatility': defaultdict(lambda: {'wins': 0, 'losses': 0})
        })
        
        # Output files
        self.outcome_file = '/root/HydraX-v2/TRUE_OUTCOMES.jsonl'
        self.stats_file = '/root/HydraX-v2/TRUE_PATTERN_STATS.json'
        self.decisions_file = '/root/HydraX-v2/PATTERN_DECISIONS.json'
        
        # Current market prices
        self.current_prices = {}
        
        # Pattern decisions
        self.quarantined = set()
        self.killed = set()
        
    def connect_to_market_data(self):
        """Connect to market data stream"""
        self.market_sub = self.context.socket(zmq.SUB)
        self.market_sub.connect("tcp://localhost:5560")
        self.market_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        print("✅ Connected to market data on port 5560")
        
    def load_pending_signals(self):
        """Load today's signals that need tracking"""
        try:
            with open('/root/HydraX-v2/truth_log.jsonl', 'r') as f:
                for line in f:
                    try:
                        signal = json.loads(line)
                        # Only track today's signals
                        if '2025-08-20' in signal.get('generated_at', ''):
                            signal_id = signal['signal_id']
                            if signal_id not in self.active_signals:
                                self.active_signals[signal_id] = {
                                    'signal': signal,
                                    'start_time': time.time(),
                                    'max_favorable': 0,
                                    'max_adverse': 0,
                                    'outcome': None
                                }
                    except: pass
            print(f"📊 Loaded {len(self.active_signals)} pending signals to track")
        except: pass
    
    def process_tick(self, symbol, bid, ask):
        """Process market tick and check signal outcomes"""
        mid_price = (bid + ask) / 2
        self.current_prices[symbol] = mid_price
        
        # Check all active signals for this symbol
        for signal_id, tracking in list(self.active_signals.items()):
            signal = tracking['signal']
            
            if signal.get('symbol') != symbol:
                continue
                
            entry = float(signal.get('entry_price', 0))
            sl = float(signal.get('sl', 0) or signal.get('stop_loss', 0))
            tp = float(signal.get('tp', 0) or signal.get('take_profit', 0))
            direction = signal.get('direction', '').upper()
            
            if not all([entry, sl, tp]):
                continue
            
            # Calculate current P&L in pips
            if direction == 'BUY':
                current_pips = (mid_price - entry)
                sl_distance = abs(entry - sl)
                tp_distance = abs(tp - entry)
                
                # Track max favorable/adverse
                tracking['max_favorable'] = max(tracking['max_favorable'], current_pips)
                tracking['max_adverse'] = min(tracking['max_adverse'], current_pips)
                
                # Check if hit TP or SL
                if mid_price >= tp:
                    self.record_outcome(signal_id, 'WIN', tp_distance / sl_distance)
                elif mid_price <= sl:
                    self.record_outcome(signal_id, 'LOSS', -1)
                    
            else:  # SELL
                current_pips = (entry - mid_price)
                sl_distance = abs(sl - entry)
                tp_distance = abs(entry - tp)
                
                tracking['max_favorable'] = max(tracking['max_favorable'], current_pips)
                tracking['max_adverse'] = min(tracking['max_adverse'], current_pips)
                
                if mid_price <= tp:
                    self.record_outcome(signal_id, 'WIN', tp_distance / sl_distance)
                elif mid_price >= sl:
                    self.record_outcome(signal_id, 'LOSS', -1)
    
    def record_outcome(self, signal_id, outcome, r_multiple):
        """Record signal outcome and update pattern stats"""
        if signal_id not in self.active_signals:
            return
            
        tracking = self.active_signals[signal_id]
        signal = tracking['signal']
        pattern = signal.get('pattern_type', 'UNKNOWN')
        session = signal.get('session', 'UNKNOWN')
        
        # Update pattern statistics
        stats = self.pattern_stats[pattern]
        stats['total'] += 1
        
        if outcome == 'WIN':
            stats['wins'] += 1
            stats['total_r_won'] += r_multiple
            stats['by_session'][session]['wins'] += 1
        else:
            stats['losses'] += 1
            stats['total_r_lost'] += abs(r_multiple)
            stats['by_session'][session]['losses'] += 1
        
        # Calculate expectancy
        if stats['wins'] + stats['losses'] > 0:
            win_rate = stats['wins'] / (stats['wins'] + stats['losses'])
            avg_win = stats['total_r_won'] / max(1, stats['wins'])
            avg_loss = stats['total_r_lost'] / max(1, stats['losses'])
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            stats['expectancy'] = expectancy
            stats['win_rate'] = win_rate * 100
        
        # Write outcome to file
        outcome_data = {
            'signal_id': signal_id,
            'pattern': pattern,
            'outcome': outcome,
            'r_multiple': r_multiple,
            'session': session,
            'recorded_at': datetime.now().isoformat(),
            'max_favorable': tracking['max_favorable'],
            'max_adverse': tracking['max_adverse'],
            'tracking_duration': time.time() - tracking['start_time']
        }
        
        with open(self.outcome_file, 'a') as f:
            f.write(json.dumps(outcome_data) + '\n')
        
        # Make pattern decisions
        self.make_pattern_decision(pattern, stats)
        
        # Remove from active tracking
        del self.active_signals[signal_id]
        
        print(f"📊 {pattern} - {outcome}: R={r_multiple:.2f} | "
              f"Stats: {stats['wins']}W/{stats['losses']}L, "
              f"Expectancy: {stats.get('expectancy', 0):.2f}R")
    
    def make_pattern_decision(self, pattern, stats):
        """Decide if pattern should be quarantined or killed"""
        total_trades = stats['wins'] + stats['losses']
        expectancy = stats.get('expectancy', 0)
        
        # After 50 trades, quarantine if negative expectancy
        if total_trades >= 50 and expectancy < -0.05:
            if pattern not in self.quarantined:
                self.quarantined.add(pattern)
                print(f"⚠️ QUARANTINED: {pattern} (Expectancy: {expectancy:.2f}R after {total_trades} trades)")
        
        # After 100 trades, kill if still negative
        if total_trades >= 100 and expectancy < -0.1:
            if pattern not in self.killed:
                self.killed.add(pattern)
                self.quarantined.discard(pattern)
                print(f"💀 KILLED: {pattern} (Expectancy: {expectancy:.2f}R after {total_trades} trades)")
        
        # Save decisions
        decisions = {
            'quarantined': list(self.quarantined),
            'killed': list(self.killed),
            'updated_at': datetime.now().isoformat()
        }
        with open(self.decisions_file, 'w') as f:
            json.dump(decisions, f, indent=2)
    
    def save_stats(self):
        """Save current statistics"""
        stats_output = {}
        for pattern, stats in self.pattern_stats.items():
            stats_output[pattern] = {
                'total': stats['total'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': stats.get('win_rate', 0),
                'expectancy': stats.get('expectancy', 0),
                'by_session': dict(stats['by_session'])
            }
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats_output, f, indent=2)
    
    def run(self):
        """Main tracking loop"""
        self.connect_to_market_data()
        self.load_pending_signals()
        
        last_save = time.time()
        last_reload = time.time()
        
        print("🚀 TRUE PATTERN TRACKER STARTED")
        print(f"📊 Tracking {len(self.active_signals)} signals")
        
        while True:
            try:
                # Check for market data with timeout
                if self.market_sub.poll(100):
                    msg = self.market_sub.recv_string(zmq.NOBLOCK)
                    
                    # Parse tick data
                    if 'TICK' in msg:
                        parts = msg.split()
                        if len(parts) >= 4:
                            symbol = parts[1]
                            try:
                                bid = float(parts[2])
                                ask = float(parts[3])
                                self.process_tick(symbol, bid, ask)
                            except: pass
                
                # Reload new signals every 30 seconds
                if time.time() - last_reload > 30:
                    self.load_pending_signals()
                    last_reload = time.time()
                
                # Save stats every 60 seconds
                if time.time() - last_save > 60:
                    self.save_stats()
                    last_save = time.time()
                    print(f"📊 Tracking {len(self.active_signals)} active signals")
                    
                    # Show current stats
                    for pattern, stats in self.pattern_stats.items():
                        if stats['total'] > 0:
                            print(f"  {pattern}: {stats['wins']}W/{stats['losses']}L, "
                                  f"Expectancy: {stats.get('expectancy', 0):.2f}R")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
        
        print("Tracker stopped")
        self.save_stats()

if __name__ == "__main__":
    tracker = TruePatternTracker()
    tracker.run()