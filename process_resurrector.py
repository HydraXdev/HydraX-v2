#!/usr/bin/env python3
"""
PROCESS RESURRECTOR - The Undying Guardian
Automatically restarts crashed MT5 instances and maintains system health
"""

import json
import os
import time
import subprocess
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
import psutil

class ProcessResurrector:
    def __init__(self):
        self.is_active = True
        self.db_path = "C:/MT5_Farm/resurrector.db"
        self.setup_database()
        
        # Resurrection settings
        self.check_interval = 15  # Check every 15 seconds
        self.max_restart_attempts = 3
        self.restart_cooldown = 300  # 5 minutes between restart attempts
        
        # Process tracking
        self.tracked_processes = {}
        self.restart_history = {}
        
        print("⚰️ Process Resurrector initialized - The dead shall rise again!")
        
    def setup_database(self):
        """Initialize resurrection tracking database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS process_tracking (
                    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    process_name TEXT NOT NULL,
                    pid INTEGER,
                    status TEXT NOT NULL,
                    last_seen TIMESTAMP,
                    restart_count INTEGER DEFAULT 0,
                    last_restart TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS resurrection_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_pid INTEGER,
                    new_pid INTEGER,
                    success BOOLEAN,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def start_resurrection_service(self):
        """Start the resurrection monitoring service"""
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        cleanup_thread = threading.Thread(target=self.cleanup_zombies, daemon=True)
        
        monitor_thread.start()
        cleanup_thread.start()
        
        print("👹 Resurrection service started - Death is temporary!")
    
    def monitor_processes(self):
        """Monitor all tracked processes and resurrect the dead"""
        while self.is_active:
            try:
                self.discover_user_mt5_processes()
                self.check_process_health()
                self.resurrect_dead_processes()
                
            except Exception as e:
                print(f"Monitor error: {e}")
            
            time.sleep(self.check_interval)
    
    def discover_user_mt5_processes(self):
        """Discover all user MT5 processes that should be tracked"""
        users_path = Path("C:/MT5_Farm/Users")
        
        if not users_path.exists():
            return
        
        for user_dir in users_path.iterdir():
            if user_dir.is_dir() and user_dir.name.startswith("user_"):
                user_id = user_dir.name.replace("user_", "")
                mt5_exe = user_dir / "terminal64.exe"
                
                if mt5_exe.exists():
                    self.track_user_process(user_id, str(mt5_exe))
    
    def track_user_process(self, user_id, exe_path):
        """Add or update process tracking for a user"""
        if user_id not in self.tracked_processes:
            self.tracked_processes[user_id] = {
                'exe_path': exe_path,
                'expected_running': True,
                'last_pid': None,
                'last_seen': None
            }
    
    def check_process_health(self):
        """Check health of all tracked processes"""
        # Get all running MT5 processes
        running_mt5_pids = []
        
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe', '/FO', 'CSV'], 
                                  capture_output=True, text=True, check=False)
            
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if 'terminal64.exe' in line:
                    try:
                        # Parse CSV-like output to get PID
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = int(parts[1].strip('"'))
                            running_mt5_pids.append(pid)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Failed to get process list: {e}")
            return
        
        # Update tracking status
        current_time = datetime.now()
        
        for user_id, process_info in self.tracked_processes.items():
            # Check if this user's process is in the running list
            user_process_running = False
            
            # Simple check - if we have any MT5 running and user dir exists, assume it's running
            # More sophisticated tracking would require PID management
            user_path = Path(f"C:/MT5_Farm/Users/user_{user_id}")
            bridge_status = user_path / "bridge" / "status.json"
            
            if bridge_status.exists():
                try:
                    with open(bridge_status, 'r') as f:
                        status_data = json.load(f)
                        # Check if status is recent (within last 60 seconds)
                        status_time = datetime.fromisoformat(status_data.get('timestamp', '2000-01-01'))
                        if (current_time - status_time).total_seconds() < 60:
                            user_process_running = True
                except:
                    pass
            
            # Update tracking
            if user_process_running:
                process_info['last_seen'] = current_time
                self.update_process_tracking(user_id, 'alive', None)
            else:
                # Process might be dead
                if process_info.get('last_seen'):
                    time_since_seen = (current_time - process_info['last_seen']).total_seconds()
                    if time_since_seen > 30:  # Consider dead after 30 seconds
                        self.mark_process_dead(user_id)
    
    def mark_process_dead(self, user_id):
        """Mark a process as dead and schedule resurrection"""
        print(f"💀 Process DEATH detected for user {user_id}")
        
        self.update_process_tracking(user_id, 'dead', None)
        
        # Add to resurrection queue
        if user_id not in self.restart_history:
            self.restart_history[user_id] = {
                'attempts': 0,
                'last_attempt': None,
                'total_restarts': 0
            }
    
    def resurrect_dead_processes(self):
        """Resurrect dead processes"""
        current_time = datetime.now()
        
        for user_id, restart_info in self.restart_history.items():
            if user_id not in self.tracked_processes:
                continue
                
            process_info = self.tracked_processes[user_id]
            
            # Skip if process is alive
            if process_info.get('last_seen') and (current_time - process_info['last_seen']).total_seconds() < 60:
                continue
            
            # Check if we can attempt resurrection
            if restart_info['attempts'] >= self.max_restart_attempts:
                continue  # Too many attempts
            
            # Check cooldown
            if restart_info['last_attempt']:
                time_since_attempt = (current_time - restart_info['last_attempt']).total_seconds()
                if time_since_attempt < self.restart_cooldown:
                    continue  # Still in cooldown
            
            # RESURRECT THE PROCESS!
            self.resurrect_process(user_id)
    
    def resurrect_process(self, user_id):
        """Resurrect a specific user's MT5 process"""
        try:
            print(f"⚡ RESURRECTING process for user {user_id}")
            
            user_path = Path(f"C:/MT5_Farm/Users/user_{user_id}")
            mt5_exe = user_path / "terminal64.exe"
            
            if not mt5_exe.exists():
                print(f"❌ Resurrection failed: MT5 executable not found for user {user_id}")
                return False
            
            # Start the process
            process = subprocess.Popen([
                str(mt5_exe)
            ], cwd=str(user_path))
            
            print(f"✅ Process RESURRECTED for user {user_id} with PID {process.pid}")
            
            # Update bridge status
            bridge_dir = user_path / "bridge"
            bridge_dir.mkdir(exist_ok=True)
            
            status = {
                'user_id': user_id,
                'status': 'resurrected',
                'timestamp': datetime.now().isoformat(),
                'process_id': process.pid,
                'resurrected_by': 'process_resurrector'
            }
            
            with open(bridge_dir / "status.json", 'w') as f:
                json.dump(status, f, indent=2)
            
            # Update tracking
            restart_info = self.restart_history[user_id]
            restart_info['attempts'] += 1
            restart_info['last_attempt'] = datetime.now()
            restart_info['total_restarts'] += 1
            
            self.log_resurrection(user_id, None, process.pid, True, "Process successfully resurrected")
            self.update_process_tracking(user_id, 'resurrected', process.pid)
            
            return True
            
        except Exception as e:
            error_msg = f"Resurrection failed: {e}"
            print(f"❌ {error_msg}")
            
            self.log_resurrection(user_id, None, None, False, error_msg)
            return False
    
    def cleanup_zombies(self):
        """Clean up zombie processes and reset counters"""
        while self.is_active:
            try:
                current_time = datetime.now()
                
                # Reset restart attempts after 24 hours
                for user_id, restart_info in self.restart_history.items():
                    if restart_info['last_attempt']:
                        hours_since = (current_time - restart_info['last_attempt']).total_seconds() / 3600
                        if hours_since > 24:
                            restart_info['attempts'] = 0
                            print(f"🔄 Reset restart counter for user {user_id}")
                
                # Clean old resurrection logs
                with sqlite3.connect(self.db_path) as conn:
                    week_ago = current_time - timedelta(days=7)
                    conn.execute("DELETE FROM resurrection_log WHERE timestamp < ?", (week_ago,))
                
            except Exception as e:
                print(f"Cleanup error: {e}")
            
            time.sleep(3600)  # Run every hour
    
    def force_resurrect_user(self, user_id):
        """Force resurrect a specific user (bypass cooldowns)"""
        print(f"🔥 FORCE RESURRECTION requested for user {user_id}")
        
        # Reset restart history
        self.restart_history[user_id] = {
            'attempts': 0,
            'last_attempt': None,
            'total_restarts': self.restart_history.get(user_id, {}).get('total_restarts', 0)
        }
        
        return self.resurrect_process(user_id)
    
    def update_process_tracking(self, user_id, status, pid):
        """Update process tracking in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO process_tracking 
                    (user_id, process_name, pid, status, last_seen)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, 'terminal64.exe', pid, status))
        except Exception as e:
            print(f"Database update failed: {e}")
    
    def log_resurrection(self, user_id, old_pid, new_pid, success, details):
        """Log resurrection event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO resurrection_log (user_id, action, old_pid, new_pid, success, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, 'resurrect', old_pid, new_pid, success, details))
        except Exception as e:
            print(f"Logging failed: {e}")
    
    def get_resurrection_stats(self):
        """Get resurrection statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_resurrections,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_resurrections,
                        COUNT(DISTINCT user_id) as unique_users_resurrected
                    FROM resurrection_log
                    WHERE timestamp > datetime('now', '-24 hours')
                """)
                stats = cursor.fetchone()
                
                return {
                    'total_resurrections_24h': stats[0],
                    'successful_resurrections_24h': stats[1],
                    'unique_users_resurrected_24h': stats[2],
                    'success_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
                }
        except Exception as e:
            return {'error': str(e)}

def run_resurrector_service():
    """Run the Process Resurrector as a service"""
    resurrector = ProcessResurrector()
    resurrector.start_resurrection_service()
    
    print("💀 Process Resurrector Service started")
    print("Death is not the end - all processes shall rise again!")
    
    try:
        while True:
            time.sleep(60)
            stats = resurrector.get_resurrection_stats()
            if stats.get('total_resurrections_24h', 0) > 0:
                print(f"📊 Resurrection Stats (24h): {stats['successful_resurrections_24h']}/{stats['total_resurrections_24h']} successful ({stats['success_rate']:.1f}%)")
    
    except KeyboardInterrupt:
        print("Stopping Process Resurrector...")
        resurrector.is_active = False

if __name__ == "__main__":
    run_resurrector_service()