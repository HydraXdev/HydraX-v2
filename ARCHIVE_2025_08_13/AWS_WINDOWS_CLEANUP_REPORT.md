# AWS Windows Server Cleanup Report
## Server: 3.145.84.187 (Port 5555)
## Date: 2025-07-11

## Current Directory Structure

### 1. **C:\BITTEN_Agent** (Current Active Directory)
- **agent.py** - Main agent script
- **backup_agent.py** - Backup agent
- **primary_agent.py** - Primary agent
- **websocket_agent.py** - WebSocket agent
- **START_AGENTS.bat** - Batch file to start agents
- **BITTENBridge_v3_ENHANCED.mq5** - EA file (empty placeholder)
- **bitten_market_secure.txt** - Market data file
- **bitten_status_secure.txt** - Status file
- **market_data.txt** - Market data
- **EA_placeholder.mq5** - EA placeholder file

### 2. **C:\HydraBridge** (OLD - Should be removed)
- **inject_trade.ps1** - Old PowerShell script
- **signal.json** - Old signal file
- **test.txt** - Test file
- **trade.json** - Old trade file
- **Windows (C) - Shortcut.lnk** - Shortcut file

### 3. **C:\HydraTools** (OLD - Should be removed)
- **HydraX-v2/** - Old project directory
- **compile.log** - Old compilation log

### 4. **C:\MT5_Farm** (Current MT5 Structure)
- **Masters/** - Master MT5 instances directory
- **Clones/** - Clone instances directory
- **EA/** - Expert Advisors directory
- **create_clones.ps1** - Clone creation script
- **install_mt5.ps1** - MT5 installation script
- **launch_instances.ps1** - Instance launch script

### 5. **Old MT5 Terminal Directories** (Should be removed)
- **C:\MT5-Terminal-9001**
- **C:\MT5-Terminal-9002**
- **C:\MT5-Terminal-9003**
- **C:\MT5-Terminal-9004**
- **C:\MT5-Terminal-9005**
- **C:\MT5-Coinexx**

Each contains full MT5 installations with:
- MetaEditor64.exe
- metatester64.exe
- terminal64.exe
- Config files and folders

### 6. **Program Files MT5 Installations** (Review)
- **C:\Program Files\Coinexx MT5 Terminal** - Old Coinexx installation
- **C:\Program Files\FOREX.com US** - Forex.com installation

## Cleanup Recommendations

### High Priority - Remove Immediately:
1. **C:\HydraBridge** - Old bridge directory, no longer needed
2. **C:\HydraTools** - Old tools directory with outdated HydraX-v2
3. **C:\MT5-Terminal-900X** directories - Old MT5 installations replaced by MT5_Farm structure
4. **C:\MT5-Coinexx** - Old broker-specific installation

### Medium Priority - Review and Clean:
1. **JSON files** in various locations (signal.json, trade.json)
2. **Log files** that are old (compile.log)
3. **Test files** (test.txt)

### Keep and Organize:
1. **C:\BITTEN_Agent** - Active agent directory
2. **C:\MT5_Farm** - New organized MT5 structure
3. **Active .bat and .ps1 scripts** in MT5_Farm

## Estimated Space to be Freed:
- Each MT5 Terminal directory: ~250MB
- Total from 6 old MT5 directories: ~1.5GB
- Program Files MT5 installations: ~500MB
- HydraTools and HydraBridge: ~50MB
- **Total: ~2.05GB**

## Recommended Cleanup Commands:

```powershell
# Remove old Hydra directories
Remove-Item -Path "C:\HydraBridge" -Recurse -Force
Remove-Item -Path "C:\HydraTools" -Recurse -Force

# Remove old MT5 installations in C:\
Remove-Item -Path "C:\MT5-Terminal-9001" -Recurse -Force
Remove-Item -Path "C:\MT5-Terminal-9002" -Recurse -Force
Remove-Item -Path "C:\MT5-Terminal-9003" -Recurse -Force
Remove-Item -Path "C:\MT5-Terminal-9004" -Recurse -Force
Remove-Item -Path "C:\MT5-Terminal-9005" -Recurse -Force
Remove-Item -Path "C:\MT5-Coinexx" -Recurse -Force

# Remove old MT5 installations in Program Files (optional - review first)
# Remove-Item -Path "C:\Program Files\Coinexx MT5 Terminal" -Recurse -Force
# Remove-Item -Path "C:\Program Files\FOREX.com US" -Recurse -Force

# Clean up any stray JSON files
Get-ChildItem -Path "C:\" -Filter "*.json" -Recurse | Where-Object {$_.DirectoryName -notlike "*BITTEN*" -and $_.DirectoryName -notlike "*MT5_Farm*"} | Remove-Item -Force

# Clean up old bridge configuration files
Get-ChildItem -Path "C:\" -Filter "bridge.cfg" -Recurse | Where-Object {$_.DirectoryName -notlike "*MT5_Farm*"} | Remove-Item -Force
```

## Post-Cleanup Structure:
```
C:\
├── BITTEN_Agent\     # Active agent directory
├── MT5_Farm\         # Organized MT5 structure
│   ├── Masters\
│   ├── Clones\
│   └── EA\
└── [System directories]
```

## Safety Notes:
- All cleanup commands include `-Force` to avoid prompts
- Important BITTEN and MT5_Farm directories are preserved
- Recommend backing up any important data before cleanup

## Summary of Files/Directories to Clean:

### Junk/Old Files to Remove:
1. **C:\HydraBridge** - Old bridge implementation (contains inject_trade.ps1, signal.json, test.txt, trade.json)
2. **C:\HydraTools** - Old tools directory with outdated HydraX-v2 folder
3. **C:\MT5-Terminal-9001 through 9005** - 5 old MT5 installations (~250MB each)
4. **C:\MT5-Coinexx** - Old Coinexx-specific MT5 installation
5. **Old JSON files** scattered in non-BITTEN directories
6. **bridge.cfg files** in old MT5 terminal directories

### Files/Directories to Keep:
1. **C:\BITTEN_Agent** - Active agent with running services
2. **C:\MT5_Farm** - New organized MT5 structure with Masters, Clones, and EA folders
3. **C:\Program Files\Python311** - Python installation needed for agents
4. **System directories** (Windows, Program Files core components)

### Additional Observations:
- The BITTEN_Agent directory contains active agent scripts and market data files
- MT5_Farm appears to be the new centralized structure for managing MT5 instances
- Old MT5 terminals in C:\ root are redundant and can be safely removed
- HydraBridge and HydraTools are legacy implementations replaced by BITTEN system