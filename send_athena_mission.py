#!/usr/bin/env python3
"""Send mission via Athena bot with working button"""

import os
import json
import time
import uuid
import sqlite3
import requests
from datetime import datetime, timezone, timedelta

# Athena credentials (NOT production bot)
ATHENA_TOKEN = os.getenv("ATHENA_BOT_TOKEN")
ATHENA_CHAT_ID = -1002581996861
WEBAPP_BASE = "https://joinbitten.com"
DB_PATH = "bitten.db"

def store_mission(signal):
    """Store mission in database first"""
    conn = sqlite3.connect(DB_PATH)
    mission_id = f"msn_{uuid.uuid4().hex[:12]}"
    
    expires_at = int(time.time()) + (2*3600)  # 2 hours
    
    conn.execute("""
        INSERT INTO missions(mission_id, signal_id, payload_json, tg_message_id, status, expires_at, created_at)
        VALUES(?,?,?,?,?,?,?)
    """, (
        mission_id,
        signal.get('signal_id', ''),
        json.dumps(signal),
        0,  # Will update after sending
        "PENDING",
        expires_at,
        int(time.time())
    ))
    conn.commit()
    conn.close()
    
    return mission_id

def send_athena_mission():
    """Send mission via Athena bot (NOT production bot)"""
    
    # Create test signal
    signal = {
        "signal_id": f"ATHENA_TEST_{int(time.time())}",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.08500,
        "stop_loss": 1.08300,
        "take_profit": 1.08900,
        "confidence": 88,
        "pattern_type": "LIQUIDITY_SWEEP",
        "signal_type": "PRECISION_STRIKE",
        "citadel_score": 8.8,
        "risk_reward": "1:2",
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    }
    
    # Store in database first
    mission_id = store_mission(signal)
    print(f"Stored mission: {mission_id}")
    
    # Format message
    symbol = signal['symbol']
    side = signal['direction']
    confidence = signal['confidence']
    citadel_score = signal['citadel_score']
    pattern = signal['pattern_type']
    entry = signal['entry_price']
    sl = signal['stop_loss']
    tp = signal['take_profit']
    
    message = f"""🪖 <b>TACTICAL MISSION BRIEF</b>
━━━━━━━━━━━━━━━━━━━━━

🟢 <b>{symbol} {side}</b>
🎯 <code>PRECISION_STRIKE</code>

<b>📊 INTEL REPORT</b>
├ Pattern: <code>{pattern}</code>
├ Confidence: <b>{confidence}%</b>
├ CITADEL: <b>{citadel_score:.1f}/10</b>
└ Risk:Reward: <b>1:2</b>

<b>💰 ENTRY ZONES</b>
├ Entry: <b>{entry:.5f}</b>
├ Stop Loss: <b>{sl:.5f}</b>
└ Take Profit: <b>{tp:.5f}</b>

<b>⏰ MISSION TIMER</b>
└ Expires: <code>2 hours</code>

━━━━━━━━━━━━━━━━━━━━━
🤖 <i>Sent via Athena Bot</i>"""

    # Send via Athena (NOT production bot!)
    brief_url = f"{WEBAPP_BASE}/brief"
    
    payload = {
        "chat_id": ATHENA_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🎯 OPEN MISSION HUD", "url": brief_url}
            ]]
        }
    }
    
    print(f"Sending via Athena bot token: {ATHENA_TOKEN[:20]}...")
    r = requests.post(
        f"https://api.telegram.org/bot{ATHENA_TOKEN}/sendMessage",
        json=payload,
        timeout=10
    )
    
    if r.status_code == 200:
        result = r.json()
        msg_id = result['result']['message_id']
        
        # Update message ID in database
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE missions SET tg_message_id=? WHERE mission_id=?", (msg_id, mission_id))
        conn.commit()
        conn.close()
        
        print(f"✅ ATHENA BOT sent mission to group")
        print(f"Message ID: {msg_id}")
        print(f"Mission ID: {mission_id}")
        print(f"Button URL: {brief_url}")
    else:
        print(f"❌ Failed: {r.text}")

if __name__ == "__main__":
    send_athena_mission()