#!/usr/bin/env python3
"""
Ask-anchored MF-3 success test with ultra-wide distances
"""
import json
import time

import zmq


def send_ask_anchored_fire():
    """Send ask-anchored BUY fire with ultra-wide SL/TP"""

    # Live tick data
    symbol = "XAUUSD"
    ask = 2651.00
    point = 0.01
    digits = 2

    # Ultra-wide distances
    sl_pts = 4000  # $40 below ask
    tp_pts = 6000  # $60 above ask

    # Calculate SL/TP anchored to ASK
    sl = round(ask - sl_pts * point, digits)  # 2611.00
    tp = round(ask + tp_pts * point, digits)  # 2711.00

    # Sanity check
    assert sl < ask < tp, f"Bad bounds: sl={sl} ask={ask} tp={tp}"

    fire_id = f"MF3-{int(time.time())}"

    # Ask-anchored BUY fire
    fire_command = {
        "type": "fire",
        "fire_id": fire_id,
        "target_uuid": "COMMANDER_DEV_001",
        "symbol": symbol,
        "direction": "BUY",
        "entry": 0,  # Market order
        "sl": sl,
        "tp": tp,
        "lot": 0.01,
        "snapshot_tf": "M1",
    }

    print(f"🎯 ASK-ANCHORED MF-3:")
    print(f"   Fire ID: {fire_id}")
    print(f"   Ask: {ask}")
    print(f"   SL: {sl} ({sl_pts} pts below)")
    print(f"   TP: {tp} ({tp_pts} pts above)")
    print(f"   Bounds: {sl} < {ask} < {tp} ✓")

    # Send via IPC
    context = zmq.Context()
    sender = context.socket(zmq.PUSH)
    sender.connect("ipc:///tmp/bitten_cmdqueue")

    sender.send_json(fire_command)
    sender.close()
    context.term()

    return fire_id, ask, point, digits, sl, tp, sl_pts, tp_pts


if __name__ == "__main__":
    fire_id, ask, point, digits, sl, tp, sl_pts, tp_pts = send_ask_anchored_fire()
    print(f"\n✅ ASK-ANCHORED FIRE SENT: {fire_id}")
    print(f"   ask={ask}, point={point}, digits={digits}")
    print(f"   sl={sl}, tp={tp}, sl_pts={sl_pts}, tp_pts={tp_pts}")
