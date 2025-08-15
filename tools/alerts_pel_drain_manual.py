#!/usr/bin/env python3
import os, time, json, redis, requests

R = redis.Redis(host=os.getenv("REDIS_HOST","127.0.0.1"), port=int(os.getenv("REDIS_PORT","6379")), decode_responses=True)
STREAM = os.getenv("STREAM","alerts")
GROUP = os.getenv("GROUP","telegram")
CONSUMER = os.getenv("CONSUMER","athena")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

assert TG_TOKEN and CHAT_ID, "Missing TELEGRAM_BOT_TOKEN/CHAT_ID env"

def send(msg):
    u = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(u, json={"chat_id": CHAT_ID, "text": msg, "disable_web_page_preview": True})
    r.raise_for_status()
    return r.json().get("result",{}).get("message_id")

claimed = 0
errors = 0

# Get all pending messages
pending = R.xpending_range(STREAM, GROUP, "-", "+", 100)
print(f"[PEL-DRAIN] Found {len(pending)} pending messages")

for item in pending:
    msg_id = item['message_id']
    try:
        # Claim the message
        claimed_msgs = R.xclaim(STREAM, GROUP, CONSUMER, 0, [msg_id])
        
        if claimed_msgs:
            # Get the message content
            for mid, fields in claimed_msgs:
                # Build minimal 3-line alert
                pc = fields.get("pattern_class","RAPID")
                sym = fields.get("symbol","?")
                dirn = fields.get("direction","?")
                conf = fields.get("confidence","?")
                rr = fields.get("target_rr","?")
                url = fields.get("mission_url","")
                
                if pc == "SNIPER":
                    line1 = "🎯 SNIPER"
                else:
                    line1 = "⚡ RAPID"
                    
                msg = f"{line1}\n{sym} {dirn} • TCS {conf}% • RR {rr}\n{url}".strip()
                
                # Send to Telegram
                tg_msg_id = send(msg)
                
                # ACK after successful send
                R.xack(STREAM, GROUP, mid)
                claimed += 1
                print(f"[PEL-DRAIN] SENT {mid} → Telegram msg_id={tg_msg_id}")
                
    except Exception as e:
        print(f"[PEL-DRAIN][ERR] {msg_id}: {e}")
        errors += 1

print(f"[PEL-DRAIN] Done. Sent {claimed} messages, {errors} errors.")