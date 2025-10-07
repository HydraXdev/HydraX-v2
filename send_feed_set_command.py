#!/usr/bin/env python3
"""
Send feed_set command to EA to initialize watchlist

This sends the command through the IPC queue that command_router monitors,
which will then route it to the EA via ZMQ.
"""

import json
import time

import zmq


def send_feed_set_command():
    """Send feed_set command to initialize EA watchlist"""

    # Default symbols from EA code (line 36)
    symbols = "XAUUSD,EURUSD,GBPJPY,USDJPY,GBPUSD,USDCAD,USDCHF,AUDUSD,NZDUSD,EURJPY,EURGBP,EURCAD,EURAUD,AUDJPY,NZDJPY,GBPCAD,CHFJPY,GBPCHF,EURCHF"

    command = {
        "type": "feed_set",
        "request_ref": f"init-feed-{int(time.time())}",
        "target_uuid": "COMMANDER_DEV_001",  # EA identity for routing
        "symbols": symbols,
        "tfs": "M1,M5,H1",
        "lookback": 200,
        "midbar": 0,
        "midbar_sec": 10,
    }

    try:
        # Connect to IPC queue (same as webapp uses for fire commands)
        context = zmq.Context()
        sender = context.socket(zmq.PUSH)
        sender.connect("ipc:///tmp/bitten_cmdqueue")

        # Send command
        sender.send_json(command)
        print(f"✅ Sent feed_set command to EA")
        print(f"   Symbols: 19 pairs")
        print(f"   Timeframes: M1, M5, H1")
        print(f"   Lookback: 200 candles")

        sender.close()
        context.term()

        print("\n📊 Expected result:")
        print("   1. EA will call BuildWatchlist()")
        print("   2. EA will call EmitBootstrap() - sending historical bars")
        print("   3. EA will start emitting custom_bar_closed every 15 seconds")
        print("   4. Universal Bridge will forward to port 5556")
        print("   5. zmq_telemetry_bridge will relay to port 5560")
        print("   6. Elite Guard will receive data and start pattern scanning")
        print("\n⏱️  Check logs in 30 seconds:")
        print("   tail -f /var/log/hydrasocket_universal_bridge.log | grep -E 'bar_closed|custom_bar'")

        return True

    except Exception as e:
        print(f"❌ Failed to send command: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Sending feed_set Command to EA")
    print("=" * 60)
    print()

    result = send_feed_set_command()

    if result:
        print("\n✅ Command sent successfully!")
    else:
        print("\n❌ Command failed!")
