#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Signal Parity Comparison Tool

Compares signal generation between v1 (SQLite) and v2 (PostgreSQL) to validate
identical behavior during shadow testing.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import sqlite3
import psycopg2
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SignalRecord:
    """Signal record structure"""
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    sl_pips: float
    tp_pips: float
    confidence: float
    pattern_type: str
    created_at: int  # Unix timestamp
    status: str


@dataclass
class ParityReport:
    """Parity comparison report"""
    v1_count: int
    v2_count: int
    count_match: bool
    count_diff_pct: float
    missing_in_v2: List[str]
    extra_in_v2: List[str]
    confidence_discrepancies: List[Dict]
    pattern_distribution_v1: Dict[str, int]
    pattern_distribution_v2: Dict[str, int]
    pattern_distribution_match: bool
    timestamp: str
    pass_threshold: bool  # True if within acceptable variance


class SignalParityChecker:
    """Compare v1 SQLite signals vs v2 PostgreSQL signals"""

    def __init__(
        self,
        v1_db_path: str = "/root/HydraX-v2/bitten.db",
        v2_conn_str: str = "host=localhost port=5433 dbname=bitten_v2 user=bitten_admin password=bitten_secure_2025"
    ):
        """
        Initialize parity checker

        Args:
            v1_db_path: Path to SQLite v1 database
            v2_conn_str: PostgreSQL connection string
        """
        self.v1_db_path = v1_db_path
        self.v2_conn_str = v2_conn_str

    def get_v1_signals(self, cutoff_timestamp: int) -> List[SignalRecord]:
        """
        Get signals from v1 SQLite database

        Args:
            cutoff_timestamp: Unix timestamp cutoff

        Returns:
            List of signal records
        """
        try:
            conn = sqlite3.connect(self.v1_db_path)
            cursor = conn.cursor()

            query = """
                SELECT signal_id, symbol, direction,
                       COALESCE(entry_price, entry) as entry_price,
                       COALESCE(stop_pips, 0) as sl_pips,
                       COALESCE(target_pips, 0) as tp_pips,
                       confidence, pattern_type, created_at,
                       COALESCE(outcome, 'ACTIVE') as status
                FROM signals
                WHERE created_at >= ?
                ORDER BY created_at DESC
            """

            cursor.execute(query, (cutoff_timestamp,))
            rows = cursor.fetchall()

            signals = [
                SignalRecord(
                    signal_id=row[0],
                    symbol=row[1],
                    direction=row[2],
                    entry_price=row[3],
                    sl_pips=row[4],
                    tp_pips=row[5],
                    confidence=row[6],
                    pattern_type=row[7],
                    created_at=row[8],
                    status=row[9]
                )
                for row in rows
            ]

            conn.close()
            logger.info(f"Retrieved {len(signals)} signals from v1 database")
            return signals

        except Exception as e:
            logger.error(f"Error retrieving v1 signals: {e}")
            return []

    def get_v2_signals(self, cutoff_datetime: datetime) -> List[SignalRecord]:
        """
        Get signals from v2 PostgreSQL database

        Args:
            cutoff_datetime: Datetime cutoff

        Returns:
            List of signal records
        """
        try:
            conn = psycopg2.connect(self.v2_conn_str)
            cursor = conn.cursor()

            query = """
                SELECT signal_id, symbol, direction, entry_price, sl_pips, tp_pips,
                       confidence, pattern_type, EXTRACT(EPOCH FROM created_at)::INTEGER, status
                FROM signals
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """

            cursor.execute(query, (cutoff_datetime,))
            rows = cursor.fetchall()

            signals = [
                SignalRecord(
                    signal_id=row[0],
                    symbol=row[1],
                    direction=row[2],
                    entry_price=row[3],
                    sl_pips=row[4],
                    tp_pips=row[5],
                    confidence=row[6],
                    pattern_type=row[7],
                    created_at=row[8],
                    status=row[9]
                )
                for row in rows
            ]

            conn.close()
            logger.info(f"Retrieved {len(signals)} signals from v2 database")
            return signals

        except psycopg2.OperationalError as e:
            logger.warning(f"v2 database not yet available: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving v2 signals: {e}")
            return []

    def find_missing(
        self,
        source_signals: List[SignalRecord],
        target_signals: List[SignalRecord]
    ) -> List[str]:
        """
        Find signal IDs in source but not in target

        Args:
            source_signals: Source signal list
            target_signals: Target signal list

        Returns:
            List of missing signal IDs
        """
        source_ids = {s.signal_id for s in source_signals}
        target_ids = {s.signal_id for s in target_signals}
        return list(source_ids - target_ids)

    def compare_confidence(
        self,
        v1_signals: List[SignalRecord],
        v2_signals: List[SignalRecord],
        tolerance: float = 2.0
    ) -> List[Dict]:
        """
        Compare confidence scores between v1 and v2

        Args:
            v1_signals: v1 signal list
            v2_signals: v2 signal list
            tolerance: Acceptable difference percentage

        Returns:
            List of signals with confidence discrepancies
        """
        # Create lookup for v2 signals
        v2_lookup = {s.signal_id: s for s in v2_signals}

        discrepancies = []

        for v1_signal in v1_signals:
            if v1_signal.signal_id in v2_lookup:
                v2_signal = v2_lookup[v1_signal.signal_id]
                diff = abs(v1_signal.confidence - v2_signal.confidence)

                if diff > tolerance:
                    discrepancies.append({
                        'signal_id': v1_signal.signal_id,
                        'v1_confidence': v1_signal.confidence,
                        'v2_confidence': v2_signal.confidence,
                        'difference': diff
                    })

        return discrepancies

    def get_pattern_distribution(self, signals: List[SignalRecord]) -> Dict[str, int]:
        """
        Get pattern type distribution

        Args:
            signals: Signal list

        Returns:
            Dict mapping pattern_type to count
        """
        distribution = {}
        for signal in signals:
            pattern = signal.pattern_type
            distribution[pattern] = distribution.get(pattern, 0) + 1

        return distribution

    def compare_last_24h(self, hours: int = 24) -> ParityReport:
        """
        Compare signals from last N hours

        Args:
            hours: Number of hours to look back

        Returns:
            Parity report
        """
        # Calculate cutoff
        cutoff_datetime = datetime.utcnow() - timedelta(hours=hours)
        cutoff_timestamp = int(cutoff_datetime.timestamp())

        logger.info(f"Comparing signals from last {hours} hours (since {cutoff_datetime})")

        # Get signals from both databases
        v1_signals = self.get_v1_signals(cutoff_timestamp)
        v2_signals = self.get_v2_signals(cutoff_datetime)

        # Find missing/extra signals
        missing_in_v2 = self.find_missing(v1_signals, v2_signals)
        extra_in_v2 = self.find_missing(v2_signals, v1_signals)

        # Compare confidence scores
        confidence_discrepancies = self.compare_confidence(v1_signals, v2_signals)

        # Compare pattern distributions
        pattern_dist_v1 = self.get_pattern_distribution(v1_signals)
        pattern_dist_v2 = self.get_pattern_distribution(v2_signals)

        # Calculate count difference
        count_diff = 0 if len(v1_signals) == 0 else abs(len(v1_signals) - len(v2_signals)) / len(v1_signals) * 100

        # Determine if within acceptable variance (±5%)
        pass_threshold = (
            count_diff <= 5.0 and
            len(confidence_discrepancies) == 0 and
            pattern_dist_v1 == pattern_dist_v2
        )

        report = ParityReport(
            v1_count=len(v1_signals),
            v2_count=len(v2_signals),
            count_match=(len(v1_signals) == len(v2_signals)),
            count_diff_pct=count_diff,
            missing_in_v2=missing_in_v2,
            extra_in_v2=extra_in_v2,
            confidence_discrepancies=confidence_discrepancies,
            pattern_distribution_v1=pattern_dist_v1,
            pattern_distribution_v2=pattern_dist_v2,
            pattern_distribution_match=(pattern_dist_v1 == pattern_dist_v2),
            timestamp=datetime.utcnow().isoformat(),
            pass_threshold=pass_threshold
        )

        return report

    def generate_json_report(self, report: ParityReport, output_file: str):
        """
        Generate JSON report file

        Args:
            report: Parity report
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)

        logger.info(f"Report saved to {output_file}")


def main():
    """Main execution"""
    checker = SignalParityChecker()

    print("=" * 70)
    print("BITTEN v2.0 - Signal Parity Comparison")
    print("=" * 70)

    # Compare last 24 hours
    report = checker.compare_last_24h(hours=24)

    print(f"\n📊 SIGNAL COUNT:")
    print(f"   v1 (SQLite):    {report.v1_count}")
    print(f"   v2 (PostgreSQL): {report.v2_count}")
    print(f"   Match:          {'✅' if report.count_match else '❌'}")
    print(f"   Difference:     {report.count_diff_pct:.2f}%")

    print(f"\n📋 PATTERN DISTRIBUTION:")
    print(f"   v1: {report.pattern_distribution_v1}")
    print(f"   v2: {report.pattern_distribution_v2}")
    print(f"   Match: {'✅' if report.pattern_distribution_match else '❌'}")

    if report.missing_in_v2:
        print(f"\n⚠️  MISSING IN v2 ({len(report.missing_in_v2)} signals):")
        for sig_id in report.missing_in_v2[:5]:  # Show first 5
            print(f"   - {sig_id}")

    if report.extra_in_v2:
        print(f"\n⚠️  EXTRA IN v2 ({len(report.extra_in_v2)} signals):")
        for sig_id in report.extra_in_v2[:5]:  # Show first 5
            print(f"   - {sig_id}")

    if report.confidence_discrepancies:
        print(f"\n⚠️  CONFIDENCE DISCREPANCIES ({len(report.confidence_discrepancies)}):")
        for disc in report.confidence_discrepancies[:5]:  # Show first 5
            print(f"   - {disc['signal_id']}: v1={disc['v1_confidence']:.1f}% "
                  f"v2={disc['v2_confidence']:.1f}% (diff={disc['difference']:.1f}%)")

    print(f"\n🎯 OVERALL RESULT: {'✅ PASS' if report.pass_threshold else '❌ FAIL'}")
    print("=" * 70)

    # Save report
    output_file = f"/tmp/signal_parity_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    checker.generate_json_report(report, output_file)

    return 0 if report.pass_threshold else 1


if __name__ == "__main__":
    exit(main())
