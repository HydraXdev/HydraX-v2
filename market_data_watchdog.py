#!/usr/bin/env python3
"""
Market Data Watchdog System
Monitors market data receiver health and restarts if needed
Alerts user 7176191872 via Telegram on critical failures
"""

import requests
import time
import json
import logging
import subprocess
import signal
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
import psutil

# Configuration
MARKET_DATA_HOST = "localhost"
MARKET_DATA_PORT = 8001
CHECK_INTERVAL = 60  # seconds
ALERT_USER_ID = "7176191872"
PROCESS_NAME = "market_data_receiver_enhanced.py"
PROCESS_PATH = "/root/HydraX-v2/market_data_receiver_enhanced.py"

# Endpoints to check
HEALTH_ENDPOINTS = [
    f"http://{MARKET_DATA_HOST}:{MARKET_DATA_PORT}/market-data/health",
    f"http://{MARKET_DATA_HOST}:{MARKET_DATA_PORT}/market-data/venom-feed?symbol=EURUSD"
]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/market_data_watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarketDataWatchdog:
    def __init__(self):
        self.consecutive_failures = 0
        self.last_restart_time = None
        self.total_restarts = 0
        
    def check_endpoint_health(self, url: str, timeout: int = 5) -> Tuple[bool, str]:
        """
        Check if an endpoint is healthy
        Returns (is_healthy, error_message)
        """
        try:
            response = requests.get(url, timeout=timeout)
            
            # Check HTTP status - allow 404 for venom-feed as it's normal when no data
            if response.status_code == 404 and "/venom-feed" in url:
                # 404 is acceptable for venom-feed - check if response is valid JSON
                pass
            elif response.status_code != 200:
                return False, f"HTTP {response.status_code}: {response.text[:200]}"
            
            # Check if response is valid JSON
            try:
                data = response.json()
                
                # Special checks for specific endpoints
                if "/health" in url:
                    if not isinstance(data, dict) or data.get("status") != "healthy":
                        return False, f"Health check failed: {data}"
                elif "/venom-feed" in url:
                    if not isinstance(data, dict):
                        return False, f"Venom feed invalid format: {data}"
                    # Accept both error messages and valid data for venom-feed
                    # "No recent data available" is a valid response indicating service is up
                    valid_responses = ["Symbol required", "No recent data available"]
                    if "error" in data and data["error"] not in valid_responses:
                        if "Symbol required" not in data["error"] and "No recent data available" not in data["error"]:
                            return False, f"Venom feed error: {data['error']}"
                    
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON response: {str(e)}"
                
            return True, "OK"
            
        except requests.exceptions.Timeout:
            return False, f"Timeout after {timeout}s"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - service likely down"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def find_market_data_process(self) -> Optional[psutil.Process]:
        """Find the market data receiver process"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any(PROCESS_NAME in arg for arg in cmdline):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def kill_market_data_process(self) -> bool:
        """Kill the market data receiver process"""
        proc = self.find_market_data_process()
        if proc:
            try:
                logger.warning(f"Killing market data process PID {proc.pid}")
                proc.terminate()
                
                # Wait up to 10 seconds for graceful shutdown
                try:
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    logger.warning("Process didn't terminate gracefully, force killing")
                    proc.kill()
                    proc.wait(timeout=5)
                
                logger.info("Market data process terminated successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to kill process: {e}")
                return False
        else:
            logger.warning("Market data process not found")
            return True  # Consider it "killed" if not found
    
    def start_market_data_process(self) -> bool:
        """Start the market data receiver process"""
        try:
            # Change to the correct directory
            os.chdir('/root/HydraX-v2')
            
            # Start the process in background
            process = subprocess.Popen(
                ['python3', PROCESS_NAME],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            logger.info(f"Started market data process with PID {process.pid}")
            
            # Wait a moment to see if it starts successfully
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info("Market data process started successfully")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Process failed to start. STDOUT: {stdout.decode()[:500]}")
                logger.error(f"STDERR: {stderr.decode()[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start market data process: {e}")
            return False
    
    def restart_market_data_service(self) -> bool:
        """Kill and restart the market data service"""
        logger.critical("🚨 RESTARTING MARKET DATA SERVICE 🚨")
        
        # Kill existing process
        if not self.kill_market_data_process():
            logger.error("Failed to kill existing process")
            return False
        
        # Wait a moment before restart
        time.sleep(3)
        
        # Start new process
        if not self.start_market_data_process():
            logger.error("Failed to start new process")
            return False
        
        # Wait for service to be ready
        time.sleep(10)
        
        # Verify service is responding
        healthy, error = self.check_endpoint_health(HEALTH_ENDPOINTS[0], timeout=15)
        if healthy:
            logger.info("✅ Market data service restart successful")
            self.last_restart_time = datetime.now()
            self.total_restarts += 1
            self.consecutive_failures = 0
            return True
        else:
            logger.error(f"❌ Service still unhealthy after restart: {error}")
            return False
    
    def send_telegram_alert(self, message: str):
        """Send alert to user 7176191872 via Telegram bot"""
        try:
            # Import config loader
            sys.path.append('/root/HydraX-v2/src')
            from config_loader import get_bot_token
            
            bot_token = get_bot_token()
            
            # Send via Telegram API directly
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            alert_text = f"🚨 **MARKET DATA ALERT** 🚨\n\n{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\nServer: 134.199.204.67"
            
            payload = {
                'chat_id': ALERT_USER_ID,
                'text': alert_text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram alert sent successfully")
            else:
                logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                
        except FileNotFoundError:
            logger.error("Config file not found - cannot send Telegram alerts")
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    def run_health_check(self) -> bool:
        """Run comprehensive health check on all endpoints"""
        all_healthy = True
        errors = []
        
        for endpoint in HEALTH_ENDPOINTS:
            healthy, error = self.check_endpoint_health(endpoint)
            if not healthy:
                all_healthy = False
                errors.append(f"❌ {endpoint}: {error}")
                logger.error(f"Health check failed for {endpoint}: {error}")
            else:
                logger.debug(f"✅ {endpoint}: OK")
        
        if not all_healthy:
            self.consecutive_failures += 1
            logger.warning(f"Health check failed ({self.consecutive_failures} consecutive failures)")
            
            # Send alert on first failure and every 5th failure
            if self.consecutive_failures == 1 or self.consecutive_failures % 5 == 0:
                alert_message = f"Market Data Health Check Failed!\n\nConsecutive failures: {self.consecutive_failures}\n\nErrors:\n" + "\n".join(errors)
                self.send_telegram_alert(alert_message)
            
            # Restart after 2 consecutive failures
            if self.consecutive_failures >= 2:
                restart_success = self.restart_market_data_service()
                if restart_success:
                    self.send_telegram_alert(f"✅ Market data service restarted successfully after {self.consecutive_failures} failures.\n\nTotal restarts today: {self.total_restarts}")
                else:
                    self.send_telegram_alert(f"❌ CRITICAL: Failed to restart market data service!\n\nConsecutive failures: {self.consecutive_failures}\nManual intervention required!")
        else:
            if self.consecutive_failures > 0:
                logger.info(f"✅ Health check passed after {self.consecutive_failures} failures - service recovered")
                self.consecutive_failures = 0
        
        return all_healthy
    
    def run_forever(self):
        """Main watchdog loop"""
        logger.info("🐕 Market Data Watchdog started")
        logger.info(f"Monitoring endpoints: {HEALTH_ENDPOINTS}")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        logger.info(f"Alert user: {ALERT_USER_ID}")
        
        while True:
            try:
                logger.debug("Running health check...")
                self.run_health_check()
                
                # Log status every 10 minutes
                if int(time.time()) % 600 == 0:
                    logger.info(f"📊 Watchdog status: {self.consecutive_failures} consecutive failures, {self.total_restarts} total restarts")
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("🛑 Watchdog stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in watchdog loop: {e}")
                time.sleep(CHECK_INTERVAL)

def main():
    """Main entry point"""
    # Ensure log directory exists
    os.makedirs('/root/HydraX-v2/logs', exist_ok=True)
    
    # Create and run watchdog
    watchdog = MarketDataWatchdog()
    
    # Handle signals gracefully
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the watchdog
    watchdog.run_forever()

if __name__ == "__main__":
    main()