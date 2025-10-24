#!/usr/bin/env python3
"""
Firebase System Health Sync
============================
Syncs comprehensive system health data to Firestore for the Admin Health dashboard.

Updates every 30 seconds to system_stats/current document with:
- PM2 process status
- ZMQ port bindings
- Database health metrics
- System metrics (CPU, memory, disk)
- Recent error logs

Author: BITTEN System
Date: October 16, 2025
"""

import os
import sqlite3
import time
import subprocess
import json
import psutil
from datetime import datetime
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

class SystemHealthSync:
    """Syncs system health data to Firebase for Admin dashboard"""

    def __init__(self):
        # Initialize Firebase (if not already initialized)
        if not firebase_admin._apps:
            cred = credentials.Certificate('/root/bitten-firebase-sa.json')
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.sqlite_db = '/root/HydraX-v2/bitten.db'
        print("🚀 Firebase System Health Sync initialized")

    def get_pm2_processes(self):
        """Get PM2 process information"""
        try:
            result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                processes = json.loads(result.stdout)
                process_list = []
                for proc in processes:
                    process_list.append({
                        'name': proc.get('name', 'unknown'),
                        'pid': proc.get('pid', 0),
                        'status': proc.get('pm2_env', {}).get('status', 'unknown'),
                        'uptime': proc.get('pm2_env', {}).get('pm_uptime', 0),
                        'restarts': proc.get('pm2_env', {}).get('restart_time', 0),
                        'cpu': proc.get('monit', {}).get('cpu', 0),
                        'memory': proc.get('monit', {}).get('memory', 0),
                        'script': proc.get('pm2_env', {}).get('pm_exec_path', '')
                    })
                return {'success': True, 'processes': process_list}
            else:
                return {'success': False, 'error': 'PM2 command failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_zmq_ports(self):
        """Check ZMQ port bindings"""
        ports = [5555, 5556, 5557, 5558, 5560]
        port_list = []

        try:
            # Check listening ports
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port in ports and conn.status == 'LISTEN':
                    try:
                        process = psutil.Process(conn.pid) if conn.pid else None
                        process_name = process.name() if process else 'unknown'
                    except:
                        process_name = 'unknown'

                    port_list.append({
                        'port': conn.laddr.port,
                        'status': 'listening',
                        'process': process_name
                    })

            # Add missing ports as closed
            listening_ports = {p['port'] for p in port_list}
            for port in ports:
                if port not in listening_ports:
                    port_list.append({
                        'port': port,
                        'status': 'closed',
                        'process': 'none'
                    })

            return {'success': True, 'ports': sorted(port_list, key=lambda x: x['port'])}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_database_health(self):
        """Get database health metrics"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()

            # Database size
            db_size = os.path.getsize(self.sqlite_db)

            # Table count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # Record counts
            cursor.execute("SELECT COUNT(*) FROM signals")
            signal_count = cursor.fetchone()[0]

            try:
                cursor.execute("SELECT COUNT(*) FROM fires")
                fire_count = cursor.fetchone()[0]
            except:
                fire_count = 0

            try:
                cursor.execute("SELECT COUNT(*) FROM missions")
                mission_count = cursor.fetchone()[0]
            except:
                mission_count = 0

            conn.close()

            return {
                'success': True,
                'database': {
                    'size_mb': round(db_size / (1024 * 1024), 2),
                    'size_bytes': db_size,
                    'table_count': table_count,
                    'signal_count': signal_count,
                    'fire_count': fire_count,
                    'mission_count': mission_count,
                    'last_backup': None  # Can be enhanced with actual backup tracking
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_system_metrics(self):
        """Get system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg()

            return {
                'success': True,
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': round(memory.used / (1024**3), 2),
                    'memory_total_gb': round(memory.total / (1024**3), 2),
                    'disk_percent': disk.percent,
                    'disk_used_gb': round(disk.used / (1024**3), 2),
                    'disk_total_gb': round(disk.total / (1024**3), 2),
                    'load_avg': list(load_avg)
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_recent_errors(self, max_errors=10):
        """Get recent errors from PM2 logs"""
        errors = []
        log_dirs = [
            '/root/.pm2/logs/',
            '/root/HydraX-v2/',
        ]

        try:
            for log_dir in log_dirs:
                if not os.path.exists(log_dir):
                    continue

                for log_file in Path(log_dir).glob('*error*.log'):
                    try:
                        # Read last 20 lines
                        with open(log_file, 'r') as f:
                            lines = f.readlines()[-20:]
                            for line in lines:
                                line = line.strip()
                                if line and ('error' in line.lower() or 'exception' in line.lower()):
                                    errors.append({
                                        'file': log_file.name,
                                        'message': line[:200],  # Truncate long messages
                                        'timestamp': int(time.time())
                                    })
                                    if len(errors) >= max_errors:
                                        break
                    except:
                        continue

                    if len(errors) >= max_errors:
                        break

            return {'success': True, 'errors': errors[-max_errors:]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def sync_to_firebase(self):
        """Sync all health data to Firebase"""
        try:
            health_data = {
                'timestamp': int(time.time()),
                'pm2': self.get_pm2_processes(),
                'zmq_ports': self.get_zmq_ports(),
                'database': self.get_database_health(),
                'system_metrics': self.get_system_metrics(),
                'recent_errors': self.get_recent_errors()
            }

            # Write to Firestore
            self.db.collection('system_stats').document('current').set(health_data)

            # Print summary
            pm2_ok = health_data['pm2']['success']
            port_ok = health_data['zmq_ports']['success']
            db_ok = health_data['database']['success']
            metrics_ok = health_data['system_metrics']['success']

            status = "✅" if all([pm2_ok, port_ok, db_ok, metrics_ok]) else "⚠️"

            pm2_count = len(health_data['pm2'].get('processes', [])) if pm2_ok else 0
            port_count = len([p for p in health_data['zmq_ports'].get('ports', []) if p['status'] == 'listening']) if port_ok else 0

            print(f"{status} Health sync: {pm2_count} PM2 processes, {port_count}/5 ZMQ ports, "
                  f"{health_data['system_metrics']['metrics']['cpu_percent']:.1f}% CPU" if metrics_ok else "N/A CPU")

        except Exception as e:
            print(f"❌ Error syncing health data: {e}")

    def run(self, interval=30):
        """Main loop - sync every 30 seconds"""
        print(f"🔄 Starting health sync loop (every {interval}s)")
        while True:
            try:
                self.sync_to_firebase()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n⚠️  Shutdown signal received")
                break
            except Exception as e:
                print(f"❌ Fatal error: {e}")
                time.sleep(interval)

if __name__ == '__main__':
    syncer = SystemHealthSync()
    syncer.run(interval=30)
