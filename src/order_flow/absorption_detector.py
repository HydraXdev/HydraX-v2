"""
Absorption Pattern Detector

Detects absorption patterns where large orders are being filled without 
significant price movement, indicating institutional accumulation or distribution.
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
class AbsorptionEvent:
    """Represents an absorption event"""
    timestamp: float
    symbol: str
    exchange: str
    side: str  # 'bid' or 'ask'
    price_level: float
    volume_absorbed: float
    time_duration: float  # seconds
    price_movement: float
    absorption_rate: float  # volume per second
    strength: str  # 'weak', 'moderate', 'strong'
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'side': self.side,
            'price_level': self.price_level,
            'volume_absorbed': self.volume_absorbed,
            'time_duration': self.time_duration,
            'price_movement': self.price_movement,
            'absorption_rate': self.absorption_rate,
            'strength': self.strength
        }

@dataclass
class AbsorptionPattern:
    """Represents a complete absorption pattern"""
    start_time: float
    end_time: float
    symbol: str
    exchange: str
    pattern_type: str  # 'accumulation', 'distribution', 'support', 'resistance'
    total_volume: float
    average_price: float
    price_range: Tuple[float, float]
    events: List[AbsorptionEvent]
    confidence: float  # 0-1
    
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'pattern_type': self.pattern_type,
            'total_volume': self.total_volume,
            'average_price': self.average_price,
            'price_range': self.price_range,
            'event_count': len(self.events),
            'duration': self.duration(),
            'confidence': self.confidence
        }

class AbsorptionPatternDetector:
    """Detects absorption patterns in order flow"""
    
    def __init__(self,
                 min_volume_threshold: float = 100.0,
                 max_price_movement: float = 0.001,  # 0.1%
                 min_duration: float = 10.0,  # seconds
                 lookback_snapshots: int = 100):
        """
        Initialize absorption detector
        
        Args:
            min_volume_threshold: Minimum volume to consider for absorption
            max_price_movement: Maximum price movement percentage for absorption
            min_duration: Minimum time duration for pattern
            lookback_snapshots: Number of snapshots to analyze
        """
        self.min_volume_threshold = min_volume_threshold
        self.max_price_movement = max_price_movement
        self.min_duration = min_duration
        self.lookback_snapshots = lookback_snapshots
        
        # Historical data
        self.snapshot_history: Dict[str, deque] = {}
        self.trade_history: Dict[str, deque] = {}
        self.absorption_events: Dict[str, deque] = {}
        self.active_patterns: Dict[str, List[AbsorptionPattern]] = {}
        
        # Thresholds
        self.absorption_rate_thresholds = {
            'weak': 10.0,
            'moderate': 50.0,
            'strong': 100.0
        }
    
    def analyze_snapshot(self, snapshot: OrderBookSnapshot, trades: List[Dict] = None):
        """Analyze order book snapshot for absorption patterns"""
        key = f"{snapshot.exchange}:{snapshot.symbol}"
        
        # Initialize history if needed
        if key not in self.snapshot_history:
            self.snapshot_history[key] = deque(maxlen=self.lookback_snapshots)
            self.trade_history[key] = deque(maxlen=self.lookback_snapshots * 10)
            self.absorption_events[key] = deque(maxlen=1000)
            self.active_patterns[key] = []
        
        # Store snapshot
        self.snapshot_history[key].append(snapshot)
        
        # Store trades if provided
        if trades:
            self.trade_history[key].extend(trades)
        
        # Need enough history
        if len(self.snapshot_history[key]) < 10:
            return None
        
        # Detect absorption at key levels
        absorption_event = self._detect_level_absorption(key, snapshot)
        if absorption_event:
            self.absorption_events[key].append(absorption_event)
            
            # Check if this forms a pattern
            pattern = self._check_pattern_formation(key)
            if pattern:
                self.active_patterns[key].append(pattern)
                return pattern
        
        return absorption_event
    
    def _detect_level_absorption(self, key: str, current_snapshot: OrderBookSnapshot) -> Optional[AbsorptionEvent]:
        """Detect absorption at specific price levels"""
        
        snapshots = list(self.snapshot_history[key])
        if len(snapshots) < 2:
            return None
        
        # Compare with previous snapshots
        initial_snapshot = snapshots[-10] if len(snapshots) >= 10 else snapshots[0]
        
        # Check bid absorption (buying pressure absorbed at asks)
        ask_absorption = self._check_side_absorption(
            initial_snapshot.asks[:5],
            current_snapshot.asks[:5],
            snapshots,
            'ask'
        )
        
        if ask_absorption:
            return ask_absorption
        
        # Check ask absorption (selling pressure absorbed at bids)
        bid_absorption = self._check_side_absorption(
            initial_snapshot.bids[:5],
            current_snapshot.bids[:5],
            snapshots,
            'bid'
        )
        
        return bid_absorption
    
    def _check_side_absorption(self, initial_levels, current_levels, snapshots, side: str) -> Optional[AbsorptionEvent]:
        """Check absorption on one side of the order book"""
        
        if not initial_levels or not current_levels:
            return None
        
        # Find persistent levels
        for i, initial_level in enumerate(initial_levels[:3]):  # Check top 3 levels
            # Find if this price level still exists
            current_level = None
            for level in current_levels:
                if abs(level.price - initial_level.price) / initial_level.price < 0.0001:  # Within 0.01%
                    current_level = level
                    break
            
            if not current_level:
                continue
            
            # Calculate volume change
            volume_change = initial_level.quantity - current_level.quantity
            
            # Check if significant volume was absorbed
            if volume_change < self.min_volume_threshold:
                continue
            
            # Calculate price movement
            initial_mid = snapshots[0].get_mid_price()
            current_mid = snapshots[-1].get_mid_price()
            price_movement = abs(current_mid - initial_mid) / initial_mid
            
            # Check if price remained stable
            if price_movement > self.max_price_movement:
                continue
            
            # Calculate time duration
            time_duration = snapshots[-1].timestamp - snapshots[0].timestamp
            
            if time_duration < self.min_duration:
                continue
            
            # Calculate absorption rate
            absorption_rate = volume_change / time_duration
            
            # Classify strength
            strength = self._classify_absorption_strength(absorption_rate)
            
            return AbsorptionEvent(
                timestamp=snapshots[-1].timestamp,
                symbol=snapshots[-1].symbol,
                exchange=snapshots[-1].exchange,
                side=side,
                price_level=initial_level.price,
                volume_absorbed=volume_change,
                time_duration=time_duration,
                price_movement=price_movement,
                absorption_rate=absorption_rate,
                strength=strength
            )
        
        return None
    
    def _check_pattern_formation(self, key: str) -> Optional[AbsorptionPattern]:
        """Check if recent absorption events form a pattern"""
        
        if key not in self.absorption_events:
            return None
        
        events = list(self.absorption_events[key])
        if len(events) < 3:
            return None
        
        # Group recent events by time proximity
        recent_events = []
        current_time = events[-1].timestamp
        
        for event in reversed(events):
            if current_time - event.timestamp > 300:  # 5 minutes
                break
            recent_events.append(event)
        
        recent_events.reverse()
        
        if len(recent_events) < 3:
            return None
        
        # Analyze pattern characteristics
        bid_events = [e for e in recent_events if e.side == 'bid']
        ask_events = [e for e in recent_events if e.side == 'ask']
        
        # Determine pattern type
        if len(bid_events) > len(ask_events) * 2:
            pattern_type = 'accumulation'
        elif len(ask_events) > len(bid_events) * 2:
            pattern_type = 'distribution'
        elif len(bid_events) > 0 and len(ask_events) == 0:
            pattern_type = 'support'
        elif len(ask_events) > 0 and len(bid_events) == 0:
            pattern_type = 'resistance'
        else:
            return None  # No clear pattern
        
        # Calculate pattern metrics
        total_volume = sum(e.volume_absorbed for e in recent_events)
        prices = [e.price_level for e in recent_events]
        average_price = np.mean(prices)
        price_range = (min(prices), max(prices))
        
        # Calculate confidence based on consistency and strength
        strength_scores = {'weak': 0.3, 'moderate': 0.6, 'strong': 1.0}
        avg_strength = np.mean([strength_scores.get(e.strength, 0.5) for e in recent_events])
        
        # Consistency of absorption (low variance in rates)
        rates = [e.absorption_rate for e in recent_events]
        rate_consistency = 1 - (np.std(rates) / (np.mean(rates) + 1))
        
        confidence = (avg_strength + rate_consistency) / 2
        
        return AbsorptionPattern(
            start_time=recent_events[0].timestamp,
            end_time=recent_events[-1].timestamp,
            symbol=recent_events[0].symbol,
            exchange=recent_events[0].exchange,
            pattern_type=pattern_type,
            total_volume=total_volume,
            average_price=average_price,
            price_range=price_range,
            events=recent_events,
            confidence=confidence
        )
    
    def _classify_absorption_strength(self, rate: float) -> str:
        """Classify absorption strength based on rate"""
        for strength, threshold in sorted(self.absorption_rate_thresholds.items(),
                                        key=lambda x: x[1], reverse=True):
            if rate >= threshold:
                return strength
        return 'weak'
    
    def get_active_patterns(self, symbol: str, exchange: str = None) -> List[AbsorptionPattern]:
        """Get currently active absorption patterns"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.active_patterns:
            return []
        
        # Filter out old patterns (older than 30 minutes)
        current_time = datetime.now().timestamp()
        active = [p for p in self.active_patterns[key] 
                 if current_time - p.end_time < 1800]
        
        self.active_patterns[key] = active
        return active
    
    def get_statistics(self, symbol: str, exchange: str = None) -> Dict:
        """Get absorption statistics"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.absorption_events:
            return {
                'total_events': 0,
                'total_volume_absorbed': 0.0,
                'pattern_count': 0,
                'dominant_side': 'neutral'
            }
        
        events = list(self.absorption_events[key])
        patterns = self.get_active_patterns(symbol, exchange)
        
        if not events:
            return {
                'total_events': 0,
                'total_volume_absorbed': 0.0,
                'pattern_count': 0,
                'dominant_side': 'neutral'
            }
        
        bid_volume = sum(e.volume_absorbed for e in events if e.side == 'bid')
        ask_volume = sum(e.volume_absorbed for e in events if e.side == 'ask')
        
        if bid_volume > ask_volume * 1.5:
            dominant_side = 'bid'
        elif ask_volume > bid_volume * 1.5:
            dominant_side = 'ask'
        else:
            dominant_side = 'neutral'
        
        return {
            'total_events': len(events),
            'total_volume_absorbed': sum(e.volume_absorbed for e in events),
            'average_absorption_rate': np.mean([e.absorption_rate for e in events]),
            'pattern_count': len(patterns),
            'dominant_side': dominant_side,
            'bid_absorption': bid_volume,
            'ask_absorption': ask_volume,
            'recent_pattern': patterns[-1].pattern_type if patterns else None
        }

# Example usage
async def main():
    from order_book_reader import OrderBookSnapshot, OrderBookLevel
    import time
    
    detector = AbsorptionPatternDetector(
        min_volume_threshold=10.0,
        max_price_movement=0.001,
        min_duration=5.0
    )
    
    # Simulate absorption scenario
    base_price = 50000
    
    for i in range(20):
        # Create snapshot with decreasing ask volume (absorption)
        snapshot = OrderBookSnapshot(
            symbol='BTC/USDT',
            exchange='binance',
            bids=[
                OrderBookLevel(base_price - 1, 100),
                OrderBookLevel(base_price - 2, 80),
                OrderBookLevel(base_price - 3, 60)],
            asks=[
                OrderBookLevel(base_price + 1, 100 - i * 5),  # Decreasing volume
                OrderBookLevel(base_price + 2, 80),
                OrderBookLevel(base_price + 3, 60)],
            timestamp=time.time() + i * 2
        )
        
        result = detector.analyze_snapshot(snapshot)
        
        if isinstance(result, AbsorptionEvent):
            print(f"Absorption detected at {result.price_level}: "
                  f"{result.volume_absorbed:.2f} volume in {result.time_duration:.1f}s")
        elif isinstance(result, AbsorptionPattern):
            print(f"Pattern formed: {result.pattern_type} with "
                  f"{result.total_volume:.2f} total volume, confidence: {result.confidence:.2f}")
        
        await asyncio.sleep(0.1)
    
    # Get statistics
    stats = detector.get_statistics('BTC/USDT', 'binance')
    print(f"\nStatistics: {stats}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())