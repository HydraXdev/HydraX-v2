#!/usr/bin/env python3
"""
Black Box Truth Dashboard - Real-Time Post-Mortem Visualization
Shows entry quality, sweeps, traps, and performance truth
"""

from flask import Flask, jsonify, render_template_string
from pathlib import Path
import json
from datetime import datetime, timedelta
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BlackBoxDashboard')

TRUTH_LOG = Path("/root/HydraX-v2/truth_log.jsonl")

@app.route('/')
def dashboard():
    """Main dashboard view"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>🔒 Black Box Truth Dashboard</title>
    <style>
        body {
            background: #0a0a0a;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 20px;
            border-bottom: 2px solid #00ff00;
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-box {
            background: #1a1a1a;
            border: 1px solid #00ff00;
            padding: 20px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            color: #ffff00;
            margin: 10px 0;
        }
        .trades-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .trades-table th, .trades-table td {
            border: 1px solid #333;
            padding: 10px;
            text-align: left;
        }
        .trades-table th {
            background: #1a1a1a;
            color: #00ff00;
        }
        .win { color: #00ff00; }
        .loss { color: #ff0000; }
        .perfect { color: #00ffff; }
        .trapped { color: #ff00ff; }
        .swept { color: #ffaa00; }
        .refresh-btn {
            background: #00ff00;
            color: #000;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
        }
        .analysis-section {
            background: #1a1a1a;
            border: 1px solid #444;
            padding: 20px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 BLACK BOX TRUTH SYSTEM</h1>
        <p>Real-Time Post-Mortem Analysis | The ONLY Source of Truth</p>
        <button class="refresh-btn" onclick="location.reload()">REFRESH DATA</button>
    </div>
    
    <div id="stats-container"></div>
    <div id="analysis-container"></div>
    <div id="trades-container"></div>
    
    <script>
        async function loadDashboard() {
            // Load statistics
            const statsRes = await fetch('/api/statistics');
            const stats = await statsRes.json();
            
            // Display stats
            document.getElementById('stats-container').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-box">
                        <div>Win Rate</div>
                        <div class="stat-value">${stats.win_rate.toFixed(1)}%</div>
                        <div>${stats.wins}W / ${stats.losses}L</div>
                    </div>
                    <div class="stat-box">
                        <div>Entry Quality</div>
                        <div class="stat-value perfect">${stats.perfect_entries}</div>
                        <div>Perfect Entries</div>
                    </div>
                    <div class="stat-box">
                        <div>Market Traps</div>
                        <div class="stat-value trapped">${stats.trapped_entries}</div>
                        <div>Times Trapped</div>
                    </div>
                    <div class="stat-box">
                        <div>Sweeps Detected</div>
                        <div class="stat-value swept">${stats.sweeps_detected}</div>
                        <div>Stop Hunts</div>
                    </div>
                    <div class="stat-box">
                        <div>Avg Adverse</div>
                        <div class="stat-value loss">${stats.average_adverse.toFixed(1)} pips</div>
                        <div>Against Us</div>
                    </div>
                    <div class="stat-box">
                        <div>Avg Favorable</div>
                        <div class="stat-value win">${stats.average_favorable.toFixed(1)} pips</div>
                        <div>In Profit</div>
                    </div>
                </div>
            `;
            
            // Load entry analysis
            const analysisRes = await fetch('/api/entry_analysis');
            const analysis = await analysisRes.json();
            
            document.getElementById('analysis-container').innerHTML = `
                <div class="analysis-section">
                    <h2>📊 Entry Analysis (Last 24h)</h2>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div>Entry Efficiency</div>
                            <div class="stat-value">${analysis.average_efficiency.toFixed(1)}%</div>
                        </div>
                        <div class="stat-box">
                            <div>Quick Sweeps</div>
                            <div class="stat-value swept">${analysis.quick_sweeps}</div>
                            <div>&lt; 5 min adverse</div>
                        </div>
                        <div class="stat-box">
                            <div>Late Entries</div>
                            <div class="stat-value">${analysis.late_entries}</div>
                            <div>Chased price</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Load recent trades
            const tradesRes = await fetch('/api/recent_trades');
            const trades = await tradesRes.json();
            
            let tradesHtml = `
                <h2>📜 Recent Trades - Post-Mortem Analysis</h2>
                <table class="trades-table">
                    <tr>
                        <th>Signal ID</th>
                        <th>Symbol</th>
                        <th>Result</th>
                        <th>Entry Quality</th>
                        <th>Max Adverse</th>
                        <th>Sweep/Trap</th>
                        <th>Runtime</th>
                        <th>Efficiency</th>
                    </tr>
            `;
            
            trades.forEach(trade => {
                const resultClass = trade.result === 'WIN' ? 'win' : 'loss';
                const qualityClass = trade.entry_quality === 'PERFECT' ? 'perfect' : 
                                   trade.entry_quality === 'TRAPPED' ? 'trapped' : '';
                const sweepTrap = trade.sweep_detected ? '🌊 Swept' : 
                                trade.trap_detected ? '🪤 Trapped' : '✓ Clean';
                
                tradesHtml += `
                    <tr>
                        <td>${trade.signal_id}</td>
                        <td>${trade.symbol}</td>
                        <td class="${resultClass}">${trade.result}</td>
                        <td class="${qualityClass}">${trade.entry_quality}</td>
                        <td class="loss">${Math.abs(trade.max_adverse_excursion).toFixed(1)} pips</td>
                        <td class="${trade.sweep_detected || trade.trap_detected ? 'swept' : ''}">${sweepTrap}</td>
                        <td>${Math.floor(trade.runtime_seconds / 60)} min</td>
                        <td>${trade.entry_efficiency.toFixed(1)}%</td>
                    </tr>
                `;
            });
            
            tradesHtml += '</table>';
            document.getElementById('trades-container').innerHTML = tradesHtml;
        }
        
        // Load on startup
        loadDashboard();
        
        // Auto-refresh every 30 seconds
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
    ''')

@app.route('/api/statistics')
def api_statistics():
    """Get overall statistics"""
    stats = {
        'total_trades': 0,
        'wins': 0,
        'losses': 0,
        'win_rate': 0,
        'perfect_entries': 0,
        'trapped_entries': 0,
        'sweeps_detected': 0,
        'average_adverse': 0,
        'average_favorable': 0
    }
    
    if TRUTH_LOG.exists():
        total_adverse = 0
        total_favorable = 0
        
        with open(TRUTH_LOG, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    stats['total_trades'] += 1
                    
                    if record['result'] == 'WIN':
                        stats['wins'] += 1
                    elif record['result'] == 'LOSS':
                        stats['losses'] += 1
                        
                    if record['entry_quality'] == 'PERFECT':
                        stats['perfect_entries'] += 1
                    elif record['entry_quality'] == 'TRAPPED':
                        stats['trapped_entries'] += 1
                        
                    if record['sweep_detected']:
                        stats['sweeps_detected'] += 1
                        
                    total_adverse += abs(record['max_adverse_excursion'])
                    total_favorable += record['max_favorable_excursion']
                    
                except:
                    pass
                    
        if stats['total_trades'] > 0:
            stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100
            stats['average_adverse'] = total_adverse / stats['total_trades']
            stats['average_favorable'] = total_favorable / stats['total_trades']
            
    return jsonify(stats)

@app.route('/api/recent_trades')
def api_recent_trades():
    """Get recent trades with full analysis"""
    trades = []
    
    if TRUTH_LOG.exists():
        with open(TRUTH_LOG, 'r') as f:
            lines = f.readlines()
            
        # Get last 20 trades
        for line in lines[-20:]:
            try:
                record = json.loads(line.strip())
                trades.append(record)
            except:
                pass
                
    # Reverse to show newest first
    trades.reverse()
    return jsonify(trades)

@app.route('/api/entry_analysis')
def api_entry_analysis():
    """Analyze entry quality patterns"""
    analysis = {
        'average_efficiency': 0,
        'quick_sweeps': 0,
        'late_entries': 0,
        'total_efficiency': 0,
        'trades_analyzed': 0
    }
    
    if TRUTH_LOG.exists():
        # Analyze last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        with open(TRUTH_LOG, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    
                    # Check if within 24h
                    exit_time = datetime.fromisoformat(record['exit_timestamp'].replace('Z', '+00:00'))
                    if exit_time < cutoff_time:
                        continue
                        
                    analysis['trades_analyzed'] += 1
                    analysis['total_efficiency'] += record['entry_efficiency']
                    
                    # Quick sweep = adverse in < 5 minutes
                    if record['sweep_detected'] and record['time_to_max_adverse'] < 300:
                        analysis['quick_sweeps'] += 1
                        
                    # Late entry = poor efficiency
                    if record['entry_efficiency'] < 50:
                        analysis['late_entries'] += 1
                        
                except:
                    pass
                    
        if analysis['trades_analyzed'] > 0:
            analysis['average_efficiency'] = analysis['total_efficiency'] / analysis['trades_analyzed']
            
    return jsonify(analysis)

@app.route('/api/truth_report')
def api_truth_report():
    """Generate detailed truth report"""
    report = {
        'generated_at': datetime.utcnow().isoformat(),
        'summary': {},
        'entry_patterns': {},
        'time_analysis': {},
        'recommendations': []
    }
    
    # TODO: Implement detailed report generation
    
    return jsonify(report)

if __name__ == '__main__':
    logger.info("🔒 Starting Black Box Truth Dashboard")
    logger.info("📊 Access at http://localhost:8899/")
    app.run(host='0.0.0.0', port=8899, debug=False)