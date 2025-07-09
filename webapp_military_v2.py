#!/usr/bin/env python3
"""HOLOGRAPHIC COMMAND CENTER - Minority Report Style"""

from flask import Flask, render_template_string, request
import json
import urllib.parse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# HOLOGRAPHIC WARFARE COLORS
HOLOGRAM_STYLES = {
    'nibbler': {
        'primary': '#00D4FF',      # Holographic blue
        'secondary': '#FFFFFF',     
        'accent': '#FF00FF',        # Neon magenta
        'warning': '#FFFF00',       # Electric yellow
        'background': '#000814',    # Deep space black
        'surface': '#001D3D',       # Navy blue
        'hologram': '#00F5FF',      # Cyan glow
        'plasma': '#FF006E',        # Hot pink
        'danger': '#FF006E',        
        'success': '#00F5FF',       
        'neural': '#8338EC',        # Purple neural
        'data': '#3A86FF'           # Data stream blue
    }
}

def get_tier_styles(tier):
    return HOLOGRAM_STYLES.get(tier.lower(), HOLOGRAM_STYLES['nibbler'])

def get_user_stats(user_id):
    return {
        'designation': 'GHOST-7',
        'clearance': 'OMEGA',
        'tier': 'nibbler',
        'neural_sync': 87,
        'rounds_remaining': 3,
        'accuracy_index': 75,
        'profit_delta': 2.4,
        'engagement_streak': 3,
        'threat_level': 'MODERATE',
        'augmentations': ['REFLEX_BOOST', 'TACTICAL_AI'],
        'squad_link': 'PHANTOM_CELL'
    }

