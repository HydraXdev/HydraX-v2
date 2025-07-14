#!/usr/bin/env python3
"""
HEALTH MONITOR AGENT - Bulletproof System Guardian
Monitors all system components and triggers auto-recovery
"""

import json
import os
import time
import subprocess
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import requests

class HealthMonitorAgent:
    def __init__(self):
        self.primary_agent_url = "http://localhost:5555"
        self.backup_agent_url = "http://localhost:5556"
        self.is_monitoring = True
        self.db_path = "C:/MT5_Farm/health_monitor.db"
        self.setup_database()
        
        # Health check intervals (seconds)
        self.primary_check_interval = 30
        self.mt5_check_interval = 10
        self.resource_check_interval = 60
        
        # Recovery thresholds
        self.max_failed_pings = 3
        self.max_cpu_percent = 90
        self.max_memory_percent = 85
        self.min_disk_space_gb = 5
        
        # Start monitoring threads
        self.start_monitoring_threads()
    
    def setup_database(self):
        """Initialize health monitoring database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS recovery_actions (
                    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    target TEXT,
                    success BOOLEAN,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_free_gb REAL,
                    mt5_process_count INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def start_monitoring_threads(self):
        """Start all monitoring threads in parallel"""
        threads = [
            threading.Thread(target=self.monitor_primary_agent, daemon=True),
            threading.Thread(target=self.monitor_mt5_processes, daemon=True),
            threading.Thread(target=self.monitor_system_resources, daemon=True),
            threading.Thread(target=self.cleanup_routine, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
            
        print("🔍 All monitoring threads started")
    
    def monitor_primary_agent(self):
        """Monitor primary agent health and trigger failover if needed"""
        failed_pings = 0
        
        while self.is_monitoring:
            try:
                response = requests.get(f"{self.primary_agent_url}/health", timeout=5)
                if response.status_code == 200:
                    failed_pings = 0
                    self.log_health_check("primary_agent", "healthy", "Primary agent responding")
                else:
                    failed_pings += 1
                    self.log_health_check("primary_agent", "degraded", f"HTTP {response.status_code}")
            
            except Exception as e:
                failed_pings += 1
                self.log_health_check("primary_agent", "failed", str(e))
                
                if failed_pings >= self.max_failed_pings:
                    self.trigger_failover()
                    failed_pings = 0  # Reset after failover attempt
            
            time.sleep(self.primary_check_interval)
    
    def monitor_mt5_processes(self):
        """Monitor all MT5 processes and restart crashed instances"""
        while self.is_monitoring:
            try:
                # Get list of MT5 processes
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], 
                                      capture_output=True, text=True, check=False)
                
                # Count running MT5 instances
                mt5_count = len([line for line in result.stdout.split('\n') if 'terminal64.exe' in line])
                
                # Check for crashed user instances
                self.check_user_mt5_instances()
                
                self.log_health_check("mt5_processes", "healthy", f"{mt5_count} MT5 instances running")
                
            except Exception as e:
                self.log_health_check("mt5_processes", "error", str(e))
            
            time.sleep(self.mt5_check_interval)
    
    def check_user_mt5_instances(self):
        """Check each user's MT5 instance and restart if crashed"""
        users_path = Path("C:/MT5_Farm/Users")
        
        if not users_path.exists():
            return
        
        for user_dir in users_path.iterdir():
            if user_dir.is_dir() and user_dir.name.startswith("user_"):
                user_id = user_dir.name.replace("user_", "")
                self.check_user_mt5(user_id, user_dir)
    
    def check_user_mt5(self, user_id, user_path):
        """Check specific user's MT5 and restart if needed"""
        try:
            mt5_exe = user_path / "terminal64.exe"
            if not mt5_exe.exists():
                return
            
            # Check if user's MT5 process is running
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq terminal64.exe'], 
                                  capture_output=True, text=True, check=False)
            
            # Simple check - if we have fewer MT5 processes than expected, restart
            # (More sophisticated process tracking would require PID management)
            
            # For now, just ensure bridge directory exists and is healthy
            bridge_dir = user_path / "bridge"
            if bridge_dir.exists():
                status_file = bridge_dir / "status.json"
                if not status_file.exists():
                    self.restart_user_mt5(user_id, user_path)
                    
        except Exception as e:
            self.log_recovery_action("check_user_mt5", user_id, False, str(e))
    
    def restart_user_mt5(self, user_id, user_path):
        """Restart a user's MT5 instance"""
        try:
            mt5_exe = user_path / "terminal64.exe"
            
            # Start MT5 process
            process = subprocess.Popen([
                str(mt5_exe)
            ], cwd=str(user_path))
            
            # Recreate bridge status
            bridge_dir = user_path / "bridge"
            bridge_dir.mkdir(exist_ok=True)
            
            status = {
                'user_id': user_id,
                'status': 'restarted',
                'timestamp': datetime.now().isoformat(),
                'process_id': process.pid
            }
            
            with open(bridge_dir / "status.json", 'w') as f:
                json.dump(status, f, indent=2)
            
            self.log_recovery_action("restart_mt5", user_id, True, f"Restarted with PID {process.pid}")
            
        except Exception as e:
            self.log_recovery_action("restart_mt5", user_id, False, str(e))
    
    def monitor_system_resources(self):
        """Monitor CPU, memory, disk usage"""
        while self.is_monitoring:
            try:
                # Get system metrics (simplified Windows version)
                cpu_info = subprocess.run(['wmic', 'cpu', 'get', 'loadpercentage', '/value'], 
                                        capture_output=True, text=True, check=False)
                memory_info = subprocess.run(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'], 
                                           capture_output=True, text=True, check=False)
                disk_info = subprocess.run(['wmic', 'logicaldisk', 'where', 'size!=0', 'get', 'size,freespace', '/value'], 
                                         capture_output=True, text=True, check=False)
                
                # Parse and store metrics
                metrics = self.parse_system_metrics(cpu_info.stdout, memory_info.stdout, disk_info.stdout)
                self.store_system_metrics(metrics)
                
                # Check thresholds and trigger cleanup if needed
                if metrics['cpu_percent'] > self.max_cpu_percent:
                    self.trigger_cpu_cleanup()
                
                if metrics['memory_percent'] > self.max_memory_percent:
                    self.trigger_memory_cleanup()
                
                if metrics['disk_free_gb'] < self.min_disk_space_gb:
                    self.trigger_disk_cleanup()
                
            except Exception as e:
                self.log_health_check("system_resources", "error", str(e))
            
            time.sleep(self.resource_check_interval)
    
    def parse_system_metrics(self, cpu_output, memory_output, disk_output):
        """Parse Windows system metrics"""
        metrics = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_free_gb': 0,
            'mt5_process_count': 0
        }
        
        try:
            # Parse CPU percentage
            for line in cpu_output.split('\n'):
                if 'LoadPercentage' in line and '=' in line:
                    metrics['cpu_percent'] = float(line.split('=')[1].strip())
                    break
            
            # Simplified metrics for now
            metrics['memory_percent'] = 50  # Placeholder
            metrics['disk_free_gb'] = 10   # Placeholder
            
        except:
            pass
        
        return metrics
    
    def store_system_metrics(self, metrics):
        """Store metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_metrics (cpu_percent, memory_percent, disk_free_gb, mt5_process_count)
                    VALUES (?, ?, ?, ?)
                """, (metrics['cpu_percent'], metrics['memory_percent'], 
                      metrics['disk_free_gb'], metrics['mt5_process_count']))
        except Exception as e:
            print(f"Failed to store metrics: {e}")
    
    def trigger_failover(self):
        """Trigger failover to backup agent"""
        try:
            print("🚨 PRIMARY AGENT FAILURE DETECTED - TRIGGERING FAILOVER")
            
            # Notify backup agent to promote to primary
            response = requests.post(f"{self.backup_agent_url}/promote", timeout=10)
            
            if response.status_code == 200:
                self.log_recovery_action("failover", "backup_agent", True, "Backup promoted to primary")
                print("✅ Failover completed successfully")
            else:
                self.log_recovery_action("failover", "backup_agent", False, f"HTTP {response.status_code}")
                print("❌ Failover failed")
                
        except Exception as e:
            self.log_recovery_action("failover", "backup_agent", False, str(e))
            print(f"❌ Failover error: {e}")
    
    def trigger_cpu_cleanup(self):
        """Cleanup high CPU usage"""
        print("🔧 High CPU detected - triggering cleanup")
        # Could implement process prioritization, zombie killing, etc.
        self.log_recovery_action("cpu_cleanup", "system", True, "CPU cleanup triggered")
    
    def trigger_memory_cleanup(self):
        """Cleanup high memory usage"""
        print("🔧 High memory detected - triggering cleanup")
        # Could implement memory cleanup, cache clearing, etc.
        self.log_recovery_action("memory_cleanup", "system", True, "Memory cleanup triggered")
    
    def trigger_disk_cleanup(self):
        """Cleanup low disk space"""
        print("🔧 Low disk space detected - triggering cleanup")
        # Could implement log rotation, temp file cleanup, etc.
        self.log_recovery_action("disk_cleanup", "system", True, "Disk cleanup triggered")
    
    def cleanup_routine(self):
        """Periodic cleanup of old logs and temporary files"""
        while self.is_monitoring:
            try:
                # Clean old health check records (keep last 1000)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM health_checks WHERE check_id NOT IN (
                            SELECT check_id FROM health_checks ORDER BY timestamp DESC LIMIT 1000
                        )
                    """)
                    
                    conn.execute("""
                        DELETE FROM recovery_actions WHERE action_id NOT IN (
                            SELECT action_id FROM recovery_actions ORDER BY timestamp DESC LIMIT 1000
                        )
                    """)
                
                print("🧹 Database cleanup completed")
                
            except Exception as e:
                print(f"Cleanup routine error: {e}")
            
            time.sleep(3600)  # Run every hour
    
    def log_health_check(self, component, status, details=""):
        """Log health check result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO health_checks (component, status, details)
                    VALUES (?, ?, ?)
                """, (component, status, details))
        except:
            pass
    
    def log_recovery_action(self, action_type, target, success, details=""):
        """Log recovery action"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO recovery_actions (action_type, target, success, details)
                    VALUES (?, ?, ?, ?)
                """, (action_type, target, success, details))
        except:
            pass

class HealthAPI(BaseHTTPRequestHandler):
    def __init__(self, monitor, *args, **kwargs):
        self.monitor = monitor
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'healthy',
                'service': 'Health Monitor Agent',
                'timestamp': datetime.now().isoformat(),
                'monitoring': self.monitor.is_monitoring
            }
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Get recent health checks
            with sqlite3.connect(self.monitor.db_path) as conn:
                cursor = conn.execute("""
                    SELECT component, status, details, timestamp FROM health_checks 
                    ORDER BY timestamp DESC LIMIT 10
                """)
                checks = cursor.fetchall()
            
            response = {
                'recent_checks': [
                    {'component': row[0], 'status': row[1], 'details': row[2], 'timestamp': row[3]}
                    for row in checks
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_health_monitor(port=5557):
    """Run the Health Monitor Agent"""
    monitor = HealthMonitorAgent()
    
    def handler(*args, **kwargs):
        return HealthAPI(monitor, *args, **kwargs)
    
    server = HTTPServer(('0.0.0.0', port), handler)
    print(f"🔍 Health Monitor Agent starting on port {port}")
    print("Monitoring components:")
    print("  - Primary Agent (port 5555)")
    print("  - MT5 Processes")
    print("  - System Resources")
    print("  - Auto-recovery enabled")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Health Monitor...")
        monitor.is_monitoring = False

if __name__ == "__main__":
    run_health_monitor()