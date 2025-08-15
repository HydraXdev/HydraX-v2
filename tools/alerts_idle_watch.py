#!/usr/bin/env python3
import os, time, redis, sys
R = redis.Redis(host=os.environ.get("REDIS_HOST","127.0.0.1"),
                port=int(os.environ.get("REDIS_PORT","6379")), decode_responses=True)
def xlen(key):
    try: return int(R.xlen(key))
    except: return -1
last_alert_len = xlen("alerts")
last_sig_len = xlen("signals")
t0 = time.time()
while True:
    time.sleep(60)
    sig_len = xlen("signals")
    al_len  = xlen("alerts")
    # Heuristic: if signals grew but alerts didn't for >=10 minutes, warn.
    if sig_len > last_sig_len and al_len == last_alert_len:
        if time.time() - t0 >= 600:
            print(f"[WATCH:NO-ALERTS] signals grew ({last_sig_len}->{sig_len}) but alerts stuck at {al_len} for >=10m")
    else:
        t0 = time.time()
    last_sig_len, last_alert_len = sig_len, al_len