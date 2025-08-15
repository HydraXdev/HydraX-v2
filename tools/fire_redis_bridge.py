#!/usr/bin/env python3
import os, time, json, redis, zmq, sqlite3, signal, sys

REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
GROUP = os.environ.get("FIRE_GROUP", "router")
CONSUMER = os.environ.get("FIRE_CONSUMER", "router-1")
DB_PATH = os.environ.get("BITTEN_DB", "/root/HydraX-v2/bitten.db")
IPC_ADDR = os.environ.get("CMDQ", "ipc:///tmp/bitten_cmdqueue")
ENQUEUE = os.environ.get("FIRE_BRIDGE_ENQUEUE", "0") == "1"
STREAM_PREFIX = "fire."

ctx = zmq.Context.instance()
push = None
if ENQUEUE:
    push = ctx.socket(zmq.PUSH)
    push.connect(IPC_ADDR)
    print(f"[FIRE_BRIDGE] Connected to IPC: {IPC_ADDR}")

def db_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = lambda cur, row: {d[0]: row[i] for i, d in enumerate(cur.description)}
    return c

def already_enqueued(conn, idem):
    if not idem:
        return False
    try:
        r = conn.execute("SELECT 1 FROM fires WHERE idem=? LIMIT 1", (idem,)).fetchone()
        return bool(r)
    except Exception:
        return False

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Discover existing per-EA streams
def list_streams():
    # No native pattern scan for streams; we can track known keys by scanning
    keys = []
    cur = 0
    while True:
        cur, batch = r.scan(cur, match=f"{STREAM_PREFIX}*", count=200)
        keys.extend([k for k in batch])
        if cur == 0:
            break
    return list(sorted(set(keys)))

def ensure_group(stream):
    try:
        r.xgroup_create(stream, GROUP, id="0-0", mkstream=True)
        print(f"[FIRE_BRIDGE] Created group {GROUP} for stream {stream}")
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            print(f"[FIRE_BRIDGE] Group create error for {stream}: {e}")

streams = list_streams()
for s in streams:
    ensure_group(s)

print(f"[FIRE_BRIDGE] Starting - Watching streams: {streams}")
print(f"[FIRE_BRIDGE] Mode: {'ENQUEUE to IPC' if ENQUEUE else 'LOG-ONLY (no enqueue)'}")
print(f"[FIRE_BRIDGE] Group: {GROUP}, Consumer: {CONSUMER}")

last_scan = time.time()
conn = db_conn()

def handle(stream, msg_id, fields):
    # IGNORE dry_run payloads for absolute safety
    # fields may contain event JSON or direct fields
    data = None
    if "event" in fields:
        try:
            data = json.loads(fields["event"])
        except:
            data = None
    if not data:
        data = fields
    
    # Safety: never forward dry_run to IPC
    if str(data.get('dry_run', '')).lower() in ('1', 'true', 'yes'):
        print(f'[FIRE_BRIDGE] Ignoring dry_run payload: {data.get("fire_id", "")}')
        r.xack(stream, GROUP, msg_id)
        return
    
    idem = data.get("idem", "")
    fire_id = data.get("fire_id", "")
    target_uuid = data.get("target_uuid", "")
    symbol = data.get("symbol", "")
    
    print(f"[FIRE_BRIDGE] Processing: fire_id={fire_id}, target={target_uuid}, symbol={symbol}, idem={idem}")
    
    if ENQUEUE and already_enqueued(conn, idem):
        # Ack and drop duplicate
        r.xack(stream, GROUP, msg_id)
        print(f"[FIRE_BRIDGE] Duplicate detected (idem={idem}), skipping")
        return
    
    if ENQUEUE:
        try:
            push.send_json(data)
            print(f"[FIRE_BRIDGE] Enqueued to IPC: {fire_id}")
        except Exception as e:
            print(f"[FIRE_BRIDGE] IPC enqueue error: {e}")
            return
    else:
        print(f"[FIRE_BRIDGE] LOG-ONLY mode, would enqueue: {fire_id}")
    
    # Ack after success or log-only
    r.xack(stream, GROUP, msg_id)

try:
    print("[FIRE_BRIDGE] Listening for fire commands...")
    while True:
        now = time.time()
        # Periodically rescan for new per-EA streams
        if now - last_scan > 30:
            new_streams = list_streams()
            for s in new_streams:
                if s not in streams:
                    ensure_group(s)
                    print(f"[FIRE_BRIDGE] Discovered new stream: {s}")
            streams = new_streams
            last_scan = now
        
        # Read from all known streams
        # Build dict {stream: '>'}
        watch = {s: ">" for s in streams}
        if not watch:
            time.sleep(1)
            continue
        
        try:
            msgs = r.xreadgroup(GROUP, CONSUMER, streams=watch, count=128, block=1500)
        except Exception as e:
            if "NOGROUP" in str(e):
                # Re-create groups
                for s in streams:
                    ensure_group(s)
                continue
            raise
        
        if not msgs:
            continue
        
        for stream, entries in msgs:
            for msg_id, fields in entries:
                handle(stream, msg_id, fields)
                
except KeyboardInterrupt:
    print("\n[FIRE_BRIDGE] Shutting down...")
except Exception as e:
    print(f"[FIRE_BRIDGE] Fatal error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        conn.close()
    except:
        pass
    print("[FIRE_BRIDGE] Exited")