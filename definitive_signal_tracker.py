#!/usr/bin/env python3
"""
DEFINITIVE SIGNAL TRACKER - THE ONLY ONE
Tracks EVERY signal from database to TP/SL completion
100% accountability - NO timeouts, NO fake data, NO duplicates
"""

import sys

sys.path.append("/root/HydraX-v2")

import json
import logging
import sqlite3
import time
from collections import defaultdict
from datetime import datetime

import zmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class DefinitiveSignalTracker:
    def __init__(self):
        self.context = zmq.Context()

        # Subscribe to market data for price updates
        self.market_socket = self.context.socket(zmq.SUB)
        self.market_socket.connect("tcp://localhost:5560")
        self.market_socket.setsockopt(zmq.SUBSCRIBE, b"")

        # Database connection
        self.db_path = "/root/HydraX-v2/bitten.db"

        # Current prices for each symbol
        self.current_prices = {}

        # Tracking file (append-only JSONL)
        self.tracking_file = "/root/HydraX-v2/signal_tracking.jsonl"

        # Load pending signals from database on startup
        self.pending_signals = {}
        self._load_pending_signals()

        logger.info("🎯 DEFINITIVE SIGNAL TRACKER - 100% Accountability Mode")
        logger.info(f"📊 Loaded {len(self.pending_signals)} pending signals to track")

    def _load_pending_signals(self):
        """Load all signals from database that need tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all signals without outcomes (or with PENDING outcome)
        cursor.execute(
            """
            SELECT
                signal_id,
                symbol,
                direction,
                entry_price,
                stop_pips,
                target_pips,
                confidence,
                pattern_type,
                created_at
            FROM signals
            WHERE outcome IS NULL OR outcome = 'PENDING'
            ORDER BY created_at DESC
        """
        )

        for row in cursor.fetchall():
            signal_id = row[0]
            self.pending_signals[signal_id] = {
                "signal_id": signal_id,
                "symbol": row[1],
                "direction": row[2],
                "entry_price": float(row[3]),
                "stop_pips": float(row[4]),
                "target_pips": float(row[5]),
                "confidence": float(row[6]),
                "pattern_type": row[7],
                "created_at": row[8],
                "start_time": time.time(),
            }

        conn.close()

    def _calculate_pip_value(self, symbol):
        """Calculate pip value based on symbol type"""
        if "JPY" in symbol:
            return 0.01  # JPY pairs use 2 decimal places
        elif symbol in ["XAUUSD", "XAGUSD", "BTCUSD"]:
            return 0.1  # Metals/crypto
        else:
            return 0.0001  # Standard forex pairs

    def process_market_data(self):
        """Process real-time market data and update prices"""
        message_count = 0

        while True:
            try:
                if self.market_socket.poll(1000):
                    message = self.market_socket.recv_string(zmq.NOBLOCK)
                    message_count += 1

                    try:
                        tick_data = json.loads(message)
                        if tick_data.get("type", "").upper() == "TICK":
                            symbol = tick_data.get("symbol")
                            bid = float(tick_data.get("bid", 0))
                            ask = float(tick_data.get("ask", 0))

                            if symbol and bid > 0 and ask > 0:
                                self.current_prices[symbol] = {"bid": bid, "ask": ask, "timestamp": time.time()}

                                # Check if this price update triggers any outcomes
                                self._check_signal_outcomes(symbol, bid, ask)
                    except:
                        continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Market data error: {e}")
                time.sleep(1)

    def _check_signal_outcomes(self, symbol, bid, ask):
        """Check if any pending signals hit TP or SL"""
        to_remove = []

        for signal_id, signal in list(self.pending_signals.items()):
            if signal["symbol"] != symbol:
                continue

            direction = signal["direction"].upper()
            entry = signal["entry_price"]
            stop_pips = signal["stop_pips"]
            target_pips = signal["target_pips"]

            # Calculate pip value for this symbol
            pip_value = self._calculate_pip_value(symbol)

            # Calculate SL and TP prices
            if direction == "BUY":
                current_price = bid  # Exit on bid for BUY
                sl_price = entry - (stop_pips * pip_value)
                tp_price = entry + (target_pips * pip_value)

                # Check SL hit
                if current_price <= sl_price:
                    self._record_outcome(signal, "LOSS", current_price, sl_price)
                    to_remove.append(signal_id)
                    continue

                # Check TP hit
                if current_price >= tp_price:
                    self._record_outcome(signal, "WIN", current_price, tp_price)
                    to_remove.append(signal_id)
                    continue

            elif direction == "SELL":
                current_price = ask  # Exit on ask for SELL
                sl_price = entry + (stop_pips * pip_value)
                tp_price = entry - (target_pips * pip_value)

                # Check SL hit
                if current_price >= sl_price:
                    self._record_outcome(signal, "LOSS", current_price, sl_price)
                    to_remove.append(signal_id)
                    continue

                # Check TP hit
                if current_price <= tp_price:
                    self._record_outcome(signal, "WIN", current_price, tp_price)
                    to_remove.append(signal_id)
                    continue

        # Remove completed signals
        for signal_id in to_remove:
            del self.pending_signals[signal_id]

    def _record_outcome(self, signal, outcome, exit_price, target_price):
        """Record signal outcome to database and tracking file"""
        signal_id = signal["signal_id"]
        duration = int(time.time() - signal["start_time"])

        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE signals
            SET outcome = ?,
                exit_price = ?,
                duration_seconds = ?
            WHERE signal_id = ?
        """,
            (outcome, exit_price, duration, signal_id),
        )
        conn.commit()
        conn.close()

        # Write to tracking file (append-only JSONL)
        tracking_data = {
            "signal_id": signal_id,
            "symbol": signal["symbol"],
            "direction": signal["direction"],
            "pattern_type": signal["pattern_type"],
            "confidence": signal["confidence"],
            "entry_price": signal["entry_price"],
            "exit_price": exit_price,
            "outcome": outcome,
            "duration_seconds": duration,
            "created_at": signal["created_at"],
            "completed_at": int(time.time()),
        }

        with open(self.tracking_file, "a") as f:
            f.write(json.dumps(tracking_data) + "\n")

        # Log outcome
        duration_min = duration // 60
        logger.info(
            f"{'✅ WIN' if outcome == 'WIN' else '❌ LOSS'} | {signal['symbol']} {signal['direction']} | {signal['pattern_type']} | {signal['confidence']:.0f}% | {duration_min}min | {signal_id}"
        )

    def monitor_new_signals(self):
        """Monitor database for new signals to track"""
        last_check = time.time()

        while True:
            try:
                current_time = time.time()

                # Check every 5 seconds for new signals
                if current_time - last_check >= 5:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    # Get signals created in last 10 seconds that aren't being tracked
                    cursor.execute(
                        """
                        SELECT
                            signal_id,
                            symbol,
                            direction,
                            entry_price,
                            stop_pips,
                            target_pips,
                            confidence,
                            pattern_type,
                            created_at
                        FROM signals
                        WHERE created_at > ?
                        AND (outcome IS NULL OR outcome = 'PENDING')
                    """,
                        (int(current_time - 10),),
                    )

                    new_count = 0
                    for row in cursor.fetchall():
                        signal_id = row[0]
                        if signal_id not in self.pending_signals:
                            self.pending_signals[signal_id] = {
                                "signal_id": signal_id,
                                "symbol": row[1],
                                "direction": row[2],
                                "entry_price": float(row[3]),
                                "stop_pips": float(row[4]),
                                "target_pips": float(row[5]),
                                "confidence": float(row[6]),
                                "pattern_type": row[7],
                                "created_at": row[8],
                                "start_time": current_time,
                            }
                            new_count += 1

                    if new_count > 0:
                        logger.info(f"📊 Tracking {new_count} new signals | Total pending: {len(self.pending_signals)}")

                    conn.close()
                    last_check = current_time

                time.sleep(1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)

    def run(self):
        """Run the tracker"""
        import threading

        # Start market data processor thread
        market_thread = threading.Thread(target=self.process_market_data, daemon=True)
        market_thread.start()

        # Start new signal monitor thread
        monitor_thread = threading.Thread(target=self.monitor_new_signals, daemon=True)
        monitor_thread.start()

        logger.info("✅ All tracking threads started")
        logger.info("🎯 Tracking signals to TP/SL - NO timeouts, 100% accountability")

        # Main loop
        try:
            while True:
                time.sleep(30)
                if len(self.pending_signals) > 0:
                    symbols = set(s["symbol"] for s in self.pending_signals.values())
                    logger.info(f"📊 Tracking {len(self.pending_signals)} signals across {len(symbols)} symbols")
        except KeyboardInterrupt:
            logger.info("Shutting down tracker...")


if __name__ == "__main__":
    tracker = DefinitiveSignalTracker()
    tracker.run()
