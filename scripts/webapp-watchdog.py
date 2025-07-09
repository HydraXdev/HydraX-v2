#!/usr/bin/env python3
"""
BITTEN WebApp Watchdog Service
Advanced monitoring and auto-recovery for the webapp service
"""

import time
import logging
import requests
import subprocess
import json
import os
import sys
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import psutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
CONFIG = {
    'service_name': 'bitten-webapp',
    'pm2_app_name': 'bitten-webapp',
    'health_check_url': 'http://localhost:8888/health',
    'check_interval': 60,
    'max_failures': 3,
    'recovery_timeout': 300,
    'log_file': '/var/log/bitten/webapp/watchdog.log',
    'alert_email': os.getenv('ALERT_EMAIL', ''),
    'smtp_server': os.getenv('SMTP_SERVER', ''),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'smtp_username': os.getenv('SMTP_USERNAME', ''),
    'smtp_password': os.getenv('SMTP_PASSWORD', ''),
    'webhook_url': os.getenv('WEBHOOK_URL', ''),
    'thresholds': {
        'cpu_warning': 80,
        'cpu_critical': 95,
        'memory_warning': 80,
        'memory_critical': 95,
        'disk_warning': 80,
        'disk_critical': 95,
        'response_time_warning': 5000,  # milliseconds
        'response_time_critical': 10000  # milliseconds
    }
}

