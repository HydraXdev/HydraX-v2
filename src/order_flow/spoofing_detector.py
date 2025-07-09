# spoofing_detector.py
# Spoofing Pattern Recognition - Detect Market Manipulation

import numpy as np
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class OrderBookSnapshot:
    """Point-in-time order book state"""
    timestamp: datetime
    bid_levels: List[Tuple[float, float]]  # [(price, size), ...]
    ask_levels: List[Tuple[float, float]]
    mid_price: float
    spread: float

@dataclass
class SpoofingEvent:
    """Detected spoofing activity"""
    timestamp: datetime
    side: str  # 'bid' or 'ask'
    spoofed_price: float
    spoofed_volume: float
    pattern_type: str  # 'layering', 'momentum_ignition', 'flash'
    duration_seconds: float
    price_impact: float  # In pips
    confidence: float
    affected_levels: int
    
class SpoofingDetector:
    """
    SPOOFING DETECTION ENGINE
    
    Identifies market manipulation patterns:
    - Layering: Multiple fake orders to create illusion of demand
    - Momentum ignition: Orders placed and quickly cancelled
    - Quote stuffing: Rapid order placement/cancellation
    - Painting the tape: Artificial activity generation
    """
    
    def __init__(self, symbol: str, tick_size: float = 0.0001):
        self.symbol = symbol
        self.tick_size = tick_size
        
        # Detection parameters
        self.min_spoof_size_ratio = 3.0  # Spoof size vs avg size
        self.cancel_time_threshold = timedelta(seconds=5)  # Quick cancel
        self.min_cancel_rate = 0.8  # 80% cancellation rate
        self.price_impact_threshold = 5  # Pips
        
        # Pattern detection windows
        self.snapshot_interval = timedelta(milliseconds=100)
        self.detection_window = timedelta(seconds=30)
        
        # Data storage
        self.order_book_history = deque(maxlen=1000)
        self.order_lifecycle = defaultdict(dict)  # Track order placement/cancellation
        self.detected_spoofs = deque(maxlen=100)
        
        # Pattern signatures
        self.spoofing_signatures = {
            'layering': self._detect_layering,
            'momentum_ignition': self._detect_momentum_ignition,
            'flash': self._detect_flash_spoofing
        }
        
        # Statistical baselines
        self.baseline_order_sizes = deque(maxlen=1000)
        self.baseline_lifetimes = deque(maxlen=1000)
        
    def update_order_book(self, timestamp: datetime, 
                         bid_levels: List[Tuple[float, float]], 
                         ask_levels: List[Tuple[float, float]]) -> Optional[SpoofingEvent]:
        """
        Update order book and detect spoofing patterns
        
        Args:
            timestamp: Snapshot timestamp
            bid_levels: Bid price/size pairs (sorted descending)
            ask_levels: Ask price/size pairs (sorted ascending)
            
        Returns:
            SpoofingEvent if spoofing detected
        """
        
        # Calculate metrics
        mid_price = (bid_levels[0][0] + ask_levels[0][0]) / 2 if bid_levels and ask_levels else 0
        spread = ask_levels[0][0] - bid_levels[0][0] if bid_levels and ask_levels else 0
        
        # Store snapshot
        snapshot = OrderBookSnapshot(
            timestamp=timestamp,
            bid_levels=bid_levels[:10],  # Top 10 levels
            ask_levels=ask_levels[:10],
            mid_price=mid_price,
            spread=spread
        )
        self.order_book_history.append(snapshot)
        
        # Update baselines
        self._update_baselines(snapshot)
        
        # Check for spoofing patterns
        for pattern_name, detector_func in self.spoofing_signatures.items():
            event = detector_func(snapshot)
            if event:
                self.detected_spoofs.append(event)
                logger.warning(f"Spoofing detected: {event}")
                return event
        
        return None
    
    def track_order_event(self, order_id: str, timestamp: datetime, 
                         event_type: str, price: float, size: float, side: str):
        """
        Track individual order lifecycle events
        
        Args:
            order_id: Unique order identifier
            timestamp: Event timestamp
            event_type: 'placed', 'modified', 'cancelled', 'filled'
            price: Order price
            size: Order size
            side: 'bid' or 'ask'
        """
        
        if event_type == 'placed':
            self.order_lifecycle[order_id] = {
                'placed_at': timestamp,
                'price': price,
                'size': size,
                'side': side,
                'events': [(timestamp, event_type)]
            }
        elif order_id in self.order_lifecycle:
            self.order_lifecycle[order_id]['events'].append((timestamp, event_type))
            
            # Check for suspicious patterns
            if event_type == 'cancelled':
                lifetime = (timestamp - self.order_lifecycle[order_id]['placed_at']).total_seconds()
                if lifetime < self.cancel_time_threshold.total_seconds():
                    # Quick cancellation - potential spoofing
                    self._flag_suspicious_order(order_id)
    
    def _detect_layering(self, snapshot: OrderBookSnapshot) -> Optional[SpoofingEvent]:
        """Detect layering spoofing pattern"""
        
        if len(self.order_book_history) < 10:
            return None
        
        # Analyze each side
        for side, levels in [('bid', snapshot.bid_levels), ('ask', snapshot.ask_levels)]:
            # Look for sudden appearance of large orders
            suspicious_levels = self._find_suspicious_layers(side, levels)
            
            if len(suspicious_levels) >= 3:  # Multiple layers
                # Check if they disappear quickly
                if self._check_layer_cancellation(side, suspicious_levels):
                    return self._create_spoofing_event(
                        snapshot=snapshot,
                        side=side,
                        pattern_type='layering',
                        suspicious_levels=suspicious_levels
                    )
        
        return None
    
    def _detect_momentum_ignition(self, snapshot: OrderBookSnapshot) -> Optional[SpoofingEvent]:
        """Detect momentum ignition pattern"""
        
        if len(self.order_book_history) < 20:
            return None
        
        # Look for large orders that move price then disappear
        recent_snapshots = list(self.order_book_history)[-20:]
        
        # Check bid side
        bid_ignition = self._check_momentum_pattern(recent_snapshots, 'bid')
        if bid_ignition:
            return bid_ignition
        
        # Check ask side
        ask_ignition = self._check_momentum_pattern(recent_snapshots, 'ask')
        if ask_ignition:
            return ask_ignition
        
        return None
    
    def _detect_flash_spoofing(self, snapshot: OrderBookSnapshot) -> Optional[SpoofingEvent]:
        """Detect flash spoofing (very brief order appearance)"""
        
        if len(self.order_book_history) < 5:
            return None
        
        # Look for orders that appear and disappear within milliseconds
        recent = list(self.order_book_history)[-5:]
        
        for side in ['bid', 'ask']:
            flash_orders = self._find_flash_orders(recent, side)
            
            if flash_orders:
                total_volume = sum(order[1] for order in flash_orders)
                avg_baseline = self._get_baseline_order_size()
                
                if total_volume > avg_baseline * self.min_spoof_size_ratio:
                    return SpoofingEvent(
                        timestamp=snapshot.timestamp,
                        side=side,
                        spoofed_price=flash_orders[0][0],
                        spoofed_volume=total_volume,
                        pattern_type='flash',
                        duration_seconds=0.5,  # Flash duration
                        price_impact=0,  # Minimal impact due to brief appearance
                        confidence=0.8,
                        affected_levels=len(flash_orders)
                    )
        
        return None
    
    def _find_suspicious_layers(self, side: str, levels: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Find suspicious layered orders"""
        
        suspicious = []
        avg_size = self._get_baseline_order_size()
        
        for price, size in levels[1:6]:  # Skip best level, check next 5
            if size > avg_size * self.min_spoof_size_ratio:
                # Check if this is new or significantly increased
                if self._is_new_large_order(side, price, size):
                    suspicious.append((price, size))
        
        return suspicious
    
    def _check_layer_cancellation(self, side: str, layers: List[Tuple[float, float]]) -> bool:
        """Check if layered orders are quickly cancelled"""
        
        # This would require order-level tracking in production
        # For now, check if similar large orders disappeared
        
        if len(self.order_book_history) < 50:
            return False
        
        # Look ahead in history (simulating real-time detection with delay)
        future_snapshots = list(self.order_book_history)[-10:]
        
        for snapshot in future_snapshots:
            levels = snapshot.bid_levels if side == 'bid' else snapshot.ask_levels
            
            # Check if large orders are gone
            remaining_large = 0
            for price, size in levels:
                for layer_price, layer_size in layers:
                    if abs(price - layer_price) < self.tick_size:
                        if size > layer_size * 0.5:  # Still substantial
                            remaining_large += 1
            
            if remaining_large < len(layers) * 0.3:  # Most disappeared
                return True
        
        return False
    
    def _check_momentum_pattern(self, snapshots: List[OrderBookSnapshot], side: str) -> Optional[SpoofingEvent]:
        """Check for momentum ignition pattern"""
        
        # Find large order appearance
        for i in range(5, len(snapshots) - 5):
            snapshot = snapshots[i]
            levels = snapshot.bid_levels if side == 'bid' else snapshot.ask_levels
            
            # Look for unusually large order
            if levels:
                top_size = levels[0][1]
                avg_size = self._get_baseline_order_size()
                
                if top_size > avg_size * self.min_spoof_size_ratio * 2:
                    # Check price movement
                    prev_mid = snapshots[i-5].mid_price
                    next_mid = snapshots[i+5].mid_price
                    
                    price_move = (next_mid - prev_mid) / self.tick_size
                    
                    if abs(price_move) > self.price_impact_threshold:
                        # Check if order disappeared
                        later_levels = snapshots[i+5].bid_levels if side == 'bid' else snapshots[i+5].ask_levels
                        
                        if not any(s > top_size * 0.5 for _, s in later_levels[:3]):
                            return SpoofingEvent(
                                timestamp=snapshot.timestamp,
                                side=side,
                                spoofed_price=levels[0][0],
                                spoofed_volume=top_size,
                                pattern_type='momentum_ignition',
                                duration_seconds=1.0,
                                price_impact=abs(price_move),
                                confidence=0.85,
                                affected_levels=1
                            )
        
        return None
    
    def _find_flash_orders(self, snapshots: List[OrderBookSnapshot], side: str) -> List[Tuple[float, float]]:
        """Find orders that appear and disappear quickly"""
        
        flash_orders = []
        
        # Compare consecutive snapshots
        for i in range(1, len(snapshots) - 1):
            prev_levels = snapshots[i-1].bid_levels if side == 'bid' else snapshots[i-1].ask_levels
            curr_levels = snapshots[i].bid_levels if side == 'bid' else snapshots[i].ask_levels
            next_levels = snapshots[i+1].bid_levels if side == 'bid' else snapshots[i+1].ask_levels
            
            # Find orders that appear in curr but not in prev or next
            curr_dict = {price: size for price, size in curr_levels}
            prev_dict = {price: size for price, size in prev_levels}
            next_dict = {price: size for price, size in next_levels}
            
            for price, size in curr_levels:
                if price not in prev_dict and price not in next_dict:
                    # Flash order detected
                    flash_orders.append((price, size))
        
        return flash_orders
    
    def _is_new_large_order(self, side: str, price: float, size: float) -> bool:
        """Check if this is a new large order"""
        
        if len(self.order_book_history) < 2:
            return True
        
        prev_snapshot = self.order_book_history[-2]
        prev_levels = prev_snapshot.bid_levels if side == 'bid' else prev_snapshot.ask_levels
        
        for prev_price, prev_size in prev_levels:
            if abs(prev_price - price) < self.tick_size:
                # Found same level - check if size increased significantly
                return size > prev_size * 2
        
        # New level
        return True
    
    def _create_spoofing_event(self, snapshot: OrderBookSnapshot, side: str, 
                              pattern_type: str, suspicious_levels: List[Tuple[float, float]]) -> SpoofingEvent:
        """Create spoofing event from detection"""
        
        total_volume = sum(size for _, size in suspicious_levels)
        spoofed_price = suspicious_levels[0][0] if suspicious_levels else 0
        
        # Estimate price impact
        price_impact = self._estimate_price_impact(snapshot, side, total_volume)
        
        # Calculate confidence based on pattern strength
        confidence = self._calculate_spoofing_confidence(pattern_type, suspicious_levels)
        
        return SpoofingEvent(
            timestamp=snapshot.timestamp,
            side=side,
            spoofed_price=spoofed_price,
            spoofed_volume=total_volume,
            pattern_type=pattern_type,
            duration_seconds=2.0,  # Estimated
            price_impact=price_impact,
            confidence=confidence,
            affected_levels=len(suspicious_levels)
        )
    
    def _estimate_price_impact(self, snapshot: OrderBookSnapshot, side: str, volume: float) -> float:
        """Estimate potential price impact of spoofed orders"""
        
        # Simple estimation based on order book imbalance
        total_bid_volume = sum(size for _, size in snapshot.bid_levels[:5])
        total_ask_volume = sum(size for _, size in snapshot.ask_levels[:5])
        
        if side == 'bid':
            imbalance = (total_bid_volume + volume) / total_ask_volume if total_ask_volume > 0 else 2.0
        else:
            imbalance = total_bid_volume / (total_ask_volume + volume) if total_ask_volume + volume > 0 else 0.5
        
        # Convert imbalance to estimated pip impact
        if imbalance > 2.0:
            return 10.0
        elif imbalance > 1.5:
            return 5.0
        elif imbalance < 0.5:
            return -10.0
        elif imbalance < 0.75:
            return -5.0
        else:
            return 0.0
    
    def _calculate_spoofing_confidence(self, pattern_type: str, 
                                     suspicious_levels: List[Tuple[float, float]]) -> float:
        """Calculate confidence score for spoofing detection"""
        
        base_confidence = {
            'layering': 0.7,
            'momentum_ignition': 0.8,
            'flash': 0.75
        }.get(pattern_type, 0.5)
        
        # Adjust based on evidence strength
        if len(suspicious_levels) > 5:
            base_confidence += 0.15
        elif len(suspicious_levels) > 3:
            base_confidence += 0.1
        
        # Size relative to baseline
        avg_baseline = self._get_baseline_order_size()
        avg_suspicious = np.mean([size for _, size in suspicious_levels])
        
        if avg_suspicious > avg_baseline * 5:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    def _update_baselines(self, snapshot: OrderBookSnapshot):
        """Update statistical baselines"""
        
        # Collect all order sizes
        all_sizes = []
        for _, size in snapshot.bid_levels:
            all_sizes.append(size)
        for _, size in snapshot.ask_levels:
            all_sizes.append(size)
        
        if all_sizes:
            self.baseline_order_sizes.extend(all_sizes)
    
    def _get_baseline_order_size(self) -> float:
        """Get baseline average order size"""
        
        if not self.baseline_order_sizes:
            return 1000.0  # Default
        
        return np.median(list(self.baseline_order_sizes))
    
    def _flag_suspicious_order(self, order_id: str):
        """Flag order as potentially suspicious"""
        
        if order_id in self.order_lifecycle:
            self.order_lifecycle[order_id]['suspicious'] = True
            logger.info(f"Flagged suspicious order: {order_id}")
    
    def get_recent_spoofing_events(self, minutes: int = 5) -> List[SpoofingEvent]:
        """Get recent spoofing events"""
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [e for e in self.detected_spoofs if e.timestamp >= cutoff_time]
    
    def get_spoofing_statistics(self) -> Dict[str, Any]:
        """Get spoofing detection statistics"""
        
        if not self.detected_spoofs:
            return {
                'total_events': 0,
                'events_by_type': {},
                'avg_confidence': 0,
                'avg_price_impact': 0
            }
        
        events = list(self.detected_spoofs)
        
        # Count by type
        type_counts = defaultdict(int)
        for event in events:
            type_counts[event.pattern_type] += 1
        
        return {
            'total_events': len(events),
            'events_by_type': dict(type_counts),
            'avg_confidence': np.mean([e.confidence for e in events]),
            'avg_price_impact': np.mean([abs(e.price_impact) for e in events]),
            'bid_events': len([e for e in events if e.side == 'bid']),
            'ask_events': len([e for e in events if e.side == 'ask'])
        }