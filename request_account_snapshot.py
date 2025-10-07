#!/usr/bin/env python3
"""
Request fresh account snapshot from EA via HydraSocket router

Sends a request_snapshot command to the EA on the command port (5555)
to trigger an immediate portfolio_snapshot response.

Usage:
    python3 request_account_snapshot.py --account 843859
    python3 request_account_snapshot.py --all  # Request from all connected EAs
"""

import argparse
import json
import logging
import socket
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("SnapshotRequest")


def send_snapshot_request(account_id, host="127.0.0.1", port=5555, timeout=10.0):
    """
    Send request_snapshot command to EA via HydraSocket router

    Args:
        account_id: EA account ID to request snapshot from
        host: HydraSocket router host
        port: HydraSocket command port (5555)
        timeout: Response timeout in seconds

    Returns:
        dict: Response from EA or error
    """
    try:
        # Connect to command router
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.settimeout(timeout)

        # Create request_snapshot command
        request_ref = f"snapshot-{account_id}-{int(time.time())}"
        command = {"type": "request_snapshot", "request_ref": request_ref, "account_id": account_id}

        # Send as JSONL (JSON with newline)
        payload = json.dumps(command) + "\n"
        sock.send(payload.encode("utf-8"))

        logger.info(f"📡 Sent snapshot request to account {account_id}")
        logger.info(f"   Request ref: {request_ref}")

        # Wait for response
        response_data = b""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk

                # Check if we have complete JSON
                if b"\n" in response_data:
                    break
            except socket.timeout:
                break

        sock.close()

        if response_data:
            try:
                # Parse response (may be multiple lines)
                lines = response_data.decode("utf-8").strip().split("\n")
                responses = []

                for line in lines:
                    if line.strip():
                        response = json.loads(line)
                        responses.append(response)

                        # Log response
                        if response.get("type") == "command_result":
                            if response.get("status") == "success":
                                logger.info(f"✅ Command acknowledged: {response.get('info', 'OK')}")
                            else:
                                logger.warning(f"⚠️ Command response: {response.get('message', 'Unknown')}")

                        elif response.get("type") == "portfolio_snapshot":
                            balances = response.get("balances", {})
                            positions = response.get("positions", [])
                            logger.info(f"📸 Snapshot received!")
                            logger.info(f"   Account: {response.get('account_id')}")
                            logger.info(f"   Balance: ${balances.get('balance', 0):,.2f}")
                            logger.info(f"   Equity: ${balances.get('equity', 0):,.2f}")
                            logger.info(f"   Free Margin: ${balances.get('free_margin', 0):,.2f}")
                            logger.info(f"   Positions: {len(positions)}")

                return {"success": True, "responses": responses}

            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON response: {e}")
                logger.error(f"   Raw data: {response_data[:200]}")
                return {"success": False, "error": "Invalid JSON response"}
        else:
            logger.warning(f"⏱️ No response received within {timeout}s")
            logger.info(f"   Note: Snapshot may still be sent on event port (5559)")
            return {"success": False, "error": "Timeout - check event logs"}

    except ConnectionRefusedError:
        logger.error(f"❌ Connection refused to {host}:{port}")
        logger.error(f"   Is HydraSocket router running?")
        return {"success": False, "error": "Connection refused"}

    except Exception as e:
        logger.error(f"❌ Failed to send snapshot request: {e}")
        return {"success": False, "error": str(e)}


def request_all_snapshots(host="127.0.0.1", port=5555):
    """
    Request snapshots from all connected EAs

    Note: This sends a broadcast request. Individual accounts
    can also be queried by checking the ea_instances table.
    """
    import sqlite3

    try:
        # Get all connected EAs from database
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT account_login, target_uuid,
                   (strftime('%s', 'now') - last_seen) as age_seconds
            FROM ea_instances
            ORDER BY last_seen DESC
        """
        )

        accounts = cursor.fetchall()
        conn.close()

        if not accounts:
            logger.warning("⚠️ No EAs found in database")
            return {"success": False, "error": "No EAs found"}

        logger.info(f"📡 Found {len(accounts)} EA(s) in database:")
        results = []

        for account_login, target_uuid, age_seconds in accounts:
            logger.info(f"\n{'='*60}")
            logger.info(f"Account: {account_login} (UUID: {target_uuid})")
            logger.info(f"Last seen: {age_seconds}s ago")

            if age_seconds > 120:
                logger.warning(f"⚠️ EA may be disconnected (last seen {age_seconds}s ago)")

            # Send request
            result = send_snapshot_request(account_login, host, port)
            result["account_id"] = account_login
            result["age_seconds"] = age_seconds
            results.append(result)

            # Small delay between requests
            time.sleep(0.5)

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Sent snapshot requests to {len(accounts)} EA(s)")

        return {"success": True, "results": results}

    except Exception as e:
        logger.error(f"❌ Error querying database: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Request fresh account snapshot from EA")
    parser.add_argument("--account", type=str, help="Account ID to request snapshot from")
    parser.add_argument("--all", action="store_true", help="Request snapshots from all connected EAs")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="HydraSocket router host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5555, help="HydraSocket command port (default: 5555)")
    parser.add_argument("--timeout", type=float, default=10.0, help="Response timeout in seconds (default: 10.0)")

    args = parser.parse_args()

    print("=" * 60)
    print("🔍 HydraSocket Account Snapshot Request Tool")
    print("=" * 60)
    print()

    if args.all:
        # Request from all EAs
        result = request_all_snapshots(args.host, args.port)
    elif args.account:
        # Request from specific account
        result = send_snapshot_request(args.account, args.host, args.port, args.timeout)
    else:
        parser.print_help()
        print()
        print("Example usage:")
        print("  python3 request_account_snapshot.py --account 843859")
        print("  python3 request_account_snapshot.py --all")
        exit(1)

    print()
    if result.get("success"):
        print("✅ Snapshot request completed successfully")
        print()
        print("📊 Next steps:")
        print("  1. Check event logs: tail -f /var/log/hydra-router-5559-6000.log")
        print("  2. Check bridge logs: tail -f /var/log/hydrasocket_account_capture.log")
        print("  3. Verify database: SELECT * FROM ea_instances WHERE account_login='843859';")
    else:
        print(f"❌ Snapshot request failed: {result.get('error')}")
        exit(1)
