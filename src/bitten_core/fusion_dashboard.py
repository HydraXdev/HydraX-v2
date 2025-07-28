"""
BITTEN Signal Fusion Dashboard
Real-time monitoring and visualization of the fusion system
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
import logging
import traceback
from dataclasses import asdict

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .signal_fusion import signal_fusion_engine, tier_router, engagement_balancer
from .complete_signal_flow_v3 import FusionEnhancedSignalFlow

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bitten-fusion-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global flow instance
signal_flow = None

class FusionDashboard:
    """Dashboard for monitoring signal fusion system"""
    
    def __init__(self, flow: FusionEnhancedSignalFlow):
        self.flow = flow
        self.update_interval = 5  # seconds
    
    def _get_mock_tier_stats(self) -> Dict[str, Any]:
        """Get mock tier statistics for testing"""
        return {
            'sniper': {
                'win_rate': 0.85,
                'total_signals': 25,
                'active_signals': 2
            },
            'precision': {
                'win_rate': 0.78,
                'total_signals': 45,
                'active_signals': 3
            },
            'rapid': {
                'win_rate': 0.72,
                'total_signals': 85,
                'active_signals': 5
            },
            'training': {
                'win_rate': 0.65,
                'total_signals': 150,
                'active_signals': 8
            }
        }
    
    @staticmethod
    def _get_mock_tier_stats() -> Dict[str, Any]:
        """Static method for mock tier statistics"""
        return {
            'sniper': {
                'win_rate': 0.85,
                'total_signals': 25,
                'active_signals': 2
            },
            'precision': {
                'win_rate': 0.78,
                'total_signals': 45,
                'active_signals': 3
            },
            'rapid': {
                'win_rate': 0.72,
                'total_signals': 85,
                'active_signals': 5
            },
            'training': {
                'win_rate': 0.65,
                'total_signals': 150,
                'active_signals': 8
            }
        }
        
    async def start_updates(self):
        """Start sending real-time updates"""
        logger.info("Starting fusion dashboard updates")
        while True:
            try:
                # Get system stats
                stats = self.flow.get_system_stats()
                
                # Get tier performance
                try:
                    tier_stats = signal_fusion_engine.get_tier_stats()
                except NameError:
                    logger.warning("signal_fusion_engine not available, using mock data")
                    tier_stats = self._get_mock_tier_stats()
                
                # Get active signals
                active_signals = []
                try:
                    for signal_id, active in self.flow.active_signals.items():
                        signal_data = {
                            'id': signal_id,
                            'pair': getattr(active.fused_signal, 'pair', 'UNKNOWN'),
                            'direction': getattr(active.fused_signal, 'direction', 'UNKNOWN'),
                            'confidence': getattr(active.fused_signal, 'confidence', 0),
                            'tier': getattr(active.fused_signal, 'tier', 'training').value if hasattr(active.fused_signal, 'tier') else 'training',
                            'sources': len(getattr(active.fused_signal, 'sources', [])),
                            'agreement': getattr(active.fused_signal, 'agreement_score', 0),
                            'age': (datetime.now() - active.timestamp).total_seconds() / 60,
                            'executions': len(getattr(active, 'executions', []))
                        }
                        active_signals.append(signal_data)
                except Exception as e:
                    logger.warning(f"Error processing active signals: {e}")
                    active_signals = []
                
                # Sort by confidence
                active_signals.sort(key=lambda x: x['confidence'], reverse=True)
                
                # Prepare update data
                update_data = {
                    'timestamp': datetime.now().isoformat(),
                    'tier_stats': tier_stats,
                    'active_signals': active_signals[:20],  # Top 20
                    'system_stats': stats,
                    'router_stats': stats.get('router_stats', {})
                }
                
                # Emit update
                try:
                    socketio.emit('fusion_update', update_data)
                    logger.debug(f"Emitted fusion update with {len(active_signals)} signals")
                except Exception as e:
                    logger.error(f"Failed to emit fusion update: {e}")
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(self.update_interval)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('fusion_dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get current system statistics"""
    try:
        if signal_flow:
            stats = signal_flow.get_system_stats()
            logger.debug("Retrieved system stats via API")
            return jsonify(stats)
        else:
            logger.warning("System not initialized for stats request")
            return jsonify({'error': 'System not initialized'})
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to retrieve stats'})

