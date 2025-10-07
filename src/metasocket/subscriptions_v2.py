"""
subscriptions_v2.py - Enhanced subscription system mirroring TypeScript logic
Implements asyncio, backoff, and per-symbol tick freshness tracking
"""

import asyncio
import json
import time
import random
import logging
from typing import Dict, List, Optional, Protocol, Any
from datetime import datetime
import websockets

from symbols import SYMBOLS

logger = logging.getLogger(__name__)

class Connection(Protocol):
    """Connection interface matching TypeScript Conn type"""
    async def send(self, message: dict) -> None: ...
    def is_open(self) -> bool: ...
    async def reopen(self) -> None: ...
    def on(self, event: str, callback) -> None: ...

class WebSocketConnection:
    """WebSocket connection implementation"""

    def __init__(self, url: str):
        self.url = url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.event_handlers: Dict[str, List] = {}

    async def send(self, message: dict) -> None:
        """Send message to WebSocket"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps(message))
        else:
            raise ConnectionError("WebSocket not connected")

    def is_open(self) -> bool:
        """Check if connection is open"""
        return self.websocket is not None and not self.websocket.closed

    async def reopen(self) -> None:
        """Reopen WebSocket connection"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.close()
        except:
            pass

        self.websocket = await websockets.connect(
            self.url,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5
        )
        logger.info(f"🔗 WebSocket reconnected to {self.url}")

    def on(self, event: str, callback) -> None:
        """Register event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(callback)

class MetricsTracker:
    """Track per-symbol metrics"""

    def __init__(self):
        self.last_tick_ts: Dict[str, float] = {}
        self.tick_counts: Dict[str, int] = {}
        self.subscription_attempts: Dict[str, int] = {}

    def update_tick(self, symbol: str, timestamp: float = None):
        """Update last tick timestamp for symbol"""
        if timestamp is None:
            timestamp = time.time() * 1000  # milliseconds

        self.last_tick_ts[symbol] = timestamp
        self.tick_counts[symbol] = self.tick_counts.get(symbol, 0) + 1

    def get_stale_symbols(self, max_age_ms: int = 3000) -> List[str]:
        """Get symbols with stale tick data"""
        now = time.time() * 1000
        stale = []

        for symbol in SYMBOLS:
            last_tick = self.last_tick_ts.get(symbol, 0)
            age = now - last_tick
            if age > max_age_ms:
                stale.append(symbol)

        return stale

    def get_health_stats(self) -> dict:
        """Get health statistics"""
        now = time.time() * 1000

        return {
            "symbols_tracked": len(self.last_tick_ts),
            "total_ticks": sum(self.tick_counts.values()),
            "stale_symbols": self.get_stale_symbols(),
            "last_tick_ages": {
                symbol: int(now - ts)
                for symbol, ts in self.last_tick_ts.items()
            }
        }

async def subscribe_all(conn: Connection) -> None:
    """Subscribe to all symbols for price tracking and OHLC"""
    logger.info(f"📡 Subscribing to {len(SYMBOLS)} symbols")

    for symbol in SYMBOLS:
        try:
            # Subscribe to price tracking
            await conn.send({
                "op": "TRACK_PRICES",
                "symbol": symbol
            })

            # Prefer native OHLC if platform supports it
            # If unsupported, our candle builder will handle it
            await conn.send({
                "op": "TRACK_OHLC",
                "symbol": symbol,
                "timeframe": "M1"
            })

            # Small delay to avoid overwhelming server
            await asyncio.sleep(0.05)

        except Exception as e:
            logger.warning(f"⚠️ Failed to subscribe to {symbol}: {e}")

async def resubscribe_loop(conn: Connection, metrics: MetricsTracker) -> None:
    """
    Main resubscription loop with backoff and per-symbol freshness checks
    Mirrors TypeScript resubscribeLoop logic
    """
    backoffs = [1000, 2000, 5000, 10000, 15000, 30000]  # milliseconds
    idx = 0

    logger.info("🔄 Starting resubscription loop")

    while True:
        try:
            # Ensure connection is open
            if not conn.is_open():
                logger.info("🔌 Connection closed, reopening...")
                await conn.reopen()

            # Subscribe to all symbols
            await subscribe_all(conn)

            # Reset backoff after success
            idx = 0

            # Health heartbeat period
            await asyncio.sleep(15)

            # Check per-symbol tick freshness and resubscribe stale ones
            stale_symbols = metrics.get_stale_symbols(max_age_ms=3000)

            if stale_symbols:
                logger.warning(f"⚠️ Resubscribing to {len(stale_symbols)} stale symbols: {stale_symbols}")

                for symbol in stale_symbols:
                    try:
                        await conn.send({
                            "op": "TRACK_PRICES",
                            "symbol": symbol
                        })
                        await conn.send({
                            "op": "TRACK_OHLC",
                            "symbol": symbol,
                            "timeframe": "M1"
                        })

                        metrics.subscription_attempts[symbol] = metrics.subscription_attempts.get(symbol, 0) + 1

                    except Exception as e:
                        logger.error(f"❌ Failed to resubscribe to {symbol}: {e}")

        except Exception as e:
            logger.error(f"❌ Resubscription loop error: {e}")

            # Apply exponential backoff with jitter
            wait_ms = backoffs[min(idx, len(backoffs) - 1)]
            jitter_ms = random.randint(0, int(wait_ms * 0.1))  # 10% jitter
            total_wait_ms = wait_ms + jitter_ms

            logger.info(f"⏳ Backing off for {total_wait_ms}ms (attempt {idx + 1})")

            await asyncio.sleep(total_wait_ms / 1000)  # Convert to seconds
            idx += 1

class EnhancedSubscriptionManager:
    """Enhanced subscription manager with TypeScript-mirrored logic"""

    def __init__(self, websocket_url: str):
        self.connection = WebSocketConnection(websocket_url)
        self.metrics = MetricsTracker()
        self.running = False
        self.tasks: List[asyncio.Task] = []

        # Callbacks
        self.tick_callback = None
        self.ohlc_callback = None
        self.error_callback = None

    def set_callbacks(self, tick_cb=None, ohlc_cb=None, error_cb=None):
        """Set callback functions"""
        if tick_cb:
            self.tick_callback = tick_cb
        if ohlc_cb:
            self.ohlc_callback = ohlc_cb
        if error_cb:
            self.error_callback = error_cb

    async def handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type") or data.get("op")
            symbol = data.get("symbol")

            if msg_type == "tick" or msg_type == "price_update":
                if symbol:
                    self.metrics.update_tick(symbol)

                if self.tick_callback:
                    # Normalize to v1 schema
                    normalized_tick = {
                        "symbol": symbol,
                        "bid": data.get("bid"),
                        "ask": data.get("ask"),
                        "mid": (data.get("bid", 0) + data.get("ask", 0)) / 2 if data.get("bid") and data.get("ask") else None,
                        "ts_epoch_ms": int(time.time() * 1000),
                        "src": "metasocket"
                    }
                    await self.tick_callback(normalized_tick)

            elif msg_type == "ohlc" or msg_type == "candle":
                if self.ohlc_callback:
                    # Normalize to v1 schema
                    normalized_ohlc = {
                        "symbol": symbol,
                        "timeframe": data.get("timeframe", "M1"),
                        "open": data.get("open"),
                        "high": data.get("high"),
                        "low": data.get("low"),
                        "close": data.get("close"),
                        "volume": data.get("volume", 0),
                        "ts_epoch_ms": int(time.time() * 1000),
                        "src": "metasocket"
                    }
                    await self.ohlc_callback(normalized_ohlc)

        except json.JSONDecodeError:
            logger.warning(f"⚠️ Invalid JSON received: {message[:100]}...")
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
            if self.error_callback:
                await self.error_callback(e)

    async def message_listener(self):
        """Listen for incoming messages"""
        try:
            async for message in self.connection.websocket:
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ Message listener error: {e}")

    async def start(self):
        """Start the enhanced subscription manager"""
        logger.info("🚀 Starting enhanced subscription manager")

        self.running = True

        try:
            # Initial connection
            await self.connection.reopen()

            # Start background tasks
            self.tasks = [
                asyncio.create_task(resubscribe_loop(self.connection, self.metrics)),
                asyncio.create_task(self.message_listener()),
                asyncio.create_task(self.stats_reporter())
            ]

            # Wait for tasks
            await asyncio.gather(*self.tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ Enhanced subscription manager error: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop the subscription manager"""
        logger.info("🛑 Stopping enhanced subscription manager")

        self.running = False

        # Cancel tasks
        for task in self.tasks:
            task.cancel()

        # Close connection
        if self.connection.websocket:
            await self.connection.websocket.close()

    async def stats_reporter(self):
        """Periodic stats reporting"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Report every minute

                stats = self.metrics.get_health_stats()
                stale_count = len(stats["stale_symbols"])
                total_ticks = stats["total_ticks"]

                logger.info(f"📊 Stats: {total_ticks} ticks, {stale_count} stale symbols")

                if stale_count > 5:
                    logger.warning(f"⚠️ High stale symbol count: {stats['stale_symbols']}")

            except Exception as e:
                logger.error(f"❌ Stats reporter error: {e}")

    def get_health_status(self) -> dict:
        """Get current health status"""
        return {
            "connected": self.connection.is_open(),
            "running": self.running,
            "metrics": self.metrics.get_health_stats(),
            "symbols_configured": len(SYMBOLS)
        }

# Example usage matching TypeScript patterns
async def main():
    """Example usage"""

    # Create subscription manager
    manager = EnhancedSubscriptionManager("ws://185.244.67.11:8777")

    # Set callbacks
    async def handle_tick(tick):
        print(f"TICK: {tick['symbol']} = {tick['mid']:.5f}")

    async def handle_ohlc(ohlc):
        print(f"OHLC: {ohlc['symbol']} {ohlc['timeframe']} = {ohlc['close']:.5f}")

    async def handle_error(error):
        print(f"ERROR: {error}")

    manager.set_callbacks(
        tick_cb=handle_tick,
        ohlc_cb=handle_ohlc,
        error_cb=handle_error
    )

    # Start manager
    try:
        await manager.start()
    except KeyboardInterrupt:
        logger.info("⏹️ Stopping...")
    finally:
        await manager.stop()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())