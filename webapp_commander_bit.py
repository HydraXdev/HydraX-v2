#!/usr/bin/env python3
"""COMMANDER BIT - Battle-Hardened Trading Interface"""

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
COMMANDER_COLORS = {
    'nibbler': {
        # High contrast, colorblind-safe palette
        'primary': '#00D9FF',      # Cyan (replaces green)
        'secondary': '#FFFFFF',     
        'warning': '#FF9500',      # Orange
        'danger': '#FF3B30',       # Red (kept for universal recognition)
        'success': '#00D9FF',      # Cyan for positive
        'background': '#000000',   
        'surface': '#0F0F0F',      
        'border': '#1A1A1A',
        'text_primary': '#FFFFFF',
        'text_secondary': '#B0B0B0',
        'accent': '#FFD700',       # Gold for important elements
        'tactical': '#4A5568',     # Steel gray
        'intel': '#2D3748',        # Dark steel
        'bit_command': '#FF9500',  # Commander Bit's signature orange
    }
}

def get_tier_styles(tier):
    return COMMANDER_COLORS.get(tier.lower(), COMMANDER_COLORS['nibbler'])

def get_user_stats(user_id):
    """Get soldier's combat record"""
    return {
        'callsign': 'SOLDIER-7',
        'rank': 'Private',
        'tier': 'nibbler',
        'combat_rating': 87,
        'rounds_remaining': 3,
        'accuracy': 75,
        'confirmed_kills': 2.4,  # Profit in risk units
        'missions_completed': 47,
        'current_streak': 3,
        'command_trust': 85,  # Bit's trust level
    }

def get_commander_status(user_stats):
    """Commander Bit's assessment"""
    if user_stats['current_streak'] >= 3:
        return 'APPROVED', '✓'
    elif user_stats['current_streak'] <= -3:
        return 'CONCERNED', '!'
    elif user_stats['accuracy'] >= 80:
        return 'WATCHING', '○'
    else:
        return 'EVALUATING', '◊'

