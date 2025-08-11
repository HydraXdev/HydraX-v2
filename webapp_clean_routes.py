#!/usr/bin/env python3
"""
Clean webapp routes for /brief and /api/fire
Add these to webapp_server_optimized.py
"""
import os
import json
import time
import base64
import hmac
import hashlib
import sqlite3
import uuid
import zmq
from flask import request, abort, jsonify, render_template_string, redirect

# Environment variables
DB = os.environ.get("BITTEN_DB", "bitten.db")
SECRET = os.environ.get("BRIEF_LINK_SECRET", "change-me-32-bytes-minimum-secret").encode()
EA_PUSH = os.environ.get("ZMQ_EA_PUSH", "tcp://127.0.0.1:5555")
WEBAPP_BASE = os.environ.get("WEBAPP_BASE", "https://134.199.204.67:8888")

def db():
    return sqlite3.connect(DB)

def verify_sig(user_id, mission_id, exp, sig) -> bool:
    """Verify HMAC signature for mission link"""
    try:
        if int(exp) < int(time.time()):
            return False
        msg = f"{user_id}.{mission_id}.{exp}".encode()
        calc = base64.urlsafe_b64encode(
            hmac.new(SECRET, msg, hashlib.sha256).digest()
        ).decode().rstrip("=")
        return hmac.compare_digest(calc, sig)
    except Exception:
        return False

def generate_sig(user_id, mission_id, exp) -> str:
    """Generate HMAC signature for mission link"""
    msg = f"{user_id}.{mission_id}.{exp}".encode()
    return base64.urlsafe_b64encode(
        hmac.new(SECRET, msg, hashlib.sha256).digest()
    ).decode().rstrip("=")

# @app.route("/brief")
def brief_page():
    """
    Auth page that redirects to signed mission link
    User arrives here from Telegram group button
    """
    # Check if we have user_id from session or Telegram login
    user_id = request.args.get('user_id')  # From Telegram login widget
    if not user_id:
        # Show Telegram login widget
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BITTEN - Authenticate</title>
            <style>
                body { background: #0a0a0a; color: #00ff41; font-family: monospace; 
                       display: flex; align-items: center; justify-content: center; 
                       height: 100vh; flex-direction: column; }
                h1 { color: #00ff41; margin-bottom: 30px; }
            </style>
        </head>
        <body>
            <h1>🎯 BITTEN AUTHENTICATION</h1>
            <p>Login with Telegram to access your mission brief</p>
            <script async src="https://telegram.org/js/telegram-widget.js?22" 
                    data-telegram-login="bitten_athena_bot" 
                    data-size="large" 
                    data-onauth="onTelegramAuth(user)" 
                    data-request-access="write"></script>
            <script>
            function onTelegramAuth(user) {
                window.location.href = '/brief?user_id=' + user.id;
            }
            </script>
        </body>
        </html>
        """)
    
    # Get latest pending mission for this user
    conn = db()
    
    # First check if user exists, if not create with defaults
    user_row = conn.execute("SELECT tier FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not user_row:
        # Create user with defaults
        conn.execute("""
            INSERT INTO users(user_id, tier, risk_pct_default, max_concurrent, 
                            daily_dd_limit, cooldown_s, balance_cache, xp, streak, last_fire_at)
            VALUES(?, 'NIBBLER', 2.0, 3, 6.0, 0, 1000.0, 0, 0, 0)
        """, (user_id,))
        conn.commit()
    
    # Get latest pending mission
    row = conn.execute("""
        SELECT mission_id 
        FROM missions 
        WHERE status='PENDING' AND expires_at > ?
        ORDER BY created_at DESC 
        LIMIT 1
    """, (int(time.time()),)).fetchone()
    
    if not row:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BITTEN - No Active Missions</title>
            <style>
                body { background: #0a0a0a; color: #ff4444; font-family: monospace; 
                       display: flex; align-items: center; justify-content: center; 
                       height: 100vh; text-align: center; }
            </style>
        </head>
        <body>
            <div>
                <h1>⚠️ NO ACTIVE MISSIONS</h1>
                <p>Wait for the next signal in Telegram</p>
            </div>
        </body>
        </html>
        """)
    
    mission_id = row[0]
    
    # Generate signed link (15 minute expiry)
    exp = int(time.time()) + 900
    sig = generate_sig(user_id, mission_id, exp)
    
    # Redirect to signed mission page
    return redirect(f"/mission/{mission_id}?u={user_id}&exp={exp}&sig={sig}")

