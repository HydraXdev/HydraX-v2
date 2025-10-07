#!/usr/bin/env python3
"""
Proper Fire Execution with Database-First Approach
Creates database record BEFORE sending command to ensure confirmations can be stored
"""
import json
import sqlite3
import time
from collections import OrderedDict

import zmq

DB_PATH = "/root/HydraX-v2/bitten.db"
QUEUE_ADDR = "ipc:///tmp/bitten_cmdqueue"


def execute_fire_proper(
    fire_id: str,
    user_id: str,
    target_uuid: str,
    symbol: str,
    direction: str,
    entry: float = 0,
    sl: float = 0,
    tp: float = 0,
    lot: float = 0.01,
    mission_id: str = None,
):
    """
    Execute fire command with proper database-first approach

    Args:
        fire_id: Unique fire identifier
        user_id: User ID (e.g., '7176191872')
        target_uuid: EA UUID (e.g., 'COMMANDER_DEV_001')
        symbol: Trading pair (e.g., 'EURUSD')
        direction: BUY or SELL
        entry: Entry price (0 = market order)
        sl: Stop loss price
        tp: Take profit price
        lot: Lot size (rounded to 2 decimals)
        mission_id: Optional mission ID for tracking

    Returns:
        dict: Result with success status and details
    """

    # Round lot size to 2 decimals for MT5 compatibility
    lot = round(lot, 2)

    current_time = int(time.time())

    # STEP 1: Create database record FIRST
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO fires (
                fire_id, mission_id, user_id, status,
                symbol, direction, sl, tp, lot,
                target_uuid, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                fire_id,
                mission_id or fire_id,
                user_id,
                "SENT",
                symbol,
                direction,
                sl,
                tp,
                lot,
                target_uuid,
                current_time,
                current_time,
            ),
        )

        conn.commit()
        conn.close()

        print(f"✅ STEP 1: Created database record for {fire_id}")

    except Exception as e:
        print(f"❌ STEP 1 FAILED: Database record creation failed: {e}")
        return {"success": False, "error": f"Database creation failed: {e}", "fire_id": fire_id}

    # STEP 2: Send fire command to IPC queue
    try:
        context = zmq.Context()
        push = context.socket(zmq.PUSH)
        push.connect(QUEUE_ADDR)
        push.setsockopt(zmq.LINGER, 0)

        fire_cmd = OrderedDict(
            [
                ("type", "fire"),
                ("target_uuid", target_uuid),
                ("fire_id", fire_id),
                ("symbol", symbol),
                ("direction", direction),
                ("entry", entry),
                ("sl", sl),
                ("tp", tp),
                ("lot", lot),
            ]
        )

        push.send_json(dict(fire_cmd))
        push.close()
        context.term()

        print(f"✅ STEP 2: Sent fire command to IPC queue")
        print(f"   Symbol: {symbol} {direction}")
        print(f"   Entry: {entry} (0 = market)")
        print(f"   SL: {sl}, TP: {tp}")
        print(f"   Lot: {lot}")

        return {
            "success": True,
            "fire_id": fire_id,
            "status": "SENT",
            "message": "Fire command sent, awaiting EA confirmation",
        }

    except Exception as e:
        print(f"❌ STEP 2 FAILED: Command routing failed: {e}")

        # Update database status to FAILED
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE fires SET status='FAILED', updated_at=? WHERE fire_id=?", (int(time.time()), fire_id)
            )
            conn.commit()
            conn.close()
        except:
            pass

        return {"success": False, "error": f"Command routing failed: {e}", "fire_id": fire_id}


def check_fire_status(fire_id: str):
    """Check the status of a fire command"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT fire_id, status, ticket, price, created_at, updated_at
            FROM fires WHERE fire_id = ?
        """,
            (fire_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "fire_id": row[0],
                "status": row[1],
                "ticket": row[2],
                "price": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "age_seconds": int(time.time()) - row[4],
            }
        else:
            return None

    except Exception as e:
        print(f"Error checking status: {e}")
        return None


if __name__ == "__main__":
    # Test execution
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 execute_fire_proper.py <SYMBOL> [DIRECTION] [SL] [TP]")
        print("Example: python3 execute_fire_proper.py EURUSD BUY 1.05 1.20")
        sys.exit(1)

    symbol = sys.argv[1]
    direction = sys.argv[2] if len(sys.argv) > 2 else "BUY"
    sl = float(sys.argv[3]) if len(sys.argv) > 3 else 1.05
    tp = float(sys.argv[4]) if len(sys.argv) > 4 else 1.20

    fire_id = f"PROPER_TEST_{symbol}_{int(time.time())}"

    print("\n" + "=" * 60)
    print("🔥 PROPER FIRE EXECUTION TEST")
    print("=" * 60)

    result = execute_fire_proper(
        fire_id=fire_id,
        user_id="7176191872",
        target_uuid="COMMANDER_DEV_001",
        symbol=symbol,
        direction=direction,
        sl=sl,
        tp=tp,
        lot=0.01,
    )

    print("\n" + "=" * 60)
    print("RESULT:")
    print(json.dumps(result, indent=2))
    print("=" * 60)

    print("\nWaiting 5 seconds for EA confirmation...")
    time.sleep(5)

    status = check_fire_status(fire_id)
    if status:
        print("\n" + "=" * 60)
        print("FINAL STATUS:")
        print(json.dumps(status, indent=2))
        print("=" * 60)

        if status["ticket"]:
            print(f"\n✅ SUCCESS: Trade executed with ticket #{status['ticket']}")
        elif status["status"] == "SENT":
            print(f"\n⏳ PENDING: Waiting for EA confirmation (age: {status['age_seconds']}s)")
        else:
            print(f"\n❌ FAILED: Status = {status['status']}")
