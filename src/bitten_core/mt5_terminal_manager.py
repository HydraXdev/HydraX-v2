#!/usr/bin/env python3
"""
MT5 Terminal Manager for Press Pass Accounts
Handles MT5 terminal launching, bridge management, and process lifecycle
"""

import os
import time
import json
import signal
import shutil
import psutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger('MT5TerminalManager')

class MT5TerminalManager:
    """
    Manages MT5 terminal instances and bridge processes for Press Pass users
    """
    
    def __init__(self):
        self.base_terminal_path = "/opt/mt5/base_terminal"  # Pre-configured MT5 template
        self.user_terminals_path = "/opt/mt5/user_terminals"  # User-specific terminals
        self.bridge_script = "/root/HydraX-v2/bulletproof_agents/primary_agent_mt5_enhanced.py"
        self.processes_file = "/root/HydraX-v2/data/presspass_processes.json"
        
        # Ensure directories exist
        os.makedirs(self.user_terminals_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.processes_file), exist_ok=True)
    
    def setup_user_terminal(self, user_id: str, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setup a dedicated MT5 terminal instance for a Press Pass user
        """
        try:
            user_terminal_path = f"{self.user_terminals_path}/user_{user_id}"
            
            # Remove existing terminal if it exists
            if os.path.exists(user_terminal_path):
                shutil.rmtree(user_terminal_path)
            
            # Copy base terminal to user directory
            if os.path.exists(self.base_terminal_path):
                shutil.copytree(self.base_terminal_path, user_terminal_path)
                logger.info(f"Copied base terminal to {user_terminal_path}")
            else:
                # Create minimal terminal structure
                os.makedirs(user_terminal_path, exist_ok=True)
                os.makedirs(f"{user_terminal_path}/MQL5", exist_ok=True)
                os.makedirs(f"{user_terminal_path}/Profiles", exist_ok=True)
                logger.info(f"Created minimal terminal structure at {user_terminal_path}")
            
            # Create user-specific configuration
            config_content = f"""
; Press Pass MT5 Terminal Configuration
; User: {user_id}
; Account: {account['login']}
; Server: {account['server']}
; Created: {datetime.now().isoformat()}

[Common]
Login={account['login']}
Password={account['password']}
Server={account['server']}
AutoLogin=true

[Charts]
MaxBars=10000
TemplateDefault=\\Profiles\\\\Templates\\\\default.tpl

[Expert]
AllowLiveTrading=true
AllowDllImport=true
AllowImport=true
"""
            
            with open(f"{user_terminal_path}/config.ini", 'w') as f:
                f.write(config_content)
            
            return {
                "success": True,
                "terminal_path": user_terminal_path,
                "config_file": f"{user_terminal_path}/config.ini"
            }
            
        except Exception as e:
            logger.error(f"Error setting up user terminal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def launch_mt5_terminal(self, user_id: str, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Launch MT5 terminal for a Press Pass user
        """
        try:
            # Setup user terminal
            setup_result = self.setup_user_terminal(user_id, account)
            if not setup_result["success"]:
                return setup_result
            
            terminal_path = setup_result["terminal_path"]
            
            # MT5 terminal executable paths (try multiple locations)
            possible_terminal_paths = [
                "/opt/mt5/terminal64.exe",
                "/usr/local/bin/mt5/terminal64.exe",
                "/opt/MetaTrader5/terminal64.exe",
                f"{terminal_path}/terminal64.exe"
            ]
            
            terminal_exe = None
            for path in possible_terminal_paths:
                if os.path.exists(path):
                    terminal_exe = path
                    break
            
            if not terminal_exe:
                logger.warning("MT5 terminal executable not found, skipping terminal launch")
                return {
                    "success": True,  # Still success, bridge can work without terminal GUI
                    "terminal_launched": False,
                    "message": "MT5 terminal executable not found, bridge only mode"
                }
            
            # Launch MT5 terminal with account credentials
            terminal_cmd = [
                "wine",  # Assuming Wine is used for Windows MT5 on Linux
                terminal_exe,
                f"/config:{terminal_path}/config.ini",
                f"/login:{account['login']}",
                f"/password:{account['password']}",
                f"/server:{account['server']}"
            ]
            
            logger.info(f"Launching MT5 terminal for user {user_id}")
            
            # Start terminal process in background
            terminal_process = subprocess.Popen(
                terminal_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=terminal_path,
                preexec_fn=os.setsid
            )
            
            # Give terminal time to start
            time.sleep(5)
            
            # Check if process is running
            if terminal_process.poll() is None:
                logger.info(f"MT5 terminal launched successfully for user {user_id}")
                return {
                    "success": True,
                    "terminal_launched": True,
                    "terminal_pid": terminal_process.pid,
                    "terminal_path": terminal_path,
                    "process": terminal_process
                }
            else:
                logger.warning(f"MT5 terminal failed to start for user {user_id}")
                return {
                    "success": True,  # Still success, bridge can work without terminal
                    "terminal_launched": False,
                    "message": "Terminal failed to start, bridge only mode"
                }
                
        except Exception as e:
            logger.error(f"Error launching MT5 terminal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def launch_bridge_process(self, user_id: str, account: Dict[str, Any], port_offset: int = 0) -> Dict[str, Any]:
        """
        Launch bridge process for Press Pass user with dynamic port assignment
        """
        try:
            base_port = 9100  # Start Press Pass bridges at port 9100+
            bridge_port = base_port + port_offset
            
            # Set environment variables for this bridge instance
            bridge_env = os.environ.copy()
            bridge_env.update({
                'MT5_LOGIN': str(account['login']),
                'MT5_PASSWORD': account['password'],
                'MT5_SERVER': account['server'],
                'MT5_BROKER': account['broker'],
                'BRIDGE_PORT': str(bridge_port),
                'PRESS_PASS_USER': user_id,
                'PRESS_PASS_MODE': 'true'
            })
            
            # Create bridge launch script
            bridge_script_content = f"""#!/bin/bash
# Press Pass Bridge Launcher for User {user_id}
# Account: {account['login']} | Server: {account['server']}

export MT5_LOGIN="{account['login']}"
export MT5_PASSWORD="{account['password']}"
export MT5_SERVER="{account['server']}"
export MT5_BROKER="{account['broker']}"
export BRIDGE_PORT="{bridge_port}"
export PRESS_PASS_USER="{user_id}"
export PRESS_PASS_MODE="true"

echo "[PRESS_PASS] Starting bridge for user {user_id}"
echo "[PRESS_PASS] Account: {account['login']}"
echo "[PRESS_PASS] Server: {account['server']}"
echo "[PRESS_PASS] Port: {bridge_port}"

cd /root/HydraX-v2
python3 {self.bridge_script}
"""
            
            bridge_script_path = f"/tmp/bridge_user_{user_id}.sh"
            with open(bridge_script_path, 'w') as f:
                f.write(bridge_script_content)
            os.chmod(bridge_script_path, 0o755)
            
            # Launch bridge process
            logger.info(f"Launching bridge for user {user_id} on port {bridge_port}")
            
            bridge_process = subprocess.Popen(
                ["bash", bridge_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=bridge_env,
                preexec_fn=os.setsid
            )
            
            # Give bridge time to start
            time.sleep(3)
            
            # Check if process is running
            if bridge_process.poll() is None:
                logger.info(f"Bridge launched successfully for user {user_id} on port {bridge_port}")
                
                # Save process info
                self.save_process_info(user_id, {
                    "bridge_pid": bridge_process.pid,
                    "bridge_port": bridge_port,
                    "account": account,
                    "started_at": datetime.now().isoformat(),
                    "script_path": bridge_script_path
                })
                
                return {
                    "success": True,
                    "bridge_launched": True,
                    "bridge_pid": bridge_process.pid,
                    "bridge_port": bridge_port,
                    "account": account,
                    "process": bridge_process
                }
            else:
                logger.error(f"Bridge failed to start for user {user_id}")
                return {
                    "success": False,
                    "error": "Bridge process failed to start"
                }
                
        except Exception as e:
            logger.error(f"Error launching bridge process: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_process_info(self, user_id: str, process_info: Dict[str, Any]):
        """Save process information for tracking"""
        try:
            # Load existing processes
            processes = {}
            if os.path.exists(self.processes_file):
                with open(self.processes_file, 'r') as f:
                    processes = json.load(f)
            
            # Add/update user process info
            processes[user_id] = process_info
            
            # Save updated processes
            with open(self.processes_file, 'w') as f:
                json.dump(processes, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving process info: {e}")
    
    def load_process_info(self) -> Dict[str, Any]:
        """Load process information"""
        try:
            if os.path.exists(self.processes_file):
                with open(self.processes_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading process info: {e}")
            return {}
    
    def terminate_user_processes(self, user_id: str) -> bool:
        """
        Terminate all processes for a specific user
        """
        try:
            processes = self.load_process_info()
            
            if user_id in processes:
                process_info = processes[user_id]
                
                # Terminate bridge process
                if "bridge_pid" in process_info:
                    try:
                        self.kill_process_tree(process_info["bridge_pid"])
                        logger.info(f"Terminated bridge process {process_info['bridge_pid']} for user {user_id}")
                    except:
                        pass
                
                # Clean up script file
                if "script_path" in process_info:
                    try:
                        os.remove(process_info["script_path"])
                    except:
                        pass
                
                # Remove from processes file
                del processes[user_id]
                with open(self.processes_file, 'w') as f:
                    json.dump(processes, f, indent=2)
            
            # Clean up user terminal directory
            user_terminal_path = f"{self.user_terminals_path}/user_{user_id}"
            if os.path.exists(user_terminal_path):
                try:
                    shutil.rmtree(user_terminal_path)
                    logger.info(f"Cleaned up terminal directory for user {user_id}")
                except:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error terminating processes for user {user_id}: {e}")
            return False
    
    def kill_process_tree(self, pid: int):
        """Kill a process and all its children"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except:
                    pass
            
            # Wait for children to terminate
            _, alive = psutil.wait_procs(children, timeout=3)
            
            # Force kill remaining children
            for child in alive:
                try:
                    child.kill()
                except:
                    pass
            
            # Terminate parent
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except:
                try:
                    parent.kill()
                except:
                    pass
                    
        except psutil.NoSuchProcess:
            pass  # Process already dead
        except Exception as e:
            logger.error(f"Error killing process tree {pid}: {e}")
    
    def get_user_processes_status(self, user_id: str) -> Dict[str, Any]:
        """Get status of user's processes"""
        try:
            processes = self.load_process_info()
            
            if user_id not in processes:
                return {
                    "has_processes": False,
                    "message": "No active processes found"
                }
            
            process_info = processes[user_id]
            
            # Check if bridge is still running
            bridge_running = False
            if "bridge_pid" in process_info:
                try:
                    bridge_running = psutil.pid_exists(process_info["bridge_pid"])
                except:
                    pass
            
            return {
                "has_processes": True,
                "bridge_running": bridge_running,
                "bridge_port": process_info.get("bridge_port"),
                "account": process_info.get("account"),
                "started_at": process_info.get("started_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting process status: {e}")
            return {
                "has_processes": False,
                "error": str(e)
            }
    
    def cleanup_orphaned_processes(self) -> Dict[str, Any]:
        """Clean up orphaned processes that are no longer tracked"""
        try:
            processes = self.load_process_info()
            cleaned_count = 0
            
            for user_id, process_info in list(processes.items()):
                # Check if bridge process is still running
                bridge_running = False
                if "bridge_pid" in process_info:
                    try:
                        bridge_running = psutil.pid_exists(process_info["bridge_pid"])
                    except:
                        pass
                
                if not bridge_running:
                    # Process is dead, clean up
                    self.terminate_user_processes(user_id)
                    cleaned_count += 1
                    logger.info(f"Cleaned up orphaned processes for user {user_id}")
            
            return {
                "success": True,
                "cleaned_count": cleaned_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning orphaned processes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    # Test the terminal manager
    manager = MT5TerminalManager()
    
    test_account = {
        "login": "843859",
        "password": "Ao4@brz64erHaG",
        "server": "Coinexx-Demo",
        "broker": "Coinexx"
    }
    
    test_user = "test_terminal_user"
    
    # Test bridge launch
    result = manager.launch_bridge_process(test_user, test_account, 0)
    print(f"Bridge launch result: {result}")
    
    if result["success"]:
        time.sleep(5)
        
        # Test status check
        status = manager.get_user_processes_status(test_user)
        print(f"Process status: {status}")
        
        # Clean up
        manager.terminate_user_processes(test_user)