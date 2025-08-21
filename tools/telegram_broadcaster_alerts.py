#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, time, redis, requests, sys
import hmac, hashlib, base64

# Load secrets for link signing and TTL
try:
    exec(open("/root/HydraX-v2/.secrets/links.env").read())
    exec(open("/root/HydraX-v2/.secrets/telegram.env").read())
except:
    pass

# Token signing functions (duplicate from webapp for offline operation)
SIGN_KEY = os.environ.get("MISSION_LINK_SIGNING_KEY","").encode()
TTL = int(os.environ.get("MISSION_LINK_TTL_SEC","600"))

def _mint_link_token(user_id, signal_id, ttl=TTL):
    payload = {"uid": str(user_id), "sid": str(signal_id), "exp": int(time.time()) + ttl}
    msg = json.dumps(payload, separators=(",",":"), sort_keys=True).encode()
    sig = hmac.new(SIGN_KEY, msg, hashlib.sha256).digest()
    tok = base64.urlsafe_b64encode(msg + b"." + sig).decode().rstrip("=")
    return tok

# DM format removed - all alerts go to group channel only

R=redis.Redis(host=os.environ.get("REDIS_HOST","127.0.0.1"),
              port=int(os.environ.get("REDIS_PORT","6379")), decode_responses=True)
STREAM=os.environ.get("ALERT_STREAM","alerts")
GROUP=os.environ.get("ALERT_GROUP","telegram")
CONS =os.environ.get("ALERT_CONSUMER","athena")
# NO FALLBACK - must use environment variables
TG_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")
EXPECTED_USERNAME=os.environ.get("EXPECTED_BOT_USERNAME", "athena_signal_bot")

def fmt(ev):
    # Extract fields safely
    sid = ev.get("signal_id", "")
    sym = ev.get("symbol", "?")
    dire = ev.get("direction", "?")
    conf = int(round(ev.get("confidence", 0)))
    hold = ev.get("expected_hold_min") or ev.get("hold_min") or None
    pclass = (ev.get("pattern_class", "RAPID") or "RAPID").upper()
    stop_pips = ev.get('stop_pips', 0)
    target_pips = ev.get('target_pips', 0)
    pattern = ev.get('pattern_type', ev.get('pattern', ''))  # Get pattern name
    signal_mode = ev.get('signal_mode', '')  # New dual-mode field
    
    # Format pattern name for display
    pattern_display = pattern.replace('_', ' ').title() if pattern else ''
    
    # Line 1 with distinct emojis - check signal_mode first, then target_pips, then pattern_class
    if signal_mode == "SNIPER" or target_pips >= 30:
        emoji = "🎯"
        tag = "SNIPER"
    elif signal_mode == "RAPID" or (target_pips > 0 and target_pips < 30):
        emoji = "⚡"
        tag = "RAPID"
    elif pclass == "SNIPER":
        emoji = "🎯"
        tag = "SNIPER"
    else:
        emoji = "⚡"
        tag = "RAPID"
    
    # Include pattern in line 1
    if pattern_display:
        line1 = f"{emoji} {tag} • {sym} {dire} • {conf}% • {pattern_display}"
    else:
        line1 = f"{emoji} {tag} • {sym} {dire} • {conf}%"
    
    # Line 2 - Simple and clean, no risk/reward details
    if hold is not None:
        try: 
            line2 = f"est {int(hold)}m hold"
        except: 
            line2 = "mission ready"
    else:
        # Just show pattern type or simple message
        pattern = ev.get("pattern_type", "").replace("_", " ").title() if ev.get("pattern_type") else ""
        if pattern and len(pattern) < 30:
            line2 = pattern
        else:
            line2 = "mission ready"
    
    # Join exactly 2 lines (no URL in text since button provides it)
    text = "\n".join([line1, line2])
    
    return text

