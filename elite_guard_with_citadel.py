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
        
        # Load candle cache on startup
        self.load_candles()
        self.hourly_signal_count = defaultdict(int)  # Track signals per hour
        self.current_hour = datetime.now().hour
        
        # News calendar for confidence adjustment (Forex Factory API)
        self.news_client = NewsAPIClient()
        self.news_events = []
        self.last_news_fetch = 0
        
        # Quality tracking
        self.pattern_performance = defaultdict(lambda: {'wins': 0, 'losses': 0})
        
        # Balanced thresholds (less strict than optimized)
        # Define trading pairs to monitor (FOREX ONLY + Gold)
        self.trading_pairs = [
            # ACTUAL symbols from ZMQ feed
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
            "EURJPY", "GBPJPY", "USDCNH", "USDSEK", "XAUUSD"
            # Skip crypto (BTCUSD, ETHUSD, XRPUSD) - forex only
        ]
        
        self.MIN_MOMENTUM = 0    # Disabled for testing
        self.MIN_VOLUME = 0      # Disabled for testing
        self.MIN_TREND = 0       # Disabled for testing
        self.MIN_CONFIDENCE = 25 # LOWERED for more signals
        self.COOLDOWN_MINUTES = 3 # SHORTER cooldown for more frequency
        
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
    
    def calculate_quality_score(self, signal: PatternSignal) -> float:
        """Calculate overall quality score for ranking"""
        score = 0
        
        # Base pattern confidence
        score += signal.confidence * 0.3
        
        # Momentum contribution
        if signal.momentum_score > 25:
            score += 20
        elif signal.momentum_score > 15:
            score += 10
        
        # Volume quality
        if signal.volume_quality > 20:
            score += 15
        elif signal.volume_quality > 10:
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
        """Less strict momentum calculation"""
        try:
            if symbol not in self.candles or 'M1' not in self.candles[symbol]:
                return 0
                
            candles = self.candles[symbol]['M1']
            if len(candles) < 5:
                return 0
            
            recent = list(candles.values())[-5:]
            
            # 3-bar momentum
            momentum_3 = (recent[-1]['close'] - recent[-3]['close']) / recent[-3]['close'] * 100
            
            # Direction check (less strict)
            if direction == "BUY" and momentum_3 > 0:
                return abs(momentum_3) * 10
            elif direction == "SELL" and momentum_3 < 0:
                return abs(momentum_3) * 10
            
            return 5  # Small base score even if momentum is weak
            
        except:
            return 0
    
    def analyze_volume_profile(self, symbol: str) -> float:
        """Less strict volume analysis"""
        try:
            if symbol not in self.candles or 'M1' not in self.candles[symbol]:
                return 10  # Default minimum score
                
            candles = self.candles[symbol]['M1']
            if len(candles) < 10:
                return 10
            
            recent = list(candles.values())[-10:]
            volumes = [c.get('tick_volume', 0) for c in recent]
            
            if not volumes or np.mean(volumes) == 0:
                return 10
            
            # Current vs average
            current_vol = volumes[-1]
            avg_vol = np.mean(volumes[:-1])
            
            if avg_vol > 0:
                vol_ratio = current_vol / avg_vol
                if vol_ratio > 1.2:  # Just 20% above average (was 30%)
                    return min(50, vol_ratio * 15)
                elif vol_ratio > 1.1:
                    return 15
            
            return 10
            
        except:
            return 10
    
    def detect_liquidity_sweep_reversal(self, symbol: str) -> Optional[PatternSignal]:
        """Detect liquidity sweep with balanced requirements"""
        try:
            if len(self.m5_data[symbol]) < 2:  # LOWERED  # Need at least 3 M5 candles
                logger.debug(f"LSR: {symbol} has only {len(self.m5_data[symbol])} M5 candles, need 3")
                return None
                
            recent_candles = list(self.m5_data[symbol])[-10:]
            
            # Find recent high/low
            recent_high = max(c['high'] for c in recent_candles[:-1])
            recent_low = min(c['low'] for c in recent_candles[:-1])
            current_candle = recent_candles[-1]
            
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            
            # BULLISH: Sweep below low and recovery
            if current_candle['low'] < recent_low - (2 * pip_size):  # Less strict
                sweep_depth = (recent_low - current_candle['low']) / pip_size
                
                if sweep_depth >= 2 and current_candle['close'] > recent_low:  # Reduced from 3 pips
                    # Check momentum
                    momentum = self.calculate_momentum_score(symbol, "BUY")
                    if momentum < self.MIN_MOMENTUM:
                        return None
                    
                    # Check volume
                    volume_quality = self.analyze_volume_profile(symbol)
                    if volume_quality < self.MIN_VOLUME:
                        return None
                    
                    entry_price = current_candle['close'] + pip_size  # Entry above close
                    
                    confidence = 65 + (momentum * 0.2) + (volume_quality * 0.1)  # LOWERED base
                    
                    signal = PatternSignal(
                        pattern="LIQUIDITY_SWEEP_REVERSAL",
                        direction="BUY",
                        entry_price=entry_price,
                        confidence=min(85, confidence),  # Cap at 85
                        timeframe="M5",
                        pair=symbol,
                        momentum_score=momentum,
                        volume_quality=volume_quality
                    )
                    signal.quality_score = self.calculate_quality_score(signal)
                    return signal
            
            # BEARISH: Sweep above high and rejection
            elif current_candle['high'] > recent_high + (2 * pip_size):
                sweep_height = (current_candle['high'] - recent_high) / pip_size
                
                if sweep_height >= 2 and current_candle['close'] < recent_high:
                    momentum = self.calculate_momentum_score(symbol, "SELL")
                    if momentum < self.MIN_MOMENTUM:
                        return None
                    
                    volume_quality = self.analyze_volume_profile(symbol)
                    if volume_quality < self.MIN_VOLUME:
                        return None
                    
                    entry_price = current_candle['close'] - pip_size
                    
                    confidence = 65 + (momentum * 0.2) + (volume_quality * 0.1)  # LOWERED base
                    
                    signal = PatternSignal(
                        pattern="LIQUIDITY_SWEEP_REVERSAL",
                        direction="SELL",
                        entry_price=entry_price,
                        confidence=min(85, confidence),
                        timeframe="M5",
                        pair=symbol,
                        momentum_score=momentum,
                        volume_quality=volume_quality
                    )
                    signal.quality_score = self.calculate_quality_score(signal)
                    return signal
                    
        except Exception as e:
            logger.debug(f"Error in liquidity sweep: {e}")
        
        return None
    
    def detect_order_block_bounce(self, symbol: str) -> Optional[PatternSignal]:
        """Detect order block patterns with balanced requirements"""
        try:
            if len(self.m5_data[symbol]) < 2:  # LOWERED
                return None
                
            candles = list(self.m5_data[symbol])
            if len(candles) < 4:  # Reduced from 15 for faster signals
                return None
                
            recent_candles = list(candles.values())[-15:]
            
            # Find strong moves (order blocks)
            for i in range(5, 12):  # Look back 5-12 candles
                candle = recent_candles[i]
                candle_range = candle['high'] - candle['low']
                
                # Significant candle (order block candidate)
                if candle_range > 0:
                    body = abs(candle['close'] - candle['open'])
                    if body / candle_range > 0.6:  # Strong body (reduced from 0.7)
                        
                        # Define order block zone
                        block_high = candle['high']
                        block_low = candle['low']
                        block_range = block_high - block_low
                        current_price = recent_candles[-1]['close']
                        
                        # BULLISH: Price at support zone
                        if block_low <= current_price <= block_low + (block_range * 0.4):
                            direction = "BUY"
                            
                            # Check momentum
                            momentum = self.calculate_momentum_score(symbol, direction)
                            if momentum < self.MIN_MOMENTUM:
                                continue
                            
                            # Volume check
                            volume_quality = self.analyze_volume_profile(symbol)
                            if volume_quality < self.MIN_VOLUME:
                                continue
                            
                            pip_size = 0.01 if 'JPY' in symbol else 0.0001
                            entry_price = current_price + pip_size
                            
                            confidence = 60 + (momentum * 0.2) + (volume_quality * 0.1)  # LOWERED
                            
                            signal = PatternSignal(
                                pattern="ORDER_BLOCK_BOUNCE",
                                direction=direction,
                                entry_price=entry_price,
                                confidence=min(80, confidence),
                                timeframe="M5",
                                pair=symbol,
                                momentum_score=momentum,
                                volume_quality=volume_quality
                            )
                            signal.quality_score = self.calculate_quality_score(signal)
                            return signal
                        
                        # BEARISH: Price at resistance zone
                        elif block_high - (block_range * 0.4) <= current_price <= block_high:
                            direction = "SELL"
                            
                            momentum = self.calculate_momentum_score(symbol, direction)
                            if momentum < self.MIN_MOMENTUM:
                                continue
                            
                            volume_quality = self.analyze_volume_profile(symbol)
                            if volume_quality < self.MIN_VOLUME:
                                continue
                            
                            pip_size = 0.01 if 'JPY' in symbol else 0.0001
                            entry_price = current_price - pip_size
                            
                            confidence = 60 + (momentum * 0.2) + (volume_quality * 0.1)  # LOWERED
                            
                            signal = PatternSignal(
                                pattern="ORDER_BLOCK_BOUNCE",
                                direction=direction,
                                entry_price=entry_price,
                                confidence=min(80, confidence),
                                timeframe="M5",
                                pair=symbol,
                                momentum_score=momentum,
                                volume_quality=volume_quality
                            )
                            signal.quality_score = self.calculate_quality_score(signal)
                            return signal
                            
        except Exception as e:
            logger.debug(f"Error in order block: {e}")
        
        return None
    
    def detect_sweep_and_return(self, symbol: str) -> Optional[PatternSignal]:
        """Detect Sweep and Return (SRL) pattern - liquidity grab followed by reversal"""
        try:
            if len(self.m5_data[symbol]) < 2:  # LOWERED
                return None
                
            candles = list(self.m5_data[symbol])
            if len(candles) < 4:  # Reduced from 15 for faster signals
                return None
                
            recent = list(candles.values())[-15:]
            current = recent[-1]
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            
            # Find swing highs and lows
            swing_high = max(c['high'] for c in recent[:-3])
            swing_low = min(c['low'] for c in recent[:-3])
            
            # BULLISH SRL: Sweep below low, then strong recovery
            if recent[-2]['low'] < swing_low - (2 * pip_size):  # Previous candle swept
                wick_size = recent[-2]['low'] - min(recent[-2]['open'], recent[-2]['close'])
                body_size = abs(recent[-2]['open'] - recent[-2]['close'])
                
                # Check for strong wick (60%+ of range)
                if wick_size > 0 and body_size > 0:
                    wick_ratio = wick_size / (wick_size + body_size)
                    
                    if wick_ratio > 0.6 and current['close'] > swing_low:
                        # Confirmed sweep and return
                        momentum = self.calculate_momentum_score(symbol, "BUY")
                        if momentum < 20:
                            return None
                        
                        volume_quality = self.analyze_volume_profile(symbol)
                        confidence = 70 + (momentum * 0.15) + (volume_quality * 0.1)
                        
                        signal = PatternSignal(
                            pattern="SWEEP_RETURN",
                            direction="BUY",
                            entry_price=current['close'] + pip_size,
                            confidence=min(85, confidence),
                            timeframe="M5",
                            pair=symbol,
                            momentum_score=momentum,
                            volume_quality=volume_quality
                        )
                        signal.quality_score = self.calculate_quality_score(signal)
                        return signal
            
            # BEARISH SRL: Sweep above high, then rejection
            elif recent[-2]['high'] > swing_high + (2 * pip_size):  # Previous candle swept
                wick_size = recent[-2]['high'] - max(recent[-2]['open'], recent[-2]['close'])
                body_size = abs(recent[-2]['open'] - recent[-2]['close'])
                
                if wick_size > 0 and body_size > 0:
                    wick_ratio = wick_size / (wick_size + body_size)
                    
                    if wick_ratio > 0.6 and current['close'] < swing_high:
                        momentum = self.calculate_momentum_score(symbol, "SELL")
                        if momentum < 20:
                            return None
                        
                        volume_quality = self.analyze_volume_profile(symbol)
                        confidence = 70 + (momentum * 0.15) + (volume_quality * 0.1)
                        
                        signal = PatternSignal(
                            pattern="SWEEP_RETURN",
                            direction="SELL",
                            entry_price=current['close'] - pip_size,
                            confidence=min(85, confidence),
                            timeframe="M5",
                            pair=symbol,
                            momentum_score=momentum,
                            volume_quality=volume_quality
                        )
                        signal.quality_score = self.calculate_quality_score(signal)
                        return signal
                        
        except Exception as e:
            logger.debug(f"Error in SRL detection: {e}")
        
        return None
    
    def detect_vcb_breakout(self, symbol: str) -> Optional[PatternSignal]:
        """Detect Volatility Compression Breakout (VCB) pattern"""
        try:
            if len(self.m5_data[symbol]) < 2:  # LOWERED
                return None
                
            candles = list(self.m5_data[symbol])
            if len(candles) < 5:  # Reduced from 20 for faster signals
                return None
                
            recent = list(candles.values())[-20:]
            current = recent[-1]
            
            # Calculate ATR for volatility
            atr_values = []
            for i in range(1, len(recent)):
                high_low = recent[i]['high'] - recent[i]['low']
                high_close = abs(recent[i]['high'] - recent[i-1]['close'])
                low_close = abs(recent[i]['low'] - recent[i-1]['close'])
                tr = max(high_low, high_close, low_close)
                atr_values.append(tr)
            
            if not atr_values:
                return None
                
            atr = sum(atr_values) / len(atr_values)
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            
            # Check for compression (current range < 50% of ATR)
            current_range = current['high'] - current['low']
            if current_range > atr * 0.5:
                return None  # Not compressed enough
            
            # Check for breakout
            recent_high = max(c['high'] for c in recent[:-5])
            recent_low = min(c['low'] for c in recent[:-5])
            
            # BULLISH VCB
            if current['close'] > recent_high:
                momentum = self.calculate_momentum_score(symbol, "BUY")
                if momentum < 15:
                    return None
                
                volume_quality = self.analyze_volume_profile(symbol)
                if volume_quality < 10:
                    return None
                
                confidence = 65 + (momentum * 0.2) + (volume_quality * 0.15)
                
                signal = PatternSignal(
                    pattern="VCB_BREAKOUT",
                    direction="BUY",
                    entry_price=current['close'] + pip_size,
                    confidence=min(85, confidence),
                    timeframe="M5",
                    pair=symbol,
                    momentum_score=momentum,
                    volume_quality=volume_quality
                )
                signal.quality_score = self.calculate_quality_score(signal)
                return signal
            
            # BEARISH VCB
            elif current['close'] < recent_low:
                momentum = self.calculate_momentum_score(symbol, "SELL")
                if momentum < 15:
                    return None
                
                volume_quality = self.analyze_volume_profile(symbol)
                if volume_quality < 10:
                    return None
                
                confidence = 65 + (momentum * 0.2) + (volume_quality * 0.15)
                
                signal = PatternSignal(
                    pattern="VCB_BREAKOUT",
                    direction="SELL",
                    entry_price=current['close'] - pip_size,
                    confidence=min(85, confidence),
                    timeframe="M5",
                    pair=symbol,
                    momentum_score=momentum,
                    volume_quality=volume_quality
                )
                signal.quality_score = self.calculate_quality_score(signal)
                return signal
                
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
                
                confidence = 60 + (momentum * 0.15) + (volume_quality * 0.1)
                
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
                
                confidence = 60 + (momentum * 0.15) + (volume_quality * 0.1)
                
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
        """Detect fair value gap fill pattern"""
        if len(self.m5_data[symbol]) < 5:  # LOWERED for faster signals
            return None
            
        try:
            recent_candles = list(self.m5_data[symbol])[-10:]
            closes = [c.get('close', 0) for c in recent_candles]
            highs = [c.get('high', 0) for c in recent_candles]
            lows = [c.get('low', 0) for c in recent_candles]
            current_price = closes[-1]
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            
            # Look for fair value gaps
            for i in range(len(recent_candles) - 8, len(recent_candles) - 2):
                if i <= 0:
                    continue
                    
                prev_high = highs[i-1]
                current_low = lows[i]
                next_high = highs[i+1]
                next_low = lows[i+1]
                
                # Bullish gap (price jumped up, leaving unfilled space)
                if prev_high < current_low:
                    gap_size = current_low - prev_high
                    gap_mid = (current_low + prev_high) / 2
                    
                    # Check if price is approaching gap from above
                    if current_price > gap_mid and current_price <= current_low + (gap_size * 0.3):
                        confidence = 68 + min(15, gap_size / pip_size)  # Base + gap size bonus
                        signal = PatternSignal(
                            pattern="FAIR_VALUE_GAP_FILL",
                            direction="SELL",
                            entry_price=current_price,
                            confidence=min(85, confidence),
                            timeframe="M5",
                            pair=symbol
                        )
                        signal.quality_score = self.calculate_quality_score(signal)
                        return signal
                
                # Bearish gap (price gapped down)
                if prev_low > current_high:
                    gap_size = prev_low - current_high
                    gap_mid = (prev_low + current_high) / 2
                    
                    # Check if price is approaching gap from below
                    if current_price < gap_mid and current_price >= current_high - (gap_size * 0.3):
                        confidence = 68 + min(15, gap_size / pip_size)
                        signal = PatternSignal(
                            pattern="FAIR_VALUE_GAP_FILL",
                            direction="BUY",
                            entry_price=current_price,
                            confidence=min(85, confidence),
                            timeframe="M5",
                            pair=symbol
                        )
                        signal.quality_score = self.calculate_quality_score(signal)
                        return signal
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
        pip_size = 0.01 if 'JPY' in pattern_signal.pair else 0.0001
        
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
    
    def build_candles_from_tick(self, symbol: str, tick_data: dict = None):
        """Fetch OHLC data from ZMQ port 5556 and store candles - ENHANCED VERSION"""
        # ONLY process symbols in our trading pairs list
        if symbol not in self.trading_pairs:
            return
            
        import json
        import time
        
        # Track last OHLC receipt time for fallback logic
        if not hasattr(self, 'last_ohlc_time'):
            self.last_ohlc_time = {}
        
        current_time = time.time()
        ohlc_received = False
        
        try:
            # Check for OHLC messages from EA on port 5556
            message_count = 0
            while True:
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
                        
                except zmq.Again:
                    # No more messages available
                    if message_count > 0:
                        print(f"✅ Processed {message_count} OHLC messages from port 5556")
                    break
                except Exception as e:
                    print(f"❌ OHLC parsing error: {e}")
                    break
        
        except Exception as e:
            print(f"❌ OHLC fetch error for {symbol}: {e}")
        
        # Fallback logic: Use tick data if no OHLC for 5 seconds
        last_time = self.last_ohlc_time.get(symbol, 0)
        if current_time - last_time > 5 and tick_data:
            if current_time - last_time > 10:  # Only log after 10s to reduce spam
                print(f"🟡 {symbol}: No OHLC for {current_time - last_time:.1f}s, using tick fallback")
            self._process_tick_fallback(symbol, tick_data)
        elif ohlc_received:
            print(f"✨ {symbol}: Using direct OHLC data (last update {current_time - last_time:.1f}s ago)")
        elif tick_data:
            # Always use tick data if available and no OHLC
            self._process_tick_fallback(symbol, tick_data)
    
    def _process_tick_fallback(self, symbol: str, tick_data: dict):
        """Fallback tick processing for backwards compatibility"""
        try:
            bid = float(tick_data.get('bid', 0))
            ask = float(tick_data.get('ask', 0))
            timestamp_str = tick_data.get('timestamp', '')
            
            # Parse timestamp and get mid price
            if not bid or not ask:
                return
                
            mid_price = (bid + ask) / 2
            
            # Convert timestamp to unix time
            from datetime import datetime
            import time
            dt = datetime.strptime(timestamp_str, "%Y.%m.%d %H:%M:%S")
            unix_time = time.mktime(dt.timetuple())
            current_minute = int(unix_time / 60) * 60  # Round down to minute
            
            # Initialize storage if needed
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
                    'volume': 1,
                    'timestamp': current_minute
                }
                print(f"🕯️ {symbol}: New M1 candle at {current_minute} (tick fallback)")
            else:
                # Update existing candle
                candle = self.current_candles[symbol][current_minute]
                candle['high'] = max(candle['high'], mid_price)
                candle['low'] = min(candle['low'], mid_price)
                candle['close'] = mid_price
                candle['volume'] += 1
            
            # Push completed candles to M1 buffer
            completed_minutes = [m for m in self.current_candles[symbol] if m < current_minute]
            for minute in completed_minutes:
                completed_candle = self.current_candles[symbol].pop(minute)
                self.m1_data[symbol].append(completed_candle)
                print(f"📊 {symbol}: M1 added, total: {len(self.m1_data[symbol])} (tick fallback)")
                
                # Force M5 aggregation every 5 M1 candles
                if len(self.m1_data[symbol]) % 5 == 0:
                    self.force_aggregate_m5(symbol)
                
                # Force M15 aggregation every 15 M1 candles
                if len(self.m1_data[symbol]) % 15 == 0:
                    self.force_aggregate_m15(symbol)
                    
        except Exception as e:
            print(f"❌ Fallback candle building error for {symbol}: {e}")
    
    def force_aggregate_m5(self, symbol: str):
        """Force create M5 candle from last 5 M1 candles"""
        if len(self.m1_data[symbol]) >= 5:
            last_5 = list(self.m1_data[symbol])[-5:]
            m5_candle = {
                'open': last_5[0]['open'],
                'high': max(c['high'] for c in last_5),
                'low': min(c['low'] for c in last_5),
                'close': last_5[-1]['close'],
                'volume': sum(c['volume'] for c in last_5),
                'timestamp': last_5[0]['timestamp']
            }
            self.m5_data[symbol].append(m5_candle)
            print(f"📊 {symbol}: M5 created from 5 M1, total M5: {len(self.m5_data[symbol])}")
    
    def force_aggregate_m15(self, symbol: str):
        """Force create M15 candle from last 15 M1 candles"""
        if len(self.m1_data[symbol]) >= 15:
            last_15 = list(self.m1_data[symbol])[-15:]
            m15_candle = {
                'open': last_15[0]['open'],
                'high': max(c['high'] for c in last_15),
                'low': min(c['low'] for c in last_15),
                'close': last_15[-1]['close'],
                'volume': sum(c['volume'] for c in last_15),
                'timestamp': last_15[0]['timestamp']
            }
            self.m15_data[symbol].append(m15_candle)
            print(f"📊 {symbol}: M15 created from 15 M1, total M15: {len(self.m15_data[symbol])}")
    
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
        """Save candle data to cache file"""
        try:
            cache_data = {
                'm1_data': {},
                'm5_data': {},
                'm15_data': {},
                'last_update': time.time()
            }
            
            # Convert deques to lists for JSON serialization
            for symbol in self.trading_pairs:
                if symbol in self.m1_data:
                    cache_data['m1_data'][symbol] = list(self.m1_data[symbol])
                if symbol in self.m5_data:
                    cache_data['m5_data'][symbol] = list(self.m5_data[symbol])
                if symbol in self.m15_data:
                    cache_data['m15_data'][symbol] = list(self.m15_data[symbol])
            
            with open('/root/HydraX-v2/candle_cache.json', 'w') as f:
                json.dump(cache_data, f)
                
            print(f"💾 Saved candles: {sum(len(self.m1_data[s]) for s in self.trading_pairs)} M1, {sum(len(self.m5_data[s]) for s in self.trading_pairs)} M5, {sum(len(self.m15_data[s]) for s in self.trading_pairs)} M15")
            
        except Exception as e:
            print(f"❌ Error saving candles: {e}")

    def load_candles(self):
        """Load candle data from cache file"""
        try:
            if os.path.exists('/root/HydraX-v2/candle_cache.json'):
                with open('/root/HydraX-v2/candle_cache.json', 'r') as f:
                    cache_data = json.load(f)
                
                # Restore M1 candles from cache and aggregate M5/M15
                for symbol in self.trading_pairs:
                    if symbol in cache_data.get('m1_data', {}):
                        candles = cache_data['m1_data'][symbol]
                        self.m1_data[symbol] = deque(candles, maxlen=500)
                        
                        # Aggregate M5 candles from M1 (every 5 M1 candles)
                        m5_candles = []
                        for i in range(0, len(candles), 5):
                            chunk = candles[i:i+5]
                            if len(chunk) >= 5:  # Only create M5 if we have full 5 M1 candles
                                m5_candle = {
                                    'open': chunk[0]['open'],
                                    'high': max(c['high'] for c in chunk),
                                    'low': min(c['low'] for c in chunk),
                                    'close': chunk[-1]['close'],
                                    'volume': sum(c['volume'] for c in chunk),
                                    'timestamp': chunk[0]['timestamp']  # Use first M1 timestamp
                                }
                                m5_candles.append(m5_candle)
                        self.m5_data[symbol] = deque(m5_candles, maxlen=300)
                        
                        # Aggregate M15 candles from M5 (every 3 M5 candles)  
                        m15_candles = []
                        for i in range(0, len(m5_candles), 3):
                            chunk = m5_candles[i:i+3]
                            if len(chunk) >= 3:  # Only create M15 if we have full 3 M5 candles
                                m15_candle = {
                                    'open': chunk[0]['open'],
                                    'high': max(c['high'] for c in chunk),
                                    'low': min(c['low'] for c in chunk),
                                    'close': chunk[-1]['close'],
                                    'volume': sum(c['volume'] for c in chunk),
                                    'timestamp': chunk[0]['timestamp']  # Use first M5 timestamp
                                }
                                m15_candles.append(m15_candle)
                        self.m15_data[symbol] = deque(m15_candles, maxlen=200)
                        
                        print(f"📂 {symbol}: Loaded {len(candles)} M1 → Aggregated {len(m5_candles)} M5 → {len(m15_candles)} M15")
                    else:
                        # Initialize empty deques if no cached data
                        self.m1_data[symbol] = deque(maxlen=500)
                        self.m5_data[symbol] = deque(maxlen=300)
                        self.m15_data[symbol] = deque(maxlen=200)
                
                total_m1 = sum(len(self.m1_data[s]) for s in self.trading_pairs)
                total_m5 = sum(len(self.m5_data[s]) for s in self.trading_pairs)
                total_m15 = sum(len(self.m15_data[s]) for s in self.trading_pairs)
                
                print(f"📂 Loaded candles: {total_m1} M1, {total_m5} M5, {total_m15} M15")
                
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
        """Apply ML filtering for 5-10 signals/hour target"""
        min_confidence = 68.0  # LOWERED for more signals
        
        # Apply news impact adjustment to confidence
        news_adjustment = self.get_news_impact(signal.pair)
        adjusted_confidence = signal.confidence + news_adjustment
        
        if news_adjustment != 0:
            print(f"📰 {signal.pair}: News impact {news_adjustment} → Confidence {signal.confidence:.1f}% → {adjusted_confidence:.1f}%")
        
        if adjusted_confidence < min_confidence:
            return False, f"Below threshold ({min_confidence}%) after news", adjusted_confidence
        
        # Check performance history
        pattern_clean = signal.pattern.replace('_INTELLIGENT', '')
        combo_key = f"{signal.pair}_{pattern_clean}_{session}"
        perf = self.performance_history.get(combo_key, {})
        if perf.get('enabled') == False:
            return False, f"Disabled: poor performance", adjusted_confidence
        
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
            
            # Write to truth log
            with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
                f.write(json.dumps(truth_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging to truth tracker: {e}")

    def scan_for_patterns(self):
        """Scan all symbols for patterns"""
        # ONLY scan our defined forex pairs
        symbols_to_scan = [s for s in self.trading_pairs if s in self.tick_data]
        logger.info(f"🔍 Starting pattern scan for {len(symbols_to_scan)} forex symbols")
        
        # Log candle status with tick reception
        for symbol in symbols_to_scan[:5]:
            m1_count = len(self.m1_data[symbol])
            m5_count = len(self.m5_data[symbol])
            tick_count = len(self.tick_data[symbol])
            time_since_tick = time.time() - self.last_tick_time.get(symbol, 0)
            logger.info(f"  {symbol}: {tick_count} ticks, {m1_count} M1, {m5_count} M5 candles (last tick {time_since_tick:.1f}s ago)")
        
        signals_generated = []
        
        for symbol in symbols_to_scan:
            # Check if data is fresh
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
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    logger.info(f"✅ VCB BREAKOUT on {symbol} - {tier_reason}")
                    patterns.append(signal)
                else:
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
                    
                    if protected_signal and protected_signal.get('confidence', 0) >= 50:  # LOWERED
                        # Signal passed CITADEL protection and meets final threshold
                        signals_generated.append(protected_signal)
                        
                        # Update tracking
                        self.last_signal_time[symbol] = time.time()
                        self.hourly_signal_count[symbol] += 1
                        self.signal_history.append(protected_signal)
                        
                        # Publish
                        self.publish_signal(protected_signal)
                        
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
                    
            except Exception as e:
                logger.error(f"Failed to publish signal: {e}")
    
    def data_listener(self):
        """Listen for market data"""
        logger.info("📡 Starting data listener")
        
        while self.running:
            try:
                if self.subscriber.poll(timeout=100):
                    message = self.subscriber.recv_string()
                    
                    # Handle "tick {json}" format from telemetry bridge
                    if message.startswith("tick "):
                        json_data = message[5:]  # Skip "tick " prefix
                        try:
                            tick_data = json.loads(json_data)
                            # Process tick directly with proper data
                            if 'symbol' in tick_data and 'bid' in tick_data:
                                symbol = tick_data.get('symbol')
                                if symbol:
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
            if signal.get('confidence', 0) >= 50:  # LOWERED threshold
                self.publish_signal(signal)
                logger.info(f"🏆 CITADEL RELEASE: {signal['symbol']} {signal['direction']} "
                          f"(delayed {signal.get('delay_time', 0)}s, confidence: {signal['confidence']}%)")
    
    def show_stats(self):
        """Display current statistics"""
        logger.info("\n" + "="*60)
        logger.info("📊 ELITE GUARD BALANCED v7.0 STATUS")
        logger.info("="*60)
        
        # Signal stats
        recent_signals = [s for s in self.signal_history 
                         if time.time() - float(s.get('timestamp', 0)) < 3600]
        
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
                
                # Scan for patterns every 30 seconds
                if current_time - last_scan >= 30:
                    logger.info(f"⏰ 30-second scan trigger, active_session={self.is_active_session()}")
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