@app.route('/api/signals/active')
def get_active_signals():
    """Get active signals"""
    try:
        if signal_flow:
            signals = []
            for signal_id, active in signal_flow.active_signals.items():
                try:
                    signals.append({
                        'id': signal_id,
                        'pair': getattr(active.fused_signal, 'pair', 'UNKNOWN'),
                        'direction': getattr(active.fused_signal, 'direction', 'UNKNOWN'),
                        'confidence': getattr(active.fused_signal, 'confidence', 0),
                        'tier': getattr(active.fused_signal, 'tier', 'training').value if hasattr(active.fused_signal, 'tier') else 'training',
                        'timestamp': active.timestamp.isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Error processing signal {signal_id}: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(signals)} active signals via API")
            return jsonify(signals)
        else:
            logger.warning("System not initialized for active signals request")
            return jsonify([])
    except Exception as e:
        logger.error(f"Error getting active signals: {e}")
        return jsonify({'error': 'Failed to retrieve active signals'})

@app.route('/api/performance/<tier>')
def get_tier_performance(tier):
    """Get performance for specific tier"""
    try:
        try:
            tier_stats = signal_fusion_engine.get_tier_stats()
        except NameError:
            logger.warning("signal_fusion_engine not available, using mock data")
            tier_stats = FusionDashboard._get_mock_tier_stats()
        
        if tier in tier_stats:
            logger.debug(f"Retrieved performance for tier {tier}")
            return jsonify(tier_stats[tier])
        else:
            logger.warning(f"Invalid tier requested: {tier}")
            return jsonify({'error': 'Invalid tier'})
    except Exception as e:
        logger.error(f"Error getting tier performance for {tier}: {e}")
        return jsonify({'error': 'Failed to retrieve tier performance'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        logger.info("Client connected to fusion dashboard")
        emit('connected', {'status': 'Connected to Fusion Dashboard'})
    except Exception as e:
        logger.error(f"Error handling client connection: {e}")

@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request"""
    try:
        if signal_flow:
            stats = signal_flow.get_system_stats()
            emit('fusion_update', {'system_stats': stats})
            logger.debug("Handled manual update request")
        else:
            logger.warning("System not initialized for manual update request")
            emit('error', {'message': 'System not initialized'})
    except Exception as e:
        logger.error(f"Error handling update request: {e}")
        emit('error', {'message': 'Failed to get update'})

# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>BITTEN Signal Fusion Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #0a0a0a;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        .dashboard {
            max-width: 1600px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #00ff88;
            font-size: 2.5em;
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            border: 1px solid #333;
        }
        .stat-card h3 {
            margin-top: 0;
            color: #00ff88;
            font-size: 1.2em;
        }
        .tier-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
        }
        .tier-sniper { background: linear-gradient(45deg, #ff6b6b, #ff4444); }
        .tier-precision { background: linear-gradient(45deg, #ffa500, #ff8800); }
        .tier-rapid { background: linear-gradient(45deg, #4dabf7, #339af0); }
        .tier-training { background: linear-gradient(45deg, #69db7c, #51cf66); }
        .signals-table {
            width: 100%;
            background: #1a1a1a;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
        }
        .signals-table th {
            background: #2a2a2a;
            padding: 15px;
            text-align: left;
            color: #00ff88;
        }
        .signals-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #333;
        }
        .confidence-bar {
            width: 100px;
            height: 20px;
            background: #333;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff4444, #ffa500, #00ff88);
            transition: width 0.3s;
        }
        .direction-buy { color: #00ff88; }
        .direction-sell { color: #ff4444; }
        .chart-container {
            background: #1a1a1a;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>🎯 BITTEN Signal Fusion Dashboard <span class="live-indicator"></span></h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>🎯 Sniper Tier</h3>
                <div id="sniper-stats">
                    <p>Win Rate: <span class="win-rate">-</span></p>
                    <p>Total Signals: <span class="total-signals">-</span></p>
                    <p>Active: <span class="active-signals">-</span></p>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>⭐ Precision Tier</h3>
                <div id="precision-stats">
                    <p>Win Rate: <span class="win-rate">-</span></p>
                    <p>Total Signals: <span class="total-signals">-</span></p>
                    <p>Active: <span class="active-signals">-</span></p>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>⚡ Rapid Tier</h3>
                <div id="rapid-stats">
                    <p>Win Rate: <span class="win-rate">-</span></p>
                    <p>Total Signals: <span class="total-signals">-</span></p>
                    <p>Active: <span class="active-signals">-</span></p>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>📚 Training Tier</h3>
                <div id="training-stats">
                    <p>Win Rate: <span class="win-rate">-</span></p>
                    <p>Total Signals: <span class="total-signals">-</span></p>
                    <p>Active: <span class="active-signals">-</span></p>
                </div>
            </div>
        </div>
        
        <div class="stat-card">
            <h3>📊 Tier Distribution Today</h3>
            <div class="stats-grid">
                <div id="nibbler-dist">Nibbler: <span>-</span></div>
                <div id="fang-dist">Fang: <span>-</span></div>
                <div id="commander-dist">Commander: <span>-</span></div>
                <div id="apex-dist">Apex: <span>-</span></div>
            </div>
        </div>
        
        <div class="stat-card">
            <h3>🚀 Active Signals</h3>
            <table class="signals-table">
                <thead>
                    <tr>
                        <th>Pair</th>
                        <th>Direction</th>
                        <th>Tier</th>
                        <th>Confidence</th>
                        <th>Sources</th>
                        <th>Agreement</th>
                        <th>Age</th>
                        <th>Fires</th>
                    </tr>
                </thead>
                <tbody id="signals-tbody">
                    <!-- Signals will be inserted here -->
                </tbody>
            </table>
        </div>
        
        <div class="chart-container">
            <h3>📈 Performance Trends</h3>
            <canvas id="performanceChart"></canvas>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        // Chart setup
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Sniper Win Rate',
                        data: [],
                        borderColor: '#ff4444',
                        tension: 0.1
                    },
                    {
                        label: 'Precision Win Rate',
                        data: [],
                        borderColor: '#ffa500',
                        tension: 0.1
                    },
                    {
                        label: 'Rapid Win Rate',
                        data: [],
                        borderColor: '#339af0',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { color: '#ffffff' }
                    },
                    x: {
                        ticks: { color: '#ffffff' }
                    }
                }
            }
        });
        
        // Update functions
        function updateTierStats(tierStats) {
            for (const [tier, stats] of Object.entries(tierStats)) {
                const container = document.getElementById(`${tier}-stats`);
                if (container) {
                    container.querySelector('.win-rate').textContent = 
                        `${(stats.win_rate * 100).toFixed(1)}%`;
                    container.querySelector('.total-signals').textContent = 
                        stats.total_signals;
                    container.querySelector('.active-signals').textContent = 
                        stats.active_signals;
                }
            }
        }
        
        function updateSignalsTable(signals) {
            const tbody = document.getElementById('signals-tbody');
            tbody.innerHTML = '';
            
            signals.forEach(signal => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${signal.pair}</td>
                    <td class="direction-${signal.direction.toLowerCase()}">${signal.direction}</td>
                    <td><span class="tier-badge tier-${signal.tier}">${signal.tier.toUpperCase()}</span></td>
                    <td>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${signal.confidence}%"></div>
                        </div>
                        ${signal.confidence.toFixed(0)}%
                    </td>
                    <td>${signal.sources}</td>
                    <td>${signal.agreement.toFixed(0)}%</td>
                    <td>${signal.age.toFixed(0)}m</td>
                    <td>${signal.executions}</td>
                `;
            });
        }
        
        function updateDistribution(routerStats) {
            for (const [tier, stats] of Object.entries(routerStats)) {
                const elem = document.getElementById(`${tier}-dist`);
                if (elem) {
                    elem.querySelector('span').textContent = 
                        `${stats.signals_today}/${stats.daily_limit}`;
                }
            }
        }
        
        // Socket event handlers
        socket.on('connect', () => {
            console.log('Connected to dashboard');
        });
        
        socket.on('fusion_update', (data) => {
            if (data.tier_stats) {
                updateTierStats(data.tier_stats);
                
                // Update chart
                const time = new Date().toLocaleTimeString();
                performanceChart.data.labels.push(time);
                performanceChart.data.datasets[0].data.push(
                    data.tier_stats.sniper.win_rate * 100
                );
                performanceChart.data.datasets[1].data.push(
                    data.tier_stats.precision.win_rate * 100
                );
                performanceChart.data.datasets[2].data.push(
                    data.tier_stats.rapid.win_rate * 100
                );
                
                // Keep last 20 points
                if (performanceChart.data.labels.length > 20) {
                    performanceChart.data.labels.shift();
                    performanceChart.data.datasets.forEach(dataset => {
                        dataset.data.shift();
                    });
                }
                
                performanceChart.update();
            }
            
            if (data.active_signals) {
                updateSignalsTable(data.active_signals);
            }
            
            if (data.router_stats) {
                updateDistribution(data.router_stats);
            }
        });
        
        // Request initial update
        socket.emit('request_update');
    </script>
</body>
</html>
"""

def create_dashboard_app(flow: FusionEnhancedSignalFlow):
    """Create and configure dashboard app"""
    try:
        global signal_flow
        signal_flow = flow
        
        logger.info("Creating fusion dashboard app")
        
        # Save template
        import os
        os.makedirs('templates', exist_ok=True)
        with open('templates/fusion_dashboard.html', 'w') as f:
            f.write(DASHBOARD_HTML)
        logger.info("Saved dashboard template")
        
        # Create dashboard instance
        dashboard = FusionDashboard(flow)
        
        # Start background updates in separate thread
        import threading
        def run_updates():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(dashboard.start_updates())
            except Exception as e:
                logger.error(f"Error in dashboard update thread: {e}")
                logger.error(traceback.format_exc())
        
        update_thread = threading.Thread(target=run_updates, daemon=True)
        update_thread.start()
        logger.info("Started dashboard update thread")
        
        return app, socketio
        
    except Exception as e:
        logger.error(f"Error creating dashboard app: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    # Example standalone run
    from .complete_signal_flow_v3 import FusionEnhancedSignalFlow
    
    flow = FusionEnhancedSignalFlow()
    app, socketio = create_dashboard_app(flow)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)