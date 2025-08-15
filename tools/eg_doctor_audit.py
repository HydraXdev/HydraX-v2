import zmq, time, json, statistics, collections, os
# Subscribe to market ticks only; do not publish anything.
SRC="tcp://127.0.0.1:5560"
WINDOW_SEC=int(os.environ.get("EGD_WIN","300"))  # 5 min default
ctx=zmq.Context.instance()
s=ctx.socket(zmq.SUB); s.connect(SRC); s.setsockopt_string(zmq.SUBSCRIBE,""); s.RCVTIMEO=1000

def mid(j):
    for k in ("mid","price","last"): 
        v=j.get(k); 
        if isinstance(v,(int,float)): return float(v)
    b,a=j.get("bid"), j.get("ask")
    if b is not None and a is not None:
        try: return (float(b)+float(a))/2
        except: return None
    return None

buf=collections.defaultdict(list)
start=time.time()
scans=0
reasons=collections.Counter()

def gates(series):
    # Quick/rough "is there any structure?" audit; not your trading logic.
    # 1) momentum breakout vs last N
    if len(series)<15: return None
    last=series[-1]
    hi=max(series[-15:-1]); lo=min(series[-15:-1])
    if last>hi: return ("breakout_up", None)
    if last<lo: return ("breakout_dn", None)
    # 2) simple engulfing with last 2 pseudo-candles (10-tick buckets)
    a=series[-20:-10]; b=series[-10:]
    if not a or not b: return None
    ao, ah, al, ac = a[0], max(a), min(a), a[-1]
    bo, bh, bl, bc = b[0], max(b), min(b), b[-1]
    bull = (bc>bo) and (ac<ao) and (bc>=ao) and (bo<=ac)
    bear = (bc<bo) and (ac>ao) and (bo>=ac) and (bc<=ao)
    if bull: return ("engulf_bull", None)
    if bear: return ("engulf_bear", None)
    return None

while time.time()-start < WINDOW_SEC:
    try:
        m=s.recv()
        try:
            j=json.loads(m.decode() if isinstance(m,bytes) else m)
        except:
            m2=m.decode() if isinstance(m,bytes) else m
            j=json.loads(m2[m2.find('{'):])
        sym = j.get("symbol") or j.get("Symbol") or j.get("sym")
        p = mid(j)
        if sym and p is not None:
            buf[sym].append(p)
            if len(buf[sym])>300: buf[sym]=buf[sym][-300:]
    except Exception:
        pass
    if int(time.time()-start)%10==0:
        scans+=1

hits=[]
for sym, series in buf.items():
    g=gates(series)
    if g:
        hits.append((sym,g[0]))

report=[]
report.append(f"[EG-DOCTOR] Window {WINDOW_SEC}s, symbols_seen={len(buf)}, patterns_found={len(hits)}")
if hits:
    # summarize counts per type
    cnt=collections.Counter([h[1] for h in hits])
    report.append("[EG-DOCTOR] hit_types: " + ", ".join(f"{k}:{v}" for k,v in cnt.items()))
    # show up to 10 symbols
    tops=collections.Counter([h[0] for h in hits]).most_common(10)
    report.append("[EG-DOCTOR] example_symbols: " + ", ".join(f"{k}" for k,_ in tops))
else:
    report.append("[EG-DOCTOR] no simple structures detected; either market is quiet or higher-level gates are stricter than these.")
print("\n".join(report))