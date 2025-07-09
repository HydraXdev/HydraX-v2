"""
Performance Benchmark Suite for TCS++ and Stealth Protocol
Tests system performance under various loads and conditions
"""

import pytest
import time
import statistics
import json
import concurrent.futures
import threading
import psutil
import gc
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tcs_engine import score_tcs, classify_trade
from src.bitten_core.stealth_protocol import (
    StealthProtocol, StealthConfig, StealthLevel
)


class PerformanceMetrics:
    """Helper class to track performance metrics"""
    
    def __init__(self):
        self.timings = []
        self.memory_usage = []
        self.cpu_usage = []
        self.throughput = []
        
    def add_timing(self, duration: float):
        self.timings.append(duration)
        
    def add_memory(self, memory_mb: float):
        self.memory_usage.append(memory_mb)
        
    def add_cpu(self, cpu_percent: float):
        self.cpu_usage.append(cpu_percent)
        
    def add_throughput(self, ops_per_second: float):
        self.throughput.append(ops_per_second)
        
    def get_summary(self) -> Dict:
        """Get performance summary statistics"""
        return {
            'timing': {
                'mean': statistics.mean(self.timings) if self.timings else 0,
                'median': statistics.median(self.timings) if self.timings else 0,
                'min': min(self.timings) if self.timings else 0,
                'max': max(self.timings) if self.timings else 0,
                'stdev': statistics.stdev(self.timings) if len(self.timings) > 1 else 0
            },
            'memory': {
                'mean': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                'max': max(self.memory_usage) if self.memory_usage else 0
            },
            'cpu': {
                'mean': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                'max': max(self.cpu_usage) if self.cpu_usage else 0
            },
            'throughput': {
                'mean': statistics.mean(self.throughput) if self.throughput else 0,
                'max': max(self.throughput) if self.throughput else 0
            }
        }


