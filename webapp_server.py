#!/usr/bin/env python3
"""Simple Flask server to serve BITTEN WebApp HUDs"""

from flask import Flask, render_template_string, request
import json
import urllib.parse

app = Flask(__name__)

# Base HUD template with dynamic content
HUD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITTEN {{ tier|upper }} Mission Brief</title>
    <style>
        body {
            background-color: #0a0a0a;
            color: #ffffff;
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 0;
        }
        .top-bar {
            background: rgba(0,0,0,0.8);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .back-button {
            color: {{ primary_color }};
            text-decoration: none;
            padding: 5px 15px;
            border: 1px solid {{ primary_color }};
            border-radius: 5px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.3s;
        }
        .back-button:hover {
            background: {{ primary_color }};
            color: #000;
        }
        .hud-container {
            max-width: 600px;
            margin: 20px auto;
            border: 2px solid {{ border_color }};
            border-radius: 10px;
            padding: 20px;
            background: linear-gradient(135deg, #0a0a0a, {{ bg_color }});
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .tier-badge {
            display: inline-block;
            background: {{ primary_color }};
            color: #000;
            padding: 5px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .signal-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid {{ primary_color }};
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .data-row {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
        }
        .label {
            color: #aaa;
        }
        .value {
            color: {{ primary_color }};
            font-weight: bold;
        }
        .locked {
            color: #666;
            font-style: italic;
        }
        .fire-button {
            width: 100%;
            padding: 15px;
            background: {{ primary_color }};
            color: #000;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
        }
        .personal-stats {
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .glitch {
            animation: glitch 2s infinite;
        }
        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-1px, 1px); }
            40% { transform: translate(1px, -1px); }
        }
        .pulse {
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .floating-close {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            background: rgba(255, 0, 0, 0.8);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            transition: all 0.3s;
            z-index: 200;
        }
        .floating-close:hover {
            background: rgba(255, 0, 0, 1);
            transform: scale(1.1);
        }
        
        /* Glass Breaking Effect */
        .glass-break {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            display: none;
        }
        
        .glass-break.active {
            display: block;
            animation: shatter 0.6s ease-out forwards;
            background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M10,10 L50,40 L20,60 Z" fill="none" stroke="white" stroke-width="0.5" opacity="0.8"/><path d="M50,40 L90,10 L80,60 Z" fill="none" stroke="white" stroke-width="0.5" opacity="0.8"/><path d="M20,60 L50,40 L80,60 L50,90 Z" fill="none" stroke="white" stroke-width="0.5" opacity="0.8"/></svg>') center no-repeat;
            background-size: cover;
        }
        
        @keyframes shatter {
            0% {
                opacity: 0;
                transform: scale(0.8);
            }
            50% {
                opacity: 1;
                transform: scale(1.1);
            }
            100% {
                opacity: 0;
                transform: scale(1.2) rotate(5deg);
            }
        }
        
        .unauthorized-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0);
            background: #1a0000;
            border: 3px solid #ff0000;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            z-index: 10000;
            transition: transform 0.3s;
            max-width: 400px;
        }
        
        .unauthorized-modal.active {
            transform: translate(-50%, -50%) scale(1);
        }
        
        .unauthorized-modal h2 {
            color: #ff0000;
            margin: 0 0 20px 0;
            font-size: 28px;
            animation: pulse 1s infinite;
        }
        
        .upgrade-button-modal {
            background: #ff0000;
            color: #fff;
            border: none;
            padding: 15px 30px;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.3s;
        }
        
        .upgrade-button-modal:hover {
            background: #cc0000;
            transform: scale(1.05);
        }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <!-- Top Navigation Bar -->
    <div class="top-bar">
        <a href="#" class="back-button" onclick="exitBriefing()">
            ← Back to Telegram
        </a>
        <div style="color: {{ primary_color }};">
            BITTEN {{ tier|upper }} BRIEF
        </div>
        <div style="color: #666; font-size: 14px;">
            {{ symbol }} | {{ direction }}
        </div>
    </div>
    
    <div class="hud-container">
        <div class="header">
            <div class="tier-badge">{{ tier|upper }} OPERATIVE</div>
            <h1 class="{{ 'glitch' if tier in ['commander', 'apex'] else '' }}">MISSION BRIEFING</h1>
            <div style="color: #666; font-size: 12px;">Signal ID: {{ signal_id }}</div>
        </div>

        <!-- Personal Stats -->
        <div class="personal-stats">
            <h3 style="color: {{ primary_color }}; margin-top: 0;">YOUR STATS</h3>
            <div class="stats-grid">
                <div>
                    <div class="label">Last Trade</div>
                    <div class="value">+34 pips WIN</div>
                </div>
                <div>
                    <div class="label">Session</div>
                    <div class="value">73% (8/11)</div>
                </div>
                <div>
                    <div class="label">Streak</div>
                    <div class="value">🔥 3 wins</div>
                </div>
                <div>
                    <div class="label">TCS Avg</div>
                    <div class="value">{{ user_tcs }}%</div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <a href="https://joinbitten.com/me" style="color: {{ primary_color }}; text-decoration: none; font-size: 14px;">
                    📊 View Full War Room →
                </a>
            </div>
        </div>

        <!-- Signal Details -->
        <div class="signal-card">
            <h2 style="color: {{ primary_color }}; margin-top: 0;">{{ symbol }} - {{ direction|upper }}</h2>
            
            <div class="data-row">
                <span class="label">Entry Price:</span>
                <span class="value">{{ entry }}</span>
            </div>
            
            <div class="data-row">
                <span class="label">Stop Loss:</span>
                <span class="value">{{ stop_loss }} (-${{ risk_amount }})</span>
            </div>
            
            <div class="data-row">
                <span class="label">Take Profit:</span>
                <span class="value">{{ take_profit }} (+${{ reward_amount }})</span>
            </div>
            
            <div class="data-row">
                <span class="label">TCS Score:</span>
                <span class="value pulse">{{ tcs }}%</span>
            </div>
            
            <div class="data-row">
                <span class="label">Risk/Reward:</span>
                <span class="value">1:{{ risk_reward }}</span>
            </div>

            {% if tier in ['fang', 'commander', 'apex'] %}
            <!-- AI Analysis (FANG+) -->
            <div style="border-top: 1px solid #333; margin-top: 15px; padding-top: 15px;">
                <h3 style="color: {{ primary_color }};">🤖 AI ANALYSIS</h3>
                <div class="data-row">
                    <span class="label">Success Probability:</span>
                    <span class="value">{{ ai_probability }}%</span>
                </div>
                <div class="data-row">
                    <span class="label">Momentum Score:</span>
                    <span class="value">{{ momentum }}/10</span>
                </div>
            </div>
            {% endif %}

            {% if tier in ['commander', 'apex'] %}
            <!-- Spotter Confirmation (COMMANDER+) -->
            <div style="border-top: 1px solid #333; margin-top: 15px; padding-top: 15px;">
                <h3 style="color: {{ primary_color }};">🎯 SPOTTER CONFIRMATION</h3>
                <div class="data-row">
                    <span class="label">Pattern Match:</span>
                    <span class="value">{{ pattern }}</span>
                </div>
                <div class="data-row">
                    <span class="label">Squad Position:</span>
                    <span class="value">{{ squad_percent }}% active</span>
                </div>
                <div class="data-row">
                    <span class="label">Smart Money:</span>
                    <span class="value">{{ smart_money }}</span>
                </div>
            </div>
            {% endif %}

            {% if tier == 'apex' %}
            <!-- Quantum Metrics (APEX ONLY) -->
            <div style="border-top: 1px solid #333; margin-top: 15px; padding-top: 15px;">
                <h3 style="color: {{ primary_color }};">🌌 QUANTUM ANALYSIS</h3>
                <div class="data-row">
                    <span class="label">Quantum Probability:</span>
                    <span class="value glitch">{{ quantum_prob }}%</span>
                </div>
                <div class="data-row">
                    <span class="label">Reality Distortion:</span>
                    <span class="value glitch">Level {{ reality_level }}</span>
                </div>
            </div>
            {% endif %}
        </div>

        <!-- Action Button -->
        <button class="fire-button" onclick="executeTrade()">
            🔫 EXECUTE TRADE
        </button>

        <!-- Tier-specific message -->
        <div style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
            {% if tier == 'nibbler' %}
            💡 Pro tip: Wait for TCS 85%+ for better results
            {% elif tier == 'fang' %}
            🤖 AI confidence: {{ 'HIGH' if tcs|int > 85 else 'MODERATE' }}
            {% elif tier == 'commander' %}
            🎯 All systems aligned - Spotter confirmed
            {% elif tier == 'apex' %}
            🌌 Reality bending to your will
            {% endif %}
        </div>

        <!-- Additional Links -->
        <div style="display: flex; justify-content: space-around; margin-top: 20px; padding-top: 20px; border-top: 1px solid #333;">
            {% if tier == 'nibbler' %}
            <a href="/wwbd?signal={{ signal_id }}" style="color: {{ primary_color }}; text-decoration: none;">
                🐾 What Would Bit Do?
            </a>
            {% endif %}
            <a href="/history" style="color: {{ primary_color }}; text-decoration: none;">
                📜 Trade History
            </a>
            <a href="/learn/{{ tier }}" style="color: {{ primary_color }}; text-decoration: none;">
                📚 {{ tier|title }} Training
            </a>
        </div>
    </div>

    <!-- Floating Close Button -->
    <div class="floating-close" onclick="exitBriefing()" title="Close and return to Telegram">
        ✖
    </div>
    
    <!-- Glass Break Overlay -->
    <div class="glass-break" id="glassBreak"></div>
    
    <!-- Unauthorized Access Modal -->
    <div class="unauthorized-modal" id="unauthorizedModal">
        <h2>🚫 ACCESS DENIED</h2>
        <p style="color: #ff6666; font-size: 18px;">{{ tier|upper }} CLEARANCE REQUIRED</p>
        <p style="color: #aaa; margin: 20px 0;">This signal requires higher authorization.<br>Your current tier cannot execute this trade.</p>
        <button class="upgrade-button-modal" onclick="window.open('https://t.me/bitten_bot?start=upgrade', '_blank')">
            UPGRADE ACCESS
        </button>
        <div style="margin-top: 20px;">
            <a href="#" onclick="closeUnauthorized()" style="color: #666; text-decoration: none;">Continue Observing</a>
        </div>
    </div>

    <script>
        // Initialize Telegram WebApp
        if (window.Telegram && window.Telegram.WebApp) {
            Telegram.WebApp.ready();
            Telegram.WebApp.expand();
        }
        
        // Ka-ching sound for profits (using Web Audio API)
        function playKaChing() {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create a simple ka-ching sound using oscillators
            const createBeep = (frequency, startTime, duration) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = frequency;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0, startTime);
                gainNode.gain.linearRampToValueAtTime(0.3, startTime + 0.01);
                gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
                
                oscillator.start(startTime);
                oscillator.stop(startTime + duration);
            };
            
            // Ka-ching is two quick high notes
            const now = audioContext.currentTime;
            createBeep(1318.5, now, 0.1);        // E6
            createBeep(1661.2, now + 0.1, 0.15); // G#6
            
            // Optional: Add coin-like metallic shimmer
            createBeep(2093, now + 0.05, 0.05);   // C7 (overtone)
            createBeep(2637, now + 0.15, 0.05);   // E7 (overtone)
        }
        
        function exitBriefing() {
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.close();
            } else {
                // Fallback for testing in browser
                window.history.back();
            }
        }
        
        // Check if user is authorized for this signal
        function checkAuthorization() {
            const userTier = '{{ tier }}';  // User's actual tier
            const signalTcs = parseInt('{{ tcs }}');
            
            // Simulate authorization check based on TCS requirements
            if (userTier === 'nibbler' && signalTcs > 85) {
                return false;
            } else if (userTier === 'fang' && signalTcs > 90) {
                return false;
            }
            return true;
        }
        
        function triggerGlassBreak() {
            // Visual glass break
            const glassBreak = document.getElementById('glassBreak');
            glassBreak.classList.add('active');
            
            // Haptic feedback - strong vibration
            if (window.navigator && window.navigator.vibrate) {
                // War-like impact pattern: strong-short-strong
                window.navigator.vibrate([100, 50, 100, 50, 200]);
            }
            
            // Sound effect (if we add audio later)
            // const audio = new Audio('/sounds/glass-break.mp3');
            // audio.play();
            
            // Show unauthorized modal after glass effect
            setTimeout(() => {
                document.getElementById('unauthorizedModal').classList.add('active');
                glassBreak.classList.remove('active');
            }, 600);
        }
        
        function closeUnauthorized() {
            document.getElementById('unauthorizedModal').classList.remove('active');
        }
        
        function executeTrade() {
            // Check authorization first
            if (!checkAuthorization()) {
                triggerGlassBreak();
                return;
            }
            
            // Haptic feedback for confirmation
            if (window.navigator && window.navigator.vibrate) {
                // Quick double tap for confirmation prompt
                window.navigator.vibrate([50, 50, 50]);
            }
            
            if (confirm('Execute this trade?')) {
                // War-like haptic feedback for execution
                if (window.navigator && window.navigator.vibrate) {
                    // Machine gun burst pattern
                    window.navigator.vibrate([30, 30, 30, 30, 30, 30, 30, 30, 100]);
                }
                
                // Direct execution on this server
                fetch('/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        signal_id: '{{ signal_id }}',
                        tier: '{{ tier }}',
                        symbol: '{{ symbol }}',
                        direction: '{{ direction }}',
                        entry: '{{ entry }}'
                    })
                }).then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          // Victory haptic pattern
                          if (window.navigator && window.navigator.vibrate) {
                              window.navigator.vibrate([100, 100, 100, 100, 300]);
                          }
                          alert('Trade executed! Returning to Telegram...');
                          exitBriefing();
                      } else {
                          // Failure haptic
                          if (window.navigator && window.navigator.vibrate) {
                              window.navigator.vibrate([500]);
                          }
                          alert('Execution failed: ' + data.message);
                      }
                  });
            }
        }
        
        // Add keyboard shortcut for exit
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                exitBriefing();
            }
        });
    </script>
