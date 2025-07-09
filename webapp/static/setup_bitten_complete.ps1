# BITTEN Complete Setup Script for Windows
# Downloads EA and sets up 3 MT5 instances

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "BITTEN EA Complete Setup v1.0" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Download EA if not present
if (-not (Test-Path "BITTENBridge_v3_ENHANCED.mq5")) {
    Write-Host "Downloading BITTEN EA..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "http://134.199.204.67:8888/static/BITTENBridge_v3_ENHANCED.mq5" -OutFile "BITTENBridge_v3_ENHANCED.mq5"
        Write-Host "EA downloaded successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download EA. Trying alternative method..." -ForegroundColor Red
        curl http://134.199.204.67:8888/static/BITTENBridge_v3_ENHANCED.mq5 -o BITTENBridge_v3_ENHANCED.mq5
    }
} else {
    Write-Host "EA file found!" -ForegroundColor Green
}

# Step 2: Create directory structure
Write-Host ""
Write-Host "Creating BITTEN directories..." -ForegroundColor Yellow

$directories = @(
    "C:\BITTEN_Bridge",
    "C:\BITTEN_Bridge\Instance1",
    "C:\BITTEN_Bridge\Instance2", 
    "C:\BITTEN_Bridge\Instance3",
    "C:\BITTEN_Bridge\Logs",
    "C:\BITTEN_Bridge\Config"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Write-Host "Created: $dir" -ForegroundColor Gray
}

# Step 3: Find MT5 installations
Write-Host ""
Write-Host "Searching for MT5 installations..." -ForegroundColor Yellow

$mt5Paths = @()
$terminalPath = "$env:APPDATA\MetaQuotes\Terminal"

if (Test-Path $terminalPath) {
    Get-ChildItem -Path $terminalPath -Directory | ForEach-Object {
        if (Test-Path "$($_.FullName)\MQL5\Experts") {
            $mt5Paths += $_.FullName
            Write-Host "Found MT5: $($_.Name)" -ForegroundColor Green
        }
    }
}

# Step 4: Setup each instance
if ($mt5Paths.Count -eq 0) {
    Write-Host ""
    Write-Host "No MT5 installations found!" -ForegroundColor Red
    Write-Host "Please install MT5 first." -ForegroundColor Red
    Write-Host ""
    Write-Host "Quick MT5 Setup:" -ForegroundColor Yellow
    Write-Host "1. Download MT5 from your broker" -ForegroundColor Gray
    Write-Host "2. Install 3 times to different folders:" -ForegroundColor Gray
    Write-Host "   - C:\MT5_Nibbler" -ForegroundColor Gray
    Write-Host "   - C:\MT5_Commander" -ForegroundColor Gray
    Write-Host "   - C:\MT5_APEX" -ForegroundColor Gray
    exit
}

Write-Host ""
Write-Host "Setting up MT5 instances..." -ForegroundColor Yellow

# Instance configurations
$configs = @(
    @{
        Name = "Nibbler/Fang"
        Magic = 20250626
        MaxRisk = 2.0
        MaxTrades = 10
        Prefix = "bitten1_"
    },
    @{
        Name = "Commander"
        Magic = 20250627
        MaxRisk = 3.0
        MaxTrades = 20
        Prefix = "bitten2_"
    },
    @{
        Name = "APEX"
        Magic = 20250628
        MaxRisk = 5.0
        MaxTrades = 50
        Prefix = "bitten3_"
    }
)

# Copy EA to each available MT5
for ($i = 0; $i -lt [Math]::Min($mt5Paths.Count, 3); $i++) {
    $mt5Path = $mt5Paths[$i]
    $config = $configs[$i]
    $instance = $i + 1
    
    Write-Host ""
    Write-Host "Configuring Instance $instance ($($config.Name))..." -ForegroundColor Cyan
    
    # Copy EA
    $eaPath = "$mt5Path\MQL5\Experts\BITTEN_Instance$instance.mq5"
    Copy-Item -Path "BITTENBridge_v3_ENHANCED.mq5" -Destination $eaPath -Force
    Write-Host "  - EA copied to: $eaPath" -ForegroundColor Gray
    
    # Create set file for EA configuration
    $setContent = @"
; BITTEN Instance $instance Configuration
; Tier: $($config.Name)
; Generated: $(Get-Date)

InstructionFile=$($config.Prefix)instructions_secure.txt
CommandFile=$($config.Prefix)commands_secure.txt
ResultFile=$($config.Prefix)results_secure.txt
StatusFile=$($config.Prefix)status_secure.txt
PositionsFile=$($config.Prefix)positions_secure.txt
AccountFile=$($config.Prefix)account_secure.txt
MarketFile=$($config.Prefix)market_secure.txt
CheckIntervalMs=100
MagicNumber=$($config.Magic)
EnableTrailing=true
EnablePartialClose=true
EnableBreakEven=true
EnableMultiTP=true
PartialClosePercent=50.0
BreakEvenPoints=20
BreakEvenBuffer=5
MaxLotSize=10.0
MaxRiskPercent=$($config.MaxRisk)
MaxDailyTrades=$($config.MaxTrades)
MaxConcurrentTrades=10
"@
    
    $setPath = "$mt5Path\MQL5\Presets\BITTEN_Instance$instance.set"
    New-Item -ItemType Directory -Force -Path "$mt5Path\MQL5\Presets" | Out-Null
    Set-Content -Path $setPath -Value $setContent
    Write-Host "  - Settings saved to: $setPath" -ForegroundColor Gray
}

