#!/usr/bin/env python3
"""
ML Signal Filter - Simple but Effective Real-time Learning
Tracks performance and adjusts confidence dynamically without killing performance
"""

import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
import numpy as np
import sqlite3
import redis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLSignalFilter:
    def __init__(self):
        # Performance tracking (last 100 trades per combo)
        self.performance_history = defaultdict(lambda: {
            'trades': deque(maxlen=100),  # Rolling window
            'recent_wins': 0,
            'total_trades': 0,
            'win_rate': 0.0,
            'last_update': time.time(),
            'confidence_adjustment': 0,
            'enabled': True,
            'trend': 'unknown'
        })
        
        # Static filters (your proven winners from forensic analysis)
        # RELAXED for Sunday testing - allow more pairs and sessions
        self.WINNING_PAIRS = ['EURUSD', 'GBPUSD', 'EURJPY', 'GBPJPY', 'XAUUSD', 'USDJPY']
        self.WINNING_PATTERNS = ['VCB_BREAKOUT', 'LIQUIDITY_SWEEP_REVERSAL', 'ORDER_BLOCK_BOUNCE', 'FAIR_VALUE_GAP_FILL', 'SWEEP_RETURN']
        self.WINNING_SESSIONS = ['LONDON', 'OVERLAP', 'NY', 'ASIAN']
        
        # Dynamic thresholds (ML adjusts these)
        self.min_confidence = 80  # Lowered for Sunday testing
        self.max_signals_per_hour = 8
        self.min_win_rate_threshold = 40  # Auto-disable below this
        
        # Signal rate limiting
        self.signal_timestamps = deque(maxlen=20)
        
        # Database for outcome tracking
        self.db_path = '/root/HydraX-v2/bitten.db'
        
        # Redis for real-time stats
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        except:
            self.redis_client = None
            
        # Load historical performance on startup
        self.load_historical_performance()
        
    def should_fire_signal(self, signal):
        """Main filter - combines static rules + ML learning"""
        
        # STEP 1: Static filters (fast rejection)
        if not self._passes_static_filters(signal):
            return False, "Failed static filters"
            
        # STEP 2: Rate limiting (prevent spam)
        if not self._check_rate_limit():
            return False, "Rate limit exceeded"
            
        # STEP 3: ML performance check
        combo_key = self._get_combo_key(signal)
        performance = self.performance_history[combo_key]
        
        # Auto-disable losing patterns
        if not performance['enabled']:
            return False, f"Pattern disabled (win rate: {performance['win_rate']:.1f}%)"
            
        # STEP 4: Dynamic confidence adjustment
        adjusted_confidence = self._calculate_adjusted_confidence(signal, performance)
        
        if adjusted_confidence < self.min_confidence:
            return False, f"Confidence too low: {adjusted_confidence:.1f}%"
            
        # STEP 5: Pattern-specific checks
        if not self._pattern_specific_checks(signal, performance):
            return False, "Pattern-specific conditions not met"
            
        # Log the decision
        logger.info(f"✅ APPROVED: {signal.get('symbol')} {signal.get('pattern')} "
                   f"@ {adjusted_confidence:.1f}% (was {signal.get('confidence', 0):.1f}%)")
            
        return True, f"APPROVED - Adjusted confidence: {adjusted_confidence:.1f}%"
    
    def _passes_static_filters(self, signal):
        """Static filters based on your forensic analysis"""
        
        # Pair filter (your winners only)
        symbol = signal.get('symbol', signal.get('pair', ''))
        if symbol not in self.WINNING_PAIRS:
            return False
            
        # Pattern filter  
        if signal.get('pattern') not in self.WINNING_PATTERNS:
            return False
            
        # Session filter
        session = signal.get('session', self._get_current_session())
        if session not in self.WINNING_SESSIONS:
            return False
            
        # Confidence range (allow high scores for testing)
        confidence = signal.get('confidence', 0)
        if confidence < 70:  # Only block very low confidence
            return False
            
        return True
    
    def _check_rate_limit(self):
        """Prevent signal spam (max 8/hour)"""
        current_time = time.time()
        
        # Remove old timestamps (older than 1 hour)
        while self.signal_timestamps and current_time - self.signal_timestamps[0] > 3600:
            self.signal_timestamps.popleft()
            
        # Check if under limit
        return len(self.signal_timestamps) < self.max_signals_per_hour
    
    def _calculate_adjusted_confidence(self, signal, performance):
        """ML part - adjust confidence based on performance"""
        base_confidence = signal.get('confidence', 0)
        
        # Performance-based adjustment
        win_rate = performance['win_rate']
        
        if win_rate > 65:
            adjustment = +8  # Boost high performers
        elif win_rate > 55:
            adjustment = +3  # Slight boost
        elif win_rate < 35:
            adjustment = -15  # Penalize poor performers
        elif win_rate < 45:
            adjustment = -5  # Slight penalty
        else:
            adjustment = 0  # Neutral
            
        # Trend-based adjustment
        if performance['trend'] == 'improving':
            adjustment += 3
        elif performance['trend'] == 'declining':
            adjustment -= 3
            
        # Session bonus (your best sessions)
        session = signal.get('session', self._get_current_session())
        if session == 'LONDON':
            adjustment += 2  # London bonus
        elif session == 'OVERLAP':
            adjustment += 1  # Overlap bonus
            
        return min(99, max(70, base_confidence + adjustment))
    
    def _pattern_specific_checks(self, signal, performance):
        """Pattern-specific ML rules"""
        pattern = signal.get('pattern')
        symbol = signal.get('symbol', signal.get('pair', ''))
        
        # EURUSD VCB special treatment (your best combo)
        if symbol == 'EURUSD' and pattern == 'VCB_BREAKOUT':
            return True  # Always allow your best performer
            
        # GBPUSD needs higher confidence
        if symbol == 'GBPUSD' and signal.get('confidence', 0) < 88:
            return False
            
        # Other pattern-specific rules
        if performance['total_trades'] > 20 and performance['win_rate'] < 30:
            return False  # Pattern is proven bad
            
        return True
    
    def update_performance(self, signal, outcome):
        """Learn from trade outcomes (call this when trades close)"""
        combo_key = self._get_combo_key(signal)
        performance = self.performance_history[combo_key]
        
        # Add trade result
        is_win = outcome in ['WIN', 'TP_HIT', 'PROFIT', 'FILLED']
        performance['trades'].append({
            'timestamp': time.time(),
            'win': is_win,
            'confidence': signal.get('confidence', 0)
        })
        
        # Update statistics
        performance['total_trades'] += 1
        if is_win:
            performance['recent_wins'] += 1
            
        # Recalculate win rate (last 50 trades)
        recent_trades = list(performance['trades'])[-50:]
        recent_wins = sum(1 for t in recent_trades if t['win'])
        performance['win_rate'] = (recent_wins / len(recent_trades)) * 100 if recent_trades else 0
        
        # Update trend
        performance['trend'] = self._calculate_trend(performance['trades'])
        
        # Auto-disable poor performers
        if performance['total_trades'] >= 20 and performance['win_rate'] < self.min_win_rate_threshold:
            performance['enabled'] = False
            logger.warning(f"🚫 Auto-disabled {combo_key} - Win rate: {performance['win_rate']:.1f}%")
            
        # Auto-enable recovering patterns
        elif not performance['enabled'] and performance['win_rate'] > 50:
            performance['enabled'] = True
            logger.info(f"✅ Re-enabled {combo_key} - Win rate: {performance['win_rate']:.1f}%")
            
        performance['last_update'] = time.time()
        
        # Store in Redis for real-time access
        if self.redis_client:
            try:
                self.redis_client.hset(f"ml:combo:{combo_key}", mapping={
                    'win_rate': performance['win_rate'],
                    'trend': performance['trend'],
                    'enabled': int(performance['enabled']),
                    'total_trades': performance['total_trades']
                })
            except:
                pass
    
    def _calculate_trend(self, trades):
        """Simple trend detection"""
        if len(trades) < 20:
            return 'unknown'
            
        recent_20 = list(trades)[-20:]
        first_half = recent_20[:10]
        second_half = recent_20[10:]
        
        first_wr = sum(1 for t in first_half if t['win']) / 10 * 100
        second_wr = sum(1 for t in second_half if t['win']) / 10 * 100
        
        if second_wr > first_wr + 10:
            return 'improving'
        elif second_wr < first_wr - 10:
            return 'declining'
        else:
            return 'stable'
    
    def _get_combo_key(self, signal):
        """Create unique key for pattern combinations"""
        symbol = signal.get('symbol', signal.get('pair', 'UNKNOWN'))
        pattern = signal.get('pattern', 'UNKNOWN')
        session = signal.get('session', self._get_current_session())
        return f"{symbol}_{pattern}_{session}"
    
    def _get_current_session(self):
        """Determine current trading session"""
        hour = datetime.utcnow().hour  # Use UTC for consistency
        if 7 <= hour <= 11:  # 7-11 UTC
            return 'LONDON'
        elif 12 <= hour <= 16:  # 12-16 UTC
            return 'OVERLAP'
        elif 17 <= hour <= 21:  # 17-21 UTC
            return 'NY'
        else:
            return 'ASIAN'
    
    def load_historical_performance(self):
        """Load recent performance data on startup"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get last 24 hours of trades
            cursor.execute("""
                SELECT 
                    s.symbol,
                    json_extract(s.payload_json, '$.pattern') as pattern,
                    json_extract(s.payload_json, '$.session') as session,
                    s.confidence,
                    f.status
                FROM signals s
                LEFT JOIN fires f ON s.signal_id = f.fire_id
                WHERE s.created_at > strftime('%s', 'now', '-24 hours')
                AND f.fire_id IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                symbol, pattern, session, confidence, status = row
                if not all([symbol, pattern]):
                    continue
                    
                # Create combo key
                combo_key = f"{symbol}_{pattern}_{session if session else 'UNKNOWN'}"
                
                # Simulate historical trade
                is_win = status in ['FILLED', 'WIN']  # Simplified
                self.performance_history[combo_key]['trades'].append({
                    'timestamp': time.time() - 3600,  # Historical
                    'win': is_win,
                    'confidence': confidence
                })
                self.performance_history[combo_key]['total_trades'] += 1
                
            conn.close()
            logger.info(f"Loaded historical data for {len(self.performance_history)} combinations")
            
        except Exception as e:
            logger.error(f"Error loading historical performance: {e}")
    
    def get_performance_report(self):
        """Generate performance summary"""
        report = []
        for combo_key, perf in self.performance_history.items():
            if perf['total_trades'] > 5:
                report.append({
                    'combo': combo_key,
                    'win_rate': round(perf['win_rate'], 1),
                    'total_trades': perf['total_trades'],
                    'trend': perf['trend'],
                    'enabled': perf['enabled']
                })
        
        return sorted(report, key=lambda x: x['win_rate'], reverse=True)
    
    def get_current_stats(self):
        """Get current ML filter statistics"""
        enabled_combos = sum(1 for p in self.performance_history.values() if p['enabled'])
        total_combos = len(self.performance_history)
        
        avg_win_rate = 0
        if total_combos > 0:
            total_wr = sum(p['win_rate'] for p in self.performance_history.values())
            avg_win_rate = total_wr / total_combos
            
        return {
            'enabled_patterns': enabled_combos,
            'total_patterns': total_combos,
            'avg_win_rate': round(avg_win_rate, 1),
            'signals_this_hour': len(self.signal_timestamps),
            'max_per_hour': self.max_signals_per_hour
        }

# Global instance
ml_filter = MLSignalFilter()

def process_signal(signal):
    """Integration point for webapp"""
    should_fire, reason = ml_filter.should_fire_signal(signal)
    
    if should_fire:
        # Add to signal timestamps for rate limiting
        ml_filter.signal_timestamps.append(time.time())
        logger.info(f"🎯 SIGNAL APPROVED: {signal.get('symbol')} {signal.get('pattern')} - {reason}")
        return True, reason
    else:
        logger.debug(f"🚫 SIGNAL BLOCKED: {signal.get('symbol')} {signal.get('pattern')} - {reason}")
        return False, reason

def report_trade_outcome(signal, outcome):
    """Call this when trades close"""
    ml_filter.update_performance(signal, outcome)
    
def get_ml_report():
    """Get performance report"""
    return ml_filter.get_performance_report()

def get_ml_stats():
    """Get current stats"""
    return ml_filter.get_current_stats()

if __name__ == "__main__":
    # Test the filter
    print("ML Signal Filter initialized")
    print(f"Current stats: {get_ml_stats()}")
    print(f"Performance report: {get_ml_report()[:5]}")  # Top 5