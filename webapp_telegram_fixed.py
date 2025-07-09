#!/usr/bin/env python3
"""Fixed Flask server with proper Telegram WebApp integration"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import json
import urllib.parse
import os
import sys
from datetime import datetime
import random

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
        'squad_engagement': random.randint(45, 89)  # Percentage of squad taking this signal
    }

# Military-themed pattern names
PATTERN_NAMES = {
    'LONDON_RAID': {
        'name': 'LONDON RAID',
        'description': 'London session breakout assault',
        'best_time': '08:00-10:00 GMT',
        'success_rate': 78,
        'risk_level': 'MODERATE'
    },
    'WALL_BREACH': {
        'name': 'WALL BREACH', 
        'description': 'Major support/resistance breakthrough',
        'best_time': 'Any high volume period',
        'success_rate': 82,
        'risk_level': 'LOW'
    },
    'SNIPER_NEST': {
        'name': "SNIPER'S NEST",
        'description': 'Range-bound precision strike',
        'best_time': 'Asian session',
        'success_rate': 75,
        'risk_level': 'LOW'
    },
    'AMBUSH_POINT': {
        'name': 'AMBUSH POINT',
        'description': 'Trend reversal trap',
        'best_time': 'Session overlaps',
        'success_rate': 71,
        'risk_level': 'HIGH'
    },
    'SUPPLY_DROP': {
        'name': 'SUPPLY DROP',
        'description': 'Pullback to moving average',
        'best_time': 'Trending markets',
        'success_rate': 80,
        'risk_level': 'LOW'
    },
    'PINCER_MOVE': {
        'name': 'PINCER MOVE',
        'description': 'Volatility squeeze breakout',
        'best_time': 'Pre-news consolidation',
        'success_rate': 69,
        'risk_level': 'HIGH'
    }
}

def get_random_pattern():
    """Get a random pattern for the signal"""
    import random
    pattern_key = random.choice(list(PATTERN_NAMES.keys()))
    return pattern_key, PATTERN_NAMES[pattern_key]

# Enhanced HUD template with proper Telegram WebApp integration
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="format-detection" content="telephone=no">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>BITTEN {{ tier|upper }} Mission Brief</title>
    
    <!-- CRITICAL: Telegram WebApp Script MUST be first -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            background-color: {{ colors.background }};
            color: {{ colors.secondary }};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            overflow-x: hidden;
            min-height: 100vh;
            /* Prevent rubber band scrolling on iOS */
            position: fixed;
            width: 100%;
            height: 100%;
            overflow: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        /* Telegram WebApp specific styles */
        body.telegram-webapp {
            padding-top: env(safe-area-inset-top);
            padding-bottom: env(safe-area-inset-bottom);
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
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
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
            cursor: pointer;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            user-select: none;
        }
        
        .back-button:hover,
        .back-button:active {
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
            position: relative;
        }
        
        /* Trophy room link */
        .trophy-link {
            position: absolute;
            bottom: -20px;
            right: 20px;
            font-size: 11px;
            color: {{ colors.primary }};
            text-decoration: none;
            opacity: 0.7;
            transition: opacity 0.3s;
        }
        
        .trophy-link:hover {
            opacity: 1;
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
        
        /* Ammo display */
        .ammo-display {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .ammo-icon {
            width: 20px;
            height: 20px;
            background: {{ colors.accent }};
            clip-path: polygon(40% 0%, 60% 0%, 60% 60%, 100% 60%, 100% 100%, 0% 100%, 0% 60%, 40% 60%);
            opacity: 0.8;
        }
        
        .ammo-icon.empty {
            background: rgba(255,255,255,0.2);
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
        
        /* Squad engagement display */
        .squad-status {
            background: rgba({{ colors.primary }}, 0.1);
            border: 1px solid {{ colors.primary }};
            border-radius: 4px;
            padding: 8px 16px;
            margin: 20px;
            text-align: center;
            font-weight: bold;
            letter-spacing: 1px;
        }
        
        .squad-percentage {
            font-size: 24px;
            color: {{ colors.primary }};
        }
        
        /* Main Content */
        .content {
            max-width: 600px;
            margin: 0 auto;
            padding: 0 20px 20px;
            padding-bottom: calc(20px + env(safe-area-inset-bottom));
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
        
        .param-value.masked {
            font-family: monospace;
            letter-spacing: 1px;
        }
        
        /* Dollar value display */
        .dollar-value {
            font-size: 14px;
            color: rgba(255,255,255,0.6);
            margin-top: 4px;
        }
        
        /* Action Buttons */
        .actions {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        /* Tactical Fire Button */
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
            position: relative;
            overflow: hidden;
            animation: tactical-pulse 2s ease-in-out infinite;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            user-select: none;
        }
        
        @keyframes tactical-pulse {
            0% { box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
            50% { box-shadow: 0 4px 25px {{ colors.danger }}, 0 0 30px rgba(255,255,255,0.2); }
            100% { box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        }
        
        .fire-button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
            transform: translate(-50%, -50%) scale(0);
            transition: transform 0.5s;
        }
        
        .fire-button:hover::before,
        .fire-button:active::before {
            transform: translate(-50%, -50%) scale(2);
        }
        
        .fire-button:hover,
        .fire-button:active {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }
        
        .fire-button:disabled {
            animation: none;
            opacity: 0.5;
            cursor: not-allowed;
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
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            user-select: none;
        }
        
        .skip-button:hover,
        .skip-button:active {
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
        
        .bottom-links a:hover,
        .bottom-links a:active {
            background: {{ colors.primary }};
            color: {{ colors.background }};
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
            body {
                font-size: 14px;
            }
            
            .stats-bar {
                flex-direction: column;
                gap: 15px;
                padding-bottom: 25px;
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
            
            .bottom-links {
                flex-direction: column;
            }
            
            .bottom-links a {
                width: 100%;
                text-align: center;
                justify-content: center;
            }
            
            .pair-direction {
                font-size: 24px;
            }
            
            .tcs-score {
                font-size: 36px;
            }
            
            .mission-card {
                padding: 20px;
            }
        }
        
        /* Setup Intel Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
        }
        
        .modal-content {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: {{ colors.surface }};
            border: 2px solid {{ colors.border }};
            border-radius: 8px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 0 30px rgba(0,0,0,0.8);
        }
        
        .modal-header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .modal-title {
            font-size: 24px;
            font-weight: bold;
            color: {{ colors.primary }};
            letter-spacing: 2px;
        }
        
        .pattern-visual {
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            font-family: monospace;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .pattern-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        
        .pattern-stat {
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 4px;
            padding: 15px;
            text-align: center;
        }
        
        .pattern-stat-label {
            font-size: 11px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .pattern-stat-value {
            font-size: 18px;
            font-weight: bold;
            color: {{ colors.secondary }};
        }
        
        .close-button {
            background: {{ colors.primary }};
            color: {{ colors.background }};
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 20px;
            width: 100%;
        }
        
        .close-button:hover,
        .close-button:active {
            opacity: 0.8;
        }
        
        /* Loading state */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: {{ colors.background }};
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        }
        
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: {{ colors.primary }};
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- Loading overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner"></div>
    </div>
    
    <!-- Setup Intel Modal -->
    <div class="modal-overlay" id="setupModal" onclick="hideSetupIntel()">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div class="modal-title">{{ pattern.name }} INTEL</div>
            </div>
            
            <div class="pattern-visual">
                {% if pattern_key == 'LONDON_RAID' %}
                ┌─────────────────────────┐<br>
                │  BREAKOUT ZONE          │<br>
                │  ═══════════════ ← BUY  │<br>
                │         ┊               │<br>
                │   RANGE ┊               │<br>
                │         ┊               │<br>
                │  ═══════════════ ← SELL │<br>
                └─────────────────────────┘
                {% elif pattern_key == 'WALL_BREACH' %}
                    ↑<br>
                ────┼──── RESISTANCE<br>
                    │  /<br>
                    │ /<br>
                    │/<br>
                ────● BREACH POINT<br>
                {% elif pattern_key == 'SNIPER_NEST' %}
                ┌─────────────────────────┐<br>
                │  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔ TOP    │<br>
                │    ↓        ↑          │<br>
                │     \      /           │<br>
                │      \    /            │<br>
                │       \  /             │<br>
                │  ▁▁▁▁▁▁▁▁▁▁▁▁▁▁ BOTTOM │<br>
                └─────────────────────────┘
                {% else %}
                    [CLASSIFIED PATTERN]<br>
                    Access Level Required
                {% endif %}
            </div>
            
            <div class="pattern-stats">
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Success Rate</div>
                    <div class="pattern-stat-value" style="color: {{ colors.success }};">{{ pattern.success_rate }}%</div>
                </div>
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Risk Level</div>
                    <div class="pattern-stat-value" style="color: {% if pattern.risk_level == 'HIGH' %}{{ colors.danger }}{% elif pattern.risk_level == 'MODERATE' %}{{ colors.accent }}{% else %}{{ colors.success }}{% endif %};">{{ pattern.risk_level }}</div>
                </div>
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Best Time</div>
                    <div class="pattern-stat-value">{{ pattern.best_time }}</div>
                </div>
                <div class="pattern-stat">
                    <div class="pattern-stat-label">Avg Pips</div>
                    <div class="pattern-stat-value">45-60</div>
                </div>
            </div>
            
            <div style="color: rgba(255,255,255,0.8); line-height: 1.6; margin-top: 20px;">
                <strong>How to Trade:</strong><br>
                {{ pattern.description }}. Wait for clear confirmation before entry. Always respect your stop loss and take profit levels. This setup works best during {{ pattern.best_time }}.
            </div>
            
            <button class="close-button" onclick="hideSetupIntel()">UNDERSTOOD</button>
        </div>
    </div>
    
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
            <div class="stat-label">Shots Left</div>
            <div class="stat-value">
                <div class="ammo-display">
                    {% for i in range(6) %}
                        <div class="ammo-icon {% if i >= user_stats.trades_remaining %}empty{% endif %}"></div>
                    {% endfor %}
                </div>
            </div>
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
        
        <a href="/me/{{ user_id }}" class="trophy-link" target="_blank">View Trophy Room →</a>
    </div>
    
    <!-- Squad Engagement Status -->
    <div class="squad-status">
        <span>SQUAD ENGAGEMENT: </span>
        <span class="squad-percentage">{{ user_stats.squad_engagement }}%</span>
    </div>
    
    <div class="content">
        <div class="mission-card">
            <div class="mission-header">
                <div class="signal-type">{{ pattern.name }}</div>
                <div class="pair-direction">
                    {{ symbol }} {{ direction }}
                </div>
                <div style="font-size: 14px; color: rgba(255,255,255,0.6); margin-top: 8px;">
                    {{ pattern.description }}
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
                        <span class="highlight">⚠️ No ammo left!</span> Reload tomorrow.
                    {% elif tcs_score >= 85 and user_stats.win_rate >= 70 %}
                        <span class="highlight">🔥 Strong signal + Good form = GO!</span>
                    {% elif tcs_score >= 85 and user_stats.win_rate < 70 %}
                        <span class="highlight">🎯 High confidence signal.</span> Trust the process.
                    {% elif tcs_score < 75 and user_stats.trades_remaining <= 2 %}
                        <span class="highlight">💭 Low score.</span> Save ammo for better targets?
                    {% elif user_stats.streak <= -3 %}
                        <span class="highlight">🛡️ Rough patch.</span> Maybe take a break?
                    {% else %}
                        You have <span class="highlight">{{ user_stats.trades_remaining }} shots</span> remaining.
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
                    <div class="param-value masked">{{ entry_masked }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Stop Loss</div>
                    <div class="param-value negative masked">{{ sl_masked }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Take Profit</div>
                    <div class="param-value positive masked">{{ tp_masked }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Risk/Reward</div>
                    <div class="param-value">1:{{ rr_ratio }}</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Risk</div>
                    <div class="param-value">{{ sl_pips }} pips</div>
                    <div class="dollar-value">(${{ sl_dollars }})</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Reward</div>
                    <div class="param-value positive">{{ tp_pips }} pips</div>
                    <div class="dollar-value positive">(${{ tp_dollars }})</div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="actions">
                <button class="fire-button" onclick="fireSignal()" {% if user_stats.trades_remaining <= 0 %}disabled{% endif %}>
                    🎯 EXECUTE MISSION
                </button>
                <button class="skip-button" onclick="skipSignal()">
                    Stand Down
                </button>
            </div>
            
            <!-- Bottom Links -->
            <div class="bottom-links">
                <a href="#" onclick="showSetupIntel(); return false;">
                    <span>📖</span>
                    <span>Setup Intel</span>
                </a>
                <a href="/notebook/{{ user_id }}" onclick="openLink(event, this.href)">
                    <span>📓</span>
                    <span>Norman's Notebook</span>
                </a>
                <a href="/stats/{{ user_id }}" onclick="openLink(event, this.href)">
                    <span>📊</span>
                    <span>Stats & History</span>
                </a>
                <a href="/education/{{ user_stats.tier }}" onclick="openLink(event, this.href)">
                    <span>📚</span>
                    <span>Training</span>
                </a>
            </div>
        </div>
    </div>
    
    <script>
        // Telegram WebApp initialization
        let tg = null;
        let webAppReady = false;
        
        // Initialize Telegram WebApp
        function initTelegramWebApp() {
            try {
                if (window.Telegram && window.Telegram.WebApp) {
                    tg = window.Telegram.WebApp;
                    
                    // Add class to body for specific styling
                    document.body.classList.add('telegram-webapp');
                    
                    // Initialize WebApp
                    tg.ready();
                    
                    // Set theme colors
                    tg.setHeaderColor(tg.themeParams.bg_color || '#000000');
                    tg.setBackgroundColor(tg.themeParams.bg_color || '#0A0A0A');
                    
                    // Expand to full height
                    tg.expand();
                    
                    // Enable closing confirmation
                    tg.enableClosingConfirmation();
                    
                    // Set up back button
                    if (tg.BackButton) {
                        tg.BackButton.show();
                        tg.BackButton.onClick(() => {
                            exitBriefing();
                        });
                    }
                    
                    // Log initialization
                    console.log('Telegram WebApp initialized:', {
                        version: tg.version,
                        platform: tg.platform,
                        colorScheme: tg.colorScheme,
                        isExpanded: tg.isExpanded
                    });
                    
                    webAppReady = true;
                }
            } catch (error) {
                console.error('Error initializing Telegram WebApp:', error);
            }
            
            // Hide loading overlay after initialization
            setTimeout(() => {
                document.getElementById('loadingOverlay').style.display = 'none';
            }, 500);
        }
        
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initTelegramWebApp);
        } else {
            initTelegramWebApp();
        }
        
        // Exit briefing
        function exitBriefing() {
            if (tg && webAppReady) {
                // Disable closing confirmation before closing
                tg.disableClosingConfirmation();
                tg.close();
            } else {
                // Fallback for non-Telegram environment
                window.close();
                setTimeout(() => {
                    window.location.href = 'https://t.me/BittenCommander';
                }, 100);
            }
        }
        
        // Fire signal
        function fireSignal() {
            // Check if user has trades remaining
            if ({{ user_stats.trades_remaining }} <= 0) {
                if (tg && webAppReady) {
                    tg.showAlert('No ammo left! Reload tomorrow, soldier.');
                } else {
                    alert('No ammo left! Reload tomorrow, soldier.');
                }
                return;
            }
            
            // Prepare data to send back
            const signalData = {
                action: 'fire',
                signal_id: '{{ signal_id }}',
                symbol: '{{ symbol }}',
                direction: '{{ direction }}',
                entry: '{{ entry }}',
                sl: '{{ sl }}',
                tp: '{{ tp }}',
                timestamp: Date.now()
            };
            
            // Send data back to bot
            if (tg && webAppReady) {
                tg.sendData(JSON.stringify(signalData));
            }
            
            // Visual feedback
            const fireBtn = document.querySelector('.fire-button');
            fireBtn.textContent = '✅ FIRED!';
            fireBtn.disabled = true;
            
            // Haptic feedback if available
            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }
            
            // Close after delay
            setTimeout(exitBriefing, 1500);
        }
        
        // Skip signal
        function skipSignal() {
            const skipData = {
                action: 'skip',
                signal_id: '{{ signal_id }}',
                timestamp: Date.now()
            };
            
            if (tg && webAppReady) {
                // Haptic feedback
                if (tg.HapticFeedback) {
                    tg.HapticFeedback.impactOccurred('light');
                }
                tg.sendData(JSON.stringify(skipData));
            }
            
            exitBriefing();
        }
        
        // Open links in Telegram WebApp
        function openLink(event, url) {
            event.preventDefault();
            
            if (tg && webAppReady) {
                // Open in Telegram's browser
                tg.openLink(url);
            } else {
                // Fallback for non-Telegram environment
                window.open(url, '_blank');
            }
            
            return false;
        }
        
        // Show Setup Intel modal
        function showSetupIntel() {
            document.getElementById('setupModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
            
            // Haptic feedback
            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('light');
            }
        }
        
        // Hide Setup Intel modal
        function hideSetupIntel() {
            document.getElementById('setupModal').style.display = 'none';
            document.body.style.overflow = 'auto';
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
                
                // Haptic feedback for expiration
                if (tg && tg.HapticFeedback) {
                    tg.HapticFeedback.notificationOccurred('error');
                }
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
            }
        }, 1000);
        {% endif %}
        
        // Handle viewport changes (keyboard, etc)
        if (tg && tg.onEvent) {
            tg.onEvent('viewportChanged', (isStateStable) => {
                if (isStateStable) {
                    // Viewport is stable, can adjust layout if needed
                    console.log('Viewport stable, height:', tg.viewportHeight);
                }
            });
        }
        
        // Prevent zoom on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (event) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Log any errors for debugging
        window.addEventListener('error', (event) => {
            console.error('WebApp Error:', event.error);
        });
    </script>
</body>
</html>
"""

