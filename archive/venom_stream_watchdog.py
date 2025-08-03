#!/usr/bin/env python3
"""
🐍 VENOM Stream Pipeline Watchdog
Monitors venom_stream_pipeline.py process health and ensures always running

Features:
- Intelligent PID-based process monitoring
- Auto-restart with crash frequency limits
- Telegram alerts on failures/recoveries
- CPU and memory resource monitoring
- Production-safe logging and error handling
"""

import os
import sys
import time
import signal
import psutil
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import requests

# Configuration
TARGET_SCRIPT = "venom_stream_pipeline.py"
TARGET_PATH = "/root/HydraX-v2/venom_stream_pipeline.py"
LOG_FILE = "/tmp/venom_stream_watchdog.log"
PID_FILE = "/tmp/venom_stream_watchdog.pid"

# Monitoring settings
CHECK_INTERVAL = 30  # Check every 30 seconds
MAX_RESTARTS_PER_HOUR = 10  # Limit restart frequency
RESTART_COOLDOWN = 60  # Wait 60s between restart attempts

# Resource limits for monitoring
MAX_CPU_PERCENT = 80  # Alert if process uses >80% CPU
MAX_MEMORY_MB = 1024  # Alert if process uses >1GB RAM

# Telegram notification settings
COMMANDER_USER_ID = "7176191872"
try:
    sys.path.append('/root/HydraX-v2')
    from config_loader import get_bot_token
    BOT_TOKEN = get_bot_token()
except Exception:
    BOT_TOKEN = None
    print("⚠️ Warning: Could not load bot token - Telegram alerts disabled")

