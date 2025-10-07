#!/usr/bin/env python3
"""
Robust Confirmation Listener for BITTEN Trading System
Handles trade confirmations from EA via ZMQ with fire_id correlation
"""

import json, re, os, sqlite3, zmq, logging, time
from datetime import datetime

# Hook A imports for FSM registration
try:
    from src.bitten_core.exit_profiles import exit_profile_manager
    from src.bitten_core.entitlement import EntitlementManager
    FSM_AVAILABLE = True
except ImportError as e:
    LOG = logging.getLogger("CONFIRM")
    LOG.warning(f"FSM not available: {e}")
    FSM_AVAILABLE = False

# Event Bus integration for confirmation publishing
try:
    from event_bus.producer import EventProducer
    EVENT_BUS_AVAILABLE = True
    event_producer = EventProducer()
except ImportError as e:
    LOG = logging.getLogger("CONFIRM")
    LOG.warning(f"⚠️ Event Bus: Failed to import EventProducer (non-critical): {e}")
    EVENT_BUS_AVAILABLE = False
    event_producer = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
LOG = logging.getLogger("CONFIRM")

DB = os.getenv("BITTEN_DB", "/root/HydraX-v2/bitten.db")
BIND = os.getenv("CONFIRM_BIND", "tcp://*:5558")

def parse_json_loose(b):
    """Parse JSON with tolerance for single quotes and encoding issues"""
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

