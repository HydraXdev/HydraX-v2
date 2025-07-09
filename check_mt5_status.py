#!/usr/bin/env python3
import requests
import json

agent_url = "http://3.145.84.187:5555"

# Check status
print("=== MT5 FARM STATUS ===\n")

# Get current status
resp = requests.get(f"{agent_url}/status")
status = resp.json()
print(f"Setup Progress: {status.get('setup_progress', 0)}%")
print(f"MT5 Instances Found: {status.get('mt5_instances', {})}")

# Find existing MT5 installations
print("\n=== SEARCHING FOR MT5 INSTALLATIONS ===")
resp = requests.get(f"{agent_url}/find_mt5")
mt5_data = resp.json()

if 'mt5_installations' in mt5_data:
    print(f"\nFound {len(mt5_data['mt5_installations'])} MT5 installations:")
    for mt5 in mt5_data['mt5_installations']:
        print(f"  - {mt5['path']}")
        print(f"    Executable: {mt5['exe']}")

# Check what files exist
print("\n=== CHECKING MT5 FARM STRUCTURE ===")
cmd = "Get-ChildItem -Path C:\\MT5_Farm -Recurse -Filter *.exe | Select-Object -First 10 | Format-Table FullName"
resp = requests.post(f"{agent_url}/execute", json={"command": cmd, "powershell": True})
result = resp.json()
if 'stdout' in result:
    print(result['stdout'])

# Check if installers downloaded
print("\n=== CHECKING DOWNLOADED INSTALLERS ===")
cmd = "Get-ChildItem -Path C:\\MT5_Farm\\Masters -Filter installer.exe -Recurse | Format-Table FullName, Length"
resp = requests.post(f"{agent_url}/execute", json={"command": cmd, "powershell": True})
result = resp.json()
if 'stdout' in result:
    print(result['stdout'])