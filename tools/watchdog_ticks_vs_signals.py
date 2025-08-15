import zmq, time, json, redis, os, sys
TICK_ADDR="tcp://127.0.0.1:5560"
REDIS_HOST=os.environ.get("REDIS_HOST","127.0.0.1")
REDIS_PORT=int(os.environ.get("REDIS_PORT","6379"))
WINDOW=int(os.environ.get("WDS_WINDOW","60"))      # seconds
MISS_FOR=int(os.environ.get("WDS_MISS_FOR","180")) # seconds

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
ctx=zmq.Context.instance()
sub=ctx.socket(zmq.SUB); sub.connect(TICK_ADDR); sub.setsockopt_string(zmq.SUBSCRIBE,""); sub.RCVTIMEO=500

last_signal_ts = int(time.time())
last_ticks_ts   = 0
last_id = '0'
t0=time.time()
while True:
    now=time.time()
    # Consume some ticks non-blocking within the window
    got_tick=False
    end=now + 0.5
    while time.time()<end:
        try:
            sub.recv(flags=zmq.NOBLOCK)
            got_tick=True
        except zmq.error.Again:
            break
    if got_tick:
        last_ticks_ts = int(now)

    # Any new signals since last check?
    try:
        msgs = r.xread({"signals": last_id}, count=200, block=50)
        for _, entries in msgs:
            for msg_id, _ in entries:
                last_id = msg_id
                last_signal_ts = int(now)
    except:
        pass  # Redis stream might not exist yet

    # Alert if ticks flowing but no signals for MISS_FOR seconds
    if (now - last_ticks_ts) < WINDOW and (now - last_signal_ts) > MISS_FOR:
        import subprocess; msg=f"[ALERT] Ticks flowing but no signals for {int(now-last_signal_ts)}s — investigate EG config/filters.";
        print(msg, flush=True);
        subprocess.Popen(["/root/HydraX-v2/tools/notifier.sh", msg])
    time.sleep(5)