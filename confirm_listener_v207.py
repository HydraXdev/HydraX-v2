#!/usr/bin/env python3
"""
Enhanced Confirmation Listener for BITTEN v2.07H
Handles all new message types: confirmation, position_closed, hybrid_event, pong, close_confirmation
"""

import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime

import zmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOG = logging.getLogger("CONFIRM_v207")

DB = os.getenv("BITTEN_DB", "/root/HydraX-v2/bitten.db")
CONFIRM_BIND = os.getenv("CONFIRM_BIND", "tcp://*:5558")

# Hook A imports for FSM registration
try:
    from src.bitten_core.entitlement import EntitlementManager
    from src.bitten_core.exit_profiles import exit_profile_manager

    FSM_AVAILABLE = True
except ImportError as e:
    LOG.warning(f"FSM not available: {e}")
    FSM_AVAILABLE = False

# Event Bus integration
try:
    from event_bus.producer import EventProducer

    EVENT_BUS_AVAILABLE = True
    event_producer = EventProducer()
except ImportError as e:
    LOG.warning(f"Event Bus not available: {e}")
    EVENT_BUS_AVAILABLE = False
    event_producer = None


def parse_json_loose(b):
    """Parse JSON with tolerance for encoding issues"""
    s = b.decode("utf-8", "ignore").strip()
    try:
        return json.loads(s)
    except Exception:
        try:
            # Try replacing single quotes with double quotes
            return json.loads(re.sub(r"'", '"', s))
        except Exception as e:
            LOG.error("JSON parse failed: %s | payload=%r", e, s[:500])
            return None


