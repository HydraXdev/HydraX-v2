#!/usr/bin/env python3
"""
ELITE GUARD v6.0 + CITADEL SHIELD - Signal Generation Engine
Integrates with existing ZMQ data stream for high-probability signal generation
"""

import zmq
import json
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from collections import defaultdict, deque

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    VOLATILE_RANGE = "volatile_range"
    CALM_RANGE = "calm_range"
    BREAKOUT = "breakout"
    NEWS_EVENT = "news_event"

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
    """
    ELITE GUARD v6.0 Signal Generation Engine
    Connects to existing ZMQ data stream for real-time pattern detection
    """
    
    def __init__(self):
        # ZMQ Configuration
        self.context = zmq.Context()
        self.subscriber = None
        self.publisher = None
        
        # Trading pairs (15 pairs, NO XAUUSD per constraints)
        self.trading_pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
            "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
            "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
        ]
        
        # Market data storage (multi-timeframe)
        self.tick_data = defaultdict(lambda: deque(maxlen=200))  # Last 200 ticks per pair
        self.m1_data = defaultdict(lambda: deque(maxlen=200))    # M1 OHLC data
        self.m5_data = defaultdict(lambda: deque(maxlen=200))    # M5 OHLC data
        self.m15_data = defaultdict(lambda: deque(maxlen=200))   # M15 OHLC data
        
        # Signal generation controls
        self.daily_signal_count = 0
        self.last_signal_time = {}
        self.signal_cooldown = 5 * 60  # 5 minutes per pair
        self.running = True
        
        # VENOM session intelligence (preserved from original)
        self.session_intelligence = {
            'LONDON': {
                'optimal_pairs': ['EURUSD', 'GBPUSD', 'EURGBP', 'USDCHF'],
                'win_rate_boost': 0.10,
                'volume_multiplier': 1.5,
                'quality_bonus': 18
            },
            'NY': {
                'optimal_pairs': ['EURUSD', 'GBPUSD', 'USDCAD'],
                'win_rate_boost': 0.08,
                'volume_multiplier': 1.3,
                'quality_bonus': 15
            },
            'OVERLAP': {
                'optimal_pairs': ['EURUSD', 'GBPUSD', 'EURJPY', 'GBPJPY'],
                'win_rate_boost': 0.15,
                'volume_multiplier': 2.0,
                'quality_bonus': 25
            },
            'ASIAN': {
                'optimal_pairs': ['USDJPY', 'AUDUSD', 'NZDUSD'],
                'win_rate_boost': 0.03,
                'volume_multiplier': 0.9,
                'quality_bonus': 8
            }
        }
        
        logger.info("🛡️ ELITE GUARD v6.0 Engine Initialized")
        logger.info("📊 Monitoring 15 pairs for high-probability patterns")
    
    def setup_zmq_connections(self):
        """Setup ZMQ subscriber to existing data stream"""
        try:
            # Subscribe to telemetry data (port 5556)
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://127.0.0.1:5556")
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
            self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            
            # Publisher for signals (port 5557 - new port for Elite Guard)
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")
            
            logger.info("✅ ZMQ connections established")
            logger.info("📡 Subscribing to telemetry: tcp://127.0.0.1:5556")
            logger.info("📡 Publishing signals on: tcp://*:5557")
            
        except Exception as e:
            logger.error(f"❌ ZMQ setup failed: {e}")
            raise
    
    def get_current_session(self) -> str:
        """Determine current trading session"""
        utc_hour = datetime.utcnow().hour
        
        if 7 <= utc_hour <= 16:  # London session
            if 12 <= utc_hour <= 16:  # Overlap with NY
                return 'OVERLAP'
            return 'LONDON'
        elif 13 <= utc_hour <= 22:  # NY session
            return 'NY'
        elif 22 <= utc_hour or utc_hour <= 7:  # Asian session
            return 'ASIAN'
        else:
            return 'OFF_HOURS'
    
    def process_market_data(self, data: Dict):
        """Process incoming market data from ZMQ stream"""
        try:
            # Extract tick data from ZMQ message
            if 'symbol' in data and 'bid' in data and 'ask' in data:
                symbol = data['symbol']
                
                if symbol in self.trading_pairs:
                    tick = MarketTick(
                        symbol=symbol,
                        bid=float(data['bid']),
                        ask=float(data['ask']),
                        spread=float(data.get('spread', (data['ask'] - data['bid']) * 10000)),
                        volume=int(data.get('volume', 0)),
                        timestamp=time.time()
                    )
                    
                    # Store tick data
                    self.tick_data[symbol].append(tick)
                    
                    # Update OHLC data (simplified - in production would use proper timeframe aggregation)
                    self.update_ohlc_data(symbol, tick)
                    
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    def update_ohlc_data(self, symbol: str, tick: MarketTick):
        """Update OHLC data for different timeframes"""
        mid_price = (tick.bid + tick.ask) / 2
        
        # For now, store simplified price data - in production would aggregate by time
        price_data = {
            'price': mid_price,
            'timestamp': tick.timestamp,
            'volume': tick.volume
        }
        
        # Update all timeframes (simplified)
        self.m1_data[symbol].append(price_data)
        if len(self.m1_data[symbol]) % 5 == 0:  # Every 5 M1 = M5
            self.m5_data[symbol].append(price_data)
        if len(self.m5_data[symbol]) % 3 == 0:  # Every 3 M5 = M15
            self.m15_data[symbol].append(price_data)
    
    def detect_liquidity_sweep_reversal(self, symbol: str) -> Optional[PatternSignal]:
        """Detect liquidity sweep reversal pattern (highest priority - 75 base score)"""
        if len(self.m1_data[symbol]) < 20:
            return None
            
        try:
            recent_prices = [p['price'] for p in list(self.m1_data[symbol])[-20:]]
            recent_volumes = [p['volume'] for p in list(self.m1_data[symbol])[-20:]]
            
            # Look for price spike followed by quick reversal
            if len(recent_prices) < 10:
                return None
                
            # Calculate price movement and volume surge
            price_change = abs(recent_prices[-1] - recent_prices[-5]) / recent_prices[-5] * 100
            avg_volume = np.mean(recent_volumes[-10:]) if recent_volumes else 1
            recent_volume = recent_volumes[-1] if recent_volumes else 1
            volume_surge = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Pattern criteria
            if price_change > 0.02 and volume_surge > 1.5:  # 2+ pip movement with volume surge
                # Determine reversal direction
                if recent_prices[-1] > recent_prices[-3]:  # Price spiked up
                    direction = "SELL"  # Expect reversal down
                else:  # Price spiked down
                    direction = "BUY"   # Expect reversal up
                
                return PatternSignal(
                    pattern="LIQUIDITY_SWEEP_REVERSAL",
                    direction=direction,
                    entry_price=recent_prices[-1],
                    confidence=75,  # Base score
                    timeframe="M1",
                    pair=symbol
                )
                
        except Exception as e:
            logger.error(f"Error detecting liquidity sweep for {symbol}: {e}")
        
        return None
    
    def detect_order_block_bounce(self, symbol: str) -> Optional[PatternSignal]:
        """Detect order block bounce pattern (70 base score)"""
        if len(self.m5_data[symbol]) < 30:
            return None
            
        try:
            prices = [p['price'] for p in list(self.m5_data[symbol])[-30:]]
            
            # Look for consolidation zone (order block)
            recent_high = max(prices[-10:])
            recent_low = min(prices[-10:])
            ob_range = recent_high - recent_low
            
            # Check if price is touching order block
            current_price = prices[-1]
            
            # Bullish order block (price near recent low)
            if current_price <= recent_low + (ob_range * 0.2):
                return PatternSignal(
                    pattern="ORDER_BLOCK_BOUNCE",
                    direction="BUY",
                    entry_price=current_price,
                    confidence=70,
                    timeframe="M5",
                    pair=symbol
                )
            
            # Bearish order block (price near recent high)
            if current_price >= recent_high - (ob_range * 0.2):
                return PatternSignal(
                    pattern="ORDER_BLOCK_BOUNCE",
                    direction="SELL", 
                    entry_price=current_price,
                    confidence=70,
                    timeframe="M5",
                    pair=symbol
                )
                
        except Exception as e:
            logger.error(f"Error detecting order block for {symbol}: {e}")
        
        return None
    
    def detect_fair_value_gap_fill(self, symbol: str) -> Optional[PatternSignal]:
        """Detect fair value gap fill pattern (65 base score)"""
        if len(self.m5_data[symbol]) < 20:
            return None
            
        try:
            prices = [p['price'] for p in list(self.m5_data[symbol])[-20:]]
            
            # Look for gaps in price action
            for i in range(len(prices) - 5, len(prices) - 1):
                gap_size = abs(prices[i+1] - prices[i]) / prices[i] * 100
                
                if gap_size > 0.05:  # 5+ pip gap
                    gap_midpoint = (prices[i] + prices[i+1]) / 2
                    current_price = prices[-1]
                    
                    # Check if price is approaching gap
                    distance_to_gap = abs(current_price - gap_midpoint) / current_price * 100
                    
                    if distance_to_gap < 0.02:  # Within 2 pips of gap
                        # Determine fill direction
                        if current_price < gap_midpoint:
                            direction = "BUY"  # Fill gap upward
                        else:
                            direction = "SELL"  # Fill gap downward
                        
                        return PatternSignal(
                            pattern="FAIR_VALUE_GAP_FILL",
                            direction=direction,
                            entry_price=current_price,
                            confidence=65,
                            timeframe="M5",
                            pair=symbol
                        )
                        
        except Exception as e:
            logger.error(f"Error detecting FVG for {symbol}: {e}")
        
        return None
    
    def apply_ml_confluence_scoring(self, signal: PatternSignal) -> float:
        """Apply ML-style confluence scoring (simplified for now)"""
        try:
            # Base features for scoring
            session = self.get_current_session()
            session_intel = self.session_intelligence.get(session, {})
            
            score = signal.confidence  # Start with base pattern score
            
            # Session compatibility bonus
            if signal.pair in session_intel.get('optimal_pairs', []):
                score += session_intel.get('quality_bonus', 0)
            
            # Volume confirmation (simplified)
            if len(self.tick_data[signal.pair]) > 5:
                recent_ticks = list(self.tick_data[signal.pair])[-5:]
                avg_volume = np.mean([t.volume for t in recent_ticks]) if recent_ticks else 1
                if avg_volume > 1000:  # Above average volume
                    score += 5
            
            # Spread quality bonus
            if len(self.tick_data[signal.pair]) > 0:
                current_tick = list(self.tick_data[signal.pair])[-1]
                if current_tick.spread < 2.0:  # Tight spread
                    score += 3
            
            # Multi-timeframe alignment (simplified)
            if len(self.m1_data[signal.pair]) > 10 and len(self.m5_data[signal.pair]) > 10:
                m1_trend = self.calculate_simple_trend(signal.pair, 'M1')
                m5_trend = self.calculate_simple_trend(signal.pair, 'M5')
                
                if m1_trend == m5_trend == signal.direction:
                    score += 15  # Strong alignment bonus
                    signal.tf_alignment = 0.9
                elif m1_trend == signal.direction or m5_trend == signal.direction:
                    score += 8   # Partial alignment
                    signal.tf_alignment = 0.6
            
            return min(score, 90)  # Cap at 90%
            
        except Exception as e:
            logger.error(f"Error in ML scoring for {signal.pair}: {e}")
            return signal.confidence
    
    def calculate_simple_trend(self, symbol: str, timeframe: str) -> str:
        """Calculate simple trend direction for timeframe"""
        try:
            if timeframe == 'M1':
                data = self.m1_data[symbol]
            elif timeframe == 'M5':
                data = self.m5_data[symbol]
            else:
                data = self.m15_data[symbol]
            
            if len(data) < 10:
                return "NEUTRAL"
                
            prices = [p['price'] for p in list(data)[-10:]]
            short_ma = np.mean(prices[-3:])  # 3-period MA
            long_ma = np.mean(prices[-10:])  # 10-period MA
            
            if short_ma > long_ma:
                return "BUY"
            elif short_ma < long_ma:
                return "SELL"
            else:
                return "NEUTRAL"
                
        except:
            return "NEUTRAL"
    
    def calculate_atr(self, symbol: str, periods: int = 14) -> float:
        """Calculate Average True Range for stop/target calculation"""
        try:
            if len(self.m5_data[symbol]) < periods:
                return 0.0001  # Default pip size
                
            prices = [p['price'] for p in list(self.m5_data[symbol])[-periods:]]
            
            if len(prices) < 2:
                return 0.0001
                
            # Simplified ATR calculation
            ranges = []
            for i in range(1, len(prices)):
                ranges.append(abs(prices[i] - prices[i-1]))
            
            atr = np.mean(ranges) if ranges else 0.0001
            return max(atr, 0.0001)  # Minimum ATR
            
        except:
            return 0.0001
    
    def generate_elite_signal(self, pattern_signal: PatternSignal, user_tier: str = 'average') -> Dict:
        """Generate final Elite Guard signal with tier-specific parameters"""
        try:
            atr = self.calculate_atr(pattern_signal.pair, 14)
            
            # Tier-specific configuration
            if user_tier in ['average', 'nibbler']:
                # RAPID_ASSAULT (1:1.5 R:R)
                sl_multiplier = 1.5
                tp_multiplier = 1.5
                duration = 30 * 60  # 30 minutes
                signal_type = SignalType.RAPID_ASSAULT
                xp_multiplier = 1.5
            else:
                # PRECISION_STRIKE (1:2 R:R)
                sl_multiplier = 2.0
                tp_multiplier = 2.0
                duration = 60 * 60  # 60 minutes
                signal_type = SignalType.PRECISION_STRIKE
                xp_multiplier = 2.0
            
            # Calculate levels
            pip_size = 0.01 if 'JPY' in pattern_signal.pair else 0.0001
            stop_distance = atr * sl_multiplier
            stop_pips = int(stop_distance / pip_size)
            target_pips = int(stop_pips * tp_multiplier)
            
            entry_price = pattern_signal.entry_price
            
            if pattern_signal.direction == "BUY":
                stop_loss = entry_price - stop_distance
                take_profit = entry_price + (stop_distance * tp_multiplier)
            else:
                stop_loss = entry_price + stop_distance
                take_profit = entry_price - (stop_distance * tp_multiplier)
            
            # Create signal
            signal = {
                'signal_id': f'ELITE_GUARD_{pattern_signal.pair}_{int(time.time())}',
                'pair': pattern_signal.pair,
                'direction': pattern_signal.direction,
                'signal_type': signal_type.value,
                'pattern': pattern_signal.pattern,
                'confidence': round(pattern_signal.final_score, 1),
                'entry_price': round(entry_price, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'stop_pips': stop_pips,
                'target_pips': target_pips,
                'risk_reward': round(target_pips / stop_pips, 1),
                'duration': duration,
                'xp_reward': int(pattern_signal.final_score * xp_multiplier),
                'session': self.get_current_session(),
                'timeframe': pattern_signal.timeframe,
                'timestamp': time.time(),
                'source': 'ELITE_GUARD_v6'
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
    
    def scan_for_patterns(self, symbol: str) -> List[PatternSignal]:
        """Scan single pair for all Elite Guard patterns"""
        patterns = []
        
        try:
            # 1. Liquidity Sweep Reversal (highest priority)
            sweep_signal = self.detect_liquidity_sweep_reversal(symbol)
            if sweep_signal:
                patterns.append(sweep_signal)
            
            # 2. Order Block Bounce
            ob_signal = self.detect_order_block_bounce(symbol)
            if ob_signal:
                patterns.append(ob_signal)
            
            # 3. Fair Value Gap Fill
            fvg_signal = self.detect_fair_value_gap_fill(symbol)
            if fvg_signal:
                patterns.append(fvg_signal)
            
            # Apply ML confluence scoring to all patterns
            for pattern in patterns:
                pattern.final_score = self.apply_ml_confluence_scoring(pattern)
            
            # Filter by minimum quality (60+ score)
            quality_patterns = [p for p in patterns if p.final_score >= 60]
            
            # Sort by score (highest first)
            return sorted(quality_patterns, key=lambda x: x.final_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error scanning patterns for {symbol}: {e}")
            return []
    
    def publish_signal(self, signal: Dict):
        """Publish signal via ZMQ to BITTEN core"""
        try:
            if self.publisher:
                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
                logger.info(f"📡 Published signal: {signal['pair']} {signal['direction']} @ {signal['confidence']}%")
        except Exception as e:
            logger.error(f"Error publishing signal: {e}")
    
    def main_loop(self):
        """Main Elite Guard processing loop"""
        logger.info("🚀 Starting Elite Guard main processing loop")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Reset daily counter at midnight
                if datetime.now().hour == 0 and datetime.now().minute == 0:
                    self.daily_signal_count = 0
                    logger.info("🔄 Daily signal counter reset")
                
                # Daily limit check (20-30 signals max)
                if self.daily_signal_count >= 30:
                    time.sleep(300)  # Wait 5 minutes
                    continue
                
                # Scan all pairs for patterns
                for symbol in self.trading_pairs:
                    try:
                        # Cooldown check (5 minutes per pair)
                        if symbol in self.last_signal_time:
                            if current_time - self.last_signal_time[symbol] < self.signal_cooldown:
                                continue
                        
                        # Scan for patterns
                        patterns = self.scan_for_patterns(symbol)
                        
                        if patterns:
                            # Take highest scoring pattern
                            best_pattern = patterns[0]
                            
                            # Generate signals for different tiers
                            rapid_signal = self.generate_elite_signal(best_pattern, 'average')
                            precision_signal = self.generate_elite_signal(best_pattern, 'sniper')
                            
                            if rapid_signal and precision_signal:
                                # Publish both signals
                                self.publish_signal(rapid_signal)
                                self.publish_signal(precision_signal)
                                
                                # Update tracking
                                self.last_signal_time[symbol] = current_time
                                self.daily_signal_count += 1
                                
                                logger.info(f"🎯 ELITE GUARD: {symbol} {best_pattern.direction} "
                                          f"@ {best_pattern.final_score:.1f}% | {best_pattern.pattern}")
                    
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue
                
                # Adaptive sleep based on session
                session = self.get_current_session()
                sleep_time = 30 if session == 'OVERLAP' else 60
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)
    
    def data_listener_loop(self):
        """Separate thread for listening to ZMQ data stream"""
        logger.info("📡 Starting ZMQ data listener")
        
        while self.running:
            try:
                if self.subscriber:
                    # Receive market data
                    message = self.subscriber.recv_string(zmq.NOBLOCK)
                    
                    try:
                        # Parse JSON data
                        data = json.loads(message)
                        self.process_market_data(data)
                    except json.JSONDecodeError:
                        # Handle non-JSON messages
                        if "MARKET_DATA" in message:
                            # Extract JSON part
                            json_part = message.split("MARKET_DATA", 1)[1].strip()
                            data = json.loads(json_part)
                            self.process_market_data(data)
                        
            except zmq.Again:
                # No message received, continue
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in data listener: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the Elite Guard engine"""
        try:
            # Setup ZMQ connections
            self.setup_zmq_connections()
            
            # Start data listener thread
            data_thread = threading.Thread(target=self.data_listener_loop, daemon=True)
            data_thread.start()
            
            # Give data listener time to start
            time.sleep(2)
            
            logger.info("✅ Elite Guard v6.0 engine started successfully")
            logger.info("🎯 Target: 60-70% win rate | 20-30 signals/day")
            logger.info("🛡️ Ready for high-probability pattern detection")
            
            # Start main processing loop
            self.main_loop()
            
        except KeyboardInterrupt:
            logger.info("👋 Elite Guard engine shutting down...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Elite Guard engine error: {e}")
        finally:
            if self.context:
                self.context.term()

if __name__ == "__main__":
    engine = EliteGuardEngine()
    engine.start()