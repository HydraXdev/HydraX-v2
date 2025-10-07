#!/usr/bin/env python3
"""
Mission Session Manager
Handles CRUD operations and lifecycle for mission sessions
"""

import logging
import secrets
import sqlite3
import time
from typing import Dict, List, Optional

import ulid

logger = logging.getLogger(__name__)


class MissionSessionManager:
    """Manages mission session lifecycle and state"""

    def __init__(self, db_path: str = "/root/HydraX-v2/bitten.db"):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def create_session(
        self,
        user_id: str,
        signal_id: str,
        alert_id: int,
        pair: Optional[str] = None,
        timeframe: Optional[str] = None,
        risk_max_usd: Optional[float] = None,
        ttl_seconds: int = 28800,  # 8 hours default (8 * 3600)
    ) -> Dict:
        """
        Create a new mission session

        Args:
            user_id: User identifier
            signal_id: Signal identifier
            alert_id: Alert ID
            pair: Trading pair
            timeframe: Timeframe
            risk_max_usd: Maximum risk in USD
            ttl_seconds: Time to live in seconds

        Returns:
            Mission session data dictionary
        """
        now = int(time.time())
        expires_at = now + ttl_seconds

        # Generate unique IDs
        mission_session_id = f"ms_{ulid.new()}"
        nonce = secrets.token_urlsafe(32)

        session_data = {
            "mission_session_id": mission_session_id,
            "user_id": user_id,
            "alert_id": alert_id,
            "signal_id": signal_id,
            "status": "PENDING",
            "pair": pair,
            "timeframe": timeframe,
            "risk_max_usd": risk_max_usd,
            "token_nonce": nonce,
            "created_at": now,
            "expires_at": expires_at,
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO mission_sessions (
                        mission_session_id, user_id, alert_id, signal_id,
                        status, pair, timeframe, risk_max_usd, token_nonce,
                        created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        mission_session_id,
                        user_id,
                        alert_id,
                        signal_id,
                        "PENDING",
                        pair,
                        timeframe,
                        risk_max_usd,
                        nonce,
                        now,
                        expires_at,
                    ),
                )
                conn.commit()

            logger.info(
                f"✅ Created mission session {mission_session_id} for user {user_id}, expires in {ttl_seconds}s"
            )
            return session_data

        except sqlite3.IntegrityError as e:
            logger.error(f"❌ Database integrity error creating session: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error creating mission session: {e}")
            raise

    def get_session(self, mission_session_id: str) -> Optional[Dict]:
        """
        Get mission session by ID

        Args:
            mission_session_id: Mission session ID

        Returns:
            Session data dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT mission_session_id, user_id, alert_id, signal_id,
                           status, pair, timeframe, risk_max_usd, token_nonce,
                           created_at, expires_at, executed_at
                    FROM mission_sessions
                    WHERE mission_session_id = ?
                """,
                    (mission_session_id,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                return {
                    "mission_session_id": row[0],
                    "user_id": row[1],
                    "alert_id": row[2],
                    "signal_id": row[3],
                    "status": row[4],
                    "pair": row[5],
                    "timeframe": row[6],
                    "risk_max_usd": row[7],
                    "token_nonce": row[8],
                    "created_at": row[9],
                    "expires_at": row[10],
                    "executed_at": row[11],
                }

        except Exception as e:
            logger.error(f"❌ Error getting mission session: {e}")
            return None

    def validate_session(self, mission_session_id: str, expected_nonce: str) -> Dict:
        """
        Validate session for execution

        Args:
            mission_session_id: Mission session ID
            expected_nonce: Nonce from JWT token

        Returns:
            Validation result dictionary
        """
        session = self.get_session(mission_session_id)

        if not session:
            return {"valid": False, "error": "Session not found", "error_code": "SESSION_NOT_FOUND"}

        now = int(time.time())

        # Check expiration
        if now > session["expires_at"]:
            return {"valid": False, "error": "Session expired", "error_code": "SESSION_EXPIRED", "session": session}

        # Check status
        if session["status"] != "PENDING":
            return {
                "valid": False,
                "error": f"Session already {session['status'].lower()}",
                "error_code": "SESSION_ALREADY_PROCESSED",
                "session": session,
            }

        # Check nonce
        if session["token_nonce"] != expected_nonce:
            return {"valid": False, "error": "Invalid token nonce", "error_code": "NONCE_MISMATCH"}

        return {"valid": True, "session": session}

    def mark_executed(self, mission_session_id: str) -> bool:
        """
        Mark session as executed

        Args:
            mission_session_id: Mission session ID

        Returns:
            True if successful, False otherwise
        """
        try:
            now = int(time.time())
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE mission_sessions
                    SET status = 'EXECUTED', executed_at = ?
                    WHERE mission_session_id = ? AND status = 'PENDING'
                """,
                    (now, mission_session_id),
                )

                if cursor.rowcount == 0:
                    logger.warning(f"⚠️ Session {mission_session_id} not updated (already processed or not found)")
                    return False

                conn.commit()

            logger.info(f"✅ Marked session {mission_session_id} as EXECUTED")
            return True

        except Exception as e:
            logger.error(f"❌ Error marking session as executed: {e}")
            return False

    def expire_old_sessions(self) -> int:
        """
        Expire old pending sessions

        Returns:
            Number of sessions expired
        """
        try:
            now = int(time.time())
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE mission_sessions
                    SET status = 'EXPIRED'
                    WHERE status = 'PENDING' AND expires_at < ?
                """,
                    (now,),
                )

                expired_count = cursor.rowcount
                conn.commit()

            if expired_count > 0:
                logger.info(f"✅ Expired {expired_count} old mission sessions")

            return expired_count

        except Exception as e:
            logger.error(f"❌ Error expiring sessions: {e}")
            return 0

    def get_user_sessions(self, user_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get sessions for a user

        Args:
            user_id: User ID
            status: Optional status filter (PENDING/EXECUTED/EXPIRED)
            limit: Maximum number of results

        Returns:
            List of session dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if status:
                    cursor.execute(
                        """
                        SELECT mission_session_id, user_id, alert_id, signal_id,
                               status, pair, timeframe, risk_max_usd,
                               created_at, expires_at, executed_at
                        FROM mission_sessions
                        WHERE user_id = ? AND status = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """,
                        (user_id, status, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT mission_session_id, user_id, alert_id, signal_id,
                               status, pair, timeframe, risk_max_usd,
                               created_at, expires_at, executed_at
                        FROM mission_sessions
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """,
                        (user_id, limit),
                    )

                sessions = []
                for row in cursor.fetchall():
                    sessions.append(
                        {
                            "mission_session_id": row[0],
                            "user_id": row[1],
                            "alert_id": row[2],
                            "signal_id": row[3],
                            "status": row[4],
                            "pair": row[5],
                            "timeframe": row[6],
                            "risk_max_usd": row[7],
                            "created_at": row[8],
                            "expires_at": row[9],
                            "executed_at": row[10],
                        }
                    )

                return sessions

        except Exception as e:
            logger.error(f"❌ Error getting user sessions: {e}")
            return []


# Global instance
_session_manager = None


def get_session_manager() -> MissionSessionManager:
    """Get or create global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = MissionSessionManager()
    return _session_manager


if __name__ == "__main__":
    # Test
    manager = get_session_manager()

    # Create test session
    session = manager.create_session(
        user_id="user_test",
        signal_id="ELITE_GUARD_EURUSD_123",
        alert_id=999,
        pair="EURUSD",
        timeframe="M5",
        risk_max_usd=150.0,
        ttl_seconds=600,
    )

    print(f"Created session: {session}")

    # Validate
    validation = manager.validate_session(session["mission_session_id"], session["token_nonce"])

    print(f"Validation result: {validation}")

    # Mark executed
    success = manager.mark_executed(session["mission_session_id"])
    print(f"Marked executed: {success}")

    # Get updated session
    updated = manager.get_session(session["mission_session_id"])
    print(f"Updated session: {updated}")
