#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Load Test HTML Report Generator

Generates visual HTML reports from load test results.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import json
import sys
from datetime import datetime


class LoadTestReportGenerator:
    """Generate HTML reports from load test results"""

    def __init__(self, results_file: str):
        with open(results_file, 'r') as f:
            self.results = json.load(f)

    def generate_html(self, output_file: str):
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN v2.0 Load Test Report</title>
    <style>{self._get_css()}</style>
</head>
<body>
    <div class="container">
        {self._build_header()}
        {self._build_summary()}
        {self._build_performance_chart()}
        {self._build_test_details()}
        {self._build_footer()}
    </div>
</body>
</html>"""

        with open(output_file, 'w') as f:
            f.write(html)

        print(f"✅ Load test report generated: {output_file}")

    def _get_css(self) -> str:
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Courier New', monospace; background: #0a0e27; color: #e0e0e0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%); padding: 30px; border-radius: 10px;
                  margin-bottom: 30px; border: 2px solid #00ffcc; }
        .header h1 { color: #00ffcc; font-size: 32px; margin-bottom: 10px; text-transform: uppercase; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #1a1f3a; border: 2px solid #2d3561; border-radius: 10px; padding: 20px; }
        .card h3 { color: #00ffcc; margin-bottom: 15px; font-size: 16px; }
        .pass { color: #00ff88; }
        .fail { color: #ff4444; }
        .metric { padding: 10px 0; border-bottom: 1px solid #2d3561; }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #888; font-size: 12px; }
        .metric-value { font-size: 24px; font-weight: bold; margin-top: 5px; }
        .chart { background: #1a1f3a; border: 2px solid #2d3561; border-radius: 10px; padding: 25px; margin-bottom: 20px; }
        .chart h2 { color: #00ffcc; margin-bottom: 20px; }
        .bar-container { margin-bottom: 20px; }
        .bar-label { color: #888; margin-bottom: 5px; display: flex; justify-content: space-between; }
        .bar-wrapper { background: #0f1229; height: 40px; border-radius: 5px; overflow: hidden; }
        .bar { height: 100%; background: linear-gradient(90deg, #00ffcc 0%, #00aa88 100%);
               display: flex; align-items: center; padding: 0 15px; color: #000; font-weight: bold; }
        .bar.warning { background: linear-gradient(90deg, #ffaa00 0%, #ff8800 100%); }
        .bar.critical { background: linear-gradient(90deg, #ff4444 0%, #cc0000 100%); }
        """

    def _build_header(self) -> str:
        overall = self.results['overall_pass']
        badge_class = 'pass' if overall else 'fail'
        return f"""
        <div class="header">
            <h1>⚡ BITTEN v2.0 Load Test Report</h1>
            <div class="subtitle">Generated: {self.results['timestamp']}</div>
            <div style="margin-top: 20px; font-size: 24px; font-weight: bold; color: {'#00ff88' if overall else '#ff4444'};">
                {'✅ PASS - System Ready for Production Load' if overall else '❌ FAIL - Optimization Required'}
            </div>
        </div>
        """

    def _build_summary(self) -> str:
        summary = self.results['summary']
        return f"""
        <div class="summary">
            <div class="card">
                <h3>📊 Test Results</h3>
                <div class="metric">
                    <div class="metric-label">Passed</div>
                    <div class="metric-value pass">{summary['passed_tests']}/4</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Failed</div>
                    <div class="metric-value fail">{summary['failed_tests']}/4</div>
                </div>
            </div>
            <div class="card">
                <h3>🔌 WebSocket</h3>
                <div class="metric">
                    <div class="metric-label">Status</div>
                    <div class="metric-value {'pass' if self.results['websocket_pass'] else 'fail'}">
                        {'✅ PASS' if self.results['websocket_pass'] else '❌ FAIL'}
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">P95 Latency</div>
                    <div class="metric-value">{self.results['websocket_results']['p95_latency_ms']:.1f}ms</div>
                </div>
            </div>
            <div class="card">
                <h3>🔥 Fire Burst</h3>
                <div class="metric">
                    <div class="metric-label">Status</div>
                    <div class="metric-value {'pass' if self.results['fire_burst_pass'] else 'fail'}">
                        {'✅ PASS' if self.results['fire_burst_pass'] else '❌ FAIL'}
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">P95 Latency</div>
                    <div class="metric-value">{self.results['fire_burst_results']['p95_latency_ms']:.1f}ms</div>
                </div>
            </div>
            <div class="card">
                <h3>🗄️ Database</h3>
                <div class="metric">
                    <div class="metric-label">Status</div>
                    <div class="metric-value {'pass' if self.results['db_pool_pass'] else 'fail'}">
                        {'✅ PASS' if self.results['db_pool_pass'] else '❌ FAIL'}
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">P95 Query Time</div>
                    <div class="metric-value">{self.results['db_pool_results']['p95_query_ms']:.1f}ms</div>
                </div>
            </div>
        </div>
        """

    def _build_performance_chart(self) -> str:
        perf = self.results['summary']['performance_summary']

        # Calculate bar widths (percentage of target)
        ws_width = min((perf['websocket_p95_ms'] / 250) * 100, 100)
        fire_width = min((perf['fire_p95_ms'] / 100) * 100, 100)
        signal_width = min((perf['signal_p95_ms'] / 50) * 100, 100)
        db_width = min((perf['db_p95_ms'] / 50) * 100, 100)

        def get_bar_class(value, target):
            if value <= target: return ''
            if value <= target * 1.2: return 'warning'
            return 'critical'

        return f"""
        <div class="chart">
            <h2>⚡ P95 Latency Performance</h2>
            <div class="bar-container">
                <div class="bar-label">
                    <span>WebSocket (Target: <250ms)</span>
                    <span>{perf['websocket_p95_ms']:.1f}ms</span>
                </div>
                <div class="bar-wrapper">
                    <div class="bar {get_bar_class(perf['websocket_p95_ms'], 250)}" style="width: {ws_width}%;">
                        {ws_width:.0f}%
                    </div>
                </div>
            </div>
            <div class="bar-container">
                <div class="bar-label">
                    <span>Fire Commands (Target: <100ms)</span>
                    <span>{perf['fire_p95_ms']:.1f}ms</span>
                </div>
                <div class="bar-wrapper">
                    <div class="bar {get_bar_class(perf['fire_p95_ms'], 100)}" style="width: {fire_width}%;">
                        {fire_width:.0f}%
                    </div>
                </div>
            </div>
            <div class="bar-container">
                <div class="bar-label">
                    <span>Signal Publishing (Target: <50ms)</span>
                    <span>{perf['signal_p95_ms']:.1f}ms</span>
                </div>
                <div class="bar-wrapper">
                    <div class="bar {get_bar_class(perf['signal_p95_ms'], 50)}" style="width: {signal_width}%;">
                        {signal_width:.0f}%
                    </div>
                </div>
            </div>
            <div class="bar-container">
                <div class="bar-label">
                    <span>Database Queries (Target: <50ms)</span>
                    <span>{perf['db_p95_ms']:.1f}ms</span>
                </div>
                <div class="bar-wrapper">
                    <div class="bar {get_bar_class(perf['db_p95_ms'], 50)}" style="width: {db_width}%;">
                        {db_width:.0f}%
                    </div>
                </div>
            </div>
        </div>
        """

    def _build_test_details(self) -> str:
        return "<div class='chart'><h2>📊 Detailed Test Results</h2><p>See JSON output for complete details.</p></div>"

    def _build_footer(self) -> str:
        return "<div style='text-align:center; color:#666; padding:30px; border-top:1px solid #2d3561;'>BITTEN v2.0 Phase 1 Load Testing Framework</div>"


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate load test HTML report')
    parser.add_argument('results_file', help='JSON results file from load_runner.py')
    parser.add_argument('--output', help='Output HTML file path')
    args = parser.parse_args()

    generator = LoadTestReportGenerator(args.results_file)
    output = args.output or f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    generator.generate_html(output)

if __name__ == "__main__":
    main()
