#!/usr/bin/env python3
"""
BITTEN CLONE MANAGER
Handles user-specific MT5 instance creation from BITTEN_MASTER template
"""

import json
import os
import shutil
import subprocess
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
import configparser

class BittenCloneManager:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_database()
        self.setup_routes()
        
        # Paths
        self.master_path = Path("C:/MT5_Farm/Masters/BITTEN_MASTER")
        self.users_path = Path("C:/MT5_Farm/Users")
        self.users_path.mkdir(parents=True, exist_ok=True)
        
        # Port allocation range for user instances
        self.port_start = 20000
        self.port_end = 25000
        
    def setup_database(self):
        """Initialize user clone tracking database"""
        self.db_path = "C:/MT5_Farm/bitten_clones.db"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_clones (
                    user_id TEXT PRIMARY KEY,
                    clone_path TEXT NOT NULL,
                    port INTEGER UNIQUE,
                    status TEXT DEFAULT 'created',
                    broker_type TEXT DEFAULT 'demo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP,
                    process_id INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS clone_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    status TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'BITTEN Clone Manager',
                'version': '1.0.0'
            })
        
        @self.app.route('/clone/create', methods=['POST'])
        def create_clone():
            """Create new user clone"""
            data = request.json
            user_id = data.get('user_id')
            credentials = data.get('credentials')  # Optional for live accounts
            
            if not user_id:
                return jsonify({'error': 'user_id required'}), 400
            
            try:
                result = self.create_user_clone(user_id, credentials)
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/clone/status/<user_id>', methods=['GET'])
        def clone_status(user_id):
            """Get clone status for user"""
            status = self.get_clone_status(user_id)
            return jsonify(status)
        
        @self.app.route('/clone/start/<user_id>', methods=['POST'])
        def start_clone(user_id):
            """Start MT5 instance for user"""
            try:
                result = self.start_user_mt5(user_id)
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/clone/stop/<user_id>', methods=['POST'])
        def stop_clone(user_id):
            """Stop MT5 instance for user"""
            try:
                result = self.stop_user_mt5(user_id)
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/clone/destroy/<user_id>', methods=['DELETE'])
        def destroy_clone(user_id):
            """Completely remove user clone"""
            try:
                result = self.destroy_user_clone(user_id)
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/clones/list', methods=['GET'])
        def list_clones():
            """List all user clones"""
            clones = self.list_all_clones()
            return jsonify(clones)
    
    def create_user_clone(self, user_id, credentials=None):
        """Create a new MT5 clone for user"""
        try:
            self.log_action(user_id, "create_clone", "started", f"Creating clone for user {user_id}")
            
            # Check if user already has a clone
            existing = self.get_clone_status(user_id)
            if existing and existing.get('exists'):
                raise Exception(f"User {user_id} already has a clone")
            
            # Create user directory
            user_path = self.users_path / f"user_{user_id}"
            if user_path.exists():
                shutil.rmtree(user_path)
            
            # Copy BITTEN_MASTER template
            self.log_action(user_id, "copy_template", "started", "Copying BITTEN_MASTER template")
            shutil.copytree(str(self.master_path), str(user_path))
            
            # Allocate port
            port = self.allocate_port(user_id)
            if not port:
                raise Exception("No available ports for user instance")
            
            # Setup file bridge directories
            self.setup_file_bridge(user_id, user_path)
            
            # Configure MT5 for user
            broker_type = 'demo'
            if credentials:
                self.inject_credentials(user_path, credentials)
                broker_type = 'live'
                # Secure wipe credentials after injection
                credentials = None
            
            # Register in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO user_clones (user_id, clone_path, port, broker_type, status)
                    VALUES (?, ?, ?, ?, 'ready')
                """, (user_id, str(user_path), port, broker_type))
            
            self.log_action(user_id, "create_clone", "completed", f"Clone created successfully at {user_path}")
            
            return {
                'status': 'success',
                'user_id': user_id,
                'clone_path': str(user_path),
                'port': port,
                'broker_type': broker_type,
                'bridge_path': str(user_path / 'bridge'),
                'ready_to_start': True
            }
            
        except Exception as e:
            self.log_action(user_id, "create_clone", "error", str(e))
            raise
    
    def inject_credentials(self, user_path, credentials):
        """Inject broker credentials into MT5 configuration"""
        try:
            # Create/modify MT5 configuration files
            config_dir = user_path / 'Config'
            config_dir.mkdir(exist_ok=True)
            
            # Create terminal configuration
            terminal_ini = config_dir / 'terminal.ini'
            config = configparser.ConfigParser()
            
            # Basic terminal settings
            config['Common'] = {
                'Login': credentials.get('username', ''),
                'Password': credentials.get('password', ''),
                'Server': credentials.get('server', ''),
                'AutoTrading': 'true',
                'ExpertAdvisor': 'true'
            }
            
            with open(terminal_ini, 'w') as f:
                config.write(f)
            
            # Create accounts file
            accounts_ini = config_dir / 'accounts.ini'
            with open(accounts_ini, 'w') as f:
                f.write(f"[Account1]\\n")
                f.write(f"Login={credentials.get('username', '')}\\n")
                f.write(f"Server={credentials.get('server', '')}\\n")
            
            return True
            
        except Exception as e:
            raise Exception(f"Credential injection failed: {str(e)}")
    
    def setup_file_bridge(self, user_id, user_path):
        """Setup file-based communication bridge for user"""
        bridge_dir = user_path / 'bridge'
        bridge_dir.mkdir(exist_ok=True)
        
        # Create bridge configuration
        bridge_config = {
            'user_id': user_id,
            'input_file': str(bridge_dir / 'signals_in.json'),
            'output_file': str(bridge_dir / 'results_out.json'),
            'status_file': str(bridge_dir / 'status.json'),
            'heartbeat_file': str(bridge_dir / 'heartbeat.json')
        }
        
        # Write bridge config for EA to read
        with open(bridge_dir / 'bridge_config.json', 'w') as f:
            json.dump(bridge_config, f, indent=2)
        
        # Create initial status file
        initial_status = {
            'user_id': user_id,
            'status': 'initialized',
            'timestamp': datetime.now().isoformat(),
            'ea_version': 'BITTEN_v3_ENHANCED'
        }
        
        with open(bridge_dir / 'status.json', 'w') as f:
            json.dump(initial_status, f, indent=2)
        
        return str(bridge_dir)
    
    def start_user_mt5(self, user_id):
        """Start MT5 instance for user"""
        try:
            # Get user clone info
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT clone_path, port FROM user_clones WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise Exception(f"No clone found for user {user_id}")
                
                clone_path, port = result
            
            # Check if already running
            if self.is_mt5_running(user_id):
                return {'status': 'already_running', 'message': 'MT5 already active for user'}
            
            # Start MT5 process
            mt5_exe = Path(clone_path) / 'terminal64.exe'
            config_path = Path(clone_path) / 'Config'
            
            # Start MT5 with user-specific configuration
            process = subprocess.Popen([
                str(mt5_exe),
                f'/config:{config_path}',
                f'/profile:user_{user_id}'
            ], cwd=clone_path)
            
            # Update database with process ID
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE user_clones 
                    SET status = 'running', process_id = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (process.pid, user_id))
            
            self.log_action(user_id, "start_mt5", "success", f"MT5 started with PID {process.pid}")
            
            return {
                'status': 'success',
                'user_id': user_id,
                'process_id': process.pid,
                'message': 'MT5 instance started successfully'
            }
            
        except Exception as e:
            self.log_action(user_id, "start_mt5", "error", str(e))
            raise
    
    def allocate_port(self, user_id):
        """Allocate unique port for user"""
        # Simple hash-based allocation to ensure consistency
        base_port = self.port_start + (abs(hash(user_id)) % (self.port_end - self.port_start))
        
        # Check if port is available in database
        with sqlite3.connect(self.db_path) as conn:
            for port_offset in range(100):  # Try up to 100 ports
                candidate_port = base_port + port_offset
                cursor = conn.execute("SELECT COUNT(*) FROM user_clones WHERE port = ?", (candidate_port,))
                if cursor.fetchone()[0] == 0:
                    return candidate_port
        
        return None
    
    def get_clone_status(self, user_id):
        """Get current status of user's clone"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT clone_path, port, status, broker_type, created_at, last_active, process_id
                    FROM user_clones WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                if not result:
                    return {'exists': False, 'user_id': user_id}
                
                clone_path, port, status, broker_type, created_at, last_active, process_id = result
                
                # Check if MT5 process is actually running
                is_running = self.is_process_running(process_id) if process_id else False
                
                return {
                    'exists': True,
                    'user_id': user_id,
                    'clone_path': clone_path,
                    'port': port,
                    'status': status,
                    'broker_type': broker_type,
                    'created_at': created_at,
                    'last_active': last_active,
                    'process_id': process_id,
                    'is_running': is_running,
                    'bridge_path': f"{clone_path}/bridge"
                }
        except Exception as e:
            return {'exists': False, 'error': str(e)}
    
    def is_process_running(self, pid):
        """Check if process is running by PID"""
        if not pid:
            return False
        try:
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                  capture_output=True, text=True, check=False)
            return str(pid) in result.stdout
        except:
            return False
    
    def is_mt5_running(self, user_id):
        """Check if MT5 is running for user"""
        status = self.get_clone_status(user_id)
        return status.get('is_running', False)
    
    def list_all_clones(self):
        """List all user clones"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, clone_path, port, status, broker_type, created_at, process_id
                    FROM user_clones ORDER BY created_at DESC
                """)
                results = cursor.fetchall()
                
                clones = []
                for row in results:
                    user_id, clone_path, port, status, broker_type, created_at, process_id = row
                    clones.append({
                        'user_id': user_id,
                        'clone_path': clone_path,
                        'port': port,
                        'status': status,
                        'broker_type': broker_type,
                        'created_at': created_at,
                        'process_id': process_id,
                        'is_running': self.is_process_running(process_id)
                    })
                
                return {'total_clones': len(clones), 'clones': clones}
        except Exception as e:
            return {'error': str(e)}
    
    def log_action(self, user_id, action, status, details=""):
        """Log action to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO clone_logs (user_id, action, status, details)
                    VALUES (?, ?, ?, ?)
                """, (user_id, action, status, details))
        except Exception as e:
            print(f"Logging failed: {e}")

def run_clone_manager(host='0.0.0.0', port=5559):
    """Run the BITTEN Clone Manager"""
    manager = BittenCloneManager()
    print(f"BITTEN Clone Manager starting on {host}:{port}")
    print("Available endpoints:")
    print("  GET  /health - Service health check")
    print("  POST /clone/create - Create new user clone")
    print("  GET  /clone/status/<user_id> - Get clone status")
    print("  POST /clone/start/<user_id> - Start MT5 for user")
    print("  POST /clone/stop/<user_id> - Stop MT5 for user")
    print("  DELETE /clone/destroy/<user_id> - Remove user clone")
    print("  GET  /clones/list - List all clones")
    
    try:
        manager.app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print("Shutting down Clone Manager...")

if __name__ == "__main__":
    run_clone_manager()