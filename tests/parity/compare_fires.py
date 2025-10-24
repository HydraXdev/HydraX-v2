#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Fire Execution Parity Comparison Tool

Compares fire execution records between v1 (SQLite) and v2 (PostgreSQL) to validate
identical trade execution behavior during shadow testing.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import sqlite3
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FireRecord:
    """Fire execution record structure"""
    fire_id: str
    signal_id: Optional[str]
    user_id: str
    status: str
    ticket: Optional[int]
    price: Optional[float]
    lot_size: Optional[float]
    created_at: int  # Unix timestamp


@dataclass
class FireParityReport:
    """Fire parity comparison report"""
    v1_count: int
    v2_count: int
    count_match: bool
    count_diff_pct: float
    missing_in_v2: List[str]
    extra_in_v2: List[str]
    status_discrepancies: List[Dict]
    lot_size_discrepancies: List[Dict]
    avg_lot_size_v1: float
    avg_lot_size_v2: float
    timestamp: str
    pass_threshold: bool


class FireParityChecker:
    """Compare v1 SQLite fires vs v2 PostgreSQL fires"""

    def __init__(
        self,
        v1_db_path: str = "/root/HydraX-v2/bitten.db",
        v2_conn_str: str = "host=localhost port=5433 dbname=bitten_v2 user=bitten_admin password=bitten_secure_2025"
    ):
        self.v1_db_path = v1_db_path
        self.v2_conn_str = v2_conn_str

    def get_v1_fires(self, cutoff_timestamp: int) -> List[FireRecord]:
        """Get fires from v1 SQLite database"""
        try:
            conn = sqlite3.connect(self.v1_db_path)
            cursor = conn.cursor()

            # Check if fires table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fires'")
            if not cursor.fetchone():
                logger.warning("Fires table does not exist in v1 database")
                conn.close()
                return []

            query = """
                SELECT fire_id, mission_id as signal_id, user_id, status, ticket, price,
                       COALESCE(lot, equity_used) as lot_size, created_at
                FROM fires
                WHERE created_at >= ?
                ORDER BY created_at DESC
            """

            cursor.execute(query, (cutoff_timestamp,))
            rows = cursor.fetchall()

            fires = [
                FireRecord(
                    fire_id=row[0],
                    signal_id=row[1],
                    user_id=row[2],
                    status=row[3],
                    ticket=row[4],
                    price=row[5],
                    lot_size=row[6],
                    created_at=row[7]
                )
                for row in rows
            ]

            conn.close()
            logger.info(f"Retrieved {len(fires)} fires from v1 database")
            return fires

        except Exception as e:
            logger.error(f"Error retrieving v1 fires: {e}")
            return []

    def get_v2_fires(self, cutoff_datetime: datetime) -> List[FireRecord]:
        """Get fires from v2 PostgreSQL database"""
        try:
            conn = psycopg2.connect(self.v2_conn_str)
            cursor = conn.cursor()

            query = """
                SELECT fire_id, signal_id, user_id, status, ticket, fill_price as price,
                       lot_size, EXTRACT(EPOCH FROM created_at)::INTEGER
                FROM fires
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """

            cursor.execute(query, (cutoff_datetime,))
            rows = cursor.fetchall()

            fires = [
                FireRecord(
                    fire_id=row[0],
                    signal_id=row[1],
                    user_id=row[2],
                    status=row[3],
                    ticket=row[4],
                    price=row[5],
                    lot_size=row[6],
                    created_at=row[7]
                )
                for row in rows
            ]

            conn.close()
            logger.info(f"Retrieved {len(fires)} fires from v2 database")
            return fires

        except psycopg2.OperationalError as e:
            logger.warning(f"v2 database not yet available: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving v2 fires: {e}")
            return []

    def find_missing(self, source_fires: List[FireRecord], target_fires: List[FireRecord]) -> List[str]:
        """Find fire IDs in source but not in target"""
        source_ids = {f.fire_id for f in source_fires}
        target_ids = {f.fire_id for f in target_fires}
        return list(source_ids - target_ids)

    def compare_status(self, v1_fires: List[FireRecord], v2_fires: List[FireRecord]) -> List[Dict]:
        """Compare status between v1 and v2 fires"""
        v2_lookup = {f.fire_id: f for f in v2_fires}
        discrepancies = []

        for v1_fire in v1_fires:
            if v1_fire.fire_id in v2_lookup:
                v2_fire = v2_lookup[v1_fire.fire_id]
                if v1_fire.status != v2_fire.status:
                    discrepancies.append({
                        'fire_id': v1_fire.fire_id,
                        'v1_status': v1_fire.status,
                        'v2_status': v2_fire.status
                    })

        return discrepancies

    def compare_lot_sizes(
        self,
        v1_fires: List[FireRecord],
        v2_fires: List[FireRecord],
        tolerance: float = 0.01
    ) -> List[Dict]:
        """Compare lot sizes between v1 and v2"""
        v2_lookup = {f.fire_id: f for f in v2_fires}
        discrepancies = []

        for v1_fire in v1_fires:
            if v1_fire.fire_id in v2_lookup and v1_fire.lot_size and v2_lookup[v1_fire.fire_id].lot_size:
                v2_fire = v2_lookup[v1_fire.fire_id]
                diff = abs(v1_fire.lot_size - v2_fire.lot_size)

                if diff > tolerance:
                    discrepancies.append({
                        'fire_id': v1_fire.fire_id,
                        'v1_lot_size': v1_fire.lot_size,
                        'v2_lot_size': v2_fire.lot_size,
                        'difference': diff
                    })

        return discrepancies

    def calculate_avg_lot_size(self, fires: List[FireRecord]) -> float:
        """Calculate average lot size"""
        lot_sizes = [f.lot_size for f in fires if f.lot_size]
        return sum(lot_sizes) / len(lot_sizes) if lot_sizes else 0.0

    def compare_last_24h(self, hours: int = 24) -> FireParityReport:
        """Compare fires from last N hours"""
        cutoff_datetime = datetime.utcnow() - timedelta(hours=hours)
        cutoff_timestamp = int(cutoff_datetime.timestamp())

        logger.info(f"Comparing fires from last {hours} hours (since {cutoff_datetime})")

        # Get fires from both databases
        v1_fires = self.get_v1_fires(cutoff_timestamp)
        v2_fires = self.get_v2_fires(cutoff_datetime)

        # Find missing/extra
        missing_in_v2 = self.find_missing(v1_fires, v2_fires)
        extra_in_v2 = self.find_missing(v2_fires, v1_fires)

        # Compare status
        status_discrepancies = self.compare_status(v1_fires, v2_fires)

        # Compare lot sizes
        lot_size_discrepancies = self.compare_lot_sizes(v1_fires, v2_fires)

        # Calculate averages
        avg_lot_v1 = self.calculate_avg_lot_size(v1_fires)
        avg_lot_v2 = self.calculate_avg_lot_size(v2_fires)

        # Calculate count difference
        count_diff = 0 if len(v1_fires) == 0 else abs(len(v1_fires) - len(v2_fires)) / len(v1_fires) * 100

        # Pass threshold
        pass_threshold = (
            count_diff <= 5.0 and
            len(status_discrepancies) == 0 and
            len(lot_size_discrepancies) == 0
        )

        return FireParityReport(
            v1_count=len(v1_fires),
            v2_count=len(v2_fires),
            count_match=(len(v1_fires) == len(v2_fires)),
            count_diff_pct=count_diff,
            missing_in_v2=missing_in_v2,
            extra_in_v2=extra_in_v2,
            status_discrepancies=status_discrepancies,
            lot_size_discrepancies=lot_size_discrepancies,
            avg_lot_size_v1=avg_lot_v1,
            avg_lot_size_v2=avg_lot_v2,
            timestamp=datetime.utcnow().isoformat(),
            pass_threshold=pass_threshold
        )

    def generate_json_report(self, report: FireParityReport, output_file: str):
        """Generate JSON report file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        logger.info(f"Report saved to {output_file}")


def main():
    """Main execution"""
    checker = FireParityChecker()

    print("=" * 70)
    print("BITTEN v2.0 - Fire Execution Parity Comparison")
    print("=" * 70)

    report = checker.compare_last_24h(hours=24)

    print(f"\n🔥 FIRE COUNT:")
    print(f"   v1 (SQLite):    {report.v1_count}")
    print(f"   v2 (PostgreSQL): {report.v2_count}")
    print(f"   Match:          {'✅' if report.count_match else '❌'}")
    print(f"   Difference:     {report.count_diff_pct:.2f}%")

    print(f"\n📊 LOT SIZE AVERAGES:")
    print(f"   v1: {report.avg_lot_size_v1:.2f} lots")
    print(f"   v2: {report.avg_lot_size_v2:.2f} lots")

    if report.status_discrepancies:
        print(f"\n⚠️  STATUS DISCREPANCIES ({len(report.status_discrepancies)}):")
        for disc in report.status_discrepancies[:5]:
            print(f"   - {disc['fire_id']}: v1={disc['v1_status']} v2={disc['v2_status']}")

    if report.lot_size_discrepancies:
        print(f"\n⚠️  LOT SIZE DISCREPANCIES ({len(report.lot_size_discrepancies)}):")
        for disc in report.lot_size_discrepancies[:5]:
            print(f"   - {disc['fire_id']}: v1={disc['v1_lot_size']:.2f} "
                  f"v2={disc['v2_lot_size']:.2f} (diff={disc['difference']:.2f})")

    print(f"\n🎯 OVERALL RESULT: {'✅ PASS' if report.pass_threshold else '❌ FAIL'}")
    print("=" * 70)

    # Save report
    output_file = f"/tmp/fire_parity_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    checker.generate_json_report(report, output_file)

    return 0 if report.pass_threshold else 1


if __name__ == "__main__":
    exit(main())
