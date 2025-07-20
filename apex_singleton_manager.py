#!/usr/bin/env python3
"""
APEX Singleton Process Manager
Ensures only ONE instance of APEX engine can run at a time
Provides robust failsafe against duplicate processes
"""

import os
import sys
import psutil
import signal
import time
import fcntl
import logging
from pathlib import Path
from typing import Optional, List

class APEXSingletonManager:
    def __init__(self, process_name: str = "apex_v5_live_real.py"):
        self.process_name = process_name
        self.pid_file = Path("/root/HydraX-v2/.apex_engine.pid")
        self.lock_file = Path("/root/HydraX-v2/.apex_engine.lock")
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for singleton manager"""
        logger = logging.getLogger("APEX_SINGLETON")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('/root/HydraX-v2/apex_singleton.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def acquire_lock(self) -> bool:
        """Acquire exclusive lock - only one process can hold this"""
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.lockf(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.logger.info(f"✅ Acquired exclusive lock for APEX engine")
            return True
        except IOError:
            self.logger.warning(f"❌ Could not acquire lock - another instance may be running")
            return False
    
    def release_lock(self):
        """Release the exclusive lock"""
        try:
            if hasattr(self, 'lock_fd'):
                fcntl.lockf(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                self.logger.info("🔓 Released exclusive lock")
        except:
            pass
    
    def find_apex_processes(self) -> List[psutil.Process]:
        """Find all running APEX processes"""
        apex_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any(self.process_name in str(arg) for arg in cmdline):
                    apex_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return apex_processes
    
    def kill_existing_processes(self, exclude_pid: Optional[int] = None) -> int:
        """Kill all APEX processes except the excluded PID"""
        killed_count = 0
        apex_processes = self.find_apex_processes()
        
        for proc in apex_processes:
            if exclude_pid and proc.pid == exclude_pid:
                continue
                
            try:
                self.logger.warning(f"🔫 Killing duplicate APEX process PID={proc.pid}")
                proc.terminate()
                time.sleep(0.5)
                
                if proc.is_running():
                    self.logger.warning(f"⚡ Force killing stubborn process PID={proc.pid}")
                    proc.kill()
                
                killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.error(f"Error killing process {proc.pid}: {e}")
        
        return killed_count
    
    def write_pid_file(self, pid: int):
        """Write current PID to file"""
        try:
            self.pid_file.write_text(str(pid))
            self.logger.info(f"📝 Wrote PID {pid} to {self.pid_file}")
        except Exception as e:
            self.logger.error(f"Error writing PID file: {e}")
    
    def read_pid_file(self) -> Optional[int]:
        """Read PID from file"""
        try:
            if self.pid_file.exists():
                return int(self.pid_file.read_text().strip())
        except:
            pass
        return None
    
    def is_process_running(self, pid: int) -> bool:
        """Check if a specific PID is running"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
    
    def ensure_singleton(self) -> bool:
        """Main method to ensure only one APEX instance runs"""
        current_pid = os.getpid()
        
        # Step 1: Try to acquire exclusive lock
        if not self.acquire_lock():
            self.logger.error("❌ Another APEX instance has the lock. Exiting.")
            return False
        
        # Step 2: Check for existing processes
        apex_processes = self.find_apex_processes()
        other_processes = [p for p in apex_processes if p.pid != current_pid]
        
        if other_processes:
            self.logger.warning(f"⚠️ Found {len(other_processes)} other APEX processes running!")
            
            # Kill all other processes
            killed = self.kill_existing_processes(exclude_pid=current_pid)
            self.logger.info(f"🎯 Killed {killed} duplicate APEX processes")
            
            # Wait a moment for processes to fully terminate
            time.sleep(1)
            
            # Verify they're gone
            remaining = self.find_apex_processes()
            other_remaining = [p for p in remaining if p.pid != current_pid]
            
            if other_remaining:
                self.logger.error(f"❌ Still {len(other_remaining)} APEX processes running!")
                self.release_lock()
                return False
        
        # Step 3: Check PID file
        stored_pid = self.read_pid_file()
        if stored_pid and stored_pid != current_pid:
            if self.is_process_running(stored_pid):
                self.logger.error(f"❌ PID file shows process {stored_pid} is running")
                self.release_lock()
                return False
            else:
                self.logger.info(f"🧹 Cleaning up stale PID file (old PID: {stored_pid})")
        
        # Step 4: Write our PID
        self.write_pid_file(current_pid)
        
        # Step 5: Set up cleanup on exit
        signal.signal(signal.SIGTERM, self._cleanup_handler)
        signal.signal(signal.SIGINT, self._cleanup_handler)
        
        self.logger.info(f"✅ APEX Singleton established - PID: {current_pid}")
        return True
    
    def _cleanup_handler(self, signum, frame):
        """Clean up on exit"""
        self.logger.info(f"🛑 Received signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up lock and PID file"""
        try:
            # Remove PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
                self.logger.info("🧹 Removed PID file")
            
            # Release lock
            self.release_lock()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def enforce_singleton():
    """Helper function to be called at the start of APEX engine"""
    manager = APEXSingletonManager()
    if not manager.ensure_singleton():
        print("❌ Failed to establish singleton - another APEX instance is running!")
        sys.exit(1)
    return manager


if __name__ == "__main__":
    # Test the singleton manager
    print("Testing APEX Singleton Manager...")
    
    manager = APEXSingletonManager()
    
    # Find existing processes
    processes = manager.find_apex_processes()
    print(f"\nFound {len(processes)} APEX processes:")
    for proc in processes:
        print(f"  - PID: {proc.pid}, CMD: {' '.join(proc.cmdline())[:80]}...")
    
    # Try to establish singleton
    if manager.ensure_singleton():
        print("\n✅ Successfully established singleton!")
        print("Press Ctrl+C to exit and test cleanup...")
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            pass
        finally:
            manager.cleanup()
    else:
        print("\n❌ Could not establish singleton!")