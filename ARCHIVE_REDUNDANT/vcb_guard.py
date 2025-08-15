#!/usr/bin/env python3
import os, time, json, math, statistics, collections, uuid
import zmq
#
# Volatility Compression Breakout (VCB)
# - Build rolling M1 "pseudo-candles" from ticks (simple bucket by time)
# - Detect compression (tight range vs ATR) then breakout + optional retest
# - Compute SL/TP to satisfy RR >= 1.4 (hard gate)
#
EG_VCB_ENABLED = os.getenv("EG_VCB_ENABLED","1") == "1"
EG_VCB_MODE    = os.getenv("EG_VCB_MODE","live")  # live | shadow (shadow still publishes but can include suppress_fire)
COMP_RATIO     = float(os.getenv("EG_VCB_COMP_RATIO","0.9"))
MIN_COMP_BARS  = int(os.getenv("EG_VCB_MIN_COMP_BARS","5"))
CLOSE_PCT      = float(os.getenv("EG_VCB_CLOSE_PCT","25"))/100.0
RETEST_BARS    = int(os.getenv("EG_VCB_RETEST_BARS","3"))
RETEST_PIPS    = float(os.getenv("EG_VCB_RETEST_PIPS","2"))
SL_BUF_PIPS    = float(os.getenv("EG_VCB_SL_BUFFER_PIPS","1"))
RR_TARGET      = float(os.getenv("EG_VCB_RR_TARGET","1.6"))
MIN_RR         = max(1.4, float(os.getenv("EG_MIN_RR","1.4")))  # NEVER below 1.4
SESSION_ENF    = os.getenv("EG_SESSION_ENFORCE","0") == "1"      # leave default open for now
COOLDOWN_SEC   = int(os.getenv("EG_GLOBAL_COOLDOWN_SEC","5"))
DUP_SUP_SEC    = int(os.getenv("EG_DUP_SUPPRESS_SEC","10"))

# Basic symbol config (pip sizes). Adjust as needed.
# FOREX ONLY - No crypto signals
PIP = {
  "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDJPY": 0.01, "EURJPY": 0.01, "GBPJPY": 0.01,
  "XAUUSD": 0.1, "XAGUSD": 0.01, "USDCAD": 0.0001,
  "USDCHF": 0.0001, "AUDUSD": 0.0001, "NZDUSD": 0.0001, "USDSEK": 0.0001
}

def pip_size(sym): return PIP.get(sym, 0.0001)

def calc_rr(direction, entry, sl, tp):
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    return (reward / risk) if risk>0 else 0

def now_ts(): return int(time.time())

