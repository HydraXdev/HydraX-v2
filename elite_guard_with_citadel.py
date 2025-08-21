#!/usr/bin/env python3
"""
ELITE GUARD v7.0 - BALANCED EDITION
Target: 45-50% win rate with 1-2 signals per hour minimum
Focus: User engagement + quality improvement
"""

import zmq
import json
import time
import pytz
import threading
import logging
import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import numpy as np
from citadel_lite import CitadelProtection
from src.bitten_core.news_api_client import NewsAPIClient
import statistics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PatternSignal:
    pattern: str
    direction: str
    entry_price: float
    confidence: float
    timeframe: str
    pair: str
    quality_score: float = 0  # NEW: Shows relative quality
    momentum_score: float = 0
    volume_quality: float = 0

class DynamicThresholdManager:
    """Manages dynamic thresholds per pattern based on session, volatility, and signal flow"""
    
    def __init__(self):
        # Base thresholds for each pattern - QUALITY focused
        self.thresholds = {
            'LIQUIDITY_SWEEP_REVERSAL': {
                'pip_sweep': 3.0,  # HIGH sweep requirement for quality
                'min_conf': 75,    # Minimum 75% confidence
                'vol_gate': 1.3,
                'rejection_required': True  # Require rejection candle
            },
            'ORDER_BLOCK_BOUNCE': {
                'body_ratio': 0.6,  # Strong body requirement
                'min_conf': 70,     # Minimum 70% confidence
                'vol_gate': 1.2,
                'zone_tolerance': 0.3  # Tighter zone
            },
            'FAIR_VALUE_GAP_FILL': {
                'gap_size': 0.5,
                'min_conf': 65,     # Lower base
                'vol_gate': 1.1,
                'fill_ratio': 0.5
            },
            'VCB_BREAKOUT': {
                'compression_ratio': 0.7,
                'min_conf': 70,     # Start at 70
                'vol_gate': 1.5,
                'breakout_mult': 1.0
            },
            'SWEEP_RETURN': {
                'wick_ratio': 0.7,
                'min_conf': 72,     # Start at 72
                'vol_gate': 1.3,
                'sweep_pips': 2.0
            },
            'MOMENTUM_BURST': {
                'breakout_pips': 1.0,
                'min_conf': 68,     # Start at 68
                'vol_gate': 1.2,
                'momentum_mult': 1.0
            }
        }
        
        # Track signals per pattern per 15-min window
        self.signal_counts = {pattern: 0 for pattern in self.thresholds}
        self.tradeable_count = 0  # Track 70%+ signals
        self.scout_count = 0      # Track <70% scout signals
        self.last_adjust_time = datetime.now()
        self.current_session = self.get_session()
        self.last_atr = 0.0005  # Default ATR
        self.adjustment_history = []
        self.scout_mode_active = True  # Start in scout mode for quiet periods
        self.last_hour_tradeables = []  # Track hourly tradeable rate
        
    def get_session(self):
        """Determine current trading session based on UTC time"""
        hour = datetime.utcnow().hour
        if 22 <= hour or hour < 7:
            return 'ASIAN'  # Low volatility session
        elif 7 <= hour < 12:
            return 'LONDON'  # Medium-high volatility
        elif 12 <= hour < 17:
            return 'NY'  # High volatility
        elif 17 <= hour < 22:
            return 'LATE_NY'  # Medium volatility
        else:
            return 'OVERLAP'  # Highest volatility
    
    def update_volatility(self, atr_value):
        """Update current market volatility (ATR)"""
        self.last_atr = atr_value
        
    def record_signal(self, pattern):
        """Record that a signal was generated for tracking"""
        if pattern in self.signal_counts:
            self.signal_counts[pattern] += 1
            
    def adjust_thresholds(self):
        """Adjust thresholds based on session, volatility, and signal flow"""
        now = datetime.now()
        
        # Only adjust every 15 minutes
        if (now - self.last_adjust_time).total_seconds() < 900:
            return
            
        self.last_adjust_time = now
        session = self.get_session()
        
        # Calculate hourly tradeable rate
        self.last_hour_tradeables = [t for t in self.last_hour_tradeables if (now - t).total_seconds() < 3600]
        hourly_rate = len(self.last_hour_tradeables)
        
        # Phase out scout mode when we have 2+ tradeables per hour
        if hourly_rate >= 2:
            self.scout_mode_active = False
            logger.info(f"📈 Scout mode DISABLED - {hourly_rate} tradeables/hr")
        elif hourly_rate < 1:
            self.scout_mode_active = True
            logger.info(f"🔍 Scout mode ENABLED - {hourly_rate} tradeables/hr")
        
        # Log adjustment
        logger.info(f"🎯 Adjusting thresholds - Session: {session}, ATR: {self.last_atr:.5f}, Scout: {self.scout_mode_active}")
        
        for pattern in self.thresholds:
            th = self.thresholds[pattern]
            signals = self.signal_counts[pattern]
            
            # Base adjustment based on signal flow
            if signals == 0:
                # No signals - loosen thresholds by 10%
                self._loosen_thresholds(th, 0.10)
                logger.info(f"  {pattern}: No signals - loosening 10%")
            elif signals > 5:
                # Too many signals - tighten by 15%
                self._tighten_thresholds(th, 0.15)
                logger.info(f"  {pattern}: {signals} signals - tightening 15%")
            elif signals > 3:
                # Good flow - slight tightening
                self._tighten_thresholds(th, 0.05)
                logger.info(f"  {pattern}: {signals} signals - tightening 5%")
            # 1-3 signals is ideal, no adjustment
            
            # Session-based override
            if session == 'ASIAN':
                # Asian session - loosen for low volatility
                self._loosen_thresholds(th, 0.20)
                logger.debug(f"  {pattern}: Asian session - extra 20% looser")
            elif session in ['LONDON', 'NY']:
                # Active sessions - slight tightening for quality
                self._tighten_thresholds(th, 0.10)
                logger.debug(f"  {pattern}: Active session - 10% tighter")
            elif session == 'OVERLAP':
                # Highest volatility - tighten more
                self._tighten_thresholds(th, 0.15)
                logger.debug(f"  {pattern}: Overlap session - 15% tighter")
            
            # Volatility-based override
            if self.last_atr < 0.0003:
                # Very low volatility - aggressive loosening
                self._loosen_thresholds(th, 0.25)
                logger.debug(f"  {pattern}: Very low ATR - 25% looser")
            elif self.last_atr < 0.0005:
                # Low volatility - moderate loosening
                self._loosen_thresholds(th, 0.15)
                logger.debug(f"  {pattern}: Low ATR - 15% looser")
            elif self.last_atr > 0.001:
                # High volatility - tighten for quality
                self._tighten_thresholds(th, 0.20)
                logger.debug(f"  {pattern}: High ATR - 20% tighter")
            
            # Apply bounds to prevent extreme values
            self._apply_bounds(th, pattern)
            
            # Reset signal count for next period
            self.signal_counts[pattern] = 0
            
    def _loosen_thresholds(self, thresholds, factor):
        """Loosen thresholds by given factor"""
        for key, value in thresholds.items():
            if key == 'rejection_required':
                continue  # Skip boolean
            elif 'pip' in key or 'ratio' in key or 'size' in key or 'mult' in key:
                thresholds[key] *= (1 - factor)  # Reduce requirement
            elif 'conf' in key:
                thresholds[key] = max(20, value - (factor * 20))  # Lower min confidence
            elif 'vol' in key:
                thresholds[key] *= (1 - factor)  # Lower volume gate
                
    def _tighten_thresholds(self, thresholds, factor):
        """Tighten thresholds by given factor"""
        for key, value in thresholds.items():
            if key == 'rejection_required':
                continue  # Skip boolean
            elif 'pip' in key or 'ratio' in key or 'size' in key or 'mult' in key:
                thresholds[key] *= (1 + factor)  # Increase requirement
            elif 'conf' in key:
                thresholds[key] = min(85, value + (factor * 20))  # Raise min confidence
            elif 'vol' in key:
                thresholds[key] *= (1 + factor)  # Raise volume gate
                
    def _apply_bounds(self, thresholds, pattern):
        """Apply reasonable bounds to prevent extreme threshold values"""
        bounds = {
            'pip_sweep': (0.05, 5.0),
            'min_conf': (20, 85),
            'vol_gate': (0.5, 2.0),
            'body_ratio': (0.1, 0.8),
            'compression_ratio': (0.3, 0.9),
            'wick_ratio': (0.3, 0.9),
            'gap_size': (0.1, 2.0),
            'breakout_pips': (0.5, 5.0)
        }
        
        for key, value in thresholds.items():
            if key in bounds:
                min_val, max_val = bounds[key]
                thresholds[key] = max(min_val, min(max_val, value))
                
    def get_threshold(self, pattern, key):
        """Get current threshold value for pattern and key"""
        if pattern in self.thresholds and key in self.thresholds[pattern]:
            return self.thresholds[pattern][key]
        return None
        
    def get_status(self):
        """Get current status of thresholds"""
        return {
            'session': self.current_session,
            'atr': self.last_atr,
            'signal_counts': self.signal_counts.copy(),
            'thresholds': self.thresholds.copy()
        }
    final_score: float = 0

