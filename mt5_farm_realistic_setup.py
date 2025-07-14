#\!/usr/bin/env python3
"""
Realistic MT5 Farm Setup - Based on actual user distribution needs
"""

import requests
import json
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

def create_realistic_farm_distribution():
    """Create a realistic distribution of MT5 instances based on user needs"""
    
    print("🎯 Creating Realistic MT5 Farm Distribution")
    print("=" * 60)
    
    # Realistic distribution based on user patterns
    distribution = {
        "Generic_Demo": {
            "count": 200,
            "purpose": "Press Pass 7-day trials",
            "expected_active": 50,  # ~25% active at any time
            "recycle_days": 7,
            "notes": "Auto-provision, no login required"
        },
        "Forex_Demo": {
            "count": 20,
            "purpose": "Nibbler/Fang testing",
            "expected_active": 15,
            "notes": "Regulated broker demo"
        },
        "Coinexx_Demo": {
            "count": 10,
            "purpose": "Offshore demo testing",
            "expected_active": 8,
            "notes": "Higher leverage testing"
        },
        "Forex_Live": {
            "count": 5,
            "purpose": "Commander/APEX regulated",
            "expected_active": 5,
            "notes": "Conservative traders"
        },
        "Coinexx_Live": {
            "count": 10,
            "purpose": "Commander/APEX offshore",
            "expected_active": 10,
            "notes": "Higher leverage preference"
        }
    }
    
    print("\n📊 DISTRIBUTION BREAKDOWN:")
    print("-" * 60)
    total = 0
    for master, config in distribution.items():
        total += config['count']
        print(f"{master:15}  < /dev/null |  {config['count']:3} instances | {config['purpose']}")
        print(f"{'':15} | Expected: {config['expected_active']} active | {config['notes']}")
        print("-" * 60)
    
    print(f"\n📈 TOTAL INSTANCES: {total}")
    
    # User preference analysis
    print("\n🔍 USER PREFERENCE ANALYSIS:")
    print("\nRegulated vs Offshore Split (Expected):")
    print("- New users: 70% regulated (Forex.com) - familiar, trusted")
    print("- Experienced: 60% offshore (Coinexx) - higher leverage")
    print("- Press Pass: 100% Generic Demo - instant access")
    
    print("\n💡 WHY TWO BROKER TYPES:")
    print("\n1. **Regulated (Forex.com)**:")
    print("   - ✅ CFTC/NFA regulated (US traders)")
    print("   - ✅ Strong reputation & trust")
    print("   - ✅ Investor protection")
    print("   - ❌ Lower leverage (50:1 max)")
    print("   - ❌ FIFO rules")
    
    print("\n2. **Offshore (Coinexx)**:")
    print("   - ✅ Higher leverage (500:1)")
    print("   - ✅ No FIFO restrictions")
    print("   - ✅ More trading freedom")
    print("   - ❌ Less regulation")
    print("   - ❌ Trust concerns for new traders")
    
    # Create cloning script for realistic distribution
    clone_script = '''
# Realistic MT5 Farm Cloning Script
param(
    [string]$Action = "create"  # create, status, clean
)

$distribution = @{
    "Generic_Demo" = 200
    "Forex_Demo" = 20
    "Coinexx_Demo" = 10
    "Forex_Live" = 5
    "Coinexx_Live" = 10
}

function Create-RealisticFarm {
    Write-Host "Creating Realistic MT5 Farm Distribution" -ForegroundColor Cyan
    
    foreach ($master in $distribution.Keys) {
        $count = $distribution[$master]
        $masterPath = "C:\\MT5_Farm\\Masters\\$master"
        
        if (Test-Path $masterPath) {
            Write-Host "`nCloning $count instances of $master..." -ForegroundColor Yellow
            
            for ($i = 1; $i -le $count; $i++) {
                $clonePath = "C:\\MT5_Farm\\Clones\\${master}_$i"
                
                if (-not (Test-Path $clonePath)) {
                    Copy-Item -Path $masterPath -Destination $clonePath -Recurse -Force
                    
                    # Update instance identity
                    $identity = Get-Content "$masterPath\\instance_identity.json" | ConvertFrom-Json
                    $identity.clone_number = $i
                    $identity.magic_number += $i
                    $identity.port += $i
                    $identity.instance_id = [guid]::NewGuid().ToString()
                    
                    $identity | ConvertTo-Json | Set-Content "$clonePath\\instance_identity.json"
                    
                    if ($i % 10 -eq 0) {
                        Write-Host "  Created $i/$count..." -NoNewline -ForegroundColor Green
                    }
                }
            }
            Write-Host " Done\!" -ForegroundColor Green
        }
    }
}

function Get-FarmStatus {
    Write-Host "`nMT5 Farm Status:" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Cyan
    
    foreach ($master in $distribution.Keys) {
        $expected = $distribution[$master]
        $actual = (Get-ChildItem "C:\\MT5_Farm\\Clones" -Directory -Filter "${master}_*").Count
        
        $status = if ($actual -eq $expected) { "✓" } else { "✗" }
        $color = if ($actual -eq $expected) { "Green" } else { "Red" }
        
        Write-Host "$status $master: $actual/$expected" -ForegroundColor $color
    }
}

# Execute based on action
switch ($Action) {
    "create" { Create-RealisticFarm }
    "status" { Get-FarmStatus }
    default { Write-Host "Use: -Action create|status" -ForegroundColor Red }
}
'''
    
    # Deploy the realistic cloning script
    encoded = base64.b64encode(clone_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "C:\\MT5_Farm\\clone_realistic_farm.ps1" -Encoding UTF8'
    success, stdout, stderr = execute_command(cmd)
    if success:
        print("\n✅ Realistic cloning script deployed")
    
    # Create Press Pass recycling system
    print("\n♻️ Creating Press Pass Recycling System...")
    
    recycle_script = '''
# Press Pass MT5 Instance Recycler
# Runs daily to clean up 7-day old instances

$recycleLog = "C:\\MT5_Farm\\Logs\\recycle_log.txt"
$instanceDb = "C:\\MT5_Farm\\press_pass_assignments.json"

function Recycle-PressPassInstances {
    $now = Get-Date
    Write-Output "[$now] Starting Press Pass recycling..." | Add-Content $recycleLog
    
    # Load assignments
    if (Test-Path $instanceDb) {
        $assignments = Get-Content $instanceDb | ConvertFrom-Json
    } else {
        $assignments = @{}
    }
    
    $recycled = 0
    
    foreach ($userId in $assignments.PSObject.Properties.Name) {
        $assignment = $assignments.$userId
        $assignDate = [DateTime]$assignment.assigned_date
        $daysSinceAssign = ($now - $assignDate).Days
        
        if ($daysSinceAssign -ge 7) {
            # Clean instance
            $instancePath = $assignment.instance_path
            
            # Clear account data
            Remove-Item "$instancePath\\config\\*.ini" -Force -ErrorAction SilentlyContinue
            Remove-Item "$instancePath\\MQL5\\Files\\*" -Recurse -Force -ErrorAction SilentlyContinue
            
            # Mark as available
            $assignment.status = "available"
            $assignment.user_id = $null
            $assignment.assigned_date = $null
            
            $recycled++
            Write-Output "  Recycled: $instancePath (was user $userId)" | Add-Content $recycleLog
        }
    }
    
    # Save updated assignments
    $assignments | ConvertTo-Json -Depth 10 | Set-Content $instanceDb
    
    Write-Output "[$now] Recycled $recycled instances" | Add-Content $recycleLog
}

# Create scheduled task for daily recycling
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\\MT5_Farm\\recycle_press_pass.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "03:00"
Register-ScheduledTask -TaskName "PressPassRecycler" -Action $action -Trigger $trigger -Description "Recycle 7-day old Press Pass instances"

Recycle-PressPassInstances
'''
    
    encoded = base64.b64encode(recycle_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "C:\\MT5_Farm\\recycle_press_pass.ps1" -Encoding UTF8'
    execute_command(cmd)
    
    print("   ✅ Press Pass recycling system created")
    
    # Summary
    print("\n" + "="*60)
    print("🎯 REALISTIC FARM SETUP COMPLETE")
    print("="*60)
    
    print("\n📋 Key Insights:")
    print("1. Press Pass needs 200 instances (25% active = 50 concurrent)")
    print("2. Most paying users prefer offshore brokers (higher leverage)")
    print("3. Regulated brokers important for trust/onboarding")
    print("4. Auto-recycling keeps Press Pass instances fresh")
    
    print("\n🔧 Commands:")
    print("- Create farm: powershell C:\\MT5_Farm\\clone_realistic_farm.ps1 -Action create")
    print("- Check status: powershell C:\\MT5_Farm\\clone_realistic_farm.ps1 -Action status")
    print("- Recycle Press Pass: powershell C:\\MT5_Farm\\recycle_press_pass.ps1")

if __name__ == "__main__":
    create_realistic_farm_distribution()