class TestTCSPerformance:
    """Benchmark TCS++ engine performance"""
    
    def generate_signal_data(self, count: int, quality: str = 'mixed') -> List[Dict]:
        """Generate test signal data"""
        signals = []
        
        for i in range(count):
            if quality == 'high':
                # High quality signals
                signal = {
                    'trend_clarity': 0.8 + (i % 20) / 100,
                    'sr_quality': 0.85 + (i % 15) / 100,
                    'pattern_complete': True,
                    'M15_aligned': True,
                    'H1_aligned': True,
                    'H4_aligned': i % 3 != 0,
                    'D1_aligned': i % 2 == 0,
                    'rsi': 65 + (i % 15),
                    'macd_aligned': True,
                    'volume_ratio': 1.5 + (i % 10) / 10,
                    'atr': 25 + (i % 20),
                    'spread_ratio': 1.2 + (i % 5) / 10,
                    'volatility_stable': True,
                    'session': ['london', 'new_york'][i % 2],
                    'liquidity_grab': i % 3 == 0,
                    'stop_hunt_detected': i % 4 == 0,
                    'near_institutional_level': i % 2 == 0,
                    'rr': 3.0 + (i % 20) / 10,
                    'ai_sentiment_bonus': 6 + (i % 5)
                }
            elif quality == 'low':
                # Low quality signals
                signal = {
                    'trend_clarity': 0.2 + (i % 30) / 100,
                    'sr_quality': 0.3 + (i % 20) / 100,
                    'pattern_complete': False,
                    'M15_aligned': i % 4 == 0,
                    'H1_aligned': i % 3 == 0,
                    'H4_aligned': False,
                    'D1_aligned': False,
                    'rsi': 50 + (i % 10) - 5,
                    'macd_aligned': False,
                    'volume_ratio': 0.8 + (i % 10) / 20,
                    'atr': 10 + (i % 15),
                    'spread_ratio': 2.5 + (i % 10) / 10,
                    'volatility_stable': i % 3 == 0,
                    'session': ['tokyo', 'sydney', 'dead_zone'][i % 3],
                    'liquidity_grab': False,
                    'stop_hunt_detected': False,
                    'near_institutional_level': False,
                    'rr': 1.2 + (i % 10) / 10,
                    'ai_sentiment_bonus': i % 3
                }
            else:  # mixed
                # Mix of qualities
                quality_factor = (i % 10) / 10
                signal = {
                    'trend_clarity': 0.3 + quality_factor * 0.6,
                    'sr_quality': 0.4 + quality_factor * 0.5,
                    'pattern_complete': i % 3 == 0,
                    'pattern_forming': i % 3 == 1,
                    'M15_aligned': i % 2 == 0,
                    'H1_aligned': i % 3 < 2,
                    'H4_aligned': i % 4 < 2,
                    'D1_aligned': i % 5 == 0,
                    'rsi': 35 + (i % 30),
                    'macd_aligned': i % 2 == 1,
                    'macd_divergence': i % 7 == 0,
                    'volume_ratio': 0.9 + (i % 20) / 10,
                    'atr': 15 + (i % 40),
                    'spread_ratio': 1.3 + (i % 20) / 10,
                    'volatility_stable': i % 3 != 0,
                    'session': ['london', 'new_york', 'tokyo', 'sydney', 'overlap', 'dead_zone'][i % 6],
                    'liquidity_grab': i % 10 == 0,
                    'stop_hunt_detected': i % 15 == 0,
                    'near_institutional_level': i % 8 == 0,
                    'rr': 1.5 + (i % 30) / 10,
                    'ai_sentiment_bonus': i % 11
                }
                
            signals.append(signal)
            
        return signals
    
    def test_single_scoring_performance(self):
        """Test performance of single TCS scoring operations"""
        metrics = PerformanceMetrics()
        signal = self.generate_signal_data(1, 'high')[0]
        
        # Warm up
        for _ in range(10):
            score_tcs(signal)
        
        # Measure single scoring
        for _ in range(1000):
            start = time.perf_counter()
            score = score_tcs(signal)
            duration = time.perf_counter() - start
            
            metrics.add_timing(duration * 1000)  # Convert to ms
            
        summary = metrics.get_summary()
        
        # Performance assertions
        assert summary['timing']['mean'] < 0.1  # Average under 0.1ms
        assert summary['timing']['max'] < 1.0   # Max under 1ms
        print(f"\nSingle scoring performance: {summary['timing']}")
    
    def test_batch_scoring_performance(self):
        """Test performance of batch TCS scoring"""
        batch_sizes = [10, 100, 1000, 10000]
        
        for batch_size in batch_sizes:
            metrics = PerformanceMetrics()
            signals = self.generate_signal_data(batch_size, 'mixed')
            
            # Run multiple iterations
            for iteration in range(10):
                start = time.perf_counter()
                
                scores = []
                for signal in signals:
                    score = score_tcs(signal)
                    trade_type = classify_trade(score, signal['rr'], signal)
                    scores.append((score, trade_type))
                    
                duration = time.perf_counter() - start
                
                metrics.add_timing(duration)
                metrics.add_throughput(batch_size / duration)
                
            summary = metrics.get_summary()
            
            print(f"\nBatch size {batch_size}:")
            print(f"  Average time: {summary['timing']['mean']:.3f}s")
            print(f"  Throughput: {summary['throughput']['mean']:.0f} ops/sec")
            
            # Performance requirements
            if batch_size <= 1000:
                assert summary['timing']['mean'] < 1.0  # Under 1 second for 1000
            assert summary['throughput']['mean'] > 1000  # At least 1000 ops/sec
    
    def test_concurrent_scoring(self):
        """Test TCS scoring under concurrent load"""
        metrics = PerformanceMetrics()
        signals = self.generate_signal_data(1000, 'mixed')
        
        def score_batch(signal_batch):
            results = []
            for signal in signal_batch:
                score = score_tcs(signal)
                trade_type = classify_trade(score, signal['rr'], signal)
                results.append((score, trade_type))
            return results
        
        # Test with different thread counts
        thread_counts = [1, 2, 4, 8]
        
        for num_threads in thread_counts:
            # Split signals into chunks
            chunk_size = len(signals) // num_threads
            chunks = [signals[i:i + chunk_size] for i in range(0, len(signals), chunk_size)]
            
            start = time.perf_counter()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(score_batch, chunk) for chunk in chunks]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
            duration = time.perf_counter() - start
            
            throughput = len(signals) / duration
            print(f"\nConcurrent scoring ({num_threads} threads):")
            print(f"  Time: {duration:.3f}s")
            print(f"  Throughput: {throughput:.0f} ops/sec")
            
            assert throughput > 500  # Minimum performance requirement
    
    def test_memory_efficiency(self):
        """Test memory usage of TCS scoring"""
        process = psutil.Process()
        metrics = PerformanceMetrics()
        
        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate large dataset
        signals = self.generate_signal_data(10000, 'mixed')
        
        # Score all signals
        scores = []
        for i, signal in enumerate(signals):
            score = score_tcs(signal)
            trade_type = classify_trade(score, signal['rr'], signal)
            scores.append((score, trade_type))
            
            # Check memory periodically
            if i % 1000 == 0:
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - baseline_memory
                metrics.add_memory(memory_increase)
        
        # Final memory check
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - baseline_memory
        
        print(f"\nMemory usage for 10,000 signals:")
        print(f"  Baseline: {baseline_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Increase: {total_increase:.1f} MB")
        
        # Memory should not increase excessively
        assert total_increase < 100  # Less than 100MB increase


