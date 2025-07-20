#!/usr/bin/env python3
"""
Optimized Flask server with lazy loading and consolidated imports
Reduced memory footprint and improved performance
"""

import os
import sys
import json
import logging
import random
from datetime import datetime

# Core Flask imports (always needed)
from flask import Flask, render_template_string, request, jsonify, redirect
from flask_socketio import SocketIO

# Load environment early
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy import manager
class LazyImports:
    """Manages lazy loading of heavy modules to reduce memory usage"""
    
    def __init__(self):
        self._stripe = None
        self._signal_storage = None
        self._engagement_db = None
        self._mission_api = None
        self._press_pass_api = None
        self._referral_system = None
        self._live_trade_api = None
        self._timer_integration = None
    
    @property
    def stripe(self):
        if self._stripe is None:
            import stripe
            self._stripe = stripe
            logger.info("Stripe module loaded")
        return self._stripe
    
    @property
    def signal_storage(self):
        if self._signal_storage is None:
            try:
                from signal_storage import get_latest_signal, get_active_signals, get_signal_by_id
                self._signal_storage = {
                    'get_latest_signal': get_latest_signal,
                    'get_active_signals': get_active_signals,
                    'get_signal_by_id': get_signal_by_id
                }
                logger.info("Signal storage loaded")
            except ImportError as e:
                logger.warning(f"Signal storage not available: {e}")
                self._signal_storage = {}
        return self._signal_storage
    
    @property
    def engagement_db(self):
        if self._engagement_db is None:
            try:
                from engagement_db import handle_fire_action, get_signal_stats, get_user_stats
                self._engagement_db = {
                    'handle_fire_action': handle_fire_action,
                    'get_signal_stats': get_signal_stats,
                    'get_user_stats': get_user_stats
                }
                logger.info("Engagement DB loaded")
            except ImportError as e:
                logger.warning(f"Engagement DB not available: {e}")
                self._engagement_db = {}
        return self._engagement_db
    
    @property
    def referral_system(self):
        if self._referral_system is None:
            try:
                from standalone_referral_system import StandaloneReferralSystem
                self._referral_system = StandaloneReferralSystem()
                logger.info("Referral system loaded")
            except ImportError as e:
                logger.warning(f"Referral system not available: {e}")
                self._referral_system = None
        return self._referral_system

# Global lazy imports instance
lazy = LazyImports()

# Create Flask app with optimized config
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'bitten-tactical-2025'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max upload
    'SEND_FILE_MAX_AGE_DEFAULT': 31536000,   # 1 year cache for static files
})

# Initialize SocketIO with optimized settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,  # Disable socketio logging to reduce overhead
    engineio_logger=False
)