# HOLOGRAPHIC COMMAND CENTER TEMPLATE
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GHOST PROTOCOL // ENGAGEMENT MATRIX</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: {{ colors.background }};
            color: {{ colors.secondary }};
            font-family: 'Rajdhani', sans-serif;
            font-size: 16px;
            overflow-x: hidden;
            position: relative;
            min-height: 100vh;
        }
        
        /* HOLOGRAPHIC BACKGROUND */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, {{ colors.primary }}20 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, {{ colors.plasma }}20 0%, transparent 50%),
                radial-gradient(circle at 40% 20%, {{ colors.neural }}20 0%, transparent 50%);
            animation: holoPulse 10s ease-in-out infinite;
            pointer-events: none;
        }
        
        @keyframes holoPulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.7; }
        }
        
        /* DATA RAIN EFFECT */
        .data-rain {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            pointer-events: none;
            opacity: 0.1;
        }
        
        .data-stream {
            position: absolute;
            font-size: 20px;
            color: {{ colors.data }};
            animation: fall linear infinite;
        }
        
        @keyframes fall {
            to { transform: translateY(100vh); }
        }
        
        /* MAIN INTERFACE */
        .ghost-interface {
            position: relative;
            z-index: 100;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* NEURAL LINK HEADER */
        .neural-header {
            background: linear-gradient(135deg, {{ colors.surface }}CC 0%, transparent 100%);
            border: 1px solid {{ colors.primary }}50;
            backdrop-filter: blur(10px);
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            overflow: hidden;
        }
        
        .neural-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, {{ colors.primary }}50, transparent);
            animation: neuralScan 3s linear infinite;
        }
        
        @keyframes neuralScan {
            to { left: 100%; }
        }
        
        .disconnect-btn {
            background: transparent;
            border: 1px solid {{ colors.danger }};
            color: {{ colors.danger }};
            padding: 10px 30px;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 2px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
            text-transform: uppercase;
        }
        
        .disconnect-btn:hover {
            color: black;
            background: {{ colors.danger }};
            box-shadow: 0 0 30px {{ colors.danger }};
        }
        
        .clearance-level {
            font-size: 18px;
            font-weight: 700;
            color: {{ colors.primary }};
            letter-spacing: 3px;
            text-shadow: 0 0 20px {{ colors.primary }};
        }
        
        /* OPERATIVE VITALS */
        .vitals-panel {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .vital-card {
            background: {{ colors.surface }}80;
            border: 1px solid {{ colors.primary }}30;
            backdrop-filter: blur(10px);
            padding: 20px;
            position: relative;
            overflow: hidden;
        }
        
        .vital-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, {{ colors.hologram }}, transparent);
            animation: scan 2s linear infinite;
        }
        
        @keyframes scan {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .vital-label {
            font-size: 12px;
            color: {{ colors.primary }}80;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        .vital-value {
            font-size: 32px;
            font-weight: 700;
            color: {{ colors.hologram }};
            text-shadow: 0 0 20px {{ colors.hologram }};
        }
        
        .vital-value.critical {
            color: {{ colors.danger }};
            animation: criticalPulse 0.5s infinite;
        }
        
        @keyframes criticalPulse {
            0%, 100% { opacity: 1; text-shadow: 0 0 20px {{ colors.danger }}; }
            50% { opacity: 0.5; text-shadow: 0 0 40px {{ colors.danger }}; }
        }
        
        /* ROUNDS DISPLAY */
        .rounds-display {
            display: flex;
            gap: 10px;
            align-items: center;
            justify-content: center;
        }
        
        .round-indicator {
            width: 40px;
            height: 8px;
            background: {{ colors.hologram }};
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 10px {{ colors.hologram }};
        }
        
        .round-indicator.empty {
            background: transparent;
            border: 1px solid {{ colors.danger }}50;
            box-shadow: none;
        }
        
        .round-indicator::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, white, transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        /* TARGET ANALYSIS */
        .target-analysis {
            background: {{ colors.surface }}60;
            border: 2px solid {{ colors.primary }}50;
            backdrop-filter: blur(20px);
            padding: 40px;
            margin: 30px 0;
            position: relative;
            overflow: hidden;
        }
        
        .target-analysis::before,
        .target-analysis::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border: 1px solid {{ colors.hologram }}20;
            pointer-events: none;
        }
        
        .target-analysis::before {
            top: -5px;
            left: -5px;
            animation: glitch1 3s infinite;
        }
        
        .target-analysis::after {
            bottom: -5px;
            right: -5px;
            animation: glitch2 3s infinite;
        }
        
        @keyframes glitch1 {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-2px, 2px); }
            40% { transform: translate(2px, -2px); }
        }
        
        @keyframes glitch2 {
            0%, 100% { transform: translate(0); }
            30% { transform: translate(2px, 2px); }
            60% { transform: translate(-2px, -2px); }
        }
        
        .target-header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .protocol-type {
            font-size: 20px;
            color: {{ colors.plasma }};
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 15px;
        }
        
        .target-designation {
            font-size: 48px;
            font-weight: 300;
            color: {{ colors.secondary }};
            letter-spacing: 6px;
            text-shadow: 0 0 30px {{ colors.hologram }};
            animation: dataGlitch 5s infinite;
        }
        
        @keyframes dataGlitch {
            0%, 100% { text-shadow: 0 0 30px {{ colors.hologram }}; }
            92% { text-shadow: 0 0 30px {{ colors.hologram }}; }
            93% { text-shadow: -3px 0 {{ colors.danger }}, 3px 0 {{ colors.primary }}; }
            94% { text-shadow: 0 0 30px {{ colors.hologram }}; }
        }
        
        /* PROBABILITY MATRIX */
        .probability-matrix {
            width: 300px;
            height: 300px;
            margin: 40px auto;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .probability-ring {
            position: absolute;
            border: 2px solid {{ colors.primary }}50;
            border-radius: 50%;
            animation: rotate 10s linear infinite;
        }
        
        .probability-ring:nth-child(1) {
            width: 100%;
            height: 100%;
            animation-duration: 10s;
        }
        
        .probability-ring:nth-child(2) {
            width: 80%;
            height: 80%;
            animation-duration: 7s;
            animation-direction: reverse;
        }
        
        .probability-ring:nth-child(3) {
            width: 60%;
            height: 60%;
            animation-duration: 5s;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .probability-core {
            position: relative;
            z-index: 10;
            text-align: center;
        }
        
        .probability-value {
            font-size: 80px;
            font-weight: 700;
            {% if tcs_score >= 85 %}
            color: {{ colors.success }};
            text-shadow: 0 0 50px {{ colors.success }};
            {% elif tcs_score >= 75 %}
            color: {{ colors.warning }};
            text-shadow: 0 0 50px {{ colors.warning }};
            {% else %}
            color: {{ colors.danger }};
            text-shadow: 0 0 50px {{ colors.danger }};
            {% endif %}
        }
        
        .probability-label {
            font-size: 14px;
            color: {{ colors.primary }}80;
            letter-spacing: 3px;
            text-transform: uppercase;
        }
        
        /* TACTICAL RECOMMENDATION */
        .tactical-recommendation {
            background: linear-gradient(135deg, {{ colors.neural }}20 0%, transparent 100%);
            border: 1px solid {{ colors.neural }}50;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
            font-size: 18px;
            position: relative;
            overflow: hidden;
        }
        
        .tactical-recommendation::before {
            content: 'NEURAL NETWORK ANALYSIS';
            position: absolute;
            top: 5px;
            left: 20px;
            font-size: 10px;
            color: {{ colors.neural }}80;
            letter-spacing: 2px;
        }
        
        .recommendation-text {
            margin-top: 10px;
            line-height: 1.6;
        }
        
        .recommendation-text .alert {
            color: {{ colors.plasma }};
            font-weight: 700;
            text-shadow: 0 0 10px {{ colors.plasma }};
        }
        
        /* ENGAGEMENT PARAMETERS */
        .parameters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .param-cell {
            background: {{ colors.surface }}40;
            border: 1px solid {{ colors.data }}30;
            padding: 20px;
            text-align: center;
            position: relative;
            backdrop-filter: blur(10px);
        }
        
        .param-cell::before {
            content: '';
            position: absolute;
            inset: -1px;
            background: linear-gradient(45deg, {{ colors.data }}, transparent, {{ colors.hologram }});
            opacity: 0;
            transition: opacity 0.3s;
            z-index: -1;
        }
        
        .param-cell:hover::before {
            opacity: 0.3;
        }
        
        .param-name {
            font-size: 12px;
            color: {{ colors.data }}80;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        .param-data {
            font-size: 24px;
            font-weight: 700;
            color: {{ colors.secondary }};
        }
        
        .param-data.negative {
            color: {{ colors.danger }};
        }
        
        .param-data.positive {
            color: {{ colors.success }};
        }
        
        .dollar-risk {
            font-size: 14px;
            color: {{ colors.plasma }};
            margin-top: 5px;
            font-weight: 400;
        }
        
        /* MISSION TIMER */
        .mission-countdown {
            background: {{ colors.danger }}20;
            border: 1px solid {{ colors.danger }};
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: 700;
            margin: 30px 0;
            position: relative;
            overflow: hidden;
        }
        
        .mission-countdown::before {
            content: 'ENGAGEMENT WINDOW';
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            color: {{ colors.danger }}80;
            letter-spacing: 3px;
        }
        
        #countdown {
            color: {{ colors.danger }};
            text-shadow: 0 0 20px {{ colors.danger }};
        }
        
        /* ACTION INTERFACE */
        .action-interface {
            display: flex;
            gap: 20px;
            margin-top: 40px;
        }
        
        .execute-btn {
            flex: 1;
            background: linear-gradient(135deg, {{ colors.hologram }} 0%, {{ colors.neural }} 100%);
            border: none;
            color: white;
            padding: 25px;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 3px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            transition: all 0.3s;
        }
        
        .execute-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255,255,255,0.5);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .execute-btn:hover::before {
            width: 400px;
            height: 400px;
        }
        
        .execute-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px {{ colors.hologram }}50;
        }
        
        .abort-btn {
            flex: 0.4;
            background: transparent;
            border: 1px solid {{ colors.danger }}50;
            color: {{ colors.danger }};
            padding: 25px;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 2px;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.3s;
        }
        
        .abort-btn:hover {
            background: {{ colors.danger }}20;
            border-color: {{ colors.danger }};
            box-shadow: 0 0 20px {{ colors.danger }}50;
        }
        
        /* INTEL ACCESS */
        .intel-access {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 50px;
            padding-top: 30px;
            border-top: 1px solid {{ colors.primary }}20;
        }
        
        .intel-link {
            color: {{ colors.data }};
            text-decoration: none;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            position: relative;
            padding: 10px 20px;
            transition: all 0.3s;
        }
        
        .intel-link::before {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 0;
            height: 2px;
            background: {{ colors.hologram }};
            transition: width 0.3s;
        }
        
        .intel-link:hover::before {
            width: 100%;
        }
        
        .intel-link:hover {
            color: {{ colors.hologram }};
            text-shadow: 0 0 10px {{ colors.hologram }}50;
        }
    </style>
