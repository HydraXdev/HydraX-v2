#!/usr/bin/env python3
"""
Market Data Aggregator - Hybrid Approach
=========================================
Combines Finnhub pre-built candles with real-time tick updates.

Architecture:
1. Base Layer: Poll Finnhub REST API for 1-min candles (every 60s)
2. Real-time Layer: Subscribe to Redis ticks from WebSocket manager
3. Output: Merged candle data + sub-minute tick deltas

Created: October 21, 2025
Based on: Grok's hybrid recommendation
"""

import redis
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/market_aggregator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
FINNHUB_API_KEY = 'd3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g'
FINNHUB_REST_URL = 'https://finnhub.io/api/v1'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 19 Major forex pairs
FOREX_PAIRS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
    'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY', 'EURGBP', 'EURAUD', 'EURNZD',
    'GBPAUD', 'GBPNZD', 'XAUUSD', 'XAGUSD', 'USDCNH'
]

class HybridMarketAggregator:
    """
    Hybrid market data aggregator combining Finnhub candles + WS ticks
    """

    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

        # Storage for candles (symbol -> list of candles)
        self.candles: Dict[str, List[dict]] = defaultdict(list)

        # Current live candle being built (symbol -> candle dict)
        self.live_candle: Dict[str, Optional[dict]] = {}

        # Last candle fetch time
        self.last_candle_fetch: Dict[str, float] = {}

        # Tick statistics
        self.tick_count = 0
        self.delta_signals = 0

        # Previous tick price for delta calculation
        self.prev_price: Dict[str, float] = {}

        # Average volume for anomaly detection
        self.avg_volume: Dict[str, float] = {}

        logger.info("✅ Hybrid Market Aggregator initialized")
        logger.info(f"📊 Monitoring {len(FOREX_PAIRS)} pairs")

    def convert_to_finnhub_symbol(self, mt5_symbol: str) -> str:
        """Convert MT5 symbol to Finnhub format"""
        if mt5_symbol.startswith('XAU'):
            return 'OANDA:XAU_USD'
        elif mt5_symbol.startswith('XAG'):
            return 'OANDA:XAG_USD'
        else:
            base = mt5_symbol[:3]
            quote = mt5_symbol[3:6]
            return f'OANDA:{base}_{quote}'

    def fetch_base_candles(self, symbol: str, resolution: str = '1') -> List[dict]:
        """
        Fetch base candles from Finnhub REST API

        Args:
            symbol: MT5 symbol (e.g., 'EURUSD')
            resolution: Candle resolution ('1' for 1-min)

        Returns:
            List of candle dicts with OHLCV data
        """
        try:
            finnhub_symbol = self.convert_to_finnhub_symbol(symbol)

            # Fetch last hour of data (60 candles at 1-min resolution)
            to_time = int(time.time())
            from_time = to_time - 3600  # 1 hour ago

            url = f'{FINNHUB_REST_URL}/forex/candle'
            params = {
                'symbol': finnhub_symbol,
                'resolution': resolution,
                'from': from_time,
                'to': to_time,
                'token': FINNHUB_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                logger.warning(f"⚠️ Finnhub API error {response.status_code} for {symbol}")
                return []

            data = response.json()

            if data.get('s') != 'ok':
                logger.warning(f"⚠️ Finnhub returned status: {data.get('s')} for {symbol}")
                return []

            # Transform to candle list
            candles = []
            for i, timestamp in enumerate(data['t']):
                candle = {
                    'time': timestamp,
                    'open': data['o'][i],
                    'high': data['h'][i],
                    'low': data['l'][i],
                    'close': data['c'][i],
                    'volume': data['v'][i] if 'v' in data and i < len(data['v']) else 0,
                    'source': 'finnhub_rest',
                    'symbol': symbol
                }
                candles.append(candle)

            logger.info(f"📥 Fetched {len(candles)} base candles for {symbol}")
            return candles

        except Exception as e:
            logger.error(f"❌ Error fetching base candles for {symbol}: {e}")
            return []

    def update_candles_with_tick(self, symbol: str, tick: dict):
        """
        Update live candle with incoming tick data

        Args:
            symbol: MT5 symbol
            tick: Tick data from WebSocket {price, timestamp, volume}
        """
        try:
            price = tick['price']
            timestamp = tick['timestamp'] // 1000  # Convert ms to seconds
            volume = tick.get('volume', 0)

            # Calculate current minute bucket
            current_min = timestamp - (timestamp % 60)

            # Initialize live candle if needed or if new minute started
            if symbol not in self.live_candle or self.live_candle[symbol] is None:
                self.live_candle[symbol] = {
                    'time': current_min,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': volume,
                    'source': 'hybrid_tick',
                    'symbol': symbol
                }
                logger.debug(f"🆕 New live candle started for {symbol} at {current_min}")

            elif self.live_candle[symbol]['time'] != current_min:
                # New minute - push completed candle to history
                completed_candle = self.live_candle[symbol].copy()
                self.candles[symbol].append(completed_candle)

                # Store in Redis for generator access
                self.redis_client.setex(
                    f'candle_1m_{symbol}_latest',
                    300,  # 5-min TTL
                    json.dumps(completed_candle)
                )

                # Start new candle
                self.live_candle[symbol] = {
                    'time': current_min,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': volume,
                    'source': 'hybrid_tick',
                    'symbol': symbol
                }

                logger.info(f"✅ Candle completed: {symbol} @ {completed_candle['time']} | O:{completed_candle['open']:.5f} H:{completed_candle['high']:.5f} L:{completed_candle['low']:.5f} C:{completed_candle['close']:.5f}")

            else:
                # Update current candle
                self.live_candle[symbol]['high'] = max(self.live_candle[symbol]['high'], price)
                self.live_candle[symbol]['low'] = min(self.live_candle[symbol]['low'], price)
                self.live_candle[symbol]['close'] = price
                self.live_candle[symbol]['volume'] += volume

            # Calculate delta for micro-flow signals
            if symbol in self.prev_price:
                delta = price - self.prev_price[symbol]

                # Detect significant delta + volume spike (Grok's #2 recommendation)
                threshold = 0.0001  # 1 pip for most pairs
                if symbol.startswith('JPY'):
                    threshold = 0.01  # 1 pip for JPY pairs

                avg_vol = self.avg_volume.get(symbol, 1.0)

                if abs(delta) > threshold and volume > avg_vol:
                    # Publish delta signal to Redis for generators
                    delta_signal = {
                        'type': 'IMBALANCE',
                        'symbol': symbol,
                        'delta': delta,
                        'price': price,
                        'volume': volume,
                        'avg_volume': avg_vol,
                        'timestamp': timestamp
                    }

                    self.redis_client.publish(f'delta_signal_{symbol}', json.dumps(delta_signal))
                    self.delta_signals += 1

                    logger.debug(f"⚡ Delta signal: {symbol} | Δ{delta:.5f} | Vol:{volume:.1f} (avg:{avg_vol:.1f})")

            self.prev_price[symbol] = price
            self.tick_count += 1

            # Update volume average (rolling window)
            if symbol in self.avg_volume:
                self.avg_volume[symbol] = (self.avg_volume[symbol] * 0.95) + (volume * 0.05)
            else:
                self.avg_volume[symbol] = volume

        except Exception as e:
            logger.error(f"❌ Error updating candle with tick: {e}")

    def subscribe_to_ticks(self):
        """
        Subscribe to Redis tick channels from WebSocket manager
        """
        logger.info("📡 Subscribing to tick channels...")

        pubsub = self.redis_client.pubsub()

        # Subscribe to all pair tick channels
        for symbol in FOREX_PAIRS:
            channel = f'market_tick_{symbol}'
            pubsub.subscribe(channel)
            logger.info(f"✅ Subscribed: {channel}")

        # Listen for messages
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    channel = message['channel']
                    symbol = channel.replace('market_tick_', '')

                    tick = json.loads(message['data'])
                    self.update_candles_with_tick(symbol, tick)

                    # Log stats every 500 ticks
                    if self.tick_count % 500 == 0:
                        logger.info(f"📊 Stats: {self.tick_count} ticks | {self.delta_signals} delta signals | {len(self.candles)} pairs tracked")

                except Exception as e:
                    logger.error(f"❌ Error processing tick message: {e}")

    def candle_fetch_worker(self):
        """
        Background worker to fetch base candles every 60 seconds
        """
        logger.info("🔄 Candle fetch worker started")

        while True:
            try:
                for symbol in FOREX_PAIRS:
                    # Check if it's time to fetch (every 60 seconds)
                    now = time.time()
                    last_fetch = self.last_candle_fetch.get(symbol, 0)

                    if now - last_fetch >= 60:
                        candles = self.fetch_base_candles(symbol)

                        if candles:
                            # Update candle history
                            self.candles[symbol] = candles

                            # Store latest 100 candles in Redis for generators
                            candle_history = candles[-100:] if len(candles) > 100 else candles
                            self.redis_client.setex(
                                f'candle_1m_{symbol}_history',
                                300,  # 5-min TTL
                                json.dumps(candle_history)
                            )

                            logger.info(f"🔄 Updated base candles for {symbol}: {len(candles)} candles")

                        self.last_candle_fetch[symbol] = now

                    # Small delay to avoid rate limiting
                    time.sleep(0.1)

                # Wait before next cycle
                time.sleep(10)

            except Exception as e:
                logger.error(f"❌ Error in candle fetch worker: {e}")
                time.sleep(60)

    def start(self):
        """
        Start hybrid aggregator with both workers
        """
        logger.info("🚀 Starting Hybrid Market Aggregator...")

        # Start candle fetch worker in background thread
        candle_thread = threading.Thread(target=self.candle_fetch_worker, daemon=True)
        candle_thread.start()
        logger.info("✅ Candle fetch worker started in background")

        # Subscribe to ticks (blocking, runs in main thread)
        self.subscribe_to_ticks()

def main():
    """Main entry point"""
    aggregator = HybridMarketAggregator()

    try:
        aggregator.start()
    except KeyboardInterrupt:
        logger.info("⏹️ Shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
