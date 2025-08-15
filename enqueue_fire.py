#!/usr/bin/env python3
"""
Enqueue fire commands to IPC queue for command_router
"""
import zmq
import os
import json

QUEUE_ADDR = os.getenv("BITTEN_QUEUE_ADDR", "ipc:///tmp/bitten_cmdqueue")
_ctx = None
_push = None

def enqueue_fire(cmd: dict):
    """Send fire command to IPC queue"""
    global _ctx, _push
    if _ctx is None:
        _ctx = zmq.Context.instance()
        _push = _ctx.socket(zmq.PUSH)
        _push.connect(QUEUE_ADDR)
        _push.setsockopt(zmq.LINGER, 0)
    _push.send_json(cmd)
    return True

def create_fire_command(mission_id: str, user_id: str, symbol: str, direction: str, 
                       entry: float, sl: float, tp: float, lot: float = 0.01) -> dict:
    """Create fire command for queue"""
    # Look up the correct target_uuid from the database for this user
    import sqlite3
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        cursor.execute("SELECT target_uuid FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        target_uuid = result[0] if result else "COMMANDER_DEV_001"  # Fallback to default
        conn.close()
    except Exception:
        target_uuid = "COMMANDER_DEV_001"  # Fallback if DB lookup fails
    
    # Round lot size to 2 decimal places for MT5 compatibility
    lot = round(lot, 2)
    
    return {
        "type": "fire",
        "fire_id": mission_id,
        "target_uuid": target_uuid,
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "lot": lot,
        "user_id": user_id
    }