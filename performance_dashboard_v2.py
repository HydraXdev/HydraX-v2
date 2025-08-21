#!/usr/bin/env python3
"""
Real-Time Performance Dashboard v2
Live visualization of pattern performance and trading metrics
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# HTML Template with auto-refresh
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Elite Guard Performance Dashboard v2</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
            margin: 0;
        }
        h1 {
            color: #00ff00;
            text-align: center;
            text-shadow: 0 0 10px #00ff00;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .card {
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 0 20px rgba(0,255,0,0.2);
        }
        .card h2 {
            color: #00ff00;
            margin-top: 0;
            font-size: 18px;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 5px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px dotted #333;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .value {
            color: #0ff;
            font-weight: bold;
        }
        .win { color: #0f0; }
        .loss { color: #f00; }
        .neutral { color: #ff0; }
        .pattern-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
            padding: 5px 0;
            border-bottom: 1px dotted #333;
            font-size: 14px;
        }
        .pattern-header {
            font-weight: bold;
            color: #00ff00;
            border-bottom: 2px solid #00ff00;
        }
        .active-signal {
            background: rgba(0,255,0,0.1);
            border-left: 3px solid #00ff00;
            padding-left: 10px;
            margin: 5px 0;
        }
        .promoted {
            background: rgba(255,215,0,0.1);
            color: #ffd700;
        }
        .disabled {
            background: rgba(255,0,0,0.1);
            color: #ff6666;
            opacity: 0.7;
        }
        .timestamp {
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 12px;
        }
        .performance-bar {
            height: 20px;
            background: #222;
            border: 1px solid #444;
            position: relative;
            margin: 5px 0;
        }
        .performance-fill {
            height: 100%;
            background: linear-gradient(90deg, #f00, #ff0, #0f0);
            transition: width 0.5s;
        }
        .heat-map {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 5px;
            margin-top: 10px;
        }
        .heat-cell {
            padding: 5px;
            text-align: center;
            border: 1px solid #333;
            font-size: 12px;
        }
        .heat-high { background: rgba(0,255,0,0.3); }
        .heat-med { background: rgba(255,255,0,0.2); }
        .heat-low { background: rgba(255,0,0,0.2); }
    </style>
</head>
<body>
    <h1>🎯 ELITE GUARD PERFORMANCE DASHBOARD v2 🎯</h1>
    
    <div class="grid">
        <!-- Overall Performance -->
        <div class="card">
            <h2>📊 OVERALL PERFORMANCE</h2>
            <div class="metric">
                <span>Total Signals:</span>
                <span class="value">{{ data.total_signals }}</span>
            </div>
            <div class="metric">
                <span>Win Rate:</span>
                <span class="value {% if data.win_rate >= 60 %}win{% elif data.win_rate >= 40 %}neutral{% else %}loss{% endif %}">
                    {{ "%.1f"|format(data.win_rate) }}%
                </span>
            </div>
            <div class="metric">
                <span>Active Signals:</span>
                <span class="value">{{ data.active_signals }}</span>
            </div>
            <div class="metric">
                <span>Avg R:R Achieved:</span>
                <span class="value">{{ "%.2f"|format(data.avg_rr) }}</span>
            </div>
            <div class="metric">
                <span>Efficiency Score:</span>
                <span class="value">{{ "%.1f"|format(data.avg_efficiency) }}%</span>
            </div>
            <div class="performance-bar">
                <div class="performance-fill" style="width: {{ data.win_rate }}%"></div>
            </div>
        </div>
        
        <!-- Pattern Performance -->
        <div class="card">
            <h2>🎯 PATTERN PERFORMANCE</h2>
            <div class="pattern-row pattern-header">
                <span>Pattern</span>
                <span>Trades</span>
                <span>Win%</span>
                <span>Avg RR</span>
                <span>Status</span>
            </div>
            {% for pattern in data.patterns %}
            <div class="pattern-row {% if pattern.status == 'PROMOTED' %}promoted{% elif pattern.status == 'DISABLED' %}disabled{% endif %}">
                <span>{{ pattern.name[:20] }}</span>
                <span>{{ pattern.trades }}</span>
                <span class="{% if pattern.win_rate >= 60 %}win{% elif pattern.win_rate >= 40 %}neutral{% else %}loss{% endif %}">
                    {{ "%.0f"|format(pattern.win_rate) }}%
                </span>
                <span>{{ "%.2f"|format(pattern.avg_rr) }}</span>
                <span>{{ pattern.status }}</span>
            </div>
            {% endfor %}
        </div>
        
        <!-- Session Performance -->
        <div class="card">
            <h2>⏰ SESSION PERFORMANCE</h2>
            <div class="metric">
                <span>Current Session:</span>
                <span class="value">{{ data.current_session }}</span>
            </div>
            {% for session in data.sessions %}
            <div class="metric">
                <span>{{ session.name }}:</span>
                <span class="value {% if session.win_rate >= 60 %}win{% elif session.win_rate >= 40 %}neutral{% else %}loss{% endif %}">
                    {{ session.trades }} trades, {{ "%.0f"|format(session.win_rate) }}% win
                </span>
            </div>
            {% endfor %}
        </div>
        
        <!-- Active Signals -->
        <div class="card">
            <h2>🔥 ACTIVE SIGNALS</h2>
            {% for signal in data.active_signal_list %}
            <div class="active-signal">
                <div style="font-weight: bold;">{{ signal.symbol }} {{ signal.direction }}</div>
                <div style="font-size: 12px;">{{ signal.pattern }}</div>
                <div style="font-size: 12px;">
                    P&L: <span class="{% if signal.current_pips >= 0 %}win{% else %}loss{% endif %}">
                        {{ "%.1f"|format(signal.current_pips) }} pips
                    </span>
                </div>
                <div style="font-size: 12px; color: #666;">
                    {{ signal.time_active }} min
                </div>
            </div>
            {% endfor %}
            {% if not data.active_signal_list %}
            <div style="color: #666; text-align: center; padding: 20px;">
                No active signals
            </div>
            {% endif %}
        </div>
        
        <!-- Symbol Heat Map -->
        <div class="card">
            <h2>🌍 SYMBOL PERFORMANCE</h2>
            <div class="heat-map">
                {% for symbol in data.symbol_performance %}
                <div class="heat-cell {% if symbol.win_rate >= 60 %}heat-high{% elif symbol.win_rate >= 40 %}heat-med{% else %}heat-low{% endif %}">
                    <div style="font-weight: bold;">{{ symbol.name }}</div>
                    <div>{{ "%.0f"|format(symbol.win_rate) }}%</div>
                    <div style="font-size: 10px;">{{ symbol.trades }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Recent Decisions -->
        <div class="card">
            <h2>🤖 OPTIMIZATION DECISIONS</h2>
            {% for decision in data.recent_decisions %}
            <div class="metric">
                <span style="font-size: 12px;">{{ decision.time }}</span>
                <span class="value" style="font-size: 12px;">
                    {{ decision.action }} {{ decision.pattern }}
                </span>
            </div>
            <div style="font-size: 11px; color: #666; margin-bottom: 10px;">
                {{ decision.reason }}
            </div>
            {% endfor %}
            {% if not data.recent_decisions %}
            <div style="color: #666; text-align: center; padding: 20px;">
                No recent decisions
            </div>
            {% endif %}
        </div>
    </div>
    
    <div class="timestamp">
        Last Updated: {{ data.timestamp }} | Auto-refresh: 30s
    </div>
    
    <script>
        // Auto-refresh data via AJAX every 5 seconds
        setInterval(function() {
            fetch('/api/v2/live_stats')
                .then(response => response.json())
                .then(data => {
                    // Update specific elements without full page reload
                    console.log('Data updated:', data);
                });
        }, 5000);
    </script>
</body>
</html>
"""

