#!/usr/bin/env python3
"""
MetaSocket Subscription System
Handles symbol subscriptions with auto-reconnect and backoff
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional, Set

import websockets

logger = logging.getLogger(__name__)


class MetaSocketSubscriptions:
    """Manages MetaSocket symbol subscriptions with resilience"""

    def __init__(self, host: str = "185.244.67.11", port: int = 8777):
        self.host = host
        self.port = port
        self.ws_url = f"ws://{host}:{port}"
        self.websocket = None

        # 22 active symbols (including XAGUSD, excluding USDCAD)
        self.active_symbols = [
            # Major Forex Pairs (6)
            "EURUSD",
            "GBPUSD",
            "USDCHF",
            "USDJPY",
            "AUDUSD",
            "NZDUSD",
            # Cross Pairs (10)
            "EURJPY",
            "GBPJPY",
            "EURGBP",
            "EURAUD",
            "GBPCAD",
            "AUDJPY",
            "NZDJPY",
            "CHFJPY",
            "CADJPY",
            "AUDCAD",
            # Additional Pairs (2)
            "USDCNH",
            "AUDNZD",
            # Precious Metals (2)
            "XAUUSD",
            "XAGUSD",
        ]

        # Track subscription status
        self.subscribed_symbols: Set[str] = set()
        self.subscription_timestamps: Dict[str, float] = {}
        self.last_tick_timestamps: Dict[str, float] = {}

        # Reconnect backoff settings
        self.reconnect_delays = [1, 2, 5, 10, 30]  # seconds
        self.current_delay_index = 0
        self.max_delay = 30

        # Callbacks for different event types
        self.tick_callback: Optional[Callable] = None
        self.ohlc_callback: Optional[Callable] = None
        self.position_callback: Optional[Callable] = None

        # Connection health
        self.connected = False
        self.last_heartbeat = 0

    def set_callbacks(self, tick_cb=None, ohlc_cb=None, position_cb=None):
        """Set callback functions for different event types"""
        if tick_cb:
            self.tick_callback = tick_cb
        if ohlc_cb:
            self.ohlc_callback = ohlc_cb
        if position_cb:
            self.position_callback = position_cb

    async def connect(self):
        """Establish WebSocket connection with backoff retry"""
        while not self.connected:
            try:
                logger.info(f"Connecting to MetaSocket at {self.ws_url}")

                self.websocket = await websockets.connect(
                    self.ws_url, ping_interval=20, ping_timeout=10, close_timeout=5
                )

                self.connected = True
                self.current_delay_index = 0  # Reset backoff on success
                self.last_heartbeat = time.time()

                logger.info("✅ MetaSocket connection established")

                # Start subscription process
                await self.subscribe_all_symbols()

                # Start message handler
                asyncio.create_task(self.message_handler())

                return True

            except Exception as e:
                logger.error(f"❌ MetaSocket connection failed: {e}")

                # Calculate backoff delay with jitter
                base_delay = self.reconnect_delays[min(self.current_delay_index, len(self.reconnect_delays) - 1)]
                jitter = random.uniform(0.9, 1.1)  # ±10% jitter
                delay = min(base_delay * jitter, self.max_delay)

                logger.info(f"⏳ Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

                self.current_delay_index = min(self.current_delay_index + 1, len(self.reconnect_delays) - 1)

    async def subscribe_all_symbols(self):
        """Subscribe to price tracking and OHLC for all active symbols"""
        if not self.websocket:
            logger.error("❌ No websocket connection for subscriptions")
            return

        logger.info(f"📡 Subscribing to {len(self.active_symbols)} symbols")

        for symbol in self.active_symbols:
            await self.subscribe_symbol(symbol)
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.1)

        # Subscribe to trade events
        await self.subscribe_trade_events()

        logger.info(f"✅ Subscribed to all symbols and trade events")

    async def subscribe_symbol(self, symbol: str):
        """Subscribe to price tracking and OHLC for a single symbol"""
        try:
            # Subscribe to price tracking
            price_msg = {"action": "TRACK_PRICES", "symbol": symbol, "ts": int(time.time() * 1000)}
            await self.websocket.send(json.dumps(price_msg))

            # Subscribe to OHLC if available, otherwise we'll build from ticks
            ohlc_msg = {"action": "TRACK_OHLC", "symbol": symbol, "timeframe": "M1", "ts": int(time.time() * 1000)}
            await self.websocket.send(json.dumps(ohlc_msg))

            # Track subscription
            self.subscribed_symbols.add(symbol)
            self.subscription_timestamps[symbol] = time.time()

            logger.debug(f"📊 Subscribed to {symbol}")

        except Exception as e:
            logger.error(f"❌ Failed to subscribe to {symbol}: {e}")

    async def subscribe_trade_events(self):
        """Subscribe to position/trade events"""
        try:
            trade_msg = {"action": "TRACK_TRADE_EVENTS", "ts": int(time.time() * 1000)}
            await self.websocket.send(json.dumps(trade_msg))
            logger.debug("📈 Subscribed to trade events")

        except Exception as e:
            logger.error(f"❌ Failed to subscribe to trade events: {e}")

    async def message_handler(self):
        """Handle incoming messages from MetaSocket"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.process_message(data)

                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON received: {message[:100]}...")
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 MetaSocket connection closed")
            self.connected = False
            # Trigger reconnection
            asyncio.create_task(self.connect())

        except Exception as e:
            logger.error(f"❌ Message handler error: {e}")
            self.connected = False
            asyncio.create_task(self.connect())

    async def process_message(self, data: dict):
        """Process incoming message and route to appropriate callback"""
        msg_type = data.get("type")
        symbol = data.get("symbol")
        timestamp = time.time()

        # Update heartbeat
        self.last_heartbeat = timestamp

        # Update last tick timestamp for symbol health checks
        if symbol:
            self.last_tick_timestamps[symbol] = timestamp

        if msg_type == "tick" and self.tick_callback:
            # Normalize tick data
            normalized_tick = {
                "symbol": symbol,
                "bid": data.get("bid"),
                "ask": data.get("ask"),
                "mid": (data.get("bid", 0) + data.get("ask", 0)) / 2 if data.get("bid") and data.get("ask") else None,
                "ts_epoch_ms": int(timestamp * 1000),
                "src": "metasocket",
            }
            await self.tick_callback(normalized_tick)

        elif msg_type == "ohlc" and self.ohlc_callback:
            # Normalize OHLC data
            normalized_ohlc = {
                "symbol": symbol,
                "timeframe": data.get("timeframe", "M1"),
                "open": data.get("open"),
                "high": data.get("high"),
                "low": data.get("low"),
                "close": data.get("close"),
                "volume": data.get("volume", 0),
                "ts_epoch_ms": int(timestamp * 1000),
                "src": "metasocket",
            }
            await self.ohlc_callback(normalized_ohlc)

        elif msg_type in ["position_open", "position_close", "trade_event"] and self.position_callback:
            # Normalize position event
            normalized_position = {
                "ticket": data.get("ticket"),
                "symbol": symbol,
                "side": data.get("side"),
                "state": "OPEN" if msg_type == "position_open" else "CLOSE",
                "reason": data.get("reason", "other"),
                "price": data.get("price"),
                "volume": data.get("volume"),
                "sl": data.get("sl"),
                "tp": data.get("tp"),
                "ts_epoch_ms": int(timestamp * 1000),
                "src": "metasocket",
            }
            await self.position_callback(normalized_position)

    def get_health_status(self) -> dict:
        """Get subscription health status"""
        current_time = time.time()

        # Calculate ages and tick rates
        last_event_ages = {}
        tick_rates = {}

        for symbol in self.active_symbols:
            last_tick = self.last_tick_timestamps.get(symbol, 0)
            age_ms = int((current_time - last_tick) * 1000)
            last_event_ages[symbol] = age_ms

            # Simple tick rate calculation (you might want to use EWMA)
            if last_tick > 0 and (current_time - last_tick) < 60:
                # Rough estimate: if we got a tick recently, assume decent rate
                tick_rates[symbol] = 1.0  # 1 tick per second average
            else:
                tick_rates[symbol] = 0.0

        max_age = max(last_event_ages.values()) if last_event_ages else 0

        subscriptions = []
        for symbol in self.active_symbols:
            subscriptions.append(
                {
                    "symbol": symbol,
                    "prices": symbol in self.subscribed_symbols,
                    "ohlc": symbol in self.subscribed_symbols,  # Assuming same for now
                    "last_ts_ms": int(self.last_tick_timestamps.get(symbol, 0) * 1000),
                }
            )

        return {
            "last_event_age_ms": max_age,
            "event_lag_ms_p95": max_age,  # Simplified for now
            "tick_rate_per_symbol": tick_rates,
            "account_heartbeat_age_ms": int((current_time - self.last_heartbeat) * 1000),
            "subscriptions": subscriptions,
            "connected": self.connected,
        }

    async def health_check_loop(self):
        """Periodically check symbol health and resubscribe if needed"""
        while True:
            try:
                current_time = time.time()

                for symbol in self.active_symbols:
                    last_tick = self.last_tick_timestamps.get(symbol, 0)
                    age = current_time - last_tick

                    # If no ticks for 3+ seconds, resubscribe
                    if age > 3 and self.connected:
                        logger.warning(f"⚠️ No ticks for {symbol} in {age:.1f}s, resubscribing")
                        await self.subscribe_symbol(symbol)

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                await asyncio.sleep(5)

    async def start(self):
        """Start the subscription system"""
        logger.info("🚀 Starting MetaSocket subscription system")

        # Start connection and health check loops
        await asyncio.gather(self.connect(), self.health_check_loop())


# Example usage
if __name__ == "__main__":

    async def tick_handler(tick):
        print(f"TICK: {tick['symbol']} {tick['bid']}/{tick['ask']}")

    async def ohlc_handler(ohlc):
        print(f"OHLC: {ohlc['symbol']} OHLC={ohlc['open']}/{ohlc['high']}/{ohlc['low']}/{ohlc['close']}")

    async def position_handler(pos):
        print(f"POSITION: {pos['symbol']} {pos['state']} ticket={pos['ticket']}")

    subs = MetaSocketSubscriptions()
    subs.set_callbacks(tick_handler, ohlc_handler, position_handler)

    asyncio.run(subs.start())
