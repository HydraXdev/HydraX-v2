#!/usr/bin/env python3
"""
BITTEN Press Pass Account Rotation System
Manages dynamic demo account assignment, MT5 terminal launching, and automated recycling
"""

import json
import os
import time
import subprocess
import threading
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PressPassRotation')

class PressPassRotationSystem:
    """
    Handles Press Pass demo account rotation, assignment, and lifecycle management
    """
    
    def __init__(self):
        self.vault_file = "/root/HydraX-v2/config/presspass_account_vault.json"
        self.config_file = "/root/HydraX-v2/mt5_dynamic_config.env"
        self.bridge_processes = {}  # Track active bridge processes by user_id
        self.terminal_processes = {}  # Track active terminal processes by user_id
        
        # Ensure vault file exists
        if not os.path.exists(self.vault_file):
            raise FileNotFoundError(f"Press Pass vault file not found: {self.vault_file}")
    
    def load_vault(self) -> List[Dict[str, Any]]:
        """Load the Press Pass account vault"""
        try:
            with open(self.vault_file, 'r') as f:
                vault = json.load(f)
            logger.info(f"Loaded vault with {len(vault)} accounts")
            return vault
        except Exception as e:
            logger.error(f"Error loading vault: {e}")
            return []
    
    def save_vault(self, vault: List[Dict[str, Any]]) -> bool:
        """Save the updated vault"""
        try:
            with open(self.vault_file, 'w') as f:
                json.dump(vault, f, indent=2)
            logger.info("Vault saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving vault: {e}")
            return False
    
    def assign_press_pass_account(self, user_id: str) -> Dict[str, Any]:
        """
        Assign a fresh demo account to a Press Pass user
        Returns account details or error
        """
        try:
            vault = self.load_vault()
            
            # Check if user already has an active assignment
            for account in vault:
                if account.get("assigned_to") == user_id and account.get("status") == "assigned":
                    # Check if still valid
                    if account.get("expires_at"):
                        expires_at = datetime.fromisoformat(account["expires_at"])
                        if datetime.now() < expires_at:
                            logger.info(f"User {user_id} already has active Press Pass account: {account['login']}")
                            return {
                                "success": True,
                                "account": account,
                                "message": "You already have an active Press Pass account",
                                "days_remaining": (expires_at - datetime.now()).days
                            }
            
            # Find first available account
            available_account = None
            for account in vault:
                if account.get("status") == "available":
                    available_account = account
                    break
            
            if not available_account:
                logger.warning("No available Press Pass accounts")
                return {
                    "success": False,
                    "message": "No Press Pass accounts available. Please try again later.",
                    "error": "vault_full"
                }
            
            # Assign the account
            now = datetime.now()
            expires_at = now + timedelta(days=7)
            
            available_account.update({
                "assigned_to": user_id,
                "assigned_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "status": "assigned"
            })
            
            # Save updated vault
            if not self.save_vault(vault):
                return {
                    "success": False,
                    "message": "Failed to save account assignment",
                    "error": "save_failed"
                }
            
            # Inject credentials into environment
            self.inject_credentials(available_account)
            
            logger.info(f"Assigned Press Pass account {available_account['login']} to user {user_id}")
            
            return {
                "success": True,
                "account": available_account,
                "message": f"Press Pass activated! Account {available_account['login']} assigned for 7 days.",
                "expires_at": expires_at.isoformat(),
                "broker": available_account["broker"],
                "server": available_account["server"]
            }
            
        except Exception as e:
            logger.error(f"Error assigning Press Pass account: {e}")
            return {
                "success": False,
                "message": "System error during account assignment",
                "error": str(e)
            }
    
    def inject_credentials(self, account: Dict[str, Any]) -> bool:
        """
        Inject account credentials into MT5 environment configuration
        """
        try:
            # Update environment variables
            os.environ['MT5_LOGIN'] = str(account['login'])
            os.environ['MT5_PASSWORD'] = account['password']
            os.environ['MT5_SERVER'] = account['server']
            
            # Update dynamic config file
            config_lines = [
                "#!/bin/bash",
                "# MT5 Dynamic Press Pass Configuration - Auto-generated",
                f"# Account assigned at: {account.get('assigned_at', 'Unknown')}",
                f"# Expires at: {account.get('expires_at', 'Unknown')}",
                "",
                "# Press Pass Account Configuration",
                f'export MT5_LOGIN="{account["login"]}"',
                f'export MT5_PASSWORD="{account["password"]}"',
                f'export MT5_SERVER="{account["server"]}"',
                f'export MT5_BROKER="{account["broker"]}"',
                'export MT5_PATH="/opt/mt5/terminal64.exe"',
                "",
                "# Press Pass Status",
                f'export PRESS_PASS_ACTIVE="true"',
                f'export PRESS_PASS_USER="{account.get("assigned_to", "unknown")}"',
                f'export PRESS_PASS_EXPIRES="{account.get("expires_at", "unknown")}"',
                "",
                'echo "[PRESS_PASS] 🎫 Press Pass Configuration Loaded"',
                'echo "[PRESS_PASS] 📊 Server: $MT5_SERVER"',
                'echo "[PRESS_PASS] 👤 Account: $MT5_LOGIN"',
                'echo "[PRESS_PASS] 🕰️ Expires: $PRESS_PASS_EXPIRES"',
                ""
            ]
            
            with open(self.config_file, 'w') as f:
                f.write("\\n".join(config_lines))
            
            logger.info(f"Credentials injected for account {account['login']}")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting credentials: {e}")
            return False
    
    def launch_mt5_terminal_and_bridge(self, user_id: str, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Launch MT5 terminal and bridge for the assigned account
        """
        try:
            # Kill any existing processes for this user
            self.terminate_user_processes(user_id)
            
            # Source the environment configuration
            source_cmd = f"source {self.config_file}"
            
            # Launch bridge process
            bridge_cmd = [
                "bash", "-c",
                f"{source_cmd} && python3 /root/HydraX-v2/bulletproof_agents/primary_agent_mt5_enhanced.py"
            ]
            
            logger.info(f"Launching bridge for user {user_id} with account {account['login']}")
            
            # Start bridge process
            bridge_process = subprocess.Popen(
                bridge_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy(),
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Store process reference
            self.bridge_processes[user_id] = {
                "process": bridge_process,
                "account": account,
                "started_at": datetime.now().isoformat(),
                "type": "bridge"
            }
            
            # Give process time to start
            time.sleep(3)
            
            # Check if process is still running
            if bridge_process.poll() is None:
                logger.info(f"Bridge launched successfully for user {user_id}")
                return {
                    "success": True,
                    "message": f"MT5 bridge launched for account {account['login']}",
                    "bridge_pid": bridge_process.pid,
                    "account": account
                }
            else:
                logger.error(f"Bridge failed to start for user {user_id}")
                return {
                    "success": False,
                    "message": "Failed to launch MT5 bridge",
                    "error": "bridge_start_failed"
                }
                
        except Exception as e:
            logger.error(f"Error launching MT5 terminal/bridge: {e}")
            return {
                "success": False,
                "message": "Failed to launch MT5 services",
                "error": str(e)
            }
    
    def terminate_user_processes(self, user_id: str) -> bool:
        """
        Terminate all MT5 processes for a specific user
        """
        try:
            # Terminate bridge process
            if user_id in self.bridge_processes:
                process_info = self.bridge_processes[user_id]
                process = process_info["process"]
                
                try:
                    # Terminate the process group
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    logger.info(f"Terminated bridge process for user {user_id}")
                except:
                    # Force kill if needed
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        logger.info(f"Force killed bridge process for user {user_id}")
                    except:
                        pass
                
                del self.bridge_processes[user_id]
            
            # Terminate terminal process
            if user_id in self.terminal_processes:
                process_info = self.terminal_processes[user_id]
                process = process_info["process"]
                
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    logger.info(f"Terminated terminal process for user {user_id}")
                except:
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        logger.info(f"Force killed terminal process for user {user_id}")
                    except:
                        pass
                
                del self.terminal_processes[user_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Error terminating processes for user {user_id}: {e}")
            return False
    
    def check_and_expire_accounts(self) -> Dict[str, Any]:
        """
        Check for expired Press Pass accounts and recycle them
        Daily maintenance task
        """
        try:
            vault = self.load_vault()
            now = datetime.now()
            expired_count = 0
            recycled_accounts = []
            
            for account in vault:
                if account.get("status") == "assigned" and account.get("expires_at"):
                    expires_at = datetime.fromisoformat(account["expires_at"])
                    
                    if now >= expires_at:
                        # Account has expired
                        user_id = account.get("assigned_to")
                        
                        # Terminate user processes
                        if user_id:
                            self.terminate_user_processes(user_id)
                        
                        # Reset account to available
                        account.update({
                            "assigned_to": None,
                            "assigned_at": None,
                            "expires_at": None,
                            "status": "available"
                        })
                        
                        expired_count += 1
                        recycled_accounts.append({
                            "login": account["login"],
                            "user_id": user_id,
                            "expired_at": expires_at.isoformat()
                        })
                        
                        logger.info(f"Recycled expired Press Pass account {account['login']} from user {user_id}")
            
            # Save updated vault
            if expired_count > 0:
                self.save_vault(vault)
            
            # Get current statistics
            available_count = sum(1 for acc in vault if acc.get("status") == "available")
            assigned_count = sum(1 for acc in vault if acc.get("status") == "assigned")
            
            logger.info(f"Expiry check complete: {expired_count} expired, {available_count} available, {assigned_count} assigned")
            
            return {
                "success": True,
                "expired_count": expired_count,
                "available_count": available_count,
                "assigned_count": assigned_count,
                "recycled_accounts": recycled_accounts,
                "total_accounts": len(vault)
            }
            
        except Exception as e:
            logger.error(f"Error during expiry check: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_press_pass_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get Press Pass status for a specific user
        """
        try:
            vault = self.load_vault()
            
            # Find user's account
            user_account = None
            for account in vault:
                if account.get("assigned_to") == user_id and account.get("status") == "assigned":
                    user_account = account
                    break
            
            if not user_account:
                return {
                    "success": True,
                    "has_press_pass": False,
                    "message": "No active Press Pass found"
                }
            
            # Calculate time remaining
            expires_at = datetime.fromisoformat(user_account["expires_at"])
            now = datetime.now()
            time_remaining = expires_at - now
            
            if time_remaining.total_seconds() <= 0:
                return {
                    "success": True,
                    "has_press_pass": False,
                    "message": "Press Pass has expired",
                    "expired": True
                }
            
            # Check if bridge is running
            bridge_running = user_id in self.bridge_processes
            
            return {
                "success": True,
                "has_press_pass": True,
                "account": user_account,
                "expires_at": user_account["expires_at"],
                "days_remaining": time_remaining.days,
                "hours_remaining": time_remaining.seconds // 3600,
                "bridge_running": bridge_running,
                "broker": user_account["broker"],
                "server": user_account["server"]
            }
            
        except Exception as e:
            logger.error(f"Error getting Press Pass status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def revoke_press_pass(self, user_id: str) -> Dict[str, Any]:
        """
        Manually revoke a user's Press Pass (admin function)
        """
        try:
            vault = self.load_vault()
            
            # Find and revoke user's account
            revoked = False
            for account in vault:
                if account.get("assigned_to") == user_id and account.get("status") == "assigned":
                    # Terminate processes
                    self.terminate_user_processes(user_id)
                    
                    # Reset account
                    account.update({
                        "assigned_to": None,
                        "assigned_at": None,
                        "expires_at": None,
                        "status": "available"
                    })
                    
                    revoked = True
                    logger.info(f"Manually revoked Press Pass account {account['login']} from user {user_id}")
                    break
            
            if revoked:
                self.save_vault(vault)
                return {
                    "success": True,
                    "message": "Press Pass revoked successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "No active Press Pass found for user"
                }
                
        except Exception as e:
            logger.error(f"Error revoking Press Pass: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def start_daily_expiry_monitor():
    """
    Start the daily expiry monitoring service
    """
    def daily_monitor():
        rotation_system = PressPassRotationSystem()
        
        while True:
            try:
                # Run expiry check every hour
                result = rotation_system.check_and_expire_accounts()
                if result["success"] and result["expired_count"] > 0:
                    logger.info(f"Daily monitor: Recycled {result['expired_count']} expired accounts")
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Daily monitor error: {e}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    # Start monitor in background thread
    monitor_thread = threading.Thread(target=daily_monitor, daemon=True)
    monitor_thread.start()
    logger.info("Daily Press Pass expiry monitor started")

if __name__ == "__main__":
    # Test the system
    rotation_system = PressPassRotationSystem()
    
    # Test assignment
    test_user = "test_user_123"
    result = rotation_system.assign_press_pass_account(test_user)
    print(f"Assignment result: {result}")
    
    if result["success"]:
        # Test bridge launch
        launch_result = rotation_system.launch_mt5_terminal_and_bridge(test_user, result["account"])
        print(f"Launch result: {launch_result}")
        
        # Test status check
        status_result = rotation_system.get_press_pass_status(test_user)
        print(f"Status result: {status_result}")
        
        # Clean up test
        rotation_system.revoke_press_pass(test_user)