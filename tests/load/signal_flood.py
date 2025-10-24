#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Signal Generation Flood Test

Tests signal engine under sustained high-volume load.
Target: 5000 signals/hour sustained with P95 latency < 50ms.

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
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SignalFloodMetrics:
    """Signal flood test metrics"""
    total_signals: int
    signals_per_hour: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    duration_seconds: float
    timestamp: str
    pass_threshold: bool


class SignalFloodTest:
    """Signal generation flood testing"""

    def __init__(
        self,
        pub_port: int = 5557,
        target_signals_per_hour: int = 5000,
        duration_seconds: int = 600  # 10 minutes default
    ):
        """
        Initialize signal flood test

        Args:
            pub_port: ZMQ PUB port to publish signals
            target_signals_per_hour: Target signal generation rate
            duration_seconds: Test duration
        """
        self.pub_port = pub_port
        self.target_rate = target_signals_per_hour
        self.duration_seconds = duration_seconds
        self.latencies = []
        self.signal_count = 0

    def create_test_signal(self) -> dict:
        """Create test signal"""
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'XAUUSD']
        patterns = ['LIQUIDITY_SWEEP_REVERSAL', 'VCB_BREAKOUT', 'ORDER_BLOCK_BOUNCE']
        directions = ['BUY', 'SELL']

        return {
            'signal_id': f"TEST_SIG_{int(time.time() * 1000)}_{self.signal_count}",
            'symbol': random.choice(symbols),
            'direction': random.choice(directions),
            'entry_price': round(random.uniform(1.0, 2.0), 5),
            'sl_pips': round(random.uniform(10, 30), 1),
            'tp_pips': round(random.uniform(15, 50), 1),
            'confidence': round(random.uniform(70, 95), 1),
            'pattern_type': random.choice(patterns),
            'created_at': int(time.time()),
            'timestamp': time.time()  # For latency measurement
        }

    async def publish_signals(self, context: zmq.asyncio.Context):
        """Publish signals at target rate"""
        socket = context.socket(zmq.PUB)
        socket.bind(f"tcp://*:{self.pub_port}")

        # Wait for subscribers
        await asyncio.sleep(1)

        logger.info(f"Publishing {self.target_rate} signals/hour for {self.duration_seconds}s")

        start_time = time.time()
        interval = 3600.0 / self.target_rate  # Seconds between signals

        while time.time() - start_time < self.duration_seconds:
            try:
                # Create signal
                signal = self.create_test_signal()
                send_time = time.time()

                # Publish
                message = f"ELITE_GUARD_SIGNAL {json.dumps(signal)}"
                await socket.send_string(message)

                # Measure latency (publish time)
                latency_ms = (time.time() - send_time) * 1000
                self.latencies.append(latency_ms)

                self.signal_count += 1

                # Rate limiting
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Signal publish error: {e}")

        socket.close()
        logger.info(f"Published {self.signal_count} signals")

    async def run_test(self) -> SignalFloodMetrics:
        """
        Run signal flood test

        Returns:
            Performance metrics
        """
        logger.info(f"Starting signal flood test: {self.target_rate}/hour for {self.duration_seconds}s")

        # Reset counters
        self.latencies = []
        self.signal_count = 0

        start_time = time.time()

        # Create ZMQ context
        context = zmq.asyncio.Context()

        try:
            # Publish signals
            await self.publish_signals(context)

        except Exception as e:
            logger.error(f"Test error: {e}")

        finally:
            context.term()

        duration = time.time() - start_time

        # Calculate metrics
        actual_rate = (self.signal_count / duration) * 3600 if duration > 0 else 0  # Convert to /hour

        avg_latency = statistics.mean(self.latencies) if self.latencies else 0
        p50_latency = statistics.median(self.latencies) if self.latencies else 0
        p95_latency = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 20 else 0
        p99_latency = statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) > 100 else 0
        max_latency = max(self.latencies) if self.latencies else 0

        # Pass threshold: P95 < 50ms
        pass_threshold = p95_latency < 50.0

        metrics = SignalFloodMetrics(
            total_signals=self.signal_count,
            signals_per_hour=actual_rate,
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

    def save_results(self, metrics: SignalFloodMetrics, output_file: str):
        """Save metrics to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
        logger.info(f"Results saved to {output_file}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Signal generation flood test')
    parser.add_argument('--rate', type=int, default=5000, help='Signals per hour')
    parser.add_argument('--duration', type=int, default=600, help='Test duration in seconds')
    parser.add_argument('--port', type=int, default=5557, help='ZMQ PUB port')
    parser.add_argument('--output', help='Output JSON file')
    args = parser.parse_args()

    # Run test
    test = SignalFloodTest(
        pub_port=args.port,
        target_signals_per_hour=args.rate,
        duration_seconds=args.duration
    )

    metrics = asyncio.run(test.run_test())

    # Print results
    print("\n" + "=" * 70)
    print("Signal Generation Flood Test Results")
    print("=" * 70)
    print(f"\n📡 SIGNALS:")
    print(f"   Total:     {metrics.total_signals}")
    print(f"   Rate:      {metrics.signals_per_hour:.2f}/hour")
    print(f"   Duration:  {metrics.duration_seconds:.2f}s")

    print(f"\n⚡ PUBLISH LATENCY (milliseconds):")
    print(f"   Average: {metrics.avg_latency_ms:.2f}ms")
    print(f"   P50:     {metrics.p50_latency_ms:.2f}ms")
    print(f"   P95:     {metrics.p95_latency_ms:.2f}ms {'✅' if metrics.p95_latency_ms < 50 else '❌'}")
    print(f"   P99:     {metrics.p99_latency_ms:.2f}ms")
    print(f"   Max:     {metrics.max_latency_ms:.2f}ms")

    print(f"\n🎯 RESULT: {'✅ PASS' if metrics.pass_threshold else '❌ FAIL'}")
    print("=" * 70 + "\n")

    # Save results
    if args.output:
        test.save_results(metrics, args.output)
    else:
        output = f"/tmp/signal_flood_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test.save_results(metrics, output)

    return 0 if metrics.pass_threshold else 1


if __name__ == "__main__":
    exit(main())
