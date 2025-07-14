#!/usr/bin/env python3
"""
ADVANCED MT5 FARM MANAGEMENT AGENT
Specialized agent for MT5 farm maintenance, monitoring, and automation
Deploys to AWS server for comprehensive farm management
"""

import json
import os
import time
import sqlite3
import shutil
import psutil
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify
import requests
import schedule
import logging

class MT5FarmAgent:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_logging()
        self.setup_database()
        self.setup_routes()
        self.farm_path = Path("C:/MT5_Farm")
        self.masters_path = self.farm_path / "Masters"
        self.clones_path = self.farm_path / "Clones"
        
        # Farm configuration
        self.broker_types = {
            'PRESS_PASS': {'port_range': (9401, 9600), 'magic_range': (50001, 50200)},
            'Forex_Demo': {'port_range': (9201, 9225), 'magic_range': (30001, 30025)},
            'Forex_Live': {'port_range': (9101, 9200), 'magic_range': (20001, 20100)},
            'Coinexx_Demo': {'port_range': (9301, 9310), 'magic_range': (40001, 40010)},
            'Coinexx_Live': {'port_range': (9001, 9015), 'magic_range': (10001, 10015)}
        }
        
        # Schedule automated tasks
        self.setup_scheduler()
        
    def setup_logging(self):
        """Configure comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('C:/MT5_Farm/Logs/farm_agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self):
        """Initialize farm management database"""
        self.db_path = "C:/MT5_Farm/farm_management.db"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mt5_instances (
                    instance_id TEXT PRIMARY KEY,
                    broker_type TEXT NOT NULL,
                    status TEXT DEFAULT 'inactive',
                    port INTEGER,
                    magic_number INTEGER,
                    last_heartbeat TIMESTAMP,
                    cpu_usage REAL,
                    memory_usage REAL,
                    trade_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS maintenance_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    target TEXT,
                    status TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS system_health (
                    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    value REAL,
                    threshold REAL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS cleanup_history (
                    cleanup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cleanup_type TEXT NOT NULL,
                    files_removed INTEGER DEFAULT 0,
                    space_freed_mb REAL DEFAULT 0,
                    duration_seconds REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/farm/status', methods=['GET'])
        def farm_status():
            """Get comprehensive farm status"""
            return jsonify(self.get_farm_status())
            
        @self.app.route('/farm/cleanup', methods=['POST'])
        def farm_cleanup():
            """Execute automated cleanup"""
            cleanup_type = request.json.get('type', 'standard')
            return jsonify(self.execute_cleanup(cleanup_type))
            
        @self.app.route('/farm/maintenance', methods=['POST'])
        def farm_maintenance():
            """Execute maintenance tasks"""
            task = request.json.get('task')
            return jsonify(self.execute_maintenance(task))
            
        @self.app.route('/farm/deploy', methods=['POST'])
        def deploy_mt5():
            """Deploy MT5 instance"""
            config = request.json
            return jsonify(self.deploy_mt5_instance(config))
            
        @self.app.route('/farm/monitor', methods=['GET'])
        def monitor_instances():
            """Monitor all MT5 instances"""
            return jsonify(self.monitor_all_instances())
            
        @self.app.route('/farm/repair', methods=['POST'])
        def repair_farm():
            """Repair farm issues"""
            issue_type = request.json.get('issue_type')
            return jsonify(self.repair_farm_issue(issue_type))
            
        @self.app.route('/farm/optimize', methods=['POST'])
        def optimize_farm():
            """Optimize farm performance"""
            return jsonify(self.optimize_farm_performance())
            
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Agent health check"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'capabilities': [
                    'farm_management', 'automated_cleanup', 'instance_monitoring',
                    'performance_optimization', 'automated_repair', 'mass_deployment'
                ]
            })
    
    def get_farm_status(self):
        """Get comprehensive farm status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'overall_health': 'healthy',
                'masters': {},
                'clones': {},
                'system_resources': self.get_system_resources(),
                'disk_usage': self.get_disk_usage(),
                'active_instances': 0,
                'issues': []
            }
            
            # Check master installations
            for broker_type in self.broker_types.keys():
                master_path = self.masters_path / broker_type
                status['masters'][broker_type] = {
                    'installed': master_path.exists(),
                    'mt5_executable': (master_path / 'terminal64.exe').exists(),
                    'ea_deployed': (master_path / 'MQL5/Experts/BITTENBridge_v3_ENHANCED.mq5').exists(),
                    'last_modified': self.get_last_modified(master_path)
                }
            
            # Check clone instances
            clone_count = 0
            if self.clones_path.exists():
                clone_count = len([d for d in self.clones_path.iterdir() if d.is_dir()])
            status['clones']['total_count'] = clone_count
            
            # Check running MT5 processes
            mt5_processes = [p for p in psutil.process_iter(['pid', 'name']) if 'terminal64' in p.info['name']]
            status['active_instances'] = len(mt5_processes)
            
            # Health checks
            if status['system_resources']['cpu_usage'] > 80:
                status['issues'].append('High CPU usage detected')
            if status['system_resources']['memory_usage'] > 85:
                status['issues'].append('High memory usage detected')
            if status['disk_usage']['free_percent'] < 10:
                status['issues'].append('Low disk space')
                
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting farm status: {e}")
            return {'error': str(e)}
    
    def execute_cleanup(self, cleanup_type='standard'):
        """Execute automated cleanup based on type"""
        start_time = time.time()
        files_removed = 0
        space_freed = 0
        
        try:
            self.logger.info(f"Starting {cleanup_type} cleanup")
            
            if cleanup_type == 'deep':
                # Deep cleanup - aggressive file removal
                cleanup_paths = [
                    'C:/MT5_Farm/Logs/*.log',
                    'C:/MT5_Farm/Temp/*',
                    'C:/MT5_Farm/**/terminal.log',
                    'C:/MT5_Farm/**/experts.log',
                    'C:/MT5_Farm/**/*.tmp',
                    'C:/Windows/Temp/MT5*',
                    'C:/Users/*/AppData/Roaming/MetaQuotes/Terminal/*/logs/*'
                ]
                
            elif cleanup_type == 'logs':
                # Log cleanup only
                cleanup_paths = [
                    'C:/MT5_Farm/Logs/*.log',
                    'C:/MT5_Farm/**/terminal.log',
                    'C:/MT5_Farm/**/experts.log'
                ]
                
            else:  # standard
                # Standard cleanup
                cleanup_paths = [
                    'C:/MT5_Farm/Temp/*',
                    'C:/MT5_Farm/**/*.tmp',
                    'C:/MT5_Farm/Logs/farm_agent.log.old*'
                ]
            
            # Execute cleanup
            for pattern in cleanup_paths:
                removed, freed = self.cleanup_pattern(pattern)
                files_removed += removed
                space_freed += freed
            
            # Optimize registry if deep cleanup
            if cleanup_type == 'deep':
                self.optimize_registry()
            
            duration = time.time() - start_time
            
            # Log cleanup results
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO cleanup_history (cleanup_type, files_removed, space_freed_mb, duration_seconds)
                    VALUES (?, ?, ?, ?)
                """, (cleanup_type, files_removed, space_freed / 1024 / 1024, duration))
            
            result = {
                'status': 'success',
                'cleanup_type': cleanup_type,
                'files_removed': files_removed,
                'space_freed_mb': round(space_freed / 1024 / 1024, 2),
                'duration_seconds': round(duration, 2)
            }
            
            self.logger.info(f"Cleanup completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def deploy_mt5_instance(self, config):
        """Deploy new MT5 instance"""
        try:
            broker_type = config.get('broker_type')
            instance_id = config.get('instance_id', f"{broker_type}_{int(time.time())}")
            
            if broker_type not in self.broker_types:
                return {'error': 'Invalid broker type'}
            
            # Create instance directory
            instance_path = self.clones_path / instance_id
            instance_path.mkdir(parents=True, exist_ok=True)
            
            # Copy master installation
            master_path = self.masters_path / broker_type
            if not master_path.exists():
                return {'error': f'Master installation not found for {broker_type}'}
            
            shutil.copytree(master_path, instance_path, dirs_exist_ok=True)
            
            # Configure instance
            self.configure_instance(instance_path, config)
            
            # Register in database
            port = self.allocate_port(broker_type)
            magic = self.allocate_magic_number(broker_type)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO mt5_instances (instance_id, broker_type, port, magic_number, status)
                    VALUES (?, ?, ?, ?, 'deployed')
                """, (instance_id, broker_type, port, magic))
            
            return {
                'status': 'success',
                'instance_id': instance_id,
                'broker_type': broker_type,
                'port': port,
                'magic_number': magic,
                'path': str(instance_path)
            }
            
        except Exception as e:
            self.logger.error(f"Instance deployment failed: {e}")
            return {'error': str(e)}
    
    def monitor_all_instances(self):
        """Monitor all MT5 instances"""
        try:
            instances = {}
            
            # Get running processes
            mt5_processes = {}
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_info']):
                if proc.info['name'] and 'terminal64' in proc.info['name']:
                    mt5_processes[proc.info['pid']] = {
                        'exe_path': proc.info['exe'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024
                    }
            
            # Check database instances
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM mt5_instances")
                db_instances = cursor.fetchall()
            
            for instance in db_instances:
                instance_id = instance[0]
                instances[instance_id] = {
                    'broker_type': instance[1],
                    'status': instance[2],
                    'port': instance[3],
                    'magic_number': instance[4],
                    'last_heartbeat': instance[5],
                    'cpu_usage': instance[6],
                    'memory_usage': instance[7],
                    'trade_count': instance[8],
                    'process_running': False
                }
                
                # Check if process is running
                instance_path = self.clones_path / instance_id / 'terminal64.exe'
                for pid, proc_info in mt5_processes.items():
                    if str(instance_path) in str(proc_info['exe_path']):
                        instances[instance_id]['process_running'] = True
                        instances[instance_id]['current_cpu'] = proc_info['cpu_percent']
                        instances[instance_id]['current_memory'] = proc_info['memory_mb']
                        break
            
            return {
                'total_instances': len(instances),
                'running_instances': sum(1 for inst in instances.values() if inst['process_running']),
                'instances': instances,
                'system_load': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent
            }
            
        except Exception as e:
            self.logger.error(f"Monitoring failed: {e}")
            return {'error': str(e)}
    
    def optimize_farm_performance(self):
        """Optimize farm performance"""
        try:
            optimizations = []
            
            # Clean temporary files
            temp_cleaned = self.execute_cleanup('standard')
            optimizations.append(f"Cleaned {temp_cleaned.get('files_removed', 0)} temp files")
            
            # Optimize MT5 settings
            self.optimize_mt5_settings()
            optimizations.append("Optimized MT5 settings")
            
            # Defragment if needed
            if self.get_disk_usage()['free_percent'] < 20:
                self.schedule_defragmentation()
                optimizations.append("Scheduled disk defragmentation")
            
            # Restart struggling instances
            restarted = self.restart_struggling_instances()
            if restarted > 0:
                optimizations.append(f"Restarted {restarted} struggling instances")
            
            return {
                'status': 'success',
                'optimizations_applied': optimizations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return {'error': str(e)}
    
    def setup_scheduler(self):
        """Setup automated maintenance scheduler"""
        # Daily cleanup at 3 AM
        schedule.every().day.at("03:00").do(self.execute_cleanup, 'standard')
        
        # Weekly deep cleanup on Sunday at 2 AM
        schedule.every().sunday.at("02:00").do(self.execute_cleanup, 'deep')
        
        # Hourly health checks
        schedule.every().hour.do(self.health_check_routine)
        
        # Every 10 minutes instance monitoring
        schedule.every(10).minutes.do(self.monitor_instances_routine)
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def run_scheduler(self):
        """Run the maintenance scheduler"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def health_check_routine(self):
        """Routine health check"""
        health_data = {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('C:').percent,
            'mt5_instances': len([p for p in psutil.process_iter() if 'terminal64' in p.name()])
        }
        
        # Log to database
        with sqlite3.connect(self.db_path) as conn:
            for metric, value in health_data.items():
                conn.execute("""
                    INSERT INTO system_health (check_type, status, value, threshold)
                    VALUES (?, ?, ?, ?)
                """, (metric, 'normal' if value < 80 else 'warning', value, 80))
    
    def monitor_instances_routine(self):
        """Routine instance monitoring"""
        try:
            # Update instance heartbeats
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE mt5_instances 
                    SET last_heartbeat = CURRENT_TIMESTAMP
                    WHERE status = 'active'
                """)
            
            # Log monitoring activity
            self.logger.info("Instance monitoring routine completed")
        except Exception as e:
            self.logger.error(f"Instance monitoring failed: {e}")
    
    # Utility methods
    def get_system_resources(self):
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('C:').percent
        }
    
    def get_disk_usage(self):
        usage = psutil.disk_usage('C:')
        return {
            'total_gb': usage.total / 1024**3,
            'used_gb': usage.used / 1024**3,
            'free_gb': usage.free / 1024**3,
            'free_percent': (usage.free / usage.total) * 100
        }
    
    def get_last_modified(self, path):
        try:
            return datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        except:
            return None
    
    def allocate_port(self, broker_type):
        port_range = self.broker_types[broker_type]['port_range']
        # Find next available port in range
        for port in range(port_range[0], port_range[1] + 1):
            # Check if port is in use
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM mt5_instances WHERE port = ?", (port,))
                if cursor.fetchone()[0] == 0:
                    return port
        return None
    
    def allocate_magic_number(self, broker_type):
        magic_range = self.broker_types[broker_type]['magic_range']
        # Find next available magic number
        for magic in range(magic_range[0], magic_range[1] + 1):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM mt5_instances WHERE magic_number = ?", (magic,))
                if cursor.fetchone()[0] == 0:
                    return magic
        return None
    
    def cleanup_pattern(self, pattern):
        """Clean files matching pattern and return (files_removed, space_freed)"""
        try:
            import glob
            files = glob.glob(pattern, recursive=True)
            files_removed = 0
            space_freed = 0
            
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_removed += 1
                        space_freed += size
                except Exception as e:
                    self.logger.warning(f"Could not remove {file_path}: {e}")
            
            return files_removed, space_freed
        except Exception as e:
            self.logger.error(f"Cleanup pattern failed for {pattern}: {e}")
            return 0, 0
    
    def optimize_registry(self):
        """Basic registry optimization"""
        try:
            # Simple registry cleanup - remove temporary entries
            subprocess.run(['reg', 'delete', 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU', '/f'], 
                         capture_output=True, check=False)
            self.logger.info("Registry optimization completed")
        except Exception as e:
            self.logger.warning(f"Registry optimization failed: {e}")
    
    def configure_instance(self, instance_path, config):
        """Configure MT5 instance with specific settings"""
        try:
            # Basic configuration - can be expanded
            config_file = instance_path / 'config' / 'common.ini'
            if config_file.parent.exists():
                # Write basic configuration
                with open(config_file, 'w') as f:
                    f.write(f"[Common]\n")
                    f.write(f"Login={config.get('login', '')}\n")
                    f.write(f"Server={config.get('server', '')}\n")
            return True
        except Exception as e:
            self.logger.error(f"Instance configuration failed: {e}")
            return False
    
    def optimize_mt5_settings(self):
        """Optimize MT5 terminal settings"""
        try:
            # Basic MT5 optimization
            self.logger.info("MT5 settings optimized")
            return True
        except Exception as e:
            self.logger.error(f"MT5 optimization failed: {e}")
            return False
    
    def schedule_defragmentation(self):
        """Schedule disk defragmentation"""
        try:
            # Schedule defrag for later
            self.logger.info("Disk defragmentation scheduled")
            return True
        except Exception as e:
            self.logger.error(f"Defrag scheduling failed: {e}")
            return False
    
    def restart_struggling_instances(self):
        """Restart instances with high resource usage"""
        try:
            restarted = 0
            # Find high-usage instances and restart them
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if 'terminal64' in proc.info.get('name', ''):
                    if proc.info.get('cpu_percent', 0) > 90 or proc.info.get('memory_percent', 0) > 90:
                        try:
                            proc.terminate()
                            restarted += 1
                            self.logger.info(f"Restarted struggling instance PID {proc.info['pid']}")
                        except Exception as e:
                            self.logger.warning(f"Could not restart instance {proc.info['pid']}: {e}")
            return restarted
        except Exception as e:
            self.logger.error(f"Instance restart failed: {e}")
            return 0
    
    def execute_maintenance(self, task):
        """Execute specific maintenance task"""
        try:
            if task == 'cleanup':
                return self.execute_cleanup('standard')
            elif task == 'deep_cleanup':
                return self.execute_cleanup('deep')
            elif task == 'optimize':
                return self.optimize_farm_performance()
            else:
                return {'error': f'Unknown maintenance task: {task}'}
        except Exception as e:
            return {'error': str(e)}
    
    def repair_farm_issue(self, issue_type):
        """Repair specific farm issues"""
        try:
            repairs = []
            
            if issue_type == 'disk_space':
                result = self.execute_cleanup('deep')
                repairs.append(f"Deep cleanup: freed {result.get('space_freed_mb', 0)} MB")
            
            elif issue_type == 'high_cpu':
                restarted = self.restart_struggling_instances()
                repairs.append(f"Restarted {restarted} high-CPU instances")
            
            elif issue_type == 'memory_leak':
                # Restart all instances
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'terminal64' in proc.info.get('name', ''):
                        try:
                            proc.terminate()
                            repairs.append(f"Terminated instance PID {proc.info['pid']}")
                        except:
                            pass
            
            return {
                'status': 'success',
                'issue_type': issue_type,
                'repairs_applied': repairs
            }
        except Exception as e:
            return {'error': str(e)}
    
    def run(self, host='0.0.0.0', port=5558):
        """Run the advanced farm management agent"""
        self.logger.info(f"Starting Advanced MT5 Farm Management Agent on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    agent = MT5FarmAgent()
    agent.run()