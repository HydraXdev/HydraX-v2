#!/usr/bin/env python3
"""TACTICAL WARFARE VERSION - Cyberpunk Military HUD"""

from flask import Flask, render_template_string, request, jsonify
import json
import urllib.parse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# MILITARY TACTICAL COLOR SCHEMES
WARFARE_STYLES = {
    'nibbler': {
        'primary': '#00FF41',      # Matrix green
        'secondary': '#FFFFFF',     
        'accent': '#FF0000',        # Blood red for danger
        'warning': '#FFA500',       # Amber alert
        'background': '#000000',    # Pure black ops
        'surface': '#0A0A0A',       
        'grid': '#00FF4120',        # Tactical grid overlay
        'hologram': '#00FFFF',      # Holographic blue
        'danger': '#FF0000',        
        'success': '#00FF41',       
        'border': '#00FF41',
        'tcs_critical': '#FF0000',  # Red alert
        'tcs_optimal': '#00FF41',   # Green go
        'tcs_caution': '#FFA500'    # Amber warning
    }
}

def get_tier_styles(tier):
    return WARFARE_STYLES.get(tier.lower(), WARFARE_STYLES['nibbler'])

def get_user_stats(user_id):
    """Military personnel file"""
    return {
        'callsign': 'VIPER-7',
        'rank': 'SPECIALIST',
        'tier': 'nibbler',
        'level': 5,
        'xp': 1250,
        'ammo_remaining': 3,  # Shots left
        'kill_ratio': 75,     # Win rate
        'combat_earnings': 2.4,  # P&L
        'killstreak': 3,      # Streak
        'squad': 'DELTA-9',
        'clearance': 'LEVEL-1',
        'missions_completed': 127,
        'commendations': 7
    }

