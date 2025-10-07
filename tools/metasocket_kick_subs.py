import json
import socket
import time

ACTIVE = [
    "EURUSD",
    "GBPUSD",
    "USDCHF",
    "USDJPY",
    "AUDUSD",
    "NZDUSD",
    "EURJPY",
    "GBPJPY",
    "EURGBP",
    "EURAUD",
    "GBPCAD",
    "AUDJPY",
    "NZDJPY",
    "CHFJPY",
    "CADJPY",
    "AUDCAD",
    "USDCNH",
    "AUDNZD",
    "XAUUSD",
    "XAGUSD",
]

HOST, PORT = "127.0.0.1", 5561  # daemon command port


def send(sock, obj):
    line = json.dumps(obj, separators=(",", ":")) + "\n"
    sock.sendall(line.encode("utf-8"))


with socket.create_connection((HOST, PORT), timeout=2) as s:
    # small hello if the daemon expects it
    try:
        send(s, {"op": "HELLO", "client": "kick_subs", "ts": int(time.time() * 1000)})
    except:
        pass
    for sym in ACTIVE:
        send(s, {"op": "TRACK_PRICES", "symbol": sym})
        send(s, {"op": "TRACK_OHLC", "symbol": sym, "timeframe": "M1"})
        time.sleep(0.02)
    # ask for account + order list to wake pipelines
    send(s, {"op": "ACCOUNT_STATUS"})
    send(s, {"op": "ORDER_LIST"})
    # brief wait to avoid immediate close
    time.sleep(0.2)
print("✅ Sent subscriptions for 22 symbols.")
