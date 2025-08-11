#!/usr/bin/env python3
"""
HydraX Shared Utilities - Cross-bot hardening helpers
"""
import os
import sys
import time
import json
import signal
import tempfile
import threading
import fcntl
import logging
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

# Shared executor for offloading blocking IO
EXEC = ThreadPoolExecutor(max_workers=8)

# HTTP session with retries
def http_session():
    try:
        import requests
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        
        s = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(['GET','POST','PUT','DELETE','PATCH'])
        )
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.mount("http://", HTTPAdapter(max_retries=retry))
        s.headers.update({"User-Agent": "HydraXBot/1.0"})
        return s
    except ImportError:
        return None

HTTP = http_session()

def http_post_bg(url, **kwargs):
    if not HTTP:
        raise RuntimeError("requests not available")
    kwargs.setdefault("timeout", 10)
    return EXEC.submit(HTTP.post, url, **kwargs)

def http_get_bg(url, **kwargs):
    if not HTTP:
        raise RuntimeError("requests not available")
    kwargs.setdefault("timeout", 10)
    return EXEC.submit(HTTP.get, url, **kwargs)

# Backoff-aware Telegram send/edit (FloodWait)
def send_with_retry(fn, max_attempts=5, base=1.0, **kwargs):
    try:
        from telebot.apihelper import ApiException
    except ImportError:
        class ApiException(Exception):
            result_json = {}
    
    attempt = 0
    while True:
        try:
            return fn(**kwargs)
        except ApiException as e:
            attempt += 1
            data = getattr(e, "result_json", {}) or {}
            params = data.get("parameters") or {}
            retry_after = params.get("retry_after")
            if retry_after:
                time.sleep(min(60, float(retry_after)))
            elif attempt < max_attempts:
                time.sleep(min(30, base * (2 ** (attempt - 1))))
            else:
                raise

def safe_send_message(bot, chat_id, text, **kwargs):
    return send_with_retry(lambda **kw: bot.send_message(**kw), chat_id=chat_id, text=text, **kwargs)

def safe_edit_message_text(bot, chat_id, message_id, text, **kwargs):
    return send_with_retry(lambda **kw: bot.edit_message_text(**kw),
                           chat_id=chat_id, message_id=message_id, text=text, **kwargs)

# Per-user rate limiting
RATE_BUCKET = defaultdict(lambda: deque(maxlen=10))
RATE_WINDOW = 10  # seconds
RATE_LIMIT = 5    # max events per window

def allow_user(user_id):
    now = time.time()
    dq = RATE_BUCKET[user_id]
    while dq and now - dq[0] > RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT:
        return False
    dq.append(now)
    return True

def rate_limited(bot):
    def deco(fn):
        def wrapper(message, *a, **kw):
            uid = getattr(getattr(message, "from_user", None), "id", 0)
            if not allow_user(uid):
                try:
                    bot.reply_to(message, "Slow down a bit ⚠️")
                except Exception:
                    pass
                return
            return fn(message, *a, **kw)
        return wrapper
    return deco

# Admin-only via env
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS","7176191872").split(",") if x.strip().isdigit()}

def admin_only(bot):
    def deco(fn):
        def wrapper(message, *a, **kw):
            uid = getattr(getattr(message, "from_user", None), "id", 0)
            if uid not in ADMIN_IDS:
                try:
                    bot.reply_to(message, "Admin only.")
                except Exception:
                    pass
                return
            return fn(message, *a, **kw)
        return wrapper
    return deco

# Atomic JSON persistence helpers
def atomic_write_json(path, data):
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=dir_)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(data, ensure_ascii=False, separators=(",",":")))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try: 
            os.remove(tmp)
        except FileNotFoundError: 
            pass

def locked_load_json(path, default=None):
    default = default or {}
    try:
        with open(path, "r") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                data = json.load(f)
            return data
    except FileNotFoundError:
        return default

# Schedule helper to avoid time.sleep in handlers
def run_later(delay_sec, fn, *args, **kwargs):
    t = threading.Timer(delay_sec, fn, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

# Graceful shutdown plumbing
SHUTDOWN = False

def _handle_shutdown_factory(bot, executor):
    def handle_shutdown(sig, frame):
        global SHUTDOWN
        SHUTDOWN = True
        try:
            bot.stop_polling()
        except Exception:
            pass
        try:
            executor.shutdown(wait=True, timeout=5)
        except Exception:
            pass
        os._exit(0)
    return handle_shutdown

# Latency measurement decorator
LATENCY_BUFFER = deque(maxlen=1000)
LATENCY_LOCK = threading.Lock()
LATENCY_LOGGER = logging.getLogger("hydrax.latency")

def measure_latency(bot, label_fn=None):
    """
    Decorator to measure handler latency.
    label_fn: function(message) -> str to generate label for metrics
    """
    def deco(fn):
        def wrapper(message, *a, **kw):
            start = time.monotonic()
            try:
                result = fn(message, *a, **kw)
                return result
            finally:
                duration_ms = (time.monotonic() - start) * 1000
                label = "unknown"
                if label_fn:
                    try:
                        label = label_fn(message)
                    except:
                        pass
                
                # Log individual latency
                LATENCY_LOGGER.info(json.dumps({
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "event": "latency",
                    "label": label,
                    "ms": round(duration_ms, 2)
                }))
                
                # Store for rollup
                with LATENCY_LOCK:
                    LATENCY_BUFFER.append(duration_ms)
        
        return wrapper
    return deco

def emit_latency_rollup():
    """Emit p50/p90/p99 latency stats every 60 seconds"""
    with LATENCY_LOCK:
        if not LATENCY_BUFFER:
            return
        
        sorted_latencies = sorted(LATENCY_BUFFER)
        n = len(sorted_latencies)
        p50 = sorted_latencies[n // 2]
        p90 = sorted_latencies[int(n * 0.9)]
        p99 = sorted_latencies[int(n * 0.99)]
        
        LATENCY_LOGGER.info(json.dumps({
            "ts": datetime.utcnow().isoformat() + "Z",
            "event": "latency_rollup",
            "samples": n,
            "p50_ms": round(p50, 2),
            "p90_ms": round(p90, 2),
            "p99_ms": round(p99, 2)
        }))
        
        LATENCY_BUFFER.clear()
    
    # Schedule next rollup
    run_later(60, emit_latency_rollup)

# Start latency rollup timer
run_later(60, emit_latency_rollup)

# Mission cleanup helper
def cleanup_old_files(path, days=14, max_files=500):
    """
    Delete files older than days or exceeding max_files count.
    Keeps newest files up to max_files.
    """
    try:
        path = Path(path)
        if not path.exists() or not path.is_dir():
            return
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Get all JSON files with stats
        files = []
        for f in path.glob("*.json"):
            if f.is_file():
                stat = f.stat()
                files.append((f, stat.st_mtime))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x[1], reverse=True)
        
        # Delete old files
        deleted = 0
        for i, (filepath, mtime) in enumerate(files):
            # Delete if beyond max count or too old
            if i >= max_files or datetime.fromtimestamp(mtime) < cutoff_time:
                try:
                    filepath.unlink()
                    deleted += 1
                except Exception:
                    pass
        
        if deleted > 0:
            logging.info(f"Cleaned up {deleted} old files from {path}")
            
    except Exception as e:
        logging.error(f"Cleanup error for {path}: {e}")