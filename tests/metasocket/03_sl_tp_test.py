#!/usr/bin/env python3
"""
CUTOVER TEST 03: SL/TP Handling Test
Tests that MetaSocket properly handles stop loss and take profit orders
"""

import os
import sys
import time
import json
from datetime import datetime

sys.path.append('/root/HydraX-v2')

def test_sl_tp_handling():
    """Test that MetaSocket handles SL/TP correctly"""
    print("🎯 CUTOVER TEST 03: SL/TP Handling Test")
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

        results = []

        # Test Case 1: Normal SL/TP order
        print("🚀 Test Case 1: Normal SL/TP order...")
        timestamp = int(time.time() * 1000)

        result1 = adapter.fire_order(
            signal_id=f"SLTP_NORMAL_{timestamp}",
            symbol="EURUSD",
            direction="BUY",
            volume=0.01,
            sl_pips=20,
            tp_pips=30,
            idempotency_key=f"sltp_normal_{timestamp}"
        )

        if result1.get('success'):
            print(f"✅ Normal SL/TP order successful: Ticket #{result1.get('ticket')}")
            results.append(True)
        else:
            print(f"❌ Normal SL/TP order failed: {result1}")
            results.append(False)

        time.sleep(0.5)

        # Test Case 2: No SL order (sl_pips=0)
        print("🚀 Test Case 2: No SL order (sl_pips=0)...")
        timestamp = int(time.time() * 1000)

        result2 = adapter.fire_order(
            signal_id=f"SLTP_NOSL_{timestamp}",
            symbol="EURUSD",
            direction="BUY",
            volume=0.01,
            sl_pips=0,  # No SL
            tp_pips=30,
            idempotency_key=f"sltp_nosl_{timestamp}"
        )

        if result2.get('success'):
            print(f"✅ No-SL order successful: Ticket #{result2.get('ticket')}")
            results.append(True)
        else:
            print(f"❌ No-SL order failed: {result2}")
            results.append(False)

        time.sleep(0.5)

        # Test Case 3: No TP order (tp_pips=0)
        print("🚀 Test Case 3: No TP order (tp_pips=0)...")
        timestamp = int(time.time() * 1000)

        result3 = adapter.fire_order(
            signal_id=f"SLTP_NOTP_{timestamp}",
            symbol="EURUSD",
            direction="BUY",
            volume=0.01,
            sl_pips=20,
            tp_pips=0,  # No TP
            idempotency_key=f"sltp_notp_{timestamp}"
        )

        if result3.get('success'):
            print(f"✅ No-TP order successful: Ticket #{result3.get('ticket')}")
            results.append(True)
        else:
            print(f"❌ No-TP order failed: {result3}")
            results.append(False)

        time.sleep(0.5)

        # Test Case 4: Market order (no SL/TP)
        print("🚀 Test Case 4: Market order (no SL/TP)...")
        timestamp = int(time.time() * 1000)

        result4 = adapter.fire_order(
            signal_id=f"SLTP_MARKET_{timestamp}",
            symbol="EURUSD",
            direction="BUY",
            volume=0.01,
            sl_pips=0,  # No SL
            tp_pips=0,  # No TP
            idempotency_key=f"sltp_market_{timestamp}"
        )

        if result4.get('success'):
            print(f"✅ Market order successful: Ticket #{result4.get('ticket')}")
            results.append(True)
        else:
            print(f"❌ Market order failed: {result4}")
            results.append(False)

        # Clean up - close any open positions
        print("🧹 Cleanup: Closing test positions...")
        for result in [result1, result2, result3, result4]:
            if result.get('success') and result.get('ticket'):
                try:
                    adapter.close_ticket(result['ticket'], comment="CLEANUP_SLTP_TEST")
                    time.sleep(0.2)
                except:
                    pass  # Ignore cleanup failures

        # Evaluate results
        passed_tests = sum(results)
        total_tests = len(results)

        print(f"\n📊 SL/TP TEST RESULTS:")
        print(f"   Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if passed_tests == total_tests:
            print(f"✅ PASS: All SL/TP handling tests passed")
            return True
        elif passed_tests >= total_tests * 0.75:  # 75% pass rate minimum
            print(f"⚠️  PARTIAL: {passed_tests}/{total_tests} tests passed (≥75% required)")
            return True
        else:
            print(f"❌ FAIL: Only {passed_tests}/{total_tests} tests passed (<75%)")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during test - {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_sl_tp_handling()
    print(f"\n🎯 TEST 03 RESULT: {'✅ PASS' if success else '❌ FAIL'}")
    sys.exit(0 if success else 1)