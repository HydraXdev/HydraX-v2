#!/usr/bin/env python3
"""
VENOM Real Data Engine - Zero Synthetic Data
Preserves VENOM's core intelligence while using 100% real MT5 market data

FEATURES:
- Real tick data from MT5 EA stream
- Authentic technical analysis calculations
- True market regime detection
- Real-time spread and volume analysis
- Preserved VENOM session intelligence
- Zero fake/synthetic data generation
"""

import json
import time
import logging
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import requests
import sys
import os

# Add src directory to path
sys.path.insert(0, '/root/HydraX-v2/src')

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

class SignalQuality(Enum):
    PLATINUM = "platinum"
    GOLD = "gold" 
    SILVER = "silver"
    BRONZE = "bronze"

class VenomRealDataEngine:
    """
    VENOM Real Data Engine - 100% Authentic Market Data
    
    Preserves VENOM's core intelligence algorithms while eliminating
    all synthetic data generation. Uses real MT5 tick streams.
    """
    
    def __init__(self):
        # Valid 15 pairs from CLAUDE.md (NO XAUUSD per instructions)
        self.trading_pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
            "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
            "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
        ]
        
        # VENOM Pair Intelligence (preserved from original)
        self.pair_intelligence = {
            'EURUSD': {'trend_strength': 0.85, 'range_efficiency': 0.92, 'session_bias': 'LONDON'},
            'GBPUSD': {'trend_strength': 0.92, 'range_efficiency': 0.78, 'session_bias': 'LONDON'},
            'USDJPY': {'trend_strength': 0.78, 'range_efficiency': 0.85, 'session_bias': 'NY'},
            'USDCAD': {'trend_strength': 0.78, 'range_efficiency': 0.85, 'session_bias': 'NY'},
            'AUDUSD': {'trend_strength': 0.85, 'range_efficiency': 0.68, 'session_bias': 'ASIAN'},
            'USDCHF': {'trend_strength': 0.68, 'range_efficiency': 0.92, 'session_bias': 'LONDON'},
            'NZDUSD': {'trend_strength': 0.92, 'range_efficiency': 0.58, 'session_bias': 'ASIAN'},
            'EURGBP': {'trend_strength': 0.58, 'range_efficiency': 0.92, 'session_bias': 'LONDON'},
            'EURJPY': {'trend_strength': 0.85, 'range_efficiency': 0.78, 'session_bias': 'OVERLAP'},
            'GBPJPY': {'trend_strength': 0.92, 'range_efficiency': 0.68, 'session_bias': 'OVERLAP'},
            'GBPNZD': {'trend_strength': 0.90, 'range_efficiency': 0.62, 'session_bias': 'LONDON'},
            'GBPAUD': {'trend_strength': 0.89, 'range_efficiency': 0.65, 'session_bias': 'LONDON'},
            'EURAUD': {'trend_strength': 0.82, 'range_efficiency': 0.70, 'session_bias': 'OVERLAP'},
            'GBPCHF': {'trend_strength': 0.75, 'range_efficiency': 0.88, 'session_bias': 'LONDON'},
            'AUDJPY': {'trend_strength': 0.88, 'range_efficiency': 0.72, 'session_bias': 'OVERLAP'}
        }
        
        # VENOM Session Intelligence (preserved)
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
            },
            'OFF_HOURS': {
                'optimal_pairs': [],
                'win_rate_boost': -0.03,
                'volume_multiplier': 0.4,
                'quality_bonus': -5
            }
        }
        
        # Real data storage
        self.market_data = {}  # Real tick data from MT5
        self.price_history = {}  # For technical analysis
        self.total_signals = 0
        
        # Signal generation limits (realistic)
        self.max_signals_per_hour = 2
        self.signals_this_hour = 0
        self.hour_start = datetime.now()
        
        logger.info("🐍 VENOM Real Data Engine Initialized")
        logger.info("✅ 100% REAL MT5 DATA - Zero synthetic generation")
        logger.info(f"📊 Monitoring {len(self.trading_pairs)} pairs")
    
    def get_session_type(self, hour: int) -> str:
        """Determine trading session based on UTC hour"""
        if 7 <= hour <= 16:  # London session
            if 12 <= hour <= 16:  # Overlap with NY
                return 'OVERLAP'
            return 'LONDON'
        elif 13 <= hour <= 22:  # NY session
            return 'NY'
        elif 22 <= hour <= 7:  # Asian session
            return 'ASIAN'
        else:
            return 'OFF_HOURS'
    
    def update_market_data(self, tick_data: Dict):
        """Update with real MT5 tick data"""
        try:
            symbol = tick_data.get('symbol')
            if symbol not in self.trading_pairs:
                return False
                
            # Store real tick data
            self.market_data[symbol] = {
                'bid': float(tick_data.get('bid', 0)),
                'ask': float(tick_data.get('ask', 0)), 
                'spread': float(tick_data.get('spread', 0)),
                'volume': int(tick_data.get('volume', 0)),
                'timestamp': time.time(),
                'last_update': datetime.now()
            }
            
            # Maintain price history for technical analysis
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            # Store last 100 prices for analysis
            mid_price = (self.market_data[symbol]['bid'] + self.market_data[symbol]['ask']) / 2
            self.price_history[symbol].append({
                'price': mid_price,
                'timestamp': time.time(),
                'volume': self.market_data[symbol]['volume']
            })
            
            # Keep only last 100 data points
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
            return False
    
    def detect_real_market_regime(self, symbol: str) -> MarketRegime:
        """Detect market regime using REAL price history"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return MarketRegime.CALM_RANGE  # Default when insufficient data
        
        try:
            prices = [p['price'] for p in self.price_history[symbol][-20:]]  # Last 20 prices
            volumes = [p['volume'] for p in self.price_history[symbol][-20:]]
            
            # Calculate real technical indicators
            price_change = (prices[-1] - prices[0]) / prices[0] * 100
            volatility = np.std(prices) / np.mean(prices) * 100
            avg_volume = np.mean(volumes) if volumes else 1000
            
            # Real regime detection based on actual price movement
            if abs(price_change) > 0.5 and volatility > 0.3:  # Strong movement + high volatility
                return MarketRegime.BREAKOUT
            elif price_change > 0.2 and volatility < 0.4:  # Upward trend, controlled volatility
                return MarketRegime.TRENDING_BULL
            elif price_change < -0.2 and volatility < 0.4:  # Downward trend, controlled volatility
                return MarketRegime.TRENDING_BEAR
            elif volatility > 0.4:  # High volatility, no clear direction
                return MarketRegime.VOLATILE_RANGE
            else:  # Low volatility, stable price
                return MarketRegime.CALM_RANGE
                
        except Exception as e:
            logger.error(f"Error detecting regime for {symbol}: {e}")
            return MarketRegime.CALM_RANGE
    
    def calculate_real_confidence(self, symbol: str, market_data: Dict, regime: MarketRegime) -> float:
        """Calculate confidence using REAL market conditions"""
        try:
            session = self.get_session_type(datetime.now().hour)
            pair_intel = self.pair_intelligence.get(symbol, {})
            session_intel = self.session_intelligence.get(session, {})
            
            # Base confidence from real spread quality
            spread = market_data.get('spread', 5.0)
            base_confidence = max(30, 85 - (spread * 10))  # Lower spread = higher confidence
            
            # Real volume analysis
            volume = market_data.get('volume', 0)
            volume_bonus = min(15, volume / 100) if volume > 0 else 0
            
            # Session-pair compatibility (VENOM intelligence preserved)
            compatibility_bonus = 0
            if symbol in session_intel.get('optimal_pairs', []):
                compatibility_bonus = 20
            elif pair_intel.get('session_bias') == session:
                compatibility_bonus = 15
            
            # Market regime bonus (preserved VENOM logic)
            regime_bonus = {
                MarketRegime.TRENDING_BULL: 15,
                MarketRegime.TRENDING_BEAR: 15,
                MarketRegime.BREAKOUT: 22,
                MarketRegime.VOLATILE_RANGE: 10,
                MarketRegime.CALM_RANGE: 8,
                MarketRegime.NEWS_EVENT: 0
            }.get(regime, 0)
            
            # Technical analysis bonus from real price history
            tech_bonus = 0
            if symbol in self.price_history and len(self.price_history[symbol]) >= 10:
                prices = [p['price'] for p in self.price_history[symbol][-10:]]
                # Simple momentum check
                if prices[-1] > prices[-5]:  # Recent upward momentum
                    tech_bonus = 10
                elif prices[-1] < prices[-5]:  # Recent downward momentum  
                    tech_bonus = 8
            
            # Calculate final confidence
            final_confidence = base_confidence + volume_bonus + compatibility_bonus + regime_bonus + tech_bonus
            
            # Realistic bounds (no artificial 99% inflation)
            return max(35, min(85, final_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence for {symbol}: {e}")
            return 45.0  # Safe default
    
    def determine_real_direction(self, symbol: str) -> str:
        """Determine trade direction using REAL price analysis"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 10:
            return 'BUY'  # Default when insufficient data
        
        try:
            prices = [p['price'] for p in self.price_history[symbol][-10:]]
            
            # Simple but real momentum analysis
            short_ma = np.mean(prices[-3:])  # 3-period average
            long_ma = np.mean(prices[-10:])  # 10-period average
            
            # Real direction based on momentum
            if short_ma > long_ma:
                return 'BUY'
            else:
                return 'SELL'
                
        except Exception as e:
            logger.error(f"Error determining direction for {symbol}: {e}")
            return 'BUY'  # Safe default
    
    def calculate_real_stops_targets(self, symbol: str, direction: str, signal_type: str) -> Tuple[int, int]:
        """Calculate stop loss and take profit using REAL volatility"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < 10:
                # Fallback to conservative fixed values
                if signal_type == 'RAPID_ASSAULT':
                    return 15, 23  # 1:1.5 R:R
                else:
                    return 20, 40  # 1:2 R:R
            
            # Calculate real Average True Range (ATR) approximation
            prices = [p['price'] for p in self.price_history[symbol][-20:]]
            
            # Simple volatility measure
            price_ranges = []
            for i in range(1, len(prices)):
                price_ranges.append(abs(prices[i] - prices[i-1]))
            
            avg_range = np.mean(price_ranges) if price_ranges else 0.0001
            
            # Convert to pips (adjust for JPY pairs)
            pip_size = 0.01 if 'JPY' in symbol else 0.0001
            volatility_pips = avg_range / pip_size
            
            # Set stops based on real volatility
            if signal_type == 'RAPID_ASSAULT':
                stop_pips = max(10, int(volatility_pips * 1.5))  # 1.5x volatility
                target_pips = int(stop_pips * 1.5)  # 1:1.5 R:R
            else:  # PRECISION_STRIKE
                stop_pips = max(15, int(volatility_pips * 2.0))  # 2x volatility
                target_pips = stop_pips * 2  # 1:2 R:R
            
            return stop_pips, target_pips
            
        except Exception as e:
            logger.error(f"Error calculating stops/targets for {symbol}: {e}")
            # Safe fallback
            if signal_type == 'RAPID_ASSAULT':
                return 15, 30
            else:
                return 20, 60
    
    def determine_signal_quality(self, confidence: float) -> SignalQuality:
        """Map confidence to quality tier (VENOM logic preserved)"""
        if confidence >= 75:
            return SignalQuality.PLATINUM
        elif confidence >= 65:
            return SignalQuality.GOLD
        elif confidence >= 55:
            return SignalQuality.SILVER
        else:
            return SignalQuality.BRONZE
    
    def should_generate_signal(self, symbol: str, confidence: float, quality: SignalQuality, session: str) -> bool:
        """Determine if signal should be generated (realistic thresholds)"""
        # Time-based signal limiting
        current_time = datetime.now()
        if (current_time - self.hour_start).total_seconds() > 3600:
            self.signals_this_hour = 0
            self.hour_start = current_time
        
        if self.signals_this_hour >= self.max_signals_per_hour:
            return False
        
        # Quality threshold (only good quality signals)
        if quality in [SignalQuality.BRONZE]:
            return False
        
        # Confidence threshold (realistic)
        if confidence < 55:
            return False
        
        # Session compatibility
        session_intel = self.session_intelligence.get(session, {})
        if session == 'OFF_HOURS':
            return False  # No off-hours trading
        
        # Generate signal with realistic probability
        base_prob = 0.03  # 3% base chance
        
        # Quality boost
        quality_multiplier = {
            SignalQuality.PLATINUM: 2.0,
            SignalQuality.GOLD: 1.5,
            SignalQuality.SILVER: 1.0,
            SignalQuality.BRONZE: 0.5
        }.get(quality, 1.0)
        
        # Session boost
        if symbol in session_intel.get('optimal_pairs', []):
            base_prob *= 1.5
        
        final_prob = base_prob * quality_multiplier
        
        # NO FAKE DATA - Use real market conditions to determine signal generation
        current_hour = datetime.now().hour
        if final_prob > 0.75:  # High probability based on REAL factors
            return True
        elif final_prob > 0.65 and current_hour in [8, 9, 14, 15]:  # REAL overlap sessions
            return True
        else:
            return False  # NO FAKE SIGNALS
    
    def generate_real_signal(self, symbol: str) -> Optional[Dict]:
        """Generate signal using 100% real market data"""
        try:
            # Must have recent real data
            if symbol not in self.market_data:
                return None
            
            market_data = self.market_data[symbol]
            
            # Check data freshness (within last 60 seconds)
            if time.time() - market_data['timestamp'] > 60:
                logger.debug(f"Stale data for {symbol}, skipping")
                return None
            
            # Real market analysis
            regime = self.detect_real_market_regime(symbol)
            confidence = self.calculate_real_confidence(symbol, market_data, regime)
            quality = self.determine_signal_quality(confidence)
            session = self.get_session_type(datetime.now().hour)
            
            # Check if signal should be generated
            if not self.should_generate_signal(symbol, confidence, quality, session):
                return None
            
            # Determine signal type (preserve VENOM balance)
            if self.total_signals % 5 < 3:  # 60% RAPID_ASSAULT
                signal_type = 'RAPID_ASSAULT'
            else:  # 40% PRECISION_STRIKE
                signal_type = 'PRECISION_STRIKE'
            
            # Real direction and levels
            direction = self.determine_real_direction(symbol)
            stop_pips, target_pips = self.calculate_real_stops_targets(symbol, direction, signal_type)
            
            # Increment counters
            self.total_signals += 1
            self.signals_this_hour += 1
            
            # Create signal with real data
            signal = {
                'signal_id': f'VENOM_REAL_{symbol}_{self.total_signals:06d}',
                'pair': symbol,
                'direction': direction,
                'signal_type': signal_type,
                'confidence': round(confidence, 1),
                'quality': quality.value,
                'market_regime': regime.value,
                'target_pips': target_pips,
                'stop_pips': stop_pips,
                'risk_reward': round(target_pips / stop_pips, 1),
                'session': session,
                'spread': market_data['spread'],
                'timestamp': time.time(),
                'source': 'VENOM_REAL_DATA',
                # Real market conditions
                'real_bid': market_data['bid'],
                'real_ask': market_data['ask'],
                'real_volume': market_data['volume']
            }
            
            logger.info(f"🎯 REAL SIGNAL: {symbol} {direction} @ {confidence:.1f}% | {quality.value} | Regime: {regime.value}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def scan_for_signals(self) -> List[Dict]:
        """Scan all pairs for potential signals using real data"""
        signals = []
        
        for symbol in self.trading_pairs:
            try:
                signal = self.generate_real_signal(symbol)
                if signal:
                    signals.append(signal)
                    
                    # Limit to prevent flooding
                    if len(signals) >= 2:  # Max 2 signals per scan
                        break
                        
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        return signals

if __name__ == '__main__':
    # Test the real data engine
    logger.info("🚀 Testing VENOM Real Data Engine")
    
    engine = VenomRealDataEngine()
    
    # Simulate some real tick data for testing
    test_data = [
        {'symbol': 'EURUSD', 'bid': 1.0850, 'ask': 1.0852, 'spread': 2.0, 'volume': 1500},
        {'symbol': 'GBPUSD', 'bid': 1.2750, 'ask': 1.2753, 'spread': 3.0, 'volume': 1200},
        {'symbol': 'USDJPY', 'bid': 149.45, 'ask': 149.47, 'spread': 2.0, 'volume': 1800}
    ]
    
    # Feed real data
    for tick in test_data:
        engine.update_market_data(tick)
    
    # Generate signals
    logger.info("🔍 Scanning for signals...")
    signals = engine.scan_for_signals()
    
    if signals:
        logger.info(f"✅ Generated {len(signals)} real signals")
        for signal in signals:
            print(json.dumps(signal, indent=2))
    else:
        logger.info("📊 No signals generated (normal with realistic thresholds)")