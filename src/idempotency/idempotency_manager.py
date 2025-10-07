#!/usr/bin/env python3
"""
Idempotency Manager
Prevents duplicate order execution with request deduplication
"""

import sqlite3
import time
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class IdempotencyManager:
    """Manages idempotency cache for fire requests"""

    def __init__(self, db_path: str = '/root/HydraX-v2/bitten.db', ttl_seconds: int = 600):
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds  # 10 minutes default

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def _make_cache_key(self, user_id: str, mission_session_id: str, client_request_id: str) -> str:
        """Generate cache key"""
        return f"{user_id}:{mission_session_id}:{client_request_id}"

    def check_duplicate(
        self,
        user_id: str,
        mission_session_id: str,
        client_request_id: str
    ) -> Optional[Dict]:
        """
        Check if request is a duplicate

        Args:
            user_id: User ID
            mission_session_id: Mission session ID
            client_request_id: Client-generated request ID

        Returns:
            Cached response dictionary if duplicate, None if new request
        """
        cache_key = self._make_cache_key(user_id, mission_session_id, client_request_id)
        now = int(time.time())

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT response_json, op_id, created_at
                    FROM idempotency_cache
                    WHERE cache_key = ? AND expires_at > ?
                ''', (cache_key, now))

                row = cursor.fetchone()
                if not row:
                    return None

                # Parse cached response
                response_json = json.loads(row[0])
                op_id = row[1]
                created_at = row[2]

                logger.info(f"✅ Found duplicate request: {cache_key}, returning cached response (op_id: {op_id})")

                return {
                    'is_duplicate': True,
                    'cached_response': response_json,
                    'op_id': op_id,
                    'original_timestamp': created_at
                }

        except Exception as e:
            logger.error(f"❌ Error checking idempotency: {e}")
            return None

    def cache_response(
        self,
        user_id: str,
        mission_session_id: str,
        client_request_id: str,
        op_id: str,
        response: Dict
    ) -> bool:
        """
        Cache a response for idempotency

        Args:
            user_id: User ID
            mission_session_id: Mission session ID
            client_request_id: Client-generated request ID
            op_id: Operation ID from execution
            response: Response dictionary to cache

        Returns:
            True if cached successfully, False otherwise
        """
        cache_key = self._make_cache_key(user_id, mission_session_id, client_request_id)
        now = int(time.time())
        expires_at = now + self.ttl_seconds

        try:
            response_json = json.dumps(response)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO idempotency_cache (
                        cache_key, user_id, mission_session_id, client_request_id,
                        op_id, response_json, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cache_key, user_id, mission_session_id, client_request_id,
                    op_id, response_json, now, expires_at
                ))
                conn.commit()

            logger.info(f"✅ Cached response for {cache_key}, expires in {self.ttl_seconds}s")
            return True

        except Exception as e:
            logger.error(f"❌ Error caching response: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries

        Returns:
            Number of entries removed
        """
        try:
            now = int(time.time())
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM idempotency_cache
                    WHERE expires_at < ?
                ''', (now,))

                removed_count = cursor.rowcount
                conn.commit()

            if removed_count > 0:
                logger.info(f"✅ Cleaned up {removed_count} expired idempotency cache entries")

            return removed_count

        except Exception as e:
            logger.error(f"❌ Error cleaning up cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict:
        """
        Get idempotency cache statistics

        Returns:
            Statistics dictionary
        """
        try:
            now = int(time.time())
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total entries
                cursor.execute('SELECT COUNT(*) FROM idempotency_cache')
                total = cursor.fetchone()[0]

                # Active entries
                cursor.execute('SELECT COUNT(*) FROM idempotency_cache WHERE expires_at > ?', (now,))
                active = cursor.fetchone()[0]

                # Expired entries
                expired = total - active

                return {
                    'total_entries': total,
                    'active_entries': active,
                    'expired_entries': expired,
                    'ttl_seconds': self.ttl_seconds
                }

        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {
                'total_entries': 0,
                'active_entries': 0,
                'expired_entries': 0,
                'ttl_seconds': self.ttl_seconds
            }


# Global instance
_idempotency_manager = None

def get_idempotency_manager() -> IdempotencyManager:
    """Get or create global idempotency manager instance"""
    global _idempotency_manager
    if _idempotency_manager is None:
        _idempotency_manager = IdempotencyManager()
    return _idempotency_manager


if __name__ == '__main__':
    # Test
    manager = get_idempotency_manager()

    # Test data
    user_id = "user_test"
    ms_id = "ms_test123"
    request_id = "crid_abc123"
    op_id = "op_xyz789"

    # Test caching
    response = {
        'success': True,
        'opId': op_id,
        'status': 'ACCEPTED'
    }

    cached = manager.cache_response(user_id, ms_id, request_id, op_id, response)
    print(f"Cached: {cached}")

    # Test duplicate check
    duplicate = manager.check_duplicate(user_id, ms_id, request_id)
    print(f"Duplicate check: {duplicate}")

    # Test stats
    stats = manager.get_cache_stats()
    print(f"Cache stats: {stats}")

    # Test cleanup
    removed = manager.cleanup_expired()
    print(f"Cleaned up: {removed} entries")
