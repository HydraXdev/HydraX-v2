#!/usr/bin/env python3
import re, sqlite3, os, sys, json, time

root = os.environ.get("BITTEN_ROOT", "/root/HydraX-v2")
dbp = os.environ.get("BITTEN_DB", f"{root}/bitten.db")
fp = os.environ.get("WEBAPP_FILE", "/root/HydraX-v2/webapp_server_optimized.py")

if not fp or not os.path.isfile(fp):
    print("ERROR: WEBAPP_FILE missing")
    sys.exit(1)

src = open(fp, 'r', encoding='utf-8').read()
if "## FIRE_MAPPING_PATCH_START" in src:
    print("[INFO] Fire mapping patch already present; skipping.")
    sys.exit(0)

# Minimal helper block: will be inserted near top-level imports
helper = '''
# ## FIRE_MAPPING_PATCH_START
def _bitten_resolve_user_and_check_fresh(db_path, target_uuid, freshness_sec=180):
    import sqlite3, time
    conn=sqlite3.connect(db_path)
    conn.row_factory=lambda c,r:{d[0]:r[i] for i,d in enumerate(c.description)}
    try:
        row=conn.execute("SELECT user_id, last_seen FROM ea_instances WHERE target_uuid=?",(target_uuid,)).fetchone()
        if not row or not row.get("user_id"):
            return (None, "mapping_missing")
        age = int(time.time()) - int(row.get("last_seen") or 0)
        if age>freshness_sec:
            return (row["user_id"], f"stale:{age}")
        return (row["user_id"], "fresh")
    finally:
        conn.close()
# ## FIRE_MAPPING_PATCH_END
'''.lstrip()

# Find a reasonable insertion point (after first imports)
m = re.search(r"(^import .+?$|^from .+? import .+?$)(?:\n|\r\n)+", src, flags=re.M|re.S)
if m:
    ins_idx = m.end()
    src = src[:ins_idx] + helper + src[ins_idx:]
else:
    src = helper + src

# Find the fire_mission function (handles /api/fire)
fire_mission_match = re.search(r"def fire_mission\(\):\s*\n", src)
if fire_mission_match:
    print("Found fire_mission function")
    # Insert after the function definition
    insert_pos = fire_mission_match.end()
    
    # The patch to insert
    insertion = '''    # --- SERVER-SIDE FIRE MAPPING (NO CLIENT user_id REQUIRED) ---
    try:
        # Accept JSON body from request context
        _req = request.get_json() if request.method == 'POST' else None
    except Exception:
        _req = None
    if _req is None:
        _req = {}
    
    # Derive user_id from ea_instances by target_uuid if missing/empty
    tgt = _req.get("target_uuid")
    if not tgt:
        return jsonify({"ok":False,"error":"target_uuid required"}), 400
    
    uid = _req.get("user_id")
    if not uid:
        from pathlib import Path
        DB_PATH = os.environ.get("BITTEN_DB", str(Path(__file__).resolve().parent / "bitten.db"))
        uid, freshness = _bitten_resolve_user_and_check_fresh(DB_PATH, tgt, freshness_sec=180)
        if not uid:
            return jsonify({"ok":False,"error":"mapping_not_found","target_uuid":tgt}), 400
        _req["user_id"] = uid
        if isinstance(freshness,str) and freshness.startswith("stale"):
            return jsonify({"ok":False,"error":"ea_stale","details":freshness,"target_uuid":tgt}), 409
    
    # Add idempotency key if missing
    if not _req.get("idem"):
        import time
        _req["idem"] = f"{_req.get('fire_id','') or 'fire'}:{_req['user_id']}:{_req['symbol']}:{int(time.time())}"
    
    # Optional: dry_run support to allow health checks without trading
    if _req.get("dry_run") is True:
        return jsonify({"ok":True,"dry_run":True,"user_id":_req["user_id"],"target_uuid":tgt,"idem":_req["idem"]}), 200
    
    # Use _req for the zmq send
    data = _req
    # --- END SERVER-SIDE FIRE MAPPING ---
    
'''
    src = src[:insert_pos] + insertion + src[insert_pos:]
    open(fp, 'w', encoding='utf-8').write(src)
    print("[OK] /api/fire patched with server-side mapping and optional dry_run.")
else:
    print("ERROR: Could not find fire_mission function")
    sys.exit(2)