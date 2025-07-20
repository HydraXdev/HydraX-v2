#!/usr/bin/env python3
"""
RDT Command Agent - Local Task File Monitor
Monitors for tasks.txt file and executes commands locally
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

class RDTCommandAgent:
    def __init__(self):
        self.setup_logging()
        self.tasks_file = "tasks.txt"
        self.lock_file = "rdt_agent.lock"
        self.running = True
        
    def setup_logging(self):
        """Setup logging to rdt_agent.log"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [RDT] %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rdt_agent.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_lock_file(self):
        """Check if another instance is running"""
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is still running on Windows
                try:
                    import psutil
                    if psutil.pid_exists(pid):
                        self.logger.error(f"Another instance is running (PID: {pid})")
                        return False
                except ImportError:
                    # Fallback method without psutil
                    try:
                        os.kill(pid, 0)  # Check if PID exists
                        self.logger.error(f"Another instance is running (PID: {pid})")
                        return False
                    except OSError:
                        pass  # Process doesn't exist, continue
                        
                # Remove stale lock file
                os.remove(self.lock_file)
                self.logger.info("Removed stale lock file")
                
            except Exception as e:
                self.logger.warning(f"Error checking lock file: {e}")
                
        # Create new lock file
        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"Created lock file with PID: {os.getpid()}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create lock file: {e}")
            return False
    
    def cleanup_lock_file(self):
        """Remove lock file on shutdown"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                self.logger.info("Removed lock file")
        except Exception as e:
            self.logger.warning(f"Error removing lock file: {e}")
    
    def execute_command(self, command_line):
        """Execute a command and return result"""
        try:
            self.logger.info(f"Executing: {command_line}")
            
            # Use shell=True for Windows compatibility
            process = subprocess.Popen(
                command_line,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
                
                result = {
                    'success': process.returncode == 0,
                    'returncode': process.returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                    'command': command_line
                }
                
                if result['success']:
                    self.logger.info(f"✅ Command succeeded: {command_line}")
                    if stdout:
                        self.logger.info(f"Output: {stdout.strip()}")
                else:
                    self.logger.error(f"❌ Command failed: {command_line}")
                    self.logger.error(f"Exit code: {process.returncode}")
                    if stderr:
                        self.logger.error(f"Error: {stderr.strip()}")
                
                return result
                
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.error(f"⏰ Command timed out: {command_line}")
                return {
                    'success': False,
                    'returncode': -1,
                    'stdout': '',
                    'stderr': 'Command timed out after 5 minutes',
                    'command': command_line
                }
                
        except Exception as e:
            self.logger.error(f"💥 Exception executing command: {command_line} - {e}")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'command': command_line
            }
    
    def process_tasks_file(self):
        """Process tasks from tasks.txt file"""
        if not os.path.exists(self.tasks_file):
            return
            
        self.logger.info(f"📋 Found {self.tasks_file}, processing tasks...")
        
        try:
            with open(self.tasks_file, 'r') as f:
                tasks = f.readlines()
            
            if not tasks:
                self.logger.info("No tasks found in file")
                os.remove(self.tasks_file)
                return
                
            self.logger.info(f"Processing {len(tasks)} tasks")
            
            for i, task in enumerate(tasks, 1):
                task = task.strip()
                if not task or task.startswith('#'):
                    continue
                    
                self.logger.info(f"📝 Task {i}: {task}")
                
                # Execute the command
                result = self.execute_command(task)
                
                # Log result summary
                if result['success']:
                    self.logger.info(f"✅ Task {i} completed successfully")
                else:
                    self.logger.error(f"❌ Task {i} failed")
                    
                # Small delay between tasks
                time.sleep(1)
            
            # Remove tasks file after processing
            os.remove(self.tasks_file)
            self.logger.info(f"🗑️ Removed {self.tasks_file} after processing")
            
        except Exception as e:
            self.logger.error(f"❌ Error processing tasks file: {e}")
            try:
                os.remove(self.tasks_file)
            except:
                pass
    
    def run(self):
        """Main monitoring loop"""
        if not self.check_lock_file():
            return
            
        self.logger.info("🚀 RDT Command Agent started")
        self.logger.info(f"👁️ Monitoring for {self.tasks_file} every 60 seconds")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while self.running:
                try:
                    # Check for tasks file
                    self.process_tasks_file()
                    
                    # Wait 60 seconds before next check
                    time.sleep(60)
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 Shutdown requested")
                    self.running = False
                    break
                    
                except Exception as e:
                    self.logger.error(f"❌ Error in main loop: {e}")
                    time.sleep(60)  # Continue after error
                    
        except Exception as e:
            self.logger.error(f"💥 Fatal error: {e}")
            
        finally:
            self.cleanup_lock_file()
            self.logger.info("✅ RDT Command Agent stopped")

def main():
    """Main entry point"""
    print("🎯 RDT Command Agent - Local Task Monitor")
    print("=" * 50)
    print("Monitors for tasks.txt file and executes commands locally")
    print("Supports Python scripts and shell commands")
    print("Logs all activity to rdt_agent.log")
    print("=" * 50)
    
    agent = RDTCommandAgent()
    agent.run()

if __name__ == "__main__":
    main()