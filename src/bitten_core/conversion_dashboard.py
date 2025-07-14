"""
BITTEN Conversion Optimization Dashboard
Real-time analytics and A/B testing dashboard
"""

from flask import Blueprint, render_template_string, jsonify, request
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List
from .analytics_tracker import analytics_tracker
from .ab_testing_framework import ab_testing
from .press_pass_manager import press_pass_manager
from .onboarding_system import onboarding_manager
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
conversion_dashboard = Blueprint('conversion_dashboard', __name__)

# Dashboard HTML template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN Conversion Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            padding: 20px;
        }
        
        .dashboard-header {
            font-family: 'Orbitron', monospace;
            font-size: 2.5rem;
            font-weight: 700;
            color: #00ff41;
            margin-bottom: 30px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 65, 0.3);
            padding: 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #00ff41, transparent);
            animation: scan 3s linear infinite;
        }
        
        @keyframes scan {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #00ff41;
            font-family: 'Orbitron', monospace;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #888;
            text-transform: uppercase;
            margin-top: 5px;
        }
        
        .metric-change {
            font-size: 0.8rem;
            margin-top: 10px;
        }
        
        .positive { color: #00ff41; }
        .negative { color: #ff0040; }
        
        .section {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 30px;
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #00ff41;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .funnel-stage {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px;
            margin-bottom: 10px;
            background: rgba(0, 255, 65, 0.05);
            border-left: 3px solid #00ff41;
        }
        
        .funnel-stage-name {
            font-weight: 600;
        }
        
        .funnel-stage-stats {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .ab-test {
            margin-bottom: 20px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.03);
        }
        
        .ab-test-name {
            font-weight: 600;
            color: #00ff41;
            margin-bottom: 10px;
        }
        
        .variant {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            margin-bottom: 5px;
            background: rgba(255, 255, 255, 0.02);
        }
        
        .winner {
            background: rgba(0, 255, 65, 0.1);
            border: 1px solid #00ff41;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #00ff41;
            color: #0a0a0a;
            border: none;
            padding: 15px 30px;
            font-weight: 700;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 255, 65, 0.5);
        }
        
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff41;
            border-radius: 50%;
            margin-right: 10px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <h1 class="dashboard-header">
        <span class="live-indicator"></span>
        BITTEN Conversion Dashboard
    </h1>
    
    <!-- Real-time Metrics -->
    <div class="metrics-grid" id="metricsGrid">
        <!-- Populated by JavaScript -->
    </div>
    
    <!-- Conversion Funnel -->
    <div class="section">
        <h2 class="section-title">Press Pass Conversion Funnel</h2>
        <div id="funnelStages">
            <!-- Populated by JavaScript -->
        </div>
        <div class="chart-container">
            <canvas id="funnelChart"></canvas>
        </div>
    </div>
    
    <!-- A/B Tests -->
    <div class="section">
        <h2 class="section-title">Active A/B Tests</h2>
        <div id="abTests">
            <!-- Populated by JavaScript -->
        </div>
    </div>
    
    <!-- Hourly Trend -->
    <div class="section">
        <h2 class="section-title">Hourly Conversion Trend</h2>
        <div class="chart-container">
            <canvas id="trendChart"></canvas>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
    
    <script>
        let funnelChart, trendChart;
        
        async function loadDashboardData() {
            try {
                const response = await fetch('/api/conversion/dashboard-data');
                const data = await response.json();
                
                updateMetrics(data.metrics);
                updateFunnel(data.funnel);
                updateABTests(data.ab_tests);
                updateCharts(data);
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }
        
        function updateMetrics(metrics) {
            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = '';
            
            const metricConfigs = [
                { key: 'page_views', label: 'Page Views Today', format: 'number' },
                { key: 'press_pass_claims', label: 'Press Pass Claims', format: 'number' },
                { key: 'activation_rate', label: 'Activation Rate', format: 'percent' },
                { key: 'conversion_rate', label: 'Conversion Rate', format: 'percent' },
                { key: 'average_time_to_convert', label: 'Avg Time to Convert', format: 'time' },
                { key: 'revenue_today', label: 'Revenue Today', format: 'currency' }
            ];
            
            metricConfigs.forEach(config => {
                const value = metrics[config.key] || 0;
                const change = metrics[`${config.key}_change`] || 0;
                
                const card = document.createElement('div');
                card.className = 'metric-card';
                card.innerHTML = `
                    <div class="metric-value">${formatValue(value, config.format)}</div>
                    <div class="metric-label">${config.label}</div>
                    <div class="metric-change ${change >= 0 ? 'positive' : 'negative'}">
                        ${change >= 0 ? '↑' : '↓'} ${Math.abs(change).toFixed(1)}%
                    </div>
                `;
                grid.appendChild(card);
            });
        }
        
        function updateFunnel(funnel) {
            const container = document.getElementById('funnelStages');
            container.innerHTML = '';
            
            funnel.steps.forEach((step, index) => {
                const stage = document.createElement('div');
                stage.className = 'funnel-stage';
                stage.innerHTML = `
                    <div class="funnel-stage-name">${step.name}</div>
                    <div class="funnel-stage-stats">
                        <span>${step.count.toLocaleString()} users</span>
                        <span>${step.conversion_rate}%</span>
                    </div>
                `;
                container.appendChild(stage);
            });
            
            // Update funnel chart
            if (funnelChart) {
                funnelChart.data.labels = funnel.steps.map(s => s.name);
                funnelChart.data.datasets[0].data = funnel.steps.map(s => s.count);
                funnelChart.update();
            } else {
                const ctx = document.getElementById('funnelChart').getContext('2d');
                funnelChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: funnel.steps.map(s => s.name),
                        datasets: [{
                            label: 'Users',
                            data: funnel.steps.map(s => s.count),
                            backgroundColor: 'rgba(0, 255, 65, 0.5)',
                            borderColor: '#00ff41',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, ticks: { color: '#888' } },
                            x: { ticks: { color: '#888' } }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }
        }
        
        function updateABTests(tests) {
            const container = document.getElementById('abTests');
            container.innerHTML = '';
            
            Object.values(tests).forEach(test => {
                const testDiv = document.createElement('div');
                testDiv.className = 'ab-test';
                
                let testHTML = `<div class="ab-test-name">${test.experiment.name}</div>`;
                
                Object.entries(test.variants).forEach(([variant, data]) => {
                    const isWinner = test.analysis && test.analysis.is_significant && 
                                   data.metrics.conversion_rate > test.variants.control?.metrics.conversion_rate;
                    
                    testHTML += `
                        <div class="variant ${isWinner ? 'winner' : ''}">
                            <span>${variant}</span>
                            <span>${data.unique_users} users | ${data.metrics.conversion_rate || 0}% conversion</span>
                        </div>
                    `;
                });
                
                if (test.analysis) {
                    testHTML += `
                        <div style="margin-top: 10px; font-size: 0.9rem; color: #888;">
                            Lift: ${test.analysis.lift}% | p-value: ${test.analysis.p_value}
                            ${test.analysis.is_significant ? ' | ✓ Significant' : ''}
                        </div>
                    `;
                }
                
                testDiv.innerHTML = testHTML;
                container.appendChild(testDiv);
            });
        }
        
        function updateCharts(data) {
            // Update trend chart
            const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
            const hourlyData = hours.map(h => data.hourly_metrics[h] || 0);
            
            if (trendChart) {
                trendChart.data.labels = hours;
                trendChart.data.datasets[0].data = hourlyData;
                trendChart.update();
            } else {
                const ctx = document.getElementById('trendChart').getContext('2d');
                trendChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: hours,
                        datasets: [{
                            label: 'Conversions',
                            data: hourlyData,
                            borderColor: '#00ff41',
                            backgroundColor: 'rgba(0, 255, 65, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, ticks: { color: '#888' } },
                            x: { ticks: { color: '#888' } }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }
        }
        
        function formatValue(value, format) {
            switch(format) {
                case 'number':
                    return value.toLocaleString();
                case 'percent':
                    return value.toFixed(1) + '%';
                case 'currency':
                    return '$' + value.toLocaleString();
                case 'time':
                    return value + 'h';
                default:
                    return value;
            }
        }
        
        function refreshData() {
            loadDashboardData();
        }
        
        // Load initial data
        loadDashboardData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadDashboardData, 30000);
    </script>
</body>
</html>
"""

@conversion_dashboard.route('/conversion-dashboard')
def dashboard():
    """Render conversion dashboard"""
    # TODO: Add authentication check
    return render_template_string(DASHBOARD_TEMPLATE)

@conversion_dashboard.route('/api/conversion/dashboard-data')
def dashboard_data():
    """Get dashboard data API endpoint"""
    try:
        # Get date range
        days = int(request.args.get('days', 7))
        
        # Get real-time metrics
        metrics = analytics_tracker.get_real_time_metrics()
        
        # Get Press Pass metrics
        press_pass_metrics = press_pass_manager.get_conversion_metrics()
        
        # Get funnel metrics
        funnel = analytics_tracker.get_funnel_metrics('press_pass', days)
        
        # Get A/B test results
        ab_tests = {}
        for test_id in ['press_pass_cta', 'urgency_messaging', 'email_subject_lines']:
            ab_tests[test_id] = ab_testing.get_experiment_results(test_id)
        
        # Get hourly trend data
        hourly_metrics = _get_hourly_trend()
        
        # Get onboarding metrics
        stuck_users = onboarding_manager.get_stuck_users(24)
        
        # Combine all metrics
        dashboard_data = {
            'metrics': {
                'page_views': metrics['daily'].get('page_views', 0),
                'page_views_change': _calculate_change('page_views'),
                'press_pass_claims': press_pass_metrics.get('total_claims', 0),
                'press_pass_claims_change': _calculate_change('claims'),
                'activation_rate': press_pass_metrics.get('activation_rate', 0),
                'activation_rate_change': _calculate_change('activation_rate'),
                'conversion_rate': press_pass_metrics.get('conversion_rate', 0),
                'conversion_rate_change': _calculate_change('conversion_rate'),
                'average_time_to_convert': _get_avg_conversion_time(),
                'revenue_today': metrics['daily'].get('revenue', 0),
                'revenue_today_change': _calculate_change('revenue'),
                'active_users': metrics.get('active_users', 0),
                'press_pass_remaining': press_pass_metrics.get('daily_remaining', 0)
            },
            'funnel': funnel,
            'ab_tests': ab_tests,
            'hourly_metrics': hourly_metrics,
            'stuck_users': len(stuck_users),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

def _calculate_change(metric: str) -> float:
    """Calculate percentage change from previous period"""
    # In production, this would compare with actual historical data
    # For now, return mock data
    import random
    return round(random.uniform(-20, 30), 2)

def _get_avg_conversion_time() -> float:
    """Get average time to conversion in hours"""
    # In production, calculate from actual data
    return 4.5

def _get_hourly_trend() -> Dict[str, int]:
    """Get hourly conversion trend"""
    # In production, get from analytics
    import random
    return {
        f"{h}:00": random.randint(5, 50) 
        for h in range(24)
    }