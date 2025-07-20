#!/usr/bin/env python3
"""
Configure MT5 Masters with appropriate settings for each type
"""

import requests
import json
import base64

AWS_SERVER = "localhost"
PORT = 5555

def execute_command(command):
    """Execute command on Windows server"""
    try:
        url = f"http://{AWS_SERVER}:{PORT}/execute"
        response = requests.post(url, json={"command": command}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('success', False), result.get('stdout', ''), result.get('stderr', '')
        return False, '', f"HTTP {response.status_code}"
    except Exception as e:
        return False, '', str(e)

def create_master_configs():
    """Create configuration files for each master type"""
    
    print("🔧 Creating MT5 Master Configurations")
    print("=" * 60)
    
    # Master configurations
    masters = {
        "Coinexx_Live": {
            "path": "C:\\MT5_Farm\\Masters\\Coinexx_Live",
            "magic_start": 10001,
            "magic_end": 10100,
            "risk_percent": 1.0,
            "max_daily_loss": 5.0,
            "mode": "CONSERVATIVE",
            "broker": "Coinexx",
            "account_type": "LIVE"
        },
        "Forex_Live": {
            "path": "C:\\MT5_Farm\\Masters\\Forex_Live",
            "magic_start": 20001,
            "magic_end": 20100,
            "risk_percent": 1.0,
            "max_daily_loss": 5.0,
            "mode": "CONSERVATIVE",
            "broker": "Forex.com",
            "account_type": "LIVE"
        },
        "Forex_Demo": {
            "path": "C:\\MT5_Farm\\Masters\\Forex_Demo",
            "magic_start": 30001,
            "magic_end": 30100,
            "risk_percent": 3.0,
            "max_daily_loss": 10.0,
            "mode": "NORMAL",
            "broker": "Forex.com",
            "account_type": "DEMO"
        },
        "Coinexx_Demo": {
            "path": "C:\\MT5_Farm\\Masters\\Coinexx_Demo",
            "magic_start": 40001,
            "magic_end": 40100,
            "risk_percent": 3.0,
            "max_daily_loss": 10.0,
            "mode": "NORMAL",
            "broker": "Coinexx",
            "account_type": "DEMO"
        },
        "Generic_Demo": {
            "path": "C:\\MT5_Farm\\Masters\\Generic_Demo",
            "magic_start": 50001,
            "magic_end": 50200,
            "risk_percent": 5.0,
            "max_daily_loss": 20.0,
            "mode": "AGGRESSIVE",
            "broker": "MetaQuotes",
            "account_type": "DEMO_AUTO"
        }
    }
    
    # Create master directories
    print("\n📁 Creating master directories...")
    for master_name, config in masters.items():
        cmd = f'New-Item -ItemType Directory -Path "{config["path"]}" -Force'
        success, stdout, stderr = execute_command(cmd)
        if success:
            print(f"   ✅ Created: {master_name}")
        
        # Create MQL5 subdirectories
        for subdir in ["\\MQL5\\Experts\\BITTEN", "\\MQL5\\Files\\BITTEN"]:
            cmd = f'New-Item -ItemType Directory -Path "{config["path"]}{subdir}" -Force'
            execute_command(cmd)
    
    # Create configuration files for each master
    print("\n📝 Creating configuration files...")
    for master_name, config in masters.items():
        # Create BITTEN config
        bitten_config = {
            "master_type": master_name,
            "broker": config["broker"],
            "account_type": config["account_type"],
            "magic_number_range": [config["magic_start"], config["magic_end"]],
            "risk_settings": {
                "risk_per_trade": config["risk_percent"],
                "max_daily_loss": config["max_daily_loss"],
                "mode": config["mode"]
            },
            "pairs": [
                "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY",
                "AUDUSD", "NZDUSD", "EURGBP", "USDCHF", "EURJPY"
            ],
            "ea_settings": {
                "trade_comment": f"BITTEN_{master_name}",
                "slippage": 3,
                "max_spread": 3.0 if "Live" in master_name else 5.0,
                "news_filter": "Live" in master_name,
                "stealth_mode": "Live" in master_name
            }
        }
        
        # Convert to JSON and encode
        config_json = json.dumps(bitten_config, indent=2)
        encoded = base64.b64encode(config_json.encode()).decode()
        
        # Write config file
        config_path = f"{config['path']}\\MQL5\\Files\\BITTEN\\master_config.json"
        cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "{config_path}" -Encoding UTF8'
        success, stdout, stderr = execute_command(cmd)
        if success:
            print(f"   ✅ Config created for: {master_name}")
    
    # Create EA initialization file for each master
    print("\n🤖 Creating EA initialization files...")
    for master_name, config in masters.items():
        ea_init = f"""
// Auto-generated initialization for {master_name}
// Risk: {config['risk_percent']}%
// Mode: {config['mode']}
// Magic: {config['magic_start']}-{config['magic_end']}

MASTER_TYPE={master_name}
RISK_PERCENT={config['risk_percent']}
MAX_DAILY_LOSS={config['max_daily_loss']}
MAGIC_START={config['magic_start']}
MAGIC_END={config['magic_end']}
TRADING_MODE={config['mode']}
"""
        
        encoded = base64.b64encode(ea_init.encode()).decode()
        init_path = f"{config['path']}\\MQL5\\Files\\BITTEN\\ea_init.txt"
        cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "{init_path}" -Encoding UTF8'
        success, stdout, stderr = execute_command(cmd)
        if success:
            print(f"   ✅ EA init created for: {master_name}")
    
    # Create cloning helper script
    print("\n🔄 Creating cloning helper script...")
    clone_script = '''
# MT5 Master Cloning Script
param(
    [string]$MasterType,
    [int]$StartIndex = 1,
    [int]$Count = 10
)

$masters = @{
    "Coinexx_Live" = "C:\\MT5_Farm\\Masters\\Coinexx_Live"
    "Forex_Live" = "C:\\MT5_Farm\\Masters\\Forex_Live"
    "Forex_Demo" = "C:\\MT5_Farm\\Masters\\Forex_Demo"
    "Coinexx_Demo" = "C:\\MT5_Farm\\Masters\\Coinexx_Demo"
    "Generic_Demo" = "C:\\MT5_Farm\\Masters\\Generic_Demo"
}

if (-not $masters.ContainsKey($MasterType)) {
    Write-Host "Invalid master type. Choose from: $($masters.Keys -join ', ')" -ForegroundColor Red
    return
}

$masterPath = $masters[$MasterType]
$clonePath = "C:\\MT5_Farm\\Clones"

Write-Host "Cloning $Count instances of $MasterType starting at index $StartIndex" -ForegroundColor Cyan

for ($i = $StartIndex; $i -lt ($StartIndex + $Count); $i++) {
    $targetPath = "$clonePath\\${MasterType}_$i"
    
    Write-Host "Creating clone $i..." -NoNewline
    
    # Copy master to clone
    Copy-Item -Path $masterPath -Destination $targetPath -Recurse -Force
    
    # Update magic number in config
    $configPath = "$targetPath\\MQL5\\Files\\BITTEN\\master_config.json"
    if (Test-Path $configPath) {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        $config.magic_number_range[0] += $i
        $config.magic_number_range[1] += $i
        $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
    }
    
    # Create unique instance ID
    $instanceId = [guid]::NewGuid().ToString()
    Set-Content -Path "$targetPath\\instance_id.txt" -Value $instanceId
    
    Write-Host " Done!" -ForegroundColor Green
}

Write-Host "Cloning complete! Created $Count clones in $clonePath" -ForegroundColor Green
'''
    
    encoded = base64.b64encode(clone_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "C:\\MT5_Farm\\clone_masters.ps1" -Encoding UTF8'
    success, stdout, stderr = execute_command(cmd)
    if success:
        print("   ✅ Cloning script created")
    
    # Summary
    print("\n" + "="*60)
    print("📊 MASTER CONFIGURATION SUMMARY")
    print("="*60)
    print("\n1. Coinexx Live: Conservative, 1% risk, Magic 10001-10100")
    print("2. Forex Live: Conservative, 1% risk, Magic 20001-20100")
    print("3. Forex Demo: Normal, 3% risk, Magic 30001-30100")
    print("4. Coinexx Demo: Normal, 3% risk, Magic 40001-40100")
    print("5. Generic Demo: Aggressive, 5% risk, Magic 50001-50200")
    print("\n📋 Next Steps:")
    print("1. Install MT5 in each master directory")
    print("2. Login to accounts (except Generic Demo)")
    print("3. Attach EA to all 10 pairs on each master")
    print("4. Test with: powershell C:\\MT5_Farm\\clone_masters.ps1 -MasterType Forex_Demo -Count 5")

if __name__ == "__main__":
    create_master_configs()