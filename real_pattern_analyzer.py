#!/usr/bin/env python3
"""
REAL PATTERN ANALYZER - Actually works with proper expectancy calculation
Based on proven pandas/talib approach, not broken promises
"""

import pandas as pd
import numpy as np
import json
import time
import zmq
from datetime import datetime, timedelta
from collections import defaultdict, deque
import os
import sys

# Try to import talib, install if needed
try:
    import talib
except ImportError:
    print("Installing TA-Lib...")
    os.system("pip3 install TA-Lib")
    import talib

try:
    import pytz
except ImportError:
    print("Installing pytz...")
    os.system("pip3 install pytz")
    import pytz

class RealPatternAnalyzer:
    def __init__(self):
        self.context = zmq.Context()
        
        # Market data storage (5min candles per symbol)
        self.candles = defaultdict(lambda: deque(maxlen=500))  # Keep 500 candles
        self.ticks = defaultdict(list)  # Collect ticks to build candles
        
        # Tracking files
        self.tracking_file = '/root/HydraX-v2/REAL_tracking.jsonl'
        self.outcomes_file = '/root/HydraX-v2/REAL_outcomes.jsonl'
        self.decisions_file = '/root/HydraX-v2/REAL_decisions.json'
        
        # Pattern statistics
        self.pattern_stats = defaultdict(lambda: {
            'total': 0, 'wins': 0, 'losses': 0,
            'total_pips_won': 0, 'total_pips_lost': 0,
            'by_regime': defaultdict(lambda: {'wins': 0, 'losses': 0}),
            'ev_history': []
        })
        
        # Quarantine system
        self.quarantine = {}  # pattern -> {'stage': 'demo'/'killed', 'reason': str}
        
        # Active signal tracking
        self.active_signals = {}
        
        # Current prices for outcome monitoring
        self.current_prices = {}
        
    def connect_market_data(self):
        """Connect to real market data stream"""
        self.market_sub = self.context.socket(zmq.SUB)
        self.market_sub.connect("tcp://localhost:5560")
        self.market_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        print("✅ Connected to REAL market data on port 5560")
        
    def build_candle(self, symbol):
        """Build 5-minute candle from ticks"""
        if symbol not in self.ticks or len(self.ticks[symbol]) == 0:
            return None
            
        tick_df = pd.DataFrame(self.ticks[symbol])
        tick_df['timestamp'] = pd.to_datetime(tick_df['timestamp'])
        tick_df.set_index('timestamp', inplace=True)
        
        # Resample to 5-minute candles
        candle = tick_df['price'].resample('5T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'count'
        }).dropna()
        
        if not candle.empty:
            return candle.iloc[-1].to_dict()
        return None
        
    def calculate_indicators(self, symbol):
        """Calculate ATR, ADX for regime detection"""
        if symbol not in self.candles or len(self.candles[symbol]) < 20:
            return None, None
            
        df = pd.DataFrame(list(self.candles[symbol]))
        if df.empty or len(df) < 20:
            return None, None
            
        try:
            atr = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            adx = talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            return atr[-1] if len(atr) > 0 else None, adx[-1] if len(adx) > 0 else None
        except:
            return None, None
    
    def get_regime(self, timestamp, symbol):
        """Determine market regime"""
        utc = pytz.UTC
        dt = datetime.fromtimestamp(timestamp, tz=utc)
        hour = dt.hour
        
        # Session detection
        if 23 <= hour or hour < 7:
            session = 'ASIAN'
        elif 8 <= hour < 16:
            session = 'LONDON'
        elif 13 <= hour < 21:
            session = 'NY'
        else:
            session = 'OVERLAP'
        
        # Trend/volatility detection
        atr, adx = self.calculate_indicators(symbol)
        
        regime = {
            'session': session,
            'trend': 'UNKNOWN',
            'volatility': 'UNKNOWN'
        }
        
        if adx is not None:
            regime['trend'] = 'TREND' if adx > 25 else 'RANGE'
        
        if atr is not None and len(self.candles[symbol]) > 50:
            df = pd.DataFrame(list(self.candles[symbol]))
            avg_atr = df['high'].rolling(50).mean().iloc[-1] - df['low'].rolling(50).mean().iloc[-1]
            regime['volatility'] = 'HIGH' if atr > avg_atr * 1.5 else 'LOW'
        
        return regime
    
    def check_convergence(self, new_signal):
        """Check if multiple patterns converging on same symbol"""
        symbol = new_signal['symbol']
        convergence_count = 0
        
        # Check active signals for same symbol within 5 minutes
        current_time = time.time()
        for sig_id, sig_data in self.active_signals.items():
            if (sig_data['symbol'] == symbol and 
                abs(sig_data['timestamp'] - current_time) < 300 and
                sig_data['pattern'] != new_signal.get('pattern_type')):
                convergence_count += 1
        
        if convergence_count > 0:
            boost = convergence_count * 10  # +10% per converging pattern
            new_signal['convergence_boost'] = boost
            new_signal['convergence_patterns'] = convergence_count + 1
            print(f"🎯 CONVERGENCE: {symbol} has {convergence_count + 1} patterns aligning! +{boost}% confidence")
            return boost
        return 0
    
    def calculate_expectancy(self, pattern):
        """Calculate true expectancy: EV = (Win% × AvgWin) - (Loss% × AvgLoss)"""
        stats = self.pattern_stats[pattern]
        
        if stats['wins'] + stats['losses'] == 0:
            return 0
        
        total_trades = stats['wins'] + stats['losses']
        win_rate = stats['wins'] / total_trades
        
        avg_win = stats['total_pips_won'] / max(1, stats['wins'])
        avg_loss = stats['total_pips_lost'] / max(1, stats['losses'])
        
        # Convert pips to R-multiple (assuming avg loss = 1R)
        avg_win_r = avg_win / max(1, avg_loss) if avg_loss > 0 else avg_win / 10
        
        # True expectancy formula
        expectancy = (win_rate * avg_win_r) - ((1 - win_rate) * 1)
        
        return expectancy
    
    def monitor_signal_outcome(self, signal_id):
        """Track signal until TP/SL hit"""
        if signal_id not in self.active_signals:
            return
            
        signal = self.active_signals[signal_id]
        symbol = signal['symbol']
        
        if symbol not in self.current_prices:
            return
            
        current_price = self.current_prices[symbol]
        entry = signal['entry_price']
        sl = signal['sl']
        tp = signal['tp']
        direction = signal['direction']
        
        outcome = None
        pips = 0
        
        if direction == 'BUY':
            if current_price >= tp:
                outcome = 'WIN'
                pips = (tp - entry) * 10000 if 'JPY' not in symbol else (tp - entry) * 100
            elif current_price <= sl:
                outcome = 'LOSS'
                pips = (sl - entry) * 10000 if 'JPY' not in symbol else (sl - entry) * 100
        else:  # SELL
            if current_price <= tp:
                outcome = 'WIN'
                pips = (entry - tp) * 10000 if 'JPY' not in symbol else (entry - tp) * 100
            elif current_price >= sl:
                outcome = 'LOSS'
                pips = (entry - sl) * 10000 if 'JPY' not in symbol else (entry - sl) * 100
        
        if outcome:
            self.record_outcome(signal_id, outcome, abs(pips))
    
    def record_outcome(self, signal_id, outcome, pips):
        """Record outcome and update pattern statistics"""
        if signal_id not in self.active_signals:
            return
            
        signal = self.active_signals[signal_id]
        pattern = signal.get('pattern_type', 'UNKNOWN')
        regime = signal.get('regime', {})
        
        # Update pattern stats
        stats = self.pattern_stats[pattern]
        stats['total'] += 1
        
        if outcome == 'WIN':
            stats['wins'] += 1
            stats['total_pips_won'] += pips
            regime_key = f"{regime.get('session', 'UNK')}_{regime.get('trend', 'UNK')}"
            stats['by_regime'][regime_key]['wins'] += 1
        else:
            stats['losses'] += 1
            stats['total_pips_lost'] += pips
            regime_key = f"{regime.get('session', 'UNK')}_{regime.get('trend', 'UNK')}"
            stats['by_regime'][regime_key]['losses'] += 1
        
        # Calculate and store expectancy
        expectancy = self.calculate_expectancy(pattern)
        stats['ev_history'].append(expectancy)
        stats['current_expectancy'] = expectancy
        
        # Log outcome
        outcome_data = {
            'signal_id': signal_id,
            'pattern': pattern,
            'outcome': outcome,
            'pips': pips,
            'expectancy_after': expectancy,
            'total_trades': stats['total'],
            'win_rate': (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0,
            'regime': regime,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.outcomes_file, 'a') as f:
            f.write(json.dumps(outcome_data) + '\n')
        
        print(f"📊 {pattern}: {outcome} ({pips:.1f} pips) | "
              f"Stats: {stats['wins']}W/{stats['losses']}L | "
              f"Win Rate: {outcome_data['win_rate']:.1f}% | "
              f"Expectancy: {expectancy:.2f}R")
        
        # Make quarantine decisions
        self.analyze_for_elimination(pattern, stats)
        
        # Remove from active tracking
        del self.active_signals[signal_id]
    
    def analyze_for_elimination(self, pattern, stats):
        """Two-stage quarantine system"""
        total = stats['total']
        expectancy = stats['current_expectancy']
        
        # Stage 1: Quarantine after 50 signals if negative expectancy
        if total >= 50 and expectancy < -0.05:
            if pattern not in self.quarantine:
                self.quarantine[pattern] = {
                    'stage': 'QUARANTINE',
                    'reason': f'Negative expectancy {expectancy:.2f}R after {total} trades',
                    'timestamp': datetime.now().isoformat()
                }
                print(f"⚠️ QUARANTINED: {pattern} - {self.quarantine[pattern]['reason']}")
        
        # Stage 2: Kill after 100 signals if still negative
        if total >= 100 and expectancy < -0.1:
            self.quarantine[pattern] = {
                'stage': 'KILLED',
                'reason': f'Persistent negative expectancy {expectancy:.2f}R after {total} trades',
                'timestamp': datetime.now().isoformat()
            }
            print(f"💀 KILLED: {pattern} - {self.quarantine[pattern]['reason']}")
        
        # Recovery: Remove from quarantine if positive
        if pattern in self.quarantine and expectancy > 0.1 and total >= 20:
            print(f"✅ RECOVERED: {pattern} - Expectancy improved to {expectancy:.2f}R")
            del self.quarantine[pattern]
        
        # Save decisions
        self.save_decisions()
    
    def save_decisions(self):
        """Save quarantine decisions"""
        decisions = {
            'quarantine': self.quarantine,
            'pattern_stats': {
                pattern: {
                    'total': stats['total'],
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'win_rate': (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0,
                    'expectancy': stats.get('current_expectancy', 0),
                    'last_10_ev': stats['ev_history'][-10:] if len(stats['ev_history']) > 0 else []
                }
                for pattern, stats in self.pattern_stats.items()
                if stats['total'] > 0
            },
            'updated_at': datetime.now().isoformat()
        }
        
        with open(self.decisions_file, 'w') as f:
            json.dump(decisions, f, indent=2)
    
    def load_pending_signals(self):
        """Load signals from truth_log that need tracking"""
        try:
            with open('/root/HydraX-v2/truth_log.jsonl', 'r') as f:
                for line in f:
                    try:
                        signal = json.loads(line)
                        # Only track recent signals
                        if '2025-08-20' in signal.get('generated_at', ''):
                            signal_id = signal['signal_id']
                            if signal_id not in self.active_signals:
                                # Apply convergence check
                                convergence_boost = self.check_convergence(signal)
                                if convergence_boost > 0:
                                    signal['confidence'] = signal.get('confidence', 0) + convergence_boost
                                
                                # Get regime
                                signal['regime'] = self.get_regime(time.time(), signal.get('symbol', 'EURUSD'))
                                
                                # Check if pattern is killed
                                pattern = signal.get('pattern_type', 'UNKNOWN')
                                if pattern in self.quarantine and self.quarantine[pattern]['stage'] == 'KILLED':
                                    continue  # Skip killed patterns
                                
                                # Add to tracking
                                self.active_signals[signal_id] = signal
                                signal['timestamp'] = time.time()
                                
                                # Log signal
                                tracking_data = {
                                    'signal_id': signal_id,
                                    'pattern': pattern,
                                    'confidence': signal.get('confidence', 0),
                                    'would_fire': signal.get('confidence', 0) >= 78,
                                    'fired': signal.get('confidence', 0) >= 90,
                                    'convergence': convergence_boost > 0,
                                    'regime': signal['regime'],
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                with open(self.tracking_file, 'a') as f:
                                    f.write(json.dumps(tracking_data) + '\n')
                                    
                    except Exception as e:
                        continue
                        
            print(f"📊 Loaded {len(self.active_signals)} signals to track")
        except Exception as e:
            print(f"Error loading signals: {e}")
    
    def process_market_tick(self, msg):
        """Process incoming market data"""
        try:
            if 'TICK' in msg:
                parts = msg.split()
                if len(parts) >= 4:
                    symbol = parts[1]
                    bid = float(parts[2])
                    ask = float(parts[3])
                    
                    # Update current price
                    self.current_prices[symbol] = (bid + ask) / 2
                    
                    # Store tick for candle building
                    self.ticks[symbol].append({
                        'timestamp': datetime.now(),
                        'price': self.current_prices[symbol]
                    })
                    
                    # Build candle every 5 minutes
                    if len(self.ticks[symbol]) % 100 == 0:  # Every 100 ticks
                        candle = self.build_candle(symbol)
                        if candle:
                            candle['timestamp'] = datetime.now()
                            self.candles[symbol].append(candle)
                    
                    # Check outcomes for all active signals of this symbol
                    for signal_id in list(self.active_signals.keys()):
                        if self.active_signals[signal_id].get('symbol') == symbol:
                            self.monitor_signal_outcome(signal_id)
                            
        except Exception as e:
            pass
    
    def run(self):
        """Main loop"""
        self.connect_market_data()
        self.load_pending_signals()
        
        last_reload = time.time()
        last_save = time.time()
        
        print("🚀 REAL PATTERN ANALYZER STARTED")
        print("📊 Building on proven pandas/talib foundation")
        print("✅ Expectancy-based elimination active")
        print("✅ Convergence detection active")
        print("✅ Regime awareness active")
        print("✅ Two-stage quarantine active")
        
        while True:
            try:
                # Get market data
                if self.market_sub.poll(100):
                    msg = self.market_sub.recv_string(zmq.NOBLOCK)
                    self.process_market_tick(msg)
                
                # Reload signals every 30 seconds
                if time.time() - last_reload > 30:
                    self.load_pending_signals()
                    last_reload = time.time()
                
                # Save stats every minute
                if time.time() - last_save > 60:
                    self.save_decisions()
                    last_save = time.time()
                    
                    # Show current status
                    print(f"\n📊 CURRENT STATUS:")
                    print(f"Tracking: {len(self.active_signals)} signals")
                    print(f"Quarantined: {sum(1 for p in self.quarantine.values() if p['stage'] == 'QUARANTINE')} patterns")
                    print(f"Killed: {sum(1 for p in self.quarantine.values() if p['stage'] == 'KILLED')} patterns")
                    
                    # Show top patterns by expectancy
                    patterns_by_ev = sorted(
                        [(p, s['current_expectancy']) for p, s in self.pattern_stats.items() if s['total'] >= 10],
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    if patterns_by_ev:
                        print("\n🏆 TOP PATTERNS BY EXPECTANCY:")
                        for pattern, ev in patterns_by_ev[:3]:
                            stats = self.pattern_stats[pattern]
                            print(f"  {pattern}: {ev:.2f}R ({stats['wins']}W/{stats['losses']}L)")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
        
        print("\n📊 Final statistics saved")
        self.save_decisions()

if __name__ == "__main__":
    analyzer = RealPatternAnalyzer()
    analyzer.run()