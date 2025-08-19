#!/usr/bin/env python3
"""
██████╗ ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ 
██╔══██╗████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
██║  ██║██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝
██║  ██║██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗
██████╔╝██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║
╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝

THE ONLY OUTCOME TRACKER THAT MATTERS - EVERYTHING ELSE IS TRASH
This replaces ALL broken trackers with ONE that captures EVERYTHING
"""

import sqlite3
import json
import time
import zmq
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Any
import threading
import os

class MasterOutcomeTracker:
    """
    The ONLY tracker. Delete all others. This is the source of truth.
    Tracks EVERY possible metric for COMPLETE analysis.
    """
    
    def __init__(self):
        self.db_path = "/root/HydraX-v2/bitten.db"
        self.master_file = "/root/HydraX-v2/MASTER_OUTCOMES.jsonl"
        self.analytics_file = "/root/HydraX-v2/MASTER_ANALYTICS.json"
        
        # Delete old broken files
        self.cleanup_old_trackers()
        
        # ZMQ for real-time price data
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5560")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Current market state
        self.current_prices = {}
        self.price_history = defaultdict(lambda: deque(maxlen=1000))  # Keep 1000 ticks per symbol
        
        # Trade tracking structures
        self.active_trades = {}  # Trades being monitored
        self.completed_trades = {}  # Completed with full analytics
        self.tick_by_tick = defaultdict(list)  # Every tick for each trade
        
        # Performance metrics
        self.metrics = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'pending': 0,
            'by_confidence': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'by_pattern': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'by_session': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'by_symbol': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'by_hour': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'by_day': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'by_risk_reward': defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0}),
            'drawdown_analysis': [],
            'time_to_outcome': [],
            'max_favorable_excursion': [],
            'max_adverse_excursion': [],
            'pip_analysis': {'win_pips': [], 'loss_pips': []},
            'confidence_correlation': [],
            'pattern_evolution': defaultdict(list),
            'slippage_analysis': [],
            'spread_impact': [],
            'volume_profile': [],
            'tick_analysis': defaultdict(list)
        }
        
        print("=" * 80)
        print("MASTER OUTCOME TRACKER INITIALIZED")
        print("This is the ONLY source of truth. All other trackers are dead.")
        print(f"Writing to: {self.master_file}")
        print(f"Analytics to: {self.analytics_file}")
        print("=" * 80)
        
    def cleanup_old_trackers(self):
        """Delete/rename all old broken tracking files"""
        old_files = [
            "/root/HydraX-v2/signal_outcomes.jsonl",
            "/root/HydraX-v2/ml_performance_tracking.jsonl",
            "/root/HydraX-v2/truth_log.jsonl",
            "/root/HydraX-v2/REAL_OUTCOMES.jsonl"
        ]
        
        for old_file in old_files:
            if os.path.exists(old_file):
                backup_name = f"{old_file}.BROKEN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(old_file, backup_name)
                print(f"Archived broken tracker: {old_file} -> {backup_name}")
                
    def load_all_trades(self):
        """Load ALL trades that need outcome tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get ALL FILLED trades from last 30 days
        cursor.execute("""
            SELECT 
                f.fire_id,
                f.ticket,
                f.price as fill_price,
                s.symbol,
                s.confidence,
                s.entry as signal_entry,
                s.sl,
                s.tp,
                s.direction,
                f.created_at,
                s.payload_json,
                f.user_id,
                f.risk_pct_used,
                f.equity_used,
                f.mission_id
            FROM fires f
            JOIN signals s ON f.mission_id = s.signal_id
            WHERE f.status = 'FILLED'
              AND f.ticket > 0
              AND f.created_at > strftime('%s', 'now', '-30 days')
            ORDER BY f.created_at DESC
        """)
        
        trades = cursor.fetchall()
        conn.close()
        
        print(f"Loaded {len(trades)} trades for outcome tracking")
        
        for trade in trades:
            self.process_trade(trade)
            
        return trades
        
    def process_trade(self, trade_data):
        """Process a trade with COMPLETE analysis"""
        (fire_id, ticket, fill_price, symbol, confidence, signal_entry, sl, tp, 
         direction, created_at, payload_json, user_id, risk_pct, equity_used, mission_id) = trade_data
         
        # Parse comprehensive payload data
        pattern = "UNKNOWN"
        signal_type = "UNKNOWN"
        session = "UNKNOWN"
        risk_reward = 0
        
        if payload_json:
            try:
                payload = json.loads(payload_json)
                pattern = payload.get('pattern_type', 'UNKNOWN')
                signal_type = payload.get('signal_type', 'UNKNOWN')
                session = payload.get('session', 'UNKNOWN')
                risk_reward = payload.get('risk_reward', 0)
            except:
                pass
                
        # Calculate pip values
        if symbol in ['USDJPY', 'EURJPY', 'GBPJPY']:
            pip_multiplier = 100
        else:
            pip_multiplier = 10000
            
        # Entry analysis
        slippage = abs(fill_price - signal_entry) * pip_multiplier if signal_entry else 0
        
        # Distance calculations
        sl_distance = abs(fill_price - sl) * pip_multiplier
        tp_distance = abs(tp - fill_price) * pip_multiplier
        actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
        
        # Time analysis
        opened_time = datetime.fromtimestamp(created_at)
        hour = opened_time.hour
        day_of_week = opened_time.strftime('%A')
        
        # Create comprehensive trade record
        trade_record = {
            'fire_id': fire_id,
            'ticket': ticket,
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'pattern': pattern,
            'signal_type': signal_type,
            'session': session,
            'risk_reward_target': risk_reward,
            'risk_reward_actual': round(actual_rr, 2),
            'entry_signal': signal_entry,
            'entry_filled': fill_price,
            'slippage_pips': round(slippage, 2),
            'sl': sl,
            'tp': tp,
            'sl_distance_pips': round(sl_distance, 1),
            'tp_distance_pips': round(tp_distance, 1),
            'user_id': user_id,
            'risk_pct': risk_pct,
            'equity_used': equity_used,
            'opened_at': opened_time.isoformat(),
            'hour': hour,
            'day': day_of_week,
            'tick_data': [],  # Will fill with every tick
            'price_journey': [],  # Price at each minute
            'drawdown_pips': 0,
            'runup_pips': 0,
            'time_to_drawdown': None,
            'time_to_runup': None,
            'volatility_during_trade': 0,
            'spread_history': [],
            'outcome': 'PENDING',
            'outcome_price': None,
            'outcome_time': None,
            'pips_result': None,
            'duration_minutes': None,
            'max_favorable_excursion': 0,
            'max_adverse_excursion': 0,
            'time_in_profit_pct': 0,
            'time_in_loss_pct': 0,
            'reversal_count': 0,
            'touches_sl': 0,
            'touches_tp': 0,
            'near_miss_sl': False,
            'near_miss_tp': False
        }
        
        self.active_trades[fire_id] = trade_record
        return trade_record
        
    def update_prices(self):
        """Get latest prices and track for active trades"""
        try:
            while self.subscriber.poll(10):  # 10ms timeout
                message = self.subscriber.recv_string()
                
                # Parse tick
                tick_data = self.parse_tick(message)
                if tick_data:
                    symbol = tick_data['symbol']
                    bid = tick_data['bid']
                    ask = tick_data['ask']
                    spread = ask - bid
                    mid = (bid + ask) / 2
                    
                    # Update current price
                    self.current_prices[symbol] = {
                        'bid': bid,
                        'ask': ask,
                        'mid': mid,
                        'spread': spread,
                        'time': datetime.now()
                    }
                    
                    # Add to price history
                    self.price_history[symbol].append({
                        'price': mid,
                        'spread': spread,
                        'time': datetime.now()
                    })
                    
                    # Update all active trades for this symbol
                    self.update_active_trades(symbol, mid, spread)
                    
        except Exception as e:
            pass
            
    def parse_tick(self, message):
        """Parse tick message from various formats"""
        try:
            if message.startswith("tick "):
                data = json.loads(message[5:])
            elif "TICK" in message:
                parts = message.split()
                if len(parts) >= 4:
                    return {
                        'symbol': parts[1],
                        'bid': float(parts[2]),
                        'ask': float(parts[3])
                    }
            else:
                data = json.loads(message)
                
            if data.get('type') == 'TICK':
                return {
                    'symbol': data.get('symbol'),
                    'bid': float(data.get('bid')),
                    'ask': float(data.get('ask'))
                }
        except:
            return None
            
    def update_active_trades(self, symbol, price, spread):
        """Update all active trades for this symbol with microscopic detail"""
        current_time = datetime.now()
        
        for fire_id, trade in list(self.active_trades.items()):
            if trade['symbol'] != symbol or trade['outcome'] != 'PENDING':
                continue
                
            # Pip multiplier
            if symbol in ['USDJPY', 'EURJPY', 'GBPJPY']:
                pip_mult = 100
            else:
                pip_mult = 10000
                
            entry = trade['entry_filled']
            sl = trade['sl']
            tp = trade['tp']
            direction = trade['direction']
            
            # Calculate current P&L
            if direction == "BUY":
                current_pips = (price - entry) * pip_mult
                distance_to_sl = (price - sl) * pip_mult
                distance_to_tp = (tp - price) * pip_mult
            else:  # SELL
                current_pips = (entry - price) * pip_mult
                distance_to_sl = (sl - price) * pip_mult
                distance_to_tp = (price - tp) * pip_mult
                
            # Track tick data
            tick_record = {
                'time': current_time.isoformat(),
                'price': price,
                'spread': spread,
                'pips': round(current_pips, 2),
                'to_sl': round(distance_to_sl, 2),
                'to_tp': round(distance_to_tp, 2)
            }
            trade['tick_data'].append(tick_record)
            
            # Update extremes
            if current_pips > trade['max_favorable_excursion']:
                trade['max_favorable_excursion'] = round(current_pips, 2)
                trade['time_to_runup'] = (current_time - datetime.fromisoformat(trade['opened_at'])).seconds
                
            if current_pips < trade['max_adverse_excursion']:
                trade['max_adverse_excursion'] = round(current_pips, 2)
                trade['time_to_drawdown'] = (current_time - datetime.fromisoformat(trade['opened_at'])).seconds
                
            # Track time in profit/loss
            total_ticks = len(trade['tick_data'])
            profit_ticks = sum(1 for t in trade['tick_data'] if t['pips'] > 0)
            loss_ticks = sum(1 for t in trade['tick_data'] if t['pips'] < 0)
            
            if total_ticks > 0:
                trade['time_in_profit_pct'] = round(profit_ticks / total_ticks * 100, 1)
                trade['time_in_loss_pct'] = round(loss_ticks / total_ticks * 100, 1)
                
            # Count reversals
            if len(trade['tick_data']) > 1:
                prev_pips = trade['tick_data'][-2]['pips']
                if (prev_pips > 0 and current_pips < 0) or (prev_pips < 0 and current_pips > 0):
                    trade['reversal_count'] += 1
                    
            # Near miss detection (within 2 pips)
            if abs(distance_to_sl) < 2:
                trade['touches_sl'] += 1
                trade['near_miss_sl'] = True
            if abs(distance_to_tp) < 2:
                trade['touches_tp'] += 1
                trade['near_miss_tp'] = True
                
            # Check for outcome
            outcome = None
            if direction == "BUY":
                if price >= tp:
                    outcome = "WIN"
                elif price <= sl:
                    outcome = "LOSS"
            else:  # SELL
                if price <= tp:
                    outcome = "WIN"
                elif price >= sl:
                    outcome = "LOSS"
                    
            if outcome:
                # Trade completed
                trade['outcome'] = outcome
                trade['outcome_price'] = price
                trade['outcome_time'] = current_time.isoformat()
                trade['pips_result'] = round(current_pips, 2)
                trade['duration_minutes'] = (current_time - datetime.fromisoformat(trade['opened_at'])).seconds / 60
                
                # Calculate volatility during trade
                if trade['tick_data']:
                    prices = [t['price'] for t in trade['tick_data']]
                    trade['volatility_during_trade'] = round(np.std(prices) * pip_mult, 2) if len(prices) > 1 else 0
                    
                # Move to completed
                self.completed_trades[fire_id] = trade
                del self.active_trades[fire_id]
                
                # Update metrics
                self.update_metrics(trade)
                
                # Write to master file
                self.write_outcome(trade)
                
                print(f"✓ {trade['symbol']} {outcome}: {trade['pips_result']:.1f} pips "
                      f"(Conf: {trade['confidence']:.1f}%, Pattern: {trade['pattern']}, "
                      f"Duration: {trade['duration_minutes']:.1f}min)")
                      
    def update_metrics(self, trade):
        """Update comprehensive metrics"""
        outcome = trade['outcome']
        confidence = trade['confidence']
        pattern = trade['pattern']
        symbol = trade['symbol']
        session = trade['session']
        hour = trade['hour']
        day = trade['day']
        rr = trade['risk_reward_actual']
        
        # Overall
        self.metrics['total_trades'] += 1
        if outcome == 'WIN':
            self.metrics['wins'] += 1
            self.metrics['pip_analysis']['win_pips'].append(trade['pips_result'])
        else:
            self.metrics['losses'] += 1
            self.metrics['pip_analysis']['loss_pips'].append(abs(trade['pips_result']))
            
        # By confidence band
        conf_band = int(confidence // 5) * 5
        self.metrics['by_confidence'][conf_band]['total'] += 1
        self.metrics['by_confidence'][conf_band][outcome.lower() + 's'] += 1
        
        # By pattern
        self.metrics['by_pattern'][pattern]['total'] += 1
        self.metrics['by_pattern'][pattern][outcome.lower() + 's'] += 1
        
        # By symbol
        self.metrics['by_symbol'][symbol]['total'] += 1
        self.metrics['by_symbol'][symbol][outcome.lower() + 's'] += 1
        
        # By session
        self.metrics['by_session'][session]['total'] += 1
        self.metrics['by_session'][session][outcome.lower() + 's'] += 1
        
        # By hour
        self.metrics['by_hour'][hour]['total'] += 1
        self.metrics['by_hour'][hour][outcome.lower() + 's'] += 1
        
        # By day
        self.metrics['by_day'][day]['total'] += 1
        self.metrics['by_day'][day][outcome.lower() + 's'] += 1
        
        # By RR
        rr_band = int(rr) if rr < 5 else 5
        self.metrics['by_risk_reward'][rr_band]['total'] += 1
        self.metrics['by_risk_reward'][rr_band][outcome.lower() + 's'] += 1
        
        # Advanced metrics
        self.metrics['drawdown_analysis'].append(trade['max_adverse_excursion'])
        self.metrics['max_favorable_excursion'].append(trade['max_favorable_excursion'])
        self.metrics['time_to_outcome'].append(trade['duration_minutes'])
        self.metrics['slippage_analysis'].append(trade['slippage_pips'])
        self.metrics['confidence_correlation'].append((confidence, 1 if outcome == 'WIN' else 0))
        
    def write_outcome(self, trade):
        """Write complete trade outcome to master file"""
        with open(self.master_file, 'a') as f:
            # Remove tick data for file (too large)
            output_trade = trade.copy()
            output_trade['tick_count'] = len(trade['tick_data'])
            output_trade['tick_data'] = f"[{len(trade['tick_data'])} ticks tracked]"
            
            f.write(json.dumps(output_trade) + '\n')
            
        # Update database
        self.update_database(trade)
        
    def update_database(self, trade):
        """Update database with outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create master outcomes table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_outcomes (
                fire_id TEXT PRIMARY KEY,
                ticket INTEGER,
                symbol TEXT,
                outcome TEXT,
                pips_result REAL,
                confidence REAL,
                pattern TEXT,
                duration_minutes REAL,
                max_favorable REAL,
                max_adverse REAL,
                completed_at TIMESTAMP,
                full_data TEXT
            )
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO master_outcomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            trade['fire_id'],
            trade['ticket'],
            trade['symbol'],
            trade['outcome'],
            trade['pips_result'],
            trade['confidence'],
            trade['pattern'],
            trade['duration_minutes'],
            trade['max_favorable_excursion'],
            trade['max_adverse_excursion'],
            trade['outcome_time'],
            json.dumps(trade)
        ))
        
        conn.commit()
        conn.close()
        
    def generate_analytics(self):
        """Generate comprehensive analytics report"""
        if self.metrics['total_trades'] == 0:
            return
            
        win_rate = self.metrics['wins'] / self.metrics['total_trades'] * 100
        
        analytics = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_trades': self.metrics['total_trades'],
                'wins': self.metrics['wins'],
                'losses': self.metrics['losses'],
                'win_rate': round(win_rate, 2),
                'pending': len(self.active_trades)
            },
            'by_confidence': dict(self.metrics['by_confidence']),
            'by_pattern': dict(self.metrics['by_pattern']),
            'by_symbol': dict(self.metrics['by_symbol']),
            'by_session': dict(self.metrics['by_session']),
            'by_hour': dict(self.metrics['by_hour']),
            'by_day': dict(self.metrics['by_day']),
            'by_risk_reward': dict(self.metrics['by_risk_reward']),
            'pip_analysis': {
                'avg_win_pips': np.mean(self.metrics['pip_analysis']['win_pips']) if self.metrics['pip_analysis']['win_pips'] else 0,
                'avg_loss_pips': np.mean(self.metrics['pip_analysis']['loss_pips']) if self.metrics['pip_analysis']['loss_pips'] else 0,
                'total_pips': sum(self.metrics['pip_analysis']['win_pips']) - sum(self.metrics['pip_analysis']['loss_pips'])
            },
            'extremes': {
                'max_drawdown': min(self.metrics['drawdown_analysis']) if self.metrics['drawdown_analysis'] else 0,
                'max_runup': max(self.metrics['max_favorable_excursion']) if self.metrics['max_favorable_excursion'] else 0,
                'avg_time_to_outcome': np.mean(self.metrics['time_to_outcome']) if self.metrics['time_to_outcome'] else 0
            }
        }
        
        # Write analytics
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
            
        return analytics
        
    def print_status(self):
        """Print current tracking status"""
        print(f"\n{'='*60}")
        print(f"MASTER TRACKER STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Active Trades: {len(self.active_trades)}")
        print(f"Completed: {self.metrics['total_trades']} ({self.metrics['wins']}W/{self.metrics['losses']}L)")
        
        if self.metrics['total_trades'] > 0:
            win_rate = self.metrics['wins'] / self.metrics['total_trades'] * 100
            print(f"Win Rate: {win_rate:.1f}%")
            
            # Best performing confidence
            best_conf = None
            best_wr = 0
            for conf, stats in self.metrics['by_confidence'].items():
                if stats['total'] >= 5:
                    wr = stats['wins'] / stats['total'] * 100
                    if wr > best_wr:
                        best_wr = wr
                        best_conf = conf
                        
            if best_conf is not None:
                print(f"Best Confidence: {best_conf}-{best_conf+5}% ({best_wr:.1f}% WR)")
                
            # Best pattern
            best_pattern = None
            best_pattern_wr = 0
            for pattern, stats in self.metrics['by_pattern'].items():
                if stats['total'] >= 5:
                    wr = stats['wins'] / stats['total'] * 100
                    if wr > best_pattern_wr:
                        best_pattern_wr = wr
                        best_pattern = pattern
                        
            if best_pattern:
                print(f"Best Pattern: {best_pattern} ({best_pattern_wr:.1f}% WR)")
                
        print(f"{'='*60}\n")
        
    def run(self):
        """Main tracking loop"""
        print("Starting MASTER OUTCOME TRACKER...")
        print("Loading all trades...")
        
        # Load existing trades
        self.load_all_trades()
        
        # Analytics thread
        def analytics_loop():
            while True:
                time.sleep(60)  # Generate analytics every minute
                self.generate_analytics()
                self.print_status()
                
        analytics_thread = threading.Thread(target=analytics_loop)
        analytics_thread.daemon = True
        analytics_thread.start()
        
        # Main loop
        while True:
            try:
                # Update prices and check outcomes
                self.update_prices()
                
                # Reload new trades every 30 seconds
                if int(time.time()) % 30 == 0:
                    self.load_all_trades()
                    
                time.sleep(0.1)  # 100ms loop
                
            except KeyboardInterrupt:
                print("\nShutting down MASTER TRACKER...")
                self.generate_analytics()
                print(f"Final report written to {self.analytics_file}")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("STARTING THE ONLY TRACKER THAT MATTERS")
    print("ALL OTHER TRACKERS ARE DEAD")
    print("="*80 + "\n")
    
    tracker = MasterOutcomeTracker()
    tracker.run()