# 🪟 AWS WINDOWS MANUAL CLEANUP & ORGANIZATION

**Target Server**: 3.145.84.187  
**Purpose**: Complete cleanup and organization of Windows side  
**Status**: MANUAL EXECUTION REQUIRED (Agent not responding)

---

## 🚨 STEP 1: RESTART AGENT & CONNECT

### Connect to AWS Windows:
1. **RDP to 3.145.84.187**
2. **Open PowerShell as Administrator**
3. **Navigate to agent**: `cd C:\BITTEN_Agent`
4. **Start agent**: `python agent.py`
5. **Keep PowerShell window open**

---

## 🧹 STEP 2: CLEANUP OLD FILES

### Remove Old/Conflicting Files:
```powershell
# Remove old bridge/hydra files (keep BITTEN files)
Get-ChildItem -Path 'C:\' -Recurse -Include '*HydraX*', '*Bridge*', '*hydra*' -ErrorAction SilentlyContinue | Where-Object {$_.Name -notlike '*BITTENBridge*'} | Remove-Item -Force -Recurse

# Clean temp directories
Remove-Item -Path 'C:\Windows\Temp\*' -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path 'C:\Temp\*' -Recurse -Force -ErrorAction SilentlyContinue

# Stop old processes (keep BITTEN processes)
Get-Process | Where-Object {$_.ProcessName -like '*bridge*' -and $_.ProcessName -notlike '*BITTEN*'} | Stop-Process -Force -ErrorAction SilentlyContinue

# Clean old EA files (keep only BITTEN)
Get-ChildItem -Path 'C:\' -Recurse -Filter '*.mq*' -ErrorAction SilentlyContinue | Where-Object {$_.Name -notlike '*BITTEN*'} | Remove-Item -Force

# Create cleanup temp directory
New-Item -ItemType Directory -Path 'C:\CLEANUP_TEMP' -Force
```

---

## 🏗️ STEP 3: ORGANIZE DIRECTORY STRUCTURE

### Create Proper Directory Structure:
```powershell
# Main directories
New-Item -ItemType Directory -Path 'C:\MT5_Farm' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Masters' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Masters\Forex_Demo' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Masters\Forex_Live' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Masters\Coinexx_Live' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Masters\Generic_Demo' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Clones' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\EA' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Commands' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Responses' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Logs' -Force

# BITTEN Bridge directories
New-Item -ItemType Directory -Path 'C:\BITTEN_Bridge' -Force
New-Item -ItemType Directory -Path 'C:\BITTEN_Bridge\Commands' -Force
New-Item -ItemType Directory -Path 'C:\BITTEN_Bridge\Responses' -Force
```

---

## 📦 STEP 4: VERIFY EA DEPLOYMENT

### Check EA Files:
```powershell
# Check main EA file
Get-ChildItem -Path 'C:\MT5_Farm\EA\BITTENBridge_v3_ENHANCED.mq5' -ErrorAction SilentlyContinue

# Check EA in each master
Get-ChildItem -Path 'C:\MT5_Farm\Masters\*\MQL5\Experts\BITTENBridge_v3_ENHANCED.mq5' -ErrorAction SilentlyContinue

# List all EA files
Write-Host 'EA Files Found:' -ForegroundColor Green
Get-ChildItem -Path 'C:\MT5_Farm' -Recurse -Filter '*.mq5' -ErrorAction SilentlyContinue | Select-Object FullName
```

---

## 🔍 STEP 5: CHECK MT5 INSTALLATIONS

### Find MT5 Installations:
```powershell
# Find MT5 executables
Write-Host "Searching for MT5 installations..." -ForegroundColor Cyan
$mt5Paths = @()
$searchPaths = @(
    "C:\Program Files\MetaTrader 5\terminal64.exe",
    "C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
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

# Check running MT5 processes
Write-Host "Checking running MT5 processes..." -ForegroundColor Cyan
$processes = Get-Process | Where-Object {$_.ProcessName -like "*terminal*"}
if ($processes) {
    Write-Host "Running MT5 instances: $($processes.Count)" -ForegroundColor Green
    $processes | Format-Table ProcessName, Id, StartTime -AutoSize
} else {
    Write-Host "No MT5 instances currently running" -ForegroundColor Yellow
}
```

---

## 📡 STEP 6: CREATE BRIDGE MONITOR

