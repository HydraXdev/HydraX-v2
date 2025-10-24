#!/usr/bin/env python3
"""
Finnhub Data Adapter for Generators
====================================
Provides clean interface for generators to access hybrid Finnhub data.

Usage in generators:
    from services.finnhub_data_adapter import FinnhubDataAdapter

    adapter = FinnhubDataAdapter()
    candles = adapter.get_candles('EURUSD', count=100)
    latest_tick = adapter.get_latest_tick('EURUSD')

Created: October 21, 2025
"""

import redis
import json
import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class FinnhubDataAdapter:
    """
    Clean interface for generators to access hybrid Finnhub data from Redis
    """

    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        """
        Initialize adapter with Redis connection

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )

        # Test connection
        try:
            self.redis_client.ping()
            logger.info("✅ Finnhub Data Adapter connected to Redis")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

    def get_candles(self, symbol: str, count: int = 100) -> List[Dict]:
        """
        Get historical candles for a symbol

        Args:
            symbol: MT5 symbol (e.g., 'EURUSD')
            count: Number of candles to retrieve (default 100, max 100)

        Returns:
            List of candle dicts: [
                {
                    'time': 1761086880,
                    'open': 1.16021,
                    'high': 1.16024,
                    'low': 1.16019,
                    'close': 1.16021,
                    'volume': 123,
                    'source': 'finnhub_rest' or 'hybrid_tick',
                    'symbol': 'EURUSD'
                },
                ...
            ]
        """
        try:
            key = f'candle_1m_{symbol}_history'
            data = self.redis_client.get(key)

            if not data:
                logger.warning(f"⚠️ No candle history found for {symbol}")
                return []

            candles = json.loads(data)

            # Return last N candles
            return candles[-count:] if len(candles) > count else candles

        except Exception as e:
            logger.error(f"❌ Error getting candles for {symbol}: {e}")
            return []

    def get_latest_candle(self, symbol: str) -> Optional[Dict]:
        """
        Get the most recent completed candle

        Args:
            symbol: MT5 symbol

        Returns:
            Latest candle dict or None
        """
        try:
            key = f'candle_1m_{symbol}_latest'
            data = self.redis_client.get(key)

            if not data:
                # Fallback: get last candle from history
                candles = self.get_candles(symbol, count=1)
                return candles[0] if candles else None

            return json.loads(data)

        except Exception as e:
            logger.error(f"❌ Error getting latest candle for {symbol}: {e}")
            return None

    def get_latest_tick(self, symbol: str) -> Optional[Dict]:
        """
        Get the most recent tick (real-time price)

        Args:
            symbol: MT5 symbol

        Returns:
            Tick dict: {
                'symbol': 'EURUSD',
                'price': 1.16021,
                'timestamp': 1761086921973,
                'volume': 0,
                'source': 'finnhub',
                'received_at': 1761086923251
            }
        """
        try:
            key = f'latest_tick_{symbol}'
            data = self.redis_client.get(key)

            if not data:
                logger.debug(f"No tick data for {symbol}")
                return None

            return json.loads(data)

        except Exception as e:
            logger.error(f"❌ Error getting tick for {symbol}: {e}")
            return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol (convenience method)

        Args:
            symbol: MT5 symbol

        Returns:
            Current price (float) or None
        """
        tick = self.get_latest_tick(symbol)
        return tick['price'] if tick else None

    def get_ohlc(self, symbol: str, timeframe_minutes: int = 1) -> Optional[Dict]:
        """
        Get current OHLC for a timeframe

        Args:
            symbol: MT5 symbol
            timeframe_minutes: Timeframe in minutes (1, 5, 15, etc.)

        Returns:
            OHLC dict: {'open': 1.16021, 'high': 1.16024, 'low': 1.16019, 'close': 1.16021}
        """
        if timeframe_minutes == 1:
            # For 1-min, return latest candle
            candle = self.get_latest_candle(symbol)
            if candle:
                return {
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle.get('volume', 0),
                    'time': candle['time']
                }

        else:
            # For higher timeframes, aggregate candles
            candles = self.get_candles(symbol, count=timeframe_minutes)
            if not candles:
                return None

            return {
                'open': candles[0]['open'],
                'high': max(c['high'] for c in candles),
                'low': min(c['low'] for c in candles),
                'close': candles[-1]['close'],
                'volume': sum(c.get('volume', 0) for c in candles),
                'time': candles[-1]['time']
            }

    def subscribe_to_delta_signals(self, symbol: str, callback):
        """
        Subscribe to delta/imbalance signals for micro-flow detection

        Args:
            symbol: MT5 symbol
            callback: Function to call on new delta signal
                     callback(signal_dict) where signal_dict = {
                         'type': 'IMBALANCE',
                         'symbol': 'EURUSD',
                         'delta': 0.00015,
                         'price': 1.16021,
                         'volume': 150,
                         'avg_volume': 100,
                         'timestamp': 1761086921
                     }
        """
        try:
            pubsub = self.redis_client.pubsub()
            channel = f'delta_signal_{symbol}'
            pubsub.subscribe(channel)

            logger.info(f"✅ Subscribed to delta signals for {symbol}")

            for message in pubsub.listen():
                if message['type'] == 'message':
                    signal = json.loads(message['data'])
                    callback(signal)

        except Exception as e:
            logger.error(f"❌ Error subscribing to delta signals for {symbol}: {e}")

    def is_data_fresh(self, symbol: str, max_age_seconds: int = 120) -> bool:
        """
        Check if data for a symbol is fresh (recent tick within max_age)

        Args:
            symbol: MT5 symbol
            max_age_seconds: Maximum age in seconds (default 120s)

        Returns:
            True if data is fresh, False otherwise
        """
        import time

        tick = self.get_latest_tick(symbol)
        if not tick:
            return False

        tick_age = (time.time() * 1000) - tick['received_at']
        return tick_age < (max_age_seconds * 1000)

    def get_active_symbols(self) -> List[str]:
        """
        Get list of symbols with active data

        Returns:
            List of symbol strings
        """
        try:
            keys = self.redis_client.keys('latest_tick_*')
            symbols = [k.replace('latest_tick_', '') for k in keys]
            return symbols

        except Exception as e:
            logger.error(f"❌ Error getting active symbols: {e}")
            return []


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    adapter = FinnhubDataAdapter()

    # Test candle retrieval
    print("\n📊 Testing candle retrieval:")
    candles = adapter.get_candles('EURUSD', count=5)
    print(f"Retrieved {len(candles)} candles for EURUSD")
    if candles:
        print(f"Latest candle: {candles[-1]}")

    # Test tick retrieval
    print("\n📈 Testing tick retrieval:")
    tick = adapter.get_latest_tick('EURUSD')
    if tick:
        print(f"Latest tick: EURUSD @ {tick['price']} (age: {tick['received_at']})")

    # Test current price
    print("\n💰 Testing current price:")
    price = adapter.get_current_price('EURUSD')
    if price:
        print(f"Current EURUSD price: {price}")

    # Test OHLC
    print("\n📉 Testing OHLC:")
    ohlc = adapter.get_ohlc('EURUSD', timeframe_minutes=1)
    if ohlc:
        print(f"EURUSD 1-min OHLC: {ohlc}")

    # Test data freshness
    print("\n⏰ Testing data freshness:")
    is_fresh = adapter.is_data_fresh('EURUSD', max_age_seconds=120)
    print(f"EURUSD data fresh: {is_fresh}")

    # Test active symbols
    print("\n📋 Testing active symbols:")
    symbols = adapter.get_active_symbols()
    print(f"Active symbols ({len(symbols)}): {', '.join(symbols[:10])}")