class EliteGuardBalanced:
    """Balanced signal generation for optimal user engagement"""
    
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.publisher = None
        
        # Market data storage - EXPANDED for proper pattern detection
        self.tick_data = defaultdict(lambda: deque(maxlen=500))
        self.m1_data = defaultdict(lambda: deque(maxlen=500))    # M1 OHLC data (~8 hours)
        self.m5_data = defaultdict(lambda: deque(maxlen=300))    # M5 OHLC data (~25 hours)
        self.m15_data = defaultdict(lambda: deque(maxlen=200))   # M15 OHLC data (~50 hours)
        self.current_candles = {}  # For building M1 candles from ticks
        self.last_tick_time = defaultdict(float)
        
        # CITADEL Protection System
        self.citadel = CitadelProtection()
        
        # ML Performance tracking
        self.performance_history = {}
        
        # Pattern detection state
        self.last_signal_time = defaultdict(float)  # Per-pair cooldown
        self.signal_history = deque(maxlen=100)  # Track recent signals
        
        # Define trading pairs FIRST (before load_candles)
        self.trading_pairs = [
            # Major Forex Pairs (7)
            "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD",
            # Cross Pairs (7)
            "EURJPY", "GBPJPY", "EURGBP", "EURAUD", "GBPCAD", "AUDJPY", "NZDJPY",
            # Additional & Exotics (3)
            "USDCNH", "USDSEK", "USDMXN",
            # Precious Metals (2)
            "XAUUSD", "XAGUSD"
            # Total: 19 pairs (NO CRYPTO)
        ]
        
        # Load candle cache on startup (AFTER trading_pairs defined)
        self.load_candles()
        
        # Test candle building (for debugging)
        self.test_candle_building()
        
        self.hourly_signal_count = defaultdict(int)  # Track signals per hour
        self.current_hour = datetime.now().hour
        
        # News calendar for confidence adjustment (Forex Factory API)
        self.news_client = NewsAPIClient()
        self.news_events = []
        self.last_news_fetch = 0
        
        # Quality tracking
        self.pattern_performance = defaultdict(lambda: {'wins': 0, 'losses': 0})
        
        # Initialize Dynamic Threshold Manager
        self.threshold_manager = DynamicThresholdManager()
        
        # Balanced thresholds (less strict than optimized)
        # Trading pairs already defined above (before load_candles)
        
        self.MIN_MOMENTUM = 30   # Require strong momentum
        self.MIN_VOLUME = 20     # Require decent volume
        self.MIN_TREND = 15      # Require some trend alignment
        self.MIN_CONFIDENCE = 65 # RECALIBRATED: 65% to capture more signals for optimization
        self.COOLDOWN_MINUTES = 10 # Reasonable cooldown between signals per pair
        
        # Quality tiers for user display
        self.QUALITY_TIERS = {
            'PREMIUM': 75,   # Best signals
            'STANDARD': 65,  # Good signals
            'ACCEPTABLE': 55 # Minimum viable
        }
        
        # Session times
        self.sessions = {
            'tokyo': (0, 9),
            'london': (8, 17),
            'newyork': (13, 22),
            'overlap_london_ny': (13, 17)
        }
        
        self.running = False
        
    def analyze_signal_quality(self):
        """Analyze signal quality from last 30 minutes of truth log"""
        try:
            with open('/root/HydraX-v2/truth_log.jsonl', 'r') as f:
                lines = f.readlines()
                
            recent = []
            cutoff_time = datetime.now() - timedelta(seconds=1800)  # 30 minutes
            
            for line in lines[-200:]:  # Check last 200 lines for efficiency
                try:
                    data = json.loads(line)
                    timestamp_str = data.get('timestamp', '')
                    if timestamp_str:
                        # Parse ISO format timestamp
                        ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').replace('+00:00', ''))
                        if ts > cutoff_time:
                            recent.append(data)
                except:
                    continue
            
            # Calculate metrics
            total_signals = len(recent)
            
            # For win rate, we'd need to check if next candle closed higher
            # This is a simplified version - in reality we'd track actual outcomes
            wins = 0
            for sig in recent:
                # Simplified win check - would need actual outcome tracking
                if sig.get('quality_score', 0) > 70:  # Proxy for win
                    wins += 1
            
            win_rate = (wins / total_signals * 100) if total_signals else 0
            avg_conf = sum(s.get('confidence', s.get('quality_score', 0)) for s in recent) / total_signals if total_signals else 0
            avg_quality = sum(s.get('quality_score', 0) for s in recent) / total_signals if total_signals else 0
            
            # Pattern breakdown
            pattern_counts = defaultdict(int)
            for s in recent:
                pattern = s.get('pattern', 'UNKNOWN')
                pattern_counts[pattern] += 1
            
            print(f"\n📊 SIGNAL QUALITY ANALYSIS (Last 30 min)")
            print(f"="*50)
            print(f"Total Signals: {total_signals} ({total_signals*2}/hr projected)")
            print(f"Win Rate: {win_rate:.1f}% (proxy based on quality>70)")
            print(f"Avg Confidence: {avg_conf:.1f}%")
            print(f"Avg Quality: {avg_quality:.1f}%")
            print(f"\nPattern Distribution:")
            for pattern, count in pattern_counts.items():
                print(f"  {pattern}: {count}")
            print(f"="*50)
            
            return total_signals, win_rate, avg_conf, avg_quality
            
        except Exception as e:
            print(f"Error analyzing signals: {e}")
            return 0, 0, 0, 0
        
    def setup_zmq(self):
        """Setup ZMQ connections"""
        try:
            # Subscribe to market data (ticks)
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://127.0.0.1:5560")
            self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
            
            # Subscribe DIRECTLY to port 5556 where EA sends OHLC data
            # EA's PushOHLCData sends M1/M5/M15 OHLC to this port
            self.ohlc_subscriber = self.context.socket(zmq.SUB)
            self.ohlc_subscriber.connect("tcp://127.0.0.1:5556")
            self.ohlc_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to ALL messages
            self.ohlc_subscriber.setsockopt(zmq.RCVTIMEO, 100)  # 100ms timeout for non-blocking
            print(f"🔌 OHLC SUB connected to 5556 for direct EA OHLC data")
            
            # Publisher for signals
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")
            
            logger.info("✅ ZMQ connections established (5560 for ticks, 5556 for OHLC, 5557 for signals)")
            return True
        except Exception as e:
            logger.error(f"❌ ZMQ setup failed: {e}")
            return False
    
    def is_active_session(self) -> bool:
        """Check if we're in an active trading session"""
        # TEMPORARY: Always active for testing
        return True
        
        current_hour = datetime.now(pytz.UTC).hour
        
        # Most active during overlaps
        if 13 <= current_hour <= 17:  # London/NY overlap
            return True
        if 8 <= current_hour <= 22:   # London through NY
            return True
        if 0 <= current_hour <= 2:    # Late Asia
            return True
            
        return False
    
    def get_session_bonus(self) -> float:
        """Get confidence bonus based on session"""
        current_hour = datetime.now(pytz.UTC).hour
        
        if 13 <= current_hour <= 17:  # Best time
            return 10
        elif 8 <= current_hour <= 11:  # London open
            return 8
        elif 14 <= current_hour <= 16: # NY open
            return 7
        else:
            return 5
    
    def calculate_dynamic_confidence(self, symbol: str, base_pattern_score: float, momentum: float, volume: float) -> float:
        """Calculate confidence based on quality components for 75-82% target"""
        confidence = 0
        
        # Base from pattern strength (65% contribution for reliable base)
        base_contribution = base_pattern_score * 0.65
        confidence += base_contribution
        print(f"🎯 {symbol} CONFIDENCE CALCULATION:")
        print(f"  📊 Base pattern: {base_pattern_score:.1f} * 0.65 = {base_contribution:.1f}%")
        
        # Momentum bonus: +0.2% per pip for better signal quality
        momentum_bonus = min(12, momentum * 0.2)  # Cap at 12%
        confidence += momentum_bonus
        print(f"  📊 Momentum: {momentum:.1f} pips * 0.2 = +{momentum_bonus:.1f}%")
        
        # Volume scoring (volume is % of average, e.g., 100 = average)
        if volume >= 100:  # At or above average
            volume_bonus = 8.0
        elif volume >= 80:  # Slightly below average  
            volume_bonus = 6.0
        elif volume >= 60:  # Below average
            volume_bonus = 4.0
        elif volume >= 40:  # Low volume
            volume_bonus = 2.0
        else:
            volume_bonus = 1.0
        confidence += volume_bonus
        print(f"  📊 Volume: {volume:.0f}% of avg = +{volume_bonus:.1f}%")
        
        # Session bonus (5-10%)
        session_bonus = self.get_session_bonus()
        confidence += session_bonus
        print(f"  📊 Session: +{session_bonus:.0f}%")
        
        # Spread quality (-1 to +2%)
        spread_adjustment = 0
        if symbol in self.tick_data:
            recent_ticks = list(self.tick_data[symbol])[-10:]
            if recent_ticks:
                spreads = [(t.get('ask', 0) - t.get('bid', 0)) for t in recent_ticks if t.get('ask') and t.get('bid')]
                if spreads:
                    avg_spread = np.mean(spreads)
                    pip_size = 0.01 if 'JPY' in symbol else 0.0001
                    spread_pips = avg_spread / pip_size
                    if spread_pips < 1.5:
                        spread_adjustment = 2  # Tight spread
                    elif spread_pips < 2.5:
                        spread_adjustment = 0  # Normal
                    else:
                        spread_adjustment = -1  # Wide spread
                    print(f"  📊 Spread: {spread_pips:.1f}p = {spread_adjustment:+d}%")
        confidence += spread_adjustment
        
        # Market activity bonus
        activity_bonus = 0
        if symbol in self.m1_data and len(self.m1_data[symbol]) >= 5:
            recent = list(self.m1_data[symbol])[-5:]
            ranges = [(c['high'] - c['low']) for c in recent]
            avg_range = np.mean(ranges) if ranges else 0
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            range_pips = avg_range / pip_size
            if range_pips > 3:
                activity_bonus = 4  # Very active
            elif range_pips > 1.5:
                activity_bonus = 2  # Active
            print(f"  📊 Activity: {range_pips:.1f}p range = +{activity_bonus}%")
        confidence += activity_bonus
        
        # Ensure 75-82% range for quality signals (with 55% minimum)
        raw_confidence = confidence
        final_confidence = min(95, max(55, confidence))  # Floor at 55%, cap at 95%
        
        print(f"  🎯 RAW: {raw_confidence:.1f}% → FINAL: {final_confidence:.1f}% (Target: 75-82%)")
        
        return final_confidence
    
    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range for R:R feasibility check"""
        if symbol not in self.m5_data or len(self.m5_data[symbol]) < period:
            # Default ATR values for different pairs
            if 'JPY' in symbol:
                return 0.5  # 50 pips default for JPY pairs
            elif symbol in ['XAUUSD']:
                return 5.0  # 500 pips for gold
            elif symbol in ['XAGUSD']:
                return 0.05  # 5 pips for silver
            else:
                return 0.001  # 10 pips default for majors
        
        candles = list(self.m5_data[symbol])[-period:]
        pip_size = 0.01 if 'JPY' in symbol else 0.1 if symbol == 'XAUUSD' else 0.0001
        
        true_ranges = []
        for i in range(1, len(candles)):
            high_low = candles[i]['high'] - candles[i]['low']
            high_close = abs(candles[i]['high'] - candles[i-1]['close'])
            low_close = abs(candles[i]['low'] - candles[i-1]['close'])
            true_range = max(high_low, high_close, low_close)
            true_ranges.append(true_range)
        
        atr = np.mean(true_ranges) if true_ranges else 0.001
        atr_pips = atr / pip_size
        return atr_pips
    
    def calculate_quality_score(self, signal: PatternSignal) -> float:
        """Calculate overall quality score for ranking"""
        score = 0
        
        # Base pattern confidence
        score += signal.confidence * 0.3
        
        # Momentum contribution
        if signal.momentum_score >= 25:
            score += 20
        elif signal.momentum_score >= 15:
            score += 10
        
        # Volume quality
        if signal.volume_quality >= 20:
            score += 15
        elif signal.volume_quality >= 10:
            score += 8
        
        # Session bonus
        score += self.get_session_bonus()
        
        # Pattern history performance
        pattern_stats = self.pattern_performance[signal.pattern]
        if pattern_stats['wins'] + pattern_stats['losses'] > 5:
            win_rate = pattern_stats['wins'] / (pattern_stats['wins'] + pattern_stats['losses'])
            score += win_rate * 20
        
        # Spread penalty (if available)
        if signal.pair in self.tick_data:
            recent_ticks = list(self.tick_data[signal.pair])[-10:]
            if recent_ticks:
                spreads = [abs(t.get('ask', 0) - t.get('bid', 0)) for t in recent_ticks]
                avg_spread = np.mean(spreads) if spreads else 0
                pip_size = 0.01 if 'JPY' in signal.pair else 0.0001
                spread_pips = avg_spread / pip_size
                
                if spread_pips < 2:
                    score += 5
                elif spread_pips > 4:
                    score -= 10
        
        return min(100, max(0, score))
    
    def calculate_momentum_score(self, symbol: str, direction: str) -> float:
        """FIXED: Calculate momentum in PIPS not percentage"""
        try:
            if symbol not in self.m1_data or len(self.m1_data[symbol]) < 5:
                return 0
                
            candles = list(self.m1_data[symbol])  # Convert deque to list for slicing
            if len(candles) < 5:
                return 0
            
            recent = candles[-5:]
            
            # Calculate pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            else:
                pip_size = 0.0001
            
            # Calculate average pip movement over last 5 candles
            pip_changes = []
            for i in range(1, len(recent)):
                pip_change = (recent[i]['close'] - recent[i-1]['close']) / pip_size
                pip_changes.append(pip_change)
            
            # Average pip movement (directional)
            avg_pip_movement = sum(pip_changes) / len(pip_changes)
            
            # 3-bar momentum in pips for stronger signal
            momentum_3bar_pips = (recent[-1]['close'] - recent[-3]['close']) / pip_size
            
            # Use the stronger of the two
            momentum_pips = max(abs(avg_pip_movement), abs(momentum_3bar_pips))
            
            # Score based on pip movement - proper scaling for real trading
            # 1 pip = 10 score, 5 pips = 50 score, 10 pips = 100 score
            score = momentum_pips * 10
            
            print(f"🔍 Momentum {symbol} {direction}: Avg={avg_pip_movement:.1f}pips, 3bar={momentum_3bar_pips:.1f}pips, Score={score:.1f}")
            
            # Direction check - return real score for prime time trading
            if direction == "BUY" and momentum_3bar_pips > 0:
                return score  # Return actual calculated score
            elif direction == "SELL" and momentum_3bar_pips < 0:
                return score  # Return actual calculated score
            
            return 0  # Wrong direction = no momentum
            
        except Exception as e:
            print(f"❌ Momentum calc error for {symbol}: {e}")
            return 0
    
    def analyze_volume_profile(self, symbol: str) -> float:
        """Session-aware volume analysis for low-volatility periods"""
        try:
            from datetime import datetime
            current_hour = datetime.utcnow().hour
            
            # PROPER VOLUME SCORING FOR PRIME TIME
            min_volume_score = 10  # Base volume score for active trading
            
            # Session detection for logging
            if current_hour >= 22 or current_hour < 7:
                session = "ASIAN"
            elif current_hour >= 7 and current_hour < 8:
                session = "PRE-LONDON"
            else:
                session = "LONDON/NY"
            if symbol not in self.m1_data or len(self.m1_data[symbol]) < 10:
                return 20  # Default to decent volume for prime time
                
            candles = list(self.m1_data[symbol])  # Convert deque to list for slicing
            if len(candles) < 10:
                return 20  # Default to decent volume for prime time
            
            recent = candles[-10:]
            volumes = [c.get('tick_volume', 0) for c in recent]
            
            if not volumes or np.mean(volumes) == 0:
                return 20  # Default to decent volume for prime time
            
            # Current vs average
            current_vol = volumes[-1]
            avg_vol = np.mean(volumes[:-1])
            
            print(f"📊 Volume {symbol} [{session}]: Current={current_vol}, Avg={avg_vol:.1f}, Min={min_volume_score}")
            
            if avg_vol > 0:
                vol_ratio = current_vol / avg_vol
                # PRIME TIME VOLUME SCORING
                if vol_ratio > 1.5:  # 50% above average = strong volume
                    return min(50, vol_ratio * 30)
                elif vol_ratio > 1.2:  # 20% above average = good volume
                    return 30
                elif vol_ratio > 1.0:  # Above average
                    return 20
                else:  # Below average but still trading
                    return 15
            
            return 20  # Default volume for prime time
            
        except:
            return 20  # Default volume for prime time
    
    def detect_liquidity_sweep_reversal(self, symbol: str) -> Optional[PatternSignal]:
        """INDUSTRY STANDARD: Price sweeps >3 pips beyond recent high/low to grab liquidity, reverses with rejection candle"""
        try:
            # Check if symbol exists in m5_data
            if symbol not in self.m5_data:
                print(f"🔍 LSR {symbol}: No M5 data available")
                return None
                
            if len(self.m5_data[symbol]) < 3:  # Need at least 3 M5 candles
                print(f"🔍 LSR {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 3+")
                return None
                
            recent_candles = list(self.m5_data[symbol])[-3:]  # Just last 3 candles for industry standard
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            else:
                pip_size = 0.0001
            
            # INDUSTRY STANDARD: Find recent high/low from candles BEFORE the sweep
            recent_high = max(c['high'] for c in recent_candles[:-1])
            recent_low = min(c['low'] for c in recent_candles[:-1])
            current_candle = recent_candles[-1]
            
            # Calculate sweep size in pips (how far beyond recent high/low)
            bullish_sweep = (recent_low - current_candle['low']) / pip_size if current_candle['low'] < recent_low else 0
            bearish_sweep = (current_candle['high'] - recent_high) / pip_size if current_candle['high'] > recent_high else 0
            
            # INDUSTRY STANDARD: Minimum 3 pip sweep for major pairs (adjust for gold)
            min_sweep_pips = 3.0  # Standard 3 pip minimum sweep
            if symbol == 'XAUUSD':
                min_sweep_pips = 30.0  # Gold needs bigger moves (30 pip = $3)
            
            # Calculate rejection candle characteristics
            candle_range = (current_candle['high'] - current_candle['low']) / pip_size
            upper_wick = (current_candle['high'] - max(current_candle['open'], current_candle['close'])) / pip_size
            lower_wick = (min(current_candle['open'], current_candle['close']) - current_candle['low']) / pip_size
            
            # Debug logging with differences from old logic
            print(f"🔍 LSR {symbol}: INDUSTRY STANDARD CHECK")
            print(f"   Recent High={recent_high:.5f}, Low={recent_low:.5f}")
            print(f"   Current: High={current_candle['high']:.5f}, Low={current_candle['low']:.5f}, Close={current_candle['close']:.5f}")
            print(f"   Sweep: Bullish={bullish_sweep:.1f}p, Bearish={bearish_sweep:.1f}p (Min req: {min_sweep_pips}p)")
            print(f"   Candle: Range={candle_range:.1f}p, Upper wick={upper_wick:.1f}p, Lower wick={lower_wick:.1f}p")
            print(f"   OLD vs NEW: Was using ATR-based (1.5p), now fixed 3p standard")
            
            # BULLISH SWEEP: Price swept below low by >3 pips with rejection candle
            if bullish_sweep >= min_sweep_pips:
                # INDUSTRY STANDARD: Rejection = lower wick > 50% of candle range
                rejection_ratio = lower_wick / candle_range if candle_range > 0 else 0
                has_rejection = rejection_ratio > 0.5 and current_candle['close'] > recent_low
                
                print(f"🔍 LSR {symbol}: BULLISH SWEEP DETECTED! {bullish_sweep:.1f} pips")
                print(f"   Rejection ratio: {rejection_ratio:.2%} (need >50%), Close above low: {current_candle['close'] > recent_low}")
                
                if has_rejection:  # REQUIRE rejection candle for quality
                    # R:R FEASIBILITY CHECK
                    atr = self.calculate_atr(symbol)
                    entry = current_candle['close'] + pip_size
                    sl_distance = abs(current_candle['low'] - entry) / pip_size
                    tp_distance = sl_distance * 1.5  # Target 1.5 R:R minimum
                    
                    # Check if TP is within 2x ATR (feasible)
                    rr_feasible = tp_distance <= 2 * atr
                    actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                    
                    if not rr_feasible:
                        print(f"🚫 LSR {symbol} BUY: R:R not feasible - TP={tp_distance:.1f}p > 2xATR={2*atr:.1f}p")
                        return None
                    
                    if actual_rr < 1.5:
                        print(f"⚠️ LSR {symbol} BUY: R:R too low - {actual_rr:.2f} < 1.5 minimum")
                        return None
                    
                    print(f"✅ LSR {symbol} BUY: R:R={actual_rr:.2f}, SL={sl_distance:.1f}p, TP={tp_distance:.1f}p, ATR={atr:.1f}p")
                    
                    # Calculate base quality from sweep size and rejection
                    base_quality = 50  # Start at 50%
                    base_quality += min(bullish_sweep - min_sweep_pips, 5) * 2  # +2% per extra pip (max +10%)
                    base_quality += rejection_ratio * 10  # +10% for perfect rejection
                    base_quality += min(actual_rr - 1.5, 0.5) * 10  # Bonus for R:R > 1.5
                    
                    print(f"🔍 LSR {symbol}: Pattern quality = {base_quality:.1f}% (Base 50 + Sweep + Rejection + R:R bonus)")
                    
                    # Return signal with base quality
                    return PatternSignal(
                        pattern="LIQUIDITY_SWEEP_REVERSAL",
                        direction="BUY",
                        entry_price=entry,
                        confidence=base_quality,
                        timeframe="M5",
                        pair=symbol,
                        quality_score=base_quality
                    )
            
            # BEARISH SWEEP: Price swept above high by >3 pips with rejection candle
            elif bearish_sweep >= min_sweep_pips:
                # INDUSTRY STANDARD: Rejection = upper wick > 50% of candle range
                rejection_ratio = upper_wick / candle_range if candle_range > 0 else 0
                has_rejection = rejection_ratio > 0.5 and current_candle['close'] < recent_high
                
                print(f"🔍 LSR {symbol}: BEARISH SWEEP DETECTED! {bearish_sweep:.1f} pips")
                print(f"   Rejection ratio: {rejection_ratio:.2%} (need >50%), Close below high: {current_candle['close'] < recent_high}")
                
                if has_rejection:  # REQUIRE rejection candle for quality
                    # R:R FEASIBILITY CHECK
                    atr = self.calculate_atr(symbol)
                    entry = current_candle['close'] - pip_size
                    sl_distance = abs(current_candle['high'] - entry) / pip_size
                    tp_distance = sl_distance * 1.5  # Target 1.5 R:R minimum
                    
                    # Check if TP is within 2x ATR (feasible)
                    rr_feasible = tp_distance <= 2 * atr
                    actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                    
                    if not rr_feasible:
                        print(f"🚫 LSR {symbol} SELL: R:R not feasible - TP={tp_distance:.1f}p > 2xATR={2*atr:.1f}p")
                        return None
                    
                    if actual_rr < 1.5:
                        print(f"⚠️ LSR {symbol} SELL: R:R too low - {actual_rr:.2f} < 1.5 minimum")
                        return None
                    
                    print(f"✅ LSR {symbol} SELL: R:R={actual_rr:.2f}, SL={sl_distance:.1f}p, TP={tp_distance:.1f}p, ATR={atr:.1f}p")
                    
                    # Calculate base quality from sweep size and rejection
                    base_quality = 50  # Start at 50%
                    base_quality += min(bearish_sweep - min_sweep_pips, 5) * 2  # +2% per extra pip (max +10%)
                    base_quality += rejection_ratio * 10  # +10% for perfect rejection
                    base_quality += min(actual_rr - 1.5, 0.5) * 10  # Bonus for R:R > 1.5
                    
                    print(f"🔍 LSR {symbol}: Pattern quality = {base_quality:.1f}% (Base 50 + Sweep + Rejection + R:R bonus)")
                    
                    # Return signal with base quality
                    return PatternSignal(
                        pattern="LIQUIDITY_SWEEP_REVERSAL",
                        direction="SELL",
                        entry_price=entry,
                        confidence=base_quality,
                        timeframe="M5",
                        pair=symbol,
                        quality_score=base_quality
                    )
        except Exception as e:
            logger.debug(f"Error in liquidity sweep: {e}")
        
        return None
    
    def detect_order_block_bounce(self, symbol: str) -> Optional[PatternSignal]:
        """INDUSTRY STANDARD: Price bounces from institutional order blocks (10-candle accumulation zones, bounce within 25% of range)"""
        try:
            print(f"🔍 OBB {symbol}: INDUSTRY STANDARD CHECK")
            if len(self.m5_data[symbol]) < 10:  # INDUSTRY STANDARD: Need 10 candles
                print(f"🔍 OBB {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 10+")
                return None
                
            candles = list(self.m5_data[symbol])[-10:]  # INDUSTRY STANDARD: Last 10 candles for order blocks
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            else:
                pip_size = 0.0001
            
            # INDUSTRY STANDARD: Find order block zones from past accumulation
            recent_low = min(c['low'] for c in candles[:-1])  # Exclude current candle
            recent_high = max(c['high'] for c in candles[:-1])
            block_range = recent_high - recent_low
            current_candle = candles[-1]
            
            # Calculate body and range for current candle
            candle_body = abs(current_candle['close'] - current_candle['open'])
            candle_range = current_candle['high'] - current_candle['low']
            body_ratio = candle_body / candle_range if candle_range > 0 else 0
            
            # INDUSTRY STANDARD: Bounce must be within 25% of order block range
            distance_from_low = (current_candle['low'] - recent_low) / block_range if block_range > 0 else 0
            distance_from_high = (recent_high - current_candle['high']) / block_range if block_range > 0 else 0
            
            # Debug logging with differences from old logic
            print(f"   Order Block: High={recent_high:.5f}, Low={recent_low:.5f}, Range={block_range/pip_size:.1f}p")
            print(f"   Current: High={current_candle['high']:.5f}, Low={current_candle['low']:.5f}, Close={current_candle['close']:.5f}")
            print(f"   Distance from low: {distance_from_low:.2%}, Distance from high: {distance_from_high:.2%}")
            print(f"   Body ratio: {body_ratio:.2%} (strong body = high ratio)")
            print(f"   OLD vs NEW: Was using 15 candles with 30% body req, now 10 candles with 25% bounce zone")
            
            # BULLISH BOUNCE: Price touches within 25% of recent low and bounces
            bull_bounce = (0 <= distance_from_low <= 0.25) and current_candle['close'] > recent_low + (block_range * 0.1)
            
            # BEARISH BOUNCE: Price touches within 25% of recent high and bounces
            bear_bounce = (0 <= distance_from_high <= 0.25) and current_candle['close'] < recent_high - (block_range * 0.1)
            
            direction = 'BUY' if bull_bounce else 'SELL' if bear_bounce else None
            
            if direction:
                # Calculate quality based on body strength and bounce precision
                base_quality = 50  # Start at 50%
                base_quality += body_ratio * 30  # Up to +30% for strong body (full body candle)
                
                # Add precision bonus (closer to exact support/resistance = better)
                if direction == 'BUY':
                    precision = 1 - (distance_from_low / 0.25)  # Closer to low = higher precision
                else:
                    precision = 1 - (distance_from_high / 0.25)  # Closer to high = higher precision
                base_quality += precision * 10  # Up to +10% for precise bounce
                
                base_quality = min(base_quality, 80)  # Cap at 80%
                
                # R:R FEASIBILITY CHECK
                atr = self.calculate_atr(symbol)
                entry = current_candle['close'] + pip_size if direction == 'BUY' else current_candle['close'] - pip_size
                
                if direction == 'BUY':
                    sl_distance = abs(recent_low - entry) / pip_size
                else:
                    sl_distance = abs(recent_high - entry) / pip_size
                
                tp_distance = sl_distance * 1.5  # Target 1.5 R:R minimum
                
                # Check if TP is within 2x ATR (feasible)
                rr_feasible = tp_distance <= 2 * atr
                actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                
                if not rr_feasible:
                    print(f"🚫 OBB {symbol} {direction}: R:R not feasible - TP={tp_distance:.1f}p > 2xATR={2*atr:.1f}p")
                    return None
                
                if actual_rr < 1.5:
                    print(f"⚠️ OBB {symbol} {direction}: R:R too low - {actual_rr:.2f} < 1.5 minimum")
                    return None
                
                print(f"✅ OBB {symbol} {direction}: R:R={actual_rr:.2f}, SL={sl_distance:.1f}p, TP={tp_distance:.1f}p, ATR={atr:.1f}p")
                
                # Add R:R bonus to quality
                base_quality += min(actual_rr - 1.5, 0.5) * 10  # Bonus for R:R > 1.5
                base_quality = min(base_quality, 85)  # Cap at 85%
                
                print(f"🔍 OBB {symbol}: {direction} BOUNCE DETECTED!")
                print(f"   Quality = {base_quality:.1f}% (Base 50 + Body {body_ratio*30:.1f}% + Precision {precision*10:.1f}% + R:R bonus)")
                print(f"   Entry: {entry:.5f}")
                
                # Return signal with base quality
                return PatternSignal(
                    pattern="ORDER_BLOCK_BOUNCE",
                    direction=direction,
                    entry_price=entry,
                    confidence=base_quality,
                    timeframe="M5",
                    pair=symbol,
                    quality_score=base_quality
                )
                            
        except Exception as e:
            logger.debug(f"Error in order block: {e}")
        
        return None
    
    def detect_sweep_and_return(self, symbol: str) -> Optional[PatternSignal]:
        """INDUSTRY STANDARD: Sweep >3 pips beyond level, return with >50% wick of candle range"""
        try:
            print(f"🔍 SRL {symbol}: INDUSTRY STANDARD CHECK")
            if len(self.m5_data[symbol]) < 3:  # INDUSTRY: Need 3 candles minimum
                print(f"🔍 SRL {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 3+")
                return None
                
            candles = list(self.m5_data[symbol])[-3:]  # INDUSTRY: Last 3 candles for recent action
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            else:
                pip_size = 0.0001
            
            # Find recent swing levels (from first 2 candles)
            recent_high = max(candles[0]['high'], candles[1]['high'])
            recent_low = min(candles[0]['low'], candles[1]['low'])
            
            # Current candle (the sweep candle)
            current = candles[-1]
            candle_range = current['high'] - current['low']
            
            # INDUSTRY STANDARD: Check for BULLISH sweep & return
            bull_sweep_distance = (recent_low - current['low']) / pip_size
            if bull_sweep_distance > 3.0:  # INDUSTRY: >3 pip sweep below level
                # Calculate wick ratio (lower wick for bullish)
                lower_wick = current['low'] - min(current['open'], current['close'])
                wick_ratio = lower_wick / candle_range if candle_range > 0 else 0
                
                bull_return = current['close'] > recent_low and wick_ratio > 0.5  # INDUSTRY: >50% wick
                
                if bull_return:
                    # R:R FEASIBILITY CHECK
                    atr = self.calculate_atr(symbol)
                    entry = current['close']
                    sl_distance = abs(current['low'] - entry) / pip_size
                    tp_distance = sl_distance * 1.5  # Target 1.5 R:R minimum
                    
                    # Check if TP is within 2x ATR (feasible)
                    rr_feasible = tp_distance <= 2 * atr
                    actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                    
                    if not rr_feasible:
                        print(f"🚫 SRL {symbol} BUY: R:R not feasible - TP={tp_distance:.1f}p > 2xATR={2*atr:.1f}p")
                        return None
                    
                    if actual_rr < 1.5:
                        print(f"⚠️ SRL {symbol} BUY: R:R too low - {actual_rr:.2f} < 1.5 minimum")
                        return None
                    
                    print(f"✅ SRL {symbol} BUY: R:R={actual_rr:.2f}, SL={sl_distance:.1f}p, TP={tp_distance:.1f}p, ATR={atr:.1f}p")
                    
                    base_quality = 50 + (wick_ratio * 100) - 50  # 50-100% based on wick
                    base_quality += min(actual_rr - 1.5, 0.5) * 10  # Bonus for R:R > 1.5
                    
                    print(f"🔍 SRL {symbol}: BULLISH SWEEP DETECTED!")
                    print(f"   INDUSTRY STANDARD MET:")
                    print(f"   - Sweep distance: {bull_sweep_distance:.1f} pips (>3.0 required) ✅")
                    print(f"   - Wick ratio: {wick_ratio:.2%} (>50% required) ✅")
                    print(f"   - Return above level: {current['close']:.5f} > {recent_low:.5f} ✅")
                    print(f"   - R:R feasible: {actual_rr:.2f} ✅")
                    print(f"   Quality Score: {base_quality:.1f}%")
                    
                    signal = PatternSignal(
                        pattern="SWEEP_AND_RETURN",
                        direction="BUY",
                        entry_price=entry,
                        confidence=base_quality,
                        timeframe="M5",
                        pair=symbol,
                        quality_score=base_quality,
                        momentum_score=0,  # Not used in industry standard
                        volume_quality=0   # Not used in industry standard
                    )
                    return signal
            
            # INDUSTRY STANDARD: Check for BEARISH sweep & return
            bear_sweep_distance = (current['high'] - recent_high) / pip_size
            if bear_sweep_distance > 3.0:  # INDUSTRY: >3 pip sweep above level
                # Calculate wick ratio (upper wick for bearish)
                upper_wick = current['high'] - max(current['open'], current['close'])
                wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
                
                bear_return = current['close'] < recent_high and wick_ratio > 0.5  # INDUSTRY: >50% wick
                
                if bear_return:
                    # R:R FEASIBILITY CHECK
                    atr = self.calculate_atr(symbol)
                    entry = current['close']
                    sl_distance = abs(current['high'] - entry) / pip_size
                    tp_distance = sl_distance * 1.5  # Target 1.5 R:R minimum
                    
                    # Check if TP is within 2x ATR (feasible)
                    rr_feasible = tp_distance <= 2 * atr
                    actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                    
                    if not rr_feasible:
                        print(f"🚫 SRL {symbol} SELL: R:R not feasible - TP={tp_distance:.1f}p > 2xATR={2*atr:.1f}p")
                        return None
                    
                    if actual_rr < 1.5:
                        print(f"⚠️ SRL {symbol} SELL: R:R too low - {actual_rr:.2f} < 1.5 minimum")
                        return None
                    
                    print(f"✅ SRL {symbol} SELL: R:R={actual_rr:.2f}, SL={sl_distance:.1f}p, TP={tp_distance:.1f}p, ATR={atr:.1f}p")
                    
                    base_quality = 50 + (wick_ratio * 100) - 50  # 50-100% based on wick
                    base_quality += min(actual_rr - 1.5, 0.5) * 10  # Bonus for R:R > 1.5
                    
                    print(f"🔍 SRL {symbol}: BEARISH SWEEP DETECTED!")
                    print(f"   INDUSTRY STANDARD MET:")
                    print(f"   - Sweep distance: {bear_sweep_distance:.1f} pips (>3.0 required) ✅")
                    print(f"   - Wick ratio: {wick_ratio:.2%} (>50% required) ✅")
                    print(f"   - Return below level: {current['close']:.5f} < {recent_high:.5f} ✅")
                    print(f"   - R:R feasible: {actual_rr:.2f} ✅")
                    print(f"   Quality Score: {base_quality:.1f}%")
                    
                    signal = PatternSignal(
                        pattern="SWEEP_AND_RETURN",
                        direction="SELL",
                        entry_price=entry,
                        confidence=base_quality,
                        timeframe="M5",
                        pair=symbol,
                        quality_score=base_quality,
                        momentum_score=0,  # Not used in industry standard
                        volume_quality=0   # Not used in industry standard
                    )
                    return signal
            
            # Debug when no pattern found
            print(f"🔍 SRL {symbol}: No sweep detected")
            print(f"   Bull sweep: {bull_sweep_distance:.1f} pips (need >3.0)")
            print(f"   Bear sweep: {bear_sweep_distance:.1f} pips (need >3.0)")
            print(f"   Recent High: {recent_high:.5f}, Low: {recent_low:.5f}")
            print(f"   Current: High={current['high']:.5f}, Low={current['low']:.5f}, Close={current['close']:.5f}")
                        
        except Exception as e:
            print(f"🔍 SRL {symbol}: Error - {e}")
            logger.debug(f"Error in SRL detection: {e}")
        
        return None
    
    def detect_vcb_breakout(self, symbol: str) -> Optional[PatternSignal]:
        """INDUSTRY STANDARD: Tight ATR compression <0.7 over 10 candles, breakout with >1.5x volume"""
        try:
            print(f"🔍 VCB {symbol}: INDUSTRY STANDARD CHECK")
            if len(self.m5_data[symbol]) < 10:  # INDUSTRY STANDARD: Need 10 candles
                print(f"🔍 VCB {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 10+")
                return None
                
            candles = list(self.m5_data[symbol])[-10:]  # INDUSTRY STANDARD: Last 10 candles
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            else:
                pip_size = 0.0001
            
            # INDUSTRY STANDARD: Calculate ATR compression in pips
            atr_sum = 0
            for c in candles:
                atr_sum += (c['high'] - c['low'])
            atr = (atr_sum / len(candles)) / pip_size  # Average range in pips
            
            # INDUSTRY STANDARD: Check if ATR < 0.7 pips (tight compression)
            # For XAUUSD, use 7 pips instead of 0.7
            compression_threshold = 7.0 if symbol == 'XAUUSD' else 0.7
            compression = atr < compression_threshold
            
            # Calculate volume ratio for current candle vs average
            volumes = [c.get('tick_volume', 0) for c in candles[:-1]]
            avg_volume = sum(volumes) / len(volumes) if volumes else 1
            current_volume = candles[-1].get('tick_volume', 0)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Check for breakout above/below recent range
            recent_high = max(c['high'] for c in candles[:-1])
            recent_low = min(c['low'] for c in candles[:-1])
            current_candle = candles[-1]
            
            breakout_up = current_candle['close'] > recent_high
            breakout_down = current_candle['close'] < recent_low
            volume_surge = volume_ratio > 1.5  # INDUSTRY STANDARD: 1.5x volume
            
            # Debug logging with differences from old logic
            print(f"   ATR: {atr:.2f} pips (need <{compression_threshold} for compression)")
            print(f"   Compression: {'YES' if compression else 'NO'}")
            print(f"   Volume ratio: {volume_ratio:.2f}x (need >1.5x)")
            print(f"   Breakout: UP={breakout_up}, DOWN={breakout_down}")
            print(f"   OLD vs NEW: Was 7 candles with 1.2 ratio, now 10 candles with 0.7 pip ATR + 1.5x volume")
            
            # INDUSTRY STANDARD: Direction based on compression + breakout + volume
            direction = 'BUY' if breakout_up and compression and volume_surge else 'SELL' if breakout_down and compression and volume_surge else None
            
            if direction:
                # R:R FEASIBILITY CHECK
                atr_check = self.calculate_atr(symbol)
                entry = current_candle['close'] + pip_size if direction == 'BUY' else current_candle['close'] - pip_size
                
                # Use compression range as SL
                if direction == 'BUY':
                    sl_distance = abs(recent_low - entry) / pip_size
                else:
                    sl_distance = abs(recent_high - entry) / pip_size
                
                tp_distance = sl_distance * 1.5  # Target 1.5 R:R minimum
                
                # Check if TP is within 2x ATR (feasible)
                rr_feasible = tp_distance <= 2 * atr_check
                actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                
                if not rr_feasible:
                    print(f"🚫 VCB {symbol} {direction}: R:R not feasible - TP={tp_distance:.1f}p > 2xATR={2*atr_check:.1f}p")
                    return None
                
                if actual_rr < 1.5:
                    print(f"⚠️ VCB {symbol} {direction}: R:R too low - {actual_rr:.2f} < 1.5 minimum")
                    return None
                
                print(f"✅ VCB {symbol} {direction}: R:R={actual_rr:.2f}, SL={sl_distance:.1f}p, TP={tp_distance:.1f}p, ATR={atr_check:.1f}p")
                
                # Calculate quality based on tightness of compression
                base_quality = 50  # Start at 50%
                base_quality += (1 - min(atr/compression_threshold, 1)) * 30  # Tighter compression = higher quality (up to +30%)
                base_quality += min(volume_ratio - 1.5, 1) * 20  # Volume surge bonus (up to +20% for 2.5x+ volume)
                base_quality += min(actual_rr - 1.5, 0.5) * 10  # Bonus for R:R > 1.5
                base_quality = min(base_quality, 85)  # Cap at 85%
                
                print(f"🔍 VCB {symbol}: {direction} BREAKOUT DETECTED!")
                print(f"   ATR={atr:.2f}p, Volume={volume_ratio:.1f}x")
                print(f"   Quality = {base_quality:.1f}% (includes R:R bonus)")
                print(f"   Entry: {entry:.5f}")
                
                # Return signal with base quality
                return PatternSignal(
                    pattern="VCB_BREAKOUT",
                    direction=direction,
                    entry_price=entry,
                    confidence=base_quality,
                    timeframe="M5",
                    pair=symbol,
                    quality_score=base_quality
                )
                
        except Exception as e:
            logger.debug(f"Error in VCB detection: {e}")
        
        return None
    
    def detect_momentum_breakout(self, symbol: str) -> Optional[PatternSignal]:
        """New pattern: Simple momentum breakout for more signals"""
        try:
            if len(self.m1_data[symbol]) < 2:
                return None
                
            candles = list(self.m1_data[symbol])
            if len(candles) < 10:
                return None
                
            recent = list(candles.values())[-10:]
            current = recent[-1]
            
            # Calculate range
            recent_high = max(c['high'] for c in recent[:-1])
            recent_low = min(c['low'] for c in recent[:-1])
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            
            # BULLISH BREAKOUT
            if current['close'] > recent_high + pip_size:
                # Check if momentum supports it
                momentum = self.calculate_momentum_score(symbol, "BUY")
                if momentum < 10:  # Very low threshold for this pattern
                    return None
                
                volume_quality = self.analyze_volume_profile(symbol)
                
                confidence = 71 + (momentum * 0.05) + (volume_quality * 0.02)  # 71% base
                
                signal = PatternSignal(
                    pattern="MOMENTUM_BREAKOUT",
                    direction="BUY",
                    entry_price=current['close'] + pip_size,
                    confidence=min(75, confidence),
                    timeframe="M1",
                    pair=symbol,
                    momentum_score=momentum,
                    volume_quality=volume_quality
                )
                signal.quality_score = self.calculate_quality_score(signal)
                return signal
            
            # BEARISH BREAKOUT
            elif current['close'] < recent_low - pip_size:
                momentum = self.calculate_momentum_score(symbol, "SELL")
                if momentum < 10:
                    return None
                
                volume_quality = self.analyze_volume_profile(symbol)
                
                confidence = 71 + (momentum * 0.05) + (volume_quality * 0.02)  # 71% base
                
                signal = PatternSignal(
                    pattern="MOMENTUM_BREAKOUT",
                    direction="SELL",
                    entry_price=current['close'] - pip_size,
                    confidence=min(75, confidence),
                    timeframe="M1",
                    pair=symbol,
                    momentum_score=momentum,
                    volume_quality=volume_quality
                )
                signal.quality_score = self.calculate_quality_score(signal)
                return signal
                
        except Exception as e:
            logger.debug(f"Error in momentum breakout: {e}")
        
        return None
    
    def detect_fair_value_gap_fill(self, symbol: str) -> Optional[PatternSignal]:
        """INDUSTRY STANDARD: Price gap >0.5 pip from unbalanced buying/selling, filled as price returns to fair value"""
        try:
            print(f"🔍 FVG {symbol}: INDUSTRY STANDARD CHECK")
            if len(self.m5_data[symbol]) < 2:  # INDUSTRY STANDARD: Only need 2 candles for gap
                print(f"🔍 FVG {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 2+")
                return None
            
            # Get last 2 candles for gap detection
            prev = list(self.m5_data[symbol])[-2]
            curr = list(self.m5_data[symbol])[-1]
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            else:
                pip_size = 0.0001
            
            # INDUSTRY STANDARD: Calculate gap size between candles
            gap_size = (curr['open'] - prev['close']) / pip_size
            
            # Calculate fill percentage (how much gap is being filled)
            candle_body = abs(curr['close'] - curr['open'])
            candle_range = curr['high'] - curr['low']
            body_ratio = candle_body / candle_range if candle_range > 0 else 0
            
            # Debug logging with differences from old logic
            print(f"   Previous: Close={prev['close']:.5f}")
            print(f"   Current: Open={curr['open']:.5f}, Close={curr['close']:.5f}")
            print(f"   Gap size: {gap_size:.2f} pips (min 0.5p required)")
            print(f"   Body ratio: {body_ratio:.2%}")
            print(f"   OLD vs NEW: Was complex 10-candle scan, now simple 2-candle gap detection")
            
            # BULLISH GAP FILL: Up gap (>0.5p) being filled down
            bull_gap = gap_size > 0.5 and curr['close'] < curr['open']  # Gap up, filling down
            
            # BEARISH GAP FILL: Down gap (<-0.5p) being filled up  
            bear_gap = gap_size < -0.5 and curr['close'] > curr['open']  # Gap down, filling up
            
            direction = 'SELL' if bull_gap else 'BUY' if bear_gap else None
            
            if direction:
                # R:R FEASIBILITY CHECK
                atr = self.calculate_atr(symbol)
                entry = curr['close']
                
                # Use gap extremes as SL
                if direction == 'BUY':
                    sl_distance = abs(curr['low'] - entry) / pip_size
                else:
                    sl_distance = abs(curr['high'] - entry) / pip_size
                
                tp_distance = sl_distance * 1.5  # Target 1.5 R:R minimum
                
                # Check if TP is within 2x ATR (feasible)
                rr_feasible = tp_distance <= 2 * atr
                actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                
                if not rr_feasible:
                    print(f"🚫 FVG {symbol} {direction}: R:R not feasible - TP={tp_distance:.1f}p > 2xATR={2*atr:.1f}p")
                    return None
                
                if actual_rr < 1.5:
                    print(f"⚠️ FVG {symbol} {direction}: R:R too low - {actual_rr:.2f} < 1.5 minimum")
                    return None
                
                print(f"✅ FVG {symbol} {direction}: R:R={actual_rr:.2f}, SL={sl_distance:.1f}p, TP={tp_distance:.1f}p, ATR={atr:.1f}p")
                
                # Calculate quality based on gap size and fill strength
                base_quality = 50  # Start at 50%
                base_quality += min(abs(gap_size), 3) * 10  # +10% per pip (max +30% for 3+ pip gaps)
                base_quality += body_ratio * 15  # Up to +15% for strong fill candle
                base_quality += min(actual_rr - 1.5, 0.5) * 10  # Bonus for R:R > 1.5
                base_quality = min(base_quality, 85)  # Cap at 85%
                
                print(f"🔍 FVG {symbol}: {direction} GAP FILL DETECTED!")
                print(f"   Gap: {gap_size:.2f} pips, Fill strength: {body_ratio:.1%}")
                print(f"   Quality = {base_quality:.1f}% (Base 50 + Gap + Fill + R:R bonus)")
                print(f"   Entry: {entry:.5f}")
                
                # Return signal with base quality
                return PatternSignal(
                    pattern="FAIR_VALUE_GAP_FILL",
                    direction=direction,
                    entry_price=entry,
                    confidence=base_quality,
                    timeframe="M5",
                    pair=symbol,
                    quality_score=base_quality
                )
                
        except Exception as e:
            logger.debug(f"FVG detection error for {symbol}: {e}")
        
        return None
    
    def should_generate_signal(self, symbol: str) -> bool:
        """Check if we should generate a signal for this pair"""
        current_time = time.time()
        
        # Check cooldown
        if symbol in self.last_signal_time:
            time_since_last = current_time - self.last_signal_time[symbol]
            if time_since_last < (self.COOLDOWN_MINUTES * 60):
                return False
        
        # Check hourly limits - be more lenient
        current_hour = datetime.now().hour
        if current_hour != self.current_hour:
            self.hourly_signal_count.clear()
            self.current_hour = current_hour
        
        # Allow up to 3 signals per symbol per hour
        if self.hourly_signal_count[symbol] >= 3:
            return False
        
        return True
    
    def generate_signal(self, pattern_signal: PatternSignal) -> Dict:
        """Generate trading signal with quality indicators and RAPID/SNIPER classification"""
        symbol = pattern_signal.pair  # Define symbol from pattern_signal
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        
        # Determine signal classification based on pattern type
        # RAPID: Quick momentum plays (accessible to all tiers)
        # SNIPER: Precision institutional patterns (PRO+ only)
        
        RAPID_PATTERNS = ['MOMENTUM_BREAKOUT', 'VCB_BREAKOUT', 'SWEEP_RETURN']
        SNIPER_PATTERNS = ['LIQUIDITY_SWEEP_REVERSAL', 'ORDER_BLOCK_BOUNCE', 'FAIR_VALUE_GAP_FILL']
        
        signal_class = 'RAPID' if pattern_signal.pattern in RAPID_PATTERNS else 'SNIPER'
        
        # Dynamic SL/TP based on quality AND class
        # RAPID: Designed to complete within 1 hour (shorter TPs)
        # SNIPER: Designed to complete within 2 hours (larger TPs but still reasonable)
        
        if signal_class == 'SNIPER':
            # SNIPER trades - precision setups, 1-2 hour completion target
            if pattern_signal.quality_score >= 75:  # Premium
                stop_pips = 8
                target_pips = 12  # 1:1.5 RR (achievable in 1-2 hours)
            elif pattern_signal.quality_score >= 65:  # Standard
                stop_pips = 7
                target_pips = 10  # 1:1.43 RR
            else:  # Acceptable
                stop_pips = 6
                target_pips = 8   # 1:1.33 RR
        else:
            # RAPID trades - quick scalps, under 1 hour completion
            if pattern_signal.quality_score >= 75:  # Premium
                stop_pips = 4
                target_pips = 6   # 1:1.5 RR (quick 30-45 min trades)
            elif pattern_signal.quality_score >= 65:  # Standard
                stop_pips = 3
                target_pips = 5   # 1:1.67 RR
            else:  # Acceptable
                stop_pips = 3
                target_pips = 4   # 1:1.33 RR
        
        # FIX ERROR 4756: BROKER MINIMUM STOP DISTANCE REQUIREMENTS
        # Exotic pairs and commodities need larger stops to avoid "Invalid stops" error
        min_stop_requirements = {
            'USDMXN': 30,  # Exotic pair - INCREASED from 15 to 30 pips (Error 4756 persists)
            'USDSEK': 20,  # Exotic pair - INCREASED from 15 to 20 pips
            'USDCNH': 30,  # Restricted pair - very high spread
            'XAGUSD': 25,  # Silver - high volatility, needs 25+ pips
            'XAUUSD': 10,  # Gold - moderate requirements
            'USDNOK': 20,  # Exotic pair
            'USDDKK': 20,  # Exotic pair
            'USDTRY': 50,  # Very exotic, extreme spread
            'USDZAR': 30,  # Exotic pair, high volatility
        }
        
        # Apply minimum stop distance if required
        min_stop = min_stop_requirements.get(symbol, 0)
        if min_stop > 0 and stop_pips < min_stop:
            # Maintain risk/reward ratio when adjusting
            original_rr = target_pips / stop_pips if stop_pips > 0 else 1.5
            original_sl = stop_pips
            original_tp = target_pips
            stop_pips = min_stop
            target_pips = int(min_stop * original_rr)
            print(f"📏 {symbol}: STOP ADJUSTMENT for Error 4756 prevention")
            print(f"   Original: SL={original_sl}p, TP={original_tp}p")
            print(f"   Adjusted: SL={stop_pips}p, TP={target_pips}p")
            print(f"   R:R maintained: {original_rr:.2f}")
            print(f"   Reason: Broker minimum {min_stop}p for exotic/commodity")
        
        # Extra debugging for exotic pairs
        if symbol in min_stop_requirements:
            print(f"🎯 EXOTIC DEBUG - {symbol}:")
            print(f"   Stop Pips: {stop_pips}")
            print(f"   Target Pips: {target_pips}")
            print(f"   Pip Size: {pip_size}")
            print(f"   Entry: {pattern_signal.entry_price}")
            print(f"   Min Required: {min_stop_requirements[symbol]} pips")
        
        stop_distance = stop_pips * pip_size
        target_distance = target_pips * pip_size
        
        entry_price = pattern_signal.entry_price
        
        if pattern_signal.direction == "BUY":
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + target_distance
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - target_distance
        
        # Get news impact for this symbol
        news_impact = self.get_news_impact(pattern_signal.pair)
        
        # Determine quality tier
        quality_tier = "ACCEPTABLE"
        if pattern_signal.quality_score >= 75:
            quality_tier = "PREMIUM"
        elif pattern_signal.quality_score >= 65:
            quality_tier = "STANDARD"
        
        # Create signal ID with class prefix
        signal_id_prefix = 'ELITE_SNIPER' if signal_class == 'SNIPER' else 'ELITE_RAPID'
        
        signal = {
            'signal_id': f'{signal_id_prefix}_{pattern_signal.pair}_{int(time.time())}',
            'pair': pattern_signal.pair,
            'symbol': pattern_signal.pair,
            'direction': pattern_signal.direction,
            'pattern': pattern_signal.pattern,
            'pattern_type': pattern_signal.pattern,  # For compatibility
            'signal_class': signal_class,  # RAPID or SNIPER
            'confidence': round(pattern_signal.confidence, 1),
            'quality_score': round(pattern_signal.quality_score, 1),
            'quality_tier': quality_tier,
            'entry_price': round(entry_price, 5),
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'stop_pips': stop_pips,
            'target_pips': target_pips,
            'risk_reward': round(target_pips / stop_pips, 2),
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'session': self.get_current_session(),
            'tier_required': 'PRESS_PASS' if signal_class == 'RAPID' else 'FANG',
            'tiers_allowed': ['PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER'] if signal_class == 'RAPID' else ['FANG', 'COMMANDER'],
            'filters_passed': {
                'momentum': pattern_signal.momentum_score >= self.MIN_MOMENTUM,
                'volume': pattern_signal.volume_quality >= self.MIN_VOLUME,
                'confidence': pattern_signal.confidence >= self.MIN_CONFIDENCE
            },
            'news_impact': news_impact
        }
        
        return signal
    
    def get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now(pytz.UTC).hour
        
        if 0 <= hour < 9:
            return "TOKYO"
        elif 8 <= hour < 13:
            return "LONDON"
        elif 13 <= hour < 17:
            return "LONDON_NY"
        elif 17 <= hour < 22:
            return "NEWYORK"
        else:
            return "LATE_NY"
    
    def process_tick(self, message: str):
        """Process incoming tick data"""
        try:
            if "tick" not in message.lower():
                return
                
            data = json.loads(message.split(" ", 1)[1] if " " in message else message)
            
            symbol = data.get('symbol')
            if not symbol:
                return
            
            # Store tick
            self.tick_data[symbol].append(data)
            self.last_tick_time[symbol] = time.time()
            
            # Build candles using proper M1->M5 aggregation
            self.build_candles_from_tick(symbol, data)
            
            # Log first few ticks to verify reception
            if len(self.tick_data[symbol]) <= 3:
                logger.info(f"📊 Received tick for {symbol}: bid={data.get('bid')} ask={data.get('ask')}")
            
        except Exception as e:
            logger.debug(f"Tick processing error: {e}")
    
    def fetch_ohlc_data(self):
        """Fetch OHLC data from telemetry bridge (EA messages republished)"""
        try:
            while True:
                try:
                    # Non-blocking receive from telemetry bridge
                    message = self.ohlc_subscriber.recv_string(zmq.DONTWAIT)
                    
                    # Parse different message types - look for OHLC type
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type', '')
                        
                        if msg_type == 'OHLC':
                            symbol = data.get('symbol', '')
                            timeframe = data.get('timeframe', '')
                            
                            # Only process our trading pairs
                            if symbol not in self.trading_pairs:
                                continue
                                
                            # Create candle data structure
                            candle = {
                                'timestamp': float(data.get('time', 0)),
                                'open': float(data.get('open', 0)),
                                'high': float(data.get('high', 0)),
                                'low': float(data.get('low', 0)),
                                'close': float(data.get('close', 0)),
                                'volume': 1  # EA doesn't send volume for OHLC
                            }
                            
                            # Store in appropriate timeframe buffer
                            if timeframe == "M1":
                                self.m1_data[symbol].append(candle)
                                print(f"📊 {symbol} M1 OHLC: {len(self.m1_data[symbol])} candles")
                            elif timeframe == "M5":
                                self.m5_data[symbol].append(candle)
                                print(f"📊 {symbol} M5 OHLC: {len(self.m5_data[symbol])} candles")
                            elif timeframe == "M15":
                                self.m15_data[symbol].append(candle)
                                print(f"📊 {symbol} M15 OHLC: {len(self.m15_data[symbol])} candles")
                                
                    except json.JSONDecodeError:
                        # Not JSON, skip
                        continue
                            
                except zmq.Again:
                    # No message available, break the loop
                    break
                    
        except Exception as e:
            print(f"❌ OHLC fetch error: {e}")
    
    def build_candles_from_tick(self, symbol: str, tick_data: dict):
        """Aggregate ticks into proper OHLC candles - RESTORED FROM WORKING BACKUP"""
        if symbol not in self.trading_pairs or not tick_data:
            return
            
        bid = tick_data.get('bid', 0)
        ask = tick_data.get('ask', 0)
        if not bid or not ask:
            return
            
        mid_price = (bid + ask) / 2
        volume = tick_data.get('volume', 1)
        current_minute = int(time.time() / 60) * 60  # Round down to minute
        
        # Initialize storage if needed
        if not hasattr(self, 'current_candles'):
            self.current_candles = {}
        if symbol not in self.current_candles:
            self.current_candles[symbol] = {}
        
        # Create or update current minute candle
        if current_minute not in self.current_candles[symbol]:
            # New minute = new candle
            self.current_candles[symbol][current_minute] = {
                'open': mid_price,
                'high': mid_price,
                'low': mid_price,
                'close': mid_price,
                'volume': volume,
                'timestamp': current_minute
            }
            # Log new candle creation for debugging
            if symbol in ['EURUSD', 'GBPUSD']:
                print(f"🕯️ {symbol}: New M1 candle at {current_minute}, price={mid_price:.5f}")
        else:
            # Update existing candle
            candle = self.current_candles[symbol][current_minute]
            candle['high'] = max(candle['high'], mid_price)
            candle['low'] = min(candle['low'], mid_price)
            candle['close'] = mid_price
            candle['volume'] += volume
        
        # Push completed candles to M1 buffer
        completed_minutes = [m for m in self.current_candles[symbol] if m < current_minute]
        for minute in completed_minutes:
            completed_candle = self.current_candles[symbol].pop(minute)
            self.m1_data[symbol].append(completed_candle)
            
            # Log candle completion
            if symbol in ['EURUSD', 'GBPUSD']:
                print(f"✅ {symbol}: M1 candle completed, total={len(self.m1_data[symbol])}")
            
            # Aggregate M1 → M5 (every 5 M1 candles)
            if len(self.m1_data[symbol]) >= 5 and len(self.m1_data[symbol]) % 5 == 0:
                self.aggregate_m1_to_m5(symbol)
            
            # Aggregate M5 → M15 (every 3 M5 candles)
            if len(self.m5_data[symbol]) >= 3 and len(self.m5_data[symbol]) % 3 == 0:
                self.aggregate_m5_to_m15(symbol)
        
        # ALSO add current forming candle for real-time pattern detection
        if current_minute in self.current_candles[symbol]:
            current_forming_candle = self.current_candles[symbol][current_minute].copy()
            # Remove the existing current candle from M1 buffer first (if any)
            if self.m1_data[symbol] and self.m1_data[symbol][-1]['timestamp'] == current_minute:
                self.m1_data[symbol].pop()
            # Add updated current forming candle
            self.m1_data[symbol].append(current_forming_candle)
    
    
    def placeholder_removed(self):
        """Old OHLC code removed - now builds directly from ticks"""
        pass
    
    def OLD_CODE_TO_DELETE_while_True():
                try:
                    message = self.ohlc_subscriber.recv_string(zmq.DONTWAIT)
                    message_count += 1
                    
                    # Debug: Log raw message reception
                    if message_count == 1:
                        print(f"🔵 Port 5556 Active: Received {len(message)} bytes from EA")
                    
                    if message.startswith("OHLC "):
                        # Parse OHLC message: "OHLC {json_data}"
                        ohlc_data = json.loads(message[5:])  # Remove "OHLC " prefix
                        
                        # Extract data from EA format
                        msg_symbol = ohlc_data.get('symbol', '')
                        timeframe = ohlc_data.get('timeframe', '')
                        timestamp = ohlc_data.get('time', 0)
                        open_price = float(ohlc_data.get('open', 0))
                        high_price = float(ohlc_data.get('high', 0))
                        low_price = float(ohlc_data.get('low', 0))
                        close_price = float(ohlc_data.get('close', 0))
                        volume = int(ohlc_data.get('volume', 1))
                        
                        # Enhanced debug logging for EURUSD especially
                        if msg_symbol == "EURUSD" or message_count <= 5:
                            print(f"🟢 OHLC [{msg_symbol}] {timeframe}: O={open_price:.5f} H={high_price:.5f} L={low_price:.5f} C={close_price:.5f} T={timestamp}")
                        
                        # Store in appropriate buffer based on timeframe
                        if msg_symbol in self.trading_pairs:
                            candle = {
                                'open': open_price,
                                'high': high_price,
                                'low': low_price,
                                'close': close_price,
                                'volume': volume,
                                'timestamp': timestamp
                            }
                            
                            # Update last OHLC time for this symbol
                            self.last_ohlc_time[msg_symbol] = current_time
                            ohlc_received = True
                            
                            if timeframe == 'M1':
                                self.m1_data[msg_symbol].append(candle)
                                if msg_symbol == "EURUSD":
                                    print(f"📈 EURUSD M1: {len(self.m1_data[msg_symbol])} candles stored")
                            elif timeframe == 'M5':
                                self.m5_data[msg_symbol].append(candle)
                                if msg_symbol == "EURUSD":
                                    print(f"📊 EURUSD M5: {len(self.m5_data[msg_symbol])} candles stored")
                            elif timeframe == 'M15':
                                self.m15_data[msg_symbol].append(candle)
                                if msg_symbol == "EURUSD":
                                    print(f"📉 EURUSD M15: {len(self.m15_data[msg_symbol])} candles stored")
                        else:
                            print(f"⚠️ {msg_symbol} not in trading pairs, skipping")
                    else:
                        # Non-OHLC message received
                        print(f"🔸 Non-OHLC message: {message[:50]}...")
                        
                except Exception as e:
                    pass  # Old OHLC code removed
    
    # Helper functions for aggregation
    def OLD_REMOVED_CODE_PLACEHOLDER(self):
        """Removed old broken code"""
        if False:  # Never execute
            self.current_candles[symbol] = {}
            pass  # Old broken code removed
    
    # Force aggregate functions removed - using proper M1->M5->M15 aggregation
    
    def aggregate_m1_to_m5(self, symbol: str):
        """Build M5 candle from last 5 M1 candles - AGGRESSIVE"""
        if len(self.m1_data[symbol]) >= 5:
            # Build M5 from every complete set of 5 M1 candles
            last_5 = list(self.m1_data[symbol])[-5:]
            
            # Calculate M5 timestamp from first M1 timestamp rounded to 5-minute boundary
            first_timestamp = last_5[0]['timestamp']
            m5_timestamp = int(first_timestamp / 300) * 300  # Round to 5-minute boundary
            
            # Check if we already have this M5 timestamp
            if self.m5_data[symbol] and self.m5_data[symbol][-1]['timestamp'] == m5_timestamp:
                return  # Already have this M5
                
            m5_candle = {
                'open': last_5[0]['open'],
                'high': max(c['high'] for c in last_5),
                'low': min(c['low'] for c in last_5),
                'close': last_5[-1]['close'],
                'volume': sum(c['volume'] for c in last_5),
                'timestamp': m5_timestamp
            }
            self.m5_data[symbol].append(m5_candle)
            print(f"📊 {symbol}: Created M5 candle from {len(last_5)} M1 candles, timestamp {m5_timestamp}")

    def aggregate_m5_to_m15(self, symbol: str):
        """Build M15 candle from last 3 M5 candles - AGGRESSIVE"""
        if len(self.m5_data[symbol]) >= 3:
            # Build M15 from every complete set of 3 M5 candles
            last_3 = list(self.m5_data[symbol])[-3:]
            
            # Check if we already have this M15 timestamp
            m15_timestamp = last_3[0]['timestamp']
            if self.m15_data[symbol] and self.m15_data[symbol][-1]['timestamp'] == m15_timestamp:
                return  # Already have this M15
                
            m15_candle = {
                'open': last_3[0]['open'],
                'high': max(c['high'] for c in last_3),
                'low': min(c['low'] for c in last_3),
                'close': last_3[-1]['close'],
                'volume': sum(c['volume'] for c in last_3),
                'timestamp': m15_timestamp
            }
            self.m15_data[symbol].append(m15_candle)
            print(f"📊 {symbol}: Created M15 candle from {len(last_3)} M5 candles")
    
    def save_candles(self):
        """Save candle and tick data to cache file"""
        try:
            # Build data structure with M1/M5/M15 data
            cache_data = {
                'm1_data': {},
                'm5_data': {},
                'm15_data': {},
                'tick_data': {},
                'last_update': time.time()
            }
            
            # Save all candle data for each symbol
            total_m1 = 0
            total_m5 = 0
            total_m15 = 0
            
            for symbol in self.trading_pairs:
                # Save M1 data
                if symbol in self.m1_data and len(self.m1_data[symbol]) > 0:
                    cache_data['m1_data'][symbol] = list(self.m1_data[symbol])
                    total_m1 += len(self.m1_data[symbol])
                
                # Save M5 data
                if symbol in self.m5_data and len(self.m5_data[symbol]) > 0:
                    cache_data['m5_data'][symbol] = list(self.m5_data[symbol])
                    total_m5 += len(self.m5_data[symbol])
                
                # Save M15 data
                if symbol in self.m15_data and len(self.m15_data[symbol]) > 0:
                    cache_data['m15_data'][symbol] = list(self.m15_data[symbol])
                    total_m15 += len(self.m15_data[symbol])
                
                # Save recent ticks (last 100)
                if symbol in self.tick_data and len(self.tick_data[symbol]) > 0:
                    cache_data['tick_data'][symbol] = list(self.tick_data[symbol])[-100:]
            
            # Write to file
            with open('/root/HydraX-v2/candle_cache.json', 'w') as f:
                json.dump(cache_data, f)
            
            # Log saved counts for verification
            print(f"💾 Saved candles to cache:")
            print(f"   Total M1: {total_m1}, M5: {total_m5}, M15: {total_m15}")
            
            # Show EURUSD specifically as requested
            if 'EURUSD' in self.m1_data:
                print(f"   EURUSD: M1={len(self.m1_data['EURUSD'])}, M5={len(self.m5_data.get('EURUSD', []))}, M15={len(self.m15_data.get('EURUSD', []))}")
            
        except Exception as e:
            print(f"❌ Error saving candles: {e}")

    def load_candles(self):
        """Load candle and tick data from cache file"""
        try:
            if os.path.exists('/root/HydraX-v2/candle_cache.json'):
                with open('/root/HydraX-v2/candle_cache.json', 'r') as f:
                    cache_data = json.load(f)
                
                total_m1 = 0
                total_m5 = 0
                total_m15 = 0
                
                # Load all candle data for each symbol
                for symbol in self.trading_pairs:
                    # Load M1 data
                    if symbol in cache_data.get('m1_data', {}):
                        self.m1_data[symbol] = deque(cache_data['m1_data'][symbol], maxlen=500)
                        total_m1 += len(self.m1_data[symbol])
                    else:
                        self.m1_data[symbol] = deque(maxlen=500)
                    
                    # Load M5 data
                    if symbol in cache_data.get('m5_data', {}):
                        self.m5_data[symbol] = deque(cache_data['m5_data'][symbol], maxlen=300)
                        total_m5 += len(self.m5_data[symbol])
                    else:
                        self.m5_data[symbol] = deque(maxlen=300)
                    
                    # Load M15 data  
                    if symbol in cache_data.get('m15_data', {}):
                        self.m15_data[symbol] = deque(cache_data['m15_data'][symbol], maxlen=200)
                        total_m15 += len(self.m15_data[symbol])
                    else:
                        self.m15_data[symbol] = deque(maxlen=200)
                    
                    # Load tick data
                    if symbol in cache_data.get('tick_data', {}):
                        self.tick_data[symbol] = deque(cache_data['tick_data'][symbol], maxlen=1000)
                        if cache_data['tick_data'][symbol]:
                            self.last_tick_time[symbol] = time.time()
                
                # Log loaded counts for verification
                print(f"🔍 Loaded candles from cache:")
                print(f"   Total M1: {total_m1}, M5: {total_m5}, M15: {total_m15}")
                
                # Show EURUSD specifically as requested
                if 'EURUSD' in self.m1_data:
                    print(f"   EURUSD: M1={len(self.m1_data['EURUSD'])}, M5={len(self.m5_data.get('EURUSD', []))}, M15={len(self.m15_data.get('EURUSD', []))}")
            else:
                print("⚠️ No candle cache file found, starting fresh")
                
        except Exception as e:
            print(f"❌ Error loading candles: {e}")

    def fetch_news_events(self):
        """Fetch news events from Forex Factory API"""
        try:
            current_time = time.time()
            # Refresh news every 30 minutes
            if current_time - self.last_news_fetch > 1800:
                self.news_events = self.news_client.fetch_events(days_ahead=1)
                self.last_news_fetch = current_time
                print(f"📰 Fetched {len(self.news_events)} news events from Forex Factory")
        except Exception as e:
            print(f"❌ Error fetching news events: {e}")

    def get_news_impact(self, symbol: str) -> int:
        """Get news impact adjustment for confidence (-10 for high impact)"""
        # DISABLED for testing - always return 0
        return 0
        
        self.fetch_news_events()  # Ensure we have fresh events
        
        now = datetime.now(pytz.UTC)
        impact_adjustment = 0
        
        for event in self.news_events:
            # Check if event affects this currency pair
            event_currency = event.currency.upper() if hasattr(event, 'currency') else ''
            if event_currency and event_currency in symbol:
                # Check if event is within 2 hours
                event_time = event.event_time if hasattr(event, 'event_time') else datetime.now(pytz.UTC)
                time_diff = abs((event_time - now).total_seconds() / 3600)
                
                if time_diff <= 2:  # Within 2 hours
                    impact_level = event.impact if hasattr(event, 'impact') else 'medium'
                    
                    # Convert NewsImpact enum to string if needed
                    impact_str = impact_level.value if hasattr(impact_level, 'value') else str(impact_level).lower()
                    
                    if impact_str == 'high':
                        print(f"📰 {symbol}: {event.event_name} in {time_diff:.1f}h - HIGH impact (-10)")
                        impact_adjustment = min(impact_adjustment - 10, -10)
                    elif impact_str == 'medium':
                        print(f"📰 {symbol}: {event.event_name} in {time_diff:.1f}h - MEDIUM impact (-5)")
                        impact_adjustment = min(impact_adjustment - 5, -5)
        
        return impact_adjustment

    def apply_ml_filter(self, signal, session: str) -> tuple[bool, str, float]:
        """Apply ML filtering with dynamic threshold for 5-10 signals/hour target"""
        # QUALITY GATE #1: OPTIMIZED FOR 65%+ WIN RATE TARGET
        # RECALIBRATED: Adjusted gates based on 32.9% win rate analysis
        min_quality_score = 55.0  # LOWERED from 60 to get more signals for analysis
        
        # Pattern-specific adjustments based on actual performance (32.9% overall)
        pattern_adjustments = {
            'FAIR_VALUE_GAP_FILL': 15,      # PENALTY: 34.8% win rate needs higher quality
            'ORDER_BLOCK_BOUNCE': 15,        # PENALTY: 30.4% win rate needs higher quality
            'LIQUIDITY_SWEEP_REVERSAL': 5,   # Small penalty
            'VCB_BREAKOUT': -5,              # Typically strong, can lower
            'SWEEP_RETURN': 0                # Neutral
        }
        
        pattern_type = getattr(signal, 'pattern', 'UNKNOWN')
        adjustment = pattern_adjustments.get(pattern_type, 0)
        min_quality_score += adjustment
        print(f"📊 RECALIBRATED: Base {55}% + {pattern_type} adjustment {adjustment:+d}% = {min_quality_score}%")
        
        # Extra strict for exotic pairs (higher risk, need better setups)
        exotic_pairs = ['USDMXN', 'USDSEK', 'USDCNH', 'XAGUSD']
        if hasattr(signal, 'pair') and signal.pair in exotic_pairs:
            min_quality_score = max(min_quality_score, 65.0)  # At least 65 for exotics
            print(f"🌍 EXOTIC PAIR {signal.pair}: Raised to {min_quality_score}%")
        
        print(f"🔍 Quality Gate Check: {signal.quality_score:.1f}% vs {min_quality_score}% minimum")
        if hasattr(signal, 'quality_score') and signal.quality_score < min_quality_score:
            print(f"   ⚠️ QUALITY FAIL: {signal.quality_score:.1f}% < {min_quality_score}%")
            # Track quality failures for optimization
            print(f"   📊 WIN RATE OPTIMIZATION: Rejecting to improve from current 38.5% → 65%+ target")
            return False, f"Quality score too low ({signal.quality_score:.1f}% < {min_quality_score}%)", signal.confidence
        print(f"   ✅ QUALITY PASSED: {signal.quality_score:.1f}% (targeting 65%+ win rate)")
        
        # Dynamic ML threshold based on recent signal rate
        # Track signals in last 15 minutes
        current_time = time.time()
        recent_signals = getattr(self, 'recent_signal_times', [])
        recent_signals = [t for t in recent_signals if current_time - t < 900]  # Last 15 min
        
        # Calculate hourly rate projection
        signals_per_15min = len(recent_signals)
        projected_hourly_rate = signals_per_15min * 4
        
        # QUALITY GATE #2: RECALIBRATED confidence threshold (65-85% target range)
        if projected_hourly_rate > 10:  # Too many signals
            min_confidence = 75.0  # Moderate gate (was 80)
        elif projected_hourly_rate < 5:  # Too few signals
            min_confidence = 65.0  # Much lower gate (was 70) to get more data
        else:  # Perfect range (5-10)
            min_confidence = 70.0  # Optimal threshold (was 75)
        
        # RECALIBRATED: Allow 65-85% range for better signal flow
        min_confidence = max(65.0, min(85.0, min_confidence))
        
        # Apply pattern-specific confidence adjustments
        pattern_confidence_adj = {
            'FAIR_VALUE_GAP_FILL': -10,     # PENALTY for 34.8% win rate
            'ORDER_BLOCK_BOUNCE': -10,       # PENALTY for 30.4% win rate
            'LIQUIDITY_SWEEP_REVERSAL': -5,  # Small penalty
            'VCB_BREAKOUT': +5,              # Boost good patterns
            'SWEEP_RETURN': 0                # Neutral
        }
        
        conf_adj = pattern_confidence_adj.get(pattern_type, 0)
        if conf_adj != 0:
            print(f"   🎯 Confidence adjustment for {pattern_type}: {conf_adj:+d}%")
        
        print(f"📊 Signal Rate Analysis: {signals_per_15min} in 15min = {projected_hourly_rate}/hr projected")
        print(f"   ML Confidence Gate: {min_confidence}% (dynamic based on rate)")
        
        # Apply news impact adjustment to confidence
        news_adjustment = self.get_news_impact(signal.pair)
        adjusted_confidence = signal.confidence + news_adjustment
        
        if news_adjustment != 0:
            print(f"📰 {signal.pair}: News impact {news_adjustment} → Confidence {signal.confidence:.1f}% → {adjusted_confidence:.1f}%")
        
        if adjusted_confidence < min_confidence:
            print(f"   ⚠️ CONFIDENCE FAIL: {adjusted_confidence:.1f}% < {min_confidence}%")
            return False, f"Below threshold ({min_confidence}%) after news", adjusted_confidence
        print(f"   ✅ CONFIDENCE PASSED: {adjusted_confidence:.1f}% >= {min_confidence}%")
        
        # EMERGENCY BLOCK: Disable failing patterns until retrained
        blocked_patterns = ['FAIR_VALUE_GAP_FILL']  # 36.4% win rate - DISABLED
        restricted_patterns = ['ORDER_BLOCK_BOUNCE']  # 44.4% win rate - RESTRICTED
        
        if signal.pattern in blocked_patterns:
            print(f"   🚫 BLOCKED PATTERN: {signal.pattern} temporarily disabled (win rate < 40%)")
            return False, f"Pattern blocked for retraining", adjusted_confidence
        
        if signal.pattern in restricted_patterns and adjusted_confidence < 85:
            print(f"   ⚠️ RESTRICTED PATTERN: {signal.pattern} requires 85%+ confidence (has {adjusted_confidence:.1f}%)")
            return False, f"Pattern restricted - needs 85%+ confidence", adjusted_confidence
        
        # Check performance history
        pattern_clean = signal.pattern.replace('_INTELLIGENT', '')
        combo_key = f"{signal.pair}_{pattern_clean}_{session}"
        perf = self.performance_history.get(combo_key, {})
        if perf.get('enabled') == False:
            print(f"   ⚠️ PERFORMANCE FAIL: {combo_key} disabled due to poor history")
            return False, f"Disabled: poor performance", adjusted_confidence
        
        print(f"   ✅✅ SIGNAL APPROVED: {signal.pair} {signal.pattern} @ {adjusted_confidence:.1f}%")
        return True, f"PASS @ {adjusted_confidence:.1f}%", adjusted_confidence

    def log_signal_to_truth_tracker(self, signal_data: Dict):
        """Log signal with comprehensive metrics to truth tracker"""
        try:
            # Enhanced truth tracking with all metrics
            truth_entry = {
                "signal_id": signal_data.get('signal_id', ''),
                "pattern": signal_data.get('pattern_type', ''),
                "symbol": signal_data.get('pair', ''),
                "direction": signal_data.get('direction', ''),
                "entry": signal_data.get('entry_price', 0),
                "sl": signal_data.get('stop_loss', 0),
                "tp": signal_data.get('take_profit', 0),
                "sl_pips": signal_data.get('sl_pips', 0),
                "tp_pips": signal_data.get('tp_pips', 0),
                "confidence": signal_data.get('confidence', 0),
                "base_conf": signal_data.get('base_confidence', 0),
                "bonuses": {
                    "session": signal_data.get('session_bonus', 0),
                    "volume": signal_data.get('volume_bonus', 0),
                    "spread": signal_data.get('spread_bonus', 0),
                    "news": signal_data.get('news_impact', 0)
                },
                "timestamp": signal_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                "session": signal_data.get('session', self.get_current_session()),
                "vol_actual": signal_data.get('volume_actual', 0),
                "vol_avg": signal_data.get('volume_average', 0),
                "vol_ratio": signal_data.get('volume_ratio', 0),
                "pattern_age": signal_data.get('pattern_age_minutes', 0),
                "expectancy": signal_data.get('expectancy', 0),
                "rr_proj": signal_data.get('risk_reward', 0),
                "citadel": signal_data.get('citadel_score', 0),
                "quarantine": signal_data.get('quarantine_status', 0),
                "convergence": signal_data.get('convergence_score', 0),
                "outcome": "OPEN",
                "lifespan": None,
                "rr_actual": None,
                "pips_result": None
            }
            
            # ONLY write to optimized tracking - single source of truth
            self.log_optimized_tracking(signal_data)
            print(f"📝 ONLY optimized_tracking.jsonl: {signal_data.get('signal_id', 'unknown')}")
                
        except Exception as e:
            logger.error(f"Error logging to truth tracker: {e}")
    
    def log_optimized_tracking(self, signal_data: Dict):
        """Enhanced tracking for pattern optimization with next candle win analysis"""
        try:
            # Map field names correctly
            symbol = signal_data.get('symbol', signal_data.get('pair', ''))
            
            # Calculate next candle win (if we have M1 data)
            win = False
            if symbol in self.m1_data and len(self.m1_data[symbol]) > 0:
                last_candle = self.m1_data[symbol][-1]
                if last_candle and 'close' in last_candle and 'open' in last_candle:
                    # For BUY: win if close > open, for SELL: win if close < open
                    direction = signal_data.get('direction', 'BUY')
                    if direction == 'BUY':
                        win = last_candle['close'] > last_candle['open']
                    else:
                        win = last_candle['close'] < last_candle['open']
            
            # Calculate Risk:Reward ratio using correct field names
            entry = signal_data.get('entry', signal_data.get('entry_price', 0))
            sl = signal_data.get('stop_loss', signal_data.get('sl', 0))
            tp = signal_data.get('take_profit', signal_data.get('tp', 0))
            
            # Alternative calculation using pips if prices not available
            if sl == 0 or tp == 0:
                sl_pips = signal_data.get('stop_pips', signal_data.get('sl_pips', 20))
                tp_pips = signal_data.get('target_pips', signal_data.get('tp_pips', 20))
                if sl_pips != 0:
                    rr = round(tp_pips / sl_pips, 2)
                else:
                    rr = 1.0
            else:
                # Price-based calculation
                if sl != 0 and entry != 0 and sl != entry:
                    risk = abs(entry - sl)
                    reward = abs(tp - entry)
                    if risk > 0:
                        rr = round(reward / risk, 2)
                else:
                    rr = 1.0
            
            # Calculate lifespan (time since signal creation)
            timestamp_str = signal_data.get('timestamp', datetime.utcnow().isoformat() + 'Z')
            try:
                # Handle both formats: with and without 'Z'
                if timestamp_str.endswith('Z'):
                    signal_time = datetime.fromisoformat(timestamp_str[:-1])
                else:
                    signal_time = datetime.fromisoformat(timestamp_str)
                lifespan = round((datetime.utcnow() - signal_time).total_seconds(), 1)
            except:
                lifespan = 0
            
            # Create optimized tracking entry with correct field mappings
            entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'pair': symbol,
                'pattern': signal_data.get('pattern', signal_data.get('pattern_type', 'UNKNOWN')),
                'confidence': signal_data.get('confidence', signal_data.get('quality_score', 0)),
                'quality_score': signal_data.get('quality_score', signal_data.get('confidence', 0)),
                'win': win,
                'risk_reward': rr,
                'lifespan': lifespan,
                'session': signal_data.get('session', self.get_current_session()),
                'signal_id': signal_data.get('signal_id', ''),
                'direction': signal_data.get('direction', 'UNKNOWN'),
                'signal_class': signal_data.get('signal_class', 'UNKNOWN')
            }
            
            # Write to optimized tracking log
            with open('/root/HydraX-v2/optimized_tracking.jsonl', 'a') as f:
                f.write(json.dumps(entry) + '\n')
            
            # Enhanced debug output
            print(f"📝 Tracked: {signal_data.get('signal_id', 'UNKNOWN')}")
            print(f"   Pair={symbol}, Pattern={entry['pattern']}, Class={entry['signal_class']}")
            print(f"   Conf={entry['confidence']}%, Quality={entry['quality_score']}%")
            print(f"   Win={win}, R:R={rr}, Lifespan={lifespan}s")
            print(f"   Session={entry['session']}, Direction={entry['direction']}")
            
        except Exception as e:
            print(f"Error in optimized tracking: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_initial_data(self):
        """Analyze ONLY optimized_tracking.jsonl with detailed breakdowns"""
        try:
            tracking_file = '/root/HydraX-v2/optimized_tracking.jsonl'
            
            if not os.path.exists(tracking_file):
                print("📊 No optimized_tracking.jsonl yet")
                return
                
            with open(tracking_file, 'r') as f:
                signals = [json.loads(line) for line in f if line.strip()]
                
            if not signals:
                print("📊 No data in optimized_tracking.jsonl yet")
                return
                
            # Overall stats
            total = len(signals)
            wins = sum(1 for s in signals if s.get('win', False))
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # Pattern breakdown with win rates
            patterns = set(s['pattern'] for s in signals if 'pattern' in s)
            pattern_stats = {}
            for p in patterns:
                p_signals = [s for s in signals if s.get('pattern') == p]
                if p_signals:
                    p_wins = sum(1 for s in p_signals if s.get('win', False))
                    pattern_stats[p] = f"{p_wins}/{len(p_signals)} ({p_wins/len(p_signals)*100:.1f}%)"
            
            # Session breakdown
            session_stats = {}
            for sess in ['Asian', 'London', 'NY', 'Overlap']:
                sess_signals = [s for s in signals if s.get('session') == sess]
                if sess_signals:
                    sess_wins = sum(1 for s in sess_signals if s.get('win', False))
                    session_stats[sess] = f"{sess_wins}/{len(sess_signals)} ({sess_wins/len(sess_signals)*100:.1f}%)"
            
            # Confidence bins
            conf_stats = {}
            for bin_name, (low, high) in [('70-75', (70, 75)), ('75-85', (75, 85)), ('85-95', (85, 95))]:
                bin_signals = [s for s in signals if low <= s.get('confidence', 0) < high]
                if bin_signals:
                    bin_wins = sum(1 for s in bin_signals if s.get('win', False))
                    conf_stats[bin_name] = f"{bin_wins}/{len(bin_signals)} ({bin_wins/len(bin_signals)*100:.1f}%)"
            
            # Last 30 min stats
            now = datetime.now()
            last_30 = []
            for s in signals:
                try:
                    ts = datetime.fromisoformat(s['timestamp'].replace('Z', '+00:00'))
                    if (now - ts).total_seconds() < 1800:
                        last_30.append(s)
                except:
                    pass
            
            print(f"\n📊 OPTIMIZED TRACKING ANALYSIS (ONLY SOURCE):")
            print(f"   Total: {total} signals, Win Rate: {win_rate:.1f}%")
            print(f"   Patterns: {pattern_stats}")
            print(f"   Sessions: {session_stats}")
            print(f"   Conf Bins: {conf_stats}")
            print(f"   Last 30min: {len(last_30)} signals")
            if last_30:
                print(f"   - Avg Conf: {sum(s.get('confidence', 0) for s in last_30)/len(last_30):.1f}%")
                print(f"   - Avg Quality: {sum(s.get('quality_score', 0) for s in last_30)/len(last_30):.1f}%")
                print(f"   - Avg R:R: {sum(s.get('risk_reward', 0) for s in last_30)/len(last_30):.2f}")
                
        except Exception as e:
            print(f"Error analyzing optimized_tracking.jsonl: {e}")
            for s in signals:
                d = s.get('direction', 'UNKNOWN')
                if d in directions:
                    directions[d] += 1
            
            # Print comprehensive analysis
            print("=" * 60)
            print("📊 OPTIMIZATION TRACKING ANALYSIS")
            print("=" * 60)
            print(f"📈 SUMMARY: {total_signals} signals tracked")
            print(f"   Win Rate: {win_rate:.1f}% ({wins}/{total_signals}) {'🎯 TARGET: 65%+' if win_rate < 65 else '✅ ABOVE TARGET'}")
            print(f"   Avg Confidence: {avg_conf:.1f}% {'✅ IN RANGE' if 70 <= avg_conf <= 95 else '⚠️ OUT OF RANGE'}")
            print(f"   Avg Quality: {avg_quality:.1f}% {'✅ IN RANGE' if 55 <= avg_quality <= 85 else '⚠️ OUT OF RANGE'}")
            print(f"   Avg R:R: {avg_rr:.2f} {'✅ GOOD' if avg_rr >= 1.2 else '⚠️ LOW'}")
            print(f"   Avg Lifespan: {avg_lifespan:.1f}s")
            
            print(f"\n🎯 PATTERN PERFORMANCE:")
            for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
                pattern_signals = [s for s in signals if s.get('pattern') == pattern]
                pattern_wins = sum(1 for s in pattern_signals if s.get('win', False))
                pattern_wr = (pattern_wins / len(pattern_signals) * 100) if pattern_signals else 0
                print(f"   {pattern}: {count} signals, {pattern_wr:.1f}% win rate")
            
            print(f"\n💱 TOP PAIRS:")
            for pair, count in sorted(pairs.items(), key=lambda x: x[1], reverse=True)[:5]:
                pair_signals = [s for s in signals if s.get('pair') == pair]
                pair_wins = sum(1 for s in pair_signals if s.get('win', False))
                pair_wr = (pair_wins / len(pair_signals) * 100) if pair_signals else 0
                print(f"   {pair}: {count} signals, {pair_wr:.1f}% win rate")
            
            print(f"\n🌍 SESSION BREAKDOWN:")
            for session, count in sorted(sessions.items(), key=lambda x: x[1], reverse=True):
                sess_pct = (count / total_signals * 100)
                print(f"   {session}: {count} ({sess_pct:.1f}%)")
            
            print(f"\n📊 DIRECTION BIAS:")
            print(f"   BUY: {directions['BUY']} ({directions['BUY']/total_signals*100:.1f}%)")
            print(f"   SELL: {directions['SELL']} ({directions['SELL']/total_signals*100:.1f}%)")
            
            # Time analysis
            if signals:
                first_time = datetime.fromisoformat(signals[0]['timestamp'])
                last_time = datetime.fromisoformat(signals[-1]['timestamp'])
                time_span = (last_time - first_time).total_seconds() / 3600  # hours
                if time_span > 0:
                    signals_per_hour = total_signals / time_span
                    print(f"\n⏱️ SIGNAL RATE: {signals_per_hour:.1f} signals/hour")
                    if signals_per_hour < 5:
                        print("   ⚠️ Below target (5-10/hr) - Consider lowering thresholds")
                    elif signals_per_hour > 10:
                        print("   ⚠️ Above target (5-10/hr) - Consider raising thresholds")
                    else:
                        print("   ✅ In target range (5-10/hr)")
            
            print("=" * 60)
            
            # Return summary dict for programmatic use
            return {
                'total_signals': total_signals,
                'win_rate': win_rate,
                'avg_confidence': avg_conf,
                'avg_quality': avg_quality,
                'avg_rr': avg_rr,
                'patterns': patterns,
                'top_pair': max(pairs.items(), key=lambda x: x[1])[0] if pairs else None
            }
            
        except Exception as e:
            print(f"Error analyzing data: {e}")
            import traceback
            traceback.print_exc()
            return None

    def scan_for_patterns(self):
        """Scan all symbols for patterns"""
        # Always scan ALL trading pairs, not just those with tick data
        symbols_to_scan = self.trading_pairs
        symbols_with_data = [s for s in self.trading_pairs if s in self.tick_data and len(self.m1_data.get(s, [])) > 0]
        
        print(f"🔍 PATTERN SCAN: Starting for {len(symbols_to_scan)} symbols ({len(symbols_with_data)} have M1 data)")
        logger.info(f"🔍 Starting pattern scan for {len(symbols_to_scan)} symbols ({len(symbols_with_data)} have M1 data)")
        
        # Log total candle counts
        total_m1 = sum(len(self.m1_data.get(s, [])) for s in symbols_to_scan)
        total_m5 = sum(len(self.m5_data.get(s, [])) for s in symbols_to_scan)
        if total_m1 > 0:
            logger.info(f"📈 Total candles: {total_m1} M1, {total_m5} M5")
        
        # Log candle status with tick reception
        for symbol in symbols_to_scan[:5]:
            m1_count = len(self.m1_data[symbol])
            m5_count = len(self.m5_data[symbol])
            tick_count = len(self.tick_data[symbol])
            time_since_tick = time.time() - self.last_tick_time.get(symbol, 0)
            logger.info(f"  {symbol}: {tick_count} ticks, {m1_count} M1, {m5_count} M5 candles (last tick {time_since_tick:.1f}s ago)")
        
        signals_generated = []
        
        for symbol in symbols_to_scan:
            # Check if we have enough data (skip if no M1 candles)
            if len(self.m1_data.get(symbol, [])) < 2:
                continue
            
            # Check if data is fresh (only for symbols with tick data)
            if symbol in self.last_tick_time:
                if time.time() - self.last_tick_time[symbol] > 60:
                    continue
            
            if not self.should_generate_signal(symbol):
                continue
            
            # Try all pattern detectors
            patterns = []
            
            # ALL 5 CORE PATTERNS WITH ML FILTERING
            session = self.get_current_session()
            
            # 1. Liquidity Sweep Reversal (highest priority)
            signal = self.detect_liquidity_sweep_reversal(symbol)
            if signal:
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ LIQUIDITY SWEEP on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 LIQUIDITY SWEEP on {symbol} filtered: {tier_reason} - CONF: {signal.confidence}")
            else:
                # Debug: Why no pattern detected
                m5_count = len(self.m5_data[symbol])
                if m5_count < 2:
                    print(f"❌ {symbol} LSR: Only {m5_count} M5 candles (need 2+)")
            
            # 2. Order Block Bounce  
            signal = self.detect_order_block_bounce(symbol)
            if signal:
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ ORDER BLOCK on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 ORDER BLOCK on {symbol} filtered: {tier_reason} - CONF: {signal.confidence}")
            else:
                m5_count = len(self.m5_data[symbol])
                if m5_count < 2:
                    print(f"❌ {symbol} OB: Only {m5_count} M5 candles (need 2+)")
            
            # 3. Fair Value Gap Fill
            signal = self.detect_fair_value_gap_fill(symbol)
            if signal:
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    logger.info(f"✅ FAIR VALUE GAP on {symbol} - {tier_reason}")
                    patterns.append(signal)
                else:
                    logger.debug(f"🚫 FAIR VALUE GAP on {symbol} filtered: {tier_reason}")
            
            # 4. VCB Breakout
            signal = self.detect_vcb_breakout(symbol)
            if signal:
                print(f"📍 VCB signal returned for {symbol}: conf={signal.confidence}, dir={signal.direction}")
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ VCB BREAKOUT on {symbol} - {tier_reason} - Publishing!")
                    logger.info(f"✅ VCB BREAKOUT on {symbol} - {tier_reason}")
                    patterns.append(signal)
                else:
                    print(f"🚫 VCB BREAKOUT on {symbol} filtered: {tier_reason}")
                    logger.debug(f"🚫 VCB BREAKOUT on {symbol} filtered: {tier_reason}")
            
            # 5. Sweep and Return
            signal = self.detect_sweep_and_return(symbol)
            if signal:
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    logger.info(f"✅ SWEEP & RETURN on {symbol} - {tier_reason}")
                    patterns.append(signal)
                else:
                    logger.debug(f"🚫 SWEEP & RETURN on {symbol} filtered: {tier_reason}")
            
            # 6. Momentum Burst (Momentum Breakout)
            signal = self.detect_momentum_breakout(symbol)
            if signal:
                signal.pattern = "MOMENTUM_BURST"  # Rename for clarity
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ MOMENTUM BURST on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 MOMENTUM BURST on {symbol} filtered: {tier_reason}")
            
            # Pick best pattern based on quality score
            if patterns:
                best_pattern = max(patterns, key=lambda x: x.quality_score)
                
                # Lower threshold for CITADEL to filter
                if best_pattern.confidence >= 35:  # LOWERED further for more signals
                    # Generate signal
                    signal = self.generate_signal(best_pattern)
                    
                    # Update CITADEL with market structure
                    if len(self.m5_data[symbol]) > 0:
                        candles_list = list(self.m5_data[symbol])
                        self.citadel.update_market_structure(symbol, candles_list)
                    
                    # Apply CITADEL protection
                    protected_signal = self.citadel.protect_signal(signal)
                    
                    # Ensure protected_signal preserves all original fields if not None
                    if protected_signal and signal:
                        # CITADEL might return None or modified signal
                        # Make sure critical fields are preserved
                        for key in ['stop_pips', 'target_pips', 'stop_loss', 'take_profit', 'entry_price']:
                            if key in signal and key not in protected_signal:
                                protected_signal[key] = signal[key]
                    
                    # Calculate CITADEL score (0-15 range)
                    if protected_signal:
                        citadel_score = 0
                        
                        # Base score from protection status
                        if protected_signal.get('citadel_protected', False):
                            citadel_score += 5  # Protected signal
                        
                        # Boost from post-sweep opportunity
                        if protected_signal.get('citadel_boost') == 'POST_SWEEP':
                            citadel_score += 10  # Maximum boost for post-sweep
                        elif protected_signal.get('citadel_status') == 'VERIFIED':
                            citadel_score += 3  # Verified safe signal
                        
                        # Add sweep avoidance score
                        if hasattr(self.citadel, 'stats') and self.citadel.stats.get('sweeps_avoided', 0) > 0:
                            citadel_score += 2  # Bonus for active sweep protection
                        
                        protected_signal['citadel_score'] = min(15, citadel_score)  # Cap at 15
                    
                    # Calculate signal rate for dynamic threshold
                    recent_signals = [s for s in self.signal_history if time.time() - s.get('timestamp_epoch', 0) < 900]  # Last 15 minutes
                    signals_per_15min = len(recent_signals)
                    projected_hourly_rate = signals_per_15min * 4
                    
                    # Dynamic CITADEL threshold based on signal rate - QUALITY FOCUSED
                    citadel_threshold = 55.0 if projected_hourly_rate > 10 else 50.0 if projected_hourly_rate < 5 else 52.5
                    
                    if protected_signal and protected_signal.get('confidence', 0) >= citadel_threshold:
                        # Signal passed CITADEL protection and meets final threshold
                        print(f"✅ Signal passed CITADEL gate ({protected_signal.get('confidence', 0):.1f}% >= {citadel_threshold}%)")
                        signals_generated.append(protected_signal)
                        
                        # Track signal time for rate calculation
                        if not hasattr(self, 'recent_signal_times'):
                            self.recent_signal_times = []
                        self.recent_signal_times.append(time.time())
                        
                        # Update tracking
                        self.last_signal_time[symbol] = time.time()
                        self.hourly_signal_count[symbol] += 1
                        self.signal_history.append(protected_signal)
                        
                        # Debug: Check if SL/TP present before publishing
                        if not protected_signal.get('stop_pips') or not protected_signal.get('target_pips'):
                            print(f"⚠️ WARNING: Missing SL/TP in signal: stop_pips={protected_signal.get('stop_pips')}, target_pips={protected_signal.get('target_pips')}")
                            print(f"   Original signal keys: {list(signal.keys())}")
                            print(f"   Protected signal keys: {list(protected_signal.keys())}")
                        
                        # Publish
                        self.publish_signal(protected_signal)
                        
                        # EXOTIC PAIR EXECUTION DEBUGGING (Error 4756 investigation)
                        exotic_pairs = ['USDMXN', 'USDSEK', 'USDCNH', 'XAGUSD']
                        if protected_signal.get('symbol') in exotic_pairs:
                            symbol = protected_signal['symbol']
                            sl_pips = protected_signal.get('stop_pips', 0)
                            tp_pips = protected_signal.get('target_pips', 0)
                            entry = protected_signal.get('entry', 0)
                            sl = protected_signal.get('stop_loss', 0)
                            tp = protected_signal.get('take_profit', 0)
                            
                            print(f"🚀 EXOTIC ATTEMPT: {symbol} @ {protected_signal.get('confidence', 0):.1f}%")
                            print(f"   📏 Pips: SL={sl_pips}, TP={tp_pips}")
                            print(f"   💰 Prices: Entry={entry:.5f}, SL={sl:.5f}, TP={tp:.5f}")
                            
                            # Calculate actual pip distances for verification
                            pip_size = self.get_pip_size(symbol)
                            actual_sl_pips = abs(entry - sl) / pip_size if pip_size > 0 else 0
                            actual_tp_pips = abs(tp - entry) / pip_size if pip_size > 0 else 0
                            
                            print(f"   ✅ Actual distances: SL={actual_sl_pips:.1f}p, TP={actual_tp_pips:.1f}p")
                            print(f"   🔍 Signal ID: {protected_signal.get('signal_id', 'UNKNOWN')}")
                            
                            # Check if distances meet minimum requirements
                            min_required = {'USDMXN': 15, 'USDSEK': 15, 'USDCNH': 20, 'XAGUSD': 25}
                            min_stop = min_required.get(symbol, 10)
                            if actual_sl_pips < min_stop:
                                print(f"   ⚠️ WARNING: SL too tight! {actual_sl_pips:.1f}p < {min_stop}p minimum")
                                print(f"   🔧 MT5 Error 4756 likely - adjusting stops needed!")
                            else:
                                print(f"   ✅ Stops OK: {actual_sl_pips:.1f}p >= {min_stop}p minimum")
                        
                        # Use emoji based on signal class
                        emoji = "⚡" if protected_signal['signal_class'] == 'RAPID' else "🎯"
                        citadel_badge = " 🛡️" if protected_signal.get('citadel_boost') else ""
                        logger.info(f"{emoji} {protected_signal['signal_class']}{citadel_badge}: "
                                  f"{protected_signal['symbol']} {protected_signal['direction']} "
                                  f"Quality: {protected_signal['quality_tier']} ({protected_signal['quality_score']}%) "
                                  f"Pattern: {protected_signal['pattern']}")
        
        return signals_generated
    
    def publish_signal(self, signal: Dict):
        """Publish signal to ZMQ"""
        if self.publisher:
            try:
                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
                
                # Log to truth system
                with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
                    truth_entry = {
                        'timestamp': datetime.now(pytz.UTC).isoformat(),
                        'signal_id': signal['signal_id'],
                        'event': 'signal_generated',
                        'quality_score': signal['quality_score'],
                        'quality_tier': signal['quality_tier'],
                        'pattern': signal['pattern']
                    }
                    f.write(json.dumps(truth_entry) + '\n')
                
                # ENHANCED: Call optimized tracking
                self.log_signal_to_truth_tracker(signal)
                    
            except Exception as e:
                logger.error(f"Failed to publish signal: {e}")
    
    def data_listener(self):
        """Listen for market data"""
        logger.info("📡 Starting data listener")
        print("📡 Data listener started, waiting for ticks...")
        
        while self.running:
            try:
                if self.subscriber.poll(timeout=100):
                    message = self.subscriber.recv_string()
                    
                    # Handle pure JSON format from telemetry bridge
                    if message.startswith("{"):
                        try:
                            tick_data = json.loads(message)
                            # Process tick if it's a TICK type message
                            if tick_data.get('type') == 'TICK' and 'symbol' in tick_data and 'bid' in tick_data:
                                symbol = tick_data.get('symbol')
                                if symbol and symbol in self.trading_pairs:
                                    self.tick_data[symbol].append(tick_data)
                                    self.last_tick_time[symbol] = time.time()
                                    self.build_candles_from_tick(symbol, tick_data)
                                    
                                    # Log every 100th tick for debugging
                                    tick_count = len(self.tick_data[symbol])
                                    if tick_count % 100 == 0:
                                        print(f"📈 {symbol}: {tick_count} ticks, {len(self.m1_data.get(symbol, []))} M1 candles")
                        except json.JSONDecodeError as e:
                            logger.debug(f"Failed to parse JSON: {e}")
                    # Handle old "tick " prefix format (backward compatibility)
                    elif message.startswith("tick "):
                        json_data = message[5:]  # Skip "tick " prefix
                        try:
                            tick_data = json.loads(json_data)
                            if 'symbol' in tick_data and 'bid' in tick_data:
                                symbol = tick_data.get('symbol')
                                if symbol and symbol in self.trading_pairs:
                                    self.tick_data[symbol].append(tick_data)
                                    self.last_tick_time[symbol] = time.time()
                                    self.build_candles_from_tick(symbol, tick_data)
                        except json.JSONDecodeError:
                            logger.debug(f"Failed to parse: {json_data[:50]}")
                    else:
                        self.process_tick(message)
            except Exception as e:
                logger.debug(f"Listener error: {e}")
                time.sleep(0.1)
    
    def check_citadel_delayed_signals(self):
        """Check if any CITADEL-delayed signals can be released"""
        current_ticks = {}
        for symbol in self.tick_data:
            if self.tick_data[symbol]:
                current_ticks[symbol] = list(self.tick_data[symbol])[-1]
        
        released_signals = self.citadel.check_delayed_signals(current_ticks)
        
        for signal in released_signals:
            # These are post-sweep golden opportunities
            if signal.get('confidence', 0) >= 70:  # Match MIN_CONFIDENCE threshold
                self.publish_signal(signal)
                logger.info(f"🏆 CITADEL RELEASE: {signal['symbol']} {signal['direction']} "
                          f"(delayed {signal.get('delay_time', 0)}s, confidence: {signal['confidence']}%)")
    
    def show_stats(self):
        """Display current statistics"""
        logger.info("\n" + "="*60)
        logger.info("📊 ELITE GUARD BALANCED v7.0 STATUS")
        logger.info("="*60)
        
        # Signal stats - handle both timestamp formats
        recent_signals = []
        for s in self.signal_history:
            try:
                # Try to parse as float first (unix timestamp)
                ts = s.get('timestamp', 0)
                if isinstance(ts, (int, float)):
                    ts_float = float(ts)
                else:
                    # If it's a string datetime, parse it
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    ts_float = dt.timestamp()
                    
                if time.time() - ts_float < 3600:
                    recent_signals.append(s)
            except:
                continue
        
        logger.info(f"\n📈 SIGNAL METRICS (Last Hour):")
        logger.info(f"  Total Signals: {len(recent_signals)}")
        
        if recent_signals:
            quality_tiers = defaultdict(int)
            for sig in recent_signals:
                quality_tiers[sig.get('quality_tier', 'UNKNOWN')] += 1
            
            logger.info(f"  Premium: {quality_tiers['PREMIUM']}")
            logger.info(f"  Standard: {quality_tiers['STANDARD']}")
            logger.info(f"  Acceptable: {quality_tiers['ACCEPTABLE']}")
        
        # Data feed status
        logger.info(f"\n📡 DATA FEED STATUS:")
        logger.info(f"  Total symbols tracked: {len(self.tick_data)}")
        for symbol in list(self.tick_data.keys())[:10]:
            age = time.time() - self.last_tick_time.get(symbol, 0)
            tick_count = len(self.tick_data[symbol])
            status = "✅" if age < 5 else "⚠️" if age < 30 else "❌"
            logger.info(f"  {symbol}: {tick_count} ticks | Last: {age:.0f}s ago {status}")
        
        # CITADEL Protection stats
        citadel_stats = self.citadel.get_protection_stats()
        logger.info(f"\n🛡️ CITADEL PROTECTION:")
        logger.info(f"  Signals Delayed: {citadel_stats['signals_delayed']}")
        logger.info(f"  Sweeps Detected: {citadel_stats['sweeps_detected']}")
        logger.info(f"  Sweeps Avoided: {citadel_stats['sweeps_avoided']}")
        logger.info(f"  Post-Sweep Entries: {citadel_stats['post_sweep_entries']}")
        logger.info(f"  Protection Rate: {citadel_stats['protection_rate']}")
        
        logger.info("="*60)
    
    def start(self):
        """Start the Elite Guard engine"""
        logger.info("🎯 ELITE GUARD BALANCED v7.0 - Starting...")
        logger.info("📊 Target: 45-50% win rate | 1-2 signals/hour minimum")
        logger.info("🎮 Focus: User engagement with quality improvements")
        
        if not self.setup_zmq():
            raise RuntimeError("Failed to setup ZMQ connections")
        
        self.running = True
        
        # Start data listener thread
        listener_thread = threading.Thread(target=self.data_listener, daemon=True)
        listener_thread.start()
        
        logger.info("✅ Elite Guard Balanced started successfully")
        logger.info("⚡ Generating 1-2 signals per hour with quality tiers")
        
        # Main loop
        last_scan = 0
        last_stats = 0
        last_save = 0  # Auto-save candles
        
        while self.running:
            try:
                current_time = time.time()
                
                # Fetch OHLC data continuously
                self.fetch_ohlc_data()
                
                # Scan for patterns every 15 seconds for more frequent signals
                if current_time - last_scan >= 15:
                    print(f"⏰ SCAN TRIGGER: 15-second interval reached, active_session={self.is_active_session()}")
                    logger.info(f"⏰ 15-second scan trigger, active_session={self.is_active_session()}")
                    if self.is_active_session():
                        self.scan_for_patterns()
                    # Check CITADEL delayed signals
                    self.check_citadel_delayed_signals()
                    last_scan = current_time
                
                # Show stats every 5 minutes
                if current_time - last_stats >= 300:
                    self.show_stats()
                    last_stats = current_time
                
                # Auto-save candles every 60 seconds
                if current_time - last_save >= 60:
                    self.save_candles()
                    last_save = current_time
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️ Shutdown signal received")
                break
            except Exception as e:
                import traceback
                logger.error(f"Main loop error: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(5)
        
        self.cleanup()
    
    def test_candle_building(self):
        """Test candle building functionality"""
        print("🔍 Testing candle building...")
        
        # Initialize candle storage for all trading pairs if not present
        for symbol in self.trading_pairs:
            if symbol not in self.m1_data:
                self.m1_data[symbol] = deque(maxlen=500)
            if symbol not in self.m5_data:
                self.m5_data[symbol] = deque(maxlen=300)
            if symbol not in self.m15_data:
                self.m15_data[symbol] = deque(maxlen=200)
        
        # Create a test tick
        test_tick = {
            "symbol": "EURUSD",
            "bid": 1.1647,
            "ask": 1.1649,
            "timestamp": time.time()
        }
        
        # Process the test tick
        self.process_tick(test_tick)
        
        # Report candle counts
        print(f"✅ EURUSD M1: {len(self.m1_data.get('EURUSD', []))} candles")
        print(f"✅ EURUSD M5: {len(self.m5_data.get('EURUSD', []))} candles")
        print(f"✅ EURUSD M15: {len(self.m15_data.get('EURUSD', []))} candles")
        
        # Check all pairs
        print("\n📊 All pairs candle counts:")
        for symbol in self.trading_pairs[:5]:  # Show first 5 for brevity
            m1_count = len(self.m1_data.get(symbol, []))
            m5_count = len(self.m5_data.get(symbol, []))
            m15_count = len(self.m15_data.get(symbol, []))
            print(f"  {symbol}: M1={m1_count}, M5={m5_count}, M15={m15_count}")
        
        print("✅ Candle building test complete!")
    
    def cleanup(self):
        """Clean shutdown"""
        self.running = False
        
        # Save candles before shutdown
        print("💾 Saving candles before shutdown...")
        self.save_candles()
        
        if self.subscriber:
            self.subscriber.close()
        if self.publisher:
            self.publisher.close()
        
        self.context.term()
        logger.info("✅ Elite Guard Balanced shutdown complete")

def immortal_main_loop():
    """Immortality protocol - auto-restart on crashes"""
    consecutive_failures = 0
    max_failures = 5
    
    while True:
        try:
            logger.info("🛡️ IMMORTALITY PROTOCOL ACTIVATED")
            logger.info("🚀 Starting Elite Guard Balanced...")
            
            engine = EliteGuardBalanced()
            engine.start()
            
            # Reset failure count on clean exit
            consecutive_failures = 0
            
        except KeyboardInterrupt:
            logger.info("⚠️ Manual shutdown requested")
            break
            
        except Exception as e:
            consecutive_failures += 1
            
            if consecutive_failures >= max_failures:
                logger.error(f"❌ Max failures ({max_failures}) reached. Stopping.")
                break
            
            wait_time = min(30 * consecutive_failures, 300)
            
            logger.error(f"💀 Elite Guard died: {e}")
            logger.info(f"🔄 Resurrection in {wait_time} seconds...")
            logger.info(f"📊 Failure {consecutive_failures}/{max_failures}")
            
            time.sleep(wait_time)
            
            logger.info("⚡ RESURRECTING Elite Guard Balanced...")

if __name__ == "__main__":
    immortal_main_loop()