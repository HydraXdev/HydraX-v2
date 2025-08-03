#!/usr/bin/env python3
"""
Commander Throne Health Monitor
Ensures throne service stays operational
"""

import requests
import subprocess
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ThroneMonitor')

THRONE_URL = "http://localhost:8899/throne"
CHECK_INTERVAL = 60  # seconds
MAX_FAILURES = 3

def check_throne_health():
    """Check if throne is responding"""
    try:
        response = requests.get(THRONE_URL, timeout=10)
        return response.status_code == 200
    except:
        return False

def restart_throne():
    """Restart throne service"""
    try:
        subprocess.run(['systemctl', 'restart', 'bitten-throne'], check=True)
        logger.info("✅ Throne service restarted successfully")
        return True
    except:
        logger.error("❌ Failed to restart throne service")
        return False

def main():
    """Main monitoring loop"""
    logger.info("🔍 Starting Commander Throne Monitor")
    failures = 0
    
    while True:
        if check_throne_health():
            if failures > 0:
                logger.info("✅ Throne recovered - resetting failure count")
            failures = 0
        else:
            failures += 1
            logger.warning(f"⚠️ Throne health check failed ({failures}/{MAX_FAILURES})")
            
            if failures >= MAX_FAILURES:
                logger.error("🚨 Maximum failures reached - restarting throne")
                if restart_throne():
                    failures = 0
                    time.sleep(30)  # Give it time to start
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()