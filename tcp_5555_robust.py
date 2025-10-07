#!/usr/bin/env python3
"""
Robust TCP Server on port 5555 for HydraSocket EA Commands
Handles telnet IAC sequences and keeps connection alive
"""
import json
import socket
import sys
import threading
import time

# Force unbuffered output
sys.stdout = open(1, "w", 1)
sys.stderr = open(2, "w", 1)

print(f"Starting robust TCP server on port 5555 at {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


def handle_client(conn, addr):
    print(f"✅ EA CONNECTED from {addr}", flush=True)

    try:
        # Send initial feed_set command
        feed_cmd = {
            "type": "feed_set",
            "request_ref": "server-init",
            "symbols": "XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD,USDCAD,USDCHF,AUDUSD,NZDUSD,EURJPY,EURGBP,EURCAD,EURAUD,AUDJPY,NZDJPY,GBPCAD,CHFJPY,GBPCHF,EURCHF",
            "tfs": "M1,M5,H1",
            "lookback": 200,
        }

        msg = json.dumps(feed_cmd) + "\n"
        conn.send(msg.encode())
        print(f"📤 Sent feed_set to {addr}", flush=True)

        # IMPORTANT: Keep connection open to receive responses!
        buffer = ""
        last_heartbeat = time.time()

        while True:
            try:
                # Set timeout for recv to allow periodic heartbeat
                conn.settimeout(5.0)
                data = conn.recv(4096)

                if not data:
                    print(f"Connection closed by {addr}")
                    break

                # Skip telnet IAC sequences (0xFF commands)
                if data[0:1] == b"\xff":
                    print(f"Skipping telnet IAC sequence from {addr}")
                    continue

                # Try to decode, ignoring errors
                try:
                    text = data.decode("utf-8", errors="ignore")
                    buffer += text
                except:
                    print(f"Skipping non-UTF8 data from {addr}: {data.hex()}")
                    continue

                # Process complete lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        try:
                            response = json.loads(line)
                            print(f"📥 EA response: {response}", flush=True)

                            # Handle different message types
                            msg_type = response.get("type", "")

                            if msg_type == "command_result":
                                # EA acknowledging our command
                                print(f"  ✅ EA acknowledged: {response.get('request_ref', '')}")

                            elif msg_type == "ping":
                                # Respond to ping with pong
                                pong = {"type": "pong", "timestamp": time.time()}
                                conn.send((json.dumps(pong) + "\n").encode())
                                print(f"  🏓 Sent pong to {addr}")

                            elif msg_type == "heartbeat":
                                # EA is alive
                                last_heartbeat = time.time()
                                print(f"  💗 Heartbeat from {addr}")

                            else:
                                # Unknown message type, send generic ack
                                ack = {"type": "ack", "status": "ok"}
                                conn.send((json.dumps(ack) + "\n").encode())

                        except json.JSONDecodeError as e:
                            print(f"JSON parse error from {addr}: {e}")
                            print(f"  Raw line: {line[:100]}")  # First 100 chars

            except socket.timeout:
                # Check if we should send a keepalive
                if time.time() - last_heartbeat > 30:
                    # Send server heartbeat
                    heartbeat = {"type": "server_heartbeat", "timestamp": time.time()}
                    conn.send((json.dumps(heartbeat) + "\n").encode())
                    print(f"  💓 Sent server heartbeat to {addr}")
                    last_heartbeat = time.time()

            except Exception as e:
                print(f"Connection error with {addr}: {e}")
                break

    except Exception as e:
        print(f"Handler error for {addr}: {e}")

    finally:
        print(f"🔌 EA disconnected from {addr}", flush=True)
        conn.close()


# Create server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to 0.0.0.0:5555 (accept from anywhere)
server.bind(("0.0.0.0", 5555))
server.listen(10)

print("✅ TCP Server listening on 0.0.0.0:5555", flush=True)
print("Ready for EA connections...", flush=True)

# Main accept loop
while True:
    try:
        conn, addr = server.accept()
        # Handle each connection in a separate thread
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down...", flush=True)
        break
    except Exception as e:
        print(f"Accept error: {e}", flush=True)
