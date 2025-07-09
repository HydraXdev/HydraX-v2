#!/usr/bin/env python3
import requests
import json

agent_url = "http://3.145.84.187:5555"

print("=== MT5 LIVE STATUS CHECK ===\n")

# Check running MT5 processes
cmd = '''
$processes = Get-Process | Where-Object {$_.ProcessName -like "*terminal*"}
if ($processes) {
    $processes | Format-Table ProcessName, Id, StartTime, CPU -AutoSize
    Write-Host "`nTotal MT5 instances running: $($processes.Count)" -ForegroundColor Green
} else {
    Write-Host "No MT5 instances currently running!" -ForegroundColor Red
}

# Check if EA files are in place
Write-Host "`nChecking EA deployments..." -ForegroundColor Cyan
$eaFiles = Get-ChildItem -Path "C:\\MT5_Farm\\Masters\\*\\MQL5\\Experts\\BITTENBridge*.mq5" -ErrorAction SilentlyContinue
if ($eaFiles) {
    Write-Host "Found $($eaFiles.Count) EA deployments" -ForegroundColor Green
    $eaFiles | ForEach-Object { Write-Host "  - $($_.FullName)" }
}

# Check command/response folders
Write-Host "`nChecking communication folders..." -ForegroundColor Cyan
$cmdFolders = Get-ChildItem -Path "C:\\MT5_Farm\\Commands" -Directory -ErrorAction SilentlyContinue
$respFolders = Get-ChildItem -Path "C:\\MT5_Farm\\Responses" -Directory -ErrorAction SilentlyContinue

Write-Host "Command folders: $($cmdFolders.Count)"
Write-Host "Response folders: $($respFolders.Count)"
'''

try:
    resp = requests.post(f"{agent_url}/execute", 
                        json={"command": cmd, "powershell": True},
                        timeout=30)
    result = resp.json()
    if 'stdout' in result:
        print(result['stdout'])
except Exception as e:
    print(f"Error: {e}")

# Check local signal database
import os
import sqlite3

db_path = "/root/HydraX-v2/data/live_market.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for recent ticks
    cursor.execute("SELECT COUNT(*) FROM live_ticks WHERE timestamp > datetime('now', '-5 minutes')")
    recent_ticks = cursor.fetchone()[0]
    
    # Check for signals
    cursor.execute("SELECT COUNT(*) FROM live_signals")
    total_signals = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n=== LOCAL DATABASE STATUS ===")
    print(f"Recent ticks (last 5 min): {recent_ticks}")
    print(f"Total live signals generated: {total_signals}")
else:
    print("\n❌ Live market database not found!")

print("\n=== NEXT STEPS ===")
print("1. Launch MT5 instances on Windows if not running")
print("2. Load EA in each MT5 and attach to charts")
print("3. Configure the 8 BITTEN pairs in each instance")
print("4. Start bridge monitors to forward data")