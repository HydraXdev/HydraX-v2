#!/usr/bin/env python3
"""BITTEN ULTIMATE FUSION - Military precision meets personal journey"""

from flask import Flask, render_template_string, request, jsonify
import json
import urllib.parse
import random
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# MILITARY-GRADE COLORBLIND-SAFE COLORS
FUSION_COLORS = {
    'nibbler': {
        'primary': '#00D9FF',      # Cyan (colorblind-safe)
        'secondary': '#FFFFFF',     
        'warning': '#FF9500',      # Orange
        'danger': '#FF3B30',       # Red
        'success': '#00D9FF',      # Cyan
        'background': '#000000',   
        'surface': '#0F0F0F',      
        'border': '#1A1A1A',
        'text_primary': '#FFFFFF',
        'text_secondary': '#B0B0B0',
        'accent': '#FFD700',       # Gold
        'tactical': '#4A5568',     # Steel gray
        'intel': '#2D3748',        # Dark steel
        'bit_command': '#FF9500',  # Commander Bit orange
        'money_positive': '#00FF88', # Money green (colorblind visible)
        'money_negative': '#FF4444', # Money red
    }
}

def get_tier_styles(tier):
    return FUSION_COLORS.get(tier.lower(), FUSION_COLORS['nibbler'])

def get_user_stats(user_id):
    """Get comprehensive user stats"""
    return {
        'callsign': 'SOLDIER-7',
        'user_id': user_id,
        'rank': 'Private First Class',
        'tier': 'nibbler',
        'level': 23,
        'xp': 4750,
        'xp_to_next': 5000,
        'combat_rating': 87,
        'rounds_remaining': 3,
        'accuracy': 75,
        'win_rate': 72,
        'avg_rr': 2.1,
        'total_pips': 347,
        'total_profit': 2847.50,  # USD
        'confirmed_kills': 2.4,  # Profit in risk units
        'missions_completed': 47,
        'missions_failed': 18,
        'current_streak': 3,
        'best_streak': 7,
        'command_trust': 85,
        'last_5_trades': ['W', 'W', 'W', 'L', 'W'],
        'journal_entries': 12,
        'achievements_unlocked': 8,
        'squad_rank': 14,  # Out of 127 in squad
        'global_rank': 1247,  # Out of 15,000
    }

def get_market_intel():
    """Get live market intelligence"""
    return {
        'traders_online': 342,
        'signals_active': 7,
        'global_win_rate': 71,
        'this_signal_engagement': 45,  # % who took this signal
        'avg_execution_time': '2m 14s',
        'top_performer': {'callsign': 'APEX-1', 'profit': '+18.2%'},
        'recent_executions': [
            {'callsign': 'WOLF-23', 'result': '+42 pips', 'time': '30s ago'},
            {'callsign': 'EAGLE-7', 'result': '+38 pips', 'time': '2m ago'},
            {'callsign': 'VIPER-12', 'result': '-25 pips', 'time': '5m ago'},
        ]
    }

def calculate_money(pips, risk_percent=2, account_size=10000):
    """Calculate actual money from pips"""
    # Simplified calculation - would be more complex in production
    pip_value = (account_size * risk_percent / 100) / 20  # Assuming 20 pip SL average
    return pips * pip_value

