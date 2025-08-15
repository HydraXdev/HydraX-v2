import os, time, json, requests, redis
REDIS_HOST=os.environ.get("REDIS_HOST","127.0.0.1")
REDIS_PORT=int(os.environ.get("REDIS_PORT","6379"))
STREAM=os.environ.get("STREAM","signals")
GROUP=os.environ.get("GROUP","relay")
CONSUMER=os.environ.get("CONSUMER","relay-1")
WEBAPP=os.environ.get("WEBAPP_BASE","http://127.0.0.1:8888")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
try:
    r.xgroup_create(STREAM, GROUP, id="0-0", mkstream=True)
except Exception as e:
    if "BUSYGROUP" not in str(e): print("group create:", e)
def post_signal(payload):
    # SAFETY: drop synthetic
    if payload.get('signal_type')=='DIAG_ONLY' or payload.get('pattern_type','').startswith('DIAG_'):
        return True
    # Send complete payload instead of filtered subset
    data = payload.copy()
    if not data.get("signal_id") and "event" in payload:
        try:
            ev=json.loads(payload["event"])
            for k in data.keys():
                if k in ev: data[k]=ev[k]
        except: pass
    if not data.get("signal_id"): return True
    try:
        resp=requests.post(f"{WEBAPP}/api/signals", json=data, timeout=3)
        return resp.ok
    except Exception as e:
        print("POST /api/signals error:", e)
        return False
while True:
    try:
        msgs = r.xreadgroup(GROUP, CONSUMER, streams={STREAM: ">"}, count=64, block=1500)
        if not msgs: continue
        for stream, entries in msgs:
            for msg_id, fields in entries:
                ok = post_signal(fields)
                if ok: r.xack(STREAM, GROUP, msg_id)
    except Exception as e:
        print("consumer error:", e); time.sleep(0.2)
