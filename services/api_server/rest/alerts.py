"""
Alert Feed API Endpoints
Returns user's signal feed with fire status (fired/not fired)
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import time
import sqlite3
import logging

from ..middleware.auth import verify_firebase_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def get_current_user_id(firebase_uid: str = Depends(verify_firebase_token)) -> str:
    """
    Dependency to get current authenticated user ID
    Returns Firebase UID from verified token
    """
    return firebase_uid


@router.get("/feed")
async def get_alert_feed(
    user_id: str = Depends(get_current_user_id),
    limit: int = 50,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Get user's alert feed with fire status

    Returns signals from the last N hours with fire status for the authenticated user.

    Parameters:
        - limit: Maximum number of alerts to return (default 50)
        - hours: Number of hours to look back (default 24)

    Returns:
        {
            "alerts": [
                {
                    "signal_id": str,
                    "symbol": str,
                    "direction": str,
                    "entry_price": float,
                    "sl": float,
                    "tp": float,
                    "confidence": float,
                    "pattern_type": str,
                    "created_at": int,
                    "fire_id": str | null,
                    "fire_mode": str | null,
                    "fire_status": str | null,
                    "fired_at": int | null,
                    "is_fired": bool,
                    "can_fire": bool,
                    "is_settled": bool,
                    "outcome": str | null,
                    "duration_seconds": int | null
                }
            ]
        }
    """
    try:
        # Calculate time threshold (N hours ago)
        time_threshold = int(time.time()) - (hours * 3600)

        # Connect to database
        db_path = "/root/HydraX-v2/bitten.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        # Query signals with left join to fires table
        query = """
        SELECT
            s.signal_id,
            s.symbol,
            s.direction,
            s.entry_price,
            s.sl,
            s.tp,
            s.confidence,
            s.pattern_type,
            s.created_at,
            s.outcome,
            s.duration_seconds,
            f.fire_id,
            f.fire_mode,
            f.status as fire_status,
            f.created_at as fired_at
        FROM signals s
        LEFT JOIN fires f ON (
            f.mission_id = s.signal_id
            AND f.user_id = ?
            AND f.status IN ('SENT', 'FILLED')
        )
        WHERE s.created_at > ?
        ORDER BY s.created_at DESC
        LIMIT ?
        """

        cursor.execute(query, (user_id, time_threshold, limit))
        rows = cursor.fetchall()

        # Transform rows into alert objects
        alerts = []
        for row in rows:
            # Determine UI state flags
            is_fired = row['fire_id'] is not None
            is_settled = row['outcome'] is not None
            can_fire = not is_fired and not is_settled

            alert = {
                "signal_id": row['signal_id'],
                "symbol": row['symbol'],
                "direction": row['direction'],
                "entry_price": row['entry_price'] or 0,
                "sl": row['sl'] or 0,
                "tp": row['tp'] or 0,
                "confidence": row['confidence'] or 0,
                "pattern_type": row['pattern_type'] or "UNKNOWN",
                "created_at": row['created_at'] or 0,

                # Fire status (null if not fired)
                "fire_id": row['fire_id'],
                "fire_mode": row['fire_mode'],
                "fire_status": row['fire_status'],
                "fired_at": row['fired_at'],

                # UI state flags
                "is_fired": is_fired,
                "can_fire": can_fire,
                "is_settled": is_settled,

                # Outcome (when settled)
                "outcome": row['outcome'],
                "duration_seconds": row['duration_seconds']
            }

            alerts.append(alert)

        conn.close()

        logger.info(f"✅ Alert feed for user {user_id}: {len(alerts)} alerts")

        return {
            "alerts": alerts,
            "user_id": user_id,
            "hours_lookback": hours,
            "limit": limit,
            "count": len(alerts)
        }

    except sqlite3.Error as e:
        logger.error(f"❌ Database error in alert feed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error in alert feed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
