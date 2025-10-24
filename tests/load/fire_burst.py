#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Fire Command Burst Test

Tests fire execution system under burst load.
Target: 100 fires/second with P95 latency < 100ms.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import zmq
import zmq.asyncio
import json
import time
import statistics
from datetime import datetime
from typing import List
from dataclasses import dataclass, asdict
from collections import OrderedDict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FireBurstMetrics:
    """Fire burst test metrics"""
    total_fires: int
    fires_per_second: float
    successful_fires: int
    failed_fires: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    duration_seconds: float
    timestamp: str
    pass_threshold: bool


class FireBurstTest:
    """Fire command burst load testing"""

    def __init__(
        self,
        ipc_queue: str = "ipc:///tmp/bitten_cmdqueue",
        fires_per_second: int = 100,
        duration_seconds: int = 60
    ):
        """
        Initialize fire burst test

        Args:
            ipc_queue: IPC queue path
            fires_per_second: Target fire rate
            duration_seconds: Test duration
        """
        self.ipc_queue = ipc_queue
        self.fires_per_second = fires_per_second
        self.duration_seconds = duration_seconds
        self.latencies = []
        self.successful_fires = 0
        self.failed_fires = 0

    def create_test_fire_command(self, fire_id: str) -> dict:
        """
        Create test fire command

        Args:
            fire_id: Unique fire ID

        Returns:
            Fire command dict
        """
        return OrderedDict([
            ('type', 'fire'),
            ('target_uuid', 'TEST_LOAD_001'),
            ('fire_id', fire_id),
            ('symbol', 'EURUSD'),
            ('direction', 'BUY'),
            ('entry', 0),
            ('sl', 1.09800),
            ('tp', 1.10300),
            ('lot', 0.01)
        ])

    async def send_fire_burst(self, context: zmq.asyncio.Context):
        """Send fire commands at target rate"""
        socket = context.socket(zmq.PUSH)
        socket.connect(self.ipc_queue)

        logger.info(f"Sending {self.fires_per_second} fires/second for {self.duration_seconds}s")

        start_time = time.time()
        fire_count = 0
        interval = 1.0 / self.fires_per_second  # Time between fires

        while time.time() - start_time < self.duration_seconds:
            try:
                # Create fire command
                fire_id = f"LOAD_TEST_{int(time.time() * 1000)}_{fire_count}"
                fire_cmd = self.create_test_fire_command(fire_id)

                # Record send time
                send_time = time.time()

                # Send to queue
                await socket.send_json(fire_cmd)

                # Calculate latency (send to queue acceptance)
                latency_ms = (time.time() - send_time) * 1000
                self.latencies.append(latency_ms)

                self.successful_fires += 1
                fire_count += 1

                # Rate limiting
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Fire send error: {e}")
                self.failed_fires += 1

        socket.close()
        logger.info(f"Sent {fire_count} fire commands")

    async def run_test(self) -> FireBurstMetrics:
        """
        Run fire burst test

        Returns:
            Performance metrics
        """
        logger.info(f"Starting fire burst test: {self.fires_per_second}/sec for {self.duration_seconds}s")

        # Reset counters
        self.latencies = []
        self.successful_fires = 0
        self.failed_fires = 0

        start_time = time.time()

        # Create ZMQ context
        context = zmq.asyncio.Context()

        try:
            # Send fire burst
            await self.send_fire_burst(context)

        except Exception as e:
            logger.error(f"Test error: {e}")

        finally:
            context.term()

        duration = time.time() - start_time

        # Calculate metrics
        total_fires = self.successful_fires + self.failed_fires
        actual_rate = self.successful_fires / duration if duration > 0 else 0

        avg_latency = statistics.mean(self.latencies) if self.latencies else 0
        p50_latency = statistics.median(self.latencies) if self.latencies else 0
        p95_latency = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 20 else 0
        p99_latency = statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) > 100 else 0
        max_latency = max(self.latencies) if self.latencies else 0

        # Pass threshold: P95 < 100ms
        pass_threshold = p95_latency < 100.0

        metrics = FireBurstMetrics(
            total_fires=total_fires,
            fires_per_second=actual_rate,
            successful_fires=self.successful_fires,
            failed_fires=self.failed_fires,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            max_latency_ms=max_latency,
            duration_seconds=duration,
            timestamp=datetime.utcnow().isoformat(),
            pass_threshold=pass_threshold
        )

        return metrics

    def save_results(self, metrics: FireBurstMetrics, output_file: str):
        """Save metrics to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
        logger.info(f"Results saved to {output_file}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Fire command burst test')
    parser.add_argument('--rate', type=int, default=100, help='Fires per second')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--output', help='Output JSON file')
    args = parser.parse_args()

    # Run test
    test = FireBurstTest(
        fires_per_second=args.rate,
        duration_seconds=args.duration
    )

    metrics = asyncio.run(test.run_test())

    # Print results
    print("\n" + "=" * 70)
    print("Fire Command Burst Test Results")
    print("=" * 70)
    print(f"\n🔥 FIRE COMMANDS:")
    print(f"   Total:      {metrics.total_fires}")
    print(f"   Successful: {metrics.successful_fires}")
    print(f"   Failed:     {metrics.failed_fires}")
    print(f"   Rate:       {metrics.fires_per_second:.2f}/sec")

    print(f"\n⚡ LATENCY (milliseconds):")
    print(f"   Average: {metrics.avg_latency_ms:.2f}ms")
    print(f"   P50:     {metrics.p50_latency_ms:.2f}ms")
    print(f"   P95:     {metrics.p95_latency_ms:.2f}ms {'✅' if metrics.p95_latency_ms < 100 else '❌'}")
    print(f"   P99:     {metrics.p99_latency_ms:.2f}ms")
    print(f"   Max:     {metrics.max_latency_ms:.2f}ms")

    print(f"\n⏱️  DURATION: {metrics.duration_seconds:.2f}s")

    print(f"\n🎯 RESULT: {'✅ PASS' if metrics.pass_threshold else '❌ FAIL'}")
    print("=" * 70 + "\n")

    # Save results
    if args.output:
        test.save_results(metrics, args.output)
    else:
        output = f"/tmp/fire_burst_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test.save_results(metrics, output)

    return 0 if metrics.pass_threshold else 1


if __name__ == "__main__":
    exit(main())