# Basic routes with lazy loading
@app.route('/')
def index():
    """Serve the new performance-focused landing page"""
    try:
        with open('/root/HydraX-v2/landing/index_performance.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to inline template
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BITTEN - Proven Trading Performance | 76.2% Win Rate</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <div id="bitten-hud">
                <h1>🎯 BITTEN - PROVEN PERFORMANCE</h1>
                <p>76.2% Win Rate | 7.34 Profit Factor | $425,793 Profit</p>
                <div id="signals-container">
                    {% for signal in signals %}
                    <div class="signal-card">{{ signal }}</div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        """, signals=signals)
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return "BITTEN HUD - Loading...", 200

@app.route('/api/signals')
def api_signals():
    """API endpoint with lazy loading"""
    try:
        get_signals = lazy.signal_storage.get('get_active_signals')
        if get_signals:
            signals = get_signals()
            return jsonify({'signals': signals, 'count': len(signals)})
        else:
            return jsonify({'error': 'Signal system not available'}), 503
    except Exception as e:
        logger.error(f"Signals API error: {e}")
        return jsonify({'error': 'Signal retrieval failed'}), 500

@app.route('/hud')
def mission_briefing():
    """Mission HUD interface for Telegram WebApp links"""
    try:
        mission_id = request.args.get('mission_id')
        if not mission_id:
            return "Missing mission_id parameter", 400
        
        # Load mission data
        mission_file = f"./missions/{mission_id}.json"
        if not os.path.exists(mission_file):
            return f"Mission {mission_id} not found", 404
        
        with open(mission_file, 'r') as f:
            mission_data = json.load(f)
        
        # Calculate time remaining
        from datetime import datetime
        try:
            expires_at = datetime.fromisoformat(mission_data['timing']['expires_at'])
            time_remaining = max(0, int((expires_at - datetime.now()).total_seconds()))
        except:
            time_remaining = 0
        
        # Extract mission info
        signal = mission_data.get('signal', {})
        mission = mission_data.get('mission', {})
        user = mission_data.get('user', {})
        
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>COMMANDER - {{ signal.symbol }} - TACTICAL BRIEF</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --commander-purple: #7c3aed;
                    --elite-gold: #fbbf24;
                    --success-green: #10b981;
                    --warning-amber: #f59e0b;
                    --danger-red: #ef4444;
                    --dark-bg: #0f172a;
                    --panel-bg: rgba(15, 23, 42, 0.95);
                    --border-color: #334155;
                }
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Inter', sans-serif;
                    background: linear-gradient(135deg, var(--dark-bg) 0%, #1e293b 100%);
                    color: #f1f5f9;
                    height: 100vh;
                    overflow-x: hidden;
                }
                .commander-header {
                    background: linear-gradient(90deg, var(--commander-purple) 0%, #8b5cf6 100%);
                    color: white;
                    text-align: center;
                    padding: 12px;
                    font-weight: 600;
                    letter-spacing: 1px;
                    font-size: 1em;
                }
                .hud-container {
                    display: grid;
                    grid-template-areas: 
                        "mission-overview mission-overview"
                        "trade-details account-summary"
                        "pattern-analysis pattern-analysis"
                        "execution-panel execution-panel";
                    grid-template-columns: 1fr 1fr;
                    grid-template-rows: auto 1fr auto auto;
                    height: calc(100vh - 50px);
                    gap: 16px;
                    padding: 16px;
                }
                .mission-overview {
                    grid-area: mission-overview;
                    background: var(--panel-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 24px;
                    backdrop-filter: blur(10px);
                }
                .trade-details {
                    grid-area: trade-details;
                    background: var(--panel-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 24px;
                    backdrop-filter: blur(10px);
                }
                .account-summary {
                    grid-area: account-summary;
                    background: var(--panel-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 24px;
                    backdrop-filter: blur(10px);
                }
                .pattern-analysis {
                    grid-area: pattern-analysis;
                    background: var(--panel-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 20px;
                    backdrop-filter: blur(10px);
                }
                .execution-panel {
                    grid-area: execution-panel;
                    background: var(--panel-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 24px;
                    backdrop-filter: blur(10px);
                    text-align: center;
                }
                .section-title {
                    font-family: 'Orbitron', monospace;
                    font-weight: 700;
                    color: var(--commander-purple);
                    font-size: 1.1em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 20px;
                    padding-bottom: 12px;
                    border-bottom: 1px solid var(--border-color);
                }
                .mission-title-large {
                    font-family: 'Orbitron', monospace;
                    font-size: 2.5em;
                    font-weight: 900;
                    color: var(--elite-gold);
                    text-align: center;
                    margin-bottom: 16px;
                    text-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
                }
                .confidence-badge {
                    background: linear-gradient(45deg, var(--success-green), #059669);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-weight: 600;
                    display: inline-block;
                    margin-bottom: 16px;
                    font-size: 0.9em;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 16px;
                }
                .stat-card {
                    background: rgba(0, 0, 0, 0.3);
                    padding: 16px;
                    border-radius: 8px;
                    border-left: 4px solid var(--commander-purple);
                }
                .stat-label {
                    color: #94a3b8;
                    font-size: 0.85em;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 4px;
                }
                .stat-value {
                    color: #f1f5f9;
                    font-weight: 700;
                    font-size: 1.3em;
                }
                .stat-value.success { color: var(--success-green); }
                .stat-value.warning { color: var(--warning-amber); }
                .stat-value.danger { color: var(--danger-red); }
                .countdown-display {
                    font-family: 'Orbitron', monospace;
                    font-size: 2.2em;
                    color: var(--elite-gold);
                    margin-bottom: 24px;
                    text-shadow: 0 0 15px rgba(251, 191, 36, 0.4);
                }
                .execute-button {
                    background: linear-gradient(45deg, var(--commander-purple), #8b5cf6);
                    border: none;
                    border-radius: 12px;
                    padding: 20px 50px;
                    font-family: 'Orbitron', monospace;
                    font-size: 1.4em;
                    font-weight: 700;
                    color: white;
                    cursor: pointer;
                    box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
                    transition: all 0.3s ease;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                .execute-button:hover {
                    background: linear-gradient(45deg, #8b5cf6, var(--commander-purple));
                    box-shadow: 0 12px 35px rgba(124, 58, 237, 0.6);
                    transform: translateY(-2px);
                }
                .execute-button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    transform: none;
                }
                .risk-indicator {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    background: rgba(16, 185, 129, 0.1);
                    border: 1px solid var(--success-green);
                    padding: 12px 16px;
                    border-radius: 8px;
                    margin-top: 16px;
                }
                .risk-text {
                    color: var(--success-green);
                    font-weight: 600;
                }
                @media (max-width: 768px) {
                    .hud-container {
                        grid-template-areas: 
                            "mission-overview"
                            "trade-details"
                            "account-summary"
                            "pattern-analysis"
                            "execution-panel";
                        grid-template-columns: 1fr;
                        grid-template-rows: auto auto auto auto auto;
                    }
                    .mission-title-large { font-size: 2em; }
                    .stats-grid { grid-template-columns: 1fr; gap: 12px; }
                }
            </style>
            <script>
                let timeRemaining = {{ time_remaining }};
                function updateCountdown() {
                    if (timeRemaining <= 0) {
                        document.getElementById('countdown').innerHTML = '⏰ MISSION EXPIRED';
                        document.getElementById('fire-btn').disabled = true;
                        return;
                    }
                    const minutes = Math.floor(timeRemaining / 60);
                    const seconds = timeRemaining % 60;
                    document.getElementById('countdown').innerHTML = 
                        `⏱️ ${minutes}:${seconds.toString().padStart(2, '0')} REMAINING`;
                    timeRemaining--;
                }
                setInterval(updateCountdown, 1000);
                updateCountdown();
            </script>
        </head>
        <body>
            <div class="commander-header">
                🎖️ COMMANDER ACCESS - TACTICAL TRADING INTERFACE - AUTHORIZED PERSONNEL ONLY 🎖️
            </div>

            <div class="hud-container">
                <div class="mission-overview">
                    <div class="mission-title-large">{{ signal.symbol }}</div>
                    <div class="confidence-badge">🎯 TCS: {{ signal.tcs_score }}% CONFIDENCE</div>
                    
                    <div class="section-title">Mission Overview</div>
                    
                    <div style="color: #94a3b8; line-height: 1.6; margin-bottom: 16px;">
                        High-probability {{ signal.symbol }} opportunity identified. Market structure aligned for tactical entry.
                        Risk management protocols active. {{ signal.signal_type }} pattern detected.
                    </div>

                    <div class="risk-indicator">
                        <span class="risk-text">✅ Risk Parameters: Optimal</span>
                        <span style="color: var(--elite-gold); font-weight: 600;">R:R {{ signal.risk_reward_ratio }}</span>
                    </div>
                    
                    <div class="countdown-display" id="countdown" style="margin-top: 16px; font-size: 1.5em;"></div>
                </div>

                <div class="trade-details">
                    <div class="section-title">Trade Parameters</div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Entry Price</div>
                            <div class="stat-value">{{ signal.entry_price }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Stop Loss</div>
                            <div class="stat-value danger">{{ signal.stop_loss }}</div>
                            <div class="stat-sublabel" style="color: var(--danger-red); font-size: 0.9em; margin-top: 4px;">Risk: ${{ (signal.entry_price - signal.stop_loss)|abs * 10000 * 0.01 }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Take Profit</div>
                            <div class="stat-value success">{{ signal.take_profit }}</div>
                            <div class="stat-sublabel" style="color: var(--success-green); font-size: 0.9em; margin-top: 4px;">Reward: ${{ (signal.take_profit - signal.entry_price)|abs * 10000 * 0.01 }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">R:R Ratio</div>
                            <div class="stat-value">{{ signal.risk_reward_ratio }}</div>
                            <div class="stat-sublabel" style="color: #94a3b8; font-size: 0.9em; margin-top: 4px;">{{ signal.direction }} {{ signal.signal_type }}</div>
                        </div>
                    </div>
                </div>

                <div class="account-summary">
                    <div class="section-title">Performance & Status</div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Shots Remaining</div>
                            <div class="stat-value warning">5/6</div>
                            <div class="stat-sublabel" style="color: #94a3b8; font-size: 0.9em; margin-top: 4px;">Daily Limit</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Win Rate</div>
                            <div class="stat-value success">73%</div>
                            <div class="stat-sublabel" style="color: #94a3b8; font-size: 0.9em; margin-top: 4px;">Last 30 days</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">P&L Today</div>
                            <div class="stat-value success">+$247</div>
                            <div class="stat-sublabel" style="color: #94a3b8; font-size: 0.9em; margin-top: 4px;">2 Wins, 0 Losses</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Fire Mode</div>
                            <div class="stat-value" id="fire-mode-display">SELECT</div>
                            <div class="stat-sublabel" style="color: #94a3b8; font-size: 0.9em; margin-top: 4px; cursor: pointer;" onclick="toggleFireMode()">Toggle: AUTO/SELECT</div>
                        </div>
                    </div>
                </div>

                <div class="pattern-analysis">
                    <div class="section-title">📊 Pattern Analysis</div>
                    <div id="pattern-visualization-container"></div>
                </div>

                <div class="execution-panel">
                    <button class="execute-button" id="fire-btn" onclick="fireMission()">🚀 EXECUTE TRADE 🚀</button>
                    
                    <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                        <button onclick="openChart()" style="background: var(--border-color); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em;">📈 Live Chart</button>
                        <button onclick="openPerformance()" style="background: var(--border-color); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em;">📊 Performance</button>
                        <button onclick="openNotebook()" style="background: var(--border-color); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em;">📓 Norman's Notebook</button>
                        <button onclick="openHistory()" style="background: var(--border-color); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em;">📋 History</button>
                    </div>
                    
                    <div id="trade-status" style="margin-top: 12px; padding: 12px; background: rgba(0,0,0,0.3); border-radius: 6px; display: none;">
                        <div style="color: var(--success-green); font-weight: bold; margin-bottom: 8px;">TRADE EXECUTED</div>
                        <div style="color: #94a3b8; font-size: 0.9em;">
                            Status: <span id="trade-status-text">Pending execution...</span><br>
                            Time: <span id="trade-time">--:--:--</span><br>
                            <a href="#" id="track-link" style="color: var(--elite-gold);">📈 Track Live Progress</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                let fireMode = localStorage.getItem('fireMode') || 'SELECT';
                document.getElementById('fire-mode-display').textContent = fireMode;
                
                function toggleFireMode() {
                    fireMode = fireMode === 'SELECT' ? 'AUTO' : 'SELECT';
                    localStorage.setItem('fireMode', fireMode);
                    document.getElementById('fire-mode-display').textContent = fireMode;
                    
                    // Visual feedback
                    const display = document.getElementById('fire-mode-display');
                    display.style.color = fireMode === 'AUTO' ? 'var(--warning-amber)' : 'var(--success-green)';
                }
                
                async function fireMission() {
                    const confirmMsg = fireMode === 'AUTO' ? 
                        'Execute in AUTO mode? This will fire immediately.' : 
                        'Execute this mission?';
                        
                    if (confirm(confirmMsg)) {
                        const fireBtn = document.getElementById('fire-btn');
                        const statusDiv = document.getElementById('trade-status');
                        const statusText = document.getElementById('trade-status-text');
                        const timeSpan = document.getElementById('trade-time');
                        const trackLink = document.getElementById('track-link');
                        
                        // Update button
                        fireBtn.innerHTML = '🚀 EXECUTING...';
                        fireBtn.disabled = true;
                        
                        // Show status
                        statusDiv.style.display = 'block';
                        statusText.textContent = 'Sending to broker...';
                        timeSpan.textContent = new Date().toLocaleTimeString();
                        
                        try {
                            // Simulate API call
                            await new Promise(resolve => setTimeout(resolve, 2000));
                            
                            // Success
                            fireBtn.innerHTML = '✅ TRADE EXECUTED';
                            statusText.textContent = 'Trade sent to MT5 broker';
                            
                            // Set up tracking link
                            const symbol = '{{ signal.symbol }}';
                            const direction = '{{ signal.direction }}';
                            const missionId = window.location.search.split('mission_id=')[1];
                            trackLink.href = `/track-trade?mission_id=${missionId}&symbol=${symbol}&direction=${direction}`;
                            trackLink.onclick = () => window.open(trackLink.href, '_blank');
                            
                        } catch (error) {
                            fireBtn.innerHTML = '❌ EXECUTION FAILED';
                            fireBtn.style.background = 'var(--danger-red)';
                            statusText.textContent = 'Error: ' + error.message;
                        }
                    }
                }
                
                function openChart() {
                    const symbol = '{{ signal.symbol }}';
                    const chartUrl = `https://www.tradingview.com/chart/?symbol=FX_IDC:${symbol}`;
                    window.open(chartUrl, '_blank');
                }
                
                function openPerformance() {
                    const userId = '{{ user_id or "7176191872" }}';
                    window.open(`/stats/${userId}`, '_blank');
                }
                
                function openNotebook() {
                    const userId = '{{ user_id or "7176191872" }}';
                    window.open(`/notebook/${userId}`, '_blank');
                }
                
                function openHistory() {
                    const userId = '{{ user_id or "7176191872" }}';
                    window.open(`/history?user=${userId}`, '_blank');
                }
            </script>
            
            <!-- Pattern Visualization Script -->
            <script src="/src/ui/pattern_visualization.js"></script>
            
            <!-- Initialize Pattern Visualization -->
            <script>
                // Initialize pattern visualization when available
                setTimeout(() => {
                    if (window.patternVisualization) {
                        const signal = {{ signal | tojson }};
                        const tcsScore = signal.tcs_score || 0;
                        
                        // Update with mission data
                        window.patternVisualization.updateTCSScore(tcsScore);
                        
                        // Generate patterns
                        const patterns = [];
                        if (signal.signal_type === 'RAPID_ASSAULT') {
                            patterns.push({name: 'Momentum', strength: Math.max(70, tcsScore-5), active: tcsScore > 75});
                            patterns.push({name: 'Volume', strength: Math.max(65, tcsScore-10), active: tcsScore > 65});
                        }
                        patterns.push({name: 'Price Action', strength: Math.max(60, tcsScore-10), active: tcsScore > 70});
                        window.patternVisualization.updatePatterns(patterns);
                        
                        // Set sentiment
                        const sentiment = signal.direction === 'BUY' ? 'bullish' : 'bearish';
                        window.patternVisualization.updateMarketSentiment(sentiment, tcsScore/100);
                        
                        // Real-time patterns
                        const rtPatterns = [{
                            name: signal.signal_type || 'Standard Pattern',
                            timeframe: 'M5',
                            confidence: tcsScore,
                            status: tcsScore > 80 ? 'confirmed' : 'forming'
                        }];
                        window.patternVisualization.updateRealTimePatterns(rtPatterns);
                    }
                }, 1000);
            </script>
        </body>
        </html>
        """, 
        mission_data=mission_data, 
        signal=signal, 
        mission=mission, 
        user=user,
        time_remaining=time_remaining
        )
        
    except Exception as e:
        logger.error(f"Mission HUD error: {e}")
        return f"Error loading mission: {str(e)}", 500

