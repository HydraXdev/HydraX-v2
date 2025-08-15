import os, time, json, zmq, redis
REDIS_HOST=os.environ.get("REDIS_HOST","127.0.0.1")
REDIS_PORT=int(os.environ.get("REDIS_PORT","6379"))
ZMQ_ADDR=os.environ.get("ZMQ_ADDR","tcp://127.0.0.1:5557")
STREAM=os.environ.get("STREAM","signals")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
ctx=zmq.Context.instance()
sub=ctx.socket(zmq.SUB)
sub.connect(ZMQ_ADDR)
sub.setsockopt_string(zmq.SUBSCRIBE,"")
print(f"[bridge] Starting ZMQ→Redis: {ZMQ_ADDR} → stream '{STREAM}'")
count=0
last_log=time.time()
while True:
    try:
        m=sub.recv_string()
        # Handle "ELITE_GUARD_SIGNAL {json}" format
        if m.startswith("ELITE_GUARD_SIGNAL "):
            json_part = m[len("ELITE_GUARD_SIGNAL "):]
            payload = json.loads(json_part)
        else:
            # Try direct JSON parse
            try:
                payload=json.loads(m)
            except:
                try: payload=json.loads(m.strip())
                except: payload={"raw":m}
        payload.setdefault("ingest_ts", int(time.time()))
        r.xadd(STREAM, {"event": json.dumps(payload)}, maxlen=1000)
        count+=1
        now=time.time()
        if now-last_log>10:
            print(f"[bridge] Processed {count} signals"); last_log=now
    except Exception as e:
        print("bridge error:", e); time.sleep(0.2)
