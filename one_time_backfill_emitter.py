#!/usr/bin/env python3
"""
One-Time Backfill Emitter - Achieve Event Bus Parity
Reads remaining JSONL outcomes and emits execution.outcome.v1 events
"""

import json
import logging
import sqlite3
import time
from collections import defaultdict
from datetime import datetime


class OneTimeBackfillEmitter:
    def __init__(self):
        self.setup_logging()
        self.event_bus_db = "/root/HydraX-v2/event_bus/bitten_events.db"
        self.jsonl_files = ["/root/HydraX-v2/dynamic_tracking.jsonl", "/root/HydraX-v2/comprehensive_tracking.jsonl"]

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [BACKFILL] %(levelname)s: %(message)s",
            handlers=[logging.FileHandler("/root/HydraX-v2/backfill_emitter.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def generate_deterministic_trade_id(self, outcome_data):
        """Generate deterministic trade_id for JSONL outcomes"""
        # Try to use existing identifiers
        if outcome_data.get("trade_id"):
            return outcome_data["trade_id"]

        if outcome_data.get("fire_id"):
            return f"fire:{outcome_data['fire_id']}"

        # Fallback: generate from signal data
        signal_id = outcome_data.get("signal_id", "unknown")
        timestamp = outcome_data.get("timestamp", int(time.time()))
        symbol = outcome_data.get("symbol", "UNKNOWN")

        return f"fire:{signal_id}_{timestamp}_{symbol}"

    def get_existing_trade_ids_from_bus(self):
        """Get all existing trade_ids from event bus"""
        existing_ids = set()

        try:
            conn = sqlite3.connect(self.event_bus_db)
            cursor = conn.cursor()

            # Check both data_json and correlation_id fields
            cursor.execute(
                """
                SELECT correlation_id, data_json FROM events
                WHERE event_type = 'execution.outcome.v1'
            """
            )

            for row in cursor.fetchall():
                correlation_id = row[0]
                if correlation_id:
                    existing_ids.add(correlation_id)

                # Also check trade_id from JSON data as fallback
                try:
                    data = json.loads(row[1])
                    trade_id = data.get("trade_id")
                    if trade_id:
                        existing_ids.add(trade_id)
                except Exception as e:
                    self.logger.warning(f"Failed to parse existing event: {e}")

            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to read existing trade IDs: {e}")

        return existing_ids

    def load_jsonl_outcomes(self):
        """Load all outcomes from JSONL files"""
        outcomes = []

        for jsonl_file in self.jsonl_files:
            try:
                with open(jsonl_file, "r") as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            if data.get("outcome") in ["WIN", "LOSS"]:
                                outcomes.append(data)
                        except Exception as e:
                            continue
            except FileNotFoundError:
                self.logger.warning(f"JSONL file not found: {jsonl_file}")

        return outcomes

    def convert_to_event_bus_format(self, jsonl_outcome):
        """Convert JSONL outcome to execution.outcome.v1 format"""
        trade_id = self.generate_deterministic_trade_id(jsonl_outcome)

        # Map JSONL fields to event bus schema
        event_data = {
            "trade_id": trade_id,
            "signal_id": jsonl_outcome.get("signal_id"),
            "fire_id": jsonl_outcome.get("fire_id"),
            "symbol": jsonl_outcome.get("symbol", "UNKNOWN"),
            "direction": jsonl_outcome.get("direction", "UNKNOWN"),
            "result": jsonl_outcome.get("outcome"),  # WIN/LOSS
            "pnl_pips": jsonl_outcome.get("pips_result", 0),
            "entry_price": jsonl_outcome.get("entry_price"),
            "exit_price": jsonl_outcome.get("exit_price"),
            "duration_minutes": jsonl_outcome.get("duration_ms", 0) / 60000 if jsonl_outcome.get("duration_ms") else 0,
            "pattern_type": jsonl_outcome.get("pattern_type", "UNKNOWN"),
            "confidence": jsonl_outcome.get("confidence", 0),
            "source": "jsonl-parity-backfill",
            "schema_version": 1,
        }

        return event_data

    def emit_to_event_bus(self, event_data):
        """Emit outcome event to event bus with idempotency"""
        try:
            conn = sqlite3.connect(self.event_bus_db)
            cursor = conn.cursor()

            current_time = time.time()

            # Use INSERT OR IGNORE for idempotency based on trade_id
            cursor.execute(
                """
                INSERT OR IGNORE INTO events (
                    event_type, timestamp, source, correlation_id, user_id,
                    session_id, data_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "execution.outcome.v1",
                    current_time,
                    "jsonl-parity-backfill",
                    event_data.get("trade_id"),  # Use trade_id as correlation_id for dedup
                    None,  # user_id
                    None,  # session_id
                    json.dumps(event_data),
                    current_time,
                ),
            )

            inserted = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return inserted

        except Exception as e:
            self.logger.error(f"Failed to emit event: {e}")
            return False

    def run_backfill(self):
        """Execute the complete backfill process"""
        self.logger.info("🚀 Starting One-Time Backfill for Event Bus Parity")
        self.logger.info("=" * 60)

        start_time = time.time()

        # Step 1: Get existing trade IDs from event bus
        self.logger.info("📥 Loading existing trade IDs from event bus...")
        existing_ids = self.get_existing_trade_ids_from_bus()
        self.logger.info(f"   Found {len(existing_ids)} existing trade IDs")

        # Step 2: Load all JSONL outcomes
        self.logger.info("📥 Loading outcomes from JSONL files...")
        jsonl_outcomes = self.load_jsonl_outcomes()
        self.logger.info(f"   Found {len(jsonl_outcomes)} JSONL outcomes")

        # Step 3: Filter out existing outcomes
        new_outcomes = []
        duplicate_count = 0

        for outcome in jsonl_outcomes:
            trade_id = self.generate_deterministic_trade_id(outcome)
            if trade_id not in existing_ids:
                new_outcomes.append(outcome)
            else:
                duplicate_count += 1

        self.logger.info(f"📊 Analysis:")
        self.logger.info(f"   Total JSONL outcomes: {len(jsonl_outcomes)}")
        self.logger.info(f"   Already in event bus: {duplicate_count}")
        self.logger.info(f"   Need to backfill: {len(new_outcomes)}")

        if len(new_outcomes) == 0:
            self.logger.info("✅ No backfill needed - already at parity!")
            return {"status": "success", "backfilled": 0, "reason": "already_at_parity"}

        # Step 4: Emit missing outcomes
        self.logger.info(f"📤 Backfilling {len(new_outcomes)} missing outcomes...")

        emitted_count = 0
        failed_count = 0

        for i, outcome in enumerate(new_outcomes):
            try:
                event_data = self.convert_to_event_bus_format(outcome)
                if self.emit_to_event_bus(event_data):
                    emitted_count += 1
                else:
                    failed_count += 1

                # Progress update every 10 events
                if (i + 1) % 10 == 0:
                    self.logger.info(
                        f"   Progress: {i + 1}/{len(new_outcomes)} ({emitted_count} emitted, {failed_count} failed)"
                    )

            except Exception as e:
                self.logger.error(f"Failed to process outcome {i}: {e}")
                failed_count += 1

        # Step 5: Verify final count
        self.logger.info("🔍 Verifying final parity...")
        final_existing_ids = self.get_existing_trade_ids_from_bus()
        final_count = len(final_existing_ids)

        duration = time.time() - start_time

        result = {
            "status": "success" if failed_count == 0 else "partial",
            "jsonl_total": len(jsonl_outcomes),
            "bus_before": len(existing_ids),
            "bus_after": final_count,
            "backfilled": emitted_count,
            "failed": failed_count,
            "duration_seconds": duration,
            "parity_achieved": final_count >= len(jsonl_outcomes),
        }

        self.logger.info("=" * 60)
        self.logger.info(f"🏁 Backfill Complete:")
        self.logger.info(f"   JSONL total: {result['jsonl_total']}")
        self.logger.info(f"   Event bus before: {result['bus_before']}")
        self.logger.info(f"   Event bus after: {result['bus_after']}")
        self.logger.info(f"   Backfilled: {result['backfilled']}")
        self.logger.info(f"   Failed: {result['failed']}")
        self.logger.info(f"   Duration: {duration:.1f}s")

        if result["parity_achieved"]:
            self.logger.info("✅ PARITY ACHIEVED - Event bus matches JSONL count!")
        else:
            self.logger.warning(f"⚠️ Parity not achieved: {final_count} vs {len(jsonl_outcomes)}")

        return result


def main():
    emitter = OneTimeBackfillEmitter()
    result = emitter.run_backfill()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"/root/HydraX-v2/backfill_results_{timestamp}.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    exit(main())
