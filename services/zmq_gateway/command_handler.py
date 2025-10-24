"""
Command Handler - Port 5555 (ROUTER) + IPC Queue (PULL)
Routes fire commands from webapp to EA using DEALER/ROUTER pattern
"""
import asyncio
import json
import logging
import queue
import sqlite3
import time
from collections import OrderedDict
from typing import Dict, Optional

import zmq
import zmq.asyncio

from .config import (
    DB_PATH,
    PORT_COMMAND_ROUTER,
    PORT_IPC_QUEUE,
    ROUTER_POLL_TIMEOUT_MS,
)

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handles fire command routing via ROUTER socket"""

    def __init__(self, context: zmq.asyncio.Context):
        self.context = context
        self.router = None
        self.ipc_pull = None

        # Identity mapping: uuid -> raw identity bytes
        self.identity_map: Dict[str, bytes] = {}
        self.ea_last_seen: Dict[str, float] = {}
        self.current_ea_uuid: Optional[str] = None

        # Command queue (thread-safe)
        self.command_queue = asyncio.Queue()

        # Statistics
        self.commands_enqueued = 0
        self.commands_routed = 0
        self.heartbeats_received = 0

    async def start(self):
        """Initialize and bind sockets"""
        # ROUTER socket - bidirectional with EA
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind(f"tcp://*:{PORT_COMMAND_ROUTER}")
        logger.info(f"✅ Bound ROUTER socket to port {PORT_COMMAND_ROUTER}")

        # PULL socket - receives commands from webapp
        self.ipc_pull = self.context.socket(zmq.PULL)
        self.ipc_pull.setsockopt(zmq.RCVHWM, 10000)
        self.ipc_pull.bind(PORT_IPC_QUEUE)
        logger.info(f"✅ Bound PULL socket to {PORT_IPC_QUEUE}")

        logger.info("🎯 Command router ready")

    async def process_router_messages(self):
        """Process incoming messages from EA on ROUTER socket"""
        poller = zmq.asyncio.Poller()
        poller.register(self.router, zmq.POLLIN)

        while True:
            try:
                events = await poller.poll(ROUTER_POLL_TIMEOUT_MS)

                if self.router in dict(events):
                    await self._handle_router_message()

            except Exception as e:
                logger.error(f"Error in router loop: {e}")
                await asyncio.sleep(1)

    async def _handle_router_message(self):
        """Handle a single message from ROUTER socket"""
        # ROUTER frames: [identity, empty, payload] OR [identity, payload]
        parts = await self.router.recv_multipart()

        if len(parts) == 3:
            ident, empty, payload = parts
        elif len(parts) == 2:
            ident, payload = parts
        else:
            logger.warning(f"ROUTER invalid frame parts={len(parts)}")
            return

        logger.debug(f"[ROUTER] Received from identity={ident.hex()}")

        try:
            msg = json.loads(payload.decode("utf-8", "ignore"))
            msg_type = msg.get("type", "").lower()

            # Extract UUID from payload
            uuid = msg.get("target_uuid") or msg.get("user_uuid") or msg.get("uuid")

            # Handle heartbeat/handshake messages
            if msg_type in ["heartbeat", "router_heartbeat", "dealer_heartbeat", "handshake"]:
                await self._handle_ea_heartbeat(uuid, ident, msg, msg_type)

            # Handle confirmations (route to confirmation handler via internal queue)
            elif msg_type in ["pong", "confirmation", "close_confirmation",
                            "position_closed", "hybrid_event", "position_opened"]:
                # Forward to confirmation handler via shared state
                # (confirmation_handler will pull from port 5558, but we can also
                # forward here if needed - for now, just log)
                logger.debug(f"[ROUTER] {msg_type} from {uuid}")

        except Exception as e:
            logger.warning(f"ROUTER payload parse error: {e}")

    async def _handle_ea_heartbeat(self, uuid: str, ident: bytes,
                                   msg: dict, msg_type: str):
        """Handle EA heartbeat/handshake messages"""
        if not uuid:
            try:
                uuid = ident.decode("utf-8").strip()
            except:
                uuid = f"UNKNOWN_{ident.hex()}"

        # Update tracking
        self.ea_last_seen[uuid] = time.time()

        # Store exact identity bytes for routing
        if self.identity_map.get(uuid) != ident:
            if uuid in self.identity_map:
                logger.warning(
                    f"[EA] Identity changed for {uuid}: "
                    f"{self.identity_map[uuid].hex()} → {ident.hex()}"
                )
            else:
                logger.info(f"[ROUTER] Learned {uuid} ← {ident.hex()}")

            self.identity_map[uuid] = ident
            self.current_ea_uuid = uuid

        # Update database
        await self._upsert_ea_instance(msg)

        self.heartbeats_received += 1
        if self.heartbeats_received % 10 == 0:
            logger.info(f"[EA] {msg_type} from {uuid} (total: {self.heartbeats_received})")

    async def process_ipc_commands(self):
        """Process commands from IPC queue and route to EA"""
        while True:
            try:
                # Receive command from webapp
                cmd = await self.ipc_pull.recv_json()
                self.commands_enqueued += 1

                # Handle wrapped payloads
                if "payload" in cmd and "target_uuid" in cmd:
                    uuid = cmd.get("target_uuid")
                    payload_field = cmd.get("payload")

                    # Parse wrapped payload
                    if isinstance(payload_field, str):
                        raw_cmd = json.loads(payload_field)
                    else:
                        raw_cmd = payload_field

                    cmd_type = raw_cmd.get("type", "UNKNOWN")
                    fire_id = raw_cmd.get("fire_id", "NO_ID")

                    # UUID firewall
                    if self.current_ea_uuid and uuid != self.current_ea_uuid:
                        logger.warning(
                            f"[UUID_FIREWALL] REJECTED {cmd_type} {fire_id} - "
                            f"target={uuid} != learned={self.current_ea_uuid}"
                        )
                        continue

                    # Enqueue for routing
                    await self.command_queue.put({
                        "target_uuid": uuid,
                        "payload": raw_cmd
                    })

                else:
                    # Standard command
                    uuid = cmd.get("target_uuid")
                    cmd_type = cmd.get("type", "UNKNOWN")
                    fire_id = cmd.get("fire_id", "NO_ID")

                    # UUID firewall
                    if self.current_ea_uuid and uuid != self.current_ea_uuid:
                        logger.warning(
                            f"[UUID_FIREWALL] REJECTED {cmd_type} {fire_id}"
                        )
                        continue

                    # Enqueue for routing
                    await self.command_queue.put({
                        "target_uuid": uuid,
                        "payload": cmd
                    })

                logger.info(f"[IPC_IN] {cmd_type} {fire_id} → queue")

            except Exception as e:
                logger.error(f"Error processing IPC command: {e}")
                await asyncio.sleep(0.2)

    async def route_commands(self):
        """Route queued commands to EA via ROUTER socket"""
        while True:
            try:
                # Get command from queue
                item = await self.command_queue.get()

                target_uuid = item["target_uuid"]
                payload = item["payload"]

                # Check if we have identity for this UUID
                ident = self.identity_map.get(target_uuid)
                if not ident:
                    logger.warning(f"[ROUTE] No identity for {target_uuid}, requeuing")
                    await asyncio.sleep(0.2)
                    await self.command_queue.put(item)
                    continue

                # Serialize payload with OrderedDict for EA compatibility
                payload_bytes = self._serialize_fire_command(payload)

                # Send via ROUTER: [identity, empty delimiter, payload]
                # CRITICAL: Use the learned identity bytes from DEALER, not re-encoded UUID
                await self.router.send_multipart([ident, b"", payload_bytes])

                self.commands_routed += 1

                cmd_type = payload.get("type", "unknown")
                fire_id = payload.get("fire_id", "")
                logger.info(
                    f"[ROUTE] {cmd_type} {fire_id} → {target_uuid} "
                    f"({len(payload_bytes)} bytes)"
                )

            except Exception as e:
                logger.error(f"Error routing command: {e}")
                await asyncio.sleep(0.2)

    def _serialize_fire_command(self, cmd: dict) -> bytes:
        """
        Serialize fire command with EXACT field order for EA v2.07 compatibility

        CRITICAL: EA v2.07 requires exact JSON field order:
        type, target_uuid, fire_id, symbol, direction, entry, sl, tp, lot, [hybrid]
        """
        cmd_type = cmd.get("type", "fire")

        if cmd_type == "fire":
            # Use OrderedDict to preserve field order
            ordered = OrderedDict([
                ("type", "fire"),
                ("target_uuid", cmd.get("target_uuid")),
                ("fire_id", cmd.get("fire_id")),
                ("symbol", cmd.get("symbol")),
                ("direction", cmd.get("direction")),  # Must be uppercase BUY/SELL
                ("entry", cmd.get("entry", 0)),  # 0 for market order
                ("sl", cmd.get("sl", 0)),
                ("tp", cmd.get("tp", 0)),
                ("lot", round(float(cmd.get("lot", 0.01)), 2))  # Round to 2 decimals
            ])

            # Add hybrid configuration if present
            if "hybrid" in cmd:
                ordered["hybrid"] = cmd["hybrid"]

            # Serialize with compact format
            return json.dumps(ordered, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        else:
            # For non-fire commands, use standard serialization
            return json.dumps(cmd, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    async def _upsert_ea_instance(self, payload: dict):
        """Update EA instance in database"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._upsert_ea_instance_sync,
                payload
            )
        except Exception as e:
            logger.warning(f"DB update failed: {e}")

    def _upsert_ea_instance_sync(self, payload: dict):
        """Synchronous database upsert"""
        uuid = str(payload.get("target_uuid") or payload.get("uuid", "")).strip()
        if not uuid:
            return

        now = int(time.time())
        user_id = payload.get("user_id")
        balance = float(payload.get("balance", 0) or 0)
        equity = float(payload.get("equity", 0) or 0)

        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO ea_instances(
                  target_uuid,user_id,last_balance,last_equity,last_seen,updated_at
                ) VALUES(?,?,?,?,?,?)
                ON CONFLICT(target_uuid) DO UPDATE SET
                  user_id=COALESCE(excluded.user_id, ea_instances.user_id),
                  last_balance=excluded.last_balance,
                  last_equity=excluded.last_equity,
                  last_seen=excluded.last_seen,
                  updated_at=excluded.updated_at
            """,
                (uuid, user_id, balance, equity, now, now),
            )

            conn.commit()
            conn.close()

            # ✅ WRITE TO FIREBASE (user data sync + initial capital tracking)
            if user_id and balance is not None and equity is not None:
                try:
                    from firebase_backend import update_user_data, get_firestore_client

                    # Update current balance and equity
                    update_user_data(user_id, {
                        'balance': float(balance),
                        'equity': float(equity)
                    })
                    logger.info(f"✅ User data synced to Firebase: {user_id}")

                    # Capture initial capital on first heartbeat
                    try:
                        db = get_firestore_client()
                        if db:
                            user_ref = db.collection('users').document(str(user_id))
                            user_doc = user_ref.get()

                            # If user doesn't exist or doesn't have initialCapital set
                            if not user_doc.exists or 'initialCapital' not in user_doc.to_dict():
                                update_user_data(user_id, {
                                    'initialCapital': float(balance),
                                    'displayName': f'OPERATOR_{user_id[-4:]}',  # Set default display name
                                    'tier': 'RECRUIT'  # Set default tier
                                })
                                logger.info(f"✅ Set initial capital for user {user_id}: ${balance}")

                    except Exception as ic_error:
                        logger.warning(f"Initial capital tracking failed: {ic_error}")

                except Exception as fb_error:
                    logger.warning(f"Firebase user data sync failed: {fb_error}")

        except Exception as e:
            logger.warning(f"Database error: {e}")

    async def stop(self):
        """Clean shutdown"""
        if self.router:
            self.router.close()
        if self.ipc_pull:
            self.ipc_pull.close()
        logger.info("Command handler stopped")

    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "commands_enqueued": self.commands_enqueued,
            "commands_routed": self.commands_routed,
            "heartbeats_received": self.heartbeats_received,
            "connected_eas": len(self.identity_map),
            "queue_size": self.command_queue.qsize()
        }
