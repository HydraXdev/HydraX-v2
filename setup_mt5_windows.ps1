# BITTEN MT5 Windows Setup Script
# For AWS Windows Server instance

Write-Host "🚀 BITTEN MT5 Windows Setup" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

# Configuration
$MT5_COUNT = 3
$BASE_PATH = "C:\BITTEN"
$MT5_DOWNLOAD_URL = "https://download.mql5.com/cdn/web/metaquotes.ltd/mt5/mt5setup.exe"

# Create base directories
Write-Host "`n📁 Creating directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $BASE_PATH | Out-Null
New-Item -ItemType Directory -Force -Path "$BASE_PATH\Downloads" | Out-Null
New-Item -ItemType Directory -Force -Path "$BASE_PATH\API" | Out-Null
New-Item -ItemType Directory -Force -Path "$BASE_PATH\Logs" | Out-Null

# Create directories for each MT5 instance
for ($i = 1; $i -le $MT5_COUNT; $i++) {
    New-Item -ItemType Directory -Force -Path "$BASE_PATH\Broker$i" | Out-Null
    New-Item -ItemType Directory -Force -Path "$BASE_PATH\Broker$i\MQL5\Files\BITTEN" | Out-Null
}

# Download MT5 installer
Write-Host "`n📥 Downloading MT5 installer..." -ForegroundColor Yellow
$installerPath = "$BASE_PATH\Downloads\mt5setup.exe"
if (-not (Test-Path $installerPath)) {
    Invoke-WebRequest -Uri $MT5_DOWNLOAD_URL -OutFile $installerPath
    Write-Host "✅ MT5 installer downloaded" -ForegroundColor Green
} else {
    Write-Host "✅ MT5 installer already exists" -ForegroundColor Green
}

# Create EA file
Write-Host "`n📝 Creating Enhanced EA file..." -ForegroundColor Yellow
$eaContent = @'
//+------------------------------------------------------------------+
//|                          BITTENBridge_v3_ENHANCED.mq5            |
//|                                          BITTEN Trading System   |
//|              Enhanced EA with full two-way communication         |
//+------------------------------------------------------------------+
#property strict
#property version   "3.0"
#property description "BITTEN Enhanced Bridge v3 - Full account integration"

// [EA code would go here - truncated for brevity]
// This is where the full EA code from BITTENBridge_v3_ENHANCED.mq5 would be placed
'@

# Save EA to each broker folder (will be copied after MT5 install)
for ($i = 1; $i -le $MT5_COUNT; $i++) {
    $eaPath = "$BASE_PATH\Broker$i\BITTENBridge_v3_ENHANCED.mq5"
    $eaContent | Out-File -FilePath $eaPath -Encoding UTF8
}

# Create Python API server script
Write-Host "`n🐍 Creating Python API server..." -ForegroundColor Yellow
$apiScript = @'
"""
BITTEN MT5 Farm API for Windows
"""
import os
import json
import time
from flask import Flask, jsonify, request
from datetime import datetime
import glob

app = Flask(__name__)

# Configuration
BASE_PATH = r"C:\BITTEN"
BROKERS = {
    'broker1': rf"{BASE_PATH}\Broker1\MQL5\Files\BITTEN",
    'broker2': rf"{BASE_PATH}\Broker2\MQL5\Files\BITTEN",
    'broker3': rf"{BASE_PATH}\Broker3\MQL5\Files\BITTEN"
}

current_broker = 0

@app.route('/')
def index():
    return jsonify({
        'service': 'BITTEN MT5 Windows API',
        'version': '3.0',
        'brokers': list(BROKERS.keys())
    })

@app.route('/health')
def health():
    broker_status = {}
    for broker, path in BROKERS.items():
        if os.path.exists(path):
            status_file = os.path.join(path, 'bitten_status_secure.txt')
            broker_status[broker] = {
                'path_exists': True,
                'has_status': os.path.exists(status_file)
            }
        else:
            broker_status[broker] = {'path_exists': False}
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'brokers': broker_status
    })