class WebAppWatchdog:
    def __init__(self):
        self.running = False
        self.failure_count = 0
        self.last_alert_time = None
        self.alert_cooldown = timedelta(minutes=15)
        self.setup_logging()
        
        # Integration with existing monitoring system
        self.monitoring_integrator = None
        try:
            sys.path.append('/root/HydraX-v2/src')
            from monitoring.system_integrator import get_monitoring_integrator
            self.monitoring_integrator = get_monitoring_integrator()
        except Exception as e:
            self.logger.warning(f"Could not integrate with monitoring system: {e}")
    
    def setup_logging(self):
        """Setup logging configuration"""
        os.makedirs(os.path.dirname(CONFIG['log_file']), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(CONFIG['log_file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def send_alert(self, subject: str, message: str, level: str = 'warning'):
        """Send alert via email and webhook"""
        # Check cooldown
        if self.last_alert_time and datetime.now() - self.last_alert_time < self.alert_cooldown:
            return
        
        self.last_alert_time = datetime.now()
        
        # Send email alert
        if CONFIG['alert_email'] and CONFIG['smtp_server']:
            try:
                self._send_email_alert(subject, message)
            except Exception as e:
                self.logger.error(f"Failed to send email alert: {e}")
        
        # Send webhook alert
        if CONFIG['webhook_url']:
            try:
                self._send_webhook_alert(subject, message, level)
            except Exception as e:
                self.logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_email_alert(self, subject: str, message: str):
        """Send email alert"""
        msg = MIMEMultipart()
        msg['From'] = CONFIG['smtp_username']
        msg['To'] = CONFIG['alert_email']
        msg['Subject'] = f"BITTEN WebApp Alert: {subject}"
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(CONFIG['smtp_server'], CONFIG['smtp_port'])
        server.starttls()
        server.login(CONFIG['smtp_username'], CONFIG['smtp_password'])
        text = msg.as_string()
        server.sendmail(CONFIG['smtp_username'], CONFIG['alert_email'], text)
        server.quit()
    
    def _send_webhook_alert(self, subject: str, message: str, level: str):
        """Send webhook alert"""
        payload = {
            'text': f"{subject}: {message}",
            'level': level,
            'service': 'bitten-webapp',
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(CONFIG['webhook_url'], json=payload, timeout=10)
        response.raise_for_status()
    
    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        start_time = time.time()
        
        try:
            response = requests.get(CONFIG['health_check_url'], timeout=30)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                health_data = response.json()
                health_data['response_time_ms'] = response_time
                
                # Check response time thresholds
                if response_time > CONFIG['thresholds']['response_time_critical']:
                    health_data['status'] = 'critical'
                elif response_time > CONFIG['thresholds']['response_time_warning']:
                    health_data['status'] = 'warning'
                
                return health_data
            else:
                return {
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}",
                    'response_time_ms': response_time
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': (time.time() - start_time) * 1000
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Process information
            webapp_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                if 'webapp_server' in proc.info['name'] or 'python' in proc.info['name']:
                    try:
                        cmdline = proc.cmdline()
                        if any('webapp_server.py' in cmd for cmd in cmdline):
                            webapp_processes.append({
                                'pid': proc.info['pid'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent'],
                                'status': proc.info['status']
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'webapp_processes': webapp_processes,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return {'error': str(e)}
    
    def check_service_status(self) -> Dict[str, Any]:
        """Check service status for both SystemD and PM2"""
        status = {
            'systemd': {'active': False, 'enabled': False},
            'pm2': {'active': False, 'processes': []}
        }
        
        # Check SystemD
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', CONFIG['service_name']],
                capture_output=True, text=True
            )
            status['systemd']['active'] = result.returncode == 0
            
            result = subprocess.run(
                ['systemctl', 'is-enabled', CONFIG['service_name']],
                capture_output=True, text=True
            )
            status['systemd']['enabled'] = result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Error checking SystemD status: {e}")
        
        # Check PM2
        try:
            result = subprocess.run(
                ['pm2', 'jlist'], capture_output=True, text=True
            )
            if result.returncode == 0:
                pm2_processes = json.loads(result.stdout)
                webapp_processes = [p for p in pm2_processes if p['name'] == CONFIG['pm2_app_name']]
                status['pm2']['processes'] = webapp_processes
                status['pm2']['active'] = any(p['pm2_env']['status'] == 'online' for p in webapp_processes)
            
        except Exception as e:
            self.logger.error(f"Error checking PM2 status: {e}")
        
        return status
    
    def attempt_recovery(self, method: str = 'auto') -> bool:
        """Attempt to recover the service"""
        self.logger.info(f"Attempting recovery using method: {method}")
        
        if method == 'auto':
            # Try SystemD first, then PM2
            if self._recover_systemd():
                return True
            elif self._recover_pm2():
                return True
            else:
                return False
        elif method == 'systemd':
            return self._recover_systemd()
        elif method == 'pm2':
            return self._recover_pm2()
        else:
            self.logger.error(f"Unknown recovery method: {method}")
            return False
    
    def _recover_systemd(self) -> bool:
        """Recover using SystemD"""
        try:
            result = subprocess.run(
                ['systemctl', 'restart', CONFIG['service_name']],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.logger.info("SystemD restart successful")
                # Wait for service to start
                time.sleep(10)
                
                # Verify recovery
                if self._verify_recovery():
                    self.logger.info("Service recovery verified")
                    return True
            
            self.logger.error(f"SystemD restart failed: {result.stderr}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error recovering with SystemD: {e}")
            return False
    
    def _recover_pm2(self) -> bool:
        """Recover using PM2"""
        try:
            result = subprocess.run(
                ['pm2', 'restart', CONFIG['pm2_app_name']],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.logger.info("PM2 restart successful")
                # Wait for service to start
                time.sleep(10)
                
                # Verify recovery
                if self._verify_recovery():
                    self.logger.info("Service recovery verified")
                    return True
            
            self.logger.error(f"PM2 restart failed: {result.stderr}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error recovering with PM2: {e}")
            return False
    
    def _verify_recovery(self) -> bool:
        """Verify that recovery was successful"""
        max_attempts = 6
        for attempt in range(max_attempts):
            health = self.check_health()
            if health.get('status') == 'healthy':
                return True
            
            if attempt < max_attempts - 1:
                time.sleep(10)
        
        return False
    
    def collect_diagnostics(self) -> Dict[str, Any]:
        """Collect diagnostic information"""
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'health_check': self.check_health(),
            'system_resources': self.check_system_resources(),
            'service_status': self.check_service_status(),
            'network_status': self._check_network_status(),
            'recent_logs': self._get_recent_logs()
        }
        
        # Save diagnostics to file
        diag_file = f"/tmp/webapp_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(diag_file, 'w') as f:
            json.dump(diagnostics, f, indent=2)
        
        diagnostics['diagnostic_file'] = diag_file
        return diagnostics
    
    def _check_network_status(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            # Check if port 8888 is open
            result = subprocess.run(
                ['netstat', '-tulpn'], capture_output=True, text=True
            )
            
            port_8888_open = ':8888' in result.stdout
            
            return {
                'port_8888_open': port_8888_open,
                'netstat_output': result.stdout
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_recent_logs(self) -> Dict[str, Any]:
        """Get recent logs from various sources"""
        logs = {}
        
        # SystemD logs
        try:
            result = subprocess.run(
                ['journalctl', '-u', CONFIG['service_name'], '-n', '50', '--no-pager'],
                capture_output=True, text=True
            )
            logs['systemd'] = result.stdout
        except Exception as e:
            logs['systemd'] = f"Error: {e}"
        
        # PM2 logs
        try:
            result = subprocess.run(
                ['pm2', 'logs', CONFIG['pm2_app_name'], '--lines', '50'],
                capture_output=True, text=True
            )
            logs['pm2'] = result.stdout
        except Exception as e:
            logs['pm2'] = f"Error: {e}"
        
        # Application logs
        try:
            log_files = [
                '/var/log/bitten/webapp/error.log',
                '/var/log/bitten/webapp/out.log',
                '/root/HydraX-v2/logs/webapp.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        logs[os.path.basename(log_file)] = f.read()[-5000:]  # Last 5KB
        except Exception as e:
            logs['application'] = f"Error: {e}"
        
        return logs
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        # Check health
        health = self.check_health()
        system_resources = self.check_system_resources()
        
        # Log current status
        self.logger.info(f"Health status: {health.get('status', 'unknown')}")
        
        # Check for critical resource usage
        if system_resources.get('cpu_percent', 0) > CONFIG['thresholds']['cpu_critical']:
            self.send_alert(
                "Critical CPU Usage",
                f"CPU usage is {system_resources['cpu_percent']}%",
                'critical'
            )
        
        if system_resources.get('memory_percent', 0) > CONFIG['thresholds']['memory_critical']:
            self.send_alert(
                "Critical Memory Usage",
                f"Memory usage is {system_resources['memory_percent']}%",
                'critical'
            )
        
        # Check service health
        if health.get('status') != 'healthy':
            self.failure_count += 1
            self.logger.warning(f"Service unhealthy (failure {self.failure_count}/{CONFIG['max_failures']})")
            
            if self.failure_count >= CONFIG['max_failures']:
                self.logger.error("Maximum failures reached, attempting recovery")
                
                # Collect diagnostics before recovery
                diagnostics = self.collect_diagnostics()
                
                # Attempt recovery
                if self.attempt_recovery():
                    self.failure_count = 0
                    self.send_alert(
                        "Service Recovery Successful",
                        "The webapp service has been successfully recovered",
                        'info'
                    )
                else:
                    self.send_alert(
                        "CRITICAL: Service Recovery Failed",
                        "All recovery attempts failed. Manual intervention required.",
                        'critical'
                    )
                    
                    # If integrated with monitoring system, trigger emergency protocols
                    if self.monitoring_integrator:
                        try:
                            self.monitoring_integrator.alert_manager.trigger_emergency_alert(
                                service="bitten-webapp",
                                message="Service recovery failed",
                                diagnostics=diagnostics
                            )
                        except Exception as e:
                            self.logger.error(f"Failed to trigger emergency alert: {e}")
        else:
            if self.failure_count > 0:
                self.logger.info(f"Service recovered after {self.failure_count} failures")
                self.failure_count = 0
    
    def start(self):
        """Start the watchdog monitoring"""
        self.running = True
        self.logger.info("Starting webapp watchdog monitoring")
        
        while self.running:
            try:
                self.run_monitoring_cycle()
                time.sleep(CONFIG['check_interval'])
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                time.sleep(60)  # Wait longer on error
    
    def stop(self):
        """Stop the watchdog monitoring"""
        self.running = False
        self.logger.info("Stopping webapp watchdog monitoring")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal, stopping watchdog...")
    watchdog.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start watchdog
    watchdog = WebAppWatchdog()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'check':
            health = watchdog.check_health()
            print(json.dumps(health, indent=2))
            sys.exit(0 if health.get('status') == 'healthy' else 1)
        
        elif command == 'diagnostics':
            diagnostics = watchdog.collect_diagnostics()
            print(json.dumps(diagnostics, indent=2))
            sys.exit(0)
        
        elif command == 'recover':
            method = sys.argv[2] if len(sys.argv) > 2 else 'auto'
            success = watchdog.attempt_recovery(method)
            sys.exit(0 if success else 1)
        
        else:
            print("Usage: webapp-watchdog.py [check|diagnostics|recover]")
            sys.exit(1)
    
    else:
        # Start monitoring
        watchdog.start()