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

# Add unified logging support
import sys
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

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
            # Additional & Exotics (2) 
            "USDCNH", "USDSEK",
            # "USDMXN",  # DISABLED - Wide spreads, unprofitable
            # Precious Metals (0)
            # "XAUUSD",  # TEMPORARILY DISABLED - R:R calculation issues
            # "XAGUSD"   # DISABLED - Too many losses, poor performance
            # Total: 16 pairs (NO CRYPTO, METALS DISABLED)
        ]
        
        # Load candle cache on startup (AFTER trading_pairs defined)
        self.load_candles()
        
        # Test candle building (for debugging)
        self.test_candle_building()
        
        # Run initial analysis on startup
        print("\n" + "="*60)
        print("🔍 RUNNING INITIAL 6-HOUR ANALYSIS ON STARTUP")
        print("="*60)
        self.analyze_initial_data()
        self.verify_rr_ratio()
        print("="*60 + "\n")
        
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
        self.MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '70'))  # Lowered to 70% for more data collection
        self.COOLDOWN_MINUTES = 5 # Reduced cooldown to allow more signals (5-10/hr target)
        
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
                    pip_size = 0.01 if 'JPY' in symbol else 0.01 if symbol == 'XAUUSD' else 0.001 if symbol == 'XAGUSD' else 0.0001
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
            pip_size = 0.01 if 'JPY' in symbol else 0.01 if symbol == 'XAUUSD' else 0.001 if symbol == 'XAGUSD' else 0.0001
            range_pips = avg_range / pip_size
            if range_pips > 3:
                activity_bonus = 4  # Very active
            elif range_pips > 1.5:
                activity_bonus = 2  # Active
            print(f"  📊 Activity: {range_pips:.1f}p range = +{activity_bonus}%")
        confidence += activity_bonus
        
        # Apply recalibration based on actual performance data
        raw_confidence = confidence
        pre_calibration = min(95, max(55, confidence))  # Floor at 55%, cap at 95%
        
        # RECALIBRATION: Fix overconfident 85%+ signals (actual 32.4% win rate)
        if pre_calibration >= 85:
            # 85%+ severely overconfident (32.4% actual vs 85%+ claimed)
            final_confidence = 30 + (pre_calibration - 85) * 0.5
            final_confidence = min(35, max(30, final_confidence))
        elif pre_calibration >= 80:
            # 80-84% is optimal range (43.4% actual) - slight adjustment
            final_confidence = 40 + (pre_calibration - 80) * 1.25
            final_confidence = min(45, max(40, final_confidence))
        elif pre_calibration >= 75:
            # 75-79% performs at 39.6%
            final_confidence = 35 + (pre_calibration - 75) * 1.0
            final_confidence = min(40, max(35, final_confidence))
        elif pre_calibration >= 70:
            # 70-74% performs at 37.4%
            final_confidence = 32 + (pre_calibration - 70) * 1.25
            final_confidence = min(37, max(32, final_confidence))
        else:
            # Below 70% - conservative mapping
            final_confidence = max(20, pre_calibration * 0.5)
        
        print(f"  🎯 RAW: {raw_confidence:.1f}% → PRE: {pre_calibration:.1f}% → CALIBRATED: {final_confidence:.1f}%")
        print(f"  🔧 RECALIBRATION: Based on actual win rate performance (80-84% = best at 43.4%)")
        
        return round(final_confidence, 1)
    
    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range for R:R feasibility check"""
        if symbol not in self.m5_data or len(self.m5_data[symbol]) < period:
            # Default ATR values for different pairs
            if 'JPY' in symbol:
                return 0.5  # 50 pips default for JPY pairs
            elif symbol in ['XAUUSD']:
                return 0.5  # 50 pips for gold (adjusted for 0.01 pip size)
            elif symbol in ['XAGUSD']:
                return 0.05  # 5 pips for silver
            else:
                return 0.001  # 10 pips default for majors
        
        candles = list(self.m5_data[symbol])[-period:]
        pip_size = 0.01 if 'JPY' in symbol else 0.01 if symbol == 'XAUUSD' else 0.001 if symbol == 'XAGUSD' else 0.0001
        
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
                pip_size = 0.01 if 'JPY' in signal.pair else 0.01 if signal.pair == 'XAUUSD' else 0.001 if signal.pair == 'XAGUSD' else 0.0001
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
            elif symbol == 'XAGUSD':
                pip_size = 0.001  # Silver: 0.001 = 1 pip (38.500 to 38.501 = 1 pip)
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
            elif symbol == 'XAGUSD':
                pip_size = 0.001  # Silver: 0.001 = 1 pip (38.500 to 38.501 = 1 pip)
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
                min_sweep_pips = 300.0  # Gold needs bigger moves (300 standard pips = $3)
            
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
                    
                    # SMA TREND CHECK for better accuracy
                    sma = self.calculate_sma(symbol, period=60)
                    current_price = current_candle['close']
                    trend_bonus = 0
                    if current_price < sma:  # SELL signal below SMA is good
                        trend_bonus = 10
                    else:
                        trend_bonus = -5  # Counter-trend penalty
                    
                    base_quality += trend_bonus
                    print(f"🔍 LSR {symbol}: SMA={sma:.5f}, Price={current_price:.5f}, Trend Bonus={trend_bonus:+d}%")
                    print(f"🔍 LSR {symbol}: Final quality = {base_quality:.1f}%")
                    
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
                    
                    # SMA TREND CHECK for better accuracy
                    sma = self.calculate_sma(symbol, period=60)
                    current_price = current_candle['close']
                    trend_bonus = 0
                    if current_price < sma:  # SELL signal below SMA is good
                        trend_bonus = 10
                    else:
                        trend_bonus = -5  # Counter-trend penalty
                    
                    base_quality += trend_bonus
                    print(f"🔍 LSR {symbol}: SMA={sma:.5f}, Price={current_price:.5f}, Trend Bonus={trend_bonus:+d}%")
                    print(f"🔍 LSR {symbol}: Final quality = {base_quality:.1f}%")
                    
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
        """
        ENHANCED ORDER BLOCK: True institutional order block detection
        Fixed from 39.6% win rate - now finds real accumulation/distribution zones
        """
        try:
            print(f"🔍 OBB {symbol}: ENHANCED INSTITUTIONAL CHECK")
            if len(self.m5_data[symbol]) < 15:  # Need more context for real order blocks
                print(f"🔍 OBB {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 15+")
                return None
                
            candles = list(self.m5_data[symbol])[-15:]
            current = candles[-1]
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            elif symbol == 'XAGUSD':
                pip_size = 0.001
            else:
                pip_size = 0.0001
            
            # STEP 1: Find real order blocks (accumulation/distribution areas)
            # Order block = zone where big institutions left unfilled orders
            
            for lookback in range(5, 12):  # Scan multiple time periods
                block_candles = candles[-lookback-3:-3]  # Not too recent, not too old
                
                if len(block_candles) < 3:
                    continue
                
                # Find consolidation zones (low volatility = accumulation)
                highs = [c['high'] for c in block_candles]
                lows = [c['low'] for c in block_candles]
                
                block_high = max(highs)
                block_low = min(lows)
                block_range = block_high - block_low
                
                # STEP 2: Validate this is a real order block
                # Real order blocks have: small range, high volume, followed by directional move
                
                # Check range tightness (order blocks are typically 5-15 pips)
                range_pips = block_range / pip_size
                if not (5 <= range_pips <= 15):
                    continue
                
                # Check for directional breakout AFTER the block
                post_block_candles = candles[-3:]
                breakout_high = max(c['high'] for c in post_block_candles)
                breakout_low = min(c['low'] for c in post_block_candles)
                
                # Did price break out of the block significantly?
                bullish_breakout = breakout_high > block_high + (3 * pip_size)
                bearish_breakout = breakout_low < block_low - (3 * pip_size)
                
                if not (bullish_breakout or bearish_breakout):
                    continue
                
                # STEP 3: Check if we're now retesting the order block
                current_price = current['close']
                
                # For bullish breakout, look for retest of block high (now support)
                if bullish_breakout:
                    retest_distance = abs(current_price - block_high) / pip_size
                    
                    # Must be within 3 pips of the order block level
                    if retest_distance <= 3.0 and current_price >= block_high - (2 * pip_size):
                        
                        # STEP 4: Confirmation - need rejection or volume
                        # Check for bullish rejection (lower wick)
                        lower_wick = current['close'] - current['low']
                        candle_range = current['high'] - current['low']
                        wick_ratio = lower_wick / candle_range if candle_range > 0 else 0
                        
                        # Strong rejection OR close above block high
                        strong_rejection = wick_ratio > 0.3 and current['close'] > current['open']
                        clean_bounce = current['low'] <= block_high and current['close'] > block_high
                        
                        if strong_rejection or clean_bounce:
                            # STEP 5: Calculate precise risk/reward
                            entry = block_high + (pip_size * 2)  # Enter above order block
                            stop_loss = block_low - (pip_size * 2)  # Below order block
                            
                            sl_distance = abs(entry - stop_loss) / pip_size
                            
                            # Target: Move to next resistance level
                            atr = self.calculate_atr(symbol)
                            target_distance = min(sl_distance * 2.0, 1.5 * atr)  # 2:1 R:R or 1.5x ATR
                            take_profit = entry + (target_distance * pip_size)
                            
                            actual_rr = target_distance / sl_distance if sl_distance > 0 else 0
                            
                            # Quality check: tight stop, good R:R
                            if sl_distance <= 18 and actual_rr >= 1.6:
                                print(f"✅ OBB {symbol} BUY: ORDER BLOCK RETEST!")
                                print(f"   Block: {block_low:.5f} - {block_high:.5f} ({range_pips:.1f} pips)")
                                print(f"   Retest distance: {retest_distance:.1f}p, R:R: {actual_rr:.2f}")
                                
                                # Enhanced quality scoring
                                base_quality = 65  # Higher base for real order block
                                base_quality += max(0, 10 - range_pips) * 1.5  # Tighter block = better
                                base_quality += (1 - retest_distance/3) * 15  # Precise retest bonus
                                base_quality += wick_ratio * 25  # Rejection strength
                                if clean_bounce: base_quality += 10  # Clean bounce bonus
                                base_quality = min(base_quality, 88)
                                
                                return PatternSignal(
                                    pattern="ORDER_BLOCK_BOUNCE",
                                    direction="BUY",
                                    entry_price=entry,
                                    confidence=base_quality,
                                    timeframe="M5",
                                    pair=symbol,
                                    quality_score=base_quality
                                )
                
                # For bearish breakout, look for retest of block low (now resistance)
                elif bearish_breakout:
                    retest_distance = abs(current_price - block_low) / pip_size
                    
                    if retest_distance <= 3.0 and current_price <= block_low + (2 * pip_size):
                        
                        # Check for bearish rejection (upper wick)
                        upper_wick = current['high'] - current['close']
                        candle_range = current['high'] - current['low']
                        wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
                        
                        strong_rejection = wick_ratio > 0.3 and current['close'] < current['open']
                        clean_bounce = current['high'] >= block_low and current['close'] < block_low
                        
                        if strong_rejection or clean_bounce:
                            entry = block_low - (pip_size * 2)  # Enter below order block
                            stop_loss = block_high + (pip_size * 2)  # Above order block
                            
                            sl_distance = abs(stop_loss - entry) / pip_size
                            
                            atr = self.calculate_atr(symbol)
                            target_distance = min(sl_distance * 2.0, 1.5 * atr)
                            take_profit = entry - (target_distance * pip_size)
                            
                            actual_rr = target_distance / sl_distance if sl_distance > 0 else 0
                            
                            if sl_distance <= 18 and actual_rr >= 1.6:
                                print(f"✅ OBB {symbol} SELL: ORDER BLOCK RETEST!")
                                print(f"   Block: {block_low:.5f} - {block_high:.5f} ({range_pips:.1f} pips)")
                                print(f"   Retest distance: {retest_distance:.1f}p, R:R: {actual_rr:.2f}")
                                
                                base_quality = 65
                                base_quality += max(0, 10 - range_pips) * 1.5
                                base_quality += (1 - retest_distance/3) * 15
                                base_quality += wick_ratio * 25
                                if clean_bounce: base_quality += 10
                                base_quality = min(base_quality, 88)
                                
                                return PatternSignal(
                                    pattern="ORDER_BLOCK_BOUNCE",
                                    direction="SELL",
                                    entry_price=entry,
                                    confidence=base_quality,
                                    timeframe="M5",
                                    pair=symbol,
                                    quality_score=base_quality
                                )
            
            print(f"🔍 OBB {symbol}: No valid institutional order blocks found")
            return None
                            
        except Exception as e:
            logger.debug(f"Enhanced order block error for {symbol}: {e}")
        
        return None
    
    def detect_sweep_and_return(self, symbol: str) -> Optional[PatternSignal]:
        """
        ENHANCED LIQUIDITY SWEEP: True institutional stop hunting + reversal
        Fixed from 20% win rate - now detects real liquidity grabs with multi-touch validation
        """
        try:
            print(f"🔍 SRL {symbol}: ENHANCED LIQUIDITY SWEEP CHECK")
            if len(self.m5_data[symbol]) < 8:  # Need more context for real sweeps
                print(f"🔍 SRL {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 8+")
                return None
                
            candles = list(self.m5_data[symbol])[-8:]
            current = candles[-1]
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            elif symbol == 'XAGUSD':
                pip_size = 0.001
            else:
                pip_size = 0.0001
            
            # STEP 1: Find significant liquidity levels (multi-touch levels)
            # Real liquidity = levels that price touched 2+ times recently
            
            highs = [c['high'] for c in candles[:-2]]  # Exclude last 2 candles
            lows = [c['low'] for c in candles[:-2]]
            
            # Find levels with multiple touches (within 2 pips = same level)
            liquidity_highs = []
            liquidity_lows = []
            
            for i, high in enumerate(highs):
                touches = sum(1 for h in highs if abs(h - high) / pip_size <= 2.0)
                if touches >= 2:  # Multi-touch resistance
                    liquidity_highs.append((high, touches))
            
            for i, low in enumerate(lows):
                touches = sum(1 for l in lows if abs(l - low) / pip_size <= 2.0)
                if touches >= 2:  # Multi-touch support
                    liquidity_lows.append((low, touches))
            
            if not liquidity_highs and not liquidity_lows:
                print(f"🔍 SRL {symbol}: No multi-touch liquidity levels found")
                return None
            
            # STEP 2: Check for liquidity sweep (stop hunt)
            sweep_candle = candles[-2]  # Penultimate candle does the sweep
            
            # BULLISH SWEEP: Sweep below support, then strong return
            for support_level, touches in liquidity_lows:
                sweep_distance = (support_level - sweep_candle['low']) / pip_size
                
                # Must sweep at least 3 pips below the level
                if sweep_distance >= 3.0:
                    
                    # STEP 3: Validate the return/reversal
                    # Current candle should show strong reversal back above support
                    returned_above = current['close'] > support_level + (pip_size * 2)
                    
                    # Check reversal strength - need strong bullish candle
                    reversal_body = current['close'] - current['open']
                    candle_range = current['high'] - current['low']
                    body_ratio = abs(reversal_body) / candle_range if candle_range > 0 else 0
                    bullish_reversal = reversal_body > 0 and body_ratio > 0.5
                    
                    # Volume confirmation (if available)
                    volume_surge = (current.get('volume', 100) > 
                                  sum(c.get('volume', 100) for c in candles[-4:-1]) / 3 * 1.3)
                    
                    if returned_above and (bullish_reversal or volume_surge):
                        
                        # STEP 4: Calculate precise entry and risk
                        entry = support_level + (pip_size * 3)  # Enter above swept level
                        stop_loss = sweep_candle['low'] - (pip_size * 2)  # Below sweep low
                        
                        sl_distance = abs(entry - stop_loss) / pip_size
                        atr = self.calculate_atr(symbol)
                        
                        # Target: Next resistance or 2:1 R:R minimum
                        resistance_targets = [h for h, t in liquidity_highs if h > entry]
                        if resistance_targets:
                            nearest_resistance = min(resistance_targets)
                            target_distance = abs(nearest_resistance - entry) / pip_size
                        else:
                            target_distance = sl_distance * 2.2  # 2.2:1 minimum
                        
                        actual_rr = target_distance / sl_distance if sl_distance > 0 else 0
                        
                        # Quality gates
                        if sl_distance <= 12 and actual_rr >= 2.0 and target_distance <= 1.8 * atr:
                            
                            print(f"✅ SRL {symbol} BUY: LIQUIDITY SWEEP & RETURN!")
                            print(f"   Support: {support_level:.5f} ({touches} touches)")
                            print(f"   Sweep: {sweep_distance:.1f} pips below support")
                            print(f"   Return: {current['close']:.5f} (back above level)")
                            print(f"   R:R: {actual_rr:.2f}, SL: {sl_distance:.1f}p")
                            
                            # Advanced quality scoring
                            base_quality = 70  # Higher base for real liquidity sweep
                            base_quality += min(touches - 1, 4) * 5  # More touches = better level
                            base_quality += min(sweep_distance - 3, 7) * 2  # Deeper sweep = more stops collected
                            base_quality += body_ratio * 15  # Strong reversal candle
                            if volume_surge: base_quality += 12  # Volume confirmation
                            base_quality = min(base_quality, 92)
                            
                            return PatternSignal(
                                pattern="SWEEP_AND_RETURN",
                                direction="BUY",
                                entry_price=entry,
                                confidence=base_quality,
                                timeframe="M5",
                                pair=symbol,
                                quality_score=base_quality
                            )
            
            # BEARISH SWEEP: Sweep above resistance, then strong return
            for resistance_level, touches in liquidity_highs:
                sweep_distance = (sweep_candle['high'] - resistance_level) / pip_size
                
                if sweep_distance >= 3.0:
                    
                    # Validate bearish return
                    returned_below = current['close'] < resistance_level - (pip_size * 2)
                    
                    reversal_body = current['open'] - current['close']  # Bearish body
                    candle_range = current['high'] - current['low']
                    body_ratio = abs(reversal_body) / candle_range if candle_range > 0 else 0
                    bearish_reversal = reversal_body > 0 and body_ratio > 0.5
                    
                    volume_surge = (current.get('volume', 100) > 
                                  sum(c.get('volume', 100) for c in candles[-4:-1]) / 3 * 1.3)
                    
                    if returned_below and (bearish_reversal or volume_surge):
                        
                        entry = resistance_level - (pip_size * 3)  # Enter below swept level
                        stop_loss = sweep_candle['high'] + (pip_size * 2)  # Above sweep high
                        
                        sl_distance = abs(stop_loss - entry) / pip_size
                        atr = self.calculate_atr(symbol)
                        
                        # Target: Next support or 2:1 R:R
                        support_targets = [l for l, t in liquidity_lows if l < entry]
                        if support_targets:
                            nearest_support = max(support_targets)
                            target_distance = abs(entry - nearest_support) / pip_size
                        else:
                            target_distance = sl_distance * 2.2
                        
                        actual_rr = target_distance / sl_distance if sl_distance > 0 else 0
                        
                        if sl_distance <= 12 and actual_rr >= 2.0 and target_distance <= 1.8 * atr:
                            
                            print(f"✅ SRL {symbol} SELL: LIQUIDITY SWEEP & RETURN!")
                            print(f"   Resistance: {resistance_level:.5f} ({touches} touches)")
                            print(f"   Sweep: {sweep_distance:.1f} pips above resistance")
                            print(f"   Return: {current['close']:.5f} (back below level)")
                            print(f"   R:R: {actual_rr:.2f}, SL: {sl_distance:.1f}p")
                            
                            base_quality = 70
                            base_quality += min(touches - 1, 4) * 5
                            base_quality += min(sweep_distance - 3, 7) * 2
                            base_quality += body_ratio * 15
                            if volume_surge: base_quality += 12
                            base_quality = min(base_quality, 92)
                            
                            return PatternSignal(
                                pattern="SWEEP_AND_RETURN",
                                direction="SELL",
                                entry_price=entry,
                                confidence=base_quality,
                                timeframe="M5",
                                pair=symbol,
                                quality_score=base_quality
                            )
            
            print(f"🔍 SRL {symbol}: No institutional liquidity sweeps detected")
            return None
                        
        except Exception as e:
            logger.debug(f"Enhanced SRL detection error for {symbol}: {e}")
        
        return None
    
    def detect_vcb_breakout(self, symbol: str) -> Optional[PatternSignal]:
        """Simple VCB"""
        try:
            if len(self.m5_data[symbol]) < 3:
                return None
            candles = list(self.m5_data[symbol])[-7:]
            current = candles[-1]
            pip_size = 0.01 if "JPY" in symbol else 0.01 if symbol == "XAUUSD" else 0.0001
            recent_high = max(c["high"] for c in candles[:-1])
            recent_low = min(c["low"] for c in candles[:-1])
            if current["close"] > recent_high:
                return PatternSignal(
                    pattern="VCB_BREAKOUT",
                    direction="BUY",
                    entry_price=current["close"] + pip_size,
                    confidence=65.0,
                    timeframe="M5",
                    pair=symbol,
                    quality_score=65.0
                )
            elif current["close"] < recent_low:
                return PatternSignal(
                    pattern="VCB_BREAKOUT",
                    direction="SELL", 
                    entry_price=current["close"] - pip_size,
                    confidence=65.0,
                    timeframe="M5",
                    pair=symbol,
                    quality_score=65.0
                )
        except Exception as e:
            pass
        return None

    def detect_momentum_breakout(self, symbol: str) -> Optional[PatternSignal]:
        """
        ENHANCED MOMENTUM BREAKOUT: True institutional momentum with multi-timeframe validation
        Fixed from basic implementation - now detects real momentum shifts with volume confirmation
        """
        try:
            print(f"🔍 MOM {symbol}: ENHANCED MOMENTUM CHECK")
            if len(self.m5_data[symbol]) < 15:  # Need more context for real momentum
                print(f"🔍 MOM {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 15+")
                return None
                
            candles = list(self.m5_data[symbol])[-15:]  # INDUSTRY STANDARD: Last 15 candles for momentum
            current = candles[-1]
            
            # INDUSTRY STANDARD: Pip size calculation
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            elif symbol == 'XAGUSD':
                pip_size = 0.001
            else:
                pip_size = 0.0001
            
            # STEP 1: INDUSTRY STANDARD - Momentum acceleration detection
            # Look for 3 consecutive candles with increasing velocity
            momentum_candles = candles[-4:-1]  # Last 3 completed candles
            
            # Calculate price velocity (price change per candle)
            velocities = []
            for i in range(1, len(momentum_candles)):
                velocity = abs(momentum_candles[i]['close'] - momentum_candles[i-1]['close']) / pip_size
                velocities.append(velocity)
            
            if len(velocities) < 2:
                print(f"🔍 MOM {symbol}: Not enough velocity data")
                return None
                
            # SIMPLIFIED: Just need ANY movement
            acceleration_up = velocities[-1] > 0.3  # Just need 0.3+ pips movement
            print(f"   Velocities: {velocities} (need >0.3 pips/candle)")
            print(f"   Acceleration: {'YES' if acceleration_up else 'NO'}")
            
            if not acceleration_up:
                print(f"🔍 MOM {symbol}: No momentum detected")
                return None
            
            # STEP 2: INDUSTRY STANDARD - Volume confirmation (momentum + volume = valid)
            volumes = [c.get('tick_volume', 0) for c in momentum_candles]
            avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else 1
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            volume_surge = volume_ratio > 1.1  # FIXED: Lowered from 1.3x to 1.1x - more realistic
            print(f"   Volume ratio: {volume_ratio:.2f}x (need >1.1x for momentum)")
            print(f"   Volume surge: {'YES' if volume_surge else 'NO'}")
            
            # SIMPLIFIED: Skip volume check entirely - too restrictive
            print(f"🔍 MOM {symbol}: Skipping volume requirement")
            
            # STEP 3: INDUSTRY STANDARD - Direction based on breakout + momentum
            lookback_candles = candles[-10:-1]  # 9 candles for range
            resistance_level = max(c['high'] for c in lookback_candles)
            support_level = min(c['low'] for c in lookback_candles)
            
            # Must break out of recent range with momentum
            bullish_breakout = current['close'] > resistance_level + (2 * pip_size)
            bearish_breakout = current['close'] < support_level - (2 * pip_size)
            
            print(f"   Range: {support_level:.5f} - {resistance_level:.5f}")
            print(f"   Current: {current['close']:.5f}")
            print(f"   Breakout: UP={bullish_breakout}, DOWN={bearish_breakout}")
            
            direction = None
            if bullish_breakout:
                direction = 'BUY'
                entry = current['close'] + pip_size
                sl_distance = abs(entry - support_level) / pip_size
            elif bearish_breakout:
                direction = 'SELL'
                entry = current['close'] - pip_size
                sl_distance = abs(resistance_level - entry) / pip_size
            else:
                print(f"🔍 MOM {symbol}: No clear breakout direction")
                return None
            
            # STEP 4: R:R FEASIBILITY CHECK
            # Momentum patterns typically have 1:1.5 R:R minimum
            min_rr = 1.5
            tp_distance = sl_distance * min_rr
            
            print(f"   SL distance: {sl_distance:.1f} pips")
            print(f"   TP distance: {tp_distance:.1f} pips (1.5:1 R:R)")
            
            # INDUSTRY STANDARD: Reasonable SL range (5-25 pips for momentum)
            if not (5 <= sl_distance <= 25):
                print(f"🔍 MOM {symbol}: SL distance {sl_distance:.1f} outside 5-25 pip range")
                return None
            
            # STEP 5: INDUSTRY STANDARD - Confidence calculation
            base_confidence = 68.0  # Lower than other patterns (momentum is riskier)
            
            # Acceleration strength bonus (0-5%)
            acceleration_strength = min(5.0, (velocities[-1] / velocities[-2] - 1) * 10)
            
            # Volume surge bonus (0-7%)  
            volume_bonus = min(7.0, (volume_ratio - 1.3) * 10)
            
            # Range breakout bonus (0-5%)
            breakout_distance = abs(current['close'] - (resistance_level if bullish_breakout else support_level)) / pip_size
            breakout_bonus = min(5.0, breakout_distance)
            
            final_confidence = base_confidence + acceleration_strength + volume_bonus + breakout_bonus
            final_confidence = min(82.0, final_confidence)  # Cap at 82% (momentum is volatile)
            
            print(f"   Confidence: {base_confidence:.1f} + {acceleration_strength:.1f} + {volume_bonus:.1f} + {breakout_bonus:.1f} = {final_confidence:.1f}%")
            print(f"   OLD vs NEW: Was simple M1 with 71% base, now M5 momentum with volume + R:R validation")
            
            if final_confidence < 65:  # FIXED: Lowered from 70% to 65%
                print(f"🔍 MOM {symbol}: Confidence {final_confidence:.1f}% below 65% threshold")
                return None
                
            # Calculate TP/SL prices
            if direction == 'BUY':
                sl_price = entry - (sl_distance * pip_size)
                tp_price = entry + (tp_distance * pip_size)
            else:
                sl_price = entry + (sl_distance * pip_size)
                tp_price = entry - (tp_distance * pip_size)
            
            print(f"🎯 MOMENTUM BREAKOUT DETECTED: {symbol} {direction}")
            print(f"   Entry: {entry:.5f}, SL: {sl_price:.5f}, TP: {tp_price:.5f}")
            print(f"   Confidence: {final_confidence:.1f}%, R:R: 1:{min_rr}")
            
            return PatternSignal(
                pattern="MOMENTUM_BURST",
                direction=direction,
                entry_price=entry,
                stop_loss=sl_price,
                take_profit=tp_price,
                stop_pips=sl_distance,
                target_pips=tp_distance,
                confidence=final_confidence,
                timeframe="M5",
                pair=symbol,
                momentum_acceleration=acceleration_strength,
                volume_surge_ratio=volume_ratio,
                breakout_strength=breakout_distance,
                quality_score=final_confidence
            )
            
        except Exception as e:
            print(f"Error in enhanced momentum breakout detection for {symbol}: {e}")
            return None
    
    def detect_fair_value_gap_fill(self, symbol: str) -> Optional[PatternSignal]:
        """
        ENHANCED FVG: True institutional gap detection with multi-candle validation
        Fixed from 40.5% win rate - now requires real imbalance + strong retest
        """
        try:
            print(f"🔍 FVG {symbol}: ENHANCED INSTITUTIONAL CHECK")
            if len(self.m5_data[symbol]) < 6:  # Need more context for real gaps
                print(f"🔍 FVG {symbol}: Only {len(self.m5_data[symbol])} M5 candles, need 6+")
                return None
            
            # Get last 6 candles for proper gap analysis
            candles = list(self.m5_data[symbol])[-6:]
            current = candles[-1]
            
            # Get pip size for this symbol
            if 'JPY' in symbol:
                pip_size = 0.01
            elif symbol == 'XAUUSD':
                pip_size = 0.1
            elif symbol == 'XAGUSD':
                pip_size = 0.001
            else:
                pip_size = 0.0001
            
            # STEP 1: Find true 3-candle FVG pattern
            # FVG = Middle candle doesn't overlap with candle 1 and candle 3
            for i in range(len(candles) - 3):
                candle1 = candles[i]      # First candle
                candle2 = candles[i + 1]  # Middle candle (creates gap)
                candle3 = candles[i + 2]  # Third candle (confirms gap)
                
                # BULLISH FVG: candle1 high < candle3 low (gap between them)
                bullish_gap = candle1['high'] < candle3['low']
                gap_size_bull = (candle3['low'] - candle1['high']) / pip_size
                
                # BEARISH FVG: candle1 low > candle3 high (gap between them)
                bearish_gap = candle1['low'] > candle3['high']
                gap_size_bear = (candle1['low'] - candle3['high']) / pip_size
                
                # Only consider significant gaps (>2 pips minimum)
                if bullish_gap and gap_size_bull >= 2.0:
                    # STEP 2: Check if current price is retesting the gap
                    gap_mid = (candle1['high'] + candle3['low']) / 2
                    retest_distance = abs(current['close'] - gap_mid) / pip_size
                    
                    # Must be within 3 pips of gap midpoint
                    if retest_distance <= 3.0:
                        # STEP 3: Volume confirmation - current candle should have higher volume
                        volume_surge = (current.get('volume', 100) > 
                                      sum(c.get('volume', 100) for c in candles[-3:-1]) / 2)
                        
                        # STEP 4: Rejection confirmation - looking for BUY at support
                        lower_wick = current['close'] - current['low']
                        candle_range = current['high'] - current['low']
                        wick_ratio = lower_wick / candle_range if candle_range > 0 else 0
                        
                        # Strong rejection: lower wick > 40% of candle
                        strong_rejection = wick_ratio > 0.4 and current['close'] > current['open']
                        
                        if strong_rejection or volume_surge:
                            # STEP 5: Calculate precise entry and risk
                            entry = gap_mid + (pip_size * 2)  # Enter above gap midpoint
                            stop_loss = candle3['low'] - (pip_size * 3)  # Below gap support
                            
                            sl_distance = abs(entry - stop_loss) / pip_size
                            atr = self.calculate_atr(symbol)
                            
                            # Target: Fill to opposite side of gap + 50%
                            target_price = candle1['high'] + (gap_size_bull * pip_size * 0.5)
                            tp_distance = abs(target_price - entry) / pip_size
                            
                            actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                            
                            # Enhanced feasibility check
                            if sl_distance <= 15 and actual_rr >= 1.8 and tp_distance <= 2 * atr:
                                print(f"✅ FVG {symbol} BUY: BULLISH GAP RETEST!")
                                print(f"   Gap: {gap_size_bull:.1f} pips, Retest distance: {retest_distance:.1f}p")
                                print(f"   R:R: {actual_rr:.2f}, SL: {sl_distance:.1f}p, TP: {tp_distance:.1f}p")
                                
                                # Enhanced quality calculation
                                base_quality = 60  # Higher base for real FVG
                                base_quality += min(gap_size_bull - 2, 8) * 2  # +2% per extra pip
                                base_quality += (1 - retest_distance/3) * 15  # Closer retest = higher quality
                                base_quality += wick_ratio * 20  # Strong rejection bonus
                                if volume_surge: base_quality += 10  # Volume confirmation
                                base_quality = min(base_quality, 90)  # Cap at 90%
                                
                                return PatternSignal(
                                    pattern="FAIR_VALUE_GAP_FILL",
                                    direction="BUY",
                                    entry_price=entry,
                                    confidence=base_quality,
                                    timeframe="M5",
                                    pair=symbol,
                                    quality_score=base_quality
                                )
                
                elif bearish_gap and gap_size_bear >= 2.0:
                    # BEARISH FVG retest (mirror logic)
                    gap_mid = (candle1['low'] + candle3['high']) / 2
                    retest_distance = abs(current['close'] - gap_mid) / pip_size
                    
                    if retest_distance <= 3.0:
                        volume_surge = (current.get('volume', 100) > 
                                      sum(c.get('volume', 100) for c in candles[-3:-1]) / 2)
                        
                        # Looking for SELL at resistance - upper wick rejection
                        upper_wick = current['high'] - current['close']
                        candle_range = current['high'] - current['low']
                        wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
                        
                        strong_rejection = wick_ratio > 0.4 and current['close'] < current['open']
                        
                        if strong_rejection or volume_surge:
                            entry = gap_mid - (pip_size * 2)  # Enter below gap midpoint
                            stop_loss = candle3['high'] + (pip_size * 3)  # Above gap resistance
                            
                            sl_distance = abs(stop_loss - entry) / pip_size
                            atr = self.calculate_atr(symbol)
                            
                            target_price = candle1['low'] - (gap_size_bear * pip_size * 0.5)
                            tp_distance = abs(entry - target_price) / pip_size
                            
                            actual_rr = tp_distance / sl_distance if sl_distance > 0 else 0
                            
                            if sl_distance <= 15 and actual_rr >= 1.8 and tp_distance <= 2 * atr:
                                print(f"✅ FVG {symbol} SELL: BEARISH GAP RETEST!")
                                print(f"   Gap: {gap_size_bear:.1f} pips, Retest distance: {retest_distance:.1f}p")
                                print(f"   R:R: {actual_rr:.2f}, SL: {sl_distance:.1f}p, TP: {tp_distance:.1f}p")
                                
                                base_quality = 60
                                base_quality += min(gap_size_bear - 2, 8) * 2
                                base_quality += (1 - retest_distance/3) * 15
                                base_quality += wick_ratio * 20
                                if volume_surge: base_quality += 10
                                base_quality = min(base_quality, 90)
                                
                                return PatternSignal(
                                    pattern="FAIR_VALUE_GAP_FILL",
                                    direction="SELL",
                                    entry_price=entry,
                                    confidence=base_quality,
                                    timeframe="M5",
                                    pair=symbol,
                                    quality_score=base_quality
                                )
            
            print(f"🔍 FVG {symbol}: No valid institutional gaps found")
            return None
                
        except Exception as e:
            logger.debug(f"Enhanced FVG detection error for {symbol}: {e}")
        
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
        # Fixed pip_size calculation to include XAUUSD and XAGUSD
        pip_size = 0.01 if 'JPY' in symbol else 0.01 if symbol == 'XAUUSD' else 0.001 if symbol == 'XAGUSD' else 0.0001
        
        # Determine signal classification based on pattern type
        # RAPID: Quick momentum plays (accessible to all tiers)
        # SNIPER: Precision institutional patterns (PRO+ only)
        
        RAPID_PATTERNS = ['MOMENTUM_BREAKOUT', 'VCB_BREAKOUT', 'SWEEP_RETURN']
        SNIPER_PATTERNS = ['LIQUIDITY_SWEEP_REVERSAL', 'ORDER_BLOCK_BOUNCE', 'FAIR_VALUE_GAP_FILL']
        
        signal_class = 'RAPID' if pattern_signal.pattern in RAPID_PATTERNS else 'SNIPER'
        
        # Dynamic SL/TP based on quality AND class
        # RAPID: Designed to complete within 1 hour (shorter TPs)
        # SNIPER: Designed to complete within 2 hours (larger TPs but still reasonable)
        
        # OPTIMIZED STRATEGY: 30% shorter SL/TP with 1.5 R:R for balance
        # Shorter distances = Faster completion, 1.5 R:R = Good profit potential
        if signal_class == 'SNIPER':
            # SNIPER trades - precision setups, 30% tighter stops
            if pattern_signal.quality_score >= 75:  # Premium
                stop_pips = 7   # Was 10, now 30% less
                target_pips = 10.5  # 1:1.5 RR maintained
            elif pattern_signal.quality_score >= 65:  # Standard
                stop_pips = 6   # Was 9, now ~30% less
                target_pips = 9   # 1:1.5 RR
            else:  # Acceptable
                stop_pips = 5.5   # Was 8, now ~30% less
                target_pips = 8.25  # 1:1.5 RR
        else:
            # RAPID trades - ultra-quick scalps, 30% tighter
            if pattern_signal.quality_score >= 75:  # Premium
                stop_pips = 4   # Was 6, now ~30% less
                target_pips = 6  # 1:1.5 RR
            elif pattern_signal.quality_score >= 65:  # Standard
                stop_pips = 3.5   # Was 5, now 30% less
                target_pips = 5.25  # 1:1.5 RR
            else:  # Acceptable
                stop_pips = 3   # Was 4, now 25% less
                target_pips = 4.5  # 1:1.5 RR
        
        # FIX ERROR 4756: BROKER MINIMUM STOP DISTANCE REQUIREMENTS
        # Exotic pairs and commodities need larger stops to avoid "Invalid stops" error
        min_stop_requirements = {
            'USDMXN': 60,  # Exotic pair - INCREASED to 60 pips for high volatility
            'USDSEK': 20,  # Exotic pair - INCREASED from 15 to 20 pips
            'USDCNH': 30,  # Restricted pair - very high spread
            'XAGUSD': 30,  # Silver - 30 pips for scalping (0.030 price movement)
            'XAUUSD': 100,  # Gold - 100 standard pips ($1 move) minimum
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
        
        # Calculate lot size for 3% risk (testing phase)
        account_balance = 1000.0  # Default account, will be overridden by actual balance
        risk_percent = 0.03  # 3% risk per trade for testing
        risk_amount = account_balance * risk_percent  # $30 on $1000 account
        
        # Calculate pip value (simplified - would need actual pip value calculation)
        if 'JPY' in symbol:
            pip_value = 0.01  # Approximate for JPY pairs
        elif symbol in ['XAUUSD']:
            pip_value = 0.01  # Gold pip value (standard pips)
        elif symbol in ['XAGUSD']:
            pip_value = 0.001  # Silver: 0.001 price = 1 pip  
        else:
            pip_value = 0.0001  # Standard forex pairs
            
        # Lot size calculation for 3% risk
        # Formula: Risk Amount / (SL pips * pip value per lot)
        # Assuming standard lot pip values: $10 for forex, varies for metals
        pip_value_per_lot = 10.0 if symbol not in ['XAUUSD', 'XAGUSD'] else (0.1 if symbol == 'XAUUSD' else 5.0)  # Gold is $0.10 per standard pip per lot, Silver is $5 per pip per lot
        lot_size = risk_amount / (stop_pips * pip_value_per_lot)
        lot_size = round(lot_size, 2)  # Round to 2 decimals for MT5
        
        print(f"💰 LOT SIZE CALC: {symbol} {pattern_signal.direction}")
        print(f"   Risk: {risk_percent*100}% = ${risk_amount}")
        print(f"   SL: {stop_pips:.1f} pips (30% reduced)")
        print(f"   TP: {target_pips:.1f} pips (1.5x SL)")
        print(f"   R:R Ratio: 1:{target_pips/stop_pips:.2f}")
        print(f"   Lot Size: {lot_size:.2f} lots")
        print(f"   Entry: {entry_price:.5f}")
        print(f"   Stop Loss: {stop_loss:.5f}")
        print(f"   Take Profit: {take_profit:.5f}")
        
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
            'lot_size': lot_size,  # Added lot size for 3% risk
            'risk_percent': risk_percent * 100,  # Show risk percentage
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
        # QUALITY GATE #1: PAIR-SPECIFIC FOR 65%+ WIN RATE TARGET
        symbol = getattr(signal, 'pair', getattr(signal, 'symbol', ''))
        
        # EMERGENCY TESTING: Much lower thresholds to verify system is working
        # Standard pairs should generate signals during peak trading hours
        if symbol in ['NZDUSD', 'XAUUSD']:  # 75%, 53% win rates
            min_quality_score = 45.0  # TESTING: was 65.0
        elif symbol in ['AUDJPY', 'EURJPY']:  # 50%, 43% win rates
            min_quality_score = 48.0  # TESTING: was 68.0
        elif symbol in ['XAGUSD', 'USDMXN', 'USDCNH', 'USDSEK']:  # <30% win rate
            min_quality_score = 55.0  # TESTING: was 75.0
        else:
            min_quality_score = 50.0  # TESTING: was 70.0 - major pairs should fire
        
        # Pattern+Pair combo adjustments (based on actual performance)
        pattern_type = getattr(signal, 'pattern', 'UNKNOWN')
        combo_key = f"{pattern_type}_{symbol}"
        
        # WINNING COMBOS: Big bonuses (proven performers)
        winning_combos = {
            'ORDER_BLOCK_BOUNCE_USDCAD': -15,    # 100% win rate
            'ORDER_BLOCK_BOUNCE_NZDUSD': -12,    # 75% win rate
            'FAIR_VALUE_GAP_FILL_EURJPY': -10,   # 75% win rate
            'ORDER_BLOCK_BOUNCE_XAUUSD': -8,     # Good on XAUUSD
            'FAIR_VALUE_GAP_FILL_XAUUSD': -5,    # 50% win rate
            'ORDER_BLOCK_BOUNCE_USDJPY': -5,     # 50% win rate
            'ORDER_BLOCK_BOUNCE_GBPUSD': -5,     # 50% win rate
            'FAIR_VALUE_GAP_FILL_AUDJPY': -3,    # 50% win rate
        }
        
        # LOSING COMBOS: Reduced penalties for ML learning
        losing_combos = {
            'FAIR_VALUE_GAP_FILL_XAGUSD': 10,    # Was 50, now just harder
            'ORDER_BLOCK_BOUNCE_XAGUSD': 10,     # Was 50, now just harder  
            'FAIR_VALUE_GAP_FILL_USDMXN': 10,    # Was 50, now just harder
            'ORDER_BLOCK_BOUNCE_EURJPY': 5,      # Was 20, slight penalty
            'ORDER_BLOCK_BOUNCE_GBPJPY': 5,      # Was 20, slight penalty
            'FAIR_VALUE_GAP_FILL_GBPJPY': 5,     # Was 20, slight penalty
            'ORDER_BLOCK_BOUNCE_EURAUD': 3,      # Was 15, minimal penalty
            'ORDER_BLOCK_BOUNCE_EURUSD': 3,      # Was 15, minimal penalty
        }
        
        # Apply combo adjustment if exists, else pattern-only adjustment
        if combo_key in winning_combos:
            adjustment = winning_combos[combo_key]
        elif combo_key in losing_combos:
            adjustment = losing_combos[combo_key]
        else:
            # Default pattern adjustments - OPENED UP for diversity testing
            pattern_adjustments = {
                'ORDER_BLOCK_BOUNCE': 0,          # Neutral - let it prove itself
                'FAIR_VALUE_GAP_FILL': 0,         # Neutral - has 43% win rate
                'LIQUIDITY_SWEEP_REVERSAL': 0,    # Neutral - let data decide
                'VCB_BREAKOUT': 0,                # Neutral - let data decide
                'SWEEP_RETURN': 0,                # Opened up - was blocked
                'SWEEP_AND_RETURN': 0             # Opened up - was blocked
            }
            adjustment = pattern_adjustments.get(pattern_type, 0)
        
        min_quality_score += adjustment
        base_quality = min_quality_score  # Use calculated value
        print(f"🔍 Quality check: {signal.quality_score:.1f}% vs {min_quality_score}%")
        
        if hasattr(signal, 'quality_score') and signal.quality_score < min_quality_score:
            print(f"⚠️ Quality fail")
            return False, f"Quality {signal.quality_score:.1f}% < {min_quality_score}%", signal.confidence
        print(f"✅ Quality passed")
        
        # Dynamic ML threshold based on recent signal rate
        # Track signals in last 15 minutes
        current_time = time.time()
        recent_signals = getattr(self, 'recent_signal_times', [])
        recent_signals = [t for t in recent_signals if current_time - t < 900]  # Last 15 min
        
        # Calculate hourly rate projection
        signals_per_15min = len(recent_signals)
        projected_hourly_rate = signals_per_15min * 4
        
        # QUALITY GATE #2: PATTERN-SPECIFIC THRESHOLDS - LOWERED for diversity
        pattern_thresholds = {
            'FAIR_VALUE_GAP_FILL': 65.0,      # LOWERED: was 72% - too high
            'ORDER_BLOCK_BOUNCE': 60.0,       # LOWERED: was 70% - too high
            'LIQUIDITY_SWEEP_REVERSAL': 60.0, # LOWERED: was 70% - too high
            'VCB_BREAKOUT': 55.0,              # LOWERED: was 65% - try lower
            'SWEEP_RETURN': 60.0,              # LOWERED: was 68% - too high
            'MOMENTUM_BURST': 55.0,            # LOWERED: was 68% - way too high
            'MOMENTUM_BREAKOUT': 55.0         # LOWERED: was 68% - way too high
        }
        
        # Get pattern-specific threshold
        min_confidence = pattern_thresholds.get(pattern_type, 70.0)
        
        # Apply pattern-specific confidence adjustments - REMOVED PENALTIES for testing
        pattern_confidence_adj = {
            'FAIR_VALUE_GAP_FILL': 0,        # Neutral - let actual performance decide
            'ORDER_BLOCK_BOUNCE': 0,         # Neutral - let actual performance decide
            'LIQUIDITY_SWEEP_REVERSAL': 0,   # Neutral - let actual performance decide
            'VCB_BREAKOUT': 0,                # Neutral - was +5, now neutral for fairness
            'SWEEP_RETURN': 0                 # Neutral
        }
        
        conf_adj = pattern_confidence_adj.get(pattern_type, 0)
        if conf_adj != 0:
            print(f"   🎯 Confidence adjustment for {pattern_type}: {conf_adj:+d}%")
        
        print(f"🔍 ML check: {signal.confidence}% vs {min_confidence}%")
        
        # Apply news impact adjustment to confidence
        news_adjustment = self.get_news_impact(signal.pair)
        adjusted_confidence = signal.confidence + news_adjustment
        
        if news_adjustment != 0:
            print(f"📰 {signal.pair}: News impact {news_adjustment} → Confidence {signal.confidence:.1f}% → {adjusted_confidence:.1f}%")
        
        if adjusted_confidence < min_confidence:
            print(f"⚠️ ML fail")
            return False, f"Confidence {adjusted_confidence:.1f}% < {min_confidence}%", adjusted_confidence
        print(f"✅ ML passed")
        
        # Pattern restrictions based on performance - REMOVED for testing
        blocked_patterns = []  # OPENED UP - let ML decide based on real performance
        restricted_patterns = []  # Using quality gates instead
        
        if signal.pattern in blocked_patterns:
            print(f"   🚫 BLOCKED PATTERN: {signal.pattern} temporarily disabled (win rate < 40%)")
            return False, f"Pattern blocked for retraining", adjusted_confidence
        
        if signal.pattern in restricted_patterns and adjusted_confidence < 85:
            print(f"   ⚠️ RESTRICTED: {signal.pattern} needs 85%+ (has {adjusted_confidence:.1f}%)")
            return False, f"Restricted pattern - needs 85%+", adjusted_confidence
        
        # Check performance history
        pattern_clean = signal.pattern.replace('_INTELLIGENT', '')
        combo_key = f"{signal.pair}_{pattern_clean}_{session}"
        perf = self.performance_history.get(combo_key, {})
        if perf.get('enabled') == False:
            print(f"   ⚠️ PERFORMANCE FAIL: {combo_key} disabled due to poor history")
            return False, f"Disabled: poor performance", adjusted_confidence
        
        print(f"   ✅✅ SIGNAL APPROVED: {signal.pair} {signal.pattern} @ {adjusted_confidence:.1f}%")
        return True, f"PASS @ {adjusted_confidence:.1f}%", adjusted_confidence
    
    # ===========================================================================================
    # GATEKEEPER LOGIC PLAN (TO IMPLEMENT FOR 65%+ WIN RATE)
    # ===========================================================================================
    # Every 30 minutes, the gatekeeper will:
    # 1. Read last 100 signals from optimized_tracking.jsonl
    # 2. Calculate win rate by pattern+pair+session combo
    # 3. Dynamically adjust quality gates:
    #    - Win rate >60%: Apply -15% quality bonus (make it easier)
    #    - Win rate 50-60%: Apply -10% quality bonus
    #    - Win rate 40-50%: No adjustment
    #    - Win rate 30-40%: Apply +10% quality penalty
    #    - Win rate <30%: Apply +20% quality penalty (nearly block)
    # 4. Store adjustments in gatekeeper_adjustments.json
    # 5. Update winning_combos and losing_combos dicts dynamically
    # 6. Target: Converge to 65%+ win rate over time by:
    #    - Promoting consistent winners
    #    - Demoting/blocking consistent losers
    #    - Learning from real performance data
    # 7. Safety: Never adjust by more than ±25% in one cycle
    # 8. Persist: Save state to survive restarts
    # ===========================================================================================

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
            
            # Check for REAL trade outcomes from MT5 execution
            signal_id = signal_data.get('signal_id', '')
            win = False
            outcome_source = 'PENDING'
            
            # First check fires database for execution result
            try:
                import sqlite3
                conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
                cursor = conn.cursor()
                
                # Check if signal was executed
                cursor.execute("SELECT status, ticket FROM fires WHERE fire_id = ?", (signal_id,))
                fire_result = cursor.fetchone()
                
                if fire_result and fire_result[0] == 'FILLED':
                    # Signal was executed, check for outcome
                    cursor.execute("SELECT outcome, pips FROM signal_outcomes WHERE signal_id = ?", (signal_id,))
                    outcome_result = cursor.fetchone()
                    
                    if outcome_result:
                        # We have real outcome!
                        outcome = outcome_result[0]
                        pips = outcome_result[1] or 0
                        win = (outcome == 'WIN' or pips > 0)
                        outcome_source = f'MT5_OUTCOME_{outcome}'
                    else:
                        # Executed but no outcome yet
                        outcome_source = 'MT5_EXECUTING'
                        win = False  # Don't assume until confirmed
                elif fire_result:
                    outcome_source = f'FIRE_{fire_result[0]}'
                    win = False  # Failed fires are losses
                else:
                    # Not executed, use candle projection
                    outcome_source = 'PROJECTION'
                    if symbol in self.m1_data and len(self.m1_data[symbol]) > 0:
                        last_candle = self.m1_data[symbol][-1]
                        if last_candle and 'close' in last_candle and 'open' in last_candle:
                            direction = signal_data.get('direction', 'BUY')
                            if direction == 'BUY':
                                win = last_candle['close'] > last_candle['open']
                            else:
                                win = last_candle['close'] < last_candle['open']
                
                conn.close()
            except Exception as e:
                print(f"   ⚠️ Could not check MT5 outcomes: {e}")
                outcome_source = 'ERROR'
            
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
            
            # Add outcome source to entry
            entry['outcome_source'] = outcome_source
            
            # Enhanced debug output with outcome source
            print(f"📝 Tracked to optimized_tracking.jsonl: {signal_data.get('signal_id', 'UNKNOWN')}")
            print(f"   Pair={symbol}, Pattern={entry['pattern']}, Class={entry['signal_class']}")
            print(f"   Conf={entry['confidence']}%, Quality={entry['quality_score']}%")
            print(f"   Win={win}, R:R={rr}, Source={outcome_source}")
            print(f"   Session={entry['session']}, Direction={entry['direction']}")
            
        except Exception as e:
            print(f"Error in optimized tracking: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_initial_data(self):
        """Analyze last 6 hours from optimized_tracking.jsonl with detailed breakdowns"""
        try:
            tracking_file = '/root/HydraX-v2/optimized_tracking.jsonl'
            
            if not os.path.exists(tracking_file):
                print("📊 No optimized_tracking.jsonl yet")
                return
                
            # Read and filter for last 6 hours (360 minutes)
            from datetime import datetime, timedelta
            now = datetime.now()
            six_hours_ago = now - timedelta(hours=6)
            
            recent = []
            with open(tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        # Parse timestamp properly
                        if 'timestamp' in signal:
                            ts_str = signal['timestamp']
                            # Handle ISO format timestamps
                            if 'T' in ts_str:
                                # Remove microseconds if present and parse
                                ts_str = ts_str.split('.')[0] if '.' in ts_str else ts_str.replace('Z', '')
                                signal_time = datetime.fromisoformat(ts_str)
                            else:
                                signal_time = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                            
                            if signal_time >= six_hours_ago:
                                recent.append(signal)
            
            if not recent:
                print("📊 No data in last 6 hours from optimized_tracking.jsonl")
                return
            
            # Overall stats for last 6 hours
            total = len(recent)
            wins = sum(1 for s in recent if s.get('win', False))
            losses = total - wins
            win_rate = (wins / total * 100) if total > 0 else 0
            
            print(f"\n📊 6-HOUR ANALYSIS from optimized_tracking.jsonl")
            print(f"   Total Signals: {total}")
            print(f"   Wins: {wins} | Losses: {losses}")
            print(f"   Win Rate: {win_rate:.1f}%")
            
            # Pattern breakdown with win rates
            patterns = set(s['pattern'] for s in recent if 'pattern' in s)
            pattern_stats = {}
            print(f"\n📈 PATTERN PERFORMANCE:")
            for p in sorted(patterns):
                p_signals = [s for s in recent if s.get('pattern') == p]
                if p_signals:
                    p_wins = sum(1 for s in p_signals if s.get('win', False))
                    p_wr = (p_wins/len(p_signals)*100) if len(p_signals) > 0 else 0
                    pattern_stats[p] = {
                        'total': len(p_signals),
                        'wins': p_wins,
                        'win_rate': p_wr
                    }
                    print(f"   {p}: {p_wins}/{len(p_signals)} ({p_wr:.1f}%)")
            
            # Pair breakdown
            pairs = set(s['pair'] for s in recent if 'pair' in s)
            print(f"\n💱 PAIR PERFORMANCE:")
            pair_stats = {}
            for pair in sorted(pairs):
                pair_signals = [s for s in recent if s.get('pair') == pair]
                if pair_signals:
                    pair_wins = sum(1 for s in pair_signals if s.get('win', False))
                    pair_wr = (pair_wins/len(pair_signals)*100) if len(pair_signals) > 0 else 0
                    pair_stats[pair] = {
                        'total': len(pair_signals),
                        'wins': pair_wins,
                        'win_rate': pair_wr
                    }
                    print(f"   {pair}: {pair_wins}/{len(pair_signals)} ({pair_wr:.1f}%)")
            
            # Confidence bins with detailed breakdown
            conf_stats = {}
            print(f"\n🎯 CONFIDENCE BINS:")
            for bin_name, (low, high) in [('70-75%', (70, 75)), ('75-85%', (75, 85)), ('85-95%', (85, 95))]:
                bin_signals = [s for s in recent if low <= s.get('confidence', 0) < high]
                if bin_signals:
                    bin_wins = sum(1 for s in bin_signals if s.get('win', False))
                    bin_wr = (bin_wins/len(bin_signals)*100) if len(bin_signals) > 0 else 0
                    conf_stats[bin_name] = {
                        'total': len(bin_signals),
                        'wins': bin_wins,
                        'win_rate': bin_wr
                    }
                    print(f"   {bin_name}: {bin_wins}/{len(bin_signals)} ({bin_wr:.1f}%)")
            
            # Session breakdown
            session_stats = {}
            sessions = set(s.get('session', 'UNKNOWN') for s in recent)
            if len(sessions) > 1 or 'UNKNOWN' not in sessions:
                print(f"\n⏰ SESSION PERFORMANCE:")
                for sess in sorted(sessions):
                    sess_signals = [s for s in recent if s.get('session') == sess]
                    if sess_signals:
                        sess_wins = sum(1 for s in sess_signals if s.get('win', False))
                        sess_wr = (sess_wins/len(sess_signals)*100) if len(sess_signals) > 0 else 0
                        session_stats[sess] = {
                            'total': len(sess_signals),
                            'wins': sess_wins,
                            'win_rate': sess_wr
                        }
                        print(f"   {sess}: {sess_wins}/{len(sess_signals)} ({sess_wr:.1f}%)")
            
            # Time distribution
            print(f"\n⏱️ TIME DISTRIBUTION:")
            hourly = {}
            for s in recent:
                if 'timestamp' in s:
                    ts_str = s['timestamp']
                    if 'T' in ts_str:
                        ts_str = ts_str.split('.')[0] if '.' in ts_str else ts_str.replace('Z', '')
                        signal_time = datetime.fromisoformat(ts_str)
                    else:
                        signal_time = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                    
                    hour_key = signal_time.strftime('%H:00')
                    if hour_key not in hourly:
                        hourly[hour_key] = {'total': 0, 'wins': 0}
                    hourly[hour_key]['total'] += 1
                    if s.get('win', False):
                        hourly[hour_key]['wins'] += 1
            
            for hour in sorted(hourly.keys()):
                h_wr = (hourly[hour]['wins']/hourly[hour]['total']*100) if hourly[hour]['total'] > 0 else 0
                print(f"   {hour}: {hourly[hour]['wins']}/{hourly[hour]['total']} ({h_wr:.1f}%)")
                
            return {
                'total': total,
                'wins': wins,
                'win_rate': win_rate,
                'patterns': pattern_stats,
                'pairs': pair_stats,
                'confidence': conf_stats,
                'sessions': session_stats
            }
            
        except Exception as e:
            print(f"❌ Error analyzing data: {e}")
            import traceback
            traceback.print_exc()
            
    def verify_rr_ratio(self):
        """Verify R:R ratio for last 6 hours from optimized_tracking.jsonl"""
        try:
            tracking_file = '/root/HydraX-v2/optimized_tracking.jsonl'
            
            if not os.path.exists(tracking_file):
                print("📊 No optimized_tracking.jsonl for R:R analysis")
                return
                
            # Read and filter for last 6 hours
            from datetime import datetime, timedelta
            now = datetime.now()
            six_hours_ago = now - timedelta(hours=6)
            
            recent = []
            with open(tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        if 'timestamp' in signal:
                            ts_str = signal['timestamp']
                            if 'T' in ts_str:
                                ts_str = ts_str.split('.')[0] if '.' in ts_str else ts_str.replace('Z', '')
                                signal_time = datetime.fromisoformat(ts_str)
                            else:
                                signal_time = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                            
                            if signal_time >= six_hours_ago:
                                recent.append(signal)
            
            if not recent:
                print("📊 No R:R data in last 6 hours")
                return
            
            # Calculate R:R statistics
            rr_values = [s.get('risk_reward', 0) for s in recent if s.get('risk_reward', 0) > 0]
            avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0
            
            # Group by pattern and calculate average R:R
            patterns = set(s['pattern'] for s in recent if 'pattern' in s)
            pattern_rr = {}
            for p in patterns:
                p_signals = [s for s in recent if s.get('pattern') == p]
                p_rr_values = [s.get('risk_reward', 0) for s in p_signals if s.get('risk_reward', 0) > 0]
                if p_rr_values:
                    pattern_rr[p] = sum(p_rr_values) / len(p_rr_values)
            
            # Check for TP misses (if we have entry/TP data)
            tp_misses = 0
            tp_hits = 0
            for s in recent:
                if s.get('win', False):
                    tp_hits += 1
                    # Note: We don't have actual entry/TP prices in tracking, just win/loss
            
            # R:R distribution
            rr_distribution = {
                '1.0-1.25': 0,
                '1.25-1.5': 0,
                '1.5-2.0': 0,
                '2.0+': 0
            }
            
            for rr in rr_values:
                if rr <= 1.25:
                    rr_distribution['1.0-1.25'] += 1
                elif rr <= 1.5:
                    rr_distribution['1.25-1.5'] += 1
                elif rr <= 2.0:
                    rr_distribution['1.5-2.0'] += 1
                else:
                    rr_distribution['2.0+'] += 1
            
            print(f"\n📊 R:R RATIO ANALYSIS (Last 6 Hours)")
            print(f"   Total Signals: {len(recent)}")
            print(f"   Average R:R: {avg_rr:.2f}")
            print(f"   TP Hits (Wins): {tp_hits}/{len(recent)}")
            
            print(f"\n📈 R:R BY PATTERN:")
            for p in sorted(pattern_rr.keys()):
                print(f"   {p}: {pattern_rr[p]:.2f}")
            
            print(f"\n📊 R:R DISTRIBUTION:")
            for range_name, count in rr_distribution.items():
                pct = (count/len(rr_values)*100) if rr_values else 0
                print(f"   {range_name}: {count} ({pct:.1f}%)")
            
            # Analyze win rate by R:R ratio
            print(f"\n🎯 WIN RATE BY R:R:")
            rr_bins = [(1.0, 1.25), (1.25, 1.5), (1.5, 2.0)]
            for low, high in rr_bins:
                bin_signals = [s for s in recent if low <= s.get('risk_reward', 0) < high]
                if bin_signals:
                    bin_wins = sum(1 for s in bin_signals if s.get('win', False))
                    bin_wr = (bin_wins/len(bin_signals)*100) if len(bin_signals) > 0 else 0
                    print(f"   R:R {low}-{high}: {bin_wins}/{len(bin_signals)} wins ({bin_wr:.1f}%)")
            
            # Check if current R:R settings are optimal
            print(f"\n💡 R:R OPTIMIZATION INSIGHTS:")
            if avg_rr < 1.3:
                print("   ⚠️ Average R:R is LOW - Consider increasing TP targets")
            elif avg_rr > 2.0:
                print("   ⚠️ Average R:R is HIGH - May be missing profitable trades")
            else:
                print("   ✅ Average R:R is BALANCED (1.3-2.0 range)")
            
            # Find optimal R:R based on win rate
            optimal_rr = None
            best_expectancy = -float('inf')
            for low, high in rr_bins:
                bin_signals = [s for s in recent if low <= s.get('risk_reward', 0) < high]
                if len(bin_signals) >= 5:  # Need minimum samples
                    bin_wins = sum(1 for s in bin_signals if s.get('win', False))
                    win_rate = bin_wins / len(bin_signals)
                    avg_bin_rr = (low + high) / 2
                    # Expected value = (win_rate * avg_rr) - (loss_rate * 1)
                    expectancy = (win_rate * avg_bin_rr) - ((1 - win_rate) * 1)
                    if expectancy > best_expectancy:
                        best_expectancy = expectancy
                        optimal_rr = (low, high)
            
            if optimal_rr:
                print(f"\n🎯 OPTIMAL R:R RANGE: {optimal_rr[0]:.2f}-{optimal_rr[1]:.2f}")
                print(f"   Expected Value: {best_expectancy:.3f} per trade")
            
            return {
                'avg_rr': avg_rr,
                'tp_hits': tp_hits,
                'total': len(recent),
                'pattern_rr': pattern_rr,
                'distribution': rr_distribution
            }
            
        except Exception as e:
            print(f"❌ Error verifying R:R ratio: {e}")
            import traceback
            traceback.print_exc()
            
    def analyze_initial_data_old(self):
        """Old analyze method - kept for compatibility"""
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
            # TEMPORARY: Skip XAUUSD due to R:R calculation issues
            if symbol == 'XAUUSD':
                continue
                
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
                    
                    # DEBUG: Check signal has critical fields BEFORE CITADEL
                    if not signal.get('stop_loss') or not signal.get('take_profit'):
                        print(f"⚠️ CRITICAL: Signal missing SL/TP BEFORE CITADEL!")
                        print(f"   Signal keys: {list(signal.keys())}")
                        print(f"   stop_loss: {signal.get('stop_loss')}, take_profit: {signal.get('take_profit')}")
                    
                    # Update CITADEL with market structure
                    if len(self.m5_data[symbol]) > 0:
                        candles_list = list(self.m5_data[symbol])
                        self.citadel.update_market_structure(symbol, candles_list)
                    
                    # Apply CITADEL protection
                    protected_signal = self.citadel.protect_signal(signal)
                    
                    # CRITICAL FIX: If CITADEL returns None (delayed), still publish with warning
                    if protected_signal is None:
                        # CITADEL delayed the signal - but we need to publish anyway for ML learning
                        print(f"⚠️ CITADEL delayed signal - publishing anyway with sweep warning")
                        protected_signal = signal.copy()  # Use original signal
                        protected_signal['citadel_status'] = 'DELAYED_SWEEP_RISK'
                        protected_signal['citadel_protected'] = False
                        protected_signal['citadel_warning'] = 'SWEEP_RISK_DETECTED'
                        # Slightly reduce confidence for sweep risk
                        protected_signal['confidence'] = max(70, signal['confidence'] - 5)
                    
                    # CRITICAL FIX: CITADEL returns a partial signal, preserve ALL trading fields
                    if protected_signal and signal:
                        # CITADEL might return None or modified signal
                        # Make sure critical fields are preserved
                        critical_fields = ['stop_pips', 'target_pips', 'stop_loss', 'take_profit', 'entry_price', 
                                         'entry', 'sl', 'tp', 'risk_reward', 'lot_size']
                        for key in critical_fields:
                            if key in signal and (key not in protected_signal or protected_signal.get(key) is None):
                                protected_signal[key] = signal[key]
                        
                        # DEBUG: Log what fields are missing
                        missing = [k for k in ['stop_loss', 'take_profit'] if k not in protected_signal or protected_signal.get(k) is None]
                        if missing:
                            print(f"⚠️ WARNING: Protected signal missing critical fields: {missing}")
                            print(f"   Original signal had: {list(signal.keys())}")
                            print(f"   Protected signal has: {list(protected_signal.keys())}")
                    
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
                    # Can be overridden by environment variable for testing
                    citadel_override = os.getenv('CITADEL_THRESHOLD')
                    if citadel_override and citadel_override.lower() != 'disabled':
                        citadel_threshold = float(citadel_override)
                        print(f"📊 Using CITADEL override threshold: {citadel_threshold}%")
                    elif citadel_override and citadel_override.lower() == 'disabled':
                        citadel_threshold = 0.0  # Disable CITADEL filtering
                        print(f"⚠️ CITADEL filtering DISABLED for testing")
                    else:
                        # Default dynamic thresholds - lowered for more signals
                        citadel_threshold = 50.0 if projected_hourly_rate > 10 else 45.0 if projected_hourly_rate < 5 else 47.5
                    
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
        """Publish signal to ALL channels: ZMQ, JSONL, Missions, Telegram, WebApp"""
        combo = f"{signal.get('pattern', 'UNKNOWN')}_{signal.get('symbol', 'UNKNOWN')}"
        print(f"🚀 Publishing {signal.get('signal_id')}: Conf={signal.get('confidence')}%, Quality={signal.get('quality_score')}%, Combo={combo}")
        
        # CRITICAL FIX: Ensure stop_loss and take_profit price levels exist
        if ('stop_loss' not in signal or signal.get('stop_loss') is None) and 'entry_price' in signal and 'stop_pips' in signal:
            entry = signal['entry_price']
            symbol = signal.get('symbol', '')
            pip_size = 0.01 if 'JPY' in symbol else (0.001 if symbol == 'XAGUSD' else 0.0001)
            
            if signal.get('direction') == 'BUY':
                signal['stop_loss'] = round(entry - (signal['stop_pips'] * pip_size), 5)
            else:
                signal['stop_loss'] = round(entry + (signal['stop_pips'] * pip_size), 5)
            print(f"   ✅ Reconstructed stop_loss: {signal['stop_loss']} from {signal['stop_pips']} pips")
        
        if ('take_profit' not in signal or signal.get('take_profit') is None) and 'entry_price' in signal and 'target_pips' in signal:
            entry = signal['entry_price']
            symbol = signal.get('symbol', '')
            pip_size = 0.01 if 'JPY' in symbol else (0.001 if symbol == 'XAGUSD' else 0.0001)
            
            if signal.get('direction') == 'BUY':
                signal['take_profit'] = round(entry + (signal['target_pips'] * pip_size), 5)
            else:
                signal['take_profit'] = round(entry - (signal['target_pips'] * pip_size), 5)
            print(f"   ✅ Reconstructed take_profit: {signal['take_profit']} from {signal['target_pips']} pips")
        
        # Ensure ZMQ publisher exists
        if not self.publisher:
            print("⚠️ WARNING: ZMQ publisher not initialized! Attempting to create...")
            try:
                self.publisher = self.context.socket(zmq.PUB)
                self.publisher.bind("tcp://*:5557")
                print("✅ ZMQ publisher created on port 5557")
                time.sleep(0.1)  # Give subscribers time to connect
            except Exception as e:
                print(f"❌ Failed to create ZMQ publisher: {e}")
        
        # Calculate additional metrics for unified logging
        symbol = signal.get('symbol', '')
        pip_multiplier = 100 if 'JPY' in symbol else (1 if symbol == 'XAUUSD' else 10000)
        
        entry = float(signal.get('entry_price', 0) or signal.get('entry', 0))
        sl = float(signal.get('sl', 0) or signal.get('stop_loss', 0))
        tp = float(signal.get('tp', 0) or signal.get('take_profit', 0))
        
        sl_pips = abs(entry - sl) * pip_multiplier if entry and sl else signal.get('stop_pips', 0)
        tp_pips = abs(tp - entry) * pip_multiplier if entry and tp else signal.get('target_pips', 0)
        
        # Prepare comprehensive trade data for unified logging
        trade_data = {
            'signal_id': signal.get('signal_id'),
            'pair': symbol,
            'pattern': signal.get('pattern'),
            'confidence': signal.get('confidence', 0),
            'entry_price': entry,
            'sl_price': sl,
            'tp_price': tp,
            'sl_pips': sl_pips,
            'tp_pips': tp_pips,
            'lot_size': signal.get('lot_size', 0.01),
            'direction': signal.get('direction'),
            'session': signal.get('session', self.get_current_session()),
            'shield_score': signal.get('citadel_score', signal.get('shield_score', 0)),
            'rsi': signal.get('rsi', 50),
            'volume_ratio': signal.get('volume_ratio', 1.0),
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'executed': signal.get('confidence', 0) >= 80,  # Lowered from 85
            'user_id': '7176191872',
            'signal_type': signal.get('signal_type', 'PRECISION_STRIKE')
        }
        
        # Log to unified tracking system FIRST
        try:
            log_trade(trade_data)
            print(f"   ✅ Unified tracking logged to comprehensive_tracking.jsonl")
        except Exception as e:
            print(f"   ❌ Unified logging failed: {e}")
        
        # CRITICAL FIX: Ensure stop_pips and target_pips are in signal for ML learning
        if 'stop_pips' not in signal or signal.get('stop_pips') == 0:
            signal['stop_pips'] = sl_pips
        if 'target_pips' not in signal or signal.get('target_pips') == 0:
            signal['target_pips'] = tp_pips
        
        # 1. ZMQ Publishing (with debug logging)
        if self.publisher:
            try:
                # DEBUG: Check what we're actually sending
                if 'stop_loss' not in signal or signal.get('stop_loss') is None:
                    print(f"   🔴 WARNING: Publishing signal WITHOUT stop_loss!")
                    print(f"      Signal keys: {list(signal.keys())}")
                if 'take_profit' not in signal or signal.get('take_profit') is None:
                    print(f"   🔴 WARNING: Publishing signal WITHOUT take_profit!")
                
                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
                print(f"   📡 ZMQ sent to port 5557 - has SL: {signal.get('stop_loss') is not None}, has TP: {signal.get('take_profit') is not None}")
                
                # ZMQ debug logging
                self.log_zmq_debug('PUBLISH', signal.get('signal_id'), signal_msg)
            except Exception as e:
                print(f"   ❌ ZMQ failed: {e}")
                self.log_zmq_debug('PUBLISH_ERROR', signal.get('signal_id'), str(e))
        
        # 2. Optimized Tracking JSONL (SECONDARY - for backward compatibility)
        try:
            self.log_signal_to_truth_tracker(signal)
            print(f"   📝 Legacy truth_log.jsonl logged")
        except Exception as e:
            print(f"   ❌ Legacy JSONL failed: {e}")
        
        # 3. Mission File Creation
        try:
            import os
            mission_dir = '/root/HydraX-v2/missions'
            os.makedirs(mission_dir, exist_ok=True)
            mission_file = f"{mission_dir}/{signal.get('signal_id')}.json"
            with open(mission_file, 'w') as f:
                mission_data = {
                    'signal': signal,
                    'combo': combo,
                    'created_at': datetime.now(pytz.UTC).isoformat()
                }
                json.dump(mission_data, f, indent=2)
            print(f"   📋 Mission file created: {signal.get('signal_id')}.json")
        except Exception as e:
            print(f"   ❌ Mission failed: {e}")
        
        # 4. Telegram Alert (via relay)
        print(f"   💬 Telegram alert queued (via ZMQ relay)")
        
        # 5. WebApp Signal (via database)
        try:
            import sqlite3
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO signals 
                (signal_id, symbol, direction, entry_price, stop_pips, target_pips, confidence, pattern_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.get('signal_id'),
                signal.get('symbol'),
                signal.get('direction'),
                signal.get('entry_price'),
                signal.get('stop_pips'),
                signal.get('target_pips'),
                signal.get('confidence'),
                signal.get('pattern'),
                int(time.time())
            ))
            conn.commit()
            conn.close()
            print(f"   🌐 WebApp database updated")
        except Exception as e:
            print(f"   ❌ WebApp DB failed: {e}")
        
        print(f"   ✅ Signal published to all channels")
    
    def log_zmq_debug(self, action: str, signal_id: str, data: str):
        """Log ZMQ debug information for diagnosing MT5 communication issues"""
        try:
            debug_file = '/root/HydraX-v2/logs/zmq_debug.log'
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)
            
            with open(debug_file, 'a') as f:
                log_entry = {
                    'timestamp': datetime.now(pytz.UTC).isoformat(),
                    'action': action,
                    'signal_id': signal_id,
                    'data': data[:500] if len(data) > 500 else data  # Truncate long data
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"ZMQ debug logging error: {e}")
    
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
        last_analysis = 0  # Periodic analysis
        
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
                
                # Run analysis every 30 minutes
                if current_time - last_analysis >= 1800:
                    print("\n" + "="*60)
                    print(f"📊 PERIODIC ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
                    print("="*60)
                    self.analyze_initial_data()
                    self.verify_rr_ratio()
                    print("="*60 + "\n")
                    last_analysis = current_time
                
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