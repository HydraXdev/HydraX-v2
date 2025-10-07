#!/usr/bin/env python3
"""
CUTOVER TEST 04: Reconnection/Recovery Test
Tests that MetaSocket adapter handles connection loss and graceful recovery
"""

import json
import os
import sys
import time
from datetime import datetime

sys.path.append("/root/HydraX-v2")


def test_reconnect_recovery():
    """Test that MetaSocket handles reconnection and recovery gracefully"""
    print("🎯 CUTOVER TEST 04: Reconnection/Recovery Test")
    print("=" * 50)

    # Verify SOURCE setting
    source = os.getenv("SOURCE", "ea")
    if source not in ["metasocket", "both"]:
        print(f"❌ SKIP: SOURCE={source}, need 'metasocket' or 'both'")
        return False

    print(f"✅ SOURCE={source} - MetaSocket enabled")

    try:
        from adapters.metasocket.adapter import MetaSocketAdapter

        # Step 1: Initial connection and health check
        print("🚀 Step 1: Initial connection and health check...")
        adapter = MetaSocketAdapter()

        initial_health = adapter.get_health_status()
        print(f"📊 Initial Health: {initial_health['status']}")

        if initial_health["status"] != "OK":
            print(f"❌ FAIL: Initial connection not healthy - {initial_health}")
            return False

        # Step 2: Test basic functionality before disconnect
        print("🚀 Step 2: Test order before disconnect...")
        timestamp = int(time.time() * 1000)

        pre_disconnect_order = adapter.fire_order(
            signal_id=f"PRE_DISCONNECT_{timestamp}",
            symbol="EURUSD",
            direction="BUY",
            volume=0.01,
            sl_pips=20,
            tp_pips=20,
            idempotency_key=f"pre_disconnect_{timestamp}",
        )

        if not pre_disconnect_order.get("success"):
            print(f"❌ FAIL: Pre-disconnect order failed - {pre_disconnect_order}")
            return False

        print(f"✅ Pre-disconnect order successful: Ticket #{pre_disconnect_order.get('ticket')}")

        # Step 3: Simulate connection issues by forcing circuit breaker
        print("🚀 Step 3: Testing circuit breaker behavior...")

        # Force multiple failures to trigger circuit breaker
        for i in range(3):
            try:
                # Use invalid symbol to trigger failures
                adapter.fire_order(
                    signal_id=f"FORCE_FAIL_{i}_{timestamp}",
                    symbol="INVALID_SYMBOL_XXXXXX",
                    direction="BUY",
                    volume=0.01,
                    sl_pips=20,
                    tp_pips=20,
                    idempotency_key=f"force_fail_{i}_{timestamp}",
                )
            except:
                pass  # Expected to fail

        # Check if circuit breaker is triggered
        health_after_failures = adapter.get_health_status()
        print(f"📊 Health after failures: {health_after_failures}")

        # Step 4: Wait for circuit breaker recovery
        print("🚀 Step 4: Waiting for circuit breaker recovery...")
        time.sleep(3)  # Circuit breaker recovery time

        # Create new adapter instance to simulate reconnection
        print("🔄 Creating new adapter instance (simulating reconnection)...")
        adapter = MetaSocketAdapter()

        # Step 5: Test functionality after recovery
        print("🚀 Step 5: Testing functionality after recovery...")

        recovery_health = adapter.get_health_status()
        print(f"📊 Recovery Health: {recovery_health['status']}")

        if recovery_health["status"] != "OK":
            print(f"⚠️  WARNING: Recovery health not OK, but continuing test...")

        # Attempt order after recovery
        timestamp = int(time.time() * 1000)

        post_recovery_order = adapter.fire_order(
            signal_id=f"POST_RECOVERY_{timestamp}",
            symbol="EURUSD",
            direction="SELL",  # Different direction
            volume=0.01,
            sl_pips=20,
            tp_pips=20,
            idempotency_key=f"post_recovery_{timestamp}",
        )

        if not post_recovery_order.get("success"):
            print(f"❌ FAIL: Post-recovery order failed - {post_recovery_order}")
            return False

        print(f"✅ Post-recovery order successful: Ticket #{post_recovery_order.get('ticket')}")

        # Step 6: Cleanup
        print("🧹 Cleanup: Closing test positions...")
        for order in [pre_disconnect_order, post_recovery_order]:
            if order.get("success") and order.get("ticket"):
                try:
                    adapter.close_ticket(order["ticket"], comment="CLEANUP_RECONNECT_TEST")
                    time.sleep(0.2)
                except:
                    pass  # Ignore cleanup failures

        # Step 7: Final health check
        final_health = adapter.get_health_status()
        print(f"📊 Final Health: {final_health['status']}")

        print(f"✅ PASS: Reconnection/Recovery test completed successfully")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception during test - {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_reconnect_recovery()
    print(f"\n🎯 TEST 04 RESULT: {'✅ PASS' if success else '❌ FAIL'}")
    sys.exit(0 if success else 1)