def send(text, retry=2, signal_id="", event_data=None):
    if not TG_TOKEN or not TG_CHAT: 
        print(f"[TG-DRY] No token/chat configured. Would send: {text}"); 
        return False
    
    # Prepare message data
    message_data = {
        "chat_id": TG_CHAT,
        "text": text
    }
    
    # Add inline keyboard with dynamic button label
    if signal_id and event_data:
        import urllib.parse
        base_url = os.environ.get('WEBAPP_PUBLIC_BASE', 'https://joinbitten.com')
        
        # Get pattern class for button label
        pclass = (event_data.get("pattern_class", "RAPID") or "RAPID").upper()
        btn_text = "View Intel" if pclass == "SNIPER" else "Mission Brief"
        
        # Get RR and hold for logging
        rr = event_data.get("target_rr") or event_data.get("rr") or None
        hold = event_data.get("expected_hold_min") or event_data.get("hold_min") or None
        
        # Create simple URL button with uid parameter for Commander
        # TODO: Make this dynamic per user when we have per-user alerts
        uid = "7176191872"  # Commander user for now
        mission_url = f"{base_url}/brief?signal_id={urllib.parse.quote_plus(signal_id, safe='')}&uid={uid}"
        
        inline_keyboard = {
            "inline_keyboard": [[{
                "text": btn_text,
                "url": mission_url
            }]]
        }
        
        message_data["reply_markup"] = json.dumps(inline_keyboard)
        print(f"[ALERT-3LINE] sid={signal_id} class={pclass} btn='{btn_text}' rr={rr} hold={hold} url={mission_url}")
    
    for attempt in range(retry):
        try:
            print(f"[TG-SEND] Attempt {attempt+1}/{retry} sending to chat {TG_CHAT}")
            resp = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                                data=message_data, timeout=5)
            resp_json = resp.json()
            ok = resp_json.get('ok', False)
            print(f"[TG-RESP] Status={resp.status_code} ok={ok} desc={resp_json.get('description','')}")
            if ok:
                result = resp_json.get('result', {})
                message_id = result.get('message_id')
                chat_id = result.get('chat', {}).get('id', TG_CHAT)
                
                print(f"[TG-SUCCESS] Message sent: msg_id={message_id}")
                
                # Track message for TTL deletion
                if message_id and signal_id:
                    try:
                        now_epoch = int(time.time())
                        key = f"alerts:msg:{chat_id}:{message_id}"
                        R.hset(key, mapping={
                            "chat_id": str(chat_id),
                            "message_id": str(message_id),
                            "signal_id": signal_id,
                            "sent_at": str(now_epoch),
                            "is_dm": "1" if is_dm else "0"
                        })
                        R.zadd("alerts:msgs", {f"{chat_id}:{message_id}": now_epoch})
                        print(f"[TTL-TRACK] chat={chat_id} msg_id={message_id} sid={signal_id} t={now_epoch}")
                    except Exception as e:
                        print(f"[TTL-TRACK-ERROR] Failed to track message: {e}")
                
                return True
            else:
                print(f"[TG-FAIL] Telegram API error: {resp_json}")
        except Exception as e:
            print(f"[TG-ERROR] Attempt {attempt+1} failed: {e}")
            if attempt < retry - 1:
                time.sleep(1)
    return False

def ensure(): 
    try: 
        R.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
        print(f"[REDIS] Created consumer group '{GROUP}' on stream '{STREAM}'")
    except: 
        print(f"[REDIS] Consumer group '{GROUP}' already exists on stream '{STREAM}'")

