#!/usr/bin/env python3
"""
Mission Session Cleanup Daemon
Removes expired mission sessions and idempotency cache entries
"""

import logging
import signal
import sqlite3
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SessionCleanupDaemon:
    """Daemon to clean up expired mission sessions and idempotency cache"""

    def __init__(self, db_path: str = "/root/HydraX-v2/bitten.db"):
        self.db_path = db_path
        self.running = True

    def cleanup_expired_sessions(self):
        """Remove expired mission sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = int(time.time())

            # Delete expired sessions
            cursor.execute(
                """
                DELETE FROM mission_sessions
                WHERE expires_at < ? AND status = 'PENDING'
            """,
                (now,),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"✅ Cleaned up {deleted_count} expired mission sessions")

            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error cleaning up mission sessions: {e}")
            return 0

    def cleanup_expired_idempotency(self):
        """Remove expired idempotency cache entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = int(time.time())

            # Delete expired cache entries
            cursor.execute(
                """
                DELETE FROM idempotency_cache
                WHERE expires_at < ?
            """,
                (now,),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"✅ Cleaned up {deleted_count} expired idempotency entries")

            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error cleaning up idempotency cache: {e}")
            return 0

    def get_stats(self):
        """Get statistics about sessions and cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Mission sessions stats
            cursor.execute("SELECT COUNT(*), status FROM mission_sessions GROUP BY status")
            session_stats = dict(cursor.fetchall())

            # Idempotency cache stats
            cursor.execute("SELECT COUNT(*) FROM idempotency_cache WHERE expires_at > ?", (int(time.time()),))
            active_cache = cursor.fetchone()[0]

            conn.close()

            return {"sessions": session_stats, "active_cache_entries": active_cache}

        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

    def run(self, interval_seconds: int = 300):
        """Run cleanup daemon at specified interval"""
        logger.info(f"🚀 Session cleanup daemon started (interval: {interval_seconds}s)")

        # Signal handler for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("📥 Received shutdown signal")
            self.running = False

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        while self.running:
            try:
                # Log stats before cleanup
                stats = self.get_stats()
                logger.info(f"📊 Current stats: {stats}")

                # Run cleanup
                sessions_cleaned = self.cleanup_expired_sessions()
                cache_cleaned = self.cleanup_expired_idempotency()

                # Log summary
                total_cleaned = sessions_cleaned + cache_cleaned
                if total_cleaned > 0:
                    logger.info(f"🧹 Cleanup complete: {sessions_cleaned} sessions, {cache_cleaned} cache entries")

                # Sleep for interval
                time.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

        logger.info("👋 Session cleanup daemon stopped")


def main():
    """Main entry point"""
    daemon = SessionCleanupDaemon()

    # Run every 5 minutes (300 seconds)
    daemon.run(interval_seconds=300)


if __name__ == "__main__":
    main()