# Step 5: Create helper scripts
Write-Host ""
Write-Host "Creating helper scripts..." -ForegroundColor Yellow

# Quick compile script
$compileScript = @'
@echo off
echo Compiling BITTEN EAs...
echo.

REM Find MetaEditor
for /f "tokens=*" %%a in ('where /r "%APPDATA%\MetaQuotes" metaeditor64.exe 2^>nul') do set EDITOR=%%a

if not defined EDITOR (
    echo MetaEditor not found! Please open MT5 and compile manually.
    pause
    exit /b 1
)

echo Found MetaEditor: %EDITOR%
echo.

REM Compile each instance
for %%i in (1 2 3) do (
    echo Compiling Instance %%i...
    "%EDITOR%" /compile:"%APPDATA%\MetaQuotes\Terminal\*\MQL5\Experts\BITTEN_Instance%%i.mq5" /log
)

echo.
echo Compilation complete! Check for errors above.
pause
'@

Set-Content -Path "Compile_All_EAs.bat" -Value $compileScript

# Create master launcher
$launcherScript = @'
@echo off
echo Starting all BITTEN instances...
echo.

start "BITTEN Instance 1" Launch_Instance1.bat
timeout /t 5 >nul

start "BITTEN Instance 2" Launch_Instance2.bat
timeout /t 5 >nul

start "BITTEN Instance 3" Launch_Instance3.bat

echo.
echo All instances started!
echo Use Monitor_BITTEN.bat to watch file activity.
pause
'@

Set-Content -Path "Launch_All_Instances.bat" -Value $launcherScript

# Create test signal sender
$testScript = @"
# Test signal sender for BITTEN
# Run this to test if the bridge is working

import json
import time
from datetime import datetime

def send_test_signal(instance=1):
    instruction = {
        "action": "open",
        "symbol": "EURUSD",
        "type": "buy",
        "lots": 0.01,
        "sl": 50,
        "tp": 100,
        "comment": f"BITTEN Test {datetime.now().strftime('%H:%M:%S')}",
        "timestamp": datetime.now().isoformat()
    }
    
    filename = f"C:\\BITTEN_Bridge\\Instance{instance}\\bitten{instance}_instructions_secure.txt"
    
    with open(filename, 'w') as f:
        json.dump(instruction, f)
    
    print(f"Test signal sent to Instance {instance}")
    print(f"Check: {filename}")
    
    # Wait for result
    time.sleep(2)
    
    result_file = f"C:\\BITTEN_Bridge\\Instance{instance}\\bitten{instance}_results_secure.txt"
    try:
        with open(result_file, 'r') as f:
            result = f.read()
            print(f"Result: {result}")
    except:
        print("No result yet - check if EA is running")

if __name__ == "__main__":
    instance = input("Which instance to test (1-3)? ")
    send_test_signal(int(instance))
"@

Set-Content -Path "test_bitten_signal.py" -Value $testScript

# Final summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run: .\Compile_All_EAs.bat" -ForegroundColor White
Write-Host "2. Open each MT5 terminal" -ForegroundColor White
Write-Host "3. Drag BITTEN_Instance[1/2/3] EA to a chart" -ForegroundColor White
Write-Host "4. Load the preset: BITTEN_Instance[1/2/3].set" -ForegroundColor White
Write-Host "5. Enable AutoTrading" -ForegroundColor White
Write-Host ""
Write-Host "Helper Scripts Created:" -ForegroundColor Cyan
Write-Host "- Compile_All_EAs.bat      (Compile all EAs)" -ForegroundColor Gray
Write-Host "- Launch_All_Instances.bat (Start all MT5s)" -ForegroundColor Gray
Write-Host "- Monitor_BITTEN.bat       (Watch file activity)" -ForegroundColor Gray
Write-Host "- test_bitten_signal.py    (Test the bridge)" -ForegroundColor Gray
Write-Host ""
Write-Host "Instance Configuration:" -ForegroundColor Cyan
Write-Host "Instance 1: Nibbler/Fang  (Magic: 20250626, Risk: 2%)" -ForegroundColor Gray
Write-Host "Instance 2: Commander     (Magic: 20250627, Risk: 3%)" -ForegroundColor Gray
Write-Host "Instance 3: APEX          (Magic: 20250628, Risk: 5%)" -ForegroundColor Gray