class TestStealthProtocolPerformance:
    """Benchmark stealth protocol performance"""
    
    def generate_trade_params(self, count: int) -> List[Dict]:
        """Generate test trade parameters"""
        trades = []
        
        for i in range(count):
            trade = {
                'symbol': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'][i % 4],
                'trade_id': f'perf_test_{i:06d}',
                'volume': 1.0 + (i % 10) / 10,
                'tp': 1.2100 + (i % 100) / 10000,
                'sl': 1.1900 - (i % 100) / 10000,
                'fire_mode': ['single_shot', 'burst', 'full_auto', 'sniper'][i % 4]
            }
            trades.append(trade)
            
        return trades
    
    def test_stealth_application_performance(self):
        """Test performance of stealth protocol application"""
        stealth = StealthProtocol()
        metrics = PerformanceMetrics()
        trades = self.generate_trade_params(1000)
        
        # Warm up
        for trade in trades[:10]:
            stealth.apply_full_stealth(trade)
        
        # Measure performance
        for trade in trades:
            start = time.perf_counter()
            result = stealth.apply_full_stealth(trade)
            duration = time.perf_counter() - start
            
            metrics.add_timing(duration * 1000)  # Convert to ms
            
        summary = metrics.get_summary()
        
        print(f"\nStealth application performance:")
        print(f"  Mean: {summary['timing']['mean']:.3f} ms")
        print(f"  Max: {summary['timing']['max']:.3f} ms")
        
        assert summary['timing']['mean'] < 1.0  # Average under 1ms
        assert summary['timing']['max'] < 10.0  # Max under 10ms
    
    def test_stealth_levels_performance(self):
        """Test performance impact of different stealth levels"""
        trades = self.generate_trade_params(1000)
        
        for level in StealthLevel:
            config = StealthConfig(level=level)
            stealth = StealthProtocol(config)
            metrics = PerformanceMetrics()
            
            start = time.perf_counter()
            
            executed = 0
            skipped = 0
            
            for trade in trades:
                result = stealth.apply_full_stealth(trade)
                if result.get('skip_trade'):
                    skipped += 1
                else:
                    executed += 1
                    
            duration = time.perf_counter() - start
            throughput = len(trades) / duration
            
            metrics.add_throughput(throughput)
            
            print(f"\nStealth level {level.value}:")
            print(f"  Time: {duration:.3f}s")
            print(f"  Throughput: {throughput:.0f} trades/sec")
            print(f"  Executed: {executed}, Skipped: {skipped}")
            
            assert throughput > 500  # Minimum performance for any level
    
    def test_volume_cap_performance(self):
        """Test performance of volume cap checks"""
        config = StealthConfig(
            max_concurrent_per_asset=5,
            max_total_concurrent=20
        )
        stealth = StealthProtocol(config)
        metrics = PerformanceMetrics()
        
        # Simulate many trades across different assets
        assets = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD', 'USDCAD', 'EURGBP', 'EURJPY']
        
        start = time.perf_counter()
        
        for i in range(10000):
            asset = assets[i % len(assets)]
            trade_id = f'vol_test_{i:06d}'
            
            # Check volume cap
            allowed = stealth.vol_cap(asset, trade_id)
            
            # Simulate some trades completing
            if i % 100 == 0 and i > 0:
                # Remove some trades
                for asset in assets:
                    if asset in stealth.active_trades and stealth.active_trades[asset]:
                        stealth.remove_completed_trade(asset, stealth.active_trades[asset][0])
                        
        duration = time.perf_counter() - start
        operations_per_second = 10000 / duration
        
        print(f"\nVolume cap performance:")
        print(f"  10,000 operations in {duration:.3f}s")
        print(f"  {operations_per_second:.0f} ops/sec")
        
        assert operations_per_second > 10000  # Should handle 10k+ ops/sec
    
    def test_shuffle_performance(self):
        """Test performance of execution shuffle"""
        stealth = StealthProtocol()
        
        queue_sizes = [10, 50, 100, 500]
        
        for size in queue_sizes:
            trades = self.generate_trade_params(size)
            metrics = PerformanceMetrics()
            
            # Run multiple iterations
            for _ in range(100):
                start = time.perf_counter()
                shuffled = stealth.execution_shuffle(trades)
                duration = time.perf_counter() - start
                
                metrics.add_timing(duration * 1000)
                
            summary = metrics.get_summary()
            
            print(f"\nShuffle performance (queue size {size}):")
            print(f"  Mean: {summary['timing']['mean']:.3f} ms")
            print(f"  Max: {summary['timing']['max']:.3f} ms")
            
            # Performance requirements
            assert summary['timing']['mean'] < size * 0.01  # Linear time complexity


