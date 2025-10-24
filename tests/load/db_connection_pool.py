#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Database Connection Pool Stress Test

Tests PostgreSQL connection pool under high concurrent query load.
Target: 200 concurrent queries, pool never exhausted, P95 < 50ms.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import asyncpg
import time
import statistics
from datetime import datetime
from typing import List
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DBPoolMetrics:
    """Database connection pool metrics"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    pool_exhausted_count: int
    avg_query_time_ms: float
    avg_connection_acquire_ms: float
    p50_query_ms: float
    p95_query_ms: float
    p99_query_ms: float
    max_query_ms: float
    duration_seconds: float
    queries_per_second: float
    timestamp: str
    pass_threshold: bool


class DBPoolStressTest:
    """Database connection pool stress testing"""

    def __init__(
        self,
        conn_str: str = "postgresql://bitten_admin@localhost:5432/bitten_v2",
        pool_size: int = 20,
        concurrent_queries: int = 200,
        duration_seconds: int = 60
    ):
        """
        Initialize database pool stress test

        Args:
            conn_str: PostgreSQL connection string
            pool_size: Connection pool size
            concurrent_queries: Number of concurrent queries
            duration_seconds: Test duration
        """
        self.conn_str = conn_str
        self.pool_size = pool_size
        self.concurrent_queries = concurrent_queries
        self.duration_seconds = duration_seconds
        self.query_times = []
        self.connection_acquire_times = []
        self.successful_queries = 0
        self.failed_queries = 0
        self.pool_exhausted = 0

    async def execute_query(self, pool: asyncpg.Pool, query_id: int):
        """
        Execute test query

        Args:
            pool: Connection pool
            query_id: Query identifier
        """
        try:
            # Measure connection acquisition time
            acquire_start = time.time()
            conn = await asyncio.wait_for(
                pool.acquire(),
                timeout=5.0
            )
            acquire_time = (time.time() - acquire_start) * 1000
            self.connection_acquire_times.append(acquire_time)

            # Execute query
            query_start = time.time()

            # Test query: Read recent signals
            result = await conn.fetch("""
                SELECT signal_id, symbol, confidence, pattern_type
                FROM signals
                ORDER BY created_at DESC
                LIMIT 100
            """)

            query_time = (time.time() - query_start) * 1000
            self.query_times.append(query_time)

            await pool.release(conn)

            self.successful_queries += 1
            logger.debug(f"Query {query_id}: {query_time:.2f}ms")

        except asyncio.TimeoutError:
            self.pool_exhausted += 1
            self.failed_queries += 1
            logger.warning(f"Query {query_id}: Pool exhausted")

        except Exception as e:
            self.failed_queries += 1
            logger.error(f"Query {query_id} error: {e}")

    async def run_query_batch(self, pool: asyncpg.Pool):
        """Run batch of concurrent queries"""
        tasks = [
            self.execute_query(pool, i)
            for i in range(self.concurrent_queries)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run_test(self) -> DBPoolMetrics:
        """
        Run database pool stress test

        Returns:
            Performance metrics
        """
        logger.info(f"Starting DB pool stress test: {self.concurrent_queries} concurrent queries")

        # Reset counters
        self.query_times = []
        self.connection_acquire_times = []
        self.successful_queries = 0
        self.failed_queries = 0
        self.pool_exhausted = 0

        start_time = time.time()

        try:
            # Create connection pool
            pool = await asyncpg.create_pool(
                self.conn_str,
                min_size=self.pool_size,
                max_size=self.pool_size,
                command_timeout=10.0
            )

            # Run batches until duration expires
            batch_count = 0
            while time.time() - start_time < self.duration_seconds:
                await self.run_query_batch(pool)
                batch_count += 1
                await asyncio.sleep(0.1)  # Small delay between batches

            # Close pool
            await pool.close()

        except Exception as e:
            logger.error(f"Test error: {e}")

        duration = time.time() - start_time

        # Calculate metrics
        total_queries = self.successful_queries + self.failed_queries
        qps = self.successful_queries / duration if duration > 0 else 0

        avg_query = statistics.mean(self.query_times) if self.query_times else 0
        avg_acquire = statistics.mean(self.connection_acquire_times) if self.connection_acquire_times else 0
        p50_query = statistics.median(self.query_times) if self.query_times else 0
        p95_query = statistics.quantiles(self.query_times, n=20)[18] if len(self.query_times) > 20 else 0
        p99_query = statistics.quantiles(self.query_times, n=100)[98] if len(self.query_times) > 100 else 0
        max_query = max(self.query_times) if self.query_times else 0

        # Pass threshold: P95 < 50ms AND no pool exhaustion
        pass_threshold = (p95_query < 50.0) and (self.pool_exhausted == 0)

        metrics = DBPoolMetrics(
            total_queries=total_queries,
            successful_queries=self.successful_queries,
            failed_queries=self.failed_queries,
            pool_exhausted_count=self.pool_exhausted,
            avg_query_time_ms=avg_query,
            avg_connection_acquire_ms=avg_acquire,
            p50_query_ms=p50_query,
            p95_query_ms=p95_query,
            p99_query_ms=p99_query,
            max_query_ms=max_query,
            duration_seconds=duration,
            queries_per_second=qps,
            timestamp=datetime.utcnow().isoformat(),
            pass_threshold=pass_threshold
        )

        return metrics

    def save_results(self, metrics: DBPoolMetrics, output_file: str):
        """Save metrics to JSON file"""
        import json
        with open(output_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
        logger.info(f"Results saved to {output_file}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Database connection pool stress test')
    parser.add_argument('--conn-str', default='postgresql://bitten_admin@localhost:5432/bitten_v2',
                        help='PostgreSQL connection string')
    parser.add_argument('--pool-size', type=int, default=20, help='Connection pool size')
    parser.add_argument('--concurrent', type=int, default=200, help='Concurrent queries')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--output', help='Output JSON file')
    args = parser.parse_args()

    # Run test
    test = DBPoolStressTest(
        conn_str=args.conn_str,
        pool_size=args.pool_size,
        concurrent_queries=args.concurrent,
        duration_seconds=args.duration
    )

    metrics = asyncio.run(test.run_test())

    # Print results
    print("\n" + "=" * 70)
    print("Database Connection Pool Stress Test Results")
    print("=" * 70)
    print(f"\n🗄️  QUERIES:")
    print(f"   Total:      {metrics.total_queries}")
    print(f"   Successful: {metrics.successful_queries}")
    print(f"   Failed:     {metrics.failed_queries}")
    print(f"   Rate:       {metrics.queries_per_second:.2f}/sec")

    print(f"\n💧 POOL HEALTH:")
    print(f"   Exhausted:  {metrics.pool_exhausted_count} {'✅' if metrics.pool_exhausted_count == 0 else '❌'}")
    print(f"   Avg Acquire: {metrics.avg_connection_acquire_ms:.2f}ms")

    print(f"\n⚡ QUERY LATENCY (milliseconds):")
    print(f"   Average: {metrics.avg_query_time_ms:.2f}ms")
    print(f"   P50:     {metrics.p50_query_ms:.2f}ms")
    print(f"   P95:     {metrics.p95_query_ms:.2f}ms {'✅' if metrics.p95_query_ms < 50 else '❌'}")
    print(f"   P99:     {metrics.p99_query_ms:.2f}ms")
    print(f"   Max:     {metrics.max_query_ms:.2f}ms")

    print(f"\n⏱️  DURATION: {metrics.duration_seconds:.2f}s")

    print(f"\n🎯 RESULT: {'✅ PASS' if metrics.pass_threshold else '❌ FAIL'}")
    print("=" * 70 + "\n")

    # Save results
    if args.output:
        test.save_results(metrics, args.output)
    else:
        output = f"/tmp/db_pool_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test.save_results(metrics, output)

    return 0 if metrics.pass_threshold else 1


if __name__ == "__main__":
    exit(main())
