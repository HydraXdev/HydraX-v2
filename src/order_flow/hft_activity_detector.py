# hft_activity_detector.py
# High-Frequency Trading Activity Detection System

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class HFTSignature:
    """HFT activity signature"""
    timestamp: datetime
    activity_type: str  # 'market_making', 'arbitrage', 'momentum', 'predatory'
    intensity: float  # 0-1 scale
    message_rate: float  # Messages per second
    cancel_replace_ratio: float
    quote_life_ms: float  # Average quote lifetime in milliseconds
    participation_rate: float  # % of total market activity
    aggression_score: float  # How aggressive the HFT is
    
@dataclass
class MicrostructureEvent:
    """Individual microstructure event"""
    timestamp: datetime
    event_type: str  # 'quote', 'trade', 'cancel', 'modify'
    price: float
    size: float
    side: str
    aggressive: bool  # Taking liquidity vs providing

class HFTActivityDetector:
    """
    HFT ACTIVITY DETECTION ENGINE
    
    Identifies and classifies high-frequency trading patterns:
    - Market making algorithms
    - Statistical arbitrage bots
    - Momentum/trend following HFTs
    - Predatory/latency arbitrage algorithms
    """
    
    def __init__(self, symbol: str, tick_size: float = 0.0001):
        self.symbol = symbol
        self.tick_size = tick_size
        
        # HFT detection thresholds
        self.min_message_rate = 10  # Messages per second
        self.min_cancel_ratio = 0.7  # 70% cancellation rate
        self.max_quote_life = 100  # Milliseconds
        self.min_participation = 0.1  # 10% of market activity
        
        # Time windows for analysis
        self.micro_window = timedelta(milliseconds=100)
        self.analysis_window = timedelta(seconds=1)
        self.pattern_window = timedelta(seconds=10)
        
        # Event storage
        self.event_stream = deque(maxlen=100000)
        self.hft_signatures = deque(maxlen=1000)
        
        # Pattern recognition
        self.activity_patterns = {
            'market_making': self._detect_market_making,
            'arbitrage': self._detect_arbitrage,
            'momentum': self._detect_momentum_hft,
            'predatory': self._detect_predatory_hft
        }
        
        # Statistical tracking
        self.message_rates = deque(maxlen=60)  # 1-minute rolling
        self.quote_lifetimes = deque(maxlen=1000)
        self.participant_stats = defaultdict(lambda: {'count': 0, 'volume': 0})
        
    def process_event(self, timestamp: datetime, event_type: str,
                     price: float, size: float, side: str,
                     aggressive: bool = False) -> Optional[HFTSignature]:
        """
        Process market microstructure event
        
        Args:
            timestamp: Event timestamp (microsecond precision)
            event_type: Type of event
            price: Event price
            size: Event size
            side: 'bid' or 'ask'
            aggressive: Whether order is taking liquidity
            
        Returns:
            HFTSignature if HFT activity detected
        """
        
        # Store event
        event = MicrostructureEvent(
            timestamp=timestamp,
            event_type=event_type,
            price=price,
            size=size,
            side=side,
            aggressive=aggressive
        )
        self.event_stream.append(event)
        
        # Update statistics
        self._update_statistics(event)
        
        # Check for HFT patterns
        signature = self._detect_hft_activity()
        
        if signature:
            self.hft_signatures.append(signature)
            logger.info(f"HFT activity detected: {signature}")
            
        return signature
    
    def _detect_hft_activity(self) -> Optional[HFTSignature]:
        """Main HFT detection logic"""
        
        # Need sufficient data
        if len(self.event_stream) < 100:
            return None
        
        # Calculate current metrics
        metrics = self._calculate_current_metrics()
        
        # Check if metrics indicate HFT
        if not self._is_hft_activity(metrics):
            return None
        
        # Classify HFT type
        for activity_type, detector in self.activity_patterns.items():
            if detector(metrics):
                return self._create_hft_signature(activity_type, metrics)
        
        # Unclassified HFT
        return self._create_hft_signature('unknown', metrics)
    
    def _calculate_current_metrics(self) -> Dict[str, float]:
        """Calculate current market microstructure metrics"""
        
        current_time = datetime.now()
        
        # Get recent events
        recent_events = self._get_events_in_window(self.analysis_window)
        
        if not recent_events:
            return {}
        
        # Message rate
        time_span = (recent_events[-1].timestamp - recent_events[0].timestamp).total_seconds()
        message_rate = len(recent_events) / time_span if time_span > 0 else 0
        
        # Cancel/modify ratio
        cancels = sum(1 for e in recent_events if e.event_type in ['cancel', 'modify'])
        cancel_ratio = cancels / len(recent_events) if recent_events else 0
        
        # Quote lifetime
        quote_life = self._calculate_avg_quote_lifetime(recent_events)
        
        # Participation rate
        participation = self._estimate_participation_rate(recent_events)
        
        # Aggression score
        aggression = self._calculate_aggression_score(recent_events)
        
        # Price volatility in micro timeframes
        micro_volatility = self._calculate_micro_volatility(recent_events)
        
        # Quote-to-trade ratio
        quotes = sum(1 for e in recent_events if e.event_type == 'quote')
        trades = sum(1 for e in recent_events if e.event_type == 'trade')
        quote_trade_ratio = quotes / trades if trades > 0 else float('inf')
        
        return {
            'message_rate': message_rate,
            'cancel_ratio': cancel_ratio,
            'quote_life_ms': quote_life,
            'participation_rate': participation,
            'aggression_score': aggression,
            'micro_volatility': micro_volatility,
            'quote_trade_ratio': quote_trade_ratio,
            'event_count': len(recent_events)
        }
    
    def _is_hft_activity(self, metrics: Dict[str, float]) -> bool:
        """Determine if metrics indicate HFT activity"""
        
        if not metrics:
            return False
        
        # High message rate
        if metrics['message_rate'] < self.min_message_rate:
            return False
        
        # High cancellation rate OR very short quote life
        if metrics['cancel_ratio'] < self.min_cancel_ratio:
            if metrics['quote_life_ms'] > self.max_quote_life:
                return False
        
        # Significant market participation
        if metrics['participation_rate'] < self.min_participation:
            return False
        
        return True
    
    def _detect_market_making(self, metrics: Dict[str, float]) -> bool:
        """Detect market making HFT pattern"""
        
        # Market makers characteristics:
        # - Provide liquidity on both sides
        # - Maintain tight spreads
        # - High cancel rate but low aggression
        # - Consistent presence
        
        if metrics['aggression_score'] > 0.3:  # Too aggressive
            return False
        
        if metrics['cancel_ratio'] < 0.8:  # Need high cancel rate
            return False
        
        # Check for two-sided quoting
        if self._check_two_sided_activity():
            return True
        
        return False
    
    def _detect_arbitrage(self, metrics: Dict[str, float]) -> bool:
        """Detect arbitrage HFT pattern"""
        
        # Arbitrage characteristics:
        # - Bursts of activity
        # - High aggression when executing
        # - Correlated with price discrepancies
        # - Lower message rate than market makers
        
        if metrics['aggression_score'] < 0.6:  # Need high aggression
            return False
        
        if metrics['message_rate'] > 50:  # Too high for arb
            return False
        
        # Check for burst patterns
        if self._check_burst_pattern():
            return True
        
        return False
    
    def _detect_momentum_hft(self, metrics: Dict[str, float]) -> bool:
        """Detect momentum/trend following HFT"""
        
        # Momentum HFT characteristics:
        # - Directional aggression
        # - Increases activity with volatility
        # - Lower cancel rate
        # - Takes liquidity in trend direction
        
        if metrics['cancel_ratio'] > 0.5:  # Too high cancel rate
            return False
        
        if metrics['micro_volatility'] < 2.0:  # Need volatility
            return False
        
        if metrics['aggression_score'] > 0.5:
            return True
        
        return False
    
    def _detect_predatory_hft(self, metrics: Dict[str, float]) -> bool:
        """Detect predatory/latency arbitrage HFT"""
        
        # Predatory HFT characteristics:
        # - Very high message rate
        # - Targets other orders
        # - Quick order placement/cancellation
        # - Often aggressive
        
        if metrics['message_rate'] < 50:  # Need very high rate
            return False
        
        if metrics['quote_life_ms'] > 50:  # Very short lived quotes
            return False
        
        if metrics['quote_trade_ratio'] > 100:  # Excessive quoting
            return True
        
        return False
    
    def _calculate_avg_quote_lifetime(self, events: List[MicrostructureEvent]) -> float:
        """Calculate average quote lifetime in milliseconds"""
        
        quote_times = {}
        lifetimes = []
        
        for event in events:
            if event.event_type == 'quote':
                key = (event.price, event.side)
                quote_times[key] = event.timestamp
            elif event.event_type in ['cancel', 'trade']:
                key = (event.price, event.side)
                if key in quote_times:
                    lifetime = (event.timestamp - quote_times[key]).total_seconds() * 1000
                    lifetimes.append(lifetime)
                    del quote_times[key]
        
        return np.mean(lifetimes) if lifetimes else 100.0
    
    def _estimate_participation_rate(self, events: List[MicrostructureEvent]) -> float:
        """Estimate HFT participation rate in market"""
        
        # This is simplified - in practice would need participant IDs
        total_volume = sum(e.size for e in events if e.event_type == 'trade')
        
        # Estimate HFT volume based on patterns
        hft_volume = sum(e.size for e in events 
                        if e.event_type == 'trade' and self._is_likely_hft_trade(e))
        
        return hft_volume / total_volume if total_volume > 0 else 0.0
    
    def _is_likely_hft_trade(self, event: MicrostructureEvent) -> bool:
        """Heuristic to identify likely HFT trades"""
        
        # Look for characteristic HFT trade sizes
        if event.size in [100, 1000, 10000]:  # Round lots
            return True
        
        # Check if part of rapid sequence
        nearby_events = self._get_events_near_timestamp(event.timestamp, timedelta(milliseconds=100))
        if len(nearby_events) > 5:
            return True
        
        return False
    
    def _calculate_aggression_score(self, events: List[MicrostructureEvent]) -> float:
        """Calculate aggression score (taking vs providing liquidity)"""
        
        aggressive_count = sum(1 for e in events if e.aggressive)
        total_count = len(events)
        
        return aggressive_count / total_count if total_count > 0 else 0.0
    
    def _calculate_micro_volatility(self, events: List[MicrostructureEvent]) -> float:
        """Calculate price volatility in micro timeframes"""
        
        trade_prices = [e.price for e in events if e.event_type == 'trade']
        
        if len(trade_prices) < 2:
            return 0.0
        
        # Calculate returns in pips
        returns = []
        for i in range(1, len(trade_prices)):
            ret = (trade_prices[i] - trade_prices[i-1]) / self.tick_size
            returns.append(ret)
        
        return np.std(returns) if returns else 0.0
    
    def _check_two_sided_activity(self) -> bool:
        """Check for two-sided quoting behavior"""
        
        recent_events = self._get_events_in_window(timedelta(seconds=5))
        
        bid_quotes = sum(1 for e in recent_events 
                        if e.event_type == 'quote' and e.side == 'bid')
        ask_quotes = sum(1 for e in recent_events 
                        if e.event_type == 'quote' and e.side == 'ask')
        
        # Should have roughly balanced quoting
        if min(bid_quotes, ask_quotes) > 0:
            ratio = min(bid_quotes, ask_quotes) / max(bid_quotes, ask_quotes)
            return ratio > 0.7
        
        return False
    
    def _check_burst_pattern(self) -> bool:
        """Check for burst trading pattern"""
        
        # Look for periods of intense activity followed by quiet
        window_events = self._get_events_in_window(timedelta(seconds=30))
        
        if len(window_events) < 100:
            return False
        
        # Divide into buckets
        bucket_size = len(window_events) // 10
        activity_levels = []
        
        for i in range(0, len(window_events), bucket_size):
            bucket = window_events[i:i+bucket_size]
            activity_levels.append(len(bucket))
        
        # High variance indicates burst pattern
        return np.std(activity_levels) > np.mean(activity_levels) * 0.5
    
    def _create_hft_signature(self, activity_type: str, metrics: Dict[str, float]) -> HFTSignature:
        """Create HFT signature from detected pattern"""
        
        # Calculate intensity based on metrics
        intensity = min(1.0, metrics['message_rate'] / 100)
        
        return HFTSignature(
            timestamp=datetime.now(),
            activity_type=activity_type,
            intensity=intensity,
            message_rate=metrics['message_rate'],
            cancel_replace_ratio=metrics['cancel_ratio'],
            quote_life_ms=metrics['quote_life_ms'],
            participation_rate=metrics['participation_rate'],
            aggression_score=metrics['aggression_score']
        )
    
    def _get_events_in_window(self, window: timedelta) -> List[MicrostructureEvent]:
        """Get events within time window"""
        
        if not self.event_stream:
            return []
        
        current_time = self.event_stream[-1].timestamp
        cutoff_time = current_time - window
        
        return [e for e in self.event_stream if e.timestamp >= cutoff_time]
    
    def _get_events_near_timestamp(self, timestamp: datetime, window: timedelta) -> List[MicrostructureEvent]:
        """Get events near specific timestamp"""
        
        start_time = timestamp - window
        end_time = timestamp + window
        
        return [e for e in self.event_stream 
                if start_time <= e.timestamp <= end_time]
    
    def _update_statistics(self, event: MicrostructureEvent):
        """Update running statistics"""
        
        # Update message rate
        current_second = event.timestamp.replace(microsecond=0)
        if not self.message_rates or self.message_rates[-1][0] != current_second:
            self.message_rates.append([current_second, 1])
        else:
            self.message_rates[-1][1] += 1
    
    def get_current_hft_activity(self) -> Dict[str, Any]:
        """Get current HFT activity summary"""
        
        recent_signatures = [s for s in self.hft_signatures 
                           if s.timestamp >= datetime.now() - timedelta(minutes=5)]
        
        if not recent_signatures:
            return {
                'active': False,
                'dominant_type': None,
                'intensity': 0.0,
                'message_rate': 0.0
            }
        
        # Aggregate metrics
        avg_intensity = np.mean([s.intensity for s in recent_signatures])
        avg_message_rate = np.mean([s.message_rate for s in recent_signatures])
        
        # Find dominant type
        type_counts = defaultdict(int)
        for sig in recent_signatures:
            type_counts[sig.activity_type] += 1
        dominant_type = max(type_counts, key=type_counts.get)
        
        return {
            'active': True,
            'dominant_type': dominant_type,
            'intensity': avg_intensity,
            'message_rate': avg_message_rate,
            'participation_rate': np.mean([s.participation_rate for s in recent_signatures]),
            'aggression_score': np.mean([s.aggression_score for s in recent_signatures])
        }
    
    def get_hft_impact_analysis(self) -> Dict[str, Any]:
        """Analyze market impact of HFT activity"""
        
        if len(self.event_stream) < 1000:
            return {'insufficient_data': True}
        
        # Separate periods with and without HFT
        hft_periods = []
        normal_periods = []
        
        # Simple classification based on message rate
        for i in range(0, len(self.event_stream), 100):
            period_events = self.event_stream[i:i+100]
            if not period_events:
                continue
                
            time_span = (period_events[-1].timestamp - period_events[0].timestamp).total_seconds()
            if time_span > 0:
                message_rate = len(period_events) / time_span
                
                if message_rate > self.min_message_rate:
                    hft_periods.extend(period_events)
                else:
                    normal_periods.extend(period_events)
        
        # Compare metrics
        hft_volatility = self._calculate_micro_volatility(hft_periods) if hft_periods else 0
        normal_volatility = self._calculate_micro_volatility(normal_periods) if normal_periods else 0
        
        hft_spreads = self._estimate_average_spread(hft_periods) if hft_periods else 0
        normal_spreads = self._estimate_average_spread(normal_periods) if normal_periods else 0
        
        return {
            'hft_periods_count': len(hft_periods),
            'normal_periods_count': len(normal_periods),
            'volatility_increase': (hft_volatility / normal_volatility - 1) * 100 if normal_volatility > 0 else 0,
            'spread_impact': (hft_spreads / normal_spreads - 1) * 100 if normal_spreads > 0 else 0,
            'hft_volatility': hft_volatility,
            'normal_volatility': normal_volatility
        }
    
    def _estimate_average_spread(self, events: List[MicrostructureEvent]) -> float:
        """Estimate average spread from events"""
        
        # Group by timestamp to reconstruct bid/ask
        by_time = defaultdict(lambda: {'bid': None, 'ask': None})
        
        for event in events:
            if event.event_type == 'quote':
                by_time[event.timestamp][event.side] = event.price
        
        spreads = []
        for time_data in by_time.values():
            if time_data['bid'] and time_data['ask']:
                spread = (time_data['ask'] - time_data['bid']) / self.tick_size
                spreads.append(spread)
        
        return np.mean(spreads) if spreads else 2.0