"""
BITTEN v2.0 Analytics Worker Main Service
Background job scheduler for tracking, stats, and Firestore mirroring
"""
import asyncio
import logging
import signal
import sys
import os
import threading
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from services.analytics_worker.config import JOB_SCHEDULES, LOG_LEVEL, LOG_FORMAT
from services.analytics_worker.jobs import (
    OutcomeTracker,
    StatsAggregator,
    FirestoreMirror,
    Reconciliation,
    Reports
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """Simple health check endpoint handler"""
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "healthy", "service": "analytics_worker"})
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP logging
        pass


class AnalyticsWorker:
    """Main analytics worker service with job scheduling"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.outcome_tracker = None
        self.running = False
        self._start_health_server()

    def _start_health_server(self):
        """Start HTTP health check server on port 9094"""
        def run_server():
            try:
                server = HTTPServer(('0.0.0.0', 9094), HealthHandler)
                logger.info("✅ Health check server listening on port 9094")
                server.serve_forever()
            except Exception as e:
                logger.error(f"⚠️  Health server error: {e}")

        health_thread = threading.Thread(target=run_server, daemon=True)
        health_thread.start()

    def _setup_outcome_tracker(self):
        """Setup continuous outcome tracker task"""
        logger.info("Starting Outcome Tracker (continuous ZMQ subscriber)...")
        self.outcome_tracker = OutcomeTracker()

        # Run outcome tracker as a continuous background task
        asyncio.create_task(self.outcome_tracker.run())

    def _setup_stats_aggregator(self):
        """Setup stats aggregator scheduled job"""
        schedule = JOB_SCHEDULES['stats_aggregator']
        logger.info(f"Scheduling Stats Aggregator: {schedule['description']}")

        def run_stats():
            try:
                aggregator = StatsAggregator()
                aggregator.run()
            except Exception as e:
                logger.error(f"Stats aggregator failed: {e}")

        self.scheduler.add_job(
            run_stats,
            trigger=IntervalTrigger(minutes=schedule['minutes']),
            id='stats_aggregator',
            name='Stats Aggregator',
            replace_existing=True
        )

    def _setup_firestore_mirror(self):
        """Setup Firestore mirror scheduled job"""
        schedule = JOB_SCHEDULES['firestore_mirror']
        logger.info(f"Scheduling Firestore Mirror: {schedule['description']}")

        def run_mirror():
            try:
                mirror = FirestoreMirror()
                mirror.run()
            except Exception as e:
                logger.error(f"Firestore mirror failed: {e}")

        self.scheduler.add_job(
            run_mirror,
            trigger=IntervalTrigger(hours=schedule['hours']),
            id='firestore_mirror',
            name='Firestore Mirror',
            replace_existing=True
        )

    def _setup_reconciliation(self):
        """Setup nightly reconciliation job"""
        schedule = JOB_SCHEDULES['reconciliation']
        logger.info(f"Scheduling Reconciliation: {schedule['description']}")

        def run_reconciliation():
            try:
                reconciliation = Reconciliation()
                reconciliation.run()
            except Exception as e:
                logger.error(f"Reconciliation failed: {e}")

        self.scheduler.add_job(
            run_reconciliation,
            trigger=CronTrigger(hour=schedule['hour'], minute=schedule['minute']),
            id='reconciliation',
            name='Nightly Reconciliation',
            replace_existing=True
        )

    def _setup_reports(self):
        """Setup nightly reports job"""
        schedule = JOB_SCHEDULES['reports']
        logger.info(f"Scheduling Reports: {schedule['description']}")

        def run_reports():
            try:
                reports = Reports()
                reports.run()
            except Exception as e:
                logger.error(f"Reports failed: {e}")

        self.scheduler.add_job(
            run_reports,
            trigger=CronTrigger(hour=schedule['hour'], minute=schedule['minute']),
            id='reports',
            name='Nightly Reports',
            replace_existing=True
        )

    async def start(self):
        """Start analytics worker service"""
        logger.info("=" * 70)
        logger.info("BITTEN v2.0 Analytics Worker Starting...")
        logger.info("=" * 70)

        # Setup all jobs
        self._setup_outcome_tracker()
        self._setup_stats_aggregator()
        self._setup_firestore_mirror()
        self._setup_reconciliation()
        self._setup_reports()

        # Start scheduler
        self.scheduler.start()
        self.running = True

        # Print job schedule
        logger.info("\n📅 JOB SCHEDULE:")
        logger.info("-" * 70)
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            logger.info(f"  {job.name:30} → Next run: {next_run}")
        logger.info("-" * 70)

        logger.info("\n✅ Analytics Worker running. Press Ctrl+C to stop.\n")

        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Stop analytics worker service"""
        logger.info("Stopping Analytics Worker...")

        self.running = False

        # Stop outcome tracker
        if self.outcome_tracker:
            await self.outcome_tracker.stop()

        # Stop scheduler
        self.scheduler.shutdown(wait=False)

        logger.info("Analytics Worker stopped")


# Global worker instance
worker = None


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info(f"\nReceived signal {sig}, shutting down...")
    if worker:
        asyncio.create_task(worker.stop())


async def main():
    """Main entry point"""
    global worker

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start worker
    worker = AnalyticsWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")
    finally:
        await worker.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Analytics Worker terminated")
        sys.exit(0)