# Keep other templates...
TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>BITTEN WebApp Test</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
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
        .info {
            background: rgba(0,255,0,0.1);
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 20px;
            margin: 20px auto;
            max-width: 500px;
            text-align: left;
        }
        .info div {
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <h1>🎯 BITTEN WebApp Test Page</h1>
    <div class="status">✅ WebApp is running!</div>
    <div>Server Time: {{ time }}</div>
    
    <div class="info" id="webappInfo">
        <h3>Telegram WebApp Info:</h3>
        <div id="webappStatus">Checking...</div>
    </div>
    
    <script>
        // Test Telegram WebApp integration
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            const info = document.getElementById('webappStatus');
            
            info.innerHTML = `
                <div>✅ WebApp API Available</div>
                <div>Version: ${tg.version}</div>
                <div>Platform: ${tg.platform}</div>
                <div>Color Scheme: ${tg.colorScheme}</div>
                <div>Is Expanded: ${tg.isExpanded}</div>
                <div>Viewport Height: ${tg.viewportHeight}</div>
            `;
            
            // Initialize
            tg.ready();
            tg.expand();
        } else {
            document.getElementById('webappStatus').innerHTML = '❌ Not running in Telegram WebApp';
        }
    </script>
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
            # If no data, show demo mode
            data = {
                'signal': {
                    'id': 'demo_signal',
                    'symbol': 'EUR/USD',
                    'direction': 'BUY',
                    'tcs_score': 87,
                    'entry': 1.0850,
                    'sl': 1.0830,
                    'tp': 1.0880,
                    'sl_pips': 20,
                    'tp_pips': 30,
                    'rr_ratio': 1.5,
                    'expiry': 600
                },
                'user_id': 'demo'
            }
        else:
            # Decode the data
            decoded_data = urllib.parse.unquote(encoded_data)
            data = json.loads(decoded_data)
        
        # Extract signal data
        signal = data.get('signal', data)  # Support both nested and flat structure
        
        # Get user stats (mock for now, would get from database)
        user_id = data.get('user_id', signal.get('user_id', 'demo'))
        user_stats = get_user_stats(user_id)
        
        # Get random pattern for this signal
        pattern_key, pattern = get_random_pattern()
        
        # Calculate dollar values
        sl_dollars = calculate_dollar_value(signal.get('sl_pips', signal.get('risk_pips', 20)))
        tp_dollars = calculate_dollar_value(signal.get('tp_pips', signal.get('reward_pips', 30)))
        
        # Mask prices
        entry_masked = mask_price(signal.get('entry', signal.get('entry_price', 0)))
        sl_masked = mask_price(signal.get('sl', signal.get('stop_loss', 0)))
        tp_masked = mask_price(signal.get('tp', signal.get('take_profit', 0)))
        
        # Prepare template variables
        context = {
            'user_id': user_id,
            'user_stats': user_stats,
            'signal_id': signal.get('id', signal.get('signal_id', 'unknown')),
            'signal_type': signal.get('signal_type', signal.get('fire_mode', 'STANDARD')),
            'symbol': signal.get('symbol', 'UNKNOWN'),
            'direction': signal.get('direction', 'BUY'),
            'tcs_score': signal.get('tcs_score', signal.get('confidence', 0)),
            'entry': signal.get('entry', signal.get('entry_price', 0)),
            'sl': signal.get('sl', signal.get('stop_loss', 0)),
            'tp': signal.get('tp', signal.get('take_profit', 0)),
            'entry_masked': entry_masked,
            'sl_masked': sl_masked,
            'tp_masked': tp_masked,
            'sl_pips': signal.get('sl_pips', signal.get('risk_pips', 0)),
            'tp_pips': signal.get('tp_pips', signal.get('reward_pips', 0)),
            'sl_dollars': sl_dollars,
            'tp_dollars': tp_dollars,
            'rr_ratio': signal.get('rr_ratio', round(tp_dollars / sl_dollars, 1) if sl_dollars > 0 else 0),
            'expiry_seconds': signal.get('expiry', signal.get('expires_at', 0)) - int(datetime.now().timestamp()) if signal.get('expires_at') else signal.get('expiry', 600),
            'colors': get_tier_styles(user_stats['tier']),
            'pattern_key': pattern_key,
            'pattern': pattern,
            'tier': user_stats['tier']
        }
        
        return render_template_string(HUD_TEMPLATE, **context)
        
    except Exception as e:
        return f"Error processing mission data: {str(e)}", 400

