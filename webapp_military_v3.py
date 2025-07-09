#!/usr/bin/env python3
"""MECH WARFARE COCKPIT - Pacific Rim Style"""

from flask import Flask, render_template_string, request
import json
import urllib.parse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# MECH WARFARE COLORS
MECH_STYLES = {
    'nibbler': {
        'primary': '#FF6B00',       # Orange mech glow
        'secondary': '#FFFFFF',     
        'accent': '#00FF00',        # Green systems
        'warning': '#FFD700',       # Gold alerts
        'background': '#0D0D0D',    # Deep black
        'surface': '#1A1A1A',       
        'steel': '#4A4A4A',         # Metal gray
        'plasma': '#00D4FF',        # Plasma blue
        'danger': '#FF0000',        
        'success': '#00FF00',       
        'power': '#FF00FF',         # Power core purple
        'heat': '#FF4500'           # Heat orange
    }
}

def get_tier_styles(tier):
    return MECH_STYLES.get(tier.lower(), MECH_STYLES['nibbler'])

def get_user_stats(user_id):
    return {
        'pilot_id': 'STRIKER-7',
        'mech_class': 'NIBBLER-MK1',
        'tier': 'nibbler',
        'sync_ratio': 87,
        'shells_loaded': 3,
        'hit_probability': 75,
        'combat_yield': 2.4,
        'kill_chain': 3,
        'reactor_status': 'OPTIMAL',
        'heat_level': 45,
        'armor_integrity': 92
    }