class VenomStreamWatchdog:
    """VENOM Stream Pipeline Process Watchdog"""
    
    def __init__(self):
        self.is_running = True
        self.restart_history = []  # Track restart times
        self.alert_sent_recently = False
        self.last_alert_time = None
        self.setup_logging()
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🐍 VENOM Stream Watchdog initialized")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"📡 Received signal {signum} - initiating graceful shutdown")
        self.is_running = False
        
    def write_pid_file(self):
        """Write watchdog PID to file"""
        try:
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"📝 Watchdog PID {os.getpid()} written to {PID_FILE}")
        except Exception as e:
            self.logger.error(f"❌ Failed to write PID file: {e}")
            
    def remove_pid_file(self):
        """Remove PID file on shutdown"""
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
                self.logger.info("🗑️ Watchdog PID file removed")
        except Exception as e:
            self.logger.error(f"❌ Failed to remove PID file: {e}")
            
    def find_venom_process(self):
        """Find VENOM stream pipeline process"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any(TARGET_SCRIPT in str(arg) for arg in cmdline):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None
        
    def check_process_health(self, process):
        """Check if process is healthy and within resource limits"""
        try:
            # Check if process is still running
            if not process.is_running():
                return False, "Process is not running"
                
            # Check CPU usage
            cpu_percent = process.cpu_percent()
            if cpu_percent > MAX_CPU_PERCENT:
                self.logger.warning(f"⚠️ High CPU usage: {cpu_percent:.1f}%")
                
            # Check memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > MAX_MEMORY_MB:
                self.logger.warning(f"⚠️ High memory usage: {memory_mb:.1f}MB")
                
            return True, "Process healthy"
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False, "Process no longer accessible"
            
    def can_restart(self):
        """Check if we can restart based on frequency limits"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        
        # Remove old restart records
        self.restart_history = [t for t in self.restart_history if t > cutoff]
        
        # Check if we're within limits
        if len(self.restart_history) >= MAX_RESTARTS_PER_HOUR:
            self.logger.error(f"🚨 Restart limit exceeded: {len(self.restart_history)} restarts in past hour")
            return False
            
        return True
        
    def start_venom_process(self):
        """Start the VENOM stream pipeline process"""
        try:
            if not os.path.exists(TARGET_PATH):
                self.logger.error(f"❌ Target script not found: {TARGET_PATH}")
                return False
                
            self.logger.info(f"🚀 Starting VENOM stream pipeline: {TARGET_PATH}")
            
            # Start process in background
            process = subprocess.Popen(
                [sys.executable, TARGET_PATH],
                cwd="/root/HydraX-v2",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Wait a moment to ensure it started
            time.sleep(5)
            
            # Verify it's running
            venom_proc = self.find_venom_process()
            if venom_proc:
                self.restart_history.append(datetime.now())
                self.logger.info(f"✅ VENOM stream pipeline started successfully (PID: {venom_proc.pid})")
                return True
            else:
                self.logger.error("❌ VENOM stream pipeline failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start VENOM process: {e}")
            return False
            
    def send_telegram_alert(self, message):
        """Send Telegram alert to commander"""
        if not BOT_TOKEN:
            self.logger.warning("⚠️ No bot token - skipping Telegram alert")
            return
            
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': COMMANDER_USER_ID,
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
            
    def format_failure_alert(self, restart_count):
        """Format process failure alert"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"""🐍 **VENOM Stream Pipeline Alert**

**Status**: Process failure detected
**Time**: {timestamp}
**Script**: `{TARGET_SCRIPT}`
**Restart Count**: #{restart_count}
**Server**: HydraX-v2 Production

**Action**: Attempting automatic restart...
**Watchdog**: Active and monitoring"""
        
        return message
        
    def format_recovery_alert(self, new_pid):
        """Format successful recovery alert"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"""✅ **VENOM Stream Pipeline Recovered**

**Status**: Process restarted successfully
**Time**: {timestamp}
**New PID**: {new_pid}
**Script**: `{TARGET_SCRIPT}`

**Watchdog**: Monitoring resumed
**Signal Generation**: Operational"""
        
        return message
        
    def format_persistent_failure_alert(self):
        """Format alert for persistent failures"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        restart_count = len(self.restart_history)
        
        message = f"""🚨 **VENOM Stream Pipeline - CRITICAL**

**Status**: Persistent crash detected
**Time**: {timestamp}
**Restart Attempts**: {restart_count} in past hour
**Limit**: {MAX_RESTARTS_PER_HOUR} restarts/hour

**Issue**: Process repeatedly crashing
**Action Required**: Manual investigation needed

Please check server logs and VENOM configuration."""
        
        return message
        
    def should_send_alert(self):
        """Determine if we should send an alert (avoid spam)"""
        now = datetime.now()
        
        # Send first failure alert
        if not self.alert_sent_recently:
            return True
            
        # Send alert every 30 minutes for persistent issues
        if self.last_alert_time and (now - self.last_alert_time).seconds > 1800:
            return True
            
        return False
        
    def run(self):
        """Main watchdog monitoring loop"""
        self.write_pid_file()
        self.logger.info(f"🐕 VENOM Stream Watchdog starting (PID: {os.getpid()})")
        self.logger.info(f"🎯 Target: {TARGET_SCRIPT}")
        self.logger.info(f"⏱️ Check interval: {CHECK_INTERVAL}s")
        
        # Initial process check
        venom_proc = self.find_venom_process()
        if not venom_proc:
            self.logger.warning("⚠️ VENOM stream pipeline not running - starting initial instance")
            if self.start_venom_process():
                self.send_telegram_alert("🐍 **VENOM Stream Pipeline Started**\n\nWatchdog initialized and process started successfully.")
        else:
            self.logger.info(f"✅ VENOM stream pipeline already running (PID: {venom_proc.pid})")
            
        # Main monitoring loop
        try:
            while self.is_running:
                time.sleep(CHECK_INTERVAL)
                
                if not self.is_running:
                    break
                    
                # Find current process
                venom_proc = self.find_venom_process()
                
                if not venom_proc:
                    # Process is dead
                    restart_count = len(self.restart_history) + 1
                    self.logger.error(f"❌ VENOM stream pipeline has died - attempt restart #{restart_count}")
                    
                    # Send failure alert if appropriate
                    if self.should_send_alert():
                        self.send_telegram_alert(self.format_failure_alert(restart_count))
                        self.alert_sent_recently = True
                        self.last_alert_time = datetime.now()
                    
                    # Check if we can restart
                    if self.can_restart():
                        time.sleep(RESTART_COOLDOWN)  # Brief cooldown
                        
                        if self.start_venom_process():
                            # Success - send recovery alert
                            new_proc = self.find_venom_process()
                            if new_proc:
                                self.send_telegram_alert(self.format_recovery_alert(new_proc.pid))
                                self.alert_sent_recently = False  # Reset alert flag
                        else:
                            self.logger.error("💀 Failed to restart VENOM stream pipeline")
                    else:
                        # Hit restart limit - send critical alert
                        self.send_telegram_alert(self.format_persistent_failure_alert())
                        self.logger.critical("🚨 Too many restart attempts - waiting before next attempt")
                        time.sleep(CHECK_INTERVAL * 10)  # Extended wait
                        
                else:
                    # Process is running - check health
                    healthy, status = self.check_process_health(venom_proc)
                    if healthy:
                        self.logger.debug(f"✅ VENOM stream pipeline healthy (PID: {venom_proc.pid})")
                        self.alert_sent_recently = False  # Reset alert flag when healthy
                    else:
                        self.logger.warning(f"⚠️ VENOM stream pipeline health issue: {status}")
                        
        except KeyboardInterrupt:
            self.logger.info("🛑 Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"❌ Watchdog error: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Cleanup on shutdown"""
        self.logger.info("🧹 VENOM Stream Watchdog shutting down")
        self.remove_pid_file()
        
        # Send shutdown notification
        shutdown_msg = f"""🐕 **VENOM Stream Watchdog Shutdown**

**Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
**Total Restarts**: {len(self.restart_history)}

⚠️ **Warning**: VENOM stream pipeline no longer monitored
**Action Required**: Restart watchdog to resume monitoring"""

        self.send_telegram_alert(shutdown_msg)
        self.logger.info("🏁 VENOM Stream Watchdog shutdown complete")

def main():
    """Main entry point"""
    try:
        # Check if already running
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                if psutil.pid_exists(old_pid):
                    print(f"❌ Another watchdog is already running (PID: {old_pid})")
                    sys.exit(1)
                else:
                    os.remove(PID_FILE)  # Remove stale PID file
            except (ValueError, IOError):
                os.remove(PID_FILE)  # Remove invalid PID file
                
        watchdog = VenomStreamWatchdog()
        watchdog.run()
        
    except Exception as e:
        print(f"❌ Fatal watchdog error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()