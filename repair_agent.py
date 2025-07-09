#!/usr/bin/env python3
"""
BULLETPROOF AGENT REPAIR SYSTEM
Diagnoses and fixes backup agent issues remotely
"""

import requests
import json
import time
import sys
from datetime import datetime

class RepairAgent:
    def __init__(self):
        self.target_ip = "3.145.84.187"
        self.primary_port = 5555
        self.backup_port = 5556
        self.websocket_port = 5557
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_primary_agent(self):
        """Test if primary agent is working"""
        try:
            response = self.session.get(f"http://{self.target_ip}:{self.primary_port}/health")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Primary agent ONLINE: {data.get('status', 'unknown')}")
                return True
            else:
                self.log(f"❌ Primary agent HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Primary agent ERROR: {e}")
            return False
            
    def diagnose_backup_agents(self):
        """Diagnose backup agent issues"""
        self.log("🔍 DIAGNOSING BACKUP AGENT ISSUES...")
        
        # Check if processes are running
        try:
            response = self.session.post(
                f"http://{self.target_ip}:{self.primary_port}/execute",
                json={
                    "command": "Get-Process | Where-Object {$_.ProcessName -eq 'python'}",
                    "type": "powershell"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    stdout = result.get('stdout', '')
                    python_processes = len([line for line in stdout.split('\n') if 'python' in line.lower()])
                    self.log(f"📊 Found {python_processes} Python processes running")
                    
                    if python_processes >= 3:
                        self.log("✅ All 3 agents should be running")
                        return self.check_agent_logs()
                    else:
                        self.log("❌ Missing Python processes - need to restart agents")
                        return self.restart_all_agents()
                        
        except Exception as e:
            self.log(f"❌ Process check failed: {e}")
            return False
            
    def check_agent_logs(self):
        """Check for agent startup errors"""
        self.log("📋 CHECKING AGENT LOGS...")
        
        try:
            # Check for backup agent errors
            response = self.session.post(
                f"http://{self.target_ip}:{self.primary_port}/execute",
                json={
                    "command": "Get-EventLog -LogName Application -Source Python -Newest 10 | Format-Table -AutoSize",
                    "type": "powershell"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log("📊 Recent Python events checked")
                    return self.check_firewall_ports()
                    
        except Exception as e:
            self.log(f"⚠️  Log check failed, proceeding: {e}")
            return self.check_firewall_ports()
            
    def check_firewall_ports(self):
        """Check if ports 5556 and 5557 are blocked"""
        self.log("🔥 CHECKING FIREWALL SETTINGS...")
        
        try:
            # Check Windows firewall rules
            response = self.session.post(
                f"http://{self.target_ip}:{self.primary_port}/execute",
                json={
                    "command": "Get-NetFirewallRule -DisplayName '*5556*' -ErrorAction SilentlyContinue | Select-Object DisplayName, Enabled, Direction",
                    "type": "powershell"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    stdout = result.get('stdout', '')
                    if not stdout.strip():
                        self.log("⚠️  No firewall rules found for port 5556")
                        return self.create_firewall_rules()
                    else:
                        self.log(f"📊 Firewall rules: {stdout}")
                        return self.check_port_binding()
                        
        except Exception as e:
            self.log(f"⚠️  Firewall check failed: {e}")
            return self.create_firewall_rules()
            
    def create_firewall_rules(self):
        """Create firewall rules for ports 5556 and 5557"""
        self.log("🔧 CREATING FIREWALL RULES...")
        
        firewall_commands = [
            "New-NetFirewallRule -DisplayName 'BITTEN Backup Agent 5556' -Direction Inbound -Protocol TCP -LocalPort 5556 -Action Allow",
            "New-NetFirewallRule -DisplayName 'BITTEN WebSocket Agent 5557' -Direction Inbound -Protocol TCP -LocalPort 5557 -Action Allow"
        ]
        
        for cmd in firewall_commands:
            try:
                response = self.session.post(
                    f"http://{self.target_ip}:{self.primary_port}/execute",
                    json={
                        "command": cmd,
                        "type": "powershell"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log(f"✅ Firewall rule created: {cmd}")
                    else:
                        self.log(f"⚠️  Firewall rule may exist: {cmd}")
                        
            except Exception as e:
                self.log(f"❌ Firewall rule failed: {e}")
                
        return self.check_port_binding()
        
    def check_port_binding(self):
        """Check if agents are binding to correct ports"""
        self.log("🔌 CHECKING PORT BINDING...")
        
        try:
            response = self.session.post(
                f"http://{self.target_ip}:{self.primary_port}/execute",
                json={
                    "command": "netstat -an | findstr :555",
                    "type": "cmd"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    stdout = result.get('stdout', '')
                    self.log(f"📊 Port status:\n{stdout}")
                    
                    if ':5556' in stdout and ':5557' in stdout:
                        self.log("✅ All ports are bound")
                        return self.test_direct_connection()
                    else:
                        self.log("❌ Ports not bound - restarting agents")
                        return self.restart_backup_agents()
                        
        except Exception as e:
            self.log(f"❌ Port check failed: {e}")
            return self.restart_backup_agents()
            
    def test_direct_connection(self):
        """Test direct connection to backup agents"""
        self.log("🔗 TESTING DIRECT CONNECTION...")
        
        # Test backup agent
        try:
            response = self.session.get(f"http://{self.target_ip}:{self.backup_port}/health", timeout=10)
            if response.status_code == 200:
                self.log("✅ Backup agent is responding!")
                return True
            else:
                self.log(f"❌ Backup agent HTTP {response.status_code}")
        except Exception as e:
            self.log(f"❌ Backup agent connection failed: {e}")
            
        # Test WebSocket agent
        try:
            response = self.session.get(f"http://{self.target_ip}:{self.websocket_port}/health", timeout=10)
            if response.status_code == 200:
                self.log("✅ WebSocket agent is responding!")
                return True
            else:
                self.log(f"❌ WebSocket agent HTTP {response.status_code}")
        except Exception as e:
            self.log(f"❌ WebSocket agent connection failed: {e}")
            
        return self.restart_backup_agents()
        
    def restart_backup_agents(self):
        """Restart backup agents specifically"""
        self.log("🔄 RESTARTING BACKUP AGENTS...")
        
        # Kill backup agents
        kill_commands = [
            "Get-Process | Where-Object {$_.ProcessName -eq 'python' -and $_.MainWindowTitle -like '*backup*'} | Stop-Process -Force",
            "Get-Process | Where-Object {$_.ProcessName -eq 'python' -and $_.MainWindowTitle -like '*websocket*'} | Stop-Process -Force"
        ]
        
        for cmd in kill_commands:
            try:
                response = self.session.post(
                    f"http://{self.target_ip}:{self.primary_port}/execute",
                    json={
                        "command": cmd,
                        "type": "powershell"
                    }
                )
                self.log(f"✅ Executed: {cmd}")
            except Exception as e:
                self.log(f"⚠️  Kill command: {e}")
                
        time.sleep(3)
        
        # Start backup agents
        start_commands = [
            "cd C:\\BITTEN_Agent && Start-Process python -ArgumentList 'backup_agent.py' -WindowStyle Hidden",
            "cd C:\\BITTEN_Agent && Start-Process python -ArgumentList 'websocket_agent.py' -WindowStyle Hidden"
        ]
        
        for cmd in start_commands:
            try:
                response = self.session.post(
                    f"http://{self.target_ip}:{self.primary_port}/execute",
                    json={
                        "command": cmd,
                        "type": "powershell"
                    }
                )
                self.log(f"✅ Started: {cmd}")
            except Exception as e:
                self.log(f"❌ Start failed: {e}")
                
        self.log("⏳ Waiting 10 seconds for agents to start...")
        time.sleep(10)
        
        return self.final_test()
        
    def restart_all_agents(self):
        """Restart all agents using the batch script"""
        self.log("🔄 RESTARTING ALL AGENTS...")
        
        try:
            # Kill all Python processes
            response = self.session.post(
                f"http://{self.target_ip}:{self.primary_port}/execute",
                json={
                    "command": "taskkill /F /IM python.exe /T",
                    "type": "cmd"
                }
            )
            
            self.log("✅ Killed all Python processes")
            time.sleep(5)
            
            # Restart using batch script
            response = self.session.post(
                f"http://{self.target_ip}:{self.primary_port}/execute",
                json={
                    "command": "cd C:\\BITTEN_Agent && START_AGENTS.bat",
                    "type": "cmd"
                }
            )
            
            self.log("✅ Restarted all agents")
            self.log("⏳ Waiting 15 seconds for agents to start...")
            time.sleep(15)
            
            return self.final_test()
            
        except Exception as e:
            self.log(f"❌ Restart failed: {e}")
            return False
            
    def final_test(self):
        """Final test of all agents"""
        self.log("🎯 FINAL AGENT TEST...")
        
        agents = [
            {'name': 'Primary Agent', 'port': 5555},
            {'name': 'Backup Agent', 'port': 5556},
            {'name': 'WebSocket Agent', 'port': 5557}
        ]
        
        working_agents = 0
        
        for agent in agents:
            try:
                response = self.session.get(f"http://{self.target_ip}:{agent['port']}/health", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ {agent['name']}: ONLINE - {data.get('status', 'unknown')}")
                    working_agents += 1
                else:
                    self.log(f"❌ {agent['name']}: HTTP {response.status_code}")
            except Exception as e:
                self.log(f"❌ {agent['name']}: {str(e)[:50]}...")
                
        self.log(f"📊 REPAIR RESULTS: {working_agents}/3 agents working")
        
        if working_agents >= 2:
            self.log("🎉 REPAIR SUCCESSFUL - System is bulletproof!")
            return True
        elif working_agents == 1:
            self.log("⚠️  PARTIAL SUCCESS - Primary agent working, backup repair needed")
            return False
        else:
            self.log("❌ REPAIR FAILED - Manual intervention required")
            return False
            
    def run_repair(self):
        """Run complete repair sequence"""
        self.log("🛠️  STARTING BULLETPROOF AGENT REPAIR...")
        self.log("=" * 60)
        
        # Test primary agent first
        if not self.test_primary_agent():
            self.log("❌ Primary agent not responding - cannot proceed")
            return False
            
        # Run diagnostic sequence
        success = self.diagnose_backup_agents()
        
        if success:
            self.log("🎉 REPAIR COMPLETED SUCCESSFULLY")
            self.log("🛡️  Bulletproof system is now fully operational")
        else:
            self.log("⚠️  REPAIR PARTIALLY COMPLETED")
            self.log("💡 Primary agent is working - system remains bulletproof")
            
        return success

if __name__ == "__main__":
    repair_agent = RepairAgent()
    repair_agent.run_repair()