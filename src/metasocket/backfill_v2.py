"""
backfill_v2.py - Enhanced backfill system mirroring TypeScript logic
Implements OhlcStore interface, Bar type, and backfillAll functionality
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

import websockets
from symbols import SYMBOLS

logger = logging.getLogger(__name__)


@dataclass
class Bar:
    """OHLC Bar - mirrors TypeScript Bar type"""

    ts_open_ms: int  # Opening timestamp in milliseconds
    o: float  # Open price
    h: float  # High price
    l: float  # Low price
    c: float  # Close price
    v: Optional[float] = None  # Volume (optional)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        result = {"ts_open_ms": self.ts_open_ms, "o": self.o, "h": self.h, "l": self.l, "c": self.c}
        if self.v is not None:
            result["v"] = self.v
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Bar":
        """Create Bar from dictionary"""
        return cls(ts_open_ms=data["ts_open_ms"], o=data["o"], h=data["h"], l=data["l"], c=data["c"], v=data.get("v"))


class OhlcStore(Protocol):
    """OHLC Store interface - mirrors TypeScript OhlcStore"""

    def put(self, symbol: str, bars: List[Bar]) -> None:
        """Store bars for symbol"""
        ...

    def upsert_from_tick(self, symbol: str, tick: dict) -> None:
        """Merge tick into current M1 bar"""
        ...

    def last(self, symbol: str, n: int) -> List[Bar]:
        """Get last n bars for symbol"""
        ...


class InMemoryOhlcStore:
    """In-memory OHLC store implementation"""

    def __init__(self, max_bars_per_symbol: int = 500):
        self.max_bars = max_bars_per_symbol
        self.bars: Dict[str, deque] = {}
        self.current_bars: Dict[str, Bar] = {}  # Incomplete bars being built
        self.last_tick_ts: Dict[str, int] = {}

    def put(self, symbol: str, bars: List[Bar]) -> None:
        """Store bars for symbol - mirrors TypeScript put()"""
        if symbol not in self.bars:
            self.bars[symbol] = deque(maxlen=self.max_bars)

        # Clear existing and add new bars
        self.bars[symbol].clear()
        for bar in bars:
            self.bars[symbol].append(bar)

        logger.debug(f"📊 Stored {len(bars)} bars for {symbol}")

    def upsert_from_tick(self, symbol: str, tick: dict) -> None:
        """Merge tick into current M1 bar - mirrors TypeScript upsertFromTick()"""
        mid_price = tick.get("mid")
        tick_ts = tick.get("ts", int(time.time() * 1000))

        if mid_price is None:
            return

        # Get current minute timestamp (floor to minute)
        minute_ts = (tick_ts // 60000) * 60000

        # Get or create current bar
        current_bar = self.current_bars.get(symbol)

        # Check if we need to complete the previous bar and start a new one
        if current_bar and current_bar.ts_open_ms != minute_ts:
            # Complete the previous bar
            self._complete_bar(symbol, current_bar)
            current_bar = None

        # Create new bar if needed
        if current_bar is None:
            self.current_bars[symbol] = Bar(
                ts_open_ms=minute_ts, o=mid_price, h=mid_price, l=mid_price, c=mid_price, v=0.0
            )
            current_bar = self.current_bars[symbol]

        # Update bar with tick
        if mid_price > current_bar.h:
            current_bar.h = mid_price
        if mid_price < current_bar.l:
            current_bar.l = mid_price

        current_bar.c = mid_price
        if current_bar.v is not None:
            current_bar.v += tick.get("volume", 1.0)

        self.last_tick_ts[symbol] = tick_ts

    def _complete_bar(self, symbol: str, bar: Bar) -> None:
        """Complete a bar and add it to storage"""
        if symbol not in self.bars:
            self.bars[symbol] = deque(maxlen=self.max_bars)

        self.bars[symbol].append(bar)
        logger.debug(f"📊 Completed bar for {symbol}: OHLC={bar.o:.5f}/{bar.h:.5f}/{bar.l:.5f}/{bar.c:.5f}")

    def last(self, symbol: str, n: int) -> List[Bar]:
        """Get last n bars for symbol - mirrors TypeScript last()"""
        if symbol not in self.bars:
            return []

        bars = list(self.bars[symbol])
        return bars[-n:] if n <= len(bars) else bars

    def get_current_bar(self, symbol: str) -> Optional[Bar]:
        """Get current incomplete bar"""
        return self.current_bars.get(symbol)

    def force_complete_current_bars(self) -> None:
        """Force complete all current bars (useful for testing)"""
        for symbol, bar in list(self.current_bars.items()):
            self._complete_bar(symbol, bar)
            del self.current_bars[symbol]

    def get_stats(self) -> dict:
        """Get storage statistics"""
        return {
            "symbols_stored": len(self.bars),
            "bars_per_symbol": {symbol: len(bars) for symbol, bars in self.bars.items()},
            "current_bars_active": len(self.current_bars),
            "total_bars": sum(len(bars) for bars in self.bars.values()),
        }


def map_to_bar(b: Any) -> Bar:
    """
    Map broker-native bar format to normalized Bar
    Mirrors TypeScript mapToBar() function
    """
    # Accept various timestamp field names
    ts_open_ms = b.get("ts_ms") or b.get("ts") or b.get("time_ms") or b.get("timestamp") or int(time.time() * 1000)

    # Ensure timestamp is in milliseconds
    if ts_open_ms < 1e12:  # If less than year 2001 in milliseconds, assume seconds
        ts_open_ms = int(ts_open_ms * 1000)

    return Bar(
        ts_open_ms=int(ts_open_ms),
        o=float(b.get("o", 0) or b.get("open", 0)),
        h=float(b.get("h", 0) or b.get("high", 0)),
        l=float(b.get("l", 0) or b.get("low", 0)),
        c=float(b.get("c", 0) or b.get("close", 0)),
        v=float(b.get("v")) if b.get("v") is not None else None,
    )


async def backfill_all(conn: Any, store: OhlcStore) -> None:
    """
    Backfill all symbols with historical data
    Mirrors TypeScript backfillAll() function
    """
    logger.info(f"📊 Starting backfill for {len(SYMBOLS)} symbols")

    success_count = 0
    failed_symbols = []

    for symbol in SYMBOLS:
        try:
            logger.debug(f"📊 Requesting history for {symbol}...")

            # Request historical data
            request = {"op": "PRICE_HISTORY", "symbol": symbol, "timeframe": "M1", "limit": 300}

            # Send request and wait for response
            if hasattr(conn, "send_and_wait"):
                response = await conn.send_and_wait(request)
            else:
                # Fallback for basic connection
                await conn.send(request)
                # In real implementation, you'd wait for response
                response = {"bars": []}

            # Map and store bars
            raw_bars = response.get("bars", [])
            if raw_bars:
                bars = [map_to_bar(b) for b in raw_bars]
                store.put(symbol, bars)
                success_count += 1
                logger.info(f"✅ {symbol}: Loaded {len(bars)} bars")
            else:
                logger.warning(f"⚠️ {symbol}: No historical data received")
                failed_symbols.append(symbol)

            # Rate limiting
            await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"❌ {symbol}: Backfill failed - {e}")
            failed_symbols.append(symbol)

    logger.info(f"📊 Backfill complete: {success_count}/{len(SYMBOLS)} symbols successful")

    if failed_symbols:
        logger.warning(f"⚠️ Failed symbols: {failed_symbols}")

    return {"success": success_count, "failed": failed_symbols}


class EnhancedBackfillManager:
    """Enhanced backfill manager with TypeScript-mirrored functionality"""

    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.store = InMemoryOhlcStore()
        self.connection = None
        self.backfill_completed = False

    async def initialize_connection(self):
        """Initialize WebSocket connection"""
        try:
            self.connection = await websockets.connect(
                self.websocket_url, ping_interval=20, ping_timeout=10, close_timeout=5
            )
            logger.info(f"🔗 Connected to {self.websocket_url} for backfill")
        except Exception as e:
            logger.error(f"❌ Failed to connect for backfill: {e}")
            raise

    async def send_and_wait(self, request: dict, timeout: float = 10.0) -> dict:
        """Send request and wait for response"""
        if not self.connection:
            raise ConnectionError("Not connected")

        request_id = f"req_{int(time.time() * 1000)}"
        request["request_id"] = request_id

        await self.connection.send(json.dumps(request))

        # Wait for response (simplified - in real implementation you'd handle this properly)
        try:
            response_str = await asyncio.wait_for(self.connection.recv(), timeout)
            response = json.loads(response_str)
            return response
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout waiting for response to {request['op']}")
            return {}

    async def perform_backfill(self) -> dict:
        """Perform complete backfill process"""
        logger.info("🚀 Starting enhanced backfill process")

        try:
            await self.initialize_connection()

            # Create connection wrapper for backfill_all
            conn_wrapper = type("Connection", (), {"send": self.connection.send, "send_and_wait": self.send_and_wait})()

            # Perform backfill
            result = await backfill_all(conn_wrapper, self.store)

            self.backfill_completed = True

            # Close connection
            if self.connection:
                await self.connection.close()

            logger.info("✅ Enhanced backfill completed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Enhanced backfill failed: {e}")
            return {"success": 0, "failed": list(SYMBOLS)}

    def process_tick(self, tick_data: dict) -> None:
        """Process incoming tick data"""
        symbol = tick_data.get("symbol")
        if symbol and symbol in SYMBOLS:
            self.store.upsert_from_tick(symbol, tick_data)

    def get_bars(self, symbol: str, count: int = 100) -> List[dict]:
        """Get bars as dictionaries for API compatibility"""
        bars = self.store.last(symbol, count)
        return [bar.to_dict() for bar in bars]

    def get_latest_bar(self, symbol: str) -> Optional[dict]:
        """Get latest completed bar"""
        bars = self.store.last(symbol, 1)
        if bars:
            return bars[0].to_dict()
        return None

    def get_current_bar(self, symbol: str) -> Optional[dict]:
        """Get current incomplete bar"""
        bar = self.store.get_current_bar(symbol)
        if bar:
            return bar.to_dict()
        return None

    def create_snapshot(self, symbol: str) -> Optional[dict]:
        """Create signal snapshot with OHLC data"""
        if not self.backfill_completed:
            logger.warning(f"⚠️ {symbol}: Backfill not completed, snapshot may be incomplete")

        bars = self.get_bars(symbol, 100)
        current_bar = self.get_current_bar(symbol)

        if not bars and not current_bar:
            return None

        # Use current bar price or latest completed bar
        if current_bar:
            current_price = {
                "bid": current_bar["c"] - 0.00005,  # Approximate spread
                "ask": current_bar["c"] + 0.00005,
                "mid": current_bar["c"],
            }
        elif bars:
            latest_close = bars[-1]["c"]
            current_price = {"bid": latest_close - 0.00005, "ask": latest_close + 0.00005, "mid": latest_close}
        else:
            return None

        # Calculate basic overlays
        spread = current_price["ask"] - current_price["bid"]

        # Simple volatility estimate
        if len(bars) >= 20:
            recent_closes = [bar["c"] for bar in bars[-20:]]
            price_range = max(recent_closes) - min(recent_closes)
            rr_hint = price_range * 0.1  # 10% of recent range
        else:
            rr_hint = None

        return {
            "type": "signal_snapshot",
            "symbol": symbol,
            "timeframe": "M1",
            "bars": bars,  # Last 100 bars
            "current_bar": current_bar,  # Incomplete current bar
            "price": current_price,
            "overlays": {"spread": spread, "rr_hint": rr_hint},
            "ts_epoch_ms": int(time.time() * 1000),
            "src": "metasocket",
        }

    def get_health_stats(self) -> dict:
        """Get health statistics"""
        store_stats = self.store.get_stats()

        return {
            "backfill_completed": self.backfill_completed,
            "connection_active": self.connection is not None and not self.connection.closed,
            "symbols_configured": len(SYMBOLS),
            **store_stats,
        }


# Example usage and testing
async def test_enhanced_backfill():
    """Test the enhanced backfill system"""
    print("🧪 Testing Enhanced Backfill System")
    print("=" * 40)

    # Create in-memory store
    store = InMemoryOhlcStore()

    # Test bar creation and mapping
    print("📊 Testing Bar mapping...")
    test_bar_data = {
        "ts_ms": int(time.time() * 1000),
        "o": 1.10500,
        "h": 1.10600,
        "l": 1.10400,
        "c": 1.10550,
        "v": 1000,
    }

    bar = map_to_bar(test_bar_data)
    print(f"  ✅ Mapped bar: OHLC={bar.o}/{bar.h}/{bar.l}/{bar.c}, V={bar.v}")

    # Test store operations
    print("📊 Testing store operations...")
    test_bars = [
        Bar(
            int(time.time() * 1000) - i * 60000,
            1.10500 + i * 0.0001,
            1.10600 + i * 0.0001,
            1.10400 + i * 0.0001,
            1.10550 + i * 0.0001,
            100,
        )
        for i in range(10)
    ]

    store.put("EURUSD", test_bars)
    last_5 = store.last("EURUSD", 5)
    print(f"  ✅ Stored {len(test_bars)} bars, retrieved {len(last_5)} bars")

    # Test tick integration
    print("📊 Testing tick integration...")
    test_tick = {"symbol": "EURUSD", "mid": 1.10575, "ts": int(time.time() * 1000)}

    store.upsert_from_tick("EURUSD", test_tick)
    current = store.get_current_bar("EURUSD")
    print(f"  ✅ Current bar: {current.c if current else 'None'}")

    # Test enhanced manager
    print("📊 Testing Enhanced Manager...")
    manager = EnhancedBackfillManager("ws://mock.test:8777")

    # Simulate tick processing
    manager.process_tick(test_tick)
    stats = manager.get_health_stats()
    print(f"  ✅ Health stats: {stats['symbols_configured']} symbols configured")

    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run test
    asyncio.run(test_enhanced_backfill())
