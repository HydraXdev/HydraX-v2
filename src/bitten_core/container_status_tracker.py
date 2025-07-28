#!/usr/bin/env python3
"""
Container Status Tracker - HydraX Infrastructure
Monitors and tracks the readiness status of user MT5 containers
"""

import json
import docker
import time
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass
import subprocess
import requests

logger = logging.getLogger(__name__)

@dataclass
class ContainerStatus:
    container_name: str
    status: str  # unassigned, credentials_injected, mt5_logged_in, ready_for_fire, error_state
    mt5_running: bool
    ea_active: bool
    account_balance: float
    broker_connected: bool
    last_check: str
    error_message: Optional[str] = None

class ContainerStatusTracker:
    """Track and monitor container readiness status"""
    
    def __init__(self):
        self.docker_client = None
        self.status_cache = {}
        self.last_update = None
        self._init_docker()
    
    def _init_docker(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    def check_container_status(self, container_name: str) -> ContainerStatus:
        """
        Comprehensive container status check
        Returns ContainerStatus object with all relevant information
        """
        try:
            # Initialize status object
            status = ContainerStatus(
                container_name=container_name,
                status="error_state",
                mt5_running=False,
                ea_active=False,
                account_balance=0.0,
                broker_connected=False,
                last_check=datetime.now(timezone.utc).isoformat(),
                error_message=None
            )
            
            if not self.docker_client:
                status.error_message = "Docker client not available"
                return status
            
            # Step 1: Check if container exists and is running
            try:
                container = self.docker_client.containers.get(container_name)
                if container.status != 'running':
                    status.error_message = f"Container not running (status: {container.status})"
                    status.status = "error_state"
                    return status
            except docker.errors.NotFound:
                status.error_message = "Container not found"
                status.status = "unassigned"
                return status
            
            # Step 2: Check if credentials are injected
            credentials_exist = self._check_credentials_injected(container)
            if not credentials_exist:
                status.status = "unassigned"
                return status
            
            status.status = "credentials_injected"
            
            # Step 3: Check if MT5 is running
            mt5_running = self._check_mt5_running(container)
            status.mt5_running = mt5_running
            
            if not mt5_running:
                return status
            
            # Step 4: Check if MT5 is logged in and get account info
            account_info = self._get_mt5_account_info(container)
            if account_info:
                status.status = "mt5_logged_in"
                status.broker_connected = True
                status.account_balance = account_info.get("balance", 0.0)
                
                # Step 5: Check if EA is running
                ea_active = self._check_ea_active(container)
                status.ea_active = ea_active
                
                if ea_active:
                    status.status = "ready_for_fire"
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking container {container_name}: {e}")
            return ContainerStatus(
                container_name=container_name,
                status="error_state",
                mt5_running=False,
                ea_active=False,
                account_balance=0.0,
                broker_connected=False,
                last_check=datetime.now(timezone.utc).isoformat(),
                error_message=str(e)
            )
    
    def _check_credentials_injected(self, container) -> bool:
        """Check if MT5 credentials are configured in container"""
        try:
            # Check if terminal.ini exists and has login info
            result = container.exec_run([
                'bash', '-c',
                'test -f /wine/drive_c/MetaTrader5/config/terminal.ini && grep -q "Login=" /wine/drive_c/MetaTrader5/config/terminal.ini'
            ])
            return result.exit_code == 0
        except Exception as e:
            logger.error(f"Error checking credentials: {e}")
            return False
    
    def _check_mt5_running(self, container) -> bool:
        """Check if MT5 terminal process is running"""
        try:
            result = container.exec_run(['pgrep', 'terminal64.exe'])
            return result.exit_code == 0
        except Exception as e:
            logger.error(f"Error checking MT5 process: {e}")
            return False
    
    def _get_mt5_account_info(self, container) -> Optional[Dict]:
        """Get MT5 account information"""
        try:
            # Use Python script to extract account info
            extraction_script = '''
import sys
sys.path.append("/opt/")
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        account_info = mt5.account_info()
        if account_info:
            import json
            result = {
                "login": account_info.login,
                "balance": account_info.balance,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "broker": account_info.company,
                "connected": True
            }
            print(json.dumps(result))
        else:
            print(\'{"connected": false, "error": "No account info"}\')
        mt5.shutdown()
    else:
        print(\'{"connected": false, "error": "MT5 initialization failed"}\')
except Exception as e:
    print(f\'{"connected": false, "error": "{str(e)}"}\')
'''
            
            result = container.exec_run(['python3', '-c', extraction_script])
            
            if result.exit_code == 0:
                try:
                    output = result.output.decode().strip()
                    account_data = json.loads(output)
                    if account_data.get("connected"):
                        return account_data
                except json.JSONDecodeError:
                    pass
            
            return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def _check_ea_active(self, container) -> bool:
        """Check if EA is active and ready for fire packets"""
        try:
            # Check if fire.txt file exists and EA can write to it
            result = container.exec_run([
                'bash', '-c',
                'test -f /wine/drive_c/MetaTrader5/Files/BITTEN/fire.txt && test -w /wine/drive_c/MetaTrader5/Files/BITTEN/fire.txt'
            ])
            
            if result.exit_code != 0:
                return False
            
            # Try to write a test message to check EA responsiveness
            test_signal = {
                "action": "test",
                "timestamp": int(time.time())
            }
            
            container.exec_run([
                'bash', '-c',
                f'echo \'{json.dumps(test_signal)}\' > /wine/drive_c/MetaTrader5/Files/BITTEN/fire.txt'
            ])
            
            # Wait a moment and check if file was processed
            time.sleep(1)
            
            result = container.exec_run([
                'bash', '-c',
                'cat /wine/drive_c/MetaTrader5/Files/BITTEN/fire.txt'
            ])
            
            # EA should clear the file after processing
            return result.exit_code == 0 and len(result.output.decode().strip()) == 0
            
        except Exception as e:
            logger.error(f"Error checking EA status: {e}")
            return False
    
    def get_all_container_statuses(self) -> Dict[str, ContainerStatus]:
        """Get status for all known containers"""
        statuses = {}
        
        if not self.docker_client:
            return statuses
        
        try:
            # Get all containers that match the pattern mt5_user_*
            containers = self.docker_client.containers.list(all=True)
            
            for container in containers:
                if container.name.startswith('mt5_user_'):
                    status = self.check_container_status(container.name)
                    statuses[container.name] = status
            
            # Cache the results
            self.status_cache = statuses
            self.last_update = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            logger.error(f"Error getting container statuses: {e}")
        
        return statuses
    
    def get_ready_containers(self) -> List[str]:
        """Get list of containers ready for fire packets"""
        ready_containers = []
        statuses = self.get_all_container_statuses()
        
        for container_name, status in statuses.items():
            if status.status == "ready_for_fire":
                ready_containers.append(container_name)
        
        return ready_containers
    
    def format_container_status_message(self, container_name: str) -> str:
        """Format container status for Telegram message"""
        status = self.check_container_status(container_name)
        
        # Status emoji mapping
        status_emojis = {
            "unassigned": "⚪",
            "credentials_injected": "🟡", 
            "mt5_logged_in": "🟠",
            "ready_for_fire": "🟢",
            "error_state": "🔴"
        }
        
        emoji = status_emojis.get(status.status, "❓")
        
        if status.status == "ready_for_fire":
            return f"""🧠 **Container:** `{container_name}`
{emoji} **Status:** Ready for Fire
✅ **MT5 Logged In**
💰 **Balance:** ${status.account_balance:,.2f}
🎯 **Ready to receive signals**"""
        
        elif status.status == "mt5_logged_in":
            return f"""🧠 **Container:** `{container_name}`
{emoji} **Status:** MT5 Connected
✅ **MT5 Logged In**
💰 **Balance:** ${status.account_balance:,.2f}
⚠️ **EA not active - fire packets disabled**"""
        
        elif status.status == "credentials_injected":
            return f"""🧠 **Container:** `{container_name}`
{emoji} **Status:** Credentials Set
⚠️ **MT5 not connected**
🔄 **Please restart MT5 or check connection**"""
        
        elif status.status == "error_state":
            return f"""🧠 **Container:** `{container_name}`
{emoji} **Status:** Error
❌ **Error:** {status.error_message or 'Unknown error'}
🛠️ **Please contact support**"""
        
        else:  # unassigned
            return f"""🧠 **Container:** `{container_name}`
{emoji} **Status:** Not configured
🌐 **Visit https://joinbitten.com to set up your account**"""
    
    def get_system_overview(self) -> str:
        """Get system-wide container overview"""
        statuses = self.get_all_container_statuses()
        
        if not statuses:
            return "📊 **System Status:** No containers found"
        
        status_counts = {}
        total_balance = 0.0
        
        for container_status in statuses.values():
            status = container_status.status
            status_counts[status] = status_counts.get(status, 0) + 1
            if container_status.account_balance > 0:
                total_balance += container_status.account_balance
        
        ready_count = status_counts.get("ready_for_fire", 0)
        total_count = len(statuses)
        
        return f"""📊 **HydraX System Overview**

🎯 **Ready for Fire:** {ready_count}/{total_count} containers
💰 **Total Balance:** ${total_balance:,.2f}

**Status Breakdown:**
🟢 Ready: {status_counts.get('ready_for_fire', 0)}
🟠 MT5 Connected: {status_counts.get('mt5_logged_in', 0)}
🟡 Credentials Set: {status_counts.get('credentials_injected', 0)}
⚪ Unassigned: {status_counts.get('unassigned', 0)}
🔴 Errors: {status_counts.get('error_state', 0)}

Last Updated: {self.last_update or 'Never'}"""

# Global instance
_status_tracker = None

def get_container_status_tracker() -> ContainerStatusTracker:
    """Get global container status tracker instance"""
    global _status_tracker
    if _status_tracker is None:
        _status_tracker = ContainerStatusTracker()
    return _status_tracker

# Convenience functions
def check_container_status(container_name: str) -> ContainerStatus:
    """Check single container status - convenience function"""
    return get_container_status_tracker().check_container_status(container_name)

def get_ready_containers() -> List[str]:
    """Get ready containers - convenience function"""
    return get_container_status_tracker().get_ready_containers()

def format_status_message(container_name: str) -> str:
    """Format status message - convenience function"""
    return get_container_status_tracker().format_container_status_message(container_name)

if __name__ == "__main__":
    # Test the status tracker
    tracker = ContainerStatusTracker()
    
    # Test container status check
    test_container = "hydrax_engine_node_v7"
    status = tracker.check_container_status(test_container)
    print(f"Container {test_container} status: {status}")
    
    # Test message formatting
    message = tracker.format_container_status_message(test_container)
    print(f"Status message:\\n{message}")
    
    # Test system overview
    overview = tracker.get_system_overview()
    print(f"System overview:\\n{overview}")