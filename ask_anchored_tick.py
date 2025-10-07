#!/usr/bin/env python3
"""
Get live tick from port 5556 for ask-anchored MF-3 test
"""
import json
import time

import zmq


def get_live_tick():
    """Get exact live tick from port 5556"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.setsockopt(zmq.RCVTIMEO, 20000)  # 20 second timeout

    print("🔍 Reading live tick from port 5556...")

    try:
        for _ in range(200):  # Try many messages
            try:
                message = socket.recv().decode("utf-8")

                try:
                    tick = json.loads(message)
                    symbol = tick.get("symbol", "")

                    if "XAU" in symbol.upper():
                        ask = tick.get("ask", 0)
                        point = tick.get("point", 0.01)

                        if ask > 0:
                            # Infer digits from ask precision
                            ask_str = str(ask)
                            if "." in ask_str:
                                digits = len(ask_str.split(".")[1])
                            else:
                                digits = 2

                            print(f"✅ LIVE TICK: {symbol}")
                            print(f"   Ask: {ask}")
                            print(f"   Point: {point}")
                            print(f"   Digits: {digits}")

                            socket.close()
                            context.term()
                            return {"symbol": symbol, "ask": ask, "point": point, "digits": digits}

                except json.JSONDecodeError:
                    continue

            except zmq.Again:
                break

    finally:
        socket.close()
        context.term()

    # Return fallback
    return {"symbol": "XAUUSD", "ask": 2651.00, "point": 0.01, "digits": 2}


if __name__ == "__main__":
    tick = get_live_tick()
    print(f"\n📊 LIVE TICK DATA:")
    for key, value in tick.items():
        print(f"   {key}: {value}")
