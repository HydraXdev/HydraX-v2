# /root/HydraX-v2/sidecars/healthz_8890.py
import json
import math
import threading
import time

import zmq
from flask import Flask, jsonify

PUB_ENDPOINT = "tcp://127.0.0.1:5562"
app = Flask(__name__)

last_tick_ts = {}  # symbol -> last ts ms
tick_count_60 = {}  # symbol -> count in last ~60s
window_start = time.time()


def sub_loop():
    ctx = zmq.Context.instance()
    sub = ctx.socket(zmq.SUB)
    sub.connect(PUB_ENDPOINT)
    sub.setsockopt(zmq.SUBSCRIBE, b"")  # all
    while True:
        try:
            msg = sub.recv()  # adapter publishes one-JSON-per-message
            now = time.time()
            try:
                obj = json.loads(msg.decode("utf-8", "ignore"))
            except Exception:
                continue
            # Only count ticks
            if "symbol" in obj and "bid" in obj and "ask" in obj:
                sym = obj["symbol"]
                ts = int(obj.get("ts_epoch_ms", now * 1000))
                last_tick_ts[sym] = ts
                tick_count_60[sym] = tick_count_60.get(sym, 0) + 1

            # rotate ~60s window with decay
            if now - window_start > 60:
                for k in list(tick_count_60.keys()):
                    tick_count_60[k] = max(0, int(tick_count_60[k] * 0.5))
                globals()["window_start"] = now
        except Exception:
            time.sleep(0.1)


@app.route("/healthz")
def healthz():
    now_ms = int(time.time() * 1000)
    ages = {s: now_ms - ts for s, ts in last_tick_ts.items()}
    # per-symbol ticks/sec approximated from last minute
    rates = {s: tick_count_60.get(s, 0) / 60.0 for s in last_tick_ts.keys()}
    active = [s for s, a in ages.items() if a < 5000]
    ok_rates = all(r >= 0.5 for s, r in rates.items() if s in active) and len(active) >= 4
    ok_age = (len(active) >= 4) and (max(ages[s] for s in active) < 5000)
    status = 200 if (ok_rates and ok_age) else 503
    return (
        jsonify(
            {
                "status": "ok" if status == 200 else "degraded",
                "active_symbols": len(active),
                "symbols_observed": sorted(list(last_tick_ts.keys()))[:25],
                "tick_rate_per_symbol": rates,
                "last_event_age_ms": (max(ages.values()) if ages else None),
                "uptime_seconds": int(time.time() - window_start),
                "pub_endpoint": PUB_ENDPOINT,
            }
        ),
        status,
    )


def main():
    threading.Thread(target=sub_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8890)


if __name__ == "__main__":
    main()