</body>
</html>
"""

# Tier-specific styling
TIER_STYLES = {
    'nibbler': {
        'primary_color': '#4b7c16',
        'border_color': '#4b7c16',
        'bg_color': '#1a2a1a'
    },
    'fang': {
        'primary_color': '#00ccff',
        'border_color': '#00ccff',
        'bg_color': '#001a2a'
    },
    'commander': {
        'primary_color': '#ffd700',
        'border_color': '#ffd700',
        'bg_color': '#2a2a1a'
    },
    'apex': {
        'primary_color': '#ff0044',
        'border_color': '#ff0044',
        'bg_color': '#2a1a1a'
    }
}

@app.route('/')
def mission_brief():
    # Get parameters from URL
    tier = request.args.get('tier', 'nibbler')
    signal_id = request.args.get('signal_id', 'SIG-12345')
    symbol = request.args.get('symbol', 'EURUSD')
    direction = request.args.get('direction', 'BUY')
    entry = request.args.get('entry', '1.0823')
    tcs = request.args.get('tcs', '85')
    
    # Get tier-specific styles
    styles = TIER_STYLES.get(tier, TIER_STYLES['nibbler'])
    
    # Calculate dynamic values
    stop_pips = 20
    target_pips = 35
    risk_reward = round(target_pips / stop_pips, 2)
    
    # Tier-specific data
    context = {
        'tier': tier,
        'signal_id': signal_id,
        'symbol': symbol,
        'direction': direction,
        'entry': entry,
        'stop_loss': f"-{stop_pips}p",
        'take_profit': f"+{target_pips}p",
        'risk_amount': stop_pips * 5,
        'reward_amount': target_pips * 5,
        'tcs': tcs,
        'risk_reward': risk_reward,
        'user_tcs': '81',
        **styles
    }
    
    # Add tier-specific data
    if tier in ['fang', 'commander', 'apex']:
        context.update({
            'ai_probability': '87',
            'momentum': '7.5'
        })
    
    if tier in ['commander', 'apex']:
        context.update({
            'pattern': 'Bull Flag',
            'squad_percent': '89',
            'smart_money': 'Accumulating'
        })
    
    if tier == 'apex':
        context.update({
            'quantum_prob': '94.7',
            'reality_level': '3'
        })
    
    return render_template_string(HUD_TEMPLATE, **context)

@app.route('/test')
def test_page():
    """Test page with links to all tier views"""
    return """
    <html>
    <body style="background: #000; color: #fff; font-family: monospace; padding: 20px;">
        <h1>BITTEN WebApp HUD Test Links</h1>
        <p>Click to see how each tier views the same signal:</p>
        <ul style="line-height: 2;">
            <li><a href="/?tier=nibbler&symbol=EURUSD&direction=BUY&entry=1.0823&tcs=72" style="color: #4b7c16;">
                🟢 NIBBLER View (Basic + Learning)
            </a></li>
            <li><a href="/?tier=fang&symbol=EURUSD&direction=BUY&entry=1.0823&tcs=85" style="color: #00ccff;">
                🔵 FANG View (+ AI Analysis)
            </a></li>
            <li><a href="/?tier=commander&symbol=EURUSD&direction=BUY&entry=1.0823&tcs=91" style="color: #ffd700;">
                🟡 COMMANDER View (+ Spotter & Squad)
            </a></li>
            <li><a href="/?tier=apex&symbol=EURUSD&direction=BUY&entry=1.0823&tcs=94" style="color: #ff0044;">
                🔴 APEX View (+ Quantum Reality)
            </a></li>
        </ul>
        
        <h2 style="margin-top: 40px;">Trade Result Tests:</h2>
        <ul style="line-height: 2;">
            <li><a href="/trade-result/TEST001?result=win&pips=35&profit=175" style="color: #00ff44;">
                💰 Test WIN Result (Ka-ching!)
            </a></li>
            <li><a href="/trade-result/TEST002?result=loss&pips=20&profit=100" style="color: #ff0044;">
                📉 Test LOSS Result (Silence)
            </a></li>
        </ul>
        
        <p style="margin-top: 30px; color: #666;">
        💡 Winning trades play ka-ching sound with falling coins<br>
        💡 Losing trades show moment of silence with subtle fade
        </p>
    </body>
    </html>
    """

@app.route('/wwbd')
def what_would_bit_do():
    """What Would Bit Do - analysis for Nibblers"""
    signal_id = request.args.get('signal', 'SIG-12345')
    
    return f"""
    <html>
    <body style="background: #0a0a0a; color: #fff; font-family: monospace; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; text-align: center;">
            <h1 style="color: #4b7c16;">🐾 What Would Bit Do?</h1>
            <div style="background: #1a1a1a; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <p style="font-style: italic; color: #aaa;">*Bit observes the market patterns...*</p>
                <p style="color: #4b7c16; font-size: 18px; margin: 20px 0;">
                    "Mrow... This setup shows promise, but patience young hunter.<br><br>
                    
                    Wait for TCS above 85% - those are the kills worth stalking.<br><br>
                    
                    Remember: The best traders are like cats - they wait for the perfect moment to pounce."
                </p>
                <p style="color: #666;">Signal {signal_id} - TCS below optimal threshold</p>
            </div>
            <div style="margin-top: 20px;">
                <a href="javascript:history.back()" style="color: #4b7c16;">← Back to Mission Brief</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/execute', methods=['POST'])
