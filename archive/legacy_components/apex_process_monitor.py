#!/usr/bin/env python3
"""
Process Monitor
Continuously monitors for duplicate processes and kills them
Can be run as a systemd service or cron job
"""

import time
import logging
import psutil
from datetime import datetime
from apex_singleton_manager import SingletonManager

class ProcessMonitor:
    def __init__(self):
        self.setup_logging()
        self.manager = SingletonManager()
        self.check_interval = 30  # seconds
        self.last_check = None
        self.violations_found = 0
        
    def setup_logging(self):
        """Setup monitoring logger"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - _MONITOR - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/apex_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("_MONITOR")
    
    def check_for_duplicates(self) -> int:
        """Check for and kill duplicate processes"""
        processes = self.manager.find_apex_processes()
        
        if len(processes) == 0:
            self.logger.info("✅ No processes running")
            return 0
        elif len(processes) == 1:
            self.logger.info(f"✅ Single process running (PID: {processes[0].pid})")
            return 0
        else:
            self.logger.warning(f"⚠️ Found {len(processes)} processes!")
            
            # Find the legitimate process (with lock file)
            legitimate_pid = self.manager.read_pid_file()
            
            if legitimate_pid and self.manager.is_process_running(legitimate_pid):
                # Kill all except the legitimate one
                killed = self.manager.kill_existing_processes(exclude_pid=legitimate_pid)
                self.logger.info(f"🎯 Killed {killed} duplicate processes, kept PID {legitimate_pid}")
                self.violations_found += 1
                return killed
            else:
                # No legitimate process found, kill all but the oldest
                processes.sort(key=lambda p: p.create_time())
                oldest = processes[0]
                
                killed = self.manager.kill_existing_processes(exclude_pid=oldest.pid)
                self.logger.info(f"🎯 No legitimate process found. Kept oldest (PID: {oldest.pid}), killed {killed} others")
                self.violations_found += 1
                return killed
    
    def run_monitoring(self):
        """Run continuous monitoring"""
        self.logger.info("🚀 Starting Process Monitor")
        self.logger.info(f"📊 Check interval: {self.check_interval} seconds")
        
        while True:
            try:
                self.last_check = datetime.now()
                killed = self.check_for_duplicates()
                
                if killed > 0:
                    self.logger.warning(f"⚡ Action taken: Killed {killed} duplicate processes")
                    self.logger.warning(f"📈 Total violations found: {self.violations_found}")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Monitor stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Error during monitoring: {e}")
                time.sleep(self.check_interval)
        
        self.logger.info(f"📊 Final stats: {self.violations_found} violations found and fixed")

def main():
    """Main entry point"""
    monitor = ProcessMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()