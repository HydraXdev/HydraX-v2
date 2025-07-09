# iceberg_detector.py
# Iceberg Order Detection Algorithm - Uncover Hidden Institutional Volume

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class IcebergSignal:
    """Detected iceberg order characteristics"""
    timestamp: datetime
    price_level: float
    side: str  # 'buy' or 'sell'
    total_volume: float
    slice_count: int
    average_slice_size: float
    confidence: float  # 0-1
    pattern_type: str  # 'classic', 'adaptive', 'aggressive'
    institutional_probability: float

@dataclass
class VolumeSlice:
    """Individual volume slice data"""
    timestamp: datetime
    price: float
    volume: float
    side: str
    spread: float
    
class IcebergDetector:
    """
    ICEBERG ORDER DETECTION ENGINE
    
    Identifies hidden institutional orders by analyzing:
    - Repetitive volume patterns at specific price levels
    - Consistent order slice sizes
    - Price absorption without movement
    - Reload patterns after partial fills
    """
    
    def __init__(self, symbol: str, tick_size: float = 0.0001):
        self.symbol = symbol
        self.tick_size = tick_size
        
        # Detection parameters
        self.min_slices = 3  # Minimum slices to qualify as iceberg
        self.slice_similarity_threshold = 0.8  # 80% similarity in sizes
        self.price_cluster_pips = 2  # Price clustering tolerance
        self.time_window = timedelta(minutes=30)  # Detection window
        
        # Pattern recognition
        self.volume_percentiles = {
            'small': 0.25,
            'medium': 0.50,
            'large': 0.75,
            'huge': 0.95
        }
        
        # Rolling data storage
        self.order_flow = deque(maxlen=10000)
        self.detected_icebergs = deque(maxlen=100)
        self.price_levels = {}  # Track volume at each level
        
        # Institutional footprint patterns
        self.institutional_patterns = {
            'round_numbers': True,  # Orders at round price levels
            'consistent_sizing': True,  # Similar slice sizes
            'patient_execution': True,  # Spread across time
            'price_absorption': True  # Volume without price movement
        }
        
    def update_order_flow(self, timestamp: datetime, price: float, 
                         volume: float, side: str, spread: float) -> Optional[IcebergSignal]:
        """
        Update order flow and detect iceberg patterns
        
        Args:
            timestamp: Trade timestamp
            price: Execution price
            volume: Trade volume
            side: 'buy' or 'sell'
            spread: Current bid-ask spread
            
        Returns:
            IcebergSignal if pattern detected, None otherwise
        """
        
        # Store volume slice
        slice_data = VolumeSlice(timestamp, price, volume, side, spread)
        self.order_flow.append(slice_data)
        
        # Update price level tracking
        price_key = self._normalize_price(price)
        if price_key not in self.price_levels:
            self.price_levels[price_key] = deque(maxlen=100)
        self.price_levels[price_key].append(slice_data)
        
        # Check for iceberg patterns
        signal = self._detect_iceberg_pattern(price_key)
        
        if signal:
            self.detected_icebergs.append(signal)
            logger.info(f"Iceberg detected: {signal}")
            
        return signal
    
    def _detect_iceberg_pattern(self, price_key: float) -> Optional[IcebergSignal]:
        """Detect iceberg order pattern at specific price level"""
        
        if price_key not in self.price_levels:
            return None
            
        slices = list(self.price_levels[price_key])
        
        # Need minimum slices
        if len(slices) < self.min_slices:
            return None
            
        # Time window filter
        recent_slices = self._filter_by_time_window(slices)
        if len(recent_slices) < self.min_slices:
            return None
            
        # Analyze pattern characteristics
        pattern_metrics = self._analyze_slice_pattern(recent_slices)
        
        # Check if pattern qualifies as iceberg
        if self._is_iceberg_pattern(pattern_metrics):
            return self._create_iceberg_signal(recent_slices, pattern_metrics)
            
        return None
    
    def _analyze_slice_pattern(self, slices: List[VolumeSlice]) -> Dict[str, Any]:
        """Analyze volume slice pattern for iceberg characteristics"""
        
        volumes = [s.volume for s in slices]
        timestamps = [s.timestamp for s in slices]
        sides = [s.side for s in slices]
        
        # Volume analysis
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        cv_volume = std_volume / avg_volume if avg_volume > 0 else float('inf')
        
        # Time distribution
        time_gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i-1]).total_seconds()
            time_gaps.append(gap)
        
        avg_time_gap = np.mean(time_gaps) if time_gaps else 0
        std_time_gap = np.std(time_gaps) if time_gaps else 0
        
        # Side consistency
        dominant_side = max(set(sides), key=sides.count)
        side_consistency = sides.count(dominant_side) / len(sides)
        
        # Round number detection
        price = slices[0].price
        is_round_number = self._is_round_number(price)
        
        # Price movement during execution
        first_price = slices[0].price
        last_price = slices[-1].price
        price_drift = abs(last_price - first_price) / self.tick_size
        
        return {
            'slice_count': len(slices),
            'avg_volume': avg_volume,
            'volume_cv': cv_volume,
            'avg_time_gap': avg_time_gap,
            'time_cv': std_time_gap / avg_time_gap if avg_time_gap > 0 else float('inf'),
            'dominant_side': dominant_side,
            'side_consistency': side_consistency,
            'is_round_number': is_round_number,
            'price_drift_pips': price_drift,
            'total_volume': sum(volumes),
            'execution_duration': (timestamps[-1] - timestamps[0]).total_seconds()
        }
    
    def _is_iceberg_pattern(self, metrics: Dict[str, Any]) -> bool:
        """Determine if pattern qualifies as iceberg order"""
        
        # Classic iceberg: consistent slice sizes
        if metrics['volume_cv'] < 0.3:  # Low coefficient of variation
            if metrics['side_consistency'] > 0.8:  # Same side
                if metrics['price_drift_pips'] < 5:  # Minimal price movement
                    return True
        
        # Adaptive iceberg: varying sizes but consistent timing
        if metrics['time_cv'] < 0.5:  # Regular time intervals
            if metrics['side_consistency'] > 0.9:
                if metrics['total_volume'] > self._get_large_volume_threshold():
                    return True
        
        # Institutional pattern: round numbers with absorption
        if metrics['is_round_number']:
            if metrics['price_drift_pips'] < 3:
                if metrics['slice_count'] >= 5:
                    return True
        
        return False
    
    def _create_iceberg_signal(self, slices: List[VolumeSlice], 
                              metrics: Dict[str, Any]) -> IcebergSignal:
        """Create iceberg detection signal"""
        
        # Determine pattern type
        if metrics['volume_cv'] < 0.3:
            pattern_type = 'classic'
        elif metrics['time_cv'] < 0.5:
            pattern_type = 'adaptive'
        else:
            pattern_type = 'aggressive'
        
        # Calculate confidence
        confidence = self._calculate_confidence(metrics)
        
        # Institutional probability
        inst_prob = self._calculate_institutional_probability(metrics)
        
        return IcebergSignal(
            timestamp=slices[-1].timestamp,
            price_level=slices[0].price,
            side=metrics['dominant_side'],
            total_volume=metrics['total_volume'],
            slice_count=metrics['slice_count'],
            average_slice_size=metrics['avg_volume'],
            confidence=confidence,
            pattern_type=pattern_type,
            institutional_probability=inst_prob
        )
    
    def _calculate_confidence(self, metrics: Dict[str, Any]) -> float:
        """Calculate detection confidence score"""
        
        confidence = 0.0
        
        # Volume consistency
        if metrics['volume_cv'] < 0.2:
            confidence += 0.3
        elif metrics['volume_cv'] < 0.4:
            confidence += 0.2
        
        # Side consistency
        confidence += metrics['side_consistency'] * 0.2
        
        # Price absorption
        if metrics['price_drift_pips'] < 2:
            confidence += 0.2
        elif metrics['price_drift_pips'] < 5:
            confidence += 0.1
        
        # Slice count
        if metrics['slice_count'] >= 10:
            confidence += 0.2
        elif metrics['slice_count'] >= 5:
            confidence += 0.1
        
        # Round number bonus
        if metrics['is_round_number']:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_institutional_probability(self, metrics: Dict[str, Any]) -> float:
        """Calculate probability of institutional origin"""
        
        score = 0.0
        
        # Large total volume
        if metrics['total_volume'] > self._get_huge_volume_threshold():
            score += 0.3
        elif metrics['total_volume'] > self._get_large_volume_threshold():
            score += 0.2
        
        # Patient execution
        if metrics['execution_duration'] > 300:  # > 5 minutes
            score += 0.2
        
        # Round number preference
        if metrics['is_round_number']:
            score += 0.15
        
        # Consistent sizing (algo execution)
        if metrics['volume_cv'] < 0.25:
            score += 0.2
        
        # Price absorption
        if metrics['price_drift_pips'] < 3:
            score += 0.15
        
        return min(1.0, score)
    
    def _normalize_price(self, price: float) -> float:
        """Normalize price to cluster level"""
        
        cluster_size = self.price_cluster_pips * self.tick_size
        return round(price / cluster_size) * cluster_size
    
    def _filter_by_time_window(self, slices: List[VolumeSlice]) -> List[VolumeSlice]:
        """Filter slices within time window"""
        
        if not slices:
            return []
        
        cutoff_time = slices[-1].timestamp - self.time_window
        return [s for s in slices if s.timestamp >= cutoff_time]
    
    def _is_round_number(self, price: float) -> bool:
        """Check if price is at round number level"""
        
        # Check for .00, .50 levels
        price_str = f"{price:.5f}"
        decimals = price_str.split('.')[-1]
        
        return decimals.endswith('000') or decimals.endswith('500')
    
    def _get_large_volume_threshold(self) -> float:
        """Get large volume threshold based on recent flow"""
        
        if len(self.order_flow) < 100:
            return 10000  # Default
        
        volumes = [s.volume for s in list(self.order_flow)[-1000:]]
        return np.percentile(volumes, 75)
    
    def _get_huge_volume_threshold(self) -> float:
        """Get huge volume threshold"""
        
        if len(self.order_flow) < 100:
            return 50000  # Default
        
        volumes = [s.volume for s in list(self.order_flow)[-1000:]]
        return np.percentile(volumes, 95)
    
    def get_active_icebergs(self) -> List[IcebergSignal]:
        """Get currently active iceberg orders"""
        
        if not self.detected_icebergs:
            return []
        
        # Filter recent detections
        cutoff_time = datetime.now() - timedelta(minutes=15)
        active = [i for i in self.detected_icebergs if i.timestamp >= cutoff_time]
        
        # Sort by confidence
        return sorted(active, key=lambda x: x.confidence, reverse=True)
    
    def get_iceberg_levels(self, side: Optional[str] = None) -> Dict[float, float]:
        """Get price levels with iceberg activity"""
        
        levels = {}
        
        for iceberg in self.get_active_icebergs():
            if side and iceberg.side != side:
                continue
                
            price = iceberg.price_level
            if price not in levels:
                levels[price] = 0
            levels[price] += iceberg.total_volume
        
        return dict(sorted(levels.items()))