def execute_trade():
    """Execute trade directly on this server"""
    data = request.json
    
    # Here you would integrate with the actual trade execution
    # For now, return success
    return {
        'success': True,
        'message': 'Trade queued for execution',
        'signal_id': data.get('signal_id')
    }

@app.route('/trade-result/<signal_id>')
def trade_result(signal_id):
    """Show trade result with ka-ching for profits"""
    # Get result from query params (in real app, from database)
    result = request.args.get('result', 'win')
    pips = request.args.get('pips', '35')
    profit = request.args.get('profit', '175')
    
    if result == 'win':
        # Winning trade - play ka-ching!
        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    background: #0a0a0a;
                    color: #00ff44;
                    font-family: monospace;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    overflow: hidden;
                }}
                .result-container {{
                    text-align: center;
                    animation: zoomIn 0.5s ease-out;
                }}
                .profit-amount {{
                    font-size: 72px;
                    font-weight: bold;
                    margin: 20px 0;
                    animation: pulse 1s infinite;
                    text-shadow: 0 0 20px #00ff44;
                }}
                .pips {{
                    font-size: 36px;
                    color: #00ff88;
                }}
                @keyframes zoomIn {{
                    from {{ transform: scale(0); opacity: 0; }}
                    to {{ transform: scale(1); opacity: 1; }}
                }}
                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                }}
                .coins {{
                    position: absolute;
                    font-size: 50px;
                    animation: fall 2s ease-in-out;
                }}
                @keyframes fall {{
                    0% {{ top: -50px; transform: rotate(0deg); }}
                    100% {{ top: 100vh; transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="result-container">
                <h1>🎯 TARGET ELIMINATED</h1>
                <div class="profit-amount">+${profit}</div>
                <div class="pips">+{pips} pips</div>
                <p>Mission Successful</p>
            </div>
            
            <!-- Falling coins animation -->
            <div class="coins" style="left: 10%;">💰</div>
            <div class="coins" style="left: 30%; animation-delay: 0.3s;">💰</div>
            <div class="coins" style="left: 50%; animation-delay: 0.6s;">💰</div>
            <div class="coins" style="left: 70%; animation-delay: 0.9s;">💰</div>
            <div class="coins" style="left: 90%; animation-delay: 1.2s;">💰</div>
            
            <script>
                // Play ka-ching sound immediately
                {playKaChing.toString()}
                playKaChing();
                
                // Victory haptic
                if (window.navigator && window.navigator.vibrate) {{
                    window.navigator.vibrate([100, 100, 100, 100, 300]);
                }}
                
                // Auto close after 3 seconds
                setTimeout(() => {{
                    if (window.Telegram && window.Telegram.WebApp) {{
                        window.Telegram.WebApp.close();
                    }} else {{
                        window.close();
                    }}
                }}, 3000);
            </script>
        </body>
        </html>
        """
    else:
        # Losing trade - moment of silence
        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    background: #0a0a0a;
                    color: #666;
                    font-family: monospace;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .result-container {{
                    text-align: center;
                    opacity: 0;
                    animation: fadeIn 1s ease-in forwards;
                }}
                @keyframes fadeIn {{
                    to {{ opacity: 1; }}
                }}
            </style>
        </head>
        <body>
            <div class="result-container">
                <h2>Target Escaped</h2>
                <p style="color: #ff0044;">-{pips} pips</p>
                <p style="font-size: 14px; margin-top: 30px;">Analyzing...</p>
            </div>
            
            <script>
                // Just a moment of silence - no sound
                
                // Subtle haptic for loss
                if (window.navigator && window.navigator.vibrate) {{
                    window.navigator.vibrate([200]);
                }}
                
                // Auto close after 2 seconds (quicker for losses)
                setTimeout(() => {{
                    if (window.Telegram && window.Telegram.WebApp) {{
                        window.Telegram.WebApp.close();
                    }} else {{
                        window.close();
                    }}
                }}, 2000);
            </script>
        </body>
        </html>
        """

@app.route('/history')
def trade_history():
    """Show user's trade history"""
    return """
    <html>
    <body style="background: #0a0a0a; color: #fff; font-family: monospace; padding: 20px;">
        <h1>Trade History</h1>
        <p>Your recent trades would appear here...</p>
        <a href="javascript:history.back()">← Back</a>
    </body>
    </html>
    """

@app.route('/learn/<tier>')
def learning_module(tier):
    """Tier-specific learning modules"""
    modules = {
        'nibbler': 'Basic price action, risk management, patience',
        'fang': 'Advanced patterns, AI integration, momentum trading',
        'commander': 'Market structure, liquidity flows, squad coordination',
        'apex': 'Quantum analysis, reality manipulation, transcendence'
    }
    
    return f"""
    <html>
    <body style="background: #0a0a0a; color: #fff; font-family: monospace; padding: 20px;">
        <h1>{tier.title()} Training Module</h1>
        <p>Topics covered: {modules.get(tier, 'General trading')}</p>
        <a href="javascript:history.back()">← Back to Mission</a>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🚀 Starting BITTEN WebApp server...")
    print("📱 Visit http://localhost:5000/test to see all tier views")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)