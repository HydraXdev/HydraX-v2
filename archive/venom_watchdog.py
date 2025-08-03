#!/usr/bin/env python3
"""
🐍 VENOM Watchdog Daemon - Process Guardian
Monitors venom_stream_pipeline.py process health and auto-restarts on failure

Features:
- 60-second monitoring interval
- Automatic process restart with logging
- Telegram alert notifications
- Duplicate launch protection
- Comprehensive error handling
- Persistent log file tracking
"""

import os
import sys
import time
import logging
import psutil
import subprocess
import threading
import signal
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import requests

# Add HydraX paths
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

# Configuration
SCRIPT_NAME = "venom_stream_pipeline.py"
SCRIPT_PATH = "/root/HydraX-v2/venom_stream_pipeline.py"
LOG_FILE = "/tmp/venom_watchdog.log"
PID_FILE = "/root/HydraX-v2/infra/venom_watchdog.pid"
CHECK_INTERVAL = 60  # seconds
OPERATOR_USER_ID = "7176191872"  # Telegram user ID for alerts

# Bot token for notifications
BOT_TOKEN = None
try:
    from config_loader import get_bot_token
    BOT_TOKEN = get_bot_token()
except:
    print("⚠️ Could not load bot token - Telegram alerts disabled")

class VenomWatchdog:
    """VENOM Engine Process Watchdog"""
    
    def __init__(self):
        self.is_running = True
        self.restart_count = 0
        self.last_restart = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging with both file and console output"""
        # Ensure log directory exists
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('VenomWatchdog')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplication
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("🐕 VENOM Watchdog initialized")
    
    def check_duplicate_process(self) -> bool:
        """Check if another watchdog is already running"""
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if PID is still running
                if psutil.pid_exists(old_pid):
                    try:
                        proc = psutil.Process(old_pid)
                        if 'venom_watchdog' in proc.name() or 'venom_watchdog' in ' '.join(proc.cmdline()):
                            self.logger.error(f"❌ Another watchdog is already running (PID: {old_pid})")
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Remove stale PID file
                os.remove(PID_FILE)
                self.logger.info(f"🧹 Removed stale PID file (PID {old_pid} not running)")
                
            except (ValueError, IOError) as e:
                self.logger.warning(f"⚠️ Error reading PID file: {e}")
                try:
                    os.remove(PID_FILE)
                except:
                    pass
        
        return False
    
    def write_pid_file(self):
        """Write current process PID to file"""
        try:
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"📝 PID file created: {PID_FILE}")
        except IOError as e:
            self.logger.error(f"❌ Failed to write PID file: {e}")
    
    def remove_pid_file(self):
        """Remove PID file on shutdown"""
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
                self.logger.info("🗑️ PID file removed")
        except IOError as e:
            self.logger.error(f"❌ Failed to remove PID file: {e}")
    
    def find_venom_processes(self) -> List[psutil.Process]:
        """Find all running VENOM processes"""
        venom_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any(SCRIPT_NAME in arg for arg in cmdline):
                    venom_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return venom_processes
    
    def is_venom_running(self) -> bool:
        """Check if VENOM process is running"""
        processes = self.find_venom_processes()
        return len(processes) > 0
    
    def kill_zombie_processes(self):
        """Kill any zombie or stuck VENOM processes"""
        processes = self.find_venom_processes()
        for proc in processes:
            try:
                self.logger.warning(f"🧟 Killing zombie VENOM process (PID: {proc.pid})")
                proc.terminate()
                time.sleep(2)
                if proc.is_running():
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    def start_venom_engine(self) -> bool:
        """Start the VENOM engine process"""
        try:
            # Verify script exists
            if not os.path.exists(SCRIPT_PATH):
                self.logger.error(f"❌ VENOM script not found: {SCRIPT_PATH}")
                return False
            
            # Kill any existing processes first
            self.kill_zombie_processes()
            time.sleep(2)
            
            # Start new process
            self.logger.info(f"🚀 Starting VENOM engine: {SCRIPT_PATH}")
            
            # Use subprocess.Popen with proper detachment
            process = subprocess.Popen(
                [sys.executable, SCRIPT_PATH],
                cwd="/root/HydraX-v2",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent
            )
            
            # Wait a moment to check if process started successfully
            time.sleep(3)
            
            if self.is_venom_running():
                self.restart_count += 1
                self.last_restart = datetime.now()
                self.logger.info(f"✅ VENOM engine started successfully (Restart #{self.restart_count})")
                return True
            else:
                self.logger.error("❌ VENOM engine failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start VENOM engine: {e}")
            return False
    
    def send_telegram_alert(self, message: str):
        """Send Telegram alert to operator"""
        if not BOT_TOKEN:
            self.logger.warning("⚠️ No bot token available - skipping Telegram alert")
            return
        
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': OPERATOR_USER_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("📱 Telegram alert sent successfully")
            else:
                self.logger.error(f"❌ Telegram alert failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to send Telegram alert: {e}")
    
    def format_restart_alert(self) -> str:
        """Format restart alert message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"""🐍 **VENOM Engine Restart Alert**

**Status**: Engine restarted automatically
**Time**: {timestamp}
**Restart Count**: #{self.restart_count}
**Script**: `{SCRIPT_NAME}`
**Server**: HydraX-v2 Production

**Watchdog**: Process monitoring active ✅
**Next Check**: {CHECK_INTERVAL} seconds

The VENOM engine has been restored and is generating signals."""
        
        return message
    
    def format_startup_alert(self) -> str:
        """Format watchdog startup alert"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"""🐕 **VENOM Watchdog Started**

