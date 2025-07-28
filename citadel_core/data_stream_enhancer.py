#!/usr/bin/env python3
"""
CITADEL Data Stream Enhancer
Transforms basic broker tick data into institutional-grade market intelligence

This module takes the real broker data stream and builds the sophisticated
market data structures that CITADEL needs for accurate analysis.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque, defaultdict
import numpy as np
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class TickData:
    """Single tick data point"""
    symbol: str
    bid: float
    ask: float
    spread: float
    volume: int
    timestamp: int
    
    @property
    def mid_price(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)

@dataclass
class CandleData:
    """OHLC candle data"""
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: int
    tick_count: int = 0
    
    def __post_init__(self):
        self.body_size = abs(self.close - self.open)
        self.upper_wick = self.high - max(self.open, self.close)
        self.lower_wick = min(self.open, self.close) - self.low
        self.total_range = self.high - self.low

class CitadelDataStreamEnhancer:
    """
    Enhances basic broker tick data into institutional-grade market intelligence
    """
    
    def __init__(self):
        # Data storage for each symbol
        self.tick_history = defaultdict(lambda: deque(maxlen=1000))  # Last 1000 ticks
        self.candle_data = defaultdict(lambda: {
            'M1': deque(maxlen=200),   # 200 1-minute candles
            'M5': deque(maxlen=200),   # 200 5-minute candles  
            'M15': deque(maxlen=200),  # 200 15-minute candles
            'H1': deque(maxlen=100),   # 100 1-hour candles
            'H4': deque(maxlen=50),    # 50 4-hour candles
        })
        
        # Price level tracking
        self.support_resistance = defaultdict(lambda: {
            'support_levels': [],
            'resistance_levels': [],
            'last_updated': 0
        })
        
        # Liquidity tracking
        self.liquidity_zones = defaultdict(lambda: {
            'high_liquidity': [],
            'stop_clusters': [],
            'sweep_candidates': [],
            'order_blocks': []
        })
        
        # Volume analysis
        self.volume_profile = defaultdict(lambda: {
            'volume_by_price': defaultdict(int),
            'average_volume': 0,
            'volume_spikes': []
        })
        
        # Session tracking
        self.session_data = {
            'current_session': self._get_current_session(),
            'session_high': defaultdict(float),
            'session_low': defaultdict(lambda: float('inf')),
            'session_range': defaultdict(float)
        }
        
        # ATR and volatility
        self.volatility_data = defaultdict(lambda: {
            'atr_14': 0,
            'atr_history': deque(maxlen=50),
            'volatility_percentile': 0
        })
        
        logger.info("CITADEL Data Stream Enhancer initialized")
    
    def process_broker_stream(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw broker data and return enhanced market intelligence
        
        Args:
            raw_data: Raw broker tick data from /tmp/ea_raw_data.json
            
        Returns:
            Enhanced market data for CITADEL analysis
        """
        try:
            ticks = raw_data.get('ticks', [])
            enhanced_data = {}
            
            for tick_raw in ticks:
                symbol = tick_raw['symbol']
                tick = TickData(
                    symbol=symbol,
                    bid=tick_raw['bid'],
                    ask=tick_raw['ask'], 
                    spread=tick_raw['spread'],
                    volume=tick_raw['volume'],
                    timestamp=tick_raw['time']
                )
                
                # Store tick
                self.tick_history[symbol].append(tick)
                
                # Build candles
                self._update_candles(symbol, tick)
                
                # Analyze price levels
                self._analyze_price_levels(symbol, tick)
                
                # Track liquidity
                self._track_liquidity_zones(symbol, tick)
                
                # Update volume profile
                self._update_volume_profile(symbol, tick)
                
                # Calculate volatility
                self._calculate_volatility(symbol)
                
                # Generate enhanced data for this symbol
                enhanced_data[symbol] = self._generate_enhanced_data(symbol)
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error processing broker stream: {e}")
            return {}
    
    def _update_candles(self, symbol: str, tick: TickData):
        """Update candle data for all timeframes"""
        timeframes = {
            'M1': 60,      # 1 minute
            'M5': 300,     # 5 minutes
            'M15': 900,    # 15 minutes
            'H1': 3600,    # 1 hour
            'H4': 14400    # 4 hours
        }
        
        for tf_name, tf_seconds in timeframes.items():
            candles = self.candle_data[symbol][tf_name]
            current_time = tick.timestamp
            
            # Calculate candle start time
            candle_start = (current_time // tf_seconds) * tf_seconds
            
            # Check if we need a new candle
            if not candles or candles[-1].timestamp != candle_start:
                # Create new candle
                new_candle = CandleData(
                    open=tick.mid_price,
                    high=tick.mid_price,
                    low=tick.mid_price,
                    close=tick.mid_price,
                    volume=tick.volume,
                    timestamp=candle_start,
                    tick_count=1
                )
                candles.append(new_candle)
            else:
                # Update existing candle
                candle = candles[-1]
                candle.high = max(candle.high, tick.mid_price)
                candle.low = min(candle.low, tick.mid_price)
                candle.close = tick.mid_price
                candle.volume += tick.volume
                candle.tick_count += 1
    
    def _analyze_price_levels(self, symbol: str, tick: TickData):
        """Identify support and resistance levels"""
        if len(self.tick_history[symbol]) < 50:
            return
            
        # Get recent price action
        recent_ticks = list(self.tick_history[symbol])[-50:]
        prices = [t.mid_price for t in recent_ticks]
        
        # Find local highs and lows
        highs = []
        lows = []
        
        for i in range(2, len(prices) - 2):
            # Local high
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and 
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                highs.append(prices[i])
            
            # Local low
            if (prices[i] < prices[i-1] and prices[i] < prices[i-2] and 
                prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                lows.append(prices[i])
        
        # Store as support/resistance
        levels = self.support_resistance[symbol]
        levels['resistance_levels'] = sorted(set(highs), reverse=True)[:5]
        levels['support_levels'] = sorted(set(lows))[:5]
        levels['last_updated'] = tick.timestamp
    
    def _track_liquidity_zones(self, symbol: str, tick: TickData):
        """Track liquidity and identify potential sweep zones"""
        if len(self.tick_history[symbol]) < 20:
            return
            
        # Look for rapid price movements (potential sweeps)
        recent_ticks = list(self.tick_history[symbol])[-20:]
        
        if len(recent_ticks) >= 10:
            # Check for price spikes
            prices = [t.mid_price for t in recent_ticks]
            price_changes = np.diff(prices)
            
            # Identify significant moves
            std_dev = np.std(price_changes)
            mean_change = np.mean(price_changes)
            
            for i, change in enumerate(price_changes):
                if abs(change) > mean_change + 2 * std_dev:
                    # Potential liquidity event
                    liquidity = self.liquidity_zones[symbol]
                    
                    if change > 0:
                        # Upward spike - potential resistance sweep
                        liquidity['sweep_candidates'].append({
                            'type': 'resistance_sweep',
                            'price': recent_ticks[i+1].mid_price,
                            'timestamp': recent_ticks[i+1].timestamp,
                            'magnitude': change
                        })
                    else:
                        # Downward spike - potential support sweep  
                        liquidity['sweep_candidates'].append({
                            'type': 'support_sweep', 
                            'price': recent_ticks[i+1].mid_price,
                            'timestamp': recent_ticks[i+1].timestamp,
                            'magnitude': abs(change)
                        })
    
    def _update_volume_profile(self, symbol: str, tick: TickData):
        """Update volume profile analysis"""
        profile = self.volume_profile[symbol]
        
        # Bin price for volume profile
        price_bin = round(tick.mid_price, 4)
        profile['volume_by_price'][price_bin] += tick.volume
        
        # Calculate average volume
        if len(self.tick_history[symbol]) >= 100:
            recent_volumes = [t.volume for t in list(self.tick_history[symbol])[-100:]]
            profile['average_volume'] = np.mean(recent_volumes)
            
            # Detect volume spikes
            if tick.volume > profile['average_volume'] * 2:
                profile['volume_spikes'].append({
                    'price': tick.mid_price,
                    'volume': tick.volume,
                    'timestamp': tick.timestamp
                })
    
    def _calculate_volatility(self, symbol: str):
        """Calculate ATR and volatility metrics"""
        if symbol not in self.candle_data or len(self.candle_data[symbol]['H1']) < 14:
            return
            
        # Calculate ATR from H1 candles
        h1_candles = list(self.candle_data[symbol]['H1'])[-14:]
        tr_values = []
        
        for i in range(1, len(h1_candles)):
            current = h1_candles[i]
            previous = h1_candles[i-1]
            
            tr = max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close)
            )
            tr_values.append(tr)
        
        if tr_values:
            atr = np.mean(tr_values)
            volatility = self.volatility_data[symbol]
            volatility['atr_14'] = atr
            volatility['atr_history'].append(atr)
            
            # Calculate volatility percentile
            if len(volatility['atr_history']) >= 20:
                atr_values = list(volatility['atr_history'])
                percentile = (np.searchsorted(sorted(atr_values), atr) / len(atr_values)) * 100
                volatility['volatility_percentile'] = percentile
    
    def _get_current_session(self) -> str:
        """Determine current trading session"""
        now = datetime.utcnow()
        hour = now.hour
        
        # Session times (UTC)
        if 21 <= hour <= 23 or 0 <= hour <= 6:
            return 'asian'
        elif 7 <= hour <= 11:
            return 'london'  
        elif 12 <= hour <= 17:
            return 'overlap_london_ny'
        else:
            return 'new_york'
    
    def _generate_enhanced_data(self, symbol: str) -> Dict[str, Any]:
        """Generate enhanced market data for CITADEL"""
        if len(self.tick_history[symbol]) < 10:
            return {}
            
        recent_ticks = list(self.tick_history[symbol])
        current_price = recent_ticks[-1].mid_price
        
        # Get timeframe data
        tf_data = {}
        for tf_name in ['M5', 'M15', 'H1', 'H4']:
            if self.candle_data[symbol][tf_name]:
                candles = list(self.candle_data[symbol][tf_name])
                latest = candles[-1]
                
                tf_data[tf_name] = {
                    'close': latest.close,
                    'high': latest.high,
                    'low': latest.low,
                    'open': latest.open,
                    'volume': latest.volume,
                    'body_size': latest.body_size,
                    'upper_wick': latest.upper_wick,
                    'lower_wick': latest.lower_wick,
                    'range': latest.total_range,
                    'direction': 'bullish' if latest.close > latest.open else 'bearish',
                    'recent_highs': [c.high for c in candles[-5:]] if len(candles) >= 5 else [],
                    'recent_lows': [c.low for c in candles[-5:]] if len(candles) >= 5 else []
                }
        
        # Get support/resistance
        levels = self.support_resistance[symbol]
        
        # Get liquidity data
        liquidity = self.liquidity_zones[symbol]
        
        # Get volume analysis
        volume = self.volume_profile[symbol]
        
        # Get volatility
        volatility = self.volatility_data[symbol]
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': recent_ticks[-1].timestamp,
            'session': self.session_data['current_session'],
            
            # Price levels
            'recent_high': max([t.mid_price for t in recent_ticks[-20:]]) if len(recent_ticks) >= 20 else current_price,
            'recent_low': min([t.mid_price for t in recent_ticks[-20:]]) if len(recent_ticks) >= 20 else current_price,
            'support_levels': levels['support_levels'],
            'resistance_levels': levels['resistance_levels'],
            
            # Timeframe analysis
            'timeframes': tf_data,
            
            # Liquidity analysis
            'liquidity_sweeps': liquidity['sweep_candidates'][-5:],  # Last 5 sweeps
            'high_liquidity_zones': liquidity['high_liquidity'],
            'order_blocks': liquidity['order_blocks'],
            
            # Volume analysis
            'volume_profile': dict(volume['volume_by_price']),
            'average_volume': volume['average_volume'],
            'volume_spikes': volume['volume_spikes'][-3:],  # Last 3 spikes
            
            # Volatility
            'atr': volatility['atr_14'],
            'atr_history': list(volatility['atr_history'])[-10:],  # Last 10 ATR values
            'volatility_percentile': volatility['volatility_percentile'],
            
            # Market structure
            'trend_direction': self._determine_trend(tf_data),
            'market_structure': self._analyze_market_structure(tf_data),
            'confluence_zones': self._find_confluence_zones(levels, tf_data),
            
            # Real-time metrics
            'spread_analysis': self._analyze_spread(recent_ticks),
            'price_momentum': self._calculate_momentum(recent_ticks),
            'tick_analysis': self._analyze_tick_patterns(recent_ticks)
        }
    
    def _determine_trend(self, tf_data: Dict) -> str:
        """Determine overall trend direction from multiple timeframes"""
        if not tf_data:
            return 'neutral'
            
        bullish_count = 0
        bearish_count = 0
        
        for tf_name, data in tf_data.items():
            if data['direction'] == 'bullish':
                bullish_count += 1
            else:
                bearish_count += 1
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def _analyze_market_structure(self, tf_data: Dict) -> str:
        """Analyze market structure"""
        if not tf_data or 'H1' not in tf_data:
            return 'unknown'
            
        h1_data = tf_data['H1']
        
        # Simple structure analysis
        if h1_data['body_size'] > h1_data['range'] * 0.7:
            return 'trending'
        elif h1_data['upper_wick'] > h1_data['body_size'] * 1.5 or h1_data['lower_wick'] > h1_data['body_size'] * 1.5:
            return 'rejection'
        else:
            return 'consolidation'
    
    def _find_confluence_zones(self, levels: Dict, tf_data: Dict) -> List[Dict]:
        """Find confluence zones where multiple factors align"""
        confluences = []
        
        # Find where support/resistance aligns with timeframe levels
        all_levels = levels['support_levels'] + levels['resistance_levels']
        
        for level in all_levels:
            confluence_count = 1
            factors = ['key_level']
            
            # Check if near timeframe highs/lows
            for tf_name, data in tf_data.items():
                if data['recent_highs']:
                    for high in data['recent_highs']:
                        if abs(high - level) < level * 0.001:  # Within 0.1%
                            confluence_count += 1
                            factors.append(f'{tf_name}_high')
                
                if data['recent_lows']:
                    for low in data['recent_lows']:
                        if abs(low - level) < level * 0.001:  # Within 0.1%
                            confluence_count += 1
                            factors.append(f'{tf_name}_low')
            
            if confluence_count >= 2:
                confluences.append({
                    'price': level,
                    'strength': confluence_count,
                    'factors': factors
                })
        
        return sorted(confluences, key=lambda x: x['strength'], reverse=True)[:5]
    
    def _analyze_spread(self, ticks: List[TickData]) -> Dict:
        """Analyze spread behavior"""
        if len(ticks) < 10:
            return {}
            
        spreads = [t.spread for t in ticks[-10:]]
        return {
            'current_spread': ticks[-1].spread,
            'average_spread': np.mean(spreads),
            'spread_volatility': np.std(spreads),
            'spread_trend': 'widening' if spreads[-1] > np.mean(spreads) else 'tightening'
        }
    
    def _calculate_momentum(self, ticks: List[TickData]) -> Dict:
        """Calculate price momentum"""
        if len(ticks) < 20:
            return {}
            
        prices = [t.mid_price for t in ticks[-20:]]
        short_ma = np.mean(prices[-5:])  # 5-tick MA
        long_ma = np.mean(prices[-10:])  # 10-tick MA
        
        return {
            'momentum_direction': 'bullish' if short_ma > long_ma else 'bearish',
            'momentum_strength': abs(short_ma - long_ma) / long_ma * 100,
            'price_velocity': (prices[-1] - prices[-5]) / prices[-5] * 100 if len(prices) >= 5 else 0
        }
    
    def _analyze_tick_patterns(self, ticks: List[TickData]) -> Dict:
        """Analyze tick-level patterns"""
        if len(ticks) < 15:
            return {}
            
        prices = [t.mid_price for t in ticks[-15:]]
        
        # Count consecutive moves
        consecutive_up = 0
        consecutive_down = 0
        
        for i in range(len(prices) - 1, 0, -1):
            if prices[i] > prices[i-1]:
                consecutive_up += 1
                break
            elif prices[i] < prices[i-1]:
                consecutive_down += 1
            else:
                break
        
        return {
            'consecutive_up_ticks': consecutive_up,
            'consecutive_down_ticks': consecutive_down,
            'tick_direction': 'up' if consecutive_up > 0 else 'down' if consecutive_down > 0 else 'flat',
            'price_range_15_ticks': max(prices) - min(prices)
        }

# Singleton instance
_enhancer_instance = None

def get_data_enhancer() -> CitadelDataStreamEnhancer:
    """Get singleton data enhancer instance"""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = CitadelDataStreamEnhancer()
    return _enhancer_instance

if __name__ == "__main__":
    # Test the enhancer with current broker data
    enhancer = CitadelDataStreamEnhancer()
    
    try:
        with open('/tmp/ea_raw_data.json', 'r') as f:
            raw_data = json.load(f)
        
        enhanced = enhancer.process_broker_stream(raw_data)
        
        print("=== CITADEL ENHANCED DATA SAMPLE ===")
        for symbol, data in enhanced.items():
            print(f"\n{symbol}:")
            print(f"  Current Price: {data.get('current_price', 'N/A')}")
            print(f"  Session: {data.get('session', 'N/A')}")
            print(f"  Trend: {data.get('trend_direction', 'N/A')}")
            print(f"  Structure: {data.get('market_structure', 'N/A')}")
            print(f"  ATR: {data.get('atr', 'N/A')}")
            print(f"  Support Levels: {data.get('support_levels', [])}")
            print(f"  Resistance Levels: {data.get('resistance_levels', [])}")
            break  # Just show first symbol
            
    except Exception as e:
        print(f"Test error: {e}")