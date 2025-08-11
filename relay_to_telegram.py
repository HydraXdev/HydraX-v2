#!/usr/bin/env python3
"""
Relay Service - SUB 5557 → Athena posts to group + write mission
Athena bot owns all group mission posts
"""
import os
import json
import time
import uuid
import requests
import zmq
import sqlite3
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AthenaRelay')

DB = os.environ.get("BITTEN_DB", "bitten.db")
ATHENA_TOKEN = os.environ["ATHENA_BOT_TOKEN"]
ATHENA_CHAT_ID = int(os.environ["ATHENA_CHAT_ID"])
WEBAPP_BASE = os.environ.get("WEBAPP_BASE", "https://joinbitten.com")
GEN_PUB = os.environ.get("ZMQ_GEN_PUB", "tcp://127.0.0.1:5557")

def db():
    return sqlite3.connect(DB)

def athena_send(text, buttons=None):
    """Send message via Athena bot to group"""
    try:
        payload = {
            "chat_id": ATHENA_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        
        r = requests.post(
            f"https://api.telegram.org/bot{ATHENA_TOKEN}/sendMessage",
            json=payload,
            timeout=10
        )
        r.raise_for_status()
        return r.json()["result"]["message_id"]
    except Exception as e:
        logger.error(f"Failed to send via Athena: {e}")
        return None

def format_hud_mission(s):
    """Format enhanced HUD mission message"""
    # Extract signal data
    symbol = s.get('symbol', 'UNKNOWN')
    side = s.get('direction', s.get('side', 'BUY')).upper()
    rr = s.get('risk_reward', s.get('rr', '1:2'))
    confidence = s.get('confidence', s.get('tcs', 70))
    entry = s.get('entry_price', s.get('entry', 0))
    sl = s.get('stop_loss', s.get('sl', 0))
    tp = s.get('take_profit', s.get('tp', 0))
    pattern = s.get('pattern_type', s.get('notes', 'SMART_MONEY'))
    signal_type = s.get('signal_type', 'PRECISION_STRIKE')
    citadel_score = s.get('citadel_score', 7.5)
    
    # Format expiry
    expires_str = s.get('expires_at', '')
    if not expires_str:
        exp_time = datetime.now(timezone.utc).timestamp() + (2*3600 + 5*60)
        expires_str = datetime.fromtimestamp(exp_time, timezone.utc).strftime("%H:%M UTC")
    else:
        try:
            exp_dt = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
            expires_str = exp_dt.strftime("%H:%M UTC")
        except:
            expires_str = "2h5m"
    
    # Direction indicator
    dir_icon = "🟢" if side == "BUY" else "🔴"
    action = "LONG" if side == "BUY" else "SHORT"
    
    # Signal type badge
    type_badge = "⚡" if signal_type == "RAPID_ASSAULT" else "🎯"
    
    # Build enhanced HUD message
    hud = f"""🪖 <b>TACTICAL MISSION BRIEF</b>
━━━━━━━━━━━━━━━━━━━━━

{dir_icon} <b>{symbol} {action}</b>
{type_badge} <code>{signal_type}</code>

<b>📊 INTEL REPORT</b>
├ Pattern: <code>{pattern}</code>
├ Confidence: <b>{confidence}%</b>
├ CITADEL: <b>{citadel_score:.1f}/10</b>
└ Risk:Reward: <b>{rr}</b>

<b>💰 ENTRY ZONES</b>
├ Entry: <b>{entry:.5f}</b>
├ Stop Loss: <b>{sl:.5f}</b>
└ Take Profit: <b>{tp:.5f}</b>

<b>⏰ MISSION TIMER</b>
└ Expires: <code>{expires_str}</code>

━━━━━━━━━━━━━━━━━━━━━
🎖️ <i>Elite Guard Signal v6.0</i>"""
    
    return hud

def main():
    logger.info("🚀 Starting Athena Relay Service")
    logger.info(f"📡 Subscribing to: {GEN_PUB}")
    logger.info(f"🤖 Using Athena bot for group: {ATHENA_CHAT_ID}")
    
    ctx = zmq.Context.instance()
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.RCVTIMEO, 0)  # Non-blocking
    sub.connect(GEN_PUB)
    sub.setsockopt_string(zmq.SUBSCRIBE, "ELITE_GUARD_SIGNAL")
    
    poller = zmq.Poller()
    poller.register(sub, zmq.POLLIN)
    
    conn = db()
    signal_count = 0
    
    logger.info("✅ Athena relay ready, waiting for signals...")
    
    while True:
        try:
            socks = dict(poller.poll(500))
            
            if sub in socks:
                # Receive signal
                message = sub.recv_string()
                
                # Parse message (format: "ELITE_GUARD_SIGNAL {json}")
                if message.startswith("ELITE_GUARD_SIGNAL "):
                    payload = message[19:]
                    s = json.loads(payload)
                    signal_count += 1
                    
                    logger.info(f"📨 Signal #{signal_count} received: {s.get('signal_id')}")
                    
                    # Generate mission ID
                    mission_id = f"msn_{uuid.uuid4().hex[:12]}"
                    
                    # Post mission via Athena with enhanced HUD
                    hud_message = format_hud_mission(s)
                    brief_url = f"{WEBAPP_BASE}/brief"
                    logger.info(f"[AthenaRelay] Posting brief URL: {brief_url}")
                    msg_id = athena_send(
                        hud_message,
                        buttons=[[{"text": "🎯 OPEN MISSION HUD", "url": brief_url}]]
                    )
                    
                    if msg_id:
                        logger.info(f"✅ Athena posted to group, msg_id: {msg_id}")
                        
                        # Persist mission
                        try:
                            expires_at_str = s.get('expires_at', '')
                            if expires_at_str:
                                exp_dt = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                                exp_epoch = int(exp_dt.timestamp())
                            else:
                                exp_epoch = int(time.time()) + (2*3600 + 5*60)
                        except Exception:
                            exp_epoch = int(time.time()) + (2*3600 + 5*60)
                        
                        # Get most recently active EA for routing
                        # In production, this could be more sophisticated (round-robin, load balancing, etc)
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT target_uuid FROM ea_instances 
                            WHERE last_seen > ? 
                            ORDER BY last_seen DESC 
                            LIMIT 1
                        """, (int(time.time()) - 300,))  # Active in last 5 minutes
                        row = cursor.fetchone()
                        target_uuid = row[0] if row else None
                        
                        # Add target_uuid to signal data
                        if target_uuid:
                            s['target_uuid'] = target_uuid
                        
                        conn.execute("""
                            INSERT INTO missions(mission_id, signal_id, payload_json, tg_message_id, status, expires_at, created_at, target_uuid)
                            VALUES(?,?,?,?,?,?,?,?)
                        """, (
                            mission_id,
                            s.get('signal_id', ''),
                            json.dumps(s),
                            msg_id,
                            "PENDING",
                            exp_epoch,
                            int(time.time()),
                            target_uuid
                        ))
                        conn.commit()
                        logger.info(f"💾 Stored mission: {mission_id}")
                    else:
                        logger.error("Failed to post via Athena")
                        
        except zmq.Again:
            pass
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown signal received")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(1)
    
    sub.close()
    ctx.term()
    conn.close()
    logger.info("👋 Athena relay stopped")

if __name__ == "__main__":
    main()