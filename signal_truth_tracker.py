#!/usr/bin/env python3
"""
🎯 SIGNAL TRUTH TRACKER - Complete Real-Time Signal Lifecycle Monitoring
Tracks ALL signals from generation through completion with full audit trail
Supports VENOM v7, VENOM v8 Stream, and all signal sources
"""

import json
import time
import os
import threading
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List, Set
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - TRUTH_TRACKER - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SignalTruthEntry:
    """Complete signal truth entry with all lifecycle data"""
    signal_id: str
    timestamp: str
    symbol: str
    direction: str
    rr_ratio: float
    confidence: float
    tcs_score: float
    citadel_score: float
    ml_filter_passed: bool
    status: str  # generated, fired, expired, completed, filtered
    result: Optional[str] = None  # WIN, LOSS, or null
    runtime_seconds: Optional[int] = None
    pips_result: Optional[float] = None
    source: str = "unknown"
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    fire_reason: Optional[str] = None
    user_count: int = 0  # How many users received this signal
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}

class SignalTruthTracker:
    """Real-time signal truth tracking system"""
    
    def __init__(self, truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl"):
        self.truth_log_path = Path(truth_log_path)
        self.active_signals: Dict[str, SignalTruthEntry] = {}
        self.signal_counter = defaultdict(int)  # Per-symbol counter
        self.lock = threading.Lock()
        self.running = False
        
        # Market data for completion tracking
        self.market_data_url = "http://localhost:8001/market-data/all?fast=true"
        self.last_market_check = 0
        self.market_cache = {}
        
        # Ensure truth log exists
        self._ensure_truth_log()
        
        # Load existing active signals
        self._load_active_signals()
        
        logger.info(f"Signal Truth Tracker initialized - tracking to {self.truth_log_path}")
        logger.info(f"Loaded {len(self.active_signals)} active signals for monitoring")
    
    def _ensure_truth_log(self):
        """Ensure truth log file exists and is writable"""
        try:
            if not self.truth_log_path.exists():
                # Create parent directory if needed
                self.truth_log_path.parent.mkdir(parents=True, exist_ok=True)
                # Create empty file
                self.truth_log_path.touch()
                logger.info(f"Created truth log file: {self.truth_log_path}")
            
            # Test writeability
            if not os.access(self.truth_log_path, os.W_OK):
                raise PermissionError(f"Truth log file is not writable: {self.truth_log_path}")
                
        except Exception as e:
            logger.error(f"Failed to ensure truth log: {e}")
            raise
    
    def _load_active_signals(self):
        """Load active signals from existing truth log"""
        if not self.truth_log_path.exists():
            return
            
        try:
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        signal_id = data.get('signal_id')
                        status = data.get('status')
                        
                        if signal_id and status in ['generated', 'fired']:
                            # Reconstruct SignalTruthEntry
                            entry = SignalTruthEntry(
                                signal_id=signal_id,
                                timestamp=data.get('timestamp', ''),
                                symbol=data.get('symbol', ''),
                                direction=data.get('direction', ''),
                                rr_ratio=data.get('rr_ratio', 0.0),
                                confidence=data.get('confidence', 0.0),
                                tcs_score=data.get('tcs_score', 0.0),
                                citadel_score=data.get('citadel_score', 0.0),
                                ml_filter_passed=data.get('ml_filter_passed', False),
                                status=status,
                                result=data.get('result'),
                                runtime_seconds=data.get('runtime_seconds'),
                                pips_result=data.get('pips_result'),
                                source=data.get('source', 'unknown'),
                                entry_price=data.get('entry_price'),
                                stop_loss=data.get('stop_loss'),
                                take_profit=data.get('take_profit'),
                                fire_reason=data.get('fire_reason'),
                                user_count=data.get('user_count', 0)
                            )
                            
                            self.active_signals[signal_id] = entry
                            
                            # Update counter based on signal_id
                            symbol = data.get('symbol', '')
                            if symbol and signal_id.startswith(f"VENOM_{symbol}_"):
                                try:
                                    counter_part = signal_id.split(f"VENOM_{symbol}_")[1]
                                    counter = int(counter_part)
                                    self.signal_counter[symbol] = max(self.signal_counter[symbol], counter)
                                except (IndexError, ValueError):
                                    pass
                                    
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.warning(f"Error loading active signals: {e}")
    
    def generate_signal_id(self, symbol: str, source: str = "venom") -> str:
        """Generate unique signal ID"""
        with self.lock:
            self.signal_counter[symbol] += 1
            counter = self.signal_counter[symbol]
            
            # Format: SOURCE_SYMBOL_NNNNNN
            if source.lower() == "venom_stream_pipeline":
                prefix = "VENOM8"
            elif source.lower().startswith("venom"):
                prefix = "VENOM"
            else:
                prefix = source.upper()
                
            return f"{prefix}_{symbol}_{counter:06d}"
    
    def log_signal_generated(self, 
                           symbol: str,
                           direction: str,
                           confidence: float,
                           entry_price: float = None,
                           stop_loss: float = None,
                           take_profit: float = None,
                           source: str = "venom",
                           tcs_score: float = 0.0,
                           citadel_score: float = 0.0,
                           ml_filter_passed: bool = True,
                           fire_reason: str = None,
                           **kwargs) -> str:
        """Log signal generation event"""
        
        # Generate unique signal ID
        signal_id = self.generate_signal_id(symbol, source)
        
        # Calculate R:R ratio
        rr_ratio = 0.0
        if entry_price and stop_loss and take_profit:
            if direction.upper() == "BUY":
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
            else:  # SELL
                risk = abs(stop_loss - entry_price)
                reward = abs(entry_price - take_profit)
            
            rr_ratio = reward / risk if risk > 0 else 0.0
        
        # Create truth entry
        entry = SignalTruthEntry(
            signal_id=signal_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            symbol=symbol,
            direction=direction.upper(),
            rr_ratio=round(rr_ratio, 2),
            confidence=confidence,
            tcs_score=tcs_score,
            citadel_score=citadel_score,
            ml_filter_passed=ml_filter_passed,
            status="generated",
            source=source,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            fire_reason=fire_reason
        )
        
        # Store active signal
        with self.lock:
            self.active_signals[signal_id] = entry
        
        # Log to truth file
        self._append_to_truth_log(entry)
        
        logger.info(f"🎯 GENERATED: {signal_id} - {symbol} {direction} @{confidence:.1f}% ({source})")
        return signal_id
    
    def log_signal_fired(self, signal_id: str, user_count: int = 1):
        """Log signal dispatch event"""
        with self.lock:
            if signal_id in self.active_signals:
                # Create new entry with updated status
                entry = self.active_signals[signal_id]
                fired_entry = SignalTruthEntry(
                    **{**asdict(entry), 
                       'status': 'fired', 
                       'user_count': user_count,
                       'timestamp': datetime.now(timezone.utc).isoformat()}
                )
                
                self.active_signals[signal_id] = fired_entry
                self._append_to_truth_log(fired_entry)
                
                logger.info(f"🔥 FIRED: {signal_id} → {user_count} users")
            else:
                logger.warning(f"Cannot fire unknown signal: {signal_id}")
    
    def log_signal_filtered(self, signal_id: str, filter_reason: str = "ml_citadel"):
        """Log signal filtering event"""
        with self.lock:
            if signal_id in self.active_signals:
                entry = self.active_signals[signal_id]
                filtered_entry = SignalTruthEntry(
                    **{**asdict(entry), 
                       'status': 'filtered', 
                       'fire_reason': filter_reason,
                       'timestamp': datetime.now(timezone.utc).isoformat()}
                )
                
                # Remove from active (filtered signals don't need completion tracking)
                del self.active_signals[signal_id]
                self._append_to_truth_log(filtered_entry)
                
                logger.info(f"🚫 FILTERED: {signal_id} - {filter_reason}")
    
    def log_signal_expired(self, signal_id: str):
        """Log signal expiration event"""
        with self.lock:
            if signal_id in self.active_signals:
                entry = self.active_signals[signal_id]
                expired_entry = SignalTruthEntry(
                    **{**asdict(entry), 
                       'status': 'expired',
                       'timestamp': datetime.now(timezone.utc).isoformat()}
                )
                
                # Remove from active
                del self.active_signals[signal_id]
                self._append_to_truth_log(expired_entry)
                
                logger.info(f"⏰ EXPIRED: {signal_id}")
    
    def log_signal_completed(self, signal_id: str, result: str, pips_result: float, runtime_seconds: int):
        """Log signal completion event"""
        with self.lock:
            if signal_id in self.active_signals:
                entry = self.active_signals[signal_id]
                completed_entry = SignalTruthEntry(
                    **{**asdict(entry), 
                       'status': 'completed',
                       'result': result.upper(),
                       'pips_result': round(pips_result, 1),
                       'runtime_seconds': runtime_seconds,
                       'timestamp': datetime.now(timezone.utc).isoformat()}
                )
                
                # Remove from active
                del self.active_signals[signal_id]
                self._append_to_truth_log(completed_entry)
                
                result_emoji = "✅" if result.upper() == "WIN" else "❌"
                logger.info(f"{result_emoji} COMPLETED: {signal_id} - {result} {pips_result:+.1f} pips ({runtime_seconds}s)")
    
    def _append_to_truth_log(self, entry: SignalTruthEntry):
        """Append entry to truth log file"""
        try:
            with open(self.truth_log_path, 'a') as f:
                f.write(json.dumps(entry.to_dict(), sort_keys=True) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to truth log: {e}")
    
    def get_market_data(self) -> Dict:
        """Fetch current market data for completion tracking"""
        try:
            # Cache market data for 2 seconds
            if time.time() - self.last_market_check < 2:
                return self.market_cache
                
            response = requests.get(self.market_data_url, timeout=3)
            if response.status_code == 200:
                self.market_cache = response.json()
                self.last_market_check = time.time()
                return self.market_cache
        except:
            pass
            
        return self.market_cache
    
    def check_signal_completions(self):
        """Check active signals for SL/TP completion"""
        market_data = self.get_market_data()
        if not market_data:
            return
            
        completed_signals = []
        
        with self.lock:
            for signal_id, entry in self.active_signals.items():
                if entry.status != "fired" or not entry.entry_price:
                    continue
                    
                symbol_data = market_data.get(entry.symbol)
                if not symbol_data:
                    continue
                    
                try:
                    # Get current price
                    if entry.direction == "BUY":
                        current_price = float(symbol_data.get('bid', 0))
                    else:
                        current_price = float(symbol_data.get('ask', 0))
                    
                    if current_price <= 0:
                        continue
                    
                    # Check for SL/TP hit
                    sl_hit = False
                    tp_hit = False
                    
                    if entry.direction == "BUY":
                        sl_hit = current_price <= entry.stop_loss
                        tp_hit = current_price >= entry.take_profit
                    else:  # SELL
                        sl_hit = current_price >= entry.stop_loss
                        tp_hit = current_price <= entry.take_profit
                    
                    if sl_hit or tp_hit:
                        # Calculate result
                        if tp_hit:
                            result = "WIN"
                            exit_price = entry.take_profit
                        else:
                            result = "LOSS"
                            exit_price = entry.stop_loss
                        
                        # Calculate pips
                        pip_size = 0.0001 if entry.symbol not in ['USDJPY', 'USDCAD'] else 0.01
                        if entry.direction == "BUY":
                            pips_result = (exit_price - entry.entry_price) / pip_size
                        else:
                            pips_result = (entry.entry_price - exit_price) / pip_size
                        
                        # Calculate runtime
                        entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                        runtime_seconds = int((datetime.now(timezone.utc) - entry_time).total_seconds())
                        
                        completed_signals.append((signal_id, result, pips_result, runtime_seconds))
                        
                except Exception as e:
                    logger.warning(f"Error checking completion for {signal_id}: {e}")
        
        # Log completions
        for signal_id, result, pips_result, runtime_seconds in completed_signals:
            self.log_signal_completed(signal_id, result, pips_result, runtime_seconds)
    
    def expire_old_signals(self, max_age_hours: int = 24):
        """Expire signals older than max_age_hours"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        expired_signals = []
        
        with self.lock:
            for signal_id, entry in self.active_signals.items():
                try:
                    entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                    if entry_time.timestamp() < cutoff_time:
                        expired_signals.append(signal_id)
                except:
                    continue
        
        for signal_id in expired_signals:
            self.log_signal_expired(signal_id)
    
    def start_monitoring(self):
        """Start background monitoring threads"""
        self.running = True
        
        # Completion monitoring thread
        def completion_monitor():
            while self.running:
                try:
                    self.check_signal_completions()
                    time.sleep(1)  # Check every second
                except Exception as e:
                    logger.error(f"Completion monitor error: {e}")
                    time.sleep(5)
        
        # Expiration monitoring thread
        def expiration_monitor():
            while self.running:
                try:
                    self.expire_old_signals()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Expiration monitor error: {e}")
                    time.sleep(60)
        
        # Start threads
        threading.Thread(target=completion_monitor, daemon=True).start()
        threading.Thread(target=expiration_monitor, daemon=True).start()
        
        logger.info("🎯 Truth tracking monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        logger.info("🛑 Truth tracking monitoring stopped")
    
    def get_status(self) -> Dict:
        """Get current tracker status"""
        with self.lock:
            return {
                'active_signals': len(self.active_signals),
                'signal_counters': dict(self.signal_counter),
                'truth_log_path': str(self.truth_log_path),
                'running': self.running
            }
    
    def inspect_signal(self, signal_id: str) -> List[Dict]:
        """Inspect complete lifecycle of a signal"""
        entries = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get('signal_id') == signal_id:
                            entries.append(data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error inspecting signal {signal_id}: {e}")
        
        return entries
    
    def get_recent_signals(self, count: int = 10) -> List[Dict]:
        """Get recent signal entries"""
        entries = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                lines = f.readlines()
                
            # Get last N lines
            for line in lines[-count:]:
                try:
                    data = json.loads(line.strip())
                    entries.append(data)
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
        
        return entries

# Global tracker instance
tracker = SignalTruthTracker()

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Signal Truth Tracker - Complete signal lifecycle monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 signal_truth_tracker.py                              # Start monitoring daemon
  python3 signal_truth_tracker.py --inspect VENOM_EURUSD_000123 # Inspect signal lifecycle
  python3 signal_truth_tracker.py --recent 20                  # Show recent 20 signals
  python3 signal_truth_tracker.py --status                     # Show tracker status
        """
    )
    
    parser.add_argument('--inspect', type=str, help='Inspect specific signal ID')
    parser.add_argument('--recent', type=int, help='Show recent N signals')
    parser.add_argument('--status', action='store_true', help='Show tracker status')
    
    args = parser.parse_args()
    
    if args.inspect:
        # Inspect specific signal
        entries = tracker.inspect_signal(args.inspect)
        if entries:
            print(f"\n🔍 SIGNAL LIFECYCLE: {args.inspect}")
            print("=" * 80)
            for i, entry in enumerate(entries, 1):
                status = entry.get('status', 'unknown')
                timestamp = entry.get('timestamp', '')[:19]  # Remove microseconds
                result = entry.get('result', '')
                pips = entry.get('pips_result', '')
                
                status_emoji = {
                    'generated': '🎯',
                    'fired': '🔥',
                    'filtered': '🚫',
                    'expired': '⏰',
                    'completed': '✅' if result == 'WIN' else '❌'
                }.get(status, '❓')
                
                print(f"{i}. {status_emoji} {status.upper()} - {timestamp}")
                if result:
                    print(f"   Result: {result} {pips:+.1f} pips")
                if entry.get('fire_reason'):
                    print(f"   Reason: {entry.get('fire_reason')}")
                print()
        else:
            print(f"❌ No entries found for signal: {args.inspect}")
    
    elif args.recent:
        # Show recent signals
        entries = tracker.get_recent_signals(args.recent)
        if entries:
            print(f"\n📊 RECENT {len(entries)} SIGNALS")
            print("=" * 100)
            print(f"{'Signal ID':<25} {'Symbol':<8} {'Status':<10} {'Result':<6} {'Pips':<8} {'Source':<15}")
            print("-" * 100)
            
            for entry in entries:
                signal_id = entry.get('signal_id', 'unknown')[:24]
                symbol = entry.get('symbol', '')
                status = entry.get('status', '')
                result = entry.get('result', '') or '-'
                pips = entry.get('pips_result', '')
                pips_str = f"{pips:+.1f}" if pips != '' else '-'
                source = entry.get('source', '')[:14]
                
                print(f"{signal_id:<25} {symbol:<8} {status:<10} {result:<6} {pips_str:<8} {source:<15}")
        else:
            print("❌ No recent signals found")
    
    elif args.status:
        # Show status
        status = tracker.get_status()
        print(f"\n🎯 TRUTH TRACKER STATUS")
        print("=" * 40)
        print(f"Active Signals: {status['active_signals']}")
        print(f"Truth Log: {status['truth_log_path']}")
        print(f"Running: {status['running']}")
        print(f"Signal Counters: {status['signal_counters']}")
    
    else:
        # Start monitoring daemon
        print("🎯 SIGNAL TRUTH TRACKER - Starting monitoring daemon")
        print(f"Truth log: {tracker.truth_log_path}")
        print(f"Active signals: {len(tracker.active_signals)}")
        print("Press Ctrl+C to stop")
        
        try:
            tracker.start_monitoring()
            
            while True:
                time.sleep(30)
                status = tracker.get_status()
                logger.info(f"Status: {status['active_signals']} active signals")
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            tracker.stop_monitoring()

if __name__ == "__main__":
    main()