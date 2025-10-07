#!/usr/bin/env python3
"""
BITTEN Brain - Feed Control Command Sender
Sends feed_control commands to EAs via HydraSocket router

Usage:
    python3 send_feed_control.py --account 843859 --enable
    python3 send_feed_control.py --account 843859 --disable
    python3 send_feed_control.py --providers account1,account2,account3
"""

import argparse
import json
import logging
import socket
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("FeedControl")


def send_feed_control(account_id, enabled, host="127.0.0.1", port=5555):
    """
    Send feed_control command to specific EA

    Args:
        account_id: EA account ID
        enabled: True to enable data feed, False to disable
        host: HydraSocket router host
        port: HydraSocket command port (5555)
    """
    try:
        # Connect to command router
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.settimeout(5.0)

        # Create feed_control command
        command = {
            "type": "feed_control",
            "request_ref": f"feed-{account_id}-{int(time.time())}",
            "enabled": 1 if enabled else 0,
            "account_id": account_id,  # Router uses this for routing
        }

        # Send as JSONL (JSON with newline)
        payload = json.dumps(command) + "\n"
        sock.send(payload.encode("utf-8"))

        logger.info(f"✅ Sent feed_control to {account_id}: {'ENABLED' if enabled else 'DISABLED'}")

        # Wait for command_result confirmation (optional)
        try:
            response = sock.recv(4096).decode("utf-8")
            if response:
                logger.info(f"📥 Response: {response.strip()}")
        except socket.timeout:
            logger.info("⏱️ No immediate response (command sent successfully)")

        sock.close()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send command to {account_id}: {e}")
        return False


def configure_providers(provider_list, host="127.0.0.1", port=5555):
    """
    Configure specific accounts as data providers, disable all others

    Args:
        provider_list: List of account IDs to be providers
    """
    # This would need access to full account list
    # For now, just enable the specified providers
    logger.info(f"📡 Configuring {len(provider_list)} providers...")

    success_count = 0
    for account_id in provider_list:
        if send_feed_control(account_id, enabled=True, host=host, port=port):
            success_count += 1
            time.sleep(0.1)  # Small delay between commands

    logger.info(f"✅ Configured {success_count}/{len(provider_list)} providers")
    return success_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send feed_control commands to EAs")
    parser.add_argument("--account", type=str, help="Single account ID to control")
    parser.add_argument("--enable", action="store_true", help="Enable data feed")
    parser.add_argument("--disable", action="store_true", help="Disable data feed")
    parser.add_argument("--providers", type=str, help="Comma-separated list of provider accounts")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Router host")
    parser.add_argument("--port", type=int, default=5555, help="Router command port")

    args = parser.parse_args()

    if args.providers:
        # Configure multiple providers
        provider_list = [acc.strip() for acc in args.providers.split(",")]
        configure_providers(provider_list, host=args.host, port=args.port)

    elif args.account:
        # Single account control
        if args.enable and args.disable:
            logger.error("❌ Cannot enable and disable simultaneously")
        elif args.enable:
            send_feed_control(args.account, enabled=True, host=args.host, port=args.port)
        elif args.disable:
            send_feed_control(args.account, enabled=False, host=args.host, port=args.port)
        else:
            logger.error("❌ Must specify --enable or --disable")

    else:
        parser.print_help()