# ULTIMATE FUSION HUD TEMPLATE
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN // {{ user_stats.callsign }} // Mission Brief</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: {{ colors.primary }};
            --warning: {{ colors.warning }};
            --danger: {{ colors.danger }};
            --success: {{ colors.success }};
            --background: {{ colors.background }};
            --surface: {{ colors.surface }};
            --border: {{ colors.border }};
            --text-primary: {{ colors.text_primary }};
            --text-secondary: {{ colors.text_secondary }};
            --accent: {{ colors.accent }};
            --tactical: {{ colors.tactical }};
            --intel: {{ colors.intel }};
            --bit-command: {{ colors.bit_command }};
            --money-positive: {{ colors.money_positive }};
            --money-negative: {{ colors.money_negative }};
        }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: var(--background);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        
        /* Grid overlay */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(0deg, transparent 24%, rgba(255,255,255,.01) 25%, rgba(255,255,255,.01) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.01) 75%, rgba(255,255,255,.01) 76%, transparent 77%, transparent),
                linear-gradient(90deg, transparent 24%, rgba(255,255,255,.01) 25%, rgba(255,255,255,.01) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.01) 75%, rgba(255,255,255,.01) 76%, transparent 77%, transparent);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: 1;
        }
        
        /* Top Command Bar with Personal Stats */
        .command-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(180deg, var(--surface) 0%, transparent 100%);
            border-bottom: 1px solid var(--border);
            z-index: 100;
            backdrop-filter: blur(10px);
        }
        
        .command-main {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 20px;
            border-bottom: 1px solid var(--border);
        }
        
        .command-title {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .bit-indicator {
            width: 40px;
            height: 40px;
            border: 2px solid var(--bit-command);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
            background: rgba(255, 149, 0, 0.1);
            position: relative;
        }
        
        .bit-indicator::after {
            content: '';
            position: absolute;
            top: -5px;
            right: -5px;
            width: 10px;
            height: 10px;
            background: var(--bit-command);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        
        /* Personal Stats Bar */
        .personal-stats {
            background: var(--intel);
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: 'Share Tech Mono', monospace;
            font-size: 13px;
        }
        
        .stats-left {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .stats-right {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 11px;
        }
        
        .stat-value {
            color: var(--primary);
            font-weight: 700;
        }
        
        .stat-value.positive {
            color: var(--money-positive);
        }
        
        .stat-value.negative {
            color: var(--money-negative);
        }
        
        .profile-link {
            color: var(--primary);
            text-decoration: none;
            padding: 4px 10px;
            border: 1px solid var(--primary);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s;
        }
        
        .profile-link:hover {
            background: var(--primary);
            color: var(--background);
        }
        
        /* Last 5 trades indicator */
        .trade-history {
            display: flex;
            gap: 3px;
            align-items: center;
        }
        
        .trade-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .trade-dot.win {
            background: var(--success);
        }
        
        .trade-dot.loss {
            background: var(--danger);
        }
        
        /* Main Container */
        .main-container {
            padding: 140px 20px 20px;
            max-width: 900px;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }
        
        /* Tribe Intel Section */
        .tribe-intel {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 20px;
            margin-bottom: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .tribe-stat {
            text-align: center;
            padding: 10px;
            background: var(--intel);
            border: 1px solid var(--border);
        }
        
        .tribe-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
            font-family: 'Share Tech Mono', monospace;
        }
        
        .tribe-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }
        
        /* Mission Intel Card */
        .mission-intel {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 30px;
            margin-bottom: 20px;
            position: relative;
        }
        
        .intel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }
        
        /* Strike Parameters with Money */
        .strike-params {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 25px 0;
        }
        
        .param-block {
            background: var(--intel);
            border: 1px solid var(--border);
            padding: 15px;
            text-align: center;
            position: relative;
        }
        
        .param-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .param-value {
            font-size: 24px;
            font-weight: 700;
            font-family: 'Share Tech Mono', monospace;
            color: var(--text-primary);
        }
        
        .param-sub {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 4px;
        }
        
        .param-money {
            font-size: 14px;
            font-weight: 700;
            margin-top: 8px;
            font-family: 'Share Tech Mono', monospace;
        }
        
        .money-positive {
            color: var(--money-positive);
        }
        
        .money-negative {
            color: var(--money-negative);
        }
        
        /* Live Executions Feed */
        .live-feed {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .feed-header {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .live-indicator {
            width: 8px;
            height: 8px;
            background: var(--danger);
            border-radius: 50%;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .execution-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: var(--intel);
            margin-bottom: 5px;
            border-left: 3px solid transparent;
            font-size: 14px;
        }
        
        .execution-item.win {
            border-left-color: var(--success);
        }
        
        .execution-item.loss {
            border-left-color: var(--danger);
        }
        
        /* Commander Assessment with Reflection */
        .commander-assessment {
            background: linear-gradient(135deg, rgba(255,149,0,0.1) 0%, transparent 100%);
            border: 1px solid var(--bit-command);
            padding: 20px;
            margin: 20px 0;
        }
        
        .reflection-prompt {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,149,0,0.3);
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .reflection-prompt em {
            color: var(--bit-command);
            font-style: normal;
        }
        
        /* Action Section with Links */
        .action-section {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
            flex-wrap: wrap;
        }
        
        .action-btn {
            padding: 15px 40px;
            font-size: 16px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .btn-primary {
            background: var(--primary);
            color: var(--background);
            border: 2px solid var(--primary);
        }
        
        .btn-secondary {
            background: transparent;
            color: var(--text-primary);
            border: 2px solid var(--border);
        }
        
        .action-links {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 15px;
            font-size: 13px;
        }
        
        .action-link {
            color: var(--text-secondary);
            text-decoration: none;
            transition: color 0.3s;
        }
        
        .action-link:hover {
            color: var(--primary);
        }
        
        /* Countdown */
        .countdown-section {
            text-align: center;
            margin: 30px 0;
        }
        
        .countdown-timer {
            font-size: 48px;
            font-weight: 700;
            font-family: 'Share Tech Mono', monospace;
            color: var(--warning);
            letter-spacing: 4px;
        }
        
        /* Quick Stats Overlay */
        .quick-stats {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 15px;
            font-size: 12px;
            font-family: 'Share Tech Mono', monospace;
            z-index: 100;
        }
        
        .quick-stats-title {
            color: var(--text-secondary);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .quick-stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        /* Journal Link */
        .journal-link {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 12px 20px;
            cursor: pointer;
            transition: all 0.3s;
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: var(--text-primary);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .personal-stats {
                flex-direction: column;
                gap: 10px;
            }
            
            .stats-left, .stats-right {
                flex-wrap: wrap;
            }
            
            .tribe-intel {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .strike-params {
                grid-template-columns: 1fr;
            }
            
            .quick-stats {
                display: none;
            }
        }
    </style>
</head>
<body>
    <!-- Command Bar -->
    <div class="command-bar">
        <div class="command-main">
            <div class="command-title">
                <div class="bit-indicator">B</div>
                <h1>COMMANDER BIT // TACTICAL OPERATIONS</h1>
            </div>
            <div>
                <span style="color: var(--text-secondary); font-size: 14px;">{{ market_intel.traders_online }} soldiers online</span>
            </div>
        </div>
        <!-- Personal Stats Bar -->
        <div class="personal-stats">
            <div class="stats-left">
                <div class="stat-item">
                    <span class="stat-label">CALLSIGN:</span>
                    <span class="stat-value">{{ user_stats.callsign }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">LVL:</span>
                    <span class="stat-value">{{ user_stats.level }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">XP:</span>
                    <span class="stat-value">{{ user_stats.xp }}/{{ user_stats.xp_to_next }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">ACCURACY:</span>
                    <span class="stat-value">{{ user_stats.accuracy }}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">PROFIT:</span>
                    <span class="stat-value positive">${{ "%.2f"|format(user_stats.total_profit) }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">LAST 5:</span>
                    <div class="trade-history">
                        {% for trade in user_stats.last_5_trades %}
                        <div class="trade-dot {% if trade == 'W' %}win{% else %}loss{% endif %}"></div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            <div class="stats-right">
                <div class="stat-item">
                    <span class="stat-label">STREAK:</span>
                    <span class="stat-value">{{ user_stats.current_streak }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">RANK:</span>
                    <span class="stat-value">#{{ user_stats.global_rank }}</span>
                </div>
                <a href="/me" class="profile-link">VIEW PROFILE</a>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">
        <!-- Tribe Intel -->
        <div class="tribe-intel">
            <div class="tribe-stat">
                <div class="tribe-value">{{ market_intel.this_signal_engagement }}%</div>
                <div class="tribe-label">Engaged</div>
            </div>
            <div class="tribe-stat">
                <div class="tribe-value">{{ market_intel.global_win_rate }}%</div>
                <div class="tribe-label">Win Rate Today</div>
            </div>
            <div class="tribe-stat">
                <div class="tribe-value">{{ market_intel.avg_execution_time }}</div>
                <div class="tribe-label">Avg Decision</div>
            </div>
            <div class="tribe-stat">
                <div class="tribe-value">{{ market_intel.signals_active }}</div>
                <div class="tribe-label">Active Signals</div>
            </div>
        </div>
        
        <!-- Mission Intel -->
        <div class="mission-intel">
            <div class="intel-header">
                <div class="target-info">
                    <span class="target-symbol">{{ signal.symbol }}</span>
                    <span class="operation-type">{{ signal.direction }}</span>
                </div>
                <div class="confidence-meter">
                    <span class="confidence-label">Confidence</span>
                    <span class="confidence-value {% if signal.tcs_score >= 85 %}confidence-high{% elif signal.tcs_score >= 77 %}confidence-med{% else %}confidence-low{% endif %}">
                        {{ signal.tcs_score }}%
                    </span>
                </div>
            </div>
            
            <!-- Strike Parameters with Money -->
            <div class="strike-params">
                <div class="param-block">
                    <div class="param-label">Entry Point</div>
                    <div class="param-value">{{ "%.5f"|format(signal.entry) }}</div>
                    <div class="param-sub">Strike Zone</div>
                </div>
                <div class="param-block">
                    <div class="param-label">Stop Loss</div>
                    <div class="param-value">{{ "%.5f"|format(signal.sl) }}</div>
                    <div class="param-sub">{{ signal.sl_pips }} pips</div>
                    <div class="param-money money-negative">(${{ "%.2f"|format(sl_money) }})</div>
                </div>
                <div class="param-block">
                    <div class="param-label">Take Profit</div>
                    <div class="param-value">{{ "%.5f"|format(signal.tp) }}</div>
                    <div class="param-sub">{{ signal.tp_pips }} pips</div>
                    <div class="param-money money-positive">(+${{ "%.2f"|format(tp_money) }})</div>
                </div>
            </div>
            
            <!-- Risk Assessment -->
            <div class="risk-assessment">
                <div class="risk-ratio">
                    <span class="risk-label">Risk/Reward Ratio</span>
                    <span class="risk-value">1:{{ signal.rr_ratio }}</span>
                </div>
                <div class="risk-ratio">
                    <span class="risk-label">Signal Type</span>
                    <span class="risk-value">{{ signal.signal_type }}</span>
                </div>
            </div>
        </div>
        
        <!-- Live Executions Feed -->
        <div class="live-feed">
            <div class="feed-header">
                <div class="live-indicator"></div>
                Recent Squad Executions
            </div>
            {% for exec in market_intel.recent_executions %}
            <div class="execution-item {% if '+' in exec.result %}win{% else %}loss{% endif %}">
                <span>{{ exec.callsign }}</span>
                <span>{{ exec.result }}</span>
                <span style="color: var(--text-secondary);">{{ exec.time }}</span>
            </div>
            {% endfor %}
        </div>
        
        <!-- Commander's Assessment -->
        <div class="commander-assessment">
            <div class="commander-header">
                <div class="commander-icon">B</div>
                <span class="commander-title">Commander Bit's Assessment</span>
            </div>
            <div class="commander-message">
                {% if signal.tcs_score >= 85 %}
                "High-value target confirmed. {{ user_stats.callsign }}, your recent {{ user_stats.accuracy }}% accuracy shows you're ready for this."
                {% elif signal.tcs_score >= 77 %}
                "Solid intel. Your win rate of {{ user_stats.win_rate }}% suggests you can handle this standard engagement."
                {% else %}
                "Intel suggests caution. With {{ user_stats.current_streak }} streak on the line, consider your risk carefully."
                {% endif %}
            </div>
            <div class="reflection-prompt">
                <em>Before you decide:</em> What does this setup remind you of? Check your journal for similar patterns.
            </div>
        </div>
        
        <!-- Countdown -->
        <div class="countdown-section">
            <div id="countdown" class="countdown-timer">09:45</div>
            <div class="countdown-label">Mission Window Closing</div>
        </div>
        
        <!-- Actions -->
        <div class="action-section">
            <button class="action-btn btn-primary" onclick="executeMission()">
                EXECUTE MISSION
            </button>
            <button class="action-btn btn-secondary" onclick="abortMission()">
                ABORT
            </button>
        </div>
        
        <div class="action-links">
            <a href="/training" class="action-link">📚 Training</a>
            <a href="/history" class="action-link">📊 History</a>
            <a href="/journal" class="action-link">📓 Journal</a>
            <a href="/squad" class="action-link">👥 Squad</a>
        </div>
    </div>
    
    <!-- Quick Stats Overlay -->
    <div class="quick-stats">
        <div class="quick-stats-title">Your Stats</div>
        <div class="quick-stat-row">
            <span>Today:</span>
            <span class="positive">+{{ user_stats.total_pips }} pips</span>
        </div>
        <div class="quick-stat-row">
            <span>Best:</span>
            <span>{{ user_stats.best_streak }} streak</span>
        </div>
        <div class="quick-stat-row">
            <span>Rank:</span>
            <span>#{{ user_stats.squad_rank }}/127</span>
        </div>
    </div>
    
    <!-- Journal Link -->
    <a href="/journal" class="journal-link">
        <span class="journal-icon">📓</span>
        <span class="journal-text">Combat Journal</span>
    </a>

    <script>
        // Mission data
        const missionData = {{ mission_data|tojson|safe }};
        
        // Countdown timer
        let timeLeft = missionData.signal.expiry || 600;
        const countdownEl = document.getElementById('countdown');
        
        function updateCountdown() {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            countdownEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            
            if (timeLeft <= 60) {
                countdownEl.style.color = 'var(--danger)';
            }
            
            if (timeLeft <= 0) {
                countdownEl.textContent = 'EXPIRED';
                document.querySelectorAll('.action-btn').forEach(btn => {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                });
                return;
            }
            
            timeLeft--;
        }
        
        setInterval(updateCountdown, 1000);
        updateCountdown();
        
        // Action handlers
        function executeMission() {
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.sendData(JSON.stringify({
                    action: 'execute',
                    mission_id: missionData.mission_id,
                    signal: missionData.signal
                }));
            } else {
                alert('Mission execution confirmed. (Demo mode - connect via Telegram for live trading)');
            }
        }
        
        function abortMission() {
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.close();
            } else {
                window.location.href = '/';
            }
        }
        
        // Live updates simulation
        setTimeout(() => {
            // Would connect to WebSocket for real updates
            console.log('Live updates active');
        }, 2000);
    </script>
</body>
</html>
"""

@app.route('/hud')
def mission_hud():
    """Render the mission HUD with full stats"""
    try:
        # Get data from query params
        data_str = request.args.get('data', '{}')
        decoded_data = urllib.parse.unquote(data_str)
        mission_data = json.loads(decoded_data)
        
        # Get user stats
        user_id = request.args.get('user_id', 'default')
        user_stats = get_user_stats(user_id)
        
        # Get market intelligence
        market_intel = get_market_intel()
        
        # Get tier colors
        colors = get_tier_styles(user_stats['tier'])
        
        # Get signal from mission data
        signal = mission_data.get('signal', {})
        
        # Calculate money values
        sl_money = abs(calculate_money(signal.get('sl_pips', 0)))
        tp_money = calculate_money(signal.get('tp_pips', 0))
        
        return render_template_string(
            HUD_TEMPLATE,
            mission_data=mission_data,
            signal=signal,
            user_stats=user_stats,
            market_intel=market_intel,
            colors=colors,
            sl_money=sl_money,
            tp_money=tp_money
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/me')
def profile_page():
    """User profile page"""
    return """
    <html>
    <head>
        <title>Soldier Profile</title>
        <style>
            body {
                background: #000;
                color: #fff;
                font-family: 'Rajdhani', sans-serif;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 { color: #00D9FF; }
            .stat-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin-top: 30px;
            }
            .stat-card {
                background: #0F0F0F;
                border: 1px solid #1A1A1A;
                padding: 20px;
            }
            .back {
                color: #00D9FF;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <a href="/" class="back">← Back</a>
        <h1>SOLDIER-7 Profile</h1>
        <div class="stat-grid">
            <div class="stat-card">
                <h3>Combat Record</h3>
                <p>Total Missions: 65</p>
                <p>Success Rate: 72%</p>
                <p>Total Profit: $2,847.50</p>
            </div>
            <div class="stat-card">
                <h3>Achievements</h3>
                <p>🏅 First Blood</p>
                <p>🏅 5 Win Streak</p>
                <p>🏅 Sniper Elite</p>
            </div>
            <div class="stat-card">
                <h3>Recent Performance</h3>
                <p>Last 7 Days: +347 pips</p>
                <p>Best Day: +124 pips</p>
                <p>Worst Day: -45 pips</p>
            </div>
            <div class="stat-card">
                <h3>Squad Standing</h3>
                <p>Squad Rank: #14 of 127</p>
                <p>Global Rank: #1,247</p>
                <p>Trust Level: 85%</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/test')
def test():
    return "Ultimate Fusion Interface - ONLINE"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8894))
    app.run(host='0.0.0.0', port=port, debug=False)