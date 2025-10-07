#!/usr/bin/env python3
"""
Event Bus Production Policies - Retention, Monitoring & Cleanup
Implements production-ready policies for event bus management
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta


class EventBusProductionPolicies:
    def __init__(self):
        self.setup_logging()
        self.event_bus_db = "/root/HydraX-v2/event_bus/bitten_events.db"
        self.retention_days = 30  # Keep 30 days of events
        self.archive_dir = "/root/HydraX-v2/event_bus_archives"

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [POLICIES] %(levelname)s: %(message)s",
            handlers=[logging.FileHandler("/root/HydraX-v2/event_bus_policies.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def create_archive_directory(self):
        """Ensure archive directory exists"""
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
            self.logger.info(f"Created archive directory: {self.archive_dir}")

    def archive_old_events(self):
        """Archive events older than retention period"""
        self.logger.info("🗄️ Starting event archival process")

        cutoff_time = time.time() - (self.retention_days * 24 * 3600)

        try:
            conn = sqlite3.connect(self.event_bus_db)
            cursor = conn.cursor()

            # Get events to archive
            cursor.execute(
                """
                SELECT * FROM events
                WHERE created_at < ?
                ORDER BY created_at ASC
            """,
                (cutoff_time,),
            )

            old_events = cursor.fetchall()

            if not old_events:
                self.logger.info("   No events to archive")
                conn.close()
                return

            # Create archive file
            archive_date = datetime.now().strftime("%Y%m%d")
            archive_file = f"{self.archive_dir}/events_archive_{archive_date}.jsonl"

            archived_count = 0
            with open(archive_file, "a") as f:
                for event in old_events:
                    # Convert row to dict
                    event_dict = {
                        "id": event[0],
                        "event_type": event[1],
                        "timestamp": event[2],
                        "source": event[3],
                        "correlation_id": event[4],
                        "user_id": event[5],
                        "session_id": event[6],
                        "data_json": event[7],
                        "created_at": event[8],
                        "archived_at": time.time(),
                    }
                    f.write(json.dumps(event_dict) + "\n")
                    archived_count += 1

            # Delete archived events
            cursor.execute("DELETE FROM events WHERE created_at < ?", (cutoff_time,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            self.logger.info(f"   ✅ Archived {archived_count} events to {archive_file}")
            self.logger.info(f"   ✅ Deleted {deleted_count} old events from database")

        except Exception as e:
            self.logger.error(f"   ❌ Archive failed: {e}")

    def vacuum_database(self):
        """Optimize database after cleanup"""
        self.logger.info("🔧 Optimizing database")

        try:
            conn = sqlite3.connect(self.event_bus_db)
            conn.execute("VACUUM")
            conn.close()
            self.logger.info("   ✅ Database optimized")
        except Exception as e:
            self.logger.error(f"   ❌ Database optimization failed: {e}")

    def get_database_metrics(self):
        """Get database health metrics"""
        try:
            conn = sqlite3.connect(self.event_bus_db)
            cursor = conn.cursor()

            # Event counts by type
            cursor.execute(
                """
                SELECT event_type, COUNT(*)
                FROM events
                GROUP BY event_type
                ORDER BY COUNT(*) DESC
            """
            )
            event_counts = cursor.fetchall()

            # Database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]

            # Oldest and newest events
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM events")
            min_time, max_time = cursor.fetchone()

            conn.close()

            return {
                "event_counts": event_counts,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "oldest_event": datetime.fromtimestamp(min_time) if min_time else None,
                "newest_event": datetime.fromtimestamp(max_time) if max_time else None,
                "retention_period_days": self.retention_days,
            }

        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return {}

    def check_schema_violations(self):
        """Check for events that violate schema v1"""
        from event_bus_schema_guard import EventBusSchemaGuard

        self.logger.info("🔍 Checking for schema violations")
        guard = EventBusSchemaGuard()
        violations = []

        try:
            conn = sqlite3.connect(self.event_bus_db)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, event_type, data_json
                FROM events
                WHERE event_type = 'execution.outcome.v1'
                ORDER BY created_at DESC
                LIMIT 100
            """
            )

            checked = 0
            for event_id, event_type, data_json in cursor.fetchall():
                try:
                    data = json.loads(data_json)
                    if not guard.validate_event(event_type, data, strict=False):
                        violations.append(
                            {
                                "event_id": event_id,
                                "event_type": event_type,
                                "violations": guard.validate_execution_outcome_v1(data),
                            }
                        )
                    checked += 1
                except Exception as e:
                    violations.append(
                        {"event_id": event_id, "event_type": event_type, "violations": [f"JSON parse error: {e}"]}
                    )

            conn.close()

            self.logger.info(f"   Checked {checked} recent events")
            if violations:
                self.logger.warning(f"   ⚠️ Found {len(violations)} schema violations")
                for v in violations[:5]:  # Show first 5
                    self.logger.warning(f"     Event {v['event_id']}: {v['violations']}")
            else:
                self.logger.info(f"   ✅ No schema violations found")

            return violations

        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            return []

    def monitor_performance_metrics(self):
        """Monitor key performance indicators"""
        self.logger.info("📊 Collecting performance metrics")

        try:
            conn = sqlite3.connect(self.event_bus_db)
            cursor = conn.cursor()

            # Recent outcome events (last 24h)
            cursor.execute(
                """
                SELECT COUNT(*) FROM events
                WHERE event_type = 'execution.outcome.v1'
                AND created_at > ?
            """,
                (time.time() - 86400,),
            )
            recent_outcomes = cursor.fetchone()[0]

            # Event bus lag (time between oldest unprocessed event and now)
            cursor.execute(
                """
                SELECT MIN(created_at) FROM events
                WHERE event_type = 'execution.outcome.v1'
            """
            )
            oldest_event = cursor.fetchone()[0]
            lag_hours = (time.time() - oldest_event) / 3600 if oldest_event else 0

            # Duplicate detection (same correlation_id)
            cursor.execute(
                """
                SELECT correlation_id, COUNT(*) as cnt
                FROM events
                WHERE correlation_id IS NOT NULL
                GROUP BY correlation_id
                HAVING cnt > 1
                LIMIT 5
            """
            )
            duplicates = cursor.fetchall()

            conn.close()

            metrics = {
                "recent_outcomes_24h": recent_outcomes,
                "event_bus_lag_hours": round(lag_hours, 2),
                "duplicate_correlations": len(duplicates),
                "timestamp": datetime.now().isoformat(),
            }

            # Log key metrics
            self.logger.info(f"   📈 Recent outcomes (24h): {recent_outcomes}")
            self.logger.info(f"   ⏱️ Event bus lag: {lag_hours:.1f} hours")
            self.logger.info(f"   🔄 Duplicate correlations: {len(duplicates)}")

            if duplicates:
                self.logger.warning(f"   ⚠️ Found duplicate correlation IDs: {duplicates}")

            return metrics

        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {e}")
            return {}

    def run_daily_maintenance(self):
        """Run complete daily maintenance routine"""
        self.logger.info("🚀 Starting daily event bus maintenance")
        self.logger.info("=" * 60)

        start_time = time.time()

        # Create archive directory
        self.create_archive_directory()

        # Get metrics before cleanup
        before_metrics = self.get_database_metrics()
        self.logger.info(f"📊 Before cleanup:")
        self.logger.info(f"   Database size: {before_metrics.get('database_size_mb', 0)}MB")
        self.logger.info(f"   Event counts: {before_metrics.get('event_counts', [])}")

        # Archive old events
        self.archive_old_events()

        # Optimize database
        self.vacuum_database()

        # Get metrics after cleanup
        after_metrics = self.get_database_metrics()
        self.logger.info(f"📊 After cleanup:")
        self.logger.info(f"   Database size: {after_metrics.get('database_size_mb', 0)}MB")

        # Check schema compliance
        violations = self.check_schema_violations()

        # Monitor performance
        perf_metrics = self.monitor_performance_metrics()

        duration = time.time() - start_time

        # Save metrics
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = f"{self.archive_dir}/daily_metrics_{timestamp}.json"

        daily_report = {
            "maintenance_duration_seconds": duration,
            "before_metrics": before_metrics,
            "after_metrics": after_metrics,
            "schema_violations": len(violations),
            "performance_metrics": perf_metrics,
            "timestamp": datetime.now().isoformat(),
        }

        with open(metrics_file, "w") as f:
            json.dump(daily_report, f, indent=2, default=str)

        self.logger.info("=" * 60)
        self.logger.info(f"🏁 Daily maintenance complete: {duration:.1f}s")
        self.logger.info(f"📄 Report saved: {metrics_file}")

        return daily_report


def main():
    """Run daily maintenance"""
    policies = EventBusProductionPolicies()
    report = policies.run_daily_maintenance()

    # Exit with error if schema violations found
    return 1 if report.get("schema_violations", 0) > 0 else 0


if __name__ == "__main__":
    exit(main())
