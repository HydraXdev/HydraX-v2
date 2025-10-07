#!/usr/bin/env python3
"""
BITTEN v2.1 - Postgres Event Bus Projector
Date: 2025-09-16
Purpose: Consumes comprehensive_tracking.jsonl events and projects to Postgres trade_facts

Architecture:
- Reads from comprehensive_tracking.jsonl (tail -f mode)
- Idempotent upserts to Postgres using signal_id as trade_id
- Generates XP events for gamification
- Maintains exactly-once semantics with conflict resolution
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add project root to path
sys.path.append("/root/HydraX-v2")

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    print("❌ psycopg not installed. Run: pip install psycopg[binary]")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/root/HydraX-v2/logs/postgres_projector.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class PostgresProjector:
    def __init__(self):
        self.dsn = os.getenv("POSTGRES_DSN", "postgresql://bitten:password@localhost:5432/bitten")
        self.tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
        self.position_file = "/root/HydraX-v2/data/projector_position.txt"
        self.conn = None
        self.processed_count = 0
        self.error_count = 0

        # SQL statements
        self.upsert_sql = """
        INSERT INTO trade_facts
          (trade_id, user_id, account_id, signal_id, fire_id, symbol, pattern, session,
           confidence, direction, entry, exit, sl, tp, rr, pips_net, pnl_ccy, fees_ccy,
           result, closed_reason, ts_open, ts_close, duration_min, source, raw_event, schema_version)
        VALUES
          (%(trade_id)s, %(user_id)s, %(account_id)s, %(signal_id)s, %(fire_id)s, %(symbol)s, %(pattern)s, %(session)s,
           %(confidence)s, %(direction)s, %(entry)s, %(exit)s, %(sl)s, %(tp)s, %(rr)s, %(pips_net)s, %(pnl_ccy)s, %(fees_ccy)s,
           %(result)s, %(closed_reason)s, %(ts_open)s, %(ts_close)s, %(duration_min)s, %(source)s, %(raw_event)s, 1)
        ON CONFLICT (trade_id) DO UPDATE SET
          exit = EXCLUDED.exit,
          rr = EXCLUDED.rr,
          pips_net = EXCLUDED.pips_net,
          pnl_ccy = EXCLUDED.pnl_ccy,
          fees_ccy = EXCLUDED.fees_ccy,
          result = EXCLUDED.result,
          closed_reason = EXCLUDED.closed_reason,
          ts_close = EXCLUDED.ts_close,
          duration_min = EXCLUDED.duration_min,
          raw_event = EXCLUDED.raw_event;
        """

        self.xp_insert_sql = """
        INSERT INTO xp_events (user_id, points, reason, related_trade_id, meta)
        VALUES (%(user_id)s, %(points)s, %(reason)s, %(trade_id)s, %(meta)s)
        ON CONFLICT DO NOTHING;
        """

    def connect(self):
        """Establish database connection with retry logic"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.conn = psycopg.connect(self.dsn, autocommit=True, row_factory=dict_row)
                logger.info(f"✅ Connected to Postgres database")
                return True
            except Exception as e:
                logger.error(f"❌ Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    raise

    def get_user_id_by_telegram(self, telegram_id: str) -> int:
        """Get user_id from telegram_id, create if doesn't exist"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT user_id FROM users WHERE telegram_id = %s", (int(telegram_id),))
                result = cur.fetchone()
                if result:
                    return result["user_id"]

                # Create user if doesn't exist (for future multi-user support)
                cur.execute(
                    """
                    INSERT INTO users (telegram_id, username, status)
                    VALUES (%s, %s, 'active')
                    RETURNING user_id
                """,
                    (int(telegram_id), f"user_{telegram_id}"),
                )

                new_user = cur.fetchone()
                logger.info(f"✅ Created new user {new_user['user_id']} for telegram_id {telegram_id}")
                return new_user["user_id"]

        except Exception as e:
            logger.error(f"❌ Error getting/creating user for telegram_id {telegram_id}: {e}")
            return 1  # Default to user_id 1 for now

    def parse_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse event from comprehensive_tracking.jsonl format to database format"""

        # Map current event format to database schema
        signal_id = event_data.get("signal_id", "")
        trade_id = signal_id  # Use signal_id as trade_id

        # Extract user from signal_id pattern or default to current user
        user_id = self.get_user_id_by_telegram("7176191872")  # Default to current user

        # Parse timestamp
        ts_close = None
        if event_data.get("timestamp"):
            ts_close = datetime.fromtimestamp(event_data["timestamp"])

        # Calculate trade duration (signal creation to outcome)
        duration_min = None
        if signal_id and "_" in signal_id:
            try:
                signal_ts = int(signal_id.split("_")[-1])
                if event_data.get("timestamp"):
                    duration_min = (event_data["timestamp"] - signal_ts) / 60
            except (ValueError, IndexError):
                pass

        # Estimate entry/exit prices for P&L calculation
        # This is simplified - in production you'd get these from the actual trades
        pips_net = float(event_data.get("pips_result", 0))
        symbol = event_data.get("symbol", "")

        # Rough P&L estimation (symbol-dependent pip values)
        pip_values = {
            "USDJPY": 0.01,
            "EURJPY": 0.01,
            "GBPJPY": 0.01,
            "EURUSD": 0.0001,
            "GBPUSD": 0.0001,
            "USDCAD": 0.0001,
            "XAUUSD": 0.01,
            "USDCNH": 0.0001,
        }
        pip_value = pip_values.get(symbol, 0.0001)
        estimated_pnl = pips_net * pip_value * 100000  # Assuming 1 lot trade

        return {
            "trade_id": trade_id,
            "user_id": user_id,
            "account_id": None,  # Will be populated when we have account management
            "signal_id": signal_id,
            "fire_id": None,  # Will be populated if this was an executed trade
            "symbol": event_data.get("symbol"),
            "pattern": event_data.get("pattern_type"),
            "session": None,  # Can be derived from timestamp if needed
            "confidence": float(event_data.get("confidence", 0)),
            "direction": event_data.get("direction"),
            "entry": None,  # Would come from actual trade execution
            "exit": None,  # Would come from actual trade execution
            "sl": None,  # Would come from signal data
            "tp": None,  # Would come from signal data
            "rr": None,  # Would be calculated from SL/TP
            "pips_net": pips_net,
            "pnl_ccy": estimated_pnl,
            "fees_ccy": 0,
            "result": event_data.get("outcome", "").lower(),
            "closed_reason": "tp" if event_data.get("outcome") == "WIN" else "sl",
            "ts_open": None,  # Would come from signal creation time
            "ts_close": ts_close,
            "duration_min": duration_min,
            "source": "event_bus",
            "raw_event": json.dumps(event_data),
        }

    def generate_xp_events(self, trade_data: Dict[str, Any]) -> list:
        """Generate XP events based on trade outcome"""
        xp_events = []

        result = trade_data.get("result", "")
        user_id = trade_data.get("user_id")
        trade_id = trade_data.get("trade_id")

        if result == "win":
            xp_events.append(
                {
                    "user_id": user_id,
                    "points": 10,
                    "reason": "trade_win",
                    "trade_id": trade_id,
                    "meta": json.dumps({"pattern": trade_data.get("pattern"), "symbol": trade_data.get("symbol")}),
                }
            )
        elif result == "be":
            xp_events.append(
                {
                    "user_id": user_id,
                    "points": 2,
                    "reason": "trade_breakeven",
                    "trade_id": trade_id,
                    "meta": json.dumps({"pattern": trade_data.get("pattern")}),
                }
            )
        # No XP for losses

        return xp_events

    def process_event(self, event_line: str):
        """Process a single event from the tracking file"""
        try:
            event_data = json.loads(event_line.strip())

            # Parse event to database format
            trade_data = self.parse_event(event_data)

            with self.conn.cursor() as cur:
                # Upsert trade fact
                cur.execute(self.upsert_sql, trade_data)

                # Generate XP events
                xp_events = self.generate_xp_events(trade_data)
                for xp_event in xp_events:
                    try:
                        cur.execute(self.xp_insert_sql, xp_event)
                    except Exception as e:
                        # XP events are nice-to-have, don't fail the whole process
                        logger.warning(f"⚠️ XP event creation failed: {e}")

                self.processed_count += 1

                if self.processed_count % 10 == 0:
                    logger.info(f"📊 Processed {self.processed_count} events, errors: {self.error_count}")

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Invalid JSON in event line: {e}")
            self.error_count += 1
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}")
            logger.error(f"Event data: {event_line}")
            self.error_count += 1

    def get_last_position(self) -> int:
        """Get the last processed file position"""
        if os.path.exists(self.position_file):
            try:
                with open(self.position_file, "r") as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                pass
        return 0

    def save_position(self, position: int):
        """Save the current file position"""
        os.makedirs(os.path.dirname(self.position_file), exist_ok=True)
        with open(self.position_file, "w") as f:
            f.write(str(position))

    def tail_file(self):
        """Tail the comprehensive_tracking.jsonl file and process new events"""
        if not os.path.exists(self.tracking_file):
            logger.warning(f"⚠️ Tracking file not found: {self.tracking_file}")
            return

        # Get last position
        last_position = self.get_last_position()
        logger.info(f"📍 Starting from position: {last_position}")

        with open(self.tracking_file, "r") as f:
            # Seek to last position
            f.seek(last_position)

            while True:
                line = f.readline()
                if line:
                    self.process_event(line)
                    # Save position after each successful event
                    self.save_position(f.tell())
                else:
                    # No new data, wait a bit
                    time.sleep(1)

    def backfill_existing_data(self):
        """Backfill existing data from comprehensive_tracking.jsonl"""
        if not os.path.exists(self.tracking_file):
            logger.warning(f"⚠️ No existing tracking file to backfill")
            return

        logger.info("🔄 Starting backfill of existing data...")

        with open(self.tracking_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    self.process_event(line)

                if line_num % 50 == 0:
                    logger.info(f"📊 Backfilled {line_num} events...")

        logger.info(f"✅ Backfill complete. Processed {self.processed_count} events total")

    def run(self, backfill: bool = False):
        """Main run loop"""
        logger.info("🚀 Starting Postgres Projector Service")

        # Connect to database
        self.connect()

        if backfill:
            self.backfill_existing_data()
            # Reset position after backfill
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, "r") as f:
                    f.seek(0, 2)  # Seek to end
                    self.save_position(f.tell())

        logger.info("👀 Starting real-time event processing...")

        try:
            self.tail_file()
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()
                logger.info("📡 Database connection closed")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="BITTEN Postgres Event Projector")
    parser.add_argument(
        "--backfill", action="store_true", help="Backfill existing data before starting real-time processing"
    )
    parser.add_argument("--dsn", help="Postgres DSN override")

    args = parser.parse_args()

    if args.dsn:
        os.environ["POSTGRES_DSN"] = args.dsn

    projector = PostgresProjector()
    projector.run(backfill=args.backfill)


if __name__ == "__main__":
    main()
