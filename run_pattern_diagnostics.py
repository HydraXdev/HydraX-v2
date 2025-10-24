#!/usr/bin/env python3
"""
Standalone Pattern Diagnostics Runner
Monitors elite_guard logs and checks pattern execution in real-time
"""

import re
import subprocess
import time
from collections import defaultdict
from datetime import datetime

class LivePatternMonitor:
    """Monitor elite guard output in real-time"""

    def __init__(self):
        self.pattern_counts = defaultdict(lambda: {'triggered': 0, 'filtered': 0, 'checked': 0})
        self.data_issues = defaultdict(int)
        self.start_time = time.time()
        self.scan_count = 0

        # Patterns to track
        self.pattern_names = [
            'LIQUIDITY SWEEP',
            'ORDER BLOCK',
            'BLIND SPOT',
            'TRAPDOOR SSR',
            'PRESSURE VALVE',
            'VCB BREAKOUT',
            'SWEEP & RETURN',
            'MOMENTUM BURST',
            'BB_SCALP',
            'KALMAN_QUICKFIRE',
            'EMA_RSI_BB_VWAP',
            'EMA_RSI_SCALP',
        ]

    def parse_log_line(self, line):
        """Parse elite guard log output"""
        try:
            # Check for pattern triggers
            for pattern in self.pattern_names:
                if pattern in line:
                    if '✅' in line:
                        self.pattern_counts[pattern]['triggered'] += 1
                        self.pattern_counts[pattern]['checked'] += 1
                    elif '🚫' in line:
                        self.pattern_counts[pattern]['filtered'] += 1
                        self.pattern_counts[pattern]['checked'] += 1
                    elif '❌' in line or '🔍' in line:
                        self.pattern_counts[pattern]['checked'] += 1

                    # Extract blocking reason
                    if 'filtered:' in line:
                        match = re.search(r'filtered: (.+)', line)
                        if match:
                            reason = match.group(1).strip()
                            self.pattern_counts[pattern][f'block_reason_{reason}'] = \
                                self.pattern_counts[pattern].get(f'block_reason_{reason}', 0) + 1

            # Check for data issues
            if 'Only' in line and 'candles' in line:
                match = re.search(r'Only (\d+) (\w+) candles', line)
                if match:
                    count = int(match.group(1))
                    timeframe = match.group(2)
                    self.data_issues[f'{timeframe}_candles_low'] += 1

            # Count scan cycles
            if 'Starting pattern scan cycle' in line or 'Pattern scan complete' in line:
                self.scan_count += 1

        except Exception as e:
            pass

    def monitor_elite_guard(self, duration_seconds=300):
        """Monitor elite guard process for specified duration"""
        print("=" * 70)
        print("🔍 LIVE PATTERN DIAGNOSTICS - MONITORING ELITE GUARD")
        print("=" * 70)
        print(f"Duration: {duration_seconds / 60:.0f} minutes")
        print("Monitoring elite guard output...")
        print("")

        end_time = time.time() + duration_seconds

        try:
            # Get Elite Guard PID
            result = subprocess.run(
                ['pgrep', '-f', 'elite_guard_with_citadel.py'],
                capture_output=True,
                text=True
            )
            pid = result.stdout.strip().split('\n')[0] if result.stdout.strip() else None

            if not pid:
                print("❌ Elite Guard not running!")
                return

            print(f"✅ Found Elite Guard PID: {pid}")
            print("")

            # Monitor stdout
            # Instead, tail the log file
            log_file = '/tmp/elite_guard.log'

            import subprocess
            process = subprocess.Popen(
                ['tail', '-f', log_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            line_count = 0
            print("📡 Monitoring logs (press Ctrl+C to stop early)...\n")

            while time.time() < end_time:
                line = process.stdout.readline()
                if line:
                    self.parse_log_line(line)
                    line_count += 1

                    # Show progress every 50 lines
                    if line_count % 50 == 0:
                        triggered = sum(p['triggered'] for p in self.pattern_counts.values())
                        checked = sum(p['checked'] for p in self.pattern_counts.values())
                        print(f"   Lines: {line_count} | Scans: {self.scan_count} | Checks: {checked} | Triggers: {triggered}")

                time.sleep(0.01)

            process.terminate()

        except KeyboardInterrupt:
            print("\n⏸️  Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")

    def generate_report(self):
        """Generate diagnostic report"""
        duration = time.time() - self.start_time

        report = []
        report.append("")
        report.append("=" * 70)
        report.append("📊 PATTERN DIAGNOSTIC REPORT")
        report.append("=" * 70)
        report.append(f"Monitor Duration: {duration / 60:.1f} minutes")
        report.append(f"Scan Cycles Detected: {self.scan_count}")
        report.append("")

        # Sort patterns by performance
        working = []
        not_working = []

        for pattern, stats in sorted(self.pattern_counts.items()):
            if stats['checked'] == 0:
                continue

            hit_rate = (stats['triggered'] / stats['checked'] * 100) if stats['checked'] > 0 else 0
            filter_rate = (stats['filtered'] / stats['checked'] * 100) if stats['checked'] > 0 else 0

            info = {
                'name': pattern,
                'triggered': stats['triggered'],
                'filtered': stats['filtered'],
                'checked': stats['checked'],
                'hit_rate': hit_rate,
                'filter_rate': filter_rate,
            }

            # Extract blocking reasons
            blocking_reasons = {}
            for key, value in stats.items():
                if key.startswith('block_reason_'):
                    reason = key.replace('block_reason_', '')
                    blocking_reasons[reason] = value

            info['blocking_reasons'] = blocking_reasons

            if hit_rate > 1.0:
                working.append(info)
            else:
                not_working.append(info)

        # Report working patterns
        report.append(f"📊 WORKING PATTERNS ({len(working)}):")
        report.append("-" * 70)

        if working:
            for p in sorted(working, key=lambda x: x['hit_rate'], reverse=True):
                report.append(f"✅ {p['name']}")
                report.append(f"   Hit Rate: {p['hit_rate']:.1f}% ({p['triggered']} triggers / {p['checked']} checks)")
                report.append(f"   ML Filtered: {p['filter_rate']:.1f}% ({p['filtered']} filtered)")

                if p['blocking_reasons']:
                    report.append(f"   Filter Reasons:")
                    for reason, count in sorted(p['blocking_reasons'].items(), key=lambda x: x[1], reverse=True)[:3]:
                        report.append(f"      - {reason}: {count} times")
                report.append("")
        else:
            report.append("   ⚠️  No working patterns detected in this timeframe")
            report.append("")

        # Report non-working patterns
        report.append(f"🚫 NON-WORKING PATTERNS ({len(not_working)}):")
        report.append("-" * 70)

        if not_working:
            for p in not_working:
                report.append(f"⚠️  {p['name']}")
                report.append(f"   Hit Rate: {p['hit_rate']:.2f}% ({p['triggered']} triggers / {p['checked']} checks)")

                if p['blocking_reasons']:
                    report.append(f"   Common Blocks:")
                    for reason, count in sorted(p['blocking_reasons'].items(), key=lambda x: x[1], reverse=True)[:5]:
                        pct = count / p['checked'] * 100 if p['checked'] > 0 else 0
                        report.append(f"      - {reason}: {count} times ({pct:.1f}%)")
                report.append("")
        else:
            report.append("   ✅ All monitored patterns are working")
            report.append("")

        # Data health
        if self.data_issues:
            report.append("=" * 70)
            report.append("📊 DATA HEALTH ISSUES:")
            report.append("-" * 70)
            for issue, count in sorted(self.data_issues.items(), key=lambda x: x[1], reverse=True):
                report.append(f"   {issue}: {count} occurrences")
            report.append("")

        report.append("=" * 70)
        report.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("=" * 70)

        return "\n".join(report)


def main():
    """Main entry point"""
    monitor = LivePatternMonitor()

    # Monitor for 5 minutes (300 seconds)
    monitor.monitor_elite_guard(duration_seconds=300)

    # Generate and save report
    report = monitor.generate_report()

    # Print report
    print(report)

    # Save to file
    report_file = '/root/pattern_diagnostic_report.txt'
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\n✅ Report saved to: {report_file}")


if __name__ == "__main__":
    main()
