"""
HUD endpoint - Mission briefing display
Critical for displaying signal details to users
"""

import os
import json
import logging
from flask import Blueprint, request, render_template_string
from webapp.database import SignalOperations, UserOperations
from webapp.utils import pip_size, calculate_sl_tp

logger = logging.getLogger(__name__)

hud_bp = Blueprint('hud', __name__)

@hud_bp.route('/hud')
def mission_hud():
    """Mission HUD interface - displays signal details for trading"""
    try:
        from flask import render_template
        # Get parameters
        mission_id = request.args.get('mission_id') or request.args.get('signal')
        user_id = request.args.get('user_id', '7176191872')
        
        if not mission_id:
            return "Missing mission_id parameter", 400
        
        # Load signal data from database
        signal_data = SignalOperations.get_signal(mission_id)
        
        # If not in database, try mission file
        if not signal_data:
            mission_file = f'/root/HydraX-v2/missions/{mission_id}.json'
            if os.path.exists(mission_file):
                with open(mission_file) as f:
                    signal_data = json.load(f)
            else:
                return f"Signal {mission_id} not found", 404
        
        # Extract signal details
        signal = signal_data.get('signal', signal_data)
        symbol = signal.get('symbol', 'UNKNOWN')
        direction = signal.get('direction', 'UNKNOWN')
        entry = float(signal.get('entry', 0) or signal.get('entry_price', 0))
        sl = float(signal.get('sl', 0) or signal.get('stop_loss', 0))
        tp = float(signal.get('tp', 0) or signal.get('take_profit', 0))
        confidence = float(signal.get('confidence', 0))
        
        # Get pattern type from payload if available
        pattern_type = 'UNKNOWN'
        if signal_data.get('payload_json'):
            try:
                payload = json.loads(signal_data['payload_json'])
                pattern_type = payload.get('pattern_type', 'UNKNOWN')
            except:
                pass
        
        # Calculate pips if not provided
        if entry > 0 and sl > 0:
            pip = pip_size(symbol)
            sl_pips = abs(entry - sl) / pip
            tp_pips = abs(tp - entry) / pip if tp > 0 else 0
            rr_ratio = tp_pips / sl_pips if sl_pips > 0 else 0
        else:
            sl_pips = tp_pips = rr_ratio = 0
        
        # Get user data
        user_data = UserOperations.get_user(user_id)
        ea_data = UserOperations.get_user_ea_instance(user_id)
        
        # Get balance and calculate position size
        balance = ea_data['last_balance'] if ea_data else 1000
        risk_amount = balance * 0.02  # 2% risk
        
        # Simple lot calculation
        if sl_pips > 0:
            lot_size = round(risk_amount / (sl_pips * 10), 2)
            lot_size = min(lot_size, 0.1)  # Safety cap
        else:
            lot_size = 0.01
        
        # Try to use the existing template if available
        try:
            # Prepare template data
            template_data = {
                'mission_data': {
                    'signal': signal,
                    'mission_id': mission_id,
                    'symbol': symbol,
                    'direction': direction,
                    'entry_price': entry,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'confidence': confidence,
                    'pattern_type': pattern_type,
                    'sl_pips': sl_pips,
                    'tp_pips': tp_pips,
                    'rr_ratio': rr_ratio
                },
                'user_stats': {
                    'tier': user_data.get('tier', 'GRUNT') if user_data else 'GRUNT',
                    'balance': balance,
                    'equity': ea_data.get('last_equity', balance) if ea_data else balance,
                    'win_rate': 68.5,
                    'total_pnl': 0,
                    'trades_remaining': 99
                },
                'user_id': user_id,
                'lot_size': lot_size,
                'risk_amount': risk_amount
            }
            
            # Try to render with comprehensive template
            return render_template('comprehensive_mission_briefing.html', **template_data)
        except Exception as template_error:
            logger.warning(f"Could not use template: {template_error}")
            # Fall back to inline HTML
            pass
        
        # Build HUD HTML if template fails
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>BITTEN Mission HUD</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    background: #0a0a0a;
                    color: #00ff00;
                    font-family: 'Courier New', monospace;
                    padding: 20px;
                    margin: 0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                h1 {{
                    color: #ff0000;
                    font-size: 28px;
                    margin: 10px 0;
                    text-shadow: 0 0 10px #ff0000;
                }}
                .mission-card {{
                    background: linear-gradient(135deg, #1a1a1a, #0f0f0f);
                    border: 2px solid #00ff00;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px auto;
                    max-width: 500px;
                    box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
                }}
                .signal-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #00ff00;
                }}
                .symbol {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #ffff00;
                }}
                .direction {{
                    padding: 5px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 18px;
                }}
                .direction.buy {{
                    background: #00ff00;
                    color: #000;
                }}
                .direction.sell {{
                    background: #ff0000;
                    color: #fff;
                }}
                .price-levels {{
                    display: grid;
                    gap: 10px;
                    margin: 20px 0;
                }}
                .level {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px;
                    background: rgba(0, 255, 0, 0.1);
                    border-left: 3px solid #00ff00;
                }}
                .level.sl {{ border-left-color: #ff0000; }}
                .level.tp {{ border-left-color: #00ff00; }}
                .level.entry {{ border-left-color: #ffff00; }}
                .stats {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat {{
                    background: rgba(255, 255, 255, 0.05);
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #888;
                    text-transform: uppercase;
                }}
                .stat-value {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #00ff00;
                    margin-top: 5px;
                }}
                .fire-button {{
                    width: 100%;
                    padding: 20px;
                    background: linear-gradient(135deg, #ff0000, #cc0000);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 24px;
                    font-weight: bold;
                    cursor: pointer;
                    text-transform: uppercase;
                    margin-top: 20px;
                    box-shadow: 0 5px 20px rgba(255, 0, 0, 0.5);
                    transition: all 0.3s;
                }}
                .fire-button:hover {{
                    transform: scale(1.05);
                    box-shadow: 0 8px 30px rgba(255, 0, 0, 0.7);
                }}
                .fire-button:active {{
                    transform: scale(0.98);
                }}
                .user-info {{
                    text-align: center;
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #333;
                    color: #888;
                }}
                .confidence {{
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: rgba(0, 255, 0, 0.2);
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 14px;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                    100% {{ opacity: 1; }}
                }}
                .live {{
                    animation: pulse 2s infinite;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 BITTEN MISSION HUD</h1>
                <div style="color: #888;">TACTICAL TRADING INTERFACE</div>
            </div>
            
            <div class="mission-card" style="position: relative;">
                <div class="confidence">{confidence:.1f}%</div>
                
                <div class="signal-header">
                    <div class="symbol">{symbol}</div>
                    <div class="direction {'buy' if direction.upper() == 'BUY' else 'sell'}">{direction.upper()}</div>
                </div>
                
                <div class="price-levels">
                    <div class="level entry">
                        <span>ENTRY</span>
                        <span style="color: #ffff00;">{entry:.5f}</span>
                    </div>
                    <div class="level sl">
                        <span>STOP LOSS</span>
                        <span style="color: #ff0000;">{sl:.5f}</span>
                    </div>
                    <div class="level tp">
                        <span>TAKE PROFIT</span>
                        <span style="color: #00ff00;">{tp:.5f}</span>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Risk (pips)</div>
                        <div class="stat-value" style="color: #ff0000;">{sl_pips:.1f}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Reward (pips)</div>
                        <div class="stat-value">{tp_pips:.1f}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">R:R Ratio</div>
                        <div class="stat-value" style="color: {'#00ff00' if rr_ratio >= 1.5 else '#ffff00'};">{rr_ratio:.2f}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Lot Size</div>
                        <div class="stat-value">{lot_size}</div>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Pattern</div>
                        <div class="stat-value" style="font-size: 14px;">{pattern_type}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Risk Amount</div>
                        <div class="stat-value">${risk_amount:.2f}</div>
                    </div>
                </div>
                
                <button class="fire-button live" onclick="executeFire()">
                    🔫 FIRE TRADE
                </button>
                
                <div class="user-info">
                    <div>OPERATIVE: {user_id}</div>
                    <div>BALANCE: ${balance:.2f}</div>
                    <div>MISSION: {mission_id[:20]}...</div>
                </div>
            </div>
            
            <script>
            function executeFire() {{
                const button = document.querySelector('.fire-button');
                button.disabled = true;
                button.innerHTML = '⏳ EXECUTING...';
                
                fetch('/api/fire', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-User-ID': '{user_id}'
                    }},
                    body: JSON.stringify({{
                        mission_id: '{mission_id}'
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        button.innerHTML = '✅ TRADE SENT!';
                        button.style.background = 'linear-gradient(135deg, #00ff00, #00cc00)';
                        setTimeout(() => {{
                            alert('Trade executed successfully!\\nFire ID: ' + data.fire_id);
                        }}, 500);
                    }} else {{
                        button.innerHTML = '❌ FAILED';
                        button.style.background = '#666';
                        alert('Trade failed: ' + (data.error || 'Unknown error'));
                        setTimeout(() => {{
                            button.disabled = false;
                            button.innerHTML = '🔫 FIRE TRADE';
                            button.style.background = 'linear-gradient(135deg, #ff0000, #cc0000)';
                        }}, 3000);
                    }}
                }})
                .catch(error => {{
                    button.innerHTML = '❌ ERROR';
                    button.style.background = '#666';
                    alert('Network error: ' + error);
                    setTimeout(() => {{
                        button.disabled = false;
                        button.innerHTML = '🔫 FIRE TRADE';
                        button.style.background = 'linear-gradient(135deg, #ff0000, #cc0000)';
                    }}, 3000);
                }});
            }}
            </script>
        </body>
        </html>
        '''
        
        return render_template_string(html)
        
    except Exception as e:
        logger.error(f"HUD error: {e}")
        return f"Error loading mission HUD: {str(e)}", 500

@hud_bp.route('/brief')
def mission_brief():
    """Redirect to HUD - for compatibility"""
    from flask import redirect
    
    signal_id = request.args.get('signal_id')
    user_id = request.args.get('user_id', '7176191872')
    
    if not signal_id:
        return "Missing signal_id", 400
    
    return redirect(f'/hud?mission_id={signal_id}&user_id={user_id}')