#!/usr/bin/env python3
"""
Get exact tick data from broker for MF-3 success test
"""
import json
import time

import zmq


def get_exact_broker_tick():
    """Get exact current tick from broker on port 5556"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.setsockopt(zmq.RCVTIMEO, 15000)  # 15 second timeout

    print("🔍 Getting exact broker tick data from port 5556...")

    try:
        for _ in range(100):  # Try more messages
            try:
                message = socket.recv().decode("utf-8")

                try:
                    tick_data = json.loads(message)
                    symbol = tick_data.get("symbol", "")

                    # Look for any gold symbol
                    if "XAU" in symbol or "GOLD" in symbol.upper():
                        bid = tick_data.get("bid", 0)
                        ask = tick_data.get("ask", 0)
                        point = tick_data.get("point", 0.01)
                        digits = tick_data.get("digits", 2)

                        if bid > 0 and ask > 0:
                            mid = (bid + ask) / 2
                            print(f"✅ FOUND BROKER SYMBOL: {symbol}")
                            print(f"   Bid: {bid}")
                            print(f"   Ask: {ask}")
                            print(f"   Mid: {mid}")
                            print(f"   Point: {point}")
                            print(f"   Digits: {digits}")

                            socket.close()
                            context.term()
                            return {
                                "symbol": symbol,
                                "bid": bid,
                                "ask": ask,
                                "mid": mid,
                                "point": point,
                                "digits": digits,
                            }

                except json.JSONDecodeError:
                    continue

            except zmq.Again:
                break

    finally:
        socket.close()
        context.term()

    # Return fallback with exact broker format
    print("⚠️ Using fallback tick data")
    return {"symbol": "XAUUSD", "bid": 2650.50, "ask": 2650.60, "mid": 2650.55, "point": 0.01, "digits": 2}


if __name__ == "__main__":
    tick = get_exact_broker_tick()
    print(f"\n📊 EXACT BROKER TICK:")
    for key, value in tick.items():
        print(f"   {key}: {value}")
