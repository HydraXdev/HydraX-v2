#!/usr/bin/env python3
"""
MetaSocket Backfill and OHLC Management System
Handles historical data backfill and maintains rolling OHLC store
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
import websockets

logger = logging.getLogger(__name__)

class OHLCBar:
    """Represents a single OHLC bar"""

    def __init__(self, timestamp: int, open_price: float = None):
        self.timestamp = timestamp  # Minute timestamp (epoch seconds)
        self.open = open_price
        self.high = open_price
        self.low = open_price
        self.close = open_price
        self.volume = 0
        self.tick_count = 0

    def update_tick(self, price: float, volume: float = 1):
        """Update OHLC bar with new tick"""
        if self.open is None:
            self.open = price

        if self.high is None or price > self.high:
            self.high = price

        if self.low is None or price < self.low:
            self.low = price

        self.close = price
        self.volume += volume
        self.tick_count += 1

    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "tick_count": self.tick_count
        }

class MetaSocketBackfill:
    """Handles backfill and maintains OHLC data store"""

    def __init__(self, host: str = "185.244.67.11", port: int = 8778):
        self.host = host
        self.port = port
        self.ws_url = f"ws://{host}:{port}"

        # OHLC storage - maintain 500+ bars per symbol
        self.ohlc_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))

        # Current (incomplete) bars being built from ticks
        self.current_bars: Dict[str, OHLCBar] = {}

        # Track backfill completion
        self.backfill_completed: Dict[str, bool] = defaultdict(bool)

        # Active symbols (same as subscriptions)
        self.active_symbols = [
            # Major Forex Pairs (6)
            "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD",
            # Cross Pairs (10)
            "EURJPY", "GBPJPY", "EURGBP", "EURAUD", "GBPCAD", "AUDJPY", "NZDJPY",
            "CHFJPY", "CADJPY", "AUDCAD",
            # Additional Pairs (2)
            "USDCNH", "AUDNZD",
            # Precious Metals (2)
            "XAUUSD", "XAGUSD"
        ]

        # Callbacks
        self.ohlc_update_callback = None

    def set_ohlc_callback(self, callback):
        """Set callback for OHLC updates"""
        self.ohlc_update_callback = callback

    async def start_backfill(self):
        """Start the backfill process for all symbols"""
        logger.info("🔄 Starting historical data backfill")

        for symbol in self.active_symbols:
            await self.backfill_symbol(symbol)
            await asyncio.sleep(0.2)  # Rate limiting

        logger.info("✅ Backfill completed for all symbols")

    async def backfill_symbol(self, symbol: str, bars: int = 300):
        """Backfill historical M1 data for a symbol"""
        try:
            logger.info(f"📊 Backfilling {symbol} - requesting {bars} bars")

            # Connect for backfill request
            async with websockets.connect(self.ws_url) as websocket:
                # Request historical M1 data
                request = {
                    "action": "PRICE_HISTORY",
                    "symbol": symbol,
                    "timeframe": "M1",
                    "count": bars,
                    "ts": int(time.time() * 1000)
                }

                await websocket.send(json.dumps(request))

                # Wait for response
                response = await websocket.recv()
                data = json.loads(response)

                if data.get("status") == "success" and "bars" in data:
                    bars_data = data["bars"]

                    # Store historical bars
                    for bar_data in bars_data:
                        ohlc_bar = OHLCBar(
                            timestamp=bar_data.get("timestamp"),
                            open_price=bar_data.get("open")
                        )
                        ohlc_bar.high = bar_data.get("high")
                        ohlc_bar.low = bar_data.get("low")
                        ohlc_bar.close = bar_data.get("close")
                        ohlc_bar.volume = bar_data.get("volume", 0)

                        self.ohlc_store[symbol].append(ohlc_bar)

                    self.backfill_completed[symbol] = True
                    logger.info(f"✅ {symbol}: Loaded {len(bars_data)} historical bars")

                else:
                    logger.warning(f"⚠️ {symbol}: Backfill failed - {data}")

        except Exception as e:
            logger.error(f"❌ {symbol}: Backfill error - {e}")

    def process_tick(self, tick_data: dict):
        """Process incoming tick and update current OHLC bars"""
        symbol = tick_data.get("symbol")
        if not symbol or symbol not in self.active_symbols:
            return

        # Get mid price for OHLC
        bid = tick_data.get("bid")
        ask = tick_data.get("ask")
        if not bid or not ask:
            return

        mid_price = (bid + ask) / 2
        current_time = int(time.time())

        # Get current minute timestamp (floor to minute)
        minute_timestamp = (current_time // 60) * 60

        # Check if we need to start a new bar
        current_bar = self.current_bars.get(symbol)

        if not current_bar or current_bar.timestamp != minute_timestamp:
            # Complete previous bar if exists
            if current_bar and current_bar.timestamp < minute_timestamp:
                self.complete_bar(symbol, current_bar)

            # Start new bar
            self.current_bars[symbol] = OHLCBar(minute_timestamp, mid_price)

        # Update current bar with tick
        self.current_bars[symbol].update_tick(mid_price)

    def complete_bar(self, symbol: str, bar: OHLCBar):
        """Complete a bar and add it to the OHLC store"""
        # Add to store
        self.ohlc_store[symbol].append(bar)

        # Trigger callback if set
        if self.ohlc_update_callback:
            normalized_ohlc = {
                "symbol": symbol,
                "timeframe": "M1",
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "ts_epoch_ms": int(bar.timestamp * 1000),
                "src": "metasocket"
            }

            asyncio.create_task(self.ohlc_update_callback(normalized_ohlc))

        logger.debug(f"📊 {symbol}: Bar completed - OHLC={bar.open:.5f}/{bar.high:.5f}/{bar.low:.5f}/{bar.close:.5f}")

    def get_ohlc_data(self, symbol: str, count: int = 100) -> List[dict]:
        """Get last N OHLC bars for a symbol"""
        if symbol not in self.ohlc_store:
            return []

        bars = list(self.ohlc_store[symbol])

        # Return last N bars
        return [bar.to_dict() for bar in bars[-count:]]

    def get_latest_price(self, symbol: str) -> Optional[dict]:
        """Get latest price data for a symbol"""
        # Try to get from current bar first
        current_bar = self.current_bars.get(symbol)
        if current_bar and current_bar.close:
            return {
                "symbol": symbol,
                "bid": current_bar.close - 0.00005,  # Approximate bid/ask spread
                "ask": current_bar.close + 0.00005,
                "mid": current_bar.close,
                "ts_epoch_ms": int(time.time() * 1000),
                "src": "metasocket"
            }

        # Fallback to last completed bar
        if symbol in self.ohlc_store and self.ohlc_store[symbol]:
            last_bar = self.ohlc_store[symbol][-1]
            return {
                "symbol": symbol,
                "bid": last_bar.close - 0.00005,
                "ask": last_bar.close + 0.00005,
                "mid": last_bar.close,
                "ts_epoch_ms": int(last_bar.timestamp * 1000),
                "src": "metasocket"
            }

        return None

    def create_signal_snapshot(self, symbol: str) -> Optional[dict]:
        """Create signal snapshot with OHLC and current price data"""
        if not self.backfill_completed.get(symbol):
            logger.warning(f"⚠️ {symbol}: Cannot create snapshot - backfill not completed")
            return None

        # Get last 100 bars
        ohlc_data = self.get_ohlc_data(symbol, 100)

        # Get current price
        current_price = self.get_latest_price(symbol)

        if not ohlc_data or not current_price:
            return None

        # Calculate spread
        spread = current_price["ask"] - current_price["bid"]

        # Simple R:R hint based on recent volatility
        if len(ohlc_data) >= 20:
            recent_highs = [bar["high"] for bar in ohlc_data[-20:]]
            recent_lows = [bar["low"] for bar in ohlc_data[-20:]]
            atr = (max(recent_highs) - min(recent_lows)) / 20  # Simplified ATR
            rr_hint = round(atr * 1.5, 5)  # 1.5x ATR for potential target
        else:
            rr_hint = None

        snapshot = {
            "type": "signal_snapshot",
            "symbol": symbol,
            "timeframe": "M1",
            "ohlc": ohlc_data,
            "price": {
                "bid": current_price["bid"],
                "ask": current_price["ask"],
                "mid": current_price["mid"]
            },
            "overlays": {
                "spread": spread,
                "rr_hint": rr_hint
            },
            "ts_epoch_ms": int(time.time() * 1000),
            "src": "metasocket"
        }

        return snapshot

    def get_health_stats(self) -> dict:
        """Get health statistics for backfill system"""
        current_time = time.time()

        stats = {
            "symbols_backfilled": sum(1 for completed in self.backfill_completed.values() if completed),
            "total_symbols": len(self.active_symbols),
            "ohlc_bars_per_symbol": {},
            "current_bars_active": len(self.current_bars),
            "last_bar_ages": {}
        }

        for symbol in self.active_symbols:
            stats["ohlc_bars_per_symbol"][symbol] = len(self.ohlc_store.get(symbol, []))

            # Calculate age of last completed bar
            if symbol in self.ohlc_store and self.ohlc_store[symbol]:
                last_bar = self.ohlc_store[symbol][-1]
                age_seconds = current_time - last_bar.timestamp
                stats["last_bar_ages"][symbol] = age_seconds

        return stats

# Example usage and testing
if __name__ == "__main__":
    async def test_backfill():
        async def ohlc_handler(ohlc):
            print(f"OHLC Update: {ohlc['symbol']} = {ohlc['close']:.5f}")

        backfill = MetaSocketBackfill()
        backfill.set_ohlc_callback(ohlc_handler)

        # Test backfill
        await backfill.start_backfill()

        # Test snapshot creation
        snapshot = backfill.create_signal_snapshot("EURUSD")
        if snapshot:
            print(f"Snapshot created for EURUSD with {len(snapshot['ohlc'])} bars")

    import asyncio
    asyncio.run(test_backfill())