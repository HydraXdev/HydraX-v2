import json
import socket
import sys
import threading
import time

EA_HOST = "185.244.67.11"
EA_PORT = 8777
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 5561
BUF = 65536


def forward_to_ea(payload: bytes) -> bool:
    # Open a short-lived TCP to EA and send the JSON line (payload already includes newline)
    try:
        with socket.create_connection((EA_HOST, EA_PORT), timeout=2) as s:
            s.sendall(payload)
            # optional: read ack but we don't require it
        return True
    except Exception as e:
        sys.stderr.write(f"[cmd-proxy] forward error: {e}\n")
        return False


def handle_client(conn, addr):
    try:
        data = b""
        while True:
            chunk = conn.recv(BUF)
            if not chunk:
                break
            data += chunk
            # process line-delimited JSON
            while b"\n" in data:
                line, data = data.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                ok = forward_to_ea(line + b"\n")
                # simple ack to caller
                try:
                    conn.sendall(b'{"ok":%s}\n' % (b"true" if ok else b"false"))
                except:
                    pass
    finally:
        try:
            conn.close()
        except:
            pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((LISTEN_HOST, LISTEN_PORT))
    srv.listen(100)
    sys.stdout.write(f"[cmd-proxy] listening on {LISTEN_HOST}:{LISTEN_PORT} -> {EA_HOST}:{EA_PORT}\n")
    while True:
        c, a = srv.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()


if __name__ == "__main__":
    main()
