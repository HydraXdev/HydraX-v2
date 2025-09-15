#!/usr/bin/env python3
"""
Comprehensive Signal Tracker for Elite Guard
Tracks EVERY pattern detected, not just fired signals
Logs all data to /root/HydraX-v2/logs/comprehensive_tracking.jsonl using unified logging
"""

import zmq
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
import os
import sys
import threading
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SignalTrack:
    """Complete signal tracking data structure"""
    signal_id: str
    pattern_type: str
    confidence_score: float
    pair: str
    direction: str
    entry_price: float
    sl_price: float
    tp_price: float
    sl_pips: float
    tp_pips: float
    session: str
    spread: Optional[float]
    time_utc: str
    timestamp: float
    fired: bool = False
    would_fire: bool = False
    outcome_30min: Optional[str] = None
    outcome_60min: Optional[str] = None
    pips_moved_30min: Optional[float] = None
    pips_moved_60min: Optional[float] = None
    max_favorable_30min: Optional[float] = None
    max_adverse_30min: Optional[float] = None
    max_favorable_60min: Optional[float] = None
    max_adverse_60min: Optional[float] = None
    citadel_score: float = 0.0
    risk_reward: float = 0.0
    signal_type: Optional[str] = None
    estimated_time_to_tp: Optional[float] = None

