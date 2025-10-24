#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Position Tracking Parity Comparison Tool

Compares position tracking between v1 (SQLite) and v2 (PostgreSQL) to validate
identical position management during shadow testing.

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
class PositionRecord:
    """Position tracking record structure"""
    position_id: str
    user_id: str
    fire_id: Optional[str]
    ticket: int
    symbol: str
    direction: str
    open_price: float
    lot_size: float
    status: str
    created_at: int


@dataclass
class PositionParityReport:
    """Position parity comparison report"""
    v1_count: int
    v2_count: int
    count_match: bool
    count_diff_pct: float
    missing_in_v2: List[str]
    extra_in_v2: List[str]
    status_discrepancies: List[Dict]
    price_discrepancies: List[Dict]
    orphaned_positions_v1: List[str]
    orphaned_positions_v2: List[str]
    timestamp: str
    pass_threshold: bool


class PositionParityChecker:
    """Compare v1 SQLite positions vs v2 PostgreSQL positions"""

    def __init__(
        self,
        v1_db_path: str = "/root/HydraX-v2/bitten.db",
        v2_conn_str: str = "host=localhost port=5433 dbname=bitten_v2 user=bitten_admin password=bitten_secure_2025"
    ):
        self.v1_db_path = v1_db_path
        self.v2_conn_str = v2_conn_str

    def get_v1_positions(self, cutoff_timestamp: int) -> List[PositionRecord]:
        """Get positions from v1 SQLite database"""
        try:
            conn = sqlite3.connect(self.v1_db_path)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_positions'")
            if not cursor.fetchone():
                logger.warning("user_positions table does not exist in v1 database")
                conn.close()
                return []

            query = """
                SELECT position_id, user_id, fire_id, ticket, symbol, direction,
                       open_price, lot_size, status, created_at
                FROM user_positions
                WHERE created_at >= ?
                ORDER BY created_at DESC
            """

            cursor.execute(query, (cutoff_timestamp,))
            rows = cursor.fetchall()

            positions = [
                PositionRecord(
                    position_id=row[0],
                    user_id=row[1],
                    fire_id=row[2],
                    ticket=row[3],
                    symbol=row[4],
                    direction=row[5],
                    open_price=row[6],
                    lot_size=row[7],
                    status=row[8],
                    created_at=row[9]
                )
                for row in rows
            ]

            conn.close()
            logger.info(f"Retrieved {len(positions)} positions from v1 database")
            return positions

        except Exception as e:
            logger.error(f"Error retrieving v1 positions: {e}")
            return []

    def get_v2_positions(self, cutoff_datetime: datetime) -> List[PositionRecord]:
        """Get positions from v2 PostgreSQL database"""
        try:
            conn = psycopg2.connect(self.v2_conn_str)
            cursor = conn.cursor()

            query = """
                SELECT position_id, user_id, fire_id, ticket, symbol, direction,
                       open_price, lot_size, status, EXTRACT(EPOCH FROM opened_at)::INTEGER as created_at
                FROM positions
                WHERE opened_at >= %s
                ORDER BY opened_at DESC
            """

            cursor.execute(query, (cutoff_datetime,))
            rows = cursor.fetchall()

            positions = [
                PositionRecord(
                    position_id=row[0],
                    user_id=row[1],
                    fire_id=row[2],
                    ticket=row[3],
                    symbol=row[4],
                    direction=row[5],
                    open_price=row[6],
                    lot_size=row[7],
                    status=row[8],
                    created_at=row[9]
                )
                for row in rows
            ]

            conn.close()
            logger.info(f"Retrieved {len(positions)} positions from v2 database")
            return positions

        except psycopg2.OperationalError as e:
            logger.warning(f"v2 database not yet available: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving v2 positions: {e}")
            return []

    def find_missing(self, source: List[PositionRecord], target: List[PositionRecord]) -> List[str]:
        """Find position IDs in source but not in target"""
        source_ids = {p.position_id for p in source}
        target_ids = {p.position_id for p in target}
        return list(source_ids - target_ids)

    def find_orphaned(self, positions: List[PositionRecord]) -> List[str]:
        """Find positions without valid fire_id"""
        return [p.position_id for p in positions if not p.fire_id or p.fire_id == '']

    def compare_status(self, v1_positions: List[PositionRecord], v2_positions: List[PositionRecord]) -> List[Dict]:
        """Compare status between v1 and v2"""
        v2_lookup = {p.position_id: p for p in v2_positions}
        discrepancies = []

        for v1_pos in v1_positions:
            if v1_pos.position_id in v2_lookup:
                v2_pos = v2_lookup[v1_pos.position_id]
                if v1_pos.status != v2_pos.status:
                    discrepancies.append({
                        'position_id': v1_pos.position_id,
                        'v1_status': v1_pos.status,
                        'v2_status': v2_pos.status
                    })

        return discrepancies

    def compare_prices(
        self,
        v1_positions: List[PositionRecord],
        v2_positions: List[PositionRecord],
        tolerance: float = 0.0001
    ) -> List[Dict]:
        """Compare open prices between v1 and v2"""
        v2_lookup = {p.position_id: p for p in v2_positions}
        discrepancies = []

        for v1_pos in v1_positions:
            if v1_pos.position_id in v2_lookup:
                v2_pos = v2_lookup[v1_pos.position_id]
                diff = abs(v1_pos.open_price - v2_pos.open_price)

                if diff > tolerance:
                    discrepancies.append({
                        'position_id': v1_pos.position_id,
                        'v1_price': v1_pos.open_price,
                        'v2_price': v2_pos.open_price,
                        'difference': diff
                    })

        return discrepancies

    def compare_last_24h(self, hours: int = 24) -> PositionParityReport:
        """Compare positions from last N hours"""
        cutoff_datetime = datetime.utcnow() - timedelta(hours=hours)
        cutoff_timestamp = int(cutoff_datetime.timestamp())

        logger.info(f"Comparing positions from last {hours} hours (since {cutoff_datetime})")

        # Get positions
        v1_positions = self.get_v1_positions(cutoff_timestamp)
        v2_positions = self.get_v2_positions(cutoff_datetime)

        # Find missing/extra
        missing_in_v2 = self.find_missing(v1_positions, v2_positions)
        extra_in_v2 = self.find_missing(v2_positions, v1_positions)

        # Find orphaned
        orphaned_v1 = self.find_orphaned(v1_positions)
        orphaned_v2 = self.find_orphaned(v2_positions)

        # Compare status and prices
        status_discrepancies = self.compare_status(v1_positions, v2_positions)
        price_discrepancies = self.compare_prices(v1_positions, v2_positions)

        # Calculate count difference
        count_diff = 0 if len(v1_positions) == 0 else abs(len(v1_positions) - len(v2_positions)) / len(v1_positions) * 100

        # Pass threshold
        pass_threshold = (
            count_diff <= 5.0 and
            len(status_discrepancies) == 0 and
            len(price_discrepancies) == 0 and
            len(orphaned_v1) == len(orphaned_v2)
        )

        return PositionParityReport(
            v1_count=len(v1_positions),
            v2_count=len(v2_positions),
            count_match=(len(v1_positions) == len(v2_positions)),
            count_diff_pct=count_diff,
            missing_in_v2=missing_in_v2,
            extra_in_v2=extra_in_v2,
            status_discrepancies=status_discrepancies,
            price_discrepancies=price_discrepancies,
            orphaned_positions_v1=orphaned_v1,
            orphaned_positions_v2=orphaned_v2,
            timestamp=datetime.utcnow().isoformat(),
            pass_threshold=pass_threshold
        )

    def generate_json_report(self, report: PositionParityReport, output_file: str):
        """Generate JSON report file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        logger.info(f"Report saved to {output_file}")


def main():
    """Main execution"""
    checker = PositionParityChecker()

    print("=" * 70)
    print("BITTEN v2.0 - Position Tracking Parity Comparison")
    print("=" * 70)

    report = checker.compare_last_24h(hours=24)

    print(f"\n📍 POSITION COUNT:")
    print(f"   v1 (SQLite):    {report.v1_count}")
    print(f"   v2 (PostgreSQL): {report.v2_count}")
    print(f"   Match:          {'✅' if report.count_match else '❌'}")
    print(f"   Difference:     {report.count_diff_pct:.2f}%")

    print(f"\n🔍 ORPHANED POSITIONS:")
    print(f"   v1: {len(report.orphaned_positions_v1)}")
    print(f"   v2: {len(report.orphaned_positions_v2)}")

    if report.status_discrepancies:
        print(f"\n⚠️  STATUS DISCREPANCIES ({len(report.status_discrepancies)}):")
        for disc in report.status_discrepancies[:5]:
            print(f"   - {disc['position_id']}: v1={disc['v1_status']} v2={disc['v2_status']}")

    if report.price_discrepancies:
        print(f"\n⚠️  PRICE DISCREPANCIES ({len(report.price_discrepancies)}):")
        for disc in report.price_discrepancies[:5]:
            print(f"   - {disc['position_id']}: v1={disc['v1_price']:.5f} "
                  f"v2={disc['v2_price']:.5f} (diff={disc['difference']:.5f})")

    print(f"\n🎯 OVERALL RESULT: {'✅ PASS' if report.pass_threshold else '❌ FAIL'}")
    print("=" * 70)

    # Save report
    output_file = f"/tmp/position_parity_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    checker.generate_json_report(report, output_file)

    return 0 if report.pass_threshold else 1


if __name__ == "__main__":
    exit(main())
