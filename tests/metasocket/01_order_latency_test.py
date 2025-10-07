#!/usr/bin/env python3
"""
CUTOVER TEST 01: Order Latency Test
Tests that MetaSocket fire commands execute within acceptable latency bounds
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

sys.path.append("/root/HydraX-v2")


def test_order_latency():
    """Test that MetaSocket orders execute within <500ms p95"""
    print("🎯 CUTOVER TEST 01: Order Latency Test")
    print("=" * 50)

    # Verify SOURCE setting
    source = os.getenv("SOURCE", "ea")
    if source not in ["metasocket", "both"]:
        print(f"❌ SKIP: SOURCE={source}, need 'metasocket' or 'both'")
        return False

    print(f"✅ SOURCE={source} - MetaSocket enabled")

    try:
        from adapters.metasocket.adapter import MetaSocketAdapter

        adapter = MetaSocketAdapter()

        # Health check first
        health = adapter.get_health_status()
        print(f"📊 MetaSocket Health: {health['status']}")

        if health["status"] != "OK":
            print(f"❌ FAIL: MetaSocket not healthy - {health}")
            return False

        # Run latency test - 10 test orders
        latencies = []
        print("🚀 Testing order latencies (10 sample orders)...")

        for i in range(10):
            start_time = time.time() * 1000  # ms

            result = adapter.fire_order(
                signal_id=f"LATENCY_TEST_{i}_{int(start_time)}",
                symbol="EURUSD",
                direction="BUY",
                volume=0.01,
                sl_pips=20,
                tp_pips=20,
                idempotency_key=f"test_latency_{i}_{int(start_time)}",
            )

            end_time = time.time() * 1000  # ms
            latency = end_time - start_time
            latencies.append(latency)

            print(f"   Order {i+1}: {latency:.1f}ms - {'✅' if result.get('success') else '❌'}")
            time.sleep(0.1)  # Brief pause between orders

        # Calculate p95
        latencies.sort()
        p95_index = int(0.95 * len(latencies))
        p95_latency = latencies[p95_index]
        avg_latency = sum(latencies) / len(latencies)

        print(f"\n📊 LATENCY RESULTS:")
        print(f"   Average: {avg_latency:.1f}ms")
        print(f"   P95: {p95_latency:.1f}ms")
        print(f"   Max: {max(latencies):.1f}ms")
        print(f"   Min: {min(latencies):.1f}ms")

        # Check p95 requirement
        if p95_latency <= 500:
            print(f"✅ PASS: P95 latency {p95_latency:.1f}ms ≤ 500ms")
            return True
        else:
            print(f"❌ FAIL: P95 latency {p95_latency:.1f}ms > 500ms")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during test - {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_order_latency()
    print(f"\n🎯 TEST 01 RESULT: {'✅ PASS' if success else '❌ FAIL'}")
    sys.exit(0 if success else 1)