# Build pseudo candles by minute (UTC epoch minute)
def minute_bucket(ts): return int(ts // 60)

ctx = zmq.Context.instance()
sub = ctx.socket(zmq.SUB); sub.connect("tcp://127.0.0.1:5560"); sub.setsockopt_string(zmq.SUBSCRIBE,""); sub.RCVTIMEO=1000
pub = ctx.socket(zmq.PUB); pub.bind("tcp://127.0.0.1:5557") if os.getenv("VCB_STANDALONE_BIND","0")=="1" else pub.connect("tcp://127.0.0.1:5557")

ticks=collections.defaultdict(list)   # sym -> [(ts, mid)]
candles=collections.defaultdict(lambda: collections.OrderedDict())  # sym -> {minute: [opens, highs, lows, closes]}
last_emit=collections.defaultdict(int)
last_sig_time=0

def mid_from(j):
    for k in ("mid","price","last"):
        v=j.get(k); 
        if isinstance(v,(int,float)): return float(v)
    b,a=j.get("bid"), j.get("ask")
    if b is not None and a is not None:
        try: return (float(b)+float(a))/2
        except: return None
    return None

def push_tick(sym, ts, m):
    mb = minute_bucket(ts)
    c = candles[sym].get(mb)
    if not c:
        candles[sym][mb] = [m, m, m, m]  # o,h,l,c
    else:
        o,h,l,c0 = c
        h = max(h,m); l=min(l,m); c0=m
        candles[sym][mb] = [o,h,l,c0]
    # keep last ~120 minutes
    if len(candles[sym])>240:
        while len(candles[sym])>240:
            candles[sym].popitem(last=False)

def atr14(sym):
    # crude ATR on M1 from last 15 bars
    if len(candles[sym])<15: return None
    arr=list(candles[sym].values())[-15:]
    trs=[]
    prev_close=None
    for o,h,l,c in arr:
        if prev_close is None:
            tr=h-l
        else:
            tr=max(h-l, abs(h-prev_close), abs(l-prev_close))
        trs.append(tr); prev_close=c
    return sum(trs)/len(trs) if trs else None

def compression(sym):
    # find last window of MIN_COMP_BARS where range/ATR < COMP_RATIO
    if len(candles[sym]) < (MIN_COMP_BARS+5): return None
    arr=list(candles[sym].values())
    for w in range(len(arr)-MIN_COMP_BARS-1, -1, -1):
        window=arr[w:w+MIN_COMP_BARS]
        rng = max(x[1] for x in window) - min(x[2] for x in window)
        a14 = atr14(sym)
        if not a14 or a14<=0: return None
        if rng/a14 < COMP_RATIO:
            return {"start_index": w, "end_index": w+MIN_COMP_BARS-1, "range": rng, "atr14": a14,
                    "hi": max(x[1] for x in window), "lo": min(x[2] for x in window)}
    return None

def detect_vcb(sym):
    comp = compression(sym)
    if not comp: return None
    # Look at the most recent bar as trigger
    arr=list(candles[sym].values())
    if len(arr) < 1: return None
    o,h,l,c = arr[-1]
    # breakout above
    if c > comp["hi"] and (c - comp["hi"]) >= CLOSE_PCT * comp["range"]:
        return {"dir":"BUY","level":comp["hi"],"comp":comp, "last_close":c}
    # breakout below
    if c < comp["lo"] and (comp["lo"] - c) >= CLOSE_PCT * comp["range"]:
        return {"dir":"SELL","level":comp["lo"],"comp":comp, "last_close":c}
    return None

def plan(sym, det):
    ps = pip_size(sym)
    level = det["level"]
    rng = det["comp"]["range"]
    if det["dir"]=="BUY":
        entry = level  # conservative: retest at level
        sl    = level - rng - SL_BUF_PIPS*ps
        tp    = entry + max(RR_TARGET*(entry-sl), rng)  # aim at >=RR_TARGET or >=range
    else:
        entry = level
        sl    = level + rng + SL_BUF_PIPS*ps
        tp    = entry - max(RR_TARGET*(sl-entry), rng)
    rr = calc_rr(det["dir"], entry, sl, tp)
    return {"entry":entry,"sl":sl,"tp":tp,"rr":rr}

def publish(sym, det, plan):
    global last_sig_time
    ts = now_ts()
    sid = f"ELITE_GUARD_{sym}_{ts}"
    payload = {
        "signal_id": sid,
        "symbol": sym,
        "direction": det["dir"],
        "entry_price": round(plan["entry"], 6),
        "stop_pips": round(abs(plan["entry"]-plan["sl"])/pip_size(sym), 2),
        "target_pips": round(abs(plan["tp"]-plan["entry"])/pip_size(sym), 2),
        "confidence": 60.0,  # conservative base; include breakdown
        "pattern_type": "VCB_BREAKOUT",
        "signal_type": "PRECISION_STRIKE",
        "citadel_score": 0.0,
        "timestamp": ts,
        "calculation_breakdown": {
            "vcb": {
                "compression_range": det["comp"]["range"],
                "atr14": det["comp"]["atr14"],
                "close_pct_of_range": CLOSE_PCT,
                "level": det["level"],
                "rr": plan["rr"],
                "retest_bars": RETEST_BARS,
            }
        }
    }
    if EG_VCB_MODE=="shadow":
        payload["suppress_fire"]=True
    
    # Send as ELITE_GUARD_SIGNAL format
    msg = f"ELITE_GUARD_SIGNAL {json.dumps(payload)}"
    pub.send_string(msg)
    last_sig_time = ts
    print(f"[VCB] Published signal: {sid} {sym} {det['dir']} RR={plan['rr']:.2f}")

def allowed_to_emit(sym):
    # cooldown per symbol
    if now_ts() - last_emit[sym] < COOLDOWN_SEC: return False
    return True

def loop():
    print(f"[VCB Guard] Starting... Mode={EG_VCB_MODE}, MIN_RR={MIN_RR}")
    scan_counter = 0
    while True:
        try:
            m = sub.recv(flags=zmq.NOBLOCK)
            try:
                j=json.loads(m.decode() if isinstance(m,bytes) else m)
            except:
                s=(m.decode() if isinstance(m,bytes) else m)
                j=json.loads(s[s.find('{'):])
            sym = j.get("symbol") or j.get("Symbol") or j.get("sym")
            # Handle various timestamp formats
            ts_val = j.get("ts") or j.get("timestamp") or j.get("time")
            if ts_val:
                if isinstance(ts_val, (int, float)):
                    ts = int(ts_val)
                elif isinstance(ts_val, str):
                    # Handle "2025.08.13 01:37:57" format
                    if '.' in ts_val and ':' in ts_val:
                        from datetime import datetime
                        dt = datetime.strptime(ts_val, "%Y.%m.%d %H:%M:%S")
                        ts = int(dt.timestamp())
                    else:
                        ts = int(float(ts_val))
                else:
                    ts = int(time.time())
            else:
                ts = int(time.time())
            mid = mid_from(j)
            if not sym or mid is None: continue
            push_tick(sym, ts, float(mid))
        except zmq.Again:
            time.sleep(0.02)
        except Exception:
            time.sleep(0.05)

        # scan each second
        if int(time.time())%1==0 and EG_VCB_ENABLED:
            scan_counter += 1
            if scan_counter % 30 == 0:  # Log every 30 seconds
                print(f"[VCB] Scanning... {len(candles)} symbols tracked, {sum(len(v) for v in candles.values())} candles")
            
            for sym in list(candles.keys()):
                if not allowed_to_emit(sym): continue
                det = detect_vcb(sym)
                if not det: continue
                plan_out = plan(sym, det)
                if plan_out["rr"] < MIN_RR:  # HARD gate
                    continue
                publish(sym, det, plan_out)
                last_emit[sym]=now_ts()

if __name__=="__main__":
    loop()