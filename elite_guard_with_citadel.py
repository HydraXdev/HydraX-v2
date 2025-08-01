#!/usr/bin/env python3
"""
ELITE GUARD v6.0 + CITADEL SHIELD - Integrated Signal Engine
Complete implementation with ZMQ integration and modular CITADEL filtering

🚨🚨🚨 CRITICAL DATA FLOW REQUIREMENT 🚨🚨🚨
This engine REQUIRES telemetry_pubbridge.py to be running FIRST!
Data flow: EA → 5556 → telemetry_pubbridge → 5560 → Elite Guard
Without the bridge, NO DATA WILL FLOW. See /EA_DATA_FLOW_CONTRACT.md
🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
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
import requests

# Import CITADEL Shield
from citadel_shield_filter import CitadelShieldFilter

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

class EliteGuardWithCitadel:
    """
    ELITE GUARD v6.0 + CITADEL SHIELD - Complete Signal Engine
    Integrates with ZMQ data stream and includes modular CITADEL Shield filtering
    """
    
    def __init__(self):
        # ZMQ Configuration
        self.context = zmq.Context()
        self.subscriber = None
        self.publisher = None
        
        # Initialize CITADEL Shield Filter
        self.citadel_shield = CitadelShieldFilter()
        
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
        
        # Performance tracking
        self.signals_generated = 0
        self.signals_shielded = 0
        self.signals_blocked = 0
        
        # Truth tracker integration
        self.truth_tracker_url = "http://localhost:8888/api/truth_tracker"
        self.enable_truth_tracking = True
        
        # VENOM session intelligence (preserved from original)
        self.session_intelligence = {
            'LONDON': {
                'optimal_pairs': ['EURUSD', 'GBPUSD', 'EURGBP', 'USDCHF'],
                'win_rate_boost': 0.10,
                'volume_multiplier': 1.5,
                'quality_bonus': 18,
                'signals_per_hour': 2
            },
            'NY': {
                'optimal_pairs': ['EURUSD', 'GBPUSD', 'USDCAD'],
                'win_rate_boost': 0.08,
                'volume_multiplier': 1.3,
                'quality_bonus': 15,
                'signals_per_hour': 2
            },
            'OVERLAP': {
                'optimal_pairs': ['EURUSD', 'GBPUSD', 'EURJPY', 'GBPJPY'],
                'win_rate_boost': 0.15,
                'volume_multiplier': 2.0,
                'quality_bonus': 25,
                'signals_per_hour': 3  # More signals during overlap
            },
            'ASIAN': {
                'optimal_pairs': ['USDJPY', 'AUDUSD', 'NZDUSD'],
                'win_rate_boost': 0.03,
                'volume_multiplier': 0.9,
                'quality_bonus': 8,
                'signals_per_hour': 1  # Fewer signals during Asian
            }
        }
        
        logger.info("🛡️ ELITE GUARD v6.0 + CITADEL SHIELD Engine Initialized")
        logger.info("📊 Monitoring 15 pairs for high-probability patterns")
        logger.info("🎯 Target: 60-70% win rate | 20-30 signals/day | 1-2 per hour")
    
    def setup_zmq_connections(self):
        """Setup ZMQ subscriber to shared telemetry feed"""
        try:
            # Subscribe to shared telemetry feed (port 5560)
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect("tcp://127.0.0.1:5560")
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
            self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            
            # Publisher for signals (port 5557 - Elite Guard output)
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")
            
            logger.info("✅ ZMQ connections established")
            logger.info("📡 Subscribing to shared feed: tcp://127.0.0.1:5560")
            logger.info("📡 Publishing signals on: tcp://*:5557")
            
        except Exception as e:
            logger.error(f"❌ ZMQ setup failed: {e}")
            raise
    
    def enable_citadel_demo_mode(self):
        """Enable CITADEL Shield demo mode for testing"""
        self.citadel_shield.enable_demo_mode()
        logger.info("🧪 CITADEL Shield demo mode enabled")
    
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
            # Handle different message formats from ZMQ stream
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    return
            
            # Extract tick data from various possible formats
            symbol = None
            bid = ask = spread = volume = None
            
            # Format 1: Direct symbol data
            if 'symbol' in data and 'bid' in data:
                symbol = data['symbol']
                bid = float(data['bid'])
                ask = float(data['ask'])
                spread = float(data.get('spread', (ask - bid) * 10000))
                volume = int(data.get('volume', 0))
            
            # Format 2: Nested tick data
            elif 'ticks' in data:
                for tick in data['ticks']:
                    if 'symbol' in tick:
                        symbol = tick['symbol']
                        bid = float(tick['bid'])
                        ask = float(tick['ask'])
                        spread = float(tick.get('spread', (ask - bid) * 10000))
                        volume = int(tick.get('volume', 0))
                        break
            
            # Format 3: Market data with multiple symbols
            elif isinstance(data, dict):
                for key, value in data.items():
                    if key in self.trading_pairs and isinstance(value, dict):
                        symbol = key
                        if 'bid' in value and 'ask' in value:
                            bid = float(value['bid'])
                            ask = float(value['ask'])
                            spread = float(value.get('spread', (ask - bid) * 10000))
                            volume = int(value.get('volume', 0))
                            break
            
            if symbol and symbol in self.trading_pairs and bid and ask:
                tick = MarketTick(
                    symbol=symbol,
                    bid=bid,
                    ask=ask,
                    spread=spread,
                    volume=volume,
                    timestamp=time.time()
                )
                
                # Store tick data
                self.tick_data[symbol].append(tick)
                
                # Update OHLC data
                self.update_ohlc_data(symbol, tick)
                
                logger.debug(f"📊 Processed tick: {symbol} {bid}/{ask}")
                    
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    def update_ohlc_data(self, symbol: str, tick: MarketTick):
        """Update OHLC data for different timeframes"""
        mid_price = (tick.bid + tick.ask) / 2
        
        price_data = {
            'price': mid_price,
            'timestamp': tick.timestamp,
            'volume': tick.volume,
            'bid': tick.bid,
            'ask': tick.ask
        }
        
        # Update all timeframes (simplified aggregation)
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
            recent_data = list(self.m1_data[symbol])[-20:]
            recent_prices = [p['price'] for p in recent_data]
            recent_volumes = [p['volume'] for p in recent_data]
            
            if len(recent_prices) < 10:
                return None
                
            # Calculate price movement and volume characteristics
            price_range = max(recent_prices[-5:]) - min(recent_prices[-5:])
            avg_price = np.mean(recent_prices[-10:])
            price_change_pct = (price_range / avg_price) * 100
            
            # Volume analysis
            avg_volume = np.mean(recent_volumes[-10:]) if recent_volumes else 1
            recent_volume = recent_volumes[-1] if recent_volumes else 1
            volume_surge = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Liquidity sweep criteria: sharp price movement + volume surge
            if price_change_pct > 0.03 and volume_surge > 1.3:  # 3+ pip movement with 30%+ volume surge
                # Determine reversal direction based on recent price action
                latest_price = recent_prices[-1]
                prev_price = recent_prices[-3]
                
                if latest_price > prev_price:
                    direction = "SELL"  # Price spiked up, expect reversal down
                else:
                    direction = "BUY"   # Price spiked down, expect reversal up
                
                return PatternSignal(
                    pattern="LIQUIDITY_SWEEP_REVERSAL",
                    direction=direction,
                    entry_price=latest_price,
                    confidence=75,  # Base score
                    timeframe="M1",
                    pair=symbol
                )
                
        except Exception as e:
            logger.debug(f"Error detecting liquidity sweep for {symbol}: {e}")
        
        return None
    
    def detect_order_block_bounce(self, symbol: str) -> Optional[PatternSignal]:
        """Detect order block bounce pattern (70 base score)"""
        if len(self.m5_data[symbol]) < 30:
            return None
            
        try:
            recent_data = list(self.m5_data[symbol])[-30:]
            prices = [p['price'] for p in recent_data]
            
            # Identify consolidation zone (order block)
            recent_prices = prices[-15:]  # Last 15 M5 candles
            recent_high = max(recent_prices)
            recent_low = min(recent_prices)
            ob_range = recent_high - recent_low
            
            if ob_range == 0:
                return None
            
            current_price = prices[-1]
            
            # Check if price is touching order block boundaries
            # Bullish order block (price near recent low)
            if current_price <= recent_low + (ob_range * 0.25):  # Within 25% of low
                return PatternSignal(
                    pattern="ORDER_BLOCK_BOUNCE",
                    direction="BUY",
                    entry_price=current_price,
                    confidence=70,
                    timeframe="M5",
                    pair=symbol
                )
            
            # Bearish order block (price near recent high)
            if current_price >= recent_high - (ob_range * 0.25):  # Within 25% of high
                return PatternSignal(
                    pattern="ORDER_BLOCK_BOUNCE",
                    direction="SELL", 
                    entry_price=current_price,
                    confidence=70,
                    timeframe="M5",
                    pair=symbol
                )
                
        except Exception as e:
            logger.debug(f"Error detecting order block for {symbol}: {e}")
        
        return None
    
    def detect_fair_value_gap_fill(self, symbol: str) -> Optional[PatternSignal]:
        """Detect fair value gap fill pattern (65 base score)"""
        if len(self.m5_data[symbol]) < 20:
            return None
            
        try:
            recent_data = list(self.m5_data[symbol])[-20:]
            prices = [p['price'] for p in recent_data]
            
            current_price = prices[-1]
            
            # Look for price gaps in recent history
            for i in range(len(prices) - 8, len(prices) - 2):
                if i < 1:
                    continue
                    
                # Calculate gap between consecutive prices
                gap_size = abs(prices[i] - prices[i-1]) / prices[i] * 100
                
                if gap_size > 0.04:  # 4+ pip gap
                    gap_start = prices[i-1]
                    gap_end = prices[i]
                    gap_midpoint = (gap_start + gap_end) / 2
                    
                    # Check if current price is approaching the gap
                    distance_to_gap = abs(current_price - gap_midpoint) / current_price * 100
                    
                    if distance_to_gap < 0.03:  # Within 3 pips of gap midpoint
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
            logger.debug(f"Error detecting FVG for {symbol}: {e}")
        
        return None
    
    def apply_ml_confluence_scoring(self, signal: PatternSignal) -> float:
        """Apply ML-style confluence scoring"""
        try:
            session = self.get_current_session()
            session_intel = self.session_intelligence.get(session, {})
            
            score = signal.confidence  # Start with base pattern score
            
            # Session compatibility bonus
            if signal.pair in session_intel.get('optimal_pairs', []):
                score += session_intel.get('quality_bonus', 0)
            
            # Volume confirmation
            if len(self.tick_data[signal.pair]) > 5:
                recent_ticks = list(self.tick_data[signal.pair])[-5:]
                avg_volume = np.mean([t.volume for t in recent_ticks]) if recent_ticks else 1
                if avg_volume > 1000:  # Above average volume
                    score += 5
            
            # Spread quality bonus
            if len(self.tick_data[signal.pair]) > 0:
                current_tick = list(self.tick_data[signal.pair])[-1]
                if current_tick.spread < 2.5:  # Tight spread
                    score += 3
            
            # Multi-timeframe alignment
            if len(self.m1_data[signal.pair]) > 10 and len(self.m5_data[signal.pair]) > 10:
                m1_trend = self.calculate_simple_trend(signal.pair, 'M1')
                m5_trend = self.calculate_simple_trend(signal.pair, 'M5')
                
                if m1_trend == m5_trend == signal.direction:
                    score += 15  # Strong alignment
                    signal.tf_alignment = 0.9
                elif m1_trend == signal.direction or m5_trend == signal.direction:
                    score += 8   # Partial alignment
                    signal.tf_alignment = 0.6
            
            # Volatility bonus (moderate volatility is good for scalping)
            atr = self.calculate_atr(signal.pair, 10)
            if 0.0003 <= atr <= 0.0008:  # Optimal volatility range
                score += 5
            
            return min(score, 88)  # Cap at 88% (realistic maximum)
            
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
                
            recent_data = list(data)[-10:]
            prices = [p['price'] for p in recent_data]
            
            short_ma = np.mean(prices[-3:])   # 3-period MA
            long_ma = np.mean(prices[-10:])   # 10-period MA
            
            if short_ma > long_ma * 1.0001:   # 0.01% threshold to avoid noise
                return "BUY"
            elif short_ma < long_ma * 0.9999:
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
                
            recent_data = list(self.m5_data[symbol])[-periods:]
            prices = [p['price'] for p in recent_data]
            
            if len(prices) < 2:
                return 0.0001
                
            # Calculate price ranges
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
            stop_distance = max(atr * sl_multiplier, 10 * pip_size)  # Minimum 10 pips
            stop_pips = int(stop_distance / pip_size)
            target_pips = int(stop_pips * tp_multiplier)
            
            entry_price = pattern_signal.entry_price
            
            if pattern_signal.direction == "BUY":
                stop_loss = entry_price - stop_distance
                take_profit = entry_price + (stop_distance * tp_multiplier)
            else:
                stop_loss = entry_price + stop_distance
                take_profit = entry_price - (stop_distance * tp_multiplier)
            
            # Store base confidence for CITADEL
            base_confidence = pattern_signal.final_score
            
            # Create signal
            signal = {
                'signal_id': f'ELITE_GUARD_{pattern_signal.pair}_{int(time.time())}',
                'pair': pattern_signal.pair,
                'symbol': pattern_signal.pair,  # Both formats for compatibility
                'direction': pattern_signal.direction,
                'signal_type': signal_type.value,
                'pattern': pattern_signal.pattern,
                'confidence': round(pattern_signal.final_score, 1),
                'base_confidence': base_confidence,  # For CITADEL reference
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
                'source': 'ELITE_GUARD_v6',
                'tf_alignment': pattern_signal.tf_alignment
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
            
            # Filter by minimum quality (50+ score for expanded testing - 5 hour window)
            # TEMPORARY: Lowered from 65 to 50 for truth system benchmarking (Aug 1, 2025)
            quality_patterns = [p for p in patterns if p.final_score >= 50]
            
            # Sort by score (highest first)
            return sorted(quality_patterns, key=lambda x: x.final_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error scanning patterns for {symbol}: {e}")
            return []
    
    def log_signal_to_truth_tracker(self, signal: Dict):
        """Log signal to truth tracker for performance monitoring"""
        if not self.enable_truth_tracking:
            return
            
        try:
            truth_entry = {
                'signal_id': signal['signal_id'],
                'source': 'ELITE_GUARD_v6',
                'pair': signal['pair'],
                'direction': signal['direction'],
                'pattern': signal['pattern'],
                'confidence': signal['confidence'],
                'entry_price': signal['entry_price'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'risk_reward': signal['risk_reward'],
                'signal_type': signal['signal_type'],
                'citadel_shielded': signal.get('citadel_shielded', False),
                'shield_score': signal.get('consensus_confidence', 0),
                'xp_reward': signal['xp_reward'],
                'timestamp': signal['timestamp'],
                'session': signal['session'],
                'timeframe': signal['timeframe'],
                'tf_alignment': signal.get('tf_alignment', 0),
                'status': 'ACTIVE',
                'outcome': 'PENDING'
            }
            
            # Send to truth tracker (async, don't block signal publishing)
            response = requests.post(
                self.truth_tracker_url,
                json=truth_entry,
                timeout=2
            )
            
            if response.status_code == 200:
                logger.debug(f"✅ Truth tracker logged: {signal['signal_id']}")
            else:
                logger.warning(f"⚠️ Truth tracker response: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Truth tracker error (non-critical): {e}")

    def publish_signal(self, signal: Dict):
        """Publish signal via ZMQ to BITTEN core"""
        try:
            if self.publisher:
                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
                
                # Log to truth tracker for performance monitoring
                self.log_signal_to_truth_tracker(signal)
                
                shield_status = "🛡️ SHIELDED" if signal.get('citadel_shielded') else "⚪ UNSHIELDED"
                logger.info(f"📡 Published: {signal['pair']} {signal['direction']} "
                           f"@ {signal['confidence']}% {shield_status}")
        except Exception as e:
            logger.error(f"Error publishing signal: {e}")
    
    def main_loop(self):
        """Main Elite Guard + CITADEL processing loop"""
        logger.info("🚀 Starting Elite Guard + CITADEL main processing loop")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Reset daily counter at midnight
                if datetime.now().hour == 0 and datetime.now().minute == 0:
                    self.daily_signal_count = 0
                    logger.info("🔄 Daily signal counter reset")
                
                # Adaptive session limits
                session = self.get_current_session()
                session_intel = self.session_intelligence.get(session, {})
                max_signals_per_hour = session_intel.get('signals_per_hour', 2)
                
                # Daily limit check (20-30 signals max)
                if self.daily_signal_count >= 30:
                    logger.debug("Daily signal limit reached, waiting...")
                    time.sleep(300)  # Wait 5 minutes
                    continue
                
                # Scan all pairs for patterns
                for symbol in self.trading_pairs:
                    try:
                        # Skip if insufficient data
                        if len(self.tick_data[symbol]) < 10:
                            continue
                        
                        # Cooldown check (5 minutes per pair)
                        if symbol in self.last_signal_time:
                            if current_time - self.last_signal_time[symbol] < self.signal_cooldown:
                                continue
                        
                        # Scan for patterns
                        patterns = self.scan_for_patterns(symbol)
                        
                        if patterns:
                            # Take highest scoring pattern
                            best_pattern = patterns[0]
                            
                            # Generate candidate signals for different tiers
                            rapid_signal = self.generate_elite_signal(best_pattern, 'average')
                            precision_signal = self.generate_elite_signal(best_pattern, 'sniper')
                            
                            if rapid_signal and precision_signal:
                                # Apply CITADEL Shield validation to both signals
                                shielded_rapid = self.citadel_shield.validate_and_enhance(rapid_signal.copy())
                                shielded_precision = self.citadel_shield.validate_and_enhance(precision_signal.copy())
                                
                                signals_to_publish = []
                                if shielded_rapid:
                                    signals_to_publish.append(shielded_rapid)
                                    self.signals_shielded += 1
                                else:
                                    self.signals_blocked += 1
                                
                                if shielded_precision:
                                    signals_to_publish.append(shielded_precision)
                                    self.signals_shielded += 1
                                else:
                                    self.signals_blocked += 1
                                
                                # Publish validated signals
                                for signal in signals_to_publish:
                                    self.publish_signal(signal)
                                    self.signals_generated += 1
                                
                                if signals_to_publish:
                                    # Update tracking
                                    self.last_signal_time[symbol] = current_time
                                    self.daily_signal_count += 1
                                    
                                    shield_info = "🛡️ CITADEL PROTECTED" if any(s.get('citadel_shielded') for s in signals_to_publish) else ""
                                    logger.info(f"🎯 ELITE GUARD: {symbol} {best_pattern.direction} "
                                              f"@ {best_pattern.final_score:.1f}% | {best_pattern.pattern} {shield_info}")
                    
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue
                
                # Adaptive sleep based on session activity
                sleep_time = 30 if session == 'OVERLAP' else 60
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)
    
    def data_listener_loop(self):
        """Separate thread for listening to ZMQ data stream"""
        logger.info("📡 Starting ZMQ data listener on port 5560")
        
        message_count = 0
        
        while self.running:
            try:
                if self.subscriber:
                    # Receive JSON data directly
                    data = self.subscriber.recv_json(zmq.NOBLOCK)
                    message_count += 1
                    
                    # Log first few messages and every 100th
                    if message_count <= 5 or message_count % 100 == 0:
                        logger.info(f"📊 Received message {message_count}: {data.get('type', 'unknown')}")
                    
                    # Process based on message type
                    msg_type = data.get('type', 'unknown')
                    
                    if msg_type == 'tick' or 'symbol' in data and 'bid' in data:
                        # Market tick data
                        symbol = data.get('symbol')
                        bid = data.get('bid')
                        ask = data.get('ask')
                        
                        if symbol and bid and ask:
                            logger.info(f"📈 Received tick: symbol={symbol} bid={bid} ask={ask}")
                            self.process_market_data(data)
                    
                    elif msg_type == 'heartbeat':
                        # Account status update
                        if message_count <= 3:
                            logger.info(f"💓 Heartbeat: balance=${data.get('balance', 0):.2f}, "
                                      f"equity=${data.get('equity', 0):.2f}")
                    
                    elif msg_type == 'status':
                        # EA status message
                        logger.info(f"📡 EA Status: {data.get('message', 'Connected')}")
                        
            except zmq.Again:
                # No message received, continue
                time.sleep(0.1)
            except Exception as e:
                if "Resource temporarily unavailable" not in str(e):
                    logger.debug(f"Data listener: {e}")
                time.sleep(0.1)
    
    def print_statistics(self):
        """Print engine performance statistics"""
        try:
            citadel_stats = self.citadel_shield.get_shield_statistics()
            
            logger.info("\n" + "="*60)
            logger.info("📊 ELITE GUARD + CITADEL SHIELD STATISTICS")
            logger.info("="*60)
            logger.info(f"🎯 Signals Generated: {self.signals_generated}")
            logger.info(f"🛡️ Signals Shielded: {self.signals_shielded}")
            logger.info(f"🚫 Signals Blocked: {self.signals_blocked}")
            logger.info(f"📈 Daily Count: {self.daily_signal_count}/30")
            logger.info("")
            logger.info("🛡️ CITADEL SHIELD PERFORMANCE:")
            logger.info(f"   Processed: {citadel_stats['signals_processed']}")
            logger.info(f"   Approved: {citadel_stats['signals_approved']} ({citadel_stats['approval_rate']:.1f}%)")
            logger.info(f"   Blocked: {citadel_stats['signals_blocked']}")
            logger.info(f"   Manipulation: {citadel_stats['manipulation_detected']} ({citadel_stats['manipulation_rate']:.1f}%)")
            logger.info("")
            logger.info("📡 DATA FEED STATUS:")
            for symbol in self.trading_pairs[:5]:  # Show first 5 pairs
                tick_count = len(self.tick_data[symbol])
                last_update = "Never" if not self.tick_data[symbol] else f"{time.time() - self.tick_data[symbol][-1].timestamp:.0f}s ago"
                logger.info(f"   {symbol}: {tick_count} ticks | Last: {last_update}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error printing statistics: {e}")
    
    def start(self):
        """Start the Elite Guard + CITADEL engine"""
        try:
            # Setup ZMQ connections
            self.setup_zmq_connections()
            
            # Disable CITADEL demo mode - use real data only
            # self.enable_citadel_demo_mode()
            logger.info("🎯 CITADEL Shield using REAL broker data")
            
            # Start data listener thread
            data_thread = threading.Thread(target=self.data_listener_loop, daemon=True)
            data_thread.start()
            
            # Start statistics thread
            stats_thread = threading.Thread(target=self.stats_loop, daemon=True)
            stats_thread.start()
            
            # Give threads time to start
            time.sleep(3)
            
            logger.info("✅ Elite Guard v6.0 + CITADEL Shield started successfully")
            logger.info("🎯 Target: 60-70% win rate | 20-30 signals/day | 1-2 per hour")
            logger.info("🛡️ CITADEL Shield providing multi-broker validation")
            logger.info("📡 Listening for ZMQ market data...")
            
            # Start main processing loop
            self.main_loop()
            
        except KeyboardInterrupt:
            logger.info("👋 Elite Guard + CITADEL shutting down...")
            self.running = False
            self.print_statistics()
        except Exception as e:
            logger.error(f"❌ Elite Guard engine error: {e}")
            raise
        finally:
            if self.context:
                self.context.term()
    
    def stats_loop(self):
        """Background thread to print periodic statistics"""
        while self.running:
            time.sleep(300)  # Every 5 minutes
            if self.signals_generated > 0:
                self.print_statistics()

if __name__ == "__main__":
    engine = EliteGuardWithCitadel()
    engine.start()