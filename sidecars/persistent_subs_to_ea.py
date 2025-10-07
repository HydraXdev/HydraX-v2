import socket, time, json, sys

EA_HOST, EA_PORT = "185.244.67.11", 8777
SYMS = ["EURUSD","GBPUSD","USDCHF","USDJPY","AUDUSD","NZDUSD","EURJPY","GBPJPY","EURGBP","EURAUD","GBPCAD","AUDJPY","NZDJPY","CHFJPY","CADJPY","AUDCAD","USDCNH","AUDNZD","XAUUSD","XAGUSD"]

def jsend(sock, obj):
    line = json.dumps(obj, separators=(',',':')) + "\n"
    sock.sendall(line.encode("utf-8"))

while True:
    try:
        print(f"[subs] connecting to {EA_HOST}:{EA_PORT} ...")
        with socket.create_connection((EA_HOST, EA_PORT), timeout=5) as s:
            # optional hello
            try: jsend(s, {"op":"HELLO","client":"persistent_subs","ts":int(time.time()*1000)})
            except: pass
            last = 0
            while True:
                now = time.time()
                if now - last > 30:  # every 30s, refresh subs + status
                    for sym in SYMS:
                        jsend(s, {"op":"TRACK_PRICES","symbol":sym})
                        jsend(s, {"op":"TRACK_OHLC","symbol":sym,"timeframe":"M1"})
                    jsend(s, {"op":"ACCOUNT_STATUS"})
                    jsend(s, {"op":"ORDER_LIST"})
                    last = now
                    print("[subs] refreshed 22 symbols + status")
                # light heartbeat to keep TCP warm
                try: jsend(s, {"op":"PING","ts":int(time.time()*1000)})
                except: pass
                time.sleep(5)
    except Exception as e:
        print("[subs] reconnect in 3s due to:", e); time.sleep(3)
