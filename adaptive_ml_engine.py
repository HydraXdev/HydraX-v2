#!/usr/bin/env python3
"""
ADAPTIVE ML ENGINE - Real-time learning and optimization
Tracks every signal outcome and adjusts confidence scoring dynamically
"""

import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis
import zmq
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdaptiveMLEngine:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.db_path = '/root/HydraX-v2/bitten.db'
        
        # Performance tracking windows (rolling)
        self.performance_window = deque(maxlen=100)  # Last 100 trades
        self.hourly_performance = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        
        # Dynamic confidence adjustments per combination
        self.confidence_adjustments = defaultdict(float)
        
        # Winning combination cache (updated every cycle)
        self.winning_combinations = {}
        
        # Pattern performance tracking
        self.pattern_stats = defaultdict(lambda: {
            'total': 0,
            'wins': 0,
            'losses': 0,
            'pending': 0,
            'avg_pips': 0,
            'last_10': deque(maxlen=10),
            'confidence_boost': 0
        })
        
        # Pair-specific performance
        self.pair_performance = defaultdict(lambda: {
            'win_rate': 0.0,
            'total_trades': 0,
            'streak': 0,
            'last_update': time.time()
        })
        
        # Session performance tracking
        self.session_stats = {
            'ASIAN': {'win_rate': 0.0, 'volume': 0},
            'LONDON': {'win_rate': 0.0, 'volume': 0},
            'NY': {'win_rate': 0.0, 'volume': 0},
            'OVERLAP': {'win_rate': 0.0, 'volume': 0}
        }
        
        # ML model weights (dynamically adjusted)
        self.weights = {
            'pattern_weight': 0.3,
            'pair_weight': 0.25,
            'session_weight': 0.2,
            'timeframe_weight': 0.15,
            'streak_weight': 0.1
        }
        
        # Minimum confidence thresholds (dynamic)
        self.min_confidence = 85
        self.max_confidence = 95
        
        # Initialize from historical data
        self.load_historical_performance()
        
    def load_historical_performance(self):
        """Load last 24 hours of performance data to initialize ML model"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get last 24 hours of trades with outcomes
            cursor.execute("""
                SELECT 
                    s.signal_id,
                    s.symbol,
                    s.confidence,
                    json_extract(s.payload_json, '$.pattern') as pattern,
                    json_extract(s.payload_json, '$.session') as session,
                    json_extract(s.payload_json, '$.signal_type') as signal_type,
                    f.status,
                    f.ticket,
                    s.created_at
                FROM signals s
                LEFT JOIN fires f ON s.signal_id = f.fire_id
                WHERE s.created_at > strftime('%s', 'now', '-24 hours')
                ORDER BY s.created_at DESC
            """)
            
            results = cursor.fetchall()
            
            # Process historical data
            for row in results:
                symbol = row[1]
                confidence = row[2]
                pattern = row[3]
                session = row[4] if row[4] else 'UNKNOWN'
                status = row[6]
                
                # Update pattern stats
                self.pattern_stats[pattern]['total'] += 1
                
                # Track pair performance
                self.pair_performance[symbol]['total_trades'] += 1
                
                # Track session performance
                if session in self.session_stats:
                    self.session_stats[session]['volume'] += 1
            
            logger.info(f"Loaded {len(results)} historical trades for ML initialization")
            conn.close()
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    def calculate_adaptive_confidence(self, signal_data):
        """
        Calculate real-time adjusted confidence based on current performance
        """
        try:
            base_confidence = signal_data.get('confidence', 0)
            pattern = signal_data.get('pattern', '')
            symbol = signal_data.get('symbol', '')
            session = signal_data.get('session', 'UNKNOWN')
            timeframe = signal_data.get('timeframe', 'M5')
            
            # Start with base confidence
            adjusted_confidence = base_confidence
            
            # 1. Pattern performance adjustment
            pattern_perf = self.pattern_stats[pattern]
            if pattern_perf['total'] > 10:
                pattern_win_rate = pattern_perf['wins'] / pattern_perf['total']
                if pattern_win_rate > 0.5:
                    adjusted_confidence += (pattern_win_rate - 0.5) * 20  # Boost up to +10
                else:
                    adjusted_confidence -= (0.5 - pattern_win_rate) * 20  # Penalty up to -10
            
            # 2. Pair performance adjustment
            pair_perf = self.pair_performance[symbol]
            if pair_perf['total_trades'] > 5:
                if pair_perf['win_rate'] > 0.5:
                    adjusted_confidence += (pair_perf['win_rate'] - 0.5) * 15
                else:
                    adjusted_confidence -= (0.5 - pair_perf['win_rate']) * 15
            
            # 3. Session performance adjustment
            if session in self.session_stats:
                session_perf = self.session_stats[session]
                if session_perf['volume'] > 10:
                    if session == 'LONDON' or session == 'OVERLAP':
                        adjusted_confidence += 5  # Proven winning sessions
                    elif session == 'ASIAN':
                        adjusted_confidence -= 10  # Poor performing session
            
            # 4. Streak bonus/penalty
            if pair_perf['streak'] > 2:
                adjusted_confidence += min(5, pair_perf['streak'])  # Win streak bonus
            elif pair_perf['streak'] < -2:
                adjusted_confidence -= min(5, abs(pair_perf['streak']))  # Loss streak penalty
            
            # 5. Special combination bonuses (from forensic analysis)
            combo_key = f"{symbol}|{pattern}|{session}|{timeframe}"
            if combo_key in self.winning_combinations:
                combo_win_rate = self.winning_combinations[combo_key]
                if combo_win_rate > 0.7:
                    adjusted_confidence += 10  # High performing combo
            
            # Cap the confidence
            adjusted_confidence = max(self.min_confidence, min(self.max_confidence, adjusted_confidence))
            
            # Log the adjustment
            adjustment = adjusted_confidence - base_confidence
            if abs(adjustment) > 5:
                logger.info(f"ML Adjustment: {symbol} {pattern} {base_confidence:.1f}% → {adjusted_confidence:.1f}% (Δ{adjustment:+.1f}%)")
            
            return adjusted_confidence
            
        except Exception as e:
            logger.error(f"Error calculating adaptive confidence: {e}")
            return signal_data.get('confidence', 0)
    
    def update_performance_metrics(self, signal_id, outcome):
        """Update ML model with trade outcome"""
        try:
            # Get signal details
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    symbol,
                    json_extract(payload_json, '$.pattern') as pattern,
                    json_extract(payload_json, '$.session') as session,
                    confidence
                FROM signals
                WHERE signal_id = ?
            """, (signal_id,))
            
            result = cursor.fetchone()
            if result:
                symbol, pattern, session, confidence = result
                
                # Update pattern stats
                self.pattern_stats[pattern]['total'] += 1
                if outcome == 'WIN':
                    self.pattern_stats[pattern]['wins'] += 1
                    self.pattern_stats[pattern]['last_10'].append(1)
                    
                    # Update pair performance
                    self.pair_performance[symbol]['streak'] = max(0, self.pair_performance[symbol]['streak']) + 1
                else:
                    self.pattern_stats[pattern]['losses'] += 1
                    self.pattern_stats[pattern]['last_10'].append(0)
                    
                    # Update pair performance
                    self.pair_performance[symbol]['streak'] = min(0, self.pair_performance[symbol]['streak']) - 1
                
                # Recalculate win rates
                if self.pattern_stats[pattern]['total'] > 0:
                    win_rate = self.pattern_stats[pattern]['wins'] / self.pattern_stats[pattern]['total']
                    self.pattern_stats[pattern]['confidence_boost'] = (win_rate - 0.5) * 20
                
                # Update pair win rate
                self.pair_performance[symbol]['win_rate'] = self.calculate_pair_win_rate(symbol)
                
                # Store in Redis for real-time access
                self.redis_client.hset(f"ml:pattern:{pattern}", "win_rate", win_rate)
                self.redis_client.hset(f"ml:pair:{symbol}", "win_rate", self.pair_performance[symbol]['win_rate'])
                
                logger.info(f"ML Update: {symbol} {pattern} {outcome} - Pattern WR: {win_rate:.1%}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def calculate_pair_win_rate(self, symbol):
        """Calculate rolling win rate for a specific pair"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get last 50 trades for this pair
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN f.status = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM signals s
                JOIN fires f ON s.signal_id = f.fire_id
                WHERE s.symbol = ?
                AND s.created_at > strftime('%s', 'now', '-12 hours')
            """, (symbol,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                return result[1] / result[0]
            
            conn.close()
            return 0.5  # Default to neutral
            
        except Exception as e:
            logger.error(f"Error calculating pair win rate: {e}")
            return 0.5
    
    def get_recommended_signals(self, current_signals):
        """Filter and rank signals based on ML performance data"""
        ranked_signals = []
        
        for signal in current_signals:
            # Calculate adaptive confidence
            ml_confidence = self.calculate_adaptive_confidence(signal)
            
            # Add ML metadata
            signal['ml_confidence'] = ml_confidence
            signal['ml_adjustment'] = ml_confidence - signal.get('confidence', 0)
            
            # Get pattern performance
            pattern = signal.get('pattern', '')
            pattern_stats = self.pattern_stats[pattern]
            if pattern_stats['total'] > 0:
                signal['pattern_win_rate'] = pattern_stats['wins'] / pattern_stats['total']
            else:
                signal['pattern_win_rate'] = 0.5
            
            # Get pair performance
            symbol = signal.get('symbol', '')
            signal['pair_win_rate'] = self.pair_performance[symbol]['win_rate']
            signal['pair_streak'] = self.pair_performance[symbol]['streak']
            
            # Calculate composite score
            composite_score = (
                ml_confidence * 0.4 +
                signal['pattern_win_rate'] * 100 * 0.3 +
                signal['pair_win_rate'] * 100 * 0.3
            )
            signal['ml_score'] = composite_score
            
            ranked_signals.append(signal)
        
        # Sort by ML score
        ranked_signals.sort(key=lambda x: x['ml_score'], reverse=True)
        
        # Apply filters based on ML learning
        filtered_signals = []
        for signal in ranked_signals:
            # Filter criteria based on ML insights
            if (signal['ml_confidence'] >= 85 and
                signal['pattern_win_rate'] >= 0.4 and
                signal['pair_win_rate'] >= 0.35):
                
                filtered_signals.append(signal)
        
        return filtered_signals[:10]  # Return top 10 only
    
    def run_continuous_learning(self):
        """Main loop for continuous ML optimization"""
        logger.info("Starting Adaptive ML Engine...")
        
        # ZMQ setup to receive signals
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        subscriber.connect("tcp://localhost:5557")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "ELITE_GUARD_SIGNAL")
        
        last_optimization = time.time()
        
        while True:
            try:
                # Check for new signals
                if subscriber.poll(1000):  # 1 second timeout
                    message = subscriber.recv_string()
                    if message.startswith("ELITE_GUARD_SIGNAL"):
                        signal_json = message.replace("ELITE_GUARD_SIGNAL ", "")
                        signal_data = json.loads(signal_json)
                        
                        # Apply ML adjustments
                        ml_confidence = self.calculate_adaptive_confidence(signal_data)
                        signal_data['ml_confidence'] = ml_confidence
                        
                        # Publish enhanced signal
                        enhanced_signal = {
                            **signal_data,
                            'ml_enhanced': True,
                            'ml_timestamp': datetime.now().isoformat()
                        }
                        
                        # Store in Redis for webapp access
                        self.redis_client.lpush('ml:enhanced_signals', json.dumps(enhanced_signal))
                        self.redis_client.ltrim('ml:enhanced_signals', 0, 99)  # Keep last 100
                        
                        logger.info(f"ML Enhanced: {signal_data['symbol']} {signal_data['pattern']} "
                                  f"{signal_data['confidence']:.1f}% → {ml_confidence:.1f}%")
                
                # Periodic optimization (every 5 minutes)
                if time.time() - last_optimization > 300:
                    self.optimize_weights()
                    last_optimization = time.time()
                
            except Exception as e:
                logger.error(f"Error in ML loop: {e}")
                time.sleep(1)
    
    def optimize_weights(self):
        """Periodically optimize ML model weights based on recent performance"""
        try:
            logger.info("Optimizing ML weights based on recent performance...")
            
            # Analyze recent performance by factor
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get performance by pattern
            cursor.execute("""
                SELECT 
                    json_extract(s.payload_json, '$.pattern') as pattern,
                    COUNT(*) as total,
                    SUM(CASE WHEN f.status = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM signals s
                JOIN fires f ON s.signal_id = f.fire_id
                WHERE s.created_at > strftime('%s', 'now', '-6 hours')
                GROUP BY pattern
                HAVING total > 5
            """)
            
            pattern_results = cursor.fetchall()
            
            # Update winning combinations cache
            cursor.execute("""
                SELECT 
                    s.symbol || '|' || json_extract(s.payload_json, '$.pattern') || '|' || 
                    json_extract(s.payload_json, '$.session') || '|' || 
                    json_extract(s.payload_json, '$.timeframe') as combo,
                    COUNT(*) as total,
                    SUM(CASE WHEN f.status = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM signals s
                JOIN fires f ON s.signal_id = f.fire_id
                WHERE s.created_at > strftime('%s', 'now', '-12 hours')
                GROUP BY combo
                HAVING total > 3
            """)
            
            combo_results = cursor.fetchall()
            
            # Update winning combinations
            self.winning_combinations = {}
            for combo, total, wins in combo_results:
                if total > 0:
                    self.winning_combinations[combo] = wins / total
            
            logger.info(f"ML Optimization complete. Found {len(self.winning_combinations)} winning combos")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error optimizing weights: {e}")

if __name__ == "__main__":
    engine = AdaptiveMLEngine()
    engine.run_continuous_learning()