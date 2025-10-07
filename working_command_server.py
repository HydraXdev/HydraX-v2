#!/usr/bin/env python3
"""
WORKING TCP Command Server on port 7777
Since port 5555 has mysterious issues, using 7777 which we KNOW works
"""
import socket
import json
import sys
import threading

# Force unbuffered
sys.stdout = open(1, 'w', 1)

print("Starting TCP Command Server on port 7777", flush=True)

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 7777))
server.listen(10)

print("✅ Server listening on 0.0.0.0:7777", flush=True)
print("Waiting for EA connections...", flush=True)

def handle_ea(conn, addr):
    print(f"✅ EA CONNECTED from {addr}", flush=True)

    # Send feed_set immediately
    feed_cmd = {
        "type": "feed_set",
        "request_ref": "init-feed",
        "symbols": "XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD,USDCAD,USDCHF,AUDUSD,NZDUSD,EURJPY,EURGBP,EURCAD,EURAUD,AUDJPY,NZDJPY,GBPCAD,CHFJPY,GBPCHF,EURCHF",
        "tfs": "M1,M5,H1",
        "lookback": 200,
        "midbar": 0,
        "midbar_sec": 15
    }

    msg = json.dumps(feed_cmd) + "\n"
    conn.send(msg.encode())
    print(f"📤 Sent feed_set command to EA", flush=True)

    # Handle incoming messages
    buffer = ""
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line:
                    try:
                        cmd = json.loads(line)
                        print(f"📥 From EA: {cmd.get('type', 'unknown')}", flush=True)
                    except:
                        pass
        except:
            break

    print(f"🔌 EA disconnected from {addr}", flush=True)
    conn.close()

# Main accept loop
while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_ea, args=(conn, addr), daemon=True).start()