#!/usr/bin/env python3
import os, json, redis, requests, urllib.parse, time

R = redis.Redis(host=os.getenv("REDIS_HOST","127.0.0.1"), port=int(os.getenv("REDIS_PORT","6379")), decode_responses=True)
STREAM = os.getenv("STREAM","alerts")
GROUP  = os.getenv("GROUP","telegram")
CONSUMER = os.getenv("CONSUMER","athena")
BASE   = "https://joinbitten.com"
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")

assert TG_TOKEN and CHAT_ID, "Missing TELEGRAM env"

def send_with_button(fields):
    """Send message with inline keyboard button for login"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    
    # Extract fields
    pc = fields.get("pattern_class","RAPID")
    sym = fields.get("symbol","?")
    dire = fields.get("direction","?")
    conf = fields.get("confidence","?")
    rr = fields.get("target_rr","?")
    signal_id = fields.get("signal_id", "")
    
    # Build message text
    if pc == "SNIPER":
        line1 = "🎯 SNIPER"
        btn_text = "View Intel"
    else:
        line1 = "⚡ RAPID"
        btn_text = "Mission Brief"
    
    msg_text = f"{line1}\n{sym} {dire} • TCS {conf}% • RR {rr}\n{BASE}/brief?signal_id={urllib.parse.quote_plus(signal_id)}"
    
    # Create inline keyboard with login URL
    state_data = {"sid": signal_id}
    login_url = f"{BASE}/tg_login?state={urllib.parse.quote_plus(json.dumps(state_data))}"
    
    message_data = {
        "chat_id": CHAT_ID,
        "text": msg_text,
        "disable_web_page_preview": True,
        "reply_markup": json.dumps({
            "inline_keyboard": [[{
                "text": btn_text,
                "login_url": {
                    "url": login_url,
                    "request_write_access": True,
                    "forward_text": "Authorize to view mission"
                }
            }]]
        })
    }
    
    r = requests.post(url, data=message_data, timeout=10)
    r.raise_for_status()
    return r.json().get("result",{}).get("message_id")

claimed = 0
sent = 0

# Get pending messages
pending = R.xpending_range(STREAM, GROUP, "-", "+", 100)
print(f"[HTTPS-RETRY] Found {len(pending)} pending messages")

for item in pending:
    msg_id = item['message_id']
    try:
        # Claim the message
        claimed_msgs = R.xclaim(STREAM, GROUP, CONSUMER, 0, [msg_id])
        
        if claimed_msgs:
            for mid, fields in claimed_msgs:
                try:
                    # Parse event field
                    ev = json.loads(fields.get("event","{}"))
                    signal_id = ev.get('signal_id', '')
                    print(f"[HTTPS-RETRY] Processing {mid}: {signal_id}")
                    
                    # Add small delay for rate limiting
                    time.sleep(0.5)
                    
                    # Send with HTTPS URL and button
                    tg_msg_id = send_with_button(ev)
                    
                    # ACK after successful send
                    R.xack(STREAM, GROUP, mid)
                    sent += 1
                    print(f"[HTTPS-RETRY] SENT {mid} → Telegram msg_id={tg_msg_id}")
                    
                except Exception as e:
                    print(f"[HTTPS-RETRY][ERR] {mid}: {e}")
                    
    except Exception as e:
        print(f"[HTTPS-RETRY][ERR] Failed to claim {msg_id}: {e}")

print(f"[HTTPS-RETRY] Completed. Sent={sent} of {len(pending)} pending")