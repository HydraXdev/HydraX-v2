#!/usr/bin/env python3
import json
import os
import sys
import time
import uuid

import zmq

if len(sys.argv) < 4:
    print("usage: fire_enqueue_direct.py <uuid> <symbol> <side> [lot]")
    sys.exit(2)
uid, sym, side = sys.argv[1], sys.argv[2], sys.argv[3]
lot = float(sys.argv[4]) if len(sys.argv) > 4 else 0.01
fid = f"CLI-{uuid.uuid4().hex[:6]}-{int(time.time())}"
payload = {"type": "fire", "target_uuid": uid, "fire_id": fid, "symbol": sym, "direction": side, "lot": lot}
ctx = zmq.Context()
q = ctx.socket(zmq.PUSH)
q.connect("ipc:///tmp/bitten_cmdqueue")
q.send_json(payload)
print(json.dumps({"queued": True, "fire_id": fid, "payload": payload}, indent=2))
