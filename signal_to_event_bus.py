#!/usr/bin/env python3
"""
Signal to Event Bus Bridge
Subscribes to Elite Guard signals on ZMQ 5557 and publishes to Event Bus
"""

import json
import logging
import sqlite3
import time
from datetime import datetime

import zmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SIG→EVENT] %(message)s")
logger = logging.getLogger("SIG_TO_EVENT")


class SignalToEventBridge:
    def __init__(self):
        # ZMQ setup - subscribe to Elite Guard signals
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5557")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

        # Event bus database
        self.event_db = "/root/HydraX-v2/event_bus/bitten_events.db"
        self.main_db = "/root/HydraX-v2/bitten.db"

        # Initialize event bus tables if needed
        self._init_event_bus()

        logger.info("✅ Signal→Event Bus bridge initialized")
        logger.info("   Listening: ZMQ port 5557 (Elite Guard signals)")
        logger.info("   Publishing: Event Bus database")

    def _init_event_bus(self):
        """Ensure event bus tables exist"""
        try:
            conn = sqlite3.connect(self.event_db)
            c = conn.cursor()

            # Create events table if not exists
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """
            )

            # Create index for fast queries
            c.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_type_timestamp
                ON events(event_type, timestamp)
            """
            )

            conn.commit()
            conn.close()
            logger.info("✅ Event bus tables ready")
        except Exception as e:
            logger.error(f"❌ Event bus init error: {e}")

    def publish_signal_event(self, signal_data: dict):
        """Publish signal.generated.v1 event to event bus"""
        try:
            # Extract signal details
            signal_id = signal_data.get("signal_id", "unknown")

            # Create event
            event = {
                "event_type": "signal.generated.v1",
                "event_data": json.dumps(
                    {
                        "signal_id": signal_id,
                        "symbol": signal_data.get("symbol", signal_data.get("pair")),
                        "pattern_type": signal_data.get("pattern_type", signal_data.get("pattern")),
                        "direction": signal_data.get("direction"),
                        "confidence": signal_data.get("confidence"),
                        "entry_price": signal_data.get("entry_price"),
                        "stop_loss": signal_data.get("stop_loss"),
                        "take_profit": signal_data.get("take_profit"),
                        "signal_class": signal_data.get("signal_class"),
                        "timeframe": signal_data.get("timeframe", "M5"),
                        "expires_at": signal_data.get("expires_at"),
                        "created_at": signal_data.get("created_at", int(time.time())),
                    }
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Insert into event bus
            conn = sqlite3.connect(self.event_db)
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO events (event_type, event_data, timestamp)
                VALUES (?, ?, ?)
            """,
                (event["event_type"], event["event_data"], event["timestamp"]),
            )
            conn.commit()
            conn.close()

            logger.info(f"✅ Published signal event: {signal_id} ({signal_data.get('symbol')}) to Event Bus")

            # Also insert to main DB signals table
            self._insert_to_signals_db(signal_data)

        except Exception as e:
            logger.error(f"❌ Error publishing signal event: {e}")

    def _insert_to_signals_db(self, signal_data: dict):
        """Insert signal to main signals table for backward compatibility"""
        try:
            conn = sqlite3.connect(self.main_db)
            c = conn.cursor()

            c.execute(
                """
                INSERT OR IGNORE INTO signals (
                    signal_id, symbol, direction, entry_price,
                    stop_pips, target_pips, confidence, pattern_type,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    signal_data.get("signal_id"),
                    signal_data.get("symbol", signal_data.get("pair")),
                    signal_data.get("direction"),
                    signal_data.get("entry_price"),
                    signal_data.get("stop_pips", 20),
                    signal_data.get("target_pips", 30),
                    signal_data.get("confidence"),
                    signal_data.get("pattern_type", signal_data.get("pattern")),
                    signal_data.get("created_at", int(time.time())),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"⚠️ Error inserting to signals DB: {e}")

    def run(self):
        """Main event loop"""
        logger.info("🚀 Bridge running - listening for signals...")

        while True:
            try:
                # Receive signal from ZMQ
                message = self.subscriber.recv_string(flags=zmq.NOBLOCK)

                # Parse signal data
                if message.startswith("ELITE_GUARD_SIGNAL "):
                    signal_json = message.replace("ELITE_GUARD_SIGNAL ", "")
                    signal_data = json.loads(signal_json)

                    logger.info(f"📡 Received signal: {signal_data.get('signal_id')} - {signal_data.get('symbol')}")

                    # Publish to event bus
                    self.publish_signal_event(signal_data)

            except zmq.Again:
                # No message available
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                time.sleep(1)


if __name__ == "__main__":
    bridge = SignalToEventBridge()
    bridge.run()
