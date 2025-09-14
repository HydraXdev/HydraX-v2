#!/usr/bin/env python3
"""
Fixed Redis to Webapp bridge for auto-fire functionality
Reads signals from Redis stream and POSTs to webapp API
"""
import os
import time
import json
import requests
import redis
import traceback

REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
STREAM = os.environ.get("STREAM", "signals")
GROUP = os.environ.get("GROUP", "relay")
CONSUMER = os.environ.get("CONSUMER", "relay-1")
WEBAPP = os.environ.get("WEBAPP_BASE", "http://127.0.0.1:8888")

print(f"Starting Redis to Webapp bridge...")
print(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
print(f"Stream: {STREAM}")
print(f"Webapp: {WEBAPP}")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Create consumer group if needed
try:
    r.xgroup_create(STREAM, GROUP, id="0-0", mkstream=True)
    print(f"Created consumer group: {GROUP}")
except Exception as e:
    if "BUSYGROUP" not in str(e):
        print(f"Error creating group: {e}")
    else:
        print(f"Consumer group {GROUP} already exists")

def post_signal(payload):
    """POST signal to webapp for auto-fire processing"""
    try:
        # Extract signal data from Redis event
        if "event" in payload:
            try:
                signal_data = json.loads(payload["event"])
            except:
                signal_data = payload
        else:
            signal_data = payload
        
        # Skip synthetic/diagnostic signals
        if signal_data.get('signal_type') == 'DIAG_ONLY':
            return True
        if signal_data.get('pattern_type', '').startswith('DIAG_'):
            return True
            
        # Must have signal_id
        if not signal_data.get("signal_id"):
            return True
            
        # POST to webapp
        try:
            print(f"POSTing signal {signal_data.get('signal_id')} to webapp...")
            resp = requests.post(f"{WEBAPP}/api/signals", json=signal_data, timeout=5)
            if resp.ok:
                print(f"✅ Signal {signal_data.get('signal_id')} posted successfully")
                return True
            else:
                print(f"❌ POST failed with status {resp.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"POST error: {e}")
            return False
    except Exception as e:
        print(f"Error processing signal: {e}")
        traceback.print_exc()
        return False

print("Starting main loop...")
consecutive_errors = 0

while True:
    try:
        # Read from Redis stream
        msgs = r.xreadgroup(GROUP, CONSUMER, streams={STREAM: ">"}, count=10, block=1000)
        
        if msgs:
            consecutive_errors = 0  # Reset error counter on success
            for stream_name, entries in msgs:
                for msg_id, fields in entries:
                    # Process signal
                    if post_signal(fields):
                        # Acknowledge message
                        r.xack(STREAM, GROUP, msg_id)
                    else:
                        # Don't ACK on failure, will retry
                        print(f"Will retry message {msg_id}")
        else:
            # No messages, just continue
            pass
            
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        break
    except Exception as e:
        consecutive_errors += 1
        print(f"Error in main loop (attempt {consecutive_errors}): {e}")
        
        # Exponential backoff on errors
        if consecutive_errors > 5:
            print("Too many errors, sleeping 10 seconds...")
            time.sleep(10)
        else:
            time.sleep(1)
        
        # Reconnect Redis if needed
        if consecutive_errors > 10:
            print("Reconnecting to Redis...")
            try:
                r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
                consecutive_errors = 0
            except:
                pass

print("Redis to Webapp bridge stopped")