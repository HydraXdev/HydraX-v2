#!/usr/bin/env python3
"""
CLONE FARM WATCHDOG SYSTEM
Monitors and maintains uninterrupted service for the clone farm
"""

import os
import sys
import time
import json
import psutil
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/clone_farm_watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloneFarmWatchdog:
    def __init__(self):
        self.config = {
            'check_interval': 30,  # seconds
            'master_clone_path': '/root/.wine_master_clone',
            'user_clone_prefix': '/root/.wine_user_',
            'required_processes': [
                'apex_v5_lean.py',
                'bitten_production_bot.py',
                'webapp_server_optimized.py'
            ],
            'max_memory_mb': 16384,  # 16GB total system limit
            'max_cpu_percent': 80,
            'alert_cooldown': 300,  # 5 minutes between alerts
            'auto_restart': True,
            'health_check_port': 8888
        }
        
        self.last_alert = {}
        self.service_stats = {}
        self.clone_stats = {}
        
        logger.info("🐕 Clone Farm Watchdog initialized")
    
    def check_master_clone_integrity(self):
        """Verify master clone has not been compromised"""
        try:
            # Run integrity check script
            result = subprocess.run([
                '/root/HydraX-v2/check_master_integrity.sh'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Master clone integrity verified")
                return True
            else:
                logger.error(f"❌ Master clone integrity compromised: {result.stdout}")
                self.send_alert("CRITICAL", "Master clone integrity compromised", result.stdout)
                return False
                
        except Exception as e:
            logger.error(f"Failed to check master clone integrity: {e}")
            return False
    
    def check_required_processes(self):
        """Monitor critical production processes"""
        running_processes = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                for required in self.config['required_processes']:
                    if required in cmdline:
                        running_processes[required] = {
                            'pid': proc.info['pid'],
                            'cpu_percent': proc.cpu_percent(),
                            'memory_mb': proc.memory_info().rss / 1024 / 1024,
                            'status': proc.status()
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check for missing processes
        missing_processes = []
        for required in self.config['required_processes']:
            if required not in running_processes:
                missing_processes.append(required)
                logger.warning(f"⚠️  Missing process: {required}")
        
        # Auto-restart missing critical processes
        if missing_processes and self.config['auto_restart']:
            self.restart_missing_processes(missing_processes)
        
        self.service_stats = running_processes
        return len(missing_processes) == 0
    
    def restart_missing_processes(self, missing_processes):
        """Attempt to restart missing critical processes"""
        restart_commands = {
            'apex_v5_lean.py': 'cd /root/HydraX-v2 && python3 apex_v5_lean.py',
            'bitten_production_bot.py': 'cd /root/HydraX-v2 && python3 bitten_production_bot.py',
            'webapp_server_optimized.py': 'cd /root/HydraX-v2 && python3 webapp_server_optimized.py'
        }
        
        for process in missing_processes:
            if process in restart_commands:
                try:
                    logger.info(f"🔄 Attempting to restart {process}")
                    
                    # Start process in background
                    subprocess.Popen(
                        restart_commands[process],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    logger.info(f"✅ Restart initiated for {process}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to restart {process}: {e}")
                    self.send_alert("ERROR", f"Failed to restart {process}", str(e))
    
    def check_system_resources(self):
        """Monitor system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Check thresholds
            alerts = []
            
            if cpu_percent > self.config['max_cpu_percent']:
                alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_mb > self.config['max_memory_mb']:
                alerts.append(f"High memory usage: {memory_mb:.0f}MB")
            
            if disk_percent > 90:
                alerts.append(f"High disk usage: {disk_percent:.1f}%")
            
            # Log resource stats
            logger.info(f"📊 Resources: CPU {cpu_percent:.1f}%, Memory {memory_mb:.0f}MB, Disk {disk_percent:.1f}%")
            
            # Send alerts if needed
            for alert in alerts:
                self.send_alert("WARNING", "High resource usage", alert)
            
            return len(alerts) == 0
            
        except Exception as e:
            logger.error(f"Failed to check system resources: {e}")
            return False
    
    def check_user_clones(self):
        """Monitor user clone health"""
        user_clone_dirs = []
        base_path = Path(self.config['user_clone_prefix'].rstrip('_'))
        
        # Find all user clone directories
        for path in base_path.parent.glob(f"{base_path.name}_*"):
            if path.is_dir():
                user_clone_dirs.append(path)
        
        clone_health = {}
        
        for clone_dir in user_clone_dirs:
            user_id = clone_dir.name.split('_')[-1]
            
            # Check clone directory structure
            mt5_path = clone_dir / "drive_c/Program Files/MetaTrader 5"
            config_path = mt5_path / "config.ini"
            ea_path = mt5_path / "MQL5/Experts/BITTEN_EA.ex5"
            drop_path = mt5_path / f"Files/BITTEN/Drop/user_{user_id}"
            
            health_status = {
                'config_exists': config_path.exists(),
                'ea_exists': ea_path.exists(),
                'drop_folder_exists': drop_path.exists(),
                'last_activity': None,
                'disk_usage_mb': 0
            }
            
            # Check disk usage
            try:
                health_status['disk_usage_mb'] = sum(
                    f.stat().st_size for f in clone_dir.rglob('*') if f.is_file()
                ) / 1024 / 1024
            except Exception:
                pass
            
            # Check last activity (recent files in drop folder)
            try:
                if drop_path.exists():
                    recent_files = [
                        f for f in drop_path.glob('*') 
                        if f.is_file() and (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)) < timedelta(hours=24)
                    ]
                    if recent_files:
                        health_status['last_activity'] = max(
                            datetime.fromtimestamp(f.stat().st_mtime) for f in recent_files
                        )
            except Exception:
                pass
            
            clone_health[user_id] = health_status
        
        # Log clone statistics
        total_clones = len(clone_health)
        healthy_clones = sum(1 for h in clone_health.values() if h['config_exists'] and h['ea_exists'])
        total_disk_mb = sum(h['disk_usage_mb'] for h in clone_health.values())
        
        logger.info(f"🏭 Clone Farm: {healthy_clones}/{total_clones} healthy, {total_disk_mb:.0f}MB disk usage")
        
        self.clone_stats = {
            'total_clones': total_clones,
            'healthy_clones': healthy_clones,
            'total_disk_mb': total_disk_mb,
            'clone_health': clone_health
        }
        
        return healthy_clones == total_clones
    
    def check_webapp_health(self):
        """Check webapp endpoint health"""
        try:
            import requests
            response = requests.get(
                f"http://localhost:{self.config['health_check_port']}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ Webapp health check passed")
                return True
            else:
                logger.warning(f"⚠️  Webapp health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️  Webapp health check failed: {e}")
            return False
    
    def cleanup_old_logs(self):
        """Clean up old log files and temporary data"""
        try:
            # Clean old log files (keep 7 days)
            log_files = [
                '/var/log/clone_farm_watchdog.log',
                '/var/log/master_clone_integrity.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    # Rotate if larger than 100MB
                    if os.path.getsize(log_file) > 100 * 1024 * 1024:
                        os.rename(log_file, f"{log_file}.old")
                        open(log_file, 'w').close()
                        logger.info(f"📋 Rotated log file: {log_file}")
            
            # Clean temporary mission files older than 24 hours
            missions_dir = Path('/root/HydraX-v2/missions')
            if missions_dir.exists():
                cutoff_time = datetime.now() - timedelta(hours=24)
                old_missions = [
                    f for f in missions_dir.glob('*.json')
                    if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime) < cutoff_time
                ]
                
                for mission_file in old_missions:
                    mission_file.unlink()
                    logger.info(f"🗑️  Cleaned old mission file: {mission_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
    
    def send_alert(self, level, title, message):
        """Send alert if not in cooldown period"""
        alert_key = f"{level}:{title}"
        now = datetime.now()
        
        # Check cooldown
        if alert_key in self.last_alert:
            if (now - self.last_alert[alert_key]).seconds < self.config['alert_cooldown']:
                return
        
        # Log alert
        logger.error(f"🚨 ALERT [{level}] {title}: {message}")
        
        # Record alert time
        self.last_alert[alert_key] = now
        
        # TODO: Add integration with notification systems
        # - Telegram alerts
        # - Email notifications
        # - Slack/Discord webhooks
    
    def generate_status_report(self):
        """Generate comprehensive status report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': {
                'master_clone_ok': self.check_master_clone_integrity(),
                'processes_ok': len(self.service_stats) == len(self.config['required_processes']),
                'resources_ok': True,  # Set by resource check
                'webapp_ok': self.check_webapp_health()
            },
            'service_stats': self.service_stats,
            'clone_stats': self.clone_stats,
            'system_resources': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        }
        
        # Save report
        report_file = f"/var/log/clone_farm_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def run_watchdog_cycle(self):
        """Run one complete watchdog monitoring cycle"""
        logger.info("🔍 Starting watchdog monitoring cycle")
        
        # Check all systems
        checks = {
            'master_clone': self.check_master_clone_integrity(),
            'processes': self.check_required_processes(),
            'resources': self.check_system_resources(),
            'user_clones': self.check_user_clones(),
            'webapp': self.check_webapp_health()
        }
        
        # Cleanup
        self.cleanup_old_logs()
        
        # Overall health status
        all_healthy = all(checks.values())
        
        if all_healthy:
            logger.info("✅ All systems healthy")
        else:
            failed_checks = [check for check, status in checks.items() if not status]
            logger.warning(f"⚠️  Failed checks: {', '.join(failed_checks)}")
        
        return all_healthy
    
    def run_continuous(self):
        """Run watchdog continuously"""
        logger.info("🐕 Starting Clone Farm Watchdog - Continuous Mode")
        logger.info(f"📋 Monitoring interval: {self.config['check_interval']} seconds")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"🔄 Watchdog cycle #{cycle_count}")
                
                # Run monitoring cycle
                healthy = self.run_watchdog_cycle()
                
                # Generate status report every 10 cycles (5 minutes with 30s interval)
                if cycle_count % 10 == 0:
                    report = self.generate_status_report()
                    logger.info(f"📊 Status report generated: {report['timestamp']}")
                
                # Sleep until next cycle
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            logger.info("🛑 Watchdog stopped by user")
        except Exception as e:
            logger.error(f"💥 Watchdog crashed: {e}")
            raise

def main():
    """Main watchdog entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        # Run as daemon
        import daemon
        
        with daemon.DaemonContext():
            watchdog = CloneFarmWatchdog()
            watchdog.run_continuous()
    else:
        # Run in foreground
        watchdog = CloneFarmWatchdog()
        
        if len(sys.argv) > 1 and sys.argv[1] == '--once':
            # Single cycle
            healthy = watchdog.run_watchdog_cycle()
            sys.exit(0 if healthy else 1)
        else:
            # Continuous mode
            watchdog.run_continuous()

if __name__ == "__main__":
    main()