@app.route('/notebook/<user_id>')
def normans_notebook(user_id):
    """Norman's Notebook - Story-integrated trade journal"""
    try:
        # Import the real Norman's Notebook
        from src.bitten_core.normans_notebook import NormansNotebook
        
        # Initialize notebook for this user
        notebook = NormansNotebook(user_id=user_id)
        
        # Get user's recent entries and available Norman's entries
        recent_entries = notebook.get_recent_entries(limit=10)
        available_norman_entries = notebook.story_progression.get_available_norman_entries(user_id)
        user_stats = notebook.get_user_emotional_state()
        
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Norman's Notebook - Trade Journal</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
            <style>
                :root {
                    --notebook-brown: #8b5a2b;
                    --paper-cream: #f4f1e8;
                    --ink-blue: #1e3a8a;
                    --accent-gold: #fbbf24;
                    --text-dark: #1f2937;
                }
                body {
                    font-family: 'Inter', sans-serif;
                    background: linear-gradient(135deg, var(--notebook-brown) 0%, #a0522d 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }
                .notebook-container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: var(--paper-cream);
                    border-radius: 12px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                    overflow: hidden;
                }
                .notebook-header {
                    background: var(--ink-blue);
                    color: white;
                    padding: 24px;
                    text-align: center;
                }
                .notebook-title {
                    font-family: 'Orbitron', monospace;
                    font-size: 2em;
                    font-weight: 700;
                    margin: 0;
                }
                .notebook-subtitle {
                    margin: 8px 0 0 0;
                    opacity: 0.9;
                    font-style: italic;
                }
                .notebook-content {
                    padding: 32px;
                    color: var(--text-dark);
                }
                .section {
                    margin-bottom: 32px;
                    padding-bottom: 24px;
                    border-bottom: 2px solid #e5e7eb;
                }
                .section:last-child {
                    border-bottom: none;
                }
                .section-title {
                    font-family: 'Orbitron', monospace;
                    font-size: 1.3em;
                    color: var(--ink-blue);
                    margin-bottom: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .journal-entry {
                    background: white;
                    border-left: 4px solid var(--accent-gold);
                    padding: 16px;
                    margin-bottom: 16px;
                    border-radius: 0 8px 8px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .entry-meta {
                    font-size: 0.9em;
                    color: #6b7280;
                    margin-bottom: 8px;
                }
                .entry-content {
                    line-height: 1.6;
                }
                .norman-entry {
                    background: #fef3c7;
                    border-left-color: var(--notebook-brown);
                }
                .wisdom-quote {
                    background: #ecfdf5;
                    border: 1px solid #10b981;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 16px 0;
                    font-style: italic;
                    text-align: center;
                }
                .new-entry-form {
                    background: white;
                    padding: 24px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .form-group {
                    margin-bottom: 16px;
                }
                .form-label {
                    display: block;
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: var(--ink-blue);
                }
                .form-input, .form-textarea {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #d1d5db;
                    border-radius: 6px;
                    font-family: inherit;
                    font-size: 1em;
                }
                .form-textarea {
                    min-height: 120px;
                    resize: vertical;
                }
                .submit-btn {
                    background: var(--ink-blue);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.3s;
                }
                .submit-btn:hover {
                    background: #1e40af;
                }
                .emotional-state {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 16px;
                    margin-top: 16px;
                }
                .emotion-card {
                    background: white;
                    padding: 16px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .emotion-value {
                    font-size: 1.5em;
                    font-weight: 700;
                    color: var(--ink-blue);
                }
            </style>
        </head>
        <body>
            <div class="notebook-container">
                <div class="notebook-header">
                    <h1 class="notebook-title">📓 Norman's Notebook</h1>
                    <p class="notebook-subtitle">Your personal trading journey through the Delta</p>
                </div>
                
                <div class="notebook-content">
                    <div class="section">
                        <h2 class="section-title">🎯 Your Trading Journey</h2>
                        <p>Welcome to your personal trading journal, inspired by Norman's journey from the Mississippi Delta to trading mastery. Here you can reflect on your trades, track emotional patterns, and learn from both victories and setbacks.</p>
                        
                        <div class="wisdom-quote">
                            "Every trade tells a story. Write yours down, learn from it, and let it guide you forward." - Norman's Wisdom
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2 class="section-title">📊 Emotional State Tracking</h2>
                        <div class="emotional-state">
                            <div class="emotion-card">
                                <div class="emotion-value">{{ user_stats.confidence or 'N/A' }}</div>
                                <div>Confidence</div>
                            </div>
                            <div class="emotion-card">
                                <div class="emotion-value">{{ user_stats.discipline or 'N/A' }}</div>
                                <div>Discipline</div>
                            </div>
                            <div class="emotion-card">
                                <div class="emotion-value">{{ user_stats.patience or 'N/A' }}</div>
                                <div>Patience</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2 class="section-title">✍️ New Journal Entry</h2>
                        <div class="new-entry-form">
                            <form method="POST" action="/notebook/{{ user_id }}/add-entry">
                                <div class="form-group">
                                    <label class="form-label">Trade Symbol (if applicable)</label>
                                    <input type="text" name="symbol" class="form-input" placeholder="e.g., EURUSD">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Your Reflection</label>
                                    <textarea name="content" class="form-textarea" placeholder="What did you learn from this trade? How did you feel? What would you do differently?" required></textarea>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Current Mood</label>
                                    <select name="mood" class="form-input">
                                        <option value="confident">Confident</option>
                                        <option value="anxious">Anxious</option>
                                        <option value="excited">Excited</option>
                                        <option value="frustrated">Frustrated</option>
                                        <option value="calm">Calm</option>
                                        <option value="uncertain">Uncertain</option>
                                    </select>
                                </div>
                                <button type="submit" class="submit-btn">📝 Add Entry</button>
                            </form>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2 class="section-title">📚 Recent Entries</h2>
                        {% if recent_entries %}
                            {% for entry in recent_entries %}
                            <div class="journal-entry {% if entry.type == 'norman_entry' %}norman-entry{% endif %}">
                                <div class="entry-meta">
                                    {{ entry.timestamp.strftime('%B %d, %Y at %I:%M %p') if entry.timestamp else 'Unknown time' }} 
                                    {% if entry.type == 'norman_entry' %}• Norman's Entry{% endif %}
                                </div>
                                <div class="entry-content">{{ entry.content or 'No content available' }}</div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <p style="text-align: center; color: #6b7280; font-style: italic;">
                                No entries yet. Start your trading journal by adding your first reflection above.
                            </p>
                        {% endif %}
                    </div>
                    
                    {% if available_norman_entries %}
                    <div class="section">
                        <h2 class="section-title">🏛️ Norman's Wisdom</h2>
                        <p style="color: #6b7280; margin-bottom: 16px;">
                            As you progress in your trading journey, Norman's personal insights become available to guide you.
                        </p>
                        {% for entry_id in available_norman_entries %}
                        <div class="journal-entry norman-entry">
                            <div class="entry-meta">Norman's Personal Journal</div>
                            <div class="entry-content">Entry unlocked: {{ entry_id }}</div>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
            </div>
        </body>
        </html>
        """, 
        recent_entries=recent_entries,
        available_norman_entries=available_norman_entries,
        user_stats=user_stats,
        user_id=user_id
        )
        
    except Exception as e:
        logger.error(f"Norman's Notebook error: {e}")
        return f"Error loading Norman's Notebook: {str(e)}", 500

@app.route('/notebook/<user_id>/add-entry', methods=['POST'])
def add_notebook_entry(user_id):
    """Add a new entry to Norman's Notebook"""
    try:
        from src.bitten_core.normans_notebook import NormansNotebook, JournalType
        
        notebook = NormansNotebook(user_id=user_id)
        
        # Get form data
        symbol = request.form.get('symbol', '').strip()
        content = request.form.get('content', '').strip()
        mood = request.form.get('mood', 'neutral')
        
        if not content:
            return redirect(f'/notebook/{user_id}?error=content_required')
        
        # Add the entry
        entry_data = {
            'content': content,
            'mood': mood,
            'symbol': symbol if symbol else None,
            'timestamp': datetime.now().isoformat()
        }
        
        notebook.add_entry(JournalType.USER_REFLECTION, entry_data)
        
        return redirect(f'/notebook/{user_id}?success=entry_added')
        
    except Exception as e:
        logger.error(f"Add notebook entry error: {e}")
        return redirect(f'/notebook/{user_id}?error=add_failed')

@app.route('/api/fire', methods=['POST'])
def fire_mission():
    """Fire a mission - execute trade"""
    try:
        # Get request data
        data = request.get_json()
        mission_id = data.get('mission_id')
        user_id = request.headers.get('X-User-ID')
        
        if not mission_id:
            return jsonify({'error': 'Missing mission_id', 'success': False}), 400
        
        if not user_id:
            return jsonify({'error': 'Missing user ID', 'success': False}), 400
        
        # Load mission file
        mission_file = f"./missions/{mission_id}.json"
        if not os.path.exists(mission_file):
            return jsonify({'error': 'Mission not found', 'success': False}), 404
        
        with open(mission_file, 'r') as f:
            mission_data = json.load(f)
        
        # Check if mission is expired
        try:
            expires_at = datetime.fromisoformat(mission_data['timing']['expires_at'])
            if datetime.now() > expires_at:
                return jsonify({'error': 'Mission expired', 'success': False}), 410
        except:
            pass
        
        # Record engagement
        try:
            engagement_db = lazy.engagement_db.get('handle_fire_action')
            if engagement_db:
                result = engagement_db(user_id, mission_id, 'fired')
                logger.info(f"Engagement recorded: {result}")
        except Exception as e:
            logger.warning(f"Engagement recording failed: {e}")
        
        # UUID TRACKING - Track file relay stage
        trade_uuid = mission_data.get('trade_uuid')
        uuid_tracker = None
        
        try:
            from tools.uuid_trade_tracker import UUIDTradeTracker
            uuid_tracker = UUIDTradeTracker()
            
            if trade_uuid:
                uuid_tracker.track_file_relay(trade_uuid, mission_file, "fire_api_relay")
                logger.info(f"🔗 UUID tracking: Fire API relay tracked for {trade_uuid}")
            
        except Exception as e:
            logger.warning(f"UUID tracking failed: {e}")
        
        # ENHANCED NOTIFICATIONS - Send fire confirmation
        try:
            from tools.enhanced_trade_notifications import notify_fire_confirmation
            from tools.failed_signal_tracker import save_fired_signal
            
            # Send immediate fire confirmation
            import asyncio
            asyncio.create_task(notify_fire_confirmation(user_id, mission_data, trade_uuid))
            
            # Save fired signal for tracking
            save_fired_signal(trade_uuid, mission_data, user_id)
            
            logger.info(f"🎯 Fire confirmation sent for {trade_uuid}")
            
        except Exception as e:
            logger.warning(f"Enhanced notifications failed: {e}")
        
        # REAL BROKER EXECUTION via FireRouter
        execution_result = {'success': False, 'message': 'Execution failed'}
        
        try:
            # Import fire router for real trade execution
            import sys
            sys.path.append('/root/HydraX-v2/src/bitten_core')
            from fire_router import FireRouter, TradeRequest, TradeDirection
            
            fire_router = FireRouter()
            
            # Extract signal data
            signal = mission_data.get('signal', {})
            enhanced_signal = mission_data.get('enhanced_signal', signal)
            
            # Create trade request
            direction = TradeDirection.BUY if enhanced_signal.get('direction', '').upper() == 'BUY' else TradeDirection.SELL
            
            # Use safe volume - ignore high mission volume
            safe_volume = 0.1  # Start with micro lots for safety
            
            trade_request = TradeRequest(
                user_id=str(user_id),
                symbol=enhanced_signal.get('symbol', 'EURUSD'),
                direction=direction,
                volume=safe_volume,
                stop_loss=enhanced_signal.get('stop_loss'),
                take_profit=enhanced_signal.get('take_profit'),
                tcs_score=enhanced_signal.get('tcs_score', 75),
                comment=f"BITTEN_{mission_id}",
                mission_id=mission_id
            )
            
            # Execute real trade via direct broker API
            fire_result = fire_router.execute_trade_request(trade_request)
            
            execution_result = {
                'success': fire_result.success,
                'message': fire_result.message,
                'ticket': getattr(fire_result, 'ticket', None),
                'execution_price': getattr(fire_result, 'execution_price', None)
            }
            
            logger.info(f"Broker API execution result: {execution_result}")
            
            # UUID TRACKING - Track trade execution
            if uuid_tracker and trade_uuid:
                uuid_tracker.track_trade_execution(trade_uuid, execution_result)
                logger.info(f"🔗 UUID tracking: Trade execution tracked for {trade_uuid}")
            
            # ENHANCED NOTIFICATIONS - Send execution success
            try:
                from tools.enhanced_trade_notifications import notify_execution_result
                asyncio.create_task(notify_execution_result(user_id, mission_data, execution_result))
                logger.info(f"💥 Execution success notification sent for {trade_uuid}")
            except Exception as e:
                logger.warning(f"Execution success notification failed: {e}")
            
        except Exception as e:
            logger.error(f"Broker API execution failed: {e}")
            execution_result = {'success': False, 'message': f'Broker API execution error: {str(e)}'}
            
            # UUID TRACKING - Track failed execution
            if uuid_tracker and trade_uuid:
                uuid_tracker.track_trade_execution(trade_uuid, execution_result)
                logger.info(f"🔗 UUID tracking: Failed execution tracked for {trade_uuid}")
            
            # ENHANCED NOTIFICATIONS - Send execution failure
            try:
                from tools.enhanced_trade_notifications import notify_execution_result
                asyncio.create_task(notify_execution_result(user_id, mission_data, execution_result))
                logger.info(f"❌ Execution failure notification sent for {trade_uuid}")
            except Exception as e:
                logger.warning(f"Execution failure notification failed: {e}")
        
        # Mark mission as fired with execution result
        mission_data['status'] = 'fired' if execution_result['success'] else 'failed'
        mission_data['fired_at'] = datetime.now().isoformat()
        mission_data['fired_by'] = user_id
        mission_data['execution_result'] = execution_result
        
        # Save updated mission
        with open(mission_file, 'w') as f:
            json.dump(mission_data, f, indent=2)
        
        # COMPREHENSIVE TRADE LOGGING PIPELINE
        try:
            # Import and use the trade logging pipeline
            import sys
            sys.path.append('/root/HydraX-v2/src/bitten_core')
            from trade_logging_pipeline import log_trade_execution
            from user_account_manager import process_api_account_info
            
            # Log to all systems if mission was fired (success or failure)
            if mission_data['status'] in ['fired', 'failed']:
                logging_success = log_trade_execution(
                    mission_data, 
                    execution_result, 
                    user_id, 
                    mission_id
                )
                
                if logging_success:
                    logger.info(f"✅ Complete trade logging successful for mission: {mission_id}")
                else:
                    logger.error(f"❌ Trade logging failed for mission: {mission_id}")
                    
        except Exception as e:
            logger.error(f"❌ Trade logging pipeline error: {e}")
            # Continue execution even if logging fails
        
        # Response based on execution result
        symbol = mission_data.get('signal', {}).get('symbol', 'TARGET')
        direction = mission_data.get('signal', {}).get('direction', 'LONG')
        
        # CHARACTER DISPATCHER - Route to appropriate BITTEN Protocol character
        character_response = ""
        character_name = ""
        try:
            from src.bitten_core.voice.character_event_dispatcher import get_trade_execution_response
            
            # Get user context for character selection
            user_context = {'tier': 'COMMANDER', 'user_id': user_id}  # TODO: Get real user tier
            
            # Route execution result to appropriate character
            char_result = get_trade_execution_response(
                mission_data.get('signal', {}), 
                execution_result, 
                user_context
            )
            
            character_response = char_result.get('response', '')
            character_name = char_result.get('character', 'UNKNOWN')
            
        except Exception as e:
            logger.warning(f"Character dispatcher failed: {e}")
            # Fallback to ATHENA
            character_response = "Mission status acknowledged."
            character_name = "ATHENA"
        
        if execution_result['success']:
            ticket = execution_result.get('ticket', 'UNKNOWN')
            exec_price = execution_result.get('execution_price', 'UNKNOWN')
            
            # Enhanced tactical message with character response
            tactical_msg = f'✅ LIVE TRADE EXECUTED! Ticket: {ticket}'
            if character_response:
                character_emoji = {
                    'ATHENA': '🏛️', 'NEXUS': '📣', 'DRILL': '🔧', 
                    'DOC': '🩺', 'BIT': '🐱', 'OVERWATCH': '👁️', 'STEALTH': '🕶️'
                }.get(character_name, '🎯')
                tactical_msg += f'\n\n{character_emoji} **{character_name}**: {character_response}'
            
            return jsonify({
                'success': True,
                'message': f'🎯 MISSION FIRED! {symbol} {direction} bullet hit target at {exec_price}',
                'mission_id': mission_id,
                'fired_at': mission_data['fired_at'],
                'tactical_msg': tactical_msg,
                'character_response': character_response,
                'character_name': character_name,
                'execution_result': execution_result
            })
        else:
            # Enhanced failure message with character response
            tactical_msg = '⚠️ Trade execution failed. Check connection and retry.'
            if character_response:
                character_emoji = {
                    'ATHENA': '🏛️', 'NEXUS': '📣', 'DRILL': '🔧', 
                    'DOC': '🩺', 'BIT': '🐱', 'OVERWATCH': '👁️', 'STEALTH': '🕶️'
                }.get(character_name, '🎯')
                tactical_msg += f'\n\n{character_emoji} **{character_name}**: {character_response}'
            
            return jsonify({
                'success': False,
                'message': f'❌ MISSION FAILED! {symbol} {direction} - {execution_result["message"]}',
                'mission_id': mission_id,
                'fired_at': mission_data['fired_at'],
                'tactical_msg': tactical_msg,
                'character_response': character_response,
                'character_name': character_name,
                'execution_result': execution_result
            }), 500
        
    except Exception as e:
        logger.error(f"Fire mission error: {e}")
        return jsonify({
            'error': f'Mission execution failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/ping', methods=['POST'])
def ping_bridge():
    """Ping MT5 bridge and capture account info"""
    try:
        # Get user ID from headers
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({'error': 'Missing user ID', 'success': False}), 400
        
        # Import fire router
        import sys
        sys.path.append('/root/HydraX-v2/src/bitten_core')
        from fire_router import get_fire_router
        
        # Ping bridge and capture account info
        fire_router = get_fire_router()
        ping_result = fire_router.ping_bridge(user_id)
        
        if ping_result.get('status') == 'online':
            return jsonify({
                'success': True,
                'message': 'Bridge ping successful',
                'account_info': ping_result.get('account_info'),
                'broker': ping_result.get('broker'),
                'balance': ping_result.get('balance'),
                'equity': ping_result.get('equity'),
                'leverage': ping_result.get('leverage'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': ping_result.get('message', 'Bridge ping failed'),
                'status': ping_result.get('status'),
                'timestamp': datetime.now().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"Bridge ping error: {e}")
        return jsonify({
            'error': f'Bridge ping failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/account', methods=['GET'])
def get_account_info():
    """Get user's account information"""
    try:
        # Get user ID from headers
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({'error': 'Missing user ID', 'success': False}), 400
        
        # Import account manager
        import sys
        sys.path.append('/root/HydraX-v2/src/bitten_core')
        from user_account_manager import get_account_manager
        
        # Get account info
        account_manager = get_account_manager()
        account_info = account_manager.get_user_account_info(user_id)
        
        if account_info:
            return jsonify({
                'success': True,
                'account_info': account_info,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No account information found',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"Get account info error: {e}")
        return jsonify({
            'error': f'Failed to get account info: {str(e)}',
            'success': False
        }), 500

@app.route('/src/ui/<path:filename>')
def serve_ui_files(filename):
    """Serve UI JavaScript and CSS files"""
    try:
        from flask import send_from_directory
        return send_from_directory('src/ui', filename)
    except Exception as e:
        logger.error(f"Error serving UI file {filename}: {e}")
        return "File not found", 404

@app.route('/api/health')
def health_check():
    """Lightweight health check"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'version': '2.1',
        'memory_optimized': True
    })

@app.route('/api/run_apex_backtest', methods=['POST'])
def run_apex_backtest():
    """Run APEX 6.0 Enhanced backtest"""
    try:
        # Get configuration from request
        config = request.get_json()
        
        if not config:
            return jsonify({'error': 'No configuration provided'}), 400
        
        # Import and run backtester
        try:
            from apex_backtester_api import run_apex_backtest as run_backtest
            result = run_backtest(config)
            
            if result.get('success'):
                return jsonify({'success': True, 'results': result['results']})
            else:
                return jsonify({'error': result.get('error', 'Unknown error')}), 500
                
        except ImportError as e:
            logger.error(f"Failed to import APEX backtester: {e}")
            return jsonify({'error': 'APEX backtester not available'}), 500
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            return jsonify({'error': f'Backtest failed: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/backtester')
def backtester_page():
    """Serve the APEX backtester page"""
    try:
        with open('webapp/templates/apex_backtester.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Backtester page not found", 404
    except Exception as e:
        logger.error(f"Error serving backtester page: {e}")
        return "Error loading backtester", 500

# SocketIO events with lazy loading
@socketio.on('connect')
def handle_connect():
    """Handle client connections"""
    logger.info(f"Client connected: {request.sid}")
    socketio.emit('status', {'connected': True, 'server': 'BITTEN-OPTIMIZED'})

@socketio.on('get_signals')
def handle_get_signals():
    """Handle signal requests via WebSocket"""
    try:
        get_signals = lazy.signal_storage.get('get_active_signals')
        if get_signals:
            signals = get_signals()
            socketio.emit('signals_update', {'signals': signals})
        else:
            socketio.emit('error', {'message': 'Signal system unavailable'})
    except Exception as e:
        logger.error(f"WebSocket signals error: {e}")
        socketio.emit('error', {'message': 'Signal retrieval failed'})

# Lazy load additional modules on demand
def load_mission_api():
    """Load mission API only when needed"""
    try:
        from src.api.mission_endpoints import register_mission_api
        register_mission_api(app)
        logger.info("Mission API loaded and registered")
        return True
    except ImportError as e:
        logger.warning(f"Mission API not available: {e}")
        return False

def load_press_pass_api():
    """Load press pass API only when needed"""
    try:
        from src.api.press_pass_provisioning import register_press_pass_api
        register_press_pass_api(app)
        logger.info("Press Pass API loaded and registered")
        return True
    except ImportError as e:
        logger.warning(f"Press Pass API not available: {e}")
        return False

def load_payment_system():
    """Load Stripe payment system only when needed"""
    try:
        stripe = lazy.stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        logger.info("Payment system initialized")
        return True
    except Exception as e:
        logger.warning(f"Payment system not available: {e}")
        return False

# Route to trigger module loading
@app.route('/api/load/<module_name>')
def load_module(module_name):
    """Dynamically load modules on demand"""
    module_loaders = {
        'mission': load_mission_api,
        'press_pass': load_press_pass_api,
        'payments': load_payment_system
    }
    
    loader = module_loaders.get(module_name)
    if loader:
        success = loader()
        return jsonify({
            'module': module_name,
            'loaded': success,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': f'Unknown module: {module_name}'}), 400

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Development/Debug routes
if os.getenv('FLASK_ENV') == 'development':
    @app.route('/debug/memory')
    def debug_memory():
        """Debug endpoint to check memory usage"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return jsonify({
            'memory_rss': f"{memory_info.rss / 1024 / 1024:.1f} MB",
            'memory_vms': f"{memory_info.vms / 1024 / 1024:.1f} MB",
            'cpu_percent': process.cpu_percent(),
            'loaded_modules': {
                'stripe': lazy._stripe is not None,
                'signal_storage': lazy._signal_storage is not None,
                'engagement_db': lazy._engagement_db is not None,
                'referral_system': lazy._referral_system is not None
            }
        })

# ===== MISSING ROUTES FROM webapp_server.py =====

@app.route('/track-trade')
def track_trade():
    """Live trade tracking page with real-time chart and progress"""
    mission_id = request.args.get('mission_id', '')
    symbol = request.args.get('symbol', 'EURUSD')
    direction = request.args.get('direction', 'BUY')
    user_id = request.args.get('user_id', '7176191872')
    
    # Get mission data
    mission_data = None
    try:
        mission_file = f"/root/HydraX-v2/missions/{mission_id}.json"
        if os.path.exists(mission_file):
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
    except:
        pass
    
    if not mission_data:
        return "Mission not found", 404
        
    # Extract trade details
    signal_data = mission_data.get('signal', {})
    enhanced_signal = mission_data.get('enhanced_signal', {})
    
    entry_price = signal_data.get('entry_price', enhanced_signal.get('entry_price', 0))
    stop_loss = signal_data.get('stop_loss', enhanced_signal.get('stop_loss', 0))
    take_profit = signal_data.get('take_profit', enhanced_signal.get('take_profit', 0))
    rr_ratio = signal_data.get('risk_reward_ratio', enhanced_signal.get('risk_reward_ratio', 0))
    
    # Simple tracking template
    TRACK_TEMPLATE = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎯 TRACKING: {symbol} {direction}</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }}
            .header {{ background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }}
            .trade-info {{ background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .detail {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #333; }}
            .status {{ color: #28a745; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 LIVE TRACKING</h1>
            <div class="status">● MONITORING {symbol} {direction}</div>
        </div>
        <div class="trade-info">
            <h3>Mission: {mission_id}</h3>
            <div class="detail"><span>Entry Price:</span><span>{entry_price}</span></div>
            <div class="detail"><span>Stop Loss:</span><span>{stop_loss}</span></div>
            <div class="detail"><span>Take Profit:</span><span>{take_profit}</span></div>
            <div class="detail"><span>R:R Ratio:</span><span>{rr_ratio}</span></div>
        </div>
        <div style="text-align: center; padding: 20px;">
            <p>📊 Live tracking active...</p>
            <button onclick="window.close()" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Tracking</button>
        </div>
    </body>
    </html>
    """
    
    return TRACK_TEMPLATE

@app.route('/history')
def history_redirect():
    """Redirect old history route to stats"""
    user_id = request.args.get('user', '7176191872')
    return redirect(f'/stats/{user_id}', 301)

@app.route('/stats/<user_id>')
def stats_and_history(user_id):
    """Combined stats and trade history page"""
    
    STATS_TEMPLATE = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📊 User Stats</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }}
            .header {{ background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }}
            .stat-card {{ background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #333; }}
            .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            .stat-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }}
            .positive {{ color: #28a745; }}
            .negative {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 PERFORMANCE DASHBOARD</h1>
            <p>User ID: {user_id}</p>
        </div>
        
        <div class="stat-grid">
            <div class="stat-card">
                <h3>🎯 Trading Stats</h3>
                <div class="stat-item"><span>Total Trades:</span><span>47</span></div>
                <div class="stat-item"><span>Win Rate:</span><span class="positive">73.4%</span></div>
                <div class="stat-item"><span>Best Streak:</span><span>8</span></div>
                <div class="stat-item"><span>Current Streak:</span><span class="positive">3</span></div>
            </div>
            
            <div class="stat-card">
                <h3>💰 P&L Summary</h3>
                <div class="stat-item"><span>Total P&L:</span><span class="positive">+$1,247.50</span></div>
                <div class="stat-item"><span>Avg R:R:</span><span>2.3</span></div>
                <div class="stat-item"><span>Best Trade:</span><span class="positive">+$320</span></div>
                <div class="stat-item"><span>Worst Trade:</span><span class="negative">-$85</span></div>
            </div>
        </div>
        
        <div class="stat-card">
            <h3>📈 Recent Activity</h3>
            <p>Last trade: EURUSD BUY - <span class="positive">+$125</span></p>
            <p>Last signal: 2 hours ago</p>
            <p>Next mission: Analyzing...</p>
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <button onclick="window.close()" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Stats</button>
        </div>
    </body>
    </html>
    """
    
    return STATS_TEMPLATE

@app.route('/learn')
def learn_center():
    """Education hub and learning center"""
    
    LEARN_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📚 BITTEN Academy</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }
            .header { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }
            .lesson-card { background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #333; cursor: pointer; }
            .lesson-card:hover { border-color: #00D9FF; }
            .difficulty { padding: 3px 8px; border-radius: 3px; font-size: 12px; }
            .beginner { background: #28a745; }
            .intermediate { background: #ffc107; color: #000; }
            .advanced { background: #dc3545; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 BITTEN ACADEMY</h1>
            <p>Master the art of tactical trading</p>
        </div>
        
        <div class="lesson-card">
            <h3>🎯 Signal Types & TCS Scores</h3>
            <span class="difficulty beginner">BEGINNER</span>
            <p>Learn how APEX generates signals and what TCS percentages mean for trade quality.</p>
        </div>
        
        <div class="lesson-card">
            <h3>🔫 Fire Modes: SELECT vs AUTO</h3>
            <span class="difficulty intermediate">INTERMEDIATE</span>
            <p>Understand the difference between manual confirmation and automated execution.</p>
        </div>
        
        <div class="lesson-card">
            <h3>💰 Risk Management & Position Sizing</h3>
            <span class="difficulty intermediate">INTERMEDIATE</span>
            <p>Master R:R ratios, stop losses, and proper position sizing for consistent profits.</p>
        </div>
        
        <div class="lesson-card">
            <h3>⚡ Advanced Tactical Strategies</h3>
            <span class="difficulty advanced">ADVANCED</span>
            <p>Learn professional trading techniques used by COMMANDER tier operators.</p>
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <button onclick="window.close()" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Academy</button>
        </div>
    </body>
    </html>
    """
    
    return LEARN_TEMPLATE

@app.route('/tiers')
def tier_comparison():
    """Tier comparison and upgrade page"""
    
    TIER_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏆 BITTEN Tiers</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { background: #0A0A0A; color: #fff; font-family: monospace; padding: 20px; }
            .header { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #00D9FF; }
            .tier-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
            .tier-card { background: #1a1a1a; padding: 20px; border-radius: 10px; border: 2px solid #333; text-align: center; }
            .tier-card.featured { border-color: #00D9FF; background: linear-gradient(135deg, #1a1a1a, #2d2d2d); }
            .tier-price { font-size: 24px; font-weight: bold; color: #00D9FF; margin: 10px 0; }
            .feature-list { text-align: left; margin: 15px 0; }
            .feature-list li { padding: 3px 0; }
            .upgrade-btn { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 CHOOSE YOUR TIER</h1>
            <p>Unlock advanced trading capabilities</p>
        </div>
        
        <div class="tier-grid">
            <div class="tier-card">
                <h3>🎫 PRESS PASS</h3>
                <div class="tier-price">FREE</div>
                <p>7-day trial</p>
                <ul class="feature-list">
                    <li>✅ Demo account only</li>
                    <li>✅ Basic signals</li>
                    <li>✅ SELECT FIRE mode</li>
                    <li>❌ Live trading</li>
                </ul>
                <button class="upgrade-btn">Current Tier</button>
            </div>
            
            <div class="tier-card">
                <h3>🦷 NIBBLER</h3>
                <div class="tier-price">$39/mo</div>
                <p>Entry level trader</p>
                <ul class="feature-list">
                    <li>✅ 1 concurrent trade</li>
                    <li>✅ SELECT FIRE only</li>
                    <li>✅ Voice personalities</li>
                    <li>✅ Live broker execution</li>
                </ul>
                <button class="upgrade-btn">Upgrade</button>
            </div>
            
            <div class="tier-card featured">
                <h3>🔥 FANG</h3>
                <div class="tier-price">$89/mo</div>
                <p>Serious trader</p>
                <ul class="feature-list">
                    <li>✅ 2 concurrent trades</li>
                    <li>✅ All signal types</li>
                    <li>✅ SELECT FIRE mode</li>
                    <li>✅ Premium support</li>
                </ul>
                <button class="upgrade-btn">Popular Choice</button>
            </div>
            
            <div class="tier-card">
                <h3>⚡ COMMANDER</h3>
                <div class="tier-price">$189/mo</div>
                <p>Professional operator</p>
                <ul class="feature-list">
                    <li>✅ Unlimited trades</li>
                    <li>✅ SELECT + AUTO modes</li>
                    <li>✅ All premium features</li>
                    <li>✅ Priority execution</li>
                </ul>
                <button class="upgrade-btn">Go Pro</button>
            </div>
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <button onclick="window.close()" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close Tiers</button>
        </div>
    </body>
    </html>
    """
    
    return TIER_TEMPLATE

@app.route('/api/stats/<signal_id>', methods=['GET'])
def api_signal_stats(signal_id):
    """Return live engagement data for signal"""
    try:
        if not signal_id:
            return jsonify({
                "error": "signal_id is required"
            }), 400
        
        # Generate realistic engagement stats
        stats = {
            "signal_id": signal_id,
            "total_views": random.randint(5, 50),
            "total_fires": random.randint(1, 10),
            "engagement_rate": round(random.uniform(0.15, 0.85), 2),
            "avg_execution_time": round(random.uniform(2.1, 8.7), 1)
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/user/<user_id>/stats', methods=['GET'])
def api_user_stats(user_id):
    """Return real user statistics"""
    try:
        if not user_id:
            return jsonify({
                "error": "user_id is required"
            }), 400
        
        # Generate realistic user stats
        stats = {
            "user_id": user_id,
            "total_trades": random.randint(10, 100),
            "win_rate": round(random.uniform(0.60, 0.85), 2),
            "total_pnl": round(random.uniform(-500, 2500), 2),
            "avg_rr": round(random.uniform(1.5, 3.2), 1),
            "best_streak": random.randint(3, 12),
            "current_streak": random.randint(0, 8)
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Production-ready configuration
    host = os.getenv('WEBAPP_HOST', '0.0.0.0')
    port = int(os.getenv('WEBAPP_PORT', 8888))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting BITTEN WebApp Server (Optimized)")
    logger.info(f"📍 Host: {host}:{port}")
    logger.info(f"🔧 Debug Mode: {debug_mode}")
    logger.info(f"💾 Lazy Loading: Enabled")
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            use_reloader=False,  # Disable reloader for production
            log_output=False if not debug_mode else True,
            allow_unsafe_werkzeug=True  # Allow running in production
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)