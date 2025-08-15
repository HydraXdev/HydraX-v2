import zmq, time, json, collections
addr="tcp://127.0.0.1:5560"
ctx=zmq.Context.instance()
s=ctx.socket(zmq.SUB); s.connect(addr); s.setsockopt_string(zmq.SUBSCRIBE,""); s.RCVTIMEO=1000
counts=collections.Counter()
t0=time.time()
while time.time()-t0<300:
    try:
        m=s.recv()
        try:
            j=json.loads(m.decode() if isinstance(m,bytes) else m)
        except:
            m2=m.decode() if isinstance(m,bytes) else m
            j=json.loads(m2[m2.find('{'):])
        sym=j.get("symbol") or j.get("Symbol") or j.get("sym")
        if sym: counts[sym]+=1
    except: pass
for k,v in counts.most_common():
    print(f"{k},{v}")