#!/usr/bin/env python3
"""BITTEN ULTIMATE - AAA Narrative Trading Experience"""

from flask import Flask, render_template_string, request, jsonify
import json
import urllib.parse
import random
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# BITTEN NARRATIVE COLORS - Based on the lore
BITTEN_COLORS = {
    'nibbler': {
        'primary': '#00FF00',       # Market green (hope)
        'secondary': '#FFFFFF',     
        'accent': '#FF0000',        # Market red (danger)
        'warning': '#FFA500',       # Bit's amber eyes
        'background': '#000000',    # Black like Bit
        'surface': '#0A0A0A',       
        'glitch': '#00FFFF',        # Bit's digital chirps
        'narrative': '#8B00FF',     # Norman's purple gaming lights
        'success': '#00FF00',       
        'danger': '#FF0000',
        'bit_presence': '#1A1A1A',  # Subtle Bit shadow
        'gaming': '#FF00FF'         # Gaming RGB
    }
}

def get_tier_styles(tier):
    return BITTEN_COLORS.get(tier.lower(), BITTEN_COLORS['nibbler'])

def get_user_stats(user_id):
    """Get user's journey progress"""
    return {
        'gamertag': 'NODE_7',  # Everyone is a NODE in the network
        'chapter': 2,  # Story progress
        'tier': 'nibbler',
        'sync_level': 87,  # Connection to BITTEN
        'rounds_left': 3,  # Ammo metaphor
        'accuracy': 75,
        'earnings': 2.4,
        'streak': 3,
        'bit_trust': 85,  # Bit's trust in you
        'scars': 2,  # Memorable losses
        'breakthroughs': 5,  # Big wins
        'norman_voice': True,  # Unlocked Norman's guidance
    }

def get_bit_mood(user_stats):
    """Determine Bit's current mood based on performance"""
    if user_stats['streak'] >= 3:
        return 'purring', '😸'
    elif user_stats['streak'] <= -3:
        return 'concerned', '😿'
    elif user_stats['accuracy'] >= 80:
        return 'playful', '😺'
    else:
        return 'watchful', '🐱'

def get_narrative_moment(chapter, situation):
    """Get contextual story elements"""
    moments = {
        'high_confidence': [
            "Norman: 'This pattern... I've seen it in Apex ranked. Same energy.'",
            "Bit chirps excitedly, pawing at the screen.",
            "Your father's voice echoes: 'Discipline wins wars, son.'"
        ],
        'low_ammo': [
            "Norman: 'Save your shots. The best snipers wait.'",
            "Bit's amber eyes narrow, watching the charts.",
            "Remember: Every trade costs. Make them count."
        ],
        'losing_streak': [
            "Norman: 'I lost everything three times before BITTEN.'",
            "Bit curls up beside you, purring softly.",
            "Your mother whispers: 'Lightning needs direction.'"
        ]
    }
    return random.choice(moments.get(situation, ["The market waits for no one."]))

