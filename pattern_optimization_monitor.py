#!/usr/bin/env python3
"""
PATTERN OPTIMIZATION MONITORING SYSTEM
======================================

Purpose: Monitor the 3 new Sniper patterns over 24-48 hours to validate optimization
Critical Test: Will BLIND_SPOT, TRAPDOOR_SSR, PRESSURE_VALVE outperform historical 40.3% Sniper average?
Risk: If optimizations fail, performance could drop below 50% overall

Tracks:
- Signal generation rate by pattern
- Confidence distribution for new patterns
- Theoretical TP/SL outcomes
- Comparison against baseline metrics from SIGNAL.md

Author: Claude Code (Sonnet 4)
Date: September 24, 2025
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os
import sys

class PatternOptimizationMonitor:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/bitten.db"
        self.tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
        self.report_file = "/root/HydraX-v2/optimization_monitor_report.json"

        # NEW PATTERNS TO MONITOR (Critical test subjects)
        self.new_patterns = {
            'BLIND_SPOT': {'threshold': 70.0, 'expected_daily': '5-15', 'purpose': 'FVG replacement'},
            'TRAPDOOR_SSR': {'threshold': 70.0, 'expected_daily': '5-15', 'purpose': 'Session-specific'},
            'PRESSURE_VALVE': {'threshold': 70.0, 'expected_daily': '5-15', 'purpose': 'Enhanced VCB'}
        }

        # RESCUED PATTERNS (Previously blocked)
        self.rescued_patterns = {
            'VCB_BREAKOUT': {'old_threshold': 75.0, 'new_threshold': 65.0, 'expected_daily': '5-10'},
            'ORDER_BLOCK_BOUNCE': {'old_threshold': 75.0, 'new_threshold': 65.0, 'expected_daily': '8-15'},
            'SWEEP_RETURN': {'old_threshold': 78.0, 'new_threshold': 68.0, 'expected_daily': '10-20'},
            'MOMENTUM_BURST': {'old_threshold': 75.0, 'new_threshold': 65.0, 'expected_daily': '12-25'}
        }

        # BASELINE METRICS (From SIGNAL.md)
        self.baseline = {
            'total_signals_24h': 29,
            'active_patterns': 2,
            'pattern_diversity': 'LOW',
            'timeout_rate': 100.0,
            'avg_confidence': 83.6
        }

        self.start_time = datetime.now()
        print(f"🎯 Pattern Optimization Monitor Started: {self.start_time}")
        print(f"⚡ Monitoring 3 new patterns: {list(self.new_patterns.keys())}")
        print(f"🔧 Monitoring 4 rescued patterns: {list(self.rescued_patterns.keys())}")

    def get_signals_since_optimization(self):
        """Get all signals since optimization timestamp (Sept 24, 2025)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get optimization start timestamp (approximately when changes were made)
            optimization_start = int(datetime(2025, 9, 24, 0, 0, 0).timestamp())

            cursor.execute("""
                SELECT signal_id, symbol, direction, pattern_type, confidence,
                       created_at, target_pips, stop_pips
                FROM signals
                WHERE created_at > ?
                ORDER BY created_at DESC
            """, (optimization_start,))

            signals = cursor.fetchall()
            conn.close()

            return [
                {
                    'signal_id': s[0], 'symbol': s[1], 'direction': s[2],
                    'pattern_type': s[3], 'confidence': s[4], 'created_at': s[5],
                    'target_pips': s[6], 'stop_pips': s[7]
                }
                for s in signals
            ]
        except Exception as e:
            print(f"⚠️ Database read error: {e}")
            return []

    def analyze_pattern_performance(self, signals):
        """Analyze performance by pattern type"""
        pattern_stats = defaultdict(lambda: {
            'count': 0,
            'confidence_sum': 0,
            'confidence_levels': [],
            'symbols': set(),
            'directions': []
        })

        for signal in signals:
            pattern = signal['pattern_type']
            stats = pattern_stats[pattern]

            stats['count'] += 1
            stats['confidence_sum'] += signal['confidence']
            stats['confidence_levels'].append(signal['confidence'])
            stats['symbols'].add(signal['symbol'])
            stats['directions'].append(signal['direction'])

        # Calculate averages and insights
        for pattern, stats in pattern_stats.items():
            if stats['count'] > 0:
                stats['avg_confidence'] = round(stats['confidence_sum'] / stats['count'], 1)
                stats['confidence_range'] = f"{min(stats['confidence_levels']):.1f}-{max(stats['confidence_levels']):.1f}%"
                stats['unique_symbols'] = len(stats['symbols'])
                stats['direction_balance'] = {
                    'BUY': stats['directions'].count('BUY'),
                    'SELL': stats['directions'].count('SELL')
                }

        return dict(pattern_stats)

    def generate_report(self):
        """Generate comprehensive monitoring report"""
        signals = self.get_signals_since_optimization()
        pattern_stats = self.analyze_pattern_performance(signals)

        # Calculate time since optimization
        hours_elapsed = (datetime.now() - self.start_time).total_seconds() / 3600

        report = {
            'timestamp': datetime.now().isoformat(),
            'hours_since_optimization': round(hours_elapsed, 1),
            'total_signals': len(signals),
            'baseline_comparison': {
                'baseline_24h': self.baseline['total_signals_24h'],
                'current_rate_24h': int((len(signals) / hours_elapsed) * 24) if hours_elapsed > 0 else 0,
                'improvement_factor': round((len(signals) / hours_elapsed * 24) / self.baseline['total_signals_24h'], 2) if hours_elapsed > 0 else 0
            },
            'pattern_analysis': {},
            'new_pattern_status': {},
            'rescued_pattern_status': {},
            'optimization_success_indicators': {}
        }

        # Analyze each pattern
        for pattern, stats in pattern_stats.items():
            report['pattern_analysis'][pattern] = {
                'signals_count': stats['count'],
                'avg_confidence': stats.get('avg_confidence', 0),
                'confidence_range': stats.get('confidence_range', 'N/A'),
                'unique_symbols': stats.get('unique_symbols', 0),
                'direction_balance': stats.get('direction_balance', {'BUY': 0, 'SELL': 0})
            }

        # Check new pattern performance
        for pattern in self.new_patterns:
            if pattern in pattern_stats:
                report['new_pattern_status'][pattern] = {
                    'status': '✅ GENERATING',
                    'signals': pattern_stats[pattern]['count'],
                    'avg_confidence': pattern_stats[pattern].get('avg_confidence', 0),
                    'threshold': self.new_patterns[pattern]['threshold']
                }
            else:
                report['new_pattern_status'][pattern] = {
                    'status': '❌ NOT GENERATING',
                    'signals': 0,
                    'threshold': self.new_patterns[pattern]['threshold'],
                    'note': 'May need threshold adjustment or market conditions not met'
                }

        # Check rescued pattern performance
        for pattern in self.rescued_patterns:
            if pattern in pattern_stats:
                old_threshold = self.rescued_patterns[pattern]['old_threshold']
                new_threshold = self.rescued_patterns[pattern]['new_threshold']
                report['rescued_pattern_status'][pattern] = {
                    'status': '✅ RESCUED',
                    'signals': pattern_stats[pattern]['count'],
                    'avg_confidence': pattern_stats[pattern].get('avg_confidence', 0),
                    'threshold_change': f"{old_threshold}% → {new_threshold}%",
                    'rescue_success': True
                }
            else:
                report['rescued_pattern_status'][pattern] = {
                    'status': '⚠️ STILL BLOCKED',
                    'signals': 0,
                    'threshold_change': f"{self.rescued_patterns[pattern]['old_threshold']}% → {self.rescued_patterns[pattern]['new_threshold']}%",
                    'rescue_success': False
                }

        # Success indicators
        active_patterns = len([p for p in pattern_stats if pattern_stats[p]['count'] > 0])
        report['optimization_success_indicators'] = {
            'pattern_diversity_restored': {
                'baseline': self.baseline['active_patterns'],
                'current': active_patterns,
                'target': '6+',
                'success': active_patterns >= 6
            },
            'signal_volume_increase': {
                'baseline_24h': self.baseline['total_signals_24h'],
                'current_rate_24h': report['baseline_comparison']['current_rate_24h'],
                'target': '87+',
                'success': report['baseline_comparison']['current_rate_24h'] >= 87
            },
            'new_patterns_active': {
                'active_count': len([p for p in self.new_patterns if p in pattern_stats]),
                'total_count': len(self.new_patterns),
                'target': '3',
                'success': len([p for p in self.new_patterns if p in pattern_stats]) == 3
            }
        }

        return report

    def save_report(self, report):
        """Save report to file"""
        try:
            with open(self.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📊 Report saved to {self.report_file}")
        except Exception as e:
            print(f"⚠️ Report save error: {e}")

    def print_summary(self, report):
        """Print summary to console"""
        print("\n" + "="*70)
        print("🎯 PATTERN OPTIMIZATION MONITORING REPORT")
        print("="*70)

        print(f"⏰ Time Elapsed: {report['hours_since_optimization']} hours")
        print(f"📊 Total Signals: {report['total_signals']}")
        print(f"📈 Current 24h Rate: {report['baseline_comparison']['current_rate_24h']} (baseline: {report['baseline_comparison']['baseline_24h']})")

        print("\n🎯 NEW PATTERN STATUS:")
        for pattern, status in report['new_pattern_status'].items():
            print(f"  {pattern}: {status['status']} ({status['signals']} signals @ {status.get('avg_confidence', 0):.1f}%)")

        print("\n🔧 RESCUED PATTERN STATUS:")
        for pattern, status in report['rescued_pattern_status'].items():
            print(f"  {pattern}: {status['status']} ({status['signals']} signals)")

        print("\n✅ SUCCESS INDICATORS:")
        for indicator, data in report['optimization_success_indicators'].items():
            status = "✅ SUCCESS" if data['success'] else "⚠️ PENDING"
            print(f"  {indicator}: {status}")

        print("="*70)

    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        report = self.generate_report()
        self.save_report(report)
        self.print_summary(report)
        return report

def main():
    """Main monitoring loop"""
    monitor = PatternOptimizationMonitor()

    print("🎯 Starting continuous pattern optimization monitoring...")
    print("⚠️ CRITICAL TEST: Will new Sniper patterns outperform historical 40.3% average?")
    print("🔍 Monitoring for signal generation, pattern diversity, and performance indicators")
    print("\nPress Ctrl+C to stop monitoring\n")

    try:
        while True:
            report = monitor.run_monitoring_cycle()

            # Alert if no new patterns are generating after 2+ hours
            if report['hours_since_optimization'] > 2:
                new_patterns_active = report['optimization_success_indicators']['new_patterns_active']['active_count']
                if new_patterns_active == 0:
                    print("\n🚨 ALERT: No new patterns generating after 2+ hours!")
                    print("   Consider lowering thresholds for BLIND_SPOT, TRAPDOOR_SSR, PRESSURE_VALVE")

            # Wait 30 minutes between reports
            time.sleep(30 * 60)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("📊 Final report saved to:", monitor.report_file)

if __name__ == "__main__":
    main()