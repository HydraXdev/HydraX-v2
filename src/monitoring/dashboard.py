#!/usr/bin/env python3
"""
BITTEN Monitoring Dashboard
Comprehensive real-time dashboard for monitoring all BITTEN system components
with focus on signal generation, win rates, and system health.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response
import plotly.graph_objs as go
import plotly.utils
import pandas as pd
from collections import defaultdict
import statistics

from .logging_config import setup_service_logging
from .performance_monitor import PerformanceMonitor, get_performance_monitor
from .health_check import HealthCheckManager, create_health_check_system
from .alert_system import AlertManager, get_alert_manager
from .log_manager import LogManager, get_log_manager

class DashboardAPI:
    """Flask API for dashboard data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = Flask(__name__, 
                        template_folder='/root/HydraX-v2/src/monitoring/templates',
                        static_folder='/root/HydraX-v2/src/monitoring/static')
        self.logger = setup_service_logging("dashboard-api")
        
        # Initialize monitoring components
        self.performance_monitor = get_performance_monitor()
        self.health_manager, _ = create_health_check_system(config.get('health_check', {}))
        self.alert_manager = get_alert_manager(config.get('alerts', {}))
        self.log_manager = get_log_manager(config.get('logging', {}))
        
        # Setup routes
        self._setup_routes()
        
        # Start background monitoring
        self.health_manager.start_monitoring()
        self.performance_monitor.start()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def api_status():
            """API status endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'services': {
                    'performance_monitor': 'running' if self.performance_monitor.running else 'stopped',
                    'health_monitor': 'running' if self.health_manager.running else 'stopped',
                    'alert_manager': 'active',
                    'log_manager': 'running' if self.log_manager.running else 'stopped'
                }
            })
        
        @self.app.route('/api/metrics/current')
        def current_metrics():
            """Get current performance metrics"""
            try:
                # Get current performance
                performance = self.performance_monitor.get_current_status()
                
                # Get health status
                health = self.health_manager.get_overall_health()
                
                # Get alert summary
                alerts = self.alert_manager.get_alert_summary()
                
                # Get log manager status
                log_status = self.log_manager.get_status()
                
                return jsonify({
                    'timestamp': datetime.now().isoformat(),
                    'performance': performance,
                    'health': health,
                    'alerts': alerts,
                    'logs': log_status
                })
                
            except Exception as e:
                self.logger.error(f"Error getting current metrics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics/historical')
        def historical_metrics():
            """Get historical performance metrics"""
            try:
                # Get date range from query parameters
                days = int(request.args.get('days', 7))
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Get historical data
                signal_metrics = self.performance_monitor.db.get_signal_metrics(start_date, end_date)
                trade_metrics = self.performance_monitor.db.get_trade_metrics(start_date, end_date)
                daily_reports = self.performance_monitor.db.get_daily_reports(start_date, end_date)
                
                return jsonify({
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat(),
                        'days': days
                    },
                    'signal_metrics': signal_metrics,
                    'trade_metrics': trade_metrics,
                    'daily_reports': daily_reports
                })
                
            except Exception as e:
                self.logger.error(f"Error getting historical metrics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts/signal_generation')
        def signal_generation_chart():
            """Generate signal generation chart"""
            try:
                # Get data for last 24 hours
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=24)
                
                signal_metrics = self.performance_monitor.db.get_signal_metrics(start_time, end_time)
                
                # Process data for chart
                timestamps = []
                signal_counts = []
                cumulative_signals = []
                cumulative_total = 0
                
                for metric in signal_metrics:
                    timestamps.append(metric['timestamp'])
                    signal_counts.append(metric['signal_count'])
                    cumulative_total += metric['signal_count']
                    cumulative_signals.append(cumulative_total)
                
                # Create chart
                fig = go.Figure()
                
                # Add signal count bars
                fig.add_trace(go.Bar(
                    x=timestamps,
                    y=signal_counts,
                    name='Signals Generated',
                    marker_color='rgb(55, 83, 109)'
                ))
                
                # Add cumulative line
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=cumulative_signals,
                    mode='lines+markers',
                    name='Cumulative Signals',
                    line=dict(color='rgb(26, 118, 255)'),
                    yaxis='y2'
                ))
                
                # Add target line
                fig.add_hline(y=65, line_dash="dash", line_color="red", 
                            annotation_text="Daily Target (65)")
                
                # Update layout
                fig.update_layout(
                    title='Signal Generation - Last 24 Hours',
                    xaxis_title='Time',
                    yaxis_title='Signals per Hour',
                    yaxis2=dict(
                        title='Cumulative Signals',
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified'
                )
                
                return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
                
            except Exception as e:
                self.logger.error(f"Error generating signal chart: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts/win_rate')
        def win_rate_chart():
            """Generate win rate chart"""
            try:
                # Get data for last 7 days
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)
                
                daily_reports = self.performance_monitor.db.get_daily_reports(start_time, end_time)
                
                # Process data for chart
                dates = []
                win_rates = []
                total_trades = []
                
                for report in daily_reports:
                    dates.append(report['date'])
                    win_rates.append(report['win_rate'])
                    total_trades.append(report['total_trades'])
                
                # Create chart
                fig = go.Figure()
                
                # Add win rate line
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=win_rates,
                    mode='lines+markers',
                    name='Win Rate (%)',
                    line=dict(color='rgb(26, 118, 255)', width=3),
                    marker=dict(size=8)
                ))
                
                # Add target line
                fig.add_hline(y=85, line_dash="dash", line_color="green", 
                            annotation_text="Target (85%)")
                
                # Add warning line
                fig.add_hline(y=80, line_dash="dash", line_color="orange", 
                            annotation_text="Warning (80%)")
                
                # Update layout
                fig.update_layout(
                    title='Win Rate - Last 7 Days',
                    xaxis_title='Date',
                    yaxis_title='Win Rate (%)',
                    yaxis_range=[0, 100],
                    hovermode='x unified'
                )
                
                return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
                
            except Exception as e:
                self.logger.error(f"Error generating win rate chart: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts/system_health')
        def system_health_chart():
            """Generate system health chart"""
            try:
                # Get current health status
                health = self.health_manager.get_overall_health()
                
                # Create gauge chart for overall health
                if health['status'] == 'healthy':
                    value = 100
                    color = 'green'
                elif health['status'] == 'warning':
                    value = 60
                    color = 'orange'
                elif health['status'] == 'critical':
                    value = 20
                    color = 'red'
                else:
                    value = 0
                    color = 'gray'
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = value,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "System Health Score"},
                    delta = {'reference': 100},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': color},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                
                fig.update_layout(
                    title='System Health Status',
                    height=400
                )
                
                return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
                
            except Exception as e:
                self.logger.error(f"Error generating health chart: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts/performance_score')
        def performance_score_chart():
            """Generate performance score chart"""
            try:
                # Get data for last 30 days
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)
                
                daily_reports = self.performance_monitor.db.get_daily_reports(start_time, end_time)
                
                # Process data for chart
                dates = []
                performance_scores = []
                signal_scores = []
                win_rate_scores = []
                
                for report in daily_reports:
                    dates.append(report['date'])
                    performance_scores.append(report['performance_score'])
                    
                    # Calculate component scores
                    signal_score = min(100, (report['signals_generated'] / 65) * 100)
                    win_rate_score = min(100, (report['win_rate'] / 85) * 100)
                    
                    signal_scores.append(signal_score)
                    win_rate_scores.append(win_rate_score)
                
                # Create chart
                fig = go.Figure()
                
                # Add performance score
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=performance_scores,
                    mode='lines+markers',
                    name='Overall Performance',
                    line=dict(color='rgb(26, 118, 255)', width=3)
                ))
                
                # Add signal score
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=signal_scores,
                    mode='lines',
                    name='Signal Generation',
                    line=dict(color='rgb(55, 83, 109)', width=2)
                ))
                
                # Add win rate score
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=win_rate_scores,
                    mode='lines',
                    name='Win Rate',
                    line=dict(color='rgb(255, 65, 54)', width=2)
                ))
                
                # Add target line
                fig.add_hline(y=100, line_dash="dash", line_color="green", 
                            annotation_text="Target (100%)")
                
                # Update layout
                fig.update_layout(
                    title='Performance Score - Last 30 Days',
                    xaxis_title='Date',
                    yaxis_title='Score (%)',
                    yaxis_range=[0, 120],
                    hovermode='x unified'
                )
                
                return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
                
            except Exception as e:
                self.logger.error(f"Error generating performance chart: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts/active')
        def active_alerts():
            """Get active alerts"""
            try:
                alerts = self.alert_manager.get_active_alerts()
                
                # Convert to JSON-serializable format
                alerts_data = []
                for alert in alerts:
                    alerts_data.append({
                        'id': alert.id,
                        'title': alert.title,
                        'description': alert.description,
                        'severity': alert.severity.value,
                        'service': alert.service,
                        'metric': alert.metric,
                        'current_value': alert.current_value,
                        'threshold': alert.threshold,
                        'timestamp': alert.timestamp.isoformat(),
                        'status': alert.status.value,
                        'tags': alert.tags
                    })
                
                return jsonify({
                    'alerts': alerts_data,
                    'count': len(alerts_data),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error getting active alerts: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts/acknowledge/<alert_id>', methods=['POST'])
        def acknowledge_alert(alert_id):
            """Acknowledge an alert"""
            try:
                self.alert_manager.acknowledge_alert(alert_id)
                return jsonify({'success': True, 'message': 'Alert acknowledged'})
                
            except Exception as e:
                self.logger.error(f"Error acknowledging alert: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/services/status')
        def services_status():
            """Get status of all services"""
            try:
                # Run health checks
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                health_results = loop.run_until_complete(self.health_manager.run_health_checks())
                loop.close()
                
                # Format results
                services = []
                for name, result in health_results.items():
                    services.append({
                        'name': name,
                        'status': result.status.value,
                        'message': result.message,
                        'response_time_ms': result.response_time_ms,
                        'timestamp': result.timestamp.isoformat(),
                        'details': result.details
                    })
                
                return jsonify({
                    'services': services,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error getting services status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs/recent')
        def recent_logs():
            """Get recent log entries"""
            try:
                # Get recent log entries (last 100)
                log_entries = []
                
                # This would need to be implemented based on your log storage
                # For now, return sample data
                
                return jsonify({
                    'logs': log_entries,
                    'count': len(log_entries),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error getting recent logs: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics/stream')
        def metrics_stream():
            """Server-sent events for real-time metrics"""
            def event_stream():
                while True:
                    try:
                        # Get current metrics
                        performance = self.performance_monitor.get_current_status()
                        health = self.health_manager.get_overall_health()
                        alerts = self.alert_manager.get_alert_summary()
                        
                        data = {
                            'timestamp': datetime.now().isoformat(),
                            'performance': performance,
                            'health': health,
                            'alerts': alerts
                        }
                        
                        yield f"data: {json.dumps(data)}\n\n"
                        
                    except Exception as e:
                        self.logger.error(f"Error in metrics stream: {e}")
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    
                    # Wait 5 seconds before next update
                    import time
                    time.sleep(5)
            
            return Response(event_stream(), mimetype="text/plain")
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the dashboard server"""
        self.logger.info(f"Starting dashboard server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# HTML Template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            margin: -20px -20px 20px -20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.8;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
            font-size: 1.2em;
        }
        .status-healthy { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-critical { color: #e74c3c; }
        .status-unknown { color: #95a5a6; }
        .alert {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
        }
        .alert-critical {
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        .alert-high {
            background-color: #fff3cd;
            border-color: #ffeaa7;
        }
        .alert-medium {
            background-color: #d1ecf1;
            border-color: #bee5eb;
        }
        .alert-low {
            background-color: #d4edda;
            border-color: #c3e6cb;
        }
        .chart-container {
            height: 400px;
            margin: 20px 0;
        }
        .last-updated {
            text-align: center;
            color: #7f8c8d;
            margin-top: 20px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>BITTEN Monitoring Dashboard</h1>
        <p>Real-time monitoring of signal generation, trading performance, and system health</p>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Signal Generation</h2>
            <div id="signal-metrics">
                <div class="loading">Loading...</div>
            </div>
        </div>

        <div class="card">
            <h2>Trading Performance</h2>
            <div id="trade-metrics">
                <div class="loading">Loading...</div>
            </div>
        </div>

        <div class="card">
            <h2>System Health</h2>
            <div id="health-metrics">
                <div class="loading">Loading...</div>
            </div>
        </div>

        <div class="card">
            <h2>Active Alerts</h2>
            <div id="alerts-list">
                <div class="loading">Loading...</div>
            </div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Signal Generation Chart</h2>
            <div id="signal-chart" class="chart-container"></div>
        </div>

        <div class="card">
            <h2>Win Rate Chart</h2>
            <div id="winrate-chart" class="chart-container"></div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>System Health Status</h2>
            <div id="health-chart" class="chart-container"></div>
        </div>

        <div class="card">
            <h2>Performance Score</h2>
            <div id="performance-chart" class="chart-container"></div>
        </div>
    </div>

    <div class="last-updated" id="last-updated">
        Last updated: <span id="timestamp">Never</span>
    </div>

    <script>
        // Auto-refresh data every 30 seconds
        setInterval(updateDashboard, 30000);
        
        // Initial load
        updateDashboard();
        loadCharts();

        function updateDashboard() {
            fetch('/api/metrics/current')
                .then(response => response.json())
                .then(data => {
                    updateSignalMetrics(data.performance);
                    updateTradeMetrics(data.performance);
                    updateHealthMetrics(data.health);
                    updateAlerts(data.alerts);
                    updateTimestamp(data.timestamp);
                })
                .catch(error => {
                    console.error('Error updating dashboard:', error);
                    showError('Failed to update dashboard data');
                });
        }

        function updateSignalMetrics(performance) {
            const signalPerf = performance.signal_performance || {};
            const html = `
                <div class="metric">
                    <span>Signals Today</span>
                    <span class="metric-value">${signalPerf.signals_today || 0} / ${signalPerf.target_signals || 65}</span>
                </div>
                <div class="metric">
                    <span>Completion Rate</span>
                    <span class="metric-value">${(signalPerf.completion_rate || 0).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>TCS Threshold</span>
                    <span class="metric-value">${(signalPerf.current_tcs_threshold || 0).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Avg Generation Time</span>
                    <span class="metric-value">${(signalPerf.avg_generation_time_ms || 0).toFixed(0)}ms</span>
                </div>
            `;
            document.getElementById('signal-metrics').innerHTML = html;
        }

        function updateTradeMetrics(performance) {
            const tradePerf = performance.trade_performance || {};
            const html = `
                <div class="metric">
                    <span>Total Trades</span>
                    <span class="metric-value">${tradePerf.total_trades || 0}</span>
                </div>
                <div class="metric">
                    <span>Win Rate</span>
                    <span class="metric-value ${getWinRateClass(tradePerf.win_rate)}">${(tradePerf.win_rate || 0).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Avg PnL</span>
                    <span class="metric-value">${(tradePerf.avg_pnl || 0).toFixed(2)}</span>
                </div>
                <div class="metric">
                    <span>Avg Execution Time</span>
                    <span class="metric-value">${(tradePerf.avg_execution_time_ms || 0).toFixed(0)}ms</span>
                </div>
            `;
            document.getElementById('trade-metrics').innerHTML = html;
        }

        function updateHealthMetrics(health) {
            const html = `
                <div class="metric">
                    <span>Overall Status</span>
                    <span class="metric-value status-${health.status}">${health.status.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span>Services Total</span>
                    <span class="metric-value">${health.services_total || 0}</span>
                </div>
                <div class="metric">
                    <span>Healthy Services</span>
                    <span class="metric-value status-healthy">${health.services_healthy || 0}</span>
                </div>
                <div class="metric">
                    <span>Critical Services</span>
                    <span class="metric-value status-critical">${health.services_critical || 0}</span>
                </div>
            `;
            document.getElementById('health-metrics').innerHTML = html;
        }

        function updateAlerts(alerts) {
            const activeAlerts = alerts.active_alerts || [];
            
            if (activeAlerts.length === 0) {
                document.getElementById('alerts-list').innerHTML = '<div class="metric">No active alerts</div>';
                return;
            }

            let html = '';
            activeAlerts.forEach(alert => {
                html += `
                    <div class="alert alert-${alert.severity}">
                        <strong>${alert.title}</strong><br>
                        ${alert.description}<br>
                        <small>Service: ${alert.service} | ${alert.timestamp}</small>
                    </div>
                `;
            });

            document.getElementById('alerts-list').innerHTML = html;
        }

        function loadCharts() {
            loadSignalChart();
            loadWinRateChart();
            loadHealthChart();
            loadPerformanceChart();
        }

        function loadSignalChart() {
            fetch('/api/charts/signal_generation')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('signal-chart', data.data, data.layout);
                })
                .catch(error => console.error('Error loading signal chart:', error));
        }

        function loadWinRateChart() {
            fetch('/api/charts/win_rate')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('winrate-chart', data.data, data.layout);
                })
                .catch(error => console.error('Error loading win rate chart:', error));
        }

        function loadHealthChart() {
            fetch('/api/charts/system_health')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('health-chart', data.data, data.layout);
                })
                .catch(error => console.error('Error loading health chart:', error));
        }

        function loadPerformanceChart() {
            fetch('/api/charts/performance_score')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('performance-chart', data.data, data.layout);
                })
                .catch(error => console.error('Error loading performance chart:', error));
        }

        function getWinRateClass(winRate) {
            if (winRate >= 85) return 'status-healthy';
            if (winRate >= 80) return 'status-warning';
            return 'status-critical';
        }

        function updateTimestamp(timestamp) {
            const date = new Date(timestamp);
            document.getElementById('timestamp').textContent = date.toLocaleString();
        }

        function showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            document.body.insertBefore(errorDiv, document.body.firstChild);
            
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        }
    </script>
