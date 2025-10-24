#!/usr/bin/env python3
"""
PATTERN DIAGNOSTICS - Observation-only monitoring of pattern detection
Runs alongside live trading, captures all pattern execution data, identifies issues
"""

import json
import time
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

class PatternDiagnostics:
    """Non-invasive pattern monitoring and diagnostics"""

    def __init__(self, elite_guard_instance):
        self.guard = elite_guard_instance
        self.start_time = time.time()
        self.scan_count = 0

        # Pattern execution data
        self.pattern_stats = defaultdict(lambda: {
            'total_checks': 0,
            'triggered': 0,
            'ml_filtered': 0,
            'exceptions': 0,
            'data_issues': [],
            'blocking_conditions': defaultdict(int),
            'max_values_seen': {},
            'min_values_seen': {},
            'last_trigger_time': None,
            'execution_times': [],
        })

        # Track data health
        self.data_health = defaultdict(lambda: {
            'm1_candle_count': [],
            'm5_candle_count': [],
            'm15_candle_count': [],
            'tick_freshness': [],
            'has_rsi': 0,
            'has_atr': 0,
            'has_volume': 0,
        })

        # Patterns to monitor
        self.patterns = [
            'detect_liquidity_sweep_reversal',
            'detect_order_block_bounce',
            'detect_blind_spot',
            'detect_trapdoor_ssr',
            'detect_pressure_valve',
            'detect_vcb_breakout',
            'detect_sweep_and_return',
            'detect_momentum_breakout',
            'detect_bb_scalp',
            'detect_kalman_quickfire',
            'detect_ema_rsi_bb_vwap',
            'detect_ema_rsi_scalp',
            'detect_fair_value_gap_fill',
            'detect_enhanced_impulsive_breakout',
        ]

        print("🔍 Pattern Diagnostics initialized")
        print(f"   Monitoring {len(self.patterns)} patterns")
        print(f"   Target: 20 scan cycles or 5 minutes")

    def check_data_health(self, symbol: str, pattern_name: str):
        """Check if pattern has access to required data"""
        try:
            health = {}

            # Check candle availability
            health['m1_count'] = len(self.guard.m1_data.get(symbol, []))
            health['m5_count'] = len(self.guard.m5_data.get(symbol, []))
            health['m15_count'] = len(self.guard.m15_candles.get(symbol, []))

            # Check tick freshness
            if symbol in self.guard.tick_data and len(self.guard.tick_data[symbol]) > 0:
                last_tick = self.guard.tick_data[symbol][-1]
                health['tick_age'] = time.time() - last_tick.get('timestamp', 0)
            else:
                health['tick_age'] = 999999  # No ticks

            # Check indicators (attempt to calculate)
            try:
                rsi = self.guard.calculate_rsi_for_symbol(symbol, 14)
                health['has_rsi'] = rsi is not None and rsi > 0
            except:
                health['has_rsi'] = False

            # Store in data health tracker
            self.data_health[symbol]['m1_candle_count'].append(health['m1_count'])
            self.data_health[symbol]['m5_candle_count'].append(health['m5_count'])
            self.data_health[symbol]['m15_candle_count'].append(health['m15_count'])
            self.data_health[symbol]['tick_freshness'].append(health['tick_age'])
            if health['has_rsi']:
                self.data_health[symbol]['has_rsi'] += 1

            return health
        except Exception as e:
            return {'error': str(e)}

    def monitor_pattern(self, pattern_name: str, symbol: str):
        """Monitor a single pattern execution"""
        stats = self.pattern_stats[pattern_name]
        stats['total_checks'] += 1

        start = time.time()

        try:
            # Check data health first
            health = self.check_data_health(symbol, pattern_name)

            # Get pattern detection method
            method = getattr(self.guard, pattern_name, None)
            if method is None:
                stats['data_issues'].append(f"Method {pattern_name} not found")
                return None

            # Call the pattern detector
            signal = method(symbol)

            # Record execution time
            exec_time = (time.time() - start) * 1000  # ms
            stats['execution_times'].append(exec_time)

            # Analyze result
            if signal is not None:
                # Pattern triggered!
                stats['triggered'] += 1
                stats['last_trigger_time'] = datetime.now()

                # Check if ML filter will block it
                try:
                    session = self.guard.get_current_session()
                    should_publish, tier_reason, ml_score = self.guard.apply_ml_filter(signal, session)

                    if not should_publish:
                        stats['ml_filtered'] += 1
                        stats['blocking_conditions'][f'ML_FILTER: {tier_reason}'] += 1
                    else:
                        # This will actually publish!
                        pass

                except Exception as e:
                    stats['blocking_conditions'][f'ML_FILTER_ERROR: {str(e)}'] += 1

            else:
                # Pattern did not trigger - try to figure out why
                # Log data health issues
                if health.get('m5_count', 0) < 10:
                    stats['blocking_conditions']['INSUFFICIENT_M5_CANDLES'] += 1
                if health.get('m1_count', 0) < 10:
                    stats['blocking_conditions']['INSUFFICIENT_M1_CANDLES'] += 1
                if health.get('tick_age', 0) > 60:
                    stats['blocking_conditions']['STALE_TICKS'] += 1
                if not health.get('has_rsi', False):
                    stats['blocking_conditions']['NO_RSI_DATA'] += 1

            return signal

        except Exception as e:
            stats['exceptions'] += 1
            stats['data_issues'].append(f"Exception: {str(e)}")
            return None

    def run_diagnostic_scan(self):
        """Run one diagnostic scan cycle"""
        self.scan_count += 1

        # Get symbols to scan
        symbols = list(self.guard.tick_data.keys())[:16]  # Limit to 16 symbols

        print(f"\n🔍 Diagnostic Scan #{self.scan_count} - {len(symbols)} symbols")

        for symbol in symbols:
            for pattern_name in self.patterns:
                try:
                    self.monitor_pattern(pattern_name, symbol)
                except Exception as e:
                    print(f"   ⚠️  {pattern_name} on {symbol}: {str(e)}")

        # Show quick stats
        triggered = sum(s['triggered'] for s in self.pattern_stats.values())
        total = sum(s['total_checks'] for s in self.pattern_stats.values())
        print(f"   Patterns checked: {total} | Triggered: {triggered} | Hit rate: {triggered/total*100:.1f}%")

    def generate_report(self) -> str:
        """Generate comprehensive diagnostic report"""
        duration = time.time() - self.start_time

        report = []
        report.append("=" * 70)
        report.append("🔍 PATTERN DIAGNOSTIC REPORT")
        report.append("=" * 70)
        report.append(f"Scan Duration: {duration/60:.1f} minutes | Cycles: {self.scan_count}")
        report.append(f"Total Checks: {sum(s['total_checks'] for s in self.pattern_stats.values())}")
        report.append("")

        # Categorize patterns
        working = []
        too_strict = []
        data_starved = []
        broken = []

        for pattern_name, stats in sorted(self.pattern_stats.items()):
            if stats['total_checks'] == 0:
                continue

            hit_rate = (stats['triggered'] / stats['total_checks'] * 100) if stats['total_checks'] > 0 else 0

            pattern_info = {
                'name': pattern_name.replace('detect_', '').upper(),
                'stats': stats,
                'hit_rate': hit_rate,
            }

            if stats['exceptions'] > stats['total_checks'] * 0.5:
                broken.append(pattern_info)
            elif hit_rate > 0.5:
                working.append(pattern_info)
            elif 'INSUFFICIENT' in str(stats['blocking_conditions']):
                data_starved.append(pattern_info)
            else:
                too_strict.append(pattern_info)

        # Report working patterns
        report.append(f"📊 WORKING PATTERNS ({len(working)}):")
        report.append("-" * 70)
        for p in sorted(working, key=lambda x: x['hit_rate'], reverse=True):
            stats = p['stats']
            report.append(f"✅ {p['name']}: {stats['triggered']} triggers / {stats['total_checks']} checks ({p['hit_rate']:.1f}% hit rate)")

            if stats['ml_filtered'] > 0:
                report.append(f"   ML Filtered: {stats['ml_filtered']} ({stats['ml_filtered']/stats['triggered']*100:.1f}% of triggers)")

            avg_time = sum(stats['execution_times']) / len(stats['execution_times']) if stats['execution_times'] else 0
            report.append(f"   Avg execution: {avg_time:.2f}ms")
            report.append("")

        # Report non-working patterns
        report.append(f"🚫 NON-WORKING PATTERNS ({len(too_strict) + len(data_starved) + len(broken)}):")
        report.append("-" * 70)
        report.append("")

        if data_starved:
            report.append("CATEGORY: DATA STARVED (insufficient market data)")
            for p in data_starved:
                stats = p['stats']
                report.append(f"⚠️  {p['name']}: 0 triggers / {stats['total_checks']} checks")

                # Show data issues
                top_issues = sorted(stats['blocking_conditions'].items(), key=lambda x: x[1], reverse=True)[:3]
                for issue, count in top_issues:
                    pct = count / stats['total_checks'] * 100
                    report.append(f"   - {issue}: {pct:.1f}% of checks")
                report.append("")

        if too_strict:
            report.append("CATEGORY: TOO STRICT (conditions never align)")
            for p in too_strict:
                stats = p['stats']
                report.append(f"⚠️  {p['name']}: {stats['triggered']} triggers / {stats['total_checks']} checks ({p['hit_rate']:.2f}%)")

                # Show blocking conditions
                top_blocks = sorted(stats['blocking_conditions'].items(), key=lambda x: x[1], reverse=True)[:3]
                for block, count in top_blocks:
                    pct = count / stats['total_checks'] * 100
                    report.append(f"   - {block}: {pct:.1f}% of checks")

                # Show exceptions if any
                if stats['exceptions'] > 0:
                    report.append(f"   - Exceptions: {stats['exceptions']}")
                    if stats['data_issues']:
                        report.append(f"     Examples: {stats['data_issues'][:2]}")

                report.append("")

        if broken:
            report.append("CATEGORY: BROKEN (throwing exceptions)")
            for p in broken:
                stats = p['stats']
                report.append(f"❌ {p['name']}: {stats['exceptions']} exceptions / {stats['total_checks']} checks")
                if stats['data_issues']:
                    report.append(f"   Errors: {stats['data_issues'][:3]}")
                report.append("")

        # Data health summary
        report.append("=" * 70)
        report.append("📊 DATA HEALTH SUMMARY:")
        report.append("-" * 70)

        for symbol in sorted(self.data_health.keys())[:10]:
            health = self.data_health[symbol]
            avg_m5 = sum(health['m5_candle_count']) / len(health['m5_candle_count']) if health['m5_candle_count'] else 0
            report.append(f"{symbol}: M5 candles avg: {avg_m5:.0f}")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)


