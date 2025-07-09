#!/usr/bin/env python3
"""
AWS Windows Server Complete Cleanup & Organization
Target: 3.145.84.187
Purpose: Clean, organize, and document everything on Windows side
"""

import requests
import json
import time
from datetime import datetime

class AWSWindowsOrganizer:
    def __init__(self):
        self.server_ip = "3.145.84.187"
        self.agent_port = 5555
        self.base_url = f"http://{self.server_ip}:{self.agent_port}"
        self.session = requests.Session()
        self.session.timeout = 30
        
    def execute_ps(self, command, description=""):
        """Execute PowerShell command on AWS Windows"""
        print(f"🔧 {description}")
        try:
            response = self.session.post(
                f"{self.base_url}/execute",
                json={"command": command, "powershell": True}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('stdout'):
                    print(f"✅ {result['stdout'][:300]}...")
                if result.get('stderr'):
                    print(f"⚠️  {result['stderr'][:200]}...")
                return True
            else:
                print(f"❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return False
    
    def create_aws_documentation(self):
        """Create comprehensive AWS Windows documentation"""
        print("\n📋 CREATING AWS WINDOWS DOCUMENTATION...")
        
        doc_content = '''
# AWS WINDOWS SERVER DOCUMENTATION
# Target: 3.145.84.187
# Updated: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '''

## CURRENT DIRECTORY STRUCTURE
C:\
├── MT5_Farm\                    # Main MT5 farm directory
│   ├── Masters\                 # Master MT5 instances
│   │   ├── Forex_Demo\         # Demo trading master
│   │   ├── Forex_Live\         # Live trading master  
│   │   ├── Coinexx_Live\       # Coinexx broker master
│   │   └── Generic_Demo\       # Generic demo master
│   ├── Clones\                 # User-specific clones
│   ├── EA\                     # Expert Advisors
│   ├── Commands\               # Command files for MT5
│   ├── Responses\              # Response files from MT5
│   └── Logs\                   # System logs
│
├── BITTEN_Agent\               # Control agent
│   ├── agent.py               # Main agent script
│   └── [support files]       # Agent dependencies
│
├── BITTEN_Bridge\             # Communication bridge
│   ├── Commands\              # Bridge commands
│   ├── Responses\             # Bridge responses
│   └── bridge_monitor.py      # Bridge monitoring
│
└── CLEANUP_TEMP\              # Temporary cleanup files

## TRADING CONFIGURATION
- 10 Currency Pairs: EURUSD, GBPUSD, USDJPY, USDCAD, GBPJPY, AUDUSD, NZDUSD, EURGBP, USDCHF, EURJPY
- 4 Master MT5 Instances for different broker types
- Magic Number Ranges: 20250001-20253067
- Risk Management: 1-3% per trade based on instance type

## SYSTEM STATUS
- Agent Port: 5555
- Communication: File-based bridge system
- EA: BITTENBridge_v3_ENHANCED.mq5
- Status: Needs verification and cleanup

## MAINTENANCE COMMANDS
- Check processes: Get-Process | Where-Object {$_.ProcessName -like "*terminal*"}
- Restart agent: cd C:\BITTEN_Agent && python agent.py
- Check EA files: Get-ChildItem -Path "C:\MT5_Farm\Masters\*\MQL5\Experts\*.mq5"
'''
        
        cmd = f'Set-Content -Path "C:\\AWS_WINDOWS_DOCS.txt" -Value @\'\n{doc_content}\n\'@'
        return self.execute_ps(cmd, "Creating AWS documentation")
    
    def cleanup_old_files(self):
        """Clean up old and conflicting files"""
        print("\n🧹 CLEANING UP OLD FILES ON AWS WINDOWS...")
        
        cleanup_commands = [
            # Remove old bridge/hydra files
            "Get-ChildItem -Path 'C:\\' -Recurse -Include '*HydraX*', '*Bridge*', '*hydra*' -ErrorAction SilentlyContinue | Where-Object {$_.Name -notlike '*BITTENBridge*'} | Remove-Item -Force -Recurse",
            
            # Clean temp directories
            "Remove-Item -Path 'C:\\Windows\\Temp\\*' -Recurse -Force -ErrorAction SilentlyContinue",
            "Remove-Item -Path 'C:\\Temp\\*' -Recurse -Force -ErrorAction SilentlyContinue",
            
            # Stop old processes
            "Get-Process | Where-Object {$_.ProcessName -like '*bridge*' -and $_.ProcessName -notlike '*BITTEN*'} | Stop-Process -Force -ErrorAction SilentlyContinue",
            
            # Clean old EA files (keep only BITTEN)
            "Get-ChildItem -Path 'C:\\' -Recurse -Filter '*.mq*' -ErrorAction SilentlyContinue | Where-Object {$_.Name -notlike '*BITTEN*'} | Remove-Item -Force",
            
            # Create cleanup temp directory
            "New-Item -ItemType Directory -Path 'C:\\CLEANUP_TEMP' -Force"
        ]
        
        for cmd in cleanup_commands:
            self.execute_ps(cmd, "Cleaning old files...")
            time.sleep(2)
    
    def organize_directory_structure(self):
        """Create and organize proper directory structure"""
        print("\n🏗️  ORGANIZING AWS WINDOWS DIRECTORY STRUCTURE...")
        
        directories = [
            "C:\\MT5_Farm",
            "C:\\MT5_Farm\\Masters",
            "C:\\MT5_Farm\\Masters\\Forex_Demo",
            "C:\\MT5_Farm\\Masters\\Forex_Live", 
            "C:\\MT5_Farm\\Masters\\Coinexx_Live",
            "C:\\MT5_Farm\\Masters\\Generic_Demo",
            "C:\\MT5_Farm\\Clones",
            "C:\\MT5_Farm\\EA",
            "C:\\MT5_Farm\\Commands",
            "C:\\MT5_Farm\\Responses", 
            "C:\\MT5_Farm\\Logs",
            "C:\\BITTEN_Agent",
            "C:\\BITTEN_Bridge",
            "C:\\BITTEN_Bridge\\Commands",
            "C:\\BITTEN_Bridge\\Responses"
        ]
        
        for directory in directories:
            cmd = f"New-Item -ItemType Directory -Path '{directory}' -Force"
            self.execute_ps(cmd, f"Creating {directory}")
    
    def verify_ea_deployment(self):
        """Verify EA files are properly deployed"""
        print("\n📦 VERIFYING EA DEPLOYMENT ON AWS WINDOWS...")
        
        verify_commands = [
            # Check main EA file
            "Get-ChildItem -Path 'C:\\MT5_Farm\\EA\\BITTENBridge_v3_ENHANCED.mq5' -ErrorAction SilentlyContinue",
            
            # Check EA in each master
            "Get-ChildItem -Path 'C:\\MT5_Farm\\Masters\\*\\MQL5\\Experts\\BITTENBridge_v3_ENHANCED.mq5' -ErrorAction SilentlyContinue",
            
            # List all EA files
            "Write-Host 'EA Files Found:' -ForegroundColor Green; Get-ChildItem -Path 'C:\\MT5_Farm' -Recurse -Filter '*.mq5' -ErrorAction SilentlyContinue | Select-Object FullName"
        ]
        
        for cmd in verify_commands:
            self.execute_ps(cmd, "Verifying EA files...")
    
    def check_mt5_installations(self):
        """Check MT5 installations and status"""
        print("\n🔍 CHECKING MT5 INSTALLATIONS ON AWS WINDOWS...")
        
        check_commands = [
            # Find MT5 executables
            '''
            Write-Host "Searching for MT5 installations..." -ForegroundColor Cyan
            $mt5Paths = @()
            $searchPaths = @(
                "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe"
            )
            
            foreach ($path in $searchPaths) {
                if (Test-Path $path) {
                    $mt5Paths += $path
                    Write-Host "Found: $path" -ForegroundColor Green
                }
            }
            
            if ($mt5Paths.Count -eq 0) {
                Write-Host "No MT5 installations found!" -ForegroundColor Red
            } else {
                Write-Host "Total MT5 installations: $($mt5Paths.Count)" -ForegroundColor Green
            }
            ''',
            
            # Check running MT5 processes
            '''
            Write-Host "Checking running MT5 processes..." -ForegroundColor Cyan
            $processes = Get-Process | Where-Object {$_.ProcessName -like "*terminal*"}
            if ($processes) {
                Write-Host "Running MT5 instances: $($processes.Count)" -ForegroundColor Green
                $processes | Format-Table ProcessName, Id, StartTime -AutoSize
            } else {
                Write-Host "No MT5 instances currently running" -ForegroundColor Yellow
            }
            '''
        ]
        
        for cmd in check_commands:
            self.execute_ps(cmd, "Checking MT5 status...")
    
    def setup_communication_bridge(self):
        """Set up the communication bridge system"""
        print("\n📡 SETTING UP COMMUNICATION BRIDGE ON AWS WINDOWS...")
        
        bridge_monitor = '''
import os
import json
import time
import glob
import threading
from datetime import datetime

class BITTENBridgeMonitor:
    def __init__(self):
        self.commands_dir = "C:\\\\BITTEN_Bridge\\\\Commands"
        self.responses_dir = "C:\\\\BITTEN_Bridge\\\\Responses"
        self.mt5_commands_dir = "C:\\\\MT5_Farm\\\\Commands"
        self.mt5_responses_dir = "C:\\\\MT5_Farm\\\\Responses"
        self.log_file = "C:\\\\MT5_Farm\\\\Logs\\\\bridge_monitor.log"
        
        # Ensure directories exist
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
        os.makedirs(self.mt5_commands_dir, exist_ok=True)
        os.makedirs(self.mt5_responses_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\\n"
        
        print(log_entry.strip())
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def monitor_commands(self):
        """Monitor for new command files"""
        self.log("Bridge monitor started")
        
        while True:
            try:
                # Check for new command files
                cmd_files = glob.glob(f"{self.commands_dir}\\\\*.json")
                
                for cmd_file in cmd_files:
                    self.process_command(cmd_file)
                
                # Check for responses from MT5
                response_files = glob.glob(f"{self.mt5_responses_dir}\\\\*.json")
                
                for resp_file in response_files:
                    self.process_response(resp_file)
                    
                time.sleep(1)
                
            except Exception as e:
                self.log(f"Bridge monitor error: {e}")
                time.sleep(5)
    
    def process_command(self, cmd_file):
        """Process a command file"""
        try:
            with open(cmd_file, 'r') as f:
                command = json.load(f)
            
            self.log(f"Processing command: {command.get('type', 'unknown')}")
            
            # Forward to MT5
            mt5_cmd_file = f"{self.mt5_commands_dir}\\\\cmd_{command.get('id', 'unknown')}.json"
            with open(mt5_cmd_file, 'w') as f:
                json.dump(command, f, indent=2)
            
            # Remove original command file
            os.remove(cmd_file)
            
        except Exception as e:
            self.log(f"Error processing command: {e}")
    
    def process_response(self, resp_file):
        """Process a response file from MT5"""
        try:
            with open(resp_file, 'r') as f:
                response = json.load(f)
            
            self.log(f"Processing response: {response.get('command_id', 'unknown')}")
            
            # Forward to BITTEN Bridge
            bridge_resp_file = f"{self.responses_dir}\\\\resp_{response.get('command_id', 'unknown')}.json"
            with open(bridge_resp_file, 'w') as f:
                json.dump(response, f, indent=2)
            
            # Remove original response file
            os.remove(resp_file)
            
        except Exception as e:
            self.log(f"Error processing response: {e}")

if __name__ == "__main__":
    monitor = BITTENBridgeMonitor()
    monitor.monitor_commands()
'''
        
        # Upload bridge monitor
        try:
            response = self.session.post(
                f"{self.base_url}/upload",
                json={
                    "filepath": "C:\\BITTEN_Bridge\\bridge_monitor.py",
                    "content": bridge_monitor
                }
            )
            
            if response.status_code == 200:
                print("✅ Bridge monitor deployed to AWS Windows")
            else:
                print("❌ Failed to deploy bridge monitor")
                
        except Exception as e:
            print(f"❌ Error deploying bridge monitor: {e}")
    
    def create_startup_scripts(self):
        """Create Windows startup scripts"""
        print("\n🚀 CREATING STARTUP SCRIPTS ON AWS WINDOWS...")
        
        startup_script = '''
@echo off
title BITTEN System Startup
echo Starting BITTEN System on AWS Windows...

REM Start BITTEN Agent
echo Starting BITTEN Agent...
cd C:\BITTEN_Agent
start "BITTEN Agent" python agent.py

REM Wait a moment
timeout /t 5 /nobreak > nul

REM Start Bridge Monitor
echo Starting Bridge Monitor...
cd C:\BITTEN_Bridge
start "Bridge Monitor" python bridge_monitor.py

REM Check MT5 processes
echo Checking MT5 status...
tasklist | findstr "terminal64.exe"

echo.
echo BITTEN System startup complete!
echo Press any key to exit...
pause > nul
'''
        
        cmd = f'Set-Content -Path "C:\\START_BITTEN.bat" -Value @\'\n{startup_script}\n\'@'
        return self.execute_ps(cmd, "Creating startup script")
    
    def run_full_aws_cleanup(self):
        """Run complete AWS Windows cleanup and organization"""
        print("🚀 STARTING COMPLETE AWS WINDOWS CLEANUP & ORGANIZATION")
        print("=" * 70)
        print(f"Target: {self.server_ip}:{self.agent_port}")
        
        # 1. Test connection
        try:
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                print("✅ Connected to AWS Windows agent")
            else:
                print("❌ Agent not responding properly")
                return False
        except:
            print("❌ Cannot connect to AWS Windows agent")
            print("MANUAL RESTART REQUIRED:")
            print("1. RDP to 3.145.84.187")
            print("2. cd C:\\BITTEN_Agent")
            print("3. python agent.py")
            return False
        
        # 2. Create documentation
        self.create_aws_documentation()
        
        # 3. Clean up old files
        self.cleanup_old_files()
        
        # 4. Organize directory structure
        self.organize_directory_structure()
        
        # 5. Verify EA deployment
        self.verify_ea_deployment()
        
        # 6. Check MT5 installations
        self.check_mt5_installations()
        
        # 7. Set up communication bridge
        self.setup_communication_bridge()
        
        # 8. Create startup scripts
        self.create_startup_scripts()
        
        print("\n✅ AWS WINDOWS CLEANUP & ORGANIZATION COMPLETE!")
        print("\n📋 NEXT STEPS:")
        print("1. Run C:\\START_BITTEN.bat to start all services")
        print("2. Open MT5 instances and login to brokers")
        print("3. Attach BITTENBridge EA to trading charts")
        print("4. Enable 'Allow Live Trading' in each MT5")
        print("5. Test communication from Linux server")
        
        # Final status check
        print("\n📊 FINAL STATUS CHECK:")
        self.execute_ps("Get-ChildItem -Path 'C:\\' -Directory | Where-Object {$_.Name -like '*BITTEN*' -or $_.Name -like '*MT5*'}", "Final directory check")
        
        return True

if __name__ == "__main__":
    organizer = AWSWindowsOrganizer()
    organizer.run_full_aws_cleanup()