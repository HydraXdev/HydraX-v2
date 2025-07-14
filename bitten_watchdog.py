#!/usr/bin/env python3
"""
BITTEN WebApp Watchdog - Monitors health and triggers alerts
"""
import requests
import time
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - BITTEN_WATCHDOG - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/bitten-watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BITTEN_WATCHDOG')

class BittenWatchdog:
    def __init__(self):
        self.failure_count = 0
        self.max_failures = 3
        self.check_interval = 30  # seconds
        self.webapp_url = "http://localhost:5000/health"
        self.nuclear_activated = False
        
    def check_webapp_health(self):
        """Check webapp health endpoint"""
        try:
            response = requests.get(self.webapp_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return True, data.get("mode", "UNKNOWN")
            return False, "FAILED"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False, "ERROR"
    
    def send_telegram_alert(self, message):
        """Send alert to Telegram (stub - would need bot integration)"""
        logger.warning(f"TELEGRAM ALERT: {message}")
        # TODO: Integrate with existing Telegram bot system
        
    def log_failure(self, details):
        """Log failure to dedicated failure log"""
        try:
            with open('/var/log/bitten-fail.log', 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {details}\n")
        except Exception as e:
            logger.error(f"Failed to write failure log: {e}")
    
    def activate_nuclear_fallback(self):
        """Activate nuclear fallback if needed"""
        if self.nuclear_activated:
            return False
            
        try:
            logger.critical("🚨 ACTIVATING NUCLEAR FALLBACK - WebApp failed 3x consecutively")
            
            # Kill any existing webapp processes
            subprocess.run(["pkill", "-f", "python.*webapp"], capture_output=True)
            subprocess.run(["pkill", "-f", "flask"], capture_output=True)
            time.sleep(3)
            
            # Start nuclear webapp
            subprocess.Popen([
                "nohup", "python3", "/root/HydraX-v2/EMERGENCY_WEBAPP_NUCLEAR.py"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Create nuclear flag
            with open('/root/HydraX-v2/.nuclear_active', 'w') as f:
                f.write(f"NUCLEAR_RECOVERY_MODE_ACTIVE\nTimestamp: {datetime.now().isoformat()}\nReason: 3x consecutive health failures\nMethod: Watchdog Auto-Activation\nStatus: ACTIVE")
            
            self.nuclear_activated = True
            self.send_telegram_alert("🚨 NUCLEAR FALLBACK ACTIVATED - WebApp auto-recovery initiated")
            return True
            
        except Exception as e:
            logger.error(f"Nuclear fallback activation failed: {e}")
            return False
    
    def run(self):
        """Main watchdog loop"""
        logger.info("🐕 BITTEN Watchdog starting...")
        
        while True:
            try:
                is_healthy, mode = self.check_webapp_health()
                
                if is_healthy:
                    if self.failure_count > 0:
                        logger.info(f"✅ WebApp recovered (mode: {mode}) - resetting failure count")
                    self.failure_count = 0
                    
                    # Reset nuclear flag if we're healthy and not in nuclear mode
                    if mode != "NUCLEAR_RECOVERY" and self.nuclear_activated:
                        self.nuclear_activated = False
                        logger.info("🟢 Normal operations restored - nuclear mode deactivated")
                else:
                    self.failure_count += 1
                    logger.warning(f"❌ WebApp health check failed ({self.failure_count}/{self.max_failures})")
                    
                    # Log the failure
                    self.log_failure(f"Health check failure #{self.failure_count} - Mode: {mode}")
                    
                    # Check if we need to activate nuclear fallback
                    if self.failure_count >= self.max_failures:
                        if self.activate_nuclear_fallback():
                            logger.critical("🚨 Nuclear fallback activated successfully")
                            self.send_telegram_alert("🛡️ BITTEN WebApp recovered via nuclear fallback")
                        else:
                            logger.critical("💥 Nuclear fallback FAILED - manual intervention required")
                            self.send_telegram_alert("💥 CRITICAL: Nuclear fallback failed - immediate attention required")
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Watchdog stopped by user")
                break
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    watchdog = BittenWatchdog()
    watchdog.run()