# MECH COCKPIT HUD TEMPLATE
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MECH COMBAT SYSTEM // FIRE CONTROL</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Russo+One&family=Share+Tech+Mono&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            user-select: none;
        }
        
        body {
            background: {{ colors.background }};
            color: {{ colors.secondary }};
            font-family: 'Share Tech Mono', monospace;
            font-size: 14px;
            overflow: hidden;
            position: relative;
            height: 100vh;
        }
        
        /* MECH HUD OVERLAY */
        .hud-overlay {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 1000;
        }
        
        /* CORNER BRACKETS */
        .corner-bracket {
            position: absolute;
            width: 50px;
            height: 50px;
            border: 2px solid {{ colors.primary }};
        }
        
        .corner-bracket.tl {
            top: 20px;
            left: 20px;
            border-right: none;
            border-bottom: none;
        }
        
        .corner-bracket.tr {
            top: 20px;
            right: 20px;
            border-left: none;
            border-bottom: none;
        }
        
        .corner-bracket.bl {
            bottom: 20px;
            left: 20px;
            border-right: none;
            border-top: none;
        }
        
        .corner-bracket.br {
            bottom: 20px;
            right: 20px;
            border-left: none;
            border-top: none;
        }
        
        /* SCANNING LINES */
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100vh); }
        }
        
        .scanline {
            position: fixed;
            left: 0;
            right: 0;
            height: 100px;
            background: linear-gradient(transparent, {{ colors.primary }}10, transparent);
            animation: scanline 4s linear infinite;
        }
        
        /* MAIN COCKPIT */
        .cockpit-interface {
            position: relative;
            z-index: 100;
            height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 60px 40px 40px;
        }
        
        /* TOP STATUS BAR */
        .status-bar {
            background: {{ colors.surface }};
            border: 2px solid {{ colors.steel }};
            border-radius: 5px;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
        }
        
        .eject-button {
            background: {{ colors.danger }}30;
            border: 2px solid {{ colors.danger }};
            color: {{ colors.danger }};
            padding: 10px 30px;
            font-family: 'Russo One', sans-serif;
            font-size: 14px;
            letter-spacing: 2px;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.3s;
            box-shadow: 0 0 20px {{ colors.danger }}30;
        }
        
        .eject-button:hover {
            background: {{ colors.danger }};
            color: black;
            box-shadow: 0 0 30px {{ colors.danger }};
            transform: scale(1.05);
        }
        
        .mech-designation {
            font-family: 'Russo One', sans-serif;
            font-size: 20px;
            color: {{ colors.primary }};
            text-shadow: 0 0 20px {{ colors.primary }}50;
            letter-spacing: 3px;
        }
        
        /* PILOT SYSTEMS */
        .pilot-systems {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .system-panel {
            background: {{ colors.surface }};
            border: 2px solid {{ colors.steel }};
            border-radius: 5px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
        }
        
        .system-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: {{ colors.success }};
            box-shadow: 0 0 10px {{ colors.success }};
        }
        
        .system-panel.warning::before {
            background: {{ colors.warning }};
            box-shadow: 0 0 10px {{ colors.warning }};
        }
        
        .system-panel.critical::before {
            background: {{ colors.danger }};
            box-shadow: 0 0 10px {{ colors.danger }};
            animation: alertPulse 0.5s infinite;
        }
        
        @keyframes alertPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .system-label {
            font-size: 11px;
            color: {{ colors.steel }};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .system-value {
            font-family: 'Russo One', sans-serif;
            font-size: 28px;
            color: {{ colors.secondary }};
            text-shadow: 0 0 10px currentColor;
        }
        
        /* AMMO DISPLAY */
        .ammo-display {
            display: flex;
            gap: 5px;
            justify-content: center;
            margin-top: 10px;
        }
        
        .shell {
            width: 30px;
            height: 60px;
            background: linear-gradient(to bottom, {{ colors.steel }}, {{ colors.primary }});
            border: 1px solid {{ colors.primary }};
            border-radius: 15px 15px 5px 5px;
            position: relative;
            box-shadow: 0 0 10px {{ colors.primary }}50;
        }
        
        .shell.empty {
            background: {{ colors.surface }};
            border-color: {{ colors.steel }};
            opacity: 0.3;
            box-shadow: none;
        }
        
        .shell::before {
            content: '';
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: {{ colors.heat }};
            box-shadow: 0 0 15px {{ colors.heat }};
        }
        
        .shell.empty::before {
            display: none;
        }
        
        /* MAIN COMBAT DISPLAY */
        .combat-display {
            flex: 1;
            background: {{ colors.surface }};
            border: 3px solid {{ colors.steel }};
            border-radius: 10px;
            padding: 30px;
            position: relative;
            overflow: hidden;
            box-shadow: 
                inset 0 0 50px rgba(0,0,0,0.5),
                0 0 30px {{ colors.primary }}20;
        }
        
        /* TARGETING RETICLE */
        .targeting-system {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .target-lock {
            font-family: 'Russo One', sans-serif;
            font-size: 18px;
            color: {{ colors.heat }};
            letter-spacing: 3px;
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        
        .target-data {
            font-size: 48px;
            font-weight: bold;
            color: {{ colors.secondary }};
            text-transform: uppercase;
            letter-spacing: 5px;
            text-shadow: 
                0 0 20px {{ colors.primary }},
                0 0 40px {{ colors.primary }}50;
            animation: targetPulse 2s ease-in-out infinite;
        }
        
        @keyframes targetPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        /* THREAT ASSESSMENT */
        .threat-display {
            width: 400px;
            height: 200px;
            margin: 40px auto;
            position: relative;
            background: {{ colors.background }};
            border: 2px solid {{ colors.steel }};
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* RADAR SWEEP */
        .radar-sweep {
            position: absolute;
            inset: 0;
            background: conic-gradient(
                from 0deg,
                transparent 0deg,
                {{ colors.success }}30 30deg,
                transparent 60deg
            );
            animation: radarSweep 3s linear infinite;
        }
        
        @keyframes radarSweep {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .threat-score {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 10;
        }
        
        .threat-value {
            font-family: 'Russo One', sans-serif;
            font-size: 72px;
            font-weight: bold;
            {% if tcs_score >= 85 %}
            color: {{ colors.success }};
            text-shadow: 0 0 30px {{ colors.success }};
            {% elif tcs_score >= 75 %}
            color: {{ colors.warning }};
            text-shadow: 0 0 30px {{ colors.warning }};
            {% else %}
            color: {{ colors.danger }};
            text-shadow: 0 0 30px {{ colors.danger }};
            {% endif %}
        }
        
        .threat-label {
            font-size: 14px;
            color: {{ colors.steel }};
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 10px;
        }
        
        /* COMBAT ADVISORY */
        .combat-advisory {
            background: linear-gradient(135deg, {{ colors.power }}10 0%, transparent 100%);
            border: 1px solid {{ colors.power }}50;
            border-radius: 5px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
            position: relative;
        }
        
        .combat-advisory::before {
            content: 'AI TACTICAL ANALYSIS';
            position: absolute;
            top: -10px;
            left: 20px;
            background: {{ colors.surface }};
            padding: 0 10px;
            font-size: 11px;
            color: {{ colors.power }};
            letter-spacing: 2px;
        }
        
        .advisory-text {
            font-size: 16px;
            line-height: 1.6;
            color: {{ colors.secondary }};
        }
        
        .advisory-text .critical {
            color: {{ colors.heat }};
            font-weight: bold;
            text-shadow: 0 0 10px {{ colors.heat }};
        }
        
        /* COMBAT PARAMETERS */
        .combat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }
        
        .param-module {
            background: {{ colors.background }};
            border: 2px solid {{ colors.steel }};
            border-radius: 5px;
            padding: 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .param-module::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, {{ colors.plasma }}, transparent);
            animation: dataFlow 2s linear infinite;
        }
        
        @keyframes dataFlow {
            from { transform: translateX(-100%); }
            to { transform: translateX(100%); }
        }
        
        .param-label {
            font-size: 11px;
            color: {{ colors.steel }};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .param-value {
            font-family: 'Russo One', sans-serif;
            font-size: 24px;
            color: {{ colors.secondary }};
            text-shadow: 0 0 5px currentColor;
        }
        
        .param-value.negative {
            color: {{ colors.danger }};
        }
        
        .param-value.positive {
            color: {{ colors.success }};
        }
        
        .damage-estimate {
            font-size: 14px;
            color: {{ colors.heat }};
            margin-top: 5px;
        }
        
        /* COUNTDOWN */
        .combat-timer {
            background: {{ colors.danger }}20;
            border: 2px solid {{ colors.danger }};
            border-radius: 5px;
            padding: 20px;
            text-align: center;
            font-family: 'Russo One', sans-serif;
            font-size: 32px;
            color: {{ colors.danger }};
            text-shadow: 0 0 20px {{ colors.danger }};
            margin: 30px 0;
            position: relative;
        }
        
        .combat-timer::before {
            content: 'ENGAGEMENT WINDOW';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: {{ colors.surface }};
            padding: 0 15px;
            font-size: 12px;
            letter-spacing: 2px;
        }
        
        /* FIRE CONTROL */
        .fire-control {
            display: flex;
            gap: 20px;
            margin-top: 40px;
        }
        
        .fire-button {
            flex: 1;
            background: linear-gradient(135deg, {{ colors.heat }} 0%, {{ colors.danger }} 100%);
            border: 3px solid {{ colors.heat }};
            color: white;
            padding: 25px;
            font-family: 'Russo One', sans-serif;
            font-size: 24px;
            letter-spacing: 3px;
            cursor: pointer;
            text-transform: uppercase;
            position: relative;
            overflow: hidden;
            box-shadow: 
                0 0 30px {{ colors.heat }}50,
                inset 0 0 20px rgba(0,0,0,0.3);
            transition: all 0.3s;
        }
        
        .fire-button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
            transform: translate(-50%, -50%) scale(0);
            transition: transform 0.5s;
        }
        
        .fire-button:hover::before {
            transform: translate(-50%, -50%) scale(1);
        }
        
        .fire-button:hover {
            transform: translateY(-3px);
            box-shadow: 
                0 10px 40px {{ colors.heat }}70,
                inset 0 0 30px rgba(255,255,255,0.1);
        }
        
        .fire-button:active {
            transform: translateY(0);
        }
        
        .disengage-button {
            flex: 0.4;
            background: transparent;
            border: 2px solid {{ colors.steel }};
            color: {{ colors.steel }};
            padding: 25px;
            font-family: 'Russo One', sans-serif;
            font-size: 18px;
            letter-spacing: 2px;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.3s;
        }
        
        .disengage-button:hover {
            border-color: {{ colors.danger }};
            color: {{ colors.danger }};
            background: {{ colors.danger }}10;
            box-shadow: 0 0 20px {{ colors.danger }}30;
        }
        
        /* BOTTOM LINKS */
        .tactical-links {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid {{ colors.steel }}50;
        }
        
        .tactical-link {
            color: {{ colors.plasma }};
            text-decoration: none;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
            text-transform: uppercase;
            padding: 10px 20px;
            border: 1px solid {{ colors.plasma }}50;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .tactical-link::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: {{ colors.plasma }}20;
            transition: left 0.3s;
        }
        
        .tactical-link:hover::before {
            left: 0;
        }
        
        .tactical-link:hover {
            color: {{ colors.secondary }};
            border-color: {{ colors.plasma }};
            box-shadow: 0 0 20px {{ colors.plasma }}50;
        }
        
        /* WARNING LIGHTS */
        .warning-lights {
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 20px;
            z-index: 500;
        }
        
        .warning-light {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: {{ colors.steel }};
            box-shadow: inset 0 0 5px rgba(0,0,0,0.5);
        }
        
        .warning-light.active {
            background: {{ colors.danger }};
            box-shadow: 
                0 0 20px {{ colors.danger }},
                inset 0 0 5px rgba(255,255,255,0.5);
            animation: warningBlink 1s infinite;
        }
        
        @keyframes warningBlink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        /* POWER METER */
        .power-meter {
            position: fixed;
            right: 40px;
            top: 50%;
            transform: translateY(-50%);
            width: 30px;
            height: 300px;
            background: {{ colors.surface }};
            border: 2px solid {{ colors.steel }};
            border-radius: 15px;
            overflow: hidden;
            z-index: 500;
        }
        
        .power-level {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: {{ user_stats.sync_ratio }}%;
            background: linear-gradient(to top, {{ colors.power }}, {{ colors.plasma }});
            box-shadow: 0 0 20px {{ colors.power }};
            transition: height 0.5s;
        }
        
        .power-marker {
            position: absolute;
            left: -5px;
            right: -5px;
            height: 2px;
            background: {{ colors.secondary }};
        }
        
        .power-marker.critical {
            bottom: 20%;
            background: {{ colors.danger }};
        }
        
        .power-marker.optimal {
            bottom: 80%;
            background: {{ colors.success }};
        }
    </style>
</head>
<body>
    <!-- HUD Overlay -->
    <div class="hud-overlay">
        <div class="corner-bracket tl"></div>
        <div class="corner-bracket tr"></div>
        <div class="corner-bracket bl"></div>
        <div class="corner-bracket br"></div>
    </div>
    
    <!-- Scanning Line -->
    <div class="scanline"></div>
    
    <!-- Warning Lights -->
    <div class="warning-lights">
        <div class="warning-light {% if user_stats.shells_loaded <= 1 %}active{% endif %}"></div>
        <div class="warning-light {% if user_stats.heat_level > 80 %}active{% endif %}"></div>
        <div class="warning-light {% if user_stats.armor_integrity < 50 %}active{% endif %}"></div>
    </div>
    
    <!-- Power Meter -->
    <div class="power-meter">
        <div class="power-level"></div>
        <div class="power-marker critical"></div>
        <div class="power-marker optimal"></div>
    </div>
    
    <div class="cockpit-interface">
        <!-- Status Bar -->
        <div class="status-bar">
            <button class="eject-button" onclick="eject()">
                ◄ EJECT
            </button>
            <div class="mech-designation">{{ user_stats.mech_class }}</div>
        </div>
        
        <!-- Pilot Systems -->
        <div class="pilot-systems">
            <div class="system-panel">
                <div class="system-label">Pilot ID</div>
                <div class="system-value">{{ user_stats.pilot_id }}</div>
            </div>
            
            <div class="system-panel {% if user_stats.shells_loaded <= 1 %}critical{% elif user_stats.shells_loaded <= 3 %}warning{% endif %}">
                <div class="system-label">Ammunition</div>
                <div class="system-value">
                    <div class="ammo-display">
                        {% for i in range(6) %}
                            <div class="shell {% if i >= user_stats.shells_loaded %}empty{% endif %}"></div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div class="system-panel {% if user_stats.hit_probability < 70 %}warning{% endif %}">
                <div class="system-label">Hit Probability</div>
                <div class="system-value">{{ user_stats.hit_probability }}%</div>
            </div>
            
            <div class="system-panel {% if user_stats.combat_yield < 0 %}critical{% endif %}">
                <div class="system-label">Combat Yield</div>
                <div class="system-value">{{ "{:+.1f}".format(user_stats.combat_yield) }}%</div>
            </div>
        </div>
        
        <!-- Combat Display -->
        <div class="combat-display">
            <!-- Targeting System -->
            <div class="targeting-system">
                <div class="target-lock">{{ signal_type }} TARGET ACQUIRED</div>
                <div class="target-data">{{ symbol }} // {{ direction }}</div>
            </div>
            
            <!-- Threat Display -->
            <div class="threat-display">
                <div class="radar-sweep"></div>
                <div class="threat-score">
                    <div class="threat-value">{{ tcs_score }}%</div>
                    <div class="threat-label">KILL PROBABILITY</div>
                </div>
            </div>
            
            <!-- Combat Advisory -->
            <div class="combat-advisory">
                <div class="advisory-text">
                    {% if user_stats.shells_loaded <= 0 %}
                        <span class="critical">⚠️ AMMUNITION CRITICAL</span><br>
                        Return to base for reload. Systems reset at 00:00 UTC.
                    {% elif tcs_score >= 85 and user_stats.hit_probability >= 70 %}
                        <span class="critical">🎯 OPTIMAL FIRING SOLUTION</span><br>
                        All systems green. Weapons free.
                    {% elif tcs_score >= 85 and user_stats.hit_probability < 70 %}
                        <span class="critical">⚡ HIGH-VALUE TARGET</span><br>
                        Override accuracy warnings. Fire at will.
                    {% elif tcs_score < 75 and user_stats.shells_loaded <= 2 %}
                        <span class="critical">💭 CONSERVE AMMUNITION</span><br>
                        Low probability shot. Save rounds for better targets.
                    {% elif user_stats.kill_chain <= -3 %}
                        <span class="critical">🛡️ SYSTEM OVERHEAT</span><br>
                        Disengage and cool systems.
                    {% else %}
                        <span class="critical">{{ user_stats.shells_loaded }} ROUNDS</span> in magazine.
                    {% endif %}
                </div>
            </div>
            
            <!-- Combat Timer -->
            {% if expiry_seconds > 0 %}
            <div class="combat-timer">
                <span id="countdown">{{ expiry_seconds }}s</span>
            </div>
            {% endif %}
            
            <!-- Combat Parameters -->
            <div class="combat-grid">
                <div class="param-module">
                    <div class="param-label">Lock Vector</div>
                    <div class="param-value">{{ entry|round(5) }}</div>
                </div>
                <div class="param-module">
                    <div class="param-label">Damage Limit</div>
                    <div class="param-value negative">{{ sl|round(5) }}</div>
                    <div class="damage-estimate">-${{ (sl_pips * 10)|round(0)|int }}</div>
                </div>
                <div class="param-module">
                    <div class="param-label">Kill Zone</div>
                    <div class="param-value positive">{{ tp|round(5) }}</div>
                    <div class="damage-estimate">+${{ (tp_pips * 10)|round(0)|int }}</div>
                </div>
                <div class="param-module">
                    <div class="param-label">Risk Matrix</div>
                    <div class="param-value">1:{{ rr_ratio }}</div>
                </div>
                <div class="param-module">
                    <div class="param-label">Exposure</div>
                    <div class="param-value">{{ sl_pips }}</div>
                </div>
                <div class="param-module">
                    <div class="param-label">Payload</div>
                    <div class="param-value positive">{{ tp_pips }}</div>
                </div>
            </div>
            
            <!-- Fire Control -->
            <div class="fire-control">
                <button class="fire-button" onclick="fireWeapon()" {% if user_stats.shells_loaded <= 0 %}disabled{% endif %}>
                    FIRE MAIN CANNON
                </button>
                <button class="disengage-button" onclick="disengage()">
                    DISENGAGE
                </button>
            </div>
            
            <!-- Tactical Links -->
            <div class="tactical-links">
                <a href="/education/{{ user_stats.tier }}" target="_blank" class="tactical-link">
                    COMBAT SIMULATOR
                </a>
                <a href="/stats/{{ user_id }}" target="_blank" class="tactical-link">
                    BATTLE RECORDS
                </a>
                <a href="/history" target="_blank" class="tactical-link">
                    MISSION LOGS
                </a>
            </div>
        </div>
    </div>
    
    <script>
        // Mech startup sounds
        const audio = {
            startup: new Audio('data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA='),
            warning: new Audio('data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA='),
            fire: new Audio('data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=')
        };
        
        // Simulate mech vibration
        function mechVibration() {
            const elements = document.querySelectorAll('.system-panel, .param-module');
            elements.forEach(el => {
                setInterval(() => {
                    const x = (Math.random() - 0.5) * 2;
                    const y = (Math.random() - 0.5) * 2;
                    el.style.transform = `translate(${x}px, ${y}px)`;
                }, 100);
            });
        }
        
        mechVibration();
        
        // Telegram WebApp API
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Eject
        function eject() {
            const confirm = window.confirm("CONFIRM EJECTION SEQUENCE?");
            if (!confirm) return;
            
            if (tg) {
                tg.close();
            } else {
                window.close();
                setTimeout(() => {
                    window.location.href = 'https://t.me/BittenCommander';
                }, 100);
            }
        }
        
        // Fire weapon
        function fireWeapon() {
            if ({{ user_stats.shells_loaded }} <= 0) {
                alert('AMMUNITION DEPLETED. RTB IMMEDIATELY.');
                return;
            }
            
            // Weapon fire effect
            document.body.style.animation = 'weaponRecoil 0.3s';
            setTimeout(() => {
                document.body.style.animation = '';
            }, 300);
            
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'fire',
                    signal_id: '{{ signal_id }}',
                    symbol: '{{ symbol }}',
                    direction: '{{ direction }}'
                }));
            }
            
            document.querySelector('.fire-button').innerHTML = '💥 ROUND AWAY';
            document.querySelector('.fire-button').disabled = true;
            
            setTimeout(eject, 1500);
        }
        
        // Disengage
        function disengage() {
            if (tg) {
                tg.sendData(JSON.stringify({
                    action: 'skip',
                    signal_id: '{{ signal_id }}'
                }));
            }
            eject();
        }
        
        // Add recoil animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes weaponRecoil {
                0% { transform: translateY(0); }
                25% { transform: translateY(-10px); }
                50% { transform: translateY(5px); }
                75% { transform: translateY(-3px); }
                100% { transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
        
        // Countdown
        {% if expiry_seconds > 0 %}
        let timeLeft = {{ expiry_seconds }};
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timer);
                countdownEl.textContent = 'EXPIRED';
                document.querySelector('.fire-button').disabled = true;
                document.querySelector('.fire-button').innerHTML = 'WINDOW CLOSED';
                document.querySelector('.combat-timer').style.animation = 'alertPulse 0.5s infinite';
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}s`;
                
                // Warning at low time
                if (timeLeft <= 10) {
                    document.querySelectorAll('.warning-light')[1].classList.add('active');
                }
            }
        }, 1000);
        {% endif %}
        
        // Simulate heat buildup
        let heat = {{ user_stats.heat_level }};
        setInterval(() => {
            heat += Math.random() * 2 - 1;
            heat = Math.max(0, Math.min(100, heat));
            
            if (heat > 80) {
                document.querySelectorAll('.warning-light')[1].classList.add('active');
            } else {
                document.querySelectorAll('.warning-light')[1].classList.remove('active');
            }
        }, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return "MECH SYSTEMS ONLINE", 200

@app.route('/hud')
def hud():
    try:
        encoded_data = request.args.get('data', '')
        if not encoded_data:
            return "NO TARGET DATA", 400
        
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
        return f"SYSTEM ERROR: {str(e)}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8891, debug=False)