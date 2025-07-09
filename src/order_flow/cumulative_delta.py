"""
Cumulative Delta Calculator

Calculates cumulative delta (buy volume - sell volume) to identify
buying/selling pressure and potential trend changes.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    """Trade direction classification"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


@dataclass
class DeltaBar:
    """Represents a delta bar (time or volume based)"""
    timestamp: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    buy_volume: float
    sell_volume: float
    delta: float  # buy_volume - sell_volume
    cumulative_delta: float
    total_volume: float
    trade_count: int
    
    def delta_percentage(self) -> float:
        """Calculate delta as percentage of total volume"""
        if self.total_volume == 0:
            return 0.0
        return (self.delta / self.total_volume) * 100
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'buy_volume': self.buy_volume,
            'sell_volume': self.sell_volume,
            'delta': self.delta,
            'cumulative_delta': self.cumulative_delta,
            'total_volume': self.total_volume,
            'delta_percentage': self.delta_percentage(),
            'trade_count': self.trade_count
        }


@dataclass
class DeltaDivergence:
    """Represents a price/delta divergence"""
    start_time: float
    end_time: float
    divergence_type: str  # 'bullish' or 'bearish'
    price_change: float
    delta_change: float
    strength: float  # 0-1
    confirmed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'divergence_type': self.divergence_type,
            'price_change': self.price_change,
            'delta_change': self.delta_change,
            'strength': self.strength,
            'confirmed': self.confirmed
        }


