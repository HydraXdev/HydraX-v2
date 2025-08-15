#!/usr/bin/env python3
"""
ELITE GUARD v6.1 - Refactored Signal Engine
Cleaned and optimized version with reduced logging and simplified logic
"""

import zmq
import json
import time
import pytz
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from collections import defaultdict, deque
import traceback
import os

# Import CITADEL Shield
from citadel_shield_filter import CitadelShieldFilter

# Configure logging - only critical messages
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SUBSCRIBER_PORT = 5560
PUBLISHER_PORT = 5557
CANDLE_LOOKBACK = 50
MIN_CANDLES_REQUIRED = 20
SIGNAL_COOLDOWN_SECONDS = 60
MAX_SIGNALS_PER_DAY = 40

# Trading sessions (UTC)
SESSIONS = {
    'OVERLAP': (12, 16, 1.1),   # London/NY overlap - best
    'LONDON': (7, 12, 1.05),     # London only
    'NEWYORK': (16, 21, 1.05),   # NY only
    'INACTIVE': (0, 24, 1.0)     # Default
}

# Pattern base scores
PATTERN_SCORES = {
    'LIQUIDITY_SWEEP_REVERSAL': 75,
    'ORDER_BLOCK_BOUNCE': 70,
    'FAIR_VALUE_GAP_FILL': 65
}

