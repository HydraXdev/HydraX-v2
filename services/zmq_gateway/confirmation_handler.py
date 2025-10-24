"""
Confirmation Handler - Port 5558 (PULL)
Receives trade confirmations and lifecycle events from EA
"""
import asyncio
import json
import logging
import re
import psycopg2
import psycopg2.extras
import sqlite3
import time

import zmq
import zmq.asyncio

from .config import DATABASE_URL, PORT_CONFIRMATIONS

logger = logging.getLogger(__name__)


class ConfirmationHandler:
    """Handles trade confirmations from EA"""

    def __init__(self, context: zmq.asyncio.Context):
        self.context = context
        self.receiver = None

        # Statistics
        self.confirmations_received = 0
        self.positions_opened = 0
        self.positions_closed = 0
        self.hybrid_events = 0
        self.heartbeat_metrics_received = 0

    async def start(self):
        """Initialize and bind sockets"""
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(f"tcp://*:{PORT_CONFIRMATIONS}")
        logger.info(f"✅ Bound PULL socket to port {PORT_CONFIRMATIONS}")

        # Ensure database tables exist
        await self._ensure_tables()

        logger.info("🎧 Confirmation listener ready")

    async def process_messages(self):
        """Main message processing loop"""
        while True:
            try:
                raw = await self.receiver.recv()
                msg = self._parse_json_loose(raw)

                if not msg:
                    continue

                msg_type = msg.get("type", "").lower()

                # Route to appropriate handler
                if msg_type == "confirmation":
                    await self._handle_confirmation(msg)
                elif msg_type == "position_opened":
                    # EA v3.005 sends position_opened - treat as confirmation
                    await self._handle_confirmation(msg)
                elif msg_type == "position_closed":
                    await self._handle_position_closed(msg)
                elif msg_type == "trailing_armed":
                    # EA v3.013 trailing stops - position reached breakeven
                    await self._handle_trailing_armed(msg)
                elif msg_type == "trailing_active":
                    # Trailing stop activated (first SL move)
                    await self._handle_trailing_event(msg, "ACTIVE")
                elif msg_type == "trailing_updated":
                    # Trailing SL moved (following price)
                    await self._handle_trailing_event(msg, "UPDATED")
                elif msg_type == "trailing_protection":
                    # Protection threshold achieved (slot unlock milestone)
                    await self._handle_trailing_event(msg, "PROTECTION")
                elif msg_type == "trailing_breakeven":
                    # Explicit breakeven notification (STEP style)
                    await self._handle_trailing_event(msg, "BREAKEVEN")
                elif msg_type == "trailing_exit":
                    # Position closed via trailing SL
                    await self._handle_trailing_event(msg, "EXIT")
                elif msg_type == "hybrid_event":
                    await self._handle_hybrid_event(msg)
                elif msg_type == "close_confirmation":
                    await self._handle_close_confirmation(msg)
                elif msg_type == "heartbeat_metrics":
                    # EA sends enhanced heartbeat with positions array
                    await self._handle_heartbeat_metrics(msg)
                elif msg_type == "pong":
                    await self._handle_pong(msg)
                else:
                    logger.warning(f"Unknown message type: {msg_type}")

            except Exception as e:
                logger.error(f"Error processing confirmation: {e}")
                await asyncio.sleep(1)

    def _parse_json_loose(self, b: bytes) -> dict:
        """Parse JSON with tolerance for encoding issues"""
        s = b.decode("utf-8", "ignore").strip()
        try:
            return json.loads(s)
        except Exception:
            try:
                # Try replacing single quotes with double quotes
                return json.loads(re.sub(r"'", '"', s))
            except Exception as e:
                logger.error(f"JSON parse failed: {e} | payload={s[:500]}")
                return None

    async def _handle_confirmation(self, msg: dict):
        """Handle fire confirmation messages"""
        fire_id = msg.get("fire_id")

        # Security: Log all confirmations with full data for debugging
        logger.info(f"🔍 CONFIRMATION: fire_id={fire_id}, type={msg.get('type')}")
        logger.info(f"📨 FULL EA CONFIRMATION: {msg}")

        if not fire_id:
            logger.warning(f"Confirmation without fire_id: {msg}")
            return

        # Get ticket and user UUID
        ticket = msg.get("ticket", 0)
        user_uuid = msg.get("user_uuid") or msg.get("target_uuid") or msg.get("uuid")

        # 🚨 REMOVED TEST BLOCKER - Allow all confirmations for debugging
        # Even test signals should update database with failure status

        # Map status - EA v3.005 sends different formats
        status = (msg.get("status") or "").lower()
        command_type = (msg.get("command_type") or "").lower()

        # Check multiple status fields for success
        if (status in ("success", "filled", "ok") or
            command_type == "fire" or
            msg.get("type") == "position_opened"):
            db_status = "FILLED"
        elif status in ("failed", "rejected", "error"):
            db_status = "FAILED"
        else:
            db_status = "UNKNOWN"

        # Price can be in multiple fields (EA sends different names)
        price = msg.get("price") or msg.get("entry_price") or msg.get("open_price") or msg.get("fill_price")

        # IMPORTANT: If price is 0 or None, don't overwrite existing price
        # EA sends two messages: first with price, second without
        if not price or price == 0:
            price = None  # Signal to preserve existing price

        lot = msg.get("lot") or msg.get("volume") or msg.get("lot_size")

        # Update database
        await self._update_fire_status(
            fire_id, db_status, ticket, price, lot, user_uuid
        )

        self.confirmations_received += 1
        if db_status == "FILLED":
            self.positions_opened += 1

            # ✅ CREATE FIREBASE ACTIVE_TRADES DOCUMENT
            # When position_opened is received, create the Firebase document
            # so position_update messages can sync to it
            if msg.get("type") == "position_opened":
                await self._create_firebase_active_trade(
                    fire_id=fire_id,
                    symbol=msg.get("symbol"),
                    direction=msg.get("direction"),
                    entry_price=msg.get("entry_price"),
                    volume=msg.get("volume"),
                    timestamp=msg.get("timestamp")
                )

    async def _handle_position_closed(self, msg: dict):
        """Handle position closure events"""
        ticket = msg.get("ticket")
        fire_id = msg.get("fire_id")
        symbol = msg.get("symbol")
        volume = msg.get("volume", 0)
        close_price = msg.get("close_price", 0)
        profit = msg.get("profit", 0)
        reason = msg.get("reason", "MANUAL")
        uuid = msg.get("uuid")
        timestamp = msg.get("timestamp", int(time.time()))

        if not ticket:
            logger.warning(f"position_closed without ticket: {msg}")
            return

        logger.info(f"📊 CLOSED: ticket={ticket}, reason={reason}, P&L={profit:.2f}")

        # Update database
        await self._record_position_closure(
            ticket, fire_id, symbol, volume, close_price, profit, reason, uuid, timestamp
        )

        self.positions_closed += 1

    async def _handle_hybrid_event(self, msg: dict):
        """Handle hybrid position management events"""
        event_type = msg.get("event")
        ticket = msg.get("ticket")
        fire_id = msg.get("fire_id")
        volume = msg.get("volume", 0)
        pips = msg.get("pips", 0)
        uuid = msg.get("target_uuid")
        timestamp = msg.get("timestamp", int(time.time()))

        if not event_type or not ticket:
            logger.warning(f"Invalid hybrid_event: {msg}")
            return

        logger.info(f"🎯 HYBRID: {event_type} ticket={ticket} @ {pips:.1f} pips")

        # Record hybrid event
        await self._record_hybrid_event(
            ticket, fire_id, event_type, volume, pips, timestamp, uuid
        )

        self.hybrid_events += 1

    async def _handle_trailing_armed(self, msg: dict):
        """
        Handle trailing_armed event from EA v3.013

        This event is sent when trailing stops are ARMED (position +10 pips, SL at breakeven).
        We free the slot immediately since position is now risk-free.
        """
        fire_id = msg.get("fire_id")
        ticket = msg.get("ticket")
        arm_threshold_pips = msg.get("arm_threshold_pips", 10)
        current_price = msg.get("current_price", 0)

        logger.info(f"🎯 TRAILING ARMED: fire_id={fire_id} ticket={ticket} @ +{arm_threshold_pips} pips (breakeven)")
        logger.info(f"📨 FULL TRAILING ARMED EVENT: {msg}")

        if not fire_id:
            logger.warning(f"trailing_armed without fire_id: {msg}")
            return

        # Get user_id from fire_id or message
        # fire_id format: ELITE_RAPID_EURUSD_123 or similar
        # We need to look up the user_id from the fires table
        user_id = await self._get_user_id_from_fire_id(fire_id)

        if not user_id:
            logger.warning(f"Could not find user_id for fire_id {fire_id}")
            return

        # Release the risk slot (Stage 1: Smart Unlock)
        # Import fire_mode_database here to avoid circular imports
        try:
            import sys
            sys.path.insert(0, '/root/HydraX-v2')
            from src.bitten_core.fire_mode_database import fire_mode_db

            # mission_id = fire_id for our system
            success = fire_mode_db.release_risk_slot(user_id, fire_id)

            if success:
                logger.info(f"✅ RISK SLOT FREED: User {user_id} can now take another trade (position at breakeven)")
            else:
                logger.warning(f"Failed to release risk slot for user {user_id}, fire_id {fire_id}")

        except Exception as e:
            logger.error(f"Error releasing risk slot: {e}")

    async def _handle_trailing_event(self, msg: dict, event_type: str):
        """
        Handle all trailing stop events from EA v3.013

        Events: ACTIVE, UPDATED, PROTECTION, BREAKEVEN, EXIT
        These events provide real-time tracking of trailing stop performance
        """
        fire_id = msg.get("fire_id")
        ticket = msg.get("ticket")
        symbol = msg.get("symbol", "")
        direction = msg.get("direction", "")

        # Event-specific data
        old_sl = msg.get("old_sl", 0)
        new_sl = msg.get("new_sl", 0)
        current_price = msg.get("current_price", 0)
        current_profit_pips = msg.get("current_profit_pips", 0)
        style = msg.get("style", "")

        # Log event with emoji based on type
        event_emojis = {
            "ACTIVE": "🎯",
            "UPDATED": "📈",
            "PROTECTION": "🛡️",
            "BREAKEVEN": "⚡",
            "EXIT": "🏁"
        }
        emoji = event_emojis.get(event_type, "📊")

        logger.info(f"{emoji} TRAILING {event_type}: {symbol} {direction} ticket={ticket} @ {current_profit_pips:.1f} pips")
        logger.info(f"📨 FULL TRAILING EVENT: {msg}")

        if not fire_id or not ticket:
            logger.warning(f"Trailing event missing fire_id or ticket: {msg}")
            return

        # Store event in database for tracking
        await self._record_trailing_event(
            fire_id, ticket, event_type, symbol, direction,
            old_sl, new_sl, current_price, current_profit_pips, style, msg
        )

        # Send Telegram notification for important milestones
        if event_type in ["ACTIVE", "PROTECTION", "EXIT"]:
            await self._send_trailing_notification(
                fire_id, ticket, event_type, symbol, direction,
                current_profit_pips, new_sl, style
            )

    async def _record_trailing_event(self, fire_id: str, ticket: int, event_type: str,
                                     symbol: str, direction: str, old_sl: float, new_sl: float,
                                     current_price: float, current_profit_pips: float,
                                     style: str, full_msg: dict):
        """Store trailing event in database for analytics"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._record_trailing_event_sync,
            fire_id, ticket, event_type, symbol, direction,
            old_sl, new_sl, current_price, current_profit_pips, style, json.dumps(full_msg)
        )

    def _record_trailing_event_sync(self, fire_id: str, ticket: int, event_type: str,
                                    symbol: str, direction: str, old_sl: float, new_sl: float,
                                    current_price: float, current_profit_pips: float,
                                    style: str, full_msg_json: str):
        """Synchronous database insert for trailing events"""
        try:
            import sqlite3
            DB_PATH = "/root/HydraX-v2/bitten.db"
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # Create table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trailing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fire_id TEXT NOT NULL,
                    ticket INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    symbol TEXT,
                    direction TEXT,
                    old_sl REAL,
                    new_sl REAL,
                    current_price REAL,
                    current_profit_pips REAL,
                    style TEXT,
                    full_msg_json TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)

            # Insert event
            cur.execute("""
                INSERT INTO trailing_events
                (fire_id, ticket, event_type, symbol, direction, old_sl, new_sl,
                 current_price, current_profit_pips, style, full_msg_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fire_id, ticket, event_type, symbol, direction, old_sl, new_sl,
                  current_price, current_profit_pips, style, full_msg_json))

            conn.commit()
            conn.close()

            logger.info(f"✅ Trailing event stored: {fire_id} - {event_type}")

        except Exception as e:
            logger.error(f"Failed to record trailing event: {e}")

    async def _send_trailing_notification(self, fire_id: str, ticket: int, event_type: str,
                                          symbol: str, direction: str, current_profit_pips: float,
                                          new_sl: float, style: str):
        """Send Firebase push notification for important trailing events"""
        try:
            # Get user_id from fire_id
            user_id = await self._get_user_id_from_fire_id(fire_id)
            if not user_id:
                return

            # Import Firebase notification functions
            import sys
            sys.path.insert(0, '/root/HydraX-v2')
            from firebase_notifications import (
                send_trailing_notification,
                update_trailing_status_firestore,
                create_trailing_activity_event
            )

            # Map event types
            firebase_event_type = {
                "ACTIVE": "ARMED",
                "PROTECTION": "PROTECTION",
                "EXIT": "EXIT"
            }.get(event_type, event_type)

            # Send Firebase Cloud Messaging notification
            send_trailing_notification(
                user_id=user_id,
                fire_id=fire_id,
                event_type=firebase_event_type,
                symbol=symbol,
                direction=direction,
                ticket=ticket,
                current_profit_pips=current_profit_pips,
                new_sl=new_sl if event_type == "ACTIVE" else None,
                style=style
            )

            # Update Firestore trailing status
            firestore_status = {
                "ACTIVE": "ARMED",
                "PROTECTION": "PROTECTED",
                "EXIT": "CLOSED"
            }.get(event_type, "ACTIVE")

            update_trailing_status_firestore(
                fire_id=fire_id,
                user_id=user_id,
                trailing_status=firestore_status,
                current_profit_pips=current_profit_pips,
                new_sl=new_sl if event_type == "ACTIVE" else None
            )

            # Create activity feed event
            create_trailing_activity_event(
                user_id=user_id,
                fire_id=fire_id,
                event_type=firebase_event_type,
                symbol=symbol,
                direction=direction,
                ticket=ticket,
                current_profit_pips=current_profit_pips
            )

            logger.info(f"✅ Firebase notifications sent: {firebase_event_type} for {fire_id}")

        except Exception as e:
            logger.error(f"Failed to send Firebase notifications: {e}")

    async def _handle_close_confirmation(self, msg: dict):
        """Handle close_ticket and close_all confirmations"""
        command_type = msg.get("command_type")
        status = msg.get("status", "").lower()
        message = msg.get("message", "")

        logger.info(f"📝 CLOSE: {command_type} {status} - {message}")

    async def _handle_pong(self, msg: dict):
        """Handle ping response"""
        ping_id = msg.get("ping_id")
        uuid = msg.get("user_uuid")

        logger.debug(f"🏓 PONG: {ping_id} from {uuid}")

        # Update EA last_seen if needed
        if uuid:
            await self._update_ea_last_seen(uuid)

    async def _update_fire_status(self, fire_id: str, status: str,
                                  ticket: int, price: float,
                                  lot: float, target_uuid: str):
        """Update fire record in database"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._update_fire_status_sync,
            fire_id, status, ticket, price, lot, target_uuid
        )

    def _update_fire_status_sync(self, fire_id: str, status: str,
                                 ticket: int, price: float,
                                 lot: float, target_uuid: str):
        """Synchronous database update for fire status (SQLite)"""
        try:
            import sqlite3
            DB_PATH = "/root/HydraX-v2/bitten.db"
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # Check existing status - don't downgrade FILLED to anything else
            cur.execute("SELECT status, ticket, lot FROM fires WHERE fire_id=?", (fire_id,))
            existing = cur.fetchone()

            should_update = True
            if existing:
                existing_status, existing_ticket, existing_lot = existing
                # Preserve original lot if not provided
                if lot is None or lot == 0:
                    lot = existing_lot

                # Don't downgrade FILLED with ticket
                if existing_status == "FILLED" and existing_ticket > 0 and status != "FILLED":
                    should_update = False
                    logger.info(
                        f"[CONFIRM] Ignoring {status} for {fire_id} - "
                        f"already FILLED with ticket {existing_ticket}"
                    )

            if should_update:
                # Build UPDATE dynamically - only update price if provided
                if price is not None:
                    cur.execute(
                        """
                        UPDATE fires
                        SET status=?, ticket=?, price=?, lot=?, updated_at=strftime('%s','now')
                        WHERE fire_id=?
                    """,
                        (status, ticket, price, lot, fire_id),
                    )
                else:
                    # Don't overwrite existing price
                    cur.execute(
                        """
                        UPDATE fires
                        SET status=?, ticket=?, lot=?, updated_at=strftime('%s','now')
                        WHERE fire_id=?
                    """,
                        (status, ticket, lot, fire_id),
                    )

                # If filled, create position record and update position tracking fields
                if status == "FILLED" and cur.rowcount > 0:
                    # Update current_price and unrealized_pnl for frontend sync
                    if price is not None:
                        cur.execute(
                            """
                            UPDATE fires
                            SET current_price = ?, unrealized_pnl = 0
                            WHERE fire_id = ?
                            """,
                            (price, fire_id)
                        )

                    cur.execute(
                        """
                        SELECT user_id, mission_id, sl, tp
                        FROM fires WHERE fire_id = ?
                    """,
                        (fire_id,)
                    )
                    fire_data = cur.fetchone()

                    if fire_data:
                        user_id, mission_id, sl_price, tp_price = fire_data

                        # Get symbol and direction from fires table
                        cur.execute("SELECT symbol, direction FROM fires WHERE fire_id = ?", (fire_id,))
                        symbol_data = cur.fetchone()

                        if symbol_data:
                            symbol, direction = symbol_data

                            # Generate position_id
                            position_id = f"pos_{ticket}_{fire_id}"

                            # Insert into live_positions table (TRUTH DATABASE for slot tracking)
                            cur.execute(
                                """
                                INSERT INTO live_positions
                                (fire_id, user_id, symbol, direction, entry_price,
                                 sl, tp, lot_size, ticket, status, current_price, last_update)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
                                ON CONFLICT (fire_id) DO UPDATE SET
                                    ticket = EXCLUDED.ticket,
                                    entry_price = EXCLUDED.entry_price,
                                    current_price = EXCLUDED.current_price,
                                    last_update = EXCLUDED.last_update
                            """,
                                (fire_id, user_id, symbol, direction, price,
                                 sl_price, tp_price, lot, ticket, price, int(time.time())),
                            )
                            logger.info(f"✅ FILLED: {fire_id} → ticket {ticket} @ {price}")

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update fire status: {e}")

    async def _record_position_closure(self, ticket: int, fire_id: str,
                                      symbol: str, volume: float,
                                      close_price: float, profit: float,
                                      reason: str, uuid: str, timestamp: int):
        """Record position closure in database"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._record_position_closure_sync,
            ticket, fire_id, symbol, volume, close_price, profit, reason, uuid, timestamp
        )

    def _record_position_closure_sync(self, ticket: int, fire_id: str,
                                      symbol: str, volume: float,
                                      close_price: float, profit: float,
                                      reason: str, uuid: str, timestamp: int):
        """Synchronous database insert for position closure"""
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # Record closure
            cur.execute(
                """
                INSERT INTO position_closures
                (ticket, fire_id, symbol, volume, close_price, profit, reason, uuid, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (ticket, fire_id, symbol, volume, close_price, profit, reason, uuid, timestamp),
            )

            # Update fires table if fire_id exists
            if fire_id:
                cur.execute(
                    """
                    UPDATE fires
                    SET status='CLOSED', close_reason=?, close_price=?, profit=?, updated_at=?
                    WHERE fire_id=?
                """,
                    (reason, close_price, profit, int(time.time()), fire_id),
                )

                # Update live_positions
                cur.execute(
                    """
                    UPDATE live_positions
                    SET status='CLOSED', last_update=?
                    WHERE fire_id=?
                """,
                    (int(time.time()), fire_id),
                )

                # Get entry price and user_id for Firebase sync
                cur.execute(
                    "SELECT entry_price, direction, user_id FROM live_positions WHERE fire_id=?",
                    (fire_id,)
                )
                position_data = cur.fetchone()

            conn.commit()
            conn.close()

            # ✅ SYNC TO FIREBASE
            if fire_id and position_data:
                try:
                    entry_price, direction, user_id = position_data

                    # Calculate pips
                    if 'JPY' in symbol:
                        pip_movement = (close_price - entry_price) * 100
                    else:
                        pip_movement = (close_price - entry_price) * 10000

                    # Apply direction
                    if direction == 'SELL':
                        pip_movement = -pip_movement

                    # Determine outcome
                    if reason.upper() in ['TP_HIT', 'TP']:
                        outcome = 'TP HIT'
                    elif reason.upper() in ['SL_HIT', 'SL']:
                        outcome = 'SL HIT'
                    else:
                        outcome = 'TP HIT' if profit > 0 else 'SL HIT'

                    from firebase_backend import close_active_trade
                    close_active_trade(
                        trade_id=fire_id,
                        exit_price=float(close_price),
                        profit=float(profit),
                        pips=pip_movement,
                        outcome=outcome
                    )
                    logger.info(f"✅ Firebase: Trade {fire_id} closed (${profit:.2f}, {outcome})")
                except Exception as fb_error:
                    logger.error(f"❌ Firebase sync failed: {fb_error}")

        except Exception as e:
            logger.error(f"Failed to record position closure: {e}")

    async def _handle_heartbeat_metrics(self, msg: dict):
        """Handle HEARTBEAT_METRICS messages with position arrays from EA"""
        self.heartbeat_metrics_received += 1

        target_uuid = msg.get("target_uuid", "")
        positions = msg.get("positions", [])

        logger.info(f"📡 HEARTBEAT_METRICS: {target_uuid} - {len(positions)} positions")

        # Get user_id from EA UUID
        loop = asyncio.get_event_loop()
        user_id = await loop.run_in_executor(None, self._get_user_id_from_uuid, target_uuid)

        if not user_id:
            logger.warning(f"No user_id found for UUID {target_uuid}")
            return

        # Sync positions to both database AND Firebase
        try:
            import sys
            sys.path.insert(0, '/root/HydraX-v2')
            from firebase_backend import update_active_trade_price

            # Get list of fire_ids currently open in MT5
            mt5_fire_ids = set()

            for pos in positions:
                fire_id = pos.get("fire_id", "")
                current_price = pos.get("current_price")
                pnl = pos.get("pnl")

                if not fire_id:
                    continue

                mt5_fire_ids.add(fire_id)

                # Update database live_positions with current price/PNL
                await loop.run_in_executor(
                    None,
                    self._update_live_position_sync,
                    fire_id, current_price, pnl
                )

                # Sync to Firebase
                if current_price is not None and pnl is not None:
                    update_active_trade_price(
                        trade_id=fire_id,
                        current_price=float(current_price),
                        equity=float(pnl)
                    )
                    logger.debug(f"✅ Synced {fire_id} → ${pnl:.2f}")

            # Close positions in database that are NOT in MT5's list
            if mt5_fire_ids:
                await loop.run_in_executor(
                    None,
                    self._reconcile_closed_positions,
                    user_id, list(mt5_fire_ids)
                )

        except Exception as e:
            logger.error(f"Failed to sync heartbeat positions: {e}")

    async def _create_firebase_active_trade(self, fire_id: str, symbol: str,
                                           direction: str, entry_price: float,
                                           volume: float, timestamp: int):
        """Create Firebase active_trades document when position_opened is received"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._create_firebase_active_trade_sync,
            fire_id, symbol, direction, entry_price, volume, timestamp
        )

    def _create_firebase_active_trade_sync(self, fire_id: str, symbol: str,
                                          direction: str, entry_price: float,
                                          volume: float, timestamp: int):
        """Synchronous Firebase document creation"""
        try:
            import sys
            sys.path.insert(0, '/root/HydraX-v2')
            from firebase_backend import write_active_trade
            import sqlite3

            # Query database to get user_id, sl, tp from fires table
            # Use SQLite database (DB_PATH already imported from config)
            db_path = '/root/HydraX-v2/bitten.db'  # Fallback to known path
            conn = sqlite3.connect(db_path, timeout=5)
            cur = conn.cursor()

            cur.execute(
                """
                SELECT user_id, sl, tp
                FROM fires
                WHERE fire_id = ?
                LIMIT 1
                """,
                (fire_id,)
            )
            result = cur.fetchone()

            if result:
                user_id, sl, tp = result
            else:
                # Fire not in database (test fire or external fire)
                # Try to get user_id from EA UUID mapping
                logger.warning(f"⚠️  Fire {fire_id} not found in fires table, attempting EA UUID lookup")

                # Get UUID from position_opened message (already passed as parameter in outer scope)
                # We need to query ea_instances to get user_id from UUID
                # For now, use the user_id from the fire command if available
                cur.execute(
                    """
                    SELECT user_id
                    FROM ea_instances
                    WHERE target_uuid = 'COMMANDER_DEV_001'
                    LIMIT 1
                    """
                )
                ea_result = cur.fetchone()

                if ea_result and ea_result[0]:
                    user_id = ea_result[0]
                    sl = 0  # No SL for test trades
                    tp = 0  # No TP for test trades
                    logger.info(f"✅ Resolved user_id={user_id} from EA UUID mapping")
                else:
                    logger.warning(f"⚠️  Cannot resolve user_id for fire {fire_id}")
                    conn.close()
                    return

            conn.close()

            if not user_id:
                logger.warning(f"⚠️  Fire {fire_id} has no user_id, cannot create Firebase document")
                return

            # Create Firebase active_trades document
            trade_data = {
                'fire_id': fire_id,
                'user_id': str(user_id),
                'symbol': symbol,
                'direction': direction,
                'entry': float(entry_price),
                'current': float(entry_price),  # Initial current = entry
                'sl': float(sl) if sl else 0,
                'tp': float(tp) if tp else 0,
                'equity': 0.0,  # Initial P&L is 0
                'lots': float(volume) if volume else 0,
                'startTime': timestamp
            }

            success = write_active_trade(trade_data)

            if success:
                logger.info(f"✅ Firebase: Created active_trades/{fire_id} for user {user_id}")
            else:
                logger.error(f"❌ Firebase: Failed to create active_trades/{fire_id}")

        except Exception as e:
            logger.error(f"❌ Firebase active trade creation failed for {fire_id}: {e}")

    async def _record_hybrid_event(self, ticket: int, fire_id: str,
                                   event_type: str, volume: float,
                                   pips: float, timestamp: int, uuid: str):
        """Record hybrid event in database"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._record_hybrid_event_sync,
            ticket, fire_id, event_type, volume, pips, timestamp, uuid
        )

    def _record_hybrid_event_sync(self, ticket: int, fire_id: str,
                                  event_type: str, volume: float,
                                  pips: float, timestamp: int, uuid: str):
        """Synchronous database insert for hybrid event"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO hybrid_events
                (ticket, fire_id, event_type, volume, pips, timestamp, uuid, node_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            """,
                (ticket, fire_id, event_type, volume, pips, timestamp, uuid),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to record hybrid event: {e}")

    async def _get_user_id_from_fire_id(self, fire_id: str) -> str:
        """Get user_id from fire_id by querying fires table"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_user_id_from_fire_id_sync,
            fire_id
        )

    def _get_user_id_from_fire_id_sync(self, fire_id: str) -> str:
        """Synchronous database query for user_id (SQLite)"""
        try:
            import sqlite3
            DB_PATH = "/root/HydraX-v2/bitten.db"
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            cur.execute("SELECT user_id FROM fires WHERE fire_id=?", (fire_id,))
            result = cur.fetchone()
            conn.close()

            if result:
                return result[0]
            else:
                logger.warning(f"No fire found with fire_id={fire_id}")
                return None

        except Exception as e:
            logger.error(f"Error querying user_id for fire_id {fire_id}: {e}")
            return None

    def _get_user_id_from_uuid(self, target_uuid: str) -> str:
        """Get user_id from EA UUID (SQLite)"""
        try:
            import sqlite3
            DB_PATH = "/root/HydraX-v2/bitten.db"
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM ea_instances WHERE target_uuid = ?", (target_uuid,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user_id from UUID {target_uuid}: {e}")
            return None

    def _update_live_position_sync(self, fire_id: str, current_price: float, pnl: float):
        """Update live_positions table with current price and PNL (SQLite)"""
        try:
            import sqlite3
            import time
            DB_PATH = "/root/HydraX-v2/bitten.db"
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE live_positions
                SET current_price = ?, current_pnl = ?, last_update = ?
                WHERE fire_id = ? AND status = 'OPEN'
            """, (current_price, pnl, int(time.time()), fire_id))
            conn.commit()
            conn.close()
            logger.debug(f"🔄 DB: Updated {fire_id} → ${pnl:.2f}")
        except Exception as e:
            logger.error(f"Error updating position {fire_id}: {e}")

    def _reconcile_closed_positions(self, user_id: str, mt5_fire_ids: list):
        """Close positions in database that are not in MT5's list (SQLite)"""
        try:
            import sqlite3
            import time
            DB_PATH = "/root/HydraX-v2/bitten.db"
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cursor = conn.cursor()

            # Get all OPEN positions for user
            cursor.execute("""
                SELECT fire_id FROM live_positions
                WHERE user_id = ? AND status = 'OPEN'
            """, (user_id,))

            db_positions = [row[0] for row in cursor.fetchall()]

            # Close positions not in MT5's list
            for fire_id in db_positions:
                if fire_id not in mt5_fire_ids:
                    cursor.execute("""
                        UPDATE live_positions
                        SET status = 'CLOSED', last_update = ?
                        WHERE fire_id = ?
                    """, (int(time.time()), fire_id))
                    logger.info(f"🔄 Reconciled: Closed {fire_id} (not in MT5)")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error reconciling positions: {e}")

    async def _update_ea_last_seen(self, uuid: str):
        """Update EA last_seen timestamp"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._update_ea_last_seen_sync, uuid)

    def _update_ea_last_seen_sync(self, uuid: str):
        """Synchronous database update for EA last_seen"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            cur.execute(
                """
                UPDATE ea_instances SET last_seen=? WHERE target_uuid=?
            """,
                (int(time.time()), uuid),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.warning(f"Failed to update EA last_seen: {e}")

    async def _ensure_tables(self):
        """Ensure database tables exist"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._ensure_tables_sync)

    def _ensure_tables_sync(self):
        """Synchronous table creation"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # Fires table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS fires (
                    fire_id TEXT PRIMARY KEY,
                    mission_id TEXT,
                    user_id TEXT,
                    status TEXT,
                    ticket INTEGER,
                    price REAL,
                    symbol TEXT,
                    direction TEXT,
                    sl REAL,
                    tp REAL,
                    lot REAL,
                    hybrid_enabled BOOLEAN DEFAULT FALSE,
                    partial_closes TEXT,
                    trail_updates TEXT,
                    close_reason TEXT,
                    close_price REAL,
                    profit REAL,
                    idem TEXT UNIQUE,
                    created_at INTEGER,
                    updated_at INTEGER,
                    target_uuid TEXT,
                    equity_used REAL,
                    risk_pct_used REAL
                )
            """
            )

            # Hybrid events table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS hybrid_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket INTEGER NOT NULL,
                    fire_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    volume REAL,
                    pips REAL,
                    timestamp INTEGER NOT NULL,
                    uuid TEXT NOT NULL,
                    node_id TEXT
                )
            """
            )

            # Position closures table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS position_closures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket INTEGER NOT NULL,
                    fire_id TEXT,
                    symbol TEXT,
                    volume REAL,
                    close_price REAL,
                    profit REAL,
                    reason TEXT,
                    uuid TEXT,
                    timestamp INTEGER
                )
            """
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")

    async def stop(self):
        """Clean shutdown"""
        if self.receiver:
            self.receiver.close()
        logger.info("Confirmation handler stopped")

    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "confirmations_received": self.confirmations_received,
            "positions_opened": self.positions_opened,
            "positions_closed": self.positions_closed,
            "hybrid_events": self.hybrid_events
        }