class CumulativeDeltaCalculator:
    """Calculates and analyzes cumulative delta from trade flow"""
    
    def __init__(self,
                 bar_period: int = 60,  # seconds
                 volume_bar_size: Optional[float] = None,
                 lookback_bars: int = 100,
                 divergence_threshold: float = 0.3):
        """
        Initialize cumulative delta calculator
        
        Args:
            bar_period: Time period for each bar in seconds
            volume_bar_size: If set, use volume bars instead of time bars
            lookback_bars: Number of bars to keep in history
            divergence_threshold: Minimum correlation difference for divergence
        """
        self.bar_period = bar_period
        self.volume_bar_size = volume_bar_size
        self.lookback_bars = lookback_bars
        self.divergence_threshold = divergence_threshold
        
        # Data storage
        self.trades_buffer: Dict[str, deque] = {}
        self.delta_bars: Dict[str, deque] = {}
        self.current_bar: Dict[str, Optional[DeltaBar]] = {}
        self.cumulative_delta: Dict[str, float] = {}
        self.divergences: Dict[str, deque] = {}
        
        # Analysis parameters
        self.min_trades_per_bar = 10
        self.divergence_lookback = 20  # bars
    
    def process_trade(self, symbol: str, exchange: str, trade: Dict):
        """Process a single trade"""
        key = f"{exchange}:{symbol}"
        
        # Initialize if needed
        if key not in self.trades_buffer:
            self.trades_buffer[key] = deque(maxlen=10000)
            self.delta_bars[key] = deque(maxlen=self.lookback_bars)
            self.current_bar[key] = None
            self.cumulative_delta[key] = 0.0
            self.divergences[key] = deque(maxlen=50)
        
        # Store trade
        self.trades_buffer[key].append(trade)
        
        # Classify trade direction
        direction = self._classify_trade(trade)
        
        # Update current bar
        self._update_bar(key, trade, direction)
    
    def process_trades_batch(self, symbol: str, exchange: str, trades: List[Dict]):
        """Process a batch of trades"""
        for trade in trades:
            self.process_trade(symbol, exchange, trade)
    
    def _classify_trade(self, trade: Dict) -> TradeDirection:
        """Classify trade as buy or sell based on various heuristics"""
        
        # Method 1: Use taker side if available
        if 'side' in trade:
            return TradeDirection.BUY if trade['side'] == 'buy' else TradeDirection.SELL
        
        # Method 2: Use aggressor/taker info
        if 'takerOrMaker' in trade:
            if trade['takerOrMaker'] == 'taker':
                # Taker hit the ask (buy) or bid (sell)
                if 'price' in trade and 'info' in trade:
                    # Additional logic based on exchange-specific data
                    pass
        
        # Method 3: Tick rule - compare with previous trade
        # This requires maintaining price history, implemented in _update_bar
        
        # Default to neutral if can't determine
        return TradeDirection.NEUTRAL
    
    def _update_bar(self, key: str, trade: Dict, direction: TradeDirection):
        """Update current bar with new trade"""
        
        timestamp = trade.get('timestamp', datetime.now().timestamp() * 1000) / 1000
        price = float(trade['price'])
        volume = float(trade['amount'])
        
        # Check if we need a new bar
        if self._should_create_new_bar(key, timestamp, volume):
            self._close_current_bar(key)
            self._start_new_bar(key, timestamp, price)
        
        # Update current bar
        if self.current_bar[key] is None:
            self._start_new_bar(key, timestamp, price)
        
        bar = self.current_bar[key]
        
        # Update OHLC
        bar.high_price = max(bar.high_price, price)
        bar.low_price = min(bar.low_price, price)
        bar.close_price = price
        
        # Update volumes based on classification
        if direction == TradeDirection.BUY:
            bar.buy_volume += volume
        elif direction == TradeDirection.SELL:
            bar.sell_volume += volume
        else:
            # Split neutral volume 50/50
            bar.buy_volume += volume / 2
            bar.sell_volume += volume / 2
        
        bar.total_volume += volume
        bar.trade_count += 1
        
        # Update delta
        bar.delta = bar.buy_volume - bar.sell_volume
        bar.cumulative_delta = self.cumulative_delta[key] + bar.delta
    
    def _should_create_new_bar(self, key: str, timestamp: float, volume: float) -> bool:
        """Check if we should create a new bar"""
        
        if self.current_bar[key] is None:
            return True
        
        current = self.current_bar[key]
        
        if self.volume_bar_size:
            # Volume-based bars
            return current.total_volume >= self.volume_bar_size
        else:
            # Time-based bars
            return timestamp - current.timestamp >= self.bar_period
    
    def _close_current_bar(self, key: str):
        """Close current bar and add to history"""
        
        if self.current_bar[key] is None:
            return
        
        bar = self.current_bar[key]
        
        # Update cumulative delta
        self.cumulative_delta[key] += bar.delta
        bar.cumulative_delta = self.cumulative_delta[key]
        
        # Add to history
        self.delta_bars[key].append(bar)
        
        # Check for divergences
        self._check_divergence(key)
        
        self.current_bar[key] = None
    
    def _start_new_bar(self, key: str, timestamp: float, price: float):
        """Start a new bar"""
        
        self.current_bar[key] = DeltaBar(
            timestamp=timestamp,
            open_price=price,
            high_price=price,
            low_price=price,
            close_price=price,
            buy_volume=0.0,
            sell_volume=0.0,
            delta=0.0,
            cumulative_delta=self.cumulative_delta[key],
            total_volume=0.0,
            trade_count=0
        )
    
    def _check_divergence(self, key: str):
        """Check for price/delta divergences"""
        
        if len(self.delta_bars[key]) < self.divergence_lookback:
            return
        
        bars = list(self.delta_bars[key])[-self.divergence_lookback:]
        
        # Extract price and delta series
        prices = [bar.close_price for bar in bars]
        deltas = [bar.cumulative_delta for bar in bars]
        
        # Calculate trends
        price_trend = np.polyfit(range(len(prices)), prices, 1)[0]
        delta_trend = np.polyfit(range(len(deltas)), deltas, 1)[0]
        
        # Normalize trends
        price_trend_norm = price_trend / np.mean(prices)
        delta_trend_norm = delta_trend / (np.mean(np.abs(deltas)) + 1)
        
        # Check for divergence
        divergence_score = abs(price_trend_norm - delta_trend_norm)
        
        if divergence_score > self.divergence_threshold:
            # Determine divergence type
            if price_trend_norm > 0 and delta_trend_norm < 0:
                divergence_type = 'bearish'  # Price up, delta down
            elif price_trend_norm < 0 and delta_trend_norm > 0:
                divergence_type = 'bullish'  # Price down, delta up
            else:
                return  # No classic divergence
            
            divergence = DeltaDivergence(
                start_time=bars[0].timestamp,
                end_time=bars[-1].timestamp,
                divergence_type=divergence_type,
                price_change=prices[-1] - prices[0],
                delta_change=deltas[-1] - deltas[0],
                strength=min(1.0, divergence_score),
                confirmed=False
            )
            
            self.divergences[key].append(divergence)
    
    def get_current_delta(self, symbol: str, exchange: str) -> Dict:
        """Get current delta information"""
        key = f"{exchange}:{symbol}"
        
        if key not in self.cumulative_delta:
            return {
                'cumulative_delta': 0.0,
                'current_bar_delta': 0.0,
                'delta_trend': 'neutral'
            }
        
        current_bar = self.current_bar.get(key)
        current_delta = current_bar.delta if current_bar else 0.0
        
        # Determine trend
        if len(self.delta_bars.get(key, [])) >= 5:
            recent_deltas = [bar.delta for bar in list(self.delta_bars[key])[-5:]]
            avg_delta = np.mean(recent_deltas)
            
            if avg_delta > abs(np.std(recent_deltas)):
                delta_trend = 'bullish'
            elif avg_delta < -abs(np.std(recent_deltas)):
                delta_trend = 'bearish'
            else:
                delta_trend = 'neutral'
        else:
            delta_trend = 'neutral'
        
        return {
            'cumulative_delta': self.cumulative_delta[key],
            'current_bar_delta': current_delta,
            'delta_trend': delta_trend,
            'last_bar': self.delta_bars[key][-1].to_dict() if self.delta_bars.get(key) else None
        }
    
    def get_delta_profile(self, symbol: str, exchange: str, periods: int = 20) -> Dict:
        """Get detailed delta profile"""
        key = f"{exchange}:{symbol}"
        
        if key not in self.delta_bars or len(self.delta_bars[key]) == 0:
            return {
                'bars': [],
                'statistics': {},
                'divergences': []
            }
        
        bars = list(self.delta_bars[key])[-periods:]
        
        # Calculate statistics
        deltas = [bar.delta for bar in bars]
        volumes = [bar.total_volume for bar in bars]
        
        stats = {
            'average_delta': np.mean(deltas),
            'delta_std': np.std(deltas),
            'total_buy_volume': sum(bar.buy_volume for bar in bars),
            'total_sell_volume': sum(bar.sell_volume for bar in bars),
            'average_volume': np.mean(volumes),
            'delta_velocity': (bars[-1].cumulative_delta - bars[0].cumulative_delta) / len(bars),
            'positive_bars': sum(1 for bar in bars if bar.delta > 0),
            'negative_bars': sum(1 for bar in bars if bar.delta < 0)
        }
        
        # Get recent divergences
        recent_divergences = []
        if key in self.divergences:
            cutoff_time = datetime.now().timestamp() - (periods * self.bar_period)
            recent_divergences = [
                div.to_dict() for div in self.divergences[key]
                if div.end_time > cutoff_time
            ]
        
        return {
            'bars': [bar.to_dict() for bar in bars],
            'statistics': stats,
            'divergences': recent_divergences
        }
    
    def get_delta_extremes(self, symbol: str, exchange: str) -> Dict:
        """Get delta extreme levels"""
        key = f"{exchange}:{symbol}"
        
        if key not in self.delta_bars or len(self.delta_bars[key]) < 10:
            return {
                'max_delta': 0.0,
                'min_delta': 0.0,
                'extreme_levels': []
            }
        
        bars = list(self.delta_bars[key])
        deltas = [bar.cumulative_delta for bar in bars]
        
        # Find local extremes
        extreme_levels = []
        for i in range(1, len(deltas) - 1):
            if deltas[i] > deltas[i-1] and deltas[i] > deltas[i+1]:
                extreme_levels.append({
                    'type': 'peak',
                    'delta': deltas[i],
                    'price': bars[i].close_price,
                    'timestamp': bars[i].timestamp
                })
            elif deltas[i] < deltas[i-1] and deltas[i] < deltas[i+1]:
                extreme_levels.append({
                    'type': 'trough',
                    'delta': deltas[i],
                    'price': bars[i].close_price,
                    'timestamp': bars[i].timestamp
                })
        
        return {
            'max_delta': max(deltas),
            'min_delta': min(deltas),
            'current_delta': deltas[-1],
            'extreme_levels': extreme_levels[-10:],  # Last 10 extremes
            'delta_range': max(deltas) - min(deltas)
        }


