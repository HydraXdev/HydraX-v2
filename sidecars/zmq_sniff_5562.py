import zmq, time, json, sys
EP = "tcp://127.0.0.1:5562"
ctx = zmq.Context.instance()
s = ctx.socket(zmq.SUB); s.connect(EP); s.setsockopt(zmq.SUBSCRIBE, b"")
print(f"[sniff] SUB -> {EP}; printing first 10 messages (with frame counts)...")
for i in range(10):
    try:
        parts = s.recv_multipart(flags=0, copy=True, track=False)
        print(f"[sniff] msg {i+1}: {len(parts)} frame(s)")
        for idx, p in enumerate(parts):
            dec = None
            try:
                dec = p.decode("utf-8", "ignore")
            except: pass
            print(f"  frame {idx}: {dec[:200]!r}")
        # Try to find JSON in any frame
        for p in parts:
            try:
                obj = json.loads(p.decode("utf-8","ignore"))
                print("  -> JSON detected keys:", list(obj)[:8])
                break
            except: pass
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print("[sniff] error:", e); time.sleep(0.2)
print("[sniff] done.")
