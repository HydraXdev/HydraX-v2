#!/usr/bin/env python3
"""
Check MT5 Farm Live Status and Data Flow
"""
import requests
import json
import time

agent_url = "http://localhost:5555"

def execute_ps(command):
    resp = requests.post(f"{agent_url}/execute", 
                        json={"command": command, "powershell": True},
                        timeout=30)
    return resp.json()

print("=== MT5 FARM LIVE STATUS CHECK ===\n")

# Check if any MT5 instances are running
print("Checking running MT5 instances...")
cmd = '''
Get-Process | Where-Object {$_.ProcessName -like "*terminal*"} | Select-Object ProcessName, Id, StartTime | Format-Table
'''
result = execute_ps(cmd)
if 'stdout' in result and result['stdout'].strip():
    print("Running MT5 processes:")
    print(result['stdout'])
else:
    print("❌ No MT5 instances currently running!")

# Check EA files
print("\nChecking deployed EAs...")
cmd = '''
Get-ChildItem -Path "C:\\MT5_Farm\\Masters\\*\\MQL5\\Experts\\*.mq5" -Recurse | Select-Object Directory, Name | Format-Table
'''
result = execute_ps(cmd)
if 'stdout' in result:
    print(result['stdout'])

# Check for data folders (indicates MT5 has been launched)
print("\nChecking MT5 data folders...")
cmd = '''
$masters = @("Forex_Live", "Coinexx_Live", "Forex_Demo", "Generic_Demo")
foreach ($master in $masters) {
    $dataPath = "C:\\MT5_Farm\\Masters\\$master\\MQL5\\Files"
    if (Test-Path $dataPath) {
        Write-Host "$master - Data folder exists" -ForegroundColor Green
    } else {
        Write-Host "$master - Not initialized yet" -ForegroundColor Yellow
    }
}
'''
result = execute_ps(cmd)
if 'stdout' in result:
    print(result['stdout'])

print("\n=== CHECKING BITTEN SIGNAL SYSTEM ===")

# Check local signal system status
import os
import subprocess

# Check if fake signal generator is running
try:
    ps_output = subprocess.check_output(['ps', 'aux'], text=True)
    if 'signal_generator.py' in ps_output or 'generate_signals' in ps_output:
        print("⚠️  Fake signal generator is RUNNING - needs to be stopped!")
    else:
        print("✓ Fake signal generator is not running")
except:
    pass

# Check webapp status
try:
    webapp_resp = requests.get("http://localhost:8888/health", timeout=2)
    print("✓ WebApp is running on port 8888")
except:
    print("❌ WebApp is not running on port 8888")

# Check current signal configuration
signal_config_path = "/root/HydraX-v2/config/signal_config.json"
if os.path.exists(signal_config_path):
    with open(signal_config_path, 'r') as f:
        config = json.load(f)
    print(f"\nCurrent signal config: {config.get('mode', 'unknown')}")