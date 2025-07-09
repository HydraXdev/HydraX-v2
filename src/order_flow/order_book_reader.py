"""
Order Book Reader

Connects to exchange APIs and maintains real-time order book data
with efficient updates and snapshot management.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import logging
from collections import deque
import json

logger = logging.getLogger(__name__)


@dataclass
class OrderBookLevel:
    """Represents a single level in the order book"""
    price: float
    quantity: float
    orders: int = 1
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class OrderBookSnapshot:
    """Complete order book snapshot"""
    symbol: str
    exchange: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: float
    sequence: Optional[int] = None
    
    def get_spread(self) -> float:
        """Calculate bid-ask spread"""
        if self.bids and self.asks:
            return self.asks[0].price - self.bids[0].price
        return 0.0
    
    def get_mid_price(self) -> float:
        """Calculate mid price"""
        if self.bids and self.asks:
            return (self.asks[0].price + self.bids[0].price) / 2
        return 0.0
    
    def get_depth(self, levels: int = 10) -> Tuple[float, float]:
        """Get total bid/ask depth for specified levels"""
        bid_depth = sum(level.quantity for level in self.bids[:levels])
        ask_depth = sum(level.quantity for level in self.asks[:levels])
        return bid_depth, ask_depth
    
    def get_weighted_mid_price(self, levels: int = 5) -> float:
        """Calculate volume-weighted mid price"""
        if not self.bids or not self.asks:
            return 0.0
        
        bid_weight = sum(level.price * level.quantity for level in self.bids[:levels])
        bid_volume = sum(level.quantity for level in self.bids[:levels])
        
        ask_weight = sum(level.price * level.quantity for level in self.asks[:levels])
        ask_volume = sum(level.quantity for level in self.asks[:levels])
        
        if bid_volume + ask_volume == 0:
            return self.get_mid_price()
        
        return (bid_weight + ask_weight) / (bid_volume + ask_volume)


class OrderBookMaintainer:
    """Maintains order book state with efficient updates"""
    
    def __init__(self, symbol: str, exchange: str, max_levels: int = 100):
        self.symbol = symbol
        self.exchange = exchange
        self.max_levels = max_levels
        self.bids: Dict[float, OrderBookLevel] = {}
        self.asks: Dict[float, OrderBookLevel] = {}
        self.last_update = datetime.now().timestamp()
        self.sequence = 0
        self.update_callbacks: List[Callable] = []
    
    def apply_snapshot(self, snapshot: Dict):
        """Apply a full order book snapshot"""
        self.bids.clear()
        self.asks.clear()
        
        # Process bids
        for bid in snapshot.get('bids', []):
            price, quantity = float(bid[0]), float(bid[1])
            if quantity > 0:
                self.bids[price] = OrderBookLevel(price, quantity)
        
        # Process asks
        for ask in snapshot.get('asks', []):
            price, quantity = float(ask[0]), float(ask[1])
            if quantity > 0:
                self.asks[price] = OrderBookLevel(price, quantity)
        
        self.last_update = datetime.now().timestamp()
        self._trim_levels()
        self._notify_update()
    
    def apply_update(self, updates: Dict):
        """Apply incremental updates to order book"""
        # Process bid updates
        for bid in updates.get('bids', []):
            price, quantity = float(bid[0]), float(bid[1])
            if quantity == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = OrderBookLevel(price, quantity)
        
        # Process ask updates
        for ask in updates.get('asks', []):
            price, quantity = float(ask[0]), float(ask[1])
            if quantity == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = OrderBookLevel(price, quantity)
        
        self.last_update = datetime.now().timestamp()
        self._trim_levels()
        self._notify_update()
    
    def get_snapshot(self) -> OrderBookSnapshot:
        """Get current order book snapshot"""
        # Sort and convert to lists
        sorted_bids = sorted(self.bids.values(), key=lambda x: x.price, reverse=True)
        sorted_asks = sorted(self.asks.values(), key=lambda x: x.price)
        
        return OrderBookSnapshot(
            symbol=self.symbol,
            exchange=self.exchange,
            bids=sorted_bids[:self.max_levels],
            asks=sorted_asks[:self.max_levels],
            timestamp=self.last_update,
            sequence=self.sequence
        )
    
    def add_update_callback(self, callback: Callable):
        """Add callback for order book updates"""
        self.update_callbacks.append(callback)
    
    def _trim_levels(self):
        """Trim order book to max levels"""
        if len(self.bids) > self.max_levels:
            sorted_prices = sorted(self.bids.keys(), reverse=True)
            for price in sorted_prices[self.max_levels:]:
                del self.bids[price]
        
        if len(self.asks) > self.max_levels:
            sorted_prices = sorted(self.asks.keys())
            for price in sorted_prices[self.max_levels:]:
                del self.asks[price]
    
    def _notify_update(self):
        """Notify all callbacks of update"""
        snapshot = self.get_snapshot()
        for callback in self.update_callbacks:
            try:
                callback(snapshot)
            except Exception as e:
                logger.error(f"Error in order book callback: {e}")


class OrderBookReader:
    """Main order book reader that manages multiple order books"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.order_books: Dict[str, OrderBookMaintainer] = {}
        self.history_buffer: Dict[str, deque] = {}
        self.max_history = 1000
        self.update_interval = 0.1  # 100ms default update interval
        self.tasks: Dict[str, asyncio.Task] = {}
    
    async def subscribe(self, symbol: str, exchange: str = None, callback: Callable = None):
        """Subscribe to order book updates for a symbol"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key not in self.order_books:
            self.order_books[key] = OrderBookMaintainer(symbol, exchange or 'aggregated')
            self.history_buffer[key] = deque(maxlen=self.max_history)
        
        if callback:
            self.order_books[key].add_update_callback(callback)
        
        # Start update task if not running
        if key not in self.tasks or self.tasks[key].done():
            self.tasks[key] = asyncio.create_task(
                self._update_loop(symbol, exchange)
            )
        
        logger.info(f"Subscribed to {key}")
    
    async def unsubscribe(self, symbol: str, exchange: str = None):
        """Unsubscribe from order book updates"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key in self.tasks:
            self.tasks[key].cancel()
            await asyncio.gather(self.tasks[key], return_exceptions=True)
            del self.tasks[key]
        
        if key in self.order_books:
            del self.order_books[key]
        
        if key in self.history_buffer:
            del self.history_buffer[key]
        
        logger.info(f"Unsubscribed from {key}")
    
    async def get_order_book(self, symbol: str, exchange: str = None) -> Optional[OrderBookSnapshot]:
        """Get current order book snapshot"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key in self.order_books:
            return self.order_books[key].get_snapshot()
        
        # Fetch fresh if not subscribed
        try:
            data = await self.exchange_manager.get_order_book(symbol, exchange=exchange)
            maintainer = OrderBookMaintainer(symbol, exchange or 'unknown')
            maintainer.apply_snapshot(data)
            return maintainer.get_snapshot()
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            return None
    
    async def get_aggregated_order_book(self, symbol: str) -> Optional[OrderBookSnapshot]:
        """Get aggregated order book from all exchanges"""
        all_books = await self.exchange_manager.get_all_order_books(symbol)
        
        # Aggregate all order books
        aggregated_bids = {}
        aggregated_asks = {}
        
        for exchange, book_data in all_books.items():
            if not book_data:
                continue
            
            # Aggregate bids
            for bid in book_data.get('bids', []):
                price, quantity = float(bid[0]), float(bid[1])
                if price in aggregated_bids:
                    aggregated_bids[price].quantity += quantity
                    aggregated_bids[price].orders += 1
                else:
                    aggregated_bids[price] = OrderBookLevel(price, quantity)
            
            # Aggregate asks
            for ask in book_data.get('asks', []):
                price, quantity = float(ask[0]), float(ask[1])
                if price in aggregated_asks:
                    aggregated_asks[price].quantity += quantity
                    aggregated_asks[price].orders += 1
                else:
                    aggregated_asks[price] = OrderBookLevel(price, quantity)
        
        # Sort and create snapshot
        sorted_bids = sorted(aggregated_bids.values(), key=lambda x: x.price, reverse=True)
        sorted_asks = sorted(aggregated_asks.values(), key=lambda x: x.price)
        
        return OrderBookSnapshot(
            symbol=symbol,
            exchange='aggregated',
            bids=sorted_bids[:100],
            asks=sorted_asks[:100],
            timestamp=datetime.now().timestamp()
        )
    
    async def get_historical_snapshots(self, symbol: str, exchange: str = None, limit: int = 100) -> List[OrderBookSnapshot]:
        """Get historical order book snapshots"""
        key = f"{exchange or 'all'}:{symbol}"
        
        if key in self.history_buffer:
            snapshots = list(self.history_buffer[key])
            return snapshots[-limit:]
        
        return []
    
    async def _update_loop(self, symbol: str, exchange: str = None):
        """Main update loop for a symbol"""
        key = f"{exchange or 'all'}:{symbol}"
        
        while True:
            try:
                # Get order book data
                if exchange:
                    data = await self.exchange_manager.get_order_book(symbol, exchange=exchange)
                    self.order_books[key].apply_snapshot(data)
                else:
                    # Aggregate from all exchanges
                    snapshot = await self.get_aggregated_order_book(symbol)
                    if snapshot:
                        # Store in history
                        self.history_buffer[key].append(snapshot)
                        
                        # Notify callbacks
                        for callback in self.order_books[key].update_callbacks:
                            try:
                                callback(snapshot)
                            except Exception as e:
                                logger.error(f"Error in callback: {e}")
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop for {key}: {e}")
                await asyncio.sleep(5)  # Error backoff
    
    async def close(self):
        """Close all subscriptions"""
        # Cancel all tasks
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.order_books.clear()
        self.history_buffer.clear()
        self.tasks.clear()


# Example usage
async def main():
    from exchange_manager import ExchangeManager, ExchangeConfig, RateLimitConfig
    
    # Setup exchange manager
    exchange_manager = ExchangeManager()
    await exchange_manager.add_exchange(ExchangeConfig(
        name='binance',
        rate_limits=RateLimitConfig(requests_per_second=10, requests_per_minute=1200)
    ))
    
    # Create order book reader
    reader = OrderBookReader(exchange_manager)
    
    # Subscribe with callback
    def on_update(snapshot: OrderBookSnapshot):
        print(f"Update: {snapshot.symbol} - Spread: {snapshot.get_spread():.2f}, "
              f"Mid: {snapshot.get_mid_price():.2f}")
    
    await reader.subscribe('BTC/USDT', callback=on_update)
    
    # Let it run for a bit
    await asyncio.sleep(10)
    
    # Get historical data
    history = await reader.get_historical_snapshots('BTC/USDT', limit=10)
    print(f"Historical snapshots: {len(history)}")
    
    # Clean up
    await reader.close()
    await exchange_manager.close_all()


if __name__ == "__main__":
    asyncio.run(main())