def ensure_tables():
    """Create necessary tables for v2.07H tracking"""
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Enhanced fires table with hybrid tracking
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
        partial_closes TEXT,  -- JSON array of partial close events
        trail_updates TEXT,   -- JSON array of trail update events
        close_reason TEXT,    -- TP_HIT, SL_HIT, MANUAL, STOP_OUT
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

    # Hybrid events tracking table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS hybrid_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket INTEGER NOT NULL,
        fire_id TEXT NOT NULL,
        event_type TEXT NOT NULL,  -- PARTIAL_CLOSE, SL_BREAKEVEN, TRAIL_UPDATE
        volume REAL,
        pips REAL,
        timestamp INTEGER NOT NULL,
        uuid TEXT NOT NULL,
        node_id TEXT
    )
    """
    )

    # Position snapshots from HEARTBEAT_METRICS
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS position_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        positions_json TEXT NOT NULL,
        balance REAL,
        equity REAL,
        margin_level REAL,
        open_positions INTEGER
    )
    """
    )

    # Position closures tracking
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
        reason TEXT,  -- TP_HIT, SL_HIT, MANUAL, STOP_OUT
        uuid TEXT,
        timestamp INTEGER
    )
    """
    )

    con.commit()
    con.close()


def handle_confirmation(m):
    """Handle fire confirmation messages - ONLY REAL EA DATA"""
    fire_id = m.get("fire_id")

    # SECURITY: Log all confirmations for audit trail
    LOG.info(f"🔍 CONFIRMATION RECEIVED: {json.dumps(m, indent=2)}")

    if not fire_id:
        LOG.warning("Confirmation without fire_id: %s", m)
        return

    # CORRUPTION PREVENTION: Validate this is real EA data
    ticket = m.get("ticket", 0)
    # EA sends "uuid" field - check all possible field names
    user_uuid = m.get("user_uuid") or m.get("target_uuid") or m.get("uuid")

    # Block obvious test data (allow ticket=0 for legitimate failures)
    if (
        fire_id.startswith(("TEST_", "DEBUG-", "PASS-QA"))
        or ticket in [12345678, 99999]
        or (user_uuid and user_uuid != "COMMANDER_DEV_001")
    ):
        LOG.warning(f"🚫 BLOCKED TEST/FAKE confirmation: {fire_id}, ticket={ticket}, uuid={user_uuid}")
        return

    # Map status
    status = (m.get("status") or "").lower()
    if status in ("success", "filled", "ok"):
        db_status = "FILLED"
    elif status in ("failed", "rejected", "error"):
        db_status = "FAILED"
    else:
        db_status = "UNKNOWN"

    ticket = m.get("ticket", 0)
    price = m.get("price", 0)
    lot = m.get("lot")  # Don't default to 0 - preserve original if not provided
    message = m.get("message", "")
    target_uuid = m.get("user_uuid") or m.get("target_uuid")

    # Update fires table
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

        # LAST-WRITE-WINS with SUCCESS PRIORITY: Don't downgrade success to failure
        current_time = int(time.time())

        # Check existing status first - also get existing lot
        cur.execute("SELECT status, ticket, lot FROM fires WHERE fire_id=?", (fire_id,))
        existing = cur.fetchone()

        should_update = True
        if existing:
            existing_status, existing_ticket, existing_lot = existing
            # Preserve original lot if confirmation doesn't include it
            if lot is None or lot == 0:
                lot = existing_lot  # Keep original lot value
                LOG.info(f"[CONFIRM] Preserving original lot={lot} (confirmation didn't include lot)")
            # Don't downgrade FILLED with ticket to anything else (FAILED or UNKNOWN)
            if existing_status == "FILLED" and existing_ticket > 0 and db_status != "FILLED":
                should_update = False
                LOG.info(
                    f"[CONFIRM] Ignoring {db_status} update for {fire_id} - already FILLED with ticket {existing_ticket}"
                )

        if should_update:
            cur.execute(
                """
                UPDATE fires
                SET status=?, ticket=?, price=?, lot=?, target_uuid=?, updated_at=?
                WHERE fire_id=?
            """,
                (db_status, ticket, price, lot, target_uuid, current_time, fire_id),
            )

            LOG.info(f"[CONFIRM] Updated {fire_id}: {db_status}, ticket={ticket}, price={price}")

        rows = cur.rowcount
        con.commit()

        # If filled, add to live_positions
        if db_status == "FILLED" and rows > 0:
            cur.execute(
                """
                SELECT user_id, symbol, direction, sl, tp, lot
                FROM fires WHERE fire_id = ?
            """,
                (fire_id,),
            )
            fire_data = cur.fetchone()

            if fire_data:
                user_id, symbol, direction, sl, tp, lot_size = fire_data
                cur.execute(
                    """
                    INSERT OR REPLACE INTO live_positions
                    (fire_id, user_id, symbol, direction, entry_price, sl, tp,
                     lot_size, last_update, status, ticket)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
                """,
                    (fire_id, user_id, symbol, direction, price, sl, tp, lot_size, int(time.time()), ticket),
                )
                LOG.info(f"✅ FILLED: {fire_id} → ticket {ticket} @ {price}")

        con.close()

        # Enrich confirmation with slot and account information
        try:
            from fire_integration import ConfirmationEnricher

            enricher = ConfirmationEnricher()
            enriched_confirmation = enricher.enrich_confirmation(
                {
                    "type": "confirmation",
                    "fire_id": fire_id,
                    "status": db_status.lower(),
                    "ticket": ticket,
                    "price": price,
                    "message": message,
                    "user_uuid": target_uuid,
                    "account": {"ticket": ticket, "price": price, "lot": lot},
                }
            )
            LOG.info(f"[ENRICH] Enriched confirmation: {json.dumps(enriched_confirmation.get('slots', {}))}")
        except Exception as e:
            LOG.warning(f"[ENRICH] Failed to enrich confirmation: {e}")
            enriched_confirmation = m

        # Publish enriched confirmation to event bus
        if EVENT_BUS_AVAILABLE and event_producer:
            event_producer.publish("trade.confirmation", enriched_confirmation)

    except Exception as e:
        LOG.error(f"Failed to handle confirmation: {e}")


def handle_position_closed(m):
    """Handle position closure events"""
    ticket = m.get("ticket")
    fire_id = m.get("fire_id")
    symbol = m.get("symbol")
    volume = m.get("volume", 0)
    close_price = m.get("close_price", 0)
    profit = m.get("profit", 0)
    reason = m.get("reason", "MANUAL")  # TP_HIT, SL_HIT, MANUAL, STOP_OUT
    uuid = m.get("uuid")
    timestamp = m.get("timestamp", int(time.time()))

    if not ticket:
        LOG.warning("position_closed without ticket: %s", m)
        return

    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

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

            # Release slot if applicable
            if FSM_AVAILABLE:
                try:
                    from src.bitten_core.fire_mode_database import FireModeDatabase

                    cur.execute("SELECT user_id FROM fires WHERE fire_id=?", (fire_id,))
                    result = cur.fetchone()
                    if result:
                        fire_db = FireModeDatabase()
                        fire_db.release_slot(result[0], fire_id)
                        LOG.info(f"Released slot for fire_id {fire_id}")
                except Exception as e:
                    LOG.warning(f"Failed to release slot: {e}")

        con.commit()
        con.close()

        LOG.info(f"📊 CLOSED: Ticket {ticket} ({reason}) P&L: {profit:.2f}")

        # Enrich position close event with slot settlement
        try:
            from fire_integration import ConfirmationEnricher

            enricher = ConfirmationEnricher()
            enriched_close = enricher.enrich_confirmation(
                {
                    "type": "position_closed",
                    "fire_id": fire_id,
                    "ticket": ticket,
                    "status": "closed",
                    "close_reason": reason,
                    "close_price": close_price,
                    "profit": profit,
                    "user_uuid": uuid,
                    "account": {"ticket": ticket, "close_price": close_price, "profit": profit, "reason": reason},
                }
            )
            LOG.info(f"[SETTLE] Position close enriched with slots: {json.dumps(enriched_close.get('slots', {}))}")
        except Exception as e:
            LOG.warning(f"[SETTLE] Failed to enrich position close: {e}")
            enriched_close = m

        # Publish enriched close event to event bus
        if EVENT_BUS_AVAILABLE and event_producer:
            event_producer.publish("trade.closed", enriched_close)

    except Exception as e:
        LOG.error(f"Failed to handle position_closed: {e}")


def handle_hybrid_event(m):
    """Handle hybrid position management events"""
    event_type = m.get("event")  # PARTIAL_CLOSE, SL_BREAKEVEN, TRAIL_UPDATE
    ticket = m.get("ticket")
    fire_id = m.get("fire_id")
    volume = m.get("volume", 0)
    pips = m.get("pips", 0)
    uuid = m.get("target_uuid")
    node_id = m.get("node_id")
    timestamp_str = m.get("timestamp", "")

    if not event_type or not ticket:
        LOG.warning("Invalid hybrid_event: %s", m)
        return

    # Parse timestamp if string
    if isinstance(timestamp_str, str):
        timestamp = int(time.time())
    else:
        timestamp = timestamp_str

    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

        # Record hybrid event
        cur.execute(
            """
            INSERT INTO hybrid_events
            (ticket, fire_id, event_type, volume, pips, timestamp, uuid, node_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (ticket, fire_id, event_type, volume, pips, timestamp, uuid, node_id),
        )

        # Update fires table with hybrid activity
        if fire_id:
            if event_type == "PARTIAL_CLOSE":
                # Append to partial_closes JSON array
                cur.execute("SELECT partial_closes FROM fires WHERE fire_id=?", (fire_id,))
                result = cur.fetchone()
                partials = json.loads(result[0]) if result and result[0] else []
                partials.append({"volume": volume, "pips": pips, "timestamp": timestamp})
                cur.execute(
                    """
                    UPDATE fires SET partial_closes=?, updated_at=? WHERE fire_id=?
                """,
                    (json.dumps(partials), int(time.time()), fire_id),
                )

            elif event_type == "TRAIL_UPDATE":
                # Append to trail_updates JSON array
                cur.execute("SELECT trail_updates FROM fires WHERE fire_id=?", (fire_id,))
                result = cur.fetchone()
                trails = json.loads(result[0]) if result and result[0] else []
                trails.append({"pips": pips, "timestamp": timestamp})
                cur.execute(
                    """
                    UPDATE fires SET trail_updates=?, updated_at=? WHERE fire_id=?
                """,
                    (json.dumps(trails), int(time.time()), fire_id),
                )

        con.commit()
        con.close()

        LOG.info(f"🎯 HYBRID: {event_type} for ticket {ticket} @ {pips:.1f} pips")

        # Publish to event bus
        if EVENT_BUS_AVAILABLE and event_producer:
            event_producer.publish(f"hybrid.{event_type.lower()}", m)

    except Exception as e:
        LOG.error(f"Failed to handle hybrid_event: {e}")