class MarketRegime(Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    VOLATILE_RANGE = "volatile_range"
    CALM_RANGE = "calm_range"
    BREAKOUT = "breakout"

class SignalType(Enum):
    RAPID_ASSAULT = "RAPID_ASSAULT"
    PRECISION_STRIKE = "PRECISION_STRIKE"

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

@dataclass
class MarketTick:
    symbol: str
    bid: float
    ask: float
    spread: float
    volume: int
    timestamp: float


class EliteGuardEngine:
    """Refactored Elite Guard signal engine"""
    
    def __init__(self):
        # ZMQ setup
        self.context = zmq.Context()
        self.subscriber = None
        self.publisher = None
        
        # Market data storage
        self.candles = defaultdict(lambda: defaultdict(list))
        self.ticks = defaultdict(deque)
        self.last_signal_time = defaultdict(float)
        self.daily_signal_count = 0
        self.last_reset_date = datetime.now().date()
        
        # CITADEL Shield
        self.citadel = CitadelShieldFilter()
        
        # State
        self.running = False
        
        self._setup_connections()
    
    def _setup_connections(self):
        """Initialize ZMQ connections"""
        try:
            # Subscriber for market data
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect(f"tcp://localhost:{SUBSCRIBER_PORT}")
            self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
            
            # Publisher for signals
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(f"tcp://*:{PUBLISHER_PORT}")
            
            logger.info(f"Connected to market data on port {SUBSCRIBER_PORT}")
            logger.info(f"Publishing signals on port {PUBLISHER_PORT}")
        except Exception as e:
            logger.error(f"Failed to setup ZMQ connections: {e}")
            raise
    
    def get_active_session(self) -> Tuple[bool, str, float]:
        """Get current trading session"""
        utc_hour = datetime.now(pytz.UTC).hour
        
        for session, (start, end, boost) in SESSIONS.items():
            if session == 'INACTIVE':
                continue
            if start <= utc_hour < end:
                return True, session, boost
        
        return False, 'INACTIVE', 1.0
    
    def process_tick(self, data: Dict):
        """Process incoming tick data"""
        try:
            symbol = data.get('symbol', '')
            if not symbol:
                return
            
            tick = MarketTick(
                symbol=symbol,
                bid=float(data.get('bid', 0)),
                ask=float(data.get('ask', 0)),
                spread=float(data.get('spread', 0)),
                volume=int(data.get('volume', 0)),
                timestamp=time.time()
            )
            
            # Store tick
            self.ticks[symbol].append(tick)
            if len(self.ticks[symbol]) > 100:
                self.ticks[symbol].popleft()
            
            # Build candles
            self._update_candles(symbol, tick)
            
        except Exception as e:
            logger.debug(f"Tick processing error: {e}")
    
    def _update_candles(self, symbol: str, tick: MarketTick):
        """Update candle data from tick"""
        current_minute = int(tick.timestamp / 60) * 60
        
        for timeframe in ['M1', 'M5']:
            period = 60 if timeframe == 'M1' else 300
            candle_time = int(tick.timestamp / period) * period
            
            candles = self.candles[symbol][timeframe]
            mid_price = (tick.bid + tick.ask) / 2
            
            # Find or create candle
            if not candles or candles[-1]['time'] != candle_time:
                candles.append({
                    'time': candle_time,
                    'open': mid_price,
                    'high': mid_price,
                    'low': mid_price,
                    'close': mid_price,
                    'volume': tick.volume
                })
            else:
                candles[-1]['high'] = max(candles[-1]['high'], mid_price)
                candles[-1]['low'] = min(candles[-1]['low'], mid_price)
                candles[-1]['close'] = mid_price
                candles[-1]['volume'] += tick.volume
            
            # Keep only recent candles
            if len(candles) > CANDLE_LOOKBACK:
                candles.pop(0)
    
    def analyze_patterns(self, symbol: str) -> Optional[PatternSignal]:
        """Analyze market for trading patterns"""
        if symbol not in self.candles or 'M1' not in self.candles[symbol]:
            return None
        
        candles = self.candles[symbol]['M1']
        if len(candles) < MIN_CANDLES_REQUIRED:
            return None
        
        # Check each pattern type
        patterns = [
            self._detect_liquidity_sweep(symbol, candles),
            self._detect_order_block(symbol, candles),
            self._detect_fair_value_gap(symbol, candles)
        ]
        
        # Return best pattern
        valid_patterns = [p for p in patterns if p is not None]
        if valid_patterns:
            return max(valid_patterns, key=lambda x: x.confidence)
        
        return None
    
    def _detect_liquidity_sweep(self, symbol: str, candles: List) -> Optional[PatternSignal]:
        """Detect liquidity sweep reversal pattern"""
        if len(candles) < 5:
            return None
        
        recent = candles[-5:]
        prices = [c['close'] for c in recent]
        volumes = [c['volume'] for c in recent]
        
        # Check for spike and reversal
        price_range = max(prices) - min(prices)
        if price_range < 0.0003:  # 3 pips minimum
            return None
        
        # Volume surge check
        avg_volume = np.mean(volumes[:-1])
        if volumes[-1] > avg_volume * 1.3:
            # Detect direction
            if prices[-1] > prices[-2] and prices[-2] < prices[-3]:
                return PatternSignal(
                    pattern='LIQUIDITY_SWEEP_REVERSAL',
                    direction='BUY',
                    entry_price=prices[-1],
                    confidence=PATTERN_SCORES['LIQUIDITY_SWEEP_REVERSAL'],
                    timeframe='M1',
                    pair=symbol
                )
            elif prices[-1] < prices[-2] and prices[-2] > prices[-3]:
                return PatternSignal(
                    pattern='LIQUIDITY_SWEEP_REVERSAL',
                    direction='SELL',
                    entry_price=prices[-1],
                    confidence=PATTERN_SCORES['LIQUIDITY_SWEEP_REVERSAL'],
                    timeframe='M1',
                    pair=symbol
                )
        
        return None
    
    def _detect_order_block(self, symbol: str, candles: List) -> Optional[PatternSignal]:
        """Detect order block bounce pattern"""
        if len(candles) < 10:
            return None
        
        recent = candles[-10:]
        highs = [c['high'] for c in recent]
        lows = [c['low'] for c in recent]
        closes = [c['close'] for c in recent]
        
        # Find recent high/low zones
        recent_high = max(highs[-5:])
        recent_low = min(lows[-5:])
        current_price = closes[-1]
        
        # Check if price is near support/resistance
        high_distance = abs(current_price - recent_high) / current_price
        low_distance = abs(current_price - recent_low) / current_price
        
        if low_distance < 0.0025:  # Within 0.25% of support
            return PatternSignal(
                pattern='ORDER_BLOCK_BOUNCE',
                direction='BUY',
                entry_price=current_price,
                confidence=PATTERN_SCORES['ORDER_BLOCK_BOUNCE'],
                timeframe='M1',
                pair=symbol
            )
        elif high_distance < 0.0025:  # Within 0.25% of resistance
            return PatternSignal(
                pattern='ORDER_BLOCK_BOUNCE',
                direction='SELL',
                entry_price=current_price,
                confidence=PATTERN_SCORES['ORDER_BLOCK_BOUNCE'],
                timeframe='M1',
                pair=symbol
            )
        
        return None
    
    def _detect_fair_value_gap(self, symbol: str, candles: List) -> Optional[PatternSignal]:
        """Detect fair value gap pattern"""
        if len(candles) < 3:
            return None
        
        # Check for gap between candles
        for i in range(len(candles) - 2, 0, -1):
            gap_up = candles[i]['low'] > candles[i-1]['high']
            gap_down = candles[i]['high'] < candles[i-1]['low']
            
            if gap_up or gap_down:
                gap_size = abs(candles[i]['close'] - candles[i-1]['close'])
                if gap_size > 0.0004:  # 4 pips minimum
                    current_price = candles[-1]['close']
                    gap_mid = (candles[i]['close'] + candles[i-1]['close']) / 2
                    
                    # Check if price approaching gap
                    if abs(current_price - gap_mid) / current_price < 0.002:
                        direction = 'SELL' if gap_up else 'BUY'
                        return PatternSignal(
                            pattern='FAIR_VALUE_GAP_FILL',
                            direction=direction,
                            entry_price=current_price,
                            confidence=PATTERN_SCORES['FAIR_VALUE_GAP_FILL'],
                            timeframe='M1',
                            pair=symbol
                        )
        
        return None
    
    def apply_confluence_scoring(self, signal: PatternSignal) -> float:
        """Apply multi-factor confluence scoring"""
        score = signal.confidence
        
        # Session bonus
        active, session, boost = self.get_active_session()
        if active:
            score *= boost
        
        # Multi-timeframe alignment
        if self._check_timeframe_alignment(signal.pair, signal.direction):
            score += 10
        
        # Volume confirmation
        if self._check_volume_surge(signal.pair):
            score += 5
        
        # Spread quality
        current_spread = self._get_current_spread(signal.pair)
        if current_spread < 2.5:
            score += 3
        
        return min(score, 100)
    
    def _check_timeframe_alignment(self, symbol: str, direction: str) -> bool:
        """Check if multiple timeframes align"""
        if symbol not in self.candles:
            return False
        
        aligned = True
        for tf in ['M1', 'M5']:
            if tf not in self.candles[symbol] or len(self.candles[symbol][tf]) < 3:
                continue
            
            candles = self.candles[symbol][tf]
            trend = 'BUY' if candles[-1]['close'] > candles[-3]['close'] else 'SELL'
            if trend != direction:
                aligned = False
                break
        
        return aligned
    
    def _check_volume_surge(self, symbol: str) -> bool:
        """Check for volume surge"""
        if symbol not in self.candles or 'M1' not in self.candles[symbol]:
            return False
        
        candles = self.candles[symbol]['M1']
        if len(candles) < 5:
            return False
        
        recent_volumes = [c['volume'] for c in candles[-5:]]
        avg_volume = np.mean(recent_volumes[:-1])
        
        return recent_volumes[-1] > avg_volume * 1.2
    
    def _get_current_spread(self, symbol: str) -> float:
        """Get current spread for symbol"""
        if symbol in self.ticks and self.ticks[symbol]:
            return self.ticks[symbol][-1].spread
        return 999.0
    
    def should_fire_signal(self, symbol: str) -> bool:
        """Check if we should fire a signal"""
        # Daily limit check
        if self.daily_signal_count >= MAX_SIGNALS_PER_DAY:
            return False
        
        # Cooldown check
        last_signal = self.last_signal_time.get(symbol, 0)
        if time.time() - last_signal < SIGNAL_COOLDOWN_SECONDS:
            return False
        
        # Session check
        active, _, _ = self.get_active_session()
        return active
    
    def create_signal(self, pattern: PatternSignal) -> Dict:
        """Create signal dictionary"""
        # Apply confluence scoring
        final_score = self.apply_confluence_scoring(pattern)
        
        # CITADEL Shield scoring
        signal_dict = {
            'symbol': pattern.pair,
            'direction': pattern.direction,
            'entry_price': pattern.entry_price,
            'pattern_type': pattern.pattern,
            'confidence': final_score
        }
        
        shield_score = self.citadel.calculate_shield_score(signal_dict)
        
        # Calculate SL/TP
        pip_value = 0.0001 if 'JPY' not in pattern.pair else 0.01
        sl_distance = 30 * pip_value
        tp_distance = 60 * pip_value
        
        if pattern.direction == 'BUY':
            sl_price = pattern.entry_price - sl_distance
            tp_price = pattern.entry_price + tp_distance
        else:
            sl_price = pattern.entry_price + sl_distance
            tp_price = pattern.entry_price - tp_distance
        
        # Build final signal
        return {
            'signal_id': f"ELITE_GUARD_{pattern.pair}_{int(time.time())}",
            'symbol': pattern.pair,
            'direction': pattern.direction,
            'entry_price': round(pattern.entry_price, 5),
            'stop_loss': round(sl_price, 5),
            'take_profit': round(tp_price, 5),
            'stop_pips': 30,
            'target_pips': 60,
            'confidence': round(final_score, 1),
            'shield_score': round(shield_score, 1),
            'pattern_type': pattern.pattern,
            'signal_type': SignalType.PRECISION_STRIKE.value,
            'created_at': int(time.time()),
            'expires_at': int(time.time() + 300)
        }
    
    def publish_signal(self, signal: Dict):
        """Publish signal to ZMQ"""
        if self.publisher:
            try:
                message = f"ELITE_GUARD_SIGNAL {json.dumps(signal)}"
                self.publisher.send_string(message)
                
                # Update tracking
                self.last_signal_time[signal['symbol']] = time.time()
                self.daily_signal_count += 1
                
                logger.info(f"Signal published: {signal['signal_id']}")
            except Exception as e:
                logger.error(f"Failed to publish signal: {e}")
    
    def reset_daily_counters(self):
        """Reset daily counters at midnight"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_signal_count = 0
            self.last_reset_date = current_date
            logger.info("Daily counters reset")
    
    def main_loop(self):
        """Main processing loop"""
        logger.info("Elite Guard v6.1 started")
        self.running = True
        
        while self.running:
            try:
                # Reset daily counters if needed
                self.reset_daily_counters()
                
                # Receive market data
                if self.subscriber.poll(100):
                    message = self.subscriber.recv_string()
                    
                    if message.startswith("TICK "):
                        data = json.loads(message[5:])
                        self.process_tick(data)
                        
                        # Analyze for patterns
                        symbol = data.get('symbol', '')
                        if symbol and self.should_fire_signal(symbol):
                            pattern = self.analyze_patterns(symbol)
                            if pattern:
                                signal = self.create_signal(pattern)
                                self.publish_signal(signal)
                
                time.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(1)
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        
        if self.subscriber:
            self.subscriber.close()
        if self.publisher:
            self.publisher.close()
        if self.context:
            self.context.term()
        
        logger.info("Elite Guard shutdown complete")


def immortal_main_loop():
    """Immortal wrapper with auto-restart"""
    consecutive_failures = 0
    max_failures = 5
    
    while True:
        try:
            logger.info("Starting Elite Guard engine...")
            engine = EliteGuardEngine()
            engine.main_loop()
            consecutive_failures = 0
            
        except KeyboardInterrupt:
            logger.info("Manual shutdown requested")
            break
            
        except Exception as e:
            consecutive_failures += 1
            wait_time = min(30 * consecutive_failures, 300)
            
            logger.error(f"Engine crashed: {e}")
            logger.error(traceback.format_exc())
            
            if consecutive_failures >= max_failures:
                logger.error(f"Max failures ({max_failures}) reached")
                wait_time = 300
            
            logger.info(f"Restarting in {wait_time} seconds...")
            time.sleep(wait_time)


if __name__ == "__main__":
    immortal_main_loop()