# TACTICAL WARFARE HUD TEMPLATE
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TACTICAL OPERATIONS CENTER - MISSION BRIEF</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background-color: {{ colors.background }};
            color: {{ colors.secondary }};
            font-family: 'Orbitron', monospace;
            font-size: 14px;
            line-height: 1.4;
            overflow: hidden;
            position: relative;
        }
        
        /* Tactical Grid Overlay */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                repeating-linear-gradient(0deg, {{ colors.grid }} 0px, transparent 1px, transparent 40px, {{ colors.grid }} 40px),
                repeating-linear-gradient(90deg, {{ colors.grid }} 0px, transparent 1px, transparent 40px, {{ colors.grid }} 40px);
            pointer-events: none;
            z-index: 1;
        }
        
        /* Scan Lines Effect */
        @keyframes scan {
            0% { transform: translateY(0); }
            100% { transform: translateY(100vh); }
        }
        
        .scanlines {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 200%;
            background: linear-gradient(
                transparent 0%,
                rgba(0, 255, 65, 0.03) 50%,
                transparent 100%
            );
            animation: scan 8s linear infinite;
            pointer-events: none;
            z-index: 2;
        }
        
        /* Main Container */
        .tactical-container {
            position: relative;
            z-index: 10;
            min-height: 100vh;
            padding: 20px;
        }
        
        /* TOP COMMAND BAR */
        .command-bar {
            background: linear-gradient(90deg, rgba(0,0,0,0.9) 0%, rgba(0,255,65,0.1) 50%, rgba(0,0,0,0.9) 100%);
            border: 1px solid {{ colors.primary }};
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            overflow: hidden;
        }
        
        .command-bar::before {
            content: 'ENCRYPTED CHANNEL // SECURE';
            position: absolute;
            top: 2px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 8px;
            color: {{ colors.primary }}50;
            letter-spacing: 3px;
        }
        
        .abort-mission {
            background: rgba(255,0,0,0.2);
            border: 1px solid {{ colors.danger }};
            color: {{ colors.danger }};
            padding: 8px 20px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .abort-mission:hover {
            background: {{ colors.danger }};
            color: black;
            box-shadow: 0 0 20px {{ colors.danger }};
        }
        
        .clearance-badge {
            background: {{ colors.primary }};
            color: black;
            padding: 8px 20px;
            font-weight: 900;
            letter-spacing: 3px;
            text-transform: uppercase;
            position: relative;
        }
        
        /* OPERATIVE STATUS PANEL */
        .operative-status {
            background: rgba(0,0,0,0.8);
            border: 1px solid {{ colors.primary }};
            margin: 20px 0;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }
        
        .operative-status::before {
            content: 'OPERATIVE STATUS // REAL-TIME';
            position: absolute;
            top: 5px;
            right: 10px;
            font-size: 10px;
            color: {{ colors.primary }}50;
            letter-spacing: 2px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }
        
        .status-item {
            text-align: center;
            position: relative;
        }
        
        .status-label {
            font-size: 10px;
            color: {{ colors.primary }}80;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }
        
        .status-value {
            font-size: 24px;
            font-weight: 900;
            color: {{ colors.primary }};
            text-shadow: 0 0 10px {{ colors.primary }};
        }
        
        .status-value.critical {
            color: {{ colors.danger }};
            text-shadow: 0 0 10px {{ colors.danger }};
            animation: pulse 1s infinite;
        }
        
        .status-value.optimal {
            color: {{ colors.success }};
            text-shadow: 0 0 10px {{ colors.success }};
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* AMMO COUNTER SPECIAL */
        .ammo-counter {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
        }
        
        .ammo-icon {
            width: 20px;
            height: 30px;
            background: {{ colors.primary }};
            clip-path: polygon(30% 0%, 70% 0%, 100% 100%, 0% 100%);
            margin: 0 2px;
        }
        
        .ammo-icon.spent {
            background: {{ colors.danger }}30;
            border: 1px solid {{ colors.danger }}50;
        }
        
        /* MISSION INTEL PANEL */
        .mission-intel {
            background: rgba(0,0,0,0.9);
            border: 2px solid {{ colors.primary }};
            padding: 30px;
            margin: 20px 0;
            position: relative;
            overflow: hidden;
        }
        
        .mission-intel::before {
            content: 'CLASSIFIED // EYES ONLY';
            position: absolute;
            top: 10px;
            right: 20px;
            color: {{ colors.danger }}50;
            font-size: 12px;
            letter-spacing: 3px;
        }
        
        .target-designation {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .mission-type {
            font-size: 18px;
            color: {{ colors.warning }};
            letter-spacing: 3px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        
        .target-vector {
            font-size: 36px;
            font-weight: 900;
            color: {{ colors.secondary }};
            text-transform: uppercase;
            letter-spacing: 4px;
            text-shadow: 0 0 20px {{ colors.primary }};
        }
        
        /* THREAT ASSESSMENT */
        .threat-assessment {
            background: linear-gradient(135deg, rgba(255,0,0,0.1) 0%, rgba(0,0,0,0.5) 100%);
            border: 1px solid {{ colors.danger }};
            border-radius: 0;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .threat-assessment::after {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, {{ colors.danger }}, transparent, {{ colors.danger }});
            animation: rotate 3s linear infinite;
            z-index: -1;
        }
        
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .threat-label {
            font-size: 12px;
            color: {{ colors.danger }}80;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 10px;
        }
        
        .threat-level {
            font-size: 60px;
            font-weight: 900;
            {% if tcs_score >= 85 %}
            color: {{ colors.success }};
            text-shadow: 0 0 30px {{ colors.success }};
            {% elif tcs_score >= 75 %}
            color: {{ colors.warning }};
            text-shadow: 0 0 30px {{ colors.warning }};
            {% else %}
            color: {{ colors.danger }};
            text-shadow: 0 0 30px {{ colors.danger }};
            animation: danger-flash 0.5s infinite;
            {% endif %}
        }
        
        @keyframes danger-flash {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .threat-status {
            font-size: 16px;
            font-weight: bold;
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        /* TACTICAL ADVICE */
        .tactical-advice {
            background: rgba(0,255,65,0.1);
            border: 1px solid {{ colors.primary }};
            padding: 15px;
            margin: 20px 0;
            position: relative;
            overflow: hidden;
        }
        
        .tactical-advice::before {
            content: 'TACTICAL AI // COMBAT ANALYSIS';
            position: absolute;
            top: 5px;
            left: 10px;
            font-size: 10px;
            color: {{ colors.primary }}50;
            letter-spacing: 2px;
        }
        
        .advice-text {
            font-size: 14px;
            line-height: 1.6;
            text-align: center;
            margin-top: 15px;
        }
        
        .advice-text .highlight {
            color: {{ colors.hologram }};
            font-weight: bold;
            text-shadow: 0 0 5px {{ colors.hologram }};
        }
        
        /* ENGAGEMENT PARAMETERS */
        .parameters {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 30px 0;
        }
        
        .param-box {
            background: rgba(0,0,0,0.8);
            border: 1px solid {{ colors.primary }}50;
            padding: 15px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .param-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, {{ colors.primary }}, transparent);
            animation: slide 2s linear infinite;
        }
        
        @keyframes slide {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .param-label {
            font-size: 10px;
            color: {{ colors.primary }}80;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }
        
        .param-value {
            font-size: 20px;
            font-weight: bold;
            color: {{ colors.secondary }};
        }
        
        .param-value.negative {
            color: {{ colors.danger }};
        }
        
        .param-value.positive {
            color: {{ colors.success }};
        }
        
        .risk-dollars {
            font-size: 14px;
            color: {{ colors.warning }};
            margin-top: 5px;
        }
        
        /* COUNTDOWN TIMER */
        .mission-timer {
            background: rgba(255,0,0,0.2);
            border: 2px solid {{ colors.danger }};
            padding: 15px;
            text-align: center;
            margin: 20px 0;
            font-size: 20px;
            font-weight: bold;
            position: relative;
            overflow: hidden;
        }
        
        .mission-timer::before {
            content: 'WINDOW CLOSING';
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            color: {{ colors.danger }};
            letter-spacing: 3px;
        }
        
        /* ENGAGEMENT CONTROLS */
        .engagement-controls {
            display: flex;
            gap: 20px;
            margin-top: 40px;
        }
        
        .engage-button {
            flex: 1;
            background: linear-gradient(135deg, {{ colors.danger }} 0%, {{ colors.primary }} 100%);
            color: white;
            border: none;
            padding: 20px;
            font-size: 18px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 3px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
        }
        
        .engage-button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .engage-button:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .engage-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,255,65,0.5);
        }
        
        .abort-button {
            flex: 0.5;
            background: transparent;
            color: {{ colors.danger }}80;
            border: 1px solid {{ colors.danger }}50;
            padding: 20px;
            font-size: 16px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .abort-button:hover {
            border-color: {{ colors.danger }};
            color: {{ colors.danger }};
            background: rgba(255,0,0,0.1);
        }
        
        /* INTEL LINKS */
        .intel-links {
            display: flex;
            justify-content: space-around;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid {{ colors.primary }}30;
        }
        
        .intel-link {
            color: {{ colors.primary }};
            text-decoration: none;
            padding: 10px 20px;
            border: 1px solid {{ colors.primary }}50;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 12px;
            transition: all 0.3s;
            position: relative;
        }
        
        .intel-link:hover {
            background: {{ colors.primary }};
            color: black;
            box-shadow: 0 0 20px {{ colors.primary }};
        }
        
        /* MOBILE RESPONSIVE */
        @media (max-width: 768px) {
            .parameters {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .status-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .target-vector {
                font-size: 28px;
            }
            
            .threat-level {
                font-size: 48px;
            }
        }
    </style>
</head>
<body>
    <div class="scanlines"></div>
    
    <div class="tactical-container">
        <!-- COMMAND BAR -->
        <div class="command-bar">
            <a href="#" class="abort-mission" onclick="abortMission(); return false;">
                ◄ ABORT
            </a>
            <div class="clearance-badge">{{ user_stats.clearance }}</div>
        </div>
        
        <!-- OPERATIVE STATUS -->
        <div class="operative-status">
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">Callsign</div>
                    <div class="status-value">{{ user_stats.callsign }}</div>
                </div>
                
                <div class="status-item">
                    <div class="status-label">Rank</div>
                    <div class="status-value">{{ user_stats.rank }}</div>
                </div>
                
                <div class="status-item">
                    <div class="status-label">Ammo Remaining</div>
                    <div class="status-value">
                        <div class="ammo-counter">
                            {% for i in range(6) %}
                                <div class="ammo-icon {% if i >= user_stats.ammo_remaining %}spent{% endif %}"></div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                
                <div class="status-item">
                    <div class="status-label">Kill Ratio</div>
                    <div class="status-value {% if user_stats.kill_ratio >= 70 %}optimal{% else %}critical{% endif %}">
                        {{ user_stats.kill_ratio }}%
                    </div>
                </div>
                
                <div class="status-item">
                    <div class="status-label">Combat Earnings</div>
                    <div class="status-value {% if user_stats.combat_earnings >= 0 %}optimal{% else %}critical{% endif %}">
                        {{ "{:+.1f}".format(user_stats.combat_earnings) }}%
                    </div>
                </div>
                
                <div class="status-item">
                    <div class="status-label">Killstreak</div>
                    <div class="status-value {% if user_stats.killstreak >= 3 %}optimal{% elif user_stats.killstreak < 0 %}critical{% endif %}">
                        {% if user_stats.killstreak >= 0 %}{{ user_stats.killstreak }}X{% else %}BROKEN{% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- MISSION INTEL -->
        <div class="mission-intel">
            <div class="target-designation">
                <div class="mission-type">{{ signal_type }} PROTOCOL ACTIVATED</div>
                <div class="target-vector">
                    TARGET: {{ symbol }} // VECTOR: {{ direction }}
                </div>
            </div>
            
            <!-- THREAT ASSESSMENT -->
            <div class="threat-assessment">
                <div class="threat-label">Combat Confidence Matrix</div>
                <div class="threat-level">{{ tcs_score }}%</div>
                <div class="threat-status">
                    {% if tcs_score >= 90 %}KILL ZONE CONFIRMED{% elif tcs_score >= 85 %}HIGH PROBABILITY TARGET{% elif tcs_score >= 75 %}VIABLE ENGAGEMENT{% else %}HOSTILE TERRITORY{% endif %}
                </div>
            </div>
            
            <!-- TACTICAL ADVICE -->
            <div class="tactical-advice">
                <div class="advice-text">
                    {% if user_stats.ammo_remaining <= 0 %}
                        <span class="highlight">⚠️ AMMUNITION DEPLETED!</span> RTB for resupply at 0000 hours.
                    {% elif tcs_score >= 85 and user_stats.kill_ratio >= 70 %}
                        <span class="highlight">🎯 WEAPONS HOT!</span> Target acquired. Green light to engage.
                    {% elif tcs_score >= 85 and user_stats.kill_ratio < 70 %}
                        <span class="highlight">⚡ PRIORITY TARGET.</span> Trust your training, soldier.
                    {% elif tcs_score < 75 and user_stats.ammo_remaining <= 2 %}
                        <span class="highlight">⚠️ LOW CONFIDENCE VECTOR.</span> Conserve ammunition for better targets.
                    {% elif user_stats.killstreak <= -3 %}
                        <span class="highlight">🛡️ TACTICAL RETREAT ADVISED.</span> Regroup and reassess.
                    {% else %}
                        <span class="highlight">{{ user_stats.ammo_remaining }} ROUNDS</span> remaining in magazine.
                    {% endif %}
                </div>
            </div>
            
            <!-- MISSION TIMER -->
            {% if expiry_seconds > 0 %}
            <div class="mission-timer">
                <span id="countdown">{{ expiry_seconds }}s</span>
            </div>
            {% endif %}
            
            <!-- ENGAGEMENT PARAMETERS -->
            <div class="parameters">
                <div class="param-box">
                    <div class="param-label">Entry Vector</div>
                    <div class="param-value">{{ entry|round(5) }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Extraction Point</div>
                    <div class="param-value negative">{{ sl|round(5) }}</div>
                    <div class="risk-dollars">(${{ (sl_pips * 10)|round(0)|int }})</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Target Objective</div>
                    <div class="param-value positive">{{ tp|round(5) }}</div>
                    <div class="risk-dollars">(${{ (tp_pips * 10)|round(0)|int }})</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Risk Protocol</div>
                    <div class="param-value">1:{{ rr_ratio }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Threat Exposure</div>
                    <div class="param-value">{{ sl_pips }} units</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Target Value</div>
                    <div class="param-value positive">{{ tp_pips }} units</div>
                </div>
            </div>
            
            <!-- ENGAGEMENT CONTROLS -->
            <div class="engagement-controls">
                <button class="engage-button" onclick="engageTarget()" {% if user_stats.ammo_remaining <= 0 %}disabled{% endif %}>
                    ENGAGE TARGET
                </button>
                <button class="abort-button" onclick="standDown()">
                    STAND DOWN
                </button>
            </div>
            
            <!-- INTEL LINKS -->
            <div class="intel-links">
                <a href="/education/{{ user_stats.tier }}" target="_blank" class="intel-link">
                    TRAINING SIMS
                </a>
                <a href="/stats/{{ user_id }}" target="_blank" class="intel-link">
                    COMBAT RECORD
                </a>
                <a href="/history" target="_blank" class="intel-link">
                    MISSION LOGS
                </a>
            </div>
        </div>
    </div>
    
    <script>
        // Sound effects
        const sounds = {
            hover: new Audio('data:audio/wav;base64,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'),
            click: new Audio('data:audio/wav;base64,UklGRmQCAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YUACAABhYP//Ub3//wAA//8bgP//AAD//wAAYmD//wAA//8AAAAA')
        };
        
        // Play sound on hover
        document.querySelectorAll('button, a').forEach(el => {
            el.addEventListener('mouseenter', () => {
                sounds.hover.volume = 0.1;
                sounds.hover.play().catch(() => {});
            });
        });
        
        // Telegram WebApp API
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Abort mission
        function abortMission() {
            if (tg) {
                tg.close();
            } else {
                window.close();
                setTimeout(() => {
                    window.location.href = 'https://t.me/BittenCommander';
                }, 100);
            }
        }
        
        // Engage target
        function engageTarget() {
            if ({{ user_stats.ammo_remaining }} <= 0) {
                alert('AMMUNITION DEPLETED. RTB IMMEDIATELY.');
                return;
            }
            
            sounds.click.play().catch(() => {});
            
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'fire',
                    signal_id: '{{ signal_id }}',
                    symbol: '{{ symbol }}',
                    direction: '{{ direction }}'
                }));
            }
            
            document.querySelector('.engage-button').innerHTML = '🎯 TARGET ENGAGED';
            document.querySelector('.engage-button').disabled = true;
            
            setTimeout(abortMission, 1500);
        }
        
        // Stand down
        function standDown() {
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'skip',
                    signal_id: '{{ signal_id }}'
                }));
            }
            abortMission();
        }
        
        // Countdown timer
        {% if expiry_seconds > 0 %}
        let timeLeft = {{ expiry_seconds }};
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timer);
                countdownEl.textContent = 'WINDOW CLOSED';
                document.querySelector('.engage-button').disabled = true;
                document.querySelector('.engage-button').innerHTML = 'MISSION EXPIRED';
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}s`;
            }
        }, 1000);
        {% endif %}
        
        // Type text effect
        function typeText(element, text, speed = 50) {
            element.textContent = '';
            let i = 0;
            function type() {
                if (i < text.length) {
                    element.textContent += text.charAt(i);
                    i++;
                    setTimeout(type, speed);
                }
            }
            type();
        }
        
        // Initialize typing effects
        window.addEventListener('load', () => {
            const targetVector = document.querySelector('.target-vector');
            if (targetVector) {
                typeText(targetVector, targetVector.textContent, 30);
            }
        });
    </script>
</body>
</html>
"""

TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>TACTICAL OPS CENTER</title>
    <style>
        body {
            background: #000;
            color: #00ff41;
            font-family: 'Orbitron', monospace;
            text-align: center;
            padding: 50px;
        }
        .status {
            font-size: 24px;
            margin: 20px;
            text-shadow: 0 0 10px #00ff41;
        }
    </style>
</head>
<body>
    <h1>🎯 TACTICAL OPERATIONS CENTER</h1>
    <div class="status">✅ SYSTEMS ONLINE</div>
    <div>Server Time: {{ time }}</div>
</body>
</html>
"""

@app.route('/')
def index():
    return "TACTICAL OPS CENTER - ONLINE", 200

@app.route('/test')
def test():
    from datetime import datetime
    return render_template_string(TEST_PAGE, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/hud')
def hud():
    try:
        encoded_data = request.args.get('data', '')
        if not encoded_data:
            return "NO MISSION DATA PROVIDED", 400
        
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
        return f"ERROR PROCESSING MISSION DATA: {str(e)}", 400

@app.route('/education/<tier>')
def education(tier):
    return "TRAINING SIMULATIONS UNDER CONSTRUCTION", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889, debug=False)