### Create Bridge Monitor Script:
```powershell
# Create bridge monitor Python script
$bridgeScript = @'
import os
import json
import time
import glob
import threading
from datetime import datetime

class BITTENBridgeMonitor:
    def __init__(self):
        self.commands_dir = "C:\\BITTEN_Bridge\\Commands"
        self.responses_dir = "C:\\BITTEN_Bridge\\Responses"
        self.mt5_commands_dir = "C:\\MT5_Farm\\Commands"
        self.mt5_responses_dir = "C:\\MT5_Farm\\Responses"
        self.log_file = "C:\\MT5_Farm\\Logs\\bridge_monitor.log"
        
        # Ensure directories exist
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
        os.makedirs(self.mt5_commands_dir, exist_ok=True)
        os.makedirs(self.mt5_responses_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        print(log_entry.strip())
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def monitor_commands(self):
        """Monitor for new command files"""
        self.log("Bridge monitor started")
        
        while True:
            try:
                # Check for new command files
                cmd_files = glob.glob(f"{self.commands_dir}\\*.json")
                
                for cmd_file in cmd_files:
                    self.process_command(cmd_file)
                
                # Check for responses from MT5
                response_files = glob.glob(f"{self.mt5_responses_dir}\\*.json")
                
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
            mt5_cmd_file = f"{self.mt5_commands_dir}\\cmd_{command.get('id', 'unknown')}.json"
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
            bridge_resp_file = f"{self.responses_dir}\\resp_{response.get('command_id', 'unknown')}.json"
            with open(bridge_resp_file, 'w') as f:
                json.dump(response, f, indent=2)
            
            # Remove original response file
            os.remove(resp_file)
            
        except Exception as e:
            self.log(f"Error processing response: {e}")

if __name__ == "__main__":
    monitor = BITTENBridgeMonitor()
    monitor.monitor_commands()
'@

Set-Content -Path "C:\BITTEN_Bridge\bridge_monitor.py" -Value $bridgeScript
```

---

## 🚀 STEP 7: CREATE STARTUP SCRIPTS

### Create Startup Script:
```powershell
$startupScript = @'
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
'@

Set-Content -Path "C:\START_BITTEN.bat" -Value $startupScript
```

---

## 📋 STEP 8: CREATE DOCUMENTATION

### Create AWS Documentation:
```powershell
$docContent = @'
# AWS WINDOWS SERVER DOCUMENTATION
# Target: 3.145.84.187
# Updated: '@ + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + @'

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
└── START_BITTEN.bat           # System startup script

## TRADING CONFIGURATION
- 10 Currency Pairs: EURUSD, GBPUSD, USDJPY, USDCAD, GBPJPY, AUDUSD, NZDUSD, EURGBP, USDCHF, EURJPY
- 4 Master MT5 Instances for different broker types
- Magic Number Ranges: 20250001-20253067
- Risk Management: 1-3% per trade based on instance type

## SYSTEM STATUS
- Agent Port: 5555
- Communication: File-based bridge system
- EA: BITTENBridge_v3_ENHANCED.mq5
- Status: Cleaned and organized

## NEXT STEPS
1. Run C:\START_BITTEN.bat to start all services
2. Open MT5 instances and login to brokers
3. Attach BITTENBridge EA to trading charts
4. Enable 'Allow Live Trading' in each MT5
5. Test communication from Linux server
'@

Set-Content -Path "C:\AWS_WINDOWS_DOCS.txt" -Value $docContent
```

---

## ✅ STEP 9: FINAL VERIFICATION

### Check Everything is in Place:
```powershell
# Check directory structure
Write-Host "=== DIRECTORY STRUCTURE ===" -ForegroundColor Green
Get-ChildItem -Path 'C:\' -Directory | Where-Object {$_.Name -like '*BITTEN*' -or $_.Name -like '*MT5*'} | Format-Table Name, LastWriteTime

# Check important files
Write-Host "=== IMPORTANT FILES ===" -ForegroundColor Green
$importantFiles = @(
    "C:\START_BITTEN.bat",
    "C:\AWS_WINDOWS_DOCS.txt",
    "C:\BITTEN_Agent\agent.py",
    "C:\BITTEN_Bridge\bridge_monitor.py",
    "C:\MT5_Farm\EA\BITTENBridge_v3_ENHANCED.mq5"
)

foreach ($file in $importantFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file (MISSING)" -ForegroundColor Red
    }
}

Write-Host "=== CLEANUP COMPLETE ===" -ForegroundColor Cyan
Write-Host "Ready to run C:\START_BITTEN.bat" -ForegroundColor Yellow
```

---

## 🎯 FINAL STEPS TO GO LIVE

### After Cleanup:
1. **Run**: `C:\START_BITTEN.bat`
2. **Open MT5 instances** and login to brokers
3. **Attach BITTENBridge EA** to 10 currency pair charts in each MT5
4. **Enable "Allow Live Trading"** in each MT5
5. **Test from Linux**: `python3 /root/HydraX-v2/check_mt5_live_status.py`

### Expected Result:
- Agent responding on port 5555
- Bridge monitor processing commands
- MT5 instances running with EA attached
- Communication flow: Linux → Windows → MT5 → Brokers

---

**EXECUTE THESE STEPS IN ORDER ON AWS WINDOWS SERVER 3.145.84.187**