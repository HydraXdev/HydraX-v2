#!/usr/bin/env python3
"""
STEP MF-2: Controlled tick listener for live price capture
Listens on port 5556 for EA tick data and captures XAUUSD price
"""
import json
import time
from datetime import datetime

import zmq


def capture_xauusd_price(timeout_seconds=30):
    """Capture live XAUUSD price from EA ticks"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5560")  # Connect to telemetry rebroadcast
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all
    socket.setsockopt(zmq.RCVTIMEO, timeout_seconds * 1000)

    print(f"🎯 CONTROLLED TICK LISTENER: Connecting to port 5560")
    print(f"   Searching for XAUUSD tick data...")
    print(f"   Timeout: {timeout_seconds} seconds")

    tick_count = 0
    xauusd_price = None

    try:
        while xauusd_price is None:
            try:
                # Receive tick data
                message = socket.recv().decode("utf-8")
                tick_count += 1

                # Parse tick data
                try:
                    tick_data = json.loads(message)
                    symbol = tick_data.get("symbol", "")
                    bid = tick_data.get("bid", 0)
                    ask = tick_data.get("ask", 0)

                    print(f"📊 [{tick_count}] {symbol}: bid={bid}, ask={ask}")

                    # Look for XAUUSD
                    if symbol == "XAUUSD" and bid > 0 and ask > 0:
                        xauusd_price = {
                            "symbol": "XAUUSD",
                            "bid": bid,
                            "ask": ask,
                            "mid": (bid + ask) / 2,
                            "timestamp": datetime.now().isoformat(),
                        }
                        print(f"✅ XAUUSD CAPTURED: {xauusd_price}")
                        break

                except json.JSONDecodeError:
                    # Handle non-JSON messages
                    print(f"📄 [{tick_count}] Raw: {message[:100]}...")

            except zmq.Again:
                print(f"⏰ TIMEOUT: No ticks received in {timeout_seconds} seconds")
                break

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")

    finally:
        socket.close()
        context.term()

    return xauusd_price, tick_count


if __name__ == "__main__":
    price_data, ticks = capture_xauusd_price(30)
    if price_data:
        print(f"\n🎯 SUCCESS: XAUUSD price captured after {ticks} ticks")
        print(f"   Mid Price: {price_data['mid']}")
    else:
        print(f"\n❌ FAILED: No XAUUSD price found in {ticks} ticks")
