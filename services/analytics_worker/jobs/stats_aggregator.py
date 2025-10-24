"""
Stats Aggregator Job
Calculates user statistics and updates user profiles
"""
import logging
import time
from typing import Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor

from ..config import DATABASE_URL, MAX_RETRIES, RETRY_DELAY_SECONDS

logger = logging.getLogger(__name__)


class StatsAggregator:
    """Aggregates user statistics from trading activity"""

    def __init__(self):
        self.conn = None

    def _get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def _calculate_user_stats(self, user_id: str) -> Dict:
        """Calculate stats for a single user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            stats = {
                'total_fires': 0,
                'wins': 0,
                'losses': 0,
                'pending': 0,
                'win_rate': 0.0,
                'total_pips': 0.0,
                'avg_pips_per_trade': 0.0,
                'total_profit_loss': 0.0
            }

            # Get fire statistics
            cursor.execute("""
                SELECT
                    COUNT(*) as total_fires,
                    COUNT(CASE WHEN status = 'FILLED' THEN 1 END) as filled
                FROM fires
                WHERE user_id = %s
            """, (user_id,))

            fire_stats = cursor.fetchone()
            if fire_stats:
                stats['total_fires'] = fire_stats['total_fires'] or 0

            # Get outcome statistics from positions
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'CLOSED' AND profit > 0 THEN 1 END) as wins,
                    COUNT(CASE WHEN status = 'CLOSED' AND profit <= 0 THEN 1 END) as losses,
                    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as pending,
                    COALESCE(SUM(CASE WHEN status = 'CLOSED' THEN profit ELSE 0 END), 0) as total_pl
                FROM positions
                WHERE user_id = %s
            """, (user_id,))

            outcome_stats = cursor.fetchone()
            if outcome_stats:
                stats['wins'] = outcome_stats['wins'] or 0
                stats['losses'] = outcome_stats['losses'] or 0
                stats['pending'] = outcome_stats['pending'] or 0
                stats['total_profit_loss'] = float(outcome_stats['total_pl'] or 0)

                # Calculate win rate
                total_closed = stats['wins'] + stats['losses']
                if total_closed > 0:
                    stats['win_rate'] = round((stats['wins'] / total_closed) * 100, 2)

            # Get pip statistics
            cursor.execute("""
                SELECT
                    COALESCE(SUM(pips_result), 0) as total_pips,
                    COALESCE(AVG(pips_result), 0) as avg_pips
                FROM signal_outcomes
                WHERE signal_id IN (
                    SELECT signal_id FROM fires WHERE user_id = %s
                )
            """, (user_id,))

            pip_stats = cursor.fetchone()
            if pip_stats:
                stats['total_pips'] = round(float(pip_stats['total_pips'] or 0), 1)
                stats['avg_pips_per_trade'] = round(float(pip_stats['avg_pips'] or 0), 1)

            cursor.close()
            conn.close()

            return stats

        except Exception as e:
            logger.error(f"Error calculating stats for user {user_id}: {e}")
            return None

    def _update_user_stats(self, user_id: str, stats: Dict):
        """Update user table with calculated stats"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users
                SET
                    total_fires = %s,
                    wins = %s,
                    losses = %s,
                    win_rate = %s,
                    total_pips = %s,
                    updated_at = %s
                WHERE user_id = %s
            """, (
                stats['total_fires'],
                stats['wins'],
                stats['losses'],
                stats['win_rate'],
                stats['total_pips'],
                int(time.time()),
                user_id
            ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(
                f"Updated stats for user {user_id}: "
                f"{stats['wins']}W/{stats['losses']}L "
                f"({stats['win_rate']:.1f}% WR, {stats['total_pips']:+.1f} pips)"
            )

        except Exception as e:
            logger.error(f"Error updating stats for user {user_id}: {e}")

    def run(self):
        """Run stats aggregation job"""
        logger.info("Running Stats Aggregation...")

        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get all active users
            cursor.execute("""
                SELECT DISTINCT user_id
                FROM users
                WHERE created_at > 0
            """)

            users = cursor.fetchall()
            cursor.close()
            conn.close()

            logger.info(f"Aggregating stats for {len(users)} users...")

            success_count = 0
            for user in users:
                user_id = user['user_id']

                stats = self._calculate_user_stats(user_id)
                if stats:
                    self._update_user_stats(user_id, stats)
                    success_count += 1

            logger.info(
                f"Stats aggregation complete: {success_count}/{len(users)} users updated"
            )

        except Exception as e:
            logger.error(f"Error in stats aggregation: {e}")


# Job entry point
def run_stats_aggregator():
    """Run stats aggregator job"""
    aggregator = StatsAggregator()
    aggregator.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_stats_aggregator()
