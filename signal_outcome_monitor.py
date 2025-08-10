#!/usr/bin/env python3
"""
Signal Outcome Monitor - Tracks whether signals hit SL or TP first
Monitors live tick data to determine actual signal outcomes
"""

import json
import zmq
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SignalOutcomeMonitor:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5560")  # Market data port
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        self.active_signals = {}  # signal_id -> signal data
        self.completed_signals = []
        self.truth_file = "/root/HydraX-v2/truth_log.jsonl"
        self.outcome_file = "/root/HydraX-v2/signal_outcomes.jsonl"
        
        print("📊 Signal Outcome Monitor started")
        print("   Monitoring tick data to track SL/TP hits")
        self.load_active_signals()
        
    def load_active_signals(self):
        """Load active signals from truth log"""
        try:
            with open(self.truth_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and line != '[]':
                        try:
                            signal = json.loads(line)
                            # Only track Elite Guard signals that aren't completed
                            if ('ELITE_GUARD' in signal.get('signal_id', '') and 
                                not signal.get('completed', False) and
                                signal.get('entry_price', 0) > 0):
                                
                                # Add to active signals
                                self.active_signals[signal['signal_id']] = {
                                    'signal': signal,
                                    'monitoring_started': datetime.now().isoformat(),
                                    'ticks_processed': 0,
                                    'max_favorable': 0,
                                    'max_adverse': 0,
                                    'current_price': signal['entry_price']
                                }
                        except:
                            continue
            
            print(f"   Loaded {len(self.active_signals)} active signals to monitor")
            for sid in self.active_signals:
                sig = self.active_signals[sid]['signal']
                print(f"   • {sig['symbol']} {sig['direction']} @ {sig['entry_price']}")
                
        except FileNotFoundError:
            print("   No truth log found, starting fresh")
    
    def process_tick(self, symbol: str, bid: float, ask: float):
        """Process tick data and check if any signals hit SL/TP"""
        
        # Check each active signal for this symbol
        completed_now = []
        
        for signal_id, data in self.active_signals.items():
            signal = data['signal']
            
            # Skip if different symbol
            if signal['symbol'] != symbol:
                continue
                
            data['ticks_processed'] += 1
            
            # Determine relevant price based on direction
            if signal['direction'] == 'BUY':
                # For BUY: Use bid for SL, ask for entry
                current_price = bid  # Exit price
                entry_price = signal['entry_price']
                sl = signal['sl']
                tp = signal['tp']
                
                # Track max favorable/adverse
                favorable = current_price - entry_price
                data['max_favorable'] = max(data['max_favorable'], favorable)
                data['max_adverse'] = min(data['max_adverse'], favorable)
                
                # Check SL hit (bid <= sl)
                if current_price <= sl:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'LOSS',
                        'hit_level': 'SL',
                        'exit_price': current_price,
                        'pips': (current_price - entry_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ❌ {symbol} hit SL @ {current_price:.5f}")
                    
                # Check TP hit (bid >= tp)
                elif current_price >= tp:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'WIN',
                        'hit_level': 'TP',
                        'exit_price': current_price,
                        'pips': (current_price - entry_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ✅ {symbol} hit TP @ {current_price:.5f}")
                    
            else:  # SELL
                # For SELL: Use ask for SL, bid for exit
                current_price = ask  # Exit price
                entry_price = signal['entry_price']
                sl = signal['sl']
                tp = signal['tp']
                
                # Track max favorable/adverse
                favorable = entry_price - current_price
                data['max_favorable'] = max(data['max_favorable'], favorable)
                data['max_adverse'] = min(data['max_adverse'], favorable)
                
                # Check SL hit (ask >= sl)
                if current_price >= sl:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'LOSS',
                        'hit_level': 'SL',
                        'exit_price': current_price,
                        'pips': (entry_price - current_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ❌ {symbol} hit SL @ {current_price:.5f}")
                    
                # Check TP hit (ask <= tp)
                elif current_price <= tp:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'WIN',
                        'hit_level': 'TP',
                        'exit_price': current_price,
                        'pips': (entry_price - current_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ✅ {symbol} hit TP @ {current_price:.5f}")
            
            data['current_price'] = current_price
        
        # Process completed signals
        for completion in completed_now:
            signal_id = completion['signal_id']
            data = self.active_signals[signal_id]
            
            # Create outcome record
            outcome_record = {
                'signal_id': signal_id,
                'symbol': data['signal']['symbol'],
                'direction': data['signal']['direction'],
                'pattern': data['signal'].get('pattern_type'),
                'signal_type': data['signal'].get('signal_type'),
                'entry_price': data['signal']['entry_price'],
                'sl': data['signal']['sl'],
                'tp': data['signal']['tp'],
                'outcome': completion['outcome'],
                'hit_level': completion['hit_level'],
                'exit_price': completion['exit_price'],
                'pips_result': completion['pips'],
                'max_favorable': data['max_favorable'] * self.get_pip_multiplier(data['signal']['symbol']),
                'max_adverse': data['max_adverse'] * self.get_pip_multiplier(data['signal']['symbol']),
                'ticks_processed': data['ticks_processed'],
                'completed_at': datetime.now().isoformat(),
                'monitoring_started': data['monitoring_started']
            }
            
            # Save outcome
            self.save_outcome(outcome_record)
            self.completed_signals.append(outcome_record)
            
            # Remove from active
            del self.active_signals[signal_id]
    
    def get_pip_multiplier(self, symbol: str) -> float:
        """Get pip multiplier for symbol"""
        if symbol in ['USDJPY', 'EURJPY', 'GBPJPY']:
            return 100  # JPY pairs
        elif symbol == 'XAUUSD':
            return 10   # Gold
        else:
            return 10000  # Major pairs
    
    def save_outcome(self, outcome: Dict):
        """Save signal outcome to file"""
        try:
            with open(self.outcome_file, 'a') as f:
                f.write(json.dumps(outcome) + '\n')
        except Exception as e:
            print(f"Error saving outcome: {e}")
    
    def print_statistics(self):
        """Print current monitoring statistics"""
        print(f"\n📊 OUTCOME MONITOR STATISTICS:")
        print(f"   Active Signals: {len(self.active_signals)}")
        print(f"   Completed: {len(self.completed_signals)}")
        
        if self.completed_signals:
            wins = [s for s in self.completed_signals if s['outcome'] == 'WIN']
            losses = [s for s in self.completed_signals if s['outcome'] == 'LOSS']
            
            print(f"   Wins: {len(wins)}")
            print(f"   Losses: {len(losses)}")
            if wins or losses:
                win_rate = len(wins) / (len(wins) + len(losses)) * 100
                print(f"   Win Rate: {win_rate:.1f}%")
                
                total_pips = sum(s['pips_result'] for s in self.completed_signals)
                print(f"   Total Pips: {total_pips:+.1f}")
        
        print(f"\n   Currently Monitoring:")
        for sid, data in self.active_signals.items():
            sig = data['signal']
            print(f"   • {sig['symbol']} {sig['direction']} - {data['ticks_processed']} ticks")
    
    def run(self):
        """Main monitoring loop"""
        print("\n🔍 Monitoring tick data for signal outcomes...")
        last_stats = time.time()
        
        while True:
            try:
                # Check for new tick data (non-blocking with timeout)
                if self.subscriber.poll(100):  # 100ms timeout
                    message = self.subscriber.recv_string()
                    
                    # Parse tick data
                    if message.startswith("TICK"):
                        parts = message.split()
                        if len(parts) >= 4:
                            symbol = parts[1]
                            try:
                                bid = float(parts[2])
                                ask = float(parts[3])
                                self.process_tick(symbol, bid, ask)
                            except ValueError:
                                pass
                
                # Print statistics every 30 seconds
                if time.time() - last_stats > 30:
                    self.print_statistics()
                    last_stats = time.time()
                    
            except KeyboardInterrupt:
                print("\n👋 Signal Outcome Monitor stopped")
                break
            except Exception as e:
                print(f"Error in monitor: {e}")
                time.sleep(1)

if __name__ == "__main__":
    monitor = SignalOutcomeMonitor()
    monitor.run()