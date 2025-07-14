#!/usr/bin/env python3
"""
MT5 Instance Tracking System - Know exactly which instance is which
"""

import requests
import json
import base64
import sqlite3
from datetime import datetime
import uuid

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

def create_instance_tracking_system():
    """Create a comprehensive tracking system for all MT5 instances"""
    
    print("🔍 Creating MT5 Instance Tracking System")
    print("=" * 60)
    
    # 1. Create tracking database on Linux side
    print("\n📊 Creating tracking database...")
    conn = sqlite3.connect('/root/HydraX-v2/data/mt5_instances.db')
    cursor = conn.cursor()
    
    # Create instance tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mt5_instances (
            instance_id TEXT PRIMARY KEY,
            master_type TEXT NOT NULL,
            clone_number INTEGER,
            magic_number INTEGER UNIQUE,
            port INTEGER UNIQUE,
            directory_path TEXT,
            status TEXT DEFAULT 'inactive',
            assigned_user_id TEXT,
            assigned_tier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP,
            total_trades INTEGER DEFAULT 0,
            account_balance REAL DEFAULT 0,
            broker TEXT,
            account_type TEXT,
            notes TEXT
        )
    ''')
    
    # Create user assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_assignments (
            assignment_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            instance_id TEXT NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            tier TEXT,
            total_trades INTEGER DEFAULT 0,
            profit_loss REAL DEFAULT 0,
            FOREIGN KEY (instance_id) REFERENCES mt5_instances(instance_id)
        )
    ''')
    
    conn.commit()
    print("   ✅ Database created: /root/HydraX-v2/data/mt5_instances.db")
    
    # 2. Create instance identification files
    print("\n🏷️  Creating instance identification system...")
    
    tracking_script = '''
# MT5 Instance Identifier Script
# This creates unique identifiers for each MT5 instance

param(
    [string]$Action = "create"  # create, list, check
)

function Create-InstanceIdentifiers {
    $masters = @{
        "Coinexx_Live" = @{
            "start_port" = 9001
            "magic_start" = 10001
            "broker" = "Coinexx"
            "type" = "LIVE"
        }
        "Forex_Live" = @{
            "start_port" = 9101
            "magic_start" = 20001
            "broker" = "Forex.com"
            "type" = "LIVE"
        }
        "Forex_Demo" = @{
            "start_port" = 9201
            "magic_start" = 30001
            "broker" = "Forex.com"
            "type" = "DEMO"
        }
        "Coinexx_Demo" = @{
            "start_port" = 9301
            "magic_start" = 40001
            "broker" = "Coinexx"
            "type" = "DEMO"
        }
        "Generic_Demo" = @{
            "start_port" = 9401
            "magic_start" = 50001
            "broker" = "MetaQuotes"
            "type" = "DEMO_AUTO"
        }
    }
    
    # Process each master and its clones
    foreach ($masterType in $masters.Keys) {
        $masterInfo = $masters[$masterType]
        $masterPath = "C:\\MT5_Farm\\Masters\\$masterType"
        
        if (Test-Path $masterPath) {
            # Create identifier for master
            $instanceId = [guid]::NewGuid().ToString()
            $identifier = @{
                "instance_id" = $instanceId
                "master_type" = $masterType
                "clone_number" = 0
                "magic_number" = $masterInfo.magic_start
                "port" = $masterInfo.start_port
                "directory" = $masterPath
                "broker" = $masterInfo.broker
                "account_type" = $masterInfo.type
                "created" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            }
            
            $identifier | ConvertTo-Json | Set-Content "$masterPath\\instance_identity.json"
            Write-Host "✅ Created identity for master: $masterType" -ForegroundColor Green
        }
        
        # Process clones
        $clonePath = "C:\\MT5_Farm\\Clones"
        $clones = Get-ChildItem -Path $clonePath -Directory | Where-Object { $_.Name -like "${masterType}_*" }
        
        foreach ($clone in $clones) {
            if ($clone.Name -match "${masterType}_(\d+)") {
                $cloneNumber = [int]$matches[1]
                $instanceId = [guid]::NewGuid().ToString()
                
                $identifier = @{
                    "instance_id" = $instanceId
                    "master_type" = $masterType
                    "clone_number" = $cloneNumber
                    "magic_number" = $masterInfo.magic_start + $cloneNumber
                    "port" = $masterInfo.start_port + $cloneNumber
                    "directory" = $clone.FullName
                    "broker" = $masterInfo.broker
                    "account_type" = $masterInfo.type
                    "created" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
                }
                
                $identifier | ConvertTo-Json | Set-Content "$($clone.FullName)\\instance_identity.json"
                Write-Host "✅ Created identity for clone: $($clone.Name)" -ForegroundColor Green
            }
        }
    }
}

function List-Instances {
    Write-Host "`nMT5 Instance Directory:" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    
    $allInstances = @()
    
    # Check masters
    $masters = Get-ChildItem -Path "C:\\MT5_Farm\\Masters" -Directory
    foreach ($master in $masters) {
        $identityFile = "$($master.FullName)\\instance_identity.json"
        if (Test-Path $identityFile) {
            $identity = Get-Content $identityFile | ConvertFrom-Json
            $allInstances += $identity
        }
    }
    
    # Check clones
    $clones = Get-ChildItem -Path "C:\\MT5_Farm\\Clones" -Directory
    foreach ($clone in $clones) {
        $identityFile = "$($clone.FullName)\\instance_identity.json"
        if (Test-Path $identityFile) {
            $identity = Get-Content $identityFile | ConvertFrom-Json
            $allInstances += $identity
        }
    }
    
    # Display in table format
    $allInstances | Sort-Object master_type, clone_number | Format-Table -Property @(
        @{Label="Type"; Expression={$_.master_type}},
        @{Label="Clone#"; Expression={$_.clone_number}},
        @{Label="Magic"; Expression={$_.magic_number}},
        @{Label="Port"; Expression={$_.port}},
        @{Label="Broker"; Expression={$_.broker}},
        @{Label="Account"; Expression={$_.account_type}},
        @{Label="Instance ID"; Expression={$_.instance_id.Substring(0,8) + "..."}}
    )
    
    Write-Host "`nTotal Instances: $($allInstances.Count)" -ForegroundColor Yellow
}

# Execute based on action
switch ($Action) {
    "create" { Create-InstanceIdentifiers }
    "list" { List-Instances }
    default { Write-Host "Invalid action. Use: create, list" -ForegroundColor Red }
}
'''
    
    # Deploy the tracking script
    encoded = base64.b64encode(tracking_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "C:\\MT5_Farm\\instance_tracker.ps1" -Encoding UTF8'
    success, stdout, stderr = execute_command(cmd)
    if success:
        print("   ✅ Tracking script deployed")
    
    # 3. Create visual identification system
    print("\n🎨 Creating visual identification helpers...")
    
    visual_id_script = '''
# Create visual identifiers for each MT5 instance
# This adds desktop shortcuts and window titles

function Create-VisualIdentifiers {
    $instances = Get-ChildItem -Path "C:\\MT5_Farm" -Filter "instance_identity.json" -Recurse
    
    foreach ($instanceFile in $instances) {
        $identity = Get-Content $instanceFile.FullName | ConvertFrom-Json
        $dir = Split-Path $instanceFile.FullName -Parent
        
        # Create desktop shortcut with clear name
        $shortcutName = "$($identity.master_type)_$($identity.clone_number)_M$($identity.magic_number)"
        $shortcut = "$env:USERPROFILE\\Desktop\\MT5_$shortcutName.lnk"
        
        $shell = New-Object -ComObject WScript.Shell
        $link = $shell.CreateShortcut($shortcut)
        $link.TargetPath = "$dir\\terminal64.exe"
        $link.Arguments = "/portable /config:$dir"
        $link.WorkingDirectory = $dir
        $link.IconLocation = "$dir\\terminal64.exe"
        $link.Description = "MT5 $($identity.master_type) Clone $($identity.clone_number) Magic $($identity.magic_number)"
        $link.Save()
        
        # Create startup config that sets window title
        $startupConfig = @"
[Server]
Name=$($identity.broker) [$($identity.master_type)_$($identity.clone_number)]
[StartUp]
WindowTitle=MT5 $($identity.master_type) #$($identity.clone_number) M$($identity.magic_number)
"@
        $startupConfig | Set-Content "$dir\\config\\startup.ini"
        
        Write-Host "✅ Visual ID created for: $shortcutName" -ForegroundColor Green
    }
}

Create-VisualIdentifiers
'''
    
    encoded = base64.b64encode(visual_id_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "C:\\MT5_Farm\\create_visual_ids.ps1" -Encoding UTF8'
    execute_command(cmd)
    
    # 4. Create monitoring dashboard
    print("\n📊 Creating monitoring dashboard...")
    
    monitor_script = '''
# MT5 Instance Monitor Dashboard
Clear-Host
while ($true) {
    Clear-Host
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                    MT5 INSTANCE MONITOR                         " -ForegroundColor Yellow
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Get all running MT5 processes
    $mt5Processes = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
    
    Write-Host "Running MT5 Instances: $($mt5Processes.Count)" -ForegroundColor Green
    Write-Host ""
    
    # Check each instance
    $instances = Get-ChildItem -Path "C:\\MT5_Farm" -Filter "instance_identity.json" -Recurse
    
    $runningInstances = @()
    $inactiveInstances = @()
    
    foreach ($instanceFile in $instances) {
        $identity = Get-Content $instanceFile.FullName | ConvertFrom-Json
        $dir = Split-Path $instanceFile.FullName -Parent
        
        # Check if terminal is running from this directory
        $isRunning = $false
        foreach ($proc in $mt5Processes) {
            try {
                if ($proc.Path -like "*$dir*") {
                    $isRunning = $true
                    break
                }
            } catch {}
        }
        
        # Check for recent activity
        $statusFile = "$dir\\MQL5\\Files\\BITTEN\\bitten_status_secure.txt"
        $lastActivity = "Never"
        if (Test-Path $statusFile) {
            $lastMod = (Get-Item $statusFile).LastWriteTime
            $lastActivity = $lastMod.ToString("HH:mm:ss")
        }
        
        $instanceInfo = [PSCustomObject]@{
            Type = $identity.master_type
            Clone = $identity.clone_number
            Magic = $identity.magic_number
            Port = $identity.port
            Status = if ($isRunning) { "RUNNING" } else { "STOPPED" }
            LastActivity = $lastActivity
            StatusColor = if ($isRunning) { "Green" } else { "Red" }
        }
        
        if ($isRunning) {
            $runningInstances += $instanceInfo
        } else {
            $inactiveInstances += $instanceInfo
        }
    }
    
    # Display running instances
    if ($runningInstances.Count -gt 0) {
        Write-Host "ACTIVE INSTANCES:" -ForegroundColor Green
        Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
        $runningInstances | Format-Table -Property Type, Clone, Magic, Port, LastActivity -AutoSize
    }
    
    # Display inactive instances
    if ($inactiveInstances.Count -gt 0) {
        Write-Host "`nINACTIVE INSTANCES:" -ForegroundColor Red
        Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
        $inactiveInstances | Select-Object -First 10 | Format-Table -Property Type, Clone, Magic, Port -AutoSize
        if ($inactiveInstances.Count -gt 10) {
            Write-Host "... and $($inactiveInstances.Count - 10) more inactive" -ForegroundColor Gray
        }
    }
    
    Write-Host "`nPress Ctrl+C to exit" -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
'''
    
    encoded = base64.b64encode(monitor_script.encode()).decode()
    cmd = f'[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{encoded}")) | Out-File -FilePath "C:\\MT5_Farm\\monitor_dashboard.ps1" -Encoding UTF8'
    execute_command(cmd)
    
    # 5. Create instance management functions
    print("\n🛠️  Creating instance management functions...")
    
    # Save Python management functions
    management_code = '''
def get_available_instance(master_type, tier):
    """Get an available MT5 instance for a user"""
    conn = sqlite3.connect('/root/HydraX-v2/data/mt5_instances.db')
    cursor = conn.cursor()
    
    # Find available instance
    cursor.execute("""
        SELECT instance_id, magic_number, port, directory_path 
        FROM mt5_instances 
        WHERE master_type = ? 
        AND assigned_user_id IS NULL 
        AND status = 'active'
        LIMIT 1
    """, (master_type,))
    
    instance = cursor.fetchone()
    conn.close()
    return instance

def assign_instance_to_user(user_id, tier):
    """Assign appropriate MT5 instance to user based on tier"""
    instance_map = {
        "PRESS_PASS": "Generic_Demo",
        "NIBBLER": "Forex_Demo",
        "FANG": "Forex_Demo",
        "COMMANDER": "Forex_Live",
        "APEX": "Coinexx_Live"
    }
    
    master_type = instance_map.get(tier, "Forex_Demo")
    instance = get_available_instance(master_type, tier)
    
    if instance:
        # Update assignment
        conn = sqlite3.connect('/root/HydraX-v2/data/mt5_instances.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE mt5_instances 
            SET assigned_user_id = ?, assigned_tier = ?, last_active = CURRENT_TIMESTAMP
            WHERE instance_id = ?
        """, (user_id, tier, instance[0]))
        conn.commit()
        conn.close()
        
        return {
            "instance_id": instance[0],
            "magic_number": instance[1],
            "port": instance[2],
            "directory": instance[3]
        }
    return None
'''
    
    with open('/root/HydraX-v2/src/bitten_core/mt5_instance_manager.py', 'w') as f:
        f.write(management_code)
    
    print("   ✅ Management functions created")
    
    # Summary
    print("\n" + "="*60)
    print("🎯 MT5 INSTANCE TRACKING SYSTEM CREATED")
    print("="*60)
    
    print("\n📋 How to Identify Instances:")
    print("\n1. **By Magic Number**:")
    print("   - Coinexx Live: 10001-10100")
    print("   - Forex Live: 20001-20100")
    print("   - Forex Demo: 30001-30100")
    print("   - Coinexx Demo: 40001-40100")
    print("   - Generic Demo: 50001-50200")
    
    print("\n2. **By Port Number**:")
    print("   - Coinexx Live: 9001-9100")
    print("   - Forex Live: 9101-9200")
    print("   - Forex Demo: 9201-9300")
    print("   - Coinexx Demo: 9301-9400")
    print("   - Generic Demo: 9401-9600")
    
    print("\n3. **By Directory**:")
    print("   - Masters: C:\\MT5_Farm\\Masters\\{Type}")
    print("   - Clones: C:\\MT5_Farm\\Clones\\{Type}_{Number}")
    
    print("\n4. **By Window Title**:")
    print("   - Format: 'MT5 {Type} #{Clone} M{Magic}'")
    print("   - Example: 'MT5 Forex_Demo #5 M30005'")
    
    print("\n5. **By Instance ID**:")
    print("   - Unique GUID in instance_identity.json")
    print("   - Tracked in database for assignments")
    
    print("\n🔧 Management Commands:")
    print("   - Create IDs: powershell C:\\MT5_Farm\\instance_tracker.ps1 -Action create")
    print("   - List all: powershell C:\\MT5_Farm\\instance_tracker.ps1 -Action list")
    print("   - Monitor: powershell C:\\MT5_Farm\\monitor_dashboard.ps1")
    print("   - Visual IDs: powershell C:\\MT5_Farm\\create_visual_ids.ps1")

if __name__ == "__main__":
    create_instance_tracking_system()