#\!/usr/bin/env python3
import os, time, json, collections
import zmq

# --- ENV / defaults ---
ENABLED   = os.getenv("EG_SRL_ENABLED","1") == "1"
MODE      = os.getenv("EG_SRL_MODE","shadow")   # shadow | live
LOOKBACK  = int(os.getenv("EG_SRL_LOOKBACK","30"))   # bars to find swing
WICK_PCT  = float(os.getenv("EG_SRL_WICK_PCT","60"))/100.0  # wick must be ≥60% of bar
RETURN_B  = int(os.getenv("EG_SRL_RETURN_BARS","3"))   # must return inside prior range within N bars
RR_MIN    = max(1.4, float(os.getenv("EG_MIN_RR","1.4")))   # NEVER below 1.4
RR_TARGET = float(os.getenv("EG_SRL_RR_TARGET","1.6"))
SL_BUF    = float(os.getenv("EG_SRL_SL_BUFFER_PIPS","1"))
COOLDOWN  = int(os.getenv("EG_GLOBAL_COOLDOWN_SEC","5"))

PIP = {"EURUSD":0.0001,"GBPUSD":0.0001,"USDJPY":0.01,"EURJPY":0.01,"GBPJPY":0.01,"XAUUSD":0.1,"XAGUSD":0.01,"US100":1.0,"NAS100":1.0}
def pip(sym): return PIP.get(sym,0.0001)
def now(): return int(time.time())
def rr(direction, entry, sl, tp):
    risk=abs(entry-sl); reward=abs(tp-entry); return (reward/risk) if risk>0 else 0.0

# --- Candles from ticks (M1 pseudo) ---
def mid(j):
    for k in ("mid","price","last"):
        v=j.get(k)
        if isinstance(v,(int,float)): return float(v)
    b,a=j.get("bid"), j.get("ask")
    if b is not None and a is not None:
        try: return (float(b)+float(a))/2
        except: return None
    return None
def m_bucket(ts): return int(ts//60)

ctx=zmq.Context.instance()
sub=ctx.socket(zmq.SUB); sub.connect("tcp://127.0.0.1:5560"); sub.setsockopt_string(zmq.SUBSCRIBE,""); sub.RCVTIMEO=1000
pub=ctx.socket(zmq.PUB); pub.connect("tcp://127.0.0.1:5557")

candles=collections.defaultdict(lambda: collections.OrderedDict())  # sym -> {min: [o,h,l,c]}
last_emit=collections.defaultdict(int)

def push(sym, ts, m):
    mb=m_bucket(ts)
    c=candles[sym].get(mb)
    if not c: candles[sym][mb]=[m,m,m,m]
    else:
        o,h,l,cl=c; h=max(h,m); l=min(l,m); cl=m; candles[sym][mb]=[o,h,l,cl]
    if len(candles[sym])>240:
        while len(candles[sym])>240: candles[sym].popitem(last=False)

def find_swing(sym, lookback):
    arr=list(candles[sym].values())
    if len(arr)<lookback+2: return None
    window=arr[-(lookback+1):-1]  # exclude current
    hi=max(x[1] for x in window); lo=min(x[2] for x in window)
    return hi,lo

def detect(sym):
    arr=list(candles[sym].values())
    if len(arr)<(LOOKBACK+2): return None
    hi,lo = find_swing(sym, LOOKBACK)
    o,h,l,c = arr[-1]
    body=abs(c-o); rng=max(h-l, 1e-12)
    wick_up = h-max(c,o)
    wick_dn = min(c,o)-l
    # Sweep above prior high, long upper wick, then close back inside prior range => SELL setup
    if h>hi and c<hi and wick_up >= WICK_PCT*rng:
        return {"dir":"SELL","swept":"high","swing":hi,"bar":[o,h,l,c]}
    # Sweep below prior low, long lower wick, then close back inside prior range => BUY setup
    if l<lo and c>lo and wick_dn >= WICK_PCT*rng:
        return {"dir":"BUY","swept":"low","swing":lo,"bar":[o,h,l,c]}
    return None

def plan(sym, det):
    ps=pip(sym)
    o,h,l,c=det["bar"]
    if det["dir"]=="SELL":
        entry = det["swing"]  # re-entry near swing
        sl    = h + SL_BUF*ps
        risk  = abs(entry-sl)
        tp    = entry - RR_TARGET*risk
    else:
        entry = det["swing"]
        sl    = l - SL_BUF*ps
        risk  = abs(entry-sl)
        tp    = entry + RR_TARGET*risk
    return {"entry":entry,"sl":sl,"tp":tp,"rr":rr(det["dir"],entry,sl,tp)}

def publish(sym, det, plan):
    ts=now()
    sid=f"ELITE_GUARD_{sym}_{ts}"
    payload={
        "signal_id":sid,"symbol":sym,"direction":det["dir"],
        "entry_price":round(plan["entry"],6),
        "stop_pips":round(abs(plan["entry"]-plan["sl"])/pip(sym),2),
        "target_pips":round(abs(plan["tp"]-plan["entry"])/pip(sym),2),
        "confidence":62.0,
        "pattern_type":"SWEEP_RETURN",
        "signal_type":"PRECISION_STRIKE","citadel_score":0.0,
        "timestamp":ts,
        "calculation_breakdown":{
            "srl":{
                "swept":det["swept"],"swing":det["swing"],
                "wick_pct":float(os.getenv("EG_SRL_WICK_PCT","60")),
                "rr":plan["rr"],"lookback":LOOKBACK
            }
        }
    }
    if MODE=="shadow": payload["suppress_fire"]=True
    pub.send_string(json.dumps(payload))

def loop():
    while True:
        try:
            m=sub.recv(flags=zmq.NOBLOCK)
            try: j=json.loads(m.decode() if isinstance(m,bytes) else m)
            except:
                s=m.decode() if isinstance(m,bytes) else m
                j=json.loads(s[s.find('{'):])
            sym=j.get("symbol") or j.get("Symbol") or j.get("sym")
            ts=int(j.get("ts") or j.get("timestamp") or time.time())
            md=mid(j)
            if not sym or md is None: continue
            push(sym, ts, float(md))
        except zmq.Again:
            time.sleep(0.02)
        except Exception:
            time.sleep(0.05)

        # scan once per second
        if ENABLED and int(time.time())%1==0:
            for sym in list(candles.keys()):
                if now()-last_emit[sym] < COOLDOWN: continue
                det=detect(sym)
                if not det: continue
                plan_out=plan(sym, det)
                if plan_out["rr"] < RR_MIN: continue  # HARD RR gate
                publish(sym, det, plan_out)
                last_emit[sym]=now()

if __name__=="__main__":
    loop()