def handle_close_confirmation(m):
    """Handle close_ticket and close_all confirmations"""
    command_type = m.get("command_type")  # close_ticket or close_all
    status = m.get("status", "").lower()
    ticket = m.get("ticket", 0)
    close_price = m.get("close_price", 0)
    lot = m.get("lot", 0)
    message = m.get("message", "")

    LOG.info(f"📝 CLOSE: {command_type} {status} - {message}")

    # Publish to event bus if available
    if EVENT_BUS_AVAILABLE and event_producer:
        event_producer.publish(f"close.{command_type}", m)


def handle_pong(m):
    """Handle ping response"""
    ping_id = m.get("ping_id")
    node_id = m.get("node_id")
    uuid = m.get("user_uuid")
    timestamp = m.get("timestamp")

    LOG.info(f"🏓 PONG: {ping_id} from {uuid} ({node_id})")

    # Could update EA last_seen here if needed
    if uuid:
        try:
            con = sqlite3.connect(DB)
            cur = con.cursor()
            cur.execute(
                """
                UPDATE ea_instances SET last_seen=? WHERE target_uuid=?
            """,
                (int(time.time()), uuid),
            )
            con.commit()
            con.close()
        except Exception as e:
            LOG.warning(f"Failed to update EA last_seen: {e}")