def update_fire(m):
    """Update fire status in database and manage slot releases"""
    # Extract fire_id - REQUIRED
    fire_id = m.get("fire_id") or m.get("id")
    if not fire_id:
        LOG.warning("drop confirm without fire_id: %s", m)
        return
    
    # Map status
    status = (m.get("status") or "").upper()
    if status in ("FILLED", "SUCCESS", "OK", "FILLED_OK"):
        db_status = "FILLED"
    elif status in ("FAILED", "REJECTED", "ERROR"):
        db_status = "FAILED"
    elif status in ("CLOSED", "CLOSE", "COMPLETED", "TP_HIT", "SL_HIT"):
        db_status = "CLOSED"
        # Release slot when trade closes
        try:
            # Get user_id from fires table
            con = sqlite3.connect(DB)
            cur = con.cursor()
            cur.execute("SELECT user_id FROM fires WHERE fire_id=?", (fire_id,))
            result = cur.fetchone()
            if result:
                user_id = result[0]
                # Release the slot
                from src.bitten_core.fire_mode_database import FireModeDatabase
                fire_db = FireModeDatabase()
                if fire_db.release_slot(user_id, fire_id):
                    LOG.info("Released slot for user %s, fire_id %s", user_id, fire_id)
            con.close()
        except Exception as e:
            LOG.error("Failed to release slot: %s", e)
    else:
        db_status = "FAILED"  # Default to FAILED
    
    # Extract ticket and price
    ticket = m.get("ticket") or m.get("order") or 0
    price = m.get("price") or m.get("execution_price") or 0
    
    # Extract target_uuid from message (EA identifier)
    target_uuid = m.get("target_uuid") or m.get("ea_id") or m.get("uuid")
    
    # Update database
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        
        # Update with target_uuid if available
        if target_uuid:
            cur.execute(
                "UPDATE fires SET status=?, ticket=?, price=?, target_uuid=? WHERE fire_id=?",
                (db_status, ticket, price, target_uuid, fire_id)
            )
        else:
            cur.execute(
                "UPDATE fires SET status=?, ticket=?, price=? WHERE fire_id=?",
                (db_status, ticket, price, fire_id)
            )
        rows_affected = cur.rowcount
        
        # If trade was filled, add to live_positions
        if db_status == "FILLED" and rows_affected > 0:
            # Get trade data from fires table (now includes symbol, direction, sl, tp, lot)
            cur.execute("""
                SELECT user_id, symbol, direction, sl, tp, lot 
                FROM fires WHERE fire_id = ?
            """, (fire_id,))
            fire_data = cur.fetchone()
            
            if fire_data:
                user_id, symbol, direction, sl, tp, lot_size = fire_data
                entry = price  # Use actual fill price from EA
                
                # Ensure required fields are present
                if not symbol:
                    LOG.warning(f"Missing symbol in fires table for {fire_id}, skipping live_positions insert")
                    return
                if not direction:
                    LOG.warning(f"Missing direction in fires table for {fire_id}, skipping live_positions insert")
                    return
                
                # Insert into live_positions
                cur.execute("""
                    INSERT OR REPLACE INTO live_positions 
                    (fire_id, user_id, symbol, direction, entry_price, sl, tp, 
                     lot_size, last_update, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """, (fire_id, user_id, symbol, direction, entry, sl, tp, lot_size, int(time.time())))
                LOG.info(f"Added position to live_positions: {fire_id}")
                
                # HOOK A: Register position with FSM for tiered exit management
                if FSM_AVAILABLE and ticket and symbol and direction:
                    try:
                        # Get user tier
                        em = EntitlementManager()
                        tier = em.get_user_tier(str(user_id))
                        
                        # Calculate risk in pips
                        actual_entry = price if price else entry
                        actual_sl = sl if sl else m.get("sl", 0)
                        
                        if actual_entry and actual_sl:
                            # Calculate pip risk based on symbol
                            if 'JPY' in str(symbol):
                                pip_size = 0.01
                            elif symbol in ['XAUUSD']:
                                pip_size = 0.1
                            elif symbol in ['XAGUSD']:
                                pip_size = 0.001
                            else:
                                pip_size = 0.0001
                            
                            pip_risk = abs(actual_entry - actual_sl) / pip_size
                            r_pips = int(round(pip_risk))
                            
                            # Register with FSM using exit_profile_manager
                            exit_profile_manager.on_position_open(
                                ticket=int(ticket),
                                fire_id=fire_id,
                                user_id=str(user_id),
                                symbol=str(symbol),
                                direction=str(direction).upper(),
                                entry_px=float(actual_entry),
                                sl_px=float(actual_sl),
                                tp_px=tp if tp else float(actual_entry) + (float(actual_entry) - float(actual_sl)) * 10,  # Far TP for runner
                                lot_size=float(lot_size)
                            )
                            
                            # Persist timer metadata to SQLite for timeout handling
                            from src.bitten_core.timers import set_timeout_meta
                            from datetime import datetime
                            import toml
                            
                            # Load tier config for max hold time
                            try:
                                tiers_cfg = toml.load("/root/HydraX-v2/config/tiers.toml")
                                tier_cfg = tiers_cfg.get(tier, {})
                                max_hold_min = tier_cfg.get("MAX_HOLD_MIN", 90)
                            except:
                                max_hold_min = 90  # Default fallback
                            
                            # Store timeout metadata in persistent SQLite database
                            open_ts_utc = datetime.utcnow().isoformat()
                            set_timeout_meta(int(ticket), open_ts_utc, max_hold_min)
                            
                            LOG.info(f"✅ FSM REGISTERED ticket={ticket} {symbol} {direction} entry={actual_entry:.5f} r_pips={r_pips} tier={tier} timer={max_hold_min}min")
                        else:
                            LOG.warning(f"Cannot register FSM - missing entry/SL: entry={actual_entry}, sl={actual_sl}")
                    except Exception as e:
                        LOG.error(f"FSM registration failed: {e}")
                else:
                    if FSM_AVAILABLE:
                        LOG.warning(f"Skipping FSM registration - missing data: ticket={ticket}, symbol={symbol}, direction={direction}")
        
        # If trade closed, update live_positions
        elif db_status == "CLOSED":
            cur.execute("""
                UPDATE live_positions 
                SET status = 'CLOSED', last_update = ?
                WHERE fire_id = ?
            """, (int(time.time()), fire_id))
            LOG.info(f"Closed position in live_positions: {fire_id}")
        
        con.commit()
        con.close()
        
        if rows_affected > 0:
            LOG.info("fire %s → %s (ticket=%s price=%s)", fire_id, db_status, ticket, price)
            
            # Publish confirmation event to event bus for slot management
            if EVENT_BUS_AVAILABLE and event_producer:
                try:
                    confirmation_event = {
                        "fire_id": fire_id,
                        "status": db_status,
                        "ticket": ticket,
                        "price": price,
                        "timestamp": int(time.time()),
                        "target_uuid": target_uuid
                    }
                    event_producer.publish("execution.confirmation.v1", confirmation_event)
                    LOG.debug(f"📡 Event Bus: Published confirmation for {fire_id}")
                except Exception as e:
                    LOG.warning(f"⚠️ Event Bus: Failed to publish confirmation (non-critical): {e}")
        else:
            LOG.warning("fire_id %s not found in database", fire_id)
            
    except Exception as e:
        LOG.error("DB update failed for %s: %s", fire_id, e)

