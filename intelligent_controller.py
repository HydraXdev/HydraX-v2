
import asyncio
import aiohttp
import websockets
import json
import time
import logging
from typing import Optional, Dict, Any
import paramiko

class IntelligentController:
    def __init__(self, target_ip="3.145.84.187"):
        self.target_ip = target_ip
        self.connection_methods = [
            {'type': 'http', 'port': 5555, 'priority': 1},
            {'type': 'http', 'port': 5556, 'priority': 2}, 
            {'type': 'websocket', 'port': 5557, 'priority': 3},
            {'type': 'ssh', 'port': 22, 'priority': 4}
        ]
        self.active_connection = None
        self.session = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def test_connection(self, method: Dict) -> bool:
        """Test if a connection method is working"""
        try:
            if method['type'] == 'http':
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{self.target_ip}:{method['port']}/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        return response.status == 200
                        
            elif method['type'] == 'websocket':
                async with websockets.connect(
                    f"ws://{self.target_ip}:{method['port']}", 
                    timeout=5
                ) as websocket:
                    await websocket.send(json.dumps({'type': 'ping'}))
                    return True
                    
            elif method['type'] == 'ssh':
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.target_ip, port=method['port'], 
                          username='Administrator', timeout=5)
                ssh.close()
                return True
                
        except Exception as e:
            self.logger.debug(f"Connection test failed for {method}: {e}")
            return False
            
        return False
    
    async def find_best_connection(self) -> Optional[Dict]:
        """Find the best available connection method"""
        # Sort by priority
        methods = sorted(self.connection_methods, key=lambda x: x['priority'])
        
        for method in methods:
            if await self.test_connection(method):
                self.logger.info(f"Found working connection: {method['type']}:{method['port']}")
                return method
                
        return None
    
    async def execute_command(self, command: str, command_type: str = 'powershell') -> Dict[str, Any]:
        """Execute command with automatic failover"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Find best connection if not set
                if not self.active_connection:
                    self.active_connection = await self.find_best_connection()
                    
                if not self.active_connection:
                    raise Exception("No working connections available")
                
                # Execute based on connection type
                if self.active_connection['type'] == 'http':
                    return await self._execute_http(command, command_type)
                elif self.active_connection['type'] == 'websocket':
                    return await self._execute_websocket(command, command_type)
                elif self.active_connection['type'] == 'ssh':
                    return await self._execute_ssh(command, command_type)
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                self.active_connection = None  # Reset connection
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
                    
        raise Exception("All connection attempts failed")
    
    async def _execute_http(self, command: str, command_type: str) -> Dict[str, Any]:
        """Execute via HTTP"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.target_ip}:{self.active_connection['port']}/execute",
                json={'command': command, 'type': command_type},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return await response.json()
    
    async def _execute_websocket(self, command: str, command_type: str) -> Dict[str, Any]:
        """Execute via WebSocket"""
        async with websockets.connect(
            f"ws://{self.target_ip}:{self.active_connection['port']}"
        ) as websocket:
            await websocket.send(json.dumps({
                'command': command,
                'type': command_type
            }))
            response = await websocket.recv()
            return json.loads(response)
    
    async def _execute_ssh(self, command: str, command_type: str) -> Dict[str, Any]:
        """Execute via SSH"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.target_ip, username='Administrator')
        
        if command_type == 'powershell':
            stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "{command}"')
        else:
            stdin, stdout, stderr = ssh.exec_command(command)
        
        result = {
            'success': True,
            'stdout': stdout.read().decode(),
            'stderr': stderr.read().decode(),
            'returncode': stdout.channel.recv_exit_status(),
            'agent_id': 'ssh_fallback'
        }
        
        ssh.close()
        return result
    
    async def start_monitoring(self):
        """Start continuous monitoring and auto-recovery"""
        while True:
            try:
                # Check if connection is still alive
                if self.active_connection:
                    if not await self.test_connection(self.active_connection):
                        self.logger.warning("Active connection failed, switching...")
                        self.active_connection = None
                
                # Try to restart agents if all are down
                if not self.active_connection:
                    await self._emergency_restart()
                    
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _emergency_restart(self):
        """Emergency restart of all agents"""
        self.logger.error("EMERGENCY: Attempting to restart all agents...")
        
        # Try SSH to restart
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.target_ip, username='Administrator')
            
            # Kill existing agents
            ssh.exec_command('taskkill /F /IM python.exe /T')
            time.sleep(3)
            
            # Restart agents
            ssh.exec_command('cd C:\\BITTEN_Agent && START_AGENTS.bat')
            
            ssh.close()
            
            # Wait for agents to start
            await asyncio.sleep(10)
            
        except Exception as e:
            self.logger.error(f"Emergency restart failed: {e}")

# Global controller instance
controller = IntelligentController()

async def execute_command_safe(command: str, command_type: str = 'powershell') -> Dict[str, Any]:
    """Safe command execution with automatic failover"""
    return await controller.execute_command(command, command_type)

async def start_monitoring():
    """Start the monitoring system"""
    await controller.start_monitoring()

# Example usage
if __name__ == "__main__":
    asyncio.run(start_monitoring())
