#!/usr/bin/env python3
"""
Simple TCP Event Listener for HydraSocket EA
Receives events on port 5559 (bar_closed, account_summary, etc.)
"""

import json
import socket
import threading
from datetime import datetime


def listen_events():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5559))
    server.listen(200)
    print(f"{datetime.now()} | Event listener ready on port 5559")

    connection_count = 0

    while True:
        try:
            conn, addr = server.accept()
            connection_count += 1
            print(f"{datetime.now()} | 📡 EA events connected from {addr} (connection #{connection_count})")
            threading.Thread(target=handle_events, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print(f"\n{datetime.now()} | Shutting down...")
            break
        except Exception as e:
            print(f"{datetime.now()} | Error accepting connection: {e}")


def handle_events(conn, addr):
    buffer = ""
    event_count = 0
    last_summary_time = 0

    try:
        while True:
            data = conn.recv(8192)
            if not data:
                print(f"{datetime.now()} | EA events disconnected from {addr} (processed {event_count} events)")
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    try:
                        event = json.loads(line)
                        event_count += 1
                        event_type = event.get("type", "unknown")

                        # Log different event types with smart throttling
                        if event_type == "custom_bar_closed":
                            symbol = event.get("symbol", "?")
                            close = event.get("c", 0)
                            print(f"{datetime.now()} | 📊 15-sec bar: {symbol} close={close}")

                        elif event_type == "bar_closed":
                            symbol = event.get("symbol", "?")
                            tf = event.get("tf", "?")
                            close = event.get("c", 0)
                            print(f"{datetime.now()} | 📈 Bar closed: {symbol} {tf} close={close}")

                        elif event_type == "account_summary":
                            # Throttle account_summary to once per 10 seconds
                            now = datetime.now().timestamp()
                            if now - last_summary_time > 10:
                                balance = event.get("balance", 0)
                                equity = event.get("equity", 0)
                                print(f"{datetime.now()} | 💰 Account: Balance=${balance:.2f} Equity=${equity:.2f}")
                                last_summary_time = now

                        elif event_type == "portfolio_snapshot":
                            positions = event.get("positions", [])
                            print(f"{datetime.now()} | 📸 Portfolio snapshot: {len(positions)} positions")

                        elif event_type == "position_heartbeat":
                            # Only log first heartbeat, then throttle heavily
                            if event_count <= 5:
                                ticket = event.get("ticket", "?")
                                print(f"{datetime.now()} | 💓 Position heartbeat: ticket={ticket}")

                        elif event_type == "tick":
                            # Heavy throttle on ticks
                            if event_count % 100 == 0:
                                symbol = event.get("symbol", "?")
                                bid = event.get("bid", 0)
                                ask = event.get("ask", 0)
                                print(f"{datetime.now()} | 📍 Tick: {symbol} bid={bid} ask={ask}")

                        else:
                            # Log unknown event types
                            print(f"{datetime.now()} | 📨 Event: {event_type}")

                    except json.JSONDecodeError as e:
                        print(f"{datetime.now()} | ❌ Invalid JSON: {e}")
                        print(f"   Data: {line[:100]}")

    except Exception as e:
        print(f"{datetime.now()} | Event connection error from {addr}: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    listen_events()
