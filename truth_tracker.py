#!/usr/bin/env python3
"""
Truth Tracker - Real-time signal outcome monitoring
Tracks every signal from creation to SL or TP hit using live market data
"""

import json
import os
import time
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiohttp
import aiofiles

# Market data configuration
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://127.0.0.1:8001/market-data")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SignalTracker:
    """Individual signal being tracked"""
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    tcs_score: float
    created_at: float
    start_time: float
    # 📊 METADATA TRACKING: Additional fields for ML training and analytics
    citadel_score: float = 0.0
    ml_filter_passed: str = "unknown"
    source: str = "unknown"
    
    def __post_init__(self):
        self.start_time = time.time()

class TruthTracker:
    """
    Real-time signal outcome tracker
    Monitors signals and logs WIN/LOSS results based on live market data
    """
    
    def __init__(self, 
                 signals_folder: str = "/root/HydraX-v2/missions",
                 truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl",
                 market_data_url: str = MARKET_DATA_URL,
                 citadel_state_path: str = "/root/HydraX-v2/citadel_state.json"):
        
        self.signals_folder = Path(signals_folder)
        self.truth_log_path = Path(truth_log_path)
        self.market_data_url = market_data_url
        self.citadel_state_path = Path(citadel_state_path)
        
        # Active signal tracking
        self.active_signals: Dict[str, SignalTracker] = {}
        self.processed_signals: Set[str] = set()
        
        # Threading
        self.running = False
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Market data cache
        self.market_data_cache: Dict[str, Dict] = {}
        self.last_market_update = 0
        
        # Default AUTO_CLOSE_SECONDS
        self.default_auto_close_seconds = 7200  # 2 hours
        
        logger.info("Truth Tracker initialized")
        logger.info(f"[CONFIG] Connected to market data source: {self.market_data_url}")
    
    def load_existing_signals(self):
        """Load existing signal files for tracking (both main and user-specific)"""
        if not self.signals_folder.exists():
            logger.warning(f"Signals folder {self.signals_folder} does not exist")
            return
        
        # Scan both main mission files and user-specific mission files
        file_patterns = ["mission_*.json", "5_*_USER*.json"]
        
        for pattern in file_patterns:
            for signal_file in self.signals_folder.glob(pattern):
                try:
                    with open(signal_file, 'r') as f:
                        data = json.load(f)
                    
                    signal_id = data.get('signal_id') or data.get('mission_id')  # Support both formats
                    if signal_id and signal_id not in self.processed_signals:
                        tracker = self._create_signal_tracker(data, signal_file.stat().st_mtime)
                        if tracker:
                            with self.lock:
                                self.active_signals[signal_id] = tracker
                            logger.info(f"Loaded existing signal: {signal_id}")
                            
                except Exception as e:
                    logger.error(f"Error loading signal file {signal_file}: {e}")
    
    def _create_signal_tracker(self, data: Dict, file_time: float) -> Optional[SignalTracker]:
        """Create SignalTracker from signal data with source validation"""
        try:
            # Extract signal data (support both formats)
            signal_id = data.get('signal_id') or data.get('mission_id')
            if not signal_id:
                return None
            
            # 🛡️ SECURITY: Reject signals from unauthorized sources
            source = data.get('source', '')
            if source != 'venom_scalp_master':
                logger.warning(f"[REJECTED] Signal from unknown source: {source if source else 'MISSING'} - {signal_id}")
                return None
            
            # Handle both signal formats (VENOM_SCALP and USER missions)
            if 'enhanced_signal' in data:
                # VENOM_SCALP format
                enhanced = data.get('enhanced_signal', {})
                basic = data.get('signal', {})
                symbol = data.get('pair') or enhanced.get('symbol') or basic.get('symbol')
                direction = data.get('direction') or enhanced.get('direction')
                entry_price = enhanced.get('entry_price') or 0
                stop_loss = enhanced.get('stop_loss') or 0  
                take_profit = enhanced.get('take_profit') or 0
                tcs_score = data.get('confidence', 0)
                created_at = data.get('timestamp', file_time)
            else:
                # User mission format (5_*_USER*.json)
                symbol = data.get('symbol', '')
                direction = data.get('direction', '')
                entry_price = data.get('entry_price', 0)
                stop_loss = data.get('stop_loss', 0)
                take_profit = data.get('take_profit', 0)
                tcs_score = data.get('tcs_score', 0)
                created_at_str = data.get('created_at', '')
                try:
                    from datetime import datetime
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).timestamp() if created_at_str else file_time
                except:
                    created_at = file_time
            
            # 📊 METADATA EXTRACTION: Extract additional metadata for logging
            citadel_shield = data.get('citadel_shield', {})
            citadel_score = citadel_shield.get('score', 0.0) if citadel_shield else 0.0
            
            ml_result = data.get('ml_result', {})
            ml_filter_passed = str(ml_result.get('passed', 'unknown')) if ml_result else 'unknown'
            
            if not all([symbol, direction, entry_price, stop_loss, take_profit]):
                logger.warning(f"Incomplete signal data for {signal_id}")
                return None
            
            return SignalTracker(
                signal_id=signal_id,
                symbol=symbol,
                direction=direction.upper(),
                entry_price=float(entry_price),
                stop_loss=float(stop_loss),
                take_profit=float(take_profit),
                tcs_score=float(tcs_score),
                created_at=float(created_at),
                start_time=time.time(),
                # 📊 METADATA TRACKING: Include extracted metadata
                citadel_score=float(citadel_score),
                ml_filter_passed=ml_filter_passed,
                source=source
            )
            
        except Exception as e:
            logger.error(f"Error creating signal tracker: {e}")
            return None
    
    def watch_signals_folder(self):
        """Watch for new signal files"""
        processed_files = set()
        
        while self.running:
            try:
                if not self.signals_folder.exists():
                    time.sleep(5)
                    continue
                
                # Check for new signal files (both formats)
                file_patterns = ["mission_*.json", "5_*_USER*.json"]
                
                for pattern in file_patterns:
                    for signal_file in self.signals_folder.glob(pattern):
                        if signal_file.name not in processed_files:
                            try:
                                with open(signal_file, 'r') as f:
                                    data = json.load(f)
                                
                                signal_id = data.get('signal_id') or data.get('mission_id')  # Support both formats
                                if signal_id and signal_id not in self.processed_signals:
                                    tracker = self._create_signal_tracker(data, signal_file.stat().st_mtime)
                                    if tracker:
                                        with self.lock:
                                            self.active_signals[signal_id] = tracker
                                        logger.info(f"Started tracking new signal: {signal_id}")
                                
                                processed_files.add(signal_file.name)
                                
                            except Exception as e:
                                logger.error(f"Error processing new signal file {signal_file}: {e}")
                
                time.sleep(2)  # Check for new files every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in signal folder watcher: {e}")
                time.sleep(5)
    
    def get_market_data(self) -> Dict[str, Dict]:
        """Fetch current market data from endpoint"""
        try:
            # Try the GET endpoint for retrieving all data first
            all_data_url = self.market_data_url.replace('/market-data', '/market-data/all')
            response = requests.get(all_data_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    # Format 1: Direct symbol-keyed dictionary
                    if all(isinstance(v, dict) and ('bid' in v or 'ask' in v) for v in data.values()):
                        market_data = {}
                        for symbol, prices in data.items():
                            market_data[symbol.upper()] = {
                                'bid': float(prices.get('bid', 0)),
                                'ask': float(prices.get('ask', 0)),
                                'timestamp': prices.get('timestamp', time.time())
                            }
                        self.market_data_cache = market_data
                        self.last_market_update = time.time()
                        return market_data
                    
                    # Format 2: Data wrapped in 'data' field
                    elif 'data' in data:
                        market_data = {}
                        for item in data.get('data', []):
                            symbol = item.get('symbol')
                            if symbol:
                                market_data[symbol.upper()] = {
                                    'bid': float(item.get('bid', 0)),
                                    'ask': float(item.get('ask', 0)),
                                    'timestamp': item.get('timestamp', time.time())
                                }
                        self.market_data_cache = market_data
                        self.last_market_update = time.time()
                        return market_data
                
                elif isinstance(data, list):
                    # Format 3: Array of price objects
                    market_data = {}
                    for item in data:
                        symbol = item.get('symbol')
                        if symbol:
                            market_data[symbol.upper()] = {
                                'bid': float(item.get('bid', 0)),
                                'ask': float(item.get('ask', 0)),
                                'timestamp': item.get('timestamp', time.time())
                            }
                    self.market_data_cache = market_data
                    self.last_market_update = time.time()
                    return market_data
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Market data fetch failed, retrying: {e}")
            # Try alternative endpoints (all GET endpoints)
            for alt_endpoint in ["/market-data/venom-feed", "/market-data/health"]:
                try:
                    base_url = self.market_data_url.replace('/market-data', '')
                    alt_url = base_url + alt_endpoint
                    response = requests.get(alt_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        # Process similar to above formats
                        if isinstance(data, dict) and 'data' in data:
                            market_data = {}
                            for item in data.get('data', []):
                                symbol = item.get('symbol')
                                if symbol:
                                    market_data[symbol.upper()] = {
                                        'bid': float(item.get('bid', 0)),
                                        'ask': float(item.get('ask', 0)),
                                        'timestamp': item.get('timestamp', time.time())
                                    }
                            self.market_data_cache = market_data
                            self.last_market_update = time.time()
                            return market_data
                except:
                    continue
        except Exception as e:
            logger.warning(f"Error fetching market data: {e}")
        
        # Return cached data if available
        return self.market_data_cache
    
    def get_auto_close_seconds(self) -> int:
        """Get auto close seconds from citadel_state.json or default"""
        try:
            if self.citadel_state_path.exists():
                with open(self.citadel_state_path, 'r') as f:
                    state = json.load(f)
                    global_config = state.get('global', {})
                    return int(global_config.get('auto_close_seconds', self.default_auto_close_seconds))
        except Exception as e:
            logger.warning(f"Error reading citadel state: {e}")
        
        return self.default_auto_close_seconds
    
    def check_signal_outcome(self, tracker: SignalTracker) -> Optional[Dict]:
        """Check if signal hit SL or TP, or should be auto-closed for time"""
        try:
            market_data = self.get_market_data()
            symbol_data = market_data.get(tracker.symbol.upper())
            
            if not symbol_data:
                logger.warning(f"Symbol {tracker.symbol} missing from market data response - skipping iteration")
                return None
            
            # Get current price based on direction
            if tracker.direction == 'BUY':
                current_price = symbol_data['bid']  # Exit on bid for BUY
            else:
                current_price = symbol_data['ask']  # Exit on ask for SELL
            
            runtime_seconds = time.time() - tracker.start_time
            
            # Check if SL hit
            sl_hit = False
            tp_hit = False
            
            if tracker.direction == 'BUY':
                sl_hit = current_price <= tracker.stop_loss
                tp_hit = current_price >= tracker.take_profit
            else:  # SELL
                sl_hit = current_price >= tracker.stop_loss  
                tp_hit = current_price <= tracker.take_profit
            
            # Check for time-based auto-close
            auto_close_seconds = self.get_auto_close_seconds()
            time_close = runtime_seconds >= auto_close_seconds
            
            # Determine outcome
            if sl_hit and tp_hit:
                # Both hit - use whichever is closer to entry
                sl_distance = abs(tracker.entry_price - tracker.stop_loss)
                tp_distance = abs(tracker.entry_price - tracker.take_profit)
                
                if sl_distance < tp_distance:
                    result = "LOSS"
                    exit_price = tracker.stop_loss
                    exit_type = "STOP_LOSS"
                else:
                    result = "WIN"
                    exit_price = tracker.take_profit
                    exit_type = "TAKE_PROFIT"
            elif sl_hit:
                result = "LOSS"
                exit_price = tracker.stop_loss
                exit_type = "STOP_LOSS"
            elif tp_hit:
                result = "WIN"
                exit_price = tracker.take_profit
                exit_type = "TAKE_PROFIT"
            elif time_close:
                # Check if position is in profit for time close
                if tracker.direction == 'BUY':
                    in_profit = current_price > tracker.entry_price
                else:  # SELL
                    in_profit = current_price < tracker.entry_price
                
                if in_profit:
                    result = "WIN"
                    exit_price = current_price
                    exit_type = "TIME_CLOSE"
                else:
                    # Position not in profit, don't auto-close yet
                    return None
            else:
                return None  # No exit condition met yet
            
            # Calculate pips result
            pip_size = 0.0001 if tracker.symbol not in ['USDJPY', 'USDCAD'] else 0.01
            
            if tracker.direction == 'BUY':
                pips_result = (exit_price - tracker.entry_price) / pip_size
            else:
                pips_result = (tracker.entry_price - exit_price) / pip_size
            
            return {
                'signal_id': tracker.signal_id,
                'symbol': tracker.symbol,
                'direction': tracker.direction,
                'result': result,
                'exit_type': exit_type,
                'entry_price': tracker.entry_price,
                'exit_price': exit_price,
                'stop_loss': tracker.stop_loss,
                'take_profit': tracker.take_profit,
                'tcs_score': tracker.tcs_score,
                'created_at': tracker.created_at,
                'runtime_seconds': int(runtime_seconds),
                'runtime_minutes': round(runtime_seconds / 60, 1),
                'pips_result': round(pips_result, 1),
                'completed_at': time.time(),
                'market_price': current_price,
                'auto_close_seconds': auto_close_seconds,
                # 📊 METADATA TRACKING: Include metadata in results
                'citadel_score': tracker.citadel_score,
                'ml_filter_passed': tracker.ml_filter_passed,
                'source': tracker.source
            }
            
        except Exception as e:
            logger.error(f"Error checking signal outcome for {tracker.signal_id}: {e}")
            return None
    
    def log_result(self, result: Dict):
        """Append result to truth log file with metadata tracking"""
        try:
            # ✅ VALIDATION: Check if truth_log.jsonl exists and is writable
            if not self.truth_log_path.exists():
                # Ensure parent directory exists
                self.truth_log_path.parent.mkdir(parents=True, exist_ok=True)
                # Create empty file
                self.truth_log_path.touch()
                logger.info(f"📝 Created truth log file: {self.truth_log_path}")
            
            # Test writeability
            if not os.access(self.truth_log_path, os.W_OK):
                logger.error(f"❌ Truth log file is not writable: {self.truth_log_path}")
                return
            
            # 📊 METADATA VALIDATION: Ensure required metadata fields are present
            required_metadata = ['tcs_score', 'citadel_score', 'ml_filter_passed', 'source']
            for field in required_metadata:
                if field not in result:
                    logger.warning(f"⚠️ Missing metadata field '{field}' in result, setting to 'unknown'")
                    if field in ['tcs_score', 'citadel_score']:
                        result[field] = 0.0
                    else:
                        result[field] = 'unknown'
            
            # 🛡️ SECURITY: Final source validation before logging
            if result.get('source') != 'venom_scalp_master':
                logger.error(f"❌ SECURITY VIOLATION: Attempt to log result with invalid source: {result.get('source')} - {result.get('signal_id')}")
                return
            
            # Append result as JSON line with complete metadata
            with open(self.truth_log_path, 'a') as f:
                f.write(json.dumps(result, sort_keys=True) + '\n')
            
            exit_type_display = {
                'STOP_LOSS': '🔴 SL',
                'TAKE_PROFIT': '🎯 TP', 
                'TIME_CLOSE': '⏰ TIME',
                'TIMEOUT': '⏱️ TIMEOUT'
            }.get(result.get('exit_type', 'UNKNOWN'), '❓')
            
            # Enhanced logging with metadata
            metadata_info = f"TCS:{result.get('tcs_score', 0):.1f} CITADEL:{result.get('citadel_score', 0):.1f} ML:{result.get('ml_filter_passed', 'unknown')}"
            logger.info(f"✅ {result['result']} {exit_type_display}: {result['signal_id']} - {result['symbol']} {result['direction']} - {result['runtime_minutes']}min - {result['pips_result']} pips [{metadata_info}]")
            
        except Exception as e:
            logger.error(f"❌ Error logging result to truth log: {e}")
    
    def track_active_signals(self):
        """Main tracking loop for active signals"""
        while self.running:
            try:
                completed_signals = []
                
                with self.lock:
                    active_list = list(self.active_signals.items())
                
                for signal_id, tracker in active_list:
                    # Check for absolute timeout (24 hours max tracking)
                    runtime_seconds = time.time() - tracker.start_time
                    if runtime_seconds > 86400:
                        # Log timeout result
                        timeout_result = {
                            'signal_id': tracker.signal_id,
                            'symbol': tracker.symbol,
                            'direction': tracker.direction,
                            'result': 'TIMEOUT',
                            'exit_type': 'TIMEOUT',
                            'entry_price': tracker.entry_price,
                            'exit_price': tracker.entry_price,  # No movement assumed
                            'stop_loss': tracker.stop_loss,
                            'take_profit': tracker.take_profit,
                            'tcs_score': tracker.tcs_score,
                            'created_at': tracker.created_at,
                            'runtime_seconds': int(runtime_seconds),
                            'runtime_minutes': round(runtime_seconds / 60, 1),
                            'pips_result': 0.0,
                            'completed_at': time.time(),
                            'market_price': tracker.entry_price,
                            'auto_close_seconds': self.get_auto_close_seconds(),
                            # 📊 METADATA TRACKING: Include metadata in timeout results
                            'citadel_score': tracker.citadel_score,
                            'ml_filter_passed': tracker.ml_filter_passed,
                            'source': tracker.source
                        }
                        self.log_result(timeout_result)
                        completed_signals.append(signal_id)
                        logger.info(f"Signal {signal_id} timed out after 24 hours")
                        continue
                    
                    # Check if signal completed
                    result = self.check_signal_outcome(tracker)
                    if result:
                        self.log_result(result)
                        completed_signals.append(signal_id)
                
                # Remove completed signals
                with self.lock:
                    for signal_id in completed_signals:
                        if signal_id in self.active_signals:
                            del self.active_signals[signal_id]
                        self.processed_signals.add(signal_id)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in signal tracking loop: {e}")
                time.sleep(5)
    
    def get_status(self) -> Dict:
        """Get current tracker status"""
        with self.lock:
            return {
                'active_signals': len(self.active_signals),
                'processed_signals': len(self.processed_signals),
                'market_data_age': time.time() - self.last_market_update,
                'running': self.running
            }
    
    def start(self):
        """Start the truth tracker"""
        logger.info("Starting Truth Tracker...")
        self.running = True
        
        # Load existing signals
        self.load_existing_signals()
        
        # Start background threads
        threading.Thread(target=self.watch_signals_folder, daemon=True).start()
        threading.Thread(target=self.track_active_signals, daemon=True).start()
        
        logger.info(f"Truth Tracker started - monitoring {len(self.active_signals)} signals")
    
    def stop(self):
        """Stop the truth tracker"""
        logger.info("Stopping Truth Tracker...")
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("Truth Tracker stopped")
    
    def inspect_latest_entries(self, count: int = 3):
        """
        📊 CLI INSPECTION: Display latest truth log entries in clean table format
        """
        try:
            if not self.truth_log_path.exists():
                print("❌ Truth log file does not exist yet")
                return
            
            if not os.access(self.truth_log_path, os.R_OK):
                print(f"❌ Truth log file is not readable: {self.truth_log_path}")
                return
            
            # Read the last N lines
            with open(self.truth_log_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                print("📝 Truth log is empty - no entries to display")
                return
            
            # Get the most recent entries
            recent_lines = lines[-count:] if len(lines) >= count else lines
            entries = []
            
            for line in recent_lines:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
            
            if not entries:
                print("❌ No valid JSON entries found in truth log")
                return
            
            # Print clean table format
            print(f"\n📊 TRUTH LOG INSPECTION - Latest {len(entries)} Entries")
            print("=" * 120)
            
            # Header
            header = f"{'Signal ID':<30} {'Symbol':<8} {'Dir':<4} {'Result':<8} {'TCS':<6} {'CITADEL':<8} {'ML Filter':<10} {'Pips':<8} {'Runtime':<10} {'Source':<18}"
            print(header)
            print("-" * 120)
            
            # Data rows
            for entry in entries:
                signal_id = entry.get('signal_id', 'unknown')[:29]  # Truncate if too long
                symbol = entry.get('symbol', 'N/A')
                direction = entry.get('direction', 'N/A')
                result = entry.get('result', 'N/A')
                tcs_score = entry.get('tcs_score', 'unknown')
                citadel_score = entry.get('citadel_score', 'unknown')
                ml_filter = entry.get('ml_filter_passed', 'unknown')
                pips_result = entry.get('pips_result', 'N/A')
                runtime_minutes = entry.get('runtime_minutes', 'N/A')
                source = entry.get('source', 'unknown')
                
                # Format numbers
                tcs_str = f"{tcs_score:.1f}" if isinstance(tcs_score, (int, float)) else str(tcs_score)
                citadel_str = f"{citadel_score:.1f}" if isinstance(citadel_score, (int, float)) else str(citadel_score)
                pips_str = f"{pips_result:+.1f}" if isinstance(pips_result, (int, float)) else str(pips_result)
                runtime_str = f"{runtime_minutes:.1f}m" if isinstance(runtime_minutes, (int, float)) else str(runtime_minutes)
                
                # Color coding for results
                result_colored = result
                if result == 'WIN':
                    result_colored = f"✅ {result}"
                elif result == 'LOSS':
                    result_colored = f"❌ {result}"
                elif result == 'TIMEOUT':
                    result_colored = f"⏱️ {result}"
                
                row = f"{signal_id:<30} {symbol:<8} {direction:<4} {result_colored:<8} {tcs_str:<6} {citadel_str:<8} {ml_filter:<10} {pips_str:<8} {runtime_str:<10} {source:<18}"
                print(row)
            
            print("=" * 120)
            
            # Summary stats
            wins = sum(1 for e in entries if e.get('result') == 'WIN')
            losses = sum(1 for e in entries if e.get('result') == 'LOSS')
            total_pips = sum(e.get('pips_result', 0) for e in entries if isinstance(e.get('pips_result'), (int, float)))
            
            win_rate = (wins / len(entries) * 100) if entries else 0
            
            print(f"📈 SUMMARY: {wins} wins, {losses} losses, {win_rate:.1f}% win rate, {total_pips:+.1f} total pips")
            print(f"🔍 Metadata Coverage: TCS, CITADEL, ML Filter tracking active")
            print(f"📝 Log Location: {self.truth_log_path}")
            
        except Exception as e:
            print(f"❌ Error inspecting truth log: {e}")
            logger.error(f"Truth log inspection error: {e}")

def main():
    """Main entry point with CLI argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Truth Tracker - Signal outcome monitoring with metadata tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 truth_tracker.py                    # Start tracking daemon
  python3 truth_tracker.py --inspect-latest   # Show latest 3 entries
  python3 truth_tracker.py --inspect-latest 5 # Show latest 5 entries
        """
    )
    
    parser.add_argument(
        '--inspect-latest', 
        type=int, 
        nargs='?', 
        const=3, 
        metavar='N',
        help='Display the most recent N entries from truth log in table format (default: 3)'
    )
    
    args = parser.parse_args()
    tracker = TruthTracker()
    
    # Handle CLI inspection mode
    if args.inspect_latest is not None:
        print("🔍 TRUTH TRACKER - CLI INSPECTION MODE")
        tracker.inspect_latest_entries(args.inspect_latest)
        return
    
    # Normal daemon mode
    try:
        tracker.start()
        
        # Keep running and show status
        while True:
            time.sleep(30)
            status = tracker.get_status()
            logger.info(f"Status: {status['active_signals']} active, {status['processed_signals']} completed")
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        tracker.stop()

if __name__ == "__main__":
    main()