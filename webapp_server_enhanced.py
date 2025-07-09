#!/usr/bin/env python3
"""Enhanced Flask server with improved HUD effects and trading focus"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import json
import urllib.parse
import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# Enhanced color schemes with subtle glow effects
ENHANCED_TIER_STYLES = {
    'nibbler': {
        'primary': '#00D9FF',
        'primary_glow': '0 0 10px rgba(0, 217, 255, 0.5)',
        'secondary': '#FFFFFF',
        'accent': '#FFD700',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#00D9FF',
        'gradient': 'linear-gradient(135deg, #00D9FF 0%, #0099CC 100%)'
    },
    'fang': {
        'primary': '#FF8C00',
        'primary_glow': '0 0 10px rgba(255, 140, 0, 0.5)',
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FF8C00',
        'gradient': 'linear-gradient(135deg, #FF8C00 0%, #FF6600 100%)'
    },
    'commander': {
        'primary': '#FFD700',
        'primary_glow': '0 0 10px rgba(255, 215, 0, 0.5)',
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FFD700',
        'gradient': 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)'
    },
    'apex': {
        'primary': '#FF00FF',
        'primary_glow': '0 0 15px rgba(255, 0, 255, 0.5)',
        'secondary': '#FFFFFF',
        'accent': '#00D9FF',
        'background': '#0A0A0A',
        'surface': '#1A1A1A',
        'danger': '#FF6B6B',
        'success': '#4ECDC4',
        'border': '#FF00FF',
        'gradient': 'linear-gradient(135deg, #FF00FF 0%, #CC00CC 100%)'
    }
}

def get_tier_styles(tier):
    """Get enhanced color scheme for tier"""
    return ENHANCED_TIER_STYLES.get(tier.lower(), ENHANCED_TIER_STYLES['nibbler'])

def get_user_stats(user_id):
    """Get mock user stats with trading-focused metrics"""
    return {
        'gamertag': 'Soldier_X',
        'tier': 'nibbler',
        'level': 5,
        'xp': 1250,
        'xp_to_next': 2000,
        'trades_today': 3,
        'trades_remaining': 3,
        'win_rate': 75,
        'pnl_today': 2.4,
        'pnl_week': 8.7,
        'streak': 3,
        'best_streak': 7,
        'total_trades': 127,
        'winning_trades': 95,
        'avg_rr': 2.1,
        'avg_win': 42,  # pips
        'avg_loss': 20,  # pips
        'best_trade': 156,  # pips
        'consistency_score': 82  # New metric for consistent performance
    }

# Enhanced HUD template with subtle improvements
ENHANCED_HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN {{ tier|upper }} Mission Control</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background-color: {{ colors.background }};
            color: {{ colors.secondary }};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 16px;
            line-height: 1.6;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 20% 50%, rgba({{ colors.primary }}, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba({{ colors.accent }}, 0.03) 0%, transparent 50%);
        }
        
        /* Subtle animation for background */
        @keyframes subtle-shift {
            0%, 100% { background-position: 0% 0%; }
            50% { background-position: 100% 100%; }
        }
        
        body {
            animation: subtle-shift 30s ease-in-out infinite;
            background-size: 200% 200%;
        }
        
        /* Top Navigation Bar - Enhanced */
        .top-bar {
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
            transition: all 0.3s ease;
        }
        
        .back-button {
            color: {{ colors.primary }};
            text-decoration: none;
            padding: 10px 24px;
            border: 1.5px solid {{ colors.primary }};
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s ease;
            background: transparent;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            letter-spacing: 0.5px;
        }
        
        .back-button:hover {
            background: {{ colors.primary }};
            color: {{ colors.background }};
            transform: translateY(-1px);
            box-shadow: {{ colors.primary_glow }};
        }
        
        .tier-badge {
            background: {{ colors.gradient }};
            color: {{ colors.background }};
            padding: 10px 24px;
            border-radius: 6px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 13px;
            box-shadow: {{ colors.primary_glow }};
        }
        
        /* Enhanced Stats Bar */
        .stats-bar {
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            margin: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 20px;
            align-items: center;
        }
        
        .stat-item {
            text-align: center;
            transition: transform 0.2s ease;
        }
        
        .stat-item:hover {
            transform: translateY(-2px);
        }
        
        .stat-label {
            font-size: 11px;
            color: rgba(255,255,255,0.5);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .stat-value {
            font-size: 22px;
            font-weight: 700;
            color: {{ colors.secondary }};
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
        
        /* User info section */
        .user-section {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .gamertag {
            font-size: 20px;
            font-weight: 700;
            color: {{ colors.primary }};
        }
        
        .level-badge {
            background: rgba({{ colors.accent }}, 0.2);
            color: {{ colors.accent }};
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid {{ colors.accent }};
        }
        
        /* XP Progress Bar */
        .xp-progress {
            flex: 1;
            max-width: 300px;
        }
        
        .xp-label {
            font-size: 11px;
            color: rgba(255,255,255,0.5);
            margin-bottom: 4px;
            text-align: right;
        }
        
        .xp-bar {
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            overflow: hidden;
            position: relative;
        }
        
        .xp-fill {
            height: 100%;
            background: {{ colors.gradient }};
            width: {{ (user_stats.xp / user_stats.xp_to_next * 100)|round }}%;
            transition: width 0.3s ease;
            position: relative;
        }
        
        .xp-fill::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            width: 20px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-20px); }
            100% { transform: translateX(20px); }
        }
        
        /* Main Content */
        .content {
            max-width: 700px;
            margin: 0 auto;
            padding: 0 20px 20px;
        }
        
        /* Enhanced Mission Card */
        .mission-card {
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            position: relative;
            overflow: hidden;
        }
        
        .mission-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: {{ colors.gradient }};
            opacity: 0.8;
        }
        
        .mission-header {
            text-align: center;
            margin-bottom: 32px;
        }
        
        .signal-type {
            font-size: 14px;
            font-weight: 600;
            color: {{ colors.accent }};
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 8px;
            opacity: 0.8;
        }
        
        .pair-direction {
            font-size: 32px;
            font-weight: 900;
            color: {{ colors.secondary }};
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
        }
        
        .direction-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 20px;
            background: {{ colors.gradient }};
            color: {{ colors.background }};
            border-radius: 6px;
            font-size: 18px;
            font-weight: 700;
            box-shadow: {{ colors.primary_glow }};
        }
        
        .direction-badge.buy::before {
            content: '↗';
            font-size: 20px;
        }
        
        .direction-badge.sell::before {
            content: '↘';
            font-size: 20px;
        }
        
        /* Enhanced TCS Container */
        .tcs-container {
            background: rgba(0,0,0,0.8);
            border: 2px solid {% if tcs_score >= 85 %}{{ colors.success }}{% elif tcs_score >= 75 %}{{ colors.primary }}{% else %}{{ colors.danger }}{% endif %};
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .tcs-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
            animation: sweep 3s linear infinite;
        }
        
        @keyframes sweep {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .tcs-label {
            font-size: 12px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .tcs-score {
            font-size: 56px;
            font-weight: 900;
            color: {% if tcs_score >= 85 %}{{ colors.success }}{% elif tcs_score >= 75 %}{{ colors.primary }}{% else %}{{ colors.danger }}{% endif %};
            line-height: 1;
            margin: 12px 0;
            text-shadow: 0 0 20px rgba({% if tcs_score >= 85 %}76, 205, 196{% elif tcs_score >= 75 %}255, 215, 0{% else %}255, 107, 107{% endif %}, 0.3);
        }
        
        .confidence-label {
            font-size: 16px;
            font-weight: 600;
            color: {% if tcs_score >= 85 %}{{ colors.success }}{% elif tcs_score >= 75 %}{{ colors.primary }}{% else %}{{ colors.danger }}{% endif %};
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Performance Insights */
        .insights-box {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 16px;
            margin: 20px 0;
        }
        
        .insight-text {
            font-size: 14px;
            color: rgba(255,255,255,0.8);
            line-height: 1.6;
            text-align: center;
        }
        
        .insight-text .highlight {
            color: {{ colors.accent }};
            font-weight: 600;
        }
        
        /* Enhanced Timer */
        .timer {
            background: rgba(255,107,107,0.1);
            border: 1px solid {{ colors.danger }};
            border-radius: 8px;
            padding: 12px 20px;
            text-align: center;
            margin-bottom: 20px;
            font-size: 16px;
            font-weight: 600;
            color: {{ colors.danger }};
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
        }
        
        .timer-icon {
            animation: pulse 1s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(0.95); }
        }
        
        /* Enhanced Parameters Grid */
        .parameters {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }
        
        .param-box {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .param-box:hover {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }
        
        .param-label {
            font-size: 11px;
            color: rgba(255,255,255,0.5);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .param-value {
            font-size: 20px;
            font-weight: 700;
            color: {{ colors.secondary }};
        }
        
        .param-value.positive {
            color: {{ colors.success }};
        }
        
        .param-value.negative {
            color: {{ colors.danger }};
        }
        
        /* Enhanced Action Buttons */
        .actions {
            margin-top: 32px;
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }
        
        .fire-button {
            flex: 1;
            background: {{ colors.gradient }};
            color: white;
            border: none;
            padding: 16px 32px;
            font-size: 16px;
            font-weight: 700;
            border-radius: 8px;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2), {{ colors.primary_glow }};
            min-width: 180px;
            position: relative;
            overflow: hidden;
        }
        
        .fire-button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .fire-button:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .fire-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3), {{ colors.primary_glow }};
        }
        
        .fire-button:active {
            transform: translateY(0);
        }
        
        .fire-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .skip-button {
            flex: 1;
            background: transparent;
            color: rgba(255,255,255,0.6);
            border: 1.5px solid rgba(255,255,255,0.2);
            padding: 16px 32px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            letter-spacing: 0.5px;
        }
        
        .skip-button:hover {
            border-color: rgba(255,255,255,0.4);
            color: rgba(255,255,255,0.9);
            background: rgba(255,255,255,0.05);
        }
        
        /* Bottom Links */
        .bottom-links {
            margin-top: 40px;
            padding-top: 24px;
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: center;
            gap: 24px;
            flex-wrap: wrap;
        }
        
        .bottom-links a {
            color: rgba(255,255,255,0.6);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .bottom-links a:hover {
            color: {{ colors.primary }};
        }
        
        /* Focus styles for accessibility */
        button:focus,
        a:focus {
            outline: 2px solid {{ colors.accent }};
            outline-offset: 2px;
        }
        
        /* Mobile responsive */
        @media (max-width: 600px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
            }
            
            .user-section {
                flex-direction: column;
                gap: 16px;
                text-align: center;
            }
            
            .xp-progress {
                width: 100%;
            }
            
            .parameters {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .actions {
                flex-direction: column;
            }
            
            .mission-card {
                padding: 24px 16px;
            }
        }
        
        /* Loading state */
        .loading {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-left: 8px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="top-bar">
        <a href="#" class="back-button" onclick="exitBriefing(); return false;">
            <span>←</span>
            <span>Back to Telegram</span>
        </a>
        <div class="tier-badge">{{ user_stats.tier|upper }} TIER</div>
    </div>
    
    <!-- Enhanced Stats Bar -->
    <div class="stats-bar">
        <div class="stats-grid">
            <!-- User Section -->
            <div class="user-section">
                <div class="user-info">
                    <div class="gamertag">{{ user_stats.gamertag }}</div>
                    <div class="level-badge">LVL {{ user_stats.level }}</div>
                </div>
                <div class="xp-progress">
                    <div class="xp-label">{{ user_stats.xp }} / {{ user_stats.xp_to_next }} XP</div>
                    <div class="xp-bar">
                        <div class="xp-fill"></div>
                    </div>
                </div>
            </div>
            
            <!-- Trading Stats -->
            <div class="stat-item">
                <div class="stat-label">Today</div>
                <div class="stat-value">{{ user_stats.trades_today }}/6</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value {% if user_stats.win_rate >= 70 %}positive{% else %}warning{% endif %}">{{ user_stats.win_rate }}%</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Today's P&L</div>
                <div class="stat-value {% if user_stats.pnl_today >= 0 %}positive{% else %}negative{% endif %}">{{ "{:+.1f}".format(user_stats.pnl_today) }}%</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Week P&L</div>
                <div class="stat-value {% if user_stats.pnl_week >= 0 %}positive{% else %}negative{% endif %}">{{ "{:+.1f}".format(user_stats.pnl_week) }}%</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Streak</div>
                <div class="stat-value {% if user_stats.streak >= 3 %}positive{% elif user_stats.streak < 0 %}negative{% endif %}">
                    {% if user_stats.streak >= 0 %}W{{ user_stats.streak }}{% else %}L{{ -user_stats.streak }}{% endif %}
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">Avg R:R</div>
                <div class="stat-value">{{ user_stats.avg_rr }}</div>
            </div>
        </div>
    </div>
    
    <div class="content">
        <div class="mission-card">
            <div class="mission-header">
                <div class="signal-type">{{ signal_type|upper }} SIGNAL</div>
                <div class="pair-direction">
                    <span>{{ symbol }}</span>
                    <span class="direction-badge {{ direction|lower }}">{{ direction|upper }}</span>
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
            
            <!-- Performance Insights -->
            <div class="insights-box">
                <div class="insight-text">
                    {% if user_stats.trades_remaining <= 0 %}
                        <span class="highlight">⚠️ Daily limit reached!</span> Save this for tomorrow.
                    {% elif tcs_score >= 85 and user_stats.win_rate >= 70 %}
                        Your <span class="highlight">{{ user_stats.win_rate }}% win rate</span> + <span class="highlight">high confidence signal</span> = Strong setup!
                    {% elif tcs_score >= 85 and user_stats.win_rate < 70 %}
                        <span class="highlight">High confidence signal.</span> Perfect for improving your win rate.
                    {% elif tcs_score < 75 and user_stats.trades_remaining <= 2 %}
                        Only <span class="highlight">{{ user_stats.trades_remaining }} trades</span> left. Consider waiting for higher TCS.
                    {% elif user_stats.streak <= -3 %}
                        <span class="highlight">Tough streak.</span> This {{ tcs_score }}% signal could turn it around.
                    {% elif user_stats.consistency_score >= 80 %}
                        Your <span class="highlight">{{ user_stats.consistency_score }}% consistency</span> shows disciplined trading. Keep it up!
                    {% else %}
                        You have <span class="highlight">{{ user_stats.trades_remaining }} trades</span> remaining today.
                    {% endif %}
                </div>
            </div>
            
            <!-- Expiry Timer -->
            {% if expiry_seconds > 0 %}
            <div class="timer">
                <span class="timer-icon">⏰</span>
                <span>Signal expires in: <span id="countdown">{{ expiry_seconds }}s</span></span>
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
                    <div class="param-label">Risk</div>
                    <div class="param-value">{{ sl_pips }} pips</div>
                </div>
                <div class="param-box">
                    <div class="param-label">Reward</div>
                    <div class="param-value positive">{{ tp_pips }} pips</div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="actions">
                <button class="fire-button" onclick="fireSignal()" {% if user_stats.trades_remaining <= 0 %}disabled{% endif %}>
                    🎯 EXECUTE TRADE
                </button>
                <button class="skip-button" onclick="skipSignal()">
                    Skip This One
                </button>
            </div>
            
            <!-- Bottom Links -->
            <div class="bottom-links">
                <a href="/learn/{{ user_stats.tier }}" target="_blank">
                    <span>📚</span>
                    <span>Training</span>
                </a>
                <a href="/stats/{{ user_id }}" target="_blank">
                    <span>📊</span>
                    <span>Statistics</span>
                </a>
                <a href="/history" target="_blank">
                    <span>📜</span>
                    <span>Trade History</span>
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
            
            // Set theme colors
            tg.setHeaderColor('#0a0a0a');
            tg.setBackgroundColor('#0a0a0a');
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
        
        // Fire signal with loading state
        function fireSignal() {
            // Check if user has trades remaining
            if ({{ user_stats.trades_remaining }} <= 0) {
                alert('Daily limit reached! Come back tomorrow.');
                return;
            }
            
            const button = event.target;
            const originalText = button.innerHTML;
            
            // Show loading state
            button.innerHTML = 'EXECUTING<span class="loading"></span>';
            button.disabled = true;
            
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
            setTimeout(() => {
                button.innerHTML = '✅ TRADE EXECUTED!';
                // Close after delay
                setTimeout(exitBriefing, 1500);
            }, 1000);
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
        
        // Enhanced countdown timer
        {% if expiry_seconds > 0 %}
        let timeLeft = {{ expiry_seconds }};
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timer);
                countdownEl.textContent = 'EXPIRED';
                countdownEl.style.color = '#FF6B6B';
                document.querySelector('.fire-button').disabled = true;
                document.querySelector('.fire-button').textContent = '❌ SIGNAL EXPIRED';
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                countdownEl.textContent = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
                
                // Add urgency
                if (timeLeft <= 30) {
                    countdownEl.style.color = '#FF6B6B';
                    document.querySelector('.timer').style.animation = 'pulse 1s ease-in-out infinite';
                }
            }
        }, 1000);
        {% endif %}
        
        // Smooth animations on load
        window.addEventListener('load', () => {
            // Animate elements on page load
            const elements = document.querySelectorAll('.stat-item, .param-box');
            elements.forEach((el, index) => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(10px)';
                
                setTimeout(() => {
                    el.style.transition = 'all 0.3s ease';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, index * 30);
            });
        });
    </script>
</body>
</html>
"""

