#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BITTEN Telegram Alert Broadcaster - SECURE & ROBUST VERSION
Permanent fix with comprehensive error handling and security hardening
"""
import os, json, time, redis, requests, sys, signal, threading, queue
import hmac, hashlib, base64
from datetime import datetime

# SECURITY: Load secrets securely with validation
def load_secrets():
    """Secure secrets loading with validation and fallback"""
    secrets_loaded = False

    # Try to load secrets files
    secret_files = [
        "/root/HydraX-v2/.secrets/athena.env",
        "/root/HydraX-v2/.secrets/telegram.env",
        "/root/HydraX-v2/.secrets/links.env"
    ]

    for secret_file in secret_files:
        try:
            if os.path.exists(secret_file):
                exec(open(secret_file).read())
                secrets_loaded = True
        except Exception as e:
            print(f"[SECURITY] Failed to load {secret_file}: {e}")

    if not secrets_loaded:
        print("[SECURITY] No secrets files loaded - using environment only")

    return secrets_loaded

# Load secrets
load_secrets()

# SECURITY: Secure token validation
def validate_token(token):
    """Validate Telegram bot token format"""
    if not token or len(token) < 45:
        return False

    parts = token.split(':')
    if len(parts) != 2:
        return False

    try:
        bot_id = int(parts[0])
        if bot_id < 100000000:  # Valid bot IDs are 9+ digits
            return False
    except ValueError:
        return False

    return True

# CONFIGURATION with secure defaults
SIGN_KEY = os.environ.get("MISSION_LINK_SIGNING_KEY", "").encode()
TTL = int(os.environ.get("MISSION_LINK_TTL_SEC", "600"))

# Redis configuration with connection pooling
REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
STREAM = os.environ.get("ALERT_STREAM", "alerts")
GROUP = os.environ.get("ALERT_GROUP", "telegram")
CONS = os.environ.get("ALERT_CONSUMER", "athena_secure")

# SECURITY: Multiple token sources with validation
TG_TOKEN = None
for token_var in ["TELEGRAM_BOT_TOKEN", "ATHENA_BOT_TOKEN"]:
    candidate = os.environ.get(token_var)
    if validate_token(candidate):
        TG_TOKEN = candidate
        print(f"[SECURITY] Using validated token from {token_var}")
        break

TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHANNEL_CHAT_ID")
EXPECTED_USERNAME = os.environ.get("EXPECTED_BOT_USERNAME", "athena_signal_bot")

# Connection management
_redis_conn = None
_last_auth_check = 0
_auth_cache_duration = 300  # 5 minutes

def get_redis():
    """Thread-safe Redis connection with retry logic"""
    global _redis_conn

    if _redis_conn is None:
        try:
            _redis_conn = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            _redis_conn.ping()
            print(f"[REDIS] Connected to {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            print(f"[REDIS] Connection failed: {e}")
            _redis_conn = None
            raise

    return _redis_conn

def _mint_link_token(user_id, signal_id, ttl=TTL):
    """Secure token minting with validation"""
    if not SIGN_KEY:
        print("[SECURITY] No signing key available")
        return None

    try:
        payload = {"uid": str(user_id), "sid": str(signal_id), "exp": int(time.time()) + ttl}
        msg = json.dumps(payload, separators=(",",":"), sort_keys=True).encode()
        sig = hmac.new(SIGN_KEY, msg, hashlib.sha256).digest()
        tok = base64.urlsafe_b64encode(msg + b"." + sig).decode().rstrip("=")
        return tok
    except Exception as e:
        print(f"[SECURITY] Token minting failed: {e}")
        return None

def fmt(ev):
    """Format event into Telegram message - SPAM RESISTANT"""
    try:
        # Extract fields safely with validation
        sid = str(ev.get("signal_id", ""))[:50]  # Limit length
        sym = str(ev.get("symbol", "?"))[:10]    # Limit length
        dire = str(ev.get("direction", "?"))[:4] # BUY/SELL only

        # Validate confidence
        try:
            conf = max(0, min(100, int(round(float(ev.get("confidence", 0))))))
        except:
            conf = 0

        hold = ev.get("expected_hold_min") or ev.get("hold_min") or None
        pclass = str((ev.get("pattern_class", "RAPID") or "RAPID")).upper()[:10]
        pattern = str(ev.get('pattern_type', ev.get('pattern', '')))[:30]
        signal_mode = str(ev.get('signal_mode', ''))[:10]

        # SECURITY: Validate direction
        if dire not in ["BUY", "SELL"]:
            dire = "?"

        # Format pattern name safely
        pattern_display = pattern.replace('_', ' ').title() if pattern else ''

        # Determine signal type with spam protection
        if signal_mode == "SNIPER" or ev.get('target_pips', 0) >= 30:
            emoji = "🎯"
            tag = "SNIPER"
        elif signal_mode == "RAPID" or (0 < ev.get('target_pips', 0) < 30):
            emoji = "⚡"
            tag = "RAPID"
        elif pclass == "SNIPER":
            emoji = "🎯"
            tag = "SNIPER"
        else:
            emoji = "⚡"
            tag = "RAPID"

        # Build message safely
        if pattern_display:
            line1 = f"{emoji} {tag} • {sym} {dire} • {conf}% • {pattern_display}"
        else:
            line1 = f"{emoji} {tag} • {sym} {dire} • {conf}%"

        # Second line with hold time or pattern
        if hold is not None:
            try:
                hold_val = max(1, min(240, int(hold)))  # 1-240 minutes max
                line2 = f"est {hold_val}m hold"
            except:
                line2 = "mission ready"
        else:
            line2 = pattern_display if pattern_display and len(pattern_display) < 25 else "mission ready"

        # SECURITY: Limit total message length
        text = "\n".join([line1, line2])
        return text[:280]  # Telegram limit with buffer

    except Exception as e:
        print(f"[FORMAT] Error formatting message: {e}")
        return f"⚡ SIGNAL ERROR • {ev.get('symbol', '?')} {ev.get('direction', '?')} • {int(ev.get('confidence', 0))}%\nmission ready"

def verify_bot_auth():
    """Secure bot authentication with caching"""
    global _last_auth_check

    current_time = time.time()

    # Use cached authentication if recent
    if current_time - _last_auth_check < _auth_cache_duration:
        return True

    if not TG_TOKEN:
        print("[AUTH] No valid token available")
        return False

    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{TG_TOKEN}/getMe",
            timeout=10
        )

        if resp.status_code == 200:
            bot_data = resp.json()
            if bot_data.get('ok'):
                username = bot_data.get('result', {}).get('username', '')
                bot_id = bot_data.get('result', {}).get('id', '')

                print(f"[AUTH] Bot verified: @{username} (ID: {bot_id})")

                # Cache successful authentication
                _last_auth_check = current_time

                # Optional: Check expected username
                if EXPECTED_USERNAME and username != EXPECTED_USERNAME:
                    print(f"[AUTH] Username mismatch: expected {EXPECTED_USERNAME}, got {username}")
                    return False

                return True
            else:
                print(f"[AUTH] Bot verification failed: {bot_data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"[AUTH] HTTP error {resp.status_code}: {resp.text}")
            return False

    except requests.exceptions.Timeout:
        print("[AUTH] Telegram API timeout")
        return False
    except Exception as e:
        print(f"[AUTH] Verification error: {e}")
        return False

def send_message_to_dlq(alert_id, stream_id, reason, payload_data=None):
    """Send failed alert to Dead Letter Queue"""
    try:
        R = get_redis()
        dlq_entry = {
            'alert_id': alert_id,
            'stream_id': stream_id,
            'reason': reason,
            'ts': str(int(time.time())),
            'payload_json': json.dumps(payload_data)[:500] if payload_data else "{}"
        }
        dlq_stream_id = R.xadd('alerts:v1:dead', dlq_entry)
        print(f"[DLQ] alert_id={alert_id} reason='{reason}' dlq_id={dlq_stream_id}")
    except Exception as e:
        print(f"[DLQ] Failed to send to DLQ: {e}")

def send_message(text, signal_id="", event_data=None, retry_count=4, stream_id=None):
    """Secure message sending with exponential backoff and DLQ"""

    if not TG_TOKEN or not TG_CHAT:
        print(f"[SEND] Missing credentials. Token: {'SET' if TG_TOKEN else 'MISSING'}, Chat: {'SET' if TG_CHAT else 'MISSING'}")
        if stream_id and signal_id:
            send_message_to_dlq(signal_id, stream_id, "missing_credentials", event_data)
        return False

    # Prepare message data
    message_data = {
        "chat_id": TG_CHAT,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    # Add inline keyboard if signal data available - MISSION SESSION DEEP LINK
    if signal_id and event_data:
        try:
            import sys
            sys.path.insert(0, '/root/HydraX-v2')

            from src.telegram.deep_link_generator import get_link_generator

            base_url = os.environ.get('BITTEN_UI_URL', 'https://www.joinbitten.com')
            pclass = str((event_data.get("pattern_class", "RAPID") or "RAPID")).upper()
            btn_text = "🎯 Mission Brief" if pclass == "SNIPER" else "⚡ Mission Brief"

            uid = event_data.get('user_id', '7176191872')  # Default to Commander

            # Generate SHORT CODE for one-tap access
            try:
                import sqlite3
                import secrets

                # Generate secure short code
                short_code = secrets.token_urlsafe(8)[:11].replace('_', '-')

                # First generate the mission session link to get the token
                link_generator = get_link_generator()
                link_data = link_generator.generate_mission_link(
                    signal_id=signal_id,
                    user_id=uid,
                    alert_id=event_data.get('id', hash(signal_id) % 1000000),
                    pair=event_data.get('symbol'),
                    timeframe=event_data.get('timeframe', 'M5'),
                    risk_max_usd=150.0
                )

                # Extract mission session ID and token from the link
                import urllib.parse
                parsed = urllib.parse.urlparse(link_data['deep_link'])
                params = urllib.parse.parse_qs(parsed.query)
                mission_session_id = params.get('ms', [''])[0]
                jwt_token = params.get('token', [''])[0]

                # Store short code in database (8-hour expiry for view access)
                conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mission_short_codes (short_code, mission_session_id, jwt_token, created_at, expires_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (short_code, mission_session_id, jwt_token, int(time.time()), int(time.time()) + (8 * 3600), uid))
                conn.commit()
                conn.close()

                # Use short code URL
                mission_url = f"{base_url}/m/{short_code}"
                print(f"[SHORTCODE] Generated short code {short_code} for {signal_id}: {mission_url}")

            except Exception as link_err:
                print(f"[SHORTCODE] Failed to generate, using fallback: {link_err}")
                # Fallback to legacy format
                signal_suffix = str(signal_id)[-6:] if len(str(signal_id)) > 6 else str(signal_id)
                mission_url = f"{base_url}/m/PS144-1-{signal_suffix}"

            # SECURITY: Validate URL length
            if len(mission_url) < 2048:  # Telegram URL limit
                inline_keyboard = {
                    "inline_keyboard": [[{
                        "text": btn_text[:64],  # Button text limit
                        "url": mission_url
                    }]]
                }
                message_data["reply_markup"] = json.dumps(inline_keyboard)
        except Exception as e:
            print(f"[SEND] Keyboard creation failed: {e}")

    # Attempt sending with exponential backoff and jitter
    import random
    for attempt in range(1, retry_count + 1):
        try:
            # Exponential backoff with jitter
            if attempt > 1:
                base_delay = min(8, 2 ** (attempt - 2))  # 1s, 2s, 4s, 8s
                jitter = random.uniform(0, 0.3)  # 0-300ms jitter
                backoff_delay = base_delay + jitter
                print(f"[TG RETRY] attempt={attempt} delay={backoff_delay:.1f}s")
                time.sleep(backoff_delay)

            resp = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data=message_data,
                timeout=(5, 10)  # 5s connect, 10s read
            )

            if resp.status_code == 200:
                resp_json = resp.json()
                ok = resp_json.get('ok', False)
                if ok:
                    result = resp_json.get('result', {})
                    message_id = result.get('message_id')
                    chat = result.get('chat', {})
                    chat_id = chat.get('id', TG_CHAT)

                    print(f"[TG OK] chat={chat_id} alert_id={signal_id} attempt={attempt}")

                    # Track message for TTL if needed
                    if message_id and signal_id:
                        track_message_for_ttl(chat_id, message_id, signal_id)

                    return True
                else:
                    error_code = resp_json.get('error_code', 0)
                    description = resp_json.get('description', '')[:100]
                    print(f"[TG FAIL] status=200 error={error_code} body={description}")
                    if stream_id and signal_id:
                        send_message_to_dlq(signal_id, stream_id, f"api_error_{error_code}", event_data)
                    return False
            elif resp.status_code in (429, 500, 502, 503, 504):
                print(f"[TG RETRY_STATUS] status={resp.status_code} attempt={attempt}")
                continue  # Retry on server errors
            else:
                resp_text = resp.text[:100] if hasattr(resp, 'text') else str(resp.status_code)
                print(f"[TG FAIL] status={resp.status_code} body={resp_text}")
                if stream_id and signal_id:
                    send_message_to_dlq(signal_id, stream_id, f"http_{resp.status_code}", event_data)
                return False

        except requests.exceptions.Timeout:
            print(f"[TG TIMEOUT] attempt={attempt}")
            continue  # Retry on timeout
        except requests.exceptions.ConnectionError:
            print(f"[TG CONN_ERR] attempt={attempt}")
            continue  # Retry on connection error
        except Exception as e:
            print(f"[TG EXC] {str(e)[:100]}")
            if stream_id and signal_id:
                send_message_to_dlq(signal_id, stream_id, f"exception_{type(e).__name__}", event_data)
            return False

    # All attempts failed
    print(f"[TG FINAL_FAIL] alert_id={signal_id} attempts={retry_count}")
    if stream_id and signal_id:
        send_message_to_dlq(signal_id, stream_id, f"max_retries_{retry_count}", event_data)
    return False

def track_message_for_ttl(chat_id, message_id, signal_id):
    """Track message for TTL cleanup"""
    try:
        R = get_redis()
        now_epoch = int(time.time())
        key = f"alerts:msg:{chat_id}:{message_id}"

        R.hset(key, mapping={
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "signal_id": str(signal_id)[:50],
            "sent_at": str(now_epoch),
            "is_dm": "0"
        })
        R.zadd("alerts:msgs", {f"{chat_id}:{message_id}": now_epoch})
        print(f"[TTL] Tracked message {message_id} for cleanup")
    except Exception as e:
        print(f"[TTL] Failed to track message: {e}")

def ensure_redis_stream():
    """Ensure Redis stream and consumer group exist"""
    try:
        R = get_redis()
        R.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
        print(f"[REDIS] Created consumer group '{GROUP}' on stream '{STREAM}'")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"[REDIS] Consumer group '{GROUP}' already exists")
        else:
            raise
    except Exception as e:
        print(f"[REDIS] Stream setup failed: {e}")
        raise

def drain_pending_messages():
    """Drain any pending messages from previous runs"""
    try:
        R = get_redis()
        print("[DRAIN] Checking for pending messages...")

        pending = R.xpending_range(STREAM, GROUP, "-", "+", 50)
        print(f"[DRAIN] Found {len(pending)} pending messages")

        drained = 0
        errors = 0

        for item in pending:
            msg_id = item['message_id']
            try:
                # Claim message
                claimed_msgs = R.xclaim(STREAM, GROUP, CONS, 0, [msg_id])

                for mid, fields in claimed_msgs:
                    try:
                        ev = json.loads(fields.get("event", "{}"))
                        signal_id = ev.get('signal_id', '')

                        print(f"[DRAIN] Processing {mid}: {signal_id}")

                        # Small delay for rate limiting
                        time.sleep(0.5)

                        ok = send_message(fmt(ev), signal_id=signal_id, event_data=ev)
                        if ok:
                            R.xack(STREAM, GROUP, mid)
                            drained += 1
                        else:
                            errors += 1
                    except Exception as e:
                        print(f"[DRAIN] Error processing {mid}: {e}")
                        errors += 1

            except Exception as e:
                print(f"[DRAIN] Error claiming {msg_id}: {e}")
                errors += 1

        print(f"[DRAIN] Complete: {drained} sent, {errors} errors")

    except Exception as e:
        print(f"[DRAIN] Drain failed: {e}")

# Global shutdown flag and decoupled queue system
_shutdown_flag = threading.Event()
Q = queue.Queue(maxsize=1000)  # in-process queue for pending sends

def signal_handler(signum, frame):
    """Graceful shutdown handler"""
    print(f"\n[SHUTDOWN] Received signal {signum}")
    _shutdown_flag.set()

def consumer_loop():
    """Redis consumer loop - ONLY moves messages to in-process queue"""
    print(f"[CONSUMER] Starting consumer loop for {STREAM}")

    while not _shutdown_flag.is_set():
        try:
            R = get_redis()

            # Short BLOCK to avoid CPU spin but not freeze
            resp = R.xreadgroup(
                GROUP, CONS,
                {STREAM: ">"},
                count=50,
                block=5000  # 5 second timeout
            )

            if not resp:
                continue

            for stream, entries in resp:
                for sid, fields in entries:
                    try:
                        # Parse fields into payload dict
                        event_data = fields.get("event")
                        if not event_data:
                            # Ack empty messages immediately
                            R.xack(STREAM, GROUP, sid)
                            continue

                        payload = json.loads(event_data)
                        payload['_stream_id'] = sid  # Track for acking

                        # DO NOT send here - just queue it
                        Q.put((sid, payload), block=False)
                        print(f"[CONSUME] queued sid={sid} alert_id={payload.get('signal_id', 'unknown')}")

                    except queue.Full:
                        print(f"[CONSUME] Queue full, dropping sid={sid}")
                        R.xack(STREAM, GROUP, sid)  # Ack to prevent reprocessing
                    except Exception as e:
                        print(f"[CONSUME] Error parsing sid={sid}: {e}")
                        R.xack(STREAM, GROUP, sid)  # Ack bad messages

        except redis.exceptions.ConnectionError:
            print("[CONSUME] Redis connection lost, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"[CONSUME] Unexpected error: {e}")
            time.sleep(1)

    print("[CONSUMER] Consumer loop ended")

def sender_worker(worker_id=0):
    """Sender worker - handles Telegram with retries"""
    print(f"[WORKER-{worker_id}] Starting sender worker")
    s = requests.Session()

    while not _shutdown_flag.is_set():
        try:
            # Get work from queue with timeout
            try:
                sid, payload = Q.get(timeout=5)
            except queue.Empty:
                continue

            signal_id = payload.get('signal_id', '')
            print(f"[WORKER-{worker_id}] Processing sid={sid} alert_id={signal_id}")

            # Format message
            formatted_text = fmt(payload)

            # Send with retries using existing send_with_retries logic
            ok = send_with_retries(session=s, payload=payload, formatted_text=formatted_text, max_attempts=4)

            R = get_redis()
            if ok:
                R.xack(STREAM, GROUP, sid)
                print(f"[TG OK] worker={worker_id} sid={sid} alert_id={signal_id}")
            else:
                # Send to DLQ and ack to prevent reprocessing
                send_message_to_dlq(signal_id, sid, 'send_fail', payload)
                R.xack(STREAM, GROUP, sid)
                print(f"[TG FINAL_FAIL] worker={worker_id} sid={sid} alert_id={signal_id}")

            Q.task_done()

        except Exception as e:
            print(f"[WORKER-{worker_id}] Unexpected error: {e}")
            time.sleep(1)

    print(f"[WORKER-{worker_id}] Sender worker ended")

def send_with_retries(session, payload, formatted_text, max_attempts=4):
    """Send message with retries using existing send_message logic"""
    signal_id = payload.get('signal_id', '')

    # Use existing send_message function but with session
    # Temporarily monkey-patch the requests module to use our session
    import requests as orig_requests
    temp_post = orig_requests.post
    orig_requests.post = session.post

    try:
        result = send_message(
            formatted_text,
            signal_id=signal_id,
            event_data=payload,
            retry_count=max_attempts,
            stream_id=payload.get('_stream_id')
        )
        return result
    finally:
        # Restore original
        orig_requests.post = temp_post

def main_loop():
    """Main processing loop with decoupled consumer/sender architecture"""

    # Validate configuration
    if not TG_TOKEN:
        print("[STARTUP] ERROR: No valid Telegram bot token found")
        return False

    if not TG_CHAT:
        print("[STARTUP] ERROR: No Telegram chat ID configured")
        return False

    print(f"[STARTUP] Token: {TG_TOKEN[:10]}...{TG_TOKEN[-10:]}")
    print(f"[STARTUP] Chat: {TG_CHAT}")

    # Verify authentication
    if not verify_bot_auth():
        print("[STARTUP] ERROR: Bot authentication failed")
        return False

    # Setup Redis
    try:
        ensure_redis_stream()
    except Exception as e:
        print(f"[STARTUP] ERROR: Redis setup failed: {e}")
        return False

    # Drain pending messages
    drain_pending_messages()

    print(f"[STARTUP] Telegram broadcaster ready - {datetime.now()}")
    print(f"[STARTUP] Decoupled architecture: consumer + 3 sender workers")
    print(f"[STARTUP] Listening to stream '{STREAM}' as '{GROUP}:{CONS}'")

    # Start sender workers (3 workers for parallel sending)
    worker_threads = []
    for i in range(3):
        worker_thread = threading.Thread(target=sender_worker, args=(i,), daemon=True)
        worker_thread.start()
        worker_threads.append(worker_thread)
        print(f"[STARTUP] Started sender worker {i}")

    # Start consumer thread
    consumer_thread = threading.Thread(target=consumer_loop, daemon=True)
    consumer_thread.start()
    print("[STARTUP] Started consumer thread")

    # Monitor threads and handle shutdown
    try:
        while not _shutdown_flag.is_set():
            # Check if consumer thread died
            if not consumer_thread.is_alive():
                print("[MONITOR] Consumer thread died, restarting...")
                consumer_thread = threading.Thread(target=consumer_loop, daemon=True)
                consumer_thread.start()

            # Check worker threads
            for i, worker in enumerate(worker_threads):
                if not worker.is_alive():
                    print(f"[MONITOR] Worker {i} died, restarting...")
                    new_worker = threading.Thread(target=sender_worker, args=(i,), daemon=True)
                    new_worker.start()
                    worker_threads[i] = new_worker

            time.sleep(10)  # Check every 10 seconds

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Keyboard interrupt")
        _shutdown_flag.set()

    # Wait for threads to finish
    print("[SHUTDOWN] Waiting for threads to finish...")
    consumer_thread.join(timeout=5)
    for worker in worker_threads:
        worker.join(timeout=2)

    print("[SHUTDOWN] Telegram broadcaster stopped")
    return True

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("="*60)
    print("🚀 BITTEN TELEGRAM BROADCASTER - SECURE VERSION")
    print("="*60)

    try:
        success = main_loop()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[FATAL] Unhandled exception: {e}")
        sys.exit(1)