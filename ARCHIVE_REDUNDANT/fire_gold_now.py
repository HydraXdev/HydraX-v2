#!/usr/bin/env python3
"""
Send XAUUSD fire command - Gold trades 23 hours
"""
import zmq
import json
import time

ctx = zmq.Context()
push = ctx.socket(zmq.PUSH)
push.connect("ipc:///tmp/bitten_cmdqueue")

# Send fire command for GOLD
fire_cmd = {
    "type": "fire",
    "fire_id": f"GOLD_{int(time.time())}",
    "target_uuid": "COMMANDER_DEV_001",
    "symbol": "XAUUSD",
    "direction": "BUY",
    "entry": 2650.00,
    "sl": 2640.00,
    "tp": 2660.00,
    "lot": 0.01
}

push.send_json(fire_cmd)
print(f"🔥 SENT: {fire_cmd['fire_id']}")
print(f"   {fire_cmd['symbol']} {fire_cmd['direction']}")
print(f"   Entry: {fire_cmd['entry']}")
print(f"   SL: {fire_cmd['sl']}")  
print(f"   TP: {fire_cmd['tp']}")
print(f"   Lot: {fire_cmd['lot']}")

push.close()
ctx.term()