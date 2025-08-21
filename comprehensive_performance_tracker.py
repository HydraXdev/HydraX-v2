#!/usr/bin/env python3
"""
Comprehensive Performance Tracker v2
Tracks every conceivable metric for ultimate analysis
"""

import zmq
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import logging

class ComprehensivePerformanceTracker:
    """Track and analyze every aspect of signal performance"""
    
    def __init__(self):
        # Logging
        self.logger = logging.getLogger('PerfTracker')
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler('performance_tracker_v2.log')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)
        
        # ZMQ Setup
        self.context = zmq.Context()
        
        # Subscribe to Elite Guard signals
        self.signal_sub = self.context.socket(zmq.SUB)
        self.signal_sub.connect("tcp://localhost:5557")
        self.signal_sub.setsockopt_string(zmq.SUBSCRIBE, "ELITE_GUARD_SIGNAL")
        
        # Subscribe to market data for outcome tracking
        self.market_sub = self.context.socket(zmq.SUB)
        self.market_sub.connect("tcp://localhost:5560")
        self.market_sub.setsockopt_string(zmq.SUBSCRIBE, "TICK")
        
        # Database
        self.db_path = '/root/HydraX-v2/bitten.db'
        
        # Active signals being tracked
        self.active_signals = {}  # signal_id -> signal_data
        
        # Performance cache
        self.pattern_performance = {}
        self.session_performance = {}
        
        # Market prices for outcome tracking
        self.current_prices = {}
        
        self.logger.info("Comprehensive Performance Tracker v2 initialized")
    
    def track_signal_entry(self, signal: Dict):
        """Record signal entry and start tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract all metrics
            signal_id = signal.get('signal_id')
            pattern_type = signal.get('pattern_type', signal.get('pattern'))
            symbol = signal.get('symbol')
            entry_price = signal.get('entry_price', signal.get('entry'))
            sl = signal.get('stop_loss', signal.get('sl'))
            tp = signal.get('take_profit', signal.get('tp'))
            confidence = signal.get('confidence', 0)
            session = signal.get('session', self.get_current_session())
            
            # Calculate planned R:R
            if signal.get('direction') == 'BUY':
                risk = entry_price - sl
                reward = tp - entry_price
            else:
                risk = sl - entry_price
                reward = entry_price - tp
            
            planned_rr = reward / risk if risk > 0 else 0
            
            # Determine volatility regime
            volatility_regime = self.determine_volatility_regime(symbol)
            
            # Store in active signals for tracking
            self.active_signals[signal_id] = {
                'signal': signal,
                'entry_time': int(time.time()),
                'entry_price': entry_price,
                'sl': sl,
                'tp': tp,
                'symbol': symbol,
                'direction': signal.get('direction'),
                'pattern_type': pattern_type,
                'max_favorable': 0,
                'max_adverse': 0,
                'current_price': entry_price,
                'planned_rr': planned_rr,
                'session': session,
                'confidence': confidence
            }
            
            # Insert into database
            cursor.execute("""
                INSERT OR REPLACE INTO signal_performance_v2 
                (signal_id, pattern_type, symbol, entry_time, planned_rr, session, volatility_regime)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (signal_id, pattern_type, symbol, int(time.time()), planned_rr, session, volatility_regime))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Tracking signal {signal_id}: {pattern_type} {symbol} {signal.get('direction')}")
            
        except Exception as e:
            self.logger.error(f"Error tracking signal entry: {e}")
    
    def update_signal_progress(self, signal_id: str, current_price: float):
        """Update signal progress with current price"""
        if signal_id not in self.active_signals:
            return
        
        signal_data = self.active_signals[signal_id]
        entry_price = signal_data['entry_price']
        direction = signal_data['direction']
        
        # Calculate current P&L in pips
        pip_size = 0.0001 if 'JPY' not in signal_data['symbol'] else 0.01
        
        if direction == 'BUY':
            current_pips = (current_price - entry_price) / pip_size
        else:
            current_pips = (entry_price - current_price) / pip_size
        
        # Update max favorable/adverse
        if current_pips > signal_data['max_favorable']:
            signal_data['max_favorable'] = current_pips
        if current_pips < signal_data['max_adverse']:
            signal_data['max_adverse'] = current_pips
        
        signal_data['current_price'] = current_price
        signal_data['current_pips'] = current_pips
        
        # Check if TP or SL hit
        if direction == 'BUY':
            if current_price >= signal_data['tp']:
                self.complete_signal(signal_id, 'TP', current_price)
            elif current_price <= signal_data['sl']:
                self.complete_signal(signal_id, 'SL', current_price)
        else:
            if current_price <= signal_data['tp']:
                self.complete_signal(signal_id, 'TP', current_price)
            elif current_price >= signal_data['sl']:
                self.complete_signal(signal_id, 'SL', current_price)
    
    def complete_signal(self, signal_id: str, exit_type: str, exit_price: float):
        """Complete signal tracking and record final metrics"""
        if signal_id not in self.active_signals:
            return
        
        try:
            signal_data = self.active_signals[signal_id]
            entry_price = signal_data['entry_price']
            direction = signal_data['direction']
            
            # Calculate achieved R:R
            pip_size = 0.0001 if 'JPY' not in signal_data['symbol'] else 0.01
            
            if direction == 'BUY':
                achieved_pips = (exit_price - entry_price) / pip_size
                risk_pips = (entry_price - signal_data['sl']) / pip_size
            else:
                achieved_pips = (entry_price - exit_price) / pip_size
                risk_pips = (signal_data['sl'] - entry_price) / pip_size
            
            achieved_rr = achieved_pips / risk_pips if risk_pips > 0 else 0
            
            # Calculate efficiency score (how close to perfect exit)
            if signal_data['max_favorable'] > 0:
                efficiency_score = (achieved_pips / signal_data['max_favorable']) * 100
            else:
                efficiency_score = 0 if achieved_pips < 0 else 100
            
            # Time to completion
            exit_time = int(time.time())
            time_to_complete = (exit_time - signal_data['entry_time']) / 60  # minutes
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE signal_performance_v2 
                SET exit_time = ?, achieved_rr = ?, max_favorable_pips = ?, 
                    max_adverse_pips = ?, efficiency_score = ?
                WHERE signal_id = ?
            """, (exit_time, achieved_rr, signal_data['max_favorable'], 
                  signal_data['max_adverse'], efficiency_score, signal_id))
            
            # Update pattern statistics
            pattern_type = signal_data['pattern_type']
            symbol = signal_data['symbol']
            is_win = exit_type == 'TP'
            
            cursor.execute("""
                INSERT INTO pattern_statistics_v2 (pattern_type, symbol, total_signals, wins, losses)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(pattern_type, symbol) DO UPDATE SET
                    total_signals = total_signals + 1,
                    wins = wins + ?,
                    losses = losses + ?,
                    avg_time_to_tp = (avg_time_to_tp * total_signals + ?) / (total_signals + 1),
                    avg_rr_achieved = (avg_rr_achieved * total_signals + ?) / (total_signals + 1),
                    last_updated = strftime('%s', 'now')
            """, (pattern_type, symbol, 1 if is_win else 0, 0 if is_win else 1,
                  1 if is_win else 0, 0 if is_win else 1,
                  time_to_complete if is_win else 0, achieved_rr))
            
            conn.commit()
            conn.close()
            
            # Remove from active tracking
            del self.active_signals[signal_id]
            
            self.logger.info(f"Completed {signal_id}: {exit_type} hit, RR={achieved_rr:.2f}, Efficiency={efficiency_score:.1f}%")
            
            # Log to comprehensive tracking file
            with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'a') as f:
                tracking_data = {
                    'signal_id': signal_id,
                    'pattern': pattern_type,
                    'symbol': symbol,
                    'outcome': 'WIN' if is_win else 'LOSS',
                    'planned_rr': signal_data['planned_rr'],
                    'achieved_rr': achieved_rr,
                    'max_favorable_pips': signal_data['max_favorable'],
                    'max_adverse_pips': signal_data['max_adverse'],
                    'time_to_complete_min': time_to_complete,
                    'efficiency_score': efficiency_score,
                    'session': signal_data['session'],
                    'confidence': signal_data['confidence'],
                    'timestamp': datetime.now().isoformat()
                }
                f.write(json.dumps(tracking_data) + '\n')
            
        except Exception as e:
            self.logger.error(f"Error completing signal {signal_id}: {e}")
    
    def determine_volatility_regime(self, symbol: str) -> str:
        """Determine current volatility regime"""
        # Simplified - in production would use ATR
        hour = datetime.utcnow().hour
        if 12 <= hour < 16:  # London/NY overlap
            return 'HIGH_VOL'
        elif 7 <= hour < 21:  # Main sessions
            return 'MEDIUM_VOL'
        else:
            return 'LOW_VOL'
    
    def get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.utcnow().hour
        if 7 <= hour < 16:
            if 12 <= hour < 16:
                return 'OVERLAP'
            return 'LONDON'
        elif 12 <= hour < 21:
            return 'NY'
        elif hour >= 23 or hour < 8:
            return 'ASIAN'
        else:
            return 'OFF_HOURS'
    
    def process_market_tick(self, message: str):
        """Process market tick for outcome tracking"""
        try:
            parts = message.split()
            if len(parts) >= 4:
                symbol = parts[1]
                bid = float(parts[2])
                ask = float(parts[3])
                mid = (bid + ask) / 2
                
                self.current_prices[symbol] = mid
                
                # Update all active signals for this symbol
                for signal_id, signal_data in list(self.active_signals.items()):
                    if signal_data['symbol'] == symbol:
                        self.update_signal_progress(signal_id, mid)
        
        except Exception as e:
            self.logger.error(f"Error processing tick: {e}")
    
    def generate_live_stats(self) -> Dict:
        """Generate live performance statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END),
                       AVG(achieved_rr),
                       AVG(efficiency_score)
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
                AND entry_time > strftime('%s', 'now', '-24 hours')
            """)
            
            total, wins, avg_rr, avg_efficiency = cursor.fetchone()
            
            # Pattern performance
            cursor.execute("""
                SELECT pattern_type, 
                       COUNT(*) as signals,
                       SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END) as wins,
                       AVG(achieved_rr) as avg_rr
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
                GROUP BY pattern_type
                ORDER BY avg_rr DESC
            """)
            
            pattern_stats = cursor.fetchall()
            
            conn.close()
            
            win_rate = (wins / total * 100) if total > 0 else 0
            
            return {
                'total_signals': total or 0,
                'wins': wins or 0,
                'win_rate': win_rate,
                'avg_rr': avg_rr or 0,
                'avg_efficiency': avg_efficiency or 0,
                'pattern_performance': pattern_stats,
                'active_signals': len(self.active_signals),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating stats: {e}")
            return {}
    
    def run(self):
        """Main tracking loop"""
        self.logger.info("Starting comprehensive performance tracker...")
        
        # Start market data thread
        market_thread = threading.Thread(target=self.market_data_loop, daemon=True)
        market_thread.start()
        
        # Main signal tracking loop
        while True:
            try:
                # Check for new signals
                if self.signal_sub.poll(100):
                    message = self.signal_sub.recv_string()
                    if message.startswith("ELITE_GUARD_SIGNAL "):
                        signal_json = message.replace("ELITE_GUARD_SIGNAL ", "")
                        signal = json.loads(signal_json)
                        self.track_signal_entry(signal)
                
                # Generate and save stats every minute
                if int(time.time()) % 60 == 0:
                    stats = self.generate_live_stats()
                    self.logger.info(f"Live stats: Win rate={stats.get('win_rate', 0):.1f}%, Active={len(self.active_signals)}")
                    
                    # Save to database
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO live_performance_v2 
                        (total_signals, win_rate, active_patterns, hourly_snapshot)
                        VALUES (?, ?, ?, ?)
                    """, (stats.get('total_signals', 0), stats.get('win_rate', 0),
                          json.dumps([p[0] for p in stats.get('pattern_performance', [])]),
                          json.dumps(stats)))
                    conn.commit()
                    conn.close()
                    
                    time.sleep(1)  # Prevent duplicate saves
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(1)
    
    def market_data_loop(self):
        """Separate thread for market data processing"""
        while True:
            try:
                if self.market_sub.poll(100):
                    message = self.market_sub.recv_string()
                    if message.startswith("TICK "):
                        self.process_market_tick(message)
            except Exception as e:
                self.logger.error(f"Error in market loop: {e}")
                time.sleep(0.1)


if __name__ == "__main__":
    tracker = ComprehensivePerformanceTracker()
    tracker.run()