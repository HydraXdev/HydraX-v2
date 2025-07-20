#!/usr/bin/env python3
"""
WINDOWS AGENT DIAGNOSTIC & REPAIR TOOL
Comprehensive testing and repair for Windows agent at localhost:5555
"""

import requests
import socket
import time
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class WindowsAgentDiagnostic:
    """Complete diagnostic and repair tool for Windows agent"""
    
    def __init__(self):
        self.target_ip = "localhost"
        self.agent_ports = [5555, 5556, 5557]  # Primary, Backup, WebSocket
        self.session = requests.Session()
        self.session.timeout = 10
        self.diagnostic_results = {
            'connectivity': {},
            'agent_health': {},
            'system_status': {},
            'repair_actions': []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "📋",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "REPAIR": "🔧"
        }.get(level, "📋")
        
        print(f"[{timestamp}] {prefix} {message}")
        
    def test_basic_connectivity(self) -> bool:
        """Test basic network connectivity to Windows server"""
        self.log("Testing basic connectivity to Windows server...", "INFO")
        
        # Test ping
        try:
            result = subprocess.run(
                ['ping', '-c', '3', self.target_ip],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                self.log("Ping test: PASSED", "SUCCESS")
                self.diagnostic_results['connectivity']['ping'] = True
                return True
            else:
                self.log("Ping test: FAILED - Server not responding", "ERROR")
                self.diagnostic_results['connectivity']['ping'] = False
                return False
                
        except Exception as e:
            self.log(f"Ping test: ERROR - {e}", "ERROR")
            self.diagnostic_results['connectivity']['ping'] = False
            return False
    
    def test_port_connectivity(self) -> Dict[int, bool]:
        """Test connectivity to all agent ports"""
        self.log("Testing port connectivity...", "INFO")
        
        port_results = {}
        for port in self.agent_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.target_ip, port))
                sock.close()
                
                if result == 0:
                    self.log(f"Port {port}: OPEN", "SUCCESS")
                    port_results[port] = True
                else:
                    self.log(f"Port {port}: CLOSED", "ERROR")
                    port_results[port] = False
                    
            except Exception as e:
                self.log(f"Port {port}: ERROR - {e}", "ERROR")
                port_results[port] = False
                
        self.diagnostic_results['connectivity']['ports'] = port_results
        return port_results
    
    def test_agent_health(self) -> Dict[int, dict]:
        """Test health of all agents"""
        self.log("Testing agent health endpoints...", "INFO")
        
        health_results = {}
        for port in self.agent_ports:
            agent_name = {5555: "Primary", 5556: "Backup", 5557: "WebSocket"}[port]
            
            try:
                response = self.session.get(f"http://{self.target_ip}:{port}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"{agent_name} Agent (:{port}): HEALTHY", "SUCCESS")
                    health_results[port] = {
                        'status': 'healthy',
                        'data': data
                    }
                else:
                    self.log(f"{agent_name} Agent (:{port}): HTTP {response.status_code}", "ERROR")
                    health_results[port] = {
                        'status': 'unhealthy',
                        'error': f"HTTP {response.status_code}"
                    }
                    
            except requests.exceptions.ConnectTimeout:
                self.log(f"{agent_name} Agent (:{port}): TIMEOUT", "ERROR")
                health_results[port] = {
                    'status': 'timeout',
                    'error': 'Connection timeout'
                }
            except requests.exceptions.ConnectionError:
                self.log(f"{agent_name} Agent (:{port}): CONNECTION REFUSED", "ERROR")
                health_results[port] = {
                    'status': 'refused',
                    'error': 'Connection refused'
                }
            except Exception as e:
                self.log(f"{agent_name} Agent (:{port}): ERROR - {e}", "ERROR")
                health_results[port] = {
                    'status': 'error',
                    'error': str(e)
                }
                
        self.diagnostic_results['agent_health'] = health_results
        return health_results
    
    def test_mt5_connectivity(self) -> bool:
        """Test MT5 farm connectivity through primary agent"""
        self.log("Testing MT5 farm connectivity...", "INFO")
        
        # Only test if primary agent is healthy
        if self.diagnostic_results['agent_health'].get(5555, {}).get('status') != 'healthy':
            self.log("Primary agent not healthy - skipping MT5 test", "WARNING")
            return False
            
        try:
            # Test MT5 status command
            response = self.session.post(
                f"http://{self.target_ip}:5555/execute",
                json={
                    "command": "Get-Process | Where-Object {$_.ProcessName -like '*terminal*'} | Select-Object -First 5",
                    "type": "powershell"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log("MT5 communication: WORKING", "SUCCESS")
                    self.diagnostic_results['system_status']['mt5_communication'] = True
                    return True
                else:
                    self.log(f"MT5 communication: FAILED - {result.get('error')}", "ERROR")
                    self.diagnostic_results['system_status']['mt5_communication'] = False
                    return False
            else:
                self.log(f"MT5 communication: HTTP {response.status_code}", "ERROR")
                self.diagnostic_results['system_status']['mt5_communication'] = False
                return False
                
        except Exception as e:
            self.log(f"MT5 communication: ERROR - {e}", "ERROR")
            self.diagnostic_results['system_status']['mt5_communication'] = False
            return False
    
    def attempt_agent_repair(self) -> bool:
        """Attempt to repair agents using available methods"""
        self.log("Attempting agent repair...", "REPAIR")
        
        # Check if we have any working agent
        working_agents = [
            port for port, health in self.diagnostic_results['agent_health'].items()
            if health.get('status') == 'healthy'
        ]
        
        if not working_agents:
            self.log("No working agents found - cannot perform remote repair", "ERROR")
            return False
        
        # Use the first working agent for repair
        repair_agent_port = working_agents[0]
        self.log(f"Using agent on port {repair_agent_port} for repair", "REPAIR")
        
        # Attempt to restart failed agents
        repair_success = False
        
        # Try to restart backup agents
        if 5556 not in working_agents:
            self.log("Attempting to restart backup agent...", "REPAIR")
            try:
                response = self.session.post(
                    f"http://{self.target_ip}:{repair_agent_port}/execute",
                    json={
                        "command": "cd C:\\BITTEN_Agent && Start-Process python -ArgumentList 'backup_agent.py' -WindowStyle Hidden",
                        "type": "powershell"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log("Backup agent restart: SUCCESS", "SUCCESS")
                        repair_success = True
                    else:
                        self.log(f"Backup agent restart: FAILED - {result.get('error')}", "ERROR")
                        
            except Exception as e:
                self.log(f"Backup agent restart: ERROR - {e}", "ERROR")
        
        # Try to restart WebSocket agent
        if 5557 not in working_agents:
            self.log("Attempting to restart WebSocket agent...", "REPAIR")
            try:
                response = self.session.post(
                    f"http://{self.target_ip}:{repair_agent_port}/execute",
                    json={
                        "command": "cd C:\\BITTEN_Agent && Start-Process python -ArgumentList 'websocket_agent.py' -WindowStyle Hidden",
                        "type": "powershell"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log("WebSocket agent restart: SUCCESS", "SUCCESS")
                        repair_success = True
                    else:
                        self.log(f"WebSocket agent restart: FAILED - {result.get('error')}", "ERROR")
                        
            except Exception as e:
                self.log(f"WebSocket agent restart: ERROR - {e}", "ERROR")
        
        # Wait for agents to start
        if repair_success:
            self.log("Waiting 10 seconds for agents to start...", "REPAIR")
            time.sleep(10)
            
        return repair_success
    
    def generate_repair_instructions(self) -> List[str]:
        """Generate manual repair instructions based on diagnostic results"""
        instructions = []
        
        if not self.diagnostic_results['connectivity']['ping']:
            instructions.append("1. Check if Windows server is running in AWS Console")
            instructions.append("2. Verify security groups allow inbound traffic on ports 5555-5557")
            instructions.append("3. Check if server has been stopped or terminated")
            
        elif not any(self.diagnostic_results['connectivity']['ports'].values()):
            instructions.append("1. RDP to Windows server (localhost)")
            instructions.append("2. Check Windows Firewall settings")
            instructions.append("3. Verify agents are running: tasklist | findstr python")
            instructions.append("4. Restart all agents: cd C:\\BITTEN_Agent && START_AGENTS.bat")
            
        elif not any(h.get('status') == 'healthy' for h in self.diagnostic_results['agent_health'].values()):
            instructions.append("1. RDP to Windows server (localhost)")
            instructions.append("2. Kill all Python processes: taskkill /F /IM python.exe /T")
            instructions.append("3. Restart agents: cd C:\\BITTEN_Agent && START_AGENTS.bat")
            instructions.append("4. Verify startup: curl http://localhost:5555/health")
            
        else:
            instructions.append("System appears to be working - no manual intervention needed")
            
        return instructions
    
    def run_full_diagnostic(self) -> dict:
        """Run complete diagnostic and repair sequence"""
        self.log("="*60, "INFO")
        self.log("WINDOWS AGENT DIAGNOSTIC & REPAIR TOOL", "INFO")
        self.log("="*60, "INFO")
        
        # Step 1: Basic connectivity
        basic_connectivity = self.test_basic_connectivity()
        
        # Step 2: Port connectivity
        port_connectivity = self.test_port_connectivity()
        
        # Step 3: Agent health
        agent_health = self.test_agent_health()
        
        # Step 4: MT5 connectivity (if possible)
        mt5_connectivity = self.test_mt5_connectivity()
        
        # Step 5: Attempt repair if needed
        repair_attempted = False
        if any(h.get('status') == 'healthy' for h in agent_health.values()):
            # Some agents are working, try to repair others
            repair_attempted = self.attempt_agent_repair()
            
            if repair_attempted:
                self.log("Re-testing after repair...", "REPAIR")
                time.sleep(5)
                self.test_agent_health()
        
        # Step 6: Generate report
        self.generate_final_report()
        
        return self.diagnostic_results
    
    def generate_final_report(self):
        """Generate comprehensive diagnostic report"""
        self.log("="*60, "INFO")
        self.log("DIAGNOSTIC REPORT", "INFO")
        self.log("="*60, "INFO")
        
        # Connectivity summary
        ping_status = "✅ PASS" if self.diagnostic_results['connectivity']['ping'] else "❌ FAIL"
        self.log(f"Network Connectivity: {ping_status}", "INFO")
        
        # Port summary
        ports = self.diagnostic_results['connectivity']['ports']
        open_ports = [port for port, status in ports.items() if status]
        self.log(f"Open Ports: {open_ports} / {self.agent_ports}", "INFO")
        
        # Agent summary
        healthy_agents = [
            port for port, health in self.diagnostic_results['agent_health'].items()
            if health.get('status') == 'healthy'
        ]
        self.log(f"Healthy Agents: {len(healthy_agents)}/3", "INFO")
        
        # Overall system status
        if len(healthy_agents) >= 2:
            self.log("SYSTEM STATUS: OPERATIONAL (Bulletproof)", "SUCCESS")
        elif len(healthy_agents) == 1:
            self.log("SYSTEM STATUS: DEGRADED (Backup needed)", "WARNING")
        else:
            self.log("SYSTEM STATUS: DOWN (Manual intervention required)", "ERROR")
        
        # MT5 status
        mt5_status = self.diagnostic_results['system_status'].get('mt5_communication', False)
        mt5_text = "✅ WORKING" if mt5_status else "❌ NOT WORKING"
        self.log(f"MT5 Communication: {mt5_text}", "INFO")
        
        # Manual repair instructions
        if len(healthy_agents) < 2:
            self.log("MANUAL REPAIR INSTRUCTIONS:", "REPAIR")
            instructions = self.generate_repair_instructions()
            for i, instruction in enumerate(instructions, 1):
                self.log(f"  {instruction}", "REPAIR")
        
        # Save detailed report
        self.save_diagnostic_report()
    
    def save_diagnostic_report(self):
        """Save detailed diagnostic report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"windows_agent_diagnostic_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.diagnostic_results, f, indent=2, default=str)
            
            self.log(f"Detailed report saved: {filename}", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to save report: {e}", "ERROR")

def main():
    """Main diagnostic function"""
    diagnostic = WindowsAgentDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    # Return exit code based on results
    healthy_agents = [
        port for port, health in results['agent_health'].items()
        if health.get('status') == 'healthy'
    ]
    
    if len(healthy_agents) >= 2:
        sys.exit(0)  # Success
    elif len(healthy_agents) == 1:
        sys.exit(1)  # Warning
    else:
        sys.exit(2)  # Error

if __name__ == "__main__":
    main()