</body>
</html>
"""

def create_dashboard_templates():
    """Create dashboard template files"""
    templates_dir = Path('/root/HydraX-v2/src/monitoring/templates')
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dashboard.html
    dashboard_file = templates_dir / 'dashboard.html'
    with open(dashboard_file, 'w') as f:
        f.write(DASHBOARD_HTML)

def get_default_dashboard_config() -> Dict[str, Any]:
    """Get default dashboard configuration"""
    return {
        'host': '0.0.0.0',
        'port': 8080,
        'debug': False,
        'health_check': {
            'databases': {
                'main': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'port': 5432,
                    'user': 'bitten_user',
                    'password': 'password',
                    'database': 'bitten_db'
                },
                'performance': {
                    'type': 'sqlite',
                    'path': '/var/log/bitten/performance.db'
                }
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'endpoints': {
                'webapp': {
                    'url': 'http://localhost:9001/health',
                    'method': 'GET',
                    'timeout': 5,
                    'expected_status': 200
                }
            },
            'mt5_farm': {
                'url': 'http://129.212.185.102:8001'
            }
        },
        'alerts': {
            'db_path': '/var/log/bitten/alerts.db',
            'notifiers': {
                'email': {
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'from_email': 'alerts@bitten.local',
                    'to_emails': ['admin@bitten.local']
                }
            }
        },
        'logging': {
            'log_dir': '/var/log/bitten',
            'max_file_size_mb': 100,
            'max_files': 10,
            'compress_after_days': 1,
            'delete_after_days': 30
        }
    }

def create_dashboard_app(config: Optional[Dict[str, Any]] = None) -> DashboardAPI:
    """Create dashboard application"""
    if config is None:
        config = get_default_dashboard_config()
    
    # Create template files
    create_dashboard_templates()
    
    # Create dashboard app
    dashboard = DashboardAPI(config)
    
    return dashboard

# Example usage
if __name__ == "__main__":
    # Create dashboard
    dashboard = create_dashboard_app()
    
    # Run dashboard
    dashboard.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )