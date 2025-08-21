#!/usr/bin/env python3
"""
Telemetry Bridge Watchdog
Monitors data flow and auto-restarts bridge if frozen
"""

import subprocess
import json
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TelemetryWatchdog - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

class TelemetryWatchdog:
    def __init__(self):
        self.last_signal_time = None
        self.last_tick_count = 0
        self.freeze_count = 0
        self.restart_count = 0
        
    def check_signal_activity(self):
        """Check if signals are being generated"""
        try:
            # Check the last line of optimized_tracking.jsonl
            result = subprocess.run(
                ["tail", "-1", "/root/HydraX-v2/optimized_tracking.jsonl"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                data = json.loads(result.stdout.strip())
                timestamp = data.get('timestamp', '')
                
                # Parse timestamp and check if recent
                if timestamp:
                    signal_time = datetime.fromisoformat(timestamp)
                    current_time = datetime.now()
                    time_diff = (current_time - signal_time).total_seconds()
                    
                    # If last signal is older than 10 minutes during market hours
                    if time_diff > 600:  # 10 minutes
                        logger.warning(f"⚠️ No signals for {int(time_diff/60)} minutes")
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Error checking signals: {e}")
            return True  # Don't restart on check errors
            
    def check_telemetry_logs(self):
        """Check if telemetry bridge is processing messages"""
        try:
            # Get last 10 lines of telemetry logs
            result = subprocess.run(
                ["pm2", "logs", "zmq_telemetry_bridge", "--lines", "10", "--nostream"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout
            
            # Check for recent activity
            if "Message" in output or "TICK" in output or "Heartbeat" in output:
                return True
                
            # Check for error patterns
            if "KeyboardInterrupt" in output or "recv" in output and "stuck" in output:
                logger.error("🔴 Telemetry bridge appears stuck!")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking logs: {e}")
            return True
            
    def get_process_info(self):
        """Get PM2 process information"""
        try:
            result = subprocess.run(
                ["pm2", "jlist"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout:
                processes = json.loads(result.stdout)
                for proc in processes:
                    if "telemetry" in proc.get('name', '').lower():
                        return {
                            'status': proc.get('pm2_env', {}).get('status'),
                            'restarts': proc.get('pm2_env', {}).get('restart_time', 0),
                            'uptime': proc.get('pm2_env', {}).get('pm_uptime', 0),
                            'cpu': proc.get('monit', {}).get('cpu', 0),
                            'memory': proc.get('monit', {}).get('memory', 0)
                        }
            return None
            
        except Exception as e:
            logger.error(f"Error getting process info: {e}")
            return None
            
    def restart_telemetry_bridge(self):
        """Restart the telemetry bridge"""
        logger.warning("🔄 Restarting telemetry bridge...")
        
        try:
            # Restart via PM2
            subprocess.run(
                ["pm2", "restart", "zmq_telemetry_bridge"],
                capture_output=True,
                timeout=10
            )
            
            self.restart_count += 1
            logger.info(f"✅ Bridge restarted (count: {self.restart_count})")
            
            # Wait for it to stabilize
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to restart bridge: {e}")
            return False
            
    def monitor(self):
        """Main monitoring loop"""
        logger.info("🔍 Starting telemetry watchdog...")
        
        consecutive_failures = 0
        last_check = time.time()
        
        while True:
            try:
                # Check every 30 seconds
                time.sleep(30)
                
                # Get process info
                proc_info = self.get_process_info()
                
                if proc_info:
                    status = proc_info.get('status')
                    uptime = proc_info.get('uptime', 0) / 1000  # Convert to seconds
                    restarts = proc_info.get('restarts', 0)
                    
                    # Log status
                    logger.info(f"📊 Bridge status: {status}, uptime: {int(uptime)}s, restarts: {restarts}")
                    
                    # Check if process is stopped
                    if status != 'online':
                        logger.error("🔴 Bridge is not online!")
                        self.restart_telemetry_bridge()
                        consecutive_failures = 0
                        continue
                        
                    # Check for recent restarts (sign of crashes)
                    if restarts > self.restart_count + 5:
                        logger.warning(f"⚠️ Bridge has restarted {restarts - self.restart_count} times")
                        self.restart_count = restarts
                        
                # Check log activity
                if not self.check_telemetry_logs():
                    consecutive_failures += 1
                    logger.warning(f"⚠️ Bridge appears stuck (failure {consecutive_failures}/3)")
                    
                    # Restart after 3 consecutive failures
                    if consecutive_failures >= 3:
                        self.restart_telemetry_bridge()
                        consecutive_failures = 0
                else:
                    consecutive_failures = 0
                    
                # Check signal generation (less frequent)
                if time.time() - last_check > 300:  # Every 5 minutes
                    if not self.check_signal_activity():
                        logger.warning("⚠️ Signal generation may be affected")
                    last_check = time.time()
                    
            except KeyboardInterrupt:
                logger.info("🛑 Watchdog stopped by user")
                break
                
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    watchdog = TelemetryWatchdog()
    watchdog.monitor()