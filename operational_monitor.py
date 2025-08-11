#!/usr/bin/env python3
"""
Operational monitoring and alerting for BITTEN system
Checks EA health, fire confirmations, and queue status
"""
import sqlite3
import time
import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('OpMonitor')

# Alert thresholds
EA_STALE_SECONDS = 120  # Alert if EA hasn't heartbeated in 2 minutes
FIRE_CONFIRM_TIMEOUT = 30  # Alert if fire not confirmed in 30 seconds
QUEUE_BACKUP_THRESHOLD = 10  # Alert if queue has >10 pending

def check_ea_health():
    """Check for stale EA instances"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    
    now = int(time.time())
    cursor.execute("""
        SELECT target_uuid, user_id, last_seen, last_equity 
        FROM ea_instances 
        WHERE last_seen < ?
    """, (now - EA_STALE_SECONDS,))
    
    stale_eas = cursor.fetchall()
    if stale_eas:
        for ea in stale_eas:
            age = now - ea[2]
            logger.warning(f"⚠️ STALE EA: {ea[0]} | User: {ea[1]} | Age: {age}s | Last Equity: {ea[3]}")
    
    conn.close()
    return len(stale_eas)

def check_unconfirmed_fires():
    """Check for fires without confirmations"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    
    now = int(time.time())
    timeout_ago = now - FIRE_CONFIRM_TIMEOUT
    
    cursor.execute("""
        SELECT fire_id, mission_id, created_at 
        FROM fires 
        WHERE status IN ('QUEUED', 'SENT') 
        AND created_at < ?
    """, (timeout_ago,))
    
    unconfirmed = cursor.fetchall()
    if unconfirmed:
        for fire in unconfirmed:
            age = now - fire[2]
            logger.warning(f"⚠️ UNCONFIRMED FIRE: {fire[0]} | Mission: {fire[1]} | Age: {age}s")
    
    conn.close()
    return len(unconfirmed)

def check_queue_status():
    """Check for queue backup (would need ZMQ integration)"""
    # This is a placeholder - in production you'd check actual queue depth
    # For now, just log that we're monitoring
    logger.info("✅ Queue monitoring active")
    return 0

def send_alert(message: str, severity: str = "WARNING"):
    """Send alert to monitoring system"""
    # In production, this would send to:
    # - Telegram admin channel
    # - PagerDuty/OpsGenie
    # - CloudWatch/Datadog
    logger.error(f"🚨 ALERT [{severity}]: {message}")
    
    # Write to alert log
    with open('/root/HydraX-v2/alerts.log', 'a') as f:
        f.write(f"{datetime.now().isoformat()} [{severity}] {message}\n")

def monitor_loop():
    """Main monitoring loop"""
    logger.info("🔍 Starting operational monitoring...")
    
    check_count = 0
    while True:
        try:
            check_count += 1
            
            # Run checks
            stale_ea_count = check_ea_health()
            unconfirmed_count = check_unconfirmed_fires()
            queue_depth = check_queue_status()
            
            # Send alerts if needed
            if stale_ea_count > 0:
                send_alert(f"{stale_ea_count} EA(s) are stale (>120s)", "WARNING")
            
            if unconfirmed_count > 0:
                send_alert(f"{unconfirmed_count} fire(s) unconfirmed (>30s)", "ERROR")
            
            if queue_depth > QUEUE_BACKUP_THRESHOLD:
                send_alert(f"Queue backup: {queue_depth} pending", "WARNING")
            
            # Log health status every 10 checks
            if check_count % 10 == 0:
                logger.info(f"📊 Health Check #{check_count}: Stale EAs: {stale_ea_count}, Unconfirmed: {unconfirmed_count}")
            
            # Check every 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Monitor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_loop()