def handle_enhanced_heartbeat(m):
    """Handle enhanced heartbeat with position array from EA v2.06H"""
    target_uuid = m.get("target_uuid", "")
    open_positions_count = m.get("open_positions", 0)
    positions = m.get("positions", [])
    
    LOG.info("📡 ENHANCED HEARTBEAT: %s - %d positions reported", target_uuid, open_positions_count)
    
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        
        # Get current database position count
        cur.execute("SELECT COUNT(*) FROM live_positions WHERE status = 'OPEN'")
        db_count = cur.fetchone()[0]
        
        # Sync database with EA reality
        if db_count != open_positions_count:
            LOG.warning("📊 POSITION MISMATCH: EA reports %d, DB shows %d - syncing...", 
                       open_positions_count, db_count)
        
        # Update position prices and P&L from EA data
        for pos in positions:
            ticket = pos.get("ticket", 0)
            fire_id = pos.get("fire_id", "")
            current_price = pos.get("current_price", 0)
            pnl = pos.get("pnl", 0)
            
            if ticket and fire_id:
                # Update live position with current market data
                cur.execute("""
                    UPDATE live_positions 
                    SET current_price = ?, unrealized_pnl = ?, last_update = ?
                    WHERE fire_id = ? AND status = 'OPEN'
                """, (current_price, pnl, int(time.time()), fire_id))
                
                # Update fires table with current market price
                cur.execute("""
                    UPDATE fires 
                    SET current_price = ?, unrealized_pnl = ?
                    WHERE fire_id = ?
                """, (current_price, pnl, fire_id))
        
        # Mark missing positions as potentially closed and update slots
        if len(positions) < db_count:
            # Get all DB positions
            cur.execute("""
                SELECT fire_id, symbol, user_id FROM live_positions 
                WHERE status = 'OPEN'
            """)
            db_positions = cur.fetchall()
            
            # Check which positions are missing from EA report
            ea_fire_ids = {pos.get("fire_id") for pos in positions}
            
            closed_positions = []
            for db_fire_id, symbol, user_id in db_positions:
                if db_fire_id not in ea_fire_ids:
                    LOG.warning("🔍 Position %s (%s) missing from EA - possibly closed manually", 
                               db_fire_id, symbol)
                    # Mark as potentially closed for investigation
                    cur.execute("""
                        UPDATE live_positions 
                        SET status = 'CLOSED_DETECTED', last_update = ?
                        WHERE fire_id = ? AND status = 'OPEN'
                    """, (int(time.time()), db_fire_id))
                    
                    closed_positions.append({
                        "fire_id": db_fire_id,
                        "symbol": symbol,
                        "user_id": user_id
                    })
            
            # Publish slot release events to event bus
            if closed_positions and EVENT_BUS_AVAILABLE and event_producer:
                for pos in closed_positions:
                    try:
                        slot_event = {
                            "fire_id": pos["fire_id"],
                            "user_id": pos["user_id"],
                            "symbol": pos["symbol"],
                            "event_type": "position_closed_detected",
                            "timestamp": int(time.time()),
                            "source": "enhanced_heartbeat"
                        }
                        event_producer.publish("slot.position_closed.v1", slot_event)
                        LOG.info("📡 Event Bus: Published slot release for %s (user %s)", 
                                pos["fire_id"], pos["user_id"])
                    except Exception as e:
                        LOG.warning("⚠️ Event Bus: Failed to publish slot release: %s", e)
        
        con.commit()
        con.close()
        
        # Publish position count update to event bus
        if EVENT_BUS_AVAILABLE and event_producer:
            try:
                position_update = {
                    "target_uuid": target_uuid,
                    "ea_position_count": open_positions_count,
                    "db_position_count": db_count,
                    "positions": positions,
                    "timestamp": int(time.time()),
                    "source": "enhanced_heartbeat"
                }
                event_producer.publish("position.count_update.v1", position_update)
                LOG.debug("📡 Event Bus: Published position count update")
            except Exception as e:
                LOG.warning("⚠️ Event Bus: Failed to publish position count: %s", e)
        
    except Exception as e:
        LOG.error("Enhanced heartbeat processing failed: %s", e)

