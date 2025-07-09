# hidden_liquidity_scanner.py
# Hidden Liquidity Scanner - Detect Dark Pools and Hidden Orders

import numpy as np
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class HiddenLiquiditySignal:
    """Detected hidden liquidity presence"""
    timestamp: datetime
    price_level: float
    side: str  # 'bid' or 'ask'
    estimated_size: float
    liquidity_type: str  # 'dark_pool', 'reserve_order', 'hidden_iceberg'
    detection_method: str  # How it was detected
    confidence: float
    evidence: Dict[str, Any]

@dataclass
class ExecutionAnomaly:
    """Anomalous execution indicating hidden liquidity"""
    timestamp: datetime
    price: float
    displayed_size: float
    executed_size: float
    size_ratio: float  # Executed/displayed
    subsequent_refills: int

class HiddenLiquidityScanner:
    """
    HIDDEN LIQUIDITY DETECTION ENGINE
    
    Identifies non-displayed liquidity:
    - Dark pool presence
    - Reserve/hidden orders
    - Iceberg order hidden portions
    - Pegged orders
    - Institutional hiding strategies
    """
    
    def __init__(self, symbol: str, tick_size: float = 0.0001):
        self.symbol = symbol
        self.tick_size = tick_size
        
        # Detection parameters
        self.min_execution_ratio = 2.0  # Executed > 2x displayed
        self.refill_time_threshold = timedelta(seconds=1)
        self.price_improvement_threshold = 0.5  # Pips
        
        # Data storage
        self.order_book_snapshots = deque(maxlen=1000)
        self.executions = deque(maxlen=10000)
        self.detected_liquidity = deque(maxlen=100)
        
        # Pattern tracking
        self.execution_anomalies = deque(maxlen=1000)
        self.price_improvement_events = deque(maxlen=1000)
        self.refill_patterns = defaultdict(list)
        
        # Statistical baselines
        self.typical_execution_sizes = deque(maxlen=1000)
        self.typical_book_depths = deque(maxlen=100)
        
    def analyze_execution(self, timestamp: datetime, price: float,
                         executed_size: float, displayed_liquidity: Dict[float, float],
                         side: str) -> Optional[HiddenLiquiditySignal]:
        """
        Analyze trade execution for hidden liquidity
        
        Args:
            timestamp: Execution timestamp
            price: Execution price
            executed_size: Total executed size
            displayed_liquidity: Visible order book at time of execution
            side: 'buy' or 'sell' execution
            
        Returns:
            HiddenLiquiditySignal if hidden liquidity detected
        """
        
        # Store execution
        self.executions.append({
            'timestamp': timestamp,
            'price': price,
            'size': executed_size,
            'side': side,
            'displayed': displayed_liquidity.copy()
        })
        
        # Update baselines
        self.typical_execution_sizes.append(executed_size)
        
        # Check for hidden liquidity indicators
        signal = self._detect_hidden_liquidity(
            timestamp, price, executed_size, displayed_liquidity, side
        )
        
        if signal:
            self.detected_liquidity.append(signal)
            logger.info(f"Hidden liquidity detected: {signal}")
            
        return signal
    
    def update_order_book(self, timestamp: datetime,
                         bid_book: Dict[float, float],
                         ask_book: Dict[float, float]):
        """Update order book snapshot for analysis"""
        
        snapshot = {
            'timestamp': timestamp,
            'bids': bid_book.copy(),
            'asks': ask_book.copy(),
            'total_bid_depth': sum(bid_book.values()),
            'total_ask_depth': sum(ask_book.values())
        }
        
        self.order_book_snapshots.append(snapshot)
        self.typical_book_depths.append(
            (snapshot['total_bid_depth'] + snapshot['total_ask_depth']) / 2
        )
        
        # Check for refill patterns
        self._check_refill_patterns(timestamp)
    
    def _detect_hidden_liquidity(self, timestamp: datetime, price: float,
                                executed_size: float, displayed_liquidity: Dict[float, float],
                                side: str) -> Optional[HiddenLiquiditySignal]:
        """Main hidden liquidity detection logic"""
        
        # Method 1: Execution exceeds displayed size
        excess_execution = self._check_excess_execution(
            price, executed_size, displayed_liquidity, side
        )
        if excess_execution:
            return excess_execution
        
        # Method 2: Price improvement detection
        price_improvement = self._check_price_improvement(
            timestamp, price, executed_size, side
        )
        if price_improvement:
            return price_improvement
        
        # Method 3: Rapid refill pattern
        refill_signal = self._check_refill_behavior(
            timestamp, price, side
        )
        if refill_signal:
            return refill_signal
        
        # Method 4: Dark pool signature
        dark_pool = self._check_dark_pool_signature(
            timestamp, price, executed_size, side
        )
        if dark_pool:
            return dark_pool
        
        return None
    
    def _check_excess_execution(self, price: float, executed_size: float,
                               displayed_liquidity: Dict[float, float],
                               side: str) -> Optional[HiddenLiquiditySignal]:
        """Check if execution exceeds displayed liquidity"""
        
        # Calculate displayed size at execution price
        displayed_at_price = displayed_liquidity.get(price, 0)
        
        # Also check nearby prices (price improvement)
        nearby_displayed = 0
        for level_price, level_size in displayed_liquidity.items():
            if side == 'buy' and level_price <= price:
                nearby_displayed += level_size
            elif side == 'sell' and level_price >= price:
                nearby_displayed += level_size
        
        # Check for significant excess
        if executed_size > max(displayed_at_price, nearby_displayed) * self.min_execution_ratio:
            
            # Create anomaly record
            anomaly = ExecutionAnomaly(
                timestamp=datetime.now(),
                price=price,
                displayed_size=displayed_at_price,
                executed_size=executed_size,
                size_ratio=executed_size / displayed_at_price if displayed_at_price > 0 else float('inf'),
                subsequent_refills=0
            )
            self.execution_anomalies.append(anomaly)
            
            # Estimate hidden size
            hidden_size = executed_size - nearby_displayed
            
            return HiddenLiquiditySignal(
                timestamp=datetime.now(),
                price_level=price,
                side='bid' if side == 'buy' else 'ask',
                estimated_size=hidden_size,
                liquidity_type='reserve_order',
                detection_method='excess_execution',
                confidence=min(0.9, executed_size / (displayed_at_price + 1)),
                evidence={
                    'displayed_size': displayed_at_price,
                    'executed_size': executed_size,
                    'size_ratio': anomaly.size_ratio
                }
            )
        
        return None
    
    def _check_price_improvement(self, timestamp: datetime, price: float,
                               executed_size: float, side: str) -> Optional[HiddenLiquiditySignal]:
        """Check for price improvement indicating hidden liquidity"""
        
        if len(self.order_book_snapshots) < 2:
            return None
        
        # Get order book before execution
        recent_snapshot = self.order_book_snapshots[-1]
        
        # Check for price improvement
        if side == 'buy':
            best_ask = min(recent_snapshot['asks'].keys()) if recent_snapshot['asks'] else price
            improvement = best_ask - price
        else:
            best_bid = max(recent_snapshot['bids'].keys()) if recent_snapshot['bids'] else price
            improvement = price - best_bid
        
        improvement_pips = improvement / self.tick_size
        
        if improvement_pips >= self.price_improvement_threshold:
            # Price improvement detected
            self.price_improvement_events.append({
                'timestamp': timestamp,
                'price': price,
                'improvement_pips': improvement_pips,
                'size': executed_size,
                'side': side
            })
            
            return HiddenLiquiditySignal(
                timestamp=timestamp,
                price_level=price,
                side='bid' if side == 'sell' else 'ask',  # Opposite side provided liquidity
                estimated_size=executed_size,
                liquidity_type='dark_pool',
                detection_method='price_improvement',
                confidence=min(0.85, improvement_pips / 5),  # Higher improvement = higher confidence
                evidence={
                    'improvement_pips': improvement_pips,
                    'execution_price': price,
                    'best_visible_price': best_ask if side == 'buy' else best_bid
                }
            )
        
        return None
    
    def _check_refill_behavior(self, timestamp: datetime, price: float,
                             side: str) -> Optional[HiddenLiquiditySignal]:
        """Check for rapid refill behavior indicating hidden orders"""
        
        price_key = round(price / self.tick_size) * self.tick_size
        
        # Look for recent executions at this level
        recent_executions = [e for e in self.executions
                           if abs(e['price'] - price) < self.tick_size
                           and e['timestamp'] >= timestamp - timedelta(seconds=5)]
        
        if len(recent_executions) >= 3:  # Multiple executions at same level
            # Check refill pattern
            refill_count = 0
            total_executed = sum(e['size'] for e in recent_executions)
            
            # Look for order book refills after executions
            for i, execution in enumerate(recent_executions[:-1]):
                next_execution = recent_executions[i + 1]
                time_gap = (next_execution['timestamp'] - execution['timestamp'])
                
                if time_gap <= self.refill_time_threshold:
                    refill_count += 1
            
            if refill_count >= 2:  # Multiple rapid refills
                return HiddenLiquiditySignal(
                    timestamp=timestamp,
                    price_level=price,
                    side='bid' if side == 'buy' else 'ask',
                    estimated_size=total_executed * 2,  # Estimate based on refill pattern
                    liquidity_type='hidden_iceberg',
                    detection_method='refill_pattern',
                    confidence=min(0.8, refill_count / len(recent_executions)),
                    evidence={
                        'execution_count': len(recent_executions),
                        'refill_count': refill_count,
                        'total_executed': total_executed,
                        'avg_refill_time_ms': np.mean([
                            (recent_executions[i+1]['timestamp'] - e['timestamp']).total_seconds() * 1000
                            for i, e in enumerate(recent_executions[:-1])
                        ])
                    }
                )
        
        return None
    
    def _check_dark_pool_signature(self, timestamp: datetime, price: float,
                                  executed_size: float, side: str) -> Optional[HiddenLiquiditySignal]:
        """Check for dark pool execution signatures"""
        
        # Dark pool indicators:
        # 1. Large size relative to typical
        # 2. Round lot sizes
        # 3. Execution at midpoint
        # 4. No immediate market impact
        
        # Check size
        if not self.typical_execution_sizes:
            return None
        
        avg_size = np.mean(list(self.typical_execution_sizes))
        if executed_size < avg_size * 3:  # Not large enough
            return None
        
        # Check for round lot
        is_round_lot = executed_size % 100 == 0 or executed_size % 1000 == 0
        
        # Check if at midpoint
        if self.order_book_snapshots:
            snapshot = self.order_book_snapshots[-1]
            if snapshot['bids'] and snapshot['asks']:
                best_bid = max(snapshot['bids'].keys())
                best_ask = min(snapshot['asks'].keys())
                midpoint = (best_bid + best_ask) / 2
                
                is_midpoint = abs(price - midpoint) < self.tick_size
            else:
                is_midpoint = False
        else:
            is_midpoint = False
        
        # Calculate confidence
        confidence = 0.5
        if is_round_lot:
            confidence += 0.2
        if is_midpoint:
            confidence += 0.2
        if executed_size > avg_size * 5:
            confidence += 0.1
        
        if confidence >= 0.7:
            return HiddenLiquiditySignal(
                timestamp=timestamp,
                price_level=price,
                side='bid' if side == 'sell' else 'ask',
                estimated_size=executed_size,
                liquidity_type='dark_pool',
                detection_method='dark_pool_signature',
                confidence=confidence,
                evidence={
                    'size_vs_average': executed_size / avg_size,
                    'is_round_lot': is_round_lot,
                    'is_midpoint': is_midpoint,
                    'execution_size': executed_size
                }
            )
        
        return None
    
    def _check_refill_patterns(self, timestamp: datetime):
        """Check order book for refill patterns"""
        
        if len(self.order_book_snapshots) < 2:
            return
        
        current_book = self.order_book_snapshots[-1]
        previous_book = self.order_book_snapshots[-2]
        
        # Check each price level for rapid refills
        for side_key, side_name in [('bids', 'bid'), ('asks', 'ask')]:
            current_levels = current_book[side_key]
            previous_levels = previous_book[side_key]
            
            for price, current_size in current_levels.items():
                previous_size = previous_levels.get(price, 0)
                
                # Check if level was depleted and refilled
                if previous_size < current_size * 0.3:  # Was mostly depleted
                    if current_size > self._get_typical_level_size() * 0.8:  # Now refilled
                        # Record refill event
                        self.refill_patterns[price].append({
                            'timestamp': timestamp,
                            'side': side_name,
                            'previous_size': previous_size,
                            'current_size': current_size,
                            'refill_ratio': current_size / (previous_size + 1)
                        })
    
    def _get_typical_level_size(self) -> float:
        """Get typical order book level size"""
        
        if not self.order_book_snapshots:
            return 1000.0
        
        all_sizes = []
        for snapshot in list(self.order_book_snapshots)[-10:]:
            all_sizes.extend(snapshot['bids'].values())
            all_sizes.extend(snapshot['asks'].values())
        
        return np.median(all_sizes) if all_sizes else 1000.0
    
    def get_hidden_liquidity_map(self) -> Dict[str, Dict[float, float]]:
        """Get map of detected hidden liquidity by price level"""
        
        liquidity_map = {
            'bid': defaultdict(float),
            'ask': defaultdict(float)
        }
        
        # Aggregate recent detections
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_signals = [s for s in self.detected_liquidity
                         if s.timestamp >= cutoff_time]
        
        for signal in recent_signals:
            side = signal.side
            price = signal.price_level
            
            # Weight by confidence
            weighted_size = signal.estimated_size * signal.confidence
            liquidity_map[side][price] += weighted_size
        
        return {
            'bid': dict(liquidity_map['bid']),
            'ask': dict(liquidity_map['ask'])
        }
    
    def get_dark_pool_probability(self, price_range: Tuple[float, float]) -> float:
        """Estimate probability of dark pool presence in price range"""
        
        dark_pool_signals = [s for s in self.detected_liquidity
                           if s.liquidity_type == 'dark_pool'
                           and price_range[0] <= s.price_level <= price_range[1]]
        
        if not dark_pool_signals:
            return 0.0
        
        # Weight by recency and confidence
        now = datetime.now()
        weighted_sum = 0.0
        weight_total = 0.0
        
        for signal in dark_pool_signals:
            age_minutes = (now - signal.timestamp).total_seconds() / 60
            recency_weight = np.exp(-age_minutes / 30)  # 30-minute half-life
            
            signal_weight = signal.confidence * recency_weight
            weighted_sum += signal_weight
            weight_total += recency_weight
        
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    def get_hidden_liquidity_summary(self) -> Dict[str, Any]:
        """Get summary of hidden liquidity detection"""
        
        if not self.detected_liquidity:
            return {
                'total_detections': 0,
                'liquidity_types': {},
                'detection_methods': {},
                'estimated_hidden_volume': 0
            }
        
        recent_signals = list(self.detected_liquidity)[-50:]  # Last 50 detections
        
        # Count by type and method
        type_counts = defaultdict(int)
        method_counts = defaultdict(int)
        total_hidden_volume = 0
        
        for signal in recent_signals:
            type_counts[signal.liquidity_type] += 1
            method_counts[signal.detection_method] += 1
            total_hidden_volume += signal.estimated_size
        
        # Price improvement statistics
        recent_improvements = list(self.price_improvement_events)[-20:]
        avg_improvement = np.mean([e['improvement_pips'] for e in recent_improvements]) if recent_improvements else 0
        
        return {
            'total_detections': len(recent_signals),
            'liquidity_types': dict(type_counts),
            'detection_methods': dict(method_counts),
            'estimated_hidden_volume': total_hidden_volume,
            'avg_confidence': np.mean([s.confidence for s in recent_signals]),
            'price_improvement_events': len(self.price_improvement_events),
            'avg_price_improvement_pips': avg_improvement,
            'most_common_type': max(type_counts, key=type_counts.get) if type_counts else None
        }