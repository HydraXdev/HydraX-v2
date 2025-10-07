#!/usr/bin/env python3
"""
BITTEN Account State Manager
Captures and maintains real-time account data from HydraSocket EAs

Handles:
- portfolio_snapshot (initial state on EA startup)
- account_summary (1Hz updates or on-change)
- request_snapshot (on-demand refresh)
- Position sizing calculations based on live balance
"""

import asyncio
import json
import logging
import socket
import sqlite3
import time
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AccountManager")


class AccountStateManager:
    """Manages real-time account states from all connected EAs"""

    def __init__(self, db_path="/root/HydraX-v2/bitten.db"):
        self.accounts = {}  # account_id -> account data
        self.positions = defaultdict(list)  # account_id -> list of positions
        self.db_path = db_path

        # Statistics
        self.stats = {"snapshots_received": 0, "summaries_received": 0, "accounts_tracked": 0, "snapshots_requested": 0}

    def on_portfolio_snapshot(self, event):
        """
        Parse portfolio_snapshot event (sent once at EA startup or on-demand)

        Format:
        {
            "type": "portfolio_snapshot",
            "account_id": "843859",
            "balances": {
                "balance": 10000.00,
                "equity": 10025.00,
                "margin": 108.50,
                "free_margin": 9916.50,
                "margin_level": 9234.56,
                "currency": "USD"
            },
            "positions": [...],
            "orders": [...]
        }
        """
        try:
            account_id = event.get("account_id")
            if not account_id:
                return

            balances = event.get("balances", {})
            positions = event.get("positions", [])

            # Store complete account state
            self.accounts[account_id] = {
                "balance": balances.get("balance", 0.0),
                "equity": balances.get("equity", 0.0),
                "margin": balances.get("margin", 0.0),
                "free_margin": balances.get("free_margin", 0.0),
                "margin_level": balances.get("margin_level", 0.0),
                "currency": balances.get("currency", "USD"),
                "positions": positions,
                "position_count": len(positions),
                "last_update": time.time(),
                "last_snapshot": time.time(),
            }

            self.positions[account_id] = positions
            self.stats["snapshots_received"] += 1
            self.stats["accounts_tracked"] = len(self.accounts)

            # Update database
            self._update_database(account_id, event)

            logger.info(
                f"📸 SNAPSHOT: Account {account_id} | Balance: ${balances.get('balance', 0):.2f} | "
                f"Equity: ${balances.get('equity', 0):.2f} | Positions: {len(positions)}"
            )

        except Exception as e:
            logger.error(f"Error processing portfolio_snapshot: {e}")

    def on_account_summary(self, event):
        """
        Parse account_summary event (sent every second or on-change)

        Format:
        {
            "type": "account_summary",
            "account_id": "843859",
            "balance": 10000.00,
            "equity": 10025.00,
            "margin": 108.50,
            "free_margin": 9916.50,
            "margin_level": 9234.56,
            "currency": "USD",
            "open_positions_count": 1
        }
        """
        try:
            account_id = event.get("account_id")
            if not account_id:
                return

            # If first time seeing this account, request full snapshot
            if account_id not in self.accounts:
                logger.info(f"🔍 New account detected: {account_id} - requesting snapshot")
                # Store basic data for now
                self.accounts[account_id] = {
                    "balance": event.get("balance", 0.0),
                    "equity": event.get("equity", 0.0),
                    "margin": event.get("margin", 0.0),
                    "free_margin": event.get("free_margin", 0.0),
                    "margin_level": event.get("margin_level", 0.0),
                    "currency": event.get("currency", "USD"),
                    "position_count": event.get("open_positions_count", 0),
                    "last_update": time.time(),
                    "needs_snapshot": True,
                }
            else:
                # Update existing account data
                self.accounts[account_id].update(
                    {
                        "balance": event.get("balance", self.accounts[account_id].get("balance", 0.0)),
                        "equity": event.get("equity", self.accounts[account_id].get("equity", 0.0)),
                        "margin": event.get("margin", self.accounts[account_id].get("margin", 0.0)),
                        "free_margin": event.get("free_margin", self.accounts[account_id].get("free_margin", 0.0)),
                        "margin_level": event.get("margin_level", self.accounts[account_id].get("margin_level", 0.0)),
                        "position_count": event.get("open_positions_count", 0),
                        "last_update": time.time(),
                    }
                )

            self.stats["summaries_received"] += 1

            # Log every 60 seconds
            if self.stats["summaries_received"] % 60 == 0:
                logger.info(
                    f"📊 SUMMARY: Account {account_id} | Balance: ${event.get('balance', 0):.2f} | "
                    f"Equity: ${event.get('equity', 0):.2f} | Positions: {event.get('open_positions_count', 0)}"
                )

            # Update database
            self._update_database(account_id, event)

        except Exception as e:
            logger.error(f"Error processing account_summary: {e}")

    def _update_database(self, account_id, event):
        """Update ea_instances table with fresh account data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get balance/equity from event
            if event.get("type") == "portfolio_snapshot":
                balances = event.get("balances", {})
                balance = balances.get("balance", 0.0)
                equity = balances.get("equity", 0.0)
            else:
                balance = event.get("balance", 0.0)
                equity = event.get("equity", 0.0)

            # Update ea_instances
            cursor.execute(
                """
                UPDATE ea_instances
                SET last_balance = ?,
                    last_equity = ?,
                    last_seen = ?
                WHERE account_login = ?
            """,
                (balance, equity, int(time.time()), account_id),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Database update error: {e}")

    def calculate_lot_size(self, account_id, signal, risk_percent=0.01):
        """
        Calculate position size based on account balance and risk

        Args:
            account_id: Account to trade on
            signal: Signal dict with entry, sl, symbol
            risk_percent: Risk as decimal (0.01 = 1%)

        Returns:
            lot_size: Calculated lot size, rounded to 0.01
        """
        if account_id not in self.accounts:
            logger.warning(f"Account {account_id} not found, using minimum lot size")
            return 0.01

        acc = self.accounts[account_id]
        balance = acc.get("balance", 1000.0)

        # Risk amount in account currency
        risk_amount = balance * risk_percent

        # Calculate SL distance in pips
        entry = signal.get("entry", 0)
        sl = signal.get("sl", 0)
        symbol = signal.get("symbol", "EURUSD")

        if entry == 0 or sl == 0:
            logger.warning("Invalid entry/sl prices, using minimum lot size")
            return 0.01

        sl_distance_price = abs(entry - sl)

        # Determine pip size for symbol
        if "JPY" in symbol:
            pip_size = 0.01  # JPY pairs: 0.01 = 1 pip
        elif "XAU" in symbol or "GOLD" in symbol:
            pip_size = 0.1  # Gold: $0.10 = 1 pip
        elif "XAG" in symbol or "SILVER" in symbol:
            pip_size = 0.001  # Silver: $0.001 = 1 pip
        else:
            pip_size = 0.0001  # Standard forex: 0.0001 = 1 pip

        sl_distance_pips = sl_distance_price / pip_size

        if sl_distance_pips == 0:
            logger.warning("Zero pip SL distance, using minimum lot size")
            return 0.01

        # Standard lot pip value (simplified)
        # For 1.0 lot: 1 pip = $10 for standard pairs
        # Adjust for JPY pairs and metals
        if "JPY" in symbol:
            pip_value_per_lot = 10.0  # $10 per pip for 1.0 lot
        elif "XAU" in symbol:
            pip_value_per_lot = 10.0  # $10 per pip for 1.0 lot gold
        else:
            pip_value_per_lot = 10.0  # Standard

        # Calculate lot size
        # risk_amount = lot_size × sl_distance_pips × pip_value_per_lot
        # lot_size = risk_amount / (sl_distance_pips × pip_value_per_lot)
        lot_size = risk_amount / (sl_distance_pips * pip_value_per_lot)

        # Round to 0.01 (broker standard)
        lot_size = round(lot_size, 2)

        # Clamp to reasonable range
        lot_size = max(0.01, min(lot_size, 10.0))

        logger.info(
            f"💰 Position Size: {account_id} | Risk ${risk_amount:.2f} ({risk_percent*100}%) | "
            f"SL {sl_distance_pips:.1f} pips | Lot: {lot_size}"
        )

        return lot_size

    def get_account(self, account_id):
        """Get account data for specific account"""
        return self.accounts.get(account_id)

    def get_all_accounts(self):
        """Get all tracked accounts"""
        return self.accounts.copy()

    def get_stats(self):
        """Get manager statistics"""
        return self.stats.copy()


def send_snapshot_request(account_id, host="127.0.0.1", port=5555):
    """
    Request fresh snapshot from EA via command port

    Returns True if command sent successfully
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.settimeout(5.0)

        command = {"type": "request_snapshot", "request_ref": f"snapshot-{account_id}-{int(time.time())}"}

        payload = json.dumps(command) + "\n"
        sock.send(payload.encode("utf-8"))

        logger.info(f"📡 Sent snapshot request to account {account_id}")
        sock.close()
        return True

    except Exception as e:
        logger.error(f"Failed to send snapshot request: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    manager = AccountStateManager()

    # Simulate events from EA
    test_snapshot = {
        "type": "portfolio_snapshot",
        "account_id": "843859",
        "balances": {
            "balance": 10000.00,
            "equity": 10125.00,
            "margin": 250.00,
            "free_margin": 9875.00,
            "margin_level": 4050.00,
            "currency": "USD",
        },
        "positions": [{"ticket": 123456, "symbol": "EURUSD", "side": "buy", "volume": 0.10}],
    }

    test_summary = {
        "type": "account_summary",
        "account_id": "843859",
        "balance": 10000.00,
        "equity": 10150.00,
        "margin": 250.00,
        "free_margin": 9900.00,
        "margin_level": 4060.00,
        "currency": "USD",
        "open_positions_count": 1,
    }

    # Process events
    manager.on_portfolio_snapshot(test_snapshot)
    manager.on_account_summary(test_summary)

    # Test position sizing
    test_signal = {"entry": 1.09000, "sl": 1.08900, "symbol": "EURUSD"}

    lot_size = manager.calculate_lot_size("843859", test_signal, risk_percent=0.01)
    print(f"\n✅ Calculated lot size: {lot_size} (1% risk)")

    # Show stats
    print(f"\n📊 Manager Stats: {manager.get_stats()}")