# ULTIMATE BITTEN HUD TEMPLATE
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN // Chapter {{ user_stats.chapter }}: The Signal</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            cursor: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><circle cx="10" cy="10" r="2" fill="%2300FF00"/></svg>') 10 10, auto;
        }
        
        body {
            background: {{ colors.background }};
            color: {{ colors.secondary }};
            font-family: 'Share Tech Mono', monospace;
            overflow: hidden;
            position: relative;
            height: 100vh;
        }
        
        /* BIT'S PRESENCE - Subtle shadow that moves */
        .bit-shadow {
            position: fixed;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, {{ colors.bit_presence }}40 0%, transparent 70%);
            pointer-events: none;
            animation: bitWander 20s infinite;
            z-index: 1;
        }
        
        @keyframes bitWander {
            0%, 100% { transform: translate(100px, 100px); }
            25% { transform: translate(80vw, 200px); }
            50% { transform: translate(70vw, 70vh); }
            75% { transform: translate(200px, 60vh); }
        }
        
        /* GLITCH EFFECTS - Bit's digital nature */
        @keyframes glitch {
            0%, 100% { text-shadow: 2px 0 {{ colors.glitch }}, -2px 0 {{ colors.accent }}; }
            25% { text-shadow: -2px 0 {{ colors.glitch }}, 2px 0 {{ colors.accent }}; }
            50% { text-shadow: 2px 0 {{ colors.accent }}, -2px 0 {{ colors.glitch }}; }
        }
        
        .glitch-text {
            animation: glitch 0.5s infinite;
        }
        
        /* NORMAN'S GAMING SETUP AESTHETIC */
        .main-interface {
            position: relative;
            z-index: 100;
            height: 100vh;
            padding: 20px;
            display: flex;
            flex-direction: column;
            background: 
                linear-gradient(135deg, transparent 30%, {{ colors.narrative }}05 50%, transparent 70%),
                radial-gradient(circle at 20% 50%, {{ colors.gaming }}10 0%, transparent 30%);
        }
        
        /* STORY HEADER - Where we are in the journey */
        .story-header {
            background: linear-gradient(90deg, {{ colors.surface }}CC 0%, transparent 50%, {{ colors.surface }}CC 100%);
            border-bottom: 1px solid {{ colors.primary }}30;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
        }
        
        .story-header::before {
            content: 'CHAPTER {{ user_stats.chapter }}: {{ chapter_title }}';
            position: absolute;
            top: 3px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            color: {{ colors.narrative }}80;
            letter-spacing: 3px;
            text-transform: uppercase;
        }
        
        .exit-btn {
            background: transparent;
            border: 1px solid {{ colors.danger }}50;
            color: {{ colors.danger }};
            padding: 8px 20px;
            font-size: 12px;
            letter-spacing: 2px;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
        }
        
        .exit-btn:hover {
            background: {{ colors.danger }}20;
            border-color: {{ colors.danger }};
            transform: translateY(-2px);
        }
        
        .node-id {
            font-family: 'Orbitron', sans-serif;
            color: {{ colors.primary }};
            font-size: 16px;
            letter-spacing: 2px;
        }
        
        /* BIT'S STATUS INDICATOR */
        .bit-status {
            position: absolute;
            top: 60px;
            right: 30px;
            text-align: right;
            z-index: 200;
        }
        
        .bit-mood {
            font-size: 40px;
            filter: drop-shadow(0 0 10px {{ colors.warning }}50);
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .bit-text {
            font-size: 12px;
            color: {{ colors.warning }}80;
            margin-top: 5px;
            font-style: italic;
        }
        
        /* CHARACTER STATS - Gaming RPG Style */
        .character-panel {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: {{ colors.surface }}80;
            border: 1px solid {{ colors.primary }}20;
            border-radius: 10px;
            position: relative;
        }
        
        .character-panel::before {
            content: '[ OPERATOR STATUS ]';
            position: absolute;
            top: -10px;
            left: 20px;
            background: {{ colors.background }};
            padding: 0 10px;
            font-size: 10px;
            color: {{ colors.primary }}60;
            letter-spacing: 2px;
        }
        
        .stat-item {
            text-align: center;
            position: relative;
        }
        
        .stat-label {
            font-size: 11px;
            color: {{ colors.primary }}60;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 24px;
            font-weight: 700;
            color: {{ colors.secondary }};
            text-shadow: 0 0 10px currentColor;
        }
        
        .stat-value.good {
            color: {{ colors.success }};
        }
        
        .stat-value.bad {
            color: {{ colors.danger }};
        }
        
        /* AMMO COUNTER - Gaming Style */
        .ammo-bar {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin-top: 5px;
        }
        
        .round {
            width: 25px;
            height: 35px;
            background: linear-gradient(to bottom, {{ colors.primary }} 0%, {{ colors.success }}80 100%);
            border: 1px solid {{ colors.primary }};
            position: relative;
            clip-path: polygon(20% 0%, 80% 0%, 100% 100%, 0% 100%);
            box-shadow: 0 0 5px {{ colors.primary }}50;
            transition: all 0.3s;
        }
        
        .round.spent {
            background: {{ colors.surface }};
            border-color: {{ colors.danger }}30;
            opacity: 0.3;
            box-shadow: none;
        }
        
        .round:hover:not(.spent) {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px {{ colors.primary }}50;
        }
        
        /* MAIN SIGNAL DISPLAY */
        .signal-core {
            flex: 1;
            background: {{ colors.surface }}90;
            border: 2px solid {{ colors.primary }}30;
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
            position: relative;
            overflow: hidden;
        }
        
        /* NORMAN'S VOICE / NARRATIVE TEXT */
        .narrative-voice {
            background: linear-gradient(135deg, {{ colors.narrative }}20 0%, transparent 100%);
            border-left: 3px solid {{ colors.narrative }};
            padding: 15px 20px;
            margin-bottom: 30px;
            font-style: italic;
            color: {{ colors.secondary }}CC;
            position: relative;
        }
        
        .narrative-voice::before {
            content: '💭';
            position: absolute;
            left: -15px;
            top: 15px;
            font-size: 20px;
        }
        
        /* TARGET DISPLAY - FPS Game Style */
        .target-info {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .signal-class {
            font-size: 14px;
            color: {{ colors.warning }};
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .target-designation {
            font-family: 'Orbitron', sans-serif;
            font-size: 42px;
            font-weight: 900;
            background: linear-gradient(45deg, {{ colors.primary }}, {{ colors.glitch }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
            letter-spacing: 5px;
            position: relative;
        }
        
        /* CONFIDENCE METER - RPG Style */
        .confidence-display {
            width: 80%;
            max-width: 400px;
            margin: 40px auto;
            text-align: center;
        }
        
        .confidence-bar-bg {
            height: 40px;
            background: {{ colors.surface }};
            border: 2px solid {{ colors.primary }}30;
            border-radius: 20px;
            overflow: hidden;
            position: relative;
        }
        
        .confidence-bar-fill {
            height: 100%;
            width: {{ tcs_score }}%;
            background: linear-gradient(90deg, 
                {% if tcs_score >= 85 %}{{ colors.success }}{% elif tcs_score >= 75 %}{{ colors.warning }}{% else %}{{ colors.danger }}{% endif %} 0%,
                {% if tcs_score >= 85 %}{{ colors.glitch }}{% elif tcs_score >= 75 %}{{ colors.primary }}{% else %}{{ colors.warning }}{% endif %} 100%
            );
            position: relative;
            transition: width 1s ease-out;
            box-shadow: 0 0 20px currentColor;
        }
        
        .confidence-bar-fill::after {
            content: '{{ tcs_score }}%';
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-family: 'Orbitron', sans-serif;
            font-size: 20px;
            font-weight: 700;
            color: {{ colors.background }};
            text-shadow: 0 0 5px {{ colors.secondary }};
        }
        
        .confidence-label {
            margin-top: 15px;
            font-size: 16px;
            font-weight: 700;
            {% if tcs_score >= 85 %}
            color: {{ colors.success }};
            text-shadow: 0 0 10px {{ colors.success }};
            {% elif tcs_score >= 75 %}
            color: {{ colors.warning }};
            text-shadow: 0 0 10px {{ colors.warning }};
            {% else %}
            color: {{ colors.danger }};
            text-shadow: 0 0 10px {{ colors.danger }};
            animation: pulse 1s infinite;
            {% endif %}
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* DECISION HELPER - Personal Touch */
        .decision-matrix {
            background: {{ colors.surface }};
            border: 1px solid {{ colors.primary }}20;
            border-radius: 10px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
            position: relative;
        }
        
        .decision-matrix::before {
            content: 'BITTEN ADVISORY';
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: {{ colors.surface }};
            padding: 0 15px;
            font-size: 10px;
            color: {{ colors.primary }}60;
            letter-spacing: 2px;
        }
        
        .decision-text {
            font-size: 16px;
            line-height: 1.6;
            color: {{ colors.secondary }};
        }
        
        .decision-text .highlight {
            color: {{ colors.warning }};
            font-weight: 700;
            text-shadow: 0 0 5px {{ colors.warning }}50;
        }
        
        /* COMBAT PARAMETERS - Clean Gaming UI */
        .parameters {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 30px 0;
        }
        
        .param-card {
            background: {{ colors.surface }}80;
            border: 1px solid {{ colors.primary }}20;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .param-card:hover {
            transform: translateY(-3px);
            border-color: {{ colors.primary }}50;
            box-shadow: 0 5px 15px {{ colors.primary }}20;
        }
        
        .param-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, {{ colors.primary }}, transparent);
            animation: scan 3s linear infinite;
        }
        
        @keyframes scan {
            to { left: 100%; }
        }
        
        .param-label {
            font-size: 11px;
            color: {{ colors.primary }}60;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .param-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 22px;
            font-weight: 700;
            color: {{ colors.secondary }};
        }
        
        .param-value.negative {
            color: {{ colors.danger }};
        }
        
        .param-value.positive {
            color: {{ colors.success }};
        }
        
        .risk-amount {
            font-size: 14px;
            color: {{ colors.warning }};
            margin-top: 5px;
            opacity: 0.8;
        }
        
        /* COUNTDOWN TIMER - Urgency */
        .mission-timer {
            background: {{ colors.danger }}10;
            border: 1px solid {{ colors.danger }}50;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            margin: 20px 0;
            position: relative;
        }
        
        .mission-timer::before {
            content: '⏱️ DECISION WINDOW';
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: {{ colors.surface }};
            padding: 0 15px;
            font-size: 10px;
            color: {{ colors.danger }};
            letter-spacing: 2px;
        }
        
        #countdown {
            font-family: 'Orbitron', sans-serif;
            font-size: 32px;
            font-weight: 700;
            color: {{ colors.danger }};
            text-shadow: 0 0 10px {{ colors.danger }}50;
        }
        
        /* ACTION BUTTONS - AAA Gaming Style */
        .action-panel {
            display: flex;
            gap: 20px;
            margin-top: 40px;
            padding: 0 20px;
        }
        
        .fire-btn {
            flex: 1;
            background: linear-gradient(135deg, {{ colors.success }} 0%, {{ colors.primary }} 100%);
            border: none;
            color: {{ colors.background }};
            padding: 20px;
            font-family: 'Orbitron', sans-serif;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 3px;
            cursor: pointer;
            border-radius: 10px;
            text-transform: uppercase;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
            box-shadow: 0 5px 20px {{ colors.primary }}50;
        }
        
        .fire-btn::before {
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
        
        .fire-btn:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .fire-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 30px {{ colors.primary }}70;
        }
        
        .fire-btn:active {
            transform: translateY(0);
        }
        
        .pass-btn {
            flex: 0.5;
            background: transparent;
            border: 1px solid {{ colors.danger }}50;
            color: {{ colors.danger }};
            padding: 20px;
            font-family: 'Orbitron', sans-serif;
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 2px;
            cursor: pointer;
            border-radius: 10px;
            text-transform: uppercase;
            transition: all 0.3s;
        }
        
        .pass-btn:hover {
            background: {{ colors.danger }}10;
            border-color: {{ colors.danger }};
            transform: translateY(-2px);
        }
        
        /* BOTTOM NAV - RPG Style Menu */
        .game-nav {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid {{ colors.primary }}20;
        }
        
        .nav-item {
            color: {{ colors.primary }}80;
            text-decoration: none;
            font-size: 14px;
            letter-spacing: 2px;
            text-transform: uppercase;
            padding: 10px 20px;
            border: 1px solid transparent;
            border-radius: 5px;
            transition: all 0.3s;
            position: relative;
        }
        
        .nav-item::before {
            content: attr(data-icon);
            margin-right: 8px;
            font-size: 16px;
        }
        
        .nav-item:hover {
            color: {{ colors.primary }};
            border-color: {{ colors.primary }}50;
            background: {{ colors.primary }}10;
            transform: translateY(-2px);
        }
        
        /* ACHIEVEMENT POPUP */
        .achievement-popup {
            position: fixed;
            top: 100px;
            right: -400px;
            width: 350px;
            background: {{ colors.surface }};
            border: 2px solid {{ colors.warning }};
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 30px {{ colors.warning }}50;
            transition: right 0.5s ease-out;
            z-index: 1000;
        }
        
        .achievement-popup.show {
            right: 20px;
        }
        
        .achievement-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 18px;
            color: {{ colors.warning }};
            margin-bottom: 10px;
        }
        
        .achievement-desc {
            font-size: 14px;
            color: {{ colors.secondary }}CC;
        }
        
        /* BIT'S CHIRP SOUNDS */
        .chirp-indicator {
            position: fixed;
            bottom: 30px;
            right: 30px;
            font-size: 14px;
            color: {{ colors.warning }}80;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .chirp-indicator.active {
            opacity: 1;
            animation: chirpPulse 1s ease-out;
        }
        
        @keyframes chirpPulse {
            0% { transform: scale(1); opacity: 0; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); opacity: 0; }
        }
        
        /* LOADING SCREEN */
        .loading-overlay {
            position: fixed;
            inset: 0;
            background: {{ colors.background }};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s;
        }
        
        .loading-overlay.active {
            opacity: 1;
            pointer-events: all;
        }
        
        .bit-loader {
            font-size: 60px;
            animation: float 2s ease-in-out infinite;
        }
        
        .loading-text {
            margin-top: 20px;
            font-family: 'Orbitron', sans-serif;
            color: {{ colors.primary }};
            letter-spacing: 2px;
        }
        
        /* RESPONSIVE */
        @media (max-width: 768px) {
            .parameters {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .character-panel {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .target-designation {
                font-size: 32px;
            }
            
            .action-panel {
                flex-direction: column;
            }
            
            .pass-btn {
                flex: 1;
            }
        }
    </style>
</head>
<body>
    <!-- Bit's Presence -->
    <div class="bit-shadow"></div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="bit-loader">{{ bit_emoji }}</div>
        <div class="loading-text">BITTEN INITIALIZING...</div>
    </div>
    
    <!-- Main Interface -->
    <div class="main-interface">
        <!-- Story Header -->
        <div class="story-header">
            <button class="exit-btn" onclick="exitMission()">
                ← EXIT
            </button>
            <div class="node-id">{{ user_stats.gamertag }}</div>
        </div>
        
        <!-- Bit's Status -->
        <div class="bit-status">
            <div class="bit-mood">{{ bit_emoji }}</div>
            <div class="bit-text">Bit is {{ bit_mood }}</div>
        </div>
        
        <!-- Character Stats Panel -->
        <div class="character-panel">
            <div class="stat-item">
                <div class="stat-label">Sync Level</div>
                <div class="stat-value">{{ user_stats.sync_level }}%</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Rounds Left</div>
                <div class="stat-value">
                    <div class="ammo-bar">
                        {% for i in range(6) %}
                            <div class="round {% if i >= user_stats.rounds_left %}spent{% endif %}"></div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Accuracy</div>
                <div class="stat-value {% if user_stats.accuracy >= 75 %}good{% else %}bad{% endif %}">
                    {{ user_stats.accuracy }}%
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Earnings</div>
                <div class="stat-value {% if user_stats.earnings >= 0 %}good{% else %}bad{% endif %}">
                    {{ "{:+.1f}".format(user_stats.earnings) }}%
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Streak</div>
                <div class="stat-value {% if user_stats.streak >= 3 %}good{% elif user_stats.streak < 0 %}bad{% endif %}">
                    {% if user_stats.streak >= 0 %}W{{ user_stats.streak }}{% else %}L{{ -user_stats.streak }}{% endif %}
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Bit's Trust</div>
                <div class="stat-value">{{ user_stats.bit_trust }}%</div>
            </div>
        </div>
        
        <!-- Main Signal Display -->
        <div class="signal-core">
            <!-- Norman's Voice / Narrative -->
            <div class="narrative-voice">
                {{ narrative_moment }}
            </div>
            
            <!-- Target Information -->
            <div class="target-info">
                <div class="signal-class">{{ signal_type }} SIGNAL DETECTED</div>
                <div class="target-designation">
                    {{ symbol }} {{ direction }}
                </div>
            </div>
            
            <!-- Confidence Display -->
            <div class="confidence-display">
                <div class="confidence-bar-bg">
                    <div class="confidence-bar-fill"></div>
                </div>
                <div class="confidence-label">
                    {% if tcs_score >= 90 %}LEGENDARY SETUP{% elif tcs_score >= 85 %}EPIC OPPORTUNITY{% elif tcs_score >= 75 %}SOLID CHANCE{% else %}RISKY GAMBIT{% endif %}
                </div>
            </div>
            
            <!-- Decision Helper -->
            <div class="decision-matrix">
                <div class="decision-text">
                    {% if user_stats.rounds_left <= 0 %}
                        <span class="highlight">⚠️ AMMUNITION DEPLETED</span><br>
                        Resupply arrives at midnight. Bit suggests patience.
                    {% elif tcs_score >= 85 and user_stats.accuracy >= 75 %}
                        <span class="highlight">🎯 PERFECT ALIGNMENT</span><br>
                        Your stats align with the signal. Bit purrs approvingly.
                    {% elif tcs_score >= 85 and user_stats.accuracy < 75 %}
                        <span class="highlight">⚡ HIGH VALUE TARGET</span><br>
                        Signal quality exceeds your recent performance. Trust the system.
                    {% elif tcs_score < 75 and user_stats.rounds_left <= 2 %}
                        <span class="highlight">💭 CONSERVATION MODE</span><br>
                        Low confidence + Low ammo. Bit's eyes narrow cautiously.
                    {% elif user_stats.streak <= -3 %}
                        <span class="highlight">🛡️ TILT PROTECTION</span><br>
                        Norman knows this feeling. Sometimes walking away is winning.
                    {% else %}
                        You have <span class="highlight">{{ user_stats.rounds_left }} rounds</span> remaining today.
                    {% endif %}
                </div>
            </div>
            
            <!-- Countdown Timer -->
            {% if expiry_seconds > 0 %}
            <div class="mission-timer">
                <div id="countdown">{{ expiry_seconds }}s</div>
            </div>
            {% endif %}
            
            <!-- Trade Parameters -->
            <div class="parameters">
                <div class="param-card">
                    <div class="param-label">Entry Point</div>
                    <div class="param-value">{{ entry|round(5) }}</div>
                </div>
                <div class="param-card">
                    <div class="param-label">Stop Loss</div>
                    <div class="param-value negative">{{ sl|round(5) }}</div>
                    <div class="risk-amount">-${{ (sl_pips * 10)|round(0)|int }}</div>
                </div>
                <div class="param-card">
                    <div class="param-label">Take Profit</div>
                    <div class="param-value positive">{{ tp|round(5) }}</div>
                    <div class="risk-amount">+${{ (tp_pips * 10)|round(0)|int }}</div>
                </div>
                <div class="param-card">
                    <div class="param-label">Risk Ratio</div>
                    <div class="param-value">1:{{ rr_ratio }}</div>
                </div>
                <div class="param-card">
                    <div class="param-label">Risk (pips)</div>
                    <div class="param-value">{{ sl_pips }}</div>
                </div>
                <div class="param-card">
                    <div class="param-label">Reward (pips)</div>
                    <div class="param-value positive">{{ tp_pips }}</div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="action-panel">
                <button class="fire-btn" onclick="fireSignal()" {% if user_stats.rounds_left <= 0 %}disabled{% endif %}>
                    EXECUTE TRADE
                </button>
                <button class="pass-btn" onclick="passSignal()">
                    PASS
                </button>
            </div>
        </div>
        
        <!-- Bottom Navigation -->
        <div class="game-nav">
            <a href="/education/{{ user_stats.tier }}" class="nav-item" data-icon="📚">
                Training
            </a>
            <a href="/stats/{{ user_id }}" class="nav-item" data-icon="📊">
                Stats
            </a>
            <a href="/notebook" class="nav-item" data-icon="📔">
                Notebook
            </a>
            <a href="/story" class="nav-item" data-icon="📖">
                Story
            </a>
        </div>
    </div>
    
    <!-- Achievement Popup -->
    <div class="achievement-popup" id="achievementPopup">
        <div class="achievement-title">🏆 FIRST SIGNAL VIEWED</div>
        <div class="achievement-desc">You're learning to read the market's language.</div>
    </div>
    
    <!-- Chirp Indicator -->
    <div class="chirp-indicator" id="chirpIndicator">♪ chirp ♪</div>
    
    <script>
        // Initialize with loading screen
        window.addEventListener('load', () => {
            setTimeout(() => {
                document.getElementById('loadingOverlay').classList.remove('active');
                playChirp();
                
                // Show achievement for new users
                if (Math.random() > 0.8) {
                    showAchievement();
                }
            }, 1500);
        });
        
        // Bit's chirp sounds
        function playChirp() {
            const chirp = document.getElementById('chirpIndicator');
            chirp.classList.add('active');
            
            // Play actual chirp sound here
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBzSHy+3agTkFJHHA7teSPhEWW6zn7LNaNwgUVKXm77diJwg0h8vw3YcuByN0v+3blEcPFlao5OyyWBELUKPg7bllHQUygtXx15E3CDh0v+3bj0wKFlaZ4u2tWiMKNoPQ8c+HOggyeL/s2oU9CjZ1wOvbjkAHH2ut5OyvZSEGOYLK8deOMAcUXrPq7J5aCg02eMPx2oo7Cihssuzhmmk7GCl7yfHPjj0HNnq+79WBMwgkbMDs1YlNDjN1v+zbkT0HGV6q5uyvaSEGKHy38taGPwk2ecTv1IYyBzNpu+7ZkEoKHmWy6eynVRUMOYLL7teVQAojbL7q2ZdWEBdeq+fsr2McBDiHyu7VgDYGMne/7diJQwk1e8LszpU7BBVYouPsqWAcCDh+zPLaizsHLXS97NaWQAojdMDt1pFLCjZ1wOnVkz0IGWSt5+6pWBIMRIzN8dKEOgswfMvtyI0+CRlkq+nqsF4TFEyY3++6XhsFOIHI7dKJNwchcLzp2plVDhJcqeburmIaCC9uu+zWlEkGJXLB6+CWUB0YXKXf8LVnIAU2ha3j3aRcFw02hbrt2IYyBB9MqOLwr2gdBjeS1/LOhS0JM3e/8tiIOQcjc7vq2JJKFBxnpuXus2gZDTGS0fHThzQDJHXD79iRRwgleMXu1JFGDTh8x+zTgDQGG1er5O2yZRwFH2Cp5+6ubB8HKHa98daOOwcZZ6/o5KlXGgwue8fp3JZJCD91yO7NkDkGH2ar4+2xWCQJLX/L8ciMOAk3dsXu15JFCRdprOftrGEZCz90yPHMfS8DL3a/59iSQAoibrjtzo4/BRViturstGAYBjiExfDShjkGGVyt5u2qYCEGNoLI8dWNOwgtd8Dp05RDDTZyxuXOjj0HIW259tyTSg4cZa7q6K5fFgs5gMDw0oo3CydxxOzNjkUKHWOr6OWvXRkGMn/G8NKLOgUydsLx1Y9DCR9itOTqpVcdDS+ByPLPgjQJLXfD792RRwUkbLjp2phUCRtkr+nrp10VDjh9x+7TiTsHK3e/7tSPQgkZa6vr5KxaGw0kbsHu1ZVHCB1JqODrrVwWDjiDy/HQhTcJMnPA7NWTRwcjar7i3qpZFQ01hcXu2IkyCCdvt+jYmU4JG2av7OqmWhcMLYLL79OGOwcqcrvu1JVKCRVUpePqsmccBj6FzvPUfS4EMH3A7tiJPgcjcrbq3JNNFQ5WsuDurVkZBjeAx+/ThjUELHfH8NaLPAYsecHs04tACRVbqOPsr14ZCTuDyO3RgjQHJHDA7tiVSAcYa63s56pYFRE3f8vx1YY4CTB3v+XakEoHG2WX6uyvYh0FMIfP8s2COwo3ecHr05M9Bh9MpuXtsGEdBTSByPLOhDkJOXXD7tiOQgkpa7Ps3pVOERJfpuPtrnAZBChpoN3tqGgjCDJ/yu/IhDwINnXD7tSRQwcVXqfg6K5hFQw7gsru1oo3Bids5PGJNwgdZLLi66tkGA0vgMbvzIMzCDd1we3YlEYGHV6p5eyvYRsGLnvG7tiOQAcnbrbq26hVDhJmouTvrF8YCC2Dw+/ShjgHNHfE79aOQQcZaLfn56ZXFws3f8vu2YczAiZwvuvZkEwKF1+n4+uxWiIHMIHK788/Mgg2eL/r1IxACSdstvLckUkQDmGj5+2oXxgHMoLJ79KFOAc2eMPx1o9FBiFqvu3im1ILGWK04uapWBYNMX/E8NOINwUveL7r1IxACB9nqeLqrmIWByp6x+/YkEAGJma/9deUUAkWYKvm7qhVGgo0gMvu1oc1Bix3xu3Yij0JIWy25+OaURIRVazn7axfGQguf8Xs0oo8CB5/ivDNZjEAAAA=');
            audio.volume = 0.2;
            audio.play().catch(() => {});
            
            setTimeout(() => {
                chirp.classList.remove('active');
            }, 1000);
        }
        
        // Show achievement
        function showAchievement() {
            const popup = document.getElementById('achievementPopup');
            popup.classList.add('show');
            playChirp();
            
            setTimeout(() => {
                popup.classList.remove('show');
            }, 5000);
        }
        
        // Telegram WebApp API
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Exit mission
        function exitMission() {
            playChirp();
            document.getElementById('loadingOverlay').classList.add('active');
            
            setTimeout(() => {
                if (tg) {
                    tg.close();
                } else {
                    window.close();
                    setTimeout(() => {
                        window.location.href = 'https://t.me/BittenCommander';
                    }, 100);
                }
            }, 500);
        }
        
        // Fire signal
        function fireSignal() {
            if ({{ user_stats.rounds_left }} <= 0) {
                alert("Bit chirps sadly - you're out of ammo for today.");
                return;
            }
            
            playChirp();
            
            // Send data
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'fire',
                    signal_id: '{{ signal_id }}',
                    symbol: '{{ symbol }}',
                    direction: '{{ direction }}'
                }));
            }
            
            // Update button
            document.querySelector('.fire-btn').innerHTML = '✅ TRADE EXECUTED';
            document.querySelector('.fire-btn').disabled = true;
            
            // Bit celebrates
            document.querySelector('.bit-mood').textContent = '😸';
            document.querySelector('.bit-text').textContent = 'Bit approves!';
            
            setTimeout(exitMission, 1500);
        }
        
        // Pass signal
        function passSignal() {
            playChirp();
            
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'skip',
                    signal_id: '{{ signal_id }}'
                }));
            }
            
            // Bit understands
            document.querySelector('.bit-mood').textContent = '😺';
            document.querySelector('.bit-text').textContent = 'Bit respects patience';
            
            setTimeout(exitMission, 1000);
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
                document.querySelector('.fire-btn').disabled = true;
                document.querySelector('.fire-btn').innerHTML = '❌ WINDOW CLOSED';
                
                // Bit reacts
                document.querySelector('.bit-mood').textContent = '😿';
                document.querySelector('.bit-text').textContent = 'Bit says too slow';
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}s`;
                
                // Urgency at low time
                if (timeLeft === 10) {
                    playChirp();
                    document.querySelector('.mission-timer').style.animation = 'pulse 0.5s infinite';
                }
            }
        }, 1000);
        {% endif %}
        
        // Random Bit movements
        setInterval(() => {
            if (Math.random() > 0.95) {
                playChirp();
                
                // Bit comments on the situation
                const comments = [
                    "Bit watches intently",
                    "Bit's tail twitches",
                    "Bit calculates odds",
                    "Bit senses opportunity"
                ];
                document.querySelector('.bit-text').textContent = comments[Math.floor(Math.random() * comments.length)];
            }
        }, 8000);
        
        // Glitch effect on hover
        document.querySelectorAll('.stat-value, .param-value').forEach(el => {
            el.addEventListener('mouseenter', () => {
                el.classList.add('glitch-text');
                setTimeout(() => {
                    el.classList.remove('glitch-text');
                }, 500);
            });
        });
        
        // Smooth confidence bar fill
        setTimeout(() => {
            const fillBar = document.querySelector('.confidence-bar-fill');
            if (fillBar) {
                fillBar.style.width = '0%';
                setTimeout(() => {
                    fillBar.style.width = '{{ tcs_score }}%';
                }, 100);
            }
        }, 500);
    </script>
</body>
</html>
"""

# Additional Templates...
@app.route('/')
def index():
    return "BITTEN ULTIMATE - ONLINE", 200

@app.route('/hud')
def hud():
    try:
        encoded_data = request.args.get('data', '')
        if not encoded_data:
            return "NO SIGNAL DATA", 400
        
        decoded_data = urllib.parse.unquote(encoded_data)
        data = json.loads(decoded_data)
        
        signal = data.get('signal', {})
        user_id = data.get('user_id', 'demo')
        user_stats = get_user_stats(user_id)
        
        # Get Bit's mood
        bit_mood, bit_emoji = get_bit_mood(user_stats)
        
        # Get narrative context
        if user_stats['rounds_left'] <= 0:
            narrative_moment = get_narrative_moment(user_stats['chapter'], 'low_ammo')
        elif signal.get('tcs_score', 0) >= 85:
            narrative_moment = get_narrative_moment(user_stats['chapter'], 'high_confidence')
        elif user_stats['streak'] <= -3:
            narrative_moment = get_narrative_moment(user_stats['chapter'], 'losing_streak')
        else:
            narrative_moment = "The market pulses with possibility. Bit watches, tail twitching."
        
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
            'colors': get_tier_styles(user_stats['tier']),
            'bit_mood': bit_mood,
            'bit_emoji': bit_emoji,
            'narrative_moment': narrative_moment,
            'chapter_title': 'The Signal'
        }
        
        return render_template_string(HUD_TEMPLATE, **context)
        
    except Exception as e:
        return f"ERROR: {str(e)}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8892, debug=False)