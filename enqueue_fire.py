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
    # For now, use a default target_uuid - should be looked up from user registry
    target_uuid = f"USER_{user_id}"  # This should be the actual EA UUID for the user
    
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