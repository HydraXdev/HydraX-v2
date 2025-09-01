#!/usr/bin/env python3
"""
BITTEN Convergence Tracker - Multi-Pattern Alignment Detector
Detects when 2+ patterns align on same pair within 60 seconds.
Boosts confidence +10% per additional pattern for high-conviction trades.
"""

import json
import time
import sqlite3
import zmq
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ConvergenceEvent:
    """Represents a multi-pattern convergence event"""
    convergence_id: str
    symbol: str
    direction: str
    patterns: List[str]
    signal_ids: List[str]
    timestamps: List[int]
    confidence_scores: List[float]
    boosted_confidence: float
    convergence_window: int  # seconds
    created_at: int

class ConvergenceTracker:
    """
    Tracks pattern convergence and boosts confidence for aligned signals.
    High-conviction trades often occur when multiple patterns agree.
    """
    
    def __init__(self, 
                 db_path: str = "/root/HydraX-v2/bitten.db",
                 log_file: str = "/root/HydraX-v2/convergence_signals.jsonl"):
        self.db_path = db_path
        self.log_file = log_file
        
        # Convergence settings
        self.convergence_window = 60  # seconds for pattern alignment
        self.confidence_boost_per_pattern = 0.10  # 10% boost per additional pattern
        self.min_patterns_for_convergence = 2
        self.max_convergence_window = 120  # Maximum window to consider
        
        # Pattern tracking
        self.recent_signals = defaultdict(lambda: deque(maxlen=50))  # Per symbol
        self.active_convergences = {}  # Track ongoing convergences
        
        # ZMQ setup for real-time signal monitoring
        self.context = zmq.Context()
        self.signal_subscriber = None
        self.running = False
        
        # Thread for real-time monitoring
        self.monitor_thread = None
        
        logger.info("ConvergenceTracker initialized with {}s window, {}% boost per pattern".format(
            self.convergence_window, self.confidence_boost_per_pattern * 100))
    
    def start_real_time_monitoring(self, signal_port: int = 5557):
        """Start real-time signal monitoring via ZMQ"""
        try:
            self.signal_subscriber = self.context.socket(zmq.SUB)
            self.signal_subscriber.connect(f"tcp://localhost:{signal_port}")
            self.signal_subscriber.setsockopt_string(zmq.SUBSCRIBE, "ELITE_GUARD_SIGNAL")
            self.signal_subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_signals, daemon=True)
            self.monitor_thread.start()
            
            logger.info(f"Started real-time convergence monitoring on port {signal_port}")
            
        except Exception as e:
            logger.error(f"Error starting real-time monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.running = False
        if self.signal_subscriber:
            self.signal_subscriber.close()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped convergence monitoring")
    
    def _monitor_signals(self):
        """Monitor incoming signals for convergence detection"""
        while self.running:
            try:
                # Receive signal
                message = self.signal_subscriber.recv_string(zmq.DONTWAIT)
                if message.startswith("ELITE_GUARD_SIGNAL "):
                    signal_json = message[19:]  # Remove prefix
                    signal_data = json.loads(signal_json)
                    
                    # Process signal for convergence
                    self._process_incoming_signal(signal_data)
                    
            except zmq.Again:
                # No message available, continue
                continue
            except Exception as e:
                logger.error(f"Error processing signal in convergence monitor: {e}")
                time.sleep(1)
    
    def _process_incoming_signal(self, signal_data: Dict):
        """Process incoming signal for convergence detection"""
        try:
            symbol = signal_data.get('symbol')
            direction = signal_data.get('direction')
            pattern_type = signal_data.get('pattern_type')
            signal_id = signal_data.get('signal_id')
            confidence = signal_data.get('confidence', 0)
            timestamp = int(time.time())
            
            if not all([symbol, direction, pattern_type, signal_id]):
                return
            
            # Add to recent signals for this symbol
            signal_entry = {
                'signal_id': signal_id,
                'pattern_type': pattern_type,
                'direction': direction,
                'confidence': confidence,
                'timestamp': timestamp
            }
            
            self.recent_signals[symbol].append(signal_entry)
            
            # Check for convergence
            convergence = self._detect_convergence(symbol, signal_entry)
            if convergence:
                self._handle_convergence(convergence)
                
        except Exception as e:
            logger.error(f"Error processing incoming signal: {e}")
    
    def _detect_convergence(self, symbol: str, new_signal: Dict) -> Optional[ConvergenceEvent]:
        """Detect if new signal creates convergence with recent signals"""
        current_time = new_signal['timestamp']
        direction = new_signal['direction']
        
        # Find recent signals in same direction within window
        matching_signals = []
        for signal in self.recent_signals[symbol]:
            time_diff = current_time - signal['timestamp']
            if (time_diff <= self.convergence_window and 
                signal['direction'] == direction and
                signal['signal_id'] != new_signal['signal_id']):
                matching_signals.append(signal)
        
        # Include the new signal
        all_signals = matching_signals + [new_signal]
        
        # Check if we have enough unique patterns
        unique_patterns = set(s['pattern_type'] for s in all_signals)
        if len(unique_patterns) < self.min_patterns_for_convergence:
            return None
        
        # Create convergence event
        convergence_id = f"CONV_{symbol}_{direction}_{current_time}"
        
        # Calculate boosted confidence
        base_confidence = max(s['confidence'] for s in all_signals)
        boost = (len(unique_patterns) - 1) * self.confidence_boost_per_pattern
        boosted_confidence = min(base_confidence + boost, 1.0)  # Cap at 100%
        
        convergence = ConvergenceEvent(
            convergence_id=convergence_id,
            symbol=symbol,
            direction=direction,
            patterns=list(unique_patterns),
            signal_ids=[s['signal_id'] for s in all_signals],
            timestamps=[s['timestamp'] for s in all_signals],
            confidence_scores=[s['confidence'] for s in all_signals],
            boosted_confidence=boosted_confidence,
            convergence_window=max(s['timestamp'] for s in all_signals) - min(s['timestamp'] for s in all_signals),
            created_at=current_time
        )
        
        return convergence
    
    def _handle_convergence(self, convergence: ConvergenceEvent):
        """Handle detected convergence event"""
        try:
            # Log convergence
            self._log_convergence(convergence)
            
            # Store in active convergences
            self.active_convergences[convergence.convergence_id] = convergence
            
            # Update signal confidence scores in database
            self._update_signal_confidence(convergence)
            
            logger.info(f"Convergence detected: {convergence.symbol} {convergence.direction} "
                       f"({len(convergence.patterns)} patterns, boost to {convergence.boosted_confidence:.1%})")
            
        except Exception as e:
            logger.error(f"Error handling convergence: {e}")
    
    def _log_convergence(self, convergence: ConvergenceEvent):
        """Log convergence event to JSONL file"""
        try:
            log_entry = {
                "type": "convergence_detected",
                "convergence_id": convergence.convergence_id,
                "symbol": convergence.symbol,
                "direction": convergence.direction,
                "patterns": convergence.patterns,
                "signal_ids": convergence.signal_ids,
                "original_confidences": convergence.confidence_scores,
                "boosted_confidence": convergence.boosted_confidence,
                "confidence_boost": convergence.boosted_confidence - max(convergence.confidence_scores),
                "convergence_window_seconds": convergence.convergence_window,
                "timestamp": convergence.created_at,
                "datetime": datetime.fromtimestamp(convergence.created_at).isoformat()
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging convergence: {e}")
    
    def _update_signal_confidence(self, convergence: ConvergenceEvent):
        """Update signal confidence scores in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for signal_id in convergence.signal_ids:
                    conn.execute("""
                        UPDATE signals 
                        SET confidence = ?, 
                            convergence_id = ?,
                            confidence_boosted = 1
                        WHERE signal_id = ?
                    """, (convergence.boosted_confidence, convergence.convergence_id, signal_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating signal confidence: {e}")
    
    def analyze_historical_convergences(self, days_back: int = 30) -> Dict:
        """Analyze historical convergences for pattern insights"""
        try:
            cutoff_time = int(time.time()) - (days_back * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get signals with convergence data
                cursor = conn.execute("""
                    SELECT signal_id, symbol, direction, pattern_type, confidence, 
                           convergence_id, confidence_boosted, outcome, pips_result
                    FROM signals 
                    WHERE created_at > ? AND convergence_id IS NOT NULL
                    ORDER BY created_at DESC
                """, (cutoff_time,))
                
                convergence_signals = [dict(row) for row in cursor.fetchall()]
            
            # Analyze convergence performance
            analysis = self._analyze_convergence_performance(convergence_signals)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing historical convergences: {e}")
            return {}
    
    def _analyze_convergence_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance of convergence signals"""
        if not signals:
            return {"error": "No convergence signals found"}
        
        # Group by convergence ID
        convergences = defaultdict(list)
        for signal in signals:
            convergences[signal['convergence_id']].append(signal)
        
        # Calculate statistics
        total_convergences = len(convergences)
        won_convergences = 0
        total_pips = 0
        convergence_outcomes = []
        
        pattern_combinations = defaultdict(int)
        symbol_performance = defaultdict(list)
        
        for conv_id, conv_signals in convergences.items():
            # Determine convergence outcome (majority wins)
            wins = sum(1 for s in conv_signals if s.get('outcome') == 'WIN')
            losses = sum(1 for s in conv_signals if s.get('outcome') == 'LOSS')
            
            if wins > losses:
                won_convergences += 1
                outcome = 'WIN'
            elif losses > wins:
                outcome = 'LOSS'
            else:
                outcome = 'MIXED'
            
            # Calculate pips
            conv_pips = sum(s.get('pips_result', 0) or 0 for s in conv_signals)
            total_pips += conv_pips
            
            convergence_outcomes.append({
                'convergence_id': conv_id,
                'outcome': outcome,
                'pips': conv_pips,
                'patterns': [s['pattern_type'] for s in conv_signals],
                'symbol': conv_signals[0]['symbol']
            })
            
            # Track pattern combinations
            patterns = sorted(set(s['pattern_type'] for s in conv_signals))
            pattern_key = ' + '.join(patterns)
            pattern_combinations[pattern_key] += 1
            
            # Track symbol performance
            symbol = conv_signals[0]['symbol']
            symbol_performance[symbol].append(conv_pips)
        
        # Calculate win rate
        win_rate = won_convergences / total_convergences if total_convergences > 0 else 0
        avg_pips = total_pips / total_convergences if total_convergences > 0 else 0
        
        # Top performing pattern combinations
        top_combinations = sorted(pattern_combinations.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Symbol performance summary
        symbol_stats = {}
        for symbol, pips_list in symbol_performance.items():
            if pips_list:
                symbol_stats[symbol] = {
                    'convergences': len(pips_list),
                    'total_pips': sum(pips_list),
                    'avg_pips': sum(pips_list) / len(pips_list),
                    'win_rate': sum(1 for p in pips_list if p > 0) / len(pips_list)
                }
        
        return {
            "analysis_period_days": 30,
            "total_convergences": total_convergences,
            "won_convergences": won_convergences,
            "win_rate": round(win_rate, 4),
            "total_pips": round(total_pips, 2),
            "avg_pips_per_convergence": round(avg_pips, 2),
            "top_pattern_combinations": top_combinations,
            "symbol_performance": symbol_stats,
            "recent_outcomes": convergence_outcomes[-10:],  # Last 10
            "calculated_at": int(time.time())
        }
    
    def get_active_convergences(self) -> Dict:
        """Get currently active convergences"""
        current_time = int(time.time())
        
        # Clean up old convergences (older than 10 minutes)
        expired_ids = [
            conv_id for conv_id, conv in self.active_convergences.items()
            if current_time - conv.created_at > 600
        ]
        
        for conv_id in expired_ids:
            del self.active_convergences[conv_id]
        
        return {
            "active_convergences": len(self.active_convergences),
            "convergences": {
                conv_id: {
                    "symbol": conv.symbol,
                    "direction": conv.direction,
                    "patterns": conv.patterns,
                    "boosted_confidence": conv.boosted_confidence,
                    "age_seconds": current_time - conv.created_at
                }
                for conv_id, conv in self.active_convergences.items()
            }
        }
    
    def force_convergence_check(self, symbol: str = None) -> Dict:
        """Manually check for convergences in recent signals"""
        try:
            cutoff_time = int(time.time()) - self.convergence_window
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                    SELECT signal_id, symbol, direction, pattern_type, confidence, created_at
                    FROM signals 
                    WHERE created_at > ?
                """
                params = [cutoff_time]
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                query += " ORDER BY created_at DESC"
                
                cursor = conn.execute(query, params)
                recent_signals = [dict(row) for row in cursor.fetchall()]
            
            # Group by symbol and direction
            grouped_signals = defaultdict(lambda: defaultdict(list))
            for signal in recent_signals:
                grouped_signals[signal['symbol']][signal['direction']].append(signal)
            
            detected_convergences = []
            
            # Check each group for convergences
            for symbol, directions in grouped_signals.items():
                for direction, signals in directions.items():
                    if len(set(s['pattern_type'] for s in signals)) >= self.min_patterns_for_convergence:
                        # Create convergence
                        patterns = list(set(s['pattern_type'] for s in signals))
                        max_confidence = max(s['confidence'] for s in signals)
                        boost = (len(patterns) - 1) * self.confidence_boost_per_pattern
                        boosted_confidence = min(max_confidence + boost, 1.0)
                        
                        convergence_info = {
                            "symbol": symbol,
                            "direction": direction,
                            "patterns": patterns,
                            "signal_count": len(signals),
                            "original_max_confidence": max_confidence,
                            "boosted_confidence": boosted_confidence,
                            "confidence_boost": boost
                        }
                        detected_convergences.append(convergence_info)
            
            return {
                "manual_check_timestamp": int(time.time()),
                "convergences_detected": len(detected_convergences),
                "convergences": detected_convergences
            }
            
        except Exception as e:
            logger.error(f"Error in manual convergence check: {e}")
            return {"error": str(e)}
    
    def export_convergence_report(self, days_back: int = 7) -> str:
        """Export comprehensive convergence analysis report"""
        try:
            analysis = self.analyze_historical_convergences(days_back)
            active = self.get_active_convergences()
            manual_check = self.force_convergence_check()
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "generator": "ConvergenceTracker",
                "analysis_period_days": days_back,
                "convergence_settings": {
                    "window_seconds": self.convergence_window,
                    "boost_per_pattern": self.confidence_boost_per_pattern,
                    "min_patterns": self.min_patterns_for_convergence
                },
                "historical_analysis": analysis,
                "active_convergences": active,
                "recent_check": manual_check
            }
            
            output_file = f"/root/HydraX-v2/convergence_report_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Convergence report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting convergence report: {e}")
            return ""

def main():
    """Run convergence analysis"""
    tracker = ConvergenceTracker()
    
    # Start real-time monitoring
    tracker.start_real_time_monitoring()
    
    try:
        # Generate analysis report
        report_file = tracker.export_convergence_report()
        print(f"Convergence analysis complete. Report saved to: {report_file}")
        
        # Show recent convergences
        manual_check = tracker.force_convergence_check()
        print(f"\nRecent Convergences: {manual_check.get('convergences_detected', 0)}")
        
        for conv in manual_check.get('convergences', []):
            print(f"  {conv['symbol']} {conv['direction']}: {len(conv['patterns'])} patterns "
                  f"(boost: +{conv['confidence_boost']:.1%})")
        
        # Keep monitoring for a bit
        print("\nMonitoring for new convergences... (Press Ctrl+C to stop)")
        time.sleep(60)  # Monitor for 1 minute
        
    except KeyboardInterrupt:
        print("\nStopping convergence monitoring...")
    finally:
        tracker.stop_monitoring()

if __name__ == "__main__":
    main()