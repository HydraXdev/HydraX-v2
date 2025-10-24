#!/usr/bin/env python3
"""
Admin API for System Health Monitoring
Provides comprehensive system status for admin dashboard
"""

import json
import os
import subprocess
import sqlite3
import psutil
import time
from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path("/root/HydraX-v2")
DB_PATH = BASE_DIR / "bitten.db"
LOG_DIR = BASE_DIR

def get_pm2_status():
    """Get PM2 process status"""
    try:
        result = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            processes = json.loads(result.stdout)

            # Format process data
            formatted = []
            for proc in processes:
                formatted.append({
                    'name': proc.get('name', 'unknown'),
                    'pid': proc.get('pid', 0),
                    'status': proc.get('pm2_env', {}).get('status', 'unknown'),
                    'uptime': proc.get('pm2_env', {}).get('pm_uptime', 0),
                    'restarts': proc.get('pm2_env', {}).get('restart_time', 0),
                    'cpu': proc.get('monit', {}).get('cpu', 0),
                    'memory': proc.get('monit', {}).get('memory', 0),
                    'script': proc.get('pm2_env', {}).get('pm_exec_path', '')
                })

            return {'success': True, 'processes': formatted}
        else:
            return {'success': False, 'error': result.stderr}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_zmq_ports():
    """Check ZMQ port status"""
    try:
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )

        ports_to_check = [5555, 5556, 5557, 5558, 5560, 8888, 8892, 8899]
        port_status = []

        for port in ports_to_check:
            listening = f':{port}' in result.stdout

            # Find process using port
            process_name = 'unknown'
            if listening:
                try:
                    lsof_result = subprocess.run(
                        ['lsof', '-i', f':{port}', '-t'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if lsof_result.stdout.strip():
                        pid = lsof_result.stdout.strip().split('\n')[0]
                        try:
                            proc = psutil.Process(int(pid))
                            process_name = proc.name()
                        except:
                            pass
                except:
                    pass

            port_status.append({
                'port': port,
                'status': 'listening' if listening else 'closed',
                'process': process_name
            })

        return {'success': True, 'ports': port_status}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_database_health():
    """Get SQLite database health metrics"""
    try:
        if not DB_PATH.exists():
            return {'success': False, 'error': 'Database not found'}

        # Get file size
        size_bytes = DB_PATH.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        # Get table counts
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Count tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]

        # Count signals
        try:
            cursor.execute("SELECT COUNT(*) FROM signals")
            signal_count = cursor.fetchone()[0]
        except:
            signal_count = 0

        # Count fires
        try:
            cursor.execute("SELECT COUNT(*) FROM fires")
            fire_count = cursor.fetchone()[0]
        except:
            fire_count = 0

        # Count missions
        try:
            cursor.execute("SELECT COUNT(*) FROM missions")
            mission_count = cursor.fetchone()[0]
        except:
            mission_count = 0

        # Get last backup time (check for backup files)
        backup_files = list(BASE_DIR.glob("bitten_backup_*.db"))
        last_backup = None
        if backup_files:
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            last_backup = int(latest_backup.stat().st_mtime)

        conn.close()

        return {
            'success': True,
            'database': {
                'size_mb': round(size_mb, 2),
                'size_bytes': size_bytes,
                'table_count': table_count,
                'signal_count': signal_count,
                'fire_count': fire_count,
                'mission_count': mission_count,
                'last_backup': last_backup
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_recent_errors():
    """Get recent error logs from all log files"""
    try:
        errors = []
        log_files = list(LOG_DIR.glob("*.log"))

        for log_file in log_files[:10]:  # Check first 10 log files
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Get last 50 lines
                    recent_lines = lines[-50:] if len(lines) > 50 else lines

                    for line in recent_lines:
                        if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'critical']):
                            errors.append({
                                'file': log_file.name,
                                'message': line.strip(),
                                'timestamp': int(time.time())  # Approximate
                            })
            except:
                continue

        # Sort by newest first, limit to 50
        errors = sorted(errors, key=lambda x: x['timestamp'], reverse=True)[:50]

        return {'success': True, 'errors': errors}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_system_metrics():
    """Get system-level metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

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
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/api/admin/system-health', methods=['GET'])
def system_health():
    """Main system health endpoint"""
    try:
        pm2_data = get_pm2_status()
        zmq_data = get_zmq_ports()
        db_data = get_database_health()
        error_data = get_recent_errors()
        metrics_data = get_system_metrics()

        return jsonify({
            'timestamp': int(time.time()),
            'pm2': pm2_data,
            'zmq_ports': zmq_data,
            'database': db_data,
            'recent_errors': error_data,
            'system_metrics': metrics_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/restart-process/<process_name>', methods=['POST'])
def restart_process(process_name):
    """Restart a PM2 process"""
    try:
        result = subprocess.run(
            ['pm2', 'restart', process_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Process {process_name} restarted'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/stop-process/<process_name>', methods=['POST'])
def stop_process(process_name):
    """Stop a PM2 process"""
    try:
        result = subprocess.run(
            ['pm2', 'stop', process_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Process {process_name} stopped'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/restart-all', methods=['POST'])
def restart_all():
    """Restart all PM2 processes"""
    try:
        result = subprocess.run(
            ['pm2', 'restart', 'all'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'All processes restarted'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clear-logs', methods=['POST'])
def clear_logs():
    """Clear PM2 logs"""
    try:
        result = subprocess.run(
            ['pm2', 'flush'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'Logs cleared'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/backup-database', methods=['POST'])
def backup_database():
    """Backup the SQLite database"""
    try:
        timestamp = int(time.time())
        backup_path = BASE_DIR / f"bitten_backup_{timestamp}.db"

        # Copy database
        subprocess.run(
            ['cp', str(DB_PATH), str(backup_path)],
            check=True,
            timeout=30
        )

        return jsonify({
            'success': True,
            'message': f'Database backed up to {backup_path.name}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/process-logs/<process_name>', methods=['GET'])
def process_logs(process_name):
    """Get logs for a specific process"""
    try:
        result = subprocess.run(
            ['pm2', 'logs', process_name, '--lines', '100', '--nostream'],
            capture_output=True,
            text=True,
            timeout=5
        )

        return jsonify({
            'success': True,
            'logs': result.stdout
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/healthz', methods=['GET'])
def healthz():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': int(time.time())})

if __name__ == '__main__':
    print("🚀 Admin API starting on http://localhost:8890")
    print("📊 System Health: http://localhost:8890/api/admin/system-health")
    app.run(host='0.0.0.0', port=8890, debug=False)
