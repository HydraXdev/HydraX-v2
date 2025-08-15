#!/usr/bin/env python3
"""
Send fire command directly through IPC queue RIGHT NOW
"""
import zmq
import json
import time

ctx = zmq.Context()
push = ctx.socket(zmq.PUSH)
push.connect("ipc:///tmp/bitten_cmdqueue")

# Send fire command
fire_cmd = {
    "type": "fire",
    "fire_id": f"DIRECT_{int(time.time())}",
    "target_uuid": "COMMANDER_DEV_001",
    "symbol": "EURUSD",
    "direction": "BUY",
    "entry": 1.0850,
    "sl": 1.0800,
    "tp": 1.0900,
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