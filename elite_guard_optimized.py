#!/usr/bin/env python3
"""
ELITE GUARD v8.0 - OPTIMIZED FOR WIN RATE
Critical improvements to increase win rate from 34% to 60%+
"""

import zmq
import json
import time
import pytz
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from collections import defaultdict, deque
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PatternSignal:
    pattern: str
    direction: str
    entry_price: float
    confidence: float
    timeframe: str
    pair: str
    final_score: float = 0.0
    tf_alignment: float = 0.0
    momentum_score: float = 0.0
    volume_quality: float = 0.0

@dataclass
class MarketTick:
    symbol: str
    bid: float
    ask: float
    spread: float
    volume: int
    timestamp: float

class EliteGuardOptimized:
    """
    ELITE GUARD v8.0 - Optimized for higher win rate
    Key improvements:
    - Better entry timing
    - Momentum confirmation
    - Volume profile analysis
    - Strong trend alignment
    - Volatility filtering
    """
    
    def __init__(self):
        # ZMQ Configuration
        self.context = zmq.Context()
        self.subscriber = None
        self.publisher = None
        
        # Trading pairs
        self.trading_pairs = [
            "XAUUSD", "USDJPY", "GBPUSD", "EURUSD",
            "USDCAD", "EURJPY", "GBPJPY"
        ]
        
        # Market data storage
        self.tick_data = defaultdict(lambda: deque(maxlen=500))  # More ticks for better analysis
        self.m1_data = defaultdict(lambda: deque(maxlen=200))
        self.m5_data = defaultdict(lambda: deque(maxlen=200))
        self.m15_data = defaultdict(lambda: deque(maxlen=200))
        
        # Volume profile tracking
        self.volume_profile = defaultdict(lambda: deque(maxlen=100))
        self.price_levels = defaultdict(dict)  # Track important price levels
        
        # Signal controls
        self.daily_signal_count = 0
        self.last_signal_time = {}
        self.signal_cooldown = 15 * 60  # 15 minutes minimum between signals per pair
        self.running = True
        
        # Performance tracking
        self.signals_generated = 0
        self.signals_blocked_by_filters = 0
        
        # Market regime tracking
        self.market_regime = {}
        self.volatility_state = {}
        
        logger.info("🎯 ELITE GUARD v8.0 OPTIMIZED - Target 60%+ Win Rate")
    
    def setup_zmq_connections(self):
        """Setup ZMQ connections"""
        try:
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://127.0.0.1:5560")
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")
            self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)
            
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")
            
            logger.info("✅ ZMQ connections established")
        except Exception as e:
            logger.error(f"❌ ZMQ setup failed: {e}")
            raise
    
    def calculate_market_regime(self, symbol: str) -> str:
        """Determine current market regime - CRITICAL for filtering"""
        if len(self.m5_data[symbol]) < 20:
            return "UNKNOWN"
        
        recent_candles = list(self.m5_data[symbol])[-20:]
        closes = [c['close'] for c in recent_candles]
        
        # Calculate trend strength
        sma_5 = np.mean(closes[-5:])
        sma_20 = np.mean(closes)
        
        # Calculate volatility
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * 100
        
        # Determine regime
        trend_strength = abs(sma_5 - sma_20) / sma_20 * 100
        
        if trend_strength > 0.2:  # 0.2% difference
            if sma_5 > sma_20:
                regime = "TRENDING_UP"
            else:
                regime = "TRENDING_DOWN"
        elif volatility > 0.5:  # High volatility
            regime = "VOLATILE_RANGE"
        else:
            regime = "CALM_RANGE"
        
        self.market_regime[symbol] = regime
        self.volatility_state[symbol] = volatility
        
        return regime
    
    def calculate_momentum_score(self, symbol: str, direction: str) -> float:
        """Calculate momentum in trade direction - CRITICAL for entries"""
        if len(self.m1_data[symbol]) < 10:
            return 0.0
        
        recent_candles = list(self.m1_data[symbol])[-10:]
        closes = [c['close'] for c in recent_candles]
        
        # Rate of change
        roc_3 = (closes[-1] - closes[-3]) / closes[-3] * 100
        roc_5 = (closes[-1] - closes[-5]) / closes[-5] * 100
        
        # Momentum alignment
        if direction == "BUY":
            if roc_3 > 0 and roc_5 > 0:
                return min(100, (roc_3 + roc_5) * 20)  # Both positive = good
            elif roc_3 > 0:
                return min(50, roc_3 * 20)  # Only short-term positive
            else:
                return 0  # No momentum
        else:  # SELL
            if roc_3 < 0 and roc_5 < 0:
                return min(100, abs(roc_3 + roc_5) * 20)
            elif roc_3 < 0:
                return min(50, abs(roc_3) * 20)
            else:
                return 0
    
    def analyze_volume_profile(self, symbol: str) -> float:
        """Analyze volume profile for quality - avoid low volume fakeouts"""
        if len(self.tick_data[symbol]) < 50:
            return 0.0
        
        recent_ticks = list(self.tick_data[symbol])[-50:]
        volumes = [t.volume for t in recent_ticks if t.volume > 0]
        
        if not volumes:
            return 0.0
        
        # Volume consistency
        avg_volume = np.mean(volumes)
        current_volume = volumes[-1] if volumes else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Volume trend
        recent_avg = np.mean(volumes[-10:]) if len(volumes) >= 10 else avg_volume
        older_avg = np.mean(volumes[-30:-10]) if len(volumes) >= 30 else avg_volume
        volume_trend = recent_avg / older_avg if older_avg > 0 else 1
        
        # Score calculation
        score = 0.0
        if volume_ratio > 1.5:  # 50% above average
            score += 50
        elif volume_ratio > 1.2:
            score += 30
        elif volume_ratio > 0.8:
            score += 10
        
        if volume_trend > 1.2:  # Increasing volume
            score += 30
        elif volume_trend > 1.0:
            score += 15
        
        # Penalty for very low volume
        if avg_volume < 100:
            score *= 0.5
        
        return min(100, score)
    
    def calculate_trend_alignment(self, symbol: str, direction: str) -> float:
        """Multi-timeframe trend alignment - MUST be strong"""
        score = 0.0
        
        # M1 trend
        if len(self.m1_data[symbol]) >= 20:
            m1_closes = [c['close'] for c in list(self.m1_data[symbol])[-20:]]
            m1_sma_fast = np.mean(m1_closes[-5:])
            m1_sma_slow = np.mean(m1_closes[-20:])
            
            if direction == "BUY" and m1_sma_fast > m1_sma_slow:
                score += 25
            elif direction == "SELL" and m1_sma_fast < m1_sma_slow:
                score += 25
        
        # M5 trend
        if len(self.m5_data[symbol]) >= 20:
            m5_closes = [c['close'] for c in list(self.m5_data[symbol])[-20:]]
            m5_sma_fast = np.mean(m5_closes[-5:])
            m5_sma_slow = np.mean(m5_closes[-20:])
            
            if direction == "BUY" and m5_sma_fast > m5_sma_slow:
                score += 35
            elif direction == "SELL" and m5_sma_fast < m5_sma_slow:
                score += 35
        
        # M15 trend
        if len(self.m15_data[symbol]) >= 10:
            m15_closes = [c['close'] for c in list(self.m15_data[symbol])[-10:]]
            m15_sma_fast = np.mean(m15_closes[-3:])
            m15_sma_slow = np.mean(m15_closes[-10:])
            
            if direction == "BUY" and m15_sma_fast > m15_sma_slow:
                score += 40
            elif direction == "SELL" and m15_sma_fast < m15_sma_slow:
                score += 40
        
        return score
    
    def detect_liquidity_sweep_reversal_optimized(self, symbol: str) -> Optional[PatternSignal]:
        """OPTIMIZED: Liquidity sweep with momentum confirmation"""
        if len(self.m1_data[symbol]) < 10:
            return None
        
        try:
            recent_data = list(self.m1_data[symbol])[-20:]
            highs = [p['high'] for p in recent_data]
            lows = [p['low'] for p in recent_data]
            closes = [p['close'] for p in recent_data]
            volumes = [p.get('volume', 0) for p in recent_data]
            
            # Find recent swing high/low
            recent_high = max(highs[-10:-2])  # Exclude last 2 candles
            recent_low = min(lows[-10:-2])
            current_close = closes[-1]
            prev_close = closes[-2]
            
            # Check for liquidity sweep
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            
            # BULLISH: Price swept below recent low and reversed
            if lows[-1] < recent_low and closes[-1] > lows[-1] + (2 * pip_size):
                # Confirm with volume
                avg_volume = np.mean(volumes[-10:]) if volumes else 1
                current_volume = volumes[-1] if volumes else 1
                
                if current_volume > avg_volume * 1.3:  # 30% volume increase required
                    direction = "BUY"
                    
                    # Calculate entry ABOVE current price for momentum
                    entry_price = current_close + (1 * pip_size)  # Enter 1 pip above
                    
                    # Check momentum
                    momentum = self.calculate_momentum_score(symbol, direction)
                    if momentum < 30:  # Require minimum momentum
                        return None
                    
                    # Check trend alignment
                    trend_score = self.calculate_trend_alignment(symbol, direction)
                    if trend_score < 40:  # Require decent alignment
                        return None
                    
                    confidence = 75 + (momentum * 0.15) + (trend_score * 0.1)
                    
                    return PatternSignal(
                        pattern="LIQUIDITY_SWEEP_REVERSAL",
                        direction=direction,
                        entry_price=entry_price,
                        confidence=min(95, confidence),
                        timeframe="M1",
                        pair=symbol,
                        momentum_score=momentum,
                        volume_quality=self.analyze_volume_profile(symbol)
                    )
            
            # BEARISH: Price swept above recent high and reversed
            elif highs[-1] > recent_high and closes[-1] < highs[-1] - (2 * pip_size):
                avg_volume = np.mean(volumes[-10:]) if volumes else 1
                current_volume = volumes[-1] if volumes else 1
                
                if current_volume > avg_volume * 1.3:
                    direction = "SELL"
                    
                    # Calculate entry BELOW current price for momentum
                    entry_price = current_close - (1 * pip_size)  # Enter 1 pip below
                    
                    # Check momentum
                    momentum = self.calculate_momentum_score(symbol, direction)
                    if momentum < 30:
                        return None
                    
                    # Check trend alignment
                    trend_score = self.calculate_trend_alignment(symbol, direction)
                    if trend_score < 40:
                        return None
                    
                    confidence = 75 + (momentum * 0.15) + (trend_score * 0.1)
                    
                    return PatternSignal(
                        pattern="LIQUIDITY_SWEEP_REVERSAL",
                        direction=direction,
                        entry_price=entry_price,
                        confidence=min(95, confidence),
                        timeframe="M1",
                        pair=symbol,
                        momentum_score=momentum,
                        volume_quality=self.analyze_volume_profile(symbol)
                    )
                    
        except Exception as e:
            logger.debug(f"Error in liquidity sweep: {e}")
        
        return None
    
    def detect_order_block_bounce_optimized(self, symbol: str) -> Optional[PatternSignal]:
        """OPTIMIZED: Order block with structure confirmation"""
        if len(self.m5_data[symbol]) < 20:
            return None
        
        try:
            recent_candles = list(self.m5_data[symbol])[-20:]
            
            # Find strong order blocks (3+ candle consolidation)
            for i in range(len(recent_candles) - 10, len(recent_candles) - 3):
                # Check for consolidation
                block_highs = [recent_candles[j]['high'] for j in range(i, i+3)]
                block_lows = [recent_candles[j]['low'] for j in range(i, i+3)]
                
                block_high = max(block_highs)
                block_low = min(block_lows)
                block_range = block_high - block_low
                
                if block_range == 0:
                    continue
                
                # Check if range is significant
                avg_range = np.mean([c['high'] - c['low'] for c in recent_candles])
                if block_range < avg_range * 0.5:  # Too small
                    continue
                
                current_price = recent_candles[-1]['close']
                
                # BULLISH: Price at support
                if block_low <= current_price <= block_low + (block_range * 0.3):
                    direction = "BUY"
                    
                    # Must have bullish structure
                    if recent_candles[-1]['close'] <= recent_candles[-1]['open']:
                        continue  # Current candle is bearish
                    
                    # Check momentum
                    momentum = self.calculate_momentum_score(symbol, direction)
                    if momentum < 40:
                        continue
                    
                    # Volume confirmation
                    volume_quality = self.analyze_volume_profile(symbol)
                    if volume_quality < 30:
                        continue
                    
                    # Entry at current price (already at support)
                    entry_price = current_price
                    
                    confidence = 70 + (momentum * 0.2) + (volume_quality * 0.1)
                    
                    return PatternSignal(
                        pattern="ORDER_BLOCK_BOUNCE",
                        direction=direction,
                        entry_price=entry_price,
                        confidence=min(90, confidence),
                        timeframe="M5",
                        pair=symbol,
                        momentum_score=momentum,
                        volume_quality=volume_quality
                    )
                
                # BEARISH: Price at resistance
                elif block_high - (block_range * 0.3) <= current_price <= block_high:
                    direction = "SELL"
                    
                    # Must have bearish structure
                    if recent_candles[-1]['close'] >= recent_candles[-1]['open']:
                        continue  # Current candle is bullish
                    
                    # Check momentum
                    momentum = self.calculate_momentum_score(symbol, direction)
                    if momentum < 40:
                        continue
                    
                    # Volume confirmation
                    volume_quality = self.analyze_volume_profile(symbol)
                    if volume_quality < 30:
                        continue
                    
                    entry_price = current_price
                    
                    confidence = 70 + (momentum * 0.2) + (volume_quality * 0.1)
                    
                    return PatternSignal(
                        pattern="ORDER_BLOCK_BOUNCE",
                        direction=direction,
                        entry_price=entry_price,
                        confidence=min(90, confidence),
                        timeframe="M5",
                        pair=symbol,
                        momentum_score=momentum,
                        volume_quality=volume_quality
                    )
                    
        except Exception as e:
            logger.debug(f"Error in order block: {e}")
        
        return None
    
    def apply_final_filters(self, signal: PatternSignal) -> bool:
        """Apply strict final filters to reduce false signals"""
        symbol = signal.pair
        
        # 1. Market regime filter
        regime = self.calculate_market_regime(symbol)
        if regime == "UNKNOWN":
            logger.info(f"❌ {symbol} blocked: Unknown market regime")
            return False
        
        # Block counter-trend trades in strong trends
        if regime == "TRENDING_UP" and signal.direction == "SELL":
            if signal.confidence < 85:  # Only allow very high confidence counter-trend
                logger.info(f"❌ {symbol} blocked: Counter-trend in uptrend")
                return False
        elif regime == "TRENDING_DOWN" and signal.direction == "BUY":
            if signal.confidence < 85:
                logger.info(f"❌ {symbol} blocked: Counter-trend in downtrend")
                return False
        
        # 2. Volatility filter
        if symbol in self.volatility_state:
            volatility = self.volatility_state[symbol]
            if volatility < 0.1:  # Too calm
                logger.info(f"❌ {symbol} blocked: Low volatility {volatility:.3f}")
                return False
            elif volatility > 2.0:  # Too volatile
                logger.info(f"❌ {symbol} blocked: High volatility {volatility:.3f}")
                return False
        
        # 3. Spread filter
        if len(self.tick_data[symbol]) > 0:
            current_tick = list(self.tick_data[symbol])[-1]
            if current_tick.spread > 3.0:  # Max 3 pip spread
                logger.info(f"❌ {symbol} blocked: Wide spread {current_tick.spread:.1f}")
                return False
        
        # 4. Session filter - avoid dead zones
        current_hour = datetime.now().hour
        if current_hour >= 22 or current_hour <= 6:  # Late night/early morning
            if signal.confidence < 80:
                logger.info(f"❌ {symbol} blocked: Low liquidity session")
                return False
        
        # 5. Minimum quality scores
        if signal.momentum_score < 30:
            logger.info(f"❌ {symbol} blocked: Low momentum {signal.momentum_score:.1f}")
            return False
        
        if signal.volume_quality < 20:
            logger.info(f"❌ {symbol} blocked: Poor volume {signal.volume_quality:.1f}")
            return False
        
        return True
    
    def generate_optimized_signal(self, pattern_signal: PatternSignal) -> Dict:
        """Generate signal with optimized SL/TP"""
        try:
            pip_size = 0.01 if 'JPY' in pattern_signal.pair else 0.0001
            
            # Dynamic SL/TP based on volatility
            if pattern_signal.pair in self.volatility_state:
                volatility = self.volatility_state[pattern_signal.pair]
                
                # Adjust stops based on volatility
                if volatility < 0.3:  # Low volatility
                    stop_pips = 5
                    target_pips = 8  # 1:1.6 RR
                elif volatility < 0.7:  # Normal
                    stop_pips = 7
                    target_pips = 12  # 1:1.7 RR
                else:  # Higher volatility
                    stop_pips = 10
                    target_pips = 18  # 1:1.8 RR
            else:
                # Default
                stop_pips = 7
                target_pips = 12
            
            stop_distance = stop_pips * pip_size
            target_distance = target_pips * pip_size
            
            entry_price = pattern_signal.entry_price
            
            if pattern_signal.direction == "BUY":
                stop_loss = entry_price - stop_distance
                take_profit = entry_price + target_distance
            else:
                stop_loss = entry_price + stop_distance
                take_profit = entry_price - target_distance
            
            # Create signal
            signal = {
                'signal_id': f'ELITE_OPTIMIZED_{pattern_signal.pair}_{int(time.time())}',
                'pair': pattern_signal.pair,
                'symbol': pattern_signal.pair,
                'direction': pattern_signal.direction,
                'pattern': pattern_signal.pattern,
                'confidence': round(pattern_signal.final_score, 1),
                'entry_price': round(entry_price, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'stop_pips': stop_pips,
                'target_pips': target_pips,
                'risk_reward': round(target_pips / stop_pips, 2),
                'momentum_score': round(pattern_signal.momentum_score, 1),
                'volume_quality': round(pattern_signal.volume_quality, 1),
                'timestamp': time.time(),
                'source': 'ELITE_GUARD_v8_OPTIMIZED'
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
    
    def scan_for_patterns(self, symbol: str) -> List[PatternSignal]:
        """Scan for patterns with strict filtering"""
        patterns = []
        
        try:
            # Only scan if we have enough data
            if len(self.m1_data[symbol]) < 20 or len(self.m5_data[symbol]) < 20:
                return []
            
            # 1. Liquidity Sweep (highest priority)
            sweep_signal = self.detect_liquidity_sweep_reversal_optimized(symbol)
            if sweep_signal:
                patterns.append(sweep_signal)
            
            # 2. Order Block Bounce
            ob_signal = self.detect_order_block_bounce_optimized(symbol)
            if ob_signal:
                patterns.append(ob_signal)
            
            # Apply confluence scoring
            for pattern in patterns:
                # Add trend alignment bonus
                trend_score = self.calculate_trend_alignment(symbol, pattern.direction)
                pattern.final_score = pattern.confidence + (trend_score * 0.1)
                pattern.final_score = min(95, pattern.final_score)
            
            # Sort by score
            return sorted(patterns, key=lambda x: x.final_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return []
    
    def process_market_data(self, data: Dict):
        """Process incoming market data"""
        try:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    return
            
            # Extract tick data
            symbol = None
            bid = ask = spread = volume = None
            
            if 'symbol' in data and 'bid' in data:
                symbol = data['symbol']
                bid = float(data['bid'])
                ask = float(data['ask'])
                spread = float(data.get('spread', (ask - bid) * 10000))
                volume = int(data.get('volume', 0))
            
            if symbol and symbol in self.trading_pairs and bid and ask:
                tick = MarketTick(
                    symbol=symbol,
                    bid=bid,
                    ask=ask,
                    spread=spread,
                    volume=volume,
                    timestamp=time.time()
                )
                
                self.tick_data[symbol].append(tick)
                self.update_ohlc_data(symbol, tick)
                
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    def update_ohlc_data(self, symbol: str, tick: MarketTick):
        """Update OHLC data from ticks"""
        mid_price = (tick.bid + tick.ask) / 2
        current_minute = int(tick.timestamp / 60) * 60
        
        if not hasattr(self, 'current_candles'):
            self.current_candles = {}
        if symbol not in self.current_candles:
            self.current_candles[symbol] = {}
        
        # Create or update current minute candle
        if current_minute not in self.current_candles[symbol]:
            self.current_candles[symbol][current_minute] = {
                'open': mid_price,
                'high': mid_price,
                'low': mid_price,
                'close': mid_price,
                'volume': tick.volume if tick.volume else 1,
                'timestamp': current_minute
            }
        else:
            candle = self.current_candles[symbol][current_minute]
            candle['high'] = max(candle['high'], mid_price)
            candle['low'] = min(candle['low'], mid_price)
            candle['close'] = mid_price
            candle['volume'] += tick.volume if tick.volume else 1
        
        # Push completed candles to M1 buffer
        completed_minutes = [m for m in self.current_candles[symbol] if m < current_minute]
        for minute in completed_minutes:
            completed_candle = self.current_candles[symbol].pop(minute)
            self.m1_data[symbol].append(completed_candle)
            
            # Aggregate to higher timeframes
            if len(self.m1_data[symbol]) >= 5 and len(self.m1_data[symbol]) % 5 == 0:
                self.aggregate_m1_to_m5(symbol)
            
            if len(self.m5_data[symbol]) >= 3 and len(self.m5_data[symbol]) % 3 == 0:
                self.aggregate_m5_to_m15(symbol)
    
    def aggregate_m1_to_m5(self, symbol: str):
        """Build M5 candles from M1"""
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

    def aggregate_m5_to_m15(self, symbol: str):
        """Build M15 candles from M5"""
        if len(self.m5_data[symbol]) >= 3:
            last_3 = list(self.m5_data[symbol])[-3:]
            m15_candle = {
                'open': last_3[0]['open'],
                'high': max(c['high'] for c in last_3),
                'low': min(c['low'] for c in last_3),
                'close': last_3[-1]['close'],
                'volume': sum(c['volume'] for c in last_3),
                'timestamp': last_3[0]['timestamp']
            }
            self.m15_data[symbol].append(m15_candle)
    
    def publish_signal(self, signal: Dict):
        """Publish signal via ZMQ"""
        try:
            if self.publisher:
                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
                
                logger.info(f"📡 Published: {signal['pair']} {signal['direction']} "
                           f"@ {signal['confidence']}% M:{signal['momentum_score']} V:{signal['volume_quality']}")
                
                # Log to truth tracker
                with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
                    f.write(json.dumps(signal) + '\n')
                
                # Start outcome monitoring
                from elite_guard_signal_outcome import start_outcome_monitor
                start_outcome_monitor(signal)
                
        except Exception as e:
            logger.error(f"Error publishing signal: {e}")
    
    def main_loop(self):
        """Main processing loop"""
        logger.info("🚀 Starting Elite Guard Optimized main loop")
        logger.info("🎯 Strict filters active for 60%+ win rate target")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Scan all pairs for patterns
                for symbol in self.trading_pairs:
                    try:
                        # Check cooldown
                        if symbol in self.last_signal_time:
                            if current_time - self.last_signal_time[symbol] < self.signal_cooldown:
                                continue
                        
                        # Scan for patterns
                        patterns = self.scan_for_patterns(symbol)
                        
                        if patterns:
                            best_pattern = patterns[0]
                            
                            # Apply final filters
                            if not self.apply_final_filters(best_pattern):
                                self.signals_blocked_by_filters += 1
                                continue
                            
                            # Generate signal
                            signal = self.generate_optimized_signal(best_pattern)
                            
                            if signal:
                                # Final confidence check
                                if signal['confidence'] < 70:
                                    logger.info(f"❌ {symbol} blocked: Final confidence too low {signal['confidence']}")
                                    continue
                                
                                # Publish signal
                                self.publish_signal(signal)
                                self.signals_generated += 1
                                self.last_signal_time[symbol] = current_time
                                self.daily_signal_count += 1
                                
                                logger.info(f"✅ SIGNAL: {symbol} {best_pattern.direction} "
                                          f"Pattern:{best_pattern.pattern} Conf:{best_pattern.final_score:.1f}%")
                    
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue
                
                # Log statistics every 5 minutes
                if int(current_time) % 300 == 0:
                    logger.info(f"📊 Stats: Generated={self.signals_generated} Blocked={self.signals_blocked_by_filters}")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)
    
    def data_listener_loop(self):
        """Listen for market data"""
        logger.info("📡 Starting data listener")
        
        while self.running:
            try:
                if self.subscriber:
                    try:
                        data = self.subscriber.recv_json(zmq.NOBLOCK)
                        self.process_market_data(data)
                    except zmq.Again:
                        time.sleep(0.1)
            except Exception as e:
                if "Resource temporarily unavailable" not in str(e):
                    logger.debug(f"Data listener: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start the engine"""
        try:
            self.setup_zmq_connections()
            
            # Start data listener thread
            data_thread = threading.Thread(target=self.data_listener_loop, daemon=True)
            data_thread.start()
            
            time.sleep(3)
            
            logger.info("✅ Elite Guard v8.0 OPTIMIZED started")
            logger.info("🎯 Target: 60%+ win rate with strict filtering")
            
            # Start main loop
            self.main_loop()
            
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Engine error: {e}")
            raise
        finally:
            if self.context:
                self.context.term()

def immortal_main_loop():
    """Never-die protocol"""
    consecutive_failures = 0
    max_failures = 5
    
    logger.info("🛡️ IMMORTALITY PROTOCOL ACTIVATED")
    
    while True:
        try:
            logger.info("🚀 Starting Elite Guard Optimized...")
            engine = EliteGuardOptimized()
            engine.start()
            consecutive_failures = 0
            
        except KeyboardInterrupt:
            logger.info("🛑 Manual shutdown")
            break
            
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"⚡ Error: {e}")
            
            if consecutive_failures >= max_failures:
                wait_time = 300
            else:
                wait_time = 30 * consecutive_failures
                
            logger.info(f"🔄 Restarting in {wait_time}s...")
            
            try:
                time.sleep(wait_time)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    immortal_main_loop()