#!/usr/bin/env python3
"""
SHEPHERD Health Check System
Production-ready health monitoring with comprehensive checks and alerting
"""

import os
import sys
import json
import psutil
import logging
import argparse
import smtplib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import socket
import traceback

# Configuration
PROJECT_ROOT = Path("/root/HydraX-v2")
DATA_DIR = PROJECT_ROOT / "bitten/data/shepherd"
LOG_DIR = PROJECT_ROOT / "logs/shepherd"
INDEX_FILE = DATA_DIR / "shepherd_index.json"
PID_FILE = DATA_DIR / "shepherd_watch.pid"
HEALTH_STATE_FILE = DATA_DIR / "health_state.json"

# Thresholds
MAX_INDEX_AGE_HOURS = 24
MAX_MEMORY_PERCENT = 80
MAX_CPU_PERCENT = 90
MAX_DISK_PERCENT = 90
MIN_FREE_DISK_GB = 1
MAX_LOG_SIZE_MB = 100
MAX_RESPONSE_TIME_MS = 5000

# Alert configuration (customize as needed)
ALERT_EMAIL = os.environ.get("SHEPHERD_ALERT_EMAIL", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "health" / f"healthcheck_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Health check result"""
    check_name: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    details: Dict = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}

class ShepherdHealthCheck:
    """Comprehensive health monitoring for SHEPHERD system"""
    
    def __init__(self):
        self.results: List[HealthStatus] = []
        self.start_time = time.time()
        self.load_previous_state()
    
    def load_previous_state(self):
        """Load previous health state for comparison"""
        self.previous_state = {}
        if HEALTH_STATE_FILE.exists():
            try:
                with open(HEALTH_STATE_FILE, 'r') as f:
                    self.previous_state = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load previous state: {e}")
    
    def save_current_state(self):
        """Save current health state"""
        current_state = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results],
            "summary": self.get_summary()
        }
        
        try:
            with open(HEALTH_STATE_FILE, 'w') as f:
                json.dump(current_state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health state: {e}")
    
    def add_result(self, check_name: str, status: str, message: str, details: Dict = None):
        """Add a health check result"""
        result = HealthStatus(check_name, status, message, details)
        self.results.append(result)
        
        # Log based on severity
        if status == 'critical':
            logger.error(f"{check_name}: {message}")
        elif status == 'warning':
            logger.warning(f"{check_name}: {message}")
        else:
            logger.info(f"{check_name}: {message}")
        
        return result
    
    def check_process_running(self) -> HealthStatus:
        """Check if SHEPHERD watch process is running"""
        try:
            if not PID_FILE.exists():
                return self.add_result(
                    "process_check",
                    "critical",
                    "PID file not found - SHEPHERD watch mode not running",
                    {"pid_file": str(PID_FILE)}
                )
            
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    # Verify it's actually our process
                    cmdline = ' '.join(process.cmdline())
                    if 'shepherd_watch' in cmdline:
                        return self.add_result(
                            "process_check",
                            "healthy",
                            f"SHEPHERD watch process running (PID: {pid})",
                            {
                                "pid": pid,
                                "cpu_percent": process.cpu_percent(),
                                "memory_mb": process.memory_info().rss / 1024 / 1024,
                                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
                            }
                        )
            except psutil.NoSuchProcess:
                pass
            
            return self.add_result(
                "process_check",
                "critical",
                f"Process with PID {pid} not found",
                {"pid": pid}
            )
            
        except Exception as e:
            return self.add_result(
                "process_check",
                "critical",
                f"Failed to check process: {str(e)}",
                {"error": traceback.format_exc()}
            )
    
    def check_index_health(self) -> HealthStatus:
        """Check index file health and freshness"""
        try:
            if not INDEX_FILE.exists():
                return self.add_result(
                    "index_check",
                    "critical",
                    "Index file not found",
                    {"index_file": str(INDEX_FILE)}
                )
            
            # Check file age
            stat = INDEX_FILE.stat()
            age_hours = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
            
            # Load and validate index
            with open(INDEX_FILE, 'r') as f:
                index_data = json.load(f)
            
            metadata = index_data.get("metadata", {})
            total_components = metadata.get("total_components", 0)
            
            details = {
                "file_size_mb": stat.st_size / 1024 / 1024,
                "age_hours": round(age_hours, 2),
                "total_components": total_components,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            # Check for index corruption
            if not metadata or total_components == 0:
                return self.add_result(
                    "index_check",
                    "critical",
                    "Index appears to be corrupted or empty",
                    details
                )
            
            # Check age
            if age_hours > MAX_INDEX_AGE_HOURS:
                return self.add_result(
                    "index_check",
                    "warning",
                    f"Index is {age_hours:.1f} hours old (threshold: {MAX_INDEX_AGE_HOURS}h)",
                    details
                )
            
            return self.add_result(
                "index_check",
                "healthy",
                f"Index is healthy with {total_components} components",
                details
            )
            
        except Exception as e:
            return self.add_result(
                "index_check",
                "critical",
                f"Failed to check index: {str(e)}",
                {"error": traceback.format_exc()}
            )
    
    def check_system_resources(self) -> List[HealthStatus]:
        """Check system resource usage"""
        results = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > MAX_CPU_PERCENT:
                results.append(self.add_result(
                    "cpu_check",
                    "warning",
                    f"High CPU usage: {cpu_percent}%",
                    {"cpu_percent": cpu_percent, "threshold": MAX_CPU_PERCENT}
                ))
            else:
                results.append(self.add_result(
                    "cpu_check",
                    "healthy",
                    f"CPU usage: {cpu_percent}%",
                    {"cpu_percent": cpu_percent}
                ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > MAX_MEMORY_PERCENT:
                results.append(self.add_result(
                    "memory_check",
                    "warning",
                    f"High memory usage: {memory.percent}%",
                    {
                        "memory_percent": memory.percent,
                        "used_gb": memory.used / 1024 / 1024 / 1024,
                        "available_gb": memory.available / 1024 / 1024 / 1024,
                        "threshold": MAX_MEMORY_PERCENT
                    }
                ))
            else:
                results.append(self.add_result(
                    "memory_check",
                    "healthy",
                    f"Memory usage: {memory.percent}%",
                    {
                        "memory_percent": memory.percent,
                        "used_gb": memory.used / 1024 / 1024 / 1024,
                        "available_gb": memory.available / 1024 / 1024 / 1024
                    }
                ))
            
            # Disk usage
            disk = psutil.disk_usage(str(PROJECT_ROOT))
            free_gb = disk.free / 1024 / 1024 / 1024
            
            if disk.percent > MAX_DISK_PERCENT or free_gb < MIN_FREE_DISK_GB:
                results.append(self.add_result(
                    "disk_check",
                    "critical" if free_gb < MIN_FREE_DISK_GB else "warning",
                    f"Disk space low: {disk.percent}% used, {free_gb:.1f}GB free",
                    {
                        "disk_percent": disk.percent,
                        "free_gb": free_gb,
                        "used_gb": disk.used / 1024 / 1024 / 1024,
                        "total_gb": disk.total / 1024 / 1024 / 1024
                    }
                ))
            else:
                results.append(self.add_result(
                    "disk_check",
                    "healthy",
                    f"Disk usage: {disk.percent}%, {free_gb:.1f}GB free",
                    {
                        "disk_percent": disk.percent,
                        "free_gb": free_gb
                    }
                ))
            
        except Exception as e:
            results.append(self.add_result(
                "system_resources",
                "critical",
                f"Failed to check system resources: {str(e)}",
                {"error": traceback.format_exc()}
            ))
        
        return results
    
    def check_log_health(self) -> HealthStatus:
        """Check log file sizes and rotation"""
        try:
            total_size = 0
            large_files = []
            
            if LOG_DIR.exists():
                for log_file in LOG_DIR.rglob("*.log"):
                    size_mb = log_file.stat().st_size / 1024 / 1024
                    total_size += size_mb
                    
                    if size_mb > MAX_LOG_SIZE_MB:
                        large_files.append({
                            "file": str(log_file.relative_to(PROJECT_ROOT)),
                            "size_mb": round(size_mb, 2)
                        })
            
            details = {
                "total_size_mb": round(total_size, 2),
                "log_count": len(list(LOG_DIR.rglob("*.log"))) if LOG_DIR.exists() else 0,
                "large_files": large_files
            }
            
            if large_files:
                return self.add_result(
                    "log_check",
                    "warning",
                    f"Found {len(large_files)} log files exceeding {MAX_LOG_SIZE_MB}MB",
                    details
                )
            
            return self.add_result(
                "log_check",
                "healthy",
                f"Log files healthy, total size: {total_size:.1f}MB",
                details
            )
            
        except Exception as e:
            return self.add_result(
                "log_check",
                "warning",
                f"Failed to check logs: {str(e)}",
                {"error": str(e)}
            )
    
    def check_connectivity(self) -> HealthStatus:
        """Check network connectivity for external services"""
        try:
            # Test DNS resolution
            socket.gethostbyname("google.com")
            
            # Test local services if configured
            services_ok = True
            failed_services = []
            
            # Add any service checks here
            # Example: check if database is accessible
            
            if services_ok:
                return self.add_result(
                    "connectivity_check",
                    "healthy",
                    "Network connectivity is good",
                    {"dns": "ok"}
                )
            else:
                return self.add_result(
                    "connectivity_check",
                    "warning",
                    f"Some services unreachable: {', '.join(failed_services)}",
                    {"failed_services": failed_services}
                )
                
        except Exception as e:
            return self.add_result(
                "connectivity_check",
                "warning",
                "Network connectivity issues detected",
                {"error": str(e)}
            )
    
    def check_permissions(self) -> HealthStatus:
        """Check file and directory permissions"""
        try:
            issues = []
            
            # Check critical directories are writable
            for dir_path in [DATA_DIR, LOG_DIR]:
                if dir_path.exists():
                    if not os.access(dir_path, os.W_OK):
                        issues.append(f"{dir_path} not writable")
                else:
                    issues.append(f"{dir_path} does not exist")
            
            # Check critical files
            if INDEX_FILE.exists() and not os.access(INDEX_FILE, os.R_OK):
                issues.append(f"{INDEX_FILE} not readable")
            
            if issues:
                return self.add_result(
                    "permissions_check",
                    "critical",
                    f"Permission issues: {', '.join(issues)}",
                    {"issues": issues}
                )
            
            return self.add_result(
                "permissions_check",
                "healthy",
                "All permissions correct",
                {}
            )
            
        except Exception as e:
            return self.add_result(
                "permissions_check",
                "critical",
                f"Failed to check permissions: {str(e)}",
                {"error": traceback.format_exc()}
            )
    
    def get_summary(self) -> Dict:
        """Get health check summary"""
        summary = {
            "total_checks": len(self.results),
            "healthy": sum(1 for r in self.results if r.status == "healthy"),
            "warnings": sum(1 for r in self.results if r.status == "warning"),
            "critical": sum(1 for r in self.results if r.status == "critical"),
            "duration_ms": round((time.time() - self.start_time) * 1000, 2)
        }
        
        # Overall status
        if summary["critical"] > 0:
            summary["overall_status"] = "critical"
        elif summary["warnings"] > 0:
            summary["overall_status"] = "warning"
        else:
            summary["overall_status"] = "healthy"
        
        return summary
    
    def send_alert(self, subject: str, body: str):
        """Send email alert for critical issues"""
        if not ALERT_EMAIL:
            logger.warning("Alert email not configured")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"SHEPHERD Health Monitor <shepherd@{socket.gethostname()}>"
            msg['To'] = ALERT_EMAIL
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USER:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            
            logger.info(f"Alert sent to {ALERT_EMAIL}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def notify_systemd(self):
        """Notify systemd watchdog if running as service"""
        try:
            # Check if running under systemd
            if os.environ.get('NOTIFY_SOCKET'):
                subprocess.run(['systemd-notify', 'WATCHDOG=1'], check=False)
        except:
            pass
    
    def run_all_checks(self) -> Dict:
        """Run all health checks"""
        logger.info("Starting SHEPHERD health checks...")
        
        # Run all checks
        self.check_process_running()
        self.check_index_health()
        self.check_system_resources()
        self.check_log_health()
        self.check_connectivity()
        self.check_permissions()
        
        # Get summary
        summary = self.get_summary()
        
        # Save state
        self.save_current_state()
        
        # Send alerts if needed
        critical_count = summary["critical"]
        if critical_count > 0:
            critical_checks = [r for r in self.results if r.status == "critical"]
            alert_body = f"SHEPHERD Health Check Alert\n\n"
            alert_body += f"Critical issues detected: {critical_count}\n\n"
            
            for check in critical_checks:
                alert_body += f"- {check.check_name}: {check.message}\n"
                if check.details:
                    alert_body += f"  Details: {json.dumps(check.details, indent=2)}\n"
            
            alert_body += f"\nFull report: {HEALTH_STATE_FILE}\n"
            alert_body += f"Time: {datetime.now().isoformat()}\n"
            alert_body += f"Host: {socket.gethostname()}\n"
            
            self.send_alert(
                f"[CRITICAL] SHEPHERD Health Check - {critical_count} issues",
                alert_body
            )
        
        # Notify systemd
        self.notify_systemd()
        
        # Log summary
        logger.info(f"Health check completed: {summary}")
        
        return summary

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SHEPHERD Health Check System")
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--startup', action='store_true', help='Startup check mode')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    # Ensure directories exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "health").mkdir(exist_ok=True)
    
    if args.continuous:
        # Continuous monitoring mode
        logger.info("Starting continuous health monitoring...")
        while True:
            try:
                checker = ShepherdHealthCheck()
                summary = checker.run_all_checks()
                
                if args.json:
                    print(json.dumps(summary, indent=2))
                
                time.sleep(args.interval)
                
            except KeyboardInterrupt:
                logger.info("Health monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(args.interval)
    else:
        # Single run
        checker = ShepherdHealthCheck()
        summary = checker.run_all_checks()
        
        if args.json:
            print(json.dumps({
                "summary": summary,
                "results": [asdict(r) for r in checker.results]
            }, indent=2))
        else:
            # Pretty print results
            print(f"\nSHEPHERD Health Check Report")
            print(f"{'=' * 50}")
            print(f"Timestamp: {datetime.now().isoformat()}")
            print(f"Duration: {summary['duration_ms']}ms")
            print(f"\nSummary:")
            print(f"  Total checks: {summary['total_checks']}")
            print(f"  Healthy: {summary['healthy']}")
            print(f"  Warnings: {summary['warnings']}")
            print(f"  Critical: {summary['critical']}")
            print(f"  Overall status: {summary['overall_status'].upper()}")
            
            if summary['warnings'] > 0 or summary['critical'] > 0:
                print(f"\nIssues:")
                for result in checker.results:
                    if result.status != 'healthy':
                        print(f"\n  [{result.status.upper()}] {result.check_name}:")
                        print(f"    {result.message}")
                        if result.details:
                            for key, value in result.details.items():
                                print(f"    - {key}: {value}")
        
        # Exit code based on status
        if summary['overall_status'] == 'critical':
            sys.exit(2)
        elif summary['overall_status'] == 'warning':
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    main()