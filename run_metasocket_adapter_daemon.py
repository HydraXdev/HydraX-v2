#!/usr/bin/env python3
"""
MetaSocket Adapter Daemon
Runs the MetaSocket adapter as a persistent service
"""

import os
import signal
import sys
import time

sys.path.append("/root/HydraX-v2")

from adapters.metasocket.adapter import MetaSocketAdapter


def signal_handler(signum, frame):
    print(f"🔄 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


def main():
    print("🎯 MetaSocket Adapter Daemon Starting...")

    # Read environment variables with defaults
    mission_state = os.getenv("MISSION_STATE", "0")
    min_rr = os.getenv("MIN_RR", "1.5")
    max_spread_ratio = os.getenv("MAX_SPREAD_TO_SL_RATIO", "0.20")
    expiry_grace = os.getenv("EXPIRY_GRACE_MS", "30000")

    # Handle signals gracefully
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    adapter = None

    try:
        # Create and start adapter
        adapter = MetaSocketAdapter()
        adapter.start()
        print("✅ MetaSocket adapter started (dual-socket mode)")

        # Start mission state worker if enabled
        if mission_state == "1":
            try:
                from src.metasocket import mission_state_worker

                mission_state_worker.start()
            except Exception as e:
                print(f"⚠️ Mission state worker start failed: {e}")
                # Continue without mission worker

        # Keep daemon running
        while True:
            time.sleep(30)

    except KeyboardInterrupt:
        print("🔄 Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Adapter error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if adapter:
            adapter.stop()
            print("✅ Adapter stopped gracefully")


if __name__ == "__main__":
    main()
