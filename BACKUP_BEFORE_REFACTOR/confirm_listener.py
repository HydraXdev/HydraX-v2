#!/usr/bin/env python3
"""
Robust Confirmation Listener for BITTEN Trading System
Handles trade confirmations from EA via ZMQ with fire_id correlation
"""

import json, re, os, sqlite3, zmq, logging
from datetime import datetime

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
    """Update fire status in database"""
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
    else:
        db_status = "FAILED"  # Default to FAILED
    
    # Extract ticket and price
    ticket = m.get("ticket") or m.get("order") or 0
    price = m.get("price") or m.get("execution_price") or 0
    
    # Update database
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute(
            "UPDATE fires SET status=?, ticket=?, price=? WHERE fire_id=?",
            (db_status, ticket, price, fire_id)
        )
        rows_affected = cur.rowcount
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
        else:
            LOG.info("non-confirm msg type=%s", m.get("type"))

if __name__ == "__main__":
    main()