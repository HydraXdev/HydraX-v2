#!/usr/bin/env python3
"""
Performance Analytics Event Bus Integration
Publishes analytics events when outcomes are recorded
"""

import json
import logging
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add event_bus to path
sys.path.insert(0, "/root/HydraX-v2")

try:
    from event_bus.producer import EventProducer

    EVENT_BUS_AVAILABLE = True
except ImportError:
    EVENT_BUS_AVAILABLE = False
    print("⚠️ Event Bus not available")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOG = logging.getLogger("ANALYTICS_EVENTS")

TRACKING_FILE = Path("/root/HydraX-v2/comprehensive_tracking.jsonl")


class PerformanceEventPublisher:
    def __init__(self):
        if EVENT_BUS_AVAILABLE:
            self.event_producer = EventProducer()
            LOG.info("✅ Event Bus producer initialized")
        else:
            self.event_producer = None
            LOG.warning("⚠️ Event Bus not available")

        self.last_position = 0
        self.hourly_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "patterns": defaultdict(int)})
        self.last_hourly_publish = datetime.now().replace(minute=0, second=0, microsecond=0)

    def publish_event(self, event_type, data):
        """Publish event to bus"""
        if self.event_producer:
            try:
                self.event_producer.publish(event_type, data)
                LOG.debug(f"📡 Published {event_type}")
            except Exception as e:
                LOG.error(f"Failed to publish {event_type}: {e}")

    def process_new_outcomes(self):
        """Read new outcomes from tracking file and publish events"""
        if not TRACKING_FILE.exists():
            LOG.warning(f"Tracking file not found: {TRACKING_FILE}")
            return

        try:
            with open(TRACKING_FILE, "r") as f:
                # Skip to last position
                f.seek(self.last_position)

                for line in f:
                    try:
                        data = json.loads(line.strip())
                        outcome = data.get("outcome", "PENDING")

                        # Only process completed signals
                        if outcome in ["WIN", "LOSS"]:
                            # Publish individual outcome event
                            self.publish_event(
                                "signal.outcome.recorded",
                                {
                                    "signal_id": data.get("signal_id"),
                                    "pattern": data.get("pattern_type"),
                                    "confidence": data.get("confidence"),
                                    "outcome": outcome,
                                    "lifespan": data.get("lifespan", 0),
                                    "pips": data.get("pips_result", 0),
                                    "symbol": data.get("symbol"),
                                    "session": data.get("session"),
                                    "timestamp": int(time.time()),
                                },
                            )

                            # Aggregate for hourly stats
                            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
                            hour_key = current_hour.isoformat()

                            if outcome == "WIN":
                                self.hourly_stats[hour_key]["wins"] += 1
                            else:
                                self.hourly_stats[hour_key]["losses"] += 1

                            self.hourly_stats[hour_key]["patterns"][data.get("pattern_type", "UNKNOWN")] += 1

                    except json.JSONDecodeError:
                        continue

                # Save current position
                self.last_position = f.tell()

        except Exception as e:
            LOG.error(f"Error processing outcomes: {e}")

    def publish_hourly_summary(self):
        """Publish aggregated hourly stats"""
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

        # Publish if we're in a new hour
        if current_hour > self.last_hourly_publish:
            # Publish stats for last hour
            last_hour_key = self.last_hourly_publish.isoformat()

            if last_hour_key in self.hourly_stats:
                stats = self.hourly_stats[last_hour_key]
                total = stats["wins"] + stats["losses"]
                win_rate = (stats["wins"] / total * 100) if total > 0 else 0

                # Build pattern breakdown
                pattern_breakdown = []
                for pattern, count in stats["patterns"].items():
                    pattern_breakdown.append({"pattern": pattern, "count": count})

                self.publish_event(
                    "analytics.hourly.summary",
                    {
                        "hour": last_hour_key,
                        "total_signals": total,
                        "wins": stats["wins"],
                        "losses": stats["losses"],
                        "win_rate": round(win_rate, 1),
                        "pattern_breakdown": pattern_breakdown,
                        "timestamp": int(time.time()),
                    },
                )

                LOG.info(f"📊 Hourly summary: {total} signals, {win_rate:.1f}% win rate")

            self.last_hourly_publish = current_hour

    def check_pattern_thresholds(self):
        """Check if any patterns dropped below 40% win rate"""
        if not TRACKING_FILE.exists():
            return

        # Calculate pattern performance
        pattern_stats = defaultdict(lambda: {"wins": 0, "losses": 0})

        try:
            with open(TRACKING_FILE, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        pattern = data.get("pattern_type", "UNKNOWN")
                        outcome = data.get("outcome", "PENDING")

                        if outcome == "WIN":
                            pattern_stats[pattern]["wins"] += 1
                        elif outcome == "LOSS":
                            pattern_stats[pattern]["losses"] += 1
                    except json.JSONDecodeError:
                        continue

            # Check thresholds
            for pattern, stats in pattern_stats.items():
                total = stats["wins"] + stats["losses"]
                if total >= 20:  # Only check patterns with enough data
                    win_rate = stats["wins"] / total * 100

                    if win_rate < 40:
                        self.publish_event(
                            "analytics.pattern.threshold",
                            {
                                "pattern": pattern,
                                "win_rate": round(win_rate, 1),
                                "total_signals": total,
                                "wins": stats["wins"],
                                "losses": stats["losses"],
                                "alert_type": "POOR_PERFORMANCE",
                                "threshold": 40,
                                "timestamp": int(time.time()),
                            },
                        )
                        LOG.warning(f"⚠️ Pattern {pattern} below 40% threshold: {win_rate:.1f}%")

        except Exception as e:
            LOG.error(f"Error checking thresholds: {e}")

    def run(self):
        """Main loop"""
        LOG.info("🚀 Starting Performance Event Publisher")

        if not EVENT_BUS_AVAILABLE:
            LOG.error("Event Bus not available, exiting")
            return

        while True:
            try:
                # Process new outcomes
                self.process_new_outcomes()

                # Publish hourly summary (if needed)
                self.publish_hourly_summary()

                # Check pattern thresholds every 15 minutes
                if datetime.now().minute % 15 == 0:
                    self.check_pattern_thresholds()

                # Sleep for 30 seconds
                time.sleep(30)

            except KeyboardInterrupt:
                LOG.info("Shutting down...")
                break
            except Exception as e:
                LOG.error(f"Error in main loop: {e}")
                time.sleep(60)


if __name__ == "__main__":
    publisher = PerformanceEventPublisher()
    publisher.run()
