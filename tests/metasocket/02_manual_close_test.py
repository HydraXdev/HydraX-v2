#!/usr/bin/env python3
"""
CUTOVER TEST 02: Manual Close Test
Tests that MetaSocket can manually close positions via close_ticket()
"""

import os
import sys
import time
import json
from datetime import datetime

sys.path.append('/root/HydraX-v2')

def test_manual_close():
    """Test that MetaSocket can close positions manually"""
    print("🎯 CUTOVER TEST 02: Manual Close Test")
    print("=" * 50)

    # Verify SOURCE setting
    source = os.getenv('SOURCE', 'ea')
    if source not in ['metasocket', 'both']:
        print(f"❌ SKIP: SOURCE={source}, need 'metasocket' or 'both'")
        return False

    print(f"✅ SOURCE={source} - MetaSocket enabled")

    try:
        from adapters.metasocket.adapter import MetaSocketAdapter
        adapter = MetaSocketAdapter()

        # Health check first
        health = adapter.get_health_status()
        print(f"📊 MetaSocket Health: {health['status']}")

        if health['status'] != 'OK':
            print(f"❌ FAIL: MetaSocket not healthy - {health}")
            return False

        # Step 1: Open a test position
        timestamp = int(time.time() * 1000)
        signal_id = f"CLOSE_TEST_{timestamp}"

        print("🚀 Step 1: Opening test position...")

        open_result = adapter.fire_order(
            signal_id=signal_id,
            symbol="EURUSD",
            direction="BUY",
            volume=0.01,
            sl_pips=50,  # Wide stops for manual close test
            tp_pips=50,
            idempotency_key=f"close_test_{timestamp}"
        )

        if not open_result.get('success'):
            print(f"❌ FAIL: Could not open test position - {open_result}")
            return False

        ticket = open_result.get('ticket')
        if not ticket:
            print(f"❌ FAIL: No ticket returned from open - {open_result}")
            return False

        print(f"✅ Position opened: Ticket #{ticket}")

        # Step 2: Wait briefly then close manually
        print("⏳ Step 2: Waiting 2 seconds then closing manually...")
        time.sleep(2)

        close_result = adapter.close_ticket(
            ticket=ticket,
            comment="MANUAL_CLOSE_TEST"
        )

        if not close_result.get('success'):
            print(f"❌ FAIL: Could not close position - {close_result}")
            return False

        close_price = close_result.get('close_price')
        profit = close_result.get('profit', 0)

        print(f"✅ Position closed manually")
        print(f"   Close Price: {close_price}")
        print(f"   Profit: {profit}")

        # Step 3: Verify position is actually closed
        print("🔍 Step 3: Verifying position is closed...")

        # Check if position shows as closed in adapter status
        time.sleep(1)  # Brief pause for confirmation

        # Try to close again - should fail with "position not found" or similar
        double_close = adapter.close_ticket(ticket=ticket, comment="DOUBLE_CLOSE_TEST")

        if double_close.get('success'):
            print("⚠️  WARNING: Double close succeeded - might indicate issue")
        else:
            print(f"✅ Double close failed as expected: {double_close.get('error', 'Unknown error')}")

        print(f"✅ PASS: Manual close test completed successfully")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception during test - {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_manual_close()
    print(f"\n🎯 TEST 02 RESULT: {'✅ PASS' if success else '❌ FAIL'}")
    sys.exit(0 if success else 1)