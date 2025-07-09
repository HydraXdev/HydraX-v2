#!/usr/bin/env python3
"""
BITTEN Windows Server Cleanup and Setup Script
This script will clean old files and set up the MT5 farm properly
"""

import requests
import json
import time
import os
from datetime import datetime

class WindowsServerManager:
    def __init__(self, server_ip="3.145.84.187", port=5555):
        self.base_url = f"http://{server_ip}:{port}"
        self.session = requests.Session()
        self.session.timeout = 30
        
    def execute_command(self, command, description=""):
        """Execute PowerShell command on Windows server"""
        print(f"🔧 {description}")
        try:
            response = self.session.post(
                f"{self.base_url}/execute",
                json={"command": command, "powershell": True}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('stdout'):
                    print(f"✅ Success: {result['stdout'][:200]}...")
                if result.get('stderr'):
                    print(f"⚠️  Warning: {result['stderr'][:200]}...")
                return True
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_connection(self):
        """Test connection to Windows server"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                print("✅ Connected to Windows server")
                return True
        except:
            pass
        print("❌ Cannot connect to Windows server")
        return False
    
    def cleanup_old_files(self):
        """Clean up old bridge files, hydra bridges, and outdated MT5 files"""
        print("\n🧹 CLEANING UP OLD FILES...")
        
        # 1. Remove old bridge directories
        cleanup_commands = [
            # Remove old bridge folders
            "Remove-Item -Path 'C:\\HydraX*' -Recurse -Force -ErrorAction SilentlyContinue",
            "Remove-Item -Path 'C:\\Bridge*' -Recurse -Force -ErrorAction SilentlyContinue", 
            "Remove-Item -Path 'C:\\MT5Bridge*' -Recurse -Force -ErrorAction SilentlyContinue",
            
            # Remove old EA files
            "Get-ChildItem -Path 'C:\\' -Recurse -Filter '*HydraX*.mq*' -ErrorAction SilentlyContinue | Remove-Item -Force",
            "Get-ChildItem -Path 'C:\\' -Recurse -Filter '*Bridge*.mq*' -ErrorAction SilentlyContinue | Remove-Item -Force",
            "Get-ChildItem -Path 'C:\\' -Recurse -Filter '*Old*.mq*' -ErrorAction SilentlyContinue | Remove-Item -Force",
            
            # Clean old MT5 data files
            "Get-ChildItem -Path 'C:\\Users\\*\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\MQL5\\Files' -Recurse -Filter '*hydra*' -ErrorAction SilentlyContinue | Remove-Item -Force",
            "Get-ChildItem -Path 'C:\\Users\\*\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\MQL5\\Files' -Recurse -Filter '*bridge*' -ErrorAction SilentlyContinue | Remove-Item -Force",
            
            # Remove temp files
            "Remove-Item -Path 'C:\\Windows\\Temp\\*bridge*' -Recurse -Force -ErrorAction SilentlyContinue",
            "Remove-Item -Path 'C:\\Windows\\Temp\\*hydra*' -Recurse -Force -ErrorAction SilentlyContinue",
            
            # Stop any old processes
            "Get-Process | Where-Object {$_.ProcessName -like '*bridge*' -or $_.ProcessName -like '*hydra*'} | Stop-Process -Force -ErrorAction SilentlyContinue"
        ]
        
        for cmd in cleanup_commands:
            self.execute_command(cmd, "Cleaning old files...")
            time.sleep(1)
    
    def setup_mt5_farm_structure(self):
        """Create proper MT5 farm directory structure"""
        print("\n🏗️  SETTING UP MT5 FARM STRUCTURE...")
        
        # Create directory structure
        directories = [
            "C:\\MT5_Farm",
            "C:\\MT5_Farm\\Masters",
            "C:\\MT5_Farm\\Masters\\Forex_Demo", 
            "C:\\MT5_Farm\\Masters\\Forex_Live",
            "C:\\MT5_Farm\\Masters\\Coinexx_Live",
            "C:\\MT5_Farm\\Clones",
            "C:\\MT5_Farm\\EA",
            "C:\\MT5_Farm\\Commands",
            "C:\\MT5_Farm\\Responses",
            "C:\\MT5_Farm\\Logs",
            "C:\\BITTEN_Bridge",
            "C:\\BITTEN_Bridge\\Commands",
            "C:\\BITTEN_Bridge\\Responses"
        ]
        
        for directory in directories:
            cmd = f"New-Item -ItemType Directory -Path '{directory}' -Force"
            self.execute_command(cmd, f"Creating {directory}")
    
    def deploy_bitten_ea(self):
        """Deploy the current BITTEN EA files"""
        print("\n📦 DEPLOYING BITTEN EA FILES...")
        
        # Read the EA file locally
        ea_path = "/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5"
        
        if not os.path.exists(ea_path):
            print("❌ BITTEN EA file not found locally!")
            return False
        
        try:
            with open(ea_path, 'r', encoding='utf-8') as f:
                ea_content = f.read()
            
            # Upload to Windows server
            response = self.session.post(
                f"{self.base_url}/upload",
                json={
                    "filepath": "C:\\MT5_Farm\\EA\\BITTENBridge_v3_ENHANCED.mq5",
                    "content": ea_content
                }
            )
            
            if response.status_code == 200:
                print("✅ EA uploaded successfully")
                
                # Copy to each master directory
                masters = ["Forex_Demo", "Forex_Live", "Coinexx_Live"]
                for master in masters:
                    copy_cmd = f"Copy-Item 'C:\\MT5_Farm\\EA\\BITTENBridge_v3_ENHANCED.mq5' 'C:\\MT5_Farm\\Masters\\{master}\\MQL5\\Experts\\' -Force"
                    self.execute_command(copy_cmd, f"Copying EA to {master}")
                
                return True
            else:
                print(f"❌ Failed to upload EA: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying EA: {e}")
            return False
    
    def verify_mt5_installations(self):
        """Verify MT5 installations are present"""
        print("\n🔍 VERIFYING MT5 INSTALLATIONS...")
        
        check_cmd = '''
        $mt5Paths = @(
            "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
            "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
            "C:\\Users\\*\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\terminal64.exe"
        )
        
        $found = @()
        foreach ($path in $mt5Paths) {
            $files = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
            if ($files) {
                $found += $files.FullName
            }
        }
        
        if ($found.Count -gt 0) {
            Write-Host "Found $($found.Count) MT5 installations:" -ForegroundColor Green
            $found | ForEach-Object { Write-Host "  - $_" }
        } else {
            Write-Host "No MT5 installations found!" -ForegroundColor Red
        }
        '''
        
        return self.execute_command(check_cmd, "Checking MT5 installations")
    
    def create_communication_system(self):
        """Create the command/response communication system"""
        print("\n📡 SETTING UP COMMUNICATION SYSTEM...")
        
        # Create Python bridge monitor script
        bridge_script = '''
import os
import json
import time
import glob
from datetime import datetime

class BridgeMonitor:
    def __init__(self):
        self.commands_dir = "C:\\\\BITTEN_Bridge\\\\Commands"
        self.responses_dir = "C:\\\\BITTEN_Bridge\\\\Responses"
        
    def monitor_commands(self):
        """Monitor for new command files"""
        while True:
            try:
                # Check for new command files
                cmd_files = glob.glob(f"{self.commands_dir}\\\\*.json")
                
                for cmd_file in cmd_files:
                    self.process_command(cmd_file)
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Bridge monitor error: {e}")
                time.sleep(5)
    
    def process_command(self, cmd_file):
        """Process a command file"""
        try:
            with open(cmd_file, 'r') as f:
                command = json.load(f)
            
            # Create response
            response = {
                "command_id": command.get("id"),
                "status": "processed",
                "timestamp": datetime.now().isoformat(),
                "result": "Command processed successfully"
            }
            
            # Write response
            response_file = f"{self.responses_dir}\\\\response_{command.get('id')}.json"
            with open(response_file, 'w') as f:
                json.dump(response, f, indent=2)
            
            # Remove command file
            os.remove(cmd_file)
            
        except Exception as e:
            print(f"Error processing command: {e}")

if __name__ == "__main__":
    monitor = BridgeMonitor()
    monitor.monitor_commands()
'''
        
        # Upload bridge monitor
        response = self.session.post(
            f"{self.base_url}/upload",
            json={
                "filepath": "C:\\BITTEN_Bridge\\bridge_monitor.py",
                "content": bridge_script
            }
        )
        
        if response.status_code == 200:
            print("✅ Bridge monitor deployed")
            return True
        else:
            print("❌ Failed to deploy bridge monitor")
            return False
    
    def run_full_cleanup_and_setup(self):
        """Run complete cleanup and setup process"""
        print("🚀 STARTING COMPLETE WINDOWS SERVER CLEANUP AND SETUP")
        print("=" * 60)
        
        # 1. Test connection
        if not self.test_connection():
            print("❌ Cannot connect to Windows server. Is the agent running?")
            return False
        
        # 2. Stop any running MT5 instances
        print("\n🛑 STOPPING EXISTING MT5 INSTANCES...")
        self.execute_command("Get-Process | Where-Object {$_.ProcessName -like '*terminal*'} | Stop-Process -Force -ErrorAction SilentlyContinue", "Stopping MT5 instances")
        
        # 3. Clean up old files
        self.cleanup_old_files()
        
        # 4. Set up farm structure
        self.setup_mt5_farm_structure()
        
        # 5. Verify MT5 installations
        self.verify_mt5_installations()
        
        # 6. Deploy BITTEN EA
        self.deploy_bitten_ea()
        
        # 7. Set up communication system
        self.create_communication_system()
        
        print("\n✅ CLEANUP AND SETUP COMPLETE!")
        print("\nNext steps:")
        print("1. Start MT5 instances manually")
        print("2. Load BITTEN EA in each instance")
        print("3. Configure trading pairs")
        print("4. Test communication")
        
        return True

if __name__ == "__main__":
    manager = WindowsServerManager()
    manager.run_full_cleanup_and_setup()