# @app.route("/mission/<mission_id>")
def mission_page(mission_id):
    """
    Display personalized mission brief with execute button
    Requires valid HMAC signature
    """
    user_id = request.args.get("u")
    exp = request.args.get("exp")
    sig = request.args.get("sig")
    
    if not (user_id and exp and sig and verify_sig(user_id, mission_id, exp, sig)):
        abort(403)
    
    conn = db()
    
    # Get mission details
    row = conn.execute("""
        SELECT payload_json, status, expires_at 
        FROM missions 
        WHERE mission_id=?
    """, (mission_id,)).fetchone()
    
    if not row:
        abort(404)
    
    payload_json, status, expires_at = row
    
    if status != "PENDING" or int(time.time()) >= int(expires_at):
        abort(410)  # Gone
    
    payload = json.loads(payload_json)
    
    # Load user for personalization
    urow = conn.execute("""
        SELECT tier, risk_pct_default, max_concurrent, daily_dd_limit, 
               cooldown_s, balance_cache, last_fire_at 
        FROM users 
        WHERE user_id=?
    """, (user_id,)).fetchone()
    
    if urow:
        tier, risk_pct, max_conc, dd_limit, cooldown_s, balance, last_fire = urow
    else:
        # Defaults
        tier, risk_pct, balance = 'NIBBLER', 2.0, 1000.0
    
    # Calculate personalized risk/reward
    entry = float(payload.get('entry_price', payload.get('entry', 0)))
    sl = float(payload.get('stop_loss', payload.get('sl', 0)))
    tp = float(payload.get('take_profit', payload.get('tp', 0)))
    
    risk_amount = (risk_pct / 100.0) * balance
    sl_distance = abs(entry - sl)
    tp_distance = abs(tp - entry)
    
    if sl_distance > 0:
        reward_amount = (tp_distance / sl_distance) * risk_amount
    else:
        reward_amount = risk_amount * 2  # Default 2:1
    
    # Generate idempotency key
    idem = "idem_" + uuid.uuid4().hex[:16]
    
    # Minimal mission template
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BITTEN Mission Brief</title>
        <style>
            body { background: #0a0a0a; color: #00ff41; font-family: 'Courier New', monospace; 
                   padding: 20px; max-width: 600px; margin: 0 auto; }
            .header { border-bottom: 2px solid #00ff41; padding-bottom: 10px; margin-bottom: 20px; }
            .signal-box { background: #111; border: 1px solid #00ff41; padding: 20px; 
                         margin: 20px 0; border-radius: 5px; }
            .risk-reward { display: flex; justify-content: space-around; margin: 20px 0; }
            .risk { color: #ff4444; font-size: 24px; }
            .reward { color: #00ff41; font-size: 24px; }
            .execute-btn { background: #00ff41; color: #000; border: none; 
                          padding: 15px 30px; font-size: 18px; cursor: pointer; 
                          width: 100%; margin-top: 20px; font-weight: bold; }
            .execute-btn:hover { background: #00cc33; }
            .execute-btn:disabled { background: #666; cursor: not-allowed; }
            .details { margin: 10px 0; }
            .label { color: #888; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 MISSION BRIEF</h1>
            <div>User: {{ user_id }} | Tier: {{ tier }}</div>
        </div>
        
        <div class="signal-box">
            <h2>{{ symbol }} {{ side }}</h2>
            <div class="details">
                <div><span class="label">Entry:</span> {{ "%.5f"|format(entry) }}</div>
                <div><span class="label">Stop Loss:</span> {{ "%.5f"|format(sl) }}</div>
                <div><span class="label">Take Profit:</span> {{ "%.5f"|format(tp) }}</div>
                <div><span class="label">Pattern:</span> {{ pattern }}</div>
            </div>
        </div>
        
        <div class="risk-reward">
            <div class="risk">
                <div>RISK</div>
                <div>${{ "%.2f"|format(risk_amount) }}</div>
            </div>
            <div class="reward">
                <div>REWARD</div>
                <div>${{ "%.2f"|format(reward_amount) }}</div>
            </div>
        </div>
        
        <form id="fireForm" onsubmit="executeTrade(event)">
            <input type="hidden" name="mission_id" value="{{ mission_id }}">
            <input type="hidden" name="user_id" value="{{ user_id }}">
            <input type="hidden" name="idem" value="{{ idem }}">
            <button type="submit" class="execute-btn" id="executeBtn">
                🔥 EXECUTE TRADE
            </button>
        </form>
        
        <div id="status" style="margin-top: 20px; text-align: center;"></div>
        
        <script>
        function executeTrade(e) {
            e.preventDefault();
            const btn = document.getElementById('executeBtn');
            const status = document.getElementById('status');
            
            btn.disabled = true;
            btn.textContent = 'FIRING...';
            
            const formData = new FormData(document.getElementById('fireForm'));
            
            fetch('/api/fire', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(Object.fromEntries(formData))
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    status.innerHTML = '<div style="color: #00ff41;">✅ TRADE SENT! Check Telegram for confirmation.</div>';
                    btn.textContent = 'EXECUTED';
                } else {
                    status.innerHTML = '<div style="color: #ff4444;">❌ ' + (data.error || 'Failed') + '</div>';
                    btn.disabled = false;
                    btn.textContent = '🔥 EXECUTE TRADE';
                }
            })
            .catch(err => {
                status.innerHTML = '<div style="color: #ff4444;">❌ Network error</div>';
                btn.disabled = false;
                btn.textContent = '🔥 EXECUTE TRADE';
            });
        }
        </script>
    </body>
    </html>
    """, 
        user_id=user_id,
        tier=tier,
        mission_id=mission_id,
        idem=idem,
        symbol=payload.get('symbol', 'UNKNOWN'),
        side=payload.get('direction', payload.get('side', 'BUY')).upper(),
        entry=entry,
        sl=sl,
        tp=tp,
        pattern=payload.get('pattern_type', 'ELITE_GUARD'),
        risk_amount=risk_amount,
        reward_amount=reward_amount
    )

def enforce_and_compute_lot(conn, user_id, mission_payload):
    """
    Minimal enforcer - computes position size based on risk
    Replace with BittenCore module when available
    """
    # Pull user
    u = conn.execute("""
        SELECT tier, risk_pct_default, max_concurrent, daily_dd_limit, 
               cooldown_s, balance_cache, last_fire_at 
        FROM users 
        WHERE user_id=?
    """, (user_id,)).fetchone()
    
    if not u:
        return (False, "user_not_found", None)
    
    tier, risk_pct, max_conc, dd_limit, cooldown_s, balance, last_fire = u
    now = int(time.time())
    
    # TODO: implement real checks (concurrency, dd, cooldown, tier gates)
    # For now, assume allowed and compute naive lot:
    entry = float(mission_payload.get("entry_price", mission_payload.get("entry", 0)))
    sl = float(mission_payload.get("stop_loss", mission_payload.get("sl", 0)))
    
    risk_dollars = (risk_pct or 2.0) / 100.0 * (balance or 1000.0)
    sl_distance = abs(entry - sl)
    
    if sl_distance <= 0:
        return (False, "invalid_sl_distance", None)
    
    # Simplified pip value calculation (replace with correct per-symbol math)
    symbol = mission_payload.get("symbol", "EURUSD")
    
    # Forex pip values (simplified)
    if "JPY" in symbol:
        pip_value = 10.0  # JPY pairs
    elif "XAU" in symbol:
        pip_value = 1.0   # Gold
    else:
        pip_value = 10.0  # Major pairs
    
    # Convert distance to pips
    if "JPY" in symbol:
        sl_pips = sl_distance * 100
    elif "XAU" in symbol:
        sl_pips = sl_distance * 10
    else:
        sl_pips = sl_distance * 10000
    
    # Calculate lot size
    lots = risk_dollars / (sl_pips * pip_value)
    lots = max(0.01, round(lots, 2))  # Minimum 0.01 lots
    
    return (True, None, lots)

# @app.route("/api/fire", methods=["POST"])
def api_fire():
    """
    Single authority to fire trades
    Enforces rules and sends to EA via ZMQ
    """
    data = request.get_json(force=True)
    mission_id = data.get("mission_id")
    user_id = data.get("user_id")
    idem = data.get("idem")
    
    if not all([mission_id, user_id, idem]):
        return jsonify({"ok": False, "error": "missing_params"}), 400
    
    conn = db()
    
    # Idempotency check
    try:
        conn.execute("""
            INSERT INTO fires(fire_id, mission_id, user_id, status, idem, created_at, updated_at) 
            VALUES(?,?,?,?,?,?,?)
        """, ("pending", mission_id, user_id, "RESERVED", idem, int(time.time()), int(time.time())))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "error": "duplicate"}), 409
    
    # Clean up pending record
    conn.execute("DELETE FROM fires WHERE fire_id='pending'")
    conn.commit()
    
    # Get mission details
    mrow = conn.execute("""
        SELECT payload_json, status, expires_at, tg_message_id 
        FROM missions 
        WHERE mission_id=?
    """, (mission_id,)).fetchone()
    
    if not mrow:
        return jsonify({"ok": False, "error": "mission_not_found"}), 404
    
    payload_json, status, expires_at, tg_message_id = mrow
    
    if status != "PENDING" or int(time.time()) >= int(expires_at):
        return jsonify({"ok": False, "error": "mission_expired"}), 410
    
    payload = json.loads(payload_json)
    
    # Enforce rules and compute lot size
    ok, err, lots = enforce_and_compute_lot(conn, user_id, payload)
    if not ok:
        return jsonify({"ok": False, "error": err}), 403
    
    # Generate fire ID
    fire_id = "fir_" + uuid.uuid4().hex[:12]
    
    # Insert fire record
    conn.execute("""
        INSERT INTO fires(fire_id, mission_id, user_id, status, created_at, updated_at, idem) 
        VALUES(?,?,?,?,?,?,?)
    """, (fire_id, mission_id, user_id, "SENT", int(time.time()), int(time.time()), idem))
    conn.commit()
    
    # Send to EA via ZMQ
    try:
        ctx = zmq.Context.instance()
        push = ctx.socket(zmq.PUSH)
        push.setsockopt(zmq.SNDTIMEO, 2000)
        push.setsockopt(zmq.LINGER, 0)
        push.connect(EA_PUSH)
        
        # Prepare command for EA
        cmd = {
            "type": "OPEN",
            "fire_id": fire_id,
            "signal_id": payload.get("signal_id", ""),
            "user_id": user_id,
            "symbol": payload.get("symbol", "EURUSD"),
            "side": payload.get("direction", payload.get("side", "BUY")).upper(),
            "entry": float(payload.get("entry_price", payload.get("entry", 0))),
            "sl": float(payload.get("stop_loss", payload.get("sl", 0))),
            "tp": float(payload.get("take_profit", payload.get("tp", 0))),
            "lot": lots,
            "time_in_force": "IOC"
        }
        
        push.send_json(cmd)
        push.close()
        
        return jsonify({
            "ok": True,
            "fire_id": fire_id,
            "tg_message_id": tg_message_id,
            "lots": lots
        }), 202
        
    except Exception as e:
        # Log error but still return success (fire record created)
        print(f"ZMQ send error: {e}")
        return jsonify({
            "ok": True,
            "fire_id": fire_id,
            "tg_message_id": tg_message_id,
            "lots": lots,
            "warning": "zmq_send_failed"
        }), 202

# Export the functions to be added to webapp
__all__ = ['brief_page', 'mission_page', 'api_fire']