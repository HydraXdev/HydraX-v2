"""
Imbalance Detector

Detects order book imbalances that may indicate directional pressure.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from collections import deque

from .order_book_reader import OrderBookSnapshot

logger = logging.getLogger(__name__)


@dataclass
class ImbalanceSignal:
    """Represents an order book imbalance signal"""
    timestamp: float
    symbol: str
    exchange: str
    imbalance_ratio: float
    bid_volume: float
    ask_volume: float
    levels_analyzed: int
    direction: str  # 'bullish' or 'bearish'
    strength: str  # 'weak', 'moderate', 'strong', 'extreme'
    weighted_imbalance: float
    price_level: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'imbalance_ratio': self.imbalance_ratio,
            'bid_volume': self.bid_volume,
            'ask_volume': self.ask_volume,
            'levels_analyzed': self.levels_analyzed,
            'direction': self.direction,
            'strength': self.strength,
            'weighted_imbalance': self.weighted_imbalance,
            'price_level': self.price_level
        }


class ImbalanceDetector:
    """Detects and analyzes order book imbalances"""
    
    def __init__(self, 
                 levels_to_analyze: int = 20,
                 imbalance_threshold: float = 1.5,
                 lookback_period: int = 100):
        """
        Initialize imbalance detector
        
        Args:
            levels_to_analyze: Number of order book levels to analyze
            imbalance_threshold: Minimum ratio to consider as imbalance
            lookback_period: Number of snapshots to keep for historical analysis
        """
        self.levels_to_analyze = levels_to_analyze
        self.imbalance_threshold = imbalance_threshold
        self.lookback_period = lookback_period
        
        # Historical data storage
        self.imbalance_history: Dict[str, deque] = {}
        self.signal_history: Dict[str, deque] = {}
        
        # Thresholds for strength classification
        self.strength_thresholds = {
            'weak': 1.5,
            'moderate': 2.0,
            'strong': 3.0,
            'extreme': 5.0
        }
    
    def detect_imbalance(self, snapshot: OrderBookSnapshot) -> Optional[ImbalanceSignal]:
        """Detect imbalance in order book snapshot"""
        
        # Calculate basic imbalance
        bid_volume, ask_volume = self._calculate_volumes(snapshot)
        
        if ask_volume == 0:
            imbalance_ratio = float('inf')
        else:
            imbalance_ratio = bid_volume / ask_volume
        
        # Calculate weighted imbalance
        weighted_imbalance = self._calculate_weighted_imbalance(snapshot)
        
        # Determine direction and strength
        if imbalance_ratio > self.imbalance_threshold:
            direction = 'bullish'
            strength = self._classify_strength(imbalance_ratio)
        elif imbalance_ratio < 1 / self.imbalance_threshold:
            direction = 'bearish'
            strength = self._classify_strength(1 / imbalance_ratio)
            imbalance_ratio = 1 / imbalance_ratio
        else:
            return None  # No significant imbalance
        
        # Create signal
        signal = ImbalanceSignal(
            timestamp=snapshot.timestamp,
            symbol=snapshot.symbol,
            exchange=snapshot.exchange,
            imbalance_ratio=imbalance_ratio,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            levels_analyzed=self.levels_to_analyze,
            direction=direction,
            strength=strength,
            weighted_imbalance=weighted_imbalance,
            price_level=snapshot.get_mid_price()
        )
        
        # Store in history
        self._update_history(signal)
        
        return signal
    
    def detect_dynamic_imbalance(self, snapshot: OrderBookSnapshot) -> Optional[ImbalanceSignal]:
        """Detect imbalance with dynamic level adjustment"""
        
        # Find significant levels based on volume clusters
        significant_levels = self._find_significant_levels(snapshot)
        
        if not significant_levels:
            return self.detect_imbalance(snapshot)
        
        # Calculate imbalance at significant levels
        bid_volume = sum(level.quantity for level in snapshot.bids[:significant_levels['bid']])
        ask_volume = sum(level.quantity for level in snapshot.asks[:significant_levels['ask']])
        
        if ask_volume == 0:
            imbalance_ratio = float('inf')
        else:
            imbalance_ratio = bid_volume / ask_volume
        
        # Rest of the logic similar to detect_imbalance
        weighted_imbalance = self._calculate_weighted_imbalance(snapshot, 
                                                               bid_levels=significant_levels['bid'],
                                                               ask_levels=significant_levels['ask'])
        
        if imbalance_ratio > self.imbalance_threshold:
            direction = 'bullish'
            strength = self._classify_strength(imbalance_ratio)
        elif imbalance_ratio < 1 / self.imbalance_threshold:
            direction = 'bearish'
            strength = self._classify_strength(1 / imbalance_ratio)
            imbalance_ratio = 1 / imbalance_ratio
        else:
            return None
        
        signal = ImbalanceSignal(
            timestamp=snapshot.timestamp,
            symbol=snapshot.symbol,
            exchange=snapshot.exchange,
            imbalance_ratio=imbalance_ratio,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            levels_analyzed=max(significant_levels['bid'], significant_levels['ask']),
            direction=direction,
            strength=strength,
            weighted_imbalance=weighted_imbalance,
            price_level=snapshot.get_mid_price()
        )
        
        self._update_history(signal)
        return signal
    
    def get_imbalance_trend(self, symbol: str, exchange: str = None) -> Dict:
        """Analyze imbalance trend over time"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.signal_history or len(self.signal_history[key]) < 2:
            return {
                'trend': 'neutral',
                'consistency': 0.0,
                'average_ratio': 0.0,
                'signal_count': 0
            }
        
        signals = list(self.signal_history[key])
        
        # Calculate trend metrics
        bullish_count = sum(1 for s in signals if s.direction == 'bullish')
        bearish_count = sum(1 for s in signals if s.direction == 'bearish')
        
        consistency = abs(bullish_count - bearish_count) / len(signals)
        average_ratio = np.mean([s.imbalance_ratio for s in signals])
        
        if bullish_count > bearish_count * 1.5:
            trend = 'bullish'
        elif bearish_count > bullish_count * 1.5:
            trend = 'bearish'
        else:
            trend = 'neutral'
        
        return {
            'trend': trend,
            'consistency': consistency,
            'average_ratio': average_ratio,
            'signal_count': len(signals),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        }
    
    def _calculate_volumes(self, snapshot: OrderBookSnapshot) -> Tuple[float, float]:
        """Calculate bid and ask volumes"""
        bid_volume = sum(level.quantity for level in snapshot.bids[:self.levels_to_analyze])
        ask_volume = sum(level.quantity for level in snapshot.asks[:self.levels_to_analyze])
        return bid_volume, ask_volume
    
    def _calculate_weighted_imbalance(self, snapshot: OrderBookSnapshot, 
                                    bid_levels: int = None, 
                                    ask_levels: int = None) -> float:
        """Calculate price-weighted imbalance"""
        bid_levels = bid_levels or self.levels_to_analyze
        ask_levels = ask_levels or self.levels_to_analyze
        
        mid_price = snapshot.get_mid_price()
        if mid_price == 0:
            return 0.0
        
        # Calculate weighted volumes
        weighted_bid_volume = 0.0
        for level in snapshot.bids[:bid_levels]:
            weight = 1 / (1 + abs(level.price - mid_price) / mid_price)
            weighted_bid_volume += level.quantity * weight
        
        weighted_ask_volume = 0.0
        for level in snapshot.asks[:ask_levels]:
            weight = 1 / (1 + abs(level.price - mid_price) / mid_price)
            weighted_ask_volume += level.quantity * weight
        
        if weighted_ask_volume == 0:
            return float('inf')
        
        return weighted_bid_volume / weighted_ask_volume
    
    def _find_significant_levels(self, snapshot: OrderBookSnapshot) -> Dict[str, int]:
        """Find significant levels based on volume clusters"""
        
        # Analyze bid levels
        bid_volumes = [level.quantity for level in snapshot.bids[:self.levels_to_analyze]]
        bid_significant = self._find_volume_clusters(bid_volumes)
        
        # Analyze ask levels
        ask_volumes = [level.quantity for level in snapshot.asks[:self.levels_to_analyze]]
        ask_significant = self._find_volume_clusters(ask_volumes)
        
        return {
            'bid': bid_significant,
            'ask': ask_significant
        }
    
    def _find_volume_clusters(self, volumes: List[float]) -> int:
        """Find where significant volume clusters end"""
        if not volumes:
            return 0
        
        # Calculate cumulative volume
        cumulative = np.cumsum(volumes)
        total = cumulative[-1]
        
        if total == 0:
            return len(volumes)
        
        # Find level that contains 80% of volume
        threshold = total * 0.8
        for i, cum_vol in enumerate(cumulative):
            if cum_vol >= threshold:
                return i + 1
        
        return len(volumes)
    
    def _classify_strength(self, ratio: float) -> str:
        """Classify imbalance strength"""
        for strength, threshold in sorted(self.strength_thresholds.items(), 
                                        key=lambda x: x[1], reverse=True):
            if ratio >= threshold:
                return strength
        return 'weak'
    
    def _update_history(self, signal: ImbalanceSignal):
        """Update historical data"""
        key = f"{signal.exchange}:{signal.symbol}"
        
        if key not in self.signal_history:
            self.signal_history[key] = deque(maxlen=self.lookback_period)
        
        self.signal_history[key].append(signal)
    
    def get_statistics(self, symbol: str, exchange: str = None) -> Dict:
        """Get imbalance statistics"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.signal_history:
            return {
                'total_signals': 0,
                'average_ratio': 0.0,
                'max_ratio': 0.0,
                'strength_distribution': {}
            }
        
        signals = list(self.signal_history[key])
        
        if not signals:
            return {
                'total_signals': 0,
                'average_ratio': 0.0,
                'max_ratio': 0.0,
                'strength_distribution': {}
            }
        
        ratios = [s.imbalance_ratio for s in signals]
        strength_dist = {}
        for strength in self.strength_thresholds:
            strength_dist[strength] = sum(1 for s in signals if s.strength == strength)
        
        return {
            'total_signals': len(signals),
            'average_ratio': np.mean(ratios),
            'max_ratio': max(ratios),
            'min_ratio': min(ratios),
            'std_ratio': np.std(ratios),
            'strength_distribution': strength_dist,
            'recent_direction': signals[-1].direction if signals else 'neutral'
        }


# Example usage
async def main():
    from order_book_reader import OrderBookSnapshot, OrderBookLevel
    
    # Create sample order book
    snapshot = OrderBookSnapshot(
        symbol='BTC/USDT',
        exchange='binance',
        bids=[
            OrderBookLevel(50000, 2.5),
            OrderBookLevel(49999, 1.8),
            OrderBookLevel(49998, 3.2),
            OrderBookLevel(49997, 0.5),
            OrderBookLevel(49996, 1.2),
        ],
        asks=[
            OrderBookLevel(50001, 0.8),
            OrderBookLevel(50002, 0.5),
            OrderBookLevel(50003, 0.3),
            OrderBookLevel(50004, 0.4),
            OrderBookLevel(50005, 0.2),
        ],
        timestamp=datetime.now().timestamp()
    )
    
    # Create detector
    detector = ImbalanceDetector(levels_to_analyze=5, imbalance_threshold=1.5)
    
    # Detect imbalance
    signal = detector.detect_imbalance(snapshot)
    if signal:
        print(f"Imbalance detected: {signal.direction} ({signal.strength})")
        print(f"Ratio: {signal.imbalance_ratio:.2f}")
        print(f"Bid volume: {signal.bid_volume:.2f}, Ask volume: {signal.ask_volume:.2f}")
    
    # Get statistics
    stats = detector.get_statistics('BTC/USDT', 'binance')
    print(f"Statistics: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())