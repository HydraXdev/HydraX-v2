#!/usr/bin/env python3
"""
HydraX System Monitor - Prevents Silent Failures
Monitors critical services and sends Telegram alerts when something breaks
"""

import os
import sys
import time
import json
import subprocess
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/system_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SystemMonitor')

# Telegram bot for monitoring alerts
MONITOR_BOT_TOKEN = "7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w"  # Production bot
ADMIN_CHAT_IDS = ["6150318148"]  # Admin/developer chat IDs for alerts

class SystemMonitor:
    """Monitors critical HydraX services and sends alerts"""
    
    def __init__(self):
        self.critical_services = {
            'signal_generator': {
                'process_names': ['working_signal_generator.py', 'apex_venom_v7', 'apex_production'],
                'description': 'VENOM Signal Generator',
                'check_interval': 60,  # Check every minute
                'last_check': None,
                'status': 'unknown',
                'restart_command': 'cd /root/HydraX-v2 && python3 working_signal_generator.py &'
            },
            'bitten_bot': {
                'process_names': ['bitten_production_bot.py'],
                'description': 'BITTEN Production Bot',
                'check_interval': 60,
                'last_check': None,
                'status': 'unknown',
                'restart_command': 'cd /root/HydraX-v2 && python3 bitten_production_bot.py &'
            },
            'webapp_server': {
                'process_names': ['webapp_server_optimized.py'],
                'description': 'WebApp Server',
                'check_interval': 60,
                'last_check': None,
                'status': 'unknown',
                'port_check': 8888,
                'restart_command': 'cd /root/HydraX-v2 && python3 webapp_server_optimized.py &'
            },
            'ea_data_stream': {
                'file_path': '/tmp/ea_raw_data.json',
                'description': 'EA Data Stream',
                'check_interval': 30,  # Check every 30 seconds
                'last_check': None,
                'status': 'unknown',
                'max_age_seconds': 60  # Alert if data older than 60 seconds
            }
        }
        
        self.alert_cooldown = {}  # Prevent spam - one alert per service per hour
        self.start_time = datetime.now()
        
    def send_telegram_alert(self, message: str, critical: bool = True):
        """Send alert to admins via Telegram"""
        try:
            emoji = "🚨" if critical else "⚠️"
            full_message = f"{emoji} **HydraX System Alert**\n\n{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            for chat_id in ADMIN_CHAT_IDS:
                url = f"https://api.telegram.org/bot{MONITOR_BOT_TOKEN}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": full_message,
                    "parse_mode": "Markdown"
                }
                response = requests.post(url, json=data, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Alert sent to {chat_id}: {message[:50]}...")
                else:
                    logger.error(f"Failed to send alert to {chat_id}: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
    
    def check_process_running(self, process_names: List[str]) -> bool:
        """Check if any of the process names are running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    for process_name in process_names:
                        if process_name in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"Error checking processes: {e}")
            return False
    
    def check_port_open(self, port: int) -> bool:
        """Check if a port is open"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_file_freshness(self, file_path: str, max_age_seconds: int) -> bool:
        """Check if a file exists and is recent"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # Check file modification time
            file_time = os.path.getmtime(file_path)
            current_time = time.time()
            age_seconds = current_time - file_time
            
            return age_seconds <= max_age_seconds
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")
            return False
    
    def should_send_alert(self, service_name: str) -> bool:
        """Check if we should send an alert (with cooldown)"""
        if service_name not in self.alert_cooldown:
            return True
        
        last_alert = self.alert_cooldown[service_name]
        time_since_alert = datetime.now() - last_alert
        
        # Alert cooldown: 1 hour
        return time_since_alert > timedelta(hours=1)
    
    def check_service(self, service_name: str, service_info: Dict):
        """Check a single service status"""
        try:
            # Skip if not time to check yet
            if service_info['last_check']:
                time_since_check = (datetime.now() - service_info['last_check']).seconds
                if time_since_check < service_info['check_interval']:
                    return
            
            service_info['last_check'] = datetime.now()
            was_running = service_info['status'] == 'running'
            is_running = False
            
            # Check based on service type
            if 'process_names' in service_info:
                is_running = self.check_process_running(service_info['process_names'])
                
                # Additional port check if specified
                if is_running and 'port_check' in service_info:
                    is_running = self.check_port_open(service_info['port_check'])
            
            elif 'file_path' in service_info:
                is_running = self.check_file_freshness(
                    service_info['file_path'],
                    service_info['max_age_seconds']
                )
            
            # Update status
            service_info['status'] = 'running' if is_running else 'stopped'
            
            # Send alert if service stopped
            if was_running and not is_running and self.should_send_alert(service_name):
                message = f"**{service_info['description']}** has STOPPED!\n\n"
                message += f"Service: {service_name}\n"
                message += f"Status: {service_info['status']}\n"
                
                if 'restart_command' in service_info:
                    message += f"\nRestart command:\n`{service_info['restart_command']}`"
                
                self.send_telegram_alert(message, critical=True)
                self.alert_cooldown[service_name] = datetime.now()
                
                # Log the failure
                logger.error(f"Service {service_name} ({service_info['description']}) has stopped!")
            
            # Log status changes
            if was_running != is_running:
                logger.info(f"Service {service_name} status changed: {was_running} -> {is_running}")
                
        except Exception as e:
            logger.error(f"Error checking service {service_name}: {e}")
    
    def check_all_services(self):
        """Check all critical services"""
        for service_name, service_info in self.critical_services.items():
            self.check_service(service_name, service_info)
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        status = {
            'monitor_uptime': str(datetime.now() - self.start_time),
            'services': {}
        }
        
        for service_name, service_info in self.critical_services.items():
            status['services'][service_name] = {
                'description': service_info['description'],
                'status': service_info['status'],
                'last_check': service_info['last_check'].isoformat() if service_info['last_check'] else None
            }
        
        return status
    
    def send_daily_report(self):
        """Send daily system health report"""
        try:
            status = self.get_system_status()
            
            message = "**Daily System Health Report**\n\n"
            message += f"Monitor Uptime: {status['monitor_uptime']}\n\n"
            
            all_running = True
            for service_name, service_status in status['services'].items():
                emoji = "✅" if service_status['status'] == 'running' else "❌"
                message += f"{emoji} {service_status['description']}: {service_status['status']}\n"
                if service_status['status'] != 'running':
                    all_running = False
            
            if all_running:
                message += "\n✅ All systems operational!"
            else:
                message += "\n⚠️ Some services need attention!"
            
            self.send_telegram_alert(message, critical=False)
            logger.info("Daily report sent")
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
    
    def run(self):
        """Main monitoring loop"""
        logger.info("HydraX System Monitor started")
        self.send_telegram_alert("System Monitor started - monitoring critical services", critical=False)
        
        last_daily_report = datetime.now()
        
        try:
            while True:
                # Check all services
                self.check_all_services()
                
                # Send daily report at midnight
                current_time = datetime.now()
                if current_time.hour == 0 and (current_time - last_daily_report).seconds > 3600:
                    self.send_daily_report()
                    last_daily_report = current_time
                
                # Sleep for 10 seconds before next check
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            self.send_telegram_alert("System Monitor stopped", critical=False)
        except Exception as e:
            logger.error(f"Monitor crashed: {e}")
            self.send_telegram_alert(f"System Monitor CRASHED: {str(e)}", critical=True)

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run()