#!/usr/bin/env python3
"""
Black Box Complete Truth System - The ONLY source of truth
Tracks EVERY signal from generation to completion with live market data
Records which hits first (SL/TP), total runtime, max excursions, everything
"""

# ┌──────────────────────────────────────────────────────────────┐
# │ BLACK BOX COMPLETE TRUTH SYSTEM - PERMANENT DAEMON           │
# │ This is the ONLY ground truth for ALL BITTEN signals        │
# │ Logs generation → execution → completion with full metrics   │
# │ Used for XP, performance reporting, post-mortem analysis     │
# └──────────────────────────────────────────────────────────────┘

import json
import time
import logging
import threading
import requests
import zmq
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BlackBoxTruth')

@dataclass
class CompleteSignalRecord:
    """Complete lifecycle record for EVERY signal"""
    # Generation data
    signal_id: str
    generated_at: str
    symbol: str
    direction: str
    signal_type: str
    
    # Quality metrics at generation
    tcs_score: float
    confidence: float
    
    # Entry/exit levels
    entry_price: float
    stop_loss: float
    take_profit: float
    target_pips: float
    stop_pips: float
    risk_reward: float
    
    # Optional fields with defaults
    citadel_score: float = 0.0
    venom_version: str = "v7.0"
    
    # Market conditions at generation
    spread_at_generation: float = 0
    session: str = "unknown"
    
    # Distribution tracking
    sent_to_users: bool = False
    user_count: int = 0
    users_fired: List[str] = field(default_factory=list)
    
    # Execution tracking
    first_execution_at: Optional[str] = None
    execution_count: int = 0
    avg_execution_price: float = 0
    execution_slippage: float = 0
    
    # Live market tracking
    current_price: float = 0
    max_favorable_price: float = 0
    max_adverse_price: float = 0
    max_favorable_pips: float = 0
    max_adverse_pips: float = 0
    time_to_max_favorable: int = 0  # seconds
    time_to_max_adverse: int = 0    # seconds
    
    # Completion data
    completed: bool = False
    completed_at: Optional[str] = None
    outcome: Optional[str] = None  # WIN_TP, LOSS_SL, EXPIRED, CANCELLED
    exit_price: float = 0
    exit_type: Optional[str] = None  # TAKE_PROFIT, STOP_LOSS, MANUAL, TIMEOUT
    runtime_seconds: int = 0
    
    # Post-mortem analysis
    hit_tp_first: bool = False
    hit_sl_first: bool = False
    time_to_tp: Optional[int] = None  # seconds if TP was touched
    time_to_sl: Optional[int] = None  # seconds if SL was touched
    whipsawed: bool = False  # Hit SL then would have hit TP
    trapped: bool = False    # Immediate adverse with no recovery
    
    # Performance metrics
    pips_result: float = 0
    percent_of_target: float = 0  # How much of target was achieved
    efficiency_score: float = 0   # Entry efficiency
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format for truth log"""
        return json.dumps(asdict(self))

class BlackBoxCompleteTruthSystem:
    """
    Complete truth tracking system with live market monitoring
    Tracks EVERY signal from generation to completion
    """
    
    def __init__(self):
        # File paths
        self.truth_log = Path("/root/HydraX-v2/truth_log.jsonl")
        self.active_signals_file = Path("/root/HydraX-v2/active_signals.json")
        
        # Live tracking
        self.active_signals: Dict[str, CompleteSignalRecord] = {}
        self.completed_signals: List[str] = []
        
        # Market data
        self.market_data_url = "http://localhost:8001/market-data/venom-feed"
        self.market_cache: Dict[str, Dict] = {}
        
        # ZMQ setup for execution monitoring
        self.zmq_context = zmq.Context()
        self.telemetry_socket = None
        
        # Statistics
        self.stats = {
            'total_generated': 0,
            'total_completed': 0,
            'wins_tp': 0,
            'losses_sl': 0,
            'expired': 0,
            'whipsawed': 0,
            'trapped': 0,
            'avg_runtime_win': 0,
            'avg_runtime_loss': 0
        }
        
        # Threading
        self.running = False
        self.lock = threading.Lock()
        
        # Load any active signals from previous session
        self._load_active_signals()
        
        logger.info("🔒 Black Box Complete Truth System initialized")
        logger.info("📜 Truth log: /root/HydraX-v2/truth_log.jsonl")
        logger.info("📊 Tracking EVERY signal from generation to completion")
        
    def start(self):
        """Start the complete monitoring system"""
        self.running = True
        
        # Connect to ZMQ for execution monitoring
        try:
            self.telemetry_socket = self.zmq_context.socket(zmq.SUB)
            self.telemetry_socket.connect("tcp://localhost:5556")
            self.telemetry_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.telemetry_socket.setsockopt(zmq.RCVTIMEO, 100)
            logger.info("📡 Connected to ZMQ telemetry")
        except Exception as e:
            logger.error(f"ZMQ connection failed: {e}")
        
        # Start monitoring threads
        market_thread = threading.Thread(target=self._market_monitor_loop, daemon=True)
        market_thread.start()
        
        execution_thread = threading.Thread(target=self._execution_monitor_loop, daemon=True)
        execution_thread.start()
        
        completion_thread = threading.Thread(target=self._completion_monitor_loop, daemon=True)
        completion_thread.start()
        
        logger.info("🚀 Black Box monitoring started")
        
    def stop(self):
        """Stop the monitoring system"""
        self.running = False
        self._save_active_signals()
        
        if self.telemetry_socket:
            self.telemetry_socket.close()
        self.zmq_context.term()
        
        logger.info("Black Box monitoring stopped")
        
    def log_signal_generation(self, signal_data: Dict) -> Dict:
        """
        Log a newly generated signal - called from webapp interceptor
        This is the ENTRY POINT for all signals
        """
        try:
            # Create complete signal record
            record = CompleteSignalRecord(
                signal_id=signal_data.get('signal_id', f"UNKNOWN_{int(time.time() * 1000)}"),
                generated_at=datetime.utcnow().isoformat(),
                symbol=signal_data.get('symbol', 'UNKNOWN'),
                direction=signal_data.get('direction', 'UNKNOWN'),
                signal_type=signal_data.get('signal_type', 'UNKNOWN'),
                
                # Quality scores
                tcs_score=signal_data.get('tcs_score', 0),
                confidence=signal_data.get('confidence', 0),
                citadel_score=signal_data.get('citadel_shield', {}).get('score', 0) if isinstance(signal_data.get('citadel_shield'), dict) else 0,
                
                # Levels
                entry_price=signal_data.get('entry', 0),
                stop_loss=signal_data.get('sl', 0),
                take_profit=signal_data.get('tp', 0),
                target_pips=signal_data.get('target_pips', 0),
                stop_pips=signal_data.get('stop_pips', 0),
                risk_reward=signal_data.get('risk_reward', 0),
                
                # Market conditions
                spread_at_generation=signal_data.get('spread', 0),
                session=signal_data.get('session', self._get_current_session()),
                
                # Initialize price tracking
                current_price=signal_data.get('entry', 0),
                max_favorable_price=signal_data.get('entry', 0),
                max_adverse_price=signal_data.get('entry', 0)
            )
            
            # Add to active tracking
            with self.lock:
                self.active_signals[record.signal_id] = record
                self.stats['total_generated'] += 1
            
            # Write initial record to truth log
            self._append_to_truth_log(record)
            
            logger.info(f"📝 Signal logged: {record.signal_id} - {record.symbol} {record.direction}")
            logger.info(f"   Quality: TCS {record.tcs_score}% | Confidence {record.confidence}% | CITADEL {record.citadel_score}/10")
            logger.info(f"   Total signals today: {self.stats['total_generated']}")
            
        except Exception as e:
            logger.error(f"Failed to log signal generation: {e}")
            
        return signal_data
        
    def log_signal_distribution(self, signal_id: str, user_count: int):
        """Log when signal is sent to users"""
        with self.lock:
            if signal_id in self.active_signals:
                self.active_signals[signal_id].sent_to_users = True
                self.active_signals[signal_id].user_count = user_count
                logger.info(f"📤 Signal distributed: {signal_id} to {user_count} users")
                
    def log_user_fired(self, signal_id: str, user_id: str, execution_price: float = 0):
        """Log when a user fires on a signal"""
        with self.lock:
            if signal_id in self.active_signals:
                signal = self.active_signals[signal_id]
                signal.users_fired.append(user_id)
                signal.execution_count += 1
                
                if not signal.first_execution_at:
                    signal.first_execution_at = datetime.utcnow().isoformat()
                    
                # Track execution price
                if execution_price > 0:
                    if signal.avg_execution_price == 0:
                        signal.avg_execution_price = execution_price
                    else:
                        # Running average
                        signal.avg_execution_price = (
                            (signal.avg_execution_price * (signal.execution_count - 1) + execution_price) 
                            / signal.execution_count
                        )
                    
                    # Calculate slippage
                    signal.execution_slippage = abs(execution_price - signal.entry_price)
                    
                logger.info(f"🔥 User fired: {user_id} on {signal_id} @ {execution_price}")
                
    def _market_monitor_loop(self):
        """Monitor live market data for all active signals"""
        while self.running:
            try:
                # Get market data for all symbols
                active_symbols = set()
                with self.lock:
                    for signal in self.active_signals.values():
                        if not signal.completed:
                            active_symbols.add(signal.symbol)
                
                # Fetch market data
                for symbol in active_symbols:
                    try:
                        response = requests.get(
                            f"{self.market_data_url}?symbol={symbol}",
                            timeout=2
                        )
                        if response.status_code == 200:
                            data = response.json()
                            self.market_cache[symbol] = {
                                'bid': data.get('bid', 0),
                                'ask': data.get('ask', 0),
                                'timestamp': time.time()
                            }
                    except Exception as e:
                        logger.debug(f"Market data error for {symbol}: {e}")
                
                # Update all active signals with market data
                self._update_signal_prices()
                
            except Exception as e:
                logger.error(f"Market monitor error: {e}")
                
            time.sleep(1)  # Check every second
            
    def _update_signal_prices(self):
        """Update all active signals with current market prices"""
        with self.lock:
            for signal_id, signal in self.active_signals.items():
                if signal.completed:
                    continue
                    
                market = self.market_cache.get(signal.symbol, {})
                if not market:
                    continue
                    
                # Get appropriate price based on direction
                if signal.direction.upper() == 'BUY':
                    current_price = market.get('bid', signal.current_price)
                else:
                    current_price = market.get('ask', signal.current_price)
                    
                signal.current_price = current_price
                
                # Calculate current P&L in pips
                if signal.direction.upper() == 'BUY':
                    current_pips = (current_price - signal.entry_price) * 10000
                else:
                    current_pips = (signal.entry_price - current_price) * 10000
                    
                # Update max favorable/adverse
                if current_pips > signal.max_favorable_pips:
                    signal.max_favorable_pips = current_pips
                    signal.max_favorable_price = current_price
                    signal.time_to_max_favorable = int(
                        (datetime.utcnow() - datetime.fromisoformat(signal.generated_at)).total_seconds()
                    )
                    
                if current_pips < signal.max_adverse_pips:
                    signal.max_adverse_pips = current_pips
                    signal.max_adverse_price = current_price
                    signal.time_to_max_adverse = int(
                        (datetime.utcnow() - datetime.fromisoformat(signal.generated_at)).total_seconds()
                    )
                    
                # Check if hit SL or TP
                self._check_sl_tp_hit(signal, current_price)
                
    def _check_sl_tp_hit(self, signal: CompleteSignalRecord, current_price: float):
        """Check if signal has hit SL or TP"""
        runtime = int((datetime.utcnow() - datetime.fromisoformat(signal.generated_at)).total_seconds())
        
        if signal.direction.upper() == 'BUY':
            # Check TP
            if current_price >= signal.take_profit and not signal.hit_tp_first and not signal.hit_sl_first:
                signal.hit_tp_first = True
                signal.time_to_tp = runtime
                logger.info(f"🎯 TP touched first: {signal.signal_id} after {runtime}s")
                
            # Check SL
            if current_price <= signal.stop_loss and not signal.hit_sl_first and not signal.hit_tp_first:
                signal.hit_sl_first = True
                signal.time_to_sl = runtime
                logger.info(f"🛑 SL touched first: {signal.signal_id} after {runtime}s")
                
        else:  # SELL
            # Check TP
            if current_price <= signal.take_profit and not signal.hit_tp_first and not signal.hit_sl_first:
                signal.hit_tp_first = True
                signal.time_to_tp = runtime
                logger.info(f"🎯 TP touched first: {signal.signal_id} after {runtime}s")
                
            # Check SL
            if current_price >= signal.stop_loss and not signal.hit_sl_first and not signal.hit_tp_first:
                signal.hit_sl_first = True
                signal.time_to_sl = runtime
                logger.info(f"🛑 SL touched first: {signal.signal_id} after {runtime}s")
                
    def _execution_monitor_loop(self):
        """Monitor ZMQ for execution events"""
        if not self.telemetry_socket:
            return
            
        while self.running:
            try:
                message = self.telemetry_socket.recv_string()
                data = json.loads(message)
                
                if data.get('type') == 'trade_result':
                    signal_id = data.get('signal_id', '')
                    if data.get('status') == 'success':
                        self.log_user_fired(
                            signal_id,
                            data.get('uuid', 'unknown'),
                            data.get('price', 0)
                        )
                        
            except zmq.Again:
                pass
            except Exception as e:
                logger.debug(f"Execution monitor error: {e}")
                
    def _completion_monitor_loop(self):
        """Monitor for signal completion"""
        while self.running:
            try:
                with self.lock:
                    for signal_id, signal in list(self.active_signals.items()):
                        if signal.completed:
                            continue
                            
                        runtime = int((datetime.utcnow() - datetime.fromisoformat(signal.generated_at)).total_seconds())
                        
                        # Check completion conditions
                        completed = False
                        outcome = None
                        exit_type = None
                        exit_price = signal.current_price
                        
                        # Hit TP
                        if signal.hit_tp_first and runtime - signal.time_to_tp > 60:  # Confirm for 1 minute
                            completed = True
                            outcome = "WIN_TP"
                            exit_type = "TAKE_PROFIT"
                            exit_price = signal.take_profit
                            
                        # Hit SL
                        elif signal.hit_sl_first and runtime - signal.time_to_sl > 60:  # Confirm for 1 minute
                            completed = True
                            outcome = "LOSS_SL"
                            exit_type = "STOP_LOSS"
                            exit_price = signal.stop_loss
                            
                            # Check if whipsawed (hit SL but later would have hit TP)
                            if signal.max_favorable_pips >= signal.target_pips * 0.8:
                                signal.whipsawed = True
                                
                        # Timeout after 4 hours
                        elif runtime > 14400:
                            completed = True
                            outcome = "EXPIRED"
                            exit_type = "TIMEOUT"
                            
                        # Mark as trapped if immediate adverse
                        if signal.max_adverse_pips < -10 and signal.time_to_max_adverse < 300:
                            signal.trapped = True
                            
                        if completed:
                            self._complete_signal(signal, outcome, exit_type, exit_price, runtime)
                            
            except Exception as e:
                logger.error(f"Completion monitor error: {e}")
                
            time.sleep(5)  # Check every 5 seconds
            
    def _complete_signal(self, signal: CompleteSignalRecord, outcome: str, exit_type: str, exit_price: float, runtime: int):
        """Complete a signal and calculate final metrics"""
        signal.completed = True
        signal.completed_at = datetime.utcnow().isoformat()
        signal.outcome = outcome
        signal.exit_type = exit_type
        signal.exit_price = exit_price
        signal.runtime_seconds = runtime
        
        # Calculate final P&L
        if signal.direction.upper() == 'BUY':
            signal.pips_result = (exit_price - signal.entry_price) * 10000
        else:
            signal.pips_result = (signal.entry_price - exit_price) * 10000
            
        # Calculate percent of target achieved
        if signal.target_pips > 0:
            signal.percent_of_target = (signal.pips_result / signal.target_pips) * 100
            
        # Calculate efficiency score
        if signal.max_adverse_pips < 0:
            total_range = abs(signal.max_adverse_pips) + signal.max_favorable_pips
            if total_range > 0:
                signal.efficiency_score = (signal.max_favorable_pips / total_range) * 100
                
        # Update statistics
        self.stats['total_completed'] += 1
        if outcome == "WIN_TP":
            self.stats['wins_tp'] += 1
            self.stats['avg_runtime_win'] = (
                (self.stats['avg_runtime_win'] * (self.stats['wins_tp'] - 1) + runtime)
                / self.stats['wins_tp']
            )
        elif outcome == "LOSS_SL":
            self.stats['losses_sl'] += 1
            self.stats['avg_runtime_loss'] = (
                (self.stats['avg_runtime_loss'] * (self.stats['losses_sl'] - 1) + runtime)
                / self.stats['losses_sl']
            )
        elif outcome == "EXPIRED":
            self.stats['expired'] += 1
            
        if signal.whipsawed:
            self.stats['whipsawed'] += 1
        if signal.trapped:
            self.stats['trapped'] += 1
            
        # Write final record
        self._append_to_truth_log(signal)
        
        # Remove from active
        del self.active_signals[signal.signal_id]
        self.completed_signals.append(signal.signal_id)
        
        # Log completion
        logger.info(f"✅ Signal completed: {signal.signal_id}")
        logger.info(f"   Outcome: {outcome} via {exit_type} after {runtime}s")
        logger.info(f"   Result: {signal.pips_result:.1f} pips ({signal.percent_of_target:.0f}% of target)")
        logger.info(f"   Max Favorable: {signal.max_favorable_pips:.1f} pips")
        logger.info(f"   Max Adverse: {signal.max_adverse_pips:.1f} pips")
        if signal.whipsawed:
            logger.info(f"   ⚠️ WHIPSAWED - Hit SL but would have hit TP")
        if signal.trapped:
            logger.info(f"   🪤 TRAPPED - Immediate adverse move")
            
    def _append_to_truth_log(self, record: CompleteSignalRecord):
        """Append record to truth log"""
        try:
            with open(self.truth_log, 'a') as f:
                f.write(record.to_jsonl() + '\n')
        except Exception as e:
            logger.error(f"Failed to write to truth log: {e}")
            
    def _save_active_signals(self):
        """Save active signals to file for persistence"""
        try:
            active_data = {}
            with self.lock:
                for signal_id, signal in self.active_signals.items():
                    active_data[signal_id] = asdict(signal)
                    
            with open(self.active_signals_file, 'w') as f:
                json.dump(active_data, f, indent=2)
                
            logger.info(f"Saved {len(active_data)} active signals")
            
        except Exception as e:
            logger.error(f"Failed to save active signals: {e}")
            
    def _load_active_signals(self):
        """Load active signals from previous session"""
        if self.active_signals_file.exists():
            try:
                with open(self.active_signals_file, 'r') as f:
                    active_data = json.load(f)
                    
                for signal_id, data in active_data.items():
                    # Reconstruct signal record
                    signal = CompleteSignalRecord(**data)
                    self.active_signals[signal_id] = signal
                    
                logger.info(f"Loaded {len(self.active_signals)} active signals from previous session")
                
            except Exception as e:
                logger.error(f"Failed to load active signals: {e}")
                
    def _get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.utcnow().hour
        if 7 <= hour < 16:
            return "LONDON"
        elif 12 <= hour < 21:
            return "NEWYORK"
        elif 23 <= hour or hour < 7:
            return "ASIAN"
        else:
            return "OVERLAP"
            
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        total = self.stats['total_generated']
        completed = self.stats['total_completed']
        wins = self.stats['wins_tp']
        losses = self.stats['losses_sl']
        
        stats = {
            'total_signals_generated': total,
            'total_completed': completed,
            'active_signals': len(self.active_signals),
            'wins': wins,
            'losses': losses,
            'expired': self.stats['expired'],
            'win_rate': (wins / completed * 100) if completed > 0 else 0,
            'whipsawed_count': self.stats['whipsawed'],
            'trapped_count': self.stats['trapped'],
            'avg_runtime_win_minutes': self.stats['avg_runtime_win'] / 60 if self.stats['avg_runtime_win'] > 0 else 0,
            'avg_runtime_loss_minutes': self.stats['avg_runtime_loss'] / 60 if self.stats['avg_runtime_loss'] > 0 else 0
        }
        
        return stats

# Global instance
_truth_system = None

def get_truth_system() -> BlackBoxCompleteTruthSystem:
    """Get or create singleton truth system"""
    global _truth_system
    if not _truth_system:
        _truth_system = BlackBoxCompleteTruthSystem()
    return _truth_system

def main():
    """Run as permanent daemon"""
    truth_system = get_truth_system()
    
    # Handle shutdown
    def signal_handler(sig, frame):
        logger.info("\nShutdown signal received")
        truth_system.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    truth_system.start()
    
    logger.info("=" * 60)
    logger.info("🔒 BLACK BOX COMPLETE TRUTH SYSTEM - PERMANENT DAEMON")
    logger.info("=" * 60)
    logger.info("📊 Tracking ALL signals from generation to completion")
    logger.info("📡 Monitoring live market data for SL/TP detection")
    logger.info("📜 Truth log: /root/HydraX-v2/truth_log.jsonl")
    logger.info("=" * 60)
    
    # Run forever
    while True:
        try:
            time.sleep(60)
            
            # Show periodic stats
            stats = truth_system.get_statistics()
            logger.info(f"\n📊 Black Box Statistics:")
            logger.info(f"   Generated: {stats['total_signals_generated']}")
            logger.info(f"   Active: {stats['active_signals']}")
            logger.info(f"   Completed: {stats['total_completed']}")
            logger.info(f"   Win Rate: {stats['win_rate']:.1f}%")
            logger.info(f"   Whipsawed: {stats['whipsawed_count']}")
            logger.info(f"   Trapped: {stats['trapped_count']}")
            
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            
if __name__ == "__main__":
    main()