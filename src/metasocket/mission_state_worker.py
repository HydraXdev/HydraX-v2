"""
Mission-State Worker for real-time signal viability computation
Subscribes to MetaSocket ticks and computes mission states for active signals
"""

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Callable, Dict, Optional

import zmq

logger = logging.getLogger(__name__)


class MissionStateWorker:
    def __init__(self):
        self.running = False
        self.tick_sub = None
        self.mission_pub = None
        self.db_path = "/root/HydraX-v2/bitten.db"
        self.price_cache = {}  # symbol -> {mid, bid, ask, ts}
        self.callback = None  # Optional callback for in-process consumption

        # Config from env
        self.MIN_RR = float(os.getenv("MIN_RR", "1.5"))
        self.MAX_SPREAD_TO_SL_RATIO = float(os.getenv("MAX_SPREAD_TO_SL_RATIO", "0.20"))
        self.EXPIRY_GRACE_MS = int(os.getenv("EXPIRY_GRACE_MS", "30000"))

        # Pip digits mapping
        self.pip_digits = {
            "USDJPY": 3,
            "EURJPY": 3,
            "GBPJPY": 3,
            "AUDJPY": 3,
            "NZDJPY": 3,
            "CADJPY": 3,
            "CHFJPY": 3,
            "XAUUSD": 2,
            "XAGUSD": 3,
        }

        self.stats = {"signals": 0, "active": 0, "blocked": 0, "expired": 0, "out": 0}
        self.last_log_time = 0

    def pip_value(self, symbol: str) -> float:
        """Get pip value for symbol"""
        digits = self.pip_digits.get(symbol, 5)  # Default 5 for most FX
        return 10 ** (-digits)

    def start(self, callback: Optional[Callable] = None):
        """Start the mission state worker"""
        if self.running:
            return

        self.callback = callback
        self.running = True

        try:
            # Setup ZMQ sockets
            ctx = zmq.Context.instance()

            # Subscribe to MetaSocket ticks
            self.tick_sub = ctx.socket(zmq.SUB)
            self.tick_sub.connect("tcp://127.0.0.1:5562")
            self.tick_sub.setsockopt(zmq.SUBSCRIBE, b"")

            # Publish mission states
            self.mission_pub = ctx.socket(zmq.PUB)
            self.mission_pub.bind("tcp://127.0.0.1:5564")

            print("MISSION: worker started (SUB 5562 → PUB 5564)")

            # Start worker thread
            worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            worker_thread.start()

        except Exception as e:
            logger.error(f"Failed to start mission worker: {e}")
            self.running = False
            raise

    def stop(self):
        """Stop the mission state worker"""
        self.running = False
        if self.tick_sub:
            self.tick_sub.close()
        if self.mission_pub:
            self.mission_pub.close()

    def _worker_loop(self):
        """Main worker loop"""
        last_signal_check = 0
        first_emit = True

        while self.running:
            try:
                # Process incoming ticks (non-blocking)
                try:
                    while True:
                        msg = self.tick_sub.recv_string(zmq.DONTWAIT)
                        self._process_tick_message(msg)
                except zmq.Again:
                    pass

                # Check signals every 2 seconds
                now = time.time()
                if now - last_signal_check >= 2.0:
                    self._process_active_signals(first_emit)
                    last_signal_check = now
                    first_emit = False

                # Log stats every 5 seconds
                if now - self.last_log_time >= 5.0:
                    self._log_stats()
                    self.last_log_time = now

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(1.0)

    def _process_tick_message(self, message: str):
        """Process incoming tick message"""
        try:
            data = json.loads(message)

            if data.get("type") == "TICK" and "symbol" in data:
                symbol = data["symbol"]
                bid = data.get("bid", 0)
                ask = data.get("ask", 0)
                mid = data.get("mid", (bid + ask) / 2)
                ts = data.get("ts_epoch_ms", int(time.time() * 1000))

                self.price_cache[symbol] = {"mid": mid, "bid": bid, "ask": ask, "ts": ts}

        except (json.JSONDecodeError, KeyError):
            pass  # Ignore malformed messages

    def _process_active_signals(self, first_emit: bool):
        """Process active signals and compute mission states"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT signal_id, symbol, direction, entry, sl, tp, created_at, expires_at
                FROM signals
                WHERE outcome IS NULL AND expires_at IS NOT NULL
            """
            )

            signals = cursor.fetchall()
            conn.close()

            self.stats = {"signals": len(signals), "active": 0, "blocked": 0, "expired": 0, "out": 0}

            for signal in signals:
                mission_state = self._compute_mission_state(signal)
                if mission_state:
                    self._publish_mission_state(mission_state, first_emit)

                    # Update stats
                    status = mission_state.get("status", "unknown")
                    if status in self.stats:
                        self.stats[status] += 1

        except Exception as e:
            logger.error(f"Error processing signals: {e}")

    def _compute_mission_state(self, signal) -> Optional[Dict]:
        """Compute mission state for a signal"""
        signal_id, symbol, direction, entry, sl, tp, created_at, expires_at = signal

        # Get latest price
        price_data = self.price_cache.get(symbol)
        if not price_data:
            return None

        now_ms = int(time.time() * 1000)
        price_mid = price_data["mid"]
        bid = price_data["bid"]
        ask = price_data["ask"]

        # Time to expiry
        time_to_expiry_ms = max(0, (expires_at * 1000) - now_ms + self.EXPIRY_GRACE_MS)

        # Zone status (single entry point for now)
        if abs(price_mid - entry) < 1e-9:
            zone_status = "in-zone"
        elif price_mid > entry:
            zone_status = "above"
        else:
            zone_status = "below"

        # Spread in pips
        pip_val = self.pip_value(symbol)
        spread_pips = (ask - bid) / pip_val

        # Current R:R
        if direction == "BUY":
            rr_current = (tp - price_mid) / max(1e-9, price_mid - sl)
        else:  # SELL
            rr_current = (price_mid - tp) / max(1e-9, sl - price_mid)

        # Status determination
        if time_to_expiry_ms == 0:
            status = "expired"
        elif zone_status != "in-zone":
            status = "out-of-bounds"
        else:
            # Check blocking conditions
            sl_dist = abs(price_mid - sl)
            spread_to_sl_ratio = (ask - bid) / max(1e-9, sl_dist)

            if spread_to_sl_ratio > self.MAX_SPREAD_TO_SL_RATIO or rr_current < self.MIN_RR:
                status = "blocked"
            else:
                status = "active"

        return {
            "type": "mission_state",
            "symbol": symbol,
            "signal_id": signal_id,
            "time_to_expiry_ms": int(time_to_expiry_ms),
            "zone_status": zone_status,
            "rr_current": round(rr_current, 3),
            "spread_pips": round(spread_pips, 2),
            "status": status,
        }

    def _publish_mission_state(self, mission_state: Dict, first_emit: bool):
        """Publish mission state"""
        try:
            message = json.dumps(mission_state)
            self.mission_pub.send_string(message)

            if first_emit:
                print("MISSION: first mission_state emitted")

            # Call optional callback
            if self.callback:
                self.callback(mission_state)

        except Exception as e:
            logger.error(f"Error publishing mission state: {e}")

    def _log_stats(self):
        """Log periodic statistics"""
        s = self.stats
        print(
            f"[mission] signals={s['signals']} active={s['active']} blocked={s['blocked']} expired={s['expired']} out={s['out']}"
        )


# Global worker instance
_worker = None


def start(callback: Optional[Callable] = None):
    """Start the mission state worker"""
    global _worker
    if _worker is None:
        _worker = MissionStateWorker()
    _worker.start(callback)


def stop():
    """Stop the mission state worker"""
    global _worker
    if _worker:
        _worker.stop()
        _worker = None
