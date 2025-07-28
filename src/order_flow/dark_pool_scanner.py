"""
Dark Pool Activity Scanner

Simulates detection of dark pool activity through various heuristics and patterns.
In production, this would integrate with real dark pool data feeds.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from collections import deque
import random

logger = logging.getLogger(__name__)

@dataclass
class DarkPoolPrint:
    """Represents a detected dark pool print"""
    timestamp: float
    symbol: str
    exchange: str
    price: float
    volume: float
    notional_value: float
    price_vs_market: float  # Percentage difference from market price
    likely_direction: str  # 'buy', 'sell', 'neutral'
    confidence: float  # 0-1
    detection_method: str
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'price': self.price,
            'volume': self.volume,
            'notional_value': self.notional_value,
            'price_vs_market': self.price_vs_market,
            'likely_direction': self.likely_direction,
            'confidence': self.confidence,
            'detection_method': self.detection_method
        }

@dataclass
class DarkPoolFlow:
    """Represents aggregated dark pool flow over time"""
    symbol: str
    time_period: str  # '1h', '4h', '1d'
    total_volume: float
    buy_volume: float
    sell_volume: float
    neutral_volume: float
    average_print_size: float
    large_print_count: int
    flow_score: float  # -100 to 100, negative = selling, positive = buying
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'time_period': self.time_period,
            'total_volume': self.total_volume,
            'buy_volume': self.buy_volume,
            'sell_volume': self.sell_volume,
            'neutral_volume': self.neutral_volume,
            'average_print_size': self.average_print_size,
            'large_print_count': self.large_print_count,
            'flow_score': self.flow_score,
            'buy_percentage': (self.buy_volume / self.total_volume * 100) if self.total_volume > 0 else 0
        }

class DarkPoolActivityScanner:
    """Scans for and analyzes dark pool activity patterns"""
    
    def __init__(self,
                 min_print_size: float = 10000.0,  # Minimum notional value
                 large_print_multiplier: float = 10.0,
                 lookback_hours: int = 24):
        """
        Initialize dark pool scanner
        
        Args:
            min_print_size: Minimum notional value to consider
            large_print_multiplier: Multiplier for average to consider "large"
            lookback_hours: Hours of history to maintain
        """
        self.min_print_size = min_print_size
        self.large_print_multiplier = large_print_multiplier
        self.lookback_hours = lookback_hours
        
        # Data storage
        self.prints: Dict[str, deque] = {}
        self.market_prices: Dict[str, float] = {}
        self.average_print_sizes: Dict[str, float] = {}
        
        # Detection patterns
        self.detection_patterns = {
            'volume_spike': self._detect_volume_spike,
            'price_deviation': self._detect_price_deviation,
            'time_pattern': self._detect_time_pattern,
            'size_anomaly': self._detect_size_anomaly
        }
    
    def update_market_price(self, symbol: str, price: float):
        """Update current market price for a symbol"""
        self.market_prices[symbol] = price
    
    def scan_for_activity(self, 
                         symbol: str,
                         recent_trades: List[Dict],
                         order_book_snapshot: Optional[Dict] = None) -> List[DarkPoolPrint]:
        """
        Scan for potential dark pool activity
        
        This is a simulation - in production, would use real dark pool data feeds
        """
        
        # Initialize storage if needed
        if symbol not in self.prints:
            self.prints[symbol] = deque(maxlen=10000)
            self.average_print_sizes[symbol] = self.min_print_size
        
        detected_prints = []
        
        # Analyze recent trades for patterns
        for pattern_name, pattern_func in self.detection_patterns.items():
            prints = pattern_func(symbol, recent_trades, order_book_snapshot)
            for print_data in prints:
                print_data.detection_method = pattern_name
                detected_prints.append(print_data)
                self.prints[symbol].append(print_data)
        
        # Update average print size
        if detected_prints:
            recent_sizes = [p.notional_value for p in list(self.prints[symbol])[-100:]]
            self.average_print_sizes[symbol] = np.mean(recent_sizes)
        
        return detected_prints
    
    def _detect_volume_spike(self, 
                           symbol: str,
                           trades: List[Dict],
                           order_book: Optional[Dict]) -> List[DarkPoolPrint]:
        """Detect unusual volume spikes that might indicate dark pool activity"""
        
        prints = []
        
        # Group trades by time window
        time_windows = {}
        for trade in trades:
            window = int(trade['timestamp'] // 60000)  # 1-minute windows
            if window not in time_windows:
                time_windows[window] = []
            time_windows[window].append(trade)
        
        # Analyze each window
        for window, window_trades in time_windows.items():
            total_volume = sum(float(t['amount']) for t in window_trades)
            avg_price = np.mean([float(t['price']) for t in window_trades])
            notional = total_volume * avg_price
            
            # Check if this could be a dark pool print
            if notional > self.min_print_size:
                # Simulate detection confidence based on various factors
                confidence = self._calculate_confidence_volume_spike(
                    notional, len(window_trades), symbol
                )
                
                if confidence > 0.5:
                    market_price = self.market_prices.get(symbol, avg_price)
                    price_diff = (avg_price - market_price) / market_price * 100
                    
                    prints.append(DarkPoolPrint(
                        timestamp=window * 60,
                        symbol=symbol,
                        exchange='dark_pool',
                        price=avg_price,
                        volume=total_volume,
                        notional_value=notional,
                        price_vs_market=price_diff,
                        likely_direction=self._infer_direction(price_diff, order_book),
                        confidence=confidence,
                        detection_method='volume_spike'
                    ))
        
        return prints
    
    def _detect_price_deviation(self,
                              symbol: str,
                              trades: List[Dict],
                              order_book: Optional[Dict]) -> List[DarkPoolPrint]:
        """Detect trades at prices significantly different from market"""
        
        prints = []
        market_price = self.market_prices.get(symbol)
        
        if not market_price:
            return prints
        
        # Look for trades with significant price deviation
        for trade in trades:
            price = float(trade['price'])
            volume = float(trade['amount'])
            notional = price * volume
            
            if notional < self.min_print_size:
                continue
            
            price_diff = abs(price - market_price) / market_price
            
            # Significant deviation might indicate dark pool
            if price_diff > 0.002:  # 0.2% deviation
                confidence = min(0.9, price_diff * 100)
                
                prints.append(DarkPoolPrint(
                    timestamp=trade['timestamp'] / 1000,
                    symbol=symbol,
                    exchange='dark_pool',
                    price=price,
                    volume=volume,
                    notional_value=notional,
                    price_vs_market=(price - market_price) / market_price * 100,
                    likely_direction='buy' if price > market_price else 'sell',
                    confidence=confidence,
                    detection_method='price_deviation'
                ))
        
        return prints
    
    def _detect_time_pattern(self,
                           symbol: str,
                           trades: List[Dict],
                           order_book: Optional[Dict]) -> List[DarkPoolPrint]:
        """Detect trades that occur at typical dark pool times"""
        
        prints = []
        
        # Dark pools often print at specific times (market close, etc.)
        # This is a simplified simulation
        
        for trade in trades:
            timestamp = trade['timestamp'] / 1000
            dt = datetime.fromtimestamp(timestamp)
            
            # Check if near market close (simplified)
            if dt.hour == 15 and dt.minute >= 50:  # Near 4 PM
                volume = float(trade['amount'])
                price = float(trade['price'])
                notional = volume * price
                
                if notional > self.min_print_size * 2:  # Higher threshold for time-based
                    market_price = self.market_prices.get(symbol, price)
                    
                    prints.append(DarkPoolPrint(
                        timestamp=timestamp,
                        symbol=symbol,
                        exchange='dark_pool',
                        price=price,
                        volume=volume,
                        notional_value=notional,
                        price_vs_market=(price - market_price) / market_price * 100,
                        likely_direction='neutral',
                        confidence=0.6,
                        detection_method='time_pattern'
                    ))
        
        return prints
    
    def _detect_size_anomaly(self,
                           symbol: str,
                           trades: List[Dict],
                           order_book: Optional[Dict]) -> List[DarkPoolPrint]:
        """Detect trades with unusual size characteristics"""
        
        prints = []
        avg_size = self.average_print_sizes.get(symbol, self.min_print_size)
        
        for trade in trades:
            volume = float(trade['amount'])
            price = float(trade['price'])
            notional = volume * price
            
            # Check for unusually large trades
            if notional > avg_size * self.large_print_multiplier:
                market_price = self.market_prices.get(symbol, price)
                
                # Large trades often go through dark pools
                confidence = min(0.95, notional / (avg_size * self.large_print_multiplier * 2))
                
                prints.append(DarkPoolPrint(
                    timestamp=trade['timestamp'] / 1000,
                    symbol=symbol,
                    exchange='dark_pool',
                    price=price,
                    volume=volume,
                    notional_value=notional,
                    price_vs_market=(price - market_price) / market_price * 100,
                    likely_direction=self._infer_direction_from_size(notional, avg_size),
                    confidence=confidence,
                    detection_method='size_anomaly'
                ))
        
        return prints
    
    def _calculate_confidence_volume_spike(self, notional: float, trade_count: int, symbol: str) -> float:
        """Calculate confidence score for volume spike detection"""
        
        # Base confidence on notional size
        size_score = min(1.0, notional / (self.min_print_size * 10))
        
        # Adjust for trade count (fewer trades = more likely dark pool)
        trade_score = 1.0 / (1 + trade_count / 10)
        
        # Random factor for simulation
        random_factor = 0.8 + random.random() * 0.2
        
        return size_score * trade_score * random_factor
    
    def _infer_direction(self, price_diff: float, order_book: Optional[Dict]) -> str:
        """Infer likely direction of dark pool print"""
        
        if abs(price_diff) < 0.1:
            return 'neutral'
        
        # Price above market often indicates buying
        if price_diff > 0:
            return 'buy'
        else:
            return 'sell'
    
    def _infer_direction_from_size(self, notional: float, avg_size: float) -> str:
        """Infer direction based on size characteristics"""
        
        # Very large prints often indicate institutional buying
        if notional > avg_size * 20:
            return 'buy' if random.random() > 0.3 else 'sell'
        
        return 'neutral'
    
    def get_flow_analysis(self, symbol: str, time_period: str = '1h') -> DarkPoolFlow:
        """Analyze dark pool flow over specified time period"""
        
        if symbol not in self.prints:
            return DarkPoolFlow(
                symbol=symbol,
                time_period=time_period,
                total_volume=0,
                buy_volume=0,
                sell_volume=0,
                neutral_volume=0,
                average_print_size=0,
                large_print_count=0,
                flow_score=0
            )
        
        # Calculate time cutoff
        period_hours = {
            '1h': 1,
            '4h': 4,
            '1d': 24,
            '1w': 168
        }.get(time_period, 1)
        
        cutoff_time = datetime.now().timestamp() - (period_hours * 3600)
        
        # Filter recent prints
        recent_prints = [p for p in self.prints[symbol] if p.timestamp > cutoff_time]
        
        if not recent_prints:
            return DarkPoolFlow(
                symbol=symbol,
                time_period=time_period,
                total_volume=0,
                buy_volume=0,
                sell_volume=0,
                neutral_volume=0,
                average_print_size=0,
                large_print_count=0,
                flow_score=0
            )
        
        # Aggregate metrics
        total_volume = sum(p.volume for p in recent_prints)
        buy_volume = sum(p.volume for p in recent_prints if p.likely_direction == 'buy')
        sell_volume = sum(p.volume for p in recent_prints if p.likely_direction == 'sell')
        neutral_volume = sum(p.volume for p in recent_prints if p.likely_direction == 'neutral')
        
        avg_print_size = np.mean([p.notional_value for p in recent_prints])
        large_prints = [p for p in recent_prints 
                       if p.notional_value > avg_print_size * self.large_print_multiplier]
        
        # Calculate flow score (-100 to 100)
        if total_volume > 0:
            buy_ratio = buy_volume / total_volume
            sell_ratio = sell_volume / total_volume
            flow_score = (buy_ratio - sell_ratio) * 100
        else:
            flow_score = 0
        
        return DarkPoolFlow(
            symbol=symbol,
            time_period=time_period,
            total_volume=total_volume,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            neutral_volume=neutral_volume,
            average_print_size=avg_print_size,
            large_print_count=len(large_prints),
            flow_score=flow_score
        )
    
    def get_significant_prints(self, symbol: str, limit: int = 10) -> List[DarkPoolPrint]:
        """Get most significant recent dark pool prints"""
        
        if symbol not in self.prints:
            return []
        
        # Sort by notional value and recency
        all_prints = list(self.prints[symbol])
        current_time = datetime.now().timestamp()
        
        # Score based on size and recency
        scored_prints = []
        for print_data in all_prints:
            age_hours = (current_time - print_data.timestamp) / 3600
            recency_score = 1 / (1 + age_hours / 24)  # Decay over 24 hours
            size_score = print_data.notional_value / self.min_print_size
            
            score = size_score * recency_score * print_data.confidence
            scored_prints.append((score, print_data))
        
        # Sort by score and return top prints
        scored_prints.sort(key=lambda x: x[0], reverse=True)
        
        return [print_data for _, print_data in scored_prints[:limit]]
    
    def get_statistics(self, symbol: str) -> Dict:
        """Get dark pool activity statistics"""
        
        if symbol not in self.prints:
            return {
                'total_prints': 0,
                'total_volume': 0,
                'average_confidence': 0,
                'detection_methods': {}
            }
        
        prints = list(self.prints[symbol])
        
        if not prints:
            return {
                'total_prints': 0,
                'total_volume': 0,
                'average_confidence': 0,
                'detection_methods': {}
            }
        
        # Count by detection method
        method_counts = {}
        for print_data in prints:
            method = print_data.detection_method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            'total_prints': len(prints),
            'total_volume': sum(p.volume for p in prints),
            'total_notional': sum(p.notional_value for p in prints),
            'average_confidence': np.mean([p.confidence for p in prints]),
            'average_print_size': np.mean([p.notional_value for p in prints]),
            'detection_methods': method_counts,
            'buy_prints': sum(1 for p in prints if p.likely_direction == 'buy'),
            'sell_prints': sum(1 for p in prints if p.likely_direction == 'sell'),
            'neutral_prints': sum(1 for p in prints if p.likely_direction == 'neutral')
        }

# Example usage
async def main():
    scanner = DarkPoolActivityScanner(
        min_print_size=50000,  # $50k minimum
        large_print_multiplier=10
    )
    
    # Update market price
    scanner.update_market_price('BTC/USDT', 50000)
    
    # Simulate some trades
    trades = []
    base_price = 50000
    
    # Normal trades
    for i in range(50):
        trades.append({
            'timestamp': (datetime.now() - timedelta(minutes=50-i)).timestamp() * 1000,
            'price': base_price + random.uniform(-10, 10),
            'amount': random.exponential(0.1)
        })
    
    # Add a potential dark pool print (large size)
    trades.append({
        'timestamp': datetime.now().timestamp() * 1000,
        'price': base_price * 1.001,  # Slightly above market
        'amount': 50  # Large volume
    })
    
    # Scan for activity
    detected_prints = scanner.scan_for_activity('BTC/USDT', trades)
    
    print(f"Detected {len(detected_prints)} potential dark pool prints")
    for print_data in detected_prints:
        print(f"  - ${print_data.notional_value:,.0f} at {print_data.price:.2f} "
              f"({print_data.likely_direction}, confidence: {print_data.confidence:.2f})")
    
    # Get flow analysis
    flow = scanner.get_flow_analysis('BTC/USDT', '1h')
    print(f"\nDark Pool Flow (1h):")
    print(f"  Total Volume: {flow.total_volume:.2f}")
    print(f"  Flow Score: {flow.flow_score:.1f}")
    print(f"  Buy %: {flow.buy_volume/flow.total_volume*100:.1f}%" if flow.total_volume > 0 else "  No volume")
    
    # Get statistics
    stats = scanner.get_statistics('BTC/USDT')
    print(f"\nStatistics: {stats}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())