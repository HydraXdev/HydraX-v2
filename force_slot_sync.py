#!/usr/bin/env python3
"""
Force Slot Sync - Instantly sync slots with actual open positions
Run this after manually closing trades to immediately update slot counts
"""

import sqlite3
import zmq
import json
import time

def force_sync():
    print("🔄 Force syncing slots with actual positions...")

    # Try to query EA directly for position count
    try:
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://127.0.0.1:5555")
        socket.setsockopt(zmq.RCVTIMEO, 5000)

        # Send position query
        query = {
            "type": "query_positions",
            "target_uuid": "COMMANDER_DEV_001"
        }
        socket.send_json(query)

        # Wait for response
        response = socket.recv_json()
        position_count = len(response.get('positions', []))
        print(f"✅ EA reports {position_count} open positions")

        socket.close()
        context.term()

    except Exception as e:
        print(f"⚠️ Couldn't query EA directly, using fallback method...")
        position_count = None

    # Fallback: Count FILLED trades without outcomes
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fire_id, symbol
        FROM fires
        WHERE user_id = '7176191872'
        AND status = 'FILLED'
        AND created_at > strftime('%s', 'now', '-12 hours')
        ORDER BY created_at DESC
    """)

    filled_trades = cursor.fetchall()
    conn.close()

    # Check which are still open
    open_count = 0
    open_trades = []

    for fire_id, symbol in filled_trades:
        # Skip test trades
        if 'TEST' in fire_id:
            continue

        # Check if closed in tracking
        is_closed = False
        try:
            with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'r') as f:
                for line in f:
                    if fire_id in line and ('"WIN"' in line or '"LOSS"' in line or '"MANUAL_CLOSE"' in line):
                        is_closed = True
                        break
        except:
            pass

        if not is_closed:
            open_count += 1
            open_trades.append((fire_id[:25], symbol))

    # Use EA count if available, otherwise use calculated count
    final_count = position_count if position_count is not None else open_count

    print(f"\n📊 Open positions detected: {final_count}")
    if open_trades and final_count <= 10:
        print("Open trades:")
        for fire_id, symbol in open_trades[:final_count]:
            print(f"  • {fire_id} {symbol}")

    # Update slot count
    fire_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
    fire_cursor = fire_conn.cursor()

    # Ensure we don't exceed max slots
    final_count = min(final_count, 10)

    fire_cursor.execute("""
        UPDATE user_fire_modes
        SET auto_slots_in_use = ?
        WHERE user_id = '7176191872'
    """, (final_count,))

    fire_conn.commit()

    # Get updated status
    fire_cursor.execute("""
        SELECT auto_slots_in_use, max_auto_slots
        FROM user_fire_modes
        WHERE user_id = '7176191872'
    """)

    used, max_slots = fire_cursor.fetchone()
    fire_conn.close()

    print(f"\n✅ Slots updated: {used}/{max_slots} in use")
    print(f"   Available for auto-fire: {max_slots - used} slots")

    # Also reset manual slots to 0 if needed
    if used == 0:
        fire_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
        fire_cursor = fire_conn.cursor()
        fire_cursor.execute("""
            UPDATE user_fire_modes
            SET manual_slots_in_use = 0
            WHERE user_id = '7176191872'
        """)
        fire_conn.commit()
        fire_conn.close()
        print("   Manual slots also reset to 0")

if __name__ == "__main__":
    force_sync()
    print("\n💡 Tip: Run 'python3 /root/HydraX-v2/force_slot_sync.py' anytime after manual closes")