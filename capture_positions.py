#!/usr/bin/env python3
"""
Capture and display complete position data from HydraSocket EA
"""
import json
import socket
import threading


def handle_connection(conn, addr):
    """Handle incoming EA connection and display full position data"""
    print(f"✅ Connected from {addr}")

    buffer = ""
    positions = {}

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode("utf-8", errors="ignore")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    try:
                        event = json.loads(line)

                        if event.get("type") == "position_heartbeat":
                            ticket = event.get("ticket", "unknown")
                            positions[ticket] = event

                            # Display complete position data
                            print("\n" + "=" * 60)
                            print(f"🎯 POSITION {ticket}:")
                            print(f"  Symbol: {event.get('symbol')}")
                            print(f"  Type: {event.get('direction')}")
                            print(f"  Volume: {event.get('volume')} lots")
                            print(f"  Entry: {event.get('open_price')}")
                            print(f"  Current: {event.get('current_price')}")
                            print(f"  SL: {event.get('sl')}")
                            print(f"  TP: {event.get('tp')}")
                            print(f"  Profit: ${event.get('profit')}")
                            print(f"  Commission: ${event.get('commission')}")
                            print(f"  Swap: ${event.get('swap')}")
                            print(f"  Open Time: {event.get('open_time')}")
                            print("=" * 60)

                        elif event.get("type") == "account_summary":
                            print(f"\n💰 ACCOUNT UPDATE:")
                            print(f"  Balance: ${event.get('balance')}")
                            print(f"  Equity: ${event.get('equity')}")
                            print(f"  Margin: ${event.get('margin_used')}")
                            print(f"  Free Margin: ${event.get('margin_free')}")
                            print(f"  Positions: {len(positions)}")

                    except json.JSONDecodeError as e:
                        pass

        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"\n📊 FINAL POSITION SUMMARY:")
    print(f"Total Open Positions: {len(positions)}")
    for ticket, pos in positions.items():
        print(
            f"  - {pos.get('symbol')} {pos.get('direction')} {pos.get('volume')} @ {pos.get('open_price')} | P&L: ${pos.get('profit')}"
        )

    conn.close()


# Create server on port 5559 to intercept events
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# We'll listen on a different port to not interfere
server.bind(("0.0.0.0", 5561))
server.listen(10)

print("🔍 Position Monitor listening on port 5561")
print("Waiting for EA to connect...")
print("\nTo use: Temporarily change EA events port from 5559 to 5561")
print("Or we can tap into the existing stream...\n")

# Actually, let's just connect to the existing stream
print("Connecting to existing event stream on port 5559...")

# Connect as a client to capture data
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(("127.0.0.1", 5559))
    print("Connected to event stream!")
    handle_connection(client, ("127.0.0.1", 5559))
except Exception as e:
    print(f"Could not connect to existing stream: {e}")
    print("\nAlternatively, waiting for direct EA connection on 5561...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()
