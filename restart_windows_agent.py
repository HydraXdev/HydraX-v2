#!/usr/bin/env python3
"""
Quick restart script for Windows agent
Based on HANDOVER.md - agent should be at C:\BITTEN_Agent\agent.py
"""

import subprocess
import time
import requests

def restart_agent_via_ssh():
    """Try to restart via SSH if possible"""
    commands = [
        # Try to restart existing agent
        'ssh -o ConnectTimeout=5 Administrator@localhost "taskkill /F /IM python.exe /T 2>nul; cd C:\\BITTEN_Agent && python agent.py"',
        
        # Alternative: Try PowerShell remote execution
        'ssh -o ConnectTimeout=5 Administrator@localhost "powershell -Command \\"Stop-Process -Name python -Force -ErrorAction SilentlyContinue; Start-Process -FilePath python -ArgumentList C:\\BITTEN_Agent\\agent.py -WindowStyle Hidden\\""'
    ]
    
    for cmd in commands:
        print(f"Trying: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ SSH restart successful")
                return True
        except:
            pass
    
    return False

def test_agent_connection():
    """Test if agent is responding"""
    try:
        response = requests.get("http://localhost:5555/status", timeout=5)
        if response.status_code == 200:
            print("✅ Agent is responding!")
            return True
    except:
        pass
    
    print("❌ Agent not responding")
    return False

def main():
    print("🔄 RESTARTING WINDOWS AGENT...")
    
    # Test current state
    if test_agent_connection():
        print("✅ Agent is already running!")
        return
    
    # Try SSH restart
    if restart_agent_via_ssh():
        time.sleep(5)
        if test_agent_connection():
            print("✅ Agent restart successful!")
            return
    
    print("❌ Could not restart agent via SSH")
    print("\n📋 MANUAL RESTART REQUIRED:")
    print("1. RDP to localhost")
    print("2. Open Command Prompt")
    print("3. Run: cd C:\\BITTEN_Agent")
    print("4. Run: python agent.py")
    print("5. Keep window open")

if __name__ == "__main__":
    main()