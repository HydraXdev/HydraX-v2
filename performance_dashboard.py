#!/usr/bin/env python3
"""
Performance Dashboard - HTML dashboard on port 8890
Real-time visualization of signal tracking and elimination analysis
"""

import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, render_template_string, jsonify
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/performance_dashboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PerformanceDashboard:
    """Real-time performance dashboard for signal tracking"""
    
    def __init__(self, port=8890):
        self.port = port
        self.app = Flask(__name__)
        self.tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
        self.kill_list_file = "/root/HydraX-v2/pattern_kill_list.json"
        self.inverse_results_file = "/root/HydraX-v2/inverse_analysis_results.json"
        
        # Setup Flask routes
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes for the dashboard"""
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(self.get_dashboard_template())
            
        @self.app.route('/api/signal_stats')
        def api_signal_stats():
            return jsonify(self.get_signal_stats())
            
        @self.app.route('/api/pattern_performance')
        def api_pattern_performance():
            return jsonify(self.get_pattern_performance())
            
        @self.app.route('/api/elimination_candidates')
        def api_elimination_candidates():
            return jsonify(self.get_elimination_candidates())
            
        @self.app.route('/api/inverse_opportunities')
        def api_inverse_opportunities():
            return jsonify(self.get_inverse_opportunities())
            
        @self.app.route('/api/recent_signals')
        def api_recent_signals():
            return jsonify(self.get_recent_signals())
            
    def load_signals(self, hours_back: int = 24) -> List[Dict]:
        """Load recent signals from tracking file"""
        signals = []
        cutoff_time = time.time() - (hours_back * 3600)
        
        try:
            with open(self.tracking_file, 'r') as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        if signal.get('timestamp', 0) >= cutoff_time:
                            signals.append(signal)
        except FileNotFoundError:
            logger.warning("No tracking file found")
        except Exception as e:
            logger.error(f"Error loading signals: {e}")
            
        return signals
        
    def get_signal_stats(self) -> Dict:
        """Get overall signal statistics"""
        signals = self.load_signals(24)  # Last 24 hours
        
        stats = {
            'total_signals': len(signals),
            'would_fire_count': 0,
            'tp_hit_30min': 0,
            'sl_hit_30min': 0,
            'pending_30min': 0,
            'tp_hit_60min': 0,
            'sl_hit_60min': 0,
            'pending_60min': 0,
            'win_rate_30min': 0.0,
            'win_rate_60min': 0.0,
            'avg_confidence': 0.0,
            'last_updated': datetime.now().isoformat()
        }
        
        if not signals:
            return stats
            
        total_confidence = 0
        for signal in signals:
            total_confidence += signal.get('confidence_score', 0)
            
            if signal.get('would_fire', False):
                stats['would_fire_count'] += 1
                
            outcome_30 = signal.get('outcome_30min')
            if outcome_30 == 'TP_HIT':
                stats['tp_hit_30min'] += 1
            elif outcome_30 == 'SL_HIT':
                stats['sl_hit_30min'] += 1
            elif outcome_30 is None:
                stats['pending_30min'] += 1
                
            outcome_60 = signal.get('outcome_60min')
            if outcome_60 == 'TP_HIT':
                stats['tp_hit_60min'] += 1
            elif outcome_60 == 'SL_HIT':
                stats['sl_hit_60min'] += 1
            elif outcome_60 is None:
                stats['pending_60min'] += 1
                
        # Calculate averages and rates
        stats['avg_confidence'] = round(total_confidence / len(signals), 1)
        
        total_closed_30 = stats['tp_hit_30min'] + stats['sl_hit_30min']
        if total_closed_30 > 0:
            stats['win_rate_30min'] = round(stats['tp_hit_30min'] / total_closed_30 * 100, 1)
            
        total_closed_60 = stats['tp_hit_60min'] + stats['sl_hit_60min']
        if total_closed_60 > 0:
            stats['win_rate_60min'] = round(stats['tp_hit_60min'] / total_closed_60 * 100, 1)
            
        return stats
        
    def get_pattern_performance(self) -> Dict:
        """Get pattern-specific performance data"""
        signals = self.load_signals(168)  # Last week
        
        pattern_stats = {}
        for signal in signals:
            pattern = signal.get('pattern_type', 'UNKNOWN')
            if pattern not in pattern_stats:
                pattern_stats[pattern] = {
                    'total': 0, 'tp_30min': 0, 'sl_30min': 0,
                    'win_rate_30min': 0.0, 'avg_confidence': 0.0
                }
                
            pattern_stats[pattern]['total'] += 1
            pattern_stats[pattern]['avg_confidence'] += signal.get('confidence_score', 0)
            
            if signal.get('outcome_30min') == 'TP_HIT':
                pattern_stats[pattern]['tp_30min'] += 1
            elif signal.get('outcome_30min') == 'SL_HIT':
                pattern_stats[pattern]['sl_30min'] += 1
                
        # Calculate averages
        for pattern, stats in pattern_stats.items():
            if stats['total'] > 0:
                stats['avg_confidence'] = round(stats['avg_confidence'] / stats['total'], 1)
                
            total_closed = stats['tp_30min'] + stats['sl_30min']
            if total_closed > 0:
                stats['win_rate_30min'] = round(stats['tp_30min'] / total_closed * 100, 1)
                
        return pattern_stats
        
    def get_elimination_candidates(self) -> Dict:
        """Get current elimination candidates"""
        try:
            with open(self.kill_list_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'patterns_to_kill': [], 'reasons': []}
        except Exception as e:
            logger.error(f"Error loading kill list: {e}")
            return {'patterns_to_kill': [], 'reasons': []}
            
    def get_inverse_opportunities(self) -> Dict:
        """Get inverse signal opportunities"""
        try:
            with open(self.inverse_results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'inverse_opportunities': [], 'summary': {}}
        except Exception as e:
            logger.error(f"Error loading inverse results: {e}")
            return {'inverse_opportunities': [], 'summary': {}}
            
    def get_recent_signals(self, limit: int = 50) -> List[Dict]:
        """Get most recent signals"""
        signals = self.load_signals(24)
        
        # Sort by timestamp (most recent first)
        signals.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Format for display
        formatted_signals = []
        for signal in signals[:limit]:
            formatted_signals.append({
                'signal_id': signal.get('signal_id', ''),
                'pair': signal.get('pair', ''),
                'direction': signal.get('direction', ''),
                'pattern_type': signal.get('pattern_type', ''),
                'confidence_score': signal.get('confidence_score', 0),
                'outcome_30min': signal.get('outcome_30min'),
                'pips_moved_30min': signal.get('pips_moved_30min'),
                'would_fire': signal.get('would_fire', False),
                'time_ago': self.time_ago(signal.get('timestamp', 0))
            })
            
        return formatted_signals
        
    def time_ago(self, timestamp: float) -> str:
        """Convert timestamp to human readable time ago"""
        try:
            diff = time.time() - timestamp
            if diff < 60:
                return f"{int(diff)}s ago"
            elif diff < 3600:
                return f"{int(diff/60)}m ago"
            elif diff < 86400:
                return f"{int(diff/3600)}h ago"
            else:
                return f"{int(diff/86400)}d ago"
        except:
            return "unknown"
            
    def get_dashboard_template(self) -> str:
        """Return HTML template for dashboard"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Signal Performance Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #fff;
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { 
            font-size: 2.5em; 
            color: #00ff88;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
            margin-bottom: 10px;
        }
        .subtitle { color: #888; font-size: 1.1em; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover { transform: translateY(-2px); }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label { color: #aaa; font-size: 0.9em; }
        
        .win-rate { color: #00ff88; }
        .loss-rate { color: #ff4444; }
        .neutral { color: #ffaa00; }
        
        .section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .section h2 {
            color: #00ff88;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .table th {
            background: rgba(0, 255, 136, 0.1);
            color: #00ff88;
        }
        
        .table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .kill-badge {
            background: #ff4444;
            color: white;
            padding: 3px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .invert-badge {
            background: #ffaa00;
            color: white;
            padding: 3px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .good-badge {
            background: #00ff88;
            color: white;
            padding: 3px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .refresh-info {
            text-align: center;
            color: #888;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        .loading {
            text-align: center;
            color: #ffaa00;
            padding: 20px;
        }
        
        .error {
            color: #ff4444;
            text-align: center;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 SIGNAL PERFORMANCE DASHBOARD</h1>
            <div class="subtitle">Real-time signal tracking and rapid elimination analysis</div>
        </div>
        
        <!-- Key Statistics -->
        <div class="stats-grid" id="stats-grid">
            <div class="loading">Loading statistics...</div>
        </div>
        
        <!-- Pattern Performance -->
        <div class="section">
            <h2>📊 Pattern Performance (Last 7 Days)</h2>
            <div id="pattern-performance">
                <div class="loading">Loading pattern data...</div>
            </div>
        </div>
        
        <!-- Elimination Candidates -->
        <div class="section">
            <h2>💀 Elimination Candidates</h2>
            <div id="elimination-candidates">
                <div class="loading">Loading elimination data...</div>
            </div>
        </div>
        
        <!-- Inverse Opportunities -->
        <div class="section">
            <h2>🔄 Inverse Signal Opportunities</h2>
            <div id="inverse-opportunities">
                <div class="loading">Loading inverse analysis...</div>
            </div>
        </div>
        
        <!-- Recent Signals -->
        <div class="section">
            <h2>⚡ Recent Signals (Last 24 Hours)</h2>
            <div id="recent-signals">
                <div class="loading">Loading recent signals...</div>
            </div>
        </div>
        
        <div class="refresh-info">
            Dashboard refreshes every 30 seconds | Last updated: <span id="last-updated">--</span>
        </div>
    </div>
    
    <script>
        // Utility functions
        function formatNumber(num) {
            return typeof num === 'number' ? num.toFixed(1) : '0.0';
        }
        
        function getStatusBadge(winRate) {
            if (winRate >= 60) return '<span class="good-badge">GOOD</span>';
            if (winRate >= 40) return '<span class="neutral">NEUTRAL</span>';
            return '<span class="kill-badge">KILL</span>';
        }
        
        // Load statistics
        function loadStats() {
            fetch('/api/signal_stats')
                .then(response => response.json())
                .then(data => {
                    const statsGrid = document.getElementById('stats-grid');
                    statsGrid.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value neutral">${data.total_signals}</div>
                            <div class="stat-label">Total Signals (24h)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value win-rate">${data.would_fire_count}</div>
                            <div class="stat-label">Would Fire</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value ${data.win_rate_30min >= 50 ? 'win-rate' : 'loss-rate'}">${formatNumber(data.win_rate_30min)}%</div>
                            <div class="stat-label">Win Rate (30min)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value ${data.win_rate_60min >= 50 ? 'win-rate' : 'loss-rate'}">${formatNumber(data.win_rate_60min)}%</div>
                            <div class="stat-label">Win Rate (60min)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value neutral">${formatNumber(data.avg_confidence)}%</div>
                            <div class="stat-label">Avg Confidence</div>
                        </div>
                    `;
                })
                .catch(error => {
                    document.getElementById('stats-grid').innerHTML = '<div class="error">Error loading statistics</div>';
                });
        }
        
        // Load pattern performance
        function loadPatternPerformance() {
            fetch('/api/pattern_performance')
                .then(response => response.json())
                .then(data => {
                    let html = '<table class="table"><thead><tr><th>Pattern</th><th>Signals</th><th>Win Rate</th><th>Avg Confidence</th><th>Status</th></tr></thead><tbody>';
                    
                    Object.entries(data).forEach(([pattern, stats]) => {
                        if (stats.total >= 3) {  // Only show patterns with at least 3 signals
                            html += `
                                <tr>
                                    <td>${pattern}</td>
                                    <td>${stats.total}</td>
                                    <td>${formatNumber(stats.win_rate_30min)}%</td>
                                    <td>${formatNumber(stats.avg_confidence)}%</td>
                                    <td>${getStatusBadge(stats.win_rate_30min)}</td>
                                </tr>
                            `;
                        }
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('pattern-performance').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('pattern-performance').innerHTML = '<div class="error">Error loading pattern data</div>';
                });
        }
        
        // Load elimination candidates
        function loadEliminationCandidates() {
            fetch('/api/elimination_candidates')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    
                    if (data.patterns_to_kill && data.patterns_to_kill.length > 0) {
                        html += '<h3>Patterns to Eliminate:</h3>';
                        html += '<table class="table"><thead><tr><th>Pattern</th><th>Win Rate</th><th>Signals</th><th>Reason</th></tr></thead><tbody>';
                        
                        data.patterns_to_kill.forEach(item => {
                            html += `
                                <tr>
                                    <td>${item.pattern}</td>
                                    <td class="loss-rate">${formatNumber(item.win_rate_30min)}%</td>
                                    <td>${item.total_signals}</td>
                                    <td>${item.reason}</td>
                                </tr>
                            `;
                        });
                        
                        html += '</tbody></table>';
                    } else {
                        html = '<div style="text-align: center; color: #00ff88; padding: 20px;">✅ No patterns below elimination threshold</div>';
                    }
                    
                    document.getElementById('elimination-candidates').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('elimination-candidates').innerHTML = '<div class="error">Error loading elimination data</div>';
                });
        }
        
        // Load inverse opportunities
        function loadInverseOpportunities() {
            fetch('/api/inverse_opportunities')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    
                    if (data.inverse_opportunities && data.inverse_opportunities.length > 0) {
                        html += '<h3>Patterns That Work Better Inverted:</h3>';
                        html += '<table class="table"><thead><tr><th>Pattern</th><th>Original</th><th>Inverted</th><th>Improvement</th><th>Signals</th></tr></thead><tbody>';
                        
                        data.inverse_opportunities.forEach(item => {
                            html += `
                                <tr>
                                    <td>${item.pattern} <span class="invert-badge">INVERT</span></td>
                                    <td class="loss-rate">${formatNumber(item.original_win_rate)}%</td>
                                    <td class="win-rate">${formatNumber(item.inverse_win_rate)}%</td>
                                    <td class="win-rate">+${formatNumber(item.improvement)}%</td>
                                    <td>${item.signal_count}</td>
                                </tr>
                            `;
                        });
                        
                        html += '</tbody></table>';
                    } else {
                        html = '<div style="text-align: center; color: #ffaa00; padding: 20px;">🔄 No inverse opportunities found</div>';
                    }
                    
                    document.getElementById('inverse-opportunities').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('inverse-opportunities').innerHTML = '<div class="error">Error loading inverse data</div>';
                });
        }
        
        // Load recent signals
        function loadRecentSignals() {
            fetch('/api/recent_signals')
                .then(response => response.json())
                .then(data => {
                    let html = '<table class="table"><thead><tr><th>Time</th><th>Pair</th><th>Direction</th><th>Pattern</th><th>Confidence</th><th>Outcome</th><th>Pips</th><th>Fire?</th></tr></thead><tbody>';
                    
                    data.forEach(signal => {
                        const outcomeClass = signal.outcome_30min === 'TP_HIT' ? 'win-rate' : (signal.outcome_30min === 'SL_HIT' ? 'loss-rate' : 'neutral');
                        const fireStatus = signal.would_fire ? '<span class="good-badge">FIRE</span>' : '<span style="color: #666;">NO</span>';
                        
                        html += `
                            <tr>
                                <td>${signal.time_ago}</td>
                                <td>${signal.pair}</td>
                                <td>${signal.direction}</td>
                                <td>${signal.pattern_type}</td>
                                <td>${formatNumber(signal.confidence_score)}%</td>
                                <td class="${outcomeClass}">${signal.outcome_30min || 'PENDING'}</td>
                                <td>${signal.pips_moved_30min ? formatNumber(signal.pips_moved_30min) : '--'}</td>
                                <td>${fireStatus}</td>
                            </tr>
                        `;
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('recent-signals').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('recent-signals').innerHTML = '<div class="error">Error loading recent signals</div>';
                });
        }
        
        // Update last updated time
        function updateLastUpdated() {
            document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
        }
        
        // Load all data
        function loadAllData() {
            loadStats();
            loadPatternPerformance();
            loadEliminationCandidates();
            loadInverseOpportunities();
            loadRecentSignals();
            updateLastUpdated();
        }
        
        // Initial load
        loadAllData();
        
        // Refresh every 30 seconds
        setInterval(loadAllData, 30000);
    </script>
</body>
</html>
        '''
        
    def start_server(self):
        """Start the Flask dashboard server"""
        logger.info(f"🚀 Starting performance dashboard on port {self.port}")
        
        # Run Flask in a separate thread to avoid blocking
        def run_flask():
            self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
            
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        logger.info(f"✅ Performance dashboard running at http://localhost:{self.port}")
        return flask_thread

def main():
    """Main function for standalone operation"""
    dashboard = PerformanceDashboard(port=8890)
    
    try:
        flask_thread = dashboard.start_server()
        
        logger.info("🎯 Performance dashboard is running...")
        logger.info("Access it at: http://localhost:8890")
        logger.info("Press Ctrl+C to stop")
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            logger.info("📊 Dashboard still running...")
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Dashboard failed: {e}")
        raise

if __name__ == "__main__":
    main()