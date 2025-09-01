#!/usr/bin/env python3
"""
Real-time confidence bucket performance dashboard
Shows actual performance by confidence level to identify optimal thresholds
"""

import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, jsonify, render_template_string
import threading

app = Flask(__name__)

class ConfidenceAnalyzer:
    def __init__(self):
        self.tracking_file = "/root/HydraX-v2/optimized_tracking.jsonl"
        self.stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pending': 0})
        self.pattern_stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0}))
        self.last_update = None
        
    def update_stats(self):
        """Analyze tracking file and update stats"""
        self.stats.clear()
        self.pattern_stats.clear()
        
        with open(self.tracking_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    confidence = data.get('confidence', 0)
                    pattern = data.get('pattern', 'UNKNOWN')
                    
                    # Bucket confidence
                    if confidence >= 90:
                        bucket = '90-100%'
                    elif confidence >= 85:
                        bucket = '85-90%'
                    elif confidence >= 80:
                        bucket = '80-85%'
                    elif confidence >= 75:
                        bucket = '75-80%'
                    elif confidence >= 70:
                        bucket = '70-75%'
                    else:
                        bucket = '<70%'
                    
                    # Update bucket stats
                    self.stats[bucket]['total'] += 1
                    
                    # Check outcome
                    if 'win' in data:
                        if data['win'] == True:
                            self.stats[bucket]['wins'] += 1
                            self.pattern_stats[pattern][bucket]['wins'] += 1
                        elif data['win'] == False:
                            self.stats[bucket]['losses'] += 1
                            self.pattern_stats[pattern][bucket]['losses'] += 1
                        else:
                            self.stats[bucket]['pending'] += 1
                    elif 'outcome' in data:
                        if data['outcome'] == 'win':
                            self.stats[bucket]['wins'] += 1
                            self.pattern_stats[pattern][bucket]['wins'] += 1
                        elif data['outcome'] == 'loss':
                            self.stats[bucket]['losses'] += 1
                            self.pattern_stats[pattern][bucket]['losses'] += 1
                        else:
                            self.stats[bucket]['pending'] += 1
                    
                    self.pattern_stats[pattern][bucket]['total'] += 1
                    
                except:
                    continue
        
        self.last_update = datetime.now()

analyzer = ConfidenceAnalyzer()

@app.route('/')
def dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Confidence Performance Dashboard</title>
        <style>
            body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
            h1 { color: #0f0; text-align: center; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th { background: #333; color: #0f0; padding: 10px; text-align: left; }
            td { padding: 8px; border-bottom: 1px solid #333; }
            .win-rate { font-weight: bold; }
            .good { color: #0f0; }
            .warning { color: #ff0; }
            .bad { color: #f00; }
            .refresh { text-align: center; margin: 20px; }
        </style>
        <script>
            function refreshData() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('stats-table').innerHTML = buildTable(data.buckets);
                        document.getElementById('pattern-table').innerHTML = buildPatternTable(data.patterns);
                        document.getElementById('last-update').textContent = data.last_update;
                    });
            }
            
            function buildTable(stats) {
                let html = '<tr><th>Confidence</th><th>Total</th><th>Wins</th><th>Losses</th><th>Win Rate</th><th>Recommendation</th></tr>';
                const buckets = ['90-100%', '85-90%', '80-85%', '75-80%', '70-75%', '<70%'];
                
                for (let bucket of buckets) {
                    if (stats[bucket]) {
                        const s = stats[bucket];
                        const winRate = s.wins + s.losses > 0 ? (s.wins / (s.wins + s.losses) * 100).toFixed(1) : 0;
                        const cssClass = winRate >= 60 ? 'good' : winRate >= 50 ? 'warning' : 'bad';
                        const recommendation = winRate >= 60 ? '✅ AUTO-FIRE' : winRate >= 50 ? '⚠️ MONITOR' : '❌ BLOCK';
                        
                        html += `<tr>
                            <td>${bucket}</td>
                            <td>${s.total}</td>
                            <td>${s.wins}</td>
                            <td>${s.losses}</td>
                            <td class="win-rate ${cssClass}">${winRate}%</td>
                            <td>${recommendation}</td>
                        </tr>`;
                    }
                }
                return html;
            }
            
            function buildPatternTable(patterns) {
                let html = '<tr><th>Pattern</th><th>70-75%</th><th>75-80%</th><th>80-85%</th><th>85-90%</th><th>90%+</th></tr>';
                
                for (let pattern in patterns) {
                    html += `<tr><td>${pattern}</td>`;
                    const buckets = ['70-75%', '75-80%', '80-85%', '85-90%', '90-100%'];
                    
                    for (let bucket of buckets) {
                        const stats = patterns[pattern][bucket] || {wins: 0, losses: 0};
                        const winRate = stats.wins + stats.losses > 0 ? 
                            (stats.wins / (stats.wins + stats.losses) * 100).toFixed(0) : '-';
                        const cssClass = winRate >= 60 ? 'good' : winRate >= 50 ? 'warning' : winRate === '-' ? '' : 'bad';
                        html += `<td class="${cssClass}">${winRate}%</td>`;
                    }
                    html += '</tr>';
                }
                return html;
            }
            
            setInterval(refreshData, 5000);
            refreshData();
        </script>
    </head>
    <body>
        <h1>🎯 Confidence Performance Dashboard</h1>
        <div class="refresh">Last Update: <span id="last-update">Loading...</span></div>
        
        <h2>📊 Performance by Confidence Bucket</h2>
        <table id="stats-table"></table>
        
        <h2>🔍 Pattern Performance by Confidence</h2>
        <table id="pattern-table"></table>
    </body>
    </html>
    ''')

@app.route('/api/stats')
def get_stats():
    analyzer.update_stats()
    return jsonify({
        'buckets': dict(analyzer.stats),
        'patterns': dict(analyzer.pattern_stats),
        'last_update': analyzer.last_update.strftime('%Y-%m-%d %H:%M:%S') if analyzer.last_update else 'Never'
    })

def update_loop():
    """Background thread to update stats"""
    while True:
        analyzer.update_stats()
        time.sleep(30)

if __name__ == '__main__':
    # Start background update thread
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8891, debug=False)