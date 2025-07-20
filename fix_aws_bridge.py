#!/usr/bin/env python3
"""
Fix AWS Bridge - Deploy a working enhanced agent
"""

import requests
import time
import socket
import json

def test_aws_connection():
    """Test if AWS server is reachable"""
    try:
        # Try to connect to any port to see if server is up
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('3.145.84.187', 22))  # Try SSH port
        sock.close()
        if result == 0:
            print("✅ AWS server is reachable")
            return True
        else:
            print("❌ AWS server is not reachable")
            return False
    except Exception as e:
        print(f"❌ AWS connection test failed: {e}")
        return False

def restart_original_agent():
    """Try to restart the original agent"""
    try:
        # First try to see if any agent is running
        response = requests.get('http://3.145.84.187:5555/health', timeout=5)
        if response.status_code == 200:
            print("✅ Original agent is already running")
            return True
    except:
        pass
    
    print("❌ Original agent is not running")
    return False

def test_socket_directly():
    """Test socket connection to AWS server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('3.145.84.187', 9000))
        
        ping_command = json.dumps({'command': 'ping'})
        sock.send(ping_command.encode('utf-8'))
        
        response = sock.recv(4096)
        result = json.loads(response.decode('utf-8'))
        
        sock.close()
        
        print("✅ Socket connection successful!")
        print(f"Status: {result.get('status', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Socket connection failed: {e}")
        return False

def main():
    print("🔧 AWS Bridge Fix Tool")
    print("=" * 30)
    
    # Step 1: Test basic connectivity
    if not test_aws_connection():
        print("❌ Cannot reach AWS server at all")
        return False
    
    # Step 2: Check if original agent is running
    if not restart_original_agent():
        print("❌ Original agent is down - may need manual restart")
        return False
    
    # Step 3: Test socket functionality
    if test_socket_directly():
        print("✅ Socket functionality is working!")
        return True
    else:
        print("❌ Socket functionality is not working")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ AWS Bridge is functional!")
        print("You can now test with: python3 test_mt5_socket_bridge.py")
    else:
        print("\n❌ AWS Bridge needs manual intervention")
        print("The enhanced agent may need to be restarted manually")