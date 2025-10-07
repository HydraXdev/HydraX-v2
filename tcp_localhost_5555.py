#!/usr/bin/env python3
"""
TCP Server on localhost:5555 for socat bridge
"""
import json
import socket
import sys
import threading
import time

# Force unbuffered output
sys.stdout = open(1, "w", 1)
sys.stderr = open(2, "w", 1)

print(f"Starting TCP server on localhost:5555 at {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


def handle_client(conn, addr):
    print(f"✅ EA CONNECTED via socat from {addr}", flush=True)

    # Send initial feed_set command
    feed_cmd = {
        "type": "feed_set",
        "request_ref": f"init-{int(time.time())}",
        "symbols": "XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD,USDCAD,USDCHF,AUDUSD,NZDUSD,EURJPY,EURGBP,EURCAD,EURAUD,AUDJPY,NZDJPY,GBPCAD,CHFJPY,GBPCHF,EURCHF",
        "tfs": "M1,M5,H1",
        "lookback": 200,
        "midbar": 0,
        "midbar_sec": 15,
    }

    msg = json.dumps(feed_cmd) + "\n"
    conn.send(msg.encode())
    print(f"📤 Sent feed_set to {addr}", flush=True)

    # Handle incoming messages
    buffer = ""
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    try:
                        cmd = json.loads(line)
                        print(f"📥 From EA: {cmd.get('type', 'unknown')}", flush=True)

                        # Send acknowledgment
                        ack = {"type": "command_result", "request_ref": cmd.get("request_ref", ""), "status": "success"}
                        conn.send((json.dumps(ack) + "\n").encode())
                    except Exception as e:
                        print(f"Error parsing: {e}", flush=True)
        except Exception as e:
            print(f"Connection error: {e}", flush=True)
            break

    print(f"🔌 EA disconnected from {addr}", flush=True)
    conn.close()


# Create server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to localhost:5555 (socat will bridge from external)
server.bind(("127.0.0.1", 5555))
server.listen(10)

print("✅ TCP Server listening on 127.0.0.1:5555", flush=True)
print("Socat will bridge from 0.0.0.0:5555 to here", flush=True)

# Main accept loop
while True:
    try:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down...", flush=True)
        break
    except Exception as e:
        print(f"Accept error: {e}", flush=True)
