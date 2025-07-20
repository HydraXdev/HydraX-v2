#!/usr/bin/env python3
"""
Permanent BITTEN WebApp Watchdog
Monitors webapp health and auto-restarts on failure
"""
import time
import requests
import subprocess
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/watchdog.log'),
        logging.StreamHandler()
    ]
)

class WebAppWatchdog:
    def __init__(self):
        self.webapp_url = "http://localhost:5000/health"
        self.check_interval = 30  # seconds
        self.restart_command = "cd /root/HydraX-v2 && nohup /usr/bin/python3 direct_webapp_start.py > webapp.log 2>&1 &"
        self.max_failures = 3
        self.failure_count = 0
        
    def check_health(self):
        """Check if webapp is responding"""
        try:
            response = requests.get(self.webapp_url, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def restart_webapp(self):
        """Restart the webapp"""
        logging.warning("🚨 WebApp down - attempting restart")
        
        # Kill existing processes
        try:
            subprocess.run("pkill -f direct_webapp_start.py", shell=True)
            time.sleep(5)
        except:
            pass
        
        # Start new process
        try:
            subprocess.run(self.restart_command, shell=True)
            logging.info("✅ WebApp restart command executed")
            time.sleep(15)  # Wait for startup
            
            if self.check_health():
                logging.info("🎉 WebApp successfully restarted")
                self.failure_count = 0
                return True
            else:
                logging.error("❌ WebApp restart failed - still not responding")
                return False
        except Exception as e:
            logging.error(f"💥 Restart command failed: {e}")
            return False
    
    def run_forever(self):
        """Main watchdog loop"""
        logging.info("🛡️ BITTEN WebApp Watchdog starting...")
        
        while True:
            try:
                if self.check_health():
                    if self.failure_count > 0:
                        logging.info("✅ WebApp health restored")
                        self.failure_count = 0
                else:
                    self.failure_count += 1
                    logging.warning(f"⚠️ WebApp health check failed (attempt {self.failure_count}/{self.max_failures})")
                    
                    if self.failure_count >= self.max_failures:
                        self.restart_webapp()
                        self.failure_count = 0
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logging.info("🛑 Watchdog stopped by user")
                break
            except Exception as e:
                logging.error(f"💥 Watchdog error: {e}")
                time.sleep(60)  # Wait longer on errors

if __name__ == "__main__":
    watchdog = WebAppWatchdog()
    watchdog.run_forever()