class TestIntegratedPerformance:
    """Test performance of integrated TCS++ and stealth systems"""
    
    def test_full_pipeline_performance(self):
        """Test complete signal -> score -> stealth -> execution pipeline"""
        metrics = PerformanceMetrics()
        stealth = StealthProtocol()
        
        # Generate test data
        test_count = 5000
        signals = []
        
        for i in range(test_count):
            signal = {
                'trend_clarity': (i % 10) / 10,
                'sr_quality': ((i + 3) % 10) / 10,
                'pattern_complete': i % 3 == 0,
                'M15_aligned': i % 2 == 0,
                'H1_aligned': i % 3 < 2,
                'H4_aligned': i % 4 < 2,
                'D1_aligned': i % 5 == 0,
                'rsi': 30 + (i % 40),
                'macd_aligned': i % 2 == 1,
                'volume_ratio': 1.0 + (i % 20) / 10,
                'atr': 10 + (i % 50),
                'spread_ratio': 1.0 + (i % 30) / 10,
                'volatility_stable': i % 3 != 0,
                'session': ['london', 'new_york', 'tokyo', 'sydney'][i % 4],
                'rr': 1.0 + (i % 40) / 10,
                'ai_sentiment_bonus': i % 11
            }
            signals.append(signal)
        
        # Measure full pipeline
        start = time.perf_counter()
        
        results = []
        for i, signal in enumerate(signals):
            # TCS scoring
            score = score_tcs(signal)
            trade_type = classify_trade(score, signal['rr'], signal)
            
            # Skip if below threshold
            if trade_type == 'none':
                continue
                
            # Create trade parameters
            trade_params = {
                'symbol': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'][i % 4],
                'trade_id': f'pipeline_{i:06d}',
                'volume': 1.0,
                'tp': 1.2100 + (i % 100) / 10000,
                'sl': 1.1900 - (i % 100) / 10000,
                'tcs_score': score,
                'trade_type': trade_type
            }
            
            # Apply stealth
            result = stealth.apply_full_stealth(trade_params)
            results.append(result)
            
            # Simulate trade management
            if i % 50 == 0 and i > 0:
                # Clean up some trades
                for asset in list(stealth.active_trades.keys()):
                    if stealth.active_trades[asset]:
                        stealth.remove_completed_trade(asset, stealth.active_trades[asset][0])
                        
        duration = time.perf_counter() - start
        throughput = test_count / duration
        
        executed = sum(1 for r in results if not r.get('skip_trade'))
        skipped = sum(1 for r in results if r.get('skip_trade'))
        
        print(f"\nFull pipeline performance:")
        print(f"  Processed {test_count} signals in {duration:.3f}s")
        print(f"  Throughput: {throughput:.0f} signals/sec")
        print(f"  Executed: {executed}, Skipped: {skipped}")
        
        assert throughput > 1000  # Should process 1000+ signals/sec
    
    def test_stress_test(self):
        """Stress test with high load"""
        stealth = StealthProtocol()
        process = psutil.Process()
        
        # Monitor resources
        initial_memory = process.memory_info().rss / 1024 / 1024
        initial_cpu = process.cpu_percent(interval=0.1)
        
        # Generate heavy load
        signal_count = 50000
        batch_size = 1000
        
        start = time.perf_counter()
        
        for batch_start in range(0, signal_count, batch_size):
            # Generate batch
            batch_signals = []
            for i in range(batch_start, min(batch_start + batch_size, signal_count)):
                signal = {
                    'trend_clarity': 0.7,
                    'sr_quality': 0.8,
                    'pattern_complete': i % 5 == 0,
                    'M15_aligned': True,
                    'H1_aligned': i % 2 == 0,
                    'H4_aligned': i % 3 == 0,
                    'D1_aligned': False,
                    'rsi': 60 + (i % 20),
                    'macd_aligned': i % 2 == 1,
                    'volume_ratio': 1.3,
                    'atr': 25,
                    'spread_ratio': 1.5,
                    'volatility_stable': True,
                    'session': 'new_york',
                    'rr': 2.0,
                    'ai_sentiment_bonus': 5
                }
                batch_signals.append(signal)
            
            # Process batch
            for signal in batch_signals:
                score = score_tcs(signal)
                
                if score >= 75:  # Only process decent signals
                    trade = {
                        'symbol': 'EURUSD',
                        'trade_id': f'stress_{batch_start + i}',
                        'volume': 1.0,
                        'tp': 1.2100,
                        'sl': 1.1900
                    }
                    stealth.apply_full_stealth(trade)
                    
        duration = time.perf_counter() - start
        
        # Check resource usage
        final_memory = process.memory_info().rss / 1024 / 1024
        peak_cpu = process.cpu_percent(interval=0.1)
        
        memory_increase = final_memory - initial_memory
        
        print(f"\nStress test results ({signal_count} signals):")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {signal_count / duration:.0f} signals/sec")
        print(f"  Memory increase: {memory_increase:.1f} MB")
        print(f"  CPU usage: {peak_cpu:.1f}%")
        
        # Performance requirements under stress
        assert duration < 60  # Should complete in under 1 minute
        assert memory_increase < 500  # Memory increase under 500MB
    
    def test_latency_percentiles(self):
        """Test latency percentiles for SLA compliance"""
        stealth = StealthProtocol()
        latencies = []
        
        # Generate realistic workload
        for i in range(10000):
            signal = {
                'trend_clarity': 0.7,
                'sr_quality': 0.75,
                'pattern_complete': i % 4 == 0,
                'M15_aligned': True,
                'H1_aligned': True,
                'H4_aligned': i % 2 == 0,
                'D1_aligned': False,
                'rsi': 65,
                'macd_aligned': True,
                'volume_ratio': 1.4,
                'atr': 28,
                'spread_ratio': 1.4,
                'volatility_stable': True,
                'session': 'london',
                'rr': 2.8,
                'ai_sentiment_bonus': 6
            }
            
            # Measure end-to-end latency
            start = time.perf_counter()
            
            # TCS scoring
            score = score_tcs(signal)
            trade_type = classify_trade(score, signal['rr'], signal)
            
            # Stealth application
            if trade_type != 'none':
                trade = {
                    'symbol': 'EURUSD',
                    'trade_id': f'latency_{i}',
                    'volume': 1.0,
                    'tp': 1.2100,
                    'sl': 1.1900
                }
                stealth.apply_full_stealth(trade)
                
            latency = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(latency)
        
        # Calculate percentiles
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p90 = latencies[int(len(latencies) * 0.90)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        
        print(f"\nLatency percentiles (ms):")
        print(f"  P50: {p50:.3f}")
        print(f"  P90: {p90:.3f}")
        print(f"  P95: {p95:.3f}")
        print(f"  P99: {p99:.3f}")
        
        # SLA requirements
        assert p50 < 1.0   # 50th percentile under 1ms
        assert p90 < 2.0   # 90th percentile under 2ms
        assert p95 < 5.0   # 95th percentile under 5ms
        assert p99 < 10.0  # 99th percentile under 10ms


class TestScalabilityBenchmarks:
    """Test system scalability"""
    
    def test_horizontal_scaling(self):
        """Test performance with multiple instances"""
        import multiprocessing
        
        def process_signals(process_id, signal_count):
            """Worker function for processing signals"""
            stealth = StealthProtocol()
            
            start = time.perf_counter()
            
            for i in range(signal_count):
                signal = {
                    'trend_clarity': 0.7,
                    'sr_quality': 0.8,
                    'rsi': 65,
                    'volume_ratio': 1.4,
                    'atr': 30,
                    'session': 'london',
                    'rr': 2.5
                }
                
                score = score_tcs(signal)
                
                if score >= 75:
                    trade = {
                        'symbol': 'EURUSD',
                        'trade_id': f'proc_{process_id}_{i}',
                        'volume': 1.0,
                        'tp': 1.2100,
                        'sl': 1.1900
                    }
                    stealth.apply_full_stealth(trade)
                    
            duration = time.perf_counter() - start
            return signal_count / duration
        
        # Test with different process counts
        process_counts = [1, 2, 4, 8]
        signals_per_process = 5000
        
        for num_processes in process_counts:
            with multiprocessing.Pool(processes=num_processes) as pool:
                start = time.perf_counter()
                
                # Launch parallel processes
                results = pool.starmap(
                    process_signals,
                    [(i, signals_per_process) for i in range(num_processes)]
                )
                
                duration = time.perf_counter() - start
                
            total_throughput = sum(results)
            avg_throughput = total_throughput / num_processes
            
            print(f"\nHorizontal scaling ({num_processes} processes):")
            print(f"  Total throughput: {total_throughput:.0f} signals/sec")
            print(f"  Per-process avg: {avg_throughput:.0f} signals/sec")
            print(f"  Duration: {duration:.2f}s")
            
            # Should scale reasonably well
            if num_processes > 1:
                assert total_throughput > results[0] * 0.7 * num_processes


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])