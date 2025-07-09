#!/usr/bin/env python3
"""
BITTEN Self-Optimizing TCS Engine
Dynamically adjusts TCS thresholds to maintain optimal signal volume and win rates
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sqlite3
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TCSOptimizationConfig:
    """Configuration for TCS optimization"""
    target_signals_per_day: int = 65
    min_tcs_threshold: float = 70.0
    max_tcs_threshold: float = 78.0
    target_win_rate: float = 0.85
    min_win_rate: float = 0.82
    adjustment_interval_hours: int = 4
    lookback_hours: int = 24
    signal_volume_tolerance: float = 0.15  # ±15%
    
@dataclass
class MarketCondition:
    """Current market condition assessment"""
    volatility_level: str  # LOW, MEDIUM, HIGH
    trend_strength: float  # 0-1
    session_activity: str  # ASIAN, LONDON, NY, OVERLAP
    news_impact: float  # 0-1
    
class SelfOptimizingTCS:
    """
    Self-optimizing TCS engine that adjusts thresholds based on:
    1. Signal volume targets
    2. Win rate performance
    3. Market conditions
    4. Historical patterns
    """
    
    def __init__(self, config: Optional[TCSOptimizationConfig] = None):
        self.config = config or TCSOptimizationConfig()
        self.db_path = "/root/HydraX-v2/data/tcs_optimization.db"
        self.current_tcs_threshold = self.config.min_tcs_threshold
        self.last_adjustment = datetime.now()
        
        # Performance tracking
        self.signal_history: List[Dict] = []
        self.win_rate_history: List[float] = []
        self.adjustment_history: List[Dict] = []
        
        self._init_database()
        
    def _init_database(self):
        """Initialize optimization tracking database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tcs_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                old_threshold REAL,
                new_threshold REAL,
                reason TEXT,
                signal_count_24h INTEGER,
                win_rate_24h REAL,
                market_condition TEXT,
                volatility_level TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pair TEXT,
                tcs_score REAL,
                direction TEXT,
                result TEXT,
                pips_gained REAL,
                hold_time_minutes INTEGER,
                market_condition TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def get_optimal_tcs_threshold(self, market_condition: MarketCondition) -> float:
        """
        Calculate optimal TCS threshold based on current conditions
        """
        # Get recent performance metrics
        signal_count = await self._get_signal_count_last_24h()
        win_rate = await self._get_win_rate_last_24h()
        
        # Calculate base adjustment
        adjustment = 0.0
        reason_parts = []
        
        # 1. Signal volume adjustment
        target_signals = self.config.target_signals_per_day
        signal_ratio = signal_count / target_signals if target_signals > 0 else 1.0
        
        if signal_ratio < (1.0 - self.config.signal_volume_tolerance):
            # Too few signals - lower threshold
            adjustment -= min(2.0, (1.0 - signal_ratio) * 5.0)
            reason_parts.append(f"Low signal volume ({signal_count}/{target_signals})")
            
        elif signal_ratio > (1.0 + self.config.signal_volume_tolerance):
            # Too many signals - raise threshold
            adjustment += min(2.0, (signal_ratio - 1.0) * 3.0)
            reason_parts.append(f"High signal volume ({signal_count}/{target_signals})")
        
        # 2. Win rate adjustment
        if win_rate < self.config.min_win_rate:
            # Poor win rate - raise threshold for quality
            adjustment += min(3.0, (self.config.min_win_rate - win_rate) * 10.0)
            reason_parts.append(f"Low win rate ({win_rate:.1%})")
            
        elif win_rate > self.config.target_win_rate:
            # Great win rate - can lower threshold for more signals
            adjustment -= min(1.0, (win_rate - self.config.target_win_rate) * 5.0)
            reason_parts.append(f"High win rate ({win_rate:.1%})")
        
        # 3. Market condition adjustments
        if market_condition.volatility_level == "HIGH":
            adjustment += 1.0  # Be more selective in volatile markets
            reason_parts.append("High volatility")
        elif market_condition.volatility_level == "LOW":
            adjustment -= 1.0  # Accept more signals in quiet markets
            reason_parts.append("Low volatility")
            
        # 4. News impact adjustment
        if market_condition.news_impact > 0.7:
            adjustment += 1.5  # Be very selective during news
            reason_parts.append("High news impact")
            
        # Calculate new threshold
        new_threshold = max(
            self.config.min_tcs_threshold,
            min(
                self.config.max_tcs_threshold,
                self.current_tcs_threshold + adjustment
            )
        )
        
        # Only adjust if significant change
        if abs(new_threshold - self.current_tcs_threshold) >= 0.5:
            await self._log_adjustment(
                old_threshold=self.current_tcs_threshold,
                new_threshold=new_threshold,
                reason=", ".join(reason_parts),
                signal_count=signal_count,
                win_rate=win_rate,
                market_condition=market_condition
            )
            
            self.current_tcs_threshold = new_threshold
            self.last_adjustment = datetime.now()
            
            logger.info(f"TCS threshold adjusted: {self.current_tcs_threshold:.1f}% (Reason: {', '.join(reason_parts)})")
        
        return self.current_tcs_threshold
    
    async def _get_signal_count_last_24h(self) -> int:
        """Get signal count from last 24 hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM signal_performance 
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    async def _get_win_rate_last_24h(self) -> float:
        """Get win rate from last 24 hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN result = 'WIN' THEN 1 END) as wins,
                COUNT(*) as total
            FROM signal_performance 
            WHERE timestamp > datetime('now', '-24 hours')
            AND result IN ('WIN', 'LOSS')
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result[1] > 0:
            return result[0] / result[1]
        return 0.85  # Default if no data
    
    async def _log_adjustment(self, old_threshold: float, new_threshold: float, 
                            reason: str, signal_count: int, win_rate: float,
                            market_condition: MarketCondition):
        """Log TCS threshold adjustment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tcs_adjustments 
            (old_threshold, new_threshold, reason, signal_count_24h, win_rate_24h, 
             market_condition, volatility_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            old_threshold, new_threshold, reason, signal_count, win_rate,
            market_condition.session_activity, market_condition.volatility_level
        ))
        
        conn.commit()
        conn.close()
    
    async def log_signal_performance(self, pair: str, tcs_score: float, 
                                   direction: str, result: str, 
                                   pips_gained: float, hold_time_minutes: int,
                                   market_condition: MarketCondition):
        """Log individual signal performance for optimization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO signal_performance 
            (pair, tcs_score, direction, result, pips_gained, hold_time_minutes, market_condition)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            pair, tcs_score, direction, result, pips_gained, 
            hold_time_minutes, market_condition.session_activity
        ))
        
        conn.commit()
        conn.close()
    
    def get_optimization_stats(self) -> Dict:
        """Get current optimization statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recent adjustments
        cursor.execute('''
            SELECT COUNT(*) FROM tcs_adjustments 
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        recent_adjustments = cursor.fetchone()[0]
        
        # Current performance
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                COUNT(CASE WHEN result = 'WIN' THEN 1 END) as wins,
                AVG(pips_gained) as avg_pips,
                AVG(hold_time_minutes) as avg_hold_time
            FROM signal_performance 
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        
        perf = cursor.fetchone()
        conn.close()
        
        return {
            'current_threshold': self.current_tcs_threshold,
            'last_adjustment': self.last_adjustment.isoformat(),
            'recent_adjustments_7d': recent_adjustments,
            'signals_24h': perf[0] or 0,
            'win_rate_24h': (perf[1] / perf[0]) if perf[0] > 0 else 0,
            'avg_pips_24h': perf[2] or 0,
            'avg_hold_time_24h': perf[3] or 0,
            'target_signals': self.config.target_signals_per_day
        }

class PredictiveMovementDetector:
    """
    Advanced pattern detection to catch markets BEFORE they move
    Uses multiple indicators to predict imminent price action
    """
    
    def __init__(self):
        self.momentum_threshold = 0.7
        self.volume_spike_threshold = 1.5
        self.pattern_confidence_threshold = 0.8
        
    async def detect_pre_movement_signals(self, pair_data: Dict) -> Tuple[bool, float, str]:
        """
        Detect if market is about to move before it actually moves
        Returns: (should_signal, confidence, reason)
        """
        confidence_factors = []
        
        # 1. Momentum building detection
        momentum_score = await self._detect_momentum_buildup(pair_data)
        if momentum_score > self.momentum_threshold:
            confidence_factors.append(('momentum_buildup', momentum_score))
        
        # 2. Volume spike analysis
        volume_score = await self._detect_volume_anomaly(pair_data)
        if volume_score > self.volume_spike_threshold:
            confidence_factors.append(('volume_spike', volume_score))
        
        # 3. Order flow pressure
        order_flow_score = await self._detect_order_flow_pressure(pair_data)
        if order_flow_score > 0.6:
            confidence_factors.append(('order_flow_pressure', order_flow_score))
        
        # 4. Support/Resistance proximity
        sr_score = await self._detect_sr_proximity(pair_data)
        if sr_score > 0.7:
            confidence_factors.append(('sr_proximity', sr_score))
        
        # 5. Session transition signals
        session_score = await self._detect_session_transition(pair_data)
        if session_score > 0.6:
            confidence_factors.append(('session_transition', session_score))
        
        # Calculate overall confidence
        if len(confidence_factors) >= 2:
            total_confidence = sum(score for _, score in confidence_factors) / len(confidence_factors)
            reasons = [factor for factor, _ in confidence_factors]
            
            return True, total_confidence, f"Pre-movement: {', '.join(reasons)}"
        
        return False, 0.0, "No pre-movement signals detected"
    
    async def _detect_momentum_buildup(self, pair_data: Dict) -> float:
        """Detect momentum building before breakout"""
        # Simulated momentum detection - replace with real implementation
        return np.random.uniform(0.5, 0.9)
    
    async def _detect_volume_anomaly(self, pair_data: Dict) -> float:
        """Detect volume spikes indicating institutional activity"""
        # Simulated volume analysis - replace with real implementation
        return np.random.uniform(1.0, 2.0)
    
    async def _detect_order_flow_pressure(self, pair_data: Dict) -> float:
        """Detect order flow imbalances"""
        # Simulated order flow analysis - replace with real implementation
        return np.random.uniform(0.4, 0.8)
    
    async def _detect_sr_proximity(self, pair_data: Dict) -> float:
        """Detect proximity to key support/resistance levels"""
        # Simulated S/R analysis - replace with real implementation
        return np.random.uniform(0.5, 0.9)
    
    async def _detect_session_transition(self, pair_data: Dict) -> float:
        """Detect session transition opportunities"""
        current_hour = datetime.now().hour
        
        # London open (3 AM EST)
        if 2 <= current_hour <= 4:
            return 0.8
        # NY open (8 AM EST)
        elif 7 <= current_hour <= 9:
            return 0.9
        # Asian close (3 AM EST)
        elif 2 <= current_hour <= 3:
            return 0.7
        
        return 0.3

# Global optimization instance
_optimizer = None

def get_tcs_optimizer() -> SelfOptimizingTCS:
    """Get global TCS optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = SelfOptimizingTCS()
    return _optimizer

async def main():
    """Test the self-optimizing TCS system"""
    optimizer = SelfOptimizingTCS()
    detector = PredictiveMovementDetector()
    
    # Simulate market condition
    market_condition = MarketCondition(
        volatility_level="MEDIUM",
        trend_strength=0.6,
        session_activity="LONDON",
        news_impact=0.3
    )
    
    # Get optimal threshold
    threshold = await optimizer.get_optimal_tcs_threshold(market_condition)
    print(f"Optimal TCS threshold: {threshold:.1f}%")
    
    # Test predictive detection
    pair_data = {"pair": "EURUSD", "price": 1.0900}
    should_signal, confidence, reason = await detector.detect_pre_movement_signals(pair_data)
    
    if should_signal:
        print(f"Pre-movement signal detected: {confidence:.1%} confidence ({reason})")
    else:
        print("No pre-movement signals detected")
    
    # Show stats
    stats = optimizer.get_optimization_stats()
    print(f"\nOptimization Stats:")
    print(f"Current threshold: {stats['current_threshold']:.1f}%")
    print(f"Signals last 24h: {stats['signals_24h']}")
    print(f"Win rate: {stats['win_rate_24h']:.1%}")

if __name__ == "__main__":
    asyncio.run(main())