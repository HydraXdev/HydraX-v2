#!/usr/bin/env python3
"""
QUICK FIX - Get backup agents working fast
"""

import requests
import json
import time

def quick_fix():
    target_ip = "3.145.84.187"
    primary_port = 5555
    session = requests.Session()
    session.timeout = 15
    
    print("🔥 QUICK FIX - Getting backup agents online...")
    
    # Test primary agent
    try:
        response = session.get(f"http://{target_ip}:{primary_port}/health")
        if response.status_code == 200:
            print("✅ Primary agent confirmed online")
        else:
            print("❌ Primary agent not responding")
            return False
    except Exception as e:
        print(f"❌ Primary agent error: {e}")
        return False
    
    # Simple command to restart backup agents
    commands = [
        "cd C:\\BITTEN_Agent",
        "Start-Process python -ArgumentList 'backup_agent.py' -WindowStyle Hidden",
        "Start-Process python -ArgumentList 'websocket_agent.py' -WindowStyle Hidden"
    ]
    
    for i, cmd in enumerate(commands):
        print(f"🔄 Executing step {i+1}: {cmd}")
        try:
            response = session.post(
                f"http://{target_ip}:{primary_port}/execute",
                json={
                    "command": cmd,
                    "type": "powershell"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Step {i+1} completed")
                else:
                    print(f"⚠️  Step {i+1}: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ Step {i+1} failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Step {i+1} error: {e}")
    
    print("⏳ Waiting 8 seconds for agents to start...")
    time.sleep(8)
    
    # Quick test
    agents = [5555, 5556, 5557]
    working = 0
    
    for port in agents:
        try:
            response = session.get(f"http://{target_ip}:{port}/health", timeout=8)
            if response.status_code == 200:
                data = response.json()
                agent_name = data.get('agent_id', f'port_{port}')
                print(f"✅ {agent_name}: ONLINE")
                working += 1
            else:
                print(f"❌ Port {port}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Port {port}: Connection failed")
    
    print(f"📊 RESULT: {working}/3 agents working")
    
    if working == 3:
        print("🎉 SUCCESS - All agents online!")
        return True
    elif working >= 2:
        print("⚠️  PARTIAL - System bulletproof with primary + backup")
        return True
    else:
        print("❌ FAILED - Only primary working")
        return False

if __name__ == "__main__":
    quick_fix()