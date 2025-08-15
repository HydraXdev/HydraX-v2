#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTL Cleaner for Telegram Signal Posts
Deletes expired signal messages from Telegram channel based on ALERT_TTL_HOURS
"""

import os
import time
import json
import redis
import requests

# Load TTL configuration
try:
    exec(open("/root/HydraX-v2/.secrets/telegram.env").read())
except:
    pass

# Configuration
ALERT_TTL_HOURS = float(os.environ.get("ALERT_TTL_HOURS", "8"))
ALERT_TTL_DELETE_DMS = os.environ.get("ALERT_TTL_DELETE_DMS", "0") == "1"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BATCH_SIZE = 200

# Redis connection
R = redis.Redis(
    host=os.environ.get("REDIS_HOST", "127.0.0.1"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    decode_responses=True
)

def delete_telegram_message(chat_id, message_id, retries=3):
    """Delete a message from Telegram with retry logic"""
    if not TELEGRAM_BOT_TOKEN:
        print(f"[TTL-DELETE-ERROR] No bot token configured")
        return False
    
    backoff_delays = [0.5, 1.0, 2.0]
    
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage",
                data={"chat_id": chat_id, "message_id": message_id},
                timeout=10
            )
            resp_json = resp.json()
            
            if resp_json.get("ok"):
                print(f"[TTL-DELETE] chat={chat_id} msg_id={message_id} result=ok")
                return True
            
            # Check for expected errors (message already gone)
            error_code = resp_json.get("error_code")
            description = resp_json.get("description", "").lower()
            
            if error_code in [400, 403] and ("not found" in description or "too old" in description):
                print(f"[TTL-DELETE] chat={chat_id} msg_id={message_id} result=gone")
                return True
            
            # Rate limiting
            if error_code == 429:
                retry_after = resp_json.get("parameters", {}).get("retry_after", backoff_delays[attempt])
                print(f"[TTL-DELETE-RETRY] Rate limited, waiting {retry_after}s")
                time.sleep(retry_after)
                continue
            
            print(f"[TTL-DELETE-ERROR] chat={chat_id} msg_id={message_id} code={error_code} desc={description}")
            
        except Exception as e:
            print(f"[TTL-DELETE-ERROR] chat={chat_id} msg_id={message_id} exception={e}")
        
        # Backoff before retry
        if attempt < retries - 1:
            time.sleep(backoff_delays[attempt])
    
    return False

def cleanup_expired_messages():
    """Main cleanup function"""
    print(f"[TTL-CLEANER] Starting cleanup cycle, TTL={ALERT_TTL_HOURS}h, delete_dms={ALERT_TTL_DELETE_DMS}")
    
    # Calculate cutoff time
    ttl_seconds = ALERT_TTL_HOURS * 3600
    cutoff = int(time.time()) - ttl_seconds
    
    try:
        # Get expired messages in batches
        expired_members = R.zrangebyscore("alerts:msgs", "-inf", cutoff, withscores=True, start=0, num=BATCH_SIZE)
        
        if not expired_members:
            print(f"[TTL-CLEANER] No expired messages found (cutoff={cutoff})")
            return
        
        print(f"[TTL-CLEANER] Found {len(expired_members)} expired messages")
        
        processed = 0
        deleted = 0
        
        for member_id, score in expired_members:
            try:
                # Parse member_id: "chat_id:message_id"
                chat_id, message_id = member_id.split(":", 1)
                
                # Load message metadata
                hash_key = f"alerts:msg:{chat_id}:{message_id}"
                msg_data = R.hgetall(hash_key)
                
                if not msg_data:
                    print(f"[TTL-CLEANER] No metadata for {member_id}, cleaning up ZSET entry")
                    R.zrem("alerts:msgs", member_id)
                    processed += 1
                    continue
                
                is_dm = msg_data.get("is_dm") == "1"
                signal_id = msg_data.get("signal_id", "unknown")
                
                # Skip DMs if deletion is disabled
                if is_dm and not ALERT_TTL_DELETE_DMS:
                    print(f"[TTL-CLEANER] Skipping DM {member_id} (deletion disabled)")
                    processed += 1
                    continue
                
                # Attempt to delete the message
                if delete_telegram_message(chat_id, message_id):
                    # Clean up Redis entries
                    R.zrem("alerts:msgs", member_id)
                    R.delete(hash_key)
                    deleted += 1
                    print(f"[TTL-CLEANER] Cleaned up {member_id} sid={signal_id}")
                else:
                    print(f"[TTL-CLEANER] Failed to delete {member_id}, leaving for next cycle")
                
                processed += 1
                
                # Small delay between requests to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[TTL-CLEANER-ERROR] Failed to process {member_id}: {e}")
                processed += 1
        
        print(f"[TTL-CLEANER] Cycle complete: processed={processed}, deleted={deleted}")
        
    except Exception as e:
        print(f"[TTL-CLEANER-ERROR] Cleanup cycle failed: {e}")

def main():
    """Main entry point"""
    print(f"[TTL-CLEANER] Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        cleanup_expired_messages()
    except Exception as e:
        print(f"[TTL-CLEANER-FATAL] Cleanup failed: {e}")
    
    print(f"[TTL-CLEANER] Finished at {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()