#!/usr/bin/env python3
"""
Get current XAUUSD price from port 5556 for MF-3 test
"""
import zmq
import json
import time

def get_current_xauusd_price():
    """Get live XAUUSD price from telemetry"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")  # Connect to telemetry source
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all
    socket.setsockopt(zmq.RCVTIMEO, 10000)  # 10 second timeout

    print("🔍 Fetching current XAUUSD price from port 5556...")

    try:
        for _ in range(50):  # Try up to 50 messages
            try:
                message = socket.recv().decode('utf-8')

                # Parse tick data
                try:
                    tick_data = json.loads(message)
                    symbol = tick_data.get('symbol', '')

                    if symbol == 'XAUUSD':
                        bid = tick_data.get('bid', 0)
                        ask = tick_data.get('ask', 0)
                        point = tick_data.get('point', 0.01)  # Default point value
                        digits = tick_data.get('digits', 2)   # Default digits

                        if bid > 0 and ask > 0:
                            mid = (bid + ask) / 2
                            print(f"✅ XAUUSD FOUND:")
                            print(f"   Bid: {bid}")
                            print(f"   Ask: {ask}")
                            print(f"   Mid: {mid}")
                            print(f"   Point: {point}")
                            print(f"   Digits: {digits}")

                            socket.close()
                            context.term()
                            return {
                                'bid': bid,
                                'ask': ask,
                                'mid': mid,
                                'point': point,
                                'digits': digits
                            }

                except json.JSONDecodeError:
                    continue  # Skip non-JSON messages

            except zmq.Again:
                print("⏰ Message timeout")
                break

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        socket.close()
        context.term()

    # Fallback with realistic XAUUSD values
    print("⚠️ Using fallback XAUUSD pricing")
    return {
        'bid': 2655.20,
        'ask': 2655.30,
        'mid': 2655.25,
        'point': 0.01,
        'digits': 2
    }

if __name__ == "__main__":
    price_data = get_current_xauusd_price()
    print(f"\n📊 FINAL XAUUSD DATA:")
    for key, value in price_data.items():
        print(f"   {key}: {value}")