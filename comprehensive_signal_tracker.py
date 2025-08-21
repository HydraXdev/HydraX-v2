#!/usr/bin/env python3
"""
Comprehensive Signal Tracker for Elite Guard
Tracks EVERY pattern detected, not just fired signals
Logs all data to comprehensive_tracking.jsonl for analysis
"""

import zmq
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
import os
import threading
from dataclasses import dataclass, asdict

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
    estimated_time_to_tp: Optional[int] = None

class ComprehensiveSignalTracker:
    """Tracks every Elite Guard signal for comprehensive analysis"""
    
    def __init__(self, confidence_threshold: float = 78.0):
        self.confidence_threshold = confidence_threshold
        self.context = zmq.Context()
        self.subscriber = None
        self.log_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
        self.running = False
        
        # Initialize log file if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass
        
        logger.info(f"🎯 Comprehensive Signal Tracker initialized - Threshold: {confidence_threshold}%")
    
    def connect_to_elite_guard(self):
        """Connect to Elite Guard ZMQ signal stream"""
        try:
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://localhost:5557")
            self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "ELITE_GUARD_SIGNAL")
            self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            logger.info("✅ Connected to Elite Guard on port 5557")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Elite Guard: {e}")
            return False
    
    def calculate_pips(self, price_diff: float, pair: str) -> float:
        """Calculate pips based on currency pair"""
        if pair in ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY', 'CADJPY', 'CHFJPY']:
            return abs(price_diff * 100)  # JPY pairs
        elif 'XAU' in pair or 'GOLD' in pair:
            return abs(price_diff * 10)   # Gold
        else:
            return abs(price_diff * 10000)  # Major pairs
    
    def determine_session(self) -> str:
        """Determine current trading session"""
        utc_hour = datetime.now(timezone.utc).hour
        
        if 0 <= utc_hour < 7:
            return "ASIAN"
        elif 7 <= utc_hour < 12:
            return "LONDON"
        elif 12 <= utc_hour < 17:
            return "OVERLAP"
        elif 17 <= utc_hour < 22:
            return "NY"
        else:
            return "LATE_NY"
    
    def process_signal(self, signal_data: Dict) -> SignalTrack:
        """Process Elite Guard signal into tracking format"""
        try:
            # Extract core signal data
            signal_id = signal_data.get('signal_id', '')
            pair = signal_data.get('symbol', signal_data.get('pair', ''))
            confidence = float(signal_data.get('confidence', 0))
            
            # Calculate pips
            entry = float(signal_data.get('entry_price', signal_data.get('entry', 0)))
            sl = float(signal_data.get('sl', signal_data.get('stop_loss', 0)))
            tp = float(signal_data.get('tp', signal_data.get('take_profit', 0)))
            
            sl_pips = self.calculate_pips(abs(entry - sl), pair)
            tp_pips = self.calculate_pips(abs(tp - entry), pair)
            
            # Determine if this would fire based on confidence
            would_fire = confidence >= self.confidence_threshold
            
            # Create tracking record
            track = SignalTrack(
                signal_id=signal_id,
                pattern_type=signal_data.get('pattern_type', 'UNKNOWN'),
                confidence_score=confidence,
                pair=pair,
                direction=signal_data.get('direction', ''),
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                sl_pips=sl_pips,
                tp_pips=tp_pips,
                session=signal_data.get('session', self.determine_session()),
                spread=signal_data.get('spread'),
                time_utc=datetime.now(timezone.utc).isoformat(),
                timestamp=time.time(),
                would_fire=would_fire,
                citadel_score=float(signal_data.get('citadel_score', 0)),
                risk_reward=float(signal_data.get('risk_reward', 0)),
                signal_type=signal_data.get('signal_type'),
                estimated_time_to_tp=signal_data.get('estimated_time_to_tp')
            )
            
            return track
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            logger.error(f"Signal data: {signal_data}")
            return None
    
    def log_signal(self, track: SignalTrack):
        """Log signal to comprehensive tracking file"""
        try:
            with open(self.log_file, 'a') as f:
                json.dump(asdict(track), f)
                f.write('\n')
            
            status = "🔥 WOULD_FIRE" if track.would_fire else "⚪ MONITOR"
            logger.info(f"📊 TRACKED: {track.pair} {track.direction} @ {track.confidence_score:.1f}% "
                       f"| {track.pattern_type} | {status}")
                       
        except Exception as e:
            logger.error(f"❌ Failed to log signal: {e}")
    
    def listen_for_signals(self):
        """Main loop to listen for Elite Guard signals"""
        logger.info("🎯 Starting comprehensive signal tracking...")
        self.running = True
        
        while self.running:
            try:
                # Receive signal with timeout
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                
                if message.startswith("ELITE_GUARD_SIGNAL "):
                    signal_json = message[19:]  # Remove prefix
                    signal_data = json.loads(signal_json)
                    
                    # Process and log signal
                    track = self.process_signal(signal_data)
                    if track:
                        self.log_signal(track)
                
            except zmq.Again:
                # No message received, continue
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"❌ Error in signal listening loop: {e}")
                time.sleep(1)
    
    def start_tracking(self):
        """Start the tracking service"""
        if not self.connect_to_elite_guard():
            logger.error("❌ Cannot start tracking - failed to connect to Elite Guard")
            return False
        
        # Start tracking in separate thread
        tracking_thread = threading.Thread(target=self.listen_for_signals, daemon=True)
        tracking_thread.start()
        
        logger.info("✅ Comprehensive Signal Tracker started")
        return True
    
    def stop_tracking(self):
        """Stop the tracking service"""
        self.running = False
        if self.subscriber:
            self.subscriber.close()
        logger.info("🛑 Comprehensive Signal Tracker stopped")
    
    def get_tracking_stats(self) -> Dict:
        """Get current tracking statistics"""
        try:
            total_signals = 0
            would_fire_count = 0
            pattern_counts = {}
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        total_signals += 1
                        
                        if data.get('would_fire', False):
                            would_fire_count += 1
                        
                        pattern = data.get('pattern_type', 'UNKNOWN')
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            return {
                'total_signals': total_signals,
                'would_fire_count': would_fire_count,
                'would_fire_rate': round(would_fire_count / max(total_signals, 1) * 100, 1),
                'pattern_counts': pattern_counts,
                'threshold': self.confidence_threshold
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

def main():
    """Main function for standalone operation"""
    tracker = ComprehensiveSignalTracker(confidence_threshold=78.0)
    
    try:
        if tracker.start_tracking():
            logger.info("🎯 Comprehensive Signal Tracker running...")
            logger.info("Press Ctrl+C to stop")
            
            # Keep running and show stats every 60 seconds
            while True:
                time.sleep(60)
                stats = tracker.get_tracking_stats()
                if stats:
                    logger.info(f"📊 STATS: {stats['total_signals']} total, "
                               f"{stats['would_fire_count']} would fire "
                               f"({stats['would_fire_rate']}%)")
                
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    finally:
        tracker.stop_tracking()

if __name__ == "__main__":
    main()