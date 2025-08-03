#!/usr/bin/env python3
"""
AWS Bridge Monitor - Detect when production bridge comes online
"""

import socket
import requests
import time
import json
from datetime import datetime

def test_aws_bridge():
    """Test if AWS bridge is online"""
    try:
        # Test socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 5555))
        sock.close()
        
        if result == 0:
            # Test HTTP health
            response = requests.get('http://localhost:5555/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return True, data
        
        return False, None
        
    except Exception as e:
        return False, str(e)

def monitor_bridge():
    """Monitor AWS bridge status"""
    print("🔍 AWS Bridge Monitor Started")
    print("Checking localhost:5555 every 30 seconds...")
    print("Press Ctrl+C to stop")
    
    last_status = False
    
    while True:
        try:
            online, data = test_aws_bridge()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            if online and not last_status:
                print(f"✅ {current_time} - AWS BRIDGE ONLINE!")
                if data:
                    print(f"   Agent: {data.get('agent_id', 'Unknown')}")
                    print(f"   Enhanced: {'Yes' if 'socket_running' in data else 'No'}")
                last_status = True
                
            elif not online and last_status:
                print(f"❌ {current_time} - AWS bridge went offline")
                last_status = False
                
            elif online:
                print(f"✅ {current_time} - Bridge online")
            else:
                print(f"❌ {current_time} - Bridge offline")
                
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    monitor_bridge()
