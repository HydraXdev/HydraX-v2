"""
Liquidity Void Detector

Identifies areas in the order book with minimal liquidity that could lead
to rapid price movements or slippage.
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
class LiquidityVoid:
    """Represents a liquidity void in the order book"""
    timestamp: float
    symbol: str
    exchange: str
    side: str  # 'bid' or 'ask'
    start_price: float
    end_price: float
    gap_size: float  # Price difference
    gap_percentage: float  # Percentage of mid price
    volume_before: float  # Volume before the void
    volume_after: float  # Volume after the void
    severity: str  # 'minor', 'moderate', 'severe', 'critical'
    potential_slippage: float  # Estimated slippage through the void
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'side': self.side,
            'start_price': self.start_price,
            'end_price': self.end_price,
            'gap_size': self.gap_size,
            'gap_percentage': self.gap_percentage,
            'volume_before': self.volume_before,
            'volume_after': self.volume_after,
            'severity': self.severity,
            'potential_slippage': self.potential_slippage
        }


@dataclass
class LiquidityProfile:
    """Overall liquidity profile of an order book"""
    timestamp: float
    symbol: str
    exchange: str
    total_bid_liquidity: float
    total_ask_liquidity: float
    bid_void_count: int
    ask_void_count: int
    largest_bid_void: Optional[LiquidityVoid]
    largest_ask_void: Optional[LiquidityVoid]
    liquidity_score: float  # 0-100, higher is better
    average_spread: float
    effective_spread: float  # Spread considering liquidity
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'total_bid_liquidity': self.total_bid_liquidity,
            'total_ask_liquidity': self.total_ask_liquidity,
            'bid_void_count': self.bid_void_count,
            'ask_void_count': self.ask_void_count,
            'liquidity_score': self.liquidity_score,
            'average_spread': self.average_spread,
            'effective_spread': self.effective_spread,
            'has_critical_voids': (self.largest_bid_void and self.largest_bid_void.severity == 'critical') or
                                 (self.largest_ask_void and self.largest_ask_void.severity == 'critical')
        }


class LiquidityVoidDetector:
    """Detects and analyzes liquidity voids in order books"""
    
    def __init__(self,
                 min_gap_percentage: float = 0.001,  # 0.1%
                 min_volume_threshold: float = 10.0,
                 levels_to_analyze: int = 50,
                 lookback_period: int = 100):
        """
        Initialize liquidity void detector
        
        Args:
            min_gap_percentage: Minimum gap size as percentage of price
            min_volume_threshold: Minimum volume to consider significant
            levels_to_analyze: Number of order book levels to analyze
            lookback_period: Number of snapshots to keep for history
        """
        self.min_gap_percentage = min_gap_percentage
        self.min_volume_threshold = min_volume_threshold
        self.levels_to_analyze = levels_to_analyze
        self.lookback_period = lookback_period
        
        # Historical data
        self.void_history: Dict[str, deque] = {}
        self.profile_history: Dict[str, deque] = {}
        
        # Severity thresholds (as percentage of mid price)
        self.severity_thresholds = {
            'minor': 0.001,     # 0.1%
            'moderate': 0.005,  # 0.5%
            'severe': 0.01,     # 1%
            'critical': 0.02    # 2%
        }
    
    def analyze_liquidity(self, snapshot: OrderBookSnapshot) -> LiquidityProfile:
        """Analyze overall liquidity profile of order book"""
        
        # Detect voids on both sides
        bid_voids = self._detect_side_voids(snapshot, 'bid')
        ask_voids = self._detect_side_voids(snapshot, 'ask')
        
        # Store in history
        key = f"{snapshot.exchange}:{snapshot.symbol}"
        if key not in self.void_history:
            self.void_history[key] = deque(maxlen=self.lookback_period)
            self.profile_history[key] = deque(maxlen=self.lookback_period)
        
        all_voids = bid_voids + ask_voids
        self.void_history[key].extend(all_voids)
        
        # Calculate liquidity metrics
        total_bid_liquidity = sum(level.quantity * level.price 
                                for level in snapshot.bids[:self.levels_to_analyze])
        total_ask_liquidity = sum(level.quantity * level.price 
                                for level in snapshot.asks[:self.levels_to_analyze])
        
        # Find largest voids
        largest_bid_void = max(bid_voids, key=lambda v: v.gap_percentage) if bid_voids else None
        largest_ask_void = max(ask_voids, key=lambda v: v.gap_percentage) if ask_voids else None
        
        # Calculate liquidity score
        liquidity_score = self._calculate_liquidity_score(
            snapshot, bid_voids, ask_voids, total_bid_liquidity, total_ask_liquidity
        )
        
        # Calculate spreads
        average_spread = snapshot.get_spread()
        effective_spread = self._calculate_effective_spread(snapshot, bid_voids, ask_voids)
        
        profile = LiquidityProfile(
            timestamp=snapshot.timestamp,
            symbol=snapshot.symbol,
            exchange=snapshot.exchange,
            total_bid_liquidity=total_bid_liquidity,
            total_ask_liquidity=total_ask_liquidity,
            bid_void_count=len(bid_voids),
            ask_void_count=len(ask_voids),
            largest_bid_void=largest_bid_void,
            largest_ask_void=largest_ask_void,
            liquidity_score=liquidity_score,
            average_spread=average_spread,
            effective_spread=effective_spread
        )
        
        self.profile_history[key].append(profile)
        return profile
    
    def _detect_side_voids(self, snapshot: OrderBookSnapshot, side: str) -> List[LiquidityVoid]:
        """Detect liquidity voids on one side of the order book"""
        
        levels = snapshot.bids if side == 'bid' else snapshot.asks
        if len(levels) < 2:
            return []
        
        voids = []
        mid_price = snapshot.get_mid_price()
        
        # Analyze consecutive levels
        for i in range(min(len(levels) - 1, self.levels_to_analyze - 1)):
            current_level = levels[i]
            next_level = levels[i + 1]
            
            # Calculate gap
            if side == 'bid':
                gap = current_level.price - next_level.price
            else:
                gap = next_level.price - current_level.price
            
            gap_percentage = gap / mid_price
            
            # Check if gap is significant
            if gap_percentage < self.min_gap_percentage:
                continue
            
            # Check volume significance
            if current_level.quantity < self.min_volume_threshold:
                continue
            
            # Calculate potential slippage
            volume_to_cross = current_level.quantity
            potential_slippage = self._estimate_slippage(
                volume_to_cross, gap, mid_price
            )
            
            # Classify severity
            severity = self._classify_severity(gap_percentage)
            
            void = LiquidityVoid(
                timestamp=snapshot.timestamp,
                symbol=snapshot.symbol,
                exchange=snapshot.exchange,
                side=side,
                start_price=current_level.price,
                end_price=next_level.price,
                gap_size=gap,
                gap_percentage=gap_percentage,
                volume_before=current_level.quantity,
                volume_after=next_level.quantity,
                severity=severity,
                potential_slippage=potential_slippage
            )
            
            voids.append(void)
        
        return voids
    
    def _calculate_liquidity_score(self, snapshot: OrderBookSnapshot,
                                 bid_voids: List[LiquidityVoid],
                                 ask_voids: List[LiquidityVoid],
                                 total_bid_liquidity: float,
                                 total_ask_liquidity: float) -> float:
        """Calculate overall liquidity score (0-100)"""
        
        score = 100.0
        
        # Penalize for voids
        void_penalty = len(bid_voids) + len(ask_voids)
        score -= void_penalty * 2
        
        # Penalize for severe voids
        severe_voids = sum(1 for v in bid_voids + ask_voids 
                          if v.severity in ['severe', 'critical'])
        score -= severe_voids * 5
        
        # Penalize for liquidity imbalance
        if total_bid_liquidity + total_ask_liquidity > 0:
            imbalance = abs(total_bid_liquidity - total_ask_liquidity) / \
                       (total_bid_liquidity + total_ask_liquidity)
            score -= imbalance * 10
        
        # Penalize for wide spread
        spread_percentage = snapshot.get_spread() / snapshot.get_mid_price()
        score -= min(spread_percentage * 1000, 20)  # Cap at 20 points
        
        # Bonus for deep liquidity
        depth_score = min(20, (total_bid_liquidity + total_ask_liquidity) / 10000)
        score += depth_score
        
        return max(0, min(100, score))
    
    def _calculate_effective_spread(self, snapshot: OrderBookSnapshot,
                                  bid_voids: List[LiquidityVoid],
                                  ask_voids: List[LiquidityVoid]) -> float:
        """Calculate effective spread considering liquidity voids"""
        
        base_spread = snapshot.get_spread()
        
        # Add penalty for voids near the top
        void_penalty = 0.0
        
        # Check for voids in top 5 levels
        for void in bid_voids[:5] + ask_voids[:5]:
            if void.severity in ['severe', 'critical']:
                void_penalty += void.gap_size * 0.5
            elif void.severity == 'moderate':
                void_penalty += void.gap_size * 0.25
        
        return base_spread + void_penalty
    
    def _estimate_slippage(self, volume: float, gap: float, mid_price: float) -> float:
        """Estimate potential slippage through a void"""
        
        # Simple model: slippage increases with volume and gap size
        base_slippage = gap / mid_price
        volume_factor = 1 + (volume / 100)  # Adjust based on typical volumes
        
        return base_slippage * volume_factor
    
    def _classify_severity(self, gap_percentage: float) -> str:
        """Classify void severity based on gap size"""
        
        for severity, threshold in sorted(self.severity_thresholds.items(),
                                        key=lambda x: x[1], reverse=True):
            if gap_percentage >= threshold:
                return severity
        return 'minor'
    
    def get_void_clusters(self, symbol: str, exchange: str = None) -> List[Dict]:
        """Identify clusters of liquidity voids"""
        
        key = f"{exchange or 'all'}:{symbol}"
        if key not in self.void_history:
            return []
        
        voids = list(self.void_history[key])
        if not voids:
            return []
        
        # Group voids by price proximity
        clusters = []
        current_cluster = [voids[0]]
        
        for void in voids[1:]:
            # Check if void is near the current cluster
            cluster_center = np.mean([v.start_price for v in current_cluster])
            if abs(void.start_price - cluster_center) / cluster_center < 0.01:  # Within 1%
                current_cluster.append(void)
            else:
                # Start new cluster
                if len(current_cluster) >= 3:  # Minimum cluster size
                    clusters.append(self._analyze_cluster(current_cluster))
                current_cluster = [void]
        
        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append(self._analyze_cluster(current_cluster))
        
        return clusters
    
    def _analyze_cluster(self, voids: List[LiquidityVoid]) -> Dict:
        """Analyze a cluster of liquidity voids"""
        
        price_range = (
            min(v.start_price for v in voids),
            max(v.end_price for v in voids)
        )
        
        total_gap = sum(v.gap_size for v in voids)
        avg_severity = np.mean([
            list(self.severity_thresholds.keys()).index(v.severity) 
            for v in voids
        ])
        
        return {
            'void_count': len(voids),
            'price_range': price_range,
            'total_gap': total_gap,
            'average_gap_percentage': np.mean([v.gap_percentage for v in voids]),
            'dominant_side': max(set(v.side for v in voids), 
                               key=lambda s: sum(1 for v in voids if v.side == s)),
            'severity': list(self.severity_thresholds.keys())[int(avg_severity)],
            'timestamps': [v.timestamp for v in voids]
        }
    
    def get_statistics(self, symbol: str, exchange: str = None) -> Dict:
        """Get liquidity void statistics"""
        
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.profile_history:
            return {
                'profiles_analyzed': 0,
                'average_liquidity_score': 0.0,
                'total_voids_detected': 0,
                'void_clusters': 0
            }
        
        profiles = list(self.profile_history[key])
        voids = list(self.void_history[key]) if key in self.void_history else []
        
        if not profiles:
            return {
                'profiles_analyzed': 0,
                'average_liquidity_score': 0.0,
                'total_voids_detected': 0,
                'void_clusters': 0
            }
        
        severity_counts = {s: 0 for s in self.severity_thresholds}
        for void in voids:
            severity_counts[void.severity] += 1
        
        return {
            'profiles_analyzed': len(profiles),
            'average_liquidity_score': np.mean([p.liquidity_score for p in profiles]),
            'current_liquidity_score': profiles[-1].liquidity_score,
            'total_voids_detected': len(voids),
            'void_clusters': len(self.get_void_clusters(symbol, exchange)),
            'severity_distribution': severity_counts,
            'average_effective_spread': np.mean([p.effective_spread for p in profiles]),
            'has_recent_critical_voids': any(
                p.largest_bid_void and p.largest_bid_void.severity == 'critical' or
                p.largest_ask_void and p.largest_ask_void.severity == 'critical'
                for p in profiles[-10:]
            )
        }


# Example usage
async def main():
    from order_book_reader import OrderBookSnapshot, OrderBookLevel
    
    # Create sample order book with liquidity voids
    snapshot = OrderBookSnapshot(
        symbol='BTC/USDT',
        exchange='binance',
        bids=[
            OrderBookLevel(50000, 2.5),
            OrderBookLevel(49999, 1.8),
            OrderBookLevel(49998, 3.2),
            # Liquidity void here
            OrderBookLevel(49990, 0.5),  # Big gap
            OrderBookLevel(49989, 1.2),
            OrderBookLevel(49988, 2.0),
            # Another void
            OrderBookLevel(49980, 0.3),  # Another gap
            OrderBookLevel(49979, 1.5),
        ],
        asks=[
            OrderBookLevel(50001, 0.8),
            OrderBookLevel(50002, 0.5),
            # Liquidity void here
            OrderBookLevel(50010, 0.3),  # Big gap
            OrderBookLevel(50011, 0.4),
            OrderBookLevel(50012, 0.2),
        ],
        timestamp=datetime.now().timestamp()
    )
    
    # Create detector
    detector = LiquidityVoidDetector(
        min_gap_percentage=0.0001,
        min_volume_threshold=0.1,
        levels_to_analyze=20
    )
    
    # Analyze liquidity
    profile = detector.analyze_liquidity(snapshot)
    
    print(f"Liquidity Score: {profile.liquidity_score:.2f}/100")
    print(f"Bid voids: {profile.bid_void_count}, Ask voids: {profile.ask_void_count}")
    print(f"Effective spread: {profile.effective_spread:.2f}")
    
    if profile.largest_bid_void:
        print(f"\nLargest bid void: {profile.largest_bid_void.gap_percentage*100:.3f}% "
              f"({profile.largest_bid_void.severity})")
    
    if profile.largest_ask_void:
        print(f"Largest ask void: {profile.largest_ask_void.gap_percentage*100:.3f}% "
              f"({profile.largest_ask_void.severity})")
    
    # Get statistics
    stats = detector.get_statistics('BTC/USDT', 'binance')
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())