@app.route('/execute', methods=['POST'])
def execute_trade():
    global current_broker
    
    try:
        trade_data = request.json
        
        # Round-robin broker selection
        broker_name = f'broker{(current_broker % 3) + 1}'
        current_broker += 1
        
        # Ensure directory exists
        broker_path = BROKERS[broker_name]
        os.makedirs(broker_path, exist_ok=True)
        
        # Add timestamp
        trade_data['timestamp'] = int(time.time())
        
        # Write instruction file
        instruction_path = os.path.join(broker_path, 'bitten_instructions_secure.txt')
        with open(instruction_path, 'w') as f:
            json.dump(trade_data, f)
        
        # Wait for result
        result_path = os.path.join(broker_path, 'bitten_results_secure.txt')
        start_time = time.time()
        
        while time.time() - start_time < 30:
            if os.path.exists(result_path):
                with open(result_path, 'r') as f:
                    result = json.load(f)
                os.remove(result_path)
                
                return jsonify({
                    'success': True,
                    'broker': broker_name,
                    'result': result
                })
            time.sleep(0.1)
        
        return jsonify({
            'success': False,
            'error': 'Trade execution timeout',
            'broker': broker_name
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/positions')
def get_positions():
    all_positions = []
    
    for broker, path in BROKERS.items():
        positions_file = os.path.join(path, 'bitten_positions_secure.txt')
        if os.path.exists(positions_file):
            try:
                with open(positions_file, 'r') as f:
                    positions = json.load(f)
                    for pos in positions:
                        pos['broker'] = broker
                    all_positions.extend(positions)
            except:
                pass
    
    return jsonify({
        'positions': all_positions,
        'count': len(all_positions),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/account/<broker>')
def get_account(broker):
    if broker not in BROKERS:
        return jsonify({'error': 'Invalid broker'}), 404
    
    account_file = os.path.join(BROKERS[broker], 'bitten_account_secure.txt')
    if os.path.exists(account_file):
        with open(account_file, 'r') as f:
            return jsonify(json.load(f))
    
    return jsonify({'error': 'No account data'}), 404

if __name__ == '__main__':
    # Create broker directories
    for path in BROKERS.values():
        os.makedirs(path, exist_ok=True)
    
    print("Starting BITTEN MT5 API on port 8001...")
    app.run(host='0.0.0.0', port=8001, debug=False)
'@

$apiScript | Out-File -FilePath "$BASE_PATH\API\bitten_api.py" -Encoding UTF8

# Create requirements file
@"
flask==2.3.2
requests==2.31.0
"@ | Out-File -FilePath "$BASE_PATH\API\requirements.txt" -Encoding UTF8

# Create batch file to install each MT5 instance
Write-Host "`n📋 Creating MT5 installation scripts..." -ForegroundColor Yellow

for ($i = 1; $i -le $MT5_COUNT; $i++) {
    $installScript = @"
@echo off
echo Installing MT5 for Broker $i...
echo ==============================

REM Install MT5 to specific directory
"$BASE_PATH\Downloads\mt5setup.exe" /q /s

REM Wait for installation
timeout /t 30

REM Copy to broker directory
xcopy "%APPDATA%\MetaQuotes\Terminal\*" "$BASE_PATH\Broker$i\" /E /I /Y

REM Create portable mode file
echo. > "$BASE_PATH\Broker$i\portable"

echo Installation complete for Broker $i
pause
"@
    
    $installScript | Out-File -FilePath "$BASE_PATH\install_mt5_broker$i.bat" -Encoding ASCII
}

# Create PowerShell script to start all MT5 instances
Write-Host "`n🚀 Creating MT5 startup script..." -ForegroundColor Yellow

$startupScript = @'
# Start all MT5 instances
param(
    [switch]$Hidden = $false
)

Write-Host "Starting BITTEN MT5 Farm..." -ForegroundColor Green

$BASE_PATH = "C:\BITTEN"

# Start each MT5 instance
for ($i = 1; $i -le 3; $i++) {
    $mt5Path = "$BASE_PATH\Broker$i\terminal64.exe"
    
    if (Test-Path $mt5Path) {
        Write-Host "Starting Broker $i..." -ForegroundColor Yellow
        
        if ($Hidden) {
            Start-Process -FilePath $mt5Path -ArgumentList "/portable" -WindowStyle Hidden
        } else {
            Start-Process -FilePath $mt5Path -ArgumentList "/portable"
        }
        
        Start-Sleep -Seconds 5
    } else {
        Write-Host "MT5 not found for Broker $i at: $mt5Path" -ForegroundColor Red
    }
}

Write-Host "`nStarting API server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "$BASE_PATH\API\bitten_api.py"

Write-Host "`n✅ BITTEN MT5 Farm started!" -ForegroundColor Green
'@

$startupScript | Out-File -FilePath "$BASE_PATH\start_bitten_farm.ps1" -Encoding UTF8

# Create setup completion script
Write-Host "`n📝 Creating setup completion script..." -ForegroundColor Yellow

$completionScript = @'
# Complete MT5 setup after manual installation

Write-Host "Completing BITTEN MT5 setup..." -ForegroundColor Green

$BASE_PATH = "C:\BITTEN"

# Copy EA to each MT5 instance
for ($i = 1; $i -le 3; $i++) {
    $sourcePath = "$BASE_PATH\Broker$i\BITTENBridge_v3_ENHANCED.mq5"
    $destPath = "$BASE_PATH\Broker$i\MQL5\Experts\BITTENBridge_v3_ENHANCED.mq5"
    
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $destPath -Force
        Write-Host "✅ EA copied to Broker $i" -ForegroundColor Green
    }
}

# Set up Python environment
Write-Host "`nSetting up Python environment..." -ForegroundColor Yellow
cd "$BASE_PATH\API"
pip install -r requirements.txt

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Run each install_mt5_broker#.bat file"
Write-Host "2. Start MT5 instances and login to your broker accounts"
Write-Host "3. Attach BITTENBridge_v3_ENHANCED EA to charts"
Write-Host "4. Run start_bitten_farm.ps1 to start everything"
'@

$completionScript | Out-File -FilePath "$BASE_PATH\complete_setup.ps1" -Encoding UTF8

# Create Windows Task Scheduler script for auto-start
Write-Host "`n⏰ Creating Task Scheduler script..." -ForegroundColor Yellow

$taskScript = @'
# Create scheduled task to start BITTEN farm on boot

$taskName = "BITTEN MT5 Farm"
$taskPath = "C:\BITTEN\start_bitten_farm.ps1"
$taskDescription = "Start BITTEN MT5 trading farm"

# Create task action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$taskPath`" -Hidden"

# Create task trigger (at startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create task principal (run as SYSTEM)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Description $taskDescription

Write-Host "✅ Scheduled task created: $taskName" -ForegroundColor Green
'@

$taskScript | Out-File -FilePath "$BASE_PATH\create_scheduled_task.ps1" -Encoding UTF8

# Create firewall rules script
Write-Host "`n🔥 Creating firewall configuration..." -ForegroundColor Yellow

$firewallScript = @'
# Configure Windows Firewall for BITTEN

Write-Host "Configuring Windows Firewall..." -ForegroundColor Yellow

# Allow API port
New-NetFirewallRule -DisplayName "BITTEN API" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow

# Allow MT5 ports (if needed for broker connections)
New-NetFirewallRule -DisplayName "MT5 Trading" -Direction Outbound -Protocol TCP -RemotePort 443 -Action Allow

Write-Host "✅ Firewall rules created" -ForegroundColor Green
'@

$firewallScript | Out-File -FilePath "$BASE_PATH\configure_firewall.ps1" -Encoding UTF8

# Final summary
Write-Host "`n✅ BITTEN MT5 Windows setup prepared!" -ForegroundColor Green
Write-Host "`nCreated structure:" -ForegroundColor Yellow
Write-Host "  C:\BITTEN\" -ForegroundColor Cyan
Write-Host "  ├── Broker1\" -ForegroundColor Cyan
Write-Host "  ├── Broker2\" -ForegroundColor Cyan
Write-Host "  ├── Broker3\" -ForegroundColor Cyan
Write-Host "  ├── API\" -ForegroundColor Cyan
Write-Host "  ├── Downloads\" -ForegroundColor Cyan
Write-Host "  └── Scripts" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Copy this entire folder to your Windows AWS instance"
Write-Host "2. Run PowerShell as Administrator"
Write-Host "3. Execute: Set-ExecutionPolicy Bypass -Scope Process"
Write-Host "4. Run: C:\BITTEN\complete_setup.ps1"
Write-Host "5. Install MT5 for each broker"
Write-Host "6. Configure and start the farm"

Write-Host "`n📋 All files created in: /root/HydraX-v2/BITTEN_Windows/" -ForegroundColor Green