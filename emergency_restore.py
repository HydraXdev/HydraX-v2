#!/usr/bin/env python3
"""
EMERGENCY RESTORE - Get bulletproof agent back online NOW
"""

import subprocess
import time
import requests
import socket

def test_port_connection(host, port, timeout=3):
    """Test if port is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_agent_status():
    """Check if agent is responding"""
    try:
        response = requests.get("http://3.145.84.187:5555/health", timeout=5)
        if response.status_code == 200:
            return True, "Agent responding"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def restart_file_server():
    """Restart the file server for agent deployment"""
    try:
        # Kill existing file server
        subprocess.run(["pkill", "-f", "serve_bulletproof_files.py"], capture_output=True)
        time.sleep(2)
        
        # Start new file server
        subprocess.Popen([
            "python3", "/root/HydraX-v2/serve_bulletproof_files.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(3)
        
        # Test if server is running
        if test_port_connection("0.0.0.0", 9999):
            return True, "File server restarted"
        else:
            return False, "File server failed to start"
            
    except Exception as e:
        return False, f"Error restarting server: {e}"

def main():
    print("🚨 EMERGENCY RESTORE - BULLETPROOF AGENT")
    print("=" * 50)
    
    # Step 1: Check current status
    print("1. Checking agent status...")
    is_online, status = check_agent_status()
    
    if is_online:
        print(f"✅ Agent is online: {status}")
        return True
    else:
        print(f"❌ Agent offline: {status}")
    
    # Step 2: Check port connectivity
    print("2. Testing port connectivity...")
    if test_port_connection("3.145.84.187", 5555):
        print("✅ Port 5555 is reachable")
    else:
        print("❌ Port 5555 unreachable - Windows server may be down")
        print("\n🔧 MANUAL FIX REQUIRED:")
        print("1. Check AWS console - is EC2 instance running?")
        print("2. If running, RDP to 3.145.84.187")
        print("3. Run: cd C:\\BITTEN_Agent && START_AGENTS.bat")
        return False
    
    # Step 3: Restart file server
    print("3. Restarting file distribution server...")
    server_ok, server_msg = restart_file_server()
    print(f"{'✅' if server_ok else '❌'} File server: {server_msg}")
    
    # Step 4: Final test
    print("4. Final connectivity test...")
    time.sleep(5)
    is_online, status = check_agent_status()
    
    if is_online:
        print(f"✅ RESTORE SUCCESS: {status}")
        print("\n🛡️ Bulletproof agent is back online!")
        return True
    else:
        print(f"❌ RESTORE FAILED: {status}")
        print("\n🔧 MANUAL INTERVENTION REQUIRED")
        print("The Windows server appears to be down or agents crashed")
        print("You need to manually restart the agents on Windows")
        return False

if __name__ == "__main__":
    main()