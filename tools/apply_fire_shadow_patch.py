#!/usr/bin/env python3
import os, re, sys, json, textwrap

fp = os.environ.get("WEBAPP_FILE", "/root/HydraX-v2/webapp_server_optimized.py")
src = open(fp, 'r', encoding='utf-8').read()

# Helper block to add Redis XADD
helper = '''
# ## FIRE_SHADOW_PATCH_START
def _bitten_fire_xadd(redis_host, redis_port, stream, payload):
    try:
        import redis, json
        r = redis.Redis(host=redis_host, port=int(redis_port), decode_responses=True)
        # store as event JSON; keep key fields also for XPENDING/XCLAIM tooling
        fields = {
            "event": json.dumps(payload),
            "fire_id": payload.get("fire_id",""),
            "idem": payload.get("idem",""),
            "user_id": str(payload.get("user_id","")),
            "target_uuid": payload.get("target_uuid",""),
            "symbol": payload.get("symbol",""),
        }
        r.xadd(stream, fields, maxlen=0)
        return True
    except Exception as e:
        try: print("fire_xadd error:", e, flush=True)
        except: pass
        return False
# ## FIRE_SHADOW_PATCH_END
'''.lstrip()

if "## FIRE_SHADOW_PATCH_START" not in src:
    # Insert helper after import section
    m = re.search(r"(?:^from\s+.+?import.+?$|^import\s+.+?$)\s*(?:\r?\n)+", src, flags=re.M)
    ins = m.end() if m else 0
    src = src[:ins] + helper + src[ins:]
    print("Added fire shadow helper function")

# Inject shadow publish inside /api/fire handler AFTER we assembled _req and before any enqueue
# Look for the END SERVER-SIDE FIRE MAPPING marker
if "# --- END SERVER-SIDE FIRE MAPPING ---" in src and "_bitten_fire_xadd" not in "# --- FIRE SHADOW PUBLISH":
    # Insert right after the mapping block ends (before enqueue)
    shadow_block = '''
    # --- FIRE SHADOW PUBLISH (Redis Streams) ---
    try:
        import os
        if os.environ.get("FIRE_TO_REDIS","1") == "1":
            stream = f"fire.{_req['target_uuid']}"
            _bitten_fire_xadd(os.environ.get("REDIS_HOST","127.0.0.1"), os.environ.get("REDIS_PORT","6379"), stream, _req)
    except Exception as _e:
        try: print("fire shadow publish err:", _e, flush=True)
        except: pass
    # --- END FIRE SHADOW PUBLISH ---
'''
    src = re.sub(
        r"(# --- END SERVER-SIDE FIRE MAPPING ---\s*\n)",
        r"\1" + shadow_block,
        src,
        count=1
    )
    print("Added fire shadow publish block")

# Add a guard to optionally skip IPC enqueue if FIRE_SHADOW_ONLY=1 (for future cutover)
# Look for zmq send in fire_mission function
if "s.send_json(data)" in src:
    src = re.sub(
        r"(\n\s*)(s\.send_json\(data\))",
        r"""\1# Optional cutover: skip IPC if shadow-only is enabled
\1import os as _os_cut
\1if _os_cut.environ.get("FIRE_SHADOW_ONLY","0") != "1":
\1    \2
\1# else: Redis-only; the bridge will forward to IPC
""",
        src,
        count=1
    )
    print("Added shadow-only guard for IPC enqueue")
elif "s.send_json(_req)" in src:
    src = re.sub(
        r"(\n\s*)(s\.send_json\(_req\))",
        r"""\1# Optional cutover: skip IPC if shadow-only is enabled
\1import os as _os_cut
\1if _os_cut.environ.get("FIRE_SHADOW_ONLY","0") != "1":
\1    \2
\1# else: Redis-only; the bridge will forward to IPC
""",
        src,
        count=1
    )
    print("Added shadow-only guard for IPC enqueue")

open(fp, 'w', encoding='utf-8').write(src)
print("[OK] /api/fire patched for Redis SHADOW publish with optional cutover guard.")