#!/usr/bin/env python3
import requests
import time

# Simple test with short timeout
session = requests.Session()
session.timeout = 5

try:
    # Test primary first
    print("Testing primary agent...")
    response = session.get("http://3.145.84.187:5555/health")
    if response.status_code == 200:
        print("✅ Primary agent working")
        
        # Try to restart backup via primary
        print("Restarting backup agent...")
        response = session.post(
            "http://3.145.84.187:5555/restart_backup",
            json={}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Restart result: {result}")
        else:
            print(f"❌ Restart failed: {response.status_code}")
            
    else:
        print("❌ Primary agent not working")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("Done.")