**Time**: {timestamp}
**Monitor**: `{SCRIPT_NAME}`
**Check Interval**: {CHECK_INTERVAL}s
**Log File**: `venom_watchdog.log`

**Status**: Guardian active and monitoring VENOM engine health."""
        
        return message
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received signal {signum} - shutting down gracefully")
        self.is_running = False
    
    def run(self):
        """Main watchdog monitoring loop"""
        # Check for duplicate process
        if self.check_duplicate_process():
            sys.exit(1)
        
        # Write PID file
        self.write_pid_file()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Send startup alert
        self.send_telegram_alert(self.format_startup_alert())
        
        self.logger.info(f"🐕 Starting VENOM watchdog monitoring (PID: {os.getpid()})")
        self.logger.info(f"📊 Check interval: {CHECK_INTERVAL} seconds")
        self.logger.info(f"🎯 Target script: {SCRIPT_NAME}")
        
        # Initial check and start if needed
        if not self.is_venom_running():
            self.logger.warning("⚠️ VENOM engine not running - starting initial instance")
            if self.start_venom_engine():
                self.send_telegram_alert(self.format_restart_alert())
        else:
            self.logger.info("✅ VENOM engine already running")
        
        # Main monitoring loop
        try:
            while self.is_running:
                time.sleep(CHECK_INTERVAL)
                
                if not self.is_running:
                    break
                
                # Check process health
                if not self.is_venom_running():
                    self.logger.error("❌ VENOM engine process has died - restarting")
                    
                    if self.start_venom_engine():
                        self.send_telegram_alert(self.format_restart_alert())
                    else:
                        self.logger.error("💀 Failed to restart VENOM engine")
                        
                        # Send failure alert
                        failure_msg = f"""🚨 **VENOM Engine Restart FAILED**

**Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
**Issue**: Unable to restart VENOM engine
**Action Required**: Manual intervention needed

Please check the server and logs immediately."""
                        
                        self.send_telegram_alert(failure_msg)
                        
                        # Wait longer before next attempt
                        time.sleep(CHECK_INTERVAL * 2)
                else:
                    # Process is healthy
                    processes = self.find_venom_processes()
                    self.logger.debug(f"✅ VENOM engine healthy ({len(processes)} processes)")
        
        except KeyboardInterrupt:
            self.logger.info("🛑 Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"❌ Watchdog error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup on shutdown"""
        self.logger.info("🧹 Cleaning up watchdog")
        self.remove_pid_file()
        
        # Send shutdown alert
        shutdown_msg = f"""🐕 **VENOM Watchdog Shutdown**

**Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
**Total Restarts**: {self.restart_count}
**Status**: Watchdog stopped - VENOM engine no longer monitored

⚠️ **Action Required**: Restart watchdog to resume monitoring."""

        self.send_telegram_alert(shutdown_msg)
        self.logger.info("🏁 VENOM Watchdog shutdown complete")

def main():
    """Main entry point"""
    try:
        watchdog = VenomWatchdog()
        watchdog.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()