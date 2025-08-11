#!/usr/bin/env python3
"""
HUD WebApp Watchdog Script
Monitors webapp_server_optimized.py on port 8888 and restarts it if needed.
"""

import os
import sys
import time
import requests
import subprocess
import signal
import logging
from datetime import datetime
from typing import Optional, List
import psutil

# Configuration
WEBAPP_PORT = 8888
WEBAPP_SCRIPT = "/root/HydraX-v2/webapp_server_optimized.py"
HEALTH_CHECK_URL = f"http://localhost:{WEBAPP_PORT}/hud?signal=TEST_SIGNAL"
HEALTH_CHECK_TIMEOUT = 5
CHECK_INTERVAL = 60
LOG_FILE = "/tmp/hud_watchdog.log"
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = "7176191872"
PID_FILE = "/tmp/hud_watchdog.pid"

class HUDWatchdog:
    """Watchdog to monitor and restart the HUD WebApp server"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.restart_count = 0
        
    def setup_logging(self):
        """Configure logging to file and console"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def check_single_instance(self) -> bool:
        """Ensure only one watchdog instance is running"""
        try:
            if os.path.exists(PID_FILE):
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if old process is still running
                try:
                    os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                    self.logger.error(f"Another watchdog instance is already running (PID: {old_pid})")
                    return False
                except OSError:
                    # Process doesn't exist, remove stale PID file
                    os.remove(PID_FILE)
            
            # Write current PID
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking single instance: {e}")
            return False
    
    def cleanup_pid_file(self):
        """Remove PID file on exit"""
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception as e:
            self.logger.error(f"Error removing PID file: {e}")
    
    def check_health(self) -> tuple[bool, int, str]:
        """
        Check if the WebApp server is healthy
        Returns: (is_healthy, status_code, error_message)
        """
        try:
            response = requests.get(
                HEALTH_CHECK_URL,
                timeout=HEALTH_CHECK_TIMEOUT,
                allow_redirects=False
            )
            
            # Accept 200 (success), 404 (expected for TEST_SIGNAL), or 400 (bad request)
            if response.status_code in [200, 404, 400]:
                return True, response.status_code, "OK"
            else:
                return False, response.status_code, f"Unexpected status code: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, 0, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, 0, "Connection error - server likely down"
        except Exception as e:
            return False, 0, f"Health check error: {str(e)}"
    
    def find_webapp_processes(self) -> List[psutil.Process]:
        """Find all running webapp_server_optimized.py processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('webapp_server_optimized.py' in arg for arg in cmdline):
                        processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error finding webapp processes: {e}")
        
        return processes
    
    def kill_webapp_processes(self) -> bool:
        """Kill all existing webapp_server_optimized.py processes"""
        try:
            processes = self.find_webapp_processes()
            
            if not processes:
                self.logger.info("No existing webapp processes found")
                return True
            
            for proc in processes:
                try:
                    self.logger.info(f"Killing webapp process PID: {proc.pid}")
                    proc.terminate()
                    
                    # Wait up to 10 seconds for graceful termination
                    try:
                        proc.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        self.logger.warning(f"Process {proc.pid} didn't terminate gracefully, force killing")
                        proc.kill()
                        proc.wait(timeout=5)
                    
                except psutil.NoSuchProcess:
                    self.logger.info(f"Process {proc.pid} already terminated")
                except Exception as e:
                    self.logger.error(f"Error killing process {proc.pid}: {e}")
            
            # Wait a moment for processes to fully terminate
            time.sleep(2)
            
            # Verify all processes are gone
            remaining = self.find_webapp_processes()
            if remaining:
                self.logger.error(f"Failed to kill all processes: {[p.pid for p in remaining]}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in kill_webapp_processes: {e}")
            return False
    
    def start_webapp(self) -> bool:
        """Start the webapp server"""
        try:
            if not os.path.exists(WEBAPP_SCRIPT):
                self.logger.error(f"WebApp script not found: {WEBAPP_SCRIPT}")
                return False
            
            # Start the webapp server in background
            cmd = [sys.executable, WEBAPP_SCRIPT]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.logger.info(f"Started webapp server with PID: {proc.pid}")
            
            # Wait a moment for startup
            time.sleep(3)
            
            # Verify the process is still running
            if proc.poll() is None:
                self.logger.info("WebApp server started successfully")
                return True
            else:
                self.logger.error(f"WebApp server failed to start (exit code: {proc.returncode})")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting webapp: {e}")
            return False
    
    def restart_webapp(self) -> bool:
        """Restart the webapp server"""
        self.logger.info("Restarting webapp server...")
        self.restart_count += 1
        
        # Step 1: Kill existing processes
        if not self.kill_webapp_processes():
            self.logger.error("Failed to kill existing webapp processes")
            return False
        
        # Step 2: Start new process
        if not self.start_webapp():
            self.logger.error("Failed to start new webapp process")
            return False
        
        # Step 3: Wait and verify health
        self.logger.info("Waiting for webapp to become healthy...")
        time.sleep(5)
        
        for attempt in range(3):
            is_healthy, status_code, message = self.check_health()
            if is_healthy:
                self.logger.info(f"WebApp restarted successfully (status: {status_code})")
                return True
            else:
                self.logger.warning(f"Health check failed after restart (attempt {attempt + 1}): {message}")
                time.sleep(2)
        
        self.logger.error("WebApp failed to become healthy after restart")
        return False
    
    def send_telegram_alert(self, message: str) -> bool:
        """Send alert to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Telegram alert sent successfully")
                return True
            else:
                self.logger.error(f"Telegram alert failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    def run_check_cycle(self):
        """Run a single check cycle"""
        self.logger.debug("Running health check...")
        
        is_healthy, status_code, message = self.check_health()
        
        if is_healthy:
            self.logger.debug(f"Health check passed (status: {status_code})")
            return
        
        # Health check failed
        self.logger.warning(f"Health check failed: {message} (status: {status_code})")
        
        # Attempt restart
        restart_success = self.restart_webapp()
        
        # Send Telegram alert
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        if restart_success:
            alert_message = f"⚠️ HUD WebApp was down. Restarted by watchdog at {timestamp}.\n\n" \
                          f"Restart #{self.restart_count} - Server is now healthy."
        else:
            alert_message = f"🚨 HUD WebApp is down and restart FAILED at {timestamp}.\n\n" \
                          f"Restart attempt #{self.restart_count} failed. Manual intervention needed."
        
        self.send_telegram_alert(alert_message)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.cleanup_pid_file()
        sys.exit(0)
    
    def run(self):
        """Main watchdog loop"""
        if not self.check_single_instance():
            sys.exit(1)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("🐕 HUD Watchdog started")
        self.logger.info(f"Monitoring: {HEALTH_CHECK_URL}")
        self.logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        
        try:
            while True:
                try:
                    self.run_check_cycle()
                except Exception as e:
                    self.logger.error(f"Error in check cycle: {e}")
                
                # Wait for next check
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            self.logger.info("Watchdog stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup_pid_file()

def main():
    """Main entry point"""
    try:
        watchdog = HUDWatchdog()
        watchdog.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()