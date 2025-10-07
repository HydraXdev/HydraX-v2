#!/usr/bin/env python3
import json
import logging
import os
import threading
import time

import zmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
LOG = logging.getLogger("CMD")

# CUTOVER: MetaSocket integration
SOURCE = os.getenv("SOURCE", "ea")  # ea | metasocket | both


def _route_to_metasocket(cmd):
    """Route fire command to MetaSocket adapter"""
    try:
        from adapters.metasocket.adapter import get_adapter

        adapter = get_adapter()
        result = adapter.fire_order(
            signal_id=cmd.get("fire_id", ""),
            symbol=cmd.get("symbol", ""),
            direction=cmd.get("direction", ""),
            volume=cmd.get("lot", 0.01),
            sl_pips=cmd.get("sl_pips", 0),
            tp_pips=cmd.get("tp_pips", 0),
            idempotency_key=cmd.get("fire_id"),
        )

        if result.get("success"):
            # Record fire in database for tracking
            _record_fire_command(cmd)
            LOG.info(f"[METASOCKET] Fire success: ticket={result.get('ticket')}, latency={result.get('latency_ms')}ms")
            return True
        else:
            LOG.error(f"[METASOCKET] Fire failed: {result.get('error')}")
            return False

    except Exception as e:
        LOG.error(f"[METASOCKET] Route failed: {e}")
        return False


PUSH_BIND = os.getenv("BITTEN_PUSH_ADDR", "tcp://*:5555")  # EA PULL connects here
QUEUE_PULL = os.getenv("BITTEN_QUEUE_ADDR", "ipc:///tmp/bitten_cmdqueue")  # webapp PUSHes here
CONFIRM_BIND = os.getenv("BITTEN_CONFIRM_ADDR", "tcp://*:5558")  # EA PUSH confirmations here
HEARTBEAT_SEC = int(os.getenv("BITTEN_EA_TTL_SEC", "120"))

ctx = zmq.Context.instance()

# Global sockets - must be declared before functions that use them
heartbeat_push = None
router = None
pull = None

import queue

# Thread management and queuing
import threading
import traceback

# Globals for robust queue worker
ipc_q = queue.Queue()
stop_evt = threading.Event()
worker = None
identity_map = {}  # uuid -> raw identity bytes
current_ea_uuid = None  # Store the actual EA UUID from heartbeats

# DB update functions
import sqlite3


