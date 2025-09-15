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
        
        # EVENT BUS INTEGRATION - Track trade confirmation
        try:
            from event_bus.event_bridge import trade_confirmed
            trade_confirmed({
                'fire_id': fire_id,
                'signal_id': fire_id,  # fire_id is based on signal_id
                'status': db_status,
                'ticket': m.get("ticket") or m.get("order"),
                'price': m.get("price") or m.get("execution_price"),
                'volume': m.get("volume", m.get("lot")),
                'symbol': m.get("symbol"),
                'direction': m.get("direction"),
                'timestamp': int(time.time())
            })
            LOG.info("✅ Event Bus: Trade confirmation published for %s", fire_id)
        except Exception as e:
            LOG.warning("⚠️ Event Bus: Failed to publish confirmation (non-critical): %s", e)
            
    elif status in ("FAILED", "REJECTED", "ERROR"):
        db_status = "FAILED"
    elif status in ("CLOSED", "CLOSE", "COMPLETED", "TP_HIT", "SL_HIT"):
        db_status = "CLOSED"
        
        # EVENT BUS INTEGRATION - Track trade closure/outcome
        try:
            from event_bus.event_bridge import trade_outcome
            outcome_type = 'TP_HIT' if 'TP_HIT' in status else 'SL_HIT' if 'SL_HIT' in status else 'CLOSED'
            trade_outcome({
                'fire_id': fire_id,
                'signal_id': fire_id,  # fire_id is based on signal_id
                'outcome': outcome_type,
                'status': db_status,
                'profit': m.get("profit"),
                'pips': m.get("pips"),
                'close_price': m.get("price"),
                'timestamp': int(time.time())
            })
            LOG.info("✅ Event Bus: Trade outcome published for %s (%s)", fire_id, outcome_type)
        except Exception as e:
            LOG.warning("⚠️ Event Bus: Failed to publish outcome (non-critical): %s", e)
        
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
            # Get signal details for position tracking
            cur.execute("""
                SELECT f.user_id, s.symbol, s.direction, s.entry_price, s.sl, s.tp
                FROM fires f
                LEFT JOIN signals s ON f.fire_id = s.signal_id
                WHERE f.fire_id = ?
            """, (fire_id,))
            position_data = cur.fetchone()
            
            if position_data:
                user_id, symbol, direction, entry, sl, tp = position_data
                lot_size = m.get("volume", m.get("lot", 0.01))
                
                # Fallback to message data if signal data is missing
                if not symbol:
                    symbol = m.get("symbol")
                if not direction:
                    direction = m.get("direction", m.get("type"))
                if not entry:
                    entry = price  # Use fill price
                
                # Insert into live_positions
                cur.execute("""
                    INSERT OR REPLACE INTO live_positions 
                    (fire_id, user_id, symbol, direction, entry_price, sl, tp, 
                     lot_size, last_update, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """, (fire_id, user_id, symbol or m.get("symbol"), 
                      direction or m.get("direction"), 
                      price or entry, sl, tp, lot_size, int(time.time())))
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
        else:
            LOG.warning("fire_id %s not found in database", fire_id)
            
    except Exception as e:
        LOG.error("DB update failed for %s: %s", fire_id, e)

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
        if msg_type in ("confirmation", "close_confirmation", "filled", "failed"):
            update_fire(m)
        elif msg_type == "hybrid_event":
# [DISABLED BITMODE]             # Log BITMODE hybrid events with details
            LOG.info("🎯 HYBRID_EVENT: fire_id=%s event=%s partial=%s%% trail=%s pips", 
                     m.get("fire_id", "?"), 
                     m.get("event", "?"),
                     m.get("percent", "?"),
                     m.get("trail_distance", "?"))
        else:
            LOG.info("non-confirm msg type=%s", m.get("type"))

if __name__ == "__main__":
    main()