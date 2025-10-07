#!/usr/bin/env python3
import json
import socket
import sys

# FORCE UNBUFFERED OUTPUT
sys.stdout = open(1, "w", buffering=1)
sys.stderr = open(2, "w", buffering=1)

print("Starting ultra simple server...", flush=True)

# Create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print(f"Binding to 0.0.0.0:5555...", flush=True)
s.bind(("0.0.0.0", 5555))

print(f"Listening...", flush=True)
s.listen(5)

print(f"✅ SERVER READY ON 0.0.0.0:5555 - ACCEPTING CONNECTIONS", flush=True)

# MAIN ACCEPT LOOP
while True:
    print(f"Waiting for connection...", flush=True)

    try:
        conn, addr = s.accept()
        print(f"✅✅✅ GOT CONNECTION from {addr}", flush=True)

        # Send feed_set immediately
        feed = {"type": "feed_set", "symbols": "XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD", "tfs": "M1,M5,H1", "lookback": 200}

        msg = json.dumps(feed) + "\n"
        conn.send(msg.encode())
        print(f"📤 Sent feed_set to {addr}", flush=True)

        # Keep connection open
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received: {data[:50]}", flush=True)

    except Exception as e:
        print(f"Error: {e}", flush=True)

print("Server ended", flush=True)
