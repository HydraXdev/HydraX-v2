#!/usr/bin/env python3
"""
UNIFIED SIGNAL TRACKER v2.0 - PARALLEL TESTING VERSION

Tracks signals through 3 phases:
1. GENERATION - Signal created by Elite Guard (ZMQ 5557)
2. EXECUTION - Signal fired by user (fires table + ZMQ 5558)
3. OUTCOME - Signal reaches TP/SL (ZMQ 5560 market data)

This version runs IN PARALLEL with definitive_signal_tracker for validation.
DO NOT stop existing tracker until this is proven accurate (1 week minimum).

Output:
- Database: signals table (enhanced schema)
- JSONL: unified_tracking.jsonl (event-based format)
- Metrics: Prometheus /metrics endpoint (TODO)
"""

import sys
sys.path.append("/root/HydraX-v2")

import json
import logging
import sqlite3
import time
import zmq
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UnifiedSignalTracker:
    """
    Unified tracking system that monitors signals through complete lifecycle:
    Generation → Execution → Outcome
    """

    def __init__(self):
        self.context = zmq.Context()

        # ZMQ Subscriptions
        self.signal_sub = self.context.socket(zmq.SUB)  # Port 5557 - Elite Guard signals
        self.signal_sub.connect("tcp://localhost:5557")
        self.signal_sub.setsockopt(zmq.SUBSCRIBE, b"ELITE_GUARD_SIGNAL")

        # PULSE v3 scalper signals (port 5562 - UPDATED from 5559)
        self.pulse_sub = self.context.socket(zmq.SUB)
        self.pulse_sub.connect("tcp://localhost:5562")
        self.pulse_sub.setsockopt(zmq.SUBSCRIBE, b"PULSE_SIGNAL")

        # APEX Sentinel signals (port 5561)
        self.apex_sub = self.context.socket(zmq.SUB)
        self.apex_sub.connect("tcp://localhost:5561")
        self.apex_sub.setsockopt(zmq.SUBSCRIBE, b"APEX_SIGNAL")

        self.confirm_sub = self.context.socket(zmq.SUB)  # Port 5558 - EA confirmations
        self.confirm_sub.connect("tcp://localhost:5558")
        self.confirm_sub.setsockopt(zmq.SUBSCRIBE, b"")

        self.market_sub = self.context.socket(zmq.SUB)  # Port 5570 - Market data (PUB socket)
        self.market_sub.connect("tcp://localhost:5570")
        self.market_sub.setsockopt(zmq.SUBSCRIBE, b"")

        # Database
        self.db_path = "/root/HydraX-v2/bitten.db"
        self._ensure_schema()

        # Output file
        self.tracking_file = "/root/HydraX-v2/unified_tracking.jsonl"

        # In-memory tracking state
        self.pending_signals = {}  # signal_id -> signal_data
        self.current_prices = {}   # symbol -> {bid, ask, timestamp}
        self.fire_to_signal = {}   # fire_id -> signal_id

        # Statistics
        self.stats = {
            "signals_generated": 0,
            "signals_executed": 0,
            "signals_completed": 0,
            "wins": 0,
            "losses": 0,
        }

        logger.info("🎯 UNIFIED SIGNAL TRACKER v2.0 - PARALLEL TESTING MODE")
        logger.info("⚠️  Running alongside definitive_signal_tracker for validation")
        logger.info(f"📊 Output: {self.tracking_file}")

    def _ensure_schema(self):
        """Add unified tracking columns to signals table if not present"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check what columns already exist
        cursor.execute("PRAGMA table_info(signals)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Add new columns if missing (using IF NOT EXISTS equivalent)
        new_columns = {
            "quality_score": "REAL",
            "signal_class": "TEXT",
            "was_executed": "INTEGER DEFAULT 0",
            "execution_method": "TEXT",
            "fire_id": "TEXT",
            "user_id": "TEXT",
            "mt5_ticket": "INTEGER",
            "fill_price": "REAL",
            "slippage_pips": "REAL",
            "actual_pnl_usd": "REAL",
            "theoretical_pnl_pips": "REAL",
            "commission_usd": "REAL",
            "swap_usd": "REAL",
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}")
                    logger.info(f"✅ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        logger.warning(f"⚠️  Could not add column {col_name}: {e}")

        # Create indexes if they don't exist
        indexes = {
            "idx_signals_outcome": "CREATE INDEX IF NOT EXISTS idx_signals_outcome ON signals(outcome)",
            "idx_signals_pattern": "CREATE INDEX IF NOT EXISTS idx_signals_pattern ON signals(pattern_type)",
            "idx_signals_executed": "CREATE INDEX IF NOT EXISTS idx_signals_executed ON signals(was_executed)",
            "idx_signals_user": "CREATE INDEX IF NOT EXISTS idx_signals_user ON signals(user_id)",
            "idx_signals_session": "CREATE INDEX IF NOT EXISTS idx_signals_session ON signals(session)",
        }

        for idx_name, idx_sql in indexes.items():
            try:
                cursor.execute(idx_sql)
            except sqlite3.OperationalError:
                pass  # Index already exists

        conn.commit()
        conn.close()
        logger.info("✅ Database schema verified/updated")

    def _write_event(self, event_type: str, data: Dict):
        """Write event to JSONL tracking file"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }

        try:
            with open(self.tracking_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write event: {e}")

    def _calculate_pip_value(self, symbol: str) -> float:
        """Calculate pip value based on symbol type"""
        if "JPY" in symbol:
            return 0.01
        elif symbol in ["XAUUSD", "XAGUSD", "BTCUSD"]:
            return 0.1
        else:
            return 0.0001

    def handle_signal_generation(self, signal_data: Dict):
        """Phase 1: Track signal generation from Elite Guard"""
        signal_id = signal_data.get("signal_id")
        if not signal_id:
            logger.warning("Signal missing signal_id, skipping")
            return

        # Extract all available fields
        symbol = signal_data.get("symbol")
        direction = signal_data.get("direction")
        pattern_type = signal_data.get("pattern_type", signal_data.get("pattern"))
        confidence = signal_data.get("confidence", 0.0)
        quality_score = signal_data.get("quality_score", confidence)
        signal_class = signal_data.get("signal_class", "UNKNOWN")
        entry_price = signal_data.get("entry_price", signal_data.get("entry"))
        sl_price = signal_data.get("sl_price", signal_data.get("sl"))
        tp_price = signal_data.get("tp_price", signal_data.get("tp"))
        stop_pips = signal_data.get("stop_pips", 0.0)
        target_pips = signal_data.get("target_pips", 0.0)
        risk_reward = signal_data.get("risk_reward", 0.0)
        session = signal_data.get("session", "UNKNOWN")
        created_at = signal_data.get("created_at", int(time.time()))

        # Store in pending signals for outcome tracking
        self.pending_signals[signal_id] = {
            "signal_id": signal_id,
            "symbol": symbol,
            "direction": direction,
            "pattern_type": pattern_type,
            "confidence": confidence,
            "quality_score": quality_score,
            "signal_class": signal_class,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "stop_pips": stop_pips,
            "target_pips": target_pips,
            "risk_reward": risk_reward,
            "session": session,
            "created_at": created_at,
            "start_time": time.time(),
        }

        # Write to database (check if already exists)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT signal_id FROM signals WHERE signal_id = ?", (signal_id,))
        if cursor.fetchone() is None:
            # New signal - insert with unified tracking fields
            cursor.execute("""
                INSERT INTO signals (
                    signal_id, symbol, direction, pattern_type, confidence,
                    quality_score, signal_class, entry_price, sl, tp,
                    stop_pips, target_pips, risk_reward, session, created_at,
                    was_executed, outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
            """, (
                signal_id, symbol, direction, pattern_type, confidence,
                quality_score, signal_class, entry_price, sl_price, tp_price,
                stop_pips, target_pips, risk_reward, session, created_at
            ))
            conn.commit()

        conn.close()

        # Write event to JSONL
        self._write_event("SIGNAL_GENERATION", {
            "signal_id": signal_id,
            "symbol": symbol,
            "direction": direction,
            "pattern_type": pattern_type,
            "signal_class": signal_class,
            "confidence": confidence,
            "quality_score": quality_score,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "stop_pips": stop_pips,
            "target_pips": target_pips,
            "risk_reward": risk_reward,
            "session": session,
            "created_at": created_at,
        })

        self.stats["signals_generated"] += 1
        logger.info(f"📊 GENERATION | {signal_id} | {symbol} {direction} | {pattern_type} | {confidence:.1f}% | {signal_class}")

    def handle_signal_execution(self, fire_data: Dict):
        """Phase 2: Track signal execution from fires table or confirmations"""
        fire_id = fire_data.get("fire_id")
        signal_id = fire_data.get("mission_id", fire_id)  # mission_id often equals signal_id

        if not fire_id or not signal_id:
            return

        # Extract execution details
        user_id = fire_data.get("user_id")
        mt5_ticket = fire_data.get("ticket")
        fill_price = fire_data.get("price")
        status = fire_data.get("status")
        symbol = fire_data.get("symbol")
        direction = fire_data.get("direction")
        lot = fire_data.get("lot")

        # Map fire to signal
        self.fire_to_signal[fire_id] = signal_id

        # Calculate slippage if we have both entry and fill price
        slippage_pips = 0.0
        if signal_id in self.pending_signals and fill_price:
            entry_price = self.pending_signals[signal_id].get("entry_price", 0)
            if entry_price > 0:
                pip_value = self._calculate_pip_value(symbol)
                slippage_pips = abs(fill_price - entry_price) / pip_value

        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE signals
            SET was_executed = 1,
                execution_method = ?,
                fire_id = ?,
                user_id = ?,
                mt5_ticket = ?,
                fill_price = ?,
                slippage_pips = ?
            WHERE signal_id = ?
        """, (
            "AUTO" if user_id else "MANUAL",  # TODO: Better detection
            fire_id,
            user_id,
            mt5_ticket,
            fill_price,
            slippage_pips,
            signal_id
        ))
        conn.commit()
        conn.close()

        # Write event to JSONL
        self._write_event("SIGNAL_EXECUTED", {
            "signal_id": signal_id,
            "fire_id": fire_id,
            "user_id": user_id,
            "execution_method": "AUTO" if user_id else "MANUAL",
            "mt5_ticket": mt5_ticket,
            "fill_price": fill_price,
            "slippage_pips": slippage_pips,
            "lot": lot,
            "executed_at": int(time.time()),
        })

        self.stats["signals_executed"] += 1
        logger.info(f"🔥 EXECUTION | {signal_id} | Fire: {fire_id} | Ticket: {mt5_ticket} | Fill: {fill_price}")

    def handle_signal_outcome(self, signal_id: str, outcome: str, exit_price: float, target_price: float):
        """Phase 3: Track signal outcome (TP/SL hit)"""
        if signal_id not in self.pending_signals:
            return

        signal = self.pending_signals[signal_id]
        duration = int(time.time() - signal["start_time"])

        # Calculate P&L metrics
        pip_value = self._calculate_pip_value(signal["symbol"])
        entry_price = signal.get("entry_price", 0)
        fill_price = signal.get("fill_price", entry_price)  # Use fill if executed, else entry

        # Theoretical P&L (what signal predicted)
        if signal["direction"] == "BUY":
            theoretical_pnl_pips = (target_price - entry_price) / pip_value if outcome == "WIN" else (signal["sl_price"] - entry_price) / pip_value
        else:
            theoretical_pnl_pips = (entry_price - target_price) / pip_value if outcome == "WIN" else (entry_price - signal["sl_price"]) / pip_value

        # Actual P&L (if executed)
        actual_pnl_usd = None
        actual_pnl_pips = None
        if signal.get("was_executed"):
            if signal["direction"] == "BUY":
                actual_pnl_pips = (exit_price - fill_price) / pip_value
            else:
                actual_pnl_pips = (fill_price - exit_price) / pip_value

            # TODO: Calculate actual USD P&L from pips × lot size × contract value

        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE signals
            SET outcome = ?,
                exit_price = ?,
                duration_seconds = ?,
                theoretical_pnl_pips = ?,
                actual_pnl_usd = ?
            WHERE signal_id = ?
        """, (
            outcome,
            exit_price,
            duration,
            theoretical_pnl_pips,
            actual_pnl_usd,
            signal_id
        ))
        conn.commit()
        conn.close()

        # Write event to JSONL
        self._write_event("SIGNAL_OUTCOME", {
            "signal_id": signal_id,
            "outcome": outcome,
            "exit_price": exit_price,
            "exit_reason": "TP_HIT" if outcome == "WIN" else "SL_HIT",
            "duration_seconds": duration,
            "theoretical_pnl_pips": theoretical_pnl_pips,
            "actual_pnl_pips": actual_pnl_pips,
            "actual_pnl_usd": actual_pnl_usd,
            "completed_at": int(time.time()),
        })

        # Update statistics
        self.stats["signals_completed"] += 1
        if outcome == "WIN":
            self.stats["wins"] += 1
        else:
            self.stats["losses"] += 1

        # Remove from pending
        del self.pending_signals[signal_id]

        duration_min = duration // 60
        logger.info(f"{'✅ WIN' if outcome == 'WIN' else '❌ LOSS'} | {signal['symbol']} {signal['direction']} | {signal['pattern_type']} | {duration_min}min | {signal_id}")

    def process_market_data(self):
        """Process market data ticks and check for TP/SL hits"""
        while True:
            try:
                if self.market_sub.poll(1000):
                    message = self.market_sub.recv_string(zmq.NOBLOCK)

                    try:
                        tick_data = json.loads(message)
                        if tick_data.get("type", "").upper() == "TICK":
                            symbol = tick_data.get("symbol")
                            bid = float(tick_data.get("bid", 0))
                            ask = float(tick_data.get("ask", 0))

                            if symbol and bid > 0 and ask > 0:
                                self.current_prices[symbol] = {
                                    "bid": bid,
                                    "ask": ask,
                                    "timestamp": time.time()
                                }

                                # Check outcomes
                                self._check_outcomes(symbol, bid, ask)
                    except:
                        continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Market data error: {e}")
                time.sleep(1)

    def _check_outcomes(self, symbol: str, bid: float, ask: float):
        """Check if any pending signals hit TP or SL"""
        for signal_id, signal in list(self.pending_signals.items()):
            if signal["symbol"] != symbol:
                continue

            direction = signal["direction"].upper()
            sl_price = signal["sl_price"]
            tp_price = signal["tp_price"]

            if direction == "BUY":
                current_price = bid

                # Check SL hit
                if current_price <= sl_price:
                    self.handle_signal_outcome(signal_id, "LOSS", current_price, sl_price)
                    continue

                # Check TP hit
                if current_price >= tp_price:
                    self.handle_signal_outcome(signal_id, "WIN", current_price, tp_price)
                    continue

            elif direction == "SELL":
                current_price = ask

                # Check SL hit
                if current_price >= sl_price:
                    self.handle_signal_outcome(signal_id, "LOSS", current_price, sl_price)
                    continue

                # Check TP hit
                if current_price <= tp_price:
                    self.handle_signal_outcome(signal_id, "WIN", current_price, tp_price)
                    continue

    def process_signals(self):
        """Process signal generation messages from Elite Guard and PULSE"""
        while True:
            try:
                # Check for Elite Guard signals (port 5557)
                if self.signal_sub.poll(100):
                    message = self.signal_sub.recv_string(zmq.NOBLOCK)

                    # Parse "ELITE_GUARD_SIGNAL {json}"
                    if message.startswith("ELITE_GUARD_SIGNAL"):
                        json_str = message[len("ELITE_GUARD_SIGNAL"):].strip()
                        try:
                            signal_data = json.loads(json_str)
                            self.handle_signal_generation(signal_data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse Elite Guard signal: {e}")

                # Check for PULSE signals (port 5562 - v3)
                if self.pulse_sub.poll(100):
                    message = self.pulse_sub.recv_string(zmq.NOBLOCK)

                    # Parse "PULSE_SIGNAL {json}"
                    if message.startswith("PULSE_SIGNAL"):
                        json_str = message[len("PULSE_SIGNAL"):].strip()
                        try:
                            signal_data = json.loads(json_str)
                            # Ensure PULSE signals have signal_class if missing
                            if "signal_class" not in signal_data:
                                signal_data["signal_class"] = "PULSE"
                            if "quality_score" not in signal_data:
                                signal_data["quality_score"] = signal_data.get("confidence", 0.0)
                            self.handle_signal_generation(signal_data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse PULSE signal: {e}")

                # Check for APEX signals (port 5561)
                if self.apex_sub.poll(100):
                    message = self.apex_sub.recv_string(zmq.NOBLOCK)

                    # Parse "APEX_SIGNAL {json}"
                    if message.startswith("APEX_SIGNAL"):
                        json_str = message[len("APEX_SIGNAL"):].strip()
                        try:
                            signal_data = json.loads(json_str)
                            # Ensure APEX signals have signal_class if missing
                            if "signal_class" not in signal_data:
                                signal_data["signal_class"] = "APEX"
                            if "quality_score" not in signal_data:
                                signal_data["quality_score"] = signal_data.get("confidence", 0.0)
                            # APEX uses "direction" not "action" - normalize
                            if "direction" in signal_data and "action" not in signal_data:
                                signal_data["action"] = signal_data["direction"]
                            self.handle_signal_generation(signal_data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse APEX signal: {e}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Signal processing error: {e}")
                time.sleep(1)

    def process_confirmations(self):
        """Process EA confirmations from port 5558"""
        while True:
            try:
                if self.confirm_sub.poll(1000):
                    message = self.confirm_sub.recv_string(zmq.NOBLOCK)

                    try:
                        confirm_data = json.loads(message)
                        event_type = confirm_data.get("type", "").lower()

                        if event_type == "position_opened":
                            # Signal was executed
                            self.handle_signal_execution(confirm_data)
                    except json.JSONDecodeError:
                        continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Confirmation processing error: {e}")
                time.sleep(1)

    def monitor_fires_table(self):
        """Poll fires table for new executions"""
        last_check = time.time()

        while True:
            try:
                current_time = time.time()

                if current_time - last_check >= 5:  # Check every 5 seconds
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    # Get recent fires
                    cursor.execute("""
                        SELECT fire_id, mission_id, user_id, status, ticket, price, symbol, direction, lot
                        FROM fires
                        WHERE created_at > ?
                        AND status = 'FILLED'
                    """, (int(current_time - 10),))

                    for row in cursor.fetchall():
                        fire_data = {
                            "fire_id": row[0],
                            "mission_id": row[1],
                            "user_id": row[2],
                            "status": row[3],
                            "ticket": row[4],
                            "price": row[5],
                            "symbol": row[6],
                            "direction": row[7],
                            "lot": row[8],
                        }

                        # Check if we've already processed this fire
                        if fire_data["fire_id"] not in self.fire_to_signal:
                            self.handle_signal_execution(fire_data)

                    conn.close()
                    last_check = current_time

                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Fires monitoring error: {e}")
                time.sleep(5)

    def print_stats(self):
        """Print statistics periodically"""
        while True:
            try:
                time.sleep(60)  # Every minute

                pending_count = len(self.pending_signals)
                completed = self.stats["signals_completed"]
                win_rate = (self.stats["wins"] / completed * 100) if completed > 0 else 0.0

                logger.info(f"📊 STATS | Generated: {self.stats['signals_generated']} | "
                          f"Executed: {self.stats['signals_executed']} | "
                          f"Completed: {completed} ({self.stats['wins']}W / {self.stats['losses']}L = {win_rate:.1f}%) | "
                          f"Pending: {pending_count}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Stats error: {e}")

    def load_pending_signals(self):
        """Load pending signals from database on startup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT signal_id, symbol, direction, pattern_type, confidence,
                   quality_score, signal_class, entry_price, sl, tp,
                   stop_pips, target_pips, risk_reward, session, created_at
            FROM signals
            WHERE (outcome IS NULL OR outcome = 'PENDING')
              AND entry_price IS NOT NULL
              AND sl IS NOT NULL
              AND tp IS NOT NULL
        """)

        loaded = 0
        for row in cursor.fetchall():
            signal_id = row[0]
            self.pending_signals[signal_id] = {
                "signal_id": signal_id,
                "symbol": row[1],
                "direction": row[2],
                "pattern_type": row[3],
                "confidence": row[4] or 0.0,
                "quality_score": row[5] or row[4] or 0.0,
                "signal_class": row[6] or "UNKNOWN",
                "entry_price": row[7],
                "sl_price": row[8],
                "tp_price": row[9],
                "stop_pips": row[10] or 0.0,
                "target_pips": row[11] or 0.0,
                "risk_reward": row[12] or 0.0,
                "session": row[13] or "UNKNOWN",
                "created_at": row[14],
                "start_time": time.time(),
            }
            loaded += 1

        conn.close()
        logger.info(f"📊 Loaded {loaded} trackable pending signals from database (with entry/sl/tp)")

    def run(self):
        """Run all tracking threads"""
        import threading

        # Load existing pending signals
        self.load_pending_signals()

        # Start worker threads
        threads = [
            threading.Thread(target=self.process_signals, daemon=True, name="SignalProcessor"),
            threading.Thread(target=self.process_confirmations, daemon=True, name="ConfirmProcessor"),
            threading.Thread(target=self.process_market_data, daemon=True, name="MarketProcessor"),
            threading.Thread(target=self.monitor_fires_table, daemon=True, name="FiresMonitor"),
            threading.Thread(target=self.print_stats, daemon=True, name="StatsReporter"),
        ]

        for thread in threads:
            thread.start()
            logger.info(f"✅ Started thread: {thread.name}")

        logger.info("🎯 UNIFIED SIGNAL TRACKER - ALL SYSTEMS OPERATIONAL")
        logger.info("📊 Tracking: Generation (5557) → Execution (5558 + fires) → Outcome (5560)")
        logger.info("⚠️  PARALLEL TESTING MODE: Running alongside definitive_signal_tracker")

        # Main loop
        try:
            while True:
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down unified signal tracker...")


if __name__ == "__main__":
    tracker = UnifiedSignalTracker()
    tracker.run()
