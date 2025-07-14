#!/usr/bin/env python3
"""
BITTEN System Supervisor
Ensures ALL components stay running 24/7
"""

import os
import sys
import time
import json
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/supervisor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BITTENSupervisor:
    """Supervises all BITTEN components to ensure 24/7 operation"""
    
    def __init__(self):
        self.components = {
            'webapp': {
                'name': 'BITTEN WebApp',
                'check_cmd': 'systemctl status bitten-webapp',
                'start_cmd': 'systemctl start bitten-webapp',
                'restart_cmd': 'systemctl restart bitten-webapp',
                'port': 3000,
                'critical': True
            },
            'signal_engine': {
                'name': 'Signal Engine',
                'process_name': 'python3',
                'script': 'start_bitten_live_signals.py',
                'start_cmd': 'python3 start_bitten_live_signals.py',
                'critical': True
            },
            'mt5_bridge': {
                'name': 'MT5 Bridge',
                'file_check': '/path/to/mt5/bitten_heartbeat.txt',
                'max_age': 30,  # seconds
                'critical': True
            },
            'database': {
                'name': 'PostgreSQL',
                'check_cmd': 'pg_isready',
                'start_cmd': 'systemctl start postgresql',
                'critical': True
            },
            'telegram_bot': {
                'name': 'Telegram Bot',
                'process_name': 'python3',
                'script': 'telegram_bot.py',
                'critical': True
            }
        }
        
        self.check_interval = 30  # seconds
        self.is_running = True
        self.failures = {}
        self.alerts_sent = {}
        
    def start(self):
        """Start the supervisor"""
        logger.info("🛡️ BITTEN System Supervisor starting...")
        
        # Initial system check
        self.full_system_check()
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        threading.Thread(target=self._health_check_loop, daemon=True).start()
        threading.Thread(target=self._log_monitor_loop, daemon=True).start()
        
        logger.info("✅ Supervisor started - 24/7 monitoring active")
        
        # Keep main thread alive
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Supervisor stopped by user")
            self.is_running = False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                for component_id, config in self.components.items():
                    if not self._check_component(component_id, config):
                        self._handle_component_failure(component_id, config)
                    else:
                        # Reset failure count if working
                        self.failures[component_id] = 0
                        self.alerts_sent[component_id] = False
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(10)
    
    def _check_component(self, component_id: str, config: dict) -> bool:
        """Check if a component is healthy"""
        try:
            # Port check
            if 'port' in config:
                return self._check_port(config['port'])
            
            # Process check
            elif 'process_name' in config:
                return self._check_process(config['process_name'], config.get('script'))
            
            # Command check
            elif 'check_cmd' in config:
                return self._check_command(config['check_cmd'])
            
            # File age check
            elif 'file_check' in config:
                return self._check_file_age(config['file_check'], config['max_age'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking {component_id}: {e}")
            return False
    
    def _check_port(self, port: int) -> bool:
        """Check if a port is listening"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
        return False
    
    def _check_process(self, process_name: str, script: str = None) -> bool:
        """Check if a process is running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if process_name in proc.info['name']:
                    if script:
                        cmdline = ' '.join(proc.info.get('cmdline', []))
                        if script in cmdline:
                            return True
                    else:
                        return True
            except:
                continue
        return False
    
    def _check_command(self, command: str) -> bool:
        """Check command exit status"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_file_age(self, filepath: str, max_age: int) -> bool:
        """Check if file was updated recently"""
        try:
            if os.path.exists(filepath):
                age = time.time() - os.path.getmtime(filepath)
                return age < max_age
        except:
            pass
        return False
    
    def _handle_component_failure(self, component_id: str, config: dict):
        """Handle component failure"""
        # Track failures
        self.failures[component_id] = self.failures.get(component_id, 0) + 1
        failure_count = self.failures[component_id]
        
        logger.warning(f"Component {config['name']} failed (attempt #{failure_count})")
        
        # Send alert if not already sent
        if not self.alerts_sent.get(component_id, False):
            self._send_alert(f"{config['name']} DOWN", f"Component failed {failure_count} times")
            self.alerts_sent[component_id] = True
        
        # Try to restart if critical
        if config.get('critical', False) and failure_count <= 3:
            self._restart_component(component_id, config)
    
    def _restart_component(self, component_id: str, config: dict):
        """Attempt to restart a component"""
        logger.info(f"Attempting to restart {config['name']}...")
        
        try:
            # Try restart command first
            if 'restart_cmd' in config:
                subprocess.run(config['restart_cmd'], shell=True)
                time.sleep(10)
            
            # Otherwise try start command
            elif 'start_cmd' in config:
                subprocess.run(config['start_cmd'], shell=True)
                time.sleep(10)
            
            # Check if restart worked
            if self._check_component(component_id, config):
                logger.info(f"✅ {config['name']} restarted successfully")
                self.failures[component_id] = 0
            else:
                logger.error(f"❌ Failed to restart {config['name']}")
                
        except Exception as e:
            logger.error(f"Error restarting {config['name']}: {e}")
    
    def _health_check_loop(self):
        """Periodic health checks"""
        while self.is_running:
            try:
                # Check system resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Alert on high usage
                if cpu_percent > 90:
                    self._send_alert("High CPU", f"CPU usage: {cpu_percent}%")
                
                if memory.percent > 90:
                    self._send_alert("High Memory", f"Memory usage: {memory.percent}%")
                
                if disk.percent > 90:
                    self._send_alert("Low Disk", f"Disk usage: {disk.percent}%")
                
                # Log stats
                logger.debug(f"System: CPU={cpu_percent}%, MEM={memory.percent}%, DISK={disk.percent}%")
                
                time.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(60)
    
    def _log_monitor_loop(self):
        """Monitor logs for errors"""
        while self.is_running:
            try:
                # Check various log files for errors
                log_files = [
                    'logs/live_signals.log',
                    'logs/webapp.log',
                    'logs/supervisor.log'
                ]
                
                for logfile in log_files:
                    if os.path.exists(logfile):
                        self._check_log_errors(logfile)
                
                time.sleep(60)  # Every minute
                
            except Exception as e:
                logger.error(f"Log monitor error: {e}")
                time.sleep(60)
    
    def _check_log_errors(self, logfile: str):
        """Check log file for recent errors"""
        try:
            # Read last 100 lines
            with open(logfile, 'r') as f:
                lines = f.readlines()[-100:]
            
            error_count = sum(1 for line in lines if 'ERROR' in line or 'CRITICAL' in line)
            
            if error_count > 10:
                self._send_alert(f"Many errors in {logfile}", f"{error_count} errors in last 100 lines")
                
        except Exception as e:
            logger.error(f"Error checking log {logfile}: {e}")
    
    def _send_alert(self, title: str, message: str):
        """Send alert through configured channels"""
        alert = f"🚨 {title}: {message} [{datetime.now()}]"
        logger.critical(alert)
        
        # TODO: Implement actual alert sending (Telegram, email, etc)
        # For now, just log it
        
        # Write to alert file
        with open('logs/alerts.log', 'a') as f:
            f.write(f"{alert}\n")
    
    def full_system_check(self):
        """Perform full system check"""
        logger.info("Performing full system check...")
        
        all_healthy = True
        for component_id, config in self.components.items():
            is_healthy = self._check_component(component_id, config)
            status = "✅ OK" if is_healthy else "❌ FAILED"
            logger.info(f"{config['name']}: {status}")
            
            if not is_healthy:
                all_healthy = False
                if config.get('critical', False):
                    self._restart_component(component_id, config)
        
        if all_healthy:
            logger.info("✅ All systems operational")
        else:
            logger.warning("⚠️ Some systems need attention")
        
        return all_healthy
    
    def get_status(self) -> dict:
        """Get current system status"""
        status = {
            'supervisor': 'RUNNING',
            'components': {},
            'system': {
                'cpu': psutil.cpu_percent(),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent
            },
            'uptime': self._get_uptime()
        }
        
        for component_id, config in self.components.items():
            is_healthy = self._check_component(component_id, config)
            status['components'][component_id] = {
                'name': config['name'],
                'status': 'UP' if is_healthy else 'DOWN',
                'failures': self.failures.get(component_id, 0)
            }
        
        return status
    
    def _get_uptime(self) -> str:
        """Get system uptime"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        return str(uptime).split('.')[0]


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════╗
    ║      BITTEN SYSTEM SUPERVISOR v1.0       ║
    ║         24/7 Component Monitoring        ║
    ╚══════════════════════════════════════════╝
    """)
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    
    # Start supervisor
    supervisor = BITTENSupervisor()
    
    try:
        supervisor.start()
    except Exception as e:
        logger.error(f"Supervisor crashed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()