# Keep the rest of the routes the same...
@app.route('/')
def index():
    """Root endpoint"""
    return "BITTEN WebApp Server - Enhanced Version", 200

@app.route('/test')
def test():
    """Test endpoint"""
    from datetime import datetime
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BITTEN WebApp Test</title>
        <style>
            body {
                background: #0a0a0a;
                color: #00D9FF;
                font-family: 'Inter', sans-serif;
                text-align: center;
                padding: 50px;
            }
            .status {
                font-size: 24px;
                margin: 20px;
            }
            .test-link {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 24px;
                background: #00D9FF;
                color: #000;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        <h1>🎯 BITTEN Enhanced WebApp</h1>
        <div class="status">✅ Server is running!</div>
        <div>Server Time: {{ time }}</div>
        <a href="/test-signal" class="test-link">Test Signal Display</a>
    </body>
    </html>
    """, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/test-signal')
def test_signal():
    """Test signal display"""
    # Create demo signal data
    demo_data = {
        'user_id': 'test_user',
        'signal': {
            'id': 'test_signal_001',
            'signal_type': 'PRECISION',
            'symbol': 'EUR/USD',
            'direction': 'BUY',
            'tcs_score': 82,
            'entry': 1.0850,
            'sl': 1.0820,
            'tp': 1.0910,
            'sl_pips': 30,
            'tp_pips': 60,
            'rr_ratio': 2.0,
            'expiry': 300
        }
    }
    
    # Encode and redirect to HUD
    encoded_data = urllib.parse.quote(json.dumps(demo_data))
    return f'<script>window.location.href="/hud?data={encoded_data}";</script>'

@app.route('/hud')
def hud():
    """Enhanced mission briefing HUD"""
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
        
        return render_template_string(ENHANCED_HUD_TEMPLATE, **context)
        
    except Exception as e:
        return f"Error processing mission data: {str(e)}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889, debug=False)