def main():
    """Main listener loop for port 5558"""
    ensure_tables()

    ctx = zmq.Context()
    sock = ctx.socket(zmq.PULL)
    sock.bind(CONFIRM_BIND)
    LOG.info(f"🎧 Listening on {CONFIRM_BIND} for v2.07H messages")

    poller = zmq.Poller()
    poller.register(sock, zmq.POLLIN)

    while True:
        try:
            # Poll with 1 second timeout for periodic tasks
            socks = dict(poller.poll(1000))

            if sock in socks:
                raw = sock.recv()
                m = parse_json_loose(raw)
                if not m:
                    continue

                msg_type = m.get("type", "").lower()

                # Route to appropriate handler
                if msg_type == "confirmation":
                    handle_confirmation(m)
                elif msg_type == "position_opened":
                    # EA sends position_opened events - treat as confirmation
                    handle_confirmation(m)
                elif msg_type == "position_closed":
                    handle_position_closed(m)
                elif msg_type == "hybrid_event":
                    handle_hybrid_event(m)
                elif msg_type == "close_confirmation":
                    handle_close_confirmation(m)
                elif msg_type == "pong":
                    handle_pong(m)
                else:
                    LOG.warning(f"Unknown message type: {msg_type}")

        except KeyboardInterrupt:
            LOG.info("Shutting down...")
            break
        except Exception as e:
            LOG.error(f"Error in main loop: {e}")
            time.sleep(1)

    sock.close()
    ctx.term()


if __name__ == "__main__":
    main()