def loop():
    # Verify environment variables
    if not TG_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN not set in environment. Exiting.")
        sys.exit(1)
    if not TG_CHAT:
        print("[ERROR] TELEGRAM_CHAT_ID not set in environment. Exiting.")
        sys.exit(1)
    
    # Verify bot identity
    try:
        resp = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getMe")
        if resp.status_code == 200:
            bot_data = resp.json()
            if bot_data.get('ok'):
                username = bot_data.get('result', {}).get('username', '')
                print(f"[ID] bot_username={username}, chat_id={TG_CHAT}")
                if username != EXPECTED_USERNAME:
                    print(f"[ERROR] Wrong bot! Expected {EXPECTED_USERNAME}, got {username}. Exiting.")
                    sys.exit(2)
            else:
                print(f"[ERROR] Bot verification failed: {bot_data.get('description', 'Unknown error')}")
                sys.exit(2)
        else:
            print(f"[ERROR] Failed to verify bot identity: HTTP {resp.status_code}")
            sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Failed to verify bot: {e}")
        sys.exit(2)
    
    ensure()
    print(f"[STARTED] Telegram broadcaster reading from '{STREAM}' as '{GROUP}:{CONS}'")
    print(f"[CONFIG] Token={TG_TOKEN[:10]}... Chat={TG_CHAT}")
    
    # --- PEL drain on startup ---
    try:
        print("[PEL-DRAIN] Start draining pending alerts...")
        drained = 0
        errors = 0
        
        # Get all pending messages
        pending = R.xpending_range(STREAM, GROUP, "-", "+", 100)
        print(f"[PEL-DRAIN] Found {len(pending)} pending messages")
        
        for item in pending:
            msg_id = item['message_id']
            try:
                # Claim the message with min-idle-time 0 to claim immediately
                claimed_msgs = R.xclaim(STREAM, GROUP, CONS, 0, [msg_id])
                
                if claimed_msgs:
                    for mid, fields in claimed_msgs:
                        try:
                            # Parse and send using existing logic
                            ev = json.loads(fields.get("event","{}"))
                            signal_id = ev.get('signal_id', '')
                            print(f"[PEL-DRAIN] Processing {mid}: {signal_id}")
                            
                            # Add small delay for rate limiting
                            time.sleep(0.5)
                            
                            ok = send(fmt(ev), signal_id=signal_id, is_dm=False, event_data=ev)
                            if ok:
                                R.xack(STREAM, GROUP, mid)
                                drained += 1
                                print(f"[PEL-DRAIN] SENT {mid}")
                            else:
                                print(f"[PEL-DRAIN] Failed to send {mid}")
                                errors += 1
                        except Exception as e:
                            print(f"[PEL-DRAIN][ERR] {mid}: {e}")
                            errors += 1
            except Exception as e:
                print(f"[PEL-DRAIN][ERR] Failed to claim {msg_id}: {e}")
                errors += 1
                
        print(f"[PEL-DRAIN] Completed. Drained {drained} pending alerts, {errors} errors.")
    except Exception as e:
        print(f"[PEL-DRAIN][WARN] PEL drain failed: {e}")
    # --- end PEL drain ---
    
    while True:
        try:
            print(f"[REDIS-READ] Waiting for new messages on '{STREAM}'...")
            resp = R.xreadgroup(GROUP, CONS, {STREAM:">"}, count=10, block=5000)
            
            if resp:
                print(f"[REDIS-READ] Received {len(resp[0][1])} messages")
            
            for _, items in (resp or []):
                for mid, fields in items:
                    print(f"[PROCESS] Processing message ID: {mid}")
                    ok=True
                    try:
                        ev=json.loads(fields.get("event","{}"))
                        signal_id = ev.get('signal_id', '')
                        print(f"[ALERT] {signal_id} - {ev.get('symbol')} {ev.get('direction')}")
                        ok = send(fmt(ev), signal_id=signal_id, is_dm=False, event_data=ev)
                    except Exception as e:
                        print(f"[ERROR] Failed to process {mid}: {e}")
                        ok = False
                    finally:
                        if ok: 
                            R.xack(STREAM, GROUP, mid)
                            print(f"[ACK] Message {mid} acknowledged")
                        else:
                            print(f"[NACK] Message {mid} left pending for retry")
        except Exception as e:
            print(f"[LOOP-ERROR] {e}")
            time.sleep(5)
        
        time.sleep(0.2)

if __name__=="__main__": loop()