def handle_position_monitoring(m):
    """Handle position monitoring messages from EA (position_opened/position_closed)"""
    fire_id = m.get("fire_id")
    command_type = m.get("command_type", "").lower()
    ticket = m.get("ticket", 0)
    symbol = m.get("symbol", "")
    direction = m.get("direction", "")
    price = m.get("price", 0)
    lot = m.get("lot", 0)
    target_uuid = m.get("target_uuid", "")
    
    if not fire_id or not ticket:
        LOG.warning("Position monitoring message missing fire_id or ticket: %s", m)
        return
        
    LOG.info("📊 POSITION MONITOR: %s %s ticket=%s symbol=%s", command_type.upper(), fire_id, ticket, symbol)
    
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        
        if command_type == "position_opened":
            # Check if this is a manual position (not from our fire system)
            if fire_id.startswith("MANUAL_"):
                LOG.info("⚠️ Manual position detected: %s - tracking but not managing", fire_id)
                # For manual positions, just log but don't interfere with slot management
                return
                
            # For BITTEN positions, ensure they're in our fires table
            cur.execute("SELECT user_id FROM fires WHERE fire_id = ?", (fire_id,))
            fire_record = cur.fetchone()
            
            if not fire_record:
                LOG.warning("Position opened but no fire record found: %s", fire_id)
                return
                
            user_id = fire_record[0]
            
            # Update fires table to FILLED if not already
            cur.execute("UPDATE fires SET status = 'FILLED', ticket = ?, price = ? WHERE fire_id = ?", 
                       (ticket, price, fire_id))
            
            # Add to live_positions
            cur.execute("""
                INSERT OR REPLACE INTO live_positions 
                (fire_id, user_id, symbol, direction, entry_price, sl, tp, lot_size, last_update, status)
                VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 'OPEN')
            """, (fire_id, user_id, symbol, direction, price, lot, int(time.time())))
            
            LOG.info("✅ Position opened tracked: %s ticket=%s", fire_id, ticket)
            
        elif command_type == "position_closed":
            # Update fires table to CLOSED
            cur.execute("UPDATE fires SET status = 'CLOSED' WHERE ticket = ?", (ticket,))
            
            # Update live_positions to CLOSED
            cur.execute("""
                UPDATE live_positions 
                SET status = 'CLOSED', last_update = ?
                WHERE fire_id = ? OR (SELECT ticket FROM fires WHERE fire_id = live_positions.fire_id) = ?
            """, (int(time.time()), fire_id, ticket))
            
            # Release slot for the user
            cur.execute("SELECT user_id FROM fires WHERE ticket = ?", (ticket,))
            user_record = cur.fetchone()
            
            if user_record:
                user_id = user_record[0]
                try:
                    from src.bitten_core.fire_mode_database import FireModeDatabase
                    fire_db = FireModeDatabase()
                    if fire_db.release_slot(user_id, fire_id):
                        LOG.info("Released slot for user %s, fire_id %s", user_id, fire_id)
                except Exception as e:
                    LOG.error("Failed to release slot: %s", e)
            
            LOG.info("✅ Position closed tracked: %s ticket=%s", fire_id, ticket)
        
        con.commit()
        con.close()
        
        # Publish to event bus if available
        if EVENT_BUS_AVAILABLE and event_producer:
            try:
                position_event = {
                    "fire_id": fire_id,
                    "command_type": command_type,
                    "ticket": ticket,
                    "symbol": symbol,
                    "direction": direction,
                    "price": price,
                    "lot": lot,
                    "timestamp": int(time.time()),
                    "target_uuid": target_uuid
                }
                event_producer.publish(f"position.{command_type}.v1", position_event)
                LOG.debug(f"📡 Event Bus: Published {command_type} for {fire_id}")
            except Exception as e:
                LOG.warning(f"⚠️ Event Bus: Failed to publish {command_type} (non-critical): {e}")
                
    except Exception as e:
        LOG.error("Position monitoring failed for %s: %s", fire_id, e)

def main():
    ctx = zmq.Context.instance()
    pull = ctx.socket(zmq.PULL)
    pull.bind(BIND)
    pull.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout
    
    LOG.info("confirm listener on %s", BIND)
    
    while True:
        try:
            b = pull.recv()
        except zmq.Again:
            # Timeout is normal, just continue
            continue
        
        # Parse message
        m = parse_json_loose(b)
        if not m:
            continue
        
        # Check message type
        msg_type = (m.get("type", "") or "").lower()
        command_type = (m.get("command_type", "") or "").lower()
        
        if msg_type in ("confirmation", "close_confirmation", "filled", "failed"):
            # Handle position monitoring confirmations
            if command_type in ("position_opened", "position_closed"):
                handle_position_monitoring(m)
            else:
                update_fire(m)
        elif msg_type == "heartbeat":
            # Handle enhanced heartbeat with position array from EA v2.06H
            if "positions" in m and "open_positions" in m:
                handle_enhanced_heartbeat(m)
            else:
                # Regular heartbeat - just log
                LOG.debug("Regular heartbeat from %s", m.get("target_uuid", "?"))
        elif msg_type == "hybrid_event":
# [DISABLED BITMODE]             # Log BITMODE hybrid events with details
            LOG.info("🎯 HYBRID_EVENT: fire_id=%s event=%s partial=%s%% trail=%s pips", 
                     m.get("fire_id", "?"), 
                     m.get("event", "?"),
                     m.get("percent", "?"),
                     m.get("trail_distance", "?"))
        else:
            LOG.info("non-confirm msg type=%s command_type=%s", m.get("type"), command_type)

if __name__ == "__main__":
    main()