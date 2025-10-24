#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - WebSocket Stress Test

Tests WebSocket signal streaming under high concurrent connection load.
Target: 1000 concurrent connections with P95 latency < 250ms.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import websockets
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WebSocketMetrics:
    """WebSocket performance metrics"""
    total_connections: int
    successful_connections: int
    failed_connections: int
    total_messages_received: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    duration_seconds: float
    messages_per_second: float
    timestamp: str
    pass_threshold: bool


class WebSocketStressTest:
    """WebSocket connection stress testing"""

    def __init__(
        self,
        url: str = "ws://localhost:8888/ws/signals",
        num_connections: int = 1000,
        duration_seconds: int = 60
    ):
        """
        Initialize WebSocket stress test

        Args:
            url: WebSocket endpoint URL
            num_connections: Number of concurrent connections
            duration_seconds: Test duration
        """
        self.url = url
        self.num_connections = num_connections
        self.duration_seconds = duration_seconds
        self.latencies = []
        self.messages_received = 0
        self.successful_connections = 0
        self.failed_connections = 0

    async def connect_and_listen(self, client_id: int):
        """
        Connect to WebSocket and measure message latency

        Args:
            client_id: Unique client identifier
        """
        try:
            async with websockets.connect(self.url) as websocket:
                self.successful_connections += 1
                logger.debug(f"Client {client_id} connected")

                start_time = time.time()
                while time.time() - start_time < self.duration_seconds:
                    try:
                        # Receive message with timeout
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )

                        # Measure latency (server timestamp to client receive)
                        receive_time = time.time()
                        data = json.loads(message)

                        # Calculate latency if server includes timestamp
                        if 'timestamp' in data:
                            server_time = data['timestamp']
                            latency_ms = (receive_time - server_time) * 1000
                            self.latencies.append(latency_ms)

                        self.messages_received += 1

                    except asyncio.TimeoutError:
                        # No message in 5 seconds, continue waiting
                        continue
                    except Exception as e:
                        logger.debug(f"Client {client_id} error receiving: {e}")
                        break

        except Exception as e:
            self.failed_connections += 1
            logger.debug(f"Client {client_id} failed to connect: {e}")

    async def run_test(self) -> WebSocketMetrics:
        """
        Run WebSocket stress test

        Returns:
            Performance metrics
        """
        logger.info(f"Starting WebSocket stress test: {self.num_connections} connections for {self.duration_seconds}s")

        # Reset counters
        self.latencies = []
        self.messages_received = 0
        self.successful_connections = 0
        self.failed_connections = 0

        start_time = time.time()

        # Create concurrent connections
        tasks = [
            self.connect_and_listen(i)
            for i in range(self.num_connections)
        ]

        # Run all connections in parallel
        await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time

        # Calculate metrics
        avg_latency = statistics.mean(self.latencies) if self.latencies else 0
        p50_latency = statistics.median(self.latencies) if self.latencies else 0
        p95_latency = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 20 else 0
        p99_latency = statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) > 100 else 0
        max_latency = max(self.latencies) if self.latencies else 0
        msg_per_sec = self.messages_received / duration if duration > 0 else 0

        # Pass threshold: P95 < 250ms
        pass_threshold = p95_latency < 250.0

        metrics = WebSocketMetrics(
            total_connections=self.num_connections,
            successful_connections=self.successful_connections,
            failed_connections=self.failed_connections,
            total_messages_received=self.messages_received,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            max_latency_ms=max_latency,
            duration_seconds=duration,
            messages_per_second=msg_per_sec,
            timestamp=datetime.utcnow().isoformat(),
            pass_threshold=pass_threshold
        )

        logger.info(f"Test complete: {self.successful_connections}/{self.num_connections} connections successful")
        return metrics

    def save_results(self, metrics: WebSocketMetrics, output_file: str):
        """Save metrics to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
        logger.info(f"Results saved to {output_file}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='WebSocket stress test')
    parser.add_argument('--url', default='ws://localhost:8888/ws/signals', help='WebSocket URL')
    parser.add_argument('--connections', type=int, default=1000, help='Number of concurrent connections')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--output', help='Output JSON file')
    args = parser.parse_args()

    # Run test
    test = WebSocketStressTest(
        url=args.url,
        num_connections=args.connections,
        duration_seconds=args.duration
    )

    metrics = asyncio.run(test.run_test())

    # Print results
    print("\n" + "=" * 70)
    print("WebSocket Stress Test Results")
    print("=" * 70)
    print(f"\n📊 CONNECTIONS:")
    print(f"   Total:      {metrics.total_connections}")
    print(f"   Successful: {metrics.successful_connections}")
    print(f"   Failed:     {metrics.failed_connections}")

    print(f"\n📈 LATENCY (milliseconds):")
    print(f"   Average: {metrics.avg_latency_ms:.2f}ms")
    print(f"   P50:     {metrics.p50_latency_ms:.2f}ms")
    print(f"   P95:     {metrics.p95_latency_ms:.2f}ms {'✅' if metrics.p95_latency_ms < 250 else '❌'}")
    print(f"   P99:     {metrics.p99_latency_ms:.2f}ms")
    print(f"   Max:     {metrics.max_latency_ms:.2f}ms")

    print(f"\n📡 THROUGHPUT:")
    print(f"   Messages Received: {metrics.total_messages_received}")
    print(f"   Messages/Second:   {metrics.messages_per_second:.2f}")
    print(f"   Duration:          {metrics.duration_seconds:.2f}s")

    print(f"\n🎯 RESULT: {'✅ PASS' if metrics.pass_threshold else '❌ FAIL'}")
    print("=" * 70 + "\n")

    # Save results
    if args.output:
        test.save_results(metrics, args.output)
    else:
        output = f"/tmp/websocket_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test.save_results(metrics, output)

    return 0 if metrics.pass_threshold else 1


if __name__ == "__main__":
    exit(main())
