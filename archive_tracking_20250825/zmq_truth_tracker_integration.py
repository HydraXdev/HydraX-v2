#!/usr/bin/env python3
"""
ZMQ Truth Tracker Integration - Black Box Real-Time Post-Mortem
Tracks every signal from creation to completion with detailed analysis
Shows if we entered too early, got swept, or were trapped
"""

# ┌──────────────────────────────────────────────────────────────┐
# │ BITTEN BLACK BOX TRUTH SYSTEM - CRITICAL ARCHITECTURE       │
# │ Real-time post-mortem analysis for every trade              │
# │ Tracks entry timing, sweeps, traps, and true outcomes       │
# │ The ONLY source of performance truth in BITTEN              │
# └──────────────────────────────────────────────────────────────┘

import zmq
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import threading
from dataclasses import dataclass, asdict
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BlackBoxTruth')

@dataclass
class TruthRecord:
    """Complete truth record for post-mortem analysis"""
    signal_id: str
    symbol: str
    direction: str
    signal_type: str
    tcs_score: float
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # Execution details
    actual_entry: float
    entry_slippage: float
    entry_timestamp: str
    
    # Market behavior
    max_adverse_excursion: float  # How far against us
    max_favorable_excursion: float  # How far in profit
    time_to_max_adverse: int  # Seconds to worst point
    time_to_max_favorable: int  # Seconds to best point
    
    # Outcome
    result: str  # WIN/LOSS/BREAKEVEN
    exit_type: str  # TAKE_PROFIT/STOP_LOSS/MANUAL/TIMEOUT
    exit_price: float
    exit_timestamp: str
    runtime_seconds: int
    
    # Post-mortem analysis
    entry_quality: str  # PERFECT/GOOD/EARLY/LATE/TRAPPED
    sweep_detected: bool
    trap_detected: bool
    optimal_entry_price: float
    entry_efficiency: float  # % of optimal entry achieved
    
    # P&L
    pips_result: float
    dollar_result: float
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format for truth log"""
        return json.dumps(asdict(self))

class ZMQTruthTracker:
    """
    Black Box Truth Tracker with ZMQ Integration
    Provides real-time post-mortem analysis
    """
    
    def __init__(self):
        # ZMQ setup
        self.context = zmq.Context()
        self.telemetry_socket = None
        self.market_socket = None
        
        # Truth log (append-only, never modified)
        self.truth_log = Path("/root/HydraX-v2/truth_log.jsonl")
        
        # Active tracking
        self.active_trades = {}  # signal_id -> trade data
        self.market_data = {}  # symbol -> price data
        
        # Post-mortem analysis
        self.sweep_threshold = 10  # pips
        self.trap_threshold = 5   # pips
        
        # Threading
        self.running = False
        self.lock = threading.Lock()
        
        logger.info("🔒 Black Box Truth Tracker initialized")
        logger.info("📜 Truth log: /root/HydraX-v2/truth_log.jsonl")
        
    def start(self):
        """Start the truth tracking system"""
        try:
            # Connect to ZMQ telemetry
            self.telemetry_socket = self.context.socket(zmq.SUB)
            self.telemetry_socket.connect("tcp://localhost:5556")
            self.telemetry_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.telemetry_socket.setsockopt(zmq.RCVTIMEO, 100)
            
            logger.info("📡 Connected to ZMQ telemetry stream")
            
            self.running = True
            
            # Start monitoring threads
            telemetry_thread = threading.Thread(target=self._monitor_telemetry)
            telemetry_thread.start()
            
            market_thread = threading.Thread(target=self._monitor_market_data)
            market_thread.start()
            
            analysis_thread = threading.Thread(target=self._analyze_active_trades)
            analysis_thread.start()
            
            logger.info("🚀 Black Box Truth System operational")
            
        except Exception as e:
            logger.error(f"Failed to start truth tracker: {e}")
            self.stop()
            
    def stop(self):
        """Stop the tracker"""
        self.running = False
        
        if self.telemetry_socket:
            self.telemetry_socket.close()
        if self.market_socket:
            self.market_socket.close()
            
        self.context.term()
        logger.info("Truth tracker stopped")
        
    def _monitor_telemetry(self):
        """Monitor ZMQ telemetry for trade events"""
        while self.running:
            try:
                message = self.telemetry_socket.recv_string()
                data = json.loads(message)
                
                msg_type = data.get('type', '')
                
                if msg_type == 'trade_result':
                    self._process_trade_entry(data)
                elif msg_type == 'telemetry':
                    self._update_positions(data)
                    
            except zmq.Again:
                pass
            except Exception as e:
                logger.error(f"Telemetry error: {e}")
                
    def _process_trade_entry(self, data):
        """Process new trade entry"""
        signal_id = data.get('signal_id', '')
        status = data.get('status', '')
        
        if status == 'success':
            # Start tracking this trade
            trade_data = {
                'signal_id': signal_id,
                'symbol': data.get('symbol', ''),
                'direction': data.get('action', ''),
                'entry_price': data.get('price', 0),
                'entry_timestamp': datetime.utcnow().isoformat(),
                'ticket': data.get('ticket', 0),
                'sl': data.get('sl', 0),
                'tp': data.get('tp', 0),
                'tcs_score': data.get('tcs_score', 0),
                'signal_type': data.get('signal_type', ''),
                
                # Tracking metrics
                'max_adverse': 0,
                'max_favorable': 0,
                'current_price': data.get('price', 0),
                'start_time': time.time()
            }
            
            with self.lock:
                self.active_trades[signal_id] = trade_data
                
            logger.info(f"📊 Tracking new trade: {signal_id} - {trade_data['symbol']} {trade_data['direction']}")
            
    def _monitor_market_data(self):
        """Get real-time market data"""
        while self.running:
            try:
                # Get market data from receiver
                response = requests.get("http://localhost:8001/market-data/all", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update market prices
                    for symbol, tick_data in data.get('symbols', {}).items():
                        self.market_data[symbol] = {
                            'bid': tick_data.get('bid', 0),
                            'ask': tick_data.get('ask', 0),
                            'timestamp': time.time()
                        }
                        
            except Exception as e:
                logger.error(f"Market data error: {e}")
                
            time.sleep(1)  # Update every second
            
    def _analyze_active_trades(self):
        """Analyze active trades for post-mortem data"""
        while self.running:
            with self.lock:
                for signal_id, trade in list(self.active_trades.items()):
                    self._update_trade_metrics(trade)
                    
                    # Check if trade completed
                    if self._is_trade_complete(trade):
                        self._complete_trade(signal_id, trade)
                        
            time.sleep(1)
            
    def _update_trade_metrics(self, trade):
        """Update trade metrics for analysis"""
        symbol = trade['symbol']
        direction = trade['direction'].lower()
        entry_price = trade['entry_price']
        
        # Get current price
        market = self.market_data.get(symbol, {})
        current_bid = market.get('bid', entry_price)
        current_ask = market.get('ask', entry_price)
        
        # Use appropriate price based on direction
        current_price = current_bid if direction == 'buy' else current_ask
        trade['current_price'] = current_price
        
        # Calculate excursions
        if direction == 'buy':
            profit = current_price - entry_price
        else:
            profit = entry_price - current_price
            
        # Update max adverse/favorable
        if profit < trade['max_adverse']:
            trade['max_adverse'] = profit
            trade['time_to_max_adverse'] = int(time.time() - trade['start_time'])
            
        if profit > trade['max_favorable']:
            trade['max_favorable'] = profit
            trade['time_to_max_favorable'] = int(time.time() - trade['start_time'])
            
    def _is_trade_complete(self, trade):
        """Check if trade hit SL or TP"""
        current_price = trade['current_price']
        direction = trade['direction'].lower()
        
        if direction == 'buy':
            if current_price <= trade['sl'] or current_price >= trade['tp']:
                return True
        else:
            if current_price >= trade['sl'] or current_price <= trade['tp']:
                return True
                
        # Timeout after 4 hours
        if time.time() - trade['start_time'] > 14400:
            return True
            
        return False
        
    def _complete_trade(self, signal_id, trade):
        """Complete trade and write truth record"""
        current_price = trade['current_price']
        direction = trade['direction'].lower()
        entry_price = trade['entry_price']
        
        # Determine outcome
        if direction == 'buy':
            if current_price >= trade['tp']:
                result = 'WIN'
                exit_type = 'TAKE_PROFIT'
            elif current_price <= trade['sl']:
                result = 'LOSS'
                exit_type = 'STOP_LOSS'
            else:
                result = 'BREAKEVEN'
                exit_type = 'TIMEOUT'
        else:
            if current_price <= trade['tp']:
                result = 'WIN'
                exit_type = 'TAKE_PROFIT'
            elif current_price >= trade['sl']:
                result = 'LOSS'
                exit_type = 'STOP_LOSS'
            else:
                result = 'BREAKEVEN'
                exit_type = 'TIMEOUT'
                
        # Post-mortem analysis
        entry_quality, sweep, trap = self._analyze_entry_quality(trade)
        
        # Create truth record
        truth_record = TruthRecord(
            signal_id=signal_id,
            symbol=trade['symbol'],
            direction=trade['direction'],
            signal_type=trade.get('signal_type', ''),
            tcs_score=trade.get('tcs_score', 0),
            entry_price=entry_price,
            stop_loss=trade['sl'],
            take_profit=trade['tp'],
            
            # Execution
            actual_entry=entry_price,
            entry_slippage=0,  # TODO: Calculate from ticket
            entry_timestamp=trade['entry_timestamp'],
            
            # Market behavior
            max_adverse_excursion=trade['max_adverse'],
            max_favorable_excursion=trade['max_favorable'],
            time_to_max_adverse=trade.get('time_to_max_adverse', 0),
            time_to_max_favorable=trade.get('time_to_max_favorable', 0),
            
            # Outcome
            result=result,
            exit_type=exit_type,
            exit_price=current_price,
            exit_timestamp=datetime.utcnow().isoformat(),
            runtime_seconds=int(time.time() - trade['start_time']),
            
            # Analysis
            entry_quality=entry_quality,
            sweep_detected=sweep,
            trap_detected=trap,
            optimal_entry_price=self._calculate_optimal_entry(trade),
            entry_efficiency=self._calculate_entry_efficiency(trade),
            
            # P&L
            pips_result=self._calculate_pips(trade, current_price),
            dollar_result=0  # TODO: Calculate based on lot size
        )
        
        # Write to truth log
        self._write_truth_record(truth_record)
        
        # Remove from active
        del self.active_trades[signal_id]
        
        # Log result with analysis
        logger.info(f"✅ Trade completed: {signal_id}")
        logger.info(f"   Result: {result} via {exit_type}")
        logger.info(f"   Entry Quality: {entry_quality}")
        logger.info(f"   Max Adverse: {trade['max_adverse']:.1f} pips")
        logger.info(f"   Sweep Detected: {sweep}")
        logger.info(f"   Trap Detected: {trap}")
        
    def _analyze_entry_quality(self, trade):
        """Analyze entry quality for post-mortem"""
        max_adverse = abs(trade['max_adverse'])
        max_favorable = trade['max_favorable']
        time_to_adverse = trade.get('time_to_max_adverse', 0)
        
        sweep_detected = False
        trap_detected = False
        
        # Sweep detection (quick adverse move then recovery)
        if max_adverse > self.sweep_threshold and time_to_adverse < 300:  # 5 minutes
            sweep_detected = True
            
        # Trap detection (immediate adverse that doesn't recover)
        if max_adverse > self.trap_threshold and max_favorable < 5:
            trap_detected = True
            
        # Entry quality assessment
        if trap_detected:
            quality = 'TRAPPED'
        elif sweep_detected and max_favorable > 20:
            quality = 'EARLY'  # Entered too early but recovered
        elif max_adverse < 5:
            quality = 'PERFECT'
        elif max_adverse < 10:
            quality = 'GOOD'
        else:
            quality = 'LATE'
            
        return quality, sweep_detected, trap_detected
        
    def _calculate_optimal_entry(self, trade):
        """Calculate what would have been optimal entry"""
        # Optimal entry would be at the best adverse point
        direction = trade['direction'].lower()
        entry = trade['entry_price']
        
        if direction == 'buy':
            return entry + trade['max_adverse']  # Lower price
        else:
            return entry - trade['max_adverse']  # Higher price
            
    def _calculate_entry_efficiency(self, trade):
        """Calculate how efficient our entry was"""
        if trade['max_adverse'] == 0:
            return 100.0
            
        # Efficiency = how much of adverse we avoided
        total_move = abs(trade['max_adverse']) + trade['max_favorable']
        if total_move > 0:
            efficiency = (trade['max_favorable'] / total_move) * 100
            return round(efficiency, 1)
        return 0.0
        
    def _calculate_pips(self, trade, exit_price):
        """Calculate pip result"""
        direction = trade['direction'].lower()
        entry = trade['entry_price']
        
        if direction == 'buy':
            pips = (exit_price - entry) * 10000  # Assuming 4-digit pairs
        else:
            pips = (entry - exit_price) * 10000
            
        return round(pips, 1)
        
    def _write_truth_record(self, record: TruthRecord):
        """Write truth record to append-only log"""
        try:
            with open(self.truth_log, 'a') as f:
                f.write(record.to_jsonl() + '\n')
            logger.info(f"📝 Truth record written: {record.signal_id}")
        except Exception as e:
            logger.error(f"Failed to write truth record: {e}")
            
    def get_recent_analysis(self, limit=10) -> List[Dict]:
        """Get recent trade analysis"""
        records = []
        
        if self.truth_log.exists():
            with open(self.truth_log, 'r') as f:
                lines = f.readlines()
                
            for line in lines[-limit:]:
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except:
                    pass
                    
        return records
        
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        stats = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'perfect_entries': 0,
            'trapped_entries': 0,
            'sweeps_detected': 0,
            'average_adverse': 0,
            'average_favorable': 0
        }
        
        if self.truth_log.exists():
            total_adverse = 0
            total_favorable = 0
            
            with open(self.truth_log, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        stats['total_trades'] += 1
                        
                        if record['result'] == 'WIN':
                            stats['wins'] += 1
                        elif record['result'] == 'LOSS':
                            stats['losses'] += 1
                            
                        if record['entry_quality'] == 'PERFECT':
                            stats['perfect_entries'] += 1
                        elif record['entry_quality'] == 'TRAPPED':
                            stats['trapped_entries'] += 1
                            
                        if record['sweep_detected']:
                            stats['sweeps_detected'] += 1
                            
                        total_adverse += abs(record['max_adverse_excursion'])
                        total_favorable += record['max_favorable_excursion']
                        
                    except:
                        pass
                        
            if stats['total_trades'] > 0:
                stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100
                stats['average_adverse'] = total_adverse / stats['total_trades']
                stats['average_favorable'] = total_favorable / stats['total_trades']
                
        return stats

def main():
    """Run the Black Box Truth Tracker"""
    tracker = ZMQTruthTracker()
    
    try:
        tracker.start()
        
        print("=" * 60)
        print("🔒 BLACK BOX TRUTH TRACKER - REAL-TIME POST-MORTEM")
        print("=" * 60)
        print("📡 Monitoring all trades via ZMQ")
        print("📊 Tracking entry quality, sweeps, and traps")
        print("📜 Truth log: /root/HydraX-v2/truth_log.jsonl")
        print("=" * 60)
        
        # Keep running and show periodic stats
        while True:
            time.sleep(60)
            
            # Show current stats
            stats = tracker.get_statistics()
            active = len(tracker.active_trades)
            
            print(f"\n📊 Black Box Statistics:")
            print(f"   Active Trades: {active}")
            print(f"   Total Tracked: {stats['total_trades']}")
            print(f"   Win Rate: {stats.get('win_rate', 0):.1f}%")
            print(f"   Perfect Entries: {stats['perfect_entries']}")
            print(f"   Trapped Entries: {stats['trapped_entries']}")
            print(f"   Sweeps Detected: {stats['sweeps_detected']}")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        tracker.stop()
        print("✅ Truth tracker stopped")

if __name__ == "__main__":
    main()