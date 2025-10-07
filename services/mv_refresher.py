#!/usr/bin/env python3
"""
BITTEN v2.1 - Materialized View Refresher Service
Date: 2025-09-16
Purpose: Automatically refresh materialized views for fast admin queries

Refreshes:
- user_perf_mv (user performance aggregates)
- user_pattern_perf_mv (pattern performance by user)
- user_symbol_perf_mv (symbol performance by user)
- user_best_worst_mv (best/worst performers)
"""

import logging
import os
import signal
import sys
import time
from datetime import datetime

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
    handlers=[logging.FileHandler("/root/HydraX-v2/logs/mv_refresher.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MaterializedViewRefresher:
    def __init__(self):
        self.dsn = os.getenv("POSTGRES_DSN", "postgresql://bitten:bitten_secure_2025@localhost:5432/bitten")
        self.conn = None
        self.refresh_interval = 60  # 60 seconds
        self.running = True

        # Views to refresh in order (dependencies first)
        self.views = ["user_perf_mv", "user_pattern_perf_mv", "user_symbol_perf_mv", "user_best_worst_mv"]

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, shutting down...")
        self.running = False

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

    def refresh_view(self, view_name: str) -> bool:
        """Refresh a single materialized view"""
        try:
            start_time = time.time()

            with self.conn.cursor() as cur:
                # Use CONCURRENTLY for non-blocking refresh (requires unique index)
                cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")

            duration = time.time() - start_time
            logger.info(f"✅ Refreshed {view_name} in {duration:.2f}s")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to refresh {view_name}: {e}")
            return False

    def refresh_all_views(self) -> dict:
        """Refresh all materialized views and return status"""
        results = {}
        total_start = time.time()

        logger.info("🔄 Starting materialized view refresh cycle...")

        for view_name in self.views:
            results[view_name] = self.refresh_view(view_name)

        total_duration = time.time() - total_start
        success_count = sum(1 for success in results.values() if success)

        logger.info(f"📊 Refresh cycle complete: {success_count}/{len(self.views)} views in {total_duration:.2f}s")

        return results

    def get_view_stats(self) -> dict:
        """Get statistics about materialized views"""
        try:
            stats = {}

            with self.conn.cursor() as cur:
                # Get view sizes and last refresh times
                cur.execute(
                    """
                    SELECT
                        schemaname,
                        matviewname,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size,
                        pg_stat_get_last_analyze_time(c.oid) as last_analyzed
                    FROM pg_matviews m
                    LEFT JOIN pg_class c ON c.relname = m.matviewname
                    WHERE schemaname = 'public'
                    ORDER BY matviewname
                """
                )

                for row in cur.fetchall():
                    stats[row["matviewname"]] = {"size": row["size"], "last_analyzed": row["last_analyzed"]}

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting view stats: {e}")
            return {}

    def health_check(self) -> bool:
        """Perform health check on database connection and views"""
        try:
            with self.conn.cursor() as cur:
                # Check each view has data
                for view_name in self.views:
                    cur.execute(f"SELECT COUNT(*) as count FROM {view_name}")
                    result = cur.fetchone()
                    count = result["count"] if result else 0

                    if count == 0:
                        logger.warning(f"⚠️ View {view_name} is empty")
                    else:
                        logger.debug(f"✅ View {view_name} has {count} rows")

            return True

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

    def run_once(self):
        """Run one refresh cycle"""
        if not self.conn:
            self.connect()

        # Perform health check
        if not self.health_check():
            logger.warning("⚠️ Health check failed, attempting to reconnect...")
            self.connect()

        # Refresh all views
        results = self.refresh_all_views()

        # Log view statistics periodically
        if datetime.now().minute % 10 == 0:  # Every 10 minutes
            stats = self.get_view_stats()
            for view_name, view_stats in stats.items():
                logger.info(f"📊 {view_name}: {view_stats['size']}")

        return results

    def run(self):
        """Main run loop"""
        logger.info("🚀 Starting Materialized View Refresher Service")
        logger.info(f"📋 Monitoring {len(self.views)} views with {self.refresh_interval}s interval")

        # Connect to database
        self.connect()

        # Initial refresh
        logger.info("🔄 Performing initial refresh...")
        self.run_once()

        # Main loop
        while self.running:
            try:
                time.sleep(self.refresh_interval)

                if not self.running:
                    break

                self.run_once()

            except KeyboardInterrupt:
                logger.info("🛑 Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                time.sleep(30)  # Wait longer on error

        # Cleanup
        if self.conn:
            self.conn.close()
            logger.info("📡 Database connection closed")

        logger.info("🏁 Materialized View Refresher Service stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="BITTEN Materialized View Refresher")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Refresh interval in seconds (default: 60)")
    parser.add_argument("--dsn", help="Postgres DSN override")

    args = parser.parse_args()

    if args.dsn:
        os.environ["POSTGRES_DSN"] = args.dsn

    refresher = MaterializedViewRefresher()
    refresher.refresh_interval = args.interval

    if args.once:
        refresher.connect()
        results = refresher.run_once()
        success_count = sum(1 for success in results.values() if success)
        print(f"Refreshed {success_count}/{len(results)} views successfully")
        sys.exit(0 if success_count == len(results) else 1)
    else:
        refresher.run()


if __name__ == "__main__":
    main()