class PerformanceDashboard:
    """Dashboard data provider"""
    
    def __init__(self):
        self.db_path = '/root/HydraX-v2/bitten.db'
    
    def get_dashboard_data(self):
        """Get all dashboard data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END) as wins,
                    AVG(achieved_rr) as avg_rr,
                    AVG(efficiency_score) as avg_efficiency
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
            """)
            
            row = cursor.fetchone()
            total = row[0] or 0
            wins = row[1] or 0
            avg_rr = row[2] or 0
            avg_efficiency = row[3] or 0
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # Active signals count
            cursor.execute("""
                SELECT COUNT(*) FROM signal_performance_v2
                WHERE exit_time IS NULL
            """)
            active_signals = cursor.fetchone()[0] or 0
            
            # Pattern performance
            cursor.execute("""
                SELECT 
                    pattern_type,
                    COUNT(*) as trades,
                    SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END) as wins,
                    AVG(achieved_rr) as avg_rr
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
                GROUP BY pattern_type
            """)
            
            patterns = []
            for row in cursor.fetchall():
                pattern, trades, p_wins, p_avg_rr = row
                patterns.append({
                    'name': pattern,
                    'trades': trades,
                    'win_rate': (p_wins / trades * 100) if trades > 0 else 0,
                    'avg_rr': p_avg_rr or 0,
                    'status': self.get_pattern_status(pattern)
                })
            
            # Session performance
            cursor.execute("""
                SELECT 
                    session,
                    COUNT(*) as trades,
                    SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END) as wins
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
                GROUP BY session
            """)
            
            sessions = []
            for row in cursor.fetchall():
                session, s_trades, s_wins = row
                if session:
                    sessions.append({
                        'name': session,
                        'trades': s_trades,
                        'win_rate': (s_wins / s_trades * 100) if s_trades > 0 else 0
                    })
            
            # Symbol performance
            cursor.execute("""
                SELECT 
                    symbol,
                    COUNT(*) as trades,
                    SUM(CASE WHEN achieved_rr > 0 THEN 1 ELSE 0 END) as wins
                FROM signal_performance_v2
                WHERE exit_time IS NOT NULL
                GROUP BY symbol
                HAVING COUNT(*) >= 3
            """)
            
            symbol_performance = []
            for row in cursor.fetchall():
                symbol, sym_trades, sym_wins = row
                symbol_performance.append({
                    'name': symbol,
                    'trades': sym_trades,
                    'win_rate': (sym_wins / sym_trades * 100) if sym_trades > 0 else 0
                })
            
            # Active signals details (mock for now)
            active_signal_list = self.get_active_signals()
            
            # Recent optimization decisions
            recent_decisions = self.get_recent_decisions()
            
            # Current session
            current_session = self.get_current_session()
            
            conn.close()
            
            return {
                'total_signals': total,
                'win_rate': win_rate,
                'active_signals': active_signals,
                'avg_rr': avg_rr,
                'avg_efficiency': avg_efficiency,
                'patterns': patterns,
                'sessions': sessions,
                'symbol_performance': symbol_performance,
                'active_signal_list': active_signal_list,
                'recent_decisions': recent_decisions,
                'current_session': current_session,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return {
                'total_signals': 0,
                'win_rate': 0,
                'active_signals': 0,
                'avg_rr': 0,
                'avg_efficiency': 0,
                'patterns': [],
                'sessions': [],
                'symbol_performance': [],
                'active_signal_list': [],
                'recent_decisions': [],
                'current_session': 'UNKNOWN',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def get_pattern_status(self, pattern):
        """Get pattern status from optimizer"""
        try:
            with open('/root/HydraX-v2/pattern_optimization_state.json', 'r') as f:
                state = json.load(f)
                return state.get('pattern_status', {}).get(pattern, 'ACTIVE')
        except:
            return 'ACTIVE'
    
    def get_active_signals(self):
        """Get active signal details from tracking file"""
        active = []
        try:
            # Read from comprehensive tracking
            with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 entries
                for line in lines:
                    try:
                        data = json.loads(line)
                        if not data.get('outcome'):  # Still active
                            active.append({
                                'symbol': data.get('symbol', 'UNKNOWN'),
                                'direction': data.get('direction', 'UNKNOWN'),
                                'pattern': data.get('pattern', 'UNKNOWN')[:20],
                                'current_pips': 0,  # Would need live price
                                'time_active': 0  # Would need calculation
                            })
                    except:
                        pass
        except:
            pass
        return active[:5]  # Max 5 shown
    
    def get_recent_decisions(self):
        """Get recent optimization decisions"""
        decisions = []
        try:
            with open('/root/HydraX-v2/pattern_optimization_state.json', 'r') as f:
                state = json.load(f)
                for decision in state.get('optimization_log', [])[-5:]:
                    decisions.append({
                        'time': decision.get('timestamp', '')[:16],
                        'action': decision.get('action', ''),
                        'pattern': decision.get('pattern', '')[:15],
                        'reason': decision.get('reason', '')[:50]
                    })
        except:
            pass
        return decisions
    
    def get_current_session(self):
        """Get current trading session"""
        hour = datetime.utcnow().hour
        if 7 <= hour < 16:
            if 12 <= hour < 16:
                return 'OVERLAP'
            return 'LONDON'
        elif 12 <= hour < 21:
            return 'NY'
        elif hour >= 23 or hour < 8:
            return 'ASIAN'
        else:
            return 'OFF_HOURS'


# Flask routes
dashboard = PerformanceDashboard()

@app.route('/')
def index():
    data = dashboard.get_dashboard_data()
    return render_template_string(DASHBOARD_TEMPLATE, data=data)

@app.route('/api/v2/live_stats')
def live_stats():
    return jsonify(dashboard.get_dashboard_data())

@app.route('/api/v2/patterns/performance')
def pattern_performance():
    data = dashboard.get_dashboard_data()
    return jsonify(data.get('patterns', []))

@app.route('/api/v2/signals/active')
def active_signals():
    data = dashboard.get_dashboard_data()
    return jsonify({
        'count': data.get('active_signals', 0),
        'signals': data.get('active_signal_list', [])
    })


if __name__ == '__main__':
    print("🚀 Starting Performance Dashboard v2 on http://localhost:8891")
    app.run(host='0.0.0.0', port=8891, debug=False)