def _ea_db():
    db = os.environ.get("BITTEN_DB", "/root/HydraX-v2/bitten.db")
    conn = sqlite3.connect(db, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


_last_upd_cache = {}  # uuid -> ts


def _normalize(val):
    """Convert empty strings to None"""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _handle_handshake(payload):
    """Handle EA handshake with position reconciliation"""
    uuid = str(payload.get("uuid", "")).strip()
    if not uuid:
        return

    is_reconnect = payload.get("reconnect", False)
    ea_positions = payload.get("open_positions", [])

    # Store positions in memory for tracking
    global ea_positions_by_uuid
    if "ea_positions_by_uuid" not in globals():
        ea_positions_by_uuid = {}

    if not is_reconnect:
        # Fresh start - reset position tracking
        LOG.info(f"[HANDSHAKE] Fresh start for {uuid} - resetting position tracking")
        ea_positions_by_uuid[uuid] = []
    else:
        # Reconnect - reconcile positions
        server_positions = ea_positions_by_uuid.get(uuid, [])
        ea_tickets = {p.get("ticket") for p in ea_positions}
        server_tickets = {p.get("ticket") for p in server_positions}

        if ea_tickets != server_tickets:
            LOG.warning(
                f"[RECONCILE] Position mismatch for {uuid}: " f"EA has {ea_tickets}, Server has {server_tickets}"
            )
            LOG.info(f"[RECONCILE] Trusting EA state with {len(ea_positions)} positions")
        else:
            LOG.info(f"[RECONCILE] Position sync OK for {uuid}: {len(ea_positions)} positions")

        # Trust EA as source of truth
        ea_positions_by_uuid[uuid] = ea_positions

        # Log position details
        for pos in ea_positions:
            LOG.info(
                f"[POSITION] Ticket: {pos.get('ticket')}, "
                f"Symbol: {pos.get('symbol')}, "
                f"Direction: {pos.get('direction')}, "
                f"Volume: {pos.get('volume')}, "
                f"PnL: {pos.get('pnl', 0):.2f}"
            )


def _upsert_ea_instance(payload):
    # Handle handshake messages for position reconciliation
    msg_type = str(payload.get("type", "")).lower()
    if msg_type == "handshake":
        _handle_handshake(payload)

    # Rate-limit to 1/sec per UUID
    uuid = str(payload.get("target_uuid", "")).strip()
    if not uuid:
        uuid = str(payload.get("uuid", "")).strip()  # Handshakes use 'uuid' not 'target_uuid'
    if not uuid:
        return
    now = int(time.time())
    ts = _last_upd_cache.get(uuid, 0)
    if now - ts < 1:
        return
    _last_upd_cache[uuid] = now

    # Normalize values - empty strings become None
    user_id = _normalize(payload.get("user_id"))
    acct_login = _normalize(payload.get("account_login") or payload.get("account"))
    broker = _normalize(payload.get("broker"))
    currency = _normalize(payload.get("currency") or payload.get("account_currency"))
    leverage = int(payload.get("leverage", 0) or 0)
    balance = float(payload.get("balance", payload.get("account_balance", 0)) or 0)
    equity = float(payload.get("equity", payload.get("account_equity", 0)) or 0)
    last_seen = int(payload.get("ts", now) or now)
    created_at = now
    updated_at = now

    try:
        conn = _ea_db()
        cur = conn.cursor()

        # Create table if needed
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS ea_instances (
            target_uuid     TEXT PRIMARY KEY,
            user_id         TEXT,
            account_login   TEXT,
            broker          TEXT,
            currency        TEXT,
            leverage        INTEGER,
            last_balance    REAL,
            last_equity     REAL,
            last_seen       INTEGER,
            created_at      INTEGER,
            updated_at      INTEGER
        );
        """
        )

        # UPSERT with user_id preservation using COALESCE
        cur.execute(
            """
            INSERT INTO ea_instances(
              target_uuid,user_id,account_login,broker,currency,leverage,
              last_balance,last_equity,last_seen,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(target_uuid) DO UPDATE SET
              user_id=COALESCE(excluded.user_id, ea_instances.user_id),
              account_login=COALESCE(excluded.account_login, ea_instances.account_login),
              broker=COALESCE(excluded.broker, ea_instances.broker),
              currency=COALESCE(excluded.currency, ea_instances.currency),
              leverage=COALESCE(excluded.leverage, ea_instances.leverage),
              last_balance=excluded.last_balance,
              last_equity=excluded.last_equity,
              last_seen=excluded.last_seen,
              updated_at=excluded.updated_at
        """,
            (uuid, user_id, acct_login, broker, currency, leverage, balance, equity, last_seen, created_at, updated_at),
        )

        # Log if user_id changed
        if user_id is not None:
            cur.execute("SELECT user_id FROM ea_instances WHERE target_uuid=?", (uuid,))
            row = cur.fetchone()
            if row and row[0] != user_id:
                LOG.info(f"[CMD] EA {uuid} user_id changed: {row[0]} → {user_id}")

        conn.commit()
        conn.close()
    except Exception as e:
        LOG.warning("DB update failed: %s", e)


def _insert_fire_record(cmd):
    """Insert fire command into database for tracking"""
    try:
        fire_id = cmd.get("fire_id")
        if not fire_id:
            return

        # Extract user_id from the EA instance that will execute this
        target_uuid = cmd.get("target_uuid")
        if not target_uuid:
            return

        # Get user_id from ea_instances table
        conn = _ea_db()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM ea_instances WHERE target_uuid = ?", (target_uuid,))
        row = cur.fetchone()
        user_id = row[0] if row and row[0] else "unknown"

        # Create fires table if needed (with trade data columns)
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS fires (
            fire_id TEXT PRIMARY KEY,
            mission_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            status TEXT,
            ticket INTEGER,
            price REAL,
            symbol TEXT,               -- Trade symbol for confirmation lookup
            direction TEXT,            -- BUY/SELL for confirmation lookup
            sl REAL,                   -- Stop loss for live_positions
            tp REAL,                   -- Take profit for live_positions
            lot REAL,                  -- Lot size for live_positions
            idem TEXT UNIQUE,
            created_at INTEGER,
            updated_at INTEGER,
            equity_used REAL,
            risk_pct_used REAL
        )
        """
        )

        # Extract trade data from command
        symbol = cmd.get("symbol")
        direction = cmd.get("direction")
        sl = cmd.get("sl", 0)
        tp = cmd.get("tp", 0)
        lot = cmd.get("lot", 0)

        # Insert fire record with SENT status and trade data
        now = int(time.time())
        cur.execute(
            """
            INSERT OR IGNORE INTO fires
            (fire_id, mission_id, user_id, status, symbol, direction, sl, tp, lot, created_at, updated_at)
            VALUES (?, ?, ?, 'SENT', ?, ?, ?, ?, ?, ?, ?)
        """,
            (fire_id, fire_id, user_id, symbol, direction, sl, tp, lot, now, now),
        )

        conn.commit()
        conn.close()
        LOG.info(f"[CMD] 📝 Fire record created: {fire_id} for user {user_id}")

    except Exception as e:
        LOG.warning(f"[CMD] Fire record insert error: {e}")


# Global variables for sockets (initialized in main())
router = None
pull = None

# EA registry: uuid -> last_seen
ea_last_seen = {}
# Map UUID to socket identity for routing back
uuid_to_identity = {}


def recv_router_forever():
    while True:
        # ROUTER frames: [identity, empty, payload] OR [identity, payload]
        parts = router.recv_multipart()
        if len(parts) == 3:
            ident, empty, payload = parts
        elif len(parts) == 2:
            ident, payload = parts
        else:
            LOG.warning("ROUTER invalid frame parts=%d", len(parts))
            continue

        # CRITICAL: Log EA's actual identity bytes for debugging
        LOG.info(f"[IDENTITY] EA identity bytes={ident} hex={ident.hex()}")

        try:
            msg = json.loads(payload.decode("utf-8", "ignore"))
            LOG.info(f"[DEBUG] Received message: type={msg.get('type')}")
            # Log full payload for heartbeats to debug UUID
            if msg.get("type") in ["HEARTBEAT", "ROUTER_HEARTBEAT"]:
                LOG.info(f"[UUID_DEBUG] Full heartbeat payload: {msg}")
        except Exception:
            LOG.warning("ROUTER non-json payload from identity=%s", ident.hex())
            continue

        # Extract UUID from payload (this becomes the routing key)
        typ = (msg.get("type") or "").lower()  # FIXED: Normalize to lowercase for EA compatibility
        uuid = msg.get("target_uuid") or msg.get("user_uuid") or msg.get("uuid")

        # CRITICAL: Parse and store EA's actual UUID for exact matching
        if uuid and typ in ["heartbeat", "router_heartbeat", "dealer_heartbeat"]:  # FIXED: Added dealer_heartbeat
            global current_ea_uuid
            ea_uuid_str = str(uuid).strip()  # Clean but preserve exact case
            LOG.info(
                f"[EA_UUID] Learned: {repr(ea_uuid_str)} len={len(ea_uuid_str)} hex={ea_uuid_str.encode('utf-8').hex()}"
            )
            current_ea_uuid = ea_uuid_str  # Store globally for commands
            # Store for future command routing
            identity_map[ea_uuid_str] = ident

            # Purge any stale queued items with old UUIDs
            temp_items = []
            try:
                while True:
                    item = ipc_q.get_nowait()
                    # Only keep items that match the current EA UUID
                    if item.get("target_uuid") == ea_uuid_str:
                        temp_items.append(item)
                    else:
                        LOG.info("[PURGE] Dropped stale item with UUID: %s", item.get("target_uuid"))
            except queue.Empty:
                pass
            # Re-queue valid items
            for item in temp_items:
                ipc_q.put(item)

        # Fallback: if no UUID in payload, try decoding identity (careful!)
        if not uuid:
            try:
                uuid = ident.decode("utf-8").strip()
            except:
                uuid = f"UNKNOWN_{ident.hex()}"

        # CRITICAL: Learn exact identity bytes from EA
        if uuid:
            ea_last_seen[uuid] = time.time()
            old_ident = identity_map.get(uuid)

            # Store the EXACT identity bytes the EA is using
            if old_ident != ident:
                if old_ident:
                    LOG.warning(f"[EA] Identity changed for {uuid}: {old_ident.hex()} → {ident.hex()}")
                else:
                    LOG.info(f"[ROUTER] learned %s ← %s", uuid, ident.hex())

                # Store exact bytes for routing back
                identity_map[uuid] = ident

                # Debug the mapping for UUID issues
                LOG.info(f"[MAPPING] target_uuid='{uuid}' (len={len(uuid)})")
                LOG.info(f"[MAPPING] identity_bytes={ident.hex()} (len={len(ident)})")
                LOG.info(f"[MAPPING] Router map keys={list(identity_map.keys())}")

            _upsert_ea_instance(msg)  # Update DB

        # Log specific message types
        if typ in (
            "hello",
            "heartbeat",
            "ping",
            "router_hello",
            "router_heartbeat",
            "dealer_heartbeat",
        ):  # FIXED: Added dealer_heartbeat
            LOG.info("[EA] %s %s", typ, uuid)

            # Forward enhanced heartbeats with position data to confirm_listener
            if typ == "heartbeat" and ("positions" in msg or "open_positions" in msg):  # FIXED: lowercase
                if heartbeat_push:
                    try:
                        heartbeat_push.send_json(msg, zmq.NOBLOCK)
                        LOG.info("[HEARTBEAT] Forwarded enhanced heartbeat to confirm_listener")
                    except Exception as e:
                        LOG.warning("[HEARTBEAT] Failed to forward: %s", e)
        elif typ in (
            "pong",
            "confirmation",
            "close_confirmation",
            "position_closed",
            "hybrid_event",
        ):  # FIXED: lowercase + all EA confirm types
            # PRODUCTION-SAFE FALLBACK: Route confirmations over 5555 channel
            unified_confirmation_handler(msg, "5555")
        else:
            # EAs generally shouldn't send other types here; ignore
            pass


def unified_confirmation_handler(msg, source_socket):
    """Unified handler for confirmations from both 5555 and 5558"""
    msg_type = msg.get("type", "unknown")
    msg_id = msg.get("ping_id", msg.get("fire_id", "NO_ID"))

    # Log first 80 chars + type for every message as requested
    msg_str = json.dumps(msg)
    LOG.info(f"[CONFIRM_UNIFIED] {source_socket} type={msg_type} id={msg_id} msg={msg_str[:80]}")

    # Forward to confirm_listener (this is the main purpose)
    if heartbeat_push:
        try:
            heartbeat_push.send_json(msg, zmq.NOBLOCK)
            LOG.info(f"[CONFIRM_UNIFIED] Forwarded {msg_type} from {source_socket}")
        except Exception as e:
            LOG.warning(f"[CONFIRM_UNIFIED] Failed to forward from {source_socket}: {e}")


def start_queue_worker():
    """Idempotent queue worker starter"""
    global worker
    if worker and worker.is_alive():
        return
    worker = threading.Thread(target=queue_to_router_forever, name="queue2router", daemon=True)
    worker.start()
    LOG.info("[BOOT] queue2router started")


def _extract_payload_bytes(payload_field):
    """Extract raw payload bytes from various formats"""
    if isinstance(payload_field, (bytes, bytearray)):
        return payload_field
    elif isinstance(payload_field, str):
        return payload_field.encode("utf-8")
    elif isinstance(payload_field, dict):
        return json.dumps(payload_field, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    else:
        # Fallback: convert to string then bytes
        return str(payload_field).encode("utf-8")


def queue_to_router_forever():
    """Robust queue processing with timeout and error handling"""
    backoff = 0.2
    while not stop_evt.is_set():
        try:
            try:
                item = ipc_q.get(timeout=1.0)  # DO NOT block forever
            except queue.Empty:
                continue

            tu = item["target_uuid"]
            payload_field = item["payload"]
            ident = identity_map.get(tu)
            if ident is None:
                # no route yet → requeue and pause briefly
                ipc_q.put(item)
                time.sleep(0.2)
                continue

            # Extract only the payload bytes, not the wrapper dict
            payload_bytes = _extract_payload_bytes(payload_field)

            # FRAME LOGGING: Log exact payload before sending (as per surgical checklist)
            payload_str = payload_bytes.decode("utf-8")
            LOG.info("[FRAME_SEND] First 120 chars: %s", payload_str[:120])
            LOG.info("[FRAME_SEND] Payload length: %d bytes", len(payload_bytes))

            # Hex of "type" key region to catch weird quotes
            type_region = payload_str[:50] if len(payload_str) >= 50 else payload_str
            LOG.info("[FRAME_SEND] Type region hex: %s", type_region.encode("utf-8").hex())

            # Send with DEALER/ROUTER 3-frame protocol: [identity, empty delimiter, payload]
            uuid_bytes = tu.encode("utf-8")
            router.send_multipart([uuid_bytes, b"", payload_bytes])

            # Parse payload to log target_uuid details
            try:
                cmd = json.loads(payload_bytes.decode("utf-8"))
                sent_uuid = cmd.get("target_uuid", "MISSING")
                LOG.info(
                    "[DEQ] → target_uuid=%r len=%d hex=%s bytes=%d",
                    sent_uuid,
                    len(sent_uuid) if sent_uuid != "MISSING" else 0,
                    sent_uuid.encode("utf-8").hex() if sent_uuid != "MISSING" else "N/A",
                    len(payload_bytes),
                )
            except:
                LOG.info("[DEQ] → %s bytes=%d (payload parse failed)", tu, len(payload_bytes))
            backoff = 0.2
        except Exception:
            LOG.exception("[queue2router] loop error")
            time.sleep(backoff)
            backoff = min(5.0, backoff * 2.0)


def enqueue_cmd(uuid: str, obj: dict):
    """Enqueue command for processing"""
    # Use current EA UUID if available, otherwise use provided
    global current_ea_uuid
    target_uuid = current_ea_uuid if current_ea_uuid else uuid
    target_uuid = target_uuid.strip()  # Guard against hidden chars

    # Ensure target_uuid is in the payload
    obj["target_uuid"] = target_uuid

    payload = json.dumps(obj, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ipc_q.put({"target_uuid": target_uuid, "payload": payload})
    LOG.info(
        "[ENQ] %s %s bytes=%d target_uuid=%r len=%d hex=%s",
        target_uuid,
        obj.get("type"),
        len(payload),
        target_uuid,
        len(target_uuid),
        target_uuid.encode("utf-8").hex(),
    )


def ipc_bridge_forever():
    """Bridge old IPC queue to new internal queue with UUID firewall"""
    global current_ea_uuid
    while not stop_evt.is_set():
        try:
            try:
                cmd = pull.recv_json(flags=zmq.NOBLOCK)
            except zmq.Again:
                time.sleep(0.1)
                continue

            # IPC BRIDGE GUARD: Handle wrapped payloads
            if "payload" in cmd and "target_uuid" in cmd:
                # This is a wrapped payload - extract the raw command JSON
                uuid = cmd.get("target_uuid")
                payload_field = cmd.get("payload")

                if payload_field is None:
                    LOG.warning("[IPC_BRIDGE] REJECT_MALFORMED - missing payload field")
                    continue

                try:
                    # Parse the wrapped payload to get the raw command
                    if isinstance(payload_field, str):
                        raw_cmd = json.loads(payload_field)
                    else:
                        raw_cmd = payload_field

                    cmd_type = raw_cmd.get("type", "UNKNOWN")
                    fire_id = raw_cmd.get("fire_id", "NO_ID")

                    LOG.info(
                        f"[IPC_BRIDGE] FORWARDED_RAW {cmd_type} {fire_id} target_uuid='{uuid}' unwrapped from wrapper"
                    )

                    # UUID FIREWALL: Reject commands with wrong UUID
                    if current_ea_uuid and uuid != current_ea_uuid:
                        LOG.warning(
                            f"[UUID_FIREWALL] REJECTED command {cmd_type} {fire_id} - target_uuid='{uuid}' != learned_uuid='{current_ea_uuid}'"
                        )
                        continue

                    # Forward the raw command JSON (unwrapped)
                    raw_payload = json.dumps(raw_cmd, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
                    ipc_q.put({"target_uuid": uuid, "payload": raw_payload})
                    LOG.info(f"[IPC_BRIDGE] ACCEPTED wrapped {cmd_type} {fire_id} → queue")

                except json.JSONDecodeError:
                    LOG.warning("[IPC_BRIDGE] REJECT_MALFORMED - invalid JSON in payload field")
                    continue

            else:
                # Standard command processing (backward compatibility)
                uuid = cmd.get("target_uuid")
                cmd_type = cmd.get("type", "UNKNOWN")
                fire_id = cmd.get("fire_id", "NO_ID")

                # Log EVERY inbound command with UUID details
                if uuid:
                    LOG.info(
                        f"[IPC_IN] {cmd_type} {fire_id} target_uuid='{uuid}' len={len(uuid)} hex={uuid.encode('utf-8').hex()}"
                    )

                    # UUID FIREWALL: Reject commands with wrong UUID
                    if current_ea_uuid and uuid != current_ea_uuid:
                        LOG.warning(
                            f"[UUID_FIREWALL] REJECTED command {cmd_type} {fire_id} - target_uuid='{uuid}' != learned_uuid='{current_ea_uuid}'"
                        )
                        continue  # Drop the command

                    # CUTOVER: SOURCE routing
                    if cmd_type == "fire" and SOURCE in ["metasocket", "both"]:
                        if _route_to_metasocket(cmd):
                            LOG.info(f"[CUTOVER] ROUTED {cmd_type} {fire_id} → MetaSocket")
                            continue
                        elif SOURCE == "metasocket":
                            LOG.warning(f"[CUTOVER] MetaSocket failed, dropping command {fire_id}")
                            continue

                    # Default EA routing (SOURCE=ea or fallback)
                    payload = json.dumps(cmd, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
                    ipc_q.put({"target_uuid": uuid, "payload": payload})
                    LOG.info(f"[IPC_BRIDGE] ACCEPTED {cmd_type} {fire_id} → queue")
                else:
                    LOG.warning(f"[IPC_IN] REJECTED {cmd_type} {fire_id} - NO target_uuid")
        except Exception:
            LOG.exception("[ipc-bridge] error")
            time.sleep(0.2)


def ping_self_test(uuid: str):
    """Built-in self-test - simplified version without confirm socket dependency"""
    LOG.info(f"[SELF_TEST] Testing command enqueue for {uuid}")
    try:
        # Test that we can enqueue a command
        pid = f"CONFIRM-PATH-{int(time.time())}"
        enqueue_cmd(uuid, {"type": "ping", "target_uuid": uuid, "ping_id": pid})
        LOG.info(f"[SELF_TEST] Successfully enqueued ping command {pid}")
        return True
    except Exception as e:
        LOG.error(f"[SELF_TEST] Failed to enqueue ping: {e}")
        return False


def main():
    global heartbeat_push, router, pull

    # Initialize sockets
    router = ctx.socket(zmq.ROUTER)
    router.bind(PUSH_BIND)
    pull = ctx.socket(zmq.PULL)
    pull.setsockopt(zmq.RCVHWM, 10000)
    pull.bind(QUEUE_PULL)

    # Initialize heartbeat forwarding socket (FIXED: use different port to avoid loop)
    heartbeat_push = ctx.socket(zmq.PUSH)
    heartbeat_push.connect("tcp://localhost:5559")  # FIXED: avoid port loop with 5558

    LOG.info("[CMD] ROUTER bound %s", PUSH_BIND)
    LOG.info("[CMD] Queue bound %s", QUEUE_PULL)
    LOG.info("[CMD] Confirm bound %s", CONFIRM_BIND)

    # Start identity learning thread
    threading.Thread(target=recv_router_forever, name="learn-ident", daemon=True).start()

    # Start IPC bridge thread with error handling
    ipc_thread = threading.Thread(target=ipc_bridge_forever, name="ipc-bridge", daemon=True)
    ipc_thread.start()
    LOG.info("[THREAD] IPC bridge thread started: %s", ipc_thread.name)

    # Start queue worker
    start_queue_worker()

    LOG.info("[BOOT] router online")

    # Run self-test after brief startup delay
    time.sleep(2)
    ping_self_test("COMMANDER_DEV_001")

    # Keep main thread alive but don't block on join()
    try:
        while True:
            time.sleep(1)
            if not (worker and worker.is_alive()):
                LOG.error("[MAIN] Queue worker died - restarting")
                start_queue_worker()
    except KeyboardInterrupt:
        LOG.info("[MAIN] Shutdown requested")
        stop_evt.set()


if __name__ == "__main__":
    main()