# Example usage
async def main():
    calculator = CumulativeDeltaCalculator(
        bar_period=60,  # 1-minute bars
        lookback_bars=100
    )
    
    # Simulate some trades
    symbol = 'BTC/USDT'
    exchange = 'binance'
    base_price = 50000
    
    for i in range(100):
        # Generate random trades
        for j in range(10):
            trade = {
                'timestamp': (datetime.now() + timedelta(seconds=i*6 + j*0.6)).timestamp() * 1000,
                'price': base_price + np.random.randn() * 10,
                'amount': np.random.exponential(0.1),
                'side': 'buy' if np.random.random() > 0.45 else 'sell'  # Slight buy bias
            }
            calculator.process_trade(symbol, exchange, trade)
        
        # Occasionally check current delta
        if i % 10 == 0:
            delta_info = calculator.get_current_delta(symbol, exchange)
            print(f"Bar {i}: Cumulative Delta: {delta_info['cumulative_delta']:.2f}, "
                  f"Trend: {delta_info['delta_trend']}")
    
    # Get final profile
    profile = calculator.get_delta_profile(symbol, exchange)
    print(f"\nDelta Profile Statistics: {profile['statistics']}")
    
    # Check for divergences
    if profile['divergences']:
        print(f"\nDivergences detected: {len(profile['divergences'])}")
        for div in profile['divergences']:
            print(f"  - {div['divergence_type']} divergence, strength: {div['strength']:.2f}")
    
    # Get extremes
    extremes = calculator.get_delta_extremes(symbol, exchange)
    print(f"\nDelta Extremes - Max: {extremes['max_delta']:.2f}, "
          f"Min: {extremes['min_delta']:.2f}, Current: {extremes['current_delta']:.2f}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())