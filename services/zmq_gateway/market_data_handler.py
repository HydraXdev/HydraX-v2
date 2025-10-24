"""
Market Data Handler - Dual Ingress Architecture
- Port 5556 (PULL): ticks, heartbeats from EA
- Port 5560 (PULL): position_update from EA
- Port 5570 (PUB): broadcasts all data to subscribers
"""
import asyncio
import json
import logging
import sqlite3
import time
from collections import defaultdict
from typing import Dict

import zmq
import zmq.asyncio

from .config import DB_PATH, PORT_MARKET_DATA_IN, PORT_METRICS_IN, PORT_MARKET_DATA_OUT

logger = logging.getLogger(__name__)


class MarketDataHandler:
    """Handles market data ingestion and republishing"""

    def __init__(self, context: zmq.asyncio.Context):
        self.context = context
        self.tick_receiver = None  # PULL on 5556
        self.metrics_receiver = None  # PULL on 5560
        self.publisher = None  # PUB on 5570
        self.mirror = None  # IPC PUB

        # Statistics
        self.message_count = 0
        self.tick_count = 0
        self.ohlc_count = 0
        self.heartbeat_count = 0
        self.position_update_count = 0
        self.quotes: Dict[str, Dict] = {}  # symbol -> {bid, ask}

        # Tracking
        self.last_stats_log = time.time()

    async def start(self):
        """Initialize and bind sockets"""
        # PULL socket for ticks/heartbeats from EA (5556)
        self.tick_receiver = self.context.socket(zmq.PULL)
        self.tick_receiver.setsockopt(zmq.RCVHWM, 10000)
        self.tick_receiver.bind(f"tcp://*:{PORT_MARKET_DATA_IN}")
        logger.info(f"✅ Bound tick PULL socket to port {PORT_MARKET_DATA_IN}")

        # PULL socket for position_update from EA (5560)
        self.metrics_receiver = self.context.socket(zmq.PULL)
        self.metrics_receiver.setsockopt(zmq.RCVHWM, 10000)
        self.metrics_receiver.bind(f"tcp://*:{PORT_METRICS_IN}")
        logger.info(f"✅ Bound metrics PULL socket to port {PORT_METRICS_IN}")

        # PUB socket - broadcasts to subscribers (5570)
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.setsockopt(zmq.SNDHWM, 10000)
        self.publisher.bind(f"tcp://*:{PORT_MARKET_DATA_OUT}")
        logger.info(f"✅ Bound PUB socket to port {PORT_MARKET_DATA_OUT}")

        # IPC PUB mirror - for debugging/monitoring
        self.mirror = self.context.socket(zmq.PUB)
        self.mirror.bind("ipc:///tmp/tick_mirror")
        logger.info("✅ Bound IPC mirror: ipc:///tmp/tick_mirror")

        # Small warm-up delay for PUB socket
        await asyncio.sleep(0.2)

        logger.info("📡 Market data bridge ready (dual ingress)")

    async def process_messages(self):
        """Main message processing loop - polls both ingress sockets"""
        poller = zmq.asyncio.Poller()
        poller.register(self.tick_receiver, zmq.POLLIN)
        poller.register(self.metrics_receiver, zmq.POLLIN)

        while True:
            try:
                # Poll both sockets with 1 second timeout
                events = await poller.poll(timeout=1000)

                for socket, _ in events:
                    # Receive message
                    message = await socket.recv_string()
                    self.message_count += 1

                    # Determine source and route message
                    if socket == self.tick_receiver:
                        # From port 5556: ticks, heartbeats, OHLC
                        if message.startswith("OHLC "):
                            await self._handle_ohlc(message)
                        elif message.startswith("HEARTBEAT"):
                            await self._handle_heartbeat_string(message)
                        else:
                            await self._handle_json_message(message)

                    elif socket == self.metrics_receiver:
                        # From port 5560: position_update
                        await self._handle_json_message(message)

                    # Republish to PUB socket for subscribers
                    await self.publisher.send_string(message)
                    await self.mirror.send_string(message)

                # Log statistics periodically
                if time.time() - self.last_stats_log > 60:
                    logger.info(
                        f"📊 Stats: {self.message_count} msgs | "
                        f"{self.tick_count} ticks | "
                        f"{self.ohlc_count} OHLC | "
                        f"{self.heartbeat_count} heartbeats | "
                        f"{self.position_update_count} position updates"
                    )
                    self.last_stats_log = time.time()

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await asyncio.sleep(1)

    async def _handle_ohlc(self, message: str):
        """Handle OHLC candle messages"""
        self.ohlc_count += 1

        # Log every 100th OHLC
        if self.message_count % 100 == 1:
            try:
                ohlc_data = json.loads(message[5:])
                logger.debug(
                    f"📊 OHLC: {ohlc_data.get('symbol')} "
                    f"{ohlc_data.get('timeframe')}"
                )
            except:
                pass

    async def _handle_heartbeat_string(self, message: str):
        """Handle string heartbeat messages"""
        self.heartbeat_count += 1

        if self.message_count % 30 == 0:
            logger.debug(
                f"💓 Heartbeat #{self.message_count} | "
                f"Ticks: {self.tick_count}, OHLC: {self.ohlc_count}"
            )

    async def _handle_json_message(self, message: str):
        """Handle JSON-formatted messages (ticks, heartbeats)"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")

            # Handle heartbeat messages
            if msg_type == "heartbeat":
                await self._handle_heartbeat_json(data, message)
            elif msg_type == "position_update":
                # EA v3.005 sends position updates every 1s per position
                await self._handle_position_update(data, message)
            else:
                # Handle tick data
                await self._handle_tick(data, message)

        except json.JSONDecodeError:
            logger.warning(f"Non-JSON message: {message[:100]}...")

    async def _handle_heartbeat_json(self, data: dict, original_message: str):
        """Handle JSON heartbeat messages"""
        self.heartbeat_count += 1

        # Update database with heartbeat data
        if await self._update_ea_heartbeat(data):
            # Log every 5th heartbeat
            if self.heartbeat_count % 5 == 0:
                uuid = data.get("uuid", "UNKNOWN")
                balance = data.get("balance", 0.0)
                equity = data.get("equity", 0.0)
                positions = data.get("positions", 0)
                logger.info(
                    f"💓 Heartbeat #{self.heartbeat_count} | "
                    f"{uuid} | Bal: ${balance:.2f} | "
                    f"Eq: ${equity:.2f} | Pos: {positions}"
                )

        # ✅ SYNC POSITION UPDATES TO FIREBASE
        # Check if heartbeat contains position-specific data
        position_list = data.get("position_list", [])
        if position_list:
            await self._sync_positions_to_firebase(position_list)

    async def _handle_position_update(self, data: dict, original_message: str):
        """Handle EA v3.005 position_update messages (1s per open position)"""
        self.position_update_count += 1

        try:
            fire_id = data.get("fire_id", "")
            current_price = data.get("current_price")
            pnl = data.get("pnl")
            ticket = data.get("ticket", 0)

            if not fire_id or current_price is None or pnl is None:
                logger.debug(f"Incomplete position_update: fire_id={fire_id}, price={current_price}, pnl={pnl}")
                return

            # Sync to BOTH Firebase AND Database
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._sync_position_update_to_firebase_and_db,
                fire_id,
                current_price,
                pnl,
                ticket
            )

            # Log every 50th position update
            if self.position_update_count % 50 == 0:
                logger.info(f"📍 Position update #{self.position_update_count}: {fire_id} → ${pnl:.2f}")

        except Exception as e:
            logger.error(f"Error handling position_update: {e}")

    def _sync_position_update_to_firebase_and_db(self, fire_id: str, current_price: float, pnl: float, ticket: int):
        """Synchronous sync for individual position update to BOTH Firebase AND Database"""
        try:
            import sys
            import time
            sys.path.insert(0, '/root/HydraX-v2')
            from firebase_backend import update_active_trade_price

            # Update Firebase active_trades
            update_active_trade_price(
                trade_id=fire_id,
                current_price=float(current_price),
                equity=float(pnl)
            )

            # Update Database live_positions
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE live_positions
                SET current_price = ?, current_pnl = ?, last_update = ?
                WHERE fire_id = ? AND status = 'OPEN'
            """, (current_price, pnl, int(time.time()), fire_id))
            conn.commit()
            conn.close()

            logger.debug(f"✅ Synced {fire_id} (ticket {ticket}) → ${pnl:.2f} to Firebase + DB")

        except Exception as e:
            logger.error(f"Position update sync failed for {fire_id}: {e}")

    def _sync_position_update_to_firebase(self, fire_id: str, current_price: float, pnl: float, ticket: int):
        """DEPRECATED: Use _sync_position_update_to_firebase_and_db instead"""
        self._sync_position_update_to_firebase_and_db(fire_id, current_price, pnl, ticket)

    async def _handle_tick(self, data: dict, original_message: str):
        """Handle tick data messages"""
        # Accumulate quotes for symbols
        if "symbol" in data and "bid" in data and "ask" in data:
            symbol = data["symbol"]
            self.quotes[symbol] = {
                "bid": float(data["bid"]),
                "ask": float(data["ask"])
            }

        self.tick_count += 1

    async def _update_ea_heartbeat(self, heartbeat_data: dict) -> bool:
        """Update EA instance with heartbeat data"""
        try:
            # Run database operation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._update_ea_heartbeat_sync,
                heartbeat_data
            )
        except Exception as e:
            logger.error(f"Failed to update EA heartbeat: {e}")
            return False

    def _update_ea_heartbeat_sync(self, heartbeat_data: dict) -> bool:
        """Synchronous database update for heartbeat"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()

            uuid = heartbeat_data.get("uuid")
            balance = heartbeat_data.get("balance", 0.0)
            equity = heartbeat_data.get("equity", 0.0)
            positions = heartbeat_data.get("positions", 0)
            # ALWAYS use server time for last_seen
            timestamp = int(time.time())

            # Update or insert EA instance with heartbeat data
            cursor.execute(
                """
                INSERT INTO ea_instances
                (target_uuid, last_balance, last_equity, last_seen, updated_at, open_positions)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(target_uuid) DO UPDATE SET
                    last_balance = excluded.last_balance,
                    last_equity = excluded.last_equity,
                    last_seen = excluded.last_seen,
                    updated_at = excluded.updated_at,
                    open_positions = excluded.open_positions
            """,
                (uuid, balance, equity, timestamp, timestamp, positions),
            )

            # Get user_id for this EA
            cursor.execute("SELECT user_id FROM ea_instances WHERE target_uuid = ?", (uuid,))
            result = cursor.fetchone()

            conn.commit()
            conn.close()

            # ✅ SYNC USER BALANCE/EQUITY TO FIREBASE
            if result and result[0]:
                user_id = result[0]
                try:
                    import sys
                    sys.path.insert(0, '/root/HydraX-v2')
                    from firebase_backend import (
                        update_user_data,
                        update_peak_equity_and_drawdown,
                        sync_fire_mode_status,
                        sync_autofire_settings_to_db
                    )

                    # Update balance and equity
                    update_user_data(user_id, {
                        'balance': float(balance),
                        'equity': float(equity)
                    })

                    # Update peak equity and drawdown tracking
                    if equity > 0:
                        update_peak_equity_and_drawdown(user_id, float(equity))

                    # Sync fire mode status (happens every heartbeat, but cached in Firebase)
                    sync_fire_mode_status(user_id)

                    # Sync autofire settings from Firebase to database (ensures UI changes take effect)
                    sync_autofire_settings_to_db(user_id)

                    logger.debug(f"✅ Firebase: User {user_id} → Bal: ${balance:.2f}, Eq: ${equity:.2f}")
                except Exception as fb_error:
                    logger.error(f"Firebase user update failed: {fb_error}")

            return True

        except Exception as e:
            logger.error(f"Database update failed: {e}")
            return False

    async def _sync_positions_to_firebase(self, position_list: list):
        """Sync position updates to Firebase"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._sync_positions_to_firebase_sync,
                position_list
            )
        except Exception as e:
            logger.error(f"Failed to sync positions to Firebase: {e}")

    def _sync_positions_to_firebase_sync(self, position_list: list):
        """Synchronous Firebase sync for positions"""
        try:
            # Import Firebase backend
            import sys
            sys.path.insert(0, '/root/HydraX-v2')
            from firebase_backend import update_active_trade_price

            # Get fire_id mappings from database
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()

            for position in position_list:
                ticket = position.get("ticket")
                current_price = position.get("current_price")
                pnl = position.get("pnl")

                if not ticket or current_price is None or pnl is None:
                    continue

                # Get fire_id for this ticket
                cursor.execute(
                    "SELECT fire_id FROM fires WHERE ticket = ? AND status = 'FILLED'",
                    (ticket,)
                )
                result = cursor.fetchone()

                if result:
                    fire_id = result[0]
                    # Sync to Firebase
                    update_active_trade_price(
                        trade_id=fire_id,
                        current_price=float(current_price),
                        equity=float(pnl)
                    )
                    logger.debug(f"✅ Firebase: Updated {fire_id} → ${pnl:.2f}")

            conn.close()

        except Exception as e:
            logger.error(f"Firebase sync failed: {e}")

    async def stop(self):
        """Clean shutdown"""
        if self.tick_receiver:
            self.tick_receiver.close()
        if self.metrics_receiver:
            self.metrics_receiver.close()
        if self.publisher:
            self.publisher.close()
        if self.mirror:
            self.mirror.close()
        logger.info("Market data handler stopped")

    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "message_count": self.message_count,
            "tick_count": self.tick_count,
            "ohlc_count": self.ohlc_count,
            "heartbeat_count": self.heartbeat_count,
            "position_update_count": self.position_update_count,
            "symbols_tracked": len(self.quotes)
        }