# CLEAN MILITARY HUD TEMPLATE
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN // COMMANDER BIT TACTICAL OPERATIONS</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            /* Colorblind-safe palette */
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
        }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: var(--background);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        
        /* Grid overlay for military feel */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(0deg, transparent 24%, rgba(255,255,255,.02) 25%, rgba(255,255,255,.02) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.02) 75%, rgba(255,255,255,.02) 76%, transparent 77%, transparent),
                linear-gradient(90deg, transparent 24%, rgba(255,255,255,.02) 25%, rgba(255,255,255,.02) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.02) 75%, rgba(255,255,255,.02) 76%, transparent 77%, transparent);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: 1;
        }
        
        /* Top Command Bar */
        .command-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: linear-gradient(180deg, var(--surface) 0%, transparent 100%);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 100;
            backdrop-filter: blur(10px);
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
        
        .command-title h1 {
            font-size: 20px;
            font-weight: 600;
            letter-spacing: 2px;
            color: var(--text-primary);
        }
        
        .soldier-stats {
            display: flex;
            gap: 20px;
            align-items: center;
            font-family: 'Share Tech Mono', monospace;
            font-size: 14px;
        }
        
        .stat-item {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-value {
            color: var(--primary);
            font-size: 16px;
            font-weight: 700;
        }
        
        /* Main Container */
        .main-container {
            padding: 80px 20px 20px;
            max-width: 800px;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }
        
        /* Mission Intel Card */
        .mission-intel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0;
            padding: 30px;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }
        
        .mission-intel::before {
            content: 'CLASSIFIED';
            position: absolute;
            top: 10px;
            right: 10px;
            color: var(--danger);
            font-size: 10px;
            letter-spacing: 2px;
            opacity: 0.3;
        }
        
        .intel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }
        
        .target-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .target-symbol {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: 1px;
        }
        
        .operation-type {
            padding: 5px 15px;
            background: var(--primary);
            color: var(--background);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        .confidence-meter {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .confidence-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .confidence-value {
            font-size: 32px;
            font-weight: 700;
            font-family: 'Share Tech Mono', monospace;
        }
        
        .confidence-high { color: var(--success); }
        .confidence-med { color: var(--warning); }
        .confidence-low { color: var(--danger); }
        
        /* Strike Parameters */
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
        
        /* Risk Assessment */
        .risk-assessment {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background: var(--intel);
            border: 1px solid var(--border);
            margin: 20px 0;
        }
        
        .risk-ratio {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .risk-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .risk-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--accent);
            font-family: 'Share Tech Mono', monospace;
        }
        
        /* Commander's Assessment */
        .commander-assessment {
            background: linear-gradient(135deg, rgba(255,149,0,0.1) 0%, transparent 100%);
            border: 1px solid var(--bit-command);
            padding: 20px;
            margin: 20px 0;
            position: relative;
        }
        
        .commander-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .commander-icon {
            width: 30px;
            height: 30px;
            background: var(--bit-command);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: var(--background);
        }
        
        .commander-title {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--bit-command);
            font-weight: 600;
        }
        
        .commander-message {
            font-size: 16px;
            line-height: 1.5;
            color: var(--text-primary);
            font-style: italic;
        }
        
        /* Countdown Timer */
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
        
        .countdown-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 5px;
        }
        
        /* Action Buttons */
        .action-section {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        
        .action-btn {
            padding: 15px 40px;
            font-size: 16px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            border: none;
            cursor: pointer;
            position: relative;
            overflow: hidden;
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
        
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,217,255,0.3);
        }
        
        .btn-primary:hover {
            background: transparent;
            color: var(--primary);
        }
        
        .btn-secondary:hover {
            border-color: var(--primary);
            color: var(--primary);
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
        
        .journal-link:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
        }
        
        .journal-icon {
            font-size: 18px;
        }
        
        .journal-text {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Loading State */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--background);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .loading-content {
            text-align: center;
        }
        
        .loading-spinner {
            width: 60px;
            height: 60px;
            border: 3px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-text {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-secondary);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .command-bar {
                padding: 0 15px;
            }
            
            .soldier-stats {
                display: none;
            }
            
            .strike-params {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .action-section {
                flex-direction: column;
            }
            
            .action-btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <!-- Loading Overlay -->
    <div id="loadingOverlay" class="loading-overlay">
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <div class="loading-text">ESTABLISHING SECURE CONNECTION</div>
        </div>
    </div>

    <!-- Command Bar -->
    <div class="command-bar">
        <div class="command-title">
            <div class="bit-indicator">{{ commander_status[1] }}</div>
            <h1>COMMANDER BIT</h1>
        </div>
        <div class="soldier-stats">
            <div class="stat-item">
                <span class="stat-label">Callsign</span>
                <span class="stat-value">{{ user_stats.callsign }}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Rounds</span>
                <span class="stat-value">{{ user_stats.rounds_remaining }}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Accuracy</span>
                <span class="stat-value">{{ user_stats.accuracy }}%</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Trust</span>
                <span class="stat-value">{{ user_stats.command_trust }}%</span>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">
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
            
            <!-- Strike Parameters -->
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
                </div>
                <div class="param-block">
                    <div class="param-label">Take Profit</div>
                    <div class="param-value">{{ "%.5f"|format(signal.tp) }}</div>
                    <div class="param-sub">{{ signal.tp_pips }} pips</div>
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
            
            <!-- Commander's Assessment -->
            <div class="commander-assessment">
                <div class="commander-header">
                    <div class="commander-icon">B</div>
                    <span class="commander-title">Commander Bit's Assessment</span>
                </div>
                <div class="commander-message">
                    {% if signal.tcs_score >= 85 %}
                    "High-value target confirmed. This is what we've trained for, soldier. Execute with precision."
                    {% elif signal.tcs_score >= 77 %}
                    "Solid intel. Standard engagement protocols apply. Stay sharp."
                    {% else %}
                    "Intel suggests caution. Only engage if you're prepared for the risk."
                    {% endif %}
                </div>
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
        
        // Hide loading after content loads
        window.addEventListener('load', () => {
            setTimeout(() => {
                document.getElementById('loadingOverlay').style.display = 'none';
            }, 500);
        });
        
        // Action handlers
        function executeMission() {
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.sendData(JSON.stringify({
                    action: 'execute',
                    mission_id: missionData.mission_id,
                    signal: missionData.signal
                }));
            } else {
                // Demo mode
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
        
        // Add subtle military ambiance
        let scanlineOpacity = 0.02;
        setInterval(() => {
            scanlineOpacity = 0.02 + Math.random() * 0.02;
            document.body.style.setProperty('--scanline-opacity', scanlineOpacity);
        }, 3000);
    </script>
</body>
</html>
"""

@app.route('/hud')
def mission_hud():
    """Render the mission HUD"""
    try:
        # Get data from query params
        data_str = request.args.get('data', '{}')
        decoded_data = urllib.parse.unquote(data_str)
        mission_data = json.loads(decoded_data)
        
        # Get user stats
        user_id = request.args.get('user_id', 'default')
        user_stats = get_user_stats(user_id)
        
        # Get tier colors
        colors = get_tier_styles(user_stats['tier'])
        
        # Get signal from mission data
        signal = mission_data.get('signal', {})
        
        # Get Commander Bit's status
        commander_status = get_commander_status(user_stats)
        
        return render_template_string(
            HUD_TEMPLATE,
            mission_data=mission_data,
            signal=signal,
            user_stats=user_stats,
            colors=colors,
            commander_status=commander_status
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/journal')
def combat_journal():
    """Norman's Combat Journal"""
    return """
    <html>
    <head>
        <title>Combat Journal</title>
        <style>
            body {
                background: #000;
                color: #fff;
                font-family: 'Courier New', monospace;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                color: #FF9500;
                margin-bottom: 30px;
            }
            .entry {
                background: #0F0F0F;
                border: 1px solid #1A1A1A;
                padding: 20px;
                margin-bottom: 20px;
            }
            .date {
                color: #666;
                font-size: 12px;
            }
            .content {
                margin-top: 10px;
                line-height: 1.6;
            }
            .back {
                color: #00D9FF;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <a href="/" class="back">← Back to Operations</a>
        <h1>Combat Journal</h1>
        <div class="entry">
            <div class="date">2025.07.08 - 18:00</div>
            <div class="content">
                Commander Bit watched as I took that EURUSD shot. 92% confidence. 
                The pattern was clear - same setup I've seen a hundred times in training.
                Bit's assessment was right: "This is what we've trained for."
                
                No emotions. Just execution. That's how we survive this battlefield.
            </div>
        </div>
        <div class="entry">
            <div class="date">2025.07.08 - 17:45</div>
            <div class="content">
                Lost one today. -20 pips. Bit didn't say anything, just watched.
                Sometimes the market wins. But we learn. We adapt. We come back stronger.
                
                Dad used to say: "A soldier who never loses never learns to win."
                Starting to understand what he meant.
            </div>
        </div>
        <div class="entry">
            <div class="date">2025.07.08 - 17:00</div>
            <div class="content">
                Third day with Commander Bit's system. The interface isn't trying to be 
                my friend - it's training me to be a better soldier in this war.
                
                Clean. Simple. Effective. Just like Bit.
                
                Rounds remaining: 3. Accuracy: 75%. Not perfect, but improving.
                That's all that matters.
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/test')
def test():
    return "Commander Bit Tactical Operations - ONLINE"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8893))
    app.run(host='0.0.0.0', port=port, debug=False)