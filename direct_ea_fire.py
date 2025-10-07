#!/usr/bin/env python3
"""
DIRECT EA FIRE - Bypass broken IPC bridge, send directly to ROUTER
"""
import zmq
import json
import time

def send_direct_fire():
    """Send fire command directly to EA via ROUTER socket"""
    ctx = zmq.Context()

    # Connect as DEALER to existing ROUTER (command_router on port 5555)
    dealer = ctx.socket(zmq.DEALER)
    dealer.setsockopt(zmq.IDENTITY, b"DIRECT_TEST_CLIENT")
    dealer.connect("tcp://localhost:5555")

    # Listen for confirmations
    conf_listener = ctx.socket(zmq.PULL)
    conf_listener.connect("tcp://localhost:5558")
    conf_listener.setsockopt(zmq.RCVTIMEO, 10000)  # 10 second timeout

    # Fire command with realistic XAUUSD prices
    fire_cmd = {
        "type": "fire",
        "fire_id": f"DIRECT_FIRE_{int(time.time())}",
        "symbol": "XAUUSD",
        "direction": "BUY",
        "lot": 0.01,
        "sl": 1950.0,   # Conservative distance
        "tp": 1970.0,   # Conservative target
        "snapshot_tf": "M1"
    }

    print(f"🎯 Sending DIRECT FIRE to EA:")
    print(f"   Command: {json.dumps(fire_cmd)}")

    # Send as DEALER (no identity frame needed - DEALER handles it)
    dealer.send_string(json.dumps(fire_cmd))

    print(f"⏰ Waiting for EA response on port 5558...")

    try:
        response = conf_listener.recv().decode()
        print(f"✅ EA RESPONSE: {response}")

        # Parse and display result
        try:
            resp_data = json.loads(response)
            status = resp_data.get("status", "unknown")
            message = resp_data.get("message", "")
            ticket = resp_data.get("ticket", "")

            if status == "success":
                print(f"🎉 TRADE EXECUTED! Ticket: {ticket}")
                return True
            else:
                print(f"⚠️ TRADE REJECTED: {message}")
                return False

        except Exception as e:
            print(f"📄 Raw response (parse error): {response}")
            return False

    except zmq.error.Again:
        print("❌ No EA response within 10 seconds")
        print("   EA may not be connected or command format wrong")
        return False

    finally:
        dealer.close()
        conf_listener.close()
        ctx.term()

if __name__ == "__main__":
    success = send_direct_fire()
    if success:
        print("\n✅ VICTORY! Direct EA communication works!")
        print("   Issue: IPC bridge in command_router needs fixing")
    else:
        print("\n❌ Still broken - check EA connection or command format")