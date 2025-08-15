#!/usr/bin/env python3
import os, json, redis, requests, time

# ATHENA bot credentials
ATHENA_TOKEN = "8322305650:AAHu8NmQ0rXT0LkZOlDeYop6TAUJXaXbwAg"
CHAT_ID = "-1002581996861"

R = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
STREAM = "alerts"
GROUP = "telegram"
CONSUMER = "athena"

def send_athena_message(text):
    """Send message using ATHENA bot only"""
    url = f"https://api.telegram.org/bot{ATHENA_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        result = r.json()
        if result.get('ok'):
            return result.get('result',{}).get('message_id')
        else:
            print(f"[ERROR] Telegram API: {result}")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to send: {e}")
        return None

# Verify we're using ATHENA
print("=== ATHENA BOT VERIFICATION ===")
me_url = f"https://api.telegram.org/bot{ATHENA_TOKEN}/getMe"
me_resp = requests.get(me_url)
me_data = me_resp.json()
if me_data.get('ok'):
    bot_info = me_data.get('result', {})
    print(f"✅ Using ATHENA bot: @{bot_info.get('username')} ({bot_info.get('first_name')})")
else:
    print(f"❌ Bot verification failed: {me_data}")
    exit(1)

# Get pending messages
print("\n=== PROCESSING STUCK ALERTS ===")
pending = R.xpending_range(STREAM, GROUP, "-", "+", 100)
print(f"Found {len(pending)} pending messages")

sent_count = 0
error_count = 0

for item in pending:
    msg_id = item['message_id']
    try:
        # Claim the message
        claimed_msgs = R.xclaim(STREAM, GROUP, CONSUMER, 0, [msg_id])
        
        if claimed_msgs:
            for mid, fields in claimed_msgs:
                try:
                    # Parse event data
                    ev = json.loads(fields.get("event","{}"))
                    
                    # Extract alert data
                    signal_id = ev.get('signal_id', '')
                    pc = ev.get("pattern_class","RAPID")
                    sym = ev.get("symbol","?")
                    dirn = ev.get("direction","?")
                    conf = ev.get("confidence","?")
                    rr = ev.get("target_rr","?")
                    
                    # Format message (3 lines, no button due to domain restrictions)
                    if pc == "SNIPER":
                        line1 = "🎯 SNIPER PRIME"
                    else:
                        line1 = "⚡ RAPID ALERT"
                    
                    line2 = f"{sym} {dirn} • TCS {conf}% • RR {rr}"
                    line3 = f"https://joinbitten.com/brief?signal_id={signal_id}"
                    
                    message_text = f"{line1}\n{line2}\n{line3}"
                    
                    print(f"\nProcessing {mid}: {signal_id}")
                    print(f"  Pattern: {pc}, Symbol: {sym} {dirn}")
                    
                    # Send via ATHENA
                    tg_msg_id = send_athena_message(message_text)
                    
                    if tg_msg_id:
                        # ACK successful send
                        R.xack(STREAM, GROUP, mid)
                        sent_count += 1
                        print(f"  ✅ SENT → Telegram msg_id={tg_msg_id}")
                    else:
                        error_count += 1
                        print(f"  ❌ Failed to send")
                    
                    # Rate limit
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"  ❌ Error processing {mid}: {e}")
                    error_count += 1
                    
    except Exception as e:
        print(f"❌ Failed to claim {msg_id}: {e}")
        error_count += 1

print(f"\n=== SUMMARY ===")
print(f"✅ Successfully sent: {sent_count}")
print(f"❌ Errors: {error_count}")
print(f"📊 Total processed: {len(pending)}")

# Check remaining pending
remaining = R.xpending_range(STREAM, GROUP, "-", "+", 10)
print(f"\n📋 Remaining pending: {len(remaining)}")
if remaining:
    for item in remaining[:3]:
        print(f"  - {item['message_id']} (consumer: {item['consumer']})")