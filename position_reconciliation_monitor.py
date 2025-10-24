#!/usr/bin/env python3
"""
Position Reconciliation Monitor
Compares EA reported position count vs database count
Alerts on discrepancies and optionally auto-corrects
"""
import sqlite3
import zmq
import json
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = "/root/HydraX-v2/bitten.db"
RECONCILE_INTERVAL = 300  # 5 minutes
MISMATCH_THRESHOLD = 0    # Alert if ANY difference (changed from 2 on Oct 21, 2025)

def get_database_position_count(user_id: str) -> int:
    """Get position count from database"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM live_positions 
            WHERE user_id = ? AND status = 'OPEN'
        """, (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return -1

def get_ea_position_count(timeout_ms=5000) -> tuple:
    """Get position count from EA heartbeat
    Returns: (uuid, user_id, position_count, balance, equity)
    """
    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect("tcp://127.0.0.1:5570")
    sub.setsockopt_string(zmq.SUBSCRIBE, "")
    sub.setsockopt(zmq.RCVTIMEO, timeout_ms)
    
    try:
        start = time.time()
        while time.time() - start < timeout_ms / 1000:
            msg = sub.recv_string()
            data = json.loads(msg)
            if data.get("type") == "heartbeat":
                # Get user_id from ea_instances
                conn = sqlite3.connect(DB_PATH, timeout=5)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id FROM ea_instances 
                    WHERE target_uuid = ?
                """, (data.get("uuid"),))
                result = cursor.fetchone()
                conn.close()
                
                user_id = result[0] if result else None
                return (
                    data.get("uuid"),
                    user_id,
                    data.get("positions", 0),
                    data.get("balance", 0),
                    data.get("equity", 0)
                )
    except zmq.Again:
        logger.error("Timeout waiting for EA heartbeat")
        return (None, None, -1, 0, 0)
    except Exception as e:
        logger.error(f"Error reading heartbeat: {e}")
        return (None, None, -1, 0, 0)
    finally:
        sub.close()
        ctx.term()

def auto_reconcile_positions(uuid: str, user_id: str, ea_count: int, db_count: int):
    """Auto-close stale database positions when EA count is lower"""
    if db_count <= ea_count:
        return 0  # No reconciliation needed

    try:
        # Close oldest positions that EA no longer reports
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()

        # Get positions that haven't received updates in last 120 seconds
        # (EA sends position_update every 1s, so 120s = definitely closed)
        cursor.execute("""
            SELECT fire_id, symbol, direction, last_update
            FROM live_positions
            WHERE user_id = ? AND status = 'OPEN'
            AND (strftime('%s', 'now') - last_update) > 120
            ORDER BY last_update ASC
        """, (user_id,))

        stale_positions = cursor.fetchall()
        positions_to_close = db_count - ea_count

        if len(stale_positions) >= positions_to_close:
            # Close the stalest positions
            for fire_id, symbol, direction, last_update in stale_positions[:positions_to_close]:
                age = int(time.time()) - last_update
                cursor.execute("""
                    UPDATE live_positions
                    SET status = 'CLOSED', last_update = ?
                    WHERE fire_id = ?
                """, (int(time.time()), fire_id))
                logger.info(f"✅ AUTO-CLOSED stale position: {fire_id} | {symbol} {direction} | Stale for {age}s")

            conn.commit()
            logger.info(f"🔧 AUTO-RECONCILIATION: Closed {positions_to_close} stale positions for user {user_id}")
            conn.close()
            return positions_to_close
        else:
            conn.close()
            logger.warning(f"⚠️ Cannot reconcile: Need to close {positions_to_close} but only {len(stale_positions)} are stale (>120s)")
            return 0

    except Exception as e:
        logger.error(f"Auto-reconciliation failed: {e}")
        return 0

def log_discrepancy(uuid: str, user_id: str, ea_count: int, db_count: int, balance: float, equity: float):
    """Log position count mismatch and trigger auto-reconciliation"""
    diff = abs(ea_count - db_count)

    if diff > MISMATCH_THRESHOLD:
        logger.warning(
            f"🚨 POSITION MISMATCH | UUID: {uuid} | User: {user_id} | "
            f"EA reports: {ea_count} positions | Database shows: {db_count} positions | "
            f"Difference: {diff} | Balance: ${balance:.2f} | Equity: ${equity:.2f}"
        )

        # Log to dedicated mismatch file
        with open("/root/HydraX-v2/position_mismatch.log", "a") as f:
            f.write(
                f"{datetime.now().isoformat()} | UUID: {uuid} | User: {user_id} | "
                f"EA: {ea_count} | DB: {db_count} | Diff: {diff} | "
                f"Bal: ${balance:.2f} | Eq: ${equity:.2f}\n"
            )

        # AUTO-RECONCILE if database has more positions than EA
        if db_count > ea_count:
            closed_count = auto_reconcile_positions(uuid, user_id, ea_count, db_count)
            if closed_count > 0:
                logger.info(f"✅ Auto-reconciliation completed: Closed {closed_count} stale positions")

        return True
    else:
        logger.info(
            f"✅ Position count OK | UUID: {uuid} | User: {user_id} | "
            f"EA: {ea_count} | DB: {db_count} | Bal: ${balance:.2f} | Eq: ${equity:.2f}"
        )
        return False

def get_stale_positions(user_id: str) -> list:
    """Get list of positions that might be stale (no updates in 5 min)"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fire_id, symbol, direction, 
                   (strftime('%s', 'now') - last_update) as age_seconds
            FROM live_positions 
            WHERE user_id = ? AND status = 'OPEN'
            AND (strftime('%s', 'now') - last_update) > 300
            ORDER BY age_seconds DESC
        """, (user_id,))
        stale = cursor.fetchall()
        conn.close()
        return stale
    except Exception as e:
        logger.error(f"Error checking stale positions: {e}")
        return []

def main():
    logger.info("🔍 Position Reconciliation Monitor started")
    logger.info(f"📊 Check interval: {RECONCILE_INTERVAL}s | Alert threshold: >{MISMATCH_THRESHOLD} positions")
    
    while True:
        try:
            # Get EA heartbeat data
            uuid, user_id, ea_count, balance, equity = get_ea_position_count()
            
            if uuid and user_id and ea_count >= 0:
                # Get database count
                db_count = get_database_position_count(user_id)
                
                if db_count >= 0:
                    # Check for mismatch
                    has_mismatch = log_discrepancy(uuid, user_id, ea_count, db_count, balance, equity)
                    
                    # If mismatch, check for stale positions
                    if has_mismatch:
                        stale = get_stale_positions(user_id)
                        if stale:
                            logger.warning(f"⏰ Found {len(stale)} stale positions (no update >5min):")
                            for fire_id, symbol, direction, age in stale[:5]:  # Show top 5
                                logger.warning(f"   - {fire_id} | {symbol} {direction} | Stale for {age}s")
            else:
                logger.error("❌ Could not retrieve EA heartbeat data")
            
            # Wait for next check
            time.sleep(RECONCILE_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(60)  # Wait 1 min on error

if __name__ == "__main__":
    main()
