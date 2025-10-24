#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Parity Test Orchestrator

Runs all parity comparison tools and aggregates results for comprehensive
v1 vs v2 validation during shadow testing.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import sys
import json
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict
import logging

# Import parity checkers
from compare_signals import SignalParityChecker
from compare_fires import FireParityChecker
from compare_positions import PositionParityChecker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ParityTestResults:
    """Aggregated parity test results"""
    timestamp: str
    duration_hours: int
    signals_pass: bool
    fires_pass: bool
    positions_pass: bool
    overall_pass: bool
    signals_report: Dict
    fires_report: Dict
    positions_report: Dict
    summary: Dict


class ParityRunner:
    """Orchestrate all parity comparison tests"""

    def __init__(self, duration_hours: int = 24):
        """
        Initialize parity runner

        Args:
            duration_hours: Hours of data to compare
        """
        self.duration_hours = duration_hours
        self.signal_checker = SignalParityChecker()
        self.fire_checker = FireParityChecker()
        self.position_checker = PositionParityChecker()

    def run_all_tests(self) -> ParityTestResults:
        """
        Run all parity comparison tests

        Returns:
            Aggregated test results
        """
        logger.info(f"Starting parity tests for last {self.duration_hours} hours")

        # Run signal comparison
        logger.info("Running signal parity test...")
        signals_report = self.signal_checker.compare_last_24h(hours=self.duration_hours)
        signals_pass = signals_report.pass_threshold

        # Run fire comparison
        logger.info("Running fire parity test...")
        fires_report = self.fire_checker.compare_last_24h(hours=self.duration_hours)
        fires_pass = fires_report.pass_threshold

        # Run position comparison
        logger.info("Running position parity test...")
        positions_report = self.position_checker.compare_last_24h(hours=self.duration_hours)
        positions_pass = positions_report.pass_threshold

        # Determine overall pass/fail
        overall_pass = signals_pass and fires_pass and positions_pass

        # Create summary
        summary = {
            'total_discrepancies': (
                len(signals_report.missing_in_v2) +
                len(signals_report.extra_in_v2) +
                len(signals_report.confidence_discrepancies) +
                len(fires_report.missing_in_v2) +
                len(fires_report.extra_in_v2) +
                len(fires_report.status_discrepancies) +
                len(positions_report.missing_in_v2) +
                len(positions_report.extra_in_v2) +
                len(positions_report.status_discrepancies)
            ),
            'signals_count_diff': signals_report.count_diff_pct,
            'fires_count_diff': fires_report.count_diff_pct,
            'positions_count_diff': positions_report.count_diff_pct,
            'critical_failures': self._identify_critical_failures(
                signals_report, fires_report, positions_report
            )
        }

        results = ParityTestResults(
            timestamp=datetime.utcnow().isoformat(),
            duration_hours=self.duration_hours,
            signals_pass=signals_pass,
            fires_pass=fires_pass,
            positions_pass=positions_pass,
            overall_pass=overall_pass,
            signals_report=asdict(signals_report),
            fires_report=asdict(fires_report),
            positions_report=asdict(positions_report),
            summary=summary
        )

        logger.info(f"Parity tests complete: {'PASS' if overall_pass else 'FAIL'}")
        return results

    def _identify_critical_failures(self, signals, fires, positions) -> List[str]:
        """Identify critical failures that would block cutover"""
        failures = []

        # Critical: >10% count difference
        if signals.count_diff_pct > 10.0:
            failures.append(f"Signals count difference: {signals.count_diff_pct:.1f}%")
        if fires.count_diff_pct > 10.0:
            failures.append(f"Fires count difference: {fires.count_diff_pct:.1f}%")
        if positions.count_diff_pct > 10.0:
            failures.append(f"Positions count difference: {positions.count_diff_pct:.1f}%")

        # Critical: Missing trades in v2
        if len(fires.missing_in_v2) > 0:
            failures.append(f"Missing {len(fires.missing_in_v2)} fires in v2")

        # Critical: Orphaned positions
        if len(positions.orphaned_positions_v2) > len(positions.orphaned_positions_v1):
            orphan_diff = len(positions.orphaned_positions_v2) - len(positions.orphaned_positions_v1)
            failures.append(f"{orphan_diff} extra orphaned positions in v2")

        return failures

    def save_results(self, results: ParityTestResults, output_file: str):
        """Save results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(results), f, indent=2)
        logger.info(f"Results saved to {output_file}")

    def print_summary(self, results: ParityTestResults):
        """Print human-readable summary"""
        print("\n" + "=" * 70)
        print("BITTEN v2.0 - PARITY TEST SUMMARY")
        print("=" * 70)
        print(f"\nTest Duration: {results.duration_hours} hours")
        print(f"Timestamp: {results.timestamp}")

        print(f"\n📊 TEST RESULTS:")
        print(f"   Signals:   {'✅ PASS' if results.signals_pass else '❌ FAIL'}")
        print(f"   Fires:     {'✅ PASS' if results.fires_pass else '❌ FAIL'}")
        print(f"   Positions: {'✅ PASS' if results.positions_pass else '❌ FAIL'}")

        print(f"\n📈 COUNT DIFFERENCES:")
        print(f"   Signals:   {results.summary['signals_count_diff']:.2f}%")
        print(f"   Fires:     {results.summary['fires_count_diff']:.2f}%")
        print(f"   Positions: {results.summary['positions_count_diff']:.2f}%")

        print(f"\n⚠️  TOTAL DISCREPANCIES: {results.summary['total_discrepancies']}")

        if results.summary['critical_failures']:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in results.summary['critical_failures']:
                print(f"   - {failure}")
        else:
            print(f"\n✅ No critical failures detected")

        print(f"\n🎯 OVERALL RESULT: {'✅ PASS - READY FOR CUTOVER' if results.overall_pass else '❌ FAIL - DO NOT CUTOVER'}")
        print("=" * 70 + "\n")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Run BITTEN v1 vs v2 parity tests')
    parser.add_argument('--duration', type=int, default=24, help='Hours of data to compare (default: 24)')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    args = parser.parse_args()

    # Run tests
    runner = ParityRunner(duration_hours=args.duration)
    results = runner.run_all_tests()

    # Print summary
    runner.print_summary(results)

    # Save results
    if args.output:
        runner.save_results(results, args.output)
    else:
        default_output = f"/tmp/parity_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        runner.save_results(results, default_output)

    # Exit code: 0 if pass, 1 if fail
    return 0 if results.overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
