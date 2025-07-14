#!/usr/bin/env python3
"""
EA Setup Helper - Does everything possible remotely to prepare EA
"""

import requests
import json
import time
import base64

AWS_SERVER = "3.145.84.187"
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

def setup_ea_infrastructure():
    """Set up everything possible for EA remotely"""
    
    print("🤖 EA Remote Setup Assistant")
    print("=" * 60)
    
    # Step 1: Check MT5 installations
    print("\n📊 Step 1: Checking MT5 installations...")
    mt5_paths = [
        "C:\\Program Files\\MetaTrader 5",
        "C:\\Program Files\\FOREX.com US",
        "C:\\Program Files\\Coinexx MT5 Terminal",
        "C:\\MT5_Farm\\Masters\\Forex_Demo",
        "C:\\MT5_Farm\\Masters\\Forex_Live"
    ]
    
    found_mt5 = []
    for path in mt5_paths:
        success, stdout, stderr = execute_command(f'Test-Path "{path}"')
        if success and stdout.strip() == "True":
            print(f"   ✅ Found: {path}")
            found_mt5.append(path)
        else:
            print(f"   ❌ Not found: {path}")
    
    if not found_mt5:
        print("\n⚠️  No MT5 installations found! You need to install MT5 manually.")
        return
    
    # Step 2: Create EA directories for each MT5
    print("\n📁 Step 2: Creating EA directories...")
    for mt5_path in found_mt5:
        ea_dir = f'"{mt5_path}\\MQL5\\Experts\\BITTEN"'
        files_dir = f'"{mt5_path}\\MQL5\\Files\\BITTEN"'
        
        for directory in [ea_dir, files_dir]:
            cmd = f'New-Item -ItemType Directory -Path {directory} -Force'
            success, stdout, stderr = execute_command(cmd)
            if success:
                print(f"   ✅ Created: {directory}")
    
    # Step 3: Deploy EA file
    print("\n📤 Step 3: Deploying EA file...")
    ea_content = """
// BITTENBridge EA Simplified Installer
#property copyright "BITTEN Trading System"
#property version   "3.0"

// This is a placeholder that will help with setup
int OnInit() {
    Print("BITTEN Bridge EA - Please compile the full version");
    Comment("BITTEN Bridge EA\\nPlease compile BITTENBridge_v3_ENHANCED.mq5");
    
    // Create necessary files
    int handle = FileOpen("BITTEN/setup_status.txt", FILE_WRITE|FILE_TXT);
    if(handle != INVALID_HANDLE) {
        FileWrite(handle, "EA deployed. Please compile full version.");
        FileClose(handle);
    }
    
    return(INIT_SUCCEEDED);
}

void OnTick() {
    static datetime last_message = 0;
    if(TimeCurrent() - last_message > 60) {
        Print("Waiting for full EA compilation...");
        last_message = TimeCurrent();
    }
}
"""
    
    # Encode and deploy
    encoded_ea = base64.b64encode(ea_content.encode()).decode()
    for mt5_path in found_mt5:
        ea_path = f"{mt5_path}\\MQL5\\Experts\\BITTEN\\BITTENBridge_Setup.mq5"
        cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded_ea}")) | Out-File -FilePath "{ea_path}" -Encoding UTF8'
        success, stdout, stderr = execute_command(cmd)
        if success:
            print(f"   ✅ Deployed to: {ea_path}")
    
    # Step 4: Create instruction files
    print("\n📝 Step 4: Creating instruction files...")
    instructions = {
        "bitten_instructions_secure.txt": "READY|Waiting for trades",
        "bitten_status_secure.txt": "INITIALIZED|0|0|0",
        "bitten_account_secure.txt": "10000.00|1000.00|0.00",
        "bitten_positions_secure.txt": "",
        "bitten_results_secure.txt": ""
    }
    
    for filename, content in instructions.items():
        for mt5_path in found_mt5:
            file_path = f"{mt5_path}\\MQL5\\Files\\BITTEN\\{filename}"
            cmd = f'Set-Content -Path "{file_path}" -Value "{content}"'
            success, stdout, stderr = execute_command(cmd)
            if success:
                print(f"   ✅ Created: {filename}")
    
    # Step 5: Check if MT5 is running
    print("\n🔍 Step 5: Checking if MT5 terminals are running...")
    success, stdout, stderr = execute_command('Get-Process | Where-Object {$_.ProcessName -like "*terminal*"} | Select-Object ProcessName, Id')
    if success and stdout.strip():
        print("   ✅ MT5 terminals are running:")
        print(stdout)
    else:
        print("   ❌ No MT5 terminals running")
        
        # Try to start MT5
        print("\n🚀 Attempting to start MT5...")
        for mt5_path in found_mt5:
            terminal_exe = f'"{mt5_path}\\terminal64.exe"'
            cmd = f'Start-Process {terminal_exe} -ArgumentList "/portable"'
            success, stdout, stderr = execute_command(cmd)
            if success:
                print(f"   ✅ Started: {terminal_exe}")
                break
    
    # Step 6: Create auto-start task
    print("\n⏰ Step 6: Creating auto-start task for MT5...")
    if found_mt5:
        mt5_exe = f"{found_mt5[0]}\\terminal64.exe"
        cmd = f'schtasks /CREATE /SC ONLOGON /TN "MT5AutoStart" /TR "{mt5_exe} /portable" /F /RL HIGHEST'
        success, stdout, stderr = execute_command(cmd)
        if success:
            print("   ✅ Created auto-start task")
    
    # Step 7: Instructions for manual steps
    print("\n" + "="*60)
    print("📋 MANUAL STEPS REQUIRED:")
    print("="*60)
    print("\n1. On the Windows server, open MT5 terminal")
    print("\n2. Login to your broker account:")
    print("   - File → Login to Trade Account")
    print("   - Enter credentials")
    print("\n3. Open MetaEditor (F4 or Tools → MetaEditor)")
    print("\n4. In MetaEditor:")
    print("   - File → Open → Navigate to Experts/BITTEN")
    print("   - Open BITTENBridge_v3_ENHANCED.mq5")
    print("   - Compile (F7)")
    print("   - Check for errors in the bottom panel")
    print("\n5. In MT5 terminal:")
    print("   - Open charts for your pairs (drag from Market Watch)")
    print("   - From Navigator, drag EA to each chart")
    print("   - In EA settings dialog:")
    print("     - Enable 'Allow live trading'")
    print("     - Set appropriate risk settings")
    print("     - Click OK")
    print("\n6. Enable AutoTrading button (or Ctrl+E)")
    print("\n7. Check the Experts tab for EA messages")
    print("\n" + "="*60)
    
    # Step 8: Monitoring setup
    print("\n📊 Setting up monitoring...")
    monitor_script = '''
# BITTEN EA Monitor
while($true) {
    Clear-Host
    Write-Host "BITTEN EA Monitor" -ForegroundColor Cyan
    Write-Host ("Time: " + (Get-Date)) -ForegroundColor Yellow
    Write-Host ""
    
    # Check for EA files
    $files = Get-ChildItem -Path "C:\\*\\MQL5\\Files\\BITTEN\\*.txt" -Recurse -ErrorAction SilentlyContinue
    foreach($file in $files) {
        Write-Host $file.Name -ForegroundColor Green
        Get-Content $file.FullName | Select-Object -First 5
        Write-Host ""
    }
    
    Start-Sleep -Seconds 5
}
'''
    
    encoded_monitor = base64.b64encode(monitor_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded_monitor}")) | Out-File -FilePath "C:\\BITTEN_Agent\\monitor_ea.ps1" -Encoding UTF8'
    success, stdout, stderr = execute_command(cmd)
    if success:
        print("   ✅ Created EA monitor script")
        print("   Run: powershell C:\\BITTEN_Agent\\monitor_ea.ps1")

if __name__ == "__main__":
    setup_ea_infrastructure()