#!/usr/bin/env python3
from pathlib import Path

p = Path("/root/HydraX-v2/tools/fire_redis_bridge.py")
s = p.read_text()

if "dry_run" not in s or "IGNORE dry_run" not in s:
    # Add comment after function definition
    s = s.replace(
        "def handle(stream, msg_id, fields):",
        "def handle(stream, msg_id, fields):\n    # IGNORE dry_run payloads for absolute safety"
    )
    
    # Inject skip logic after data parsing
    s = s.replace(
        "if not data:\n        data = fields",
        "if not data:\n        data = fields\n    \n    # Safety: never forward dry_run to IPC\n    if str(data.get('dry_run', '')).lower() in ('1', 'true', 'yes'):\n        print(f'[FIRE_BRIDGE] Ignoring dry_run payload: {data.get(\"fire_id\", \"\")}')\n        r.xack(stream, GROUP, msg_id)\n        return"
    )
    
    p.write_text(s)
    print("[OK] Patched bridge to ignore dry_run entries.")
else:
    print("[INFO] Bridge already ignores dry_run.")