#!/usr/bin/env python3
"""
SIMPLE MT5 FARM AGENT
Basic version without external dependencies for Windows deployment
"""

import json
import os
import time
import sqlite3
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket

class SimpleFarmAgent:
    def __init__(self):
        self.farm_path = Path("C:/MT5_Farm")
        self.masters_path = self.farm_path / "Masters"
        self.clones_path = self.farm_path / "Clones"
        
        # Ensure directories exist
        self.clones_path.mkdir(parents=True, exist_ok=True)
        (self.farm_path / "Logs").mkdir(parents=True, exist_ok=True)
        
        # Farm configuration
        self.broker_types = {
            'PRESS_PASS': {'port_range': (9401, 9600), 'magic_range': (50001, 50200)},
            'Forex_Demo': {'port_range': (9201, 9225), 'magic_range': (30001, 30025)},
            'Forex_Live': {'port_range': (9101, 9200), 'magic_range': (20001, 20100)},
            'Coinexx_Demo': {'port_range': (9301, 9310), 'magic_range': (40001, 40010)},
            'Coinexx_Live': {'port_range': (9001, 9015), 'magic_range': (10001, 10015)}
        }
        
        self.setup_database()
        
    def setup_database(self):
        """Initialize farm management database"""
        self.db_path = str(self.farm_path / "farm_management.db")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mt5_instances (
                    instance_id TEXT PRIMARY KEY,
                    broker_type TEXT NOT NULL,
                    status TEXT DEFAULT 'inactive',
                    port INTEGER,
                    magic_number INTEGER,
                    last_heartbeat TIMESTAMP,
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
            """)
    
    def log_action(self, action, target="", status="success", details=""):
        """Log an action to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO maintenance_logs (action, target, status, details)
                    VALUES (?, ?, ?, ?)
                """, (action, target, status, details))
        except Exception as e:
            print(f"Logging failed: {e}")
    
    def get_farm_status(self):
        """Get basic farm status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'overall_health': 'healthy',
                'masters': {},
                'clones': {},
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
                }
            
            # Check clone instances
            clone_count = 0
            if self.clones_path.exists():
                clone_count = len([d for d in self.clones_path.iterdir() if d.is_dir()])
            status['clones']['total_count'] = clone_count
            
            # Check running MT5 processes using tasklist
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], 
                                      capture_output=True, text=True, check=False)
                mt5_count = len([line for line in result.stdout.split('\n') if 'terminal64.exe' in line])
                status['active_instances'] = mt5_count
            except:
                status['active_instances'] = 0
                
            return status
            
        except Exception as e:
            return {'error': str(e)}
    
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
            
            # Copy master to instance
            shutil.copytree(str(master_path), str(instance_path), dirs_exist_ok=True)
            
            # Allocate port and magic number
            port = self.allocate_port(broker_type)
            magic = self.allocate_magic_number(broker_type)
            
            # Register in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO mt5_instances (instance_id, broker_type, port, magic_number, status)
                    VALUES (?, ?, ?, ?, 'deployed')
                """, (instance_id, broker_type, port, magic))
            
            self.log_action("deploy_instance", instance_id, "success", f"{broker_type} port:{port} magic:{magic}")
            
            return {
                'status': 'success',
                'instance_id': instance_id,
                'broker_type': broker_type,
                'port': port,
                'magic_number': magic,
                'path': str(instance_path)
            }
            
        except Exception as e:
            self.log_action("deploy_instance", config.get('instance_id', 'unknown'), "error", str(e))
            return {'error': str(e)}
    
    def allocate_port(self, broker_type):
        """Find next available port"""
        port_range = self.broker_types[broker_type]['port_range']
        for port in range(port_range[0], port_range[1] + 1):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM mt5_instances WHERE port = ?", (port,))
                if cursor.fetchone()[0] == 0:
                    return port
        return None
    
    def allocate_magic_number(self, broker_type):
        """Find next available magic number"""
        magic_range = self.broker_types[broker_type]['magic_range']
        for magic in range(magic_range[0], magic_range[1] + 1):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM mt5_instances WHERE magic_number = ?", (magic,))
                if cursor.fetchone()[0] == 0:
                    return magic
        return None
    
    def execute_cleanup(self, cleanup_type='standard'):
        """Basic cleanup functionality"""
        try:
            files_removed = 0
            
            # Define cleanup patterns
            cleanup_dirs = [
                str(self.farm_path / "Logs"),
                str(self.farm_path / "Temp")
            ]
            
            for dir_path in cleanup_dirs:
                if os.path.exists(dir_path):
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            if file.endswith(('.log', '.tmp')) and file != 'farm_agent.log':
                                try:
                                    file_path = os.path.join(root, file)
                                    # Only remove files older than 24 hours
                                    if os.path.getmtime(file_path) < time.time() - 86400:
                                        os.remove(file_path)
                                        files_removed += 1
                                except:
                                    pass
            
            self.log_action("cleanup", cleanup_type, "success", f"Removed {files_removed} files")
            
            return {
                'status': 'success',
                'cleanup_type': cleanup_type,
                'files_removed': files_removed
            }
        except Exception as e:
            self.log_action("cleanup", cleanup_type, "error", str(e))
            return {'error': str(e)}

class FarmRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, farm_agent, *args, **kwargs):
        self.farm_agent = farm_agent
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0-simple',
                'capabilities': ['basic_farm_management', 'instance_deployment', 'cleanup']
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/farm/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = self.farm_agent.get_farm_status()
            self.wfile.write(json.dumps(status).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode()) if post_data else {}
        except:
            data = {}
        
        if self.path == '/farm/deploy':
            response = self.farm_agent.deploy_mt5_instance(data)
        elif self.path == '/farm/cleanup':
            cleanup_type = data.get('type', 'standard')
            response = self.farm_agent.execute_cleanup(cleanup_type)
        else:
            response = {'error': 'Unknown endpoint'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass

def run_farm_agent(port=5558):
    """Run the simple farm agent"""
    farm_agent = SimpleFarmAgent()
    
    def handler(*args, **kwargs):
        return FarmRequestHandler(farm_agent, *args, **kwargs)
    
    server = HTTPServer(('0.0.0.0', port), handler)
    print(f"Simple Farm Agent starting on port {port}")
    print("Available endpoints:")
    print("  GET  /health - Agent health check")
    print("  GET  /farm/status - Farm status")
    print("  POST /farm/deploy - Deploy MT5 instance")
    print("  POST /farm/cleanup - Execute cleanup")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.shutdown()

if __name__ == "__main__":
    run_farm_agent()