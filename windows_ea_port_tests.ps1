#!/usr/bin/env powershell
<#
🪟 WINDOWS VPS EA PORT TESTING SCRIPT
Tests EA ZMQ port binding and Windows firewall status
Run this on Windows VPS where MT5 EA is running
#>

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "🪟 WINDOWS VPS EA PORT TESTING" -ForegroundColor Cyan
Write-Host "Testing EA v7.01 ZMQ port binding and connectivity" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Based on actual EA source code analysis:
# BACKEND_ENDPOINT   = "tcp://134.199.204.67:5555" (EA connects TO this)
# HEARTBEAT_ENDPOINT = "tcp://134.199.204.67:5556" (EA connects TO this)

Write-Host ""
Write-Host "📡 PHASE 1: EA PORT BINDING VERIFICATION" -ForegroundColor Yellow

# Check if EA is connected to Linux server ports
Write-Host ""
Write-Host "🔍 Checking EA connections to Linux server..." -ForegroundColor Green

# Port 5555 - Fire commands FROM Linux TO EA
Write-Host "Testing port 5555 (Fire Commands):" -ForegroundColor White
netstat -ano | findstr :5555

# Port 5556 - Market data TO Linux FROM EA
Write-Host "Testing port 5556 (Market Data Upload):" -ForegroundColor White
netstat -ano | findstr :5556

# Additional ports that might be used
Write-Host "Testing port 5557 (Signal Publishing):" -ForegroundColor White
netstat -ano | findstr :5557

Write-Host "Testing port 5558 (Trade Confirmations):" -ForegroundColor White
netstat -ano | findstr :5558

Write-Host "Testing port 5560 (Market Data Relay):" -ForegroundColor White
netstat -ano | findstr :5560

Write-Host ""
Write-Host "📋 PHASE 2: MT5 PROCESS VERIFICATION" -ForegroundColor Yellow

# Check MT5 terminal is running
Write-Host ""
Write-Host "🔍 Checking MT5 terminal processes..." -ForegroundColor Green
Get-Process | Where-Object {$_.ProcessName -like "*terminal*"} | Format-Table ProcessName, Id, CPU, WorkingSet -AutoSize

# Check for Expert Advisors
Write-Host ""
Write-Host "🔍 Checking for EA log files..." -ForegroundColor Green
Get-ChildItem -Path "C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal*\MQL5\Logs" -ErrorAction SilentlyContinue | Select-Object Name, LastWriteTime

Write-Host ""
Write-Host "🔧 PHASE 3: WINDOWS FIREWALL STATUS" -ForegroundColor Yellow

# Check Windows Firewall status
Write-Host ""
Write-Host "🔍 Checking Windows Firewall status..." -ForegroundColor Green
Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table -AutoSize

# Check for BITTEN firewall rules
Write-Host ""
Write-Host "🔍 Checking BITTEN firewall rules..." -ForegroundColor Green
Get-NetFirewallRule -DisplayName "*BITTEN*" -ErrorAction SilentlyContinue | Select-Object DisplayName, Direction, Action, Enabled | Format-Table -AutoSize

# Check for ZMQ port rules
Write-Host ""
Write-Host "🔍 Checking ZMQ port firewall rules..." -ForegroundColor Green
Get-NetFirewallRule | Where-Object {$_.DisplayName -match "555[5-8]"} | Select-Object DisplayName, Direction, Action, Enabled | Format-Table -AutoSize

Write-Host ""
Write-Host "⚡ PHASE 4: CONNECTIVITY TEST TO LINUX SERVER" -ForegroundColor Yellow

# Test connectivity to Linux control server
$LinuxServer = "134.199.204.67"
Write-Host ""
Write-Host "🔍 Testing connectivity to Linux server $LinuxServer..." -ForegroundColor Green

# Test each ZMQ port
$ZMQPorts = @(5555, 5556, 5557, 5558, 5560)
foreach ($port in $ZMQPorts) {
    Write-Host "Testing port $port..." -NoNewline -ForegroundColor White
    try {
        $connection = Test-NetConnection -ComputerName $LinuxServer -Port $port -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-Host " ✅ REACHABLE" -ForegroundColor Green
        } else {
            Write-Host " ❌ BLOCKED" -ForegroundColor Red
        }
    } catch {
        Write-Host " ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🛡️ PHASE 5: FIREWALL RULE CREATION (IF NEEDED)" -ForegroundColor Yellow

Write-Host ""
Write-Host "To create firewall rules if needed, run these commands:" -ForegroundColor Green
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5555-IN' -Direction Inbound -Protocol TCP -LocalPort 5555 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5556-IN' -Direction Inbound -Protocol TCP -LocalPort 5556 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5557-IN' -Direction Inbound -Protocol TCP -LocalPort 5557 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5558-IN' -Direction Inbound -Protocol TCP -LocalPort 5558 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5560-IN' -Direction Inbound -Protocol TCP -LocalPort 5560 -Action Allow" -ForegroundColor Cyan

Write-Host ""
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5555-OUT' -Direction Outbound -Protocol TCP -RemotePort 5555 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5556-OUT' -Direction Outbound -Protocol TCP -RemotePort 5556 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5557-OUT' -Direction Outbound -Protocol TCP -RemotePort 5557 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5558-OUT' -Direction Outbound -Protocol TCP -RemotePort 5558 -Action Allow" -ForegroundColor Cyan
Write-Host "New-NetFirewallRule -DisplayName 'BITTEN-5560-OUT' -Direction Outbound -Protocol TCP -RemotePort 5560 -Action Allow" -ForegroundColor Cyan

Write-Host ""
Write-Host "📊 PHASE 6: EA HEARTBEAT VERIFICATION" -ForegroundColor Yellow

Write-Host ""
Write-Host "🔍 Checking for EA heartbeat activity..." -ForegroundColor Green
Write-Host "Look for these patterns in MT5 Experts log:" -ForegroundColor White
Write-Host "  - '✅ Connected to backend controller'" -ForegroundColor Cyan
Write-Host "  - '💓 Heartbeat sent every 5 seconds'" -ForegroundColor Cyan
Write-Host "  - '📥 Received from ZMQ: {...}'" -ForegroundColor Cyan
Write-Host "  - No 'ERROR: Failed to connect' messages" -ForegroundColor Cyan

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "✅ WINDOWS EA PORT TESTING COMPLETE" -ForegroundColor Green
Write-Host "Report findings to Linux server for next phase testing" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan