import zmq, time, json, sys
addr="tcp://127.0.0.1:5560"
ctx=zmq.Context.instance()
s=ctx.socket(zmq.SUB); s.connect(addr); s.setsockopt_string(zmq.SUBSCRIBE,""); s.RCVTIMEO=800
seen=set(); t0=time.time()
while time.time()-t0<90:
    try:
        m=s.recv()
        try:
            j=json.loads(m.decode() if isinstance(m,bytes) else m)
        except:
            m2=m.decode() if isinstance(m,bytes) else m
            j=json.loads(m2[m2.find('{'):])
        sym=j.get("symbol") or j.get("Symbol") or j.get("sym")
        if sym: seen.add(sym)
    except Exception:
        pass
print("\n".join(sorted(seen)))
