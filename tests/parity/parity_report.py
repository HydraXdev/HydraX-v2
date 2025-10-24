#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Parity Test HTML Report Generator

Generates visual HTML reports from parity test results for easy review during
shadow testing and cutover decision making.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import json
import sys
from datetime import datetime
from typing import Dict


class ParityReportGenerator:
    """Generate HTML reports from parity test results"""

    def __init__(self, results_file: str):
        """
        Initialize report generator

        Args:
            results_file: Path to JSON results file from parity_runner.py
        """
        with open(results_file, 'r') as f:
            self.results = json.load(f)

    def generate_html(self, output_file: str):
        """
        Generate HTML report

        Args:
            output_file: Output HTML file path
        """
        html = self._build_html()

        with open(output_file, 'w') as f:
            f.write(html)

        print(f"✅ HTML report generated: {output_file}")

    def _build_html(self) -> str:
        """Build complete HTML document"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN v2.0 Parity Test Report</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._build_header()}
        {self._build_summary()}
        {self._build_signals_section()}
        {self._build_fires_section()}
        {self._build_positions_section()}
        {self._build_critical_failures()}
        {self._build_footer()}
    </div>
</body>
</html>"""

    def _get_css(self) -> str:
        """Get CSS styles"""
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0e27;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 2px solid #00ffcc;
        }
        .header h1 {
            color: #00ffcc;
            font-size: 32px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .header .subtitle {
            color: #888;
            font-size: 14px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #1a1f3a;
            border: 2px solid #2d3561;
            border-radius: 10px;
            padding: 20px;
        }
        .card h3 {
            color: #00ffcc;
            margin-bottom: 15px;
            font-size: 16px;
            text-transform: uppercase;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #2d3561;
        }
        .stat:last-child { border-bottom: none; }
        .stat-label { color: #888; }
        .stat-value { font-weight: bold; }
        .pass { color: #00ff88; }
        .fail { color: #ff4444; }
        .warning { color: #ffaa00; }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-pass {
            background: #00ff8844;
            color: #00ff88;
            border: 1px solid #00ff88;
        }
        .status-fail {
            background: #ff444444;
            color: #ff4444;
            border: 1px solid #ff4444;
        }
        .section {
            background: #1a1f3a;
            border: 2px solid #2d3561;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .section h2 {
            color: #00ffcc;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .metric-row {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 15px;
        }
        .metric {
            background: #0f1229;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #00ffcc;
        }
        .metric-label {
            color: #888;
            font-size: 12px;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
        }
        .discrepancy-list {
            background: #0f1229;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        .discrepancy-item {
            padding: 10px;
            margin-bottom: 10px;
            background: #1a1f3a;
            border-left: 4px solid #ffaa00;
            border-radius: 3px;
        }
        .critical-alert {
            background: #ff444422;
            border: 2px solid #ff4444;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .critical-alert h2 {
            color: #ff4444;
            margin-bottom: 15px;
        }
        .critical-item {
            padding: 10px;
            background: #1a1f3a;
            margin-bottom: 10px;
            border-left: 4px solid #ff4444;
            border-radius: 3px;
        }
        .footer {
            text-align: center;
            color: #666;
            padding: 30px 0;
            margin-top: 40px;
            border-top: 1px solid #2d3561;
        }
        """

    def _build_header(self) -> str:
        """Build header section"""
        timestamp = self.results['timestamp']
        duration = self.results['duration_hours']
        overall = self.results['overall_pass']

        badge_class = 'status-pass' if overall else 'status-fail'
        badge_text = '✅ PASS - READY FOR CUTOVER' if overall else '❌ FAIL - DO NOT CUTOVER'

        return f"""
        <div class="header">
            <h1>🎯 BITTEN v2.0 Parity Test Report</h1>
            <div class="subtitle">
                Generated: {timestamp} | Duration: {duration} hours
            </div>
            <div style="margin-top: 20px;">
                <span class="status-badge {badge_class}">{badge_text}</span>
            </div>
        </div>
        """

    def _build_summary(self) -> str:
        """Build summary cards"""
        signals_pass = self.results['signals_pass']
        fires_pass = self.results['fires_pass']
        positions_pass = self.results['positions_pass']
        summary = self.results['summary']

        return f"""
        <div class="summary">
            <div class="card">
                <h3>📊 Signals Test</h3>
                <div class="stat">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value {'pass' if signals_pass else 'fail'}">
                        {'✅ PASS' if signals_pass else '❌ FAIL'}
                    </span>
                </div>
                <div class="stat">
                    <span class="stat-label">Count Diff:</span>
                    <span class="stat-value">{summary['signals_count_diff']:.2f}%</span>
                </div>
            </div>

            <div class="card">
                <h3>🔥 Fires Test</h3>
                <div class="stat">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value {'pass' if fires_pass else 'fail'}">
                        {'✅ PASS' if fires_pass else '❌ FAIL'}
                    </span>
                </div>
                <div class="stat">
                    <span class="stat-label">Count Diff:</span>
                    <span class="stat-value">{summary['fires_count_diff']:.2f}%</span>
                </div>
            </div>

            <div class="card">
                <h3>📍 Positions Test</h3>
                <div class="stat">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value {'pass' if positions_pass else 'fail'}">
                        {'✅ PASS' if positions_pass else '❌ FAIL'}
                    </span>
                </div>
                <div class="stat">
                    <span class="stat-label">Count Diff:</span>
                    <span class="stat-value">{summary['positions_count_diff']:.2f}%</span>
                </div>
            </div>
        </div>
        """

    def _build_signals_section(self) -> str:
        """Build signals detail section"""
        report = self.results['signals_report']

        discrepancies_html = ""
        if report['confidence_discrepancies']:
            discrepancies_html = "<div class='discrepancy-list'>"
            for disc in report['confidence_discrepancies'][:10]:
                discrepancies_html += f"""
                <div class='discrepancy-item'>
                    <strong>{disc['signal_id']}</strong><br>
                    v1: {disc['v1_confidence']:.1f}% | v2: {disc['v2_confidence']:.1f}% |
                    Diff: {disc['difference']:.1f}%
                </div>
                """
            discrepancies_html += "</div>"

        return f"""
        <div class="section">
            <h2>📊 Signals Comparison Details</h2>
            <div class="metric-row">
                <div class="metric">
                    <div class="metric-label">v1 Count</div>
                    <div class="metric-value">{report['v1_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">v2 Count</div>
                    <div class="metric-value">{report['v2_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Missing in v2</div>
                    <div class="metric-value {'fail' if report['missing_in_v2'] else 'pass'}">
                        {len(report['missing_in_v2'])}
                    </div>
                </div>
            </div>
            {discrepancies_html if discrepancies_html else '<p style="color: #888;">No discrepancies detected</p>'}
        </div>
        """

    def _build_fires_section(self) -> str:
        """Build fires detail section"""
        report = self.results['fires_report']

        return f"""
        <div class="section">
            <h2>🔥 Fire Execution Details</h2>
            <div class="metric-row">
                <div class="metric">
                    <div class="metric-label">v1 Count</div>
                    <div class="metric-value">{report['v1_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">v2 Count</div>
                    <div class="metric-value">{report['v2_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Lot Size Avg (v1)</div>
                    <div class="metric-value">{report['avg_lot_size_v1']:.2f}</div>
                </div>
            </div>
        </div>
        """

    def _build_positions_section(self) -> str:
        """Build positions detail section"""
        report = self.results['positions_report']

        return f"""
        <div class="section">
            <h2>📍 Position Tracking Details</h2>
            <div class="metric-row">
                <div class="metric">
                    <div class="metric-label">v1 Count</div>
                    <div class="metric-value">{report['v1_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">v2 Count</div>
                    <div class="metric-value">{report['v2_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Orphaned (v1/v2)</div>
                    <div class="metric-value">
                        {len(report['orphaned_positions_v1'])}/{len(report['orphaned_positions_v2'])}
                    </div>
                </div>
            </div>
        </div>
        """

    def _build_critical_failures(self) -> str:
        """Build critical failures section"""
        failures = self.results['summary']['critical_failures']

        if not failures:
            return """
            <div class="section" style="background: #00ff8822; border-color: #00ff88;">
                <h2 style="color: #00ff88;">✅ No Critical Failures</h2>
                <p>All tests passed validation thresholds. System is ready for cutover.</p>
            </div>
            """

        failures_html = ""
        for failure in failures:
            failures_html += f"<div class='critical-item'>🚨 {failure}</div>"

        return f"""
        <div class="critical-alert">
            <h2>🚨 Critical Failures Detected</h2>
            <p style="margin-bottom: 15px;">The following issues must be resolved before cutover:</p>
            {failures_html}
        </div>
        """

    def _build_footer(self) -> str:
        """Build footer"""
        return """
        <div class="footer">
            <p>BITTEN v2.0 Phase 1 Parity Testing Framework</p>
            <p>Generated by parity_report.py | Claude Code (Sonnet 4.5)</p>
        </div>
        """


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate HTML report from parity test results')
    parser.add_argument('results_file', help='JSON results file from parity_runner.py')
    parser.add_argument('--output', help='Output HTML file path')
    args = parser.parse_args()

    # Generate report
    generator = ParityReportGenerator(args.results_file)

    output_file = args.output or f"parity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    generator.generate_html(output_file)

    print(f"\n✅ Open in browser: file://{output_file}")


if __name__ == "__main__":
    main()