</head>
<body>
    <!-- Data Rain Effect -->
    <div class="data-rain" id="dataRain"></div>
    
    <div class="ghost-interface">
        <!-- Neural Link Header -->
        <div class="neural-header">
            <button class="disconnect-btn" onclick="disconnect()">
                ◄ DISCONNECT
            </button>
            <div class="clearance-level">CLEARANCE: {{ user_stats.clearance }}</div>
        </div>
        
        <!-- Operative Vitals -->
        <div class="vitals-panel">
            <div class="vital-card">
                <div class="vital-label">Designation</div>
                <div class="vital-value">{{ user_stats.designation }}</div>
            </div>
            
            <div class="vital-card">
                <div class="vital-label">Neural Sync</div>
                <div class="vital-value">{{ user_stats.neural_sync }}%</div>
            </div>
            
            <div class="vital-card">
                <div class="vital-label">Rounds Remaining</div>
                <div class="vital-value">
                    <div class="rounds-display">
                        {% for i in range(6) %}
                            <div class="round-indicator {% if i >= user_stats.rounds_remaining %}empty{% endif %}"></div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div class="vital-card">
                <div class="vital-label">Accuracy Index</div>
                <div class="vital-value {% if user_stats.accuracy_index < 70 %}critical{% endif %}">
                    {{ user_stats.accuracy_index }}%
                </div>
            </div>
            
            <div class="vital-card">
                <div class="vital-label">Profit Delta</div>
                <div class="vital-value {% if user_stats.profit_delta < 0 %}critical{% endif %}">
                    {{ "{:+.1f}".format(user_stats.profit_delta) }}%
                </div>
            </div>
            
            <div class="vital-card">
                <div class="vital-label">Engagement Streak</div>
                <div class="vital-value">{{ user_stats.engagement_streak }}X</div>
            </div>
        </div>
        
        <!-- Target Analysis -->
        <div class="target-analysis">
            <div class="target-header">
                <div class="protocol-type">{{ signal_type }} PROTOCOL</div>
                <div class="target-designation">{{ symbol }} :: {{ direction }}</div>
            </div>
            
            <!-- Probability Matrix -->
            <div class="probability-matrix">
                <div class="probability-ring"></div>
                <div class="probability-ring"></div>
                <div class="probability-ring"></div>
                <div class="probability-core">
                    <div class="probability-value">{{ tcs_score }}</div>
                    <div class="probability-label">PROBABILITY MATRIX</div>
                </div>
            </div>
            
            <!-- Tactical Recommendation -->
            <div class="tactical-recommendation">
                <div class="recommendation-text">
                    {% if user_stats.rounds_remaining <= 0 %}
                        <span class="alert">⚠️ AMMUNITION DEPLETED</span><br>
                        Neural link will reset at 00:00 UTC for resupply.
                    {% elif tcs_score >= 85 and user_stats.accuracy_index >= 70 %}
                        <span class="alert">🎯 OPTIMAL ENGAGEMENT VECTOR</span><br>
                        All systems green. Execute with confidence.
                    {% elif tcs_score >= 85 and user_stats.accuracy_index < 70 %}
                        <span class="alert">⚡ HIGH-VALUE TARGET IDENTIFIED</span><br>
                        Override accuracy concerns. Target priority: CRITICAL.
                    {% elif tcs_score < 75 and user_stats.rounds_remaining <= 2 %}
                        <span class="alert">💭 SUBOPTIMAL PARAMETERS</span><br>
                        Recommend conserving rounds for higher probability targets.
                    {% elif user_stats.engagement_streak <= -3 %}
                        <span class="alert">🛡️ NEURAL FATIGUE DETECTED</span><br>
                        Disengage and recalibrate systems.
                    {% else %}
                        <span class="alert">{{ user_stats.rounds_remaining }} ROUNDS</span> authorized for deployment.
                    {% endif %}
                </div>
            </div>
            
            <!-- Mission Timer -->
            {% if expiry_seconds > 0 %}
            <div class="mission-countdown">
                <span id="countdown">{{ expiry_seconds }}s</span>
            </div>
            {% endif %}
            
            <!-- Engagement Parameters -->
            <div class="parameters-grid">
                <div class="param-cell">
                    <div class="param-name">Entry Vector</div>
                    <div class="param-data">{{ entry|round(5) }}</div>
                </div>
                <div class="param-cell">
                    <div class="param-name">Abort Threshold</div>
                    <div class="param-data negative">{{ sl|round(5) }}</div>
                    <div class="dollar-risk">${{ (sl_pips * 10)|round(0)|int }}</div>
                </div>
                <div class="param-cell">
                    <div class="param-name">Target Objective</div>
                    <div class="param-data positive">{{ tp|round(5) }}</div>
                    <div class="dollar-risk">${{ (tp_pips * 10)|round(0)|int }}</div>
                </div>
                <div class="param-cell">
                    <div class="param-name">Risk Matrix</div>
                    <div class="param-data">1:{{ rr_ratio }}</div>
                </div>
                <div class="param-cell">
                    <div class="param-name">Exposure Units</div>
                    <div class="param-data">{{ sl_pips }}</div>
                </div>
                <div class="param-cell">
                    <div class="param-name">Target Value</div>
                    <div class="param-data positive">{{ tp_pips }}</div>
                </div>
            </div>
            
            <!-- Action Interface -->
            <div class="action-interface">
                <button class="execute-btn" onclick="execute()" {% if user_stats.rounds_remaining <= 0 %}disabled{% endif %}>
                    EXECUTE PROTOCOL
                </button>
                <button class="abort-btn" onclick="abort()">
                    ABORT
                </button>
            </div>
        </div>
        
        <!-- Intel Access -->
        <div class="intel-access">
            <a href="/education/{{ user_stats.tier }}" target="_blank" class="intel-link">
                COMBAT SIMULATIONS
            </a>
            <a href="/stats/{{ user_id }}" target="_blank" class="intel-link">
                PERFORMANCE MATRIX
            </a>
            <a href="/history" target="_blank" class="intel-link">
                ENGAGEMENT LOGS
            </a>
        </div>
    </div>
    
    <script>
        // Create data rain effect
        function createDataRain() {
            const rain = document.getElementById('dataRain');
            const chars = '01アイウエオカキクケコサシスセソタチツテト';
            
            for (let i = 0; i < 50; i++) {
                const stream = document.createElement('div');
                stream.className = 'data-stream';
                stream.style.left = Math.random() * 100 + '%';
                stream.style.animationDuration = (Math.random() * 3 + 2) + 's';
                stream.style.animationDelay = Math.random() * 2 + 's';
                stream.textContent = chars[Math.floor(Math.random() * chars.length)];
                rain.appendChild(stream);
            }
        }
        
        createDataRain();
        
        // Sound initialization
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        function playTone(frequency, duration) {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = frequency;
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
        }
        
        // Play UI sounds
        document.querySelectorAll('button, a').forEach(el => {
            el.addEventListener('mouseenter', () => playTone(800, 0.05));
            el.addEventListener('click', () => playTone(1200, 0.1));
        });
        
        // Telegram WebApp API
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Disconnect
        function disconnect() {
            playTone(400, 0.2);
            if (tg) {
                tg.close();
            } else {
                window.close();
                setTimeout(() => {
                    window.location.href = 'https://t.me/BittenCommander';
                }, 100);
            }
        }
        
        // Execute protocol
        function execute() {
            if ({{ user_stats.rounds_remaining }} <= 0) {
                alert('AMMUNITION DEPLETED. AWAIT RESUPPLY.');
                return;
            }
            
            playTone(1600, 0.15);
            
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'fire',
                    signal_id: '{{ signal_id }}',
                    symbol: '{{ symbol }}',
                    direction: '{{ direction }}'
                }));
            }
            
            document.querySelector('.execute-btn').innerHTML = '⚡ PROTOCOL EXECUTED';
            document.querySelector('.execute-btn').disabled = true;
            
            setTimeout(disconnect, 1500);
        }
        
        // Abort
        function abort() {
            playTone(300, 0.2);
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'skip',
                    signal_id: '{{ signal_id }}'
                }));
            }
            disconnect();
        }
        
        // Countdown
        {% if expiry_seconds > 0 %}
        let timeLeft = {{ expiry_seconds }};
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timer);
                countdownEl.textContent = 'WINDOW EXPIRED';
                document.querySelector('.execute-btn').disabled = true;
                document.querySelector('.execute-btn').innerHTML = 'EXPIRED';
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}s`;
                
                if (timeLeft <= 10) {
                    playTone(600, 0.05);
                }
            }
        }, 1000);
        {% endif %}
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return "GHOST PROTOCOL ONLINE", 200

@app.route('/hud')
def hud():
    try:
        encoded_data = request.args.get('data', '')
        if not encoded_data:
            return "NO MISSION DATA", 400
        
        decoded_data = urllib.parse.unquote(encoded_data)
        data = json.loads(decoded_data)
        
        signal = data.get('signal', {})
        user_id = data.get('user_id', 'demo')
        user_stats = get_user_stats(user_id)
        
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
        return f"ERROR: {str(e)}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8890, debug=False)