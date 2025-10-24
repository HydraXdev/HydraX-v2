#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Load Test Orchestrator

Runs all load tests and aggregates results for comprehensive
performance validation before Phase 1 cutover.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import json
from datetime import datetime
from typing import Dict
from dataclasses import dataclass, asdict
import logging

# Import load tests
from websocket_stress import WebSocketStressTest
from fire_burst import FireBurstTest
from signal_flood import SignalFloodTest
from db_connection_pool import DBPoolStressTest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestSuiteResults:
    """Aggregated load test results"""
    timestamp: str
    websocket_pass: bool
    fire_burst_pass: bool
    signal_flood_pass: bool
    db_pool_pass: bool
    overall_pass: bool
    websocket_results: Dict
    fire_burst_results: Dict
    signal_flood_results: Dict
    db_pool_results: Dict
    summary: Dict


class LoadTestRunner:
    """Orchestrate all load tests"""

    def __init__(self):
        """Initialize load test runner"""
        self.websocket_test = WebSocketStressTest(
            num_connections=1000,
            duration_seconds=60
        )
        self.fire_test = FireBurstTest(
            fires_per_second=100,
            duration_seconds=60
        )
        self.signal_test = SignalFloodTest(
            target_signals_per_hour=5000,
            duration_seconds=600
        )
        self.db_test = DBPoolStressTest(
            concurrent_queries=200,
            duration_seconds=60
        )

    async def run_all_tests(self) -> LoadTestSuiteResults:
        """
        Run all load tests

        Returns:
            Aggregated test results
        """
        logger.info("Starting load test suite...")

        # Run WebSocket stress test
        logger.info("1/4: Running WebSocket stress test...")
        websocket_results = await self.websocket_test.run_test()
        websocket_pass = websocket_results.pass_threshold

        # Run fire burst test
        logger.info("2/4: Running fire burst test...")
        fire_results = await self.fire_test.run_test()
        fire_pass = fire_results.pass_threshold

        # Run signal flood test
        logger.info("3/4: Running signal flood test...")
        signal_results = await self.signal_test.run_test()
        signal_pass = signal_results.pass_threshold

        # Run DB pool test
        logger.info("4/4: Running database pool test...")
        db_results = await self.db_test.run_test()
        db_pass = db_results.pass_threshold

        # Determine overall pass/fail
        overall_pass = websocket_pass and fire_pass and signal_pass and db_pass

        # Create summary
        summary = {
            'total_tests': 4,
            'passed_tests': sum([websocket_pass, fire_pass, signal_pass, db_pass]),
            'failed_tests': sum([not websocket_pass, not fire_pass, not signal_pass, not db_pass]),
            'critical_failures': self._identify_critical_failures(
                websocket_results, fire_results, signal_results, db_results
            ),
            'performance_summary': {
                'websocket_p95_ms': websocket_results.p95_latency_ms,
                'fire_p95_ms': fire_results.p95_latency_ms,
                'signal_p95_ms': signal_results.p95_latency_ms,
                'db_p95_ms': db_results.p95_query_ms
            }
        }

        results = LoadTestSuiteResults(
            timestamp=datetime.utcnow().isoformat(),
            websocket_pass=websocket_pass,
            fire_burst_pass=fire_pass,
            signal_flood_pass=signal_pass,
            db_pool_pass=db_pass,
            overall_pass=overall_pass,
            websocket_results=asdict(websocket_results),
            fire_burst_results=asdict(fire_results),
            signal_flood_results=asdict(signal_results),
            db_pool_results=asdict(db_results),
            summary=summary
        )

        logger.info(f"Load test suite complete: {'PASS' if overall_pass else 'FAIL'}")
        return results

    def _identify_critical_failures(self, ws, fire, signal, db) -> list:
        """Identify critical failures that would block cutover"""
        failures = []

        # Critical: P95 latency thresholds
        if ws.p95_latency_ms > 250.0:
            failures.append(f"WebSocket P95 latency: {ws.p95_latency_ms:.2f}ms (> 250ms threshold)")

        if fire.p95_latency_ms > 100.0:
            failures.append(f"Fire command P95 latency: {fire.p95_latency_ms:.2f}ms (> 100ms threshold)")

        if signal.p95_latency_ms > 50.0:
            failures.append(f"Signal publish P95 latency: {signal.p95_latency_ms:.2f}ms (> 50ms threshold)")

        if db.p95_query_ms > 50.0:
            failures.append(f"Database P95 query time: {db.p95_query_ms:.2f}ms (> 50ms threshold)")

        # Critical: Pool exhaustion
        if db.pool_exhausted_count > 0:
            failures.append(f"Database pool exhausted {db.pool_exhausted_count} times")

        # Critical: High failure rates
        if ws.failed_connections > ws.total_connections * 0.05:  # >5% failure
            failures.append(f"WebSocket connection failure rate: {ws.failed_connections/ws.total_connections*100:.1f}%")

        if fire.failed_fires > fire.total_fires * 0.05:
            failures.append(f"Fire command failure rate: {fire.failed_fires/fire.total_fires*100:.1f}%")

        return failures

    def save_results(self, results: LoadTestSuiteResults, output_file: str):
        """Save results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(results), f, indent=2)
        logger.info(f"Results saved to {output_file}")

    def print_summary(self, results: LoadTestSuiteResults):
        """Print human-readable summary"""
        print("\n" + "=" * 70)
        print("BITTEN v2.0 - LOAD TEST SUITE SUMMARY")
        print("=" * 70)
        print(f"\nTimestamp: {results.timestamp}")

        print(f"\n📊 TEST RESULTS:")
        print(f"   WebSocket Stress:  {'✅ PASS' if results.websocket_pass else '❌ FAIL'}")
        print(f"   Fire Burst:        {'✅ PASS' if results.fire_burst_pass else '❌ FAIL'}")
        print(f"   Signal Flood:      {'✅ PASS' if results.signal_flood_pass else '❌ FAIL'}")
        print(f"   DB Pool Stress:    {'✅ PASS' if results.db_pool_pass else '❌ FAIL'}")

        print(f"\n⚡ PERFORMANCE SUMMARY (P95 Latency):")
        perf = results.summary['performance_summary']
        print(f"   WebSocket:  {perf['websocket_p95_ms']:.2f}ms (target: <250ms)")
        print(f"   Fire:       {perf['fire_p95_ms']:.2f}ms (target: <100ms)")
        print(f"   Signal:     {perf['signal_p95_ms']:.2f}ms (target: <50ms)")
        print(f"   Database:   {perf['db_p95_ms']:.2f}ms (target: <50ms)")

        if results.summary['critical_failures']:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in results.summary['critical_failures']:
                print(f"   - {failure}")
        else:
            print(f"\n✅ No critical failures detected")

        print(f"\n🎯 OVERALL RESULT: {'✅ PASS - SYSTEM READY FOR PRODUCTION LOAD' if results.overall_pass else '❌ FAIL - OPTIMIZATION REQUIRED'}")
        print("=" * 70 + "\n")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Run BITTEN v2.0 load test suite')
    parser.add_argument('--output', help='Output JSON file path')
    args = parser.parse_args()

    # Run tests
    runner = LoadTestRunner()
    results = asyncio.run(runner.run_all_tests())

    # Print summary
    runner.print_summary(results)

    # Save results
    if args.output:
        runner.save_results(results, args.output)
    else:
        output = f"/tmp/load_test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        runner.save_results(results, output)

    # Exit code
    return 0 if results.overall_pass else 1


if __name__ == "__main__":
    exit(main())
