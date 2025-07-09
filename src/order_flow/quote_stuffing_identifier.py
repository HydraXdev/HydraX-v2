# quote_stuffing_identifier.py
# Quote Stuffing Detection - Identify Market Manipulation via Order Spam

import numpy as np
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class QuoteStuffingEvent:
    """Detected quote stuffing incident"""
    timestamp: datetime
    start_time: datetime
    end_time: datetime
    duration_ms: float
    message_count: int
    peak_rate: float  # Messages per second
    affected_levels: int
    target_side: str  # 'bid', 'ask', or 'both'
    pattern_type: str  # 'burst', 'sustained', 'oscillating'
    severity: str  # 'low', 'medium', 'high', 'extreme'
    market_impact: Dict[str, float]

@dataclass
class QuoteMessage:
    """Individual quote update message"""
    timestamp: datetime
    message_id: str
    action: str  # 'add', 'modify', 'cancel'
    price: float
    size: float
    side: str

class QuoteStuffingIdentifier:
    """
    QUOTE STUFFING IDENTIFICATION ENGINE
    
    Detects market manipulation through excessive quote traffic:
    - Rapid order placement and cancellation
    - System overload attempts
    - Latency creation for competitive advantage
    - Market confusion tactics
    """
    
    def __init__(self, symbol: str, tick_size: float = 0.0001):
        self.symbol = symbol
        self.tick_size = tick_size
        
        # Detection thresholds
        self.burst_threshold = 100  # Messages per second
        self.sustained_threshold = 50  # Sustained rate
        self.burst_duration = timedelta(milliseconds=100)
        self.sustained_duration = timedelta(seconds=1)
        
        # Severity thresholds
        self.severity_levels = {
            'low': {'rate': 50, 'duration': 500},
            'medium': {'rate': 100, 'duration': 1000},
            'high': {'rate': 200, 'duration': 2000},
            'extreme': {'rate': 500, 'duration': 5000}
        }
        
        # Message tracking
        self.message_stream = deque(maxlen=100000)
        self.active_quotes = {}  # Track live quotes
        self.stuffing_events = deque(maxlen=100)
        
        # Pattern detection
        self.detection_window = timedelta(seconds=5)
        self.message_rate_history = deque(maxlen=300)  # 5 minutes
        
        # Market impact tracking
        self.pre_stuffing_state = None
        self.impact_metrics = defaultdict(list)
        
    def process_quote_message(self, timestamp: datetime, message_id: str,
                            action: str, price: float, size: float, 
                            side: str) -> Optional[QuoteStuffingEvent]:
        """
        Process incoming quote message
        
        Args:
            timestamp: Message timestamp (microsecond precision)
            message_id: Unique message identifier
            action: Type of quote action
            price: Quote price
            size: Quote size
            side: 'bid' or 'ask'
            
        Returns:
            QuoteStuffingEvent if stuffing detected
        """
        
        # Store message
        message = QuoteMessage(
            timestamp=timestamp,
            message_id=message_id,
            action=action,
            price=price,
            size=size,
            side=side
        )
        self.message_stream.append(message)
        
        # Update active quotes
        self._update_active_quotes(message)
        
        # Update message rate
        self._update_message_rate(timestamp)
        
        # Check for quote stuffing
        event = self._detect_quote_stuffing()
        
        if event:
            self.stuffing_events.append(event)
            logger.warning(f"Quote stuffing detected: {event}")
            return event
        
        return None
    
    def _detect_quote_stuffing(self) -> Optional[QuoteStuffingEvent]:
        """Main quote stuffing detection logic"""
        
        if len(self.message_stream) < 100:
            return None
        
        # Check for burst pattern
        burst_event = self._detect_burst_stuffing()
        if burst_event:
            return burst_event
        
        # Check for sustained pattern
        sustained_event = self._detect_sustained_stuffing()
        if sustained_event:
            return sustained_event
        
        # Check for oscillating pattern
        oscillating_event = self._detect_oscillating_stuffing()
        if oscillating_event:
            return oscillating_event
        
        return None
    
    def _detect_burst_stuffing(self) -> Optional[QuoteStuffingEvent]:
        """Detect burst quote stuffing pattern"""
        
        # Look for sudden spike in message rate
        recent_messages = self._get_recent_messages(self.burst_duration)
        
        if not recent_messages:
            return None
        
        # Calculate burst rate
        time_span = (recent_messages[-1].timestamp - recent_messages[0].timestamp).total_seconds()
        if time_span <= 0:
            return None
        
        burst_rate = len(recent_messages) / time_span
        
        if burst_rate >= self.burst_threshold:
            # Analyze the burst
            return self._analyze_stuffing_event(recent_messages, 'burst')
        
        return None
    
    def _detect_sustained_stuffing(self) -> Optional[QuoteStuffingEvent]:
        """Detect sustained quote stuffing pattern"""
        
        # Check message rate over longer period
        recent_messages = self._get_recent_messages(self.sustained_duration)
        
        if len(recent_messages) < 50:
            return None
        
        # Calculate sustained rate
        time_span = (recent_messages[-1].timestamp - recent_messages[0].timestamp).total_seconds()
        if time_span <= 0:
            return None
        
        sustained_rate = len(recent_messages) / time_span
        
        if sustained_rate >= self.sustained_threshold:
            # Check if rate is sustained (not just one burst)
            if self._is_rate_sustained(recent_messages):
                return self._analyze_stuffing_event(recent_messages, 'sustained')
        
        return None
    
    def _detect_oscillating_stuffing(self) -> Optional[QuoteStuffingEvent]:
        """Detect oscillating quote stuffing pattern"""
        
        # Look for rapid price oscillations with high message rate
        window_messages = self._get_recent_messages(timedelta(seconds=2))
        
        if len(window_messages) < 100:
            return None
        
        # Group by price level
        price_groups = defaultdict(list)
        for msg in window_messages:
            price_key = round(msg.price / self.tick_size) * self.tick_size
            price_groups[price_key].append(msg)
        
        # Check for oscillation pattern
        if len(price_groups) >= 2:
            # Find top 2 most active price levels
            sorted_groups = sorted(price_groups.items(), 
                                 key=lambda x: len(x[1]), reverse=True)
            
            if len(sorted_groups[0][1]) + len(sorted_groups[1][1]) > len(window_messages) * 0.8:
                # 80% of messages at just 2 price levels - oscillation
                return self._analyze_stuffing_event(window_messages, 'oscillating')
        
        return None
    
    def _analyze_stuffing_event(self, messages: List[QuoteMessage], 
                               pattern_type: str) -> QuoteStuffingEvent:
        """Analyze detected stuffing event"""
        
        start_time = messages[0].timestamp
        end_time = messages[-1].timestamp
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Calculate peak rate
        peak_rate = self._calculate_peak_rate(messages)
        
        # Determine affected side
        bid_count = sum(1 for m in messages if m.side == 'bid')
        ask_count = sum(1 for m in messages if m.side == 'ask')
        
        if bid_count > ask_count * 2:
            target_side = 'bid'
        elif ask_count > bid_count * 2:
            target_side = 'ask'
        else:
            target_side = 'both'
        
        # Count affected price levels
        unique_prices = len(set(m.price for m in messages))
        
        # Determine severity
        severity = self._determine_severity(peak_rate, duration_ms)
        
        # Calculate market impact
        market_impact = self._calculate_market_impact(messages)
        
        return QuoteStuffingEvent(
            timestamp=end_time,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            message_count=len(messages),
            peak_rate=peak_rate,
            affected_levels=unique_prices,
            target_side=target_side,
            pattern_type=pattern_type,
            severity=severity,
            market_impact=market_impact
        )
    
    def _calculate_peak_rate(self, messages: List[QuoteMessage]) -> float:
        """Calculate peak message rate within event"""
        
        if len(messages) < 10:
            return 0.0
        
        # Use sliding window to find peak
        window_size = timedelta(milliseconds=100)
        peak_rate = 0.0
        
        for i in range(len(messages)):
            window_end = messages[i].timestamp + window_size
            window_messages = [m for m in messages[i:] 
                             if m.timestamp <= window_end]
            
            if len(window_messages) > 1:
                time_span = (window_messages[-1].timestamp - 
                           window_messages[0].timestamp).total_seconds()
                if time_span > 0:
                    rate = len(window_messages) / time_span
                    peak_rate = max(peak_rate, rate)
        
        return peak_rate
    
    def _determine_severity(self, peak_rate: float, duration_ms: float) -> str:
        """Determine severity level of stuffing event"""
        
        for severity, thresholds in reversed(list(self.severity_levels.items())):
            if (peak_rate >= thresholds['rate'] and 
                duration_ms >= thresholds['duration']):
                return severity
        
        return 'low'
    
    def _calculate_market_impact(self, messages: List[QuoteMessage]) -> Dict[str, float]:
        """Calculate market impact of stuffing event"""
        
        # Get market state before and after
        pre_messages = self._get_messages_before(messages[0].timestamp, timedelta(seconds=1))
        post_messages = self._get_messages_after(messages[-1].timestamp, timedelta(seconds=1))
        
        impact = {}
        
        # Message rate impact
        pre_rate = len(pre_messages) if pre_messages else 10
        during_rate = len(messages) / ((messages[-1].timestamp - 
                                       messages[0].timestamp).total_seconds() or 1)
        impact['rate_increase'] = (during_rate / pre_rate - 1) * 100 if pre_rate > 0 else 0
        
        # Quote lifetime impact
        pre_lifetime = self._estimate_quote_lifetime(pre_messages)
        during_lifetime = self._estimate_quote_lifetime(messages)
        impact['lifetime_reduction'] = (1 - during_lifetime / pre_lifetime) * 100 if pre_lifetime > 0 else 0
        
        # Spread impact (simplified)
        impact['spread_volatility'] = self._calculate_spread_volatility(messages)
        
        # System load estimate
        impact['system_load'] = min(100, (during_rate / 1000) * 100)  # Normalize to 100%
        
        return impact
    
    def _estimate_quote_lifetime(self, messages: List[QuoteMessage]) -> float:
        """Estimate average quote lifetime from messages"""
        
        add_times = {}
        lifetimes = []
        
        for msg in messages:
            key = (msg.price, msg.side)
            
            if msg.action == 'add':
                add_times[key] = msg.timestamp
            elif msg.action == 'cancel' and key in add_times:
                lifetime = (msg.timestamp - add_times[key]).total_seconds() * 1000
                lifetimes.append(lifetime)
                del add_times[key]
        
        return np.mean(lifetimes) if lifetimes else 1000.0  # Default 1 second
    
    def _calculate_spread_volatility(self, messages: List[QuoteMessage]) -> float:
        """Calculate spread volatility during stuffing"""
        
        # Group messages by timestamp to reconstruct spreads
        by_time = defaultdict(lambda: {'bid': [], 'ask': []})
        
        for msg in messages:
            time_key = msg.timestamp.replace(microsecond=0)
            by_time[time_key][msg.side].append(msg.price)
        
        spreads = []
        for time_data in by_time.values():
            if time_data['bid'] and time_data['ask']:
                best_bid = max(time_data['bid'])
                best_ask = min(time_data['ask'])
                spread = (best_ask - best_bid) / self.tick_size
                spreads.append(spread)
        
        return np.std(spreads) if len(spreads) > 1 else 0.0
    
    def _is_rate_sustained(self, messages: List[QuoteMessage]) -> bool:
        """Check if high message rate is sustained"""
        
        # Divide into buckets and check each
        bucket_count = 10
        bucket_size = len(messages) // bucket_count
        
        if bucket_size < 5:
            return False
        
        high_rate_buckets = 0
        
        for i in range(0, len(messages), bucket_size):
            bucket = messages[i:i+bucket_size]
            if len(bucket) < 2:
                continue
            
            time_span = (bucket[-1].timestamp - bucket[0].timestamp).total_seconds()
            if time_span > 0:
                rate = len(bucket) / time_span
                if rate >= self.sustained_threshold * 0.8:  # 80% of threshold
                    high_rate_buckets += 1
        
        return high_rate_buckets >= bucket_count * 0.7  # 70% of buckets
    
    def _update_active_quotes(self, message: QuoteMessage):
        """Update tracking of active quotes"""
        
        key = (message.price, message.side)
        
        if message.action == 'add':
            self.active_quotes[key] = message
        elif message.action == 'cancel' and key in self.active_quotes:
            del self.active_quotes[key]
        elif message.action == 'modify' and key in self.active_quotes:
            self.active_quotes[key] = message
    
    def _update_message_rate(self, timestamp: datetime):
        """Update rolling message rate calculation"""
        
        current_second = timestamp.replace(microsecond=0)
        
        if not self.message_rate_history or self.message_rate_history[-1][0] != current_second:
            self.message_rate_history.append([current_second, 1])
        else:
            self.message_rate_history[-1][1] += 1
    
    def _get_recent_messages(self, window: timedelta) -> List[QuoteMessage]:
        """Get messages within recent time window"""
        
        if not self.message_stream:
            return []
        
        cutoff_time = self.message_stream[-1].timestamp - window
        return [m for m in self.message_stream if m.timestamp >= cutoff_time]
    
    def _get_messages_before(self, timestamp: datetime, window: timedelta) -> List[QuoteMessage]:
        """Get messages before specific timestamp"""
        
        start_time = timestamp - window
        return [m for m in self.message_stream 
                if start_time <= m.timestamp < timestamp]
    
    def _get_messages_after(self, timestamp: datetime, window: timedelta) -> List[QuoteMessage]:
        """Get messages after specific timestamp"""
        
        end_time = timestamp + window
        return [m for m in self.message_stream 
                if timestamp < m.timestamp <= end_time]
    
    def get_stuffing_statistics(self, minutes: int = 60) -> Dict[str, Any]:
        """Get quote stuffing statistics"""
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_events = [e for e in self.stuffing_events if e.timestamp >= cutoff_time]
        
        if not recent_events:
            return {
                'event_count': 0,
                'total_messages_involved': 0,
                'avg_severity': 'none',
                'patterns': {}
            }
        
        # Aggregate statistics
        pattern_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        total_messages = 0
        
        for event in recent_events:
            pattern_counts[event.pattern_type] += 1
            severity_counts[event.severity] += 1
            total_messages += event.message_count
        
        # Determine average severity
        severity_order = ['low', 'medium', 'high', 'extreme']
        weighted_severity = sum(severity_order.index(e.severity) for e in recent_events) / len(recent_events)
        avg_severity = severity_order[int(weighted_severity)]
        
        return {
            'event_count': len(recent_events),
            'total_messages_involved': total_messages,
            'avg_severity': avg_severity,
            'patterns': dict(pattern_counts),
            'severities': dict(severity_counts),
            'avg_duration_ms': np.mean([e.duration_ms for e in recent_events]),
            'avg_peak_rate': np.mean([e.peak_rate for e in recent_events]),
            'most_targeted_side': max(recent_events, key=lambda e: e.message_count).target_side
        }
    
    def is_currently_stuffing(self) -> Tuple[bool, Optional[str]]:
        """Check if quote stuffing is currently active"""
        
        if not self.message_rate_history:
            return False, None
        
        # Check last few seconds
        recent_rates = list(self.message_rate_history)[-5:]
        if not recent_rates:
            return False, None
        
        avg_rate = np.mean([r[1] for r in recent_rates])
        
        if avg_rate >= self.burst_threshold:
            return True, 'burst'
        elif avg_rate >= self.sustained_threshold:
            return True, 'sustained'
        
        return False, None