def run_diagnostics(duration_minutes=5, max_scans=20):
    """Main entry point for diagnostics"""
    print("\n" + "=" * 70)
    print("🚀 STARTING PATTERN DIAGNOSTICS")
    print("=" * 70)
    print(f"Duration: {duration_minutes} minutes or {max_scans} scans")
    print("Mode: OBSERVATION ONLY (no changes to trading logic)")
    print("")

    # Import elite guard
    import sys
    sys.path.insert(0, '/root/HydraX-v2')

    # Find the running elite guard instance
    # We'll monitor it by checking its processes
    print("⏳ Waiting for Elite Guard to be active...")

    # For now, create a mock diagnostic that can be integrated
    print("✅ Diagnostic module created")
    print("📋 To integrate: Add to elite_guard main scan loop")
    print("")
    print("INTEGRATION CODE:")
    print("-" * 70)
    integration_code = '''
# Add to elite_guard_with_citadel.py around line 5720:

from pattern_diagnostics import PatternDiagnostics

# In __init__ or main_loop:
if not hasattr(self, 'diagnostics'):
    self.diagnostics = PatternDiagnostics(self)

# In main scan loop (after line 5720):
if hasattr(self, 'diagnostics'):
    self.diagnostics.run_diagnostic_scan()

    # Generate report after 20 scans
    if self.diagnostics.scan_count >= 20:
        report = self.diagnostics.generate_report()
        with open('/root/pattern_diagnostic_report.txt', 'w') as f:
            f.write(report)
        print("📊 Diagnostic report saved to /root/pattern_diagnostic_report.txt")
        delattr(self, 'diagnostics')  # Stop diagnostics
'''
    print(integration_code)
    print("-" * 70)

    return True


if __name__ == "__main__":
    run_diagnostics()
