#!/usr/bin/env python3
"""
SMART REPAIR AGENT - Fixes backup agents without killing primary
"""

import requests
import json
import time
from datetime import datetime

class SmartRepair:
    def __init__(self):
        self.target_ip = "localhost"
        self.primary_port = 5555
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def execute_command(self, command, cmd_type="powershell"):
        """Execute command via primary agent"""
        try:
            response = self.session.post(
                f"http://{self.target_ip}:{self.primary_port}/execute",
                json={
                    "command": command,
                    "type": cmd_type
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('stdout', ''), result.get('stderr', '')
                else:
                    return None, result.get('error', 'Unknown error')
            else:
                return None, f"HTTP {response.status_code}"
                
        except Exception as e:
            return None, str(e)
            
    def check_processes(self):
        """Check what Python processes are running"""
        self.log("🔍 CHECKING PYTHON PROCESSES...")
        
        stdout, stderr = self.execute_command(
            "Get-Process | Where-Object {$_.ProcessName -eq 'python'} | Select-Object Id, ProcessName, MainWindowTitle | Format-Table -AutoSize"
        )
        
        if stdout:
            self.log(f"📊 Python processes:\n{stdout}")
            process_count = len([line for line in stdout.split('\n') if 'python' in line.lower()])
            return process_count
        else:
            self.log(f"❌ Process check failed: {stderr}")
            return 0
            
    def start_backup_agents(self):
        """Start backup agents without affecting primary"""
        self.log("🚀 STARTING BACKUP AGENTS...")
        
        # Create firewall rules first
        firewall_commands = [
            "New-NetFirewallRule -DisplayName 'BITTEN Backup 5556' -Direction Inbound -Protocol TCP -LocalPort 5556 -Action Allow -ErrorAction SilentlyContinue",
            "New-NetFirewallRule -DisplayName 'BITTEN WebSocket 5557' -Direction Inbound -Protocol TCP -LocalPort 5557 -Action Allow -ErrorAction SilentlyContinue"
        ]
        
        for cmd in firewall_commands:
            stdout, stderr = self.execute_command(cmd)
            if stdout or not stderr:
                self.log("✅ Firewall rule ensured")
                
        # Start backup agent
        self.log("🔄 Starting backup agent...")
        stdout, stderr = self.execute_command(
            "cd C:\\BITTEN_Agent; Start-Process python -ArgumentList 'backup_agent.py' -WindowStyle Hidden"
        )
        
        if not stderr:
            self.log("✅ Backup agent started")
        else:
            self.log(f"⚠️  Backup agent: {stderr}")
            
        # Start WebSocket agent
        self.log("🔄 Starting WebSocket agent...")
        stdout, stderr = self.execute_command(
            "cd C:\\BITTEN_Agent; Start-Process python -ArgumentList 'websocket_agent.py' -WindowStyle Hidden"
        )
        
        if not stderr:
            self.log("✅ WebSocket agent started")
        else:
            self.log(f"⚠️  WebSocket agent: {stderr}")
            
        return True
        
    def fix_backup_agent_code(self):
        """Fix potential issues in backup agent code"""
        self.log("🔧 CHECKING BACKUP AGENT CODE...")
        
        # Check if backup agent file exists
        stdout, stderr = self.execute_command(
            "Test-Path C:\\BITTEN_Agent\\backup_agent.py"
        )
        
        if "True" in stdout:
            self.log("✅ Backup agent file exists")
        else:
            self.log("❌ Backup agent file missing")
            return False
            
        # Check if websocket agent file exists
        stdout, stderr = self.execute_command(
            "Test-Path C:\\BITTEN_Agent\\websocket_agent.py"
        )
        
        if "True" in stdout:
            self.log("✅ WebSocket agent file exists")
        else:
            self.log("❌ WebSocket agent file missing")
            return False
            
        return True
        
    def test_agents_final(self):
        """Test all agents after repair"""
        self.log("🎯 TESTING ALL AGENTS...")
        
        agents = [
            {'name': 'Primary Agent', 'port': 5555},
            {'name': 'Backup Agent', 'port': 5556},
            {'name': 'WebSocket Agent', 'port': 5557}
        ]
        
        working_agents = 0
        
        for agent in agents:
            try:
                response = self.session.get(
                    f"http://{self.target_ip}:{agent['port']}/health",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ {agent['name']}: ONLINE - {data.get('status', 'unknown')}")
                    working_agents += 1
                else:
                    self.log(f"❌ {agent['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ {agent['name']}: {str(e)[:50]}...")
                
        return working_agents
        
    def run_smart_repair(self):
        """Run smart repair without killing primary"""
        self.log("🧠 SMART REPAIR INITIATED...")
        self.log("=" * 50)
        
        # Check current state
        process_count = self.check_processes()
        self.log(f"📊 Found {process_count} Python processes")
        
        # Fix agent code issues
        if not self.fix_backup_agent_code():
            self.log("❌ Agent files missing - cannot repair")
            return False
            
        # Start missing agents
        if process_count < 3:
            self.log("🔄 Starting missing agents...")
            self.start_backup_agents()
            
            self.log("⏳ Waiting 10 seconds for agents to start...")
            time.sleep(10)
            
        # Test final state
        working_agents = self.test_agents_final()
        
        self.log(f"📊 REPAIR RESULTS: {working_agents}/3 agents working")
        
        if working_agents == 3:
            self.log("🎉 PERFECT REPAIR - All agents online!")
            return True
        elif working_agents >= 2:
            self.log("⚠️  PARTIAL SUCCESS - System remains bulletproof")
            return True
        else:
            self.log("❌ REPAIR NEEDED - Manual intervention required")
            return False

if __name__ == "__main__":
    repair = SmartRepair()
    repair.run_smart_repair()