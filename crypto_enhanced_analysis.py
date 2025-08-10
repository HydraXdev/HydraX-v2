#!/usr/bin/env python3
"""
CRYPTO ENHANCED ANALYSIS SYSTEM - Multi-Source Data Enhancement
No External APIs Required - Leverages Existing ZMQ Market Data

🚀 IMMEDIATELY IMPLEMENTABLE ENHANCEMENTS:
- Multi-Timeframe Confluence System (M1, M5, M15)
- Advanced Volume Analysis (Volume Profile, Surge Detection)
- Cross-Crypto Correlation Analysis
- Session-Based Pattern Recognition
- Advanced Price Action Patterns
- Institutional vs Retail Volume Detection

🏷️ TAGGED FOR FUTURE (API-Dependent):
- Twitter Sentiment Analysis (requires X API)
- Whale Alert Integration (requires API key)
- CoinGecko News Sentiment (requires API)
- Multi-Broker Validation (requires multiple feeds)

Integration Points: Elite Guard, Fire Router, WebApp
Data Source: Existing ZMQ telemetry stream (port 5560)
"""

import zmq
import json
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import statistics
from scipy import stats
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CryptoEnhancedAnalysis')

class TimeFrame(Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"

class TradingSession(Enum):
    ASIAN = "asian"
    EUROPEAN = "european"
    US = "us"
    OVERLAP_EU_US = "overlap_eu_us"
    OVERLAP_ASIAN_EU = "overlap_asian_eu"
    WEEKEND = "weekend"

class MarketStructure(Enum):
    STRONG_UPTREND = "strong_uptrend"
    WEAK_UPTREND = "weak_uptrend"
    SIDEWAYS = "sideways"
    WEAK_DOWNTREND = "weak_downtrend"
    STRONG_DOWNTREND = "strong_downtrend"

class VolumeProfile(Enum):
    INSTITUTIONAL_ACCUMULATION = "institutional_accumulation"
    RETAIL_FOMO = "retail_fomo"
    WHALE_DISTRIBUTION = "whale_distribution"
    NORMAL_FLOW = "normal_flow"
    LOW_LIQUIDITY = "low_liquidity"

@dataclass
class OHLCV:
    """OHLCV candle data"""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    tick_count: int = 0

@dataclass
class MultiTimeframeSignal:
    """Enhanced signal with multi-timeframe confluence"""
    symbol: str
    primary_timeframe: str
    signal_type: str
    direction: str
    entry_price: float
    confidence: float
    
    # Multi-timeframe scores
    m1_score: float = 0.0
    m5_score: float = 0.0
    m15_score: float = 0.0
    tf_alignment_score: float = 0.0
    
    # Volume analysis
    volume_score: float = 0.0
    volume_profile: str = "unknown"
    volume_surge_factor: float = 1.0
    
    # Correlation analysis
    correlation_score: float = 0.0
    independent_move: bool = False
    
    # Session analysis
    session: str = "unknown"
    session_score: float = 0.0
    
    # Price action patterns
    pattern_score: float = 0.0
    support_resistance_score: float = 0.0
    trend_strength: float = 0.0
    
    # Final enhanced score
    enhanced_score: float = 0.0

@dataclass
class CorrelationMatrix:
    """Cross-symbol correlation data"""
    timestamp: float
    correlations: Dict[Tuple[str, str], float]
    lookback_periods: int
    significance_level: float

class CryptoEnhancedAnalyzer:
    """
    Advanced Multi-Source Crypto Analysis System
    No external APIs required - uses existing ZMQ data stream
    """
    
    def __init__(self, zmq_port=5560):
        # ZMQ Configuration
        self.context = zmq.Context()
        self.subscriber = None
        self.zmq_port = zmq_port
        
        # Active crypto symbols (from current system)
        self.crypto_symbols = [
            "BTCUSD", "ETHUSD", "XRPUSD", "ADAUSD", 
            "LTCUSD", "BCHUSD", "EOSUSD", "XLMUSD"
        ]
        
        # Forex symbols for correlation analysis
        self.forex_symbols = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
            "AUDUSD", "NZDUSD", "USDCAD"
        ]
        
        # All symbols
        self.all_symbols = self.crypto_symbols + self.forex_symbols
        
        # Multi-timeframe data storage
        self.tick_data = defaultdict(lambda: deque(maxlen=1000))
        self.m1_data = defaultdict(lambda: deque(maxlen=500))
        self.m5_data = defaultdict(lambda: deque(maxlen=300))
        self.m15_data = defaultdict(lambda: deque(maxlen=200))
        
        # Volume analysis storage
        self.volume_history = defaultdict(lambda: deque(maxlen=100))
        self.volume_profiles = {}
        
        # Correlation data
        self.correlation_matrix = None
        self.correlation_history = deque(maxlen=50)
        
        # Pattern recognition storage
        self.support_resistance_levels = defaultdict(list)
        self.trend_data = defaultdict(dict)
        
        # Analysis parameters
        self.min_correlation_periods = 20
        self.volume_surge_threshold = 2.0
        self.tf_alignment_threshold = 0.7
        
        # Threading
        self.running = False
        self.analysis_thread = None
        
    def start_analysis(self):
        """Start the enhanced analysis system"""
        logger.info("🚀 Starting Crypto Enhanced Analysis System")
        
        # Setup ZMQ subscriber
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://localhost:{self.zmq_port}")
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
        self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        
        logger.info("✅ Enhanced analysis system started")
        
    def stop_analysis(self):
        """Stop the analysis system"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join()
        if self.subscriber:
            self.subscriber.close()
        logger.info("🛑 Enhanced analysis system stopped")
        
    def _analysis_loop(self):
        """Main analysis loop"""
        logger.info("📊 Starting analysis loop")
        
        while self.running:
            try:
                # Receive market data
                try:
                    message = self.subscriber.recv_string(zmq.NOBLOCK)
                    self._process_market_data(message)
                except zmq.Again:
                    continue
                    
                # Perform periodic analysis
                self._perform_periodic_analysis()
                
                time.sleep(0.1)  # Prevent CPU overload
                
            except Exception as e:
                logger.error(f"❌ Analysis loop error: {e}")
                time.sleep(1)
                
    def _process_market_data(self, message: str):
        """Process incoming market data"""
        try:
            data = json.loads(message)
            
            # Extract symbol and validate
            symbol = data.get('symbol', '').upper()
            if symbol not in self.all_symbols:
                return
                
            # Process tick data
            if data.get('type') == 'tick':
                self._process_tick_data(symbol, data)
            elif data.get('type') == 'candle':
                self._process_candle_data(symbol, data)
                
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Invalid JSON in market data: {message[:100]}")
        except Exception as e:
            logger.error(f"❌ Error processing market data: {e}")
            
    def _process_tick_data(self, symbol: str, data: Dict):
        """Process individual tick data"""
        try:
            tick = {
                'timestamp': data.get('timestamp', time.time()),
                'bid': float(data.get('bid', 0)),
                'ask': float(data.get('ask', 0)),
                'volume': float(data.get('volume', 0)),
                'spread': float(data.get('spread', 0))
            }
            
            self.tick_data[symbol].append(tick)
            
            # Convert to OHLCV data
            self._update_ohlcv_from_ticks(symbol)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Invalid tick data for {symbol}: {e}")
            
    def _process_candle_data(self, symbol: str, data: Dict):
        """Process OHLCV candle data"""
        try:
            candle = OHLCV(
                timestamp=float(data.get('timestamp', time.time())),
                open=float(data.get('open', 0)),
                high=float(data.get('high', 0)),
                low=float(data.get('low', 0)),
                close=float(data.get('close', 0)),
                volume=float(data.get('volume', 0)),
                tick_count=int(data.get('tick_count', 0))
            )
            
            timeframe = data.get('timeframe', 'M1')
            
            if timeframe == 'M1':
                self.m1_data[symbol].append(candle)
            elif timeframe == 'M5':
                self.m5_data[symbol].append(candle)
            elif timeframe == 'M15':
                self.m15_data[symbol].append(candle)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Invalid candle data for {symbol}: {e}")
            
    def _update_ohlcv_from_ticks(self, symbol: str):
        """Convert tick data to OHLCV candles"""
        ticks = list(self.tick_data[symbol])
        if len(ticks) < 10:
            return
            
        # Group ticks by minute for M1 data
        current_minute = int(time.time() // 60)
        minute_ticks = [t for t in ticks if int(t['timestamp'] // 60) == current_minute]
        
        if len(minute_ticks) >= 5:  # Minimum ticks for valid candle
            prices = [(t['bid'] + t['ask']) / 2 for t in minute_ticks]
            volumes = [t['volume'] for t in minute_ticks]
            
            candle = OHLCV(
                timestamp=float(current_minute * 60),
                open=prices[0],
                high=max(prices),
                low=min(prices),
                close=prices[-1],
                volume=sum(volumes),
                tick_count=len(minute_ticks)
            )
            
            # Update M1 data if this is a new candle
            if not self.m1_data[symbol] or self.m1_data[symbol][-1].timestamp < candle.timestamp:
                self.m1_data[symbol].append(candle)
                
    def _perform_periodic_analysis(self):
        """Perform periodic enhanced analysis"""
        current_time = time.time()
        
        # Run analysis every 30 seconds
        if not hasattr(self, '_last_analysis') or current_time - self._last_analysis > 30:
            self._last_analysis = current_time
            
            # Update correlation matrix
            self._update_correlation_matrix()
            
            # Analyze volume profiles
            self._analyze_volume_profiles()
            
            # Update support/resistance levels
            self._update_support_resistance()
            
            # Generate enhanced signals
            self._generate_enhanced_signals()
            
    def _update_correlation_matrix(self):
        """Update cross-symbol correlation matrix"""
        try:
            correlations = {}
            
            # Get enough data for correlation calculation
            symbols_with_data = []
            price_series = {}
            
            for symbol in self.all_symbols:
                if len(self.m5_data[symbol]) >= self.min_correlation_periods:
                    symbols_with_data.append(symbol)
                    # Use close prices for correlation
                    price_series[symbol] = [candle.close for candle in list(self.m5_data[symbol])[-self.min_correlation_periods:]]
                    
            # Calculate pairwise correlations
            for i, symbol1 in enumerate(symbols_with_data):
                for j, symbol2 in enumerate(symbols_with_data[i+1:], i+1):
                    try:
                        corr, p_value = pearsonr(price_series[symbol1], price_series[symbol2])
                        if not np.isnan(corr):
                            correlations[(symbol1, symbol2)] = {
                                'correlation': float(corr),
                                'p_value': float(p_value),
                                'significant': p_value < 0.05
                            }
                    except Exception as e:
                        logger.warning(f"⚠️ Correlation calculation failed for {symbol1}-{symbol2}: {e}")
                        
            if correlations:
                self.correlation_matrix = CorrelationMatrix(
                    timestamp=time.time(),
                    correlations=correlations,
                    lookback_periods=self.min_correlation_periods,
                    significance_level=0.05
                )
                
                self.correlation_history.append(self.correlation_matrix)
                logger.debug(f"📈 Updated correlation matrix with {len(correlations)} pairs")
                
        except Exception as e:
            logger.error(f"❌ Correlation matrix update failed: {e}")
            
    def _analyze_volume_profiles(self):
        """Analyze volume profiles for institutional vs retail patterns"""
        try:
            for symbol in self.crypto_symbols:
                if len(self.m1_data[symbol]) < 50:
                    continue
                    
                recent_candles = list(self.m1_data[symbol])[-50:]
                volumes = [candle.volume for candle in recent_candles]
                prices = [candle.close for candle in recent_candles]
                
                if not volumes or sum(volumes) == 0:
                    continue
                    
                # Calculate volume statistics
                avg_volume = statistics.mean(volumes)
                volume_std = statistics.stdev(volumes) if len(volumes) > 1 else 0
                
                # Detect volume patterns
                profile = self._classify_volume_profile(volumes, prices, avg_volume, volume_std)
                self.volume_profiles[symbol] = {
                    'profile': profile,
                    'avg_volume': avg_volume,
                    'volume_std': volume_std,
                    'surge_factor': max(volumes) / avg_volume if avg_volume > 0 else 1,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            logger.error(f"❌ Volume profile analysis failed: {e}")
            
    def _classify_volume_profile(self, volumes: List[float], prices: List[float], avg_volume: float, volume_std: float) -> VolumeProfile:
        """Classify volume profile based on patterns"""
        try:
            if len(volumes) < 10:
                return VolumeProfile.NORMAL_FLOW
                
            # Calculate volume surge events
            surge_threshold = avg_volume + (2 * volume_std)
            surge_events = [v for v in volumes if v > surge_threshold]
            
            # Calculate price volatility during high volume
            high_volume_periods = [i for i, v in enumerate(volumes) if v > surge_threshold]
            
            if len(surge_events) >= 3:
                # Multiple volume surges
                if len(high_volume_periods) >= 2:
                    price_moves = [abs(prices[i+1] - prices[i]) for i in high_volume_periods[:-1]]
                    avg_price_move = statistics.mean(price_moves) if price_moves else 0
                    
                    # Large volume with small price moves = accumulation
                    if avg_price_move < statistics.stdev(prices) * 0.5:
                        return VolumeProfile.INSTITUTIONAL_ACCUMULATION
                    # Large volume with large price moves = FOMO
                    else:
                        return VolumeProfile.RETAIL_FOMO
                        
            elif max(volumes) > avg_volume * 5:
                # Single massive volume spike
                max_volume_idx = volumes.index(max(volumes))
                if max_volume_idx < len(prices) - 5:
                    # Check price action after volume spike
                    post_spike_trend = prices[-1] - prices[max_volume_idx]
                    if abs(post_spike_trend) > statistics.stdev(prices):
                        return VolumeProfile.WHALE_DISTRIBUTION
                        
            elif avg_volume < statistics.mean(volumes[-20:]) * 0.5:
                return VolumeProfile.LOW_LIQUIDITY
                
            return VolumeProfile.NORMAL_FLOW
            
        except Exception as e:
            logger.warning(f"⚠️ Volume profile classification failed: {e}")
            return VolumeProfile.NORMAL_FLOW
            
    def _update_support_resistance(self):
        """Update support and resistance levels"""
        try:
            for symbol in self.all_symbols:
                if len(self.m15_data[symbol]) < 20:
                    continue
                    
                candles = list(self.m15_data[symbol])[-50:]  # Last 50 M15 candles
                highs = [c.high for c in candles]
                lows = [c.low for c in candles]
                
                # Find resistance levels (local maxima)
                resistance_levels = self._find_levels(highs, 'resistance')
                
                # Find support levels (local minima)
                support_levels = self._find_levels(lows, 'support')
                
                self.support_resistance_levels[symbol] = {
                    'support': support_levels,
                    'resistance': resistance_levels,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            logger.error(f"❌ Support/resistance update failed: {e}")
            
    def _find_levels(self, prices: List[float], level_type: str) -> List[Dict]:
        """Find support or resistance levels"""
        levels = []
        
        try:
            if len(prices) < 10:
                return levels
                
            # Use rolling window to find local extrema
            window_size = 5
            
            for i in range(window_size, len(prices) - window_size):
                window = prices[i-window_size:i+window_size+1]
                current_price = prices[i]
                
                if level_type == 'resistance':
                    # Local maximum
                    if current_price == max(window):
                        # Count how many times price approached this level
                        touches = sum(1 for p in prices if abs(p - current_price) < current_price * 0.002)
                        if touches >= 2:
                            levels.append({
                                'price': current_price,
                                'touches': touches,
                                'strength': min(touches / 5.0, 1.0),
                                'index': i
                            })
                            
                elif level_type == 'support':
                    # Local minimum  
                    if current_price == min(window):
                        touches = sum(1 for p in prices if abs(p - current_price) < current_price * 0.002)
                        if touches >= 2:
                            levels.append({
                                'price': current_price,
                                'touches': touches,
                                'strength': min(touches / 5.0, 1.0),
                                'index': i
                            })
                            
            # Sort by strength and return top levels
            levels.sort(key=lambda x: x['strength'], reverse=True)
            return levels[:5]  # Top 5 levels
            
        except Exception as e:
            logger.warning(f"⚠️ Level finding failed for {level_type}: {e}")
            return levels
            
    def _generate_enhanced_signals(self):
        """Generate enhanced multi-source signals"""
        try:
            for symbol in self.crypto_symbols:
                signal = self._analyze_symbol_for_signal(symbol)
                if signal and signal.enhanced_score > 70:  # High-confidence signals only
                    self._publish_enhanced_signal(signal)
                    
        except Exception as e:
            logger.error(f"❌ Enhanced signal generation failed: {e}")
            
    def _analyze_symbol_for_signal(self, symbol: str) -> Optional[MultiTimeframeSignal]:
        """Comprehensive symbol analysis for signal generation"""
        try:
            # Check data availability
            if (len(self.m1_data[symbol]) < 20 or 
                len(self.m5_data[symbol]) < 10 or 
                len(self.m15_data[symbol]) < 5):
                return None
                
            # Get current price
            current_candle = self.m1_data[symbol][-1]
            current_price = current_candle.close
            
            # Initialize signal
            signal = MultiTimeframeSignal(
                symbol=symbol,
                primary_timeframe="M5",
                signal_type="ENHANCED_CONFLUENCE",
                direction="UNKNOWN",
                entry_price=current_price,
                confidence=0.0
            )
            
            # 1. Multi-timeframe confluence analysis
            signal.m1_score = self._analyze_timeframe_momentum(symbol, TimeFrame.M1)
            signal.m5_score = self._analyze_timeframe_momentum(symbol, TimeFrame.M5)
            signal.m15_score = self._analyze_timeframe_momentum(symbol, TimeFrame.M15)
            
            # Calculate timeframe alignment
            scores = [signal.m1_score, signal.m5_score, signal.m15_score]
            signal.tf_alignment_score = self._calculate_alignment_score(scores)
            
            # 2. Volume analysis
            signal.volume_score = self._analyze_volume_for_signal(symbol)
            volume_profile = self.volume_profiles.get(symbol, {})
            signal.volume_profile = volume_profile.get('profile', VolumeProfile.NORMAL_FLOW).value
            signal.volume_surge_factor = volume_profile.get('surge_factor', 1.0)
            
            # 3. Correlation analysis
            signal.correlation_score = self._analyze_correlation_for_signal(symbol)
            signal.independent_move = self._is_independent_move(symbol)
            
            # 4. Session analysis
            signal.session = self._get_current_session().value
            signal.session_score = self._get_session_score(signal.session)
            
            # 5. Price action patterns
            signal.pattern_score = self._analyze_price_patterns(symbol)
            signal.support_resistance_score = self._analyze_sr_levels(symbol, current_price)
            signal.trend_strength = self._calculate_trend_strength(symbol)
            
            # 6. Determine direction
            bullish_signals = sum([
                signal.m1_score > 0.5, signal.m5_score > 0.5, signal.m15_score > 0.5,
                signal.volume_score > 0.6, signal.pattern_score > 0.6,
                signal.support_resistance_score > 0.6
            ])
            
            bearish_signals = sum([
                signal.m1_score < -0.5, signal.m5_score < -0.5, signal.m15_score < -0.5,
                signal.volume_score < -0.6, signal.pattern_score < -0.6,
                signal.support_resistance_score < -0.6
            ])
            
            if bullish_signals >= 4:
                signal.direction = "BUY"
            elif bearish_signals >= 4:
                signal.direction = "SELL"
            else:
                return None  # No clear direction
                
            # 7. Calculate final enhanced score
            signal.enhanced_score = self._calculate_enhanced_score(signal)
            signal.confidence = signal.enhanced_score / 100.0
            
            if signal.enhanced_score > 70:
                return signal
                
            return None
            
        except Exception as e:
            logger.error(f"❌ Symbol analysis failed for {symbol}: {e}")
            return None
            
    def _analyze_timeframe_momentum(self, symbol: str, timeframe: TimeFrame) -> float:
        """Analyze momentum for specific timeframe"""
        try:
            if timeframe == TimeFrame.M1:
                data = self.m1_data[symbol]
            elif timeframe == TimeFrame.M5:
                data = self.m5_data[symbol]
            elif timeframe == TimeFrame.M15:
                data = self.m15_data[symbol]
            else:
                return 0.0
                
            if len(data) < 10:
                return 0.0
                
            candles = list(data)[-10:]
            closes = [c.close for c in candles]
            
            # Simple momentum: (current - average) / average
            current = closes[-1]
            average = statistics.mean(closes[:-1])
            
            momentum = (current - average) / average if average > 0 else 0
            
            # Normalize to -1 to 1 range
            return max(min(momentum * 100, 1.0), -1.0)
            
        except Exception as e:
            logger.warning(f"⚠️ Timeframe momentum analysis failed: {e}")
            return 0.0
            
    def _calculate_alignment_score(self, scores: List[float]) -> float:
        """Calculate multi-timeframe alignment score"""
        try:
            if not scores:
                return 0.0
                
            # Check if all scores point in same direction
            positive_scores = [s for s in scores if s > 0.2]
            negative_scores = [s for s in scores if s < -0.2]
            
            if len(positive_scores) == len(scores):
                # All bullish
                return statistics.mean(positive_scores)
            elif len(negative_scores) == len(scores):
                # All bearish
                return statistics.mean(negative_scores)
            elif len(positive_scores) >= len(scores) * 0.7:
                # Mostly bullish
                return statistics.mean(positive_scores) * 0.8
            elif len(negative_scores) >= len(scores) * 0.7:
                # Mostly bearish
                return statistics.mean(negative_scores) * 0.8
            else:
                # Mixed signals
                return 0.0
                
        except Exception as e:
            logger.warning(f"⚠️ Alignment score calculation failed: {e}")
            return 0.0
            
    def _analyze_volume_for_signal(self, symbol: str) -> float:
        """Analyze volume for signal confirmation"""
        try:
            profile = self.volume_profiles.get(symbol, {})
            surge_factor = profile.get('surge_factor', 1.0)
            volume_type = profile.get('profile', VolumeProfile.NORMAL_FLOW)
            
            # Score based on volume profile and surge
            if volume_type == VolumeProfile.INSTITUTIONAL_ACCUMULATION:
                base_score = 0.8
            elif volume_type == VolumeProfile.WHALE_DISTRIBUTION:
                base_score = -0.8
            elif volume_type == VolumeProfile.RETAIL_FOMO:
                base_score = 0.3  # Lower confidence
            elif volume_type == VolumeProfile.LOW_LIQUIDITY:
                base_score = -0.3
            else:
                base_score = 0.0
                
            # Adjust for surge factor
            surge_multiplier = min(surge_factor / 2.0, 1.5)
            
            return base_score * surge_multiplier
            
        except Exception as e:
            logger.warning(f"⚠️ Volume analysis failed: {e}")
            return 0.0
            
    def _analyze_correlation_for_signal(self, symbol: str) -> float:
        """Analyze correlation for signal quality"""
        try:
            if not self.correlation_matrix:
                return 0.0
                
            # Find correlations with BTC and major symbols
            btc_correlation = None
            major_correlations = []
            
            for (s1, s2), corr_data in self.correlation_matrix.correlations.items():
                if (s1 == symbol and s2 == "BTCUSD") or (s2 == symbol and s1 == "BTCUSD"):
                    btc_correlation = corr_data['correlation']
                elif symbol in (s1, s2) and corr_data['significant']:
                    major_correlations.append(corr_data['correlation'])
                    
            # Score based on correlation strength and independence
            score = 0.0
            
            if btc_correlation is not None:
                # Lower correlation with BTC = more independent = higher score
                independence_score = 1.0 - abs(btc_correlation)
                score += independence_score * 0.5
                
            if major_correlations:
                avg_correlation = statistics.mean([abs(c) for c in major_correlations])
                # Lower average correlation = more independent
                independence_score = 1.0 - avg_correlation
                score += independence_score * 0.3
                
            return min(score, 1.0)
            
        except Exception as e:
            logger.warning(f"⚠️ Correlation analysis failed: {e}")
            return 0.0
            
    def _is_independent_move(self, symbol: str) -> bool:
        """Check if this is an independent move (low correlation with others)"""
        try:
            if not self.correlation_matrix:
                return False
                
            correlations = []
            for (s1, s2), corr_data in self.correlation_matrix.correlations.items():
                if symbol in (s1, s2) and corr_data['significant']:
                    correlations.append(abs(corr_data['correlation']))
                    
            if correlations:
                avg_correlation = statistics.mean(correlations)
                return avg_correlation < 0.3  # Low correlation threshold
                
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Independent move check failed: {e}")
            return False
            
    def _get_current_session(self) -> TradingSession:
        """Determine current trading session"""
        try:
            current_hour = datetime.utcnow().hour
            
            # Asian session: 22:00-08:00 UTC
            if 22 <= current_hour or current_hour < 8:
                return TradingSession.ASIAN
            # European session: 07:00-16:00 UTC
            elif 7 <= current_hour < 16:
                return TradingSession.EUROPEAN
            # US session: 13:00-22:00 UTC
            elif 13 <= current_hour < 22:
                return TradingSession.US
            # Overlap periods
            elif 13 <= current_hour < 16:
                return TradingSession.OVERLAP_EU_US
            elif 7 <= current_hour < 8:
                return TradingSession.OVERLAP_ASIAN_EU
            else:
                # Weekend or low activity
                return TradingSession.WEEKEND
                
        except Exception as e:
            logger.warning(f"⚠️ Session detection failed: {e}")
            return TradingSession.WEEKEND
            
    def _get_session_score(self, session: str) -> float:
        """Get score multiplier for current session"""
        session_scores = {
            TradingSession.US.value: 1.0,              # Highest activity
            TradingSession.EUROPEAN.value: 0.9,        # High activity
            TradingSession.OVERLAP_EU_US.value: 1.2,   # Maximum overlap
            TradingSession.ASIAN.value: 0.7,           # Moderate activity
            TradingSession.OVERLAP_ASIAN_EU.value: 0.8, # Moderate overlap
            TradingSession.WEEKEND.value: 0.3          # Low activity
        }
        
        return session_scores.get(session, 0.5)
        
    def _analyze_price_patterns(self, symbol: str) -> float:
        """Analyze price action patterns"""
        try:
            if len(self.m5_data[symbol]) < 20:
                return 0.0
                
            candles = list(self.m5_data[symbol])[-20:]
            
            # Look for bullish/bearish patterns
            pattern_score = 0.0
            
            # Higher highs and higher lows (bullish)
            highs = [c.high for c in candles[-10:]]
            lows = [c.low for c in candles[-10:]]
            
            if len(highs) >= 3 and len(lows) >= 3:
                if highs[-1] > highs[-2] > highs[-3] and lows[-1] > lows[-2]:
                    pattern_score += 0.5  # Bullish pattern
                elif highs[-1] < highs[-2] < highs[-3] and lows[-1] < lows[-2]:
                    pattern_score -= 0.5  # Bearish pattern
                    
            # Consolidation breakout
            recent_range = max([c.high for c in candles[-5:]]) - min([c.low for c in candles[-5:]])
            previous_range = max([c.high for c in candles[-15:-5]]) - min([c.low for c in candles[-15:-5]])
            
            if recent_range > previous_range * 1.5:
                # Breakout detected
                current_close = candles[-1].close
                previous_avg = statistics.mean([c.close for c in candles[-10:-5]])
                
                if current_close > previous_avg:
                    pattern_score += 0.3  # Bullish breakout
                else:
                    pattern_score -= 0.3  # Bearish breakout
                    
            return max(min(pattern_score, 1.0), -1.0)
            
        except Exception as e:
            logger.warning(f"⚠️ Pattern analysis failed: {e}")
            return 0.0
            
    def _analyze_sr_levels(self, symbol: str, current_price: float) -> float:
        """Analyze support/resistance levels"""
        try:
            sr_data = self.support_resistance_levels.get(symbol, {})
            if not sr_data:
                return 0.0
                
            support_levels = sr_data.get('support', [])
            resistance_levels = sr_data.get('resistance', [])
            
            score = 0.0
            
            # Check proximity to support (bullish) or resistance (bearish)
            for level in support_levels:
                distance = abs(current_price - level['price']) / current_price
                if distance < 0.01:  # Within 1%
                    score += level['strength'] * 0.5  # Bullish near support
                    
            for level in resistance_levels:
                distance = abs(current_price - level['price']) / current_price
                if distance < 0.01:  # Within 1%
                    score -= level['strength'] * 0.5  # Bearish near resistance
                    
            return max(min(score, 1.0), -1.0)
            
        except Exception as e:
            logger.warning(f"⚠️ Support/resistance analysis failed: {e}")
            return 0.0
            
    def _calculate_trend_strength(self, symbol: str) -> float:
        """Calculate trend strength"""
        try:
            if len(self.m15_data[symbol]) < 10:
                return 0.0
                
            candles = list(self.m15_data[symbol])[-10:]
            closes = [c.close for c in candles]
            
            # Linear regression for trend
            x = list(range(len(closes)))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, closes)
            
            # Normalize slope relative to price
            normalized_slope = slope / statistics.mean(closes) if statistics.mean(closes) > 0 else 0
            
            # R-squared indicates trend strength
            trend_strength = abs(r_value) * abs(normalized_slope) * 100
            
            # Direction
            if slope > 0:
                return min(trend_strength, 1.0)
            else:
                return max(-trend_strength, -1.0)
                
        except Exception as e:
            logger.warning(f"⚠️ Trend strength calculation failed: {e}")
            return 0.0
            
    def _calculate_enhanced_score(self, signal: MultiTimeframeSignal) -> float:
        """Calculate final enhanced score"""
        try:
            # Weight different components
            weights = {
                'timeframe_alignment': 0.25,
                'volume': 0.20,
                'correlation': 0.15,
                'session': 0.10,
                'patterns': 0.15,
                'support_resistance': 0.10,
                'trend_strength': 0.05
            }
            
            # Calculate weighted score
            score = 0.0
            
            # Timeframe alignment (0-25 points)
            tf_score = abs(signal.tf_alignment_score) * 25 * weights['timeframe_alignment']
            score += tf_score
            
            # Volume analysis (0-20 points)
            volume_score = abs(signal.volume_score) * 25 * weights['volume']
            score += volume_score
            
            # Correlation independence (0-15 points)
            corr_score = signal.correlation_score * 25 * weights['correlation']
            if signal.independent_move:
                corr_score *= 1.5
            score += corr_score
            
            # Session timing (0-10 points)
            session_score = signal.session_score * 25 * weights['session']
            score += session_score
            
            # Price patterns (0-15 points)
            pattern_score = abs(signal.pattern_score) * 25 * weights['patterns']
            score += pattern_score
            
            # Support/resistance (0-10 points)
            sr_score = abs(signal.support_resistance_score) * 25 * weights['support_resistance']
            score += sr_score
            
            # Trend strength (0-5 points)
            trend_score = abs(signal.trend_strength) * 25 * weights['trend_strength']
            score += trend_score
            
            # Bonus for volume surge
            if signal.volume_surge_factor > 3.0:
                score *= 1.2
            elif signal.volume_surge_factor > 2.0:
                score *= 1.1
                
            # Institutional volume bonus
            if signal.volume_profile == VolumeProfile.INSTITUTIONAL_ACCUMULATION.value:
                score *= 1.15
                
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"❌ Enhanced score calculation failed: {e}")
            return 0.0
            
    def _publish_enhanced_signal(self, signal: MultiTimeframeSignal):
        """Publish enhanced signal to system"""
        try:
            # Convert to dict for JSON serialization
            signal_dict = asdict(signal)
            signal_dict['timestamp'] = time.time()
            signal_dict['analysis_type'] = 'ENHANCED_MULTI_SOURCE'
            
            # Log high-quality signal
            logger.info(f"🎯 ENHANCED SIGNAL: {signal.symbol} {signal.direction} - Score: {signal.enhanced_score:.1f}")
            logger.info(f"   📊 TF Alignment: {signal.tf_alignment_score:.2f}")
            logger.info(f"   📈 Volume: {signal.volume_score:.2f} ({signal.volume_profile})")
            logger.info(f"   🔗 Correlation: {signal.correlation_score:.2f} (Independent: {signal.independent_move})")
            logger.info(f"   ⏰ Session: {signal.session} (Score: {signal.session_score:.2f})")
            logger.info(f"   📉 Patterns: {signal.pattern_score:.2f}")
            logger.info(f"   🎚️ S/R: {signal.support_resistance_score:.2f}")
            logger.info(f"   📊 Trend: {signal.trend_strength:.2f}")
            
            # Here you would integrate with the existing signal publishing system
            # This could connect to Elite Guard's signal publisher or create its own
            self._integrate_with_elite_guard(signal_dict)
            
        except Exception as e:
            logger.error(f"❌ Enhanced signal publishing failed: {e}")
            
    def _integrate_with_elite_guard(self, signal_dict: Dict):
        """Integrate with Elite Guard signal publishing system"""
        try:
            # This is where you'd connect to the existing Elite Guard publisher
            # For now, just log the integration point
            logger.info(f"🔄 Integration point: Enhanced signal ready for Elite Guard")
            logger.debug(f"📦 Signal data: {json.dumps(signal_dict, indent=2)}")
            
            # TODO: Implement actual integration with:
            # - Elite Guard ZMQ publisher (port 5557)
            # - Truth tracking system
            # - WebApp signal display
            
        except Exception as e:
            logger.error(f"❌ Elite Guard integration failed: {e}")
            
    def get_analysis_status(self) -> Dict[str, Any]:
        """Get current analysis system status"""
        try:
            status = {
                'running': self.running,
                'symbols_tracked': len(self.all_symbols),
                'crypto_symbols': len(self.crypto_symbols),
                'data_points': {
                    'tick_data': {symbol: len(data) for symbol, data in self.tick_data.items()},
                    'm1_data': {symbol: len(data) for symbol, data in self.m1_data.items()},
                    'm5_data': {symbol: len(data) for symbol, data in self.m5_data.items()},
                    'm15_data': {symbol: len(data) for symbol, data in self.m15_data.items()}
                },
                'correlation_matrix': {
                    'available': self.correlation_matrix is not None,
                    'pairs': len(self.correlation_matrix.correlations) if self.correlation_matrix else 0,
                    'last_update': self.correlation_matrix.timestamp if self.correlation_matrix else None
                },
                'volume_profiles': {
                    'symbols_analyzed': len(self.volume_profiles),
                    'profiles': {symbol: data['profile'] for symbol, data in self.volume_profiles.items()}
                },
                'support_resistance': {
                    'symbols_analyzed': len(self.support_resistance_levels)
                },
                'timestamp': time.time()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Status retrieval failed: {e}")
            return {'error': str(e)}

# Main execution and testing
if __name__ == "__main__":
    analyzer = CryptoEnhancedAnalyzer()
    
    try:
        analyzer.start_analysis()
        logger.info("🚀 Crypto Enhanced Analysis System started")
        
        # Keep running
        while True:
            status = analyzer.get_analysis_status()
            logger.info(f"📊 System Status: {status['symbols_tracked']} symbols, "
                       f"{status['correlation_matrix']['pairs']} correlation pairs, "
                       f"{status['volume_profiles']['symbols_analyzed']} volume profiles")
            
            time.sleep(60)  # Status update every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Crypto Enhanced Analysis System")
        analyzer.stop_analysis()
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        analyzer.stop_analysis()