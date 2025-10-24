"""
Reports Job
Generates nightly performance reports and analytics
"""
import logging
import time
from typing import Dict, List
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

from ..config import DATABASE_URL

logger = logging.getLogger(__name__)


class Reports:
    """Generates performance reports and analytics"""

    def __init__(self):
        pass

    def _get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def _generate_pattern_performance_report(self) -> Dict:
        """Generate pattern win rate report"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get outcome stats by pattern type (last 30 days)
            cutoff_time = int((datetime.utcnow() - timedelta(days=30)).timestamp())

            cursor.execute("""
                SELECT
                    pattern_type,
                    COUNT(*) as total_signals,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    ROUND(AVG(confidence), 2) as avg_confidence,
                    ROUND(AVG(CASE WHEN outcome = 'WIN' THEN pips_result END), 2) as avg_win_pips,
                    ROUND(AVG(CASE WHEN outcome = 'LOSS' THEN pips_result END), 2) as avg_loss_pips,
                    ROUND(SUM(pips_result), 2) as total_pips
                FROM signal_outcomes
                WHERE created_at > %s
                GROUP BY pattern_type
                ORDER BY wins DESC
            """, (cutoff_time,))

            patterns = cursor.fetchall()
            cursor.close()
            conn.close()

            report = {
                'report_type': 'pattern_performance',
                'period': '30_days',
                'generated_at': int(time.time()),
                'patterns': []
            }

            for pattern in patterns:
                total = pattern['total_signals'] or 0
                wins = pattern['wins'] or 0
                losses = pattern['losses'] or 0

                win_rate = 0.0
                if total > 0:
                    win_rate = round((wins / total) * 100, 2)

                pattern_data = {
                    'pattern_type': pattern['pattern_type'],
                    'total_signals': total,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': win_rate,
                    'avg_confidence': float(pattern['avg_confidence'] or 0),
                    'avg_win_pips': float(pattern['avg_win_pips'] or 0),
                    'avg_loss_pips': abs(float(pattern['avg_loss_pips'] or 0)),
                    'total_pips': float(pattern['total_pips'] or 0)
                }

                report['patterns'].append(pattern_data)

            logger.info(f"Generated pattern performance report: {len(patterns)} patterns")
            return report

        except Exception as e:
            logger.error(f"Error generating pattern report: {e}")
            return None

    def _generate_user_leaderboard(self) -> Dict:
        """Generate user leaderboard report"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get top users by win rate (min 10 trades)
            cursor.execute("""
                SELECT
                    user_id,
                    tier,
                    wins,
                    losses,
                    win_rate,
                    total_pips,
                    total_fires
                FROM users
                WHERE (wins + losses) >= 10
                ORDER BY win_rate DESC, total_pips DESC
                LIMIT 100
            """)

            top_users = cursor.fetchall()

            # Get top users by total pips
            cursor.execute("""
                SELECT
                    user_id,
                    tier,
                    total_pips,
                    win_rate,
                    wins,
                    losses
                FROM users
                WHERE total_pips > 0
                ORDER BY total_pips DESC
                LIMIT 100
            """)

            top_pips = cursor.fetchall()

            cursor.close()
            conn.close()

            report = {
                'report_type': 'user_leaderboard',
                'generated_at': int(time.time()),
                'top_by_win_rate': [],
                'top_by_pips': []
            }

            # Top by win rate
            for i, user in enumerate(top_users, 1):
                report['top_by_win_rate'].append({
                    'rank': i,
                    'user_id': user['user_id'],
                    'tier': user['tier'],
                    'win_rate': float(user['win_rate'] or 0),
                    'wins': int(user['wins'] or 0),
                    'losses': int(user['losses'] or 0),
                    'total_pips': float(user['total_pips'] or 0)
                })

            # Top by pips
            for i, user in enumerate(top_pips, 1):
                report['top_by_pips'].append({
                    'rank': i,
                    'user_id': user['user_id'],
                    'tier': user['tier'],
                    'total_pips': float(user['total_pips'] or 0),
                    'win_rate': float(user['win_rate'] or 0),
                    'wins': int(user['wins'] or 0),
                    'losses': int(user['losses'] or 0)
                })

            logger.info(
                f"Generated leaderboard: "
                f"{len(top_users)} by win rate, {len(top_pips)} by pips"
            )
            return report

        except Exception as e:
            logger.error(f"Error generating leaderboard: {e}")
            return None

    def _generate_system_health_report(self) -> Dict:
        """Generate system health metrics report"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get system stats (last 24 hours)
            cutoff_time = int((datetime.utcnow() - timedelta(hours=24)).timestamp())

            # Signal stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_signals,
                    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_signals,
                    COUNT(CASE WHEN status = 'EXPIRED' THEN 1 END) as expired_signals,
                    ROUND(AVG(confidence), 2) as avg_confidence
                FROM signals
                WHERE created_at > %s
            """, (cutoff_time,))
            signal_stats = cursor.fetchone()

            # Fire stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_fires,
                    COUNT(CASE WHEN status = 'FILLED' THEN 1 END) as filled_fires,
                    COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_fires
                FROM fires
                WHERE created_at > %s
            """, (cutoff_time,))
            fire_stats = cursor.fetchone()

            # Position stats
            cursor.execute("""
                SELECT
                    COUNT(*) as open_positions,
                    ROUND(SUM(profit), 2) as total_unrealized_pl
                FROM positions
                WHERE status = 'OPEN'
            """)
            position_stats = cursor.fetchone()

            # Active users
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM fires
                WHERE created_at > %s
            """, (cutoff_time,))
            user_stats = cursor.fetchone()

            cursor.close()
            conn.close()

            report = {
                'report_type': 'system_health',
                'period': '24_hours',
                'generated_at': int(time.time()),
                'signals': {
                    'total': int(signal_stats['total_signals'] or 0),
                    'active': int(signal_stats['active_signals'] or 0),
                    'expired': int(signal_stats['expired_signals'] or 0),
                    'avg_confidence': float(signal_stats['avg_confidence'] or 0)
                },
                'fires': {
                    'total': int(fire_stats['total_fires'] or 0),
                    'filled': int(fire_stats['filled_fires'] or 0),
                    'pending': int(fire_stats['pending_fires'] or 0)
                },
                'positions': {
                    'open': int(position_stats['open_positions'] or 0),
                    'total_unrealized_pl': float(position_stats['total_unrealized_pl'] or 0)
                },
                'users': {
                    'active_24h': int(user_stats['active_users'] or 0)
                }
            }

            logger.info(
                f"System health: {report['signals']['total']} signals, "
                f"{report['fires']['total']} fires, "
                f"{report['users']['active_24h']} active users"
            )
            return report

        except Exception as e:
            logger.error(f"Error generating system health report: {e}")
            return None

    def _save_report(self, report: Dict):
        """Save report to PostgreSQL"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO reports
                (report_type, report_data, created_at)
                VALUES (%s, %s, %s)
            """, (
                report['report_type'],
                str(report),  # Convert to JSON string
                int(time.time())
            ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Saved {report['report_type']} report to database")

        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def run(self):
        """Run nightly reports job"""
        logger.info("Running Nightly Reports...")

        try:
            # Generate all reports
            reports_generated = 0

            # Pattern performance report
            pattern_report = self._generate_pattern_performance_report()
            if pattern_report:
                self._save_report(pattern_report)
                reports_generated += 1

            # User leaderboard
            leaderboard_report = self._generate_user_leaderboard()
            if leaderboard_report:
                self._save_report(leaderboard_report)
                reports_generated += 1

            # System health
            health_report = self._generate_system_health_report()
            if health_report:
                self._save_report(health_report)
                reports_generated += 1

            logger.info(f"Nightly reports complete: {reports_generated} reports generated")

        except Exception as e:
            logger.error(f"Error in reports job: {e}")


# Job entry point
def run_reports():
    """Run reports job"""
    reports = Reports()
    reports.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_reports()