class ComprehensiveSignalTracker:
    def __init__(self, confidence_threshold=70):
        self.context = zmq.Context()
        self.subscriber = None
        self.market_subscriber = None  # For price monitoring
        self.log_file = "/root/HydraX-v2/logs/comprehensive_tracking.jsonl"
        self.running = False
        self.tracked_signals = {}  # Store signals for outcome monitoring
        self.current_prices = {}  # Store latest prices for each pair
        
        logger.info(f"🎯 Comprehensive Signal Tracker initialized - Threshold: {confidence_threshold}%")
        
        # Load recent signals for outcome monitoring
        self.load_recent_signals()
        
        # Tracking stats
        self.confidence_threshold = confidence_threshold
        self.stats = {
            'total_signals': 0,
            'would_fire': 0,
            'did_fire': 0,
            'patterns': {},
            'sessions': {},
            'pairs': {}
        }
        
    def load_recent_signals(self):
        """Load signals from last 2 hours for outcome monitoring"""
        if not os.path.exists(self.log_file):
            return
            
        try:
            two_hours_ago = time.time() - 7200
            with open(self.log_file, 'r') as f:
                for line in f:
                    record = json.loads(line)
                    # Only load recent signals without outcomes
                    if record.get('timestamp', 0) > two_hours_ago:
                        if not record.get('outcome_60min'):
                            self.tracked_signals[record['signal_id']] = record
            
            logger.info(f"📚 Loaded {len(self.tracked_signals)} recent signals for outcome monitoring")
        except Exception as e:
            logger.error(f"Error loading recent signals: {e}")
    
    def get_trading_session(self, timestamp_utc):
        """Determine trading session from UTC timestamp"""
        dt = datetime.fromtimestamp(timestamp_utc, tz=timezone.utc)
        hour = dt.hour
        
        if 22 <= hour or hour < 7:
            return "ASIAN"
        elif 7 <= hour < 12:
            return "LONDON"
        elif 12 <= hour < 17:
            return "NEWYORK"
        elif 17 <= hour < 22:
            return "SYDNEY"
        else:
            return "OVERLAP"
    
    def calculate_risk_reward(self, sl_pips, tp_pips):
        """Calculate risk/reward ratio"""
        if sl_pips and sl_pips != 0:
            return round(tp_pips / sl_pips, 2)
        return 0.0
    
    def extract_signal_details(self, signal_data):
        """Extract and validate signal details"""
        try:
            # Get basic info
            signal_id = signal_data.get('signal_id', '')
            pattern_type = signal_data.get('pattern', 'UNKNOWN')
            confidence = float(signal_data.get('confidence', 0))
            
            # Get price data - check both field names for compatibility
            entry = float(signal_data.get('entry_price', 0) or signal_data.get('entry', 0))
            sl = float(signal_data.get('stop_loss', 0) or signal_data.get('sl', 0))
            tp = float(signal_data.get('take_profit', 0) or signal_data.get('tp', 0))
            
            # Calculate pips - use provided values or calculate
            symbol = signal_data.get('symbol', signal_data.get('pair', 'UNKNOWN'))
            
            # First try to use pre-calculated pips from signal
            sl_pips = float(signal_data.get('stop_pips', 0) or signal_data.get('sl_pips', 0))
            tp_pips = float(signal_data.get('target_pips', 0) or signal_data.get('tp_pips', 0))
            
            # If not provided, calculate from prices
            if (sl_pips == 0 or tp_pips == 0) and entry > 0 and sl > 0 and tp > 0:
                pip_multiplier = 100 if 'JPY' in symbol else (1 if symbol == 'XAUUSD' else 10000)
                if sl_pips == 0:
                    sl_pips = abs(entry - sl) * pip_multiplier
                if tp_pips == 0:
                    tp_pips = abs(tp - entry) * pip_multiplier
            
            # Determine if would fire
            would_fire = confidence >= self.confidence_threshold
            
            # Get current timestamp
            timestamp = time.time()
            time_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
            
            # Create tracking object
            track = SignalTrack(
                signal_id=signal_id,
                pattern_type=pattern_type,
                confidence_score=confidence,
                pair=symbol,
                direction=signal_data.get('direction', 'UNKNOWN'),
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                sl_pips=sl_pips,
                tp_pips=tp_pips,
                session=self.get_trading_session(timestamp),
                spread=signal_data.get('spread'),
                time_utc=time_utc,
                timestamp=timestamp,
                fired=signal_data.get('fired', False),
                would_fire=would_fire,
                citadel_score=float(signal_data.get('citadel_score', 0)),
                risk_reward=self.calculate_risk_reward(sl_pips, tp_pips),
                signal_type=signal_data.get('signal_type'),
                estimated_time_to_tp=signal_data.get('estimated_time_to_tp')
            )
            
            return track
            
        except Exception as e:
            logger.error(f"Error extracting signal details: {e}")
            return None
    
    def log_signal(self, track: SignalTrack):
        """Log signal using unified logging function"""
        try:
            # Convert dataclass to dict and use unified logging
            trade_data = asdict(track)
            
            # Map fields to unified format
            mapped_data = {
                'signal_id': trade_data.get('signal_id'),
                'pattern_type': trade_data.get('pattern_type'),
                'confidence_score': trade_data.get('confidence_score'),
                'pair': trade_data.get('pair'),
                'direction': trade_data.get('direction'),
                'entry': trade_data.get('entry_price'),
                'sl': trade_data.get('sl_price'),
                'tp': trade_data.get('tp_price'),
                'sl_pips': trade_data.get('sl_pips'),
                'tp_pips': trade_data.get('tp_pips'),
                'session': trade_data.get('session'),
                'spread': trade_data.get('spread'),
                'timestamp': trade_data.get('timestamp'),
                'executed': trade_data.get('fired'),
                'citadel_score': trade_data.get('citadel_score'),
                'outcome': trade_data.get('outcome_60min') or trade_data.get('outcome_30min'),
                'pips': trade_data.get('pips_moved_60min') or trade_data.get('pips_moved_30min'),
                'max_favorable': trade_data.get('max_favorable_60min') or trade_data.get('max_favorable_30min'),
                'max_adverse': trade_data.get('max_adverse_60min') or trade_data.get('max_adverse_30min'),
                'risk_reward': trade_data.get('risk_reward'),
                'signal_type': trade_data.get('signal_type'),
                'estimated_time_to_tp': trade_data.get('estimated_time_to_tp')
            }
            
            # Use unified logging function
            log_trade(mapped_data, self.log_file)
            
            status = "🔥 WOULD_FIRE" if track.would_fire else "⚪ MONITOR"
            logger.info(f"{status} | {track.signal_id} | {track.pattern_type} | {track.confidence_score}% | {track.pair}")
            
            # Update stats
            self.update_stats(track)
            
            # Add to tracked signals for outcome monitoring
            self.tracked_signals[track.signal_id] = asdict(track)
            
        except Exception as e:
            logger.error(f"Error logging signal: {e}")
    
    def update_stats(self, track: SignalTrack):
        """Update running statistics"""
        self.stats['total_signals'] += 1
        
        if track.would_fire:
            self.stats['would_fire'] += 1
        if track.fired:
            self.stats['did_fire'] += 1
        
        # Pattern stats
        if track.pattern_type not in self.stats['patterns']:
            self.stats['patterns'][track.pattern_type] = {'total': 0, 'would_fire': 0}
        self.stats['patterns'][track.pattern_type]['total'] += 1
        if track.would_fire:
            self.stats['patterns'][track.pattern_type]['would_fire'] += 1
        
        # Session stats
        if track.session not in self.stats['sessions']:
            self.stats['sessions'][track.session] = {'total': 0, 'would_fire': 0}
        self.stats['sessions'][track.session]['total'] += 1
        if track.would_fire:
            self.stats['sessions'][track.session]['would_fire'] += 1
        
        # Pair stats
        if track.pair not in self.stats['pairs']:
            self.stats['pairs'][track.pair] = {'total': 0, 'would_fire': 0}
        self.stats['pairs'][track.pair]['total'] += 1
        if track.would_fire:
            self.stats['pairs'][track.pair]['would_fire'] += 1
    
    def process_market_data(self, tick_data):
        """Process market tick to update current prices"""
        try:
            symbol = tick_data.get('symbol')
            bid = float(tick_data.get('bid', 0))
            ask = float(tick_data.get('ask', 0))
            
            if symbol and bid > 0:
                self.current_prices[symbol] = {
                    'bid': bid,
                    'ask': ask,
                    'mid': (bid + ask) / 2,
                    'timestamp': time.time()
                }
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    def check_signal_outcomes(self):
        """Check outcomes for tracked signals"""
        current_time = time.time()
        signals_to_update = []
        
        for signal_id, signal in list(self.tracked_signals.items()):
            signal_time = signal.get('timestamp', 0)
            time_elapsed = current_time - signal_time
            
            # Skip if already has 60min outcome
            if signal.get('outcome_60min'):
                del self.tracked_signals[signal_id]
                continue
            
            pair = signal.get('pair')
            if pair not in self.current_prices:
                continue
            
            current_price = self.current_prices[pair]['mid']
            entry_price = float(signal.get('entry_price', 0))
            tp_price = float(signal.get('tp_price', 0))
            sl_price = float(signal.get('sl_price', 0))
            direction = signal.get('direction', '').upper()
            
            # Calculate pips moved
            pip_multiplier = 100 if 'JPY' in pair else 10000
            if direction == 'BUY':
                pips_moved = (current_price - entry_price) * pip_multiplier
                hit_tp = current_price >= tp_price
                hit_sl = current_price <= sl_price
            else:
                pips_moved = (entry_price - current_price) * pip_multiplier
                hit_tp = current_price <= tp_price
                hit_sl = current_price >= sl_price
            
            # Update 30min outcome
            if time_elapsed >= 1800 and not signal.get('outcome_30min'):
                signal['outcome_30min'] = 'WIN' if hit_tp else ('LOSS' if hit_sl else 'PENDING')
                signal['pips_moved_30min'] = pips_moved
                signal['max_favorable_30min'] = max(0, pips_moved)
                signal['max_adverse_30min'] = min(0, pips_moved)
                signals_to_update.append(signal)
            
            # Update 60min outcome
            if time_elapsed >= 3600 and not signal.get('outcome_60min'):
                signal['outcome_60min'] = 'WIN' if hit_tp else ('LOSS' if hit_sl else 'PENDING')
                signal['pips_moved_60min'] = pips_moved
                signal['max_favorable_60min'] = max(0, pips_moved)
                signal['max_adverse_60min'] = min(0, pips_moved)
                signals_to_update.append(signal)
            
            # Keep tracking until actual TP/SL hit or 4 hours max
            if hit_tp or hit_sl:
                signal['final_outcome'] = 'WIN' if hit_tp else 'LOSS'
                signal['time_to_outcome'] = time_elapsed / 60  # minutes
                signal['final_pips'] = pips_moved
                signals_to_update.append(signal)
                del self.tracked_signals[signal_id]
            elif time_elapsed >= 14400:  # 4 hours max
                signal['final_outcome'] = 'TIMEOUT'
                signal['time_to_outcome'] = 240  # minutes
                signal['final_pips'] = pips_moved
                signals_to_update.append(signal)
                del self.tracked_signals[signal_id]
        
        # Update records with outcomes
        if signals_to_update:
            self.update_signal_outcomes(signals_to_update)
    
    def update_signal_outcomes(self, signals_to_update):
        """Update signal outcomes in the log file"""
        try:
            # Read all records
            records = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    for line in f:
                        records.append(json.loads(line))
            
            # Update matching records
            updated = False
            for signal in signals_to_update:
                for i, record in enumerate(records):
                    if record.get('signal_id') == signal.get('signal_id'):
                        # Update outcomes
                        for key in ['outcome_30min', 'outcome_60min', 'pips_moved_30min', 
                                   'pips_moved_60min', 'max_favorable_30min', 'max_adverse_30min',
                                   'max_favorable_60min', 'max_adverse_60min']:
                            if key in signal:
                                record[key] = signal[key]
                        records[i] = record
                        updated = True
                        
                        outcome = signal.get('outcome_60min') or signal.get('outcome_30min')
                        logger.info(f"📊 Updated outcome for {signal['signal_id']}: {outcome}")
            
            # Write back all records if updated using unified logging
            if updated:
                # Clear the file first
                open(self.log_file, 'w').close()
                # Re-write all records using unified logging
                for record in records:
                    log_trade(record, self.log_file)
                        
        except Exception as e:
            logger.error(f"Error updating signal outcomes: {e}")
    
    def connect(self):
        """Connect to ZMQ sockets"""
        try:
            # Subscribe to Elite Guard signals
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://localhost:5557")
            self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "ELITE_")
            
            # Subscribe to market data for outcome tracking
            self.market_subscriber = self.context.socket(zmq.SUB)
            self.market_subscriber.connect("tcp://localhost:5560")
            self.market_subscriber.setsockopt_string(zmq.SUBSCRIBE, "TICK")
            
            logger.info("✅ Connected to ZMQ signal and market data streams")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def run(self):
        """Main tracking loop"""
        if not self.connect():
            return
        
        self.running = True
        logger.info("🚀 Comprehensive Signal Tracker running...")
        
        # Start outcome monitoring thread
        outcome_thread = threading.Thread(target=self.outcome_monitor_loop)
        outcome_thread.daemon = True
        outcome_thread.start()
        
        last_stats_print = time.time()
        
        try:
            while self.running:
                # Use poller to check multiple sockets
                poller = zmq.Poller()
                poller.register(self.subscriber, zmq.POLLIN)
                poller.register(self.market_subscriber, zmq.POLLIN)
                
                socks = dict(poller.poll(1000))
                
                # Process Elite Guard signals
                if self.subscriber in socks:
                    message = self.subscriber.recv_string()
                    
                    if message.startswith("ELITE_"):
                        parts = message.split(' ', 1)
                        if len(parts) > 1:
                            try:
                                signal_data = json.loads(parts[1])
                                track = self.extract_signal_details(signal_data)
                                if track:
                                    self.log_signal(track)
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error: {e}")
                
                # Process market data
                if self.market_subscriber in socks:
                    message = self.market_subscriber.recv_string()
                    
                    if message.startswith("TICK"):
                        parts = message.split(' ', 1)
                        if len(parts) > 1:
                            try:
                                tick_data = json.loads(parts[1])
                                self.process_market_data(tick_data)
                            except json.JSONDecodeError:
                                pass
                
                # Print stats every 5 minutes
                if time.time() - last_stats_print > 300:
                    self.print_stats()
                    last_stats_print = time.time()
                    
        except KeyboardInterrupt:
            logger.info("⚠️ Tracker interrupted by user")
        except Exception as e:
            logger.error(f"Tracker error: {e}")
        finally:
            self.cleanup()
    
    def outcome_monitor_loop(self):
        """Separate thread for monitoring signal outcomes"""
        while self.running:
            try:
                self.check_signal_outcomes()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Outcome monitor error: {e}")
                time.sleep(10)
    
    def print_stats(self):
        """Print current tracking statistics"""
        logger.info("=" * 60)
        logger.info("📊 COMPREHENSIVE TRACKING STATS")
        logger.info(f"Total Signals: {self.stats['total_signals']}")
        logger.info(f"Would Fire (≥{self.confidence_threshold}%): {self.stats['would_fire']}")
        logger.info(f"Actually Fired: {self.stats['did_fire']}")
        
        if self.stats['patterns']:
            logger.info("\n🎯 PATTERNS:")
            for pattern, data in self.stats['patterns'].items():
                fire_rate = (data['would_fire']/data['total']*100) if data['total'] > 0 else 0
                logger.info(f"  {pattern}: {data['total']} signals, {fire_rate:.1f}% would fire")
        
        if self.stats['sessions']:
            logger.info("\n⏰ SESSIONS:")
            for session, data in self.stats['sessions'].items():
                fire_rate = (data['would_fire']/data['total']*100) if data['total'] > 0 else 0
                logger.info(f"  {session}: {data['total']} signals, {fire_rate:.1f}% would fire")
        
        logger.info("=" * 60)
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.subscriber:
            self.subscriber.close()
        if self.market_subscriber:
            self.market_subscriber.close()
        self.context.term()
        logger.info("✅ Tracker cleaned up")

def main():
    """Main entry point"""
    tracker = ComprehensiveSignalTracker(confidence_threshold=70)
    
    try:
        tracker.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()