# Keep all other routes the same...
@app.route('/notebook/<user_id>')
def notebook(user_id):
    """Norman's Trading Notebook"""
    colors = get_tier_styles('nibbler')  # Default colors
    
    NOTEBOOK_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Norman's Trading Notebook</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background: #0a0a0a;
                color: #ffffff;
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
                color: #FFD700;
            }
            .entry {
                background: #1a1a1a;
                border: 1px solid #FFD700;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .entry-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                color: #00D9FF;
            }
            .entry-content {
                line-height: 1.6;
            }
            .mood {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            .mood.positive { background: #4ECDC4; color: #000; }
            .mood.negative { background: #FF6B6B; color: #000; }
            .mood.neutral { background: #FFD700; color: #000; }
            .back-link {
                color: #00D9FF;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="#" class="back-link" onclick="window.close(); return false;">← Back</a>
            <h1 class="header">📓 Norman's Trading Notebook</h1>
            
            <div class="entry">
                <div class="entry-header">
                    <span>Today's Reflection</span>
                    <span class="mood positive">CONFIDENT</span>
                </div>
                <div class="entry-content">
                    Remember, every loss is a lesson. Every win is proof that the system works.
                    Today you showed discipline by waiting for high TCS signals. Keep it up!
                </div>
            </div>
            
            <div class="entry">
                <div class="entry-header">
                    <span>Yesterday</span>
                    <span class="mood neutral">LEARNING</span>
                </div>
                <div class="entry-content">
                    That EUR/USD loss hurt, but you stuck to your stop loss. That's growth.
                    The market will always be there tomorrow. Your capital won't if you revenge trade.
                </div>
            </div>
            
            <div class="entry">
                <div class="entry-header">
                    <span>Last Week Summary</span>
                    <span class="mood positive">IMPROVING</span>
                </div>
                <div class="entry-content">
                    5 wins, 2 losses. More importantly, you followed every rule.
                    You're becoming the trader you always wanted to be. One trade at a time.
                </div>
            </div>
        </div>
        
        <script>
            // Initialize Telegram WebApp if available
            if (window.Telegram && window.Telegram.WebApp) {
                const tg = window.Telegram.WebApp;
                tg.ready();
                tg.expand();
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(NOTEBOOK_TEMPLATE)

@app.route('/stats/<user_id>')
def stats_and_history(user_id):
    """Combined stats and trade history page"""
    colors = get_tier_styles('nibbler')
    
    STATS_HISTORY_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stats & Trade History</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background: #0a0a0a;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                color: #00D9FF;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            .stat-card {
                background: #1a1a1a;
                border: 1px solid #00D9FF;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
            }
            .stat-title {
                font-size: 12px;
                color: rgba(255,255,255,0.6);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            .stat-value {
                font-size: 28px;
                font-weight: bold;
                color: #00D9FF;
            }
            .stat-value.positive { color: #4ECDC4; }
            .stat-value.negative { color: #FF6B6B; }
            .history-section {
                background: #1a1a1a;
                border: 1px solid #FFD700;
                border-radius: 8px;
                padding: 20px;
            }
            .history-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 20px;
                border-bottom: 1px solid rgba(255,255,255,0.2);
            }
            .filter-buttons {
                display: flex;
                gap: 10px;
            }
            .filter-btn {
                background: transparent;
                color: #FFD700;
                border: 1px solid #FFD700;
                padding: 6px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
            }
            .filter-btn:hover,
            .filter-btn.active {
                background: #FFD700;
                color: #000;
            }
            .trade-table {
                width: 100%;
                border-collapse: collapse;
            }
            .trade-table th {
                text-align: left;
                padding: 12px;
                color: #FFD700;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                border-bottom: 2px solid #FFD700;
            }
            .trade-table td {
                padding: 12px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .trade-table tr:hover {
                background: rgba(255,255,255,0.05);
            }
            .pattern-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                background: rgba(0,217,255,0.2);
                color: #00D9FF;
                text-transform: uppercase;
            }
            .result-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            .result-badge.win {
                background: rgba(78,205,196,0.2);
                color: #4ECDC4;
            }
            .result-badge.loss {
                background: rgba(255,107,107,0.2);
                color: #FF6B6B;
            }
            .back-link {
                color: #00D9FF;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }
            .scroll-container {
                max-height: 400px;
                overflow-y: auto;
            }
            .scroll-container::-webkit-scrollbar {
                width: 8px;
            }
            .scroll-container::-webkit-scrollbar-track {
                background: rgba(0,0,0,0.3);
            }
            .scroll-container::-webkit-scrollbar-thumb {
                background: #FFD700;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="#" class="back-link" onclick="window.close(); return false;">← Back</a>
            <h1 class="header">📊 Trading Statistics & History</h1>
            
            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">Total Trades</div>
                    <div class="stat-value">127</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Win Rate</div>
                    <div class="stat-value positive">75%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Profit Factor</div>
                    <div class="stat-value positive">2.3</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Total P&L</div>
                    <div class="stat-value positive">+24.3%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Best Streak</div>
                    <div class="stat-value">W7</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Avg Risk:Reward</div>
                    <div class="stat-value">1:2.1</div>
                </div>
            </div>
            
            <!-- Pattern Performance -->
            <div class="stats-grid" style="margin-bottom: 40px;">
                <div class="stat-card">
                    <div class="stat-title">Best Pattern</div>
                    <div class="stat-value" style="font-size: 16px;">WALL BREACH</div>
                    <div style="color: #4ECDC4; margin-top: 5px;">82% Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Most Traded</div>
                    <div class="stat-value" style="font-size: 16px;">LONDON RAID</div>
                    <div style="color: rgba(255,255,255,0.6); margin-top: 5px;">34 Trades</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Avoid Pattern</div>
                    <div class="stat-value" style="font-size: 16px;">PINCER MOVE</div>
                    <div style="color: #FF6B6B; margin-top: 5px;">45% Win Rate</div>
                </div>
            </div>
            
            <!-- Trade History -->
            <div class="history-section">
                <div class="history-header">
                    <h2 style="color: #FFD700; margin: 0;">Trade History</h2>
                    <div class="filter-buttons">
                        <button class="filter-btn active" onclick="filterTrades('all')">All</button>
                        <button class="filter-btn" onclick="filterTrades('wins')">Wins</button>
                        <button class="filter-btn" onclick="filterTrades('losses')">Losses</button>
                        <button class="filter-btn" onclick="filterTrades('today')">Today</button>
                    </div>
                </div>
                
                <div class="scroll-container">
                    <table class="trade-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Pair</th>
                                <th>Pattern</th>
                                <th>Direction</th>
                                <th>Result</th>
                                <th>P&L</th>
                            </tr>
                        </thead>
                        <tbody id="tradeTableBody">
                            <tr>
                                <td>Today 14:23</td>
                                <td>EUR/USD</td>
                                <td><span class="pattern-badge">LONDON RAID</span></td>
                                <td>BUY</td>
                                <td><span class="result-badge win">WIN +42</span></td>
                                <td style="color: #4ECDC4;">+2.1%</td>
                            </tr>
                            <tr>
                                <td>Today 10:15</td>
                                <td>GBP/USD</td>
                                <td><span class="pattern-badge">WALL BREACH</span></td>
                                <td>SELL</td>
                                <td><span class="result-badge win">WIN +38</span></td>
                                <td style="color: #4ECDC4;">+1.9%</td>
                            </tr>
                            <tr>
                                <td>Today 08:45</td>
                                <td>USD/JPY</td>
                                <td><span class="pattern-badge">SNIPER'S NEST</span></td>
                                <td>BUY</td>
                                <td><span class="result-badge loss">LOSS -20</span></td>
                                <td style="color: #FF6B6B;">-1.0%</td>
                            </tr>
                            <tr>
                                <td>Yesterday 16:30</td>
                                <td>EUR/USD</td>
                                <td><span class="pattern-badge">SUPPLY DROP</span></td>
                                <td>BUY</td>
                                <td><span class="result-badge win">WIN +55</span></td>
                                <td style="color: #4ECDC4;">+2.8%</td>
                            </tr>
                            <tr>
                                <td>Yesterday 12:20</td>
                                <td>AUD/USD</td>
                                <td><span class="pattern-badge">AMBUSH POINT</span></td>
                                <td>SELL</td>
                                <td><span class="result-badge win">WIN +35</span></td>
                                <td style="color: #4ECDC4;">+1.8%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            // Initialize Telegram WebApp if available
            if (window.Telegram && window.Telegram.WebApp) {
                const tg = window.Telegram.WebApp;
                tg.ready();
                tg.expand();
            }
            
            function filterTrades(filter) {
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                // In a real app, this would filter the table
                console.log('Filter by:', filter);
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(STATS_HISTORY_TEMPLATE)

@app.route('/me/<user_id>')
def trophy_room(user_id):
    """User's trophy room / profile"""
    colors = get_tier_styles('nibbler')
    
    TROPHY_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trophy Room</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background: #0a0a0a;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                margin: 0;
                padding: 20px;
                text-align: center;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
            }
            .header {
                color: #FFD700;
                margin-bottom: 40px;
            }
            .trophy-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 40px;
            }
            .trophy {
                background: #1a1a1a;
                border: 2px solid #FFD700;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
            }
            .trophy-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            .trophy-name {
                font-size: 14px;
                font-weight: bold;
                color: #FFD700;
            }
            .stats-section {
                background: #1a1a1a;
                border: 1px solid #00D9FF;
                border-radius: 8px;
                padding: 30px;
                text-align: left;
            }
            .stat-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .stat-label {
                color: rgba(255,255,255,0.7);
            }
            .stat-value {
                font-weight: bold;
                color: #00D9FF;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🏆 Trophy Room</h1>
            
            <div class="trophy-grid">
                <div class="trophy">
                    <div class="trophy-icon">🎯</div>
                    <div class="trophy-name">Sharpshooter</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">🔥</div>
                    <div class="trophy-name">Hot Streak</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">💎</div>
                    <div class="trophy-name">Diamond Hands</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">📈</div>
                    <div class="trophy-name">Profit Master</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">🛡️</div>
                    <div class="trophy-name">Risk Guardian</div>
                </div>
                <div class="trophy">
                    <div class="trophy-icon">⚡</div>
                    <div class="trophy-name">Quick Draw</div>
                </div>
            </div>
            
            <div class="stats-section">
                <h2 style="color: #FFD700; text-align: center; margin-bottom: 30px;">Career Stats</h2>
                <div class="stat-row">
                    <span class="stat-label">Total Trades</span>
                    <span class="stat-value">127</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Win Rate</span>
                    <span class="stat-value">75%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Best Streak</span>
                    <span class="stat-value">W7</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total P&L</span>
                    <span class="stat-value">+24.3%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Member Since</span>
                    <span class="stat-value">3 months ago</span>
                </div>
            </div>
        </div>
        
        <script>
            // Initialize Telegram WebApp if available
            if (window.Telegram && window.Telegram.WebApp) {
                const tg = window.Telegram.WebApp;
                tg.ready();
                tg.expand();
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(TROPHY_TEMPLATE)

@app.route('/education/<tier>')
def education(tier):
    """Education/training page matching HUD style"""
    colors = get_tier_styles(tier)
    
    # Education content with pattern focus
    education_content = {
        'nibbler': {
            'title': 'NIBBLER TRAINING ACADEMY',
            'tier': 'nibbler',
            'modules': [
                {'name': 'Basic Patterns Recognition', 'progress': 75, 'completed_lessons': 6, 'total_lessons': 8},
                {'name': 'Risk Management Fundamentals', 'progress': 100, 'completed_lessons': 5, 'total_lessons': 5},
                {'name': 'Trading Psychology', 'progress': 30, 'completed_lessons': 3, 'total_lessons': 10}
            ],
            'pattern_mastery': {
                'LONDON_RAID': 65,
                'WALL_BREACH': 80,
                'SNIPER_NEST': 45,
                'SUPPLY_DROP': 70
            },
            'next_lesson': 'Understanding AMBUSH POINT Patterns',
            'achievements': ['First Trade', 'Week Warrior', 'Discipline Badge']
        },
        'fang': {
            'title': 'FANG ADVANCED TRAINING',
            'tier': 'fang',
            'modules': [
                {'name': 'Advanced Pattern Analysis', 'progress': 60, 'completed_lessons': 12, 'total_lessons': 20},
                {'name': 'Multi-Timeframe Confluence', 'progress': 40, 'completed_lessons': 8, 'total_lessons': 20},
                {'name': 'Momentum Trading Mastery', 'progress': 80, 'completed_lessons': 16, 'total_lessons': 20}
            ],
            'pattern_mastery': {
                'LONDON_RAID': 85,
                'WALL_BREACH': 90,
                'SNIPER_NEST': 75,
                'AMBUSH_POINT': 60,
                'SUPPLY_DROP': 88,
                'PINCER_MOVE': 50
            },
            'next_lesson': 'Advanced PINCER MOVE Strategies',
            'achievements': ['Pattern Master', 'Sniper Elite', '100 Trade Veteran']
        }
    }
    
    content = education_content.get(tier.lower(), education_content['nibbler'])
    
    # Enhanced education template matching HUD style
    EDUCATION_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ content.title }}</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
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
            
            /* Top Navigation Bar - Same as HUD */
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
            
            /* Main Content */
            .content {
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }
            
            /* Header Section */
            .header-section {
                text-align: center;
                margin-bottom: 40px;
                padding: 30px;
                background: {{ colors.surface }};
                border: 2px solid {{ colors.border }};
                border-radius: 8px;
            }
            
            .page-title {
                font-size: 32px;
                font-weight: bold;
                color: {{ colors.primary }};
                letter-spacing: 3px;
                text-shadow: 0 0 10px {{ colors.primary }};
                margin-bottom: 20px;
            }
            
            /* Progress Overview */
            .overview-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            
            .overview-card {
                background: rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s;
            }
            
            .overview-card:hover {
                transform: translateY(-2px);
                border-color: {{ colors.primary }};
            }
            
            .overview-label {
                font-size: 11px;
                color: rgba(255,255,255,0.6);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }
            
            .overview-value {
                font-size: 28px;
                font-weight: bold;
                color: {{ colors.primary }};
            }
            
            /* Modules Section */
            .modules-section {
                margin-bottom: 40px;
            }
            
            .section-title {
                font-size: 24px;
                color: {{ colors.accent }};
                margin-bottom: 20px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .module-card {
                background: {{ colors.surface }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                padding: 25px;
                margin-bottom: 20px;
                transition: all 0.3s;
            }
            
            .module-card:hover {
                border-color: {{ colors.primary }};
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }
            
            .module-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .module-name {
                font-size: 18px;
                font-weight: bold;
                color: {{ colors.secondary }};
            }
            
            .module-stats {
                font-size: 14px;
                color: rgba(255,255,255,0.6);
            }
            
            .progress-container {
                background: rgba(0,0,0,0.8);
                border-radius: 8px;
                padding: 4px;
                margin-bottom: 10px;
            }
            
            .progress-bar {
                background: rgba(255,255,255,0.1);
                height: 12px;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .progress-fill {
                background: {{ colors.primary }};
                height: 100%;
                transition: width 0.5s ease;
                box-shadow: 0 0 10px {{ colors.primary }};
            }
            
            .progress-text {
                text-align: center;
                margin-top: 8px;
                font-size: 14px;
                color: {{ colors.primary }};
                font-weight: bold;
            }
            
            /* Pattern Mastery Section */
            .pattern-mastery {
                background: rgba(0,0,0,0.8);
                border: 2px solid {{ colors.border }};
                border-radius: 8px;
                padding: 30px;
                margin-bottom: 40px;
            }
            
            .pattern-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .pattern-item {
                background: {{ colors.surface }};
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s;
            }
            
            .pattern-item:hover {
                transform: translateY(-2px);
                border-color: {{ colors.primary }};
            }
            
            .pattern-name {
                font-size: 14px;
                font-weight: bold;
                color: {{ colors.accent }};
                margin-bottom: 10px;
                text-transform: uppercase;
            }
            
            .mastery-circle {
                width: 80px;
                height: 80px;
                margin: 0 auto 10px;
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: conic-gradient(
                    {{ colors.primary }} 0deg,
                    {{ colors.primary }} calc(var(--progress) * 3.6deg),
                    rgba(255,255,255,0.1) calc(var(--progress) * 3.6deg)
                );
            }
            
            .mastery-value {
                position: absolute;
                font-size: 24px;
                font-weight: bold;
                color: {{ colors.secondary }};
            }
            
            /* Next Lesson Card */
            .next-lesson-card {
                background: linear-gradient(135deg, {{ colors.primary }}, {{ colors.accent }});
                color: {{ colors.background }};
                padding: 30px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 40px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }
            
            .next-lesson-title {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .next-lesson-name {
                font-size: 24px;
                margin-bottom: 20px;
            }
            
            .start-button {
                background: {{ colors.background }};
                color: {{ colors.primary }};
                border: none;
                padding: 15px 40px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 2px;
                transition: all 0.3s;
            }
            
            .start-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }
            
            /* Achievements Section */
            .achievements-section {
                margin-bottom: 40px;
            }
            
            .achievement-list {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .achievement-badge {
                background: rgba({{ colors.accent }}, 0.2);
                border: 1px solid {{ colors.accent }};
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
                color: {{ colors.accent }};
            }
            
            /* Mobile Responsive */
            @media (max-width: 600px) {
                .overview-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .pattern-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .module-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }
            }
        </style>
    </head>
    <body>
        <div class="top-bar">
            <a href="#" class="back-button" onclick="window.close(); return false;">
                <span>←</span>
                <span>Back</span>
            </a>
            <div class="tier-badge">{{ content.tier|upper }} TRAINING</div>
        </div>
        
        <div class="content">
            <!-- Header Section -->
            <div class="header-section">
                <h1 class="page-title">{{ content.title }}</h1>
                <div class="overview-grid">
                    <div class="overview-card">
                        <div class="overview-label">Total Progress</div>
                        <div class="overview-value">{{ ((content.modules|sum(attribute='progress')) / (content.modules|length))|round }}%</div>
                    </div>
                    <div class="overview-card">
                        <div class="overview-label">Patterns Learned</div>
                        <div class="overview-value">{{ content.pattern_mastery|length }}</div>
                    </div>
                    <div class="overview-card">
                        <div class="overview-label">Achievements</div>
                        <div class="overview-value">{{ content.achievements|length }}</div>
                    </div>
                    <div class="overview-card">
                        <div class="overview-label">Training Hours</div>
                        <div class="overview-value">24.5</div>
                    </div>
                </div>
            </div>
            
            <!-- Training Modules -->
            <div class="modules-section">
                <h2 class="section-title">Training Modules</h2>
                {% for module in content.modules %}
                <div class="module-card">
                    <div class="module-header">
                        <h3 class="module-name">{{ module.name }}</h3>
                        <span class="module-stats">{{ module.completed_lessons }}/{{ module.total_lessons }} Lessons</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ module.progress }}%"></div>
                        </div>
                    </div>
                    <div class="progress-text">{{ module.progress }}% Complete</div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Pattern Mastery -->
            <div class="pattern-mastery">
                <h2 class="section-title">Pattern Mastery</h2>
                <div class="pattern-grid">
                    {% for pattern, mastery in content.pattern_mastery.items() %}
                    <div class="pattern-item">
                        <div class="pattern-name">{{ pattern.replace('_', ' ') }}</div>
                        <div class="mastery-circle" style="--progress: {{ mastery }}">
                            <div class="mastery-value">{{ mastery }}%</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Next Lesson -->
            <div class="next-lesson-card">
                <h3 class="next-lesson-title">Next Lesson</h3>
                <div class="next-lesson-name">{{ content.next_lesson }}</div>
                <button class="start-button" onclick="alert('Lesson starting soon!')">START LESSON</button>
            </div>
            
            <!-- Achievements -->
            <div class="achievements-section">
                <h2 class="section-title">Recent Achievements</h2>
                <div class="achievement-list">
                    {% for achievement in content.achievements %}
                    <div class="achievement-badge">🏆 {{ achievement }}</div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <script>
            // Initialize Telegram WebApp if available
            if (window.Telegram && window.Telegram.WebApp) {
                const tg = window.Telegram.WebApp;
                tg.ready();
                tg.expand();
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(EDUCATION_TEMPLATE, content=content, colors=colors)

# Add more endpoints as needed...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)