#!/usr/bin/env python3
"""Enhanced Flask server with personalized mission briefs"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import json
import urllib.parse
import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# Color-blind friendly palette with high contrast
ACCESSIBLE_TIER_STYLES = {
    'nibbler': {
        'primary': '#00D9FF',      # Bright cyan (was green)
        'secondary': '#FFFFFF',     # White for text
        'accent': '#FFD700',        # Gold for important info
        'background': '#0A0A0A',    # Very dark background
        'surface': '#1A1A1A',       # Slightly lighter for cards
        'danger': '#FF6B6B',        # Red-orange (distinguishable)
        'success': '#4ECDC4',       # Teal (not pure green)
        'border': '#00D9FF',
        'tcs_high': '#FFD700',      # Gold for high TCS
        'tcs_medium': '#00D9FF',    # Cyan for medium TCS
        'tcs_low': '#FF6B6B'        # Red-orange for low TCS
    },
    'fang': {
        'primary': '#FF8C00',       # Dark orange
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FF8C00',
        'tcs_high': '#FFD700',
        'tcs_medium': '#FF8C00',
        'tcs_low': '#FF6B6B'
    },
    'commander': {
        'primary': '#FFD700',       # Gold
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FFD700',
        'tcs_high': '#FFFFFF',
        'tcs_medium': '#FFD700',
        'tcs_low': '#FF8C00'
    },
    'apex': {
        'primary': '#FF00FF',       # Magenta
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FF00FF',
        'tcs_high': '#FFFFFF',
        'tcs_medium': '#FF00FF',
        'tcs_low': '#FF6B6B'
    }
}

def get_tier_styles(tier):
    """Get accessible color scheme for tier"""
    return ACCESSIBLE_TIER_STYLES.get(tier.lower(), ACCESSIBLE_TIER_STYLES['nibbler'])

def mask_price(price):
    """Mask last 2 digits of price with XX for security"""
    price_str = f"{price:.5f}"
    return price_str[:-2] + "XX"

def calculate_dollar_value(pips, lot_size=0.01):
    """Calculate dollar value for pips based on standard micro lot"""
    # Standard calculation: 1 pip on 0.01 lot = $0.10
    return round(pips * lot_size * 10, 2)

def get_user_stats(user_id):
    """Get mock user stats - would connect to real database"""
    # Mock data for demo
    return {
        'gamertag': 'Soldier_X',
        'tier': 'nibbler',
        'level': 5,
        'xp': 1250,
        'trades_today': 3,
        'trades_remaining': 3,  # 6 - 3
        'win_rate': 75,
        'pnl_today': 2.4,
        'streak': 3,
        'best_streak': 7,
        'total_trades': 127,
        'avg_rr': 2.1,
        'squad_engagement': 67  # Percentage of squad taking this signal
    }

# Enhanced HUD template with personal stats
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN {{ tier|upper }} Mission Brief</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background-color: {{ colors.background }};
            color: {{ colors.secondary }};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 16px;
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        /* High contrast mode */
        @media (prefers-contrast: high) {
            body {
                background-color: #000000;
                color: #FFFFFF;
            }
            .surface {
                border: 2px solid #FFFFFF !important;
            }
        }
        
        /* Top Navigation Bar */
        .top-bar {
            background: rgba(0,0,0,0.9);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid {{ colors.border }};
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .back-button {
            color: {{ colors.primary }};
            text-decoration: none;
            padding: 8px 20px;
            border: 2px solid {{ colors.primary }};
            border-radius: 4px;
            font-weight: bold;
            transition: all 0.3s;
            background: rgba(0,0,0,0.5);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .back-button:hover {
            background: {{ colors.primary }};
            color: {{ colors.background }};
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(255,255,255,0.2);
        }
        
        .tier-badge {
            background: {{ colors.primary }};
            color: {{ colors.background }};
            padding: 8px 20px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        /* Personal Stats Bar */
        .stats-bar {
            background: rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 15px 20px;
            margin: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-label {
            font-size: 11px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-value {
            font-size: 20px;
            font-weight: bold;
            color: {{ colors.secondary }};
            margin-top: 2px;
        }
        
        .stat-value.positive {
            color: {{ colors.success }};
        }
        
        .stat-value.negative {
            color: {{ colors.danger }};
        }
        
        .stat-value.warning {
            color: {{ colors.accent }};
        }
        
        /* Gamertag and Level */
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .gamertag {
            font-size: 18px;
            font-weight: bold;
            color: {{ colors.primary }};
        }
        
        .level-badge {
            background: {{ colors.accent }};
            color: {{ colors.background }};
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }
        
        /* Main Content */
        .content {
            max-width: 600px;
            margin: 0 auto;
            padding: 0 20px 20px;
        }
        
        /* Mission Card */
        .mission-card {
            background: {{ colors.surface }};
            border: 2px solid {{ colors.border }};
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        
        .mission-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .signal-type {
            font-size: 24px;
            font-weight: bold;
            color: {{ colors.accent }};
            letter-spacing: 2px;
            text-shadow: 0 0 10px {{ colors.accent }};
            margin-bottom: 10px;
        }
        
        .pair-direction {
            font-size: 32px;
            font-weight: bold;
            color: {{ colors.secondary }};
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        /* TCS Score - Make it POP */
        .tcs-container {
            background: rgba(0,0,0,0.8);
            border: 3px solid {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 0 20px {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
        }
        
        .tcs-label {
            font-size: 14px;
            color: rgba(255,255,255,0.7);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .tcs-score {
            font-size: 48px;
            font-weight: bold;
            color: {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
            text-shadow: 0 0 20px currentColor;
            margin: 10px 0;
        }
        
        .confidence-label {
            font-size: 18px;
            font-weight: bold;
            color: {% if tcs_score >= 85 %}{{ colors.tcs_high }}{% elif tcs_score >= 75 %}{{ colors.tcs_medium }}{% else %}{{ colors.tcs_low }}{% endif %};
        }
        
        /* Decision Helper */
        .decision-helper {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        
        .helper-text {
            font-size: 16px;
            color: {{ colors.secondary }};
            line-height: 1.4;
        }
        
        .helper-text .highlight {
            color: {{ colors.accent }};
            font-weight: bold;
        }
        
        /* Trade Parameters */
        .parameters {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        
        .param-box {
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 4px;
            padding: 15px;
            text-align: center;
        }
        
        .param-label {
            font-size: 12px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .param-value {
            font-size: 20px;
            font-weight: bold;
            color: {{ colors.secondary }};
        }
        
        .param-value.positive {
            color: {{ colors.success }};
        }
        
        .param-value.negative {
            color: {{ colors.danger }};
        }
        
        /* Action Buttons */
        .actions {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .fire-button {
            flex: 1;
            background: linear-gradient(135deg, {{ colors.danger }}, {{ colors.primary }});
            color: white;
            border: none;
            padding: 18px 30px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            min-width: 200px;
        }
        
        .fire-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }
        
        .fire-button:active {
            transform: translateY(0);
        }
        
        .skip-button {
            flex: 1;
            background: transparent;
            color: rgba(255,255,255,0.6);
            border: 2px solid rgba(255,255,255,0.3);
            padding: 18px 30px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .skip-button:hover {
            border-color: rgba(255,255,255,0.6);
            color: rgba(255,255,255,0.9);
        }
        
        /* Bottom Links */
        .bottom-links {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .bottom-links a {
            color: {{ colors.primary }};
            text-decoration: none;
            padding: 10px 20px;
            border: 1px solid {{ colors.primary }};
            border-radius: 4px;
            transition: all 0.3s;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .bottom-links a:hover {
            background: {{ colors.primary }};
            color: {{ colors.background }};
        }
        
        /* Timer */
        .timer {
            background: rgba(255,0,0,0.1);
            border: 1px solid {{ colors.danger }};
            border-radius: 4px;
            padding: 10px 20px;
            text-align: center;
            margin-bottom: 20px;
            font-size: 18px;
            font-weight: bold;
            color: {{ colors.danger }};
        }
        
        /* Focus styles for accessibility */
        button:focus,
        a:focus {
            outline: 3px solid {{ colors.accent }};
            outline-offset: 2px;
        }
        
        /* Animation for urgency */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .urgent {
            animation: pulse 2s infinite;
        }
        
        /* Mobile responsive */
        @media (max-width: 600px) {
            .stats-bar {
                flex-direction: column;
                gap: 15px;
            }
            
            .stat-item {
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .stat-label {
                margin-right: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="top-bar">
        <a href="#" class="back-button" onclick="exitBriefing(); return false;">
            <span>←</span>
            <span>Back</span>
        </a>
        <div class="tier-badge">{{ user_stats.tier|upper }}</div>
    </div>
    
    <!-- Personal Stats Bar -->
    <div class="stats-bar">
        <div class="user-info">
            <div class="gamertag">{{ user_stats.gamertag }}</div>
            <div class="level-badge">LVL {{ user_stats.level }}</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">Today</div>
            <div class="stat-value">{{ user_stats.trades_today }}/6</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">Win Rate</div>
            <div class="stat-value {% if user_stats.win_rate >= 70 %}positive{% else %}warning{% endif %}">{{ user_stats.win_rate }}%</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">P&L Today</div>
            <div class="stat-value {% if user_stats.pnl_today >= 0 %}positive{% else %}negative{% endif %}">{{ "{:+.1f}".format(user_stats.pnl_today) }}%</div>
        </div>
        
        <div class="stat-item">
            <div class="stat-label">Streak</div>
            <div class="stat-value {% if user_stats.streak >= 3 %}positive{% elif user_stats.streak < 0 %}negative{% endif %}">
                {% if user_stats.streak >= 0 %}W{{ user_stats.streak }}{% else %}L{{ -user_stats.streak }}{% endif %}
            </div>
        </div>
    </div>
    
    <div class="content">
        <div class="mission-card">
            <div class="mission-header">
                <div class="signal-type">{{ signal_type|upper }} SIGNAL</div>
                <div class="pair-direction">
                    {{ symbol }} {{ direction }}
                </div>
            </div>
            
            <!-- TCS Score Section -->
            <div class="tcs-container">
                <div class="tcs-label">Tactical Confidence Score</div>
                <div class="tcs-score">{{ tcs_score }}%</div>
                <div class="confidence-label">
                    {% if tcs_score >= 90 %}EXTREME CONFIDENCE{% elif tcs_score >= 85 %}HIGH CONFIDENCE{% elif tcs_score >= 75 %}MODERATE CONFIDENCE{% else %}LOW CONFIDENCE{% endif %}
                </div>
            </div>
            
            <!-- Decision Helper -->
            <div class="decision-helper">
                <div class="helper-text">
                    {% if user_stats.trades_remaining <= 0 %}
                        <span class="highlight">⚠️ Daily limit reached!</span> Save this for tomorrow.
                    {% elif tcs_score >= 85 and user_stats.win_rate >= 70 %}
                        <span class="highlight">🔥 Strong signal + Good form = GO!</span>
                    {% elif tcs_score >= 85 and user_stats.win_rate < 70 %}
                        <span class="highlight">🎯 High confidence signal.</span> Trust the process.
                    {% elif tcs_score < 75 and user_stats.trades_remaining <= 2 %}
                        <span class="highlight">💭 Low score.</span> Save shots for better setups?
                    {% elif user_stats.streak <= -3 %}
                        <span class="highlight">🛡️ Rough patch.</span> Maybe take a break?
                    {% else %}
                        You have <span class="highlight">{{ user_stats.trades_remaining }} trades</span> left today.
                    {% endif %}
                </div>
            </div>
            
            <!-- Expiry Timer -->
            {% if expiry_seconds > 0 %}
            <div class="timer urgent" id="timer">
                Signal expires in: <span id="countdown">{{ expiry_seconds }}s</span>
            </div>
            {% endif %}
            
            <!-- Trade Parameters -->
            <div class="parameters">
                <div class="param-box">
                    <div class="param-label">Entry Price</div>
                    <div class="param-value">{{ entry|round(5) }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Stop Loss</div>
                    <div class="param-value negative">{{ sl|round(5) }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Take Profit</div>
                    <div class="param-value positive">{{ tp|round(5) }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Risk/Reward</div>
                    <div class="param-value">1:{{ rr_ratio }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Risk (pips)</div>
                    <div class="param-value">{{ sl_pips }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Reward (pips)</div>
                    <div class="param-value positive">{{ tp_pips }}</div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="actions">
                <button class="fire-button" onclick="fireSignal()" {% if user_stats.trades_remaining <= 0 %}disabled{% endif %}>
                    🎯 FIRE SIGNAL
                </button>
                <button class="skip-button" onclick="skipSignal()">
                    Pass
                </button>
            </div>
            
            <!-- Bottom Links -->
            <div class="bottom-links">
                <a href="/education/{{ user_stats.tier }}" target="_blank">
                    <span>📚</span>
                    <span>Training</span>
                </a>
                <a href="/stats/{{ user_id }}" target="_blank">
                    <span>📊</span>
                    <span>Full Stats</span>
                </a>
                <a href="/history" target="_blank">
                    <span>📜</span>
                    <span>History</span>
                </a>
            </div>
        </div>
    </div>
    
    <script>
        // Telegram WebApp API
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Exit briefing
        function exitBriefing() {
            if (tg) {
                tg.close();
            } else {
                window.close();
                // Fallback
                setTimeout(() => {
                    window.location.href = 'https://t.me/BittenCommander';
                }, 100);
            }
        }
        
        // Fire signal
        function fireSignal() {
            // Check if user has trades remaining
            if ({{ user_stats.trades_remaining }} <= 0) {
                alert('Daily limit reached! Come back tomorrow, soldier.');
                return;
            }
            
            // Send data back to bot
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'fire',
                    signal_id: '{{ signal_id }}',
                    symbol: '{{ symbol }}',
                    direction: '{{ direction }}'
                }));
            }
            
            // Visual feedback
            document.querySelector('.fire-button').textContent = '✅ FIRED!';
            document.querySelector('.fire-button').disabled = true;
            
            // Close after delay
            setTimeout(exitBriefing, 1500);
        }
        
        // Skip signal
        function skipSignal() {
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'skip',
                    signal_id: '{{ signal_id }}'
                }));
            }
            exitBriefing();
        }
        
        // Countdown timer
        {% if expiry_seconds > 0 %}
        let timeLeft = {{ expiry_seconds }};
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timer);
                countdownEl.textContent = 'EXPIRED';
                document.querySelector('.fire-button').disabled = true;
                document.querySelector('.fire-button').textContent = '❌ EXPIRED';
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
            }
        }, 1000);
        {% endif %}
    </script>
</body>
</html>
"""

# Test page remains the same...
TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>BITTEN WebApp Test</title>
    <style>
        body {
            background: #0a0a0a;
            color: #00ff00;
            font-family: monospace;
            text-align: center;
            padding: 50px;
        }
        .status {
            font-size: 24px;
            margin: 20px;
        }
    </style>
</head>
<body>
    <h1>🎯 BITTEN WebApp Test Page</h1>
    <div class="status">✅ WebApp is running!</div>
    <div>Server Time: {{ time }}</div>
</body>
</html>
"""

@app.route('/')
def index():
    """Root endpoint"""
    return "BITTEN WebApp Server Running", 200

@app.route('/test')
def test():
    """Test endpoint"""
    from datetime import datetime
    return render_template_string(TEST_PAGE, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/hud')
def hud():
    """Mission briefing HUD with personalized data"""
    try:
        # Get data from URL parameter
        encoded_data = request.args.get('data', '')
        if not encoded_data:
            return "No mission data provided", 400
        
        # Decode the data
        decoded_data = urllib.parse.unquote(encoded_data)
        data = json.loads(decoded_data)
        
        # Extract signal data
        signal = data.get('signal', {})
        
        # Get user stats (mock for now, would get from database)
        user_id = data.get('user_id', 'demo')
        user_stats = get_user_stats(user_id)
        
        # Prepare template variables
        context = {
            'user_id': user_id,
            'user_stats': user_stats,
            'signal_id': signal.get('id', 'unknown'),
            'signal_type': signal.get('signal_type', 'STANDARD'),
            'symbol': signal.get('symbol', 'UNKNOWN'),
            'direction': signal.get('direction', 'BUY'),
            'tcs_score': signal.get('tcs_score', 0),
            'entry': signal.get('entry', 0),
            'sl': signal.get('sl', 0),
            'tp': signal.get('tp', 0),
            'sl_pips': signal.get('sl_pips', 0),
            'tp_pips': signal.get('tp_pips', 0),
            'rr_ratio': signal.get('rr_ratio', 0),
            'expiry_seconds': signal.get('expiry', 600),
            'colors': get_tier_styles(user_stats['tier'])
        }
        
        return render_template_string(HUD_TEMPLATE, **context)
        
    except Exception as e:
        return f"Error processing mission data: {str(e)}", 400

@app.route('/education/<tier>')
def education(tier):
    """Education/training page for specific tier"""
    colors = get_tier_styles(tier)
    
    # Load education content based on tier
    education_content = {
        'nibbler': {
            'title': 'Nibbler Training Academy',
            'modules': [
                {'name': 'Risk Management 101', 'progress': 75},
                {'name': 'Reading Price Action', 'progress': 50},
                {'name': 'Psychology of Trading', 'progress': 30}
            ],
            'next_lesson': 'Understanding Stop Losses'
        },
        'fang': {
            'title': 'Fang Advanced Training',
            'modules': [
                {'name': 'Advanced Patterns', 'progress': 60},
                {'name': 'AI Signal Analysis', 'progress': 40},
                {'name': 'Momentum Trading', 'progress': 80}
            ],
            'next_lesson': 'Multi-Timeframe Analysis'
        },
        'commander': {
            'title': 'Commander Elite Training',
            'modules': [
                {'name': 'Market Structure', 'progress': 90},
                {'name': 'Liquidity Concepts', 'progress': 70},
                {'name': 'Squad Coordination', 'progress': 50}
            ],
            'next_lesson': 'Institutional Order Flow'
        },
        'apex': {
            'title': 'APEX Mastery',
            'modules': [
                {'name': 'Quantum Analysis', 'progress': 100},
                {'name': 'Market Manipulation', 'progress': 95},
                {'name': 'Reality Bending', 'progress': 88}
            ],
            'next_lesson': 'Transcending the Matrix'
        }
    }
    
    content = education_content.get(tier.lower(), education_content['nibbler'])
    
    # Education page template
    EDUCATION_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ content.title }}</title>
        <style>
            body {
                background: {{ colors.background }};
                color: {{ colors.secondary }};
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                color: {{ colors.primary }};
            }
            .module {
                background: {{ colors.surface }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .progress-bar {
                background: rgba(255,255,255,0.1);
                height: 10px;
                border-radius: 5px;
                overflow: hidden;
                margin-top: 10px;
            }
            .progress-fill {
                background: {{ colors.primary }};
                height: 100%;
                transition: width 0.3s;
            }
            .next-lesson {
                background: {{ colors.primary }};
                color: {{ colors.background }};
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin-top: 30px;
                font-weight: bold;
            }
            .back-link {
                color: {{ colors.primary }};
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="#" class="back-link" onclick="window.close(); return false;">← Back</a>
            <h1 class="header">{{ content.title }}</h1>
            
            <h2>Your Progress</h2>
            {% for module in content.modules %}
            <div class="module">
                <h3>{{ module.name }}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ module.progress }}%"></div>
                </div>
                <small>{{ module.progress }}% Complete</small>
            </div>
            {% endfor %}
            
            <div class="next-lesson">
                <h3>Next Lesson</h3>
                <p>{{ content.next_lesson }}</p>
                <button onclick="alert('Lesson starting soon!')">Start Now →</button>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(EDUCATION_TEMPLATE, content=content, colors